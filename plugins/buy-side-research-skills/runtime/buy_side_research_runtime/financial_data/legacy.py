"""Legacy actuals schema detection and conversion into canonical fact candidates."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from .facts import FactCandidate, Period


SECTIONS = ("income_statement", "balance_sheet", "cash_flow")


@dataclass(frozen=True)
class MigrationResult:
    periods: list[Period]
    facts: list[FactCandidate]
    detected_shapes: tuple[str, ...]
    segments: list[dict[str, Any]]
    sources: list[dict[str, Any]]
    market_snapshot: dict[str, Any] | None
    consensus_snapshot: dict[str, Any] | None


def _period(label: str, kind_hint: str | None = None) -> Period:
    text = str(label or "unknown").strip()
    date_match = re.search(r"(\d{4})-(\d{2})-(\d{2})", text)
    year_match = re.search(r"(20\d{2}|19\d{2})", text)
    if date_match:
        period_end = date_match.group(0)
    elif year_match:
        period_end = f"{year_match.group(1)}-12-31"
    else:
        period_end = "1900-12-31"
    kind = kind_hint or (
        "interim"
        if re.search(r"\bQ[1-4]\b|quarter|interim|half|H[12]", text, re.IGNORECASE)
        else "annual"
    )
    return Period(text, text, period_end, kind)


def _candidate(
    section: str,
    field: str,
    period_id: str,
    raw: Any,
    fallback_layer: str = "legacy",
    source_id: str = "legacy",
) -> FactCandidate | None:
    if field == "period":
        return None
    if isinstance(raw, dict):
        value = raw.get("value")
        layer = raw.get("source_layer") or fallback_layer
        detail = raw.get("source_detail")
        unit = raw.get("unit")
        currency = raw.get("currency")
        confidence = float(raw.get("confidence", 0.5))
    else:
        value, layer, detail, unit, currency, confidence = raw, fallback_layer, None, None, None, 0.5
    if value is None:
        return None
    return FactCandidate(
        metric=f"{section}.{field}",
        period_id=period_id,
        value=value,
        unit=unit,
        currency=currency,
        dimensions={},
        source_id=source_id,
        source_layer=layer,
        status="migrated",
        confidence=confidence,
        source_detail=detail,
    )


class LegacyMigrator:
    def convert(self, data: dict[str, Any], entity: dict[str, Any]) -> MigrationResult:
        periods: dict[str, Period] = {}
        facts: dict[tuple[str, str], FactCandidate] = {}
        shapes: list[str] = []

        if any(isinstance(data.get(section), dict) for section in SECTIONS):
            shapes.append("v2.2")
            for section in SECTIONS:
                section_data = data.get(section)
                if not isinstance(section_data, dict):
                    continue
                for alias, kind in (("latest_fy", "annual"), ("latest_quarter", "interim")):
                    block = section_data.get(alias)
                    if not isinstance(block, dict):
                        continue
                    label = (
                        block.get("period")
                        or data.get(f"{alias}_period")
                        or alias
                    )
                    period = _period(label, kind)
                    periods[period.period_id] = period
                    for field, raw in block.items():
                        candidate = _candidate(section, field, period.period_id, raw)
                        if candidate:
                            facts[(candidate.metric, candidate.period_id)] = candidate

        dynamic_found = False
        for label, block in data.items():
            if label.startswith("_") or not isinstance(block, dict):
                continue
            if not any(isinstance(block.get(section), dict) for section in SECTIONS):
                continue
            dynamic_found = True
            period = _period(label)
            periods[period.period_id] = period
            for section in SECTIONS:
                for field, raw in (block.get(section) or {}).items():
                    candidate = _candidate(section, field, period.period_id, raw)
                    if candidate:
                        facts.setdefault((candidate.metric, candidate.period_id), candidate)
        if dynamic_found:
            shapes.append("v3-dynamic")

        statements = data.get("statements")
        if isinstance(statements, dict):
            shapes.append("full-v1")
            source_layer = (
                (data.get("source_map") or {}).get("source_provider")
                if isinstance(data.get("source_map"), dict)
                else None
            ) or "provider_api"
            for section in SECTIONS:
                rows = statements.get(section)
                if not isinstance(rows, list):
                    continue
                for row in rows:
                    if not isinstance(row, dict):
                        continue
                    field = str(row.get("concept") or row.get("label") or "unmapped")
                    for label, value in (row.get("values") or {}).items():
                        period = _period(label)
                        periods[period.period_id] = period
                        candidate = _candidate(
                            section, field, period.period_id, value, source_layer, f"legacy:{source_layer}"
                        )
                        if candidate:
                            facts.setdefault((candidate.metric, candidate.period_id), candidate)

        if len(shapes) > 1:
            shapes.append("hybrid")
        source_map = data.get("source_map")
        sources: list[dict[str, Any]] = []
        if isinstance(source_map, dict):
            for source_id, raw in source_map.items():
                payload = dict(raw) if isinstance(raw, dict) else {"detail": raw}
                sources.append({"source_id": str(source_id), **payload})
        elif isinstance(source_map, list):
            sources = [dict(item) for item in source_map if isinstance(item, dict)]
        return MigrationResult(
            periods=sorted(periods.values(), key=lambda item: item.period_end),
            facts=list(facts.values()),
            detected_shapes=tuple(shapes),
            segments=list(data.get("segments") or []) if isinstance(data.get("segments"), list) else [],
            sources=sources,
            market_snapshot=data.get("market_data") if isinstance(data.get("market_data"), dict) else None,
            consensus_snapshot=data.get("consensus") if isinstance(data.get("consensus"), dict) else None,
        )
