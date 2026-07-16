"""AKShare / Eastmoney provider for China and Hong Kong financial-data routes.

Deterministic extraction: identity, income_statement, balance_sheet,
cash_flow, and CN revenue_split when structured data is available.
All output is provider-normalized-review (third-party data, not
company-original disclosure).
"""

from __future__ import annotations

import importlib.util
import math
import re
from typing import Any


PROVIDER = "akshare"
EXTRACTABLE = ["identity", "income_statement", "balance_sheet", "cash_flow", "revenue_split"]

CN_METADATA_COLUMNS = {
    "SECUCODE",
    "SECURITY_CODE",
    "SECURITY_NAME_ABBR",
    "ORG_CODE",
    "ORG_TYPE",
    "REPORT_DATE",
    "REPORT_TYPE",
    "REPORT_DATE_NAME",
    "SECURITY_TYPE_CODE",
    "NOTICE_DATE",
    "UPDATE_DATE",
    "CURRENCY",
    "OPINION_TYPE",
}

HK_METADATA_COLUMNS = {
    "SECUCODE",
    "SECURITY_CODE",
    "SECURITY_NAME_ABBR",
    "ORG_CODE",
    "REPORT_DATE",
    "DATE_TYPE_CODE",
    "FISCAL_YEAR",
    "START_DATE",
    "STD_ITEM_CODE",
    "STD_REPORT_DATE",
}


def dependency_available() -> bool:
    return importlib.util.find_spec("akshare") is not None


def fetch(request: dict[str, Any]) -> dict[str, Any]:
    if not dependency_available():
        return {"status": "dependency-gap", "provider": PROVIDER, "error": "Missing akshare. Run: pip install --user akshare"}

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

    if "identity" in items:
        try:
            result["company"] = _get_company(normalized_identifier, identifier, market)
            result["items_extracted"].append("identity")
        except Exception as e:
            result["errors"].append(f"identity: {e}")

    for item, getter in (
        ("income_statement", _get_income),
        ("balance_sheet", _get_balance),
        ("cash_flow", _get_cashflow),
    ):
        if item in items:
            try:
                df = getter(normalized_identifier, market, ak)
                rows = _df_to_rows(df)
                if rows:
                    result[item] = rows
                    result["items_extracted"].append(item)
            except Exception as e:
                result["errors"].append(f"{item}: {e}")

    if "revenue_split" in items:
        try:
            rows = _get_revenue_split(normalized_identifier, market, ak)
            if rows:
                result["revenue_split"] = rows
                result["items_extracted"].append("revenue_split")
            elif market == "hk":
                result.setdefault("data_gaps", []).append("revenue_split: no stable free structured HK revenue split route")
        except Exception as e:
            result["errors"].append(f"revenue_split: {e}")

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
    if market == "hk":
        return _get_hk_statement(identifier, "income_statement")
    raise ValueError(f"Unsupported AKShare market: {market}")


def _get_balance(identifier: str, market: str, ak) -> Any:
    if market == "cn":
        return ak.stock_balance_sheet_by_report_em(symbol=_format_cn(identifier))
    if market == "hk":
        return _get_hk_statement(identifier, "balance_sheet")
    raise ValueError(f"Unsupported AKShare market: {market}")


def _get_cashflow(identifier: str, market: str, ak) -> Any:
    if market == "cn":
        return ak.stock_cash_flow_sheet_by_report_em(symbol=_format_cn(identifier))
    if market == "hk":
        return _get_hk_statement(identifier, "cash_flow")
    raise ValueError(f"Unsupported AKShare market: {market}")


def _get_revenue_split(identifier: str, market: str, ak) -> list[dict[str, Any]]:
    if market == "cn":
        df = ak.stock_zygc_em(symbol=_format_cn(identifier).upper())
        return _cn_revenue_split_to_rows(df)
    return []


def _format_cn(identifier: str) -> str:
    """Normalize CN ticker to Eastmoney format: sh600xxx / sz000xxx."""
    clean = identifier.lower().replace(".ss", "").replace(".sh", "").replace(".sz", "")
    if clean.startswith(("sh", "sz")):
        return clean
    if clean.startswith("6") or clean.startswith("5"):
        return "sh" + clean
    return "sz" + clean


