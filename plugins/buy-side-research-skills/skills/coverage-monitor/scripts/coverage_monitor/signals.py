from __future__ import annotations

from dataclasses import dataclass
from datetime import date


ORDINARY_RETURN_PCT = 5.0
ORDINARY_VOLUME_RATIO = 3.0
ORDINARY_GAP_PCT = 7.0

IMPORTANT_RETURN_PCT = 8.0
IMPORTANT_VOLUME_RATIO = 4.0
IMPORTANT_GAP_PCT = 10.0

QUOTE_EXCEPTION_STATUSES = {"Partial", "No Data", "Stale"}


@dataclass(frozen=True)
class MoverAssessment:
    is_mover: bool
    is_important: bool
    trigger_tags: tuple[str, ...]
    highlight_tags: tuple[str, ...]


def _float(value) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def assess_snapshot(snapshot: dict) -> MoverAssessment | None:
    move = _float(snapshot.get("price_move_pct"))
    volume = _float(snapshot.get("volume_ratio"))
    gap = _float(snapshot.get("gap_pct"))

    ordinary_tags: list[str] = []
    important_tags: list[str] = []
    if move is not None and abs(move) >= ORDINARY_RETURN_PCT:
        ordinary_tags.append("Return >= 5%")
    if volume is not None and volume >= ORDINARY_VOLUME_RATIO:
        ordinary_tags.append("Volume >= 3.0x")
    if gap is not None and abs(gap) >= ORDINARY_GAP_PCT:
        ordinary_tags.append("Gap >= 7%")

    if move is not None and abs(move) >= IMPORTANT_RETURN_PCT:
        important_tags.append("Return >= 8%")
    if volume is not None and volume >= IMPORTANT_VOLUME_RATIO:
        important_tags.append("Volume >= 4.0x")
    if gap is not None and abs(gap) >= IMPORTANT_GAP_PCT:
        important_tags.append("Gap >= 10%")

    if not ordinary_tags and not important_tags:
        return None
    tags = tuple(dict.fromkeys([*ordinary_tags, *important_tags]))
    return MoverAssessment(
        is_mover=True,
        is_important=bool(important_tags),
        trigger_tags=tags,
        highlight_tags=tuple(important_tags),
    )


def quote_exception_status(snapshot: dict, report_day: str | None = None) -> str | None:
    explicit = str(snapshot.get("quote_status") or "").strip()
    if explicit in QUOTE_EXCEPTION_STATUSES:
        return explicit
    market_time = str(snapshot.get("market_time") or "").strip()
    if not market_time or not report_day:
        return None
    try:
        market_date = date.fromisoformat(market_time)
        target_date = date.fromisoformat(report_day)
    except ValueError:
        return None
    if (target_date - market_date).days > 5:
        return "Stale"
    return None


def summarize_data_health(gaps: list[str]) -> list[str]:
    counts = {
        "no_data": 0,
        "partial": 0,
        "stale": 0,
        "filing": 0,
        "search": 0,
        "source": 0,
    }
    for gap in gaps:
        lowered = gap.lower()
        if "quote_status:partial" in lowered or "partial_quote" in lowered:
            counts["partial"] += 1
        elif "quote_status:stale" in lowered:
            counts["stale"] += 1
        elif "empty_quote_history" in lowered or "quote_fetch_failed" in lowered or "quote_status:no data" in lowered:
            counts["no_data"] += 1
        elif "filing_unavailable" in lowered:
            counts["filing"] += 1
        elif "no_company_news_found" in lowered or "weak_search_results" in lowered:
            counts["search"] += 1
        elif "source_fetch_failed" in lowered:
            counts["source"] += 1
    lines: list[str] = []
    if counts["no_data"]:
        lines.append(f"{counts['no_data']} no-data ticker")
    if counts["partial"]:
        lines.append(f"{counts['partial']} partial quote")
    if counts["stale"]:
        lines.append(f"{counts['stale']} stale quote")
    if counts["filing"]:
        lines.append(f"{counts['filing']} filing unavailable")
    if counts["search"]:
        lines.append(f"{counts['search']} weak news fetch")
    if counts["source"]:
        lines.append(f"{counts['source']} source fetch failed")
    return lines
