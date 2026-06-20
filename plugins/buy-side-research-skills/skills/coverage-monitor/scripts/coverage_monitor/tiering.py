from __future__ import annotations

from datetime import date

from .coverage import CoverageEntry, extract_date_prefix


def _parse_date_prefix(value: str) -> date | None:
    prefix = extract_date_prefix(value)
    if not prefix:
        return None
    try:
        year, month, day = (int(part) for part in prefix.split("-"))
    except ValueError:
        return None
    return date(year, month, day)


def _coerce_today(today: str | date | None) -> date:
    if isinstance(today, date):
        return today
    if isinstance(today, str) and today:
        parsed = _parse_date_prefix(today)
        if parsed:
            return parsed
    return date.today()


def derive_research_tier(entry: CoverageEntry, today: str | date | None = None, artifact_count: int = 0) -> str:
    current_day = _coerce_today(today)
    monitor = entry.monitor.strip().lower()
    stage = entry.stage.strip().lower()
    last_review = _parse_date_prefix(entry.last_review)
    has_recent_review = bool(last_review and (current_day - last_review).days <= 90)
    has_trigger = bool(entry.next_trigger.strip())
    has_ticker = bool(entry.ticker.strip())
    has_company = bool(entry.company.strip())
    effective_artifact_count = max(artifact_count, entry.artifact_count)

    if stage == "dormant" or monitor == "no":
        return "T4"
    if has_ticker and (monitor == "core" or (has_trigger and has_recent_review)):
        return "T1"
    if has_ticker and (
        effective_artifact_count >= 1 or bool(entry.last_review.strip()) or stage in {"building", "monitoring", "active", "testing"}
    ):
        return "T2"
    if has_company:
        return "T3"
    return "T4"


def derive_alert_tier(entry: CoverageEntry) -> str:
    research_tier = entry.research_tier.strip().upper()
    monitor = entry.monitor.strip().lower()
    if monitor == "no" or not entry.ticker.strip():
        return "A3"
    if monitor == "daily":
        return "A2"
    if research_tier == "T1":
        return "A1"
    if research_tier == "T2":
        return "A2"
    return "A3"
