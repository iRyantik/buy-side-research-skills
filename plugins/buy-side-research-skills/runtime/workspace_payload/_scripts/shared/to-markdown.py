#!/usr/bin/env python
"""Deprecated pure conversion wrapper; it never routes, moves, or deletes sources."""

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / ".research-runtime" / "packages"))
from buy_side_research_runtime.source_intake.converters import convert_source

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("source")
args = parser.parse_args()
print("DEPRECATED: use Source Intake for publishing.", file=sys.stderr)
sys.stdout.write(convert_source(Path(args.source)).markdown)
