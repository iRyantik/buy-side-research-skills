"""EDINET provider for Japan financial-data routes.

Deterministic extraction: identity, income_statement, balance_sheet, cash_flow, latest_full_filing.
"""

from __future__ import annotations

import importlib.util
import os
from typing import Any


PROVIDER = "edinet-tools"
EXTRACTABLE = ["identity", "income_statement", "balance_sheet", "cash_flow", "latest_full_filing"]


def dependency_available() -> bool:
    return importlib.util.find_spec("edinet_tools") is not None


def fetch(request: dict[str, Any]) -> dict[str, Any]:
    if not dependency_available():
        return {"status": "dependency-gap", "provider": PROVIDER, "error": "Missing edinet-tools. Run: pip install edinet-tools"}

    identifier = request["identifier"]
    items = request.get("items", EXTRACTABLE)
    items = [i for i in items if i in EXTRACTABLE]

    result: dict[str, Any] = {
        "provider": PROVIDER,
        "market": "jp",
        "identifier": identifier,
        "items_requested": items,
        "items_extracted": [],
        "errors": [],
    }

    import edinet_tools as et

    api_key = os.getenv("EDINET_API_KEY")
    if api_key:
        et.configure(api_key=api_key)

    # --- identity ---
    entity = None
    if "identity" in items or _needs_data(items):
        try:
            entity = et.entity_by_ticker(identifier)
            result["company"] = {
                "name": getattr(entity, "name", str(entity)),
                "edinet_code": getattr(entity, "edinet_code", None),
                "ticker": identifier,
                "type": str(getattr(entity, "type", "")),
            }
            result["items_extracted"].append("identity")
        except Exception as e:
            result["errors"].append(f"identity: {e}")
            return result

    parsed_report = None
    needs_report = bool({"income_statement", "balance_sheet", "cash_flow", "latest_full_filing"} & set(items))
    if entity and hasattr(entity, "edinet_code") and needs_report:
        try:
            parsed_report = et.fetch_and_parse(entity.edinet_code, "SecuritiesReport")
        except Exception as e:
            result["errors"].append(f"securities_report: {e}")

    # --- statements ---
    if parsed_report is not None:
        for item_key in ("income_statement", "balance_sheet", "cash_flow"):
            if item_key in items:
                try:
                    stmt_data = _extract_from_parsed(parsed_report, item_key)
                    if stmt_data:
                        result[item_key] = stmt_data
                        result["items_extracted"].append(item_key)
                    else:
                        result["errors"].append(f"{item_key}: parsed report returned no rows")
                except Exception as e:
                    result["errors"].append(f"{item_key}: {e}")

    # --- latest_full_filing ---
    if "latest_full_filing" in items and parsed_report is not None and entity and hasattr(entity, "edinet_code"):
        filing = _get_filing_text(entity, parsed_report)
        result["filing"] = filing
        if filing.get("status") == "fetched" and filing.get("markdown"):
            result["items_extracted"].append("latest_full_filing")
        else:
            result["errors"].append(f"latest_full_filing: {filing.get('error', 'markdown unavailable')}")

    if result["items_extracted"]:
        result["status"] = "partial" if result["errors"] else "success"
    else:
        result["status"] = "provider-gap"
    return result


def _needs_data(items: list[str]) -> bool:
    return bool({"income_statement", "balance_sheet", "cash_flow", "latest_full_filing"} & set(items))


def _extract_from_parsed(parsed: Any, item_key: str) -> list[dict[str, Any]]:
    """Extract statement data from a ParsedReport."""
    # edinet-tools ParsedReport has structured sections
    result = []
    try:
        if hasattr(parsed, "sections"):
            for section in parsed.sections:
                section_data = {"label": str(getattr(section, "title", section)), "values": {}}
                if hasattr(section, "items"):
                    for item in section.items:
                        label = getattr(item, "label", str(item))
                        value = getattr(item, "value", getattr(item, "amount", None))
                        section_data["values"][label] = value
                result.append(section_data)
    except Exception:
        pass

    if not result:
        result = [{"label": "raw", "values": {"data": str(parsed)[:2000]}}]

    return result


def _get_filing_text(entity: Any, parsed: Any) -> dict[str, Any]:
    """Get latest securities report document text."""
    try:
        edinet_code = entity.edinet_code
        text = str(parsed)
        if not text:
            return {"status": "error", "error": "empty securities report text"}

        return {
            "edinet_code": edinet_code,
            "doc_type": "SecuritiesReport",
            "text_length": len(text),
            "markdown": text,
            "status": "fetched",
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}
