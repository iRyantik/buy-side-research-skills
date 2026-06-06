#!/usr/bin/env python3
"""Cross-check PDFPlumber table numerics against an extracted markdown file."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any

NUMBER_PATTERN = re.compile(r"(?<![A-Za-z])[-+]?\$?\d[\d,]*(?:\.\d+)?%?")


def numeric_tokens_from_text(text: str) -> list[str]:
    return NUMBER_PATTERN.findall(text)


def markdown_numeric_tokens(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    return numeric_tokens_from_text(text)


def pdfplumber_tables(path: Path) -> dict[str, Any]:
    try:
        import pdfplumber  # type: ignore
    except ImportError as exc:
        raise RuntimeError("Missing optional dependency: pdfplumber. Install with `pip install pdfplumber`.") from exc

    pages = []
    table_count = 0
    all_numbers: list[str] = []

    with pdfplumber.open(str(path)) as pdf:
        for page_index, page in enumerate(pdf.pages, start=1):
            tables = page.extract_tables() or []
            table_count += len(tables)
            page_numbers: list[str] = []
            previews = []
            for table_index, table in enumerate(tables, start=1):
                rows = table or []
                table_text = "\n".join(
                    "\t".join("" if cell is None else str(cell) for cell in row)
                    for row in rows
                )
                tokens = numeric_tokens_from_text(table_text)
                page_numbers.extend(tokens)
                all_numbers.extend(tokens)
                previews.append(
                    {
                        "table_index": table_index,
                        "row_count": len(rows),
                        "column_count": max((len(row) for row in rows), default=0),
                        "numeric_token_count": len(tokens),
                        "preview_rows": rows[:5],
                    }
                )
            pages.append(
                {
                    "page": page_index,
                    "table_count": len(tables),
                    "numeric_token_count": len(page_numbers),
                    "tables": previews,
                }
            )

    return {
        "page_count": len(pages),
        "table_count": table_count,
        "numeric_tokens": all_numbers,
        "pages": pages,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare PDFPlumber table numerics against cache markdown.")
    parser.add_argument("pdf_path", help="Original PDF path.")
    parser.add_argument("markdown_path", help="Markdown produced by PDF extraction pipeline.")
    parser.add_argument("--max-diff", type=int, default=100, help="Maximum tokens to list per side.")
    args = parser.parse_args()

    pdf_path = Path(args.pdf_path).expanduser().resolve()
    markdown_path = Path(args.markdown_path).expanduser().resolve()

    if not pdf_path.exists():
        print(json.dumps({"status": "failed", "error": f"PDF does not exist: {pdf_path}"}, ensure_ascii=False, indent=2))
        return 1
    if not markdown_path.exists():
        print(json.dumps({"status": "failed", "error": f"Markdown does not exist: {markdown_path}"}, ensure_ascii=False, indent=2))
        return 1

    try:
        pdf_summary = pdfplumber_tables(pdf_path)
        pdf_numbers = pdf_summary["numeric_tokens"]
        markdown_numbers = markdown_numeric_tokens(markdown_path)
        pdf_set = set(pdf_numbers)
        markdown_set = set(markdown_numbers)
        payload = {
            "status": "completed",
            "pdf": str(pdf_path),
            "markdown": str(markdown_path),
            "page_count": pdf_summary["page_count"],
            "table_count": pdf_summary["table_count"],
            "pdf_table_numeric_count": len(pdf_numbers),
            "markdown_numeric_count": len(markdown_numbers),
            "missing_from_markdown": sorted(pdf_set - markdown_set)[: args.max_diff],
            "extra_in_markdown": sorted(markdown_set - pdf_set)[: args.max_diff],
            "pages": pdf_summary["pages"],
            "note": "PDFPlumber table extraction is a numeric cross-check only; verify table labels, units, signs, and page references manually.",
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}, ensure_ascii=False, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
