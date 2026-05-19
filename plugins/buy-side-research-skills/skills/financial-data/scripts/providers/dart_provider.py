"""DART provider for Korea financial-data routes.

Deterministic extraction: identity, income_statement, balance_sheet, cash_flow.
"""
from __future__ import annotations

import datetime as dt
import hashlib
from html.parser import HTMLParser
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import tempfile
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from types import SimpleNamespace
from typing import Any
import zipfile
from urllib.parse import urlencode
from urllib.request import urlopen


PROVIDER = "dart-fss"
EXTRACTABLE = ["identity", "filing_index", "latest_full_filing", "income_statement", "balance_sheet", "cash_flow", "revenue_split"]
OPEN_DART_FINANCIALS_URL = "https://opendart.fss.or.kr/api/fnlttSinglAcntAll.json"
OPEN_DART_LIST_URL = "https://opendart.fss.or.kr/api/list.json"
OPEN_DART_DOCUMENT_URL = "https://opendart.fss.or.kr/api/document.xml"
FLOW_STATEMENTS = ("income_statement", "cash_flow")
QUARTERLY_REPORT_CODES = (
    ("Q1", "11013"),
    ("H1", "11012"),
    ("Q3", "11014"),
    ("FY", "11011"),
)


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
    periods_text = str(request.get("periods", "latest"))
    quarterly = _is_quarterly_request(periods_text)

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
    if "identity" in items or _needs_provider_context(items):
        try:
            years = _years_from_periods(periods_text)
            corp = _get_corp(identifier, dart, api_key, years)
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
    if corp and _needs_statements(items):
        try:
            years = _years_from_periods(periods_text)
            corp_code = getattr(corp, "corp_code", identifier)
            statements, sources, gaps = _fetch_open_dart_statements(api_key, corp_code, years, quarterly=quarterly)
            result["statement_sources"] = sources
            result.setdefault("data_gaps", []).extend(gaps)
            if quarterly:
                result.setdefault("data_gaps", []).append(
                    "quarterly_statement_scope: OpenDART Q1/H1/Q3 values may be cumulative reporting-period amounts"
                )
                derived = _derive_quarterly_flow_statements(statements)
                for derived_key, rows in derived.items():
                    if rows:
                        result[derived_key] = rows
            for item_key in ("income_statement", "balance_sheet", "cash_flow"):
                if item_key in items and statements.get(item_key):
                    result[item_key] = statements[item_key]
                    result["items_extracted"].append(item_key)
        except Exception as e:
            result["errors"].append(f"statement_extract: {e}")

    # --- filing index / latest full filing ---
    if corp and _needs_filing(items):
        try:
            years = _years_from_periods(periods_text)
            corp_code = getattr(corp, "corp_code", identifier)
            filings = _discover_periodic_filings(api_key, corp_code, years, quarterly=quarterly)
            if not filings:
                raise RuntimeError(f"periodic filing discovery failed for {corp_code} across years {years}")
            result["filing_documents"] = filings
            if "filing_index" in items:
                result["items_extracted"].append("filing_index")
            if "latest_full_filing" in items:
                filing = _get_filing_text(api_key, corp, filings[0])
                result["filing"] = filing
                if filing.get("status") == "fetched" and filing.get("markdown"):
                    result["items_extracted"].append("latest_full_filing")
                else:
                    result["errors"].append(f"latest_full_filing: {filing.get('error', 'markdown unavailable')}")
        except Exception as e:
            result["errors"].append(f"filing_extract: {e}")

    if "revenue_split" in items:
        result.setdefault("data_gaps", []).append("revenue_split: no stable free structured DART revenue split route")

    if result["items_extracted"]:
        non_identity = set(result["items_extracted"]) - {"identity"}
        result["status"] = "partial" if result["errors"] or (_needs_statements(items) and not non_identity) else "success"
    else:
        result["status"] = "provider-gap"
    return result


def _get_corp(identifier: str, dart, api_key: str, years: list[int]) -> Any:
    direct = _get_corp_from_open_dart(identifier, api_key, years)
    if direct is not None:
        return direct

    raise ValueError(f"DART: company not found for {identifier}")


