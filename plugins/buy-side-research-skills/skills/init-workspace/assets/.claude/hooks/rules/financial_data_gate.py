"""Rule: financial-data layer-based completeness check for company-level skills."""
import re, sys, os, json
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import block, warn

HOOKS_DIR = Path(__file__).resolve().parents[1]
SCHEMA_PATH = HOOKS_DIR / "config" / "actuals_schema.json"


def _load_schema_runtime_contract():
    defaults = {
        "near_required_supplementary": ["revenue_by_geography", "shares_outstanding"],
        "sector_conditional_supplementary": ["order_backlog"],
        "best_effort_supplementary": ["sbc"],
        "best_effort_skippable": [
            "cash_flow.latest_fy.dividends_paid",
            "cash_flow.latest_fy.share_buybacks",
            "cash_flow.latest_quarter.dividends_paid",
            "cash_flow.latest_quarter.share_buybacks",
            "supplementary.sbc",
        ],
    }
    try:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        supplementary = schema.get("supplementary", {})
        taxonomy = schema.get("_growth_first_taxonomy", {})
        defaults["near_required_supplementary"] = list(supplementary.get("_near_required_fields", defaults["near_required_supplementary"]))
        defaults["sector_conditional_supplementary"] = list(supplementary.get("_sector_conditional_fields", defaults["sector_conditional_supplementary"]))
        defaults["best_effort_supplementary"] = list(supplementary.get("_best_effort_fields", defaults["best_effort_supplementary"]))
        defaults["best_effort_skippable"] = list(taxonomy.get("best_effort_skippable", defaults["best_effort_skippable"]))
    except Exception:
        pass
    return defaults


SCHEMA_RUNTIME_CONTRACT = _load_schema_runtime_contract()

COMPANY_SKILLS = {
    "stock-quickread", "company-history", "driver-map",
    "alpha-thesis", "consensus-map", "earnings-setup",
    "bear-pre-mortem", "comps-analysis", "peer-deep-dive",}

SLUG_RE = re.compile(
    r'^\d{4}-\d{2}-\d{2}-(?:' +
    '|'.join(s.replace('-', r'\-') for s in COMPANY_SKILLS) +
    r')-([a-z0-9][a-z0-9\-]*)\.(?:md|html)$',
    re.IGNORECASE
)

# Which fields each layer CAN fill.
# Acquisition mode defines the layer:
# - provider_api: stable structured provider routes, including provider-fetched official filings cached locally
# - official_web / trusted_web / broad_web: Layer 3 fallback split by web-source priority
#   official_web includes company IR/results pages, official public filing portals found via web search,
#   and explicitly curated official_web cache entries written under internal/_raw/official_web_cache.json
# Source-trust ranking is separate from execution order:
# - tier 1: provider_api, official_web
# - tier 2: yfinance
# - tier 3: trusted_web, broad_web
# Lower-trust sources must not overwrite higher-trust sources in actuals-resolved.json.
# Non-finite numeric placeholders such as NaN/inf are treated as missing, not as filled values.
LAYER_COVERAGE = {
    "yfinance": {
        "income_statement.*",
        "balance_sheet.*",
        "cash_flow.*",
        "market_data.*",
        "supplementary.shares_outstanding",
    },
    "provider_api": {
        "*",
    },
    "official_web": {
        "*",
    },
    "trusted_web": {
        "*",
    },
    "broad_web": {
        "*",
    },
}

# Layer execution order
LAYERS = ["yfinance", "provider_api", "official_web", "trusted_web", "broad_web"]
LAYER_ALIAS = {"web_search": "broad_web"}
TRUST_RANK = {
    "provider_api": 3,
    "official_web": 3,
    "yfinance": 2,
    "trusted_web": 1,
    "broad_web": 1,
}
SEGMENT_STATUS_VALUES = {
    "extracted",
    "pending_official_extraction",
    "provider_unavailable",
    "not_disclosed",
}
SUPPLEMENTARY_HIGH_VALUE_FIELDS = SCHEMA_RUNTIME_CONTRACT["near_required_supplementary"]
SUPPLEMENTARY_SECTOR_CONDITIONAL_FIELDS = SCHEMA_RUNTIME_CONTRACT["sector_conditional_supplementary"]
SKIPPABLE_NULL_FIELDS = set(SCHEMA_RUNTIME_CONTRACT["best_effort_skippable"]) | {
    "supplementary." + field_name for field_name in SUPPLEMENTARY_SECTOR_CONDITIONAL_FIELDS
}


