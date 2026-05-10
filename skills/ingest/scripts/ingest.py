#!/usr/bin/env python3
"""Convert raw research files into source-tracked markdown cache files."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
from dataclasses import dataclass
import hashlib
import html
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import sys
from typing import Any


SUPPORTED_EXTENSIONS = {
    ".txt",
    ".md",
    ".markdown",
    ".csv",
    ".xlsx",
    ".xlsm",
    ".xls",
    ".docx",
    ".pptx",
    ".pdf",
}

SEC_FORM_PATTERN = re.compile(r"\b(10[-_ ]?K|10[-_ ]?Q|8[-_ ]?K|20[-_ ]?F|40[-_ ]?F)\b", re.IGNORECASE)
SEC_TEXT_PATTERNS = (
    "UNITED STATES SECURITIES AND EXCHANGE COMMISSION",
    "<SEC-DOCUMENT",
    "EDGAR",
    "FORM 10-K",
    "FORM 10-Q",
    "FORM 8-K",
    "FORM 20-F",
)
NUMBER_PATTERN = re.compile(r"(?<![A-Za-z])[-+]?\$?\d[\d,]*(?:\.\d+)?%?")


class IngestError(RuntimeError):
    pass


@dataclass
class DocumentProfile:
    extension: str
    document_type: str
    page_count: int | None = None
    table_count: int | None = None
    text_chars: int | None = None
    ocr_required: bool = False
    sec_filing: bool = False


@dataclass
class ConversionResult:
    markdown: str
    converter: str
    precision: str
    precision_level: str
    document_type: str
    route: str
    page_count: int | None = None
    table_count: int | None = None
    ocr_required: bool = False
    dependency_status: dict[str, Any] | None = None


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


def module_available(module_name: str) -> bool:
    return importlib.util.find_spec(module_name) is not None


def dependency_matrix() -> dict[str, Any]:
    packages = {
        "docling": {
            "available": module_available("docling"),
            "module": "docling",
            "install_hint": "pip install docling",
        },
        "edgartools": {
            "available": module_available("edgar"),
            "module": "edgar",
            "install_hint": "pip install edgartools",
        },
        "markitdown": {
            "available": module_available("markitdown"),
            "module": "markitdown",
            "install_hint": "pip install 'markitdown[all]'",
        },
        "openpyxl": {
            "available": module_available("openpyxl"),
            "module": "openpyxl",
            "install_hint": "pip install openpyxl",
        },
        "python-pptx": {
            "available": module_available("pptx"),
            "module": "pptx",
            "install_hint": "pip install python-pptx",
        },
        "python-docx": {
            "available": module_available("docx"),
            "module": "docx",
            "install_hint": "pip install python-docx",
        },
        "pdfplumber": {
            "available": module_available("pdfplumber"),
            "module": "pdfplumber",
            "install_hint": "pip install pdfplumber",
        },
        "pypdf": {
            "available": module_available("pypdf"),
            "module": "pypdf",
            "install_hint": "pip install pypdf",
        },
        "pytesseract": {
            "available": module_available("pytesseract"),
            "module": "pytesseract",
            "install_hint": "pip install pytesseract",
        },
        "Pillow": {
            "available": module_available("PIL"),
            "module": "PIL",
            "install_hint": "pip install Pillow",
        },
    }
    return {
        "python": {
            "version": sys.version.split()[0],
            "executable": sys.executable,
        },
        "packages": packages,
        "binaries": {
            "tesseract": {
                "available": shutil.which("tesseract") is not None,
                "path": shutil.which("tesseract"),
                "install_hint": "Install Tesseract via winget/choco or UB Mannheim Windows installer.",
            }
        },
        "env": {
            "EDGAR_IDENTITY": {
                "configured": bool(os.getenv("EDGAR_IDENTITY")),
                "value": os.getenv("EDGAR_IDENTITY"),
            }
        },
    }


def dependency_snapshot(keys: list[str]) -> dict[str, Any]:
    matrix = dependency_matrix()
    packages = matrix["packages"]
    return {
        "packages": {key: packages.get(key) for key in keys if key in packages},
        "binaries": matrix["binaries"],
        "env": matrix["env"],
    }


def require_package(package_key: str, module_name: str | None = None) -> None:
    module_name = module_name or package_key
    if not module_available(module_name):
        matrix = dependency_matrix()
        hint = matrix["packages"].get(package_key, {}).get("install_hint", f"pip install {package_key}")
        raise IngestError(f"Missing optional dependency: {package_key}. Run bootstrap-ingest-deps.ps1 or `{hint}`.")


def inspect_pdf(path: Path) -> tuple[int | None, int | None, int | None]:
    page_count: int | None = None
    text_chars: int | None = None
    table_count: int | None = None

    if module_available("pypdf"):
        try:
            from pypdf import PdfReader  # type: ignore

            reader = PdfReader(str(path))
            page_count = len(reader.pages)
            texts = []
            for page in reader.pages[:20]:
                texts.append(page.extract_text() or "")
            text_chars = sum(len(text.strip()) for text in texts)
        except Exception:
            pass

    if module_available("pdfplumber"):
        try:
            import pdfplumber  # type: ignore

            count = 0
            with pdfplumber.open(str(path)) as pdf:
                if page_count is None:
                    page_count = len(pdf.pages)
                for page in pdf.pages:
                    count += len(page.extract_tables() or [])
            table_count = count
        except Exception:
            pass

    return page_count, text_chars, table_count


def extract_pdf_text_probe(path: Path, max_chars: int = 8000) -> str:
    if not module_available("pypdf"):
        return ""
    try:
        from pypdf import PdfReader  # type: ignore

        reader = PdfReader(str(path))
        chunks = []
        for page in reader.pages[:5]:
            chunks.append(page.extract_text() or "")
            if sum(len(chunk) for chunk in chunks) >= max_chars:
                break
        return "\n".join(chunks)[:max_chars]
    except Exception:
        return ""


def detect_format(path: Path) -> DocumentProfile:
    extension = path.suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise IngestError(f"Unsupported file extension: {extension}")

    if extension == ".pdf":
        page_count, text_chars, table_count = inspect_pdf(path)
        probe_text = extract_pdf_text_probe(path)
        sec_filing = bool(SEC_FORM_PATTERN.search(path.name)) or any(pattern in probe_text.upper() for pattern in SEC_TEXT_PATTERNS)
        ocr_required = bool(page_count and (text_chars is None or text_chars < 20))
        return DocumentProfile(
            extension=extension,
            document_type="sec-filing-pdf" if sec_filing else "pdf",
            page_count=page_count,
            table_count=table_count,
            text_chars=text_chars,
            ocr_required=ocr_required,
            sec_filing=sec_filing,
        )

    type_map = {
        ".txt": "text",
        ".md": "markdown",
        ".markdown": "markdown",
        ".csv": "csv",
        ".xlsx": "excel-workbook",
        ".xlsm": "excel-workbook",
        ".xls": "legacy-excel-workbook",
        ".docx": "word-document",
        ".pptx": "powerpoint-deck",
    }
    return DocumentProfile(extension=extension, document_type=type_map[extension])


def markdown_header(source: Path, result: ConversionResult) -> str:
    modified = dt.datetime.fromtimestamp(source.stat().st_mtime, dt.timezone.utc)
    metadata = {
        "source_path": str(source),
        "source_sha256": sha256_file(source),
        "source_modified_utc": modified.replace(microsecond=0).isoformat(),
        "converter": result.converter,
        "converted_at_utc": utc_now(),
        "precision": result.precision,
        "precision_level": result.precision_level,
        "document_type": result.document_type,
        "route": result.route,
        "page_count": result.page_count if result.page_count is not None else "unknown",
        "table_count": result.table_count if result.table_count is not None else "unknown",
        "ocr_required": str(result.ocr_required).lower(),
    }
    body = "\n".join(f"{key}: {value}" for key, value in metadata.items())
    return f"<!--\n{body}\n-->\n\n"


def convert_markdown(path: Path, profile: DocumentProfile) -> ConversionResult:
    return ConversionResult(
        markdown=read_text_lossy(path),
        converter="native-markdown",
        precision="native markdown; verify quoted facts against original source",
        precision_level="native",
        document_type=profile.document_type,
        route="native-markdown",
        dependency_status=dependency_snapshot([]),
    )


def convert_text(path: Path, profile: DocumentProfile) -> ConversionResult:
    text = read_text_lossy(path)
    return ConversionResult(
        markdown=f"# {path.name}\n\n```text\n{text}\n```\n",
        converter="native-text",
        precision="plain text extraction",
        precision_level="native",
        document_type=profile.document_type,
        route="native-text",
        dependency_status=dependency_snapshot([]),
    )


def convert_csv(path: Path, profile: DocumentProfile) -> ConversionResult:
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
    return ConversionResult(
        markdown="\n".join(output),
        converter="native-csv",
        precision="CSV parsed with Python csv; inspect original for dialect/encoding issues",
        precision_level="native",
        document_type=profile.document_type,
        route="native-csv",
        dependency_status=dependency_snapshot([]),
    )


def convert_xlsx(path: Path, profile: DocumentProfile) -> ConversionResult:
    require_package("openpyxl", "openpyxl")
    scripts_dir = Path(__file__).resolve().parent
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    from ingest_xlsx import workbook_to_markdown

    return ConversionResult(
        markdown=workbook_to_markdown(path),
        converter="openpyxl",
        precision="workbook structure extraction; verify formulas and key numbers in Excel",
        precision_level="structured",
        document_type=profile.document_type,
        route="excel-openpyxl-dual-load",
        dependency_status=dependency_snapshot(["openpyxl"]),
    )


def convert_markitdown(path: Path, profile: DocumentProfile, route: str, precision: str) -> ConversionResult:
    require_package("markitdown", "markitdown")
    from markitdown import MarkItDown  # type: ignore

    converter = MarkItDown(enable_plugins=False)
    if hasattr(converter, "convert_local"):
        converted = converter.convert_local(str(path))
    else:
        converted = converter.convert(str(path))
    text = getattr(converted, "text_content", str(converted))
    return ConversionResult(
        markdown=f"# {path.name}\n\n{text}",
        converter="markitdown",
        precision=precision,
        precision_level="degraded",
        document_type=profile.document_type,
        route=route,
        page_count=profile.page_count,
        table_count=profile.table_count,
        ocr_required=profile.ocr_required,
        dependency_status=dependency_snapshot(["markitdown"]),
    )


def convert_docling(path: Path, profile: DocumentProfile, route: str, use_ocr: bool = False) -> ConversionResult:
    require_package("docling", "docling")

    if use_ocr and shutil.which("tesseract") is None:
        raise IngestError(
            "OCR required but tesseract.exe is not on PATH. Run bootstrap-ingest-deps.ps1 or install Tesseract via winget/choco/UB Mannheim."
        )

    if use_ocr:
        from docling.datamodel.base_models import InputFormat  # type: ignore
        from docling.datamodel.pipeline_options import PdfPipelineOptions, TableStructureOptions, TesseractCliOcrOptions  # type: ignore
        from docling.document_converter import DocumentConverter, PdfFormatOption  # type: ignore

        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = True
        pipeline_options.do_table_structure = True
        pipeline_options.table_structure_options = TableStructureOptions(do_cell_matching=True)
        pipeline_options.ocr_options = TesseractCliOcrOptions(force_full_page_ocr=True)
        converter = DocumentConverter(
            format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)}
        )
        converter_name = "docling-tesseract-cli-ocr"
        precision = "Docling OCR via Tesseract CLI; verify OCR text, tables, units, and page references against original scan"
        precision_level = "ocr"
    else:
        from docling.document_converter import DocumentConverter  # type: ignore

        converter = DocumentConverter()
        converter_name = "docling"
        precision = "Docling markdown conversion; verify financial tables and layout-sensitive content against original"
        precision_level = "structured"

    result = converter.convert(str(path))
    markdown = result.document.export_to_markdown()
    return ConversionResult(
        markdown=markdown,
        converter=converter_name,
        precision=precision,
        precision_level=precision_level,
        document_type=profile.document_type,
        route=route,
        page_count=profile.page_count,
        table_count=profile.table_count,
        ocr_required=profile.ocr_required,
        dependency_status=dependency_snapshot(["docling", "pypdf", "pdfplumber", "edgartools"]),
    )


def convert_docx_fallback(path: Path, profile: DocumentProfile) -> ConversionResult:
    require_package("python-docx", "docx")
    import docx  # type: ignore

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
    return ConversionResult(
        markdown="\n".join(parts),
        converter="python-docx",
        precision="DOCX fallback text/table extraction; verify layout-sensitive content in original",
        precision_level="degraded",
        document_type=profile.document_type,
        route="docx-python-docx-fallback",
        table_count=len(document.tables),
        dependency_status=dependency_snapshot(["python-docx"]),
    )


def convert_pptx_fallback(path: Path, profile: DocumentProfile) -> ConversionResult:
    require_package("python-pptx", "pptx")
    from pptx import Presentation  # type: ignore

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
    return ConversionResult(
        markdown="\n".join(parts),
        converter="python-pptx",
        precision="PPTX fallback text/notes extraction; verify charts/images in original deck",
        precision_level="degraded",
        document_type=profile.document_type,
        route="pptx-python-pptx-fallback",
        page_count=len(deck.slides),
        dependency_status=dependency_snapshot(["python-pptx"]),
    )


def convert_pdf_pypdf_fallback(path: Path, profile: DocumentProfile, route: str) -> ConversionResult:
    require_package("pypdf", "pypdf")
    from pypdf import PdfReader  # type: ignore

    reader = PdfReader(str(path))
    parts = [f"# {path.name}", ""]
    for idx, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        parts.extend([f"## Page {idx}", "", text.strip() or "[no extractable text]", ""])
    return ConversionResult(
        markdown="\n".join(parts),
        converter="pypdf",
        precision="PDF text-layer fallback only; tables, scans, and layout require manual verification",
        precision_level="degraded",
        document_type=profile.document_type,
        route=route,
        page_count=profile.page_count or len(reader.pages),
        table_count=profile.table_count,
        ocr_required=profile.ocr_required,
        dependency_status=dependency_snapshot(["pypdf", "pdfplumber"]),
    )


def ensure_sec_route_ready(profile: DocumentProfile) -> None:
    if not profile.sec_filing:
        return
    require_package("edgartools", "edgar")
    if not os.getenv("EDGAR_IDENTITY"):
        raise IngestError(
            "SEC filing detected but EDGAR_IDENTITY is not configured. Run bootstrap-ingest-deps.ps1 -EdgarIdentity \"Name email@domain.com\"."
        )


def convert_pdf(path: Path, profile: DocumentProfile) -> ConversionResult:
    if profile.ocr_required:
        missing = []
        if not module_available("docling"):
            missing.append("docling")
        if shutil.which("tesseract") is None:
            missing.append("tesseract.exe")
        if missing:
            raise IngestError(
                "OCR required for scanned PDF but dependencies are missing: "
                + ", ".join(missing)
                + ". Run bootstrap-ingest-deps.ps1; no cache was written."
            )
        return convert_docling(path, profile, route="pdf-docling-tesseract-cli-ocr", use_ocr=True)

    if profile.sec_filing:
        ensure_sec_route_ready(profile)
        try:
            result = convert_docling(path, profile, route="sec-filing-edgartools-xbrl-docling-narrative")
            note = (
                "\n\n## SEC XBRL Route Note\n\n"
                "EdgarTools dependency and EDGAR_IDENTITY are available. This cache converts the local filing narrative; "
                "financial statement numbers should still be reconciled to SEC/XBRL source before use.\n"
            )
            result.markdown = result.markdown.rstrip() + note
            return result
        except IngestError:
            raise
        except Exception as exc:
            raise IngestError(f"SEC filing route failed before cache write: {exc}") from exc

    if module_available("docling"):
        try:
            return convert_docling(path, profile, route="pdf-docling")
        except Exception as exc:
            if profile.text_chars and profile.text_chars >= 20 and module_available("pypdf"):
                fallback = convert_pdf_pypdf_fallback(path, profile, route="pdf-pypdf-fallback-after-docling-error")
                fallback.precision = f"{fallback.precision}; Docling failed: {exc}"
                return fallback
            raise IngestError(f"Docling PDF conversion failed and no safe fallback is available: {exc}") from exc

    if profile.text_chars and profile.text_chars >= 20:
        return convert_pdf_pypdf_fallback(path, profile, route="pdf-pypdf-fallback-docling-missing")

    raise IngestError("PDF conversion requires Docling. Run bootstrap-ingest-deps.ps1; no cache was written.")


def route_converter(path: Path, profile: DocumentProfile) -> ConversionResult:
    if profile.extension in {".md", ".markdown"}:
        return convert_markdown(path, profile)
    if profile.extension == ".txt":
        return convert_text(path, profile)
    if profile.extension == ".csv":
        return convert_csv(path, profile)
    if profile.extension in {".xlsx", ".xlsm"}:
        return convert_xlsx(path, profile)
    if profile.extension == ".xls":
        return convert_markitdown(
            path,
            profile,
            route="legacy-xls-markitdown-fallback",
            precision="Legacy XLS via MarkItDown fallback; verify formulas, formats, and key numbers in Excel",
        )
    if profile.extension == ".docx":
        if module_available("docling"):
            return convert_docling(path, profile, route="docx-docling")
        return convert_docx_fallback(path, profile)
    if profile.extension == ".pptx":
        if module_available("docling"):
            try:
                docling_result = convert_docling(path, profile, route="pptx-docling")
                if module_available("pptx"):
                    notes_result = convert_pptx_fallback(path, profile)
                    docling_result.markdown = (
                        docling_result.markdown.rstrip()
                        + "\n\n## python-pptx Speaker Notes Fallback\n\n"
                        + notes_result.markdown
                    )
                return docling_result
            except Exception:
                return convert_pptx_fallback(path, profile)
        return convert_pptx_fallback(path, profile)
    if profile.extension == ".pdf":
        return convert_pdf(path, profile)
    raise IngestError(f"Unsupported file extension: {profile.extension}")


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


def read_cache_metadata(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8", errors="replace")
    if not text.startswith("<!--"):
        return {}
    end = text.find("-->")
    if end == -1:
        return {}
    metadata: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            metadata[key.strip()] = value.strip()
    return metadata


def collision_safe_output_path(target: Path, source: Path) -> Path:
    suffix_token = source.suffix.lower().lstrip(".") or "file"
    return target.with_name(f"{source.stem}-{suffix_token}.md")


def candidate_files(source: Path, recursive: bool) -> list[Path]:
    if source.is_file():
        return [source]
    pattern = "**/*" if recursive else "*"
    return sorted(path for path in source.glob(pattern) if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS)


def cache(source: Path, workspace: Path, cache_root: Path | None, bucket: str | None, force: bool) -> dict[str, Any]:
    profile = detect_format(source)
    target = output_path_for(source, workspace, cache_root, bucket)
    if target.exists() and not force:
        current_hash = sha256_file(source)
        metadata = read_cache_metadata(target)
        cached_source_path = metadata.get("source_path")
        cached_hash = metadata.get("source_sha256")
        if cached_source_path != str(source) or cached_hash != current_hash:
            target = collision_safe_output_path(target, source)
            if not target.exists():
                result = route_converter(source, profile)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(markdown_header(source, result) + result.markdown.rstrip() + "\n", encoding="utf-8")
                return {
                    "source": str(source),
                    "cache": str(target),
                    "status": "converted",
                    "converter": result.converter,
                    "precision": result.precision,
                    "precision_level": result.precision_level,
                    "document_type": result.document_type,
                    "route": f"{result.route}-collision-safe-cache",
                    "page_count": result.page_count,
                    "table_count": result.table_count,
                    "ocr_required": result.ocr_required,
                    "dependency_status": result.dependency_status,
                }

        return {
            "source": str(source),
            "cache": str(target),
            "status": "skipped",
            "converter": "cache-reuse",
            "precision": "existing cache; use --force to overwrite",
            "precision_level": "existing",
            "document_type": profile.document_type,
            "route": "cache-reuse",
            "page_count": profile.page_count,
            "table_count": profile.table_count,
            "ocr_required": profile.ocr_required,
        }

    result = route_converter(source, profile)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(markdown_header(source, result) + result.markdown.rstrip() + "\n", encoding="utf-8")
    return {
        "source": str(source),
        "cache": str(target),
        "status": "converted",
        "converter": result.converter,
        "precision": result.precision,
        "precision_level": result.precision_level,
        "document_type": result.document_type,
        "route": result.route,
        "page_count": result.page_count,
        "table_count": result.table_count,
        "ocr_required": result.ocr_required,
        "dependency_status": result.dependency_status,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest raw research materials into workspace _cache markdown.")
    parser.add_argument("source_path", nargs="?", help="Source file or directory to ingest.")
    parser.add_argument("--workspace", help="Research workspace root. If omitted, discover from source path.")
    parser.add_argument("--cache-root", help="Override cache root. Defaults to <workspace>/_cache.")
    parser.add_argument("--bucket", help="Override cache bucket under _cache.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing cache files.")
    parser.add_argument("--recursive", action="store_true", help="Recursively ingest supported files in a directory.")
    parser.add_argument("--check-deps", action="store_true", help="Print ingest dependency matrix as JSON and exit.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.check_deps:
        print(json.dumps(dependency_matrix(), ensure_ascii=False, indent=2))
        return 0

    if not args.source_path:
        print(json.dumps({"status": "failed", "error": "source_path is required unless --check-deps is used"}, ensure_ascii=False, indent=2))
        return 1

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
                results.append(cache(file_path.resolve(), workspace, cache_root, args.bucket, args.force))
            except Exception as exc:
                profile: dict[str, Any] = {}
                try:
                    detected = detect_format(file_path.resolve())
                    profile = {
                        "document_type": detected.document_type,
                        "page_count": detected.page_count,
                        "table_count": detected.table_count,
                        "ocr_required": detected.ocr_required,
                    }
                except Exception:
                    pass
                failed.append({"source": str(file_path), "status": "failed", "error": str(exc), **profile})

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