def _get_corp_from_open_dart(identifier: str, api_key: str, years: list[int]) -> Any | None:
    clean = str(identifier).strip()
    if re.fullmatch(r"\d{8}", clean):
        return SimpleNamespace(corp_code=clean, stock_code=None, corp_name=clean)

    for bgn_de, end_de in _corp_lookup_windows(years):
        for corp_cls in ("Y", "K"):
            for page_no in range(1, 51):
                params = {
                    "crtfc_key": api_key,
                    "bgn_de": bgn_de,
                    "end_de": end_de,
                    "corp_cls": corp_cls,
                    "page_no": str(page_no),
                    "page_count": "100",
                }
                with urlopen(OPEN_DART_LIST_URL + "?" + urlencode(params), timeout=30) as response:
                    payload = json.loads(response.read().decode("utf-8"))
                for row in payload.get("list") or []:
                    if str(row.get("stock_code") or "").strip() == clean:
                        return SimpleNamespace(
                            corp_code=str(row.get("corp_code") or "").strip(),
                            stock_code=clean,
                            corp_name=str(row.get("corp_name") or "").strip(),
                        )
                if page_no >= int(payload.get("total_page") or page_no):
                    break
    return None


def _corp_lookup_windows(years: list[int]) -> list[tuple[str, str]]:
    today = dt.date.today()
    windows: list[tuple[dt.date, dt.date]] = [(today - dt.timedelta(days=90), today)]
    for fiscal_year in sorted(years, reverse=True):
        filing_year = fiscal_year + 1
        windows.extend([
            (dt.date(filing_year, 3, 1), dt.date(filing_year, 5, 31)),
            (dt.date(fiscal_year, 8, 1), dt.date(fiscal_year, 8, 31)),
            (dt.date(fiscal_year, 11, 1), dt.date(fiscal_year, 11, 30)),
            (dt.date(fiscal_year, 5, 1), dt.date(fiscal_year, 7, 31)),
        ])

    out: list[tuple[str, str]] = []
    seen = set()
    for start, end in windows:
        if start > today:
            continue
        end = min(end, today)
        key = (start.isoformat(), end.isoformat())
        if key not in seen:
            out.append((start.strftime("%Y%m%d"), end.strftime("%Y%m%d")))
            seen.add(key)
    return out


def _needs_statements(items: list[str]) -> bool:
    return bool({"income_statement", "balance_sheet", "cash_flow"} & set(items))


def _needs_filing(items: list[str]) -> bool:
    return bool({"filing_index", "latest_full_filing"} & set(items))


def _needs_provider_context(items: list[str]) -> bool:
    return _needs_statements(items) or _needs_filing(items)


def _years_from_periods(periods: str) -> list[int]:
    """Map request periods to report years."""
    years = [int(year) for year in re.findall(r"(20\d{2})", periods)]
    if len(years) >= 2:
        start_year, end_year = min(years), max(years)
        return list(range(start_year, end_year + 1))
    elif len(years) == 1:
        return [years[0]]
    today = dt.date.today()
    return list(range(today.year - 3, today.year + 1))


def _is_quarterly_request(periods: str | None) -> bool:
    token = re.sub(r"[^a-z0-9]+", "", str(periods or "").strip().lower())
    return token in {"latest4q", "last4q", "latest4quarters", "latestfourquarters", "quarterly"}


@contextmanager
def _suppress_progress_output():
    """Avoid dart-fss spinner output corrupting Windows GBK consoles."""
    sink = io.StringIO()
    with redirect_stdout(sink), redirect_stderr(sink):
        yield


def _fetch_open_dart_statements(api_key: str, corp_code: str, years: list[int],
                                quarterly: bool = False) -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, Any]], list[str]]:
    grouped: dict[str, dict[str, dict[str, Any]]] = {
        "income_statement": {},
        "balance_sheet": {},
        "cash_flow": {},
    }
    sources: list[dict[str, Any]] = []
    gaps: list[str] = []

    report_codes = QUARTERLY_REPORT_CODES if quarterly else (("FY", "11011"),)

    for year in years:
        for period_code, report_code in report_codes:
            rows = []
            used_fs_div = None
            for fs_div in ("CFS", "OFS"):
                payload = _open_dart_financials(api_key, corp_code, year, fs_div, report_code)
                period_rows = payload.get("list") or []
                if period_rows:
                    rows = period_rows
                    used_fs_div = fs_div
                    sources.append({
                        "year": year,
                        "period_code": period_code,
                        "reprt_code": report_code,
                        "fs_div": fs_div,
                        "row_count": len(period_rows),
                        "status": payload.get("status"),
                        "message": payload.get("message"),
                    })
                    break
            if not rows:
                gaps.append(f"financial_statements_{year}_{period_code}: OpenDART returned no CFS/OFS rows")
                continue
            _merge_open_dart_rows(grouped, rows, year, period_code, used_fs_div or "unknown")

    return ({key: list(value.values()) for key, value in grouped.items()}), sources, gaps


