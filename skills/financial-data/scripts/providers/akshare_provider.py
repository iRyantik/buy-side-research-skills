"""AKShare provider for China and Hong Kong financial-data routes.

Deterministic extraction: identity, income_statement, balance_sheet, cash_flow.
All output is provider-normalized-review (third-party data, not company-original disclosure).
"""

from __future__ import annotations

import importlib.util
from typing import Any


PROVIDER = "akshare"
EXTRACTABLE = ["identity", "income_statement", "balance_sheet", "cash_flow"]


def dependency_available() -> bool:
    return importlib.util.find_spec("akshare") is not None


def fetch(request: dict[str, Any]) -> dict[str, Any]:
    if not dependency_available():
        return {"status": "dependency-gap", "provider": PROVIDER, "error": "Missing akshare. Run: pip install akshare"}

    identifier = request["identifier"]
    market = request.get("market", "cn")
    normalized_identifier = _normalize_identifier(identifier, market)
    items = request.get("items", EXTRACTABLE)
    items = [i for i in items if i in EXTRACTABLE]

    result: dict[str, Any] = {
        "provider": PROVIDER,
        "market": market,
        "identifier": normalized_identifier,
        "input_identifier": identifier,
        "items_requested": items,
        "items_extracted": [],
        "errors": [],
    }

    import akshare as ak

    # --- identity ---
    if "identity" in items:
        try:
            result["company"] = _get_company(normalized_identifier, identifier, market)
            result["items_extracted"].append("identity")
        except Exception as e:
            result["errors"].append(f"identity: {e}")

    # --- income statement ---
    if "income_statement" in items:
        try:
            df = _get_income(normalized_identifier, market, ak)
            result["income_statement"] = _df_to_rows(df)
            result["items_extracted"].append("income_statement")
        except Exception as e:
            result["errors"].append(f"income_statement: {e}")

    # --- balance sheet ---
    if "balance_sheet" in items:
        try:
            df = _get_balance(normalized_identifier, market, ak)
            result["balance_sheet"] = _df_to_rows(df)
            result["items_extracted"].append("balance_sheet")
        except Exception as e:
            result["errors"].append(f"balance_sheet: {e}")

    # --- cash flow ---
    if "cash_flow" in items:
        try:
            df = _get_cashflow(normalized_identifier, market, ak)
            result["cash_flow"] = _df_to_rows(df)
            result["items_extracted"].append("cash_flow")
        except Exception as e:
            result["errors"].append(f"cash_flow: {e}")

    result["status"] = "success" if result["items_extracted"] else "provider-gap"
    return result


def _get_company(identifier: str, input_identifier: str, market: str) -> dict[str, Any]:
    return {
        "ticker": identifier,
        "input_ticker": input_identifier,
        "market": market,
        "display_name": "unknown",
        "name_status": "unavailable",
        "provider": PROVIDER,
    }


def _normalize_identifier(identifier: str, market: str) -> str:
    clean = str(identifier).strip()
    if market == "hk":
        clean = clean.replace(".HK", "").replace(".hk", "")
        if clean.isdigit():
            return clean.zfill(5)
    return clean


def _get_income(identifier: str, market: str, ak) -> Any:
    if market == "cn":
        return ak.stock_profit_sheet_by_report_em(symbol=_format_cn(identifier))
    elif market == "hk":
        return ak.stock_financial_hk_report_em(stock=identifier, symbol="利润表", indicator="年报")
    raise ValueError(f"Unsupported AKShare market: {market}")


def _get_balance(identifier: str, market: str, ak) -> Any:
    if market == "cn":
        return ak.stock_balance_sheet_by_report_em(symbol=_format_cn(identifier))
    elif market == "hk":
        return ak.stock_financial_hk_report_em(stock=identifier, symbol="资产负债表", indicator="年报")
    raise ValueError(f"Unsupported AKShare market: {market}")


def _get_cashflow(identifier: str, market: str, ak) -> Any:
    if market == "cn":
        return ak.stock_cash_flow_sheet_by_report_em(symbol=_format_cn(identifier))
    elif market == "hk":
        return ak.stock_financial_hk_report_em(stock=identifier, symbol="现金流量表", indicator="年报")
    raise ValueError(f"Unsupported AKShare market: {market}")



def _format_cn(identifier: str) -> str:
    """Normalize CN ticker to EastMoney format: sh600xxx / sz000xxx."""
    clean = identifier.lower().replace(".ss", "").replace(".sh", "").replace(".sz", "")
    if clean.startswith(("sh", "sz")):
        return clean
    if clean.startswith("6") or clean.startswith("5"):
        return "sh" + clean
    return "sz" + clean


def _df_to_rows(df) -> list[dict[str, Any]]:
    """Convert DataFrame to list of {field, values} rows."""
    if hasattr(df, "to_dict"):
        records = df.to_dict(orient="records")
        if records:
            # Transpose: each column becomes a field with period values
            row0 = records[0]
            rows = []
            for field in df.columns:
                values = {}
                for idx, rec in enumerate(records):
                    values[f"period_{idx}"] = rec.get(field)
                rows.append({"label": str(field), "values": values})
            return rows
    return []
