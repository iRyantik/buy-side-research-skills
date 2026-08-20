"""FMP provider for multi-market financial-data routes.

Uses FMP stable API (https://financialmodelingprep.com/stable/...).
Stable endpoints verified 2026-08-20: quote / profile / income-statement /
balance-sheet-statement / cash-flow-statement / ratios / analyst-estimates
(needs period=annual) / earnings / news/stock (US-only coverage).

Ticker mapping (workspace suffix → FMP suffix), verified by live quote:
  .US → bare, .SH → .SS, .TT → .TW, .LN → .L; others unchanged
  (.SZ/.HK/.TW/.T/.KS/.DE/.PA/.MI/.MC/.ST/.OL/.SI/.KL/.NS/.AX).

Known gaps (not blocked): historical-price-eod returns empty for this key —
1m/YTD/1y moves fall back to yfinance in lite closeout.
"""

from __future__ import annotations

import json
import os
from typing import Any
from urllib.parse import urlencode
from urllib.request import urlopen


PROVIDER = "fmp"
BASE_URL = "https://financialmodelingprep.com/stable"

# workspace ticker suffix → FMP suffix
_FMP_SUFFIX = {
    ".US": "",       # US → bare ticker
    ".SH": ".SS",    # Shanghai
    ".SZ": ".SZ",    # Shenzhen
    ".TT": ".TW",    # Taiwan
    ".LN": ".L",     # London
    ".HK": ".HK", ".TW": ".TW", ".T": ".T", ".KS": ".KS",
    ".DE": ".DE", ".PA": ".PA", ".MI": ".MI", ".MC": ".MC",
    ".ST": ".ST", ".OL": ".OL", ".SI": ".SI", ".KL": ".KL",
    ".NS": ".NS", ".AX": ".AX",
}

# FMP statement field → canonical concept key (snake_case, matches policy line items)
_IS_MAP = {
    "revenue": "revenue",
    "costOfRevenue": "cost_of_sales",
    "grossProfit": "gross_profit",
    "operatingExpenses": "operating_expense",
    "operatingIncome": "operating_income",
    "interestExpense": "interest_expense",
    "incomeTaxExpense": "income_tax",
    "netIncome": "net_income",
    "netIncomeLoss": "net_income",
    "ebitda": "ebitda",
    "eps": "eps",
}
_BS_MAP = {
    "cashAndCashEquivalents": "cash",
    "totalAssets": "total_assets",
    "totalCurrentAssets": "total_current_assets",
    "totalLiabilities": "total_liabilities",
    "totalCurrentLiabilities": "total_current_liabilities",
    "longTermDebt": "long_term_debt",
    "totalDebt": "total_debt",
    "stockholdersEquity": "stockholders_equity",
    "totalStockholdersEquity": "stockholders_equity",
    "retainedEarnings": "retained_earnings",
}
_CF_MAP = {
    "operatingCashFlow": "operating_cash_flow",
    "capitalExpenditure": "capex",
    "freeCashFlow": "free_cash_flow",
    "financingCashFlow": "financing_cash_flow",
    "investingCashFlow": "investing_cash_flow",
    "netIncome": "net_income",
}


def to_fmp_ticker(ws_ticker: str) -> str:
    """Workspace ticker (e.g. 603067.SH, DPC.US) → FMP stable ticker."""
    for suffix, fmp in _FMP_SUFFIX.items():
        if ws_ticker.endswith(suffix):
            return ws_ticker[: -len(suffix)] + fmp
    return ws_ticker


def dependency_available() -> bool:
    return bool(os.getenv("FMP_API_KEY"))


