#!/usr/bin/env python3
"""pdf-to-md.py — Convert PDF to markdown using MarkItDown.

Usage:
    python pdf-to-md.py <input.pdf> [--output <path>]

Engine: MarkItDown (Microsoft) — fast, lightweight, handles large files.
If no --output, writes to <input_stem>.md in same directory.
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path


def convert(input_path: Path, output_path: Path) -> dict:
    t0 = time.perf_counter()
    from markitdown import MarkItDown

    md = MarkItDown()
    result = md.convert(str(input_path))
    text = result.text_content or ""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text, encoding="utf-8")

    elapsed = round(time.perf_counter() - t0, 1)
    size = len(text)

    return {
        "status": "converted",
        "engine": "markitdown",
        "input": str(input_path),
        "output": str(output_path),
        "elapsed_sec": elapsed,
        "chars": size,
    }


def main():
    parser = argparse.ArgumentParser(description="Convert PDF to markdown")
    parser.add_argument("input", help="PDF file path")
    parser.add_argument("--output", "-o", help="Output markdown path (default: <input_stem>.md)")
    args = parser.parse_args()

    src = Path(args.input)
    if not src.exists():
        print(f"ERROR: file not found: {src}", file=sys.stderr)
        sys.exit(1)

    dst = Path(args.output) if args.output else src.with_suffix(".md")
    result = convert(src, dst)

    print(f"OK {result['elapsed_sec']}s {result['chars']:,} chars -> {dst}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
