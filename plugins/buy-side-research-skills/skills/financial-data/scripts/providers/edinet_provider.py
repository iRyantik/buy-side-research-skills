"""EDINET provider for Japan financial-data routes.

Deterministic extraction: identity, income_statement, balance_sheet, cash_flow, latest_full_filing.
"""

from __future__ import annotations

import datetime as dt
from concurrent.futures import ThreadPoolExecutor, as_completed
from html.parser import HTMLParser
import importlib.util
import json
import os
from pathlib import Path
import re
import tempfile
import time
from typing import Any
import zipfile


PROVIDER = "edinet-tools"
EXTRACTABLE = ["identity", "filing_index", "income_statement", "balance_sheet", "cash_flow", "latest_full_filing", "revenue_split"]
EDINET_DISCOVERY_BUDGET_SECONDS_QUARTERLY = 160
EDINET_DISCOVERY_BUDGET_SECONDS_ANNUAL = 90
EDINET_DISCOVERY_WORKERS = 4
EDINET_DOCUMENT_LIST_TIMEOUT_SECONDS = 15
EDINET_DOCUMENT_LIST_CACHE_TTL_SECONDS = 7 * 24 * 60 * 60


def dependency_available() -> bool:
    return importlib.util.find_spec("edinet_tools") is not None


def fetch(request: dict[str, Any]) -> dict[str, Any]:
    if not dependency_available():
        return {"status": "dependency-gap", "provider": PROVIDER, "error": "Missing edinet-tools. Run: pip install edinet-tools"}

    identifier = request["identifier"]
    items = request.get("items", EXTRACTABLE)
    items = [i for i in items if i in EXTRACTABLE]
    periods_text = str(request.get("periods", "latest"))
    quarterly = _is_quarterly_request(periods_text)

    api_key = os.getenv("EDINET_API_KEY")
    if not api_key:
        return {"status": "credential-gap", "provider": PROVIDER, "error": "Missing EDINET_API_KEY. Register for EDINET API access."}

    result: dict[str, Any] = {
        "provider": PROVIDER,
        "market": "jp",
        "identifier": identifier,
        "items_requested": items,
        "items_extracted": [],
        "errors": [],
    }
    timings: dict[str, float] = {}

    import edinet_tools as et

    et.configure(api_key=api_key)

    # --- identity ---
    entity = None
    if "identity" in items or _needs_data(items):
        phase_start = time.perf_counter()
        try:
            entity = et.entity_by_ticker(identifier)
            if not getattr(entity, "edinet_code", None):
                raise ValueError(f"EDINET entity not found for ticker {identifier}")
            result["company"] = {
                "name": getattr(entity, "name", str(entity)),
                "edinet_code": getattr(entity, "edinet_code", None),
                "ticker": identifier,
                "type": str(getattr(entity, "type", "")),
            }
            result["items_extracted"].append("identity")
        except Exception as e:
            result["errors"].append(f"identity: {e}")
            timings["identity_lookup_seconds"] = _elapsed(phase_start)
            result["provider_timing"] = timings
            return result
        timings["identity_lookup_seconds"] = _elapsed(phase_start)

    parsed_reports: list[tuple[Any, dict[str, Any]]] = []
    needs_report = bool({"income_statement", "balance_sheet", "cash_flow", "latest_full_filing"} & set(items))
    if entity and hasattr(entity, "edinet_code") and needs_report:
        discovery_start = time.perf_counter()
        try:
            years = _years_from_periods(periods_text)
            documents = _discover_report_documents(entity, years, api_key, quarterly=quarterly)
            timings["filing_discovery_seconds"] = _elapsed(discovery_start)
            if not documents:
                raise RuntimeError(f"docID discovery failed for {entity.edinet_code} across years {years}")
            if quarterly and len(documents) < 4:
                result.setdefault("data_gaps", []).append(
                    f"latest4q_document_coverage: EDINET discovery found {len(documents)} of 4 target documents"
                )
            parse_start = time.perf_counter()
            for document in documents:
                document_meta = _document_meta(document)
                parsed_reports.append((document.parse(), document_meta))
            timings["statement_parse_seconds"] = _elapsed(parse_start)
            result["filing_documents"] = [meta for _, meta in parsed_reports]
            if "filing_index" in items:
                result["items_extracted"].append("filing_index")
        except Exception as e:
            timings.setdefault("filing_discovery_seconds", _elapsed(discovery_start))
            result["errors"].append(f"securities_report: {e}")

    # --- statements ---
    if parsed_reports:
        for item_key in ("income_statement", "balance_sheet", "cash_flow"):
            if item_key in items:
                try:
                    merged: dict[str, dict[str, Any]] = {}
                    for parsed_report, document_meta in parsed_reports:
                        for row in _extract_from_parsed(parsed_report, item_key, document_meta):
                            _merge_statement_row(merged, row)
                    stmt_data = list(merged.values())
                    if stmt_data:
                        result[item_key] = stmt_data
                        result["items_extracted"].append(item_key)
                    else:
                        result["errors"].append(f"{item_key}: parsed report returned no rows")
                except Exception as e:
                    result["errors"].append(f"{item_key}: {e}")

    # --- latest_full_filing ---
    if "latest_full_filing" in items and parsed_reports and entity and hasattr(entity, "edinet_code"):
        filing_start = time.perf_counter()
        latest_parsed, latest_meta = parsed_reports[0]
        filing = _get_filing_text(entity, latest_parsed, latest_meta, api_key)
        timings["latest_full_filing_seconds"] = _elapsed(filing_start)
        timings.update(filing.get("timing", {}) if isinstance(filing, dict) else {})
        result["filing"] = filing
        if filing.get("status") == "fetched" and filing.get("markdown"):
            result["items_extracted"].append("latest_full_filing")
        else:
            result["errors"].append(f"latest_full_filing: {filing.get('error', 'markdown unavailable')}")

    if "revenue_split" in items:
        result.setdefault("data_gaps", []).append("revenue_split: no stable structured EDINET revenue split parser in this route")

    non_identity = set(result["items_extracted"]) - {"identity"}
    if result["items_extracted"]:
        if _needs_data(items) and not non_identity:
            result["status"] = "provider-gap"
        else:
            result["status"] = "partial" if result["errors"] else "success"
    else:
        result["status"] = "provider-gap"
    result["provider_timing"] = timings
    return result


