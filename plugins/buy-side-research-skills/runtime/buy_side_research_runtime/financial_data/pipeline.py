"""Unified Financial Data acquisition, normalization, and commit pipeline."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

from .facts import FactCandidate, FactsRepository, Period, resolve_period_ids


STANDARD_METRICS = {
    "revenue": "revenue",
    "revenues": "revenue",
    "totalrevenue": "revenue",
    "salesrevenuenet": "revenue",
    "costofrevenue": "cost_of_revenue",
    "grossprofit": "gross_profit",
    "operatingincome": "operating_income",
    "ebit": "ebit",
    "netincome": "net_income",
    "totalassets": "total_assets",
    "cash": "cash",
    "cashandcashequivalents": "cash",
    "inventory": "inventory",
    "accountsreceivable": "accounts_receivable",
    "totalequity": "total_equity_parent",
    "totalequityparent": "total_equity_parent",
    "operatingcashflow": "operating_cf",
    "operatingcf": "operating_cf",
    "capitalexpenditure": "capex",
    "capex": "capex",
    "depreciationandamortization": "d_and_a",
}
UNICODE_METRICS = {
    "매출액": "revenue",
    "영업수익": "revenue",
    "수익(매출액)": "revenue",
    "매출원가": "cost_of_revenue",
    "매출총이익": "gross_profit",
    "영업손익": "operating_income",
    "영업이익": "operating_income",
    "당기순이익": "net_income",
    "자산총계": "total_assets",
    "현금및현금성자산": "cash",
    "매출채권": "accounts_receivable",
    "재고자산": "inventory",
    "자본총계": "total_equity_parent",
    "지배기업소유주지분": "total_equity_parent",
    "영업활동으로 인한 현금흐름": "operating_cf",
    "영업활동 현금흐름": "operating_cf",
    "유형자산의 취득": "capex",
    "감가상각비": "d_and_a",
    "营业额": "revenue",
    "營業額": "revenue",
    "收入": "revenue",
    "营运收入": "revenue",
    "營運收入": "revenue",
    "销售成本": "cost_of_revenue",
    "銷售成本": "cost_of_revenue",
    "毛利": "gross_profit",
    "经营溢利": "operating_income",
    "經營溢利": "operating_income",
    "营运溢利": "operating_income",
    "營運溢利": "operating_income",
    "年内溢利": "net_income",
    "年內溢利": "net_income",
    "本年利润": "net_income",
    "本年利潤": "net_income",
    "资产总额": "total_assets",
    "資產總額": "total_assets",
    "总资产": "total_assets",
    "總資產": "total_assets",
    "现金及现金等价物": "cash",
    "現金及現金等價物": "cash",
    "存货": "inventory",
    "存貨": "inventory",
    "贸易应收款": "accounts_receivable",
    "貿易應收款": "accounts_receivable",
    "股东权益": "total_equity_parent",
    "股東權益": "total_equity_parent",
    "经营活动现金流量": "operating_cf",
    "經營活動現金流量": "operating_cf",
    "经营业务所得之现金流入净额": "operating_cf",
    "經營業務所得之現金流入淨額": "operating_cf",
    "购买物业厂房及设备": "capex",
    "購買物業廠房及設備": "capex",
    "折旧及摊销": "d_and_a",
    "折舊及攤銷": "d_and_a",
}
OFFICIAL_PROVIDERS = {"edgartools", "dart-fss", "edinet-tools", "openesef"}


class Provider(Protocol):
    name: str

    def fetch(self, request: dict[str, Any]) -> dict[str, Any]:
        ...


@dataclass(frozen=True)
class FinancialRequest:
    ticker: str
    market: str
    profile: str = "lite"
    from_value: str | None = None
    to_value: str | None = None
    complete_years: int | None = None


@dataclass(frozen=True)
class FinancialResult:
    status: str
    facts_store: str
    actuals_view: str
    raw_pack: str
    cache_pack: str
    selected_periods: tuple[str, ...]
    reason: str = ""


def _run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _metric_name(row: dict[str, Any]) -> str | None:
    for raw in (row.get("concept"), row.get("label")):
        raw_text = str(raw or "").strip()
        if raw_text in UNICODE_METRICS:
            return UNICODE_METRICS[raw_text]
        normalized = re.sub(r"[^a-z0-9]+", "", str(raw or "").lower())
        if normalized in STANDARD_METRICS:
            return STANDARD_METRICS[normalized]
    return None


def _period(label: str, basis: str | None = None) -> Period:
    text = str(label)
    date_match = re.search(r"(19\d{2}|20\d{2})-(\d{2})-(\d{2})", text)
    year_match = re.search(r"(19\d{2}|20\d{2})", text)
    if date_match:
        period_end = date_match.group(0)
    elif year_match:
        period_end = f"{year_match.group(1)}-12-31"
    else:
        period_end = "1900-12-31"
    normalized_basis = str(basis or "").lower()
    kind = (
        "interim"
        if normalized_basis in {"quarter", "quarterly", "half_year", "interim"}
        or re.search(r"\bQ[1-4]\b|\bH[12]\b|quarter|interim|half", text, re.IGNORECASE)
        else "annual"
    )
    return Period(text, text, period_end, kind)


def normalize_provider_payload(
    payload: dict[str, Any], request: FinancialRequest
) -> tuple[list[Period], list[FactCandidate]]:
    provider = str(payload.get("provider") or "unknown")
    source_layer = "regulatory_filing" if provider in OFFICIAL_PROVIDERS else "provider_api"
    periods: dict[str, Period] = {}
    candidates: list[FactCandidate] = []
    for section in ("income_statement", "balance_sheet", "cash_flow"):
        rows = payload.get(section) or []
        if not isinstance(rows, list):
            continue
        for row in rows:
            if not isinstance(row, dict):
                continue
            metric = _metric_name(row)
            if not metric:
                continue
            basis_by_period = row.get("period_basis_by_period") or {}
            for label, value in (row.get("values") or {}).items():
                if value is None:
                    continue
                period = _period(label, basis_by_period.get(label))
                periods[period.period_id] = period
                candidates.append(
                    FactCandidate(
                        metric=f"{section}.{metric}",
                        period_id=period.period_id,
                        value=value,
                        unit=row.get("unit"),
                        currency=(payload.get("company") or {}).get("currency"),
                        dimensions={},
                        source_id=f"{provider}:{request.market}:{request.ticker}",
                        source_layer=source_layer,
                        status="disclosed" if source_layer == "regulatory_filing" else "provider-normalized-review",
                        confidence=1.0 if source_layer == "regulatory_filing" else 0.7,
                        source_detail=row.get("source_detail"),
                    )
                )
    return sorted(periods.values(), key=lambda item: item.period_end), candidates


class FinancialDataPipeline:
    def __init__(self, company_root: Path, provider: Provider):
        self.company_root = Path(company_root).resolve()
        self.provider = provider

    def fetch(self, request: FinancialRequest) -> FinancialResult:
        if request.profile not in {"lite", "full"}:
            raise ValueError("profile must be lite or full")
        provider_request = {
            "ticker": request.ticker,
            "identifier": request.ticker,
            "market": request.market,
            "profile": request.profile,
            "from": request.from_value,
            "to": request.to_value,
            "periods": "latest" if request.profile == "lite" and not request.from_value else "all",
            "items": [
                "identity",
                "income_statement",
                "balance_sheet",
                "cash_flow",
                "revenue_split",
            ],
        }
        payload = self.provider.fetch(provider_request)
        periods, candidates = normalize_provider_payload(payload, request)
        selected = resolve_period_ids(
            periods,
            request.profile,
            request.from_value,
            request.to_value,
            complete_years=request.complete_years,
        )
        selected_set = set(selected)
        selected_periods = [period for period in periods if period.period_id in selected_set]
        selected_candidates = [
            candidate for candidate in candidates if candidate.period_id in selected_set
        ]

        run_id = _run_id()
        provider_name = str(payload.get("provider") or getattr(self.provider, "name", "unknown"))
        raw_pack = self.company_root / "_raw" / "datasets" / "financial-data" / provider_name / run_id
        cache_pack = self.company_root / "_cache" / "datasets" / "financial-data" / provider_name / run_id
        _write_json(raw_pack / "provider-payload.json", payload)
        _write_json(cache_pack / "normalized-candidates.json", [asdict(item) for item in selected_candidates])
        _write_json(
            cache_pack / "run-manifest.json",
            {
                "schema_version": 1,
                "run_id": run_id,
                "provider": provider_name,
                "profile": request.profile,
                "requested_range": {"from": request.from_value, "to": request.to_value},
                "deprecated_complete_years": request.complete_years,
                "selected_periods": selected,
                "evidence_level": "full" if request.profile == "full" else "light",
                "status": payload.get("status", "unknown"),
                "canonical_status": "ok" if selected_candidates else "no-canonical-facts",
                "reason": "" if selected_candidates else "provider returned no mappable canonical facts for the requested range",
            },
        )

        internal = self.company_root / "_cache" / "financial-data" / "internal"
        if not selected_candidates:
            return FinancialResult(
                status="no-canonical-facts",
                facts_store=str(internal / "facts-store.json"),
                actuals_view=str(internal / "actuals-resolved.json"),
                raw_pack=str(raw_pack),
                cache_pack=str(cache_pack),
                selected_periods=tuple(selected),
                reason="provider returned no mappable canonical facts for the requested range",
            )
        entity = {"ticker": request.ticker, "market": request.market, **(payload.get("company") or {})}
        repo = FactsRepository(internal, entity=entity)
        for period in selected_periods:
            repo.upsert_period(period)
        repo.merge(selected_candidates)
        if isinstance(payload.get("market_data"), dict) and payload["market_data"].get("as_of"):
            repo.append_snapshot("market", payload["market_data"])
        if isinstance(payload.get("consensus"), dict) and payload["consensus"].get("as_of"):
            repo.append_snapshot("consensus", payload["consensus"])
        repo.render_actuals()
        return FinancialResult(
            status=str(payload.get("status", "unknown")),
            facts_store=str(internal / "facts-store.json"),
            actuals_view=str(internal / "actuals-resolved.json"),
            raw_pack=str(raw_pack),
            cache_pack=str(cache_pack),
            selected_periods=tuple(selected),
        )
