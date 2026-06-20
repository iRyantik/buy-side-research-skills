from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re
from typing import Iterable


DATE_PREFIX_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})")


@dataclass
class CoverageEntry:
    ticker: str
    company: str
    industry: str = ""
    research_tier: str = ""
    alert_tier: str = ""
    stage: str = ""
    last_review: str = ""
    next_trigger: str = ""
    monitor: str = ""
    notes: str = ""
    source_path: str = ""
    latest_artifact: str = ""
    artifact_count: int = 0


@dataclass
class CoverageUniverse:
    entries: list[CoverageEntry] = field(default_factory=list)
    gaps: list[str] = field(default_factory=list)


HEADER_ALIASES = {
    "ticker": "ticker",
    "company": "company",
    "industry": "industry",
    "research tier": "research_tier",
    "alert tier": "alert_tier",
    "stage": "stage",
    "last review": "last_review",
    "next trigger": "next_trigger",
    "monitor": "monitor",
    "notes": "notes",
    "source path": "source_path",
    "latest artifact": "latest_artifact",
    "行业": "industry",
    "公司": "company",
    "主行业": "industry",
    "文件位置": "source_path",
    "最新 artifact": "latest_artifact",
    "状态": "stage",
}


CANONICAL_HEADERS = [
    ("Ticker", "ticker"),
    ("Company", "company"),
    ("Industry", "industry"),
    ("Research Tier", "research_tier"),
    ("Alert Tier", "alert_tier"),
    ("Stage", "stage"),
    ("Last Review", "last_review"),
    ("Next Trigger", "next_trigger"),
    ("Monitor", "monitor"),
    ("Notes", "notes"),
]


def normalize_company_token(value: str) -> str:
    token = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return token


def normalize_ticker(value: str) -> str:
    return value.strip()


def _split_row(line: str) -> list[str]:
    parts = [part.strip() for part in line.strip().strip("|").split("|")]
    return parts


def _find_first_table(lines: list[str]) -> tuple[list[str], list[list[str]]]:
    for index, line in enumerate(lines):
        if not line.lstrip().startswith("|"):
            continue
        if index + 1 >= len(lines) or not lines[index + 1].lstrip().startswith("|"):
            continue
        header = _split_row(line)
        separator = _split_row(lines[index + 1])
        if not header or not separator:
            continue
        rows: list[list[str]] = []
        for body_line in lines[index + 2 :]:
            if not body_line.lstrip().startswith("|"):
                break
            rows.append(_split_row(body_line))
        return header, rows
    return [], []


def parse_coverage_markdown(text: str) -> list[CoverageEntry]:
    lines = text.splitlines()
    header_row, body_rows = _find_first_table(lines)
    if not header_row:
        return []

    mapped_headers = [HEADER_ALIASES.get(cell.strip().lower(), "") for cell in header_row]
    entries: list[CoverageEntry] = []
    for row in body_rows:
        if len(row) < len(mapped_headers):
            row = row + [""] * (len(mapped_headers) - len(row))
        data = {field: "" for _, field in CANONICAL_HEADERS}
        data["source_path"] = ""
        data["latest_artifact"] = ""
        for header, value in zip(mapped_headers, row):
            if not header:
                continue
            cleaned = value.strip()
            if cleaned and not data.get(header):
                data[header] = cleaned
        entry = CoverageEntry(
            ticker=normalize_ticker(data["ticker"]),
            company=data["company"].strip(),
            industry=data["industry"].strip(),
            research_tier=data["research_tier"].strip(),
            alert_tier=data["alert_tier"].strip(),
            stage=data["stage"].strip(),
            last_review=data["last_review"].strip(),
            next_trigger=data["next_trigger"].strip(),
            monitor=data["monitor"].strip(),
            notes=data["notes"].strip(),
            source_path=data["source_path"].strip(),
            latest_artifact=data["latest_artifact"].strip(),
        )
        if entry.ticker or entry.company or entry.source_path:
            entries.append(entry)
    return entries


def render_coverage_markdown(entries: Iterable[CoverageEntry]) -> str:
    lines = [
        "# Coverage Map",
        "",
        "> This file is the workspace coverage source of truth. `coverage-monitor` consumes it for daily and intraday monitoring.",
        "",
        "| " + " | ".join(label for label, _ in CANONICAL_HEADERS) + " |",
        "|" + "---|" * len(CANONICAL_HEADERS),
    ]
    for entry in entries:
        cells = []
        for _, field_name in CANONICAL_HEADERS:
            cells.append(getattr(entry, field_name, "").strip())
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


def discover_company_directories(workspace: Path) -> list[Path]:
    industry_root = workspace / "industry"
    if not industry_root.exists():
        return []
    return sorted(path for path in industry_root.glob("*/companies/*") if path.is_dir())


def list_markdown_artifacts(company_dir: Path) -> list[Path]:
    return sorted(path for path in company_dir.glob("*.md") if path.is_file())


def extract_date_prefix(value: str) -> str:
    match = DATE_PREFIX_RE.match(value.strip())
    return match.group(1) if match else ""