def _find_source_layers(obj, highest=-1):
    """Recursively find source_layer values in nested dicts (handles v2.2 period wrapper)."""
    if isinstance(obj, dict):
        if "source_layer" in obj and obj["source_layer"]:
            sl = LAYER_ALIAS.get(obj["source_layer"], obj["source_layer"])
            idx = LAYERS.index(sl) if sl in LAYERS else -1
            highest = max(highest, idx)
        for k, v in obj.items():
            if k.startswith("_"):
                continue
            highest = _find_source_layers(v, highest)
    elif isinstance(obj, list):
        for item in obj:
            highest = _find_source_layers(item, highest)
    return highest


def _get_tried_layer(data: dict) -> int:
    """Return highest layer index that has been attempted (0-based)."""
    highest = -1
    source = (data.get("source") or "").lower()
    for i, layer in enumerate(LAYERS):
        if layer in source:
            highest = max(highest, i)
    if "web_search" in source:
        highest = max(highest, LAYERS.index("broad_web"))
    highest = _find_source_layers(data, highest)
    return max(highest, 0)


def _count_nulls(obj, prefix="") -> list[str]:
    """Return list of dot-paths for fields with null/None value."""
    nulls = []
    if obj is None:
        return [prefix]
    if isinstance(obj, dict):
        if "value" in obj and "source_layer" in obj:
            # This is a data field
            value = obj["value"]
            if value is None or (isinstance(value, float) and (value != value or value in (float("inf"), float("-inf")))):
                return [prefix]
            return []
        for k, v in obj.items():
            if k.startswith("_"):
                continue
            path = f"{prefix}.{k}" if prefix else k
            if isinstance(v, (dict, list)):
                nulls.extend(_count_nulls(v, path))
            elif v is None:
                nulls.append(path)
    elif isinstance(obj, list):
        if not obj:
            nulls.append(prefix)
        else:
            for i, item in enumerate(obj):
                nulls.extend(_count_nulls(item, f"{prefix}[{i}]"))
    return nulls


def _provider_gap_reason(detail: str) -> str | None:
    m = re.search(r"reason=([a-z_]+)", str(detail or ""))
    if m:
        return m.group(1)
    lowered = str(detail or "").lower()
    if "not_disclosed" in lowered:
        return "not_disclosed"
    if "provider_unavailable" in lowered:
        return "provider_unavailable"
    if "provider-gap" in lowered:
        return "official_source_available_not_extracted"
    return None


def _segments_status(data: dict) -> str | None:
    segments = data.get("segments", {})
    if not isinstance(segments, dict):
        return None
    status = segments.get("status")
    if status in SEGMENT_STATUS_VALUES:
        return status
    return None


def _resolve_actuals_path(root: str, company_slug: str) -> str | None:
    industry_root = os.path.join(root, "industry")
    if not os.path.isdir(industry_root):
        return None
    for industry_name in os.listdir(industry_root):
        candidate = os.path.join(
            industry_root, industry_name, "companies", company_slug,
            ".cache", "financial-data", "internal", "actuals-resolved.json"
        )
        if os.path.isfile(candidate):
            return candidate
    return None


def _field_value(data: dict, section: str, period_key: str, field: str):
    field_obj = data.get(section, {}).get(period_key, {}).get(field, {})
    if isinstance(field_obj, dict):
        return field_obj.get("value")
    return field_obj


def _layer_can_fill(path: str, layer_idx: int) -> bool:
    """Check if a given layer can potentially fill this field path."""
    if layer_idx >= len(LAYERS):
        return False

    # yfinance (layer 0): can fill IS/BS/CF + market_data + shares_outstanding
    # cannot fill: segments, consensus, supplementary (except shares_outstanding), data_quality
    if layer_idx == 0:
        yfinance_can = {"income_statement", "balance_sheet", "cash_flow", "market_data"}
        top = path.split(".")[0]
        if top in yfinance_can:
            return True
        if path == "supplementary.shares_outstanding" or path.startswith("supplementary.shares_outstanding"):
            return True
        return False

    # provider_api and Layer 3 web fallbacks can fill everything
    return True