def _api(path: str, params: dict[str, Any]) -> Any:
    key = os.getenv("FMP_API_KEY")
    if not key:
        raise RuntimeError("Missing FMP_API_KEY — set it in workspace .env")
    params["apikey"] = key
    url = f"{BASE_URL}{path}?{urlencode(params)}"
    with urlopen(url, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _period_basis(period: str) -> str:
    p = (period or "").upper()
    if p in {"Q1", "Q2", "Q3", "Q4"}:
        return "quarter"
    if p in {"H1", "H2"}:
        return "half_year"
    return "annual"


def _segment_rows(records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """FMP segmentation records → {segment: {date: {basis: value}}}.

    Record shape: {date, fiscalYear, period, data: {segment_name: amount}}.
    """
    out: dict[str, dict[str, Any]] = {}
    for rec in records or []:
        date = str(rec.get("date") or "").strip()
        period = str(rec.get("period") or "FY").strip()
        basis = _period_basis(period)
        data = rec.get("data") or {}
        for seg, value in data.items():
            if value is None:
                continue
            row = out.setdefault(str(seg).strip(), {})
            row.setdefault(date, {})[basis] = value
    return out


def _rows_from_statements(records: list[dict[str, Any]], field_map: dict[str, str]) -> dict[str, dict[str, Any]]:
    """FMP statement rows (one row per period) → {concept: {period: {basis: value}}}.

    Matches the canonical statements format used by actuals-resolved.json.
    """
    out: dict[str, dict[str, Any]] = {}
    for rec in records:
        date = str(rec.get("date") or "").strip()
        period = str(rec.get("period") or "FY").strip()
        basis = _period_basis(period)
        for fmp_field, concept in field_map.items():
            value = rec.get(fmp_field)
            if value is None:
                continue
            row = out.setdefault(concept, {})
            row.setdefault(date, {})[basis] = value
    return out


def fetch(request: dict[str, Any]) -> dict[str, Any]:
    identifier = str(request["identifier"]).strip()
    market = str(request.get("market", "")).lower()
    fmp_ticker = to_fmp_ticker(identifier)
    items = [i for i in request.get("items", []) if i in _EXTRACTABLE]

    result: dict[str, Any] = {
        "provider": PROVIDER,
        "market": market,
        "identifier": identifier,
        "fmp_ticker": fmp_ticker,
        "items_requested": items,
        "items_extracted": [],
        "errors": [],
        "data_gaps": [],
    }

    try:
        if "identity" in items:
            profile = _api("/profile", {"symbol": fmp_ticker})
            if profile:
                p = profile[0]
                result["company"] = {
                    "ticker": identifier,
                    "market": market,
                    "display_name": p.get("companyName") or p.get("companyName", ""),
                    "name_status": "provider",
                    "provider": PROVIDER,
                    "industry": p.get("industry"),
                    "sector": p.get("sector"),
                }
                result["items_extracted"].append("identity")
            else:
                result["errors"].append("identity: FMP profile empty")

        if "market_data" in items:
            quote = _api("/quote", {"symbol": fmp_ticker})
            if quote:
                q = quote[0]
                result["market_data"] = {
                    "price": q.get("price"),
                    "market_cap": q.get("marketCap"),
                    "change_pct": q.get("changePercentage"),
                    "day_low": q.get("dayLow"),
                    "day_high": q.get("dayHigh"),
                    "year_high": q.get("yearHigh"),
                    "year_low": q.get("yearLow"),
                    "volume": q.get("volume"),
                    "price_avg_50": q.get("priceAvg50"),
                    "price_avg_200": q.get("priceAvg200"),
                    "eps_ttm": q.get("eps"),
                    "pe_ttm": q.get("pe"),
                    "as_of": q.get("date") or "live",
                }
                result["items_extracted"].append("market_data")

        for item, path, field_map in (
            ("income_statement", "/income-statement", _IS_MAP),
            ("balance_sheet", "/balance-sheet-statement", _BS_MAP),
            ("cash_flow", "/cash-flow-statement", _CF_MAP),
        ):
            if item not in items:
                continue
            try:
                records = _api(path, {"symbol": fmp_ticker, "period": "annual", "limit": 8})
                rows = _rows_from_statements(records or [], field_map)
                if rows:
                    result[item] = rows
                    result["items_extracted"].append(item)
                else:
                    result["data_gaps"].append(f"{item}: FMP statement empty")
            except Exception as e:
                result["errors"].append(f"{item}: {e}")

        if "estimates" in items:
            try:
                est = _api("/analyst-estimates", {"symbol": fmp_ticker, "period": "annual", "limit": 4})
                if est:
                    result["estimates"] = est
                    result["items_extracted"].append("estimates")
                else:
                    result["data_gaps"].append("estimates: FMP analyst-estimates empty")
            except Exception as e:
                result["errors"].append(f"estimates: {e}")

        if "revenue_split" in items:
            # FMP stable segments 端点（实测 CRS 全通）：产品线 + 地理
            try:
                split: dict[str, Any] = {}
                for key, ep in (("product", "/revenue-product-segmentation"),
                                ("geographic", "/revenue-geographic-segmentation")):
                    recs = _api(ep, {"symbol": fmp_ticker})
                    rows = _segment_rows(recs)
                    if rows:
                        split[key] = rows
                if split:
                    result["revenue_split"] = split
                    result["items_extracted"].append("revenue_split")
                else:
                    result["data_gaps"].append("revenue_split: FMP segmentation empty")
            except Exception as e:
                result["errors"].append(f"revenue_split: {e}")

        if "historical_price" in items:
            # Correct path: /historical-price-eod/light (subpath required).
            # Feeds 1m/YTD/1y moves for the daily brief — no yfinance fallback needed.
            try:
                hist = _api("/historical-price-eod/light", {"symbol": fmp_ticker, "limit": 260})
                if hist:
                    result["historical_price"] = hist
                    result["items_extracted"].append("historical_price")
                else:
                    result["data_gaps"].append("historical_price: FMP history empty")
            except Exception as e:
                result["errors"].append(f"historical_price: {e}")

    except Exception as exc:
        result["errors"].append(str(exc))

    result["status"] = "success" if result["items_extracted"] else "provider-gap"
    return result


_EXTRACTABLE = [
    "identity", "market_data", "income_statement", "balance_sheet",
    "cash_flow", "estimates", "revenue_split", "historical_price",
]