def _derive_quarterly_flow_statements(statements: dict[str, list[dict[str, Any]]]) -> dict[str, list[dict[str, Any]]]:
    derived: dict[str, list[dict[str, Any]]] = {}
    for statement in FLOW_STATEMENTS:
        rows = []
        for row in statements.get(statement, []):
            derived_row = _derive_quarterly_row(row)
            if derived_row:
                rows.append(derived_row)
        if rows:
            derived[f"{statement}_quarterly_derived"] = rows
    return derived


def _derive_quarterly_row(row: dict[str, Any]) -> dict[str, Any] | None:
    values = row.get("cumulative_values", {}) or {}
    by_year: dict[int, dict[str, int | float]] = {}
    for period, value in values.items():
        parsed = _parse_dart_period(str(period))
        if parsed is None:
            continue
        year, period_code = parsed
        by_year.setdefault(year, {})[period_code] = value

    derived_values: dict[str, int | float] = {}
    source_periods: dict[str, list[str]] = {}
    for year, year_values in sorted(by_year.items()):
        q1 = year_values.get("Q1")
        h1 = year_values.get("H1")
        q3_ytd = year_values.get("Q3")
        fy = year_values.get("FY")

        if q1 is not None:
            period = f"FY{year}Q1"
            derived_values[period] = q1
            source_periods[period] = [period]
        if h1 is not None and q1 is not None:
            period = f"FY{year}Q2"
            derived_values[period] = h1 - q1
            source_periods[period] = [f"FY{year}H1", f"FY{year}Q1"]
        if q3_ytd is not None and h1 is not None:
            period = f"FY{year}Q3"
            derived_values[period] = q3_ytd - h1
            source_periods[period] = [f"FY{year}Q3", f"FY{year}H1"]
        if fy is not None and q3_ytd is not None:
            period = f"FY{year}Q4"
            derived_values[period] = fy - q3_ytd
            source_periods[period] = [f"FY{year}", f"FY{year}Q3"]

    if not derived_values:
        return None

    derived_row = {
        "label": row.get("label"),
        "concept": row.get("concept"),
        "values": derived_values,
        "currency": row.get("currency"),
        "source_type": "official-api-derived",
        "provider": PROVIDER,
        "statement_name": row.get("statement_name"),
        "fs_div": row.get("fs_div"),
        "derivation": "quarter_from_cumulative",
        "source_periods": source_periods,
        "confidence": "model-ready-review",
    }
    return derived_row


def _parse_dart_period(period: str) -> tuple[int, str] | None:
    match = re.fullmatch(r"FY(20\d{2}|19\d{2})(Q1|H1|Q3)?", period)
    if not match:
        return None
    year = int(match.group(1))
    period_code = match.group(2) or "FY"
    return year, period_code


def _discover_periodic_filings(api_key: str, corp_code: str, years: list[int],
                               quarterly: bool = False) -> list[dict[str, Any]]:
    matches_by_receipt: dict[str, dict[str, Any]] = {}
    report_terms = ("분기보고서", "반기보고서", "사업보고서") if quarterly else ("사업보고서",)
    max_results = 4 if quarterly else 1

    for bgn_de, end_de in _corp_lookup_windows(years):
        for page_no in range(1, 21):
            payload = _open_dart_list(api_key, bgn_de, end_de, corp_code=corp_code, page_no=page_no)
            for row in payload.get("list") or []:
                report_name = str(row.get("report_nm") or "")
                if not any(term in report_name for term in report_terms):
                    continue
                receipt = str(row.get("rcept_no") or "").strip()
                if not receipt:
                    continue
                matches_by_receipt[receipt] = _filing_meta_from_list_row(row)
            if page_no >= int(payload.get("total_page") or page_no):
                break
        if len(matches_by_receipt) >= max_results:
            break

    ordered = sorted(
        matches_by_receipt.values(),
        key=lambda row: str(row.get("rcept_dt") or ""),
        reverse=True,
    )
    return ordered[:max_results]


