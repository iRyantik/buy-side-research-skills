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
    ".CN": ".SZ",    # A-share (ChiNext/创业板)
    ".TT": ".TW",    # Taiwan
    ".LN": ".L",     # London
    ".JP": ".T",     # Japan
    ".KQ": ".KQ",    # Korea KOSDAQ
    ".NA": ".AS",    # Amsterdam
    ".SS": ".ST",    # Stockholm (Mycronic)
    ".FR": ".PA",    # Paris
    ".CA": ".TO",    # Toronto
    ".MY": ".KL",    # Malaysia
    ".HK": ".HK", ".TW": ".TW", ".T": ".T", ".KS": ".KS",
    ".DE": ".DE", ".PA": ".PA", ".MI": ".MI", ".MC": ".MC",
    ".ST": ".ST", ".OL": ".OL", ".SI": ".SI", ".KL": ".KL",
    ".NS": ".NS", ".AX": ".AX", ".HE": ".HE",
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
                md = {
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
                    "eps_ttm": None,
                    "pe_ttm": None,
                    "as_of": q.get("date") or "live",
                }
                # TTM EPS + PE：quarter IS 最近 4 季（quote 无 pe/eps 字段）
                try:
                    qis = _api("/income-statement", {"symbol": fmp_ticker, "period": "quarter", "limit": 5})
                    eps_vals = [x.get("eps") for x in qis if x.get("eps")]
                    if len(eps_vals) >= 4 and md.get("price"):
                        ttm_eps = sum(float(v) for v in eps_vals[:4])
                        md["eps_ttm"] = round(ttm_eps, 2)
                        md["pe_ttm"] = round(float(md["price"]) / ttm_eps, 1)
                except Exception:
                    pass
                result["market_data"] = md
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

        if "price_change" in items:
            # 涨跌一站式：1D/5D/1M/3M/6M/ytd/1Y/3Y/5Y —— 日报 Movers/估值表涨跌列
            try:
                pc = _api("/stock-price-change", {"symbol": fmp_ticker})
                if pc:
                    result["price_change"] = pc[0]
                    result["items_extracted"].append("price_change")
                else:
                    result["data_gaps"].append("price_change: FMP stock-price-change empty")
            except Exception as e:
                result["errors"].append(f"price_change: {e}")

        if "key_metrics" in items:
            # TTM 关键指标（EV/EBITDA、EV/FCF 等）——估值表
            try:
                km = _api("/key-metrics-ttm", {"symbol": fmp_ticker})
                if km:
                    result["key_metrics"] = km[0]
                    result["items_extracted"].append("key_metrics")
                else:
                    result["data_gaps"].append("key_metrics: FMP key-metrics-ttm empty")
            except Exception as e:
                result["errors"].append(f"key_metrics: {e}")

        if "price_target" in items:
            # 目标价共识（high/low/consensus/median）——consensus-map
            try:
                pt = _api("/price-target-consensus", {"symbol": fmp_ticker})
                if pt:
                    result["price_target"] = pt[0]
                    result["items_extracted"].append("price_target")
                else:
                    result["data_gaps"].append("price_target: FMP price-target-consensus empty")
            except Exception as e:
                result["errors"].append(f"price_target: {e}")

        if "earnings_calendar" in items:
            # 单股下次财报日：/stable/earnings 第一条 epsActual=None 的 date（= 还没公布 = 下次）
            # 全市场批量扫用 /earnings-calendar?from=&to=（日报 Review Queue 用，4000 条封顶）
            try:
                ec = _api("/earnings", {"symbol": fmp_ticker, "limit": 6})
                next_dt = None
                for x in ec or []:
                    if x.get("epsActual") is None and x.get("date"):
                        next_dt = x["date"]
                        break
                if next_dt:
                    result["next_earnings_date"] = next_dt
                    result["items_extracted"].append("earnings_calendar")
                else:
                    result["data_gaps"].append("earnings_calendar: no next earnings date found")
            except Exception as e:
                result["errors"].append(f"earnings_calendar: {e}")

        if "news" in items:
            # 公司新闻（仅美股覆盖；韩/日/中返回空 → Core Watch 走搜索链 fallback）
            try:
                nw = _api("/news/stock", {"symbols": fmp_ticker, "limit": 5})
                if nw:
                    result["news"] = nw
                    result["items_extracted"].append("news")
                else:
                    result["data_gaps"].append("news: FMP news empty (非美股覆盖——搜索链 fallback)")
            except Exception as e:
                result["errors"].append(f"news: {e}")

        if "ratios" in items:
            # 历史估值倍数（5y 中位用）：enterpriseValueMultiple 等
            try:
                rr = _api("/ratios", {"symbol": fmp_ticker, "period": "annual", "limit": 8})
                if rr:
                    result["ratios"] = rr
                    result["items_extracted"].append("ratios")
                else:
                    result["data_gaps"].append("ratios: FMP ratios empty")
            except Exception as e:
                result["errors"].append(f"ratios: {e}")

        if "dividends" in items:
            # 股息历史（capital allocation / 股息能力）
            try:
                dv = _api("/dividends", {"symbol": fmp_ticker, "limit": 8})
                if dv:
                    result["dividends"] = dv
                    result["items_extracted"].append("dividends")
                else:
                    result["data_gaps"].append("dividends: FMP dividends empty")
            except Exception as e:
                result["errors"].append(f"dividends: {e}")

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
    "cash_flow", "estimates", "revenue_split", "historical_price", "price_change",
    "key_metrics", "price_target", "earnings_calendar", "dividends", "news", "ratios",
]
