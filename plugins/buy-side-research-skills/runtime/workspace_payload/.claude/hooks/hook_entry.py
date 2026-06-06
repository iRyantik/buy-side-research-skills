#!/usr/bin/env python
import argparse
import json
import sys
from pathlib import Path

workspace = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(workspace / ".research-runtime" / "packages"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from buy_side_research_runtime.hooks import HookDispatcher


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime", choices=("claude", "codex"), required=True)
    parser.add_argument("--event", required=True)
    args = parser.parse_args()
    payload = json.load(sys.stdin)
    payload.setdefault("cwd", str(workspace))
    HookDispatcher().dispatch(args.event, payload)
    return 0


raise SystemExit(main())
