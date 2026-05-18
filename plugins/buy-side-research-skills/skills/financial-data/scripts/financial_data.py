#!/usr/bin/env python3
"""Fetch deterministic, source-tracked financial evidence packs.

Only structured, verifiable data is extracted by code. Narrative analysis,
segment interpretation, and business insights are left for LLM/research skills
at query time.

Output contract:
  _raw/.../provider_payload.json
  _raw/.../identity-source.json
  _raw/.../filings/<filing-id>/source.*
  _raw/.../filings/<filing-id>/source-metadata.json
  _raw/.../filings/<filing-id>/source.sha256

  _cache/.../manifest.json
  _cache/.../identity.json
  _cache/.../filing-index.json
  _cache/.../financials.normalized.json
  _cache/.../financials.md
  _cache/.../full-filing.md
  _cache/.../full-filing.chunks.jsonl
  _cache/.../full-filing.index.json
  _cache/.../completeness.json
  _cache/.../source-map.json
  _cache/.../cross-check.json

Modeling input aliases:
  topics/company/<company-slug>/_cache/financial-data/financial-data-summary.md
  topics/company/<company-slug>/_cache/financial-data/internal/evidence-pack.json
  topics/company/<company-slug>/_cache/financial-data/internal/actuals-resolved.json
  topics/company/<company-slug>/_cache/financial-data/internal/full-filing.md
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import sys
from typing import Any


DEFAULT_ITEMS = ["identity", "filing_index", "latest_full_filing", "income_statement", "balance_sheet", "cash_flow"]

SUPPORTED_MODES = ("latest_core", "five_years", "filing_only", "cross_check", "snapshot")

# Third-party normalized-data providers: their output is never model-ready
THIRD_PARTY_PROVIDERS = {"akshare"}
OFFICIAL_EVIDENCE_PROVIDERS = {"edgartools", "dart-fss", "edinet-tools", "openesef"}

PROVIDER_MODULES = {
    "us": "sec_provider",
    "cn": "akshare_provider",
    "hk": "akshare_provider",
    "jp": "edinet_provider",
    "kr": "dart_provider",
    "eu": "openesef_provider",
}


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def run_id() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def module_available(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def slugify(value: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", value.strip().lower())
    return value.strip("-") or "unknown"


def sha256_file(path: Path) -> str:
    d = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            d.update(chunk)
    return d.hexdigest()


def dependency_matrix() -> dict[str, Any]:
    return {
        "python": {"version": sys.version.split()[0], "executable": sys.executable},
        "packages": {
            "edgartools": {"available": module_available("edgar"), "install_hint": "pip install edgartools"},
            "akshare": {"available": module_available("akshare"), "install_hint": "pip install akshare"},
            "edinet-tools": {"available": module_available("edinet_tools"), "install_hint": "pip install edinet-tools"},
            "dart-fss": {"available": module_available("dart_fss"), "install_hint": "pip install dart-fss"},
            "openesef": {"available": module_available("openesef"), "install_hint": "pip install openesef"},
        },
        "env": {
            "EDGAR_IDENTITY": {"configured": bool(os.getenv("EDGAR_IDENTITY"))},
            "DART_API_KEY": {"configured": bool(os.getenv("DART_API_KEY"))},
            "EDINET_API_KEY": {"configured": bool(os.getenv("EDINET_API_KEY"))},
        },
    }


def discover_workspace(source: Path | None = None) -> Path:
    candidates = [source or Path.cwd(), Path.cwd()]
    for candidate in candidates:
        current = candidate if candidate.is_dir() else candidate.parent
        for parent in [current, *current.parents]:
            if (parent / "topics").is_dir():
                return parent
    raise RuntimeError("Could not discover workspace. Pass --workspace or run init-workspace first.")


def ensure_company_topic(workspace: Path, company_slug: str) -> Path:
    tp = workspace / "topics" / "company" / company_slug
    idx = tp / "index.md"
    if not idx.exists():
        raise RuntimeError(f"Company topic does not exist. Run new-session first. Missing: {idx}")
    return tp


def load_provider(market: str):
    pdir = Path(__file__).resolve().parent / "providers"
    if str(pdir) not in sys.path:
        sys.path.insert(0, str(pdir))
    mn = PROVIDER_MODULES.get(market)
    if not mn:
        raise RuntimeError(f"Unsupported market: {market}")
    return importlib.import_module(mn)


# ---------------------------------------------------------------------------
# Central normalizer
# ---------------------------------------------------------------------------
CONFIDENCE_ORDER = {"model-ready": 0, "evidence-ready": 1, "provider-normalized-review": 2, "partial": 3, "provider-gap": 4, "unavailable": 5, "failed": 5}

# Policy: providers must fail honestly (provider_gap) when dependencies, credentials,
# or market coverage are missing rather than returning empty partial results.

DEFAULT_ITEMS_REQUIRE = (
    "identity",
    "filing_index",
    "latest_full_filing",
    "income_statement",
    "balance_sheet",
    "cash_flow",
)


def normalize_result(provider_result: dict[str, Any], request: dict[str, Any]) -> dict[str, Any]:
    """Central normalizer: standardize provider output into the canonical pack format."""
    provider = provider_result.get("provider", "unknown")
    provider_status = provider_result.get("status", "provider-gap")

    company = provider_result.get("company", {})
    financials_raw = {}
    for key in ("income_statement", "balance_sheet", "cash_flow"):
        val = provider_result.get(key)
        if val:
            financials_raw[key] = val
    financials_raw = filter_financials_by_period(financials_raw, request.get("periods", "latest"))

    filing_info = provider_result.get("filing", {}) or {}
    errors = list(provider_result.get("errors", []))
    provider_error = provider_result.get("error")
    if provider_error:
        errors.append(str(provider_error))

    # Build completeness from what was actually extracted
    declared_extracted = provider_result.get("items_extracted", request.get("items", []))
    extracted = [item for item in declared_extracted if item_materialized(item, provider_result, financials_raw)]
    requested_items = request.get("items", [])
    completeness_items = []
    for item in DEFAULT_ITEMS_REQUIRE:
        if item in extracted:
            status_c = confidence_determine(item, provider_result)
        elif item in requested_items:
            status_c = "provider-gap"
        else:
            status_c = "unavailable"
        completeness_items.append({
            "data_item": item, "status": status_c,
            "source_provider": provider, "period_coverage": request.get("periods", "latest"),
            "model_usable": status_c,
        })

    status = derive_pack_status(provider_status, requested_items, extracted, errors)

    return {
        "provider": provider,
        "status": status,
        "provider_status": provider_status,
        "company": company,
        "financials_raw": financials_raw,
        "filing": filing_info,
        "completeness": completeness_items,
        "errors": errors,
        "items_extracted": extracted,
        "provider_payload": provider_result,
    }


def filter_financials_by_period(financials: dict[str, Any], periods: str | None) -> dict[str, Any]:
    if not financials or not periods or periods == "latest":
        return financials

    allowed_years = parse_fiscal_year_filter(str(periods))
    if not allowed_years:
        return financials

    filtered: dict[str, Any] = {}
    for statement, rows in financials.items():
        kept_rows = []
        for row in rows:
            values = row.get("values", {}) if isinstance(row, dict) else {}
            kept_values = {
                period: value
                for period, value in values.items()
                if fiscal_year_from_label(period) in allowed_years
            }
            if kept_values:
                kept = dict(row)
                kept["values"] = kept_values
                kept_rows.append(kept)
        filtered[statement] = kept_rows
    return filtered


def parse_fiscal_year_filter(periods: str) -> set[int]:
    years = [int(year) for year in re.findall(r"FY\s*(20\d{2}|19\d{2})", periods, flags=re.IGNORECASE)]
    if not years:
        years = [int(year) for year in re.findall(r"\b(20\d{2}|19\d{2})\b", periods)]
    if not years:
        return set()
    if len(years) >= 2:
        start, end = min(years[0], years[-1]), max(years[0], years[-1])
        return set(range(start, end + 1))
    return {years[0]}


def fiscal_year_from_label(label: str) -> int | None:
    match = re.search(r"\b(20\d{2}|19\d{2})\b", str(label))
    if not match:
        return None
    return int(match.group(1))


def item_materialized(item: str, provider_result: dict[str, Any],
                      financials_raw: dict[str, Any] | None = None) -> bool:
    """Return true only when a declared extracted item has real payload behind it."""
    if item == "identity":
        return bool(provider_result.get("company"))
    if item == "filing_index":
        filing = provider_result.get("filing", {}) or {}
        return bool(filing) and filing.get("status") != "error"
    if item == "latest_full_filing":
        filing = provider_result.get("filing", {}) or {}
        return bool(filing.get("markdown"))
    if item in ("income_statement", "balance_sheet", "cash_flow"):
        if financials_raw is not None:
            return bool(financials_raw.get(item))
        return bool(provider_result.get(item))
    return False


def confidence_determine(item: str, provider_result: dict[str, Any]) -> str:
    """Return the canonical confidence/status tier for a materialized item."""
    provider = provider_result.get("provider", "")
    if provider in THIRD_PARTY_PROVIDERS:
        return "provider-normalized-review"
    if provider in OFFICIAL_EVIDENCE_PROVIDERS and item in ("identity", "filing_index", "latest_full_filing"):
        return "evidence-ready"
    if item in ("income_statement", "balance_sheet", "cash_flow"):
        return "model-ready" if provider_result.get(item) else "provider-gap"
    return "provider-gap"


def derive_pack_status(provider_status: str, requested_items: list[str],
                       extracted_items: list[str], errors: list[str]) -> str:
    """Derive truthful top-level pack status from materialized outputs, not provider optimism."""
    if provider_status in {"dependency-gap", "credential-gap", "failed"}:
        return provider_status

    extracted = set(extracted_items)
    if not extracted:
        return "provider-gap"

    requested = set(requested_items)
    non_identity_requested = requested - {"identity"}
    non_identity_extracted = extracted - {"identity"}

    if provider_status == "partial":
        return "partial"
    if errors:
        return "partial"
    if non_identity_requested and not non_identity_extracted:
        return "partial"
    return "success"


# ---------------------------------------------------------------------------
# Output writers
# ---------------------------------------------------------------------------
def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_md(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def build_financials_markdown(financials: dict[str, Any]) -> str:
    lines = ["# Financial Data Evidence Pack", "", "## Income Statement", ""]
    for row in financials.get("income_statement", []):
        lbl = row.get("label", "")
        vals = row.get("values", {})
        if vals:
            periods_str = ", ".join(f"{p}: {v}" for p, v in sorted(vals.items()) if v is not None)
            lines.append(f"- {lbl}: {periods_str}")
    lines.extend(["", "## Balance Sheet", ""])
    for row in financials.get("balance_sheet", []):
        lbl = row.get("label", "")
        vals = row.get("values", {})
        if vals:
            periods_str = ", ".join(f"{p}: {v}" for p, v in sorted(vals.items()) if v is not None)
            lines.append(f"- {lbl}: {periods_str}")
    lines.extend(["", "## Cash Flow", ""])
    for row in financials.get("cash_flow", []):
        lbl = row.get("label", "")
        vals = row.get("values", {})
        if vals:
            periods_str = ", ".join(f"{p}: {v}" for p, v in sorted(vals.items()) if v is not None)
            lines.append(f"- {lbl}: {periods_str}")
    return "\n".join(lines)


def build_financial_data_summary(evidence_pack: dict[str, Any],
                                 actuals_resolved: dict[str, Any],
                                 internal_dir: Path) -> str:
    """Build the single public Markdown entry for financial-data outputs."""
    manifest = evidence_pack.get("manifest", {})
    identity = evidence_pack.get("identity", {})
    filing = evidence_pack.get("filing", {})
    completeness = evidence_pack.get("completeness", [])
    cross_check = evidence_pack.get("cross_check", {})
    statements = actuals_resolved.get("statements", {}) or {}
    company_name = identity.get("name") or identity.get("company_name") or manifest.get("company_slug", "unknown")
    ticker = identity.get("ticker") or manifest.get("identifier", "")
    status = cross_check.get("status") or manifest.get("status", "unknown")

    lines = [
        f"# {company_name} Financial Data Summary",
        "",
        "**Conclusion**",
        "",
        f"- Status: `{status}`",
        f"- Market / identifier: `{manifest.get('market', 'unknown')}` / `{manifest.get('identifier', ticker)}`",
        f"- Provider: `{manifest.get('provider', evidence_pack.get('source_provider', 'unknown'))}`",
        f"- Period filter: `{manifest.get('periods', 'latest')}`",
        f"- Latest run cache: `{evidence_pack.get('latest_run_cache_path', '')}`",
        f"- Internal machine data: `{internal_dir.name}/`",
        "",
        "## Filing",
        "",
        f"- Filing status: `{filing.get('status', 'unavailable')}`",
        f"- Filing date: `{filing.get('filing_date') or ''}`",
        f"- Accession / document id: `{filing.get('accession_number') or filing.get('document_id') or ''}`",
        f"- Full filing retained internally: `{bool(filing.get('has_full_filing_markdown'))}`",
        "",
        "## Completeness Matrix",
        "",
        "| Data item | Status | Provider | Period coverage | Model usable | Caveat |",
        "|---|---|---|---|---|---|",
    ]
    for item in completeness:
        lines.append(
            "| {data_item} | {status} | {source_provider} | {period_coverage} | {model_usable} | {caveat} |".format(
                data_item=item.get("data_item", ""),
                status=item.get("status", ""),
                source_provider=item.get("source_provider", ""),
                period_coverage=item.get("period_coverage", ""),
                model_usable=item.get("model_usable", ""),
                caveat=item.get("caveat", ""),
            )
        )

    lines.extend(["", "## Structured Actuals", ""])
    if statements:
        for statement in ("income_statement", "balance_sheet", "cash_flow"):
            rows = statements.get(statement, [])
            periods = sorted({
                period
                for row in rows
                for period in (row.get("values", {}) if isinstance(row, dict) else {}).keys()
            })
            lines.append(f"- `{statement}`: {len(rows)} rows; periods: {', '.join(periods) if periods else 'none'}")
    else:
        lines.append("- No structured statement rows were materialized.")

    unmapped = actuals_resolved.get("unmapped_items", [])
    lines.extend(["", "## Model Input Policy", ""])
    lines.append("- Public surface is Markdown-only: this summary is the default file for humans and LLMs.")
    lines.append("- Machine inputs are under `internal/`; modeling scripts should read JSON there and must not parse this Markdown for numbers.")
    lines.append("- Missing or unmapped actuals must stay blank and be flagged for review; never convert them to zero.")
    if unmapped:
        lines.append("- Unmapped / unavailable items:")
        for item in unmapped:
            lines.append(f"  - `{item.get('data_item')}`: `{item.get('status')}`")
    else:
        lines.append("- No unavailable default core items were reported.")

    if cross_check.get("errors"):
        lines.extend(["", "## Errors / Caveats", ""])
        for err in cross_check.get("errors", []):
            lines.append(f"- {err}")

    return "\n".join(lines) + "\n"


def chunk_full_filing(text: str, max_chars: int = 12000) -> list[dict[str, Any]]:
    """Split full filing text into overlapping chunks for retrieval."""
    chunks = []
    for i, start in enumerate(range(0, len(text), max_chars)):
        chunk_text = text[start:start + max_chars]
        chunks.append({
            "chunk_id": f"chunk_{i:04d}",
            "start_char": start,
            "end_char": start + len(chunk_text),
            "length": len(chunk_text),
            "content": chunk_text,
        })
    return chunks


# ---------------------------------------------------------------------------
# Source-map builder
# ---------------------------------------------------------------------------
def _build_source_map(provider: str, filing: dict, financials: dict,
                      completeness: list[dict[str, Any]]) -> dict:
    """Build source-map.json tracing each data dimension to its source."""
    entries = []
    completeness_by_item = {item["data_item"]: item for item in completeness}

    # Filing-level source
    if filing and filing.get("status") != "error":
        entries.append({
            "data_item": "filing_index",
            "provider": provider,
            "source_id": filing.get("accession_number", ""),
            "filing_date": filing.get("filing_date", ""),
            "filing_url": filing.get("filing_url", ""),
            "confidence": completeness_by_item.get("filing_index", {}).get("status", "provider-gap"),
        })
        if filing.get("markdown"):
            entries.append({
                "data_item": "latest_full_filing",
                "provider": provider,
                "source_id": filing.get("accession_number", ""),
                "sha256": filing.get("markdown_sha256", ""),
                "confidence": completeness_by_item.get("latest_full_filing", {}).get("status", "provider-gap"),
            })

    # Statement-level source
    for stmt_type in ("income_statement", "balance_sheet", "cash_flow"):
        rows = financials.get(stmt_type, [])
        entry = {
            "data_item": stmt_type,
            "provider": provider,
            "record_count": len(rows),
            "confidence": completeness_by_item.get(stmt_type, {}).get("status", "provider-gap"),
        }
        if rows:
            entry["source_id"] = filing.get("accession_number", "")
        entries.append(entry)

    return {"entries": entries, "source_provider": provider}


# ---------------------------------------------------------------------------
# Canonical pack writer
# ---------------------------------------------------------------------------
def write_canonical_pack(args: argparse.Namespace, normalized: dict[str, Any],
                         workspace: Path, rid: str) -> dict[str, Any]:
    company_slug = slugify(args.company_slug)
    canonical_id = slugify(args.canonical_id or args.identifier)
    topic_path = ensure_company_topic(workspace, company_slug)
    rel_tail = Path("datasets") / "financial-data" / args.market / canonical_id / rid
    raw_dir = topic_path / "_raw" / rel_tail
    cache_dir = topic_path / "_cache" / rel_tail
    raw_dir.mkdir(parents=True, exist_ok=False)
    cache_dir.mkdir(parents=True, exist_ok=False)

    provider = normalized["provider"]
    status = normalized["status"]
    company = normalized["company"]
    financials = normalized["financials_raw"]
    filing = normalized["filing"]

    # _raw output
    write_json(raw_dir / "provider_payload.json", normalized["provider_payload"])
    write_raw_evidence_pack(raw_dir, provider, company, filing)

    # _cache output
    manifest = {
        "schema_version": 2, "generated_at_utc": utc_now(), "run_id": rid,
        "output_scope": args.output_scope, "market": args.market,
        "identifier": args.identifier, "identifier_type": args.identifier_type,
        "company_slug": args.company_slug, "canonical_id": canonical_id,
        "periods": args.periods, "mode": getattr(args, "mode", "latest_core"),
        "provider": provider, "provider_status": normalized["provider_status"], "status": status,
    }
    identity_payload = company if company else {"identifier": args.identifier}
    write_json(cache_dir / "manifest.json", manifest)
    write_json(cache_dir / "identity.json", identity_payload)

    filing_md = ""
    if filing and filing.get("status") != "error":
        write_json(cache_dir / "filing-index.json", filing)
        filing_md = filing.get("markdown", "")
        if filing_md:
            write_md(cache_dir / "full-filing.md", filing_md)
            chunks = chunk_full_filing(filing_md)
            write_jsonl(cache_dir / "full-filing.chunks.jsonl", chunks)
            write_json(cache_dir / "full-filing.index.json", {
                "source": filing.get("source_url"),
                "total_chars": len(filing_md),
                "num_chunks": len(chunks),
                "chunk_size": 12000,
            })

    if financials:
        write_json(cache_dir / "financials.normalized.json", financials)
        write_md(cache_dir / "financials.md", build_financials_markdown(financials))
    else:
        write_json(cache_dir / "financials.normalized.json", [])
        write_md(cache_dir / "financials.md", "# No structured financials extracted.\n")

    write_json(cache_dir / "completeness.json", {"items": normalized["completeness"], "status": status})
    cross_check = {
        "status": status,
        "provider_status": normalized["provider_status"],
        "errors": normalized["errors"],
        "items_extracted": normalized["items_extracted"],
    }
    write_json(cache_dir / "cross-check.json", cross_check)
    source_map = _build_source_map(provider, filing, financials, normalized["completeness"])
    write_json(cache_dir / "source-map.json", source_map)

    write_modeling_input_aliases(
        topic_path=topic_path,
        raw_dir=raw_dir,
        cache_dir=cache_dir,
        manifest=manifest,
        identity=identity_payload,
        filing=filing,
        filing_md=filing_md,
        financials=financials,
        completeness=normalized["completeness"],
        source_map=source_map,
        cross_check=cross_check,
    )

    return {
        "raw": str(raw_dir), "cache": str(cache_dir),
        "financial_data_pack_path": str(cache_dir),
        "financial_data_summary_path": str(topic_path / "_cache" / "financial-data" / "financial-data-summary.md"),
        "financial_data_internal_path": str(topic_path / "_cache" / "financial-data" / "internal"),
    }


def write_modeling_input_aliases(topic_path: Path, cache_dir: Path, manifest: dict[str, Any],
                                 raw_dir: Path,
                                 identity: dict[str, Any], filing: dict[str, Any],
                                 filing_md: str, financials: dict[str, Any],
                                 completeness: list[dict[str, Any]], source_map: dict[str, Any],
                                 cross_check: dict[str, Any]) -> None:
    """Write stable latest-input files for driver-map and modeling skills.

    These aliases do not replace the run-id pack. The public surface is a
    single Markdown summary; machine-readable inputs live under internal/.
    """
    modeling_dir = topic_path / "_cache" / "financial-data"
    internal_dir = modeling_dir / "internal"
    modeling_dir.mkdir(parents=True, exist_ok=True)
    internal_dir.mkdir(parents=True, exist_ok=True)

    evidence_pack = {
        "schema_version": 1,
        "generated_at_utc": utc_now(),
        "latest_run_cache_path": str(cache_dir),
        "latest_raw_evidence_path": str(raw_dir),
        "manifest": manifest,
        "identity": identity,
        "filing": {
            "status": filing.get("status", "unavailable") if filing else "unavailable",
            "accession_number": filing.get("accession_number") if filing else None,
            "document_id": filing.get("document_id") if filing else None,
            "filing_date": filing.get("filing_date") if filing else None,
            "source_url": filing.get("filing_url", filing.get("source_url")) if filing else None,
            "has_full_filing_markdown": bool(filing_md),
        },
        "completeness": completeness,
        "source_map": source_map,
        "cross_check": cross_check,
    }
    write_json(internal_dir / "evidence-pack.json", evidence_pack)

    actuals_resolved = {
        "schema_version": 1,
        "generated_at_utc": utc_now(),
        "latest_run_cache_path": str(cache_dir),
        "status": cross_check.get("status", "unknown"),
        "resolution_policy": {
            "missing_or_unmapped": "leave_blank_and_flag_review",
            "never_fill_missing_with_zero": True,
            "model_input_gate": "use completeness/source_map before workbook population",
        },
        "statements": financials or {},
        "completeness": completeness,
        "source_map": source_map,
        "unmapped_items": [
            item for item in completeness
            if item.get("status") in {"provider-gap", "unavailable", "failed"}
        ],
    }
    write_json(internal_dir / "actuals-resolved.json", actuals_resolved)

    write_json(internal_dir / "manifest.json", manifest)
    write_json(internal_dir / "identity.json", identity)
    write_json(internal_dir / "completeness.json", {"items": completeness, "status": cross_check.get("status", "unknown")})
    write_json(internal_dir / "source-map.json", source_map)
    write_json(internal_dir / "cross-check.json", cross_check)
    write_json(internal_dir / "financials.normalized.json", financials or {})
    write_md(internal_dir / "financials.md", build_financials_markdown(financials) if financials else "# No structured financials extracted.\n")
    write_json(internal_dir / "raw-evidence.json", {
        "latest_raw_evidence_path": str(raw_dir),
        "latest_run_cache_path": str(cache_dir),
    })

    if filing:
        write_json(internal_dir / "filing-index.json", filing)

    if filing_md:
        write_md(internal_dir / "full-filing.md", filing_md)
        chunks = chunk_full_filing(filing_md)
        write_jsonl(internal_dir / "full-filing.chunks.jsonl", chunks)
        write_json(internal_dir / "full-filing.index.json", {
            "source": filing.get("source_url") if filing else None,
            "total_chars": len(filing_md),
            "num_chunks": len(chunks),
            "chunk_size": 12000,
        })
    else:
        write_md(internal_dir / "full-filing.md", "# Full filing unavailable\n\nNo full filing markdown was materialized for the latest financial-data run.\n")

    write_md(
        modeling_dir / "financial-data-summary.md",
        build_financial_data_summary(evidence_pack, actuals_resolved, internal_dir),
    )

    for legacy_name in ("evidence-pack.json", "actuals-resolved.json", "full-filing.md"):
        legacy_path = modeling_dir / legacy_name
        if legacy_path.exists() and legacy_path.is_file():
            legacy_path.unlink()


def write_raw_evidence_pack(raw_dir: Path, provider: str, company: dict[str, Any],
                            filing: dict[str, Any]) -> None:
    """Persist deterministic raw evidence files when real source material exists."""
    write_json(raw_dir / "identity-source.json", {
        "provider": provider,
        "company": company,
        "captured_at_utc": utc_now(),
        "status": "available" if company else "unavailable",
    })

    if not filing or filing.get("status") == "error":
        return

    filing_id = _filing_id(provider, filing)
    filing_dir = raw_dir / "filings" / filing_id
    filing_dir.mkdir(parents=True, exist_ok=True)

    source_path = _materialize_raw_source(filing_dir, filing)
    if not source_path:
        return

    write_json(filing_dir / "source-metadata.json", {
        "provider": provider,
        "filing_id": filing_id,
        "status": filing.get("status", "fetched"),
        "filing_url": filing.get("filing_url", filing.get("source_url")),
        "local_path": filing.get("local_path"),
        "accession_number": filing.get("accession_number"),
        "edinet_code": filing.get("edinet_code"),
        "doc_type": filing.get("doc_type"),
        "source_file": source_path.name,
    })
    (filing_dir / "source.sha256").write_text(sha256_file(source_path) + "\n", encoding="utf-8")


def _filing_id(provider: str, filing: dict[str, Any]) -> str:
    candidates = [
        filing.get("accession_number"),
        filing.get("document_id"),
        filing.get("edinet_code"),
        filing.get("corp_code"),
        filing.get("source_sha256"),
        filing.get("markdown_sha256"),
        provider,
    ]
    for candidate in candidates:
        if candidate:
            return slugify(str(candidate))
    return "unknown-filing"


def _materialize_raw_source(filing_dir: Path, filing: dict[str, Any]) -> Path | None:
    local_path = filing.get("local_path")
    if local_path:
        candidate = Path(str(local_path)).expanduser()
        if candidate.exists() and candidate.is_file():
            target = filing_dir / f"source{candidate.suffix or '.bin'}"
            shutil.copyfile(candidate, target)
            return target

    markdown = filing.get("markdown")
    if markdown:
        target = filing_dir / "source.md"
        write_md(target, markdown)
        return target

    source_url = filing.get("filing_url") or filing.get("source_url")
    if source_url:
        target = filing_dir / "source.url.txt"
        write_md(target, str(source_url) + "\n")
        return target
    return None


def write_jsonl(path: Path, items: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for item in items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------------------
# Snapshot writer
# ---------------------------------------------------------------------------
def write_snapshot(args: argparse.Namespace, normalized: dict[str, Any],
                  workspace: Path, rid: str) -> dict[str, Any]:
    if not args.topic:
        raise RuntimeError("--topic required for snapshot")
    tp = workspace / "topics" / args.topic
    if not (tp / "index.md").exists():
        raise RuntimeError(f"Topic does not exist: {tp}")
    sd = tp / "_cache" / "financial-data-snapshot" / rid
    sd.mkdir(parents=True, exist_ok=False)
    summary = {
        "run_id": rid, "generated_at_utc": utc_now(),
        "market": args.market, "identifier": args.identifier,
        "status": normalized["status"],
    }
    write_json(sd / "peer-completeness.json", summary)
    write_md(sd / "snapshot-index.md", f"# Financial Data Snapshot\n\nmarket: {args.market}\nidentifier: {args.identifier}\n")
    return {"cache": str(sd)}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Fetch financial data evidence packs.")
    p.add_argument("--check-deps", action="store_true")
    p.add_argument("--workspace")
    p.add_argument("--output-scope", choices=("canonical_company", "current_topic_snapshot"), default="canonical_company")
    p.add_argument("--company-slug")
    p.add_argument("--topic")
    p.add_argument("--market", choices=("us", "cn", "hk", "jp", "kr", "eu"), help="Market route")
    p.add_argument("--identifier", help="Ticker, CIK, filing URL, or market-specific identifier")
    p.add_argument("--identifier-type", default="ticker", choices=("ticker", "isin", "lei", "cik", "edinet_code", "dart_corp_code", "filing_url", "local_esef_package"))
    p.add_argument("--canonical-id")
    p.add_argument("--periods", default="latest")
    p.add_argument("--items", default=",".join(DEFAULT_ITEMS), help=f"Comma-separated. Default: {','.join(DEFAULT_ITEMS)}")
    p.add_argument("--mode", choices=SUPPORTED_MODES, default="latest_core")
    p.add_argument("--source-mode", choices=("auto", "filing_only", "provider_normalized"), default="auto")
    p.add_argument("--financial-data-pack-path")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    if args.check_deps:
        print(json.dumps(dependency_matrix(), ensure_ascii=False, indent=2))
        return 0

    if not args.market or not args.identifier:
        print(json.dumps({"status": "failed", "error": "--market and --identifier required"}, ensure_ascii=False, indent=2))
        return 1
    if args.output_scope == "canonical_company" and not args.company_slug:
        print(json.dumps({"status": "failed", "error": "--company-slug required for canonical_company"}, ensure_ascii=False, indent=2))
        return 1

    try:
        workspace = Path(args.workspace).expanduser().resolve() if args.workspace else discover_workspace()
        provider = load_provider(args.market)
        items = [i.strip() for i in str(args.items).split(",") if i.strip()]
        request = {k: getattr(args, k) for k in ("identifier", "identifier_type", "periods", "source_mode", "market")}
        request["items"] = items
        provider_result = provider.fetch(request)
        normalized = normalize_result(provider_result, request)
        rid = run_id()
        if args.output_scope == "canonical_company":
            output = write_canonical_pack(args, normalized, workspace, rid)
        else:
            output = write_snapshot(args, normalized, workspace, rid)

        print(json.dumps({
            "status": normalized["status"],
            "provider": normalized["provider"],
            "extracted": normalized["items_extracted"],
            "errors": normalized["errors"],
            "completeness": normalized["completeness"],
            "output": output,
        }, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}, ensure_ascii=False, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
