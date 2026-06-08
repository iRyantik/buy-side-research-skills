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
  industry/<industry>/companies/<ticker>/_cache/financial-data/financial-data-summary.md
  industry/<industry>/companies/<ticker>/_cache/financial-data/internal/evidence-pack.json
  industry/<industry>/companies/<ticker>/_cache/financial-data/internal/actuals-resolved.json
  industry/<industry>/companies/<ticker>/_cache/financial-data/internal/full-filing.md
"""

from __future__ import annotations

import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

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


DEFAULT_ITEMS = ["identity", "filing_index", "latest_full_filing", "income_statement", "balance_sheet", "cash_flow", "revenue_split"]
FINANCIAL_OUTPUT_KEYS = (
    "income_statement",
    "balance_sheet",
    "cash_flow",
    "revenue_split",
    "income_statement_quarterly_derived",
    "cash_flow_quarterly_derived",
)

SUPPORTED_MODES = ("latest_core", "five_years", "filing_only", "cross_check", "snapshot", "lite", "full")

# Third-party normalized-data providers: their output is never model-ready
THIRD_PARTY_PROVIDERS = {"akshare", "finmind"}
OFFICIAL_EVIDENCE_PROVIDERS = {"edgartools", "dart-fss", "edinet-tools", "openesef"}

# Lite/full field boundaries
LITE_FIELDS = {
    "income_statement": {
        "revenue", "cogs", "gross_profit", "sg_and_a", "r_and_d",
        "operating_income", "ebit", "ebitda", "interest_expense",
        "income_tax", "net_income", "eps",
    },
    "balance_sheet": {
        "cash", "accounts_receivable", "inventory",
        "total_assets", "total_equity", "total_debt",
    },
    "cash_flow": {
        "operating_cf", "capex", "dividends_paid",
    },
    "supplementary": {
        "order_backlog", "orders", "employees",
    },
}

FULL_EXTRA_FIELDS = {
    "income_statement": {
        "pre_tax_income", "sbc", "d_and_a", "amortization",
    },
    "balance_sheet": {
        "short_term_debt", "long_term_debt", "goodwill", "intangible_assets",
        "total_current_assets", "total_current_liabilities", "bonds_payable",
    },
    "cash_flow": {
        "d_and_a", "buybacks", "free_cash_flow",
    },
    "supplementary": {
        "installed_base", "arr", "nrr", "grr", "churn",
        "customer_count", "production_volume", "utilization_pct",
    },
}

# ---------------------------------------------------------------------------
# Concept mapping: parse statement-line-items.md → {concept_alias: standard_field}
# ---------------------------------------------------------------------------
_concept_map_cache = None

# Standard field name aliases: canonical name / variant → LITE_FIELDS-compatible key
_FIELD_ALIASES = {
    "revenue": "revenue", "sales": "revenue", "cogs": "cogs",
    "cost_of_revenue": "cogs", "cost_of_goods_sold": "cogs",
    "gross_profit": "gross_profit", "sg&a": "sg_and_a", "r&d": "r_and_d",
    "operating_income": "operating_income", "ebit": "ebit", "ebitda": "ebitda",
    "interest_expense": "interest_expense", "income_tax": "income_tax",
    "pre_tax_income": "pre_tax_income", "pre-tax_income": "pre_tax_income",
    "net_income": "net_income", "eps": "eps", "sbc": "sbc",
    "d&a": "d_and_a", "d_and_a": "d_and_a", "amortization": "amortization",
    "cash": "cash", "accounts_receivable": "accounts_receivable",
    "inventory": "inventory", "total_current_assets": "total_current_assets",
    "goodwill": "goodwill", "intangible_assets": "intangible_assets",
    "total_assets": "total_assets", "short_term_debt": "short_term_debt",
    "short-term_debt": "short_term_debt", "long_term_debt": "long_term_debt",
    "long-term_debt": "long_term_debt", "total_debt": "total_debt",
    "total_liabilities": "total_liabilities", "total_equity": "total_equity",
    "market_cap": "market_cap", "bonds_payable": "bonds_payable",
    "total_current_liabilities": "total_current_liabilities",
    "operating_cf": "operating_cf", "capex": "capex",
    "dividends": "dividends_paid", "dividends_paid": "dividends_paid",
    "buybacks": "buybacks", "free_cash_flow": "free_cash_flow",
    "order_backlog": "order_backlog", "orders": "orders",
    "book_to_bill": "book_to_bill", "installed_base": "installed_base",
    "employees": "employees", "customer_count": "customer_count",
    "arr": "arr", "nrr": "nrr", "grr": "grr", "churn": "churn",
    "production_volume": "production_volume", "utilization_pct": "utilization_pct",
}

# Common SEC US GAAP XBRL concept → standard field mappings
# Complements statement-line-items.md label-based mappings with CamelCase XBRL concepts
_SEC_CONCEPT_MAP = {
    # Income Statement
    "revenues": "revenue",
    "revenuefromcontractwithcustomerincludingassessedtax": "revenue",
    "revenuefromcontractwithcustomerexcludingassessedtax": "revenue",
    "costofgoodsandservicessold": "cogs",
    "costofrevenue": "cogs",
    "costofsales": "cogs",
    "grossprofit": "gross_profit",
    "grossprofit_calculated": "gross_profit",
    "sellinggeneralandadministrativeexpense": "sg_and_a",
    "researchanddevelopmentexpense": "r_and_d",
    "operatingincomeloss": "operating_income",
    "interestexpense": "interest_expense",
    "interestexpensenonoperating": "interest_expense",
    "incometaxexpensebenefit": "income_tax",
    "incomelossfromcontinuingoperationsbeforeincometaxesextraordinaryitemsnoncontrollinginterest": "pre_tax_income",
    "netincomeloss": "net_income",
    "profitloss": "net_income",
    "incomelossfromcontinuingoperations": "net_income",
    "earningspersharebasic": "eps",
    "earningspersharediluted": "eps",
    "incomelossfromcontinuingoperationsperbasicshare": "eps",
    "incomelossfromcontinuingoperationsperdilutedshare": "eps",
    "weightedaveragenumberofsharesoutstandingbasic": "shares_outstanding",
    "weightedaveragenumberofdilutedsharesoutstanding": "shares_outstanding",
    "sharebasedcompensation": "sbc",
    "allocatedsharebasedcompensationexpense": "sbc",
    "depreciation": "d_and_a",
    "amortizationofintangibleassets": "amortization",
    "adjustmentforamortization": "d_and_a",
    # Balance Sheet
    "cashandcashequivalentsatcarryingvalue": "cash",
    "accountsreceivablenetcurrent": "accounts_receivable",
    "inventorynet": "inventory",
    "assets": "total_assets",
    "goodwill": "goodwill",
    "intangibleassetsnetexcludinggoodwill": "intangible_assets",
    "propertyplantandequipmentnet": "ppe_net",
    "stockholdersequity": "total_equity",
    "assetscurrent": "total_current_assets",
    "liabilitiescurrent": "total_current_liabilities",
    "liabilities": "total_liabilities",
    "liabilitiesandstockholdersequity": "total_assets",
    "longtermdebt": "long_term_debt",
    "longtermdebtcurrent": "short_term_debt",
    "longtermdebtnoncurrent": "long_term_debt",
    "accountspayablecurrent": "accounts_payable",
    "operatingleaseliabilitycurrent": "short_term_debt",
    "operatingleaseliabilitynoncurrent": "long_term_debt",
    "retainedearningsaccumulateddeficit": "retained_earnings",
    "additionalpaidincapital": "additional_paid_in_capital",
    "commonstockvalue": "common_stock",
    "preferredstockvalue": "preferred_stock",
    # Cash Flow
    "netcashprovidedbyusedinoperatingactivities": "operating_cf",
    "paymentstoacquirepropertyplantandequipment": "capex",
    "paymentsforrepurchaseofcommonstock": "buybacks",
    "paymentsrelatedtotaxwithholdingforsharebasedcompensation": "buybacks",
    "netcashprovidedbyusedininvestingactivities": "investing_cf",
    "netcashprovidedbyusedinfinancingactivities": "financing_cf",
    "paymentstoacquirebusinessesnetofcashacquired": "acquisitions",
    "interestpaidnet": "interest_expense",
    "incometaxespaidnet": "income_tax_paid",
    "cashcashequivalentsrestrictedcashandrestrictedcashequivalentsperiodincreasedecreaseincludingexchangerateeffect": "change_in_cash",
    "cashcashequivalentsrestrictedcashandrestrictedcashequivalents": "cash",
    # Supplementary
    "increasedecreaseinaccountsreceivable": "accounts_receivable",
    "increasedecreaseininventories": "inventory",
    "increasedecreaseinaccountspayable": "accounts_payable",
}


def _load_concept_map(workspace: Path = None) -> dict[str, str]:
    """Parse statement-line-items.md → {concept_alias: standard_field}.

    Dynamically builds a mapping from XBRL concepts, local-language labels,
    and variant names to standard LITE_FIELDS-compatible field names.
    Cached globally after first call.
    """
    global _concept_map_cache
    if _concept_map_cache is not None:
        return _concept_map_cache

    if workspace is None:
        try:
            workspace = discover_workspace()
        except RuntimeError:
            _concept_map_cache = {}
            return {}

    template = workspace / "references" / "policy" / "statement-line-items.md"
    if not template.exists():
        _concept_map_cache = {}
        return {}

    text = template.read_text(encoding="utf-8")
    mapping = {}

    # Parse each table row. Column indices: 1=标准科目, 3=US, 4=CN, 5=HK, 6=JP, 7=KR
    for line in text.split("\n"):
        if not line.startswith("|") or "---" in line:
            continue
        cols = [c.strip() for c in line.split("|")]
        if len(cols) < 5:
            continue

        # Derive standard field name from column 1
        col1 = cols[1].strip()
        raw_name = col1.lower()
        raw_name = raw_name.replace(" ", "_").replace("/", "_")
        raw_name = raw_name.replace("(", "").replace(")", "").replace(".", "")
        if not raw_name or raw_name in ("?", "—", "数据点", "符号", "标记", "科目"):
            continue

        std_name = _FIELD_ALIASES.get(raw_name)
        if std_name is None:
            # Try stripping parenthetical (e.g. "Total Equity (Parent)" → "Total Equity")
            base = re.sub(r'\([^)]*\)', '', col1).strip().lower()
            base = base.replace(" ", "_").replace("/", "_").replace(".", "")
            std_name = _FIELD_ALIASES.get(base, raw_name)

        # Extract all language-specific labels and map them to std_name
        for col_idx in (3, 4, 5, 6, 7):
            if col_idx >= len(cols):
                continue
            cell = cols[col_idx].strip()
            if not cell or cell == "—":
                continue
            # Split on "/" and "or" for multiple label variants in one cell
            parts = re.split(r'\s*/\s*|\s+or\s+', cell)
            for part in parts:
                key = part.strip().lower()
                # Normalize: remove spaces, special chars; keep alphanumeric + CJK
                key = re.sub(r'[^a-z0-9一-鿿぀-ゟ゠-ヿ가-힯]', '', key)
                if key and len(key) >= 2:
                    mapping.setdefault(key, std_name)

    # Add FIELD_ALIASES keys as direct mappings (covers fields not in statement-line-items.md)
    for alias, std_name in _FIELD_ALIASES.items():
        mapping.setdefault(alias, std_name)

    # Add SEC XBRL concept mappings (handles CamelCase US GAAP taxonomy concepts)
    for concept, std_name in _SEC_CONCEPT_MAP.items():
        mapping.setdefault(concept, std_name)

    _concept_map_cache = mapping
    return mapping


def _map_concept(concept: str, concept_map: dict = None) -> str:
    """Map a provider concept/label to standard field name.

    Examples:
        'Revenues' → 'revenue'
        'SellingGeneralAndAdministrativeExpense' → 'sg_and_a'
        '売上高' → 'revenue' (JP label)
        '매출' → 'revenue' (KR label)
    """
    if concept_map is None:
        concept_map = _concept_map_cache or {}

    if not concept or not isinstance(concept, str):
        return concept.lower().replace(" ", "_") if concept else ""

    # Normalize input: lowercase, remove spaces and underscores
    key = concept.lower().replace(" ", "").replace("_", "")

    # Direct lookup
    if key in concept_map:
        return concept_map[key]

    # Try stripping trailing 's' (plural → singular: Revenues → Revenue)
    if key.endswith('s') and len(key) > 3:
        key_singular = key[:-1]
        if key_singular in concept_map:
            return concept_map[key_singular]

    # Fuzzy lookup: strip common XBRL concept suffixes
    key_clean = re.sub(
        r'(calculated|usd|atcarryingvalue|net|current|noncurrent|'
        r'afterallowance|forcreditloss|parent|attributableto|'
        r'fromcontractwithcustomer|abstract|member|'
        r'total|segment)$', '', key
    )
    if key_clean and key_clean != key:
        if key_clean in concept_map:
            return concept_map[key_clean]
        # Try again with trailing 's' stripped from cleaned key
        if key_clean.endswith('s') and len(key_clean) > 3:
            if key_clean[:-1] in concept_map:
                return concept_map[key_clean[:-1]]

    # Fallback: return normalized concept name
    return concept.lower().replace(" ", "_").replace("/", "_")


# ---------------------------------------------------------------------------
# Consumer helper: filter statements to lite/full field sets
# ---------------------------------------------------------------------------
def get_fields(statements: dict, mode: str = "lite") -> dict:
    """Filter provider statements to lite or full field set.

    Lite mode: keeps only fields in LITE_FIELDS (~46 fields).
    Full mode: passes through all fields.
    Consumer skills call this before reading actuals.
    """
    if mode == "full":
        return statements

    # Build flat allowed set from LITE_FIELDS
    allowed = set()
    for field_set in LITE_FIELDS.values():
        allowed.update(field_set)

    concept_map = _load_concept_map()

    filtered = {}
    for stmt_name, rows in statements.items():
        kept_rows = []
        for row in rows:
            if not isinstance(row, dict):
                kept_rows.append(row)
                continue
            concept = (row.get("concept") or "").lower()
            label = (row.get("label") or "").lower()
            if not concept and not label:
                kept_rows.append(row)
                continue

            # Try concept first (works for SEC concepts + language labels)
            std_name = _map_concept(concept, concept_map) if concept else ""
            if not std_name or std_name not in allowed:
                # Fallback: try matching via human-readable label field
                if label:
                    label_key = re.sub(r'[^a-z0-9]', '', label)
                    std_name = _map_concept(label_key, concept_map)
            if std_name in allowed:
                kept_rows.append(row)
        if kept_rows:
            filtered[stmt_name] = kept_rows
    return filtered


PROVIDER_MODULES = {
    "us": "sec_provider",
    "cn": "akshare_provider",
    "hk": "akshare_provider",
    "jp": "edinet_provider",
    "kr": "dart_provider",
    "tw": "finmind_provider",
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
            "finmind": {"available": True, "install_hint": "uses FinMind public HTTP API; no package required"},
            "edinet-tools": {"available": module_available("edinet_tools"), "install_hint": "pip install edinet-tools"},
            "dart-fss": {"available": module_available("dart_fss"), "install_hint": "pip install dart-fss"},
            "openesef": {"available": module_available("openesef"), "install_hint": "pip install openesef"},
        },
        "env": {
            "EDGAR_IDENTITY": {"configured": bool(os.getenv("EDGAR_IDENTITY"))},
            "DART_API_KEY": {"configured": bool(os.getenv("DART_API_KEY"))},
            "EDINET_API_KEY": {"configured": bool(os.getenv("EDINET_API_KEY"))},
            "FINMIND_TOKEN": {"configured": bool(os.getenv("FINMIND_TOKEN")), "required": False},
        },
    }


def discover_workspace(source: Path | None = None) -> Path:
    candidates = [source or Path.cwd(), Path.cwd()]
    for candidate in candidates:
        current = candidate if candidate.is_dir() else candidate.parent
        for parent in [current, *current.parents]:
            if (parent / "industry").is_dir():
                return parent
    raise RuntimeError("Could not discover workspace. Pass --workspace or run init-workspace first.")


def ensure_company_topic(workspace: Path, company_slug: str) -> Path:
    # Search industry/*/companies/<slug> for the company directory
    industry_dir = workspace / "industry"
    if industry_dir.is_dir():
        for ind in industry_dir.iterdir():
            if not ind.is_dir():
                continue
            tp = ind / "companies" / company_slug
            if tp.is_dir():
                return tp
    raise RuntimeError(
        f"Company directory not found under industry/*/companies/{company_slug}. "
        f"Run new-session first to create the company workspace."
    )


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
    "revenue_split",
)


def normalize_result(provider_result: dict[str, Any], request: dict[str, Any]) -> dict[str, Any]:
    """Central normalizer: standardize provider output into the canonical pack format."""
    provider = provider_result.get("provider", "unknown")
    provider_status = provider_result.get("status", "provider-gap")

    company = provider_result.get("company", {})
    financials_raw = {}
    for key in FINANCIAL_OUTPUT_KEYS:
        val = provider_result.get(key)
        if val:
            financials_raw[key] = val
    financials_raw = filter_financials_by_period(financials_raw, request.get("periods", "latest"))

    filing_info = provider_result.get("filing", {}) or {}
    errors = list(provider_result.get("errors", []))
    data_gaps = list(provider_result.get("data_gaps", []))
    provider_timing = provider_result.get("provider_timing", {}) or {}
    gap_by_item = {
        str(gap).split(":", 1)[0].strip(): str(gap).split(":", 1)[1].strip()
        for gap in data_gaps
        if ":" in str(gap)
    }
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
            "caveat": gap_by_item.get(item, ""),
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
        "data_gaps": data_gaps,
        "provider_timing": provider_timing,
        "items_extracted": extracted,
        "provider_payload": provider_result,
    }


def filter_financials_by_period(financials: dict[str, Any], periods: str | None) -> dict[str, Any]:
    if not financials or not periods or periods in ("latest", "5Y"):
        # latest: keep all periods (agent picks last FY+Q)
        # 5Y: keep all periods (agent picks 5FY+4Q for modeling)
        return financials

    if is_latest4q_period_filter(str(periods)):
        return filter_financials_latest_periods(financials, max_periods=4)

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
                if isinstance(row.get("metrics"), dict):
                    kept["metrics"] = {
                        period: metrics
                        for period, metrics in row.get("metrics", {}).items()
                        if period in kept_values
                    }
                if isinstance(row.get("source_periods"), dict):
                    kept["source_periods"] = {
                        period: sources
                        for period, sources in row.get("source_periods", {}).items()
                        if period in kept_values
                    }
                if isinstance(row.get("cumulative_values"), dict):
                    kept["cumulative_values"] = {
                        period: value
                        for period, value in row.get("cumulative_values", {}).items()
                        if period in kept_values
                    }
                if isinstance(row.get("period_basis_by_period"), dict):
                    kept["period_basis_by_period"] = {
                        period: basis
                        for period, basis in row.get("period_basis_by_period", {}).items()
                        if period in kept_values
                    }
                kept_rows.append(kept)
        filtered[statement] = kept_rows
    return filtered


def is_latest4q_period_filter(periods: str | None) -> bool:
    token = re.sub(r"[^a-z0-9]+", "", str(periods or "").strip().lower())
    return token in {"latest4q", "last4q", "latest4quarters", "latestfourquarters", "quarterly"}


def filter_financials_latest_periods(financials: dict[str, Any], max_periods: int = 4) -> dict[str, Any]:
    filtered: dict[str, Any] = {}
    for statement, rows in financials.items():
        periods = sorted(
            {
                str(period)
                for row in rows
                if isinstance(row, dict)
                for period in (row.get("values", {}) or {}).keys()
            },
            key=period_sort_key,
            reverse=True,
        )[:max_periods]
        allowed = set(periods)
        kept_rows = []
        for row in rows:
            values = row.get("values", {}) if isinstance(row, dict) else {}
            kept_values = {
                period: value
                for period, value in values.items()
                if str(period) in allowed
            }
            if kept_values:
                kept = dict(row)
                kept["values"] = kept_values
                if isinstance(row.get("metrics"), dict):
                    kept["metrics"] = {
                        period: metrics
                        for period, metrics in row.get("metrics", {}).items()
                        if str(period) in allowed
                    }
                if isinstance(row.get("source_periods"), dict):
                    kept["source_periods"] = {
                        period: sources
                        for period, sources in row.get("source_periods", {}).items()
                        if str(period) in allowed
                    }
                if isinstance(row.get("cumulative_values"), dict):
                    kept["cumulative_values"] = {
                        period: value
                        for period, value in row.get("cumulative_values", {}).items()
                        if str(period) in allowed
                    }
                if isinstance(row.get("period_basis_by_period"), dict):
                    kept["period_basis_by_period"] = {
                        period: basis
                        for period, basis in row.get("period_basis_by_period", {}).items()
                        if str(period) in allowed
                    }
                kept_rows.append(kept)
        filtered[statement] = kept_rows
    return filtered


def period_sort_key(label: Any) -> tuple[int, int, int, int, str]:
    """Sort period labels from multiple providers without inventing periods."""
    text = str(label or "").strip()
    date_match = re.search(r"(20\d{2}|19\d{2})[-/.](\d{1,2})[-/.](\d{1,2})", text)
    if date_match:
        year = int(date_match.group(1))
        month = int(date_match.group(2))
        day = int(date_match.group(3))
        quarter = max(1, min(4, (month - 1) // 3 + 1))
        return (year, quarter, month, day, text)

    year_match = re.search(r"(20\d{2}|19\d{2})", text)
    year = int(year_match.group(1)) if year_match else 0
    quarter = 4
    month = 12
    day = 31

    q_match = re.search(r"[Qq]([1-4])", text)
    if q_match:
        quarter = int(q_match.group(1))
        month = quarter * 3
        day = 31 if quarter in {1, 4} else 30
    elif re.search(r"[Hh]1|中报|半年|半期|二季|第二季", text):
        quarter, month, day = 2, 6, 30
    elif re.search(r"[Hh]2", text):
        quarter, month, day = 4, 12, 31
    elif re.search(r"一季|第一季", text):
        quarter, month, day = 1, 3, 31
    elif re.search(r"三季|第三季", text):
        quarter, month, day = 3, 9, 30
    elif re.search(r"年报|年度|annual|FY", text, flags=re.IGNORECASE):
        quarter, month, day = 4, 12, 31

    return (year, quarter, month, day, text)


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
    match = re.search(r"(20\d{2}|19\d{2})", str(label))
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
        filing_documents = provider_result.get("filing_documents") or []
        return (bool(filing) and filing.get("status") != "error") or bool(filing_documents)
    if item == "latest_full_filing":
        filing = provider_result.get("filing", {}) or {}
        return bool(filing.get("markdown"))
    if item in ("income_statement", "balance_sheet", "cash_flow", "revenue_split"):
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
    if item == "revenue_split":
        return provider_result.get("revenue_split_completeness_status", "available-review") if provider_result.get(item) else "provider-gap"
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
    lines.extend(["", "## Revenue Split", ""])
    split_rows = financials.get("revenue_split", [])
    if split_rows:
        for row in split_rows:
            lbl = row.get("label", "")
            split_type = row.get("split_type", "")
            vals = row.get("values", {})
            if vals:
                periods_str = ", ".join(f"{p}: {v}" for p, v in sorted(vals.items()) if v is not None)
                prefix = f"{split_type} / " if split_type else ""
                lines.append(f"- {prefix}{lbl}: {periods_str}")
    else:
        lines.append("- No structured revenue split extracted.")
    derived_sections = [
        ("income_statement_quarterly_derived", "Income Statement - Quarter-Only Derived"),
        ("cash_flow_quarterly_derived", "Cash Flow - Quarter-Only Derived"),
    ]
    for key, title in derived_sections:
        rows = financials.get(key, [])
        if not rows:
            continue
        lines.extend(["", f"## {title}", "", "_Derived from cumulative OpenDART reporting periods; original cumulative statements are retained._", ""])
        for row in rows:
            lbl = row.get("label", "")
            vals = row.get("values", {})
            if vals:
                periods_str = ", ".join(f"{p}: {v}" for p, v in sorted(vals.items()) if v is not None)
                lines.append(f"- {lbl}: {periods_str}")
    return "\n".join(lines)


def period_basis_summary(rows: list[dict[str, Any]]) -> str:
    counts: dict[str, int] = {}
    for row in rows:
        basis_by_period = row.get("period_basis_by_period", {}) if isinstance(row, dict) else {}
        if not isinstance(basis_by_period, dict):
            continue
        for basis in basis_by_period.values():
            key = str(basis or "unknown")
            counts[key] = counts.get(key, 0) + 1
    return ", ".join(f"{basis}={count}" for basis, count in sorted(counts.items()))


def build_financial_data_summary(evidence_pack: dict[str, Any],
                                 actuals_resolved: dict[str, Any],
                                 out_dir: Path) -> str:
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
        f"- Machine data: `_cache/financial-data/`",
        "",
        "## Filing",
        "",
        f"- Filing status: `{filing.get('status', 'unavailable')}`",
        f"- Filing date: `{filing.get('filing_date') or ''}`",
        f"- Accession / document id: `{filing.get('accession_number') or filing.get('document_id') or ''}`",
        f"- Full filing: `full-filing.md` ({'available' if filing.get('has_full_filing_markdown') else 'unavailable'})",
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
        for statement in FINANCIAL_OUTPUT_KEYS:
            rows = statements.get(statement, [])
            periods = sorted({
                period
                for row in rows
                for period in (row.get("values", {}) if isinstance(row, dict) else {}).keys()
            })
            basis = period_basis_summary(rows)
            basis_text = f"; period basis: {basis}" if basis else ""
            lines.append(f"- `{statement}`: {len(rows)} rows; periods: {', '.join(periods) if periods else 'none'}{basis_text}")
        derived_rows = {
            key: statements.get(key, [])
            for key in ("income_statement_quarterly_derived", "cash_flow_quarterly_derived")
            if statements.get(key)
        }
        if derived_rows:
            lines.extend(["", "## Derived Quarter-Only KR Flow Statements", ""])
            lines.append("- OpenDART Q1/H1/Q3/FY flow statements can be cumulative; original cumulative rows are retained.")
            lines.append("- Derived rows are calculated as `Q1 = Q1`, `Q2 = H1 - Q1`, `Q3 = Q3_YTD - H1`, `Q4 = FY - Q3_YTD`.")
            lines.append("- Balance sheet is not derived because it is a point-in-time statement.")
            for statement, rows in derived_rows.items():
                periods = sorted({
                    period
                    for row in rows
                    for period in (row.get("values", {}) if isinstance(row, dict) else {}).keys()
                })
                lines.append(f"- `{statement}`: {len(rows)} rows; derived periods: {', '.join(periods) if periods else 'none'}")
    else:
        lines.append("- No structured statement rows were materialized.")

    unmapped = actuals_resolved.get("unmapped_items", [])
    lines.extend(["", "## Model Input Policy", ""])
    lines.append("- Public surface is Markdown-only: this summary is the default file for humans and LLMs.")
    lines.append("- Machine inputs are under `_cache/financial-data/`; modeling scripts should read JSON there and must not parse this Markdown for numbers.")
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
    if cross_check.get("data_gaps"):
        if not cross_check.get("errors"):
            lines.extend(["", "## Errors / Caveats", ""])
        for gap in cross_check.get("data_gaps", []):
            lines.append(f"- {gap}")

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
    filing_source_id = _source_id_from_filing(filing)
    filing_url = filing.get("filing_url") or filing.get("source_url") if filing else ""

    # Filing-level source
    if filing and filing.get("status") != "error":
        entries.append({
            "data_item": "filing_index",
            "provider": provider,
            "source_id": filing_source_id,
            "filing_date": filing.get("filing_date", ""),
            "filing_url": filing_url,
            "confidence": completeness_by_item.get("filing_index", {}).get("status", "provider-gap"),
        })
        if filing.get("markdown"):
            entries.append({
                "data_item": "latest_full_filing",
                "provider": provider,
                "source_id": filing_source_id,
                "sha256": filing.get("markdown_sha256", ""),
                "source_package_type": filing.get("source_package_type", ""),
                "source_url": filing_url,
                "confidence": completeness_by_item.get("latest_full_filing", {}).get("status", "provider-gap"),
            })

    # Statement-level source
    for stmt_type in FINANCIAL_OUTPUT_KEYS:
        rows = financials.get(stmt_type, [])
        first_row = rows[0] if rows else {}
        entry = {
            "data_item": stmt_type,
            "provider": provider,
            "record_count": len(rows),
            "confidence": completeness_by_item.get(stmt_type, {}).get("status", first_row.get("confidence", "provider-gap")),
        }
        if rows:
            entry["source_id"] = filing_source_id
            if first_row.get("source_type"):
                entry["source_type"] = first_row.get("source_type")
            if first_row.get("derivation"):
                entry["derivation"] = first_row.get("derivation")
            if stmt_type == "revenue_split":
                entry["concepts"] = sorted({
                    str(row.get("concept"))
                    for row in rows
                    if isinstance(row, dict) and row.get("concept")
                })
                entry["axes"] = sorted({
                    str(row.get("axis"))
                    for row in rows
                    if isinstance(row, dict) and row.get("axis")
                })
                entry["members_sample"] = sorted({
                    str(row.get("member") or row.get("label"))
                    for row in rows[:25]
                    if isinstance(row, dict) and (row.get("member") or row.get("label"))
                })
                entry["split_types"] = sorted({
                    str(row.get("split_type"))
                    for row in rows
                    if isinstance(row, dict) and row.get("split_type")
                })
                entry["axis_count"] = len(entry["axes"])
                entry["extraction_methods"] = sorted({
                    str(row.get("extraction_method"))
                    for row in rows
                    if isinstance(row, dict) and row.get("extraction_method")
                })
                entry["model_bucket_hints"] = sorted({
                    str(row.get("model_bucket_hint"))
                    for row in rows
                    if isinstance(row, dict) and row.get("model_bucket_hint")
                })
                entry["review_required"] = any(
                    bool(row.get("review_required"))
                    for row in rows
                    if isinstance(row, dict)
                )
                reconciliation_statuses = sorted({
                    str(row.get("reconciliation_status") or row.get("axis_completeness_status"))
                    for row in rows
                    if isinstance(row, dict) and (row.get("reconciliation_status") or row.get("axis_completeness_status"))
                })
                if reconciliation_statuses:
                    entry["reconciliation_statuses"] = reconciliation_statuses
                    entry["reconciliation_status"] = (
                        "partial-review" if "partial-review" in reconciliation_statuses
                        else "unreconciled-review" if "unreconciled-review" in reconciliation_statuses
                        else reconciliation_statuses[0]
                    )
                if first_row.get("completeness_status"):
                    entry["revenue_split_completeness_status"] = first_row.get("completeness_status")
        entries.append(entry)

    return {"entries": entries, "source_provider": provider}


def _source_id_from_filing(filing: dict | None) -> str:
    if not filing:
        return ""
    for key in ("accession_number", "document_id", "doc_id", "rcept_no", "edinet_code", "corp_code", "source_sha256", "markdown_sha256"):
        value = filing.get(key)
        if value:
            return str(value)
    return ""


# ---------------------------------------------------------------------------
# Canonical pack writer
# ---------------------------------------------------------------------------
def write_canonical_pack(args: argparse.Namespace, normalized: dict[str, Any],
                         workspace: Path, rid: str) -> dict[str, Any]:
    company_slug = slugify(args.company_slug)
    canonical_id = slugify(args.canonical_id or args.identifier)
    topic_path = ensure_company_topic(workspace, company_slug)
    rel_tail = Path("financial-data") / args.market / canonical_id / rid
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
        "data_gaps": normalized.get("data_gaps", []),
        "provider_timing": normalized.get("provider_timing", {}),
        "items_extracted": normalized["items_extracted"],
    }
    write_json(cache_dir / "cross-check.json", cross_check)
    source_map = _build_source_map(provider, filing, financials, normalized["completeness"])
    write_json(cache_dir / "source-map.json", source_map)

    write_consumer_outputs(
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
        "financial_data_summary_path": str(topic_path / "_cache" / "financial-data" / "summary.md"),
        "financial_data_dir": str(topic_path / "_cache" / "financial-data"),
    }


def write_consumer_outputs(topic_path: Path, cache_dir: Path, manifest: dict[str, Any],
                           raw_dir: Path,
                           identity: dict[str, Any], filing: dict[str, Any],
                           filing_md: str, financials: dict[str, Any],
                           completeness: list[dict[str, Any]], source_map: dict[str, Any],
                           cross_check: dict[str, Any]) -> None:
    """Write consumer-facing files to _cache/financial-data/.

    Only 4 files: evidence-pack.json (audit pointer), actuals-resolved.json
    (what all consumer skills read), full-filing.md (latest filing full text),
    and summary.md (human entry point).

    Versioned run outputs live under _cache/financial-data/<market>/<id>/<run_id>/.
    Raw evidence lives under _raw/financial-data/<market>/<id>/<run_id>/.
    """
    out_dir = topic_path / "_cache" / "financial-data"
    out_dir.mkdir(parents=True, exist_ok=True)

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
            "rcept_no": filing.get("rcept_no") if filing else None,
            "report_name": filing.get("report_name") if filing else None,
            "source_package_type": filing.get("source_package_type") if filing else None,
            "filing_date": filing.get("filing_date") if filing else None,
            "source_url": filing.get("filing_url", filing.get("source_url")) if filing else None,
            "has_full_filing_markdown": bool(filing_md),
        },
        "completeness": completeness,
        "source_map": source_map,
        "cross_check": cross_check,
        "provider_timing": cross_check.get("provider_timing", {}),
        "statements": financials or {},
    }
    write_json(out_dir / "evidence-pack.json", evidence_pack)

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
    write_json(out_dir / "actuals-resolved.json", actuals_resolved)

    if filing_md:
        write_md(out_dir / "full-filing.md", filing_md)
    else:
        write_md(out_dir / "full-filing.md",
                 "# Full filing unavailable\n\nNo full filing markdown was materialized for the latest financial-data run.\n")

    write_md(
        out_dir / "summary.md",
        build_financial_data_summary(evidence_pack, actuals_resolved, out_dir),
    )

    # Clean up legacy internal/ directory from older plugin versions
    legacy_internal = out_dir / "internal"
    if legacy_internal.exists() and legacy_internal.is_dir():
        shutil.rmtree(legacy_internal)
    for legacy_name in ("financial-data-summary.md",):
        legacy_path = out_dir / legacy_name
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
        "rcept_no": filing.get("rcept_no"),
        "report_name": filing.get("report_name"),
        "report_code": filing.get("report_code"),
        "edinet_code": filing.get("edinet_code"),
        "doc_type": filing.get("doc_type"),
        "source_file": source_path.name,
    })
    (filing_dir / "source.sha256").write_text(sha256_file(source_path) + "\n", encoding="utf-8")


def _filing_id(provider: str, filing: dict[str, Any]) -> str:
    candidates = [
        filing.get("accession_number"),
        filing.get("document_id"),
        filing.get("rcept_no"),
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
    topic = args.topic.replace("\\", "/").strip().strip("/")
    if topic.startswith("topics/"):
        topic = topic[len("topics/"):]
    if "/" not in topic:
        topic = f"industry/{topic}"
    tp = workspace / topic
    if not tp.is_dir():
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
    p.add_argument("--market", choices=("us", "cn", "hk", "jp", "kr", "tw", "eu"), help="Market route")
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
        print(json.dumps(dependency_matrix(), ensure_ascii=True, indent=2))
        return 0

    if not args.market or not args.identifier:
        print(json.dumps({"status": "failed", "error": "--market and --identifier required"}, ensure_ascii=True, indent=2))
        return 1
    if args.output_scope == "canonical_company" and not args.company_slug:
        print(json.dumps({"status": "failed", "error": "--company-slug required for canonical_company"}, ensure_ascii=True, indent=2))
        return 1

    # Period defaults based on mode: lite=latest, full=5Y
    mode = getattr(args, 'mode', 'lite')
    if args.periods == 'latest' and mode == 'full':
        args.periods = '5Y'

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

        # Lite mode: auto-fill yfinance market snapshot
        if getattr(args, "mode", "latest_core") == "lite":
            try:
                import yfinance as yf
                data_dir = output.get("financial_data_dir", "")
                if not data_dir:
                    # Fallback: find company dir from workspace
                    tp = ensure_company_topic(workspace, args.company_slug)
                    data_dir = str(tp / "_cache" / "financial-data")
                actuals_path = Path(data_dir) / "actuals-resolved.json"
                if actuals_path.exists():
                    with open(actuals_path, encoding="utf-8") as f:
                        actuals = json.load(f)
                else:
                    actuals = {}
            except Exception:
                actuals = {}
            try:
                t = yf.Ticker(args.identifier)
                info = t.info
                actuals["market_data"] = {
                    "price": info.get("currentPrice"),
                    "market_cap": info.get("marketCap"),
                    "pe_ttm": info.get("trailingPE"),
                    "pe_ntm": info.get("forwardPE"),
                    "pb": info.get("priceToBook"),
                    "ps_ttm": info.get("priceToSalesTrailing12Months"),
                    "ev_ebitda": info.get("enterpriseToEbitda"),
                    "ev_sales": info.get("enterpriseToRevenue"),
                    "dividend_yield_pct": info.get("dividendYield"),
                    "beta": info.get("beta"),
                    "fifty_two_week_high": info.get("fiftyTwoWeekHigh"),
                    "fifty_two_week_low": info.get("fiftyTwoWeekLow"),
                }
            except Exception:
                actuals["market_data"] = {}
            try:
                actuals_path.parent.mkdir(parents=True, exist_ok=True)
                with open(actuals_path, "w", encoding="utf-8") as f:
                    json.dump(actuals, f, indent=2, ensure_ascii=False, default=str)
            except Exception:
                pass

        print(json.dumps({
            "status": normalized["status"],
            "provider": normalized["provider"],
            "extracted": normalized["items_extracted"],
            "errors": normalized["errors"],
            "provider_timing": normalized.get("provider_timing", {}),
            "completeness": normalized["completeness"],
            "output": output,
        }, ensure_ascii=True, indent=2))
        return 0
    except Exception as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}, ensure_ascii=True, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
