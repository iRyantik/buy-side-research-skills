#!/usr/bin/env python3
"""Convert raw research files into source-tracked markdown cache files."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import html
import json
import os
from pathlib import Path
import sys
from typing import Callable

SUPPORTED_EXTENSIONS = {
    ".txt",
    ".md",
    ".markdown",
    ".csv",
    ".xlsx",
    ".xlsm",
    ".docx",
    ".pptx",
    ".pdf",
}


class IngestError(RuntimeError):
    pass


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_text_lossy(path: Path) -> str:
    data = path.read_bytes()
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def markdown_header(source: Path, converter: str, precision: str) -> str:
    modified = dt.datetime.fromtimestamp(source.stat().st_mtime, dt.timezone.utc)
    metadata = {
        "source_path": str(source),
        "source_sha256": sha256_file(source),
        "source_modified_utc": modified.replace(microsecond=0).isoformat(),
        "converter": converter,
        "converted_at_utc": utc_now(),
        "precision": precision,
    }
    body = "\n".join(f"{key}: {value}" for key, value in metadata.items())
    return f"<!--\n{body}\n-->\n\n"


def convert_markdown(path: Path) -> tuple[str, str, str]:
    return read_text_lossy(path), "native-markdown", "native markdown; verify quoted facts against original source"


def convert_text(path: Path) -> tuple[str, str, str]:
    text = read_text_lossy(path)
    return f"# {path.name}\n\n```text\n{text}\n```\n", "native-text", "plain text extraction"


def convert_csv(path: Path) -> tuple[str, str, str]:
    text = read_text_lossy(path)
    rows = list(csv.reader(text.splitlines()))
    preview_rows = rows[:200]
    output = [f"# {path.name}", "", "## CSV Preview", ""]
    if preview_rows:
        width = max(len(row) for row in preview_rows)
        normalized = [row + [""] * (width - len(row)) for row in preview_rows]
        output.append("| " + " | ".join(html.escape(cell) for cell in normalized[0]) + " |")
        output.append("| " + " | ".join("---" for _ in normalized[0]) + " |")
        for row in normalized[1:]:
            output.append("| " + " | ".join(html.escape(cell) for cell in row) + " |")
    else:
        output.append("[empty csv]")
    output.extend(["", "## Raw CSV", "", "```csv", text, "```", ""])
    return "\n".join(output), "native-csv", "CSV parsed with Python csv; inspect original for dialect/encoding issues"


def convert_xlsx(path: Path) -> tuple[str, str, str]:
    scripts_dir = Path(__file__).resolve().parent
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    try:
        from ingest_xlsx import workbook_to_markdown
    except ImportError as exc:
        raise IngestError("Missing optional dependency for XLSX ingest: openpyxl. Install with `pip install openpyxl`.") from exc
    return workbook_to_markdown(path), "openpyxl", "workbook structure extraction; verify formulas and key numbers in Excel"


def convert_docx(path: Path) -> tuple[str, str, str]:
    try:
        import docx  # type: ignore
    except ImportError as exc:
        raise IngestError("Missing optional dependency for DOCX ingest: python-docx. Install with `pip install python-docx`.") from exc

    document = docx.Document(str(path))
    parts = [f"# {path.name}", ""]
    for paragraph in document.paragraphs:
        text = paragraph.text.strip()
        if text:
            parts.append(text)
            parts.append("")
    for idx, table in enumerate(document.tables, start=1):
        parts.append(f"## Table {idx}")
        for row in table.rows:
            cells = [cell.text.replace("\n", " ").strip() for cell in row.cells]
            parts.append("| " + " | ".join(html.escape(cell) for cell in cells) + " |")
        parts.append("")
    return "\n".join(parts), "python-docx", "DOCX text/table extraction; verify layout-sensitive content in original"


def convert_pptx(path: Path) -> tuple[str, str, str]:
    try:
        from pptx import Presentation  # type: ignore
    except ImportError as exc:
        raise IngestError("Missing optional dependency for PPTX ingest: python-pptx. Install with `pip install python-pptx`.") from exc

    deck = Presentation(str(path))
    parts = [f"# {path.name}", ""]
    for idx, slide in enumerate(deck.slides, start=1):
        parts.append(f"## Slide {idx}")
        for shape in slide.shapes:
            if hasattr(shape, "text"):
                text = shape.text.strip()
                if text:
                    parts.append(text)
        try:
            notes = slide.notes_slide.notes_text_frame.text.strip()
            if notes:
                parts.extend(["", "### Speaker Notes", notes])
        except Exception:
            pass
        parts.append("")
    return "\n".join(parts), "python-pptx", "PPTX text extraction; verify charts/images in original deck"


def convert_pdf(path: Path) -> tuple[str, str, str]:
    try:
        from pypdf import PdfReader  # type: ignore
    except ImportError:
        try:
            from PyPDF2 import PdfReader  # type: ignore
        except ImportError as exc:
            raise IngestError("Missing optional dependency for PDF ingest: pypdf. Install with `pip install pypdf`.") from exc

    reader = PdfReader(str(path))
    parts = [f"# {path.name}", ""]
    for idx, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        parts.extend([f"## Page {idx}", "", text.strip() or "[no extractable text]", ""])
    return "\n".join(parts), "pypdf", "PDF text-layer extraction only; tables, scans, and layout require manual verification"


CONVERTERS: dict[str, Callable[[Path], tuple[str, str, str]]] = {
    ".md": convert_markdown,
    ".markdown": convert_markdown,
    ".txt": convert_text,
    ".csv": convert_csv,
    ".xlsx": convert_xlsx,
    ".xlsm": convert_xlsx,
    ".docx": convert_docx,
    ".pptx": convert_pptx,
    ".pdf": convert_pdf,
}


def discover_workspace(source: Path) -> Path:
    candidates = [source if source.is_dir() else source.parent, Path.cwd()]
    for candidate in candidates:
        for parent in [candidate, *candidate.parents]:
            if (parent / "_cache").is_dir() and ((parent / "_raw").exists() or (parent / "_inbox").exists()):
                return parent
    raise IngestError("Could not discover research workspace. Pass --workspace or run init first.")


def infer_bucket(source: Path, workspace: Path, explicit_bucket: str | None) -> str:
    if explicit_bucket:
        return explicit_bucket
    try:
        rel = source.relative_to(workspace)
    except ValueError:
        return "unclassified"
    parts = rel.parts
    if len(parts) >= 3 and parts[0] == "_raw":
        return parts[2]
    if len(parts) >= 2 and parts[0] == "_inbox":
        return "inbox"
    return "unclassified"


def output_path_for(source: Path, workspace: Path, cache_root: Path | None, bucket: str | None) -> Path:
    root = cache_root if cache_root else workspace / "_cache"
    return root / infer_bucket(source, workspace, bucket) / f"{source.stem}.md"


def candidate_files(source: Path, recursive: bool) -> list[Path]:
    if source.is_file():
        return [source]
    pattern = "**/*" if recursive else "*"
    return sorted(path for path in source.glob(pattern) if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS)


def ingest_file(source: Path, workspace: Path, cache_root: Path | None, bucket: str | None, force: bool) -> dict[str, str]:
    extension = source.suffix.lower()
    converter = CONVERTERS.get(extension)
    if converter is None:
        raise IngestError(f"Unsupported file extension: {extension}")

    target = output_path_for(source, workspace, cache_root, bucket)
    if target.exists() and not force:
        return {
            "source": str(source),
            "cache": str(target),
            "status": "skipped",
            "converter": "cache-reuse",
            "precision": "existing cache; use --force to overwrite",
        }

    body, converter_name, precision = converter(source)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(markdown_header(source, converter_name, precision) + body.rstrip() + "\n", encoding="utf-8")
    return {
        "source": str(source),
        "cache": str(target),
        "status": "converted",
        "converter": converter_name,
        "precision": precision,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest raw research materials into workspace _cache markdown.")
    parser.add_argument("source_path", help="Source file or directory to ingest.")
    parser.add_argument("--workspace", help="Research workspace root. If omitted, discover from source path.")
    parser.add_argument("--cache-root", help="Override cache root. Defaults to <workspace>/_cache.")
    parser.add_argument("--bucket", help="Override cache bucket under _cache.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing cache files.")
    parser.add_argument("--recursive", action="store_true", help="Recursively ingest supported files in a directory.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source = Path(args.source_path).expanduser().resolve()
    if not source.exists():
        print(json.dumps({"status": "failed", "error": f"Source path does not exist: {source}"}, ensure_ascii=False, indent=2))
        return 1

    try:
        workspace = Path(args.workspace).expanduser().resolve() if args.workspace else discover_workspace(source)
        cache_root = Path(args.cache_root).expanduser().resolve() if args.cache_root else None
        files = candidate_files(source, args.recursive)
        if not files:
            raise IngestError("No supported files found to ingest.")

        results = []
        failed = []
        for file_path in files:
            try:
                results.append(ingest_file(file_path.resolve(), workspace, cache_root, args.bucket, args.force))
            except Exception as exc:
                failed.append({"source": str(file_path), "status": "failed", "error": str(exc)})

        payload = {
            "workspace": str(workspace),
            "converted": sum(1 for item in results if item["status"] == "converted"),
            "skipped": sum(1 for item in results if item["status"] == "skipped"),
            "failed": len(failed),
            "results": results,
            "errors": failed,
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 1 if failed else 0
    except Exception as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}, ensure_ascii=False, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
