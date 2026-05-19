"""FinMind provider for Taiwan financial-data routes.

Deterministic extraction: identity and three statements when the public
FinMind datasets are available. Revenue split is not treated as a stable
structured route in V1 and is left to driver-map LLM extraction from filings.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import re
from typing import Any
from urllib.parse import urlencode
from urllib.request import urlopen


PROVIDER = "finmind"
EXTRACTABLE = ["identity", "income_statement", "balance_sheet", "cash_flow", "revenue_split"]
BASE_URL = "https://api.finmindtrade.com/api/v4/data"


def dependency_available() -> bool:
    return True


def fetch(request: dict[str, Any]) -> dict[str, Any]:
    identifier = str(request["identifier"]).strip()
    items = request.get("items", EXTRACTABLE)
    items = [i for i in items if i in EXTRACTABLE]
    start_date = _start_date_from_periods(request.get("periods", "latest"))

    result: dict[str, Any] = {
        "provider": PROVIDER,
        "market": "tw",
        "identifier": identifier,
        "items_requested": items,
        "items_extracted": [],
        "errors": [],
    }

    if "identity" in items:
        result["company"] = {
            "ticker": identifier,
            "market": "tw",
            "display_name": "unknown",
            "name_status": "unavailable",
            "provider": PROVIDER,
        }
        result["items_extracted"].append("identity")

    for item, dataset in (
        ("income_statement", "TaiwanStockFinancialStatements"),
        ("balance_sheet", "TaiwanStockBalanceSheet"),
        ("cash_flow", "TaiwanStockCashFlowsStatement"),
    ):
        if item not in items:
            continue
        try:
            rows = _dataset_to_rows(_fetch_dataset(dataset, identifier, start_date))
            if rows:
                result[item] = rows
                result["items_extracted"].append(item)
        except Exception as e:
            result["errors"].append(f"{item}: {e}")

    if "revenue_split" in items:
        result.setdefault("data_gaps", []).append("revenue_split: no stable free structured TW revenue split route")

    result["status"] = "success" if result["items_extracted"] else "provider-gap"
    return result


def _fetch_dataset(dataset: str, identifier: str, start_date: str) -> list[dict[str, Any]]:
    params = {
        "dataset": dataset,
        "data_id": identifier,
        "start_date": start_date,
    }
    token = os.getenv("FINMIND_TOKEN")
    if token:
        params["token"] = token
    with urlopen(BASE_URL + "?" + urlencode(params), timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not payload.get("status") == 200:
        raise RuntimeError(payload.get("msg") or f"FinMind status {payload.get('status')}")
    return payload.get("data") or []


def _dataset_to_rows(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for rec in records:
        label = str(rec.get("type") or rec.get("origin_name") or "").strip()
        period = str(rec.get("date") or "").strip()
        value = _clean_value(rec.get("value"))
        if not label or not period or value is None:
            continue
        item = grouped.setdefault(label, {
            "label": label,
            "concept": str(rec.get("type") or ""),
            "values": {},
        })
        item["values"][period] = value
    return [row for row in grouped.values() if row.get("values")]


def _start_date_from_periods(periods: str | None) -> str:
    text = str(periods or "")
    years = [int(y) for y in __import__("re").findall(r"\b(20\d{2}|19\d{2})\b", text)]
    if years:
        return f"{min(years)}-01-01"
    if _is_quarterly_request(text):
        today = dt.date.today()
        return f"{today.year - 2}-01-01"
    return "2020-01-01"


def _is_quarterly_request(periods: str | None) -> bool:
    token = re.sub(r"[^a-z0-9]+", "", str(periods or "").strip().lower())
    return token in {"latest4q", "last4q", "latest4quarters", "latestfourquarters", "quarterly"}


def _clean_value(value: Any) -> Any:
    if value is None:
        return None
    text = str(value).strip()
    if text.lower() in {"", "nan", "none", "nat", "--"}:
        return None
    return value
