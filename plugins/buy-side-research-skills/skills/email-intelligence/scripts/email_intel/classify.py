"""Deterministic routing after the model extracts email items."""

from __future__ import annotations

from .context import coverage_lookup


_MEANINGFUL_EVENTS = {
    "earnings", "estimate_revision", "order", "guidance", "product",
    "management_change", "capital_allocation", "rating_change", "other",
}


def _coverage_match(item: dict, context: dict) -> dict | None:
    by_ticker, by_name = coverage_lookup(context)
    ticker = str(item.get("ticker") or "").strip().lower()
    company = str(item.get("company") or "").strip().lower()
    if ticker and ticker in by_ticker:
        return by_ticker[ticker]
    if company in by_name:
        return by_name[company]
    for name, row in by_name.items():
        if len(name) >= 4 and (name in company or company in name):
            return row
    return None


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
    return "industry_signal"


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
            items.append(one)
        clean["items"] = items
        clean["meetings"] = [dict(m) for m in (clean.get("meetings") or []) if isinstance(m, dict)]
        normalized.append(clean)
    return normalized
