#!/usr/bin/env python3
"""pdf-extract — extract text and tables from PDF files or URLs.

Usage:
  python pdf-extract.py <file_or_url>              # full text
  python pdf-extract.py <file_or_url> --tables     # structured tables only (JSON)
  python pdf-extract.py <file_or_url> --text --tables  # both

Outputs to stdout. Stderr: engine used + page count.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path
from urllib.request import urlopen, Request

# ── download ────────────────────────────────────────────

def _download(url: str) -> Path:
    """Download URL to temp file. Returns path."""
    req = Request(url, headers={"User-Agent": "pdf-extract/1.0"})
    with urlopen(req, timeout=30) as resp:
        data = resp.read()
    suffix = ".pdf" if url.lower().endswith(".pdf") else ""
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(data)
    tmp.close()
    return Path(tmp.name)


# ── engines ──────────────────────────────────────────────

def _try_pymupdf(path: Path) -> tuple[str, list[dict]] | None:
    """PyMuPDF4LLM — best quality. Returns (full_text, tables)."""
    try:
        import fitz
    except ImportError:
        return None
    doc = fitz.open(str(path))
    full_text = []
    tables = []
    for page in doc:
        full_text.append(page.get_text())
        for tab in page.find_tables():
            if tab.row_count > 1:
                tables.append({
                    "page": page.number + 1,
                    "rows": [[cell.text if cell.text else "" for cell in row.cells] for row in tab.rows],
                })
    doc.close()
    return "\n".join(full_text), tables


def _try_pdfplumber(path: Path) -> tuple[str, list[dict]] | None:
    """pdfplumber — reliable fallback."""
    try:
        import pdfplumber
    except ImportError:
        return None
    full_text = []
    tables = []
    with pdfplumber.open(str(path)) as pdf:
        for i, page in enumerate(pdf.pages):
            t = page.extract_text()
            if t:
                full_text.append(t)
            for tab in page.extract_tables():
                if tab and len(tab) > 1:
                    tables.append({
                        "page": i + 1,
                        "rows": [[str(cell) if cell is not None else "" for cell in row] for row in tab],
                    })
    return "\n".join(full_text), tables


def _try_pypdf(path: Path) -> str | None:
    """pypdf — last resort."""
    try:
        from pypdf import PdfReader
    except ImportError:
        return None
    reader = PdfReader(str(path))
    parts = []
    for page in reader.pages:
        t = page.extract_text()
        if t:
            parts.append(t)
    return "\n".join(parts)


# ── main ─────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Extract text and tables from PDF")
    parser.add_argument("input", help="PDF file path or URL")
    parser.add_argument("--tables", action="store_true", help="Output structured tables (JSON)")
    parser.add_argument("--text", action="store_true", help="Output full text (default)")
    args = parser.parse_args()

    # Default: text only
    if not args.tables and not args.text:
        args.text = True

    # Resolve input
    inp = args.input
    is_url = inp.startswith("http://") or inp.startswith("https://")
    tmp = None

    if is_url:
        try:
            tmp = _download(inp)
            path = tmp
        except Exception as e:
            print(json.dumps({"error": f"download failed: {e}"}), file=sys.stderr)
            sys.exit(1)
    else:
        path = Path(inp)
        if not path.exists():
            print(json.dumps({"error": f"file not found: {inp}"}), file=sys.stderr)
            sys.exit(1)

    # Try engines
    text = None
    tables = None
    engine = "none"

    for try_engine, name in [(_try_pymupdf, "pymupdf"), (_try_pdfplumber, "pdfplumber"), (None, "pypdf")]:
        if name == "pypdf":
            text = _try_pypdf(path)
            engine = "pypdf"
            tables = []
            break
        result = try_engine(path)
        if result is not None:
            text, tables = result
            engine = name
            break

    # Cleanup temp file
    if tmp:
        try:
            os.unlink(tmp)
        except OSError:
            pass

    if text is None:
        print(json.dumps({"error": "all PDF engines failed (pymupdf/pdfplumber/pypdf not installed?)"}), file=sys.stderr)
        sys.exit(1)

    # Report engine to stderr
    page_count = text.count("\f") + 1 if "\f" in text else len(text.split("\n")) // 50 + 1
    print(f"engine={engine} pages~{page_count}", file=sys.stderr)

    # Output
    if args.text and args.tables:
        print(json.dumps({"text": text, "tables": tables}, ensure_ascii=False))
    elif args.tables:
        print(json.dumps(tables, indent=2, ensure_ascii=False))
    else:
        print(text)


if __name__ == "__main__":
    main()
