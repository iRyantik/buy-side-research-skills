"""SEC / EdgarTools provider.

Fetches deterministic, source-tracked data: company identity, latest 10-K filing
markdown, and structured IS/BS/CF from XBRL.
"""

from __future__ import annotations

import hashlib
import importlib.util
import math
import os
import re
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
import sys
import tempfile


def _provider_cache_dir() -> Path:
    """Cross-platform cache directory for provider metadata (not workspace data).

    Uses OS-appropriate location so provider caches never leak into workspace:
      Windows: %LOCALAPPDATA%  or  %TEMP%
      macOS:   ~/Library/Caches
      Linux:   ~/.cache
      Fallback: tempfile.gettempdir()
    """
    if sys.platform == "win32":
        base = os.getenv("LOCALAPPDATA")
        if base:
            return Path(base) / "buy-side-research-skills" / "financial-data-cache"
    elif sys.platform == "darwin":
        return Path.home() / "Library" / "Caches" / "buy-side-research-skills" / "financial-data-cache"
    else:
        base = os.getenv("XDG_CACHE_HOME")
        if base:
            return Path(base) / "buy-side-research-skills" / "financial-data-cache"
        return Path.home() / ".cache" / "buy-side-research-skills" / "financial-data-cache"
    # Fallback
    return Path(tempfile.gettempdir()) / "buy-side-research-skills" / "financial-data-cache"


PROVIDER = "edgartools"
EXTRACTABLE = ["identity", "filing_index", "latest_full_filing", "income_statement", "balance_sheet", "cash_flow", "revenue_split"]

STANDARD_REVENUE_CONCEPTS = {
    "RevenueFromContractWithCustomerExcludingAssessedTax",
    "Revenues",
    "SalesRevenueNet",
    "SalesRevenueGoodsNet",
    "SalesRevenueServicesNet",
}

REVENUE_INCLUDE_TOKENS = ("revenue", "revenues", "sales")
REVENUE_DENY_TOKENS = (
    "cost",
    "expense",
    "deferred",
    "unearned",
    "liability",
    "receivable",
    "allowance",
    "remaining performance obligation",
    "performance obligation",
    "gross profit",
    "tax",
    "per share",
    "earnings",
    "income tax",
    "contract asset",
    "contract liability",
)

DIMENSION_DENY_TOKENS = (
    "rangeaxis",
    "statementequitycomponentsaxis",
    "conversionofstock",
    "propertyplantandequipment",
    "remainingperformanceobligation",
    "balancesheetlocation",
    "businessacquisition",
    "measurementinput",
    "intangibleassets",
    "assetacquisition",
    "financialinstrument",
    "cashandcashequivalents",
    "fairvalue",
    "longtermdebttype",
    "debtinstrument",
    "creditfacility",
    "classofstock",
    "relatedparty",
    "stockaxis",
    "plannameaxis",
    "awardtypeaxis",
    "incometaxauthorityaxis",
    "subsequentevent",
    "concentrationrisk",
    "benchmarkaxis",
)

SPLIT_TYPE_TOKENS = {
    "timing": ("timing", "transfer of good or service", "transferred at point in time", "transferred over time"),
    "geography": ("geograph", "country", "countries", "region", "international", "domestic", "foreign", "location"),
    "segment": ("segment", "business", "division", "operating segment", "reportable segment"),
    "product": ("product", "service", "offering", "platform", "subscription", "hardware", "software"),
    "customer": ("customer", "counterparty", "major customer"),
    "channel": ("channel", "market", "distribution"),
}

PRIMARY_SPLIT_TYPES = {"segment", "geography", "product", "customer", "channel"}


def dependency_available() -> bool:
    return importlib.util.find_spec("edgar") is not None


