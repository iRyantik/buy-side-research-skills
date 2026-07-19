#!/usr/bin/env python3
"""pdf-to-md.py — Convert PDF to markdown.

Usage:
    python pdf-to-md.py <input.pdf> [--output <path>] [--engine pymupdf4llm|markitdown]

Engines:
    pymupdf4llm (default) — Best for financial reports. Preserves table structure,
        line items, and percentages even for complex multi-column layouts.
        Slower (~60-90s for 100+ page PDFs) but far more complete extraction.

    markitdown (fallback) — Microsoft's doc-to-markdown converter.
        Faster (~30s) but loses data in multi-column PDF layouts.
        Use for simple/single-column PDFs or when pymupdf4llm is unavailable.
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path


def convert_markitdown(input_path: Path, output_path: Path) -> dict:
    from markitdown import MarkItDown
    md = MarkItDown()
    result = md.convert(str(input_path))
    text = result.text_content or ""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text, encoding="utf-8")
    return {"text": text, "chars": len(text)}


def convert_pymupdf4llm(input_path: Path, output_path: Path) -> dict:
    import pymupdf4llm
    text = pymupdf4llm.to_markdown(str(input_path))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text, encoding="utf-8")
    return {"text": text, "chars": len(text)}


def convert(input_path: Path, output_path: Path, engine: str = "pymupdf4llm") -> dict:
    t0 = time.perf_counter()

    if engine == "pymupdf4llm":
        try:
            result = convert_pymupdf4llm(input_path, output_path)
            used_engine = "pymupdf4llm"
        except ImportError:
            print("  WARN: pymupdf4llm not installed, falling back to markitdown", file=sys.stderr)
            print("  Install: pip install pymupdf4llm", file=sys.stderr)
            result = convert_markitdown(input_path, output_path)
            used_engine = "markitdown"
    else:
        result = convert_markitdown(input_path, output_path)
        used_engine = "markitdown"

    elapsed = round(time.perf_counter() - t0, 1)

    return {
        "status": "converted",
        "engine": used_engine,
        "input": str(input_path),
        "output": str(output_path),
        "elapsed_sec": elapsed,
        "chars": result["chars"],
    }


def main():
    parser = argparse.ArgumentParser(description="Convert PDF to markdown")
    parser.add_argument("input", help="PDF file path")
    parser.add_argument("--output", "-o", help="Output markdown path (default: <input_stem>.md)")
    parser.add_argument("--engine", choices=("pymupdf4llm", "markitdown"),
                        default="pymupdf4llm",
                        help="PDF engine (default: pymupdf4llm)")
    args = parser.parse_args()

    src = Path(args.input)
    if not src.exists():
        print(f"ERROR: file not found: {src}", file=sys.stderr)
        sys.exit(1)

    dst = Path(args.output) if args.output else src.with_suffix(".md")
    result = convert(src, dst, args.engine)

    print(f"OK {result['elapsed_sec']}s {result['chars']:,} chars -> {dst}  (engine: {result['engine']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
