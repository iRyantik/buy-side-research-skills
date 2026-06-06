"""Canonical facts repository, snapshots, period selection, and read-model rendering."""

from __future__ import annotations

import json
import math
import os
import re
import tempfile
from dataclasses import asdict, dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any


TRUST_ORDER = {
    "regulatory_filing": 100,
    "official_web": 90,
    "provider_api": 70,
    "trusted_web": 50,
    "broad_web": 30,
    "derived": 20,
    "legacy": 10,
}


@dataclass(frozen=True)
class Period:
    period_id: str
    label: str
    period_end: str
    kind: str


@dataclass(frozen=True)
class FactCandidate:
    metric: str
    period_id: str
    value: Any
    unit: str | None
    currency: str | None
    dimensions: dict[str, str]
    source_id: str
    source_layer: str
    status: str
    confidence: float
    source_detail: str | None = None


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _atomic_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", delete=False, dir=path.parent, suffix=".tmp"
    ) as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write("\n")
        temporary = Path(handle.name)
    os.replace(temporary, path)


def _finite(value: Any) -> bool:
    return not isinstance(value, float) or math.isfinite(value)


def _fact_key(fact: dict[str, Any]) -> tuple:
    return (
        fact["metric"],
        fact["period_id"],
        tuple(sorted((fact.get("dimensions") or {}).items())),
        fact.get("unit"),
        fact.get("currency"),
    )


def _period_boundary(value: str, is_start: bool) -> date:
    normalized = value.strip()
    fy = re.fullmatch(r"FY\s*(\d{4})", normalized, re.IGNORECASE)
    if fy:
        year = int(fy.group(1))
        return date(year, 1, 1) if is_start else date(year, 12, 31)
    return date.fromisoformat(normalized)


def resolve_period_ids(
    periods: list[Period],
    profile: str,
    from_value: str | None,
    to_value: str | None,
    complete_years: int | None = None,
) -> list[str]:
    """Resolve explicit or profile-default periods without coupling range to profile."""
    ordered = sorted(periods, key=lambda item: item.period_end)
    if from_value or to_value:
        lower = date.min if not from_value or from_value == "earliest" else _period_boundary(from_value, True)
        upper = date.max if not to_value or to_value == "latest" else _period_boundary(to_value, False)
        return [
            item.period_id
            for item in ordered
            if lower <= date.fromisoformat(item.period_end) <= upper
        ]
    annual = [item for item in ordered if item.kind == "annual"]
    interim = [item for item in ordered if item.kind != "annual"]
    if complete_years is not None:
        selected = annual[-complete_years:] + [
            item for item in interim if not annual or item.period_end > annual[-1].period_end
        ]
    elif profile == "lite":
        selected = annual[-1:] + interim[-1:]
    elif profile == "full":
        selected = annual[-5:] + [
            item for item in interim if not annual or item.period_end > annual[-1].period_end
        ]
    else:
        raise ValueError(f"unknown profile: {profile}")
    return [item.period_id for item in sorted(selected, key=lambda item: item.period_end)]


