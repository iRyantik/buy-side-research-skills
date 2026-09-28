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
    market: str = ""  # 上市主要市场（洲）: us|eu|asia（注册时记录，选最优/首上市地）
    country: str = ""  # 上市国家/地区 ISO 码: US|CA|GB|FR|DE|SE|NO|FI|IT|ES|NL|JP|KR|CN|HK|TW|MY
    coverage_status: str = ""
    monitor_status: str = ""
    last_review: str = ""
    next_trigger: str = ""
    notes: str = ""
    val_anchor: str = ""
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
    "market": "market",
    "上市市场": "market",
    "主要市场": "market",
    "市场": "market",
    "coverage": "coverage_status",
    "coverage status": "coverage_status",
    "status": "coverage_status",
    "monitor": "monitor_status",
    "monitor status": "monitor_status",
    "last review": "last_review",
    "next trigger": "next_trigger",
    "notes": "notes",
    "val anchor": "val_anchor",
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
    ("Market", "market"),
    ("Status", "coverage_status"),
    ("Monitor", "monitor_status"),
    ("Last Review", "last_review"),
    ("Next Trigger", "next_trigger"),
    ("Val Anchor", "val_anchor"),
    ("Notes", "notes"),
]


def normalize_company_token(value: str) -> str:
    token = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return token


def normalize_ticker(value: str) -> str:
    return value.strip()


def normalize_coverage_status(value: str) -> str:
    token = re.sub(r"\s+", " ", value.strip()).lower()
    if token in {"screened", "radar", "candidate", "screen"}:
        return "Screened"
    if token in {"quickread", "building", "building coverage", "quick read", "coverage building"}:
        return "Quickread"
    if token in {"modeled", "model", "modelled", "core", "core coverage"}:
        return "Modeled"
    if token in {"thesis", "alpha thesis", "variant"}:
        return "Thesis"
    if token in {"terminated"}:
        return "Terminated"
    return value.strip()


def normalize_monitor_status(value: str) -> str:
    token = re.sub(r"\s+", " ", value.strip()).lower()
    if token in {"core watch", "core", "yes", "true"}:
        return "Core"
    if token in {"daily watch", "daily", "daily-only"}:
        return "Daily"
    return value.strip()


# 国家/地区码 → 洲（us/eu/asia）。范围对齐 coverage 表注册值（CLAUDE.md §3.3）。
_COUNTRY_TO_MKT = {
    "US": "us", "CA": "us",
    "GB": "eu", "FR": "eu", "DE": "eu", "SE": "eu", "NO": "eu", "FI": "eu",
    "IT": "eu", "ES": "eu", "NL": "eu",
    "JP": "asia", "KR": "asia", "CN": "asia", "HK": "asia", "TW": "asia", "MY": "asia",
}


def normalize_market(value: str) -> str:
    """上市主要市场 → us|eu|asia。接受洲名（us/europe/...）、国家码（US/GB/...）、
    中文（美股/欧股/亚盘）等写法；空/无法识别返回 ''（走 ticker 推断兜底）。"""
    token = re.sub(r"\s+", " ", value.strip()).lower()
    if token in {"us", "usa", "美国", "美股", "美", "us stock", "nyse", "nasdaq"}:
        return "us"
    if token in {"eu", "europe", "european", "欧洲", "欧股", "欧"}:
        return "eu"
    if token in {"asia", "apac", "asian", "亚太", "亚洲", "亚盘", "亚股", "亚", "cn", "hk", "jp", "kr", "tw"}:
        return "asia"
    m = _COUNTRY_TO_MKT.get(value.strip().upper())
    if m:
        return m
    return ""


def normalize_country(value: str) -> str:
    """上市国家/地区码（US/CA/GB/...）。只认白名单；旧三值(us/eu/asia)/空返回 ''（走 ticker 推断）。"""
    v = value.strip().upper()
    return v if v in _COUNTRY_TO_MKT else ""


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
        raw_market = data.get("market", "")
        entry = CoverageEntry(
            ticker=normalize_ticker(data["ticker"]),
            company=data["company"].strip(),
            company_native=data["company_native"].strip(),
            industry=data["industry"].strip(),
            market=normalize_market(raw_market),
            country=normalize_country(raw_market),
            coverage_status=normalize_coverage_status(data["coverage_status"]),
            monitor_status=normalize_monitor_status(data["monitor_status"]),
            last_review=data["last_review"].strip(),
            next_trigger=data["next_trigger"].strip(),
            notes=data["notes"].strip(),
            val_anchor=data.get("val_anchor", "").strip(),
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
            if field_name == "market":
                # Market 列存国家码（country），无显式国家时回退洲值——确保 normalize
                # 回写不把国家码降级成 us/eu/asia。
                cells.append((entry.country or entry.market).strip())
                continue
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