def _df_to_rows(df) -> list[dict[str, Any]]:
    """Convert provider DataFrame to list of {label, values} rows.

    Current CN Eastmoney statements are wide: one row per reporting period
    and one column per financial item. HKF10 direct statements are long:
    one row per financial item and period with STD_ITEM_NAME / AMOUNT.
    """
    if df is None or not hasattr(df, "to_dict") or getattr(df, "empty", False):
        return []

    columns = [str(c) for c in df.columns]
    if {"STD_ITEM_NAME", "AMOUNT", "REPORT_DATE"}.issubset(set(columns)):
        return _long_amount_rows(df)

    if "REPORT_DATE" in columns or "REPORT_DATE_NAME" in columns:
        return _wide_report_rows(df, CN_METADATA_COLUMNS)

    return _indicator_rows(df)


def _wide_report_rows(df, metadata_columns: set[str]) -> list[dict[str, Any]]:
    records = df.to_dict(orient="records")
    rows = []
    for field in [str(c) for c in df.columns if str(c) not in metadata_columns]:
        values = {}
        for rec in records:
            period = _period_label(rec)
            value = _clean_value(rec.get(field))
            if period and value is not None:
                values[period] = value
        if values:
            rows.append({"label": field, "concept": field, "values": values})
    return rows


def _long_amount_rows(df) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for rec in df.to_dict(orient="records"):
        label = str(rec.get("STD_ITEM_NAME") or "").strip()
        period = _period_label(rec)
        value = _clean_value(rec.get("AMOUNT"))
        if not label or not period or value is None:
            continue
        item = grouped.setdefault(label, {
            "label": label,
            "concept": str(rec.get("STD_ITEM_CODE") or ""),
            "values": {},
            "period_basis_by_period": {},
        })
        item["values"][period] = value
        item["period_basis_by_period"][period] = _period_basis(period)
    return [row for row in grouped.values() if row.get("values")]


def _indicator_rows(df) -> list[dict[str, Any]]:
    columns = list(df.columns)
    if len(columns) < 2:
        return []
    label_col = columns[0]
    rows = []
    for _, rec in df.iterrows():
        label = str(rec.get(label_col) or "").strip()
        if not label:
            continue
        values = {
            str(col): value
            for col in columns[1:]
            for value in [_clean_value(rec.get(col))]
            if value is not None
        }
        if values:
            rows.append({"label": label, "values": values})
    return rows


def _cn_revenue_split_to_rows(df) -> list[dict[str, Any]]:
    if df is None or not hasattr(df, "to_dict") or getattr(df, "empty", False):
        return []

    rows_by_key: dict[tuple[str, str], dict[str, Any]] = {}
    for rec in df.to_dict(orient="records"):
        period = _clean_period(rec.get("报告日期"))
        split_type = str(rec.get("分类类型") or "").strip()
        label = str(rec.get("主营构成") or "").strip()
        revenue = _clean_value(rec.get("主营收入"))
        if not period or not split_type or not label or revenue is None:
            continue
        item = rows_by_key.setdefault((split_type, label), {
            "label": label,
            "split_type": split_type,
            "source_type": "provider-structured",
            "provider": PROVIDER,
            "values": {},
            "metrics": {},
        })
        item["values"][period] = revenue
        item["metrics"][period] = {
            "revenue": revenue,
            "revenue_share": _clean_value(rec.get("收入比例")),
            "cost": _clean_value(rec.get("主营成本")),
            "cost_share": _clean_value(rec.get("成本比例")),
            "gross_profit": _clean_value(rec.get("主营利润")),
            "gross_profit_share": _clean_value(rec.get("利润比例")),
            "gross_margin": _clean_value(rec.get("毛利率")),
        }
    return [row for row in rows_by_key.values() if row.get("values")]


