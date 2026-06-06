#!/usr/bin/env python
"""Deprecated compatibility wrapper for the canonical Financial Data CLI."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / ".research-runtime" / "packages"))
from buy_side_research_runtime.cli.financial_data import main

print("DEPRECATED: use `python _scripts/financial-data.py ...`.", file=sys.stderr)
raise SystemExit(main(sys.argv[1:]))