def fetch(request: dict[str, Any]) -> dict[str, Any]:
    if not dependency_available():
        return _err("dependency-gap", "Missing edgartools. Run: pip install edgartools")
    identity = os.getenv("EDGAR_IDENTITY")
    if not identity:
        return _err("credential-gap", "Missing EDGAR_IDENTITY")
    if not os.getenv("EDGAR_LOCAL_DATA_DIR"):
        cache_dir = _provider_cache_dir() / "edgar"
        cache_dir.mkdir(parents=True, exist_ok=True)
        os.environ["EDGAR_LOCAL_DATA_DIR"] = str(cache_dir)

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
    quarterly = _is_quarterly_request(request.get("periods"))
    latest_filing = None

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
            latest_filing = _get_latest_sec_filing(c, quarterly)
            if latest_filing:
                filing_info = {
                    "accession_number": str(getattr(latest_filing, "accession_number", "")),
                    "form": str(getattr(latest_filing, "form", "10-Q" if quarterly else "10-K")),
                    "filing_date": str(getattr(latest_filing, "filing_date", "")),
                    "period_of_report": str(getattr(latest_filing, "period_of_report", "")),
                    "filing_url": str(getattr(latest_filing, "filing_url", "")),
                    "markdown": "",
                    "status": "fetched",
                }
                if "latest_full_filing" in items:
                    try:
                        md = latest_filing.markdown()
                        filing_info["markdown"] = md
                        filing_info["markdown_sha256"] = hashlib.sha256(md.encode()).hexdigest()
                    except Exception as mde:
                        result["errors"].append(f"filing_markdown: {mde}")

                result["filing"] = filing_info
                result["items_extracted"].extend(["filing_index", "latest_full_filing"] if "latest_full_filing" in items else ["filing_index"])
            else:
                result["errors"].append(f"filing_index: No {'/'.join(_sec_filing_forms(quarterly))} filings found")
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
                if quarterly:
                    stmt = getattr(c3, method_name)(periods=4, period="quarterly")
                else:
                    stmt = getattr(c3, method_name)()
                periods = list(stmt.periods) if hasattr(stmt, "periods") else []
                result[key] = _flatten(stmt.items, periods)
                result["items_extracted"].append(key)
            except Exception as e:
                result["errors"].append(f"{key}: {e}")

    if "revenue_split" in items:
        try:
            if latest_filing is None:
                latest_filing = _get_latest_sec_filing(c, quarterly)
            split_rows, split_meta = _extract_revenue_split(latest_filing)
            if split_rows:
                result["revenue_split"] = split_rows
                result["revenue_split_reconciliation"] = split_meta.get("reconciliation", {})
                result["revenue_split_completeness_status"] = split_meta.get("completeness_status", "available-review")
                result["items_extracted"].append("revenue_split")
                result.setdefault("data_gaps", []).append(
                    f"revenue_split: {split_meta.get('caveat', 'SEC revenue split extracted for review; completeness not guaranteed')}"
                )
            else:
                result.setdefault("data_gaps", []).append(
                    f"revenue_split: {split_meta.get('caveat', 'no SEC XBRL dimension or table revenue split extracted')}"
                )
        except Exception as e:
            result["errors"].append(f"revenue_split: {e}")

    result["status"] = "success" if result["items_extracted"] else "provider-gap"
    return result


def _is_quarterly_request(periods: Any) -> bool:
    token = re.sub(r"[^a-z0-9]+", "", str(periods or "").strip().lower())
    return token in {"latest4q", "last4q", "latest4quarters", "latestfourquarters", "quarterly"}


def _get_latest_sec_filing(company: Any, quarterly: bool) -> Any | None:
    filings = company.get_filings(form=_sec_filing_forms(quarterly))
    return filings.latest() if filings else None


def _sec_filing_forms(quarterly: bool) -> list[str]:
    return ["10-Q", "10-K"] if quarterly else ["10-K"]


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
                    "values": vals,
                    "period_basis_by_period": {str(period): _default_period_basis(period) for period in vals},
                    "depth": depth,
                })
            if hasattr(node, "children") and node.children:
                out.extend(_walk(node.children, depth + 1))
        return out
    return _walk(items)


def _default_period_basis(period: Any) -> str:
    text = str(period or "").strip()
    if re.fullmatch(r"FY(19\d{2}|20\d{2})", text):
        return "annual"
    if re.fullmatch(r"FY(19\d{2}|20\d{2})Q[1-4]", text):
        return "quarter"
    if text.endswith("-03-31") or text.endswith("-09-30"):
        return "quarter"
    if text.endswith("-06-30"):
        return "half_year"
    if text.endswith("-12-31"):
        return "annual"
    return "unknown"


