"""DART provider for Korea financial-data routes.

Deterministic extraction: identity, income_statement, balance_sheet, cash_flow.
"""
from __future__ import annotations

import datetime as dt
import importlib.util
import io
import os
import re
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from typing import Any


PROVIDER = "dart-fss"
EXTRACTABLE = ["identity", "income_statement", "balance_sheet", "cash_flow"]


def dependency_available() -> bool:
    return importlib.util.find_spec("dart_fss") is not None


def fetch(request: dict[str, Any]) -> dict[str, Any]:
    if not dependency_available():
        return {"status": "dependency-gap", "provider": PROVIDER, "error": "Missing dart-fss. Run: pip install dart-fss"}

    api_key = os.getenv("DART_API_KEY")
    if not api_key:
        return {"status": "credential-gap", "provider": PROVIDER, "error": "Missing DART_API_KEY. Register at https://opendart.fss.or.kr/"}

    identifier = request["identifier"]
    items = request.get("items", EXTRACTABLE)
    items = [i for i in items if i in EXTRACTABLE]

    result: dict[str, Any] = {
        "provider": PROVIDER,
        "market": "kr",
        "identifier": identifier,
        "items_requested": items,
        "items_extracted": [],
        "errors": [],
    }

    import dart_fss as dart
    dart.set_api_key(api_key=api_key)

    # --- identity ---
    corp = None
    if "identity" in items or _needs_statements(items):
        try:
            corp = _get_corp(identifier, dart)
            result["company"] = {
                "name": corp.corp_name if hasattr(corp, "corp_name") else str(corp),
                "stock_code": getattr(corp, "stock_code", identifier),
                "corp_code": getattr(corp, "corp_code", None),
            }
            result["items_extracted"].append("identity")
        except Exception as e:
            result["errors"].append(f"identity: {e}")
            return result

    # --- statements ---
    fs = None
    if corp and _needs_statements(items):
        start_date, end_date = _date_window_from_periods(str(request.get("periods", "latest")))
        result["statement_window"] = {"start_date": start_date, "end_date": end_date}
        try:
            with _suppress_progress_output():
                fs = dart.fs.extract(corp, start_date, end_date, separate=True)
        except Exception as e:
            result["errors"].append(f"statement_extract: {e}")

    if fs is not None:
        for item_key, stmt_type in [("income_statement", "IS"), ("balance_sheet", "BS"), ("cash_flow", "CF")]:
            if item_key in items:
                try:
                    statements = _extract_statement(fs, stmt_type)
                    if statements:
                        result[item_key] = statements
                        result["items_extracted"].append(item_key)
                    else:
                        result["errors"].append(f"{item_key}: annual report statement unavailable")
                except Exception as e:
                    result["errors"].append(f"{item_key}: {e}")

    if result["items_extracted"]:
        non_identity = set(result["items_extracted"]) - {"identity"}
        result["status"] = "partial" if result["errors"] or (_needs_statements(items) and not non_identity) else "success"
    else:
        result["status"] = "provider-gap"
    return result


def _get_corp(identifier: str, dart) -> Any:
    with _suppress_progress_output():
        corp_list = dart.get_corp_list()
    corp = corp_list.find_by_stock_code(identifier)
    if corp is None:
        corp = corp_list.find_by_corp_code(identifier)
    if corp is None:
        raise ValueError(f"DART: company not found for {identifier}")
    return corp


def _needs_statements(items: list[str]) -> bool:
    return bool({"income_statement", "balance_sheet", "cash_flow"} & set(items))


def _date_window_from_periods(periods: str) -> tuple[str, str]:
    """Map request periods to a deterministic DART extraction window."""
    years = [int(year) for year in re.findall(r"(20\d{2})", periods)]
    if len(years) >= 2:
        start_year, end_year = min(years), max(years)
    elif len(years) == 1:
        start_year = end_year = years[0]
    else:
        today = dt.date.today()
        start_year = today.year - 3
        end_year = today.year
    return f"{start_year:04d}0101", f"{end_year:04d}1231"


@contextmanager
def _suppress_progress_output():
    """Avoid dart-fss spinner output corrupting Windows GBK consoles."""
    sink = io.StringIO()
    with redirect_stdout(sink), redirect_stderr(sink):
        yield


def _extract_statement(fs: Any, stmt_type: str) -> list[dict[str, Any]]:
    """Extract one statement type from dart_fss extraction result."""
    # fs is an ExtractionResult with attributes like .income_statement, .balance_sheet, etc
    attr_map = {"IS": "income_statement", "BS": "balance_sheet", "CF": "cash_flow"}
    attr = attr_map.get(stmt_type)
    if not attr or not hasattr(fs, attr):
        return []

    stmt = getattr(fs, attr)
    if hasattr(stmt, "to_dict"):
        d = stmt.to_dict(orient="records")
        return _normalize_records(d)
    return []


def _normalize_records(records: list[dict]) -> list[dict[str, Any]]:
    if not records:
        return records
    rows = []
    for field in records[0].keys():
        values = {}
        for idx, rec in enumerate(records):
            values[f"period_{idx}"] = rec.get(field)
        rows.append({"label": str(field), "values": values})
    return rows
