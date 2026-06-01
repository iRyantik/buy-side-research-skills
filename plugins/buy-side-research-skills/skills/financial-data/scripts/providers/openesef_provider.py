"""openesef provider for Europe ESEF/iXBRL financial-data routes.

Deterministic extraction: source provenance, filing text from local ESEF package or URL.
No structured three-statement extraction in V1 (ESEF taxonomy mapping is experimental).
"""

from __future__ import annotations

import hashlib
from html.parser import HTMLParser
import importlib.util
from pathlib import Path
from typing import Any
from urllib.request import urlopen
import zipfile


PROVIDER = "openesef"
EXTRACTABLE = ["identity", "filing_index", "latest_full_filing"]


def dependency_available() -> bool:
    return importlib.util.find_spec("openesef") is not None


def fetch(request: dict[str, Any]) -> dict[str, Any]:
    if not dependency_available():
        return _err("dependency-gap", "Missing openesef. Run: pip install openesef")

    identifier = request["identifier"]
    identifier_type = request.get("identifier_type", "ticker")
    items = request.get("items", EXTRACTABLE)
    items = [i for i in items if i in EXTRACTABLE]

    result: dict[str, Any] = {
        "provider": PROVIDER,
        "market": "eu",
        "identifier": identifier,
        "identifier_type": identifier_type,
        "items_requested": items,
        "items_extracted": [],
        "errors": [],
        "company": {"identifier": identifier, "identifier_type": identifier_type},
    }

    if identifier_type == "ticker":
        result["status"] = "provider-gap"
        result["errors"].append(
            "EU ticker-only filing discovery is experimental in V1. "
            "Provide filing_url or local_esef_package for reliable openesef parsing."
        )
        return result

    if "filing_index" in items or "latest_full_filing" in items:
        try:
            filing_info = {"provider": PROVIDER, "identifier_type": identifier_type}

            if identifier_type == "local_esef_package":
                pkg_path = Path(identifier).expanduser().resolve()
                if not pkg_path.exists():
                    raise FileNotFoundError(f"Local ESEF package not found: {pkg_path}")
                filing_info["local_path"] = str(pkg_path)
                filing_info["source_sha256"] = _sha256_file(pkg_path)
                filing_info["source_size_bytes"] = pkg_path.stat().st_size
            else:
                filing_info["filing_url"] = identifier

            try:
                _try_extract_filing_text(filing_info, identifier, identifier_type)
            except Exception as exc:
                result["errors"].append(f"parse_extract: {exc}")

            result["filing"] = filing_info
            result["items_extracted"].append("filing_index")
            if "latest_full_filing" in items and filing_info.get("markdown"):
                result["items_extracted"].append("latest_full_filing")
        except Exception as exc:
            result["errors"].append(f"source: {exc}")

    result["status"] = "partial" if result["items_extracted"] else "provider-gap"
    return result


def _try_extract_filing_text(filing_info: dict, identifier: str, identifier_type: str) -> None:
    if not dependency_available():
        return

    import openesef

    report_text = ""
    if hasattr(openesef, "open_package"):
        try:
            if identifier_type == "local_esef_package":
                pkg_path = Path(identifier).expanduser().resolve()
                package = openesef.open_package(str(pkg_path))
            elif identifier_type == "filing_url":
                package = openesef.open_package(identifier)
            else:
                return
            report_text = str(package)
            filing_info["status"] = "parsed"
        except Exception as exc:
            filing_info["openesef_parse_error"] = str(exc)

    if not report_text:
        report_text = _extract_esef_xhtml_text(identifier, identifier_type)
        if report_text:
            filing_info["status"] = "text-extracted"

    if report_text:
        filing_info["markdown"] = report_text
        filing_info["markdown_sha256"] = hashlib.sha256(report_text.encode()).hexdigest()
        filing_info["text_length"] = len(report_text)


def _extract_esef_xhtml_text(identifier: str, identifier_type: str) -> str:
    if identifier_type == "local_esef_package":
        path = Path(identifier).expanduser().resolve()
        if path.suffix.lower() in {".xhtml", ".html", ".htm"}:
            return _html_to_text(path.read_text(encoding="utf-8", errors="ignore"))
        if zipfile.is_zipfile(path):
            with zipfile.ZipFile(path) as package:
                names = package.namelist()
                candidates = [
                    name for name in names
                    if name.lower().endswith((".xhtml", ".html", ".htm"))
                ]
                if not candidates:
                    return ""
                report_name = sorted(candidates, key=lambda name: ("/reports/" not in name.lower(), len(name)))[0]
                content = package.read(report_name).decode("utf-8", errors="ignore")
                return _html_to_text(content)
        return ""

    if identifier_type == "filing_url":
        with urlopen(identifier, timeout=60) as response:  # nosec: user-provided filing URL
            content = response.read()
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            text = content.decode("latin-1", errors="ignore")
        return _html_to_text(text)

    return ""


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        text = " ".join(str(data).split())
        if text:
            self.parts.append(text)


def _html_to_text(html: str) -> str:
    parser = _TextExtractor()
    parser.feed(html)
    lines = []
    for part in parser.parts:
        if part and (not lines or lines[-1] != part):
            lines.append(part)
    return "# ESEF Filing Text\n\n" + "\n".join(lines) + "\n" if lines else ""


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _err(status: str, msg: str) -> dict[str, Any]:
    return {"status": status, "provider": PROVIDER, "error": msg}
