"""Unified hook entry point.

Usage:
  python hook_entry.py --runtime claude --event PostToolUse
  python hook_entry.py --runtime codex --event PreToolUse
"""
import sys, os, argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import load_stdin_payload

RUNTIMES = {"claude", "codex"}

# Rule routing table
PRE_TOOL_USE_RULES = [
    "workspace_guard",
    "financial_data_gate",
]
POST_TOOL_USE_RULES = [
    # Global structure & source
    "source_contract",
    "table_render_integrity",
    "image_exists",
    "data_claim_cross_check",
    "subagent_protocol",
    "skill_structure_contract",
    # Provider: market-snapshot + disclosure source boundaries
    "provider.market_snapshot_source_boundary",
    "provider.disclosure_fact_source_boundary",
    "provider.social_clue_only",
    # Viz: delivery contract
    "viz.viz_delivery_contract",
    # Fact governance: provenance + claim proximity
    "fact_provenance",
    "claim_source_proximity",
]
STOP_RULES = [
    "source_contract",
]
# Modeling rules — xlsx-only, standalone pattern (use model dispatch, not check(ctx))
MODELING_RULES = [
    "model_checks_result",
    "model_balance_integrity",
    "model_driver_breakdown",
    "model_historical_actuals",
    "model_missing_actuals",
    "model_no_hardcoded",
    "model_statement_presence",
    "model_statement_structure",
    "model_update_change_map",
    "model_valuation_basis",
    # ps1 migration
    "comps_structure_floor",
    "dcf_audit_floor",
    "dcf_structure_floor",
    "three_statement_audit_floor",
    "three_statement_driver_floor",
    # C-level: data fidelity + cross-artifact linkage
    "model_meta_sheet",
    "model_actuals_cross_check",
    "model_driver_cross_check",
    "model_internal_consistency",
    "model_period_floor",
    "model_dcf_linked_to_3sm",
    "model_dcf_input_sourcing",
    "model_dcf_tv_wacc_sanity",
    "model_comps_sourced",
    "model_comps_denominator_parity",
]


def _has_xlsx_targets(payload: dict) -> bool:
    """Check if any target is an xlsx file."""
    for t in payload.get("targets", []):
        if t.get("kind") == "file" and (t.get("path", "") or "").endswith(".xlsx"):
            return True
    return False


def _run_modeling_rules(payload: dict):
    """Run modeling rules that use standalone stdin pattern.
    Feed the raw payload as JSON to sys.stdin, import each rule module
    (which executes at module level), then restore sys.stdin."""
    import io, importlib, json as _json

    old_stdin = sys.stdin
    try:
        sys.stdin = io.StringIO(_json.dumps(payload))
        for name in MODELING_RULES:
            try:
                importlib.import_module(f"rules.modeling.{name}")
            except ImportError:
                pass  # Modeling rule not available — skip
            except Exception as e:
                sys.stderr.write(f"hook_entry: modeling rule {name} raised {e}\n")
    finally:
        sys.stdin = old_stdin


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime", required=True, choices=sorted(RUNTIMES))
    parser.add_argument("--event", required=True)
    args = parser.parse_args()

    payload = load_stdin_payload()
    if payload is None:
        sys.stderr.write("hook_entry: no payload on stdin\n")
        sys.exit(1)

    if args.runtime == "claude":
        from adapters.claude import build_context
    else:
        from adapters.codex import build_context

    ctx = build_context(payload)

    if args.event == "PreToolUse":
        rule_names = PRE_TOOL_USE_RULES
    elif args.event == "PostToolUse":
        rule_names = POST_TOOL_USE_RULES
    elif args.event == "Stop":
        rule_names = STOP_RULES
    else:
        rule_names = []

    for name in rule_names:
        import importlib
        mod = importlib.import_module(f"rules.{name}")
        mod.check(ctx)

    # Modeling dispatch: run standalone xlsx rules when xlsx targets present
    if args.event == "PostToolUse" and _has_xlsx_targets(payload):
        _run_modeling_rules(payload)

    sys.exit(0)


if __name__ == "__main__":
    main()