def _open_dart_list(api_key: str, bgn_de: str, end_de: str, corp_code: str | None = None,
                    page_no: int = 1) -> dict[str, Any]:
    params = {
        "crtfc_key": api_key,
        "bgn_de": bgn_de,
        "end_de": end_de,
        "page_no": str(page_no),
        "page_count": "100",
    }
    if corp_code:
        params["corp_code"] = corp_code
    with urlopen(OPEN_DART_LIST_URL + "?" + urlencode(params), timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    status = str(payload.get("status") or "")
    if status in {"000", "013", "014"}:
        return payload
    raise RuntimeError(f"OpenDART list {bgn_de}-{end_de}: {status} {payload.get('message')}")


def _filing_meta_from_list_row(row: dict[str, Any]) -> dict[str, Any]:
    receipt = str(row.get("rcept_no") or "").strip()
    return {
        "rcept_no": receipt,
        "report_name": str(row.get("report_nm") or "").strip(),
        "corp_code": str(row.get("corp_code") or "").strip(),
        "corp_name": str(row.get("corp_name") or "").strip(),
        "stock_code": str(row.get("stock_code") or "").strip(),
        "filer_name": str(row.get("flr_nm") or "").strip(),
        "filing_date": str(row.get("rcept_dt") or "").strip(),
        "source_url": _dart_viewer_url(receipt),
    }


def _get_filing_text(api_key: str, corp: Any, filing_meta: dict[str, Any]) -> dict[str, Any]:
    receipt = str(filing_meta.get("rcept_no") or "").strip()
    if not receipt:
        return {"status": "error", "error": "missing OpenDART receipt number"}
    try:
        package_path = _download_document_zip(api_key, receipt)
        markdown = _extract_document_markdown(package_path, corp, filing_meta)
        if not markdown:
            return {
                "status": "error",
                "error": "OpenDART document package contained no readable XML/HTML text",
                "rcept_no": receipt,
                "local_path": str(package_path),
            }
        return {
            "rcept_no": receipt,
            "corp_code": filing_meta.get("corp_code") or getattr(corp, "corp_code", None),
            "corp_name": filing_meta.get("corp_name") or getattr(corp, "corp_name", None),
            "report_name": filing_meta.get("report_name"),
            "filing_date": filing_meta.get("filing_date"),
            "source_url": filing_meta.get("source_url") or _dart_viewer_url(receipt),
            "source_package_type": "OpenDART document.xml ZIP",
            "local_path": str(package_path),
            "text_length": len(markdown),
            "markdown_sha256": hashlib.sha256(markdown.encode("utf-8")).hexdigest(),
            "markdown": markdown,
            "status": "fetched",
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "rcept_no": receipt,
            "source_url": filing_meta.get("source_url") or _dart_viewer_url(receipt),
        }


def _download_document_zip(api_key: str, receipt: str) -> Path:
    safe_receipt = re.sub(r"[^A-Za-z0-9._-]+", "_", receipt)
    target_dir = Path(tempfile.gettempdir()) / "bsrs-dart-documents"
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / f"{safe_receipt}-document.zip"
    params = {"crtfc_key": api_key, "rcept_no": receipt}
    with urlopen(OPEN_DART_DOCUMENT_URL + "?" + urlencode(params), timeout=120) as response:
        content = response.read()
    target_path.write_bytes(content)
    if not zipfile.is_zipfile(target_path):
        preview = _decode_text(content[:500])
        raise RuntimeError(f"OpenDART document.xml response is not a ZIP file: {preview}")
    return target_path


def _extract_document_markdown(package_path: Path, corp: Any, filing_meta: dict[str, Any]) -> str:
    with zipfile.ZipFile(package_path) as package:
        text_names = [
            name for name in package.namelist()
            if name.lower().endswith((".xml", ".html", ".htm", ".xhtml"))
        ]
        sections = []
        for name in sorted(text_names, key=_dart_source_priority):
            raw = package.read(name)
            content = _decode_text(raw)
            text = _markup_to_text(content)
            if not text:
                continue
            sections.append(f"## Source File: {name}\n\n{text}")

    if not sections:
        return ""

    receipt = filing_meta.get("rcept_no")
    header = [
        "# OpenDART Filing Text",
        "",
        f"- Corp code: {filing_meta.get('corp_code') or getattr(corp, 'corp_code', '')}",
        f"- Corp name: {filing_meta.get('corp_name') or getattr(corp, 'corp_name', '')}",
        f"- Receipt No: {receipt}",
        f"- Report name: {filing_meta.get('report_name')}",
        f"- Filing date: {filing_meta.get('filing_date')}",
        "- Source package: OpenDART document.xml ZIP",
        f"- Source URL: {filing_meta.get('source_url') or _dart_viewer_url(str(receipt or ''))}",
        "",
    ]
    return "\n".join(header + sections) + "\n"


def _dart_source_priority(name: str) -> tuple[int, int, str]:
    normalized = name.replace("\\", "/").lower()
    audit_rank = 1 if "audit" in normalized else 0
    return (audit_rank, len(normalized), normalized)


def _decode_text(raw: bytes) -> str:
    for encoding in ("utf-8", "cp949", "euc-kr", "latin-1"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="ignore")


class _MarkupTextExtractor(HTMLParser):
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


def _markup_to_text(content: str) -> str:
    parser = _MarkupTextExtractor()
    parser.feed(content)
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


def _dart_viewer_url(receipt: str) -> str:
    return f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={receipt}" if receipt else ""


def _open_dart_financials(api_key: str, corp_code: str, year: int, fs_div: str, report_code: str) -> dict[str, Any]:
    params = {
        "crtfc_key": api_key,
        "corp_code": corp_code,
        "bsns_year": str(year),
        "reprt_code": report_code,
        "fs_div": fs_div,
    }
    with urlopen(OPEN_DART_FINANCIALS_URL + "?" + urlencode(params), timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    status = payload.get("status")
    if status == "000":
        return payload
    if status in {"013", "014"}:
        return payload
    raise RuntimeError(f"OpenDART {year} {fs_div}: {status} {payload.get('message')}")


def _merge_open_dart_rows(grouped: dict[str, dict[str, dict[str, Any]]],
                          records: list[dict[str, Any]], year: int, period_code: str, fs_div: str) -> None:
    period = f"FY{year}" if period_code == "FY" else f"FY{year}{period_code}"
    for rec in records:
        statement = _statement_key(str(rec.get("sj_div") or ""))
        if not statement:
            continue
        label = str(rec.get("account_nm") or rec.get("account_id") or "").strip()
        if not label:
            continue
        value = _clean_amount(rec.get("thstrm_amount"))
        if value is None:
            continue
        concept = str(rec.get("account_id") or label).strip()
        row = grouped[statement].setdefault(concept, {
            "label": label,
            "concept": concept,
            "values": {},
            "cumulative_values": {},
            "currency": rec.get("currency"),
            "source_type": "official-api",
            "provider": PROVIDER,
            "statement_name": rec.get("sj_nm"),
            "fs_div": fs_div,
            "period_basis": "report_period",
            "period_basis_by_period": {},
        })
        row["values"][period] = value
        cumulative_value = _clean_amount(rec.get("thstrm_add_amount"))
        if cumulative_value is None and (statement == "cash_flow" or period_code in {"Q1", "FY"}):
            cumulative_value = value
        if cumulative_value is not None:
            row["cumulative_values"][period] = cumulative_value
        row["period_basis_by_period"][period] = "cumulative_report_period" if period_code in {"H1", "Q3"} else "report_period"


def _statement_key(sj_div: str) -> str | None:
    if sj_div in {"IS", "CIS"}:
        return "income_statement"
    if sj_div == "BS":
        return "balance_sheet"
    if sj_div == "CF":
        return "cash_flow"
    return None


def _clean_amount(value: Any) -> int | float | None:
    if value is None:
        return None
    text = str(value).strip().replace(",", "")
    if not text or text in {"-", "--"}:
        return None
    try:
        return int(text)
    except ValueError:
        try:
            return float(text)
        except ValueError:
            return None