class FactsRepository:
    """Only supported writer for canonical facts and generated actuals views."""

    def __init__(self, internal_dir: Path, entity: dict[str, Any] | None = None):
        self.internal_dir = Path(internal_dir)
        self.store_path = self.internal_dir / "facts-store.json"
        if self.store_path.exists():
            self.store = json.loads(self.store_path.read_text(encoding="utf-8"))
        else:
            self.store = {
                "schema_version": 1,
                "entity": entity or {},
                "periods": [],
                "facts": [],
                "segments": [],
                "sources": [],
                "quality": {"conflicts": [], "warnings": []},
                "migration_history": [],
            }

    def load(self) -> dict[str, Any]:
        return self.store

    def upsert_period(self, period: Period) -> None:
        payload = asdict(period)
        for index, current in enumerate(self.store["periods"]):
            if current["period_id"] == period.period_id:
                self.store["periods"][index] = payload
                return
        self.store["periods"].append(payload)
        self.store["periods"].sort(key=lambda item: item["period_end"])

    def merge(self, candidates: list[FactCandidate]) -> None:
        facts = {_fact_key(item): item for item in self.store["facts"]}
        sources = {item["source_id"]: item for item in self.store["sources"]}
        for candidate in candidates:
            if not _finite(candidate.value):
                self.store["quality"]["warnings"].append(
                    {"metric": candidate.metric, "period_id": candidate.period_id, "reason": "non-finite"}
                )
                continue
            incoming = asdict(candidate)
            key = _fact_key(incoming)
            sources.setdefault(
                candidate.source_id,
                {"source_id": candidate.source_id, "source_layer": candidate.source_layer},
            )
            existing = facts.get(key)
            if existing is None:
                facts[key] = incoming
                continue
            if existing["value"] == incoming["value"]:
                if TRUST_ORDER.get(candidate.source_layer, 0) > TRUST_ORDER.get(
                    existing.get("source_layer", ""), 0
                ):
                    facts[key] = incoming
                continue
            conflict = {
                "metric": candidate.metric,
                "period_id": candidate.period_id,
                "kept": existing,
                "candidate": incoming,
                "recorded_at_utc": _utc_now(),
            }
            if TRUST_ORDER.get(candidate.source_layer, 0) > TRUST_ORDER.get(
                existing.get("source_layer", ""), 0
            ):
                conflict["kept"], conflict["candidate"] = incoming, existing
                facts[key] = incoming
            self.store["quality"]["conflicts"].append(conflict)
        self.store["facts"] = sorted(
            facts.values(), key=lambda item: (item["period_id"], item["metric"], str(item["dimensions"]))
        )
        self.store["sources"] = sorted(sources.values(), key=lambda item: item["source_id"])
        self.commit()

    def commit(self) -> None:
        self.store["updated_at_utc"] = _utc_now()
        _atomic_json(self.store_path, self.store)

    def append_snapshot(self, kind: str, snapshot: dict[str, Any]) -> None:
        if kind not in {"market", "consensus"}:
            raise ValueError("snapshot kind must be market or consensus")
        if not snapshot.get("as_of"):
            raise ValueError("snapshot requires as_of")
        path = self.internal_dir / f"{kind}-snapshots.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(snapshot, ensure_ascii=False, allow_nan=False) + "\n")

    def _latest_snapshot(self, kind: str) -> dict[str, Any]:
        path = self.internal_dir / f"{kind}-snapshots.jsonl"
        if not path.exists():
            return {}
        records = [
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        return max(records, key=lambda item: str(item.get("as_of", "")), default={})

    def render_actuals(self, write: bool = True) -> dict[str, Any]:
        periods = {item["period_id"]: item for item in self.store["periods"]}
        annual = sorted(
            (item for item in periods.values() if item["kind"] == "annual"),
            key=lambda item: item["period_end"],
        )
        interim = sorted(
            (item for item in periods.values() if item["kind"] != "annual"),
            key=lambda item: item["period_end"],
        )
        aliases = {}
        if annual:
            aliases[annual[-1]["period_id"]] = "latest_fy"
        if interim:
            aliases[interim[-1]["period_id"]] = "latest_quarter"
        view: dict[str, Any] = {
            "_schema": "actuals-resolved v2.2",
            "_write_policy": "generated-read-model",
            "_generated_at_utc": _utc_now(),
            **self.store.get("entity", {}),
            "latest_fy_period": annual[-1]["label"] if annual else None,
            "latest_quarter_period": interim[-1]["label"] if interim else None,
            "income_statement": {"latest_fy": {}, "latest_quarter": {}},
            "balance_sheet": {"latest_fy": {}, "latest_quarter": {}},
            "cash_flow": {"latest_fy": {}, "latest_quarter": {}},
            "segments": self.store.get("segments", []),
            "market_data": self._latest_snapshot("market"),
            "consensus": self._latest_snapshot("consensus"),
            "source_map": {
                item["source_id"]: item for item in self.store.get("sources", [])
            },
        }
        for fact in self.store["facts"]:
            period_alias = aliases.get(fact["period_id"])
            if not period_alias or "." not in fact["metric"]:
                continue
            section, field = fact["metric"].split(".", 1)
            if section not in {"income_statement", "balance_sheet", "cash_flow"}:
                continue
            view[section][period_alias][field] = {
                "value": fact["value"],
                "unit": fact.get("unit"),
                "currency": fact.get("currency"),
                "source_id": fact["source_id"],
                "source_layer": fact["source_layer"],
                "source_detail": fact.get("source_detail"),
                "status": fact["status"],
            }
        if write:
            _atomic_json(self.internal_dir / "actuals-resolved.json", view)
        return view
