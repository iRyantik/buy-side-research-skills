"""Pure source converters. These functions never choose paths or mutate sources."""

from __future__ import annotations

import csv
import io
import zipfile
from xml.etree import ElementTree
from dataclasses import dataclass
from pathlib import Path


class ConversionError(RuntimeError):
    """Raised when a source cannot be converted safely."""


@dataclass(frozen=True)
class ConversionResult:
    markdown: str
    converter: str
    warnings: tuple[str, ...] = ()


def _convert_csv(path: Path) -> ConversionResult:
    text = path.read_text(encoding="utf-8-sig")
    rows = list(csv.reader(io.StringIO(text)))
    if not rows:
        return ConversionResult("", "csv")
    width = max(len(row) for row in rows)
    padded = [row + [""] * (width - len(row)) for row in rows]
    header = padded[0]
    lines = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join("---" for _ in header) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in padded[1:])
    return ConversionResult("\n".join(lines) + "\n", "csv")


def _convert_pdf(path: Path) -> ConversionResult:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise ConversionError("PDF conversion requires the optional pypdf dependency") from exc
    reader = PdfReader(str(path))
    pages = []
    for index, page in enumerate(reader.pages, start=1):
        pages.append(f"## Page {index}\n\n{page.extract_text() or ''}".strip())
    return ConversionResult("\n\n".join(pages) + "\n", "pypdf")


def _xml_text(xml: bytes) -> list[str]:
    root = ElementTree.fromstring(xml)
    return [
        str(element.text).strip()
        for element in root.iter()
        if element.tag.rsplit("}", 1)[-1] == "t" and element.text and element.text.strip()
    ]


def _convert_open_xml(path: Path) -> ConversionResult:
    suffix = path.suffix.lower()
    prefixes = {
        ".docx": ("word/document.xml",),
        ".pptx": ("ppt/slides/slide",),
        ".xlsx": ("xl/sharedStrings.xml", "xl/worksheets/sheet"),
    }
    with zipfile.ZipFile(path) as archive:
        names = [
            name
            for name in sorted(archive.namelist())
            if any(name.startswith(prefix) for prefix in prefixes[suffix]) and name.endswith(".xml")
        ]
        sections = []
        for name in names:
            text = _xml_text(archive.read(name))
            if text:
                sections.append(f"## {name}\n\n" + "\n\n".join(text))
    if not sections:
        raise ConversionError(f"{suffix} conversion produced no text")
    return ConversionResult("\n\n".join(sections) + "\n", f"open-xml:{suffix}")


def convert_source(path: Path) -> ConversionResult:
    """Convert a local source to Markdown without moving or deleting it."""
    suffix = path.suffix.lower()
    if suffix in {".md", ".txt", ".html", ".htm", ".json", ".yaml", ".yml"}:
        return ConversionResult(path.read_text(encoding="utf-8-sig"), f"text:{suffix or 'plain'}")
    if suffix == ".csv":
        return _convert_csv(path)
    if suffix == ".pdf":
        return _convert_pdf(path)
    if suffix in {".docx", ".pptx", ".xlsx"}:
        return _convert_open_xml(path)
    raise ConversionError(f"unsupported source format: {suffix or '<none>'}")
