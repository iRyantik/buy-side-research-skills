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


def derive_coverage_status(entry: CoverageEntry, today: str | date | None = None, artifact_count: int = 0) -> str:
    has_ticker = bool(entry.ticker.strip())
    has_company = bool(entry.company.strip())
    effective_artifact_count = max(artifact_count, entry.artifact_count)
    quickread_count = entry.quickread_artifact_count
    has_last_review = bool(entry.last_review.strip())

    if (has_ticker or has_company) and (quickread_count >= 1 or effective_artifact_count >= 1 or has_last_review):
        return "Building Coverage"
    if has_company:
        return "Radar"
    return "Radar"


def should_trigger_core_review(entry: CoverageEntry, today: str | date | None = None) -> bool:
    current_day = _coerce_today(today)
    last_review = _parse_date_prefix(entry.last_review)
    has_recent_review = bool(last_review and (current_day - last_review).days <= 90)
    has_trigger = bool(entry.next_trigger.strip())
    has_ticker = bool(entry.ticker.strip())
    return bool(
        entry.deepwork_artifact_count >= 1
        and entry.has_research_memory
        and has_ticker
        and has_recent_review
        and has_trigger
    )


def derive_monitor_status(entry: CoverageEntry) -> str:
    if entry.coverage_status == "Core Coverage" and entry.ticker.strip():
        return "Core Watch"
    return "Daily Watch"
