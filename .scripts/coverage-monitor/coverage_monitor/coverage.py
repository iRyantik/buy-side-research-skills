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
    company_native: str = ""
    industry: str = ""
    coverage_status: str = ""
    monitor_status: str = ""
    last_review: str = ""
    next_trigger: str = ""
    notes: str = ""
    source_path: str = ""
    latest_artifact: str = ""
    artifact_count: int = 0
    quickread_artifact_count: int = 0
    deepwork_artifact_count: int = 0
    has_research_memory: bool = False


@dataclass
class CoverageUniverse:
    entries: list[CoverageEntry] = field(default_factory=list)
    gaps: list[str] = field(default_factory=list)


HEADER_ALIASES = {
    "ticker": "ticker",
    "company": "company",
    "company (en)": "company",
    "company (native)": "company_native",
    "industry": "industry",
    "coverage": "coverage_status",
    "coverage status": "coverage_status",
    "monitor": "monitor_status",
    "monitor status": "monitor_status",
    "last review": "last_review",
    "next trigger": "next_trigger",
    "notes": "notes",
    "source path": "source_path",
    "latest artifact": "latest_artifact",
    "行业": "industry",
    "公司": "company",
    "主行业": "industry",
    "文件位置": "source_path",
    "最新 artifact": "latest_artifact",
    "状态": "coverage_status",
}


CANONICAL_HEADERS = [
    ("Ticker", "ticker"),
    ("Company (EN)", "company"),
    ("Company (Native)", "company_native"),
    ("Industry", "industry"),
    ("Coverage", "coverage_status"),
    ("Monitor", "monitor_status"),
    ("Last Review", "last_review"),
    ("Next Trigger", "next_trigger"),
    ("Notes", "notes"),
]


def normalize_company_token(value: str) -> str:
    token = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return token


def normalize_ticker(value: str) -> str:
    return value.strip()


def normalize_coverage_status(value: str) -> str:
    token = re.sub(r"\s+", " ", value.strip()).lower()
    if token in {"core coverage", "core"}:
        return "Core"
    if token in {"building coverage", "building", "coverage building"}:
        return "Building"
    if token in {"radar", "candidate"}:
        return "Radar"
    return value.strip()


def normalize_monitor_status(value: str) -> str:
    token = re.sub(r"\s+", " ", value.strip()).lower()
    if token in {"core watch", "core", "yes", "true"}:
        return "Core"
    if token in {"daily watch", "daily", "daily-only"}:
        return "Daily"
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


def _find_coverage_table(lines: list[str]) -> tuple[list[str], list[list[str]]]:
    """Prefer the canonical table under `## Coverage`; fall back for legacy files."""
    coverage_heading_index: int | None = None
    for index, line in enumerate(lines):
        if re.match(r"^#{2,6}\s+Coverage\s*$", line.strip(), flags=re.IGNORECASE):
            coverage_heading_index = index
            break
    if coverage_heading_index is None:
        return _find_first_table(lines)
    header, rows = _find_first_table(lines[coverage_heading_index + 1 :])
    if header:
        return header, rows
    return _find_first_table(lines)


def parse_coverage_markdown(text: str) -> list[CoverageEntry]:
    lines = text.splitlines()
    header_row, body_rows = _find_coverage_table(lines)
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
            company_native=data["company_native"].strip(),
            industry=data["industry"].strip(),
            coverage_status=normalize_coverage_status(data["coverage_status"]),
            monitor_status=normalize_monitor_status(data["monitor_status"]),
            last_review=data["last_review"].strip(),
            next_trigger=data["next_trigger"].strip(),
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


DEEPWORK_PATTERNS = (
    "alpha-thesis", "peer-deep-dive", "earnings-setup", "scenario-model",
    "consensus-map", "bear-pre-mortem", "driver-map", "moat-analysis",
    "catalyst-map", "capital-allocation", "3-statement-model", "dcf-model",
)
QUICKREAD_PATTERNS = ("stock-quickread", "company-history", "post-earnings-quick")


def compute_coverage_tier(company_dir: Path) -> str:
    names = " ".join(f.name.lower() for f in company_dir.glob("*.md"))
    has_thesis = "alpha-thesis" in names
    deepwork_count = sum(1 for p in DEEPWORK_PATTERNS if p in names)
    has_quickread = any(p in names for p in QUICKREAD_PATTERNS)
    has_model = "3-statement-model" in names or "dcf-model" in names
    if has_thesis or deepwork_count >= 2 or (deepwork_count >= 1 and has_model):
        return "Core"
    elif has_quickread or deepwork_count >= 1:
        return "Building"
    return "Radar"


def compute_monitor_status(coverage_tier: str) -> str:
    return "Core" if coverage_tier == "Core" else "Daily"


def extract_date_prefix(value: str) -> str:
    match = DATE_PREFIX_RE.match(value.strip())
    return match.group(1) if match else ""
