#!/usr/bin/env python3
"""image-to-md.py — Describe an image using LLM Vision.

Usage:
    python image-to-md.py <input.png|jpg> [--output <path>]

Outputs a markdown description of the image contents.
The actual LLM Vision call is done by the agent — this script
prepares the image metadata and prints instructions.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def convert(input_path: Path, output_path: Path) -> dict:
    from PIL import Image

    img = Image.open(input_path)
    w, h = img.size
    fmt = img.format or "unknown"

    prompt = f"""Describe this image in detail. Include:
- What is shown (chart, product photo, diagram, screenshot, etc.)
- Key data or text visible in the image
- Any notable visual elements

Image: {input_path.name} ({fmt}, {w}x{h}px)"""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    text = f"""# Image: {input_path.name}

- **Format**: {fmt}
- **Dimensions**: {w} × {h} pixels
- **Size**: {input_path.stat().st_size:,} bytes

## Description

[LLM Vision description pending — agent should process this image]

<!--
Vision prompt for agent:
{prompt}
-->
"""
    output_path.write_text(text, encoding="utf-8")

    return {
        "status": "prepared",
        "engine": "llm-vision",
        "format": fmt,
        "dimensions": f"{w}x{h}",
        "chars": len(text),
    }


def main():
    parser = argparse.ArgumentParser(description="Describe an image for LLM consumption")
    parser.add_argument("input", help="Image file path (.png/.jpg/.webp)")
    parser.add_argument("--output", "-o", help="Output markdown path")
    args = parser.parse_args()

    src = Path(args.input)
    if not src.exists():
        print(f"ERROR: file not found: {src}", file=sys.stderr)
        sys.exit(1)

    dst = Path(args.output) if args.output else src.with_suffix(".md")
    result = convert(src, dst)
    print(f"OK {result['format']} {result['dimensions']} → {dst}")
    print("  Agent: use LLM Vision to fill the [description pending] section.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
