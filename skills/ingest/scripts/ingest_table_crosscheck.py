#!/usr/bin/env python3
"""Lightweight numeric-token cross-check between two extracted table texts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

NUMBER_PATTERN = re.compile(r"(?<![A-Za-z])[-+]?\$?\d[\d,]*(?:\.\d+)?%?")


def numeric_tokens(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    return NUMBER_PATTERN.findall(text)


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare numeric tokens in two extracted table/text files.")
    parser.add_argument("left")
    parser.add_argument("right")
    args = parser.parse_args()

    left = numeric_tokens(Path(args.left))
    right = numeric_tokens(Path(args.right))
    left_set = set(left)
    right_set = set(right)
    payload = {
        "left_count": len(left),
        "right_count": len(right),
        "missing_from_right": sorted(left_set - right_set)[:100],
        "missing_from_left": sorted(right_set - left_set)[:100],
        "note": "Token-level check only; manually verify tables and units in the original source.",
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
