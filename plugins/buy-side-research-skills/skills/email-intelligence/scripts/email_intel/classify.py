"""Deterministic routing after the model extracts email items."""

from __future__ import annotations

import re

from .context import coverage_lookup
from .identity import company_key, normalize_related, normalize_ticker


_MEANINGFUL_EVENTS = {
    "earnings", "estimate_revision", "order", "guidance", "product",
    "management_change", "capital_allocation", "rating_change", "other",
}


def _coverage_match(item: dict, context: dict) -> dict | None:
    by_ticker, by_name = coverage_lookup(context)
    ticker = normalize_ticker(item.get("ticker") or item.get("coverage_ticker"))
    company = company_key(item.get("company"))
    for key, row in by_ticker.items():
        if ticker and normalize_ticker(key) == ticker:
            return row
    if company and company in by_name:
        return by_name[company]
    # company 为空串时 "" in name 恒为 True（空串是任意串的子串）→ 无公司名的
    # 行业级 item 会被错误命中首个覆盖公司。仅当 company 非空才做模糊匹配。
    if company:
        for name, row in by_name.items():
            if len(name) >= 4 and (name in company or company in name):
                return row
    return None


def _norm(value: object) -> str:
    return re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "", str(value or "").casefold())


def _covered_industry(item: dict, context: dict) -> bool:
    industry = _norm(item.get("industry"))
    covered = {_norm(value) for value in (context.get("covered_industries") or []) if value}
    if not covered:
        covered = {_norm(row.get("industry")) for row in (context.get("coverage") or []) if row.get("industry")}
    return bool(industry and industry in covered)


def _explicit_coverage_readthrough(item: dict, context: dict) -> bool:
    related = item.get("related_tickers") or item.get("related_companies") or []
    related_norm = {_norm(value) for value in normalize_related(related)}
    if not related_norm:
        return False
    for row in context.get("coverage") or []:
        identities = {
            _norm(normalize_ticker(row.get("ticker"))), _norm(row.get("company_en")),
            _norm(row.get("company_native")),
        }
        if (identities - {""}) & related_norm:
            return True
    return False


def classify_item(item: dict, context: dict) -> str:
    """Route one extracted item without treating sell-side initiation as New Idea."""
    match = _coverage_match(item, context)
    if match:
        item["coverage_ticker"] = match.get("ticker", "")
        item["coverage_status"] = match.get("coverage", "")
        return "core" if match.get("is_core") else "other_coverage"

    kind = str(item.get("kind") or "company_update")
    event = str(item.get("event_type") or "other")
    focus_fit = str(item.get("focus_fit") or "none").lower()
    action = str(item.get("action") or "note").lower()
    changed = bool(str(item.get("what_changed") or "").strip())

    if (kind == "company_update" and changed and event in _MEANINGFUL_EVENTS
            and focus_fit in {"strong", "moderate"}
            and action in {"read", "watch", "research"}):
        return "new_idea"
    if _covered_industry(item, context) or _explicit_coverage_readthrough(item, context):
        return "industry_signal"
    return "filtered"


def normalize_reviews(reviews: list[dict], context: dict) -> list[dict]:
    normalized: list[dict] = []
    for review in reviews:
        if not isinstance(review, dict):
            continue
        clean = dict(review)
        items = []
        for item in clean.get("items") or []:
            if not isinstance(item, dict):
                continue
            one = dict(item)
            one["bucket"] = classify_item(one, context)
            if one["bucket"] != "filtered":
                items.append(one)
        clean["items"] = items
        clean["meetings"] = [dict(m) for m in (clean.get("meetings") or []) if isinstance(m, dict)]
        normalized.append(clean)
    return normalized
