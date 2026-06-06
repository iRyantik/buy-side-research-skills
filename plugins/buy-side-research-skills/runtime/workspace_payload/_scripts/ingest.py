#!/usr/bin/env python
"""Deprecated compatibility wrapper for Source Intake."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / ".research-runtime" / "packages"))
from buy_side_research_runtime.cli.source_intake import main

print("DEPRECATED: use `python _scripts/source-intake.py add ...`.", file=sys.stderr)
raise SystemExit(main(["add", *sys.argv[1:]]))
