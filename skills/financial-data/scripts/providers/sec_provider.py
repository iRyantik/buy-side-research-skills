"""SEC / EdgarTools provider.

Fetches deterministic, source-tracked data: company identity, latest 10-K filing
markdown, and structured IS/BS/CF from XBRL.
"""

from __future__ import annotations

import hashlib
import importlib.util
import os
from typing import Any


PROVIDER = "edgartools"
EXTRACTABLE = ["identity", "filing_index", "latest_full_filing", "income_statement", "balance_sheet", "cash_flow"]


def dependency_available() -> bool:
    return importlib.util.find_spec("edgar") is not None


def fetch(request: dict[str, Any]) -> dict[str, Any]:
    if not dependency_available():
        return _err("dependency-gap", "Missing edgartools. Run: pip install edgartools")
    identity = os.getenv("EDGAR_IDENTITY")
    if not identity:
        return _err("credential-gap", "Missing EDGAR_IDENTITY")

    import edgar
    try:
        from edgar import configure_http
        configure_http(use_system_certs=True)
    except Exception:
        pass
    edgar.set_identity(identity)

    identifier = request["identifier"]
    items = request.get("items", EXTRACTABLE)
    items = [i for i in items if i in EXTRACTABLE]

    result: dict[str, Any] = {
        "provider": PROVIDER, "market": "us", "identifier": identifier,
        "items_requested": items, "items_extracted": [], "errors": [],
    }

    try:
        from edgar import Company
        c = Company(identifier)
    except Exception as e:
        result["errors"].append(f"company_lookup: {e}")
        result["status"] = "provider-gap"
        return result

    # identity
    if "identity" in items:
        try:
            fc = str(getattr(c, "filer_category", ""))
            result["company"] = {
                "name": c.name, "cik": c.cik,
                "tickers": c.tickers if hasattr(c, "tickers") else [identifier],
                "sic": getattr(c, "sic", None), "industry": getattr(c, "industry", None),
                "fiscal_year_end": getattr(c, "fiscal_year_end", None),
                "shares_outstanding": getattr(c, "shares_outstanding", None),
                "filer_category": fc,
            }
            result["items_extracted"].append("identity")
        except Exception as e:
            result["errors"].append(f"identity: {e}")
            return result  # can't proceed without identity

    # filing_index + latest_full_filing
    if "filing_index" in items or "latest_full_filing" in items:
        try:
            from edgar import Company
            c2 = Company(identifier)
            filings = c2.get_filings(form=["10-K"])
            if filings:
                latest = filings.latest()
                filing_info = {
                    "accession_number": str(getattr(latest, "accession_number", "")),
                    "form": str(getattr(latest, "form", "10-K")),
                    "filing_date": str(getattr(latest, "filing_date", "")),
                    "period_of_report": str(getattr(latest, "period_of_report", "")),
                    "filing_url": str(getattr(latest, "filing_url", "")),
                    "markdown": "",
                    "status": "fetched",
                }
                if "latest_full_filing" in items:
                    try:
                        md = latest.markdown()
                        filing_info["markdown"] = md
                        filing_info["markdown_sha256"] = hashlib.sha256(md.encode()).hexdigest()
                    except Exception as mde:
                        result["errors"].append(f"filing_markdown: {mde}")

                result["filing"] = filing_info
                result["items_extracted"].extend(["filing_index", "latest_full_filing"] if "latest_full_filing" in items else ["filing_index"])
            else:
                result["errors"].append("filing_index: No 10-Ks found")
        except Exception as e:
            result["errors"].append(f"filing_index: {e}")

    # three statements
    for key, method_name in [
        ("income_statement", "income_statement"),
        ("balance_sheet", "balance_sheet"),
        ("cash_flow", "cashflow_statement"),
    ]:
        if key in items:
            try:
                from edgar import Company
                c3 = Company(identifier)
                stmt = getattr(c3, method_name)()
                periods = list(stmt.periods) if hasattr(stmt, "periods") else []
                result[key] = _flatten(stmt.items, periods)
                result["items_extracted"].append(key)
            except Exception as e:
                result["errors"].append(f"{key}: {e}")

    result["status"] = "success" if result["items_extracted"] else "provider-gap"
    return result


def _flatten(items, periods):
    def _walk(nodes, depth=0):
        out = []
        for node in nodes:
            vals = {}
            if hasattr(node, "values") and isinstance(node.values, dict):
                vals = {p: node.values.get(p) for p in periods if node.values.get(p) is not None}
            if vals:
                out.append({
                    "concept": getattr(node, "concept", None),
                    "label": getattr(node, "label", None),
                    "values": vals, "depth": depth,
                })
            if hasattr(node, "children") and node.children:
                out.extend(_walk(node.children, depth + 1))
        return out
    return _walk(items)


def _err(status: str, msg: str) -> dict[str, Any]:
    return {"status": status, "provider": PROVIDER, "error": msg}
