"""openesef provider for Europe ESEF/iXBRL financial-data routes.

Deterministic extraction: source provenance, filing text from local ESEF package or URL.
No structured three-statement extraction in V1 (ESEF taxonomy mapping is experimental).
"""

from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
from typing import Any


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

    # --- source provenance ---
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

            # Try to parse and extract markdown text
            try:
                _try_extract_filing_text(filing_info, identifier, identifier_type)
            except Exception as e:
                result["errors"].append(f"parse_extract: {e}")

            result["filing"] = filing_info
            result["items_extracted"].append("filing_index")
            if "latest_full_filing" in items:
                result["items_extracted"].append("latest_full_filing")
        except Exception as e:
            result["errors"].append(f"source: {e}")

    result["status"] = "partial" if result["items_extracted"] else "provider-gap"
    return result


def _try_extract_filing_text(filing_info: dict, identifier: str, identifier_type: str) -> None:
    """Attempt to parse ESEF package and extract markdown text."""
    if not dependency_available():
        return

    import openesef

    if identifier_type == "local_esef_package":
        pkg_path = Path(identifier).expanduser().resolve()
        package = openesef.open_package(str(pkg_path))
    elif identifier_type == "filing_url":
        package = openesef.open_package(identifier)
    else:
        return

    filing_info["status"] = "parsed"
    try:
        report_text = str(package)
        if report_text:
            filing_info["markdown"] = report_text
            filing_info["markdown_sha256"] = hashlib.sha256(report_text.encode()).hexdigest()
            filing_info["text_length"] = len(report_text)
    except Exception:
        pass


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _err(status: str, msg: str) -> dict[str, Any]:
    return {"status": status, "provider": PROVIDER, "error": msg}
