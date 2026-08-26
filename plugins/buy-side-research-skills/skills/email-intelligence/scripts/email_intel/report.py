"""Canonical, immutable-ish report model shared by every email-intelligence renderer."""

from __future__ import annotations

import html
import re
from collections import defaultdict

from .identity import company_key, industry_key, normalize_ticker
from .parse import Email


_BROKERS = {
    "ubs.com": "UBS", "bernsteinsg.com": "Bernstein", "morganstanley.com": "Morgan Stanley",
    "jefferies.com": "Jefferies", "nomura.com": "Nomura", "bofa.com": "BofA",
    "citi.com": "Citi", "gs.com": "Goldman Sachs", "cjsc.com.cn": "长江证券",
    "mailservice.cjsc.com.cn": "长江证券", "guangfa.com.cn": "广发证券",
}

# 公司卡 read-through prun：主标的卡里出现「为<其他公司>提供/带来/贡献…增长点」这类
# 把对手方/下游受益写进主标事实的从句，裁到该从句之前，只留主标的本身。
_BENEFIT_RE = re.compile(
    r"[，,；;。](?P<target>(?:为|给|向)[^，,；;。]{2,24}(?:提供|带来|贡献|创造)"
    r"(?:下一|新的?|额外)?(?:增长点|增量|增长|空间|催化))"
)
_COMPANY_BUCKETS = {"core", "other_coverage", "new_idea"}


def _clean(value: object) -> str:
    text = str(value or "").strip()
    # Some upstream model responses contain already escaped Outlook text.
    for _ in range(2):
        decoded = html.unescape(text)
        if decoded == text:
            break
        text = decoded
    return text


def _broker(sender: str, explicit: str = "") -> str:
    if explicit:
        return _clean(explicit)
    sender = _clean(sender)
    if "@" not in sender:
        return sender or "来源邮件"
    domain = sender.rsplit("@", 1)[1].lower()
    if domain in _BROKERS:
        return _BROKERS[domain]
    for suffix, label in _BROKERS.items():
        if domain.endswith("." + suffix):
            return label
    return sender


def _norm(value: object) -> str:
    return re.sub(r"[^0-9a-z\u4e00-\u9fff]+", "", _clean(value).lower())


def _item_key(item: dict, email_id: str, sequence: int) -> str:
    ticker = normalize_ticker(item.get("coverage_ticker") or item.get("ticker"))
    if ticker:
        return "ticker:" + ticker
    company = company_key(item.get("company") or item.get("company_en"))
    if company:
        return "company:" + company
    merge_key = _clean(item.get("merge_key"))
    if merge_key:
        return "event:" + merge_key.lower()
    industry = industry_key(item.get("industry"))
    summary = _norm(item.get("what_changed") or item.get("summary"))[:80]
    return f"signal:{industry}:{summary}:{email_id}:{sequence}"


def _human_event(item: dict, last_events: dict) -> str:
    raw = _clean(item.get("what_changed") or item.get("summary"))
    summary = _clean(item.get("summary"))
    if raw.startswith("首次出现") and summary and not summary.startswith("首次出现"):
        return f"新事件｜{summary}"
    internal = "system last_events" in raw or bool(re.search(r"\([^)]*analysis-\d{4}-\d{2}-\d{2}[^)]*\)", raw))
    key = _clean(item.get("merge_key"))
    baseline = last_events.get(key, {}) if key else {}
    if not internal:
        return raw
    prior = _clean(baseline.get("what_changed") or baseline.get("summary"))
    if not prior:
        prior = summary
    if not prior or "system last_events" in prior:
        prior = f"{_clean(item.get('company') or item.get('industry') or '该主题')}此前已被跟踪"
    delta = _clean(item.get("delta_vs_last"))
    if delta:
        return f"已有事件的新信息｜此前：{prior}；本次新增：{delta}"
    return f"重复事件｜此前：{prior}；本次仅为报告正文解读，无新增事实。"


def _prune_readthrough(text: str, item: dict, all_company_keys: set[str]) -> str:
    """只对单公司卡生效：若事实里是把另一家公司当受益主角的从句，则裁到该从句前。"""
    bucket = _clean(item.get("bucket"))
    if bucket not in _COMPANY_BUCKETS:
        return text
    primary = company_key(_clean(item.get("company") or item.get("company_en")))
    if not primary:
        return text
    for m in _BENEFIT_RE.finditer(text):
        target = _clean(m.group("target"))
        # 提取受益主体（"为纽威股份提供…" → 纽威股份）
        tm = re.match(r"(?:为|给|向)([^，,；;。]+?)(?:提供|带来|贡献|创造)", target)
        if not tm:
            continue
        beneficiary = company_key(tm.group(1))
        if beneficiary and beneficiary != primary and beneficiary in all_company_keys:
            return text[: m.start()].rstrip("，,；;。 ").rstrip()
    return text


