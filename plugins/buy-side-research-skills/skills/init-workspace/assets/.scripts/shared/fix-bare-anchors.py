#!/usr/bin/env python3
"""fix-bare-anchors.py — scan a research artifact, find bare [S#]/[I#] anchors,
resolve them against the ## Resources section, and print corrected markdown.

Usage:
  python fix-bare-anchors.py <artifact.md>             # stdout
  python fix-bare-anchors.py <artifact.md> --in-place   # overwrite file
"""

from __future__ import annotations

import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

import argparse
import re
from pathlib import Path


def parse_resources(text: str) -> dict[str, str]:
    """Extract {code: url} from ## Resources section."""
    resources: dict[str, str] = {}
    match = re.search(r'(?ims)^##\s*Resources\b(.*?)(?:^##\s|\Z)', text)
    if not match:
        return resources

    section = match.group(1)
    for line in section.split("\n"):
        m = re.match(r'^\s*-\s*\[([^\]]+)\]\(([^)]+)\)', line)
        if m:
            resources[m.group(1).strip()] = m.group(2).strip()
    return resources


def fix_bare_anchors(text: str) -> tuple[str, int]:
    """Replace bare [S#] and [I#] with linked versions. Returns (fixed_text, count)."""
    resources = parse_resources(text)
    if not resources:
        return text, 0

    count = 0
    # Match [S#] or [I#] that are NOT already followed by (
    def replace_bare(m: re.Match) -> str:
        nonlocal count
        code = m.group(0).strip("[]")
        url = resources.get(code)
        if url:
            count += 1
            return f"[{code}]({url})"
        return m.group(0)

    # Only match bare anchors on non-Resources lines
    lines = text.split("\n")
    in_resources = False
    fixed_lines = []
    for line in lines:
        if re.match(r'^##\s*Resources\b', line):
            in_resources = True
        elif re.match(r'^##\s', line):
            in_resources = False

        if in_resources:
            fixed_lines.append(line)
        else:
            # Match [S<digits>] or [I<digits>] followed by non-(
            fixed = re.sub(
                r'\[([SI]\d+)\](?!\()',
                replace_bare,
                line
            )
            fixed_lines.append(fixed)

    fixed = "\n".join(fixed_lines)
    # Post-process: detect and fix || merged table cells (bug #3)
    fixed = re.sub(r'\|\s*\|\s*\|', '| |', fixed)
    return fixed, count


def main():
    p = argparse.ArgumentParser(description="Fix bare source anchors in research artifacts")
    p.add_argument("artifact", help="Path to artifact.md")
    p.add_argument("--in-place", action="store_true", help="Overwrite file instead of stdout")
    args = p.parse_args()

    path = Path(args.artifact)
    if not path.is_file():
        print(f"ERROR: {path} not found", file=sys.stderr)
        return 1

    text = path.read_text(encoding="utf-8")
    fixed, count = fix_bare_anchors(text)

    if count == 0:
        print(f"No bare anchors found in {path.name}")
        return 0

    if args.in_place:
        path.write_text(fixed, encoding="utf-8")
        print(f"Fixed {count} bare anchors in {path.name}")
    else:
        print(fixed)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
