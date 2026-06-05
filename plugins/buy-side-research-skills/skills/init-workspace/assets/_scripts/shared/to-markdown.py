#!/usr/bin/env python3
"""to-markdown — any file to clean markdown. Lightweight router.

Usage:
  python to-markdown.py <file_or_url>                        # stdout markdown
  python to-markdown.py <file> --cache <TICKER> <desc>       # stdout + _cache/
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from datetime import datetime


def _detect_format(path: str) -> str:
    """Detect file format from extension or URL scheme."""
    if path.startswith("http://") or path.startswith("https://"):
        return "web"
    ext = Path(path).suffix.lower()
    return {
        ".pdf": "pdf",
        ".docx": "docx",
        ".doc": "docx",
        ".pptx": "pptx",
        ".ppt": "pptx",
        ".xlsx": "xlsx",
        ".xls": "xlsx",
        ".xlsm": "xlsx",
        ".csv": "csv",
        ".txt": "text",
        ".md": "text",
        ".html": "web",
        ".htm": "web",
    }.get(ext, "unknown")


def _run_shared(script: str, args: list[str]) -> tuple[int, str, str]:
    """Run a shared script from the same directory as this script."""
    base = Path(__file__).parent
    cmd = [sys.executable, str(base / script)] + args
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    return r.returncode, r.stdout, r.stderr


def _cache_path(workspace: Path, ticker: str, desc: str) -> Path:
    """Resolve _cache/ path for a company. Falls back to workspace root."""
    industry_dirs = list(workspace.glob("industry/*/companies/*"))
    for d in industry_dirs:
        if ticker.lower() in d.name.lower() or ticker.split(".")[0].lower() in d.name.lower():
            return d / "_cache" / f"{ticker}-{desc}.md"
    # Fallback: workspace root _cache
    return workspace / "_cache" / f"{ticker}-{desc}.md"


def convert(filepath: str, format: str | None = None) -> tuple[str, dict | None]:
    """Convert any file to markdown. Returns (markdown, probe_info)."""
    fmt = format or _detect_format(filepath)

    if fmt == "web":
        rc, out, err = _run_shared("web-extract.py", [filepath, "--markdown"])
        if rc != 0:
            raise RuntimeError(f"web-extract failed: {err}")
        return out, None

    if fmt == "text":
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read(), None

    if fmt == "csv":
        return _csv_to_md(filepath), None

    if fmt == "pdf":
        rc, out, err = _run_shared("pdf-extract.py", [filepath, "--text"])
        if rc != 0:
            raise RuntimeError(f"pdf-extract failed: {err}")
        probe = None
        # Try to get probe info
        rc2, probe_out, _ = _run_shared("pdf-extract.py", [filepath, "--smart", "--json"])
        if rc2 == 0:
            try:
                probe = json.loads(probe_out).get("probe", {})
            except json.JSONDecodeError:
                pass
        if probe and probe.get("recommendation") == "ingest":
            pages = probe.get("pages", 0)
            text_len = probe.get("text_len", 0)
            note = (f"\n\n> ⚠️  Heavy PDF ({pages} pages, text: {text_len} chars). "
                    f"Recommend: /ingest for full Docling conversion.\n")
            return out + note, probe
        return out, probe

    # DOCX, PPTX, XLSX — extract then render
    script_map = {
        "docx": ("extract-docx.py", ["--json"]),
        "pptx": ("extract-pptx.py", ["--json"]),
        "xlsx": ("extract-xlsx.py", ["--json"]),
    }
    if fmt in script_map:
        script, extra_args = script_map[fmt]
        rc, out, err = _run_shared(script, [filepath] + extra_args)
        if rc != 0:
            raise RuntimeError(f"{script} failed: {err}")
        return _render_json_to_md(fmt, json.loads(out)), None

    raise ValueError(f"Unsupported format: {fmt}")


def _csv_to_md(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()
    if not lines:
        return ""
    headers = lines[0].split(",")
    md = ["| " + " | ".join(headers) + " |", "|---" * len(headers) + "|"]
    for line in lines[1:]:
        md.append("| " + " | ".join(line.split(",")) + " |")
    return "\n".join(md)


def _render_json_to_md(fmt: str, data) -> str:
    """Render extracted JSON to markdown for non-PDF formats."""
    if fmt == "docx":
        return _docx_to_md(data)
    if fmt == "pptx":
        return _pptx_to_md(data)
    if fmt == "xlsx":
        return _xlsx_to_md(data)
    return ""


def _docx_to_md(data: dict) -> str:
    lines = []
    for p in data.get("paragraphs", []):
        if p.get("heading"):
            lines.append(f"{'#' * p['level']} {p['text']}")
        else:
            lines.append(p["text"])
        lines.append("")
    for t in data.get("tables", []):
        if t.get("headers"):
            lines.append("| " + " | ".join(t["headers"]) + " |")
            lines.append("|---" * len(t["headers"]) + "|")
            for row in t.get("rows", []):
                lines.append("| " + " | ".join(row) + " |")
        lines.append("")
    return "\n".join(lines)


def _pptx_to_md(slides: list) -> str:
    lines = []
    for s in slides:
        lines.append(f"## Slide {s['number']}")
        if s["title"]:
            lines.append(f"**{s['title']}**")
        lines.append("")
        for t in s.get("text", []):
            lines.append(t)
            lines.append("")
        if s.get("notes"):
            lines.append(f"> Notes: {s['notes']}")
            lines.append("")
        lines.append("---")
        lines.append("")
    return "\n".join(lines)


def _xlsx_to_md(sheets: list) -> str:
    lines = []
    for s in sheets:
        lines.append(f"### {s['name']}")
        lines.append("")
        lines.append("| " + " | ".join(s["headers"]) + " |")
        lines.append("|---" * len(s["headers"]) + "|")
        for row in s.get("rows", []):
            lines.append("| " + " | ".join(row) + " |")
        lines.append("")
    return "\n".join(lines)


def _cache_header(source_url: str, pages: int = 0, source_type: str = "",
                  ticker: str = "") -> str:
    """Generate self-describing metadata header for cached markdown."""
    parts = [
        f"  source_url: {source_url}",
        f"  downloaded: {datetime.now().strftime('%Y-%m-%d')}",
        f"  converter: to-markdown.py",
    ]
    if source_type:
        parts.append(f"  source_type: {source_type}")
    if ticker:
        parts.append(f"  ticker: {ticker}")
    if pages:
        parts.append(f"  pages: {pages}")
    return "<!--\n" + "\n".join(parts) + "\n-->\n\n"


def main():
    p = argparse.ArgumentParser(description="Any file to markdown")
    p.add_argument("file", help="File path or URL")
    p.add_argument("--cache", nargs=2, metavar=("TICKER", "DESC"),
                   help="Cache output to _cache/<TICKER>-<DESC>.md")
    p.add_argument("--format", help="Force format (pdf/docx/pptx/xlsx/web/text)")
    p.add_argument("--rm", action="store_true",
                   help="Delete source file after successful cache")
    p.add_argument("--auto", action="store_true",
                   help="Silent mode: suppress stdout (for hook-driven calls)")
    p.add_argument("--source-type-top", default="",
                   help="Top-level cache dir (disclosure/sell-side/institution/primary/web/inbox)")
    p.add_argument("--source-type-sub", default="",
                   help="Sub-directory (annual/quarterly/transcript or house/source name)")
    p.add_argument("--output", help="Write markdown to this exact path (overrides --cache path logic)")
    args = p.parse_args()

    md, probe = convert(args.file, args.format)

    # Cache if requested
    if args.cache or args.output:
        if args.output:
            cp = Path(args.output)
        else:
            ticker, desc = args.cache
            ws = Path.cwd()
            cp = _cache_path(ws, ticker, f"{desc}")
        cp.parent.mkdir(parents=True, exist_ok=True)
        pages = probe.get("pages", 0) if probe else 0
        source_type = f"{args.source_type_top}/{args.source_type_sub}" if (args.source_type_top and args.source_type_sub) else ""
        header = _cache_header(
            source_url=args.file,
            pages=pages,
            source_type=source_type,
            ticker=(args.cache[0] if args.cache else ""),
        )
        with open(cp, "w", encoding="utf-8") as f:
            f.write(header + md)
        print(f"  Cached: {cp}", file=sys.stderr)
        # Delete source file on success (hook-driven auto-cache)
        if args.rm:
            try:
                os.remove(args.file)
                print(f"  Deleted: {args.file}", file=sys.stderr)
            except OSError as e:
                print(f"  WARN: could not delete {args.file}: {e}", file=sys.stderr)

    if not args.auto:
        print(md)


if __name__ == "__main__":
    main()
