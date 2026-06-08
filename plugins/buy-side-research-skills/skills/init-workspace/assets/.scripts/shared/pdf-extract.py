#!/usr/bin/env python3
"""pdf-extract — extract text and tables from PDF files or URLs.

Usage:
  python pdf-extract.py <file_or_url>              # full text
  python pdf-extract.py <file_or_url> --tables     # structured tables only (JSON)
  python pdf-extract.py <file_or_url> --text --tables  # both

Outputs to stdout. Stderr: engine used + page count.
"""
from __future__ import annotations

import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

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


# ── helpers ────────────────────────────────────────────────

def _garbled_ratio(text: str) -> float:
    """Estimate ratio of non-ASCII / garbled characters."""
    if not text:
        return 0.0
    garbled = sum(1 for c in text if c.isascii() and not c.isprintable() and c not in '\n\r\t ')
    total = len(text)
    return garbled / total if total > 0 else 0.0


def _to_markdown(text: str, tables: list[dict]) -> str:
    """Render text + tables as markdown."""
    lines = []
    if text:
        lines.append(text.strip())
        lines.append("")
    for t in tables:
        rows = t.get("rows", [])
        if not rows or len(rows) < 2:
            continue
        headers = rows[0]
        lines.append("| " + " | ".join(headers) + " |")
        lines.append("|---" * len(headers) + "|")
        for row in rows[1:]:
            # Pad short rows
            padded = row + [""] * (len(headers) - len(row))
            lines.append("| " + " | ".join(padded[:len(headers)]) + " |")
        lines.append("")
    return "\n".join(lines)


# ── main ─────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Extract text and tables from PDF")
    parser.add_argument("input", help="PDF file path or URL")
    parser.add_argument("--tables", action="store_true", help="Output structured tables (JSON)")
    parser.add_argument("--text", action="store_true", help="Output full text (default)")
    parser.add_argument("--engine", default="auto",
                       help="auto (pymupdf->pdfplumber->pypdf) | pymupdf | pdfplumber | pypdf | all")
    parser.add_argument("--tables-only", action="store_true",
                       help="Only extract tables (skip text)")
    parser.add_argument("--smart", action="store_true",
                       help="Probe PDF complexity, route fast or recommend /ingest")
    parser.add_argument("--markdown", action="store_true",
                       help="Output as markdown (text + rendered tables)")
    args = parser.parse_args()

    # Default: text only
    if not args.tables and not args.text:
        args.text = True
    if args.tables_only:
        args.tables = True
        args.text = False

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

    # ── engine dispatch ──────────────────────────────────
    _ENGINES = dict(pymupdf=_try_pymupdf, pdfplumber=_try_pdfplumber, pypdf=lambda p: (_try_pypdf(p), []))
    _FALLBACK = ["pymupdf", "pdfplumber", "pypdf"]

    text = None
    tables = []
    engines_used = []

    if args.engine == "all":
        # Run all engines, merge results
        for name in _FALLBACK:
            fn = _ENGINES.get(name)
            if not fn:
                continue
            result = fn(path)
            if result is None:
                continue
            t, tb = result
            engines_used.append(name)
            if not text and t:
                text = t
            if tb:
                tables.extend(tb)
    elif args.engine in _ENGINES:
        # Single engine
        name = args.engine
        fn = _ENGINES[name]
        result = fn(path)
        if result is None:
            print(json.dumps({"error": f"engine {name} failed or not installed"}), file=sys.stderr)
            sys.exit(1)
        text, tables = result
        if isinstance(tables, type(None)):
            tables = []
        engines_used = [name]
    else:
        # auto: first-success fallback
        for name in _FALLBACK:
            fn = _ENGINES.get(name)
            if not fn:
                continue
            result = fn(path)
            if result is None:
                continue
            text, tables = result
            if isinstance(tables, type(None)):
                tables = []
            engines_used = [name]
            break

    # Cleanup temp file
    if tmp:
        try:
            os.unlink(tmp)
        except OSError:
            pass

    if not text and not tables:
        print(json.dumps({"error": f"all PDF engines failed (tried: {', '.join(_FALLBACK)})"}), file=sys.stderr)
        sys.exit(1)

    # Report engine to stderr
    page_count = (text or "").count("\f") + 1 if text and "\f" in text else (len((text or "").split("\n")) // 50 + 1)
    print(f"engine={'+'.join(engines_used)} pages~{page_count}", file=sys.stderr)

    # ── smart probe ────────────────────────────────────
    if args.smart:
        text_len = len(text or "")
        is_scanned = text_len < 200 or (text_len > 0 and _garbled_ratio(text or "") > 0.3)
        has_tables = len(tables) > 0
        rec = "ingest" if (is_scanned or page_count > 30 or (has_tables and text_len < 500)) else "fast"
        probe = {
            "engine": engines_used[0] if engines_used else "none",
            "pages": page_count,
            "text_len": text_len,
            "has_tables": has_tables,
            "is_scanned": is_scanned,
            "recommendation": rec,
            "note": "Use /ingest for full Docling conversion" if rec == "ingest" else "Fast path OK",
        }
        if args.json:
            print(json.dumps({"text": text, "tables": tables, "probe": probe}, ensure_ascii=False))
            sys.exit(0)
        if rec == "ingest":
            print(f"Heavy PDF detected ({page_count}p, scanned={is_scanned}, tables={has_tables})", file=sys.stderr)
            print("Use /ingest for full Docling conversion", file=sys.stderr)

    # ── markdown render ────────────────────────────────
    if args.markdown:
        md = _to_markdown(text or "", tables)
        print(md)
        sys.exit(0)

    # Output
    if args.text and args.tables:
        print(json.dumps({"text": text, "tables": tables}, ensure_ascii=False))
    elif args.tables:
        print(json.dumps(tables, indent=2, ensure_ascii=False))
    else:
        print(text)


if __name__ == "__main__":
    main()