def _extract_revenue_split(filing: Any | None) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if filing is None:
        return [], {"caveat": "no SEC filing available for revenue split extraction"}

    xbrl_rows: list[dict[str, Any]] = []
    total_revenue: dict[str, float] = {}
    try:
        xbrl = filing.xbrl()
        facts_df = xbrl.facts.to_dataframe()
        xbrl_rows, total_revenue = _extract_revenue_split_from_facts(facts_df, filing)
    except Exception as exc:
        xbrl_error = str(exc)
    else:
        xbrl_error = ""

    if xbrl_rows:
        reconciliation = _reconcile_revenue_split(xbrl_rows, total_revenue)
        status = _reconciliation_status(reconciliation)
        _attach_reconciliation_metadata(xbrl_rows, reconciliation, status)
        for row in xbrl_rows:
            row["completeness_status"] = status
        caveat = "SEC XBRL dimension revenue split extracted; driver-map must review labels and completeness"
        if status == "unreconciled-review":
            caveat = "SEC XBRL dimension revenue split extracted, but no usable total revenue fact was available for reconciliation"
        elif status == "partial-review":
            caveat = "SEC XBRL dimension revenue split extracted, but split totals do not fully reconcile to total revenue"
        return xbrl_rows, {
            "source_type": "official-xbrl-dimension",
            "completeness_status": status,
            "reconciliation": reconciliation,
            "caveat": caveat,
        }

    table_rows, table_meta = _extract_revenue_split_from_tables(filing)
    if table_rows:
        return table_rows, table_meta

    caveat = "no dimensioned SEC revenue facts found"
    if xbrl_error:
        caveat = f"{caveat}; XBRL parse error: {xbrl_error}"
    return [], {"caveat": caveat}


def _extract_revenue_split_from_facts(facts_df: Any, filing: Any) -> tuple[list[dict[str, Any]], dict[str, float]]:
    rows_by_key: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    total_revenue: dict[str, float] = {}

    records = facts_df.to_dict("records")
    for rec in records:
        concept = str(rec.get("concept") or "")
        label = str(rec.get("label") or rec.get("original_label") or concept)
        if not _is_revenue_concept(concept, label):
            continue
        value = _clean_numeric(rec.get("numeric_value"))
        if value is None:
            value = _clean_numeric(rec.get("value"))
        if value is None:
            continue
        if str(rec.get("period_type") or "").lower() != "duration":
            continue

        period = _period_label(rec)
        if not period:
            continue
        dimensions = _dimension_pairs(rec)
        if not dimensions:
            total_revenue.setdefault(period, value)
            continue

        for dim in dimensions:
            split_type = _classify_split_type(dim)
            if split_type is None:
                continue
            axis = dim["axis"]
            member = dim["member"]
            member_label = dim.get("member_label") or member
            row_key = (split_type, axis, member, concept)
            row = rows_by_key.setdefault(row_key, {
                "label": member_label,
                "split_type": split_type,
                "axis": axis,
                "axis_label": dim.get("axis_label", ""),
                "member": member,
                "member_label": member_label,
                "concept": concept,
                "concept_label": label,
                "values": {},
                "period_start_by_period": {},
                "period_end_by_period": {},
                "unit": rec.get("unit_ref"),
                "source_id": str(getattr(filing, "accession_number", "")),
                "source_url": str(getattr(filing, "filing_url", "")),
                "source_type": "official-xbrl-dimension",
                "extraction_method": "xbrl-dimension",
                "confidence": "evidence-ready-review",
                "review_required": True,
                "model_bucket_hint": _model_bucket_hint(split_type, member_label, axis),
            })
            row["values"][period] = value
            if rec.get("period_start"):
                row["period_start_by_period"][period] = str(rec.get("period_start"))
            if rec.get("period_end"):
                row["period_end_by_period"][period] = str(rec.get("period_end"))
            row["period_start"] = row["period_start_by_period"].get(period, row.get("period_start", ""))
            row["period_end"] = row["period_end_by_period"].get(period, row.get("period_end", ""))

    return _sorted_split_rows(rows_by_key.values()), total_revenue


