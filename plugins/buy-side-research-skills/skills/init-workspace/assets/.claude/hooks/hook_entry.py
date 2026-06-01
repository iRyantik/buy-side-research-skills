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
    "source_contract",
    "table_render_integrity",
    "image_exists",
    "data_claim_cross_check",
    "subagent_protocol",
    "skill_structure_contract",
]
STOP_RULES = [
    "source_contract",
]


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

    # Route to rules based on event
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

    sys.exit(0)


if __name__ == "__main__":
    main()
