#!/usr/bin/env python
from pathlib import Path
import sys

HERE = Path(__file__).resolve()
for candidate in (
    HERE.parents[1] / ".research-runtime" / "packages",
    HERE.parents[2],
):
    if (candidate / "buy_side_research_runtime").is_dir():
        sys.path.insert(0, str(candidate))
        break
from buy_side_research_runtime.cli.runtime_manager import main

raise SystemExit(main())