def _extract_revenue_split_from_tables(filing: Any) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Very conservative V2 fallback: only parse obvious revenue tables from filing HTML."""
    try:
        html = filing.html()
    except Exception:
        return [], {"caveat": "SEC filing table fallback unavailable: filing HTML could not be read"}

    parser = _TableTextParser()
    try:
        parser.feed(html)
    except Exception:
        return [], {"caveat": "SEC filing table fallback unavailable: filing HTML could not be parsed"}

    candidates: list[dict[str, Any]] = []
    for table_info in parser.tables:
        table = table_info.get("rows", [])
        flat = " ".join(cell.lower() for row in table for cell in row)
        heading = str(table_info.get("heading") or "")
        context = f"{heading} {flat}".lower()
        if "revenue" not in context and "sales" not in context:
            continue
        if not any(token in context for token in ("segment", "geograph", "product", "service", "customer", "region")):
            continue
        rows = _table_to_revenue_rows(table, filing, heading)
        candidates.extend(rows)
        if candidates:
            break

    if not candidates:
        return [], {"caveat": "no obvious SEC filing HTML revenue split table extracted"}
    return candidates, {
        "source_type": "filing-table-extracted-review",
        "completeness_status": "partial-review",
        "reconciliation": {},
        "caveat": "SEC filing HTML table revenue split extracted for review; XBRL dimensions were unavailable",
    }


def _table_to_revenue_rows(table: list[list[str]], filing: Any, heading: str = "") -> list[dict[str, Any]]:
    if len(table) < 2:
        return []
    header_idx = 0
    for idx, row in enumerate(table[:8]):
        if sum(1 for cell in row if _normalize_period_text(cell)) >= 1:
            header_idx = idx
            break
    headers = table[header_idx]
    period_indexes = [(idx, _normalize_period_text(cell)) for idx, cell in enumerate(headers) if _normalize_period_text(cell)]
    if not period_indexes:
        return []

    out = []
    for row in table[header_idx + 1:]:
        if not row:
            continue
        label = row[0].strip()
        if not label or _looks_like_total_label(label):
            continue
        values: dict[str, float] = {}
        for idx, period in period_indexes:
            if idx < len(row):
                value = _parse_table_number(row[idx])
                if value is not None:
                    values[period] = value
        if values:
            split_type = _classify_label_split_type(f"{heading} {label}".strip())
            out.append({
                "label": label,
                "split_type": split_type,
                "axis": "filing-table",
                "axis_label": "Filing table",
                "member": label,
                "member_label": label,
                "concept": "filing-table:RevenueSplit",
                "concept_label": "Revenue split extracted from filing table",
                "values": values,
                "table_heading": heading,
                "source_id": str(getattr(filing, "accession_number", "")),
                "source_url": str(getattr(filing, "filing_url", "")),
                "source_type": "filing-table-extracted-review",
                "extraction_method": "filing-html-table",
                "confidence": "filing-table-extracted-review",
                "review_required": True,
                "model_bucket_hint": _model_bucket_hint(split_type, label, "filing-table"),
            })
    return out[:50]


def _is_revenue_concept(concept: str, label: str) -> bool:
    local = _local_name(concept)
    if local in STANDARD_REVENUE_CONCEPTS:
        return True
    concept_text = str(concept or "").replace("_", " ").lower()
    label_text = str(label or "").replace("_", " ").lower()
    haystack = f"{concept_text} {label_text}"
    compact = re.sub(r"[^a-z0-9]+", "", haystack)
    if not any(token in concept_text for token in REVENUE_INCLUDE_TOKENS):
        return False
    return not any(token in haystack or token.replace(" ", "") in compact for token in REVENUE_DENY_TOKENS)


def _dimension_pairs(rec: dict[str, Any]) -> list[dict[str, str]]:
    pairs: list[dict[str, str]] = []
    generic_axis = _clean_text(rec.get("dimension"))
    generic_member = _clean_text(rec.get("member"))
    if generic_axis and generic_member:
        pairs.append({
            "axis": generic_axis,
            "member": generic_member,
            "axis_label": _clean_text(rec.get("dimension_label")),
            "member_label": _clean_text(rec.get("dimension_member_label")),
        })

    for key, value in rec.items():
        if not str(key).startswith("dim_"):
            continue
        member = _clean_text(value)
        if not member:
            continue
        axis = str(key)[4:].replace("_", ":")
        if any(pair["axis"] == axis and pair["member"] == member for pair in pairs):
            continue
        pairs.append({
            "axis": axis,
            "member": member,
            "axis_label": axis,
            "member_label": _member_label(member),
        })
    return pairs


def _classify_split_type(dim: dict[str, str]) -> str | None:
    text = " ".join(str(dim.get(key, "")) for key in ("axis", "member", "axis_label", "member_label")).lower()
    compact = re.sub(r"[^a-z0-9]+", "", text)
    if any(token in compact for token in DIMENSION_DENY_TOKENS):
        return None
    for split_type, tokens in SPLIT_TYPE_TOKENS.items():
        if any(token in text for token in tokens):
            return split_type
    if "axis" in text and ("revenue" in text or "sales" in text):
        return "other"
    return None


def _classify_label_split_type(label: str) -> str:
    text = label.lower()
    for split_type, tokens in SPLIT_TYPE_TOKENS.items():
        if any(token in text for token in tokens):
            return split_type
    return "other"


def _reconcile_revenue_split(rows: list[dict[str, Any]], total_revenue: dict[str, float]) -> dict[str, Any]:
    grouped: dict[tuple[str, str], dict[str, float]] = {}
    for row in rows:
        key_base = (row.get("axis", ""), row.get("concept", ""))
        for period, value in row.get("values", {}).items():
            numeric = _clean_numeric(value)
            if numeric is None:
                continue
            grouped.setdefault(key_base, {}).setdefault(period, 0.0)
            grouped[key_base][period] += numeric

    checks = []
    for (axis, concept), values in sorted(grouped.items()):
        for period, split_sum in sorted(values.items()):
            total = total_revenue.get(period)
            ratio = None
            status = "unreconciled-review"
            if total not in (None, 0):
                ratio = split_sum / total
                status = "appears_complete-review" if 0.95 <= ratio <= 1.05 else "partial-review"
            checks.append({
                "axis": axis,
                "concept": concept,
                "period": period,
                "split_sum": split_sum,
                "total_revenue": total,
                "ratio": ratio,
                "status": status,
            })
    summary = {
        "axis_count": len({row.get("axis") for row in rows if row.get("axis")}),
        "concept_count": len({row.get("concept") for row in rows if row.get("concept")}),
        "period_count": len({period for row in rows for period in (row.get("values") or {}).keys()}),
        "check_count": len(checks),
    }
    return {"checks": checks, "summary": summary}


def _reconciliation_status(reconciliation: dict[str, Any]) -> str:
    checks = reconciliation.get("checks", [])
    if not checks:
        return "available-review"
    statuses = {check.get("status") for check in checks}
    if statuses == {"unreconciled-review"}:
        return "unreconciled-review"
    if "appears_complete-review" in statuses and "partial-review" not in statuses and "unreconciled-review" not in statuses:
        return "appears_complete-review"
    return "partial-review"


def _attach_reconciliation_metadata(rows: list[dict[str, Any]], reconciliation: dict[str, Any], overall_status: str) -> None:
    status_by_axis_concept: dict[tuple[str, str], str] = {}
    for check in reconciliation.get("checks", []):
        key = (str(check.get("axis") or ""), str(check.get("concept") or ""))
        existing = status_by_axis_concept.get(key)
        status = str(check.get("status") or overall_status)
        if existing == "partial-review" or status == "partial-review":
            status_by_axis_concept[key] = "partial-review"
        elif existing == "unreconciled-review" or status == "unreconciled-review":
            status_by_axis_concept[key] = "unreconciled-review"
        else:
            status_by_axis_concept[key] = status
    for row in rows:
        key = (str(row.get("axis") or ""), str(row.get("concept") or ""))
        axis_status = status_by_axis_concept.get(key, overall_status)
        row["axis_completeness_status"] = axis_status
        row["reconciliation_status"] = overall_status


def _period_label(rec: dict[str, Any]) -> str:
    fiscal_year = _clean_text(rec.get("fiscal_year"))
    fiscal_period = _clean_text(rec.get("fiscal_period"))
    if fiscal_year and fiscal_year.lower() != "nan":
        year = re.sub(r"\.0$", "", fiscal_year)
        if fiscal_period and fiscal_period.lower() not in {"nan", "none"}:
            return f"FY{year}{fiscal_period}" if fiscal_period != "FY" else f"FY{year}"
        return f"FY{year}"
    period_end = _clean_text(rec.get("period_end") or rec.get("period_instant"))
    return period_end


def _normalize_period_text(text: str) -> str:
    raw = str(text)
    match = re.search(r"(20\d{2}|19\d{2})", raw)
    if match:
        return f"FY{match.group(1)}"
    short = re.search(r"\b'?(2\d)\b", raw)
    if short:
        return f"FY20{short.group(1)}"
    return ""


def _clean_numeric(value: Any) -> float | None:
    if value is None:
        return None
    try:
        if isinstance(value, float) and math.isnan(value):
            return None
    except Exception:
        pass
    text = str(value).strip()
    if text.lower() in {"", "nan", "none", "nat", "--"}:
        return None
    text = text.replace(",", "").replace("$", "")
    negative = text.startswith("(") and text.endswith(")")
    text = text.strip("()")
    try:
        number = float(text)
    except ValueError:
        return None
    return -number if negative else number


def _parse_table_number(text: str) -> float | None:
    cleaned = str(text).replace("\xa0", " ").strip()
    match = re.search(r"\(?-?\$?\s*[\d,]+(?:\.\d+)?\)?", cleaned)
    return _clean_numeric(match.group(0)) if match else None


def _clean_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    return "" if text.lower() in {"", "nan", "none", "nat"} else text


def _local_name(concept: str) -> str:
    return str(concept or "").split(":")[-1]


def _member_label(member: str) -> str:
    local = _local_name(member)
    local = re.sub(r"Member$", "", local)
    return re.sub(r"(?<!^)([A-Z])", r" \1", local).strip() or member


def _looks_like_total_label(label: str) -> bool:
    return bool(re.search(r"\b(total|net revenue|revenues?|sales)\b", label, flags=re.I))


def _model_bucket_hint(split_type: str, label: str, axis: str) -> str:
    if split_type in PRIMARY_SPLIT_TYPES:
        return split_type
    if split_type == "timing":
        return "revenue_recognition_timing_review"
    if axis == "filing-table":
        return "table_extracted_bucket_review"
    return f"{split_type or 'other'}_review"


def _sorted_split_rows(rows: Any) -> list[dict[str, Any]]:
    finalized = []
    for row in rows:
        values = row.get("values", {})
        if values:
            latest_period = sorted(values.keys())[-1]
            starts = row.get("period_start_by_period", {})
            ends = row.get("period_end_by_period", {})
            if starts.get(latest_period):
                row["period_start"] = starts[latest_period]
            if ends.get(latest_period):
                row["period_end"] = ends[latest_period]
        finalized.append(row)
    return sorted(
        finalized,
        key=lambda row: (
            str(row.get("split_type", "")),
            str(row.get("axis", "")),
            str(row.get("member_label", row.get("label", ""))),
            str(row.get("concept", "")),
        ),
    )


class _TableTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.tables: list[dict[str, Any]] = []
        self._table: list[list[str]] | None = None
        self._row: list[str] | None = None
        self._cell: list[str] | None = None
        self._heading_capture: list[str] | None = None
        self._recent_heading = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "table":
            self._table = []
        elif tag.lower() == "tr" and self._table is not None:
            self._row = []
        elif tag.lower() in {"td", "th"} and self._row is not None:
            self._cell = []
        elif tag.lower() in {"h1", "h2", "h3", "h4", "h5", "strong", "b", "p"} and self._table is None:
            self._heading_capture = []

    def handle_data(self, data: str) -> None:
        if self._cell is not None:
            text = " ".join(str(data).split())
            if text:
                self._cell.append(text)
        elif self._heading_capture is not None:
            text = " ".join(str(data).split())
            if text:
                self._heading_capture.append(text)

    def handle_endtag(self, tag: str) -> None:
        lower = tag.lower()
        if lower in {"td", "th"} and self._cell is not None and self._row is not None:
            self._row.append(" ".join(self._cell).strip())
            self._cell = None
        elif lower == "tr" and self._row is not None and self._table is not None:
            if any(cell for cell in self._row):
                self._table.append(self._row)
            self._row = None
        elif lower == "table" and self._table is not None:
            if self._table:
                self.tables.append({"heading": self._recent_heading, "rows": self._table})
            self._table = None
        elif lower in {"h1", "h2", "h3", "h4", "h5", "strong", "b", "p"} and self._heading_capture is not None:
            text = " ".join(self._heading_capture).strip()
            if text and len(text) <= 180:
                self._recent_heading = text
            self._heading_capture = None


def _err(status: str, msg: str) -> dict[str, Any]:
    return {"status": status, "provider": PROVIDER, "error": msg}
