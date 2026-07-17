#!/usr/bin/env python3
"""url-to-md.py — Fetch a URL and convert its content to markdown.

Usage:
    python url-to-md.py <url> [--output <path>]

Detects content type and routes to the appropriate converter:
    - PDF → pdf-to-md.py
    - XLSX → xlsx-to-md.py
    - DOCX → docx-to-md.py
    - HTML → WebFetch + clean
    - Other → raw save + type note
"""
from __future__ import annotations

import argparse
import sys
import urllib.request
from pathlib import Path


def detect_and_convert(url: str, output_path: Path) -> dict:
    # Download and detect content type
    req = urllib.request.Request(url, headers={"User-Agent": "url-to-md/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        content_type = resp.headers.get("Content-Type", "")
        data = resp.read()

    ct_lower = content_type.lower()

    # Route based on content type
    if "pdf" in ct_lower or url.lower().endswith(".pdf"):
        # Save PDF and route to pdf-to-md
        pdf_path = output_path.with_suffix(".pdf")
        pdf_path.parent.mkdir(parents=True, exist_ok=True)
        pdf_path.write_bytes(data)
        from ingest.pdf_to_md import convert as pdf_convert
        result = pdf_convert(pdf_path, output_path)
        result["route"] = "url→pdf→md"
        return result

    if "html" in ct_lower:
        # Save HTML and strip tags
        text = _html_to_text(data)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(text, encoding="utf-8")
        return {
            "status": "converted",
            "engine": "html-strip",
            "route": "url→html→md",
            "chars": len(text),
            "content_type": content_type,
        }

    # Unknown type — save raw
    raw_path = output_path.with_suffix(".bin")
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_bytes(data)
    note = f"# {url}\n\nContent-Type: {content_type}\nSize: {len(data):,} bytes\nSaved to: {raw_path}"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(note, encoding="utf-8")
    return {
        "status": "unknown_type",
        "engine": "raw-save",
        "route": "url→raw",
        "chars": len(note),
        "content_type": content_type,
    }


def _html_to_text(data: bytes) -> str:
    """Simple HTML tag stripper."""
    import re
    text = data.decode("utf-8", errors="replace")
    text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def main():
    parser = argparse.ArgumentParser(description="Fetch URL and convert to markdown")
    parser.add_argument("url", help="URL to fetch")
    parser.add_argument("--output", "-o", help="Output markdown path")
    args = parser.parse_args()

    output = Path(args.output) if args.output else Path("output.md")
    result = detect_and_convert(args.url, output)
    ctype = result.get("content_type", "")
    print(f"OK [{result['route']}] {result.get('chars', 0):,} chars ({ctype}) → {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
