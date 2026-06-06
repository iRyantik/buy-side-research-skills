#!/usr/bin/env python
"""Deprecated development-repo wrapper for the workspace Financial Data CLI."""

from pathlib import Path
import runpy

entry = Path.cwd() / "_scripts" / "financial-data.py"
if not entry.is_file():
    raise SystemExit("Run `python _scripts/financial-data.py ...` from an initialized workspace.")
runpy.run_path(str(entry), run_name="__main__")