def _get_hk_statement(identifier: str, statement: str):
    import pandas as pd
    import requests

    report_map = {
        "income_statement": (
            "RPT_HKF10_FN_INCOME_PC",
            "SECUCODE,SECURITY_CODE,SECURITY_NAME_ABBR,ORG_CODE,REPORT_DATE,DATE_TYPE_CODE,"
            "FISCAL_YEAR,START_DATE,STD_ITEM_CODE,STD_ITEM_NAME,AMOUNT",
        ),
        "balance_sheet": (
            "RPT_HKF10_FN_BALANCE_PC",
            "SECUCODE,SECURITY_CODE,SECURITY_NAME_ABBR,ORG_CODE,REPORT_DATE,DATE_TYPE_CODE,"
            "FISCAL_YEAR,STD_ITEM_CODE,STD_ITEM_NAME,AMOUNT,STD_REPORT_DATE",
        ),
        "cash_flow": (
            "RPT_HKF10_FN_CASHFLOW_PC",
            "SECUCODE,SECURITY_CODE,SECURITY_NAME_ABBR,ORG_CODE,REPORT_DATE,DATE_TYPE_CODE,"
            "FISCAL_YEAR,START_DATE,STD_ITEM_CODE,STD_ITEM_NAME,AMOUNT",
        ),
    }
    report_name, columns = report_map[statement]
    dates = _hk_report_dates(identifier)
    if not dates:
        return pd.DataFrame()

    url = "https://datacenter.eastmoney.com/securities/api/data/v1/get"
    quoted_dates = "'" + "','".join(dates) + "'"
    params = {
        "reportName": report_name,
        "columns": columns,
        "quoteColumns": "",
        "filter": f'(SECUCODE="{identifier}.HK")(REPORT_DATE in ({quoted_dates}))',
        "pageNumber": "1",
        "pageSize": "",
        "sortTypes": "-1,1",
        "sortColumns": "REPORT_DATE,STD_ITEM_CODE",
        "source": "F10",
        "client": "PC",
        "v": "01975982096513973",
    }
    data_json = requests.get(url, params=params, timeout=20).json()
    return pd.DataFrame((data_json.get("result") or {}).get("data") or [])


def _hk_report_dates(identifier: str) -> list[str]:
    import requests

    url = "https://datacenter.eastmoney.com/securities/api/data/v1/get"
    params = {
        "reportName": "RPT_CUSTOM_HKSK_APPFN_CASHFLOW_SUMMARY",
        "columns": "SECUCODE,SECURITY_CODE,SECURITY_NAME_ABBR,START_DATE,REPORT_DATE,FISCAL_YEAR,"
        "CURRENCY,ACCOUNT_STANDARD,REPORT_TYPE",
        "quoteColumns": "",
        "filter": f'(SECUCODE="{identifier}.HK")',
        "source": "F10",
        "client": "PC",
        "v": "02092616586970355",
    }
    data_json = requests.get(url, params=params, timeout=20).json()
    data = (data_json.get("result") or {}).get("data") or []
    report_list = data[0].get("REPORT_LIST", []) if data else []
    dates = []
    for rec in report_list:
        period = _clean_period(rec.get("REPORT_DATE"))
        if period:
            dates.append(period)
    return sorted(set(dates), reverse=True)[:8]


def _period_label(rec: dict[str, Any]) -> str:
    return (
        str(rec.get("REPORT_DATE_NAME") or "").strip()
        or _clean_period(rec.get("REPORT_DATE"))
        or _clean_period(rec.get("STD_REPORT_DATE"))
    )


def _period_basis(period: str) -> str:
    text = str(period or "")
    if re.search(r"-(03-31|09-30)$", text):
        return "quarter"
    if re.search(r"-(06-30)$", text):
        return "half_year"
    if re.search(r"-(12-31)$", text):
        return "annual"
    if re.search(r"\b[Qq][1-4]\b", text):
        return "quarter"
    if re.search(r"\b[Hh][12]\b|半年|半期|中报", text):
        return "half_year"
    if re.search(r"年报|年度|annual|FY", text, flags=re.IGNORECASE):
        return "annual"
    return "unknown"


def _clean_period(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if not text or text.lower() in {"nan", "none", "nat", "--"}:
        return ""
    if " " in text and len(text) >= 10:
        return text[:10]
    return text


def _clean_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    text = str(value).strip()
    if text.lower() in {"", "nan", "none", "nat", "--"}:
        return None
    return value