def check(ctx: dict):
    if ctx.get("tool_name", "") not in ("Write", "Edit", "MultiEdit"):
        return

    root = ctx.get("cwd", "")
    for cpath in ctx.get("candidate_paths", []):
        leaf = Path(cpath).name
        rel = ""
        try:
            rel = str(Path(cpath).resolve().relative_to(Path(root).resolve()))
        except Exception:
            rel = leaf

        m = SLUG_RE.match(leaf)
        if not m:
            continue

        company_slug = m.group(1).lower()
        financial_data_path = _resolve_actuals_path(root, company_slug)

        # --- Gate 1: file exists? ---
        if not financial_data_path or not os.path.isfile(financial_data_path):
            block(
                f"Blocked by financial_data_gate: {rel} — no actuals-resolved.json for '{company_slug}'. "
                f"Run /financial-data --lite {company_slug} (layer 1: yfinance)."
            )

        # --- Gate 2: has real data? ---
        try:
            with open(financial_data_path, 'r', encoding='utf-8') as fh:
                data = json.load(fh)
        except Exception:
            block(
                f"Blocked by financial_data_gate: {rel} — actuals-resolved.json for '{company_slug}' "
                f"is unreadable. Re-run /financial-data --lite {company_slug}."
            )

        # Quick sanity: must have market_data OR IS with real data
        has_real = False
        if isinstance(data.get("market_data"), dict):
            mc = data["market_data"].get("market_cap")
            if isinstance(mc, dict) and mc.get("value") is not None:
                has_real = True
            elif isinstance(mc, (int, float)):
                has_real = True
        if not has_real:
            # Also check IS.latest_fy for at least revenue + net_income (v2.2 period-aware)
            is_data = data.get("income_statement", {})
            latest_fy = is_data.get("latest_fy", {})
            if latest_fy:
                rev = latest_fy.get("revenue", {})
                ni = latest_fy.get("net_income", {})
                if isinstance(rev, dict) and rev.get("value") is not None:
                    has_real = True
                elif isinstance(rev, (int, float)):
                    has_real = True
        if not has_real:
            block(
                f"Blocked by financial_data_gate: {rel} — actuals-resolved.json for '{company_slug}' "
                f"contains no real data (empty shell). Re-run /financial-data --lite {company_slug}."
            )

        # --- Gate 2.5: ADR / dual-class / freshness checks (warn only) ---
        shares_note = data.get('data_quality', {}).get('shares_note') if isinstance(data.get('data_quality'), dict) else None
        if shares_note and shares_note not in ('verified', 'dual_class_verified'):
            warn(
                f"financial_data_gate: {rel} — shares_note='{shares_note}' for '{company_slug}'. "
                f"Verify market cap: ADR ratio, dual-class structure, or H+A dual listing may distort yfinance data."
            )

        fiscal_period = data.get('latest_fy_period', '') or data.get('as_of_fiscal_period', '')
        if fiscal_period:
            from datetime import datetime, timedelta
            try:
                # Parse YYYY-MM-DD or FY2025 format
                pd_str = str(fiscal_period)
                if 'FY' in pd_str or 'Q' in pd_str:
                    pass  # Can't easily parse FY format, skip
                else:
                    pd_date = datetime.strptime(pd_str[:10], '%Y-%m-%d')
                    if datetime.now() - pd_date > timedelta(days=180):
                        warn(
                            f"financial_data_gate: {rel} — data for '{company_slug}' is >6 months old "
                            f"(as_of_fiscal_period={fiscal_period}). May be stale."
                        )
            except Exception:
                pass

        latest_period = data.get("latest_quarter_period")
        latest_basis = data.get("latest_quarter_period_basis")
        if latest_period and latest_basis not in {"quarter", "half_year", "annual", "report_period", "cumulative_report_period"}:
            warn(
                f"financial_data_gate: {rel} бк latest_quarter_period exists but latest_quarter_period_basis is missing or invalid "
                f"for '{company_slug}'. Consumer skills may misread the latest Q/H period."
            )

        # --- Gate 3: minimum core field coverage ---
        # Subagent must have used the schema template — check 9 core fields
        CORE_FIELDS = [
            ("income_statement", "latest_fy", "revenue"),
            ("income_statement", "latest_fy", "cost_of_revenue"),
            ("income_statement", "latest_fy", "gross_profit"),
            ("income_statement", "latest_fy", "operating_income"),
            ("income_statement", "latest_fy", "net_income"),
            ("balance_sheet", "latest_fy", "total_assets"),
            ("balance_sheet", "latest_fy", "cash"),
            ("cash_flow", "latest_fy", "operating_cf"),
            ("cash_flow", "latest_fy", "capex"),
        ]
        core_filled = 0
        for section, period_key, field in CORE_FIELDS:
            if _field_value(data, section, period_key, field) is not None:
                core_filled += 1

        if core_filled < 6:
            block(
                f"Blocked by financial_data_gate: {rel} — only {core_filled}/{len(CORE_FIELDS)} core fields filled "
                f"for '{company_slug}'. Subagent likely did not use the schema template. "
                f"Re-run /financial-data --lite {company_slug} with the 38-field template."
            )

        # --- Gate 4: layer completeness ---
        tried_layer = _get_tried_layer(data)
        nulls = _count_nulls(data)

        # Filter nulls to fields that haven't been explicitly marked as not_applicable
        actionable_nulls = []
        for path in nulls:
            if path in SKIPPABLE_NULL_FIELDS:
                continue
            # Check if there's a next layer that could fill this
            for next_layer in range(tried_layer + 1, len(LAYERS)):
                if _layer_can_fill(path, next_layer):
                    actionable_nulls.append((path, next_layer))
                    break

        # Exit: core fields (IS + market_cap) are filled → warn instead of block
        core_filled = all(
            _field_value(data, "income_statement", "latest_fy", f) is not None
            for f in ["revenue", "cost_of_revenue", "sg_and_a", "r_and_d", "operating_income", "net_income"]
        )
        has_market_cap = bool(
            (isinstance(data.get("market_data", {}).get("market_cap", {}), dict) and
             data["market_data"]["market_cap"].get("value") is not None) or
            (isinstance(data.get("market_data", {}).get("market_cap"), (int, float)) and
             data["market_data"]["market_cap"] is not None)
        )

        if core_filled and has_market_cap and actionable_nulls:
            all_remaining = []
            for section in ["income_statement","balance_sheet","cash_flow","market_data","consensus","supplementary"]:
                for k, v in data.get(section, {}).items():
                    if isinstance(v, dict) and v.get("value") is None:
                        path = f"{section}.{k}"
                        if path not in SKIPPABLE_NULL_FIELDS:
                            all_remaining.append(path)
            if all_remaining:
                warn(
                    f"financial_data_gate: {rel} — core fields filled, "
                    f"{len(all_remaining)} non-core fields unavailable: {', '.join(all_remaining[:8])}. "
                    f"Mark [ND] in artifact."
                )
            continue

        # After last layer: remaining nulls are genuinely unavailable → warn only
        if tried_layer >= len(LAYERS) - 1 and nulls:
            all_remaining = []
            for section in ["income_statement","balance_sheet","cash_flow","market_data","consensus","supplementary"]:
                for k, v in data.get(section, {}).items():
                    if isinstance(v, dict) and v.get("value") is None:
                        path = f"{section}.{k}"
                        if path not in SKIPPABLE_NULL_FIELDS:
                            all_remaining.append(path)
            if not all_remaining:
                continue
            warn(
                f"financial_data_gate: {rel} — all layers tried, "
                f"{len(all_remaining)} fields unavailable from free sources: {', '.join(all_remaining[:8])}. "
                f"Mark [ND] in artifact or use EdgarTools/paid source."
            )
            continue

        if not actionable_nulls:
            continue

        # Group by next suggested layer & collect preferred sources
        market = (data.get("market") or "").lower()
        by_layer = {}
        for path, layer_idx in actionable_nulls:
            layer_name = LAYERS[layer_idx]
            by_layer.setdefault(layer_name, []).append(path)

        # Resolve preferred sources for null fields
        def _get_preferred(p, mkt):
            parts_path = p.split(".", 1)
            if len(parts_path) < 2: return ""
            sec, fld = parts_path
            fo = data.get(sec, {}).get(fld, {})
            if isinstance(fo, dict):
                ps = fo.get("preferred_source", {})
                return ps.get(mkt) or ps.get("*", "")
            return ""

        web_source_hints = {
            "official_web": set(),
            "trusted_web": set(),
            "broad_web": set(),
        }
        for layer_name in ("official_web", "trusted_web", "broad_web"):
            for p in (by_layer.get(layer_name) or []):
                s = _get_preferred(p, market)
                if s:
                    web_source_hints[layer_name].add(s)

        # Segments
        segments_msg = ""
        segments_present = False
        for layer_name in ("official_web", "trusted_web", "broad_web"):
            segment_paths = [p for p in by_layer.get(layer_name, []) if p.startswith("segments.")]
            if segment_paths:
                by_layer[layer_name] = [p for p in by_layer.get(layer_name, []) if not p.startswith("segments.")]
                segments_present = True
                break
        if segments_present:
            ss = _get_preferred("segments.status", market) or "search company IR/annual report"
            segments_msg = f"  - segments(status={_segments_status(data) or 'missing'}): {ss}\n"

        supplementary_missing = []
        for field_name in SUPPLEMENTARY_HIGH_VALUE_FIELDS:
            field_obj = data.get("supplementary", {}).get(field_name, {})
            if not (isinstance(field_obj, dict) and field_obj.get("value") is not None):
                supplementary_missing.append("supplementary." + field_name)
        sector_conditional_missing = []
        for field_name in SUPPLEMENTARY_SECTOR_CONDITIONAL_FIELDS:
            field_obj = data.get("supplementary", {}).get(field_name, {})
            if not (isinstance(field_obj, dict) and field_obj.get("value") is not None):
                sector_conditional_missing.append("supplementary." + field_name)

        provider_gap_reason_counts = {}
        for section in ["income_statement", "balance_sheet", "cash_flow", "market_data", "consensus", "supplementary"]:
            section_obj = data.get(section, {})
            if not isinstance(section_obj, dict):
                continue
            for value in section_obj.values():
                if not isinstance(value, dict):
                    continue
                reason = _provider_gap_reason(value.get("source_detail"))
                if reason:
                    provider_gap_reason_counts[reason] = provider_gap_reason_counts.get(reason, 0) + 1

        # Build message
        parts = [f"Blocked by financial_data_gate: {rel} — Lite flow incomplete for '{company_slug}'."]
        for layer_name in LAYERS:
            paths = by_layer.get(layer_name, [])
            if not paths and (layer_name not in {"official_web", "trusted_web", "broad_web"} or not segments_msg):
                continue
            sample = paths[:5]
            more = f" (+{len(paths)-5} more)" if len(paths) > 5 else ""
            field_list = ", ".join(sample) + more

            if layer_name in {"official_web", "trusted_web", "broad_web"}:
                src_hint = ""
                layer_sources = web_source_hints.get(layer_name, set())
                if layer_sources:
                    src_hint = f"\n  → {', '.join(sorted(layer_sources)[:3])}"
                label_map = {
                    "official_web": "Layer 3a (official company IR/results or official filing portals found via search)",
                    "trusted_web": "Layer 3b (trusted third-party web sources)",
                    "broad_web": "Layer 3c (broad web fallback)",
                }
                parts.append(
                    f"  {label_map[layer_name]}: {field_list}{src_hint}\n"
                    f"{segments_msg}"
                    f"Official IR/results pages first, then 东方财富/雪球 (CN+HK), Kabutan/Yahoo JP (JP), "
                    f"FnGuide/Naver (KR), Goodinfo! (TW), Finanzen.net/Boursorama/HL (EU), "
                    f"MarketScreener (consensus). See _shared/web-search-strategies.md"
                )
            elif layer_name == "provider_api":
                parts.append(
                    f"  Layer 2 (provider API / structured filing route): {field_list}\n"
                    f"  → Use EdgarTools (US) / AKShare (CN) / EDINET (JP) / "
                    f"OpenDART (KR) / FinMind (TW) / openesef (EU)"
                )

        if supplementary_missing:
            parts.append("  Supplementary high-value missing: " + ", ".join(supplementary_missing[:6]))
        if sector_conditional_missing:
            parts.append("  Supplementary sector-conditional missing (skip if undisclosed): " + ", ".join(sector_conditional_missing[:6]))
        if provider_gap_reason_counts:
            rendered = ", ".join(f"{k}={v}" for k, v in sorted(provider_gap_reason_counts.items()))
            parts.append("  Provider-gap reasons: " + rendered)

        block("\n".join(parts))