def build_report(emails: list[Email], reviews: list[dict], *, last_events: dict | None = None) -> dict:
    """Normalize, merge and freeze the semantic report consumed by all outputs."""
    last_events = last_events or {}
    email_map = {e.key: e for e in emails}
    review_brokers = {str(r.get("_email_id") or ""): _clean(r.get("broker")) for r in reviews}
    all_company_keys: set[str] = set()
    for review in reviews:
        for raw in review.get("items") or []:
            for name in (_clean(raw.get("company")), _clean(raw.get("company_en"))):
                key = company_key(name)
                if key:
                    all_company_keys.add(key)
    merged: dict[str, dict] = {}
    sequence = 0
    for review in reviews:
        email_id = str(review.get("_email_id") or "")
        email = email_map.get(email_id)
        for raw in review.get("items") or []:
            if _clean(raw.get("bucket")) == "filtered":
                continue
            sequence += 1
            item = dict(raw)
            key = _item_key(item, email_id, sequence)
            broker = _broker(email.sender if email else "", _clean(item.get("broker")) or review_brokers.get(email_id, ""))
            fact = {
                "text": _prune_readthrough(_human_event(item, last_events), item, all_company_keys),
                "why_it_matters": _clean(item.get("why_it_matters") or item.get("focus_reason")),
                "action": _clean(item.get("action")),
                "broker": broker,
                "email_id": email_id,
                "url": _clean(email.outlook_link if email else ""),
            }
            if key not in merged:
                merged[key] = {
                    **item,
                    "company": _clean(item.get("company")),
                    "ticker": normalize_ticker(item.get("coverage_ticker") or item.get("ticker")),
                    "industry": _clean(item.get("industry")) or "Other",
                    "facts": [], "brokers": [], "source_ids": [],
                }
            current = merged[key]
            if fact["text"] and not any(x["text"] == fact["text"] and x["broker"] == broker for x in current["facts"]):
                current["facts"].append(fact)
            if broker and broker not in current["brokers"]:
                current["brokers"].append(broker)
            if email_id and email_id not in current["source_ids"]:
                current["source_ids"].append(email_id)
            if current.get("priority") != "high" and item.get("priority") == "high":
                current["priority"] = "high"
            if not current.get("why_it_matters") and item.get("why_it_matters"):
                current["why_it_matters"] = item["why_it_matters"]

    meetings: dict[str, dict] = {}
    for review in reviews:
        email_id = str(review.get("_email_id") or "")
        email = email_map.get(email_id)
        for raw in review.get("meetings") or []:
            m = dict(raw)
            key = "|".join((_norm(m.get("title")), _norm(m.get("company")), _clean(m.get("date"))))
            broker = _broker(email.sender if email else "", _clean(m.get("broker")) or review_brokers.get(email_id, ""))
            if key not in meetings:
                meetings[key] = {**m, "title": _clean(m.get("title") or m.get("company") or "Meeting"),
                                 "broker": broker, "brokers": [], "sources": []}
            current = meetings[key]
            if broker and broker not in current["brokers"]:
                current["brokers"].append(broker)
            source = {"email_id": email_id, "broker": broker,
                      "url": _clean(email.outlook_link if email else "")}
            if source not in current["sources"]:
                current["sources"].append(source)

    items = list(merged.values())
    priority = {"high": 0, "medium": 1, "low": 2}
    items.sort(key=lambda x: (priority.get(_clean(x.get("priority")), 9), _clean(x.get("company") or x.get("industry"))))
    meeting_list = sorted(meetings.values(), key=lambda x: (_clean(x.get("date")), _clean(x.get("time")), x["title"]))
    sections = defaultdict(list)
    for item in items:
        sections[_clean(item.get("bucket")) or "industry_signal"].append(item)
    return {
        "items": items,
        "meetings": meeting_list,
        "sections": {name: list(sections.get(name, [])) for name in ("industry_signal", "core", "other_coverage", "new_idea")},
        "stats": {"emails": len(emails), "signals": len(items), "meetings": len(meeting_list)},
    }


def validate_report(report: dict) -> list[str]:
    """Source-consistency check: every source/broker on a merged block must be backed by a fact."""
    problems: list[str] = []
    for item in report.get("items", []):
        label = _clean(item.get("company") or item.get("industry") or "item")
        fact_ids = {f.get("email_id") for f in item.get("facts", []) if f.get("email_id")}
        missing = set(item.get("source_ids") or []) - fact_ids
        if missing:
            problems.append(f"{label}: source_ids 缺少对应 fact.email_id: {sorted(missing)[:3]}")
        fact_brokers = {f.get("broker") for f in item.get("facts", []) if f.get("broker")}
        missing_b = set(item.get("brokers") or []) - fact_brokers
        if missing_b:
            problems.append(f"{label}: brokers 缺少对应 fact.broker: {sorted(missing_b)[:3]}")
    for meeting in report.get("meetings", []):
        label = _clean(meeting.get("title") or meeting.get("company") or "meeting")
        source_brokers = {s.get("broker") for s in meeting.get("sources", []) if s.get("broker")}
        missing = set(meeting.get("brokers") or []) - source_brokers
        if missing:
            problems.append(f"{label}: meeting brokers 缺少对应 source.broker: {sorted(missing)[:3]}")
    return problems