def _needs_data(items: list[str]) -> bool:
    return bool({"filing_index", "income_statement", "balance_sheet", "cash_flow", "latest_full_filing"} & set(items))


def _extract_from_parsed(parsed: Any, item_key: str, document_meta: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Extract core statement data from an edinet-tools ParsedReport."""
    data = parsed.to_dict() if hasattr(parsed, "to_dict") else {}
    document_meta = document_meta or {}
    current_period = _period_from_document(document_meta, data)
    prior_period = _prior_period(current_period)
    include_prior = str(document_meta.get("doc_type_code") or "") == "120"

    maps = {
        "income_statement": [
            ("Net sales", "net_sales", "prior_net_sales"),
            ("Operating income", "operating_income", "prior_operating_income"),
            ("Ordinary income", "ordinary_income", "prior_ordinary_income"),
            ("Net income", "net_income", "prior_net_income"),
            ("Profit loss", "profit_loss", None),
            ("Income before taxes", "income_before_taxes", None),
            ("Non-operating income", "non_operating_income", None),
            ("Non-operating expenses", "non_operating_expenses", None),
            ("Income taxes", "income_taxes", None),
        ],
        "balance_sheet": [
            ("Total assets", "total_assets", None),
            ("Current assets", "current_assets", None),
            ("Noncurrent assets", "noncurrent_assets", None),
            ("Cash and deposits", "cash_and_deposits", None),
            ("Property, plant and equipment", "property_plant_equipment", None),
            ("Deferred tax assets", "deferred_tax_assets", None),
            ("Total liabilities", "total_liabilities", None),
            ("Current liabilities", "current_liabilities", None),
            ("Net assets", "net_assets", None),
            ("Retained earnings", "retained_earnings", None),
            ("Short-term loans payable", "short_term_loans_payable", None),
            ("Long-term loans payable", "long_term_loans_payable", None),
            ("Bonds payable", "bonds_payable", None),
            ("Commercial paper", "commercial_paper", None),
        ],
        "cash_flow": [
            ("Operating cash flow", "operating_cash_flow", None),
            ("Investing cash flow", "investing_cash_flow", None),
            ("Financing cash flow", "financing_cash_flow", None),
            ("Depreciation and amortization", "depreciation_amortization", None),
        ],
    }

    rows = []
    for label, current_field, prior_field in maps.get(item_key, []):
        values = {}
        current_value = data.get(current_field)
        if current_value is not None:
            values[current_period] = current_value
        if include_prior and prior_field and data.get(prior_field) is not None:
            values[prior_period] = data.get(prior_field)
        if values:
            period_basis_by_period = {
                period: _edinet_period_basis(period, document_meta)
                for period in values
            }
            rows.append({
                "label": label,
                "concept": current_field,
                "values": values,
                "period_basis_by_period": period_basis_by_period,
                "currency": "JPY",
                "source_type": "official-parser",
                "provider": PROVIDER,
                "doc_id": document_meta.get("doc_id"),
                "doc_type_code": document_meta.get("doc_type_code"),
            })
    return rows


def _merge_statement_row(grouped: dict[str, dict[str, Any]], row: dict[str, Any]) -> None:
    key = str(row.get("concept") or row.get("label") or "").strip()
    if not key:
        return
    item = grouped.setdefault(key, {
        "label": row.get("label"),
        "concept": row.get("concept"),
        "values": {},
        "period_basis_by_period": {},
        "currency": row.get("currency"),
        "source_type": row.get("source_type"),
        "provider": row.get("provider"),
    })
    item["values"].update(row.get("values", {}) or {})
    item["period_basis_by_period"].update(row.get("period_basis_by_period", {}) or {})


def _get_filing_text(entity: Any, parsed: Any, document_meta: dict[str, Any],
                     api_key: str) -> dict[str, Any]:
    """Get latest EDINET filing text from official type=1 ZIP source."""
    try:
        edinet_code = entity.edinet_code
        doc_id = document_meta.get("doc_id")
        if not doc_id:
            return {"status": "error", "error": "missing EDINET document id"}

        zip_start = time.perf_counter()
        package_path = _download_public_doc_zip(str(doc_id), api_key)
        extract_start = time.perf_counter()
        markdown = _extract_public_doc_markdown(
            package_path=package_path,
            edinet_code=edinet_code,
            document_meta=document_meta,
        )
        timing = {
            "document_zip_download_seconds": _elapsed(zip_start),
            "markdown_extraction_seconds": _elapsed(extract_start),
        }
        if not markdown:
            return {
                "status": "error",
                "error": "EDINET type=1 package contained no readable PublicDoc HTML/XHTML text",
                "local_path": str(package_path),
                "timing": timing,
            }

        return {
            "edinet_code": edinet_code,
            "document_id": doc_id,
            "doc_type": document_meta.get("doc_type_code", "120"),
            "filing_date": str(document_meta.get("filing_datetime") or "")[:10],
            "source_url": f"https://disclosure.edinet-fsa.go.jp/api/v2/documents/{doc_id}",
            "source_package_type": "EDINET API type=1 ZIP",
            "local_path": str(package_path),
            "text_length": len(markdown),
            "markdown": markdown,
            "status": "fetched",
            "timing": timing,
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


def _download_public_doc_zip(doc_id: str, api_key: str) -> Path:
    from edinet_tools.api import fetch_document

    safe_doc_id = re.sub(r"[^A-Za-z0-9._-]+", "_", doc_id)
    target_dir = Path(tempfile.gettempdir()) / "bsrs-edinet-documents"
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / f"{safe_doc_id}-type1.zip"
    content = fetch_document(doc_id, type=1, api_key=api_key, timeout=120, max_retries=2)
    target_path.write_bytes(content)
    if not zipfile.is_zipfile(target_path):
        preview = content[:200].decode("utf-8", errors="ignore")
        raise RuntimeError(f"EDINET type=1 response is not a ZIP file: {preview}")
    return target_path


def _extract_public_doc_markdown(package_path: Path, edinet_code: str,
                                 document_meta: dict[str, Any]) -> str:
    with zipfile.ZipFile(package_path) as package:
        html_names = [
            name for name in package.namelist()
            if name.lower().endswith((".htm", ".html", ".xhtml"))
        ]
        ordered_names = sorted(html_names, key=_html_source_priority)
        sections = []
        for name in ordered_names:
            raw = package.read(name)
            html = _decode_html(raw)
            text = _html_to_text(html)
            if not text:
                continue
            sections.append(f"## Source File: {name}\n\n{text}")

    if not sections:
        return ""

    header = [
        "# EDINET Filing Text",
        "",
        f"- EDINET code: {edinet_code}",
        f"- Document ID: {document_meta.get('doc_id')}",
        f"- Document type: {document_meta.get('doc_type_code')}",
        f"- Filing datetime: {document_meta.get('filing_datetime')}",
        f"- Period end: {document_meta.get('period_end')}",
        f"- Description: {document_meta.get('doc_description')}",
        "- Source package: EDINET API type=1 ZIP",
        "",
    ]
    return "\n".join(header + sections) + "\n"


def _html_source_priority(name: str) -> tuple[int, int, int, str]:
    normalized = name.replace("\\", "/").lower()
    public_rank = 0 if "/publicdoc/" in normalized or "publicdoc/" in normalized else 1
    audit_rank = 1 if "/auditdoc/" in normalized or "auditdoc/" in normalized else 0
    return (public_rank, audit_rank, len(normalized), normalized)


def _decode_html(raw: bytes) -> str:
    for encoding in ("utf-8", "cp932", "shift_jis", "euc_jp"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="ignore")


class _HtmlTextExtractor(HTMLParser):
    block_tags = {
        "address", "article", "br", "caption", "div", "h1", "h2", "h3", "h4",
        "h5", "h6", "li", "p", "section", "table", "tbody", "td", "tfoot",
        "th", "thead", "tr",
    }

    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag in {"script", "style", "noscript"}:
            self._skip_depth += 1
            return
        if tag in self.block_tags:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in {"script", "style", "noscript"} and self._skip_depth:
            self._skip_depth -= 1
            return
        if tag in self.block_tags:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        text = " ".join(str(data).split())
        if text:
            self.parts.append(text)


def _html_to_text(html: str) -> str:
    parser = _HtmlTextExtractor()
    parser.feed(html)
    raw_text = "".join(
        "\n" if part == "\n" else f"{part} "
        for part in parser.parts
    )
    lines = []
    previous = ""
    for line in raw_text.splitlines():
        cleaned = " ".join(line.split())
        if not cleaned or cleaned == previous:
            continue
        lines.append(cleaned)
        previous = cleaned
    return "\n".join(lines)


def _years_from_periods(periods: str) -> list[int]:
    years = [int(year) for year in __import__("re").findall(r"(20\d{2}|19\d{2})", periods)]
    if len(years) >= 2:
        start_year, end_year = min(years), max(years)
        return list(range(start_year, end_year + 1))
    if len(years) == 1:
        return [years[0]]
    today = dt.date.today()
    return [today.year, today.year - 1, today.year - 2]


def _discover_report_documents(entity: Any, years: list[int], api_key: str | None,
                               quarterly: bool = False) -> list[Any]:
    from edinet_tools.document import Document

    last_error = None
    doc_types = {"140", "160", "120"} if quarterly else {"120"}
    max_documents = 4 if quarterly else 1
    budget_seconds = EDINET_DISCOVERY_BUDGET_SECONDS_QUARTERLY if quarterly else EDINET_DISCOVERY_BUDGET_SECONDS_ANNUAL
    started_at = time.perf_counter()
    matches_by_doc_id: dict[str, dict[str, Any]] = {}

    candidate_dates: list[str] = []
    seen_dates = set()
    for year in sorted(years, reverse=True):
        for candidate_date in _candidate_filing_dates(year, quarterly=quarterly):
            if candidate_date in seen_dates:
                continue
            candidate_dates.append(candidate_date)
            seen_dates.add(candidate_date)

    for batch in _batches(candidate_dates, EDINET_DISCOVERY_WORKERS):
        if time.perf_counter() - started_at > budget_seconds:
            if matches_by_doc_id:
                break
            raise RuntimeError(f"docID discovery budget exceeded after {budget_seconds}s")
        with ThreadPoolExecutor(max_workers=min(EDINET_DISCOVERY_WORKERS, len(batch))) as executor:
            future_map = {
                executor.submit(_fetch_documents_list_cached, candidate_date, api_key): candidate_date
                for candidate_date in batch
            }
            for future in as_completed(future_map):
                try:
                    payload = future.result()
                except Exception as e:
                    last_error = e
                    continue
                matches = [
                    item for item in (payload.get("results") or [])
                    if item.get("edinetCode") == entity.edinet_code and item.get("docTypeCode") in doc_types
                ]
                for item in matches:
                    doc_id = str(item.get("docID") or "").strip()
                    if doc_id:
                        matches_by_doc_id[doc_id] = item
        if len(matches_by_doc_id) >= max_documents:
            break

    if matches_by_doc_id:
        ordered = sorted(
            matches_by_doc_id.values(),
            key=lambda item: str(item.get("submitDateTime") or ""),
            reverse=True,
        )[:max_documents]
        return [Document(item) for item in ordered]
    if last_error:
        raise RuntimeError(f"docID discovery failed after API/cache error: {last_error}")
    return []


def _fetch_documents_list_cached(candidate_date: str, api_key: str | None) -> dict[str, Any]:
    from edinet_tools.client import fetch_documents_list

    cache_path = _edinet_document_list_cache_path(candidate_date)
    if cache_path.exists() and time.time() - cache_path.stat().st_mtime < EDINET_DOCUMENT_LIST_CACHE_TTL_SECONDS:
        try:
            return json.loads(cache_path.read_text(encoding="utf-8"))
        except Exception:
            cache_path.unlink(missing_ok=True)
    payload = fetch_documents_list(
        candidate_date,
        api_key=api_key,
        timeout=EDINET_DOCUMENT_LIST_TIMEOUT_SECONDS,
        max_retries=1,
    )
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return payload


def _edinet_document_list_cache_path(candidate_date: str) -> Path:
    base = os.getenv("LOCALAPPDATA")
    if base:
        root = Path(base)
    else:
        root = Path(tempfile.gettempdir())
    return root / "buy-side-research-skills" / "financial-data-cache" / "edinet-document-lists" / f"{candidate_date}.json"


def _batches(values: list[str], size: int) -> list[list[str]]:
    return [values[index:index + size] for index in range(0, len(values), size)]


def _candidate_filing_dates(year: int, quarterly: bool = False) -> list[str]:
    today = dt.date.today()
    if quarterly:
        windows = [
            (dt.date(year + 1, 2, 7), dt.date(year + 1, 2, 17)),
            (dt.date(year, 11, 7), dt.date(year, 11, 17)),
            (dt.date(year, 8, 7), dt.date(year, 8, 17)),
            (dt.date(year, 6, 20), dt.date(year, 7, 7)),
            (dt.date(year, 5, 7), dt.date(year, 5, 17)),
            (dt.date(year, 9, 7), dt.date(year, 9, 17)),
            (dt.date(year, 12, 7), dt.date(year, 12, 17)),
        ]
    else:
        windows = [
            (dt.date(year, 6, 20), dt.date(year, 7, 7)),
            (dt.date(year, 3, 25), dt.date(year, 4, 10)),
            (dt.date(year, 5, 15), dt.date(year, 6, 15)),
            (dt.date(year, 9, 20), dt.date(year, 10, 10)),
            (dt.date(year, 12, 20), dt.date(year + 1, 1, 10)),
        ]
    dates: list[str] = []
    seen = set()
    for start, end in windows:
        current = min(end, today)
        while current >= start:
            value = current.isoformat()
            if value not in seen:
                dates.append(value)
                seen.add(value)
            current -= dt.timedelta(days=1)
    return dates


def _document_meta(document: Any) -> dict[str, Any]:
    return {
        "doc_id": getattr(document, "doc_id", None),
        "doc_type_code": getattr(document, "doc_type_code", None),
        "doc_description": getattr(document, "doc_description", None),
        "period_end": getattr(document, "period_end", None),
        "filing_datetime": str(getattr(document, "filing_datetime", None) or ""),
        "filer_edinet_code": getattr(document, "filer_edinet_code", None),
        "filer_name": getattr(document, "filer_name", None),
    }


def _is_quarterly_request(periods: str | None) -> bool:
    token = re.sub(r"[^a-z0-9]+", "", str(periods or "").strip().lower())
    return token in {"latest4q", "last4q", "latest4quarters", "latestfourquarters", "quarterly"}


def _period_from_document(document_meta: dict[str, Any], data: dict[str, Any]) -> str:
    doc_type = str(document_meta.get("doc_type_code") or "")
    period_end = str(document_meta.get("period_end") or data.get("fiscal_year_end") or "")

    # Fallback: infer from filing_datetime if period_end is empty
    if not period_end or period_end.strip() == "":
        filing_dt = str(document_meta.get("filing_datetime") or "")
        if filing_dt:
            filing_match = re.search(r"(20\d{2}|19\d{2})", filing_dt)
            if filing_match:
                filing_year = int(filing_match.group(1))
                if doc_type == "120":
                    # Annual report filed ~3-4 months after FY end
                    return f"FY{filing_year - 1}"
                elif doc_type == "160":
                    return f"FY{filing_year}H1"
                elif doc_type == "140":
                    return f"FY{filing_year - 1}Q3"
            # If we have doc description, try to parse quarter
            desc = str(document_meta.get("doc_description") or "")
            desc_match = re.search(r"(20\d{2}|19\d{2})", desc)
            if desc_match:
                return _period_from_end(desc_match.group(1))
        return _period_from_end(period_end)

    if doc_type == "120":
        return _period_from_end(period_end)
    fiscal_year = _fiscal_year_from_period_end(period_end)
    if doc_type == "160" and fiscal_year:
        return f"FY{fiscal_year}H1"
    if doc_type == "140":
        quarter_label = _quarter_label_from_document(document_meta)
        if fiscal_year and quarter_label:
            return f"FY{fiscal_year}{quarter_label}"
    date_match = re.search(r"(20\d{2}|19\d{2})[-/.]\d{1,2}[-/.]\d{1,2}", period_end)
    if date_match:
        return date_match.group(0).replace("/", "-").replace(".", "-")
    return _period_from_end(period_end)


def _period_from_end(value: Any) -> str:
    text = str(value or "")
    match = __import__("re").search(r"(20\d{2}|19\d{2})", text)
    if match:
        return f"FY{match.group(1)}"
    return "FYunknown"


def _fiscal_year_from_period_end(value: Any) -> str | None:
    text = str(value or "")
    match = re.search(r"(20\d{2}|19\d{2})", text)
    return match.group(1) if match else None


def _prior_period(period: str) -> str:
    match = __import__("re").search(r"(20\d{2}|19\d{2})", period)
    if not match:
        return "FYprior"
    return f"FY{int(match.group(1)) - 1}"


def _edinet_period_basis(period: str, document_meta: dict[str, Any]) -> str:
    text = str(period or "").strip()
    if re.fullmatch(r"FY(19\d{2}|20\d{2})H1", text):
        return "half_year"
    if re.fullmatch(r"FY(19\d{2}|20\d{2})Q[1-4]", text):
        return "quarter"
    if re.fullmatch(r"FY(19\d{2}|20\d{2})", text):
        return "annual"
    if text.endswith("-03-31") or text.endswith("-09-30"):
        return "quarter"
    if text.endswith("-06-30"):
        return "half_year"
    if text.endswith("-12-31"):
        return "annual"
    doc_type = str(document_meta.get("doc_type_code") or "")
    if doc_type == "120":
        return "annual"
    if doc_type in {"140", "160"}:
        return "quarter"
    return "unknown"


def _quarter_label_from_document(document_meta: dict[str, Any]) -> str | None:
    description = str(document_meta.get("doc_description") or "")
    compact = description.translate(str.maketrans("０１２３４５６７８９", "0123456789"))
    match = re.search(r"第\s*([13])\s*四半期", compact)
    if match:
        return f"Q{match.group(1)}"
    return None


def _elapsed(start: float) -> float:
    return round(time.perf_counter() - start, 3)
