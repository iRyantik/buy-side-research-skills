"""Load the light workspace context used to rank email information."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class CoverageRow:
    ticker: str
    company_en: str
    company_native: str
    industry: str
    coverage: str
    monitor: str

    @property
    def is_core(self) -> bool:
        return self.monitor.strip().lower() == "core"


def _cells(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def load_coverage(workspace: Path) -> list[CoverageRow]:
    path = workspace / "COVERAGE.md"
    try:
        lines = path.read_text(encoding="utf-8-sig").splitlines()
    except OSError:
        return []

    rows: list[CoverageRow] = []
    headers: list[str] | None = None
    in_coverage = False
    for line in lines:
        if line.strip().lower() == "## coverage":
            in_coverage = True
            headers = None
            continue
        if in_coverage and line.startswith("## "):
            break
        if not in_coverage or not line.lstrip().startswith("|"):
            continue
        cells = _cells(line)
        lowered = [cell.lower() for cell in cells]
        if "ticker" in lowered and "industry" in lowered:
            headers = lowered
            continue
        if headers is None or all(set(cell) <= {"-", ":"} for cell in cells):
            continue
        values = dict(zip(headers, cells))
        ticker = values.get("ticker", "")
        if not ticker:
            continue
        rows.append(CoverageRow(
            ticker=ticker,
            company_en=values.get("company (en)", values.get("company", "")),
            company_native=values.get("company (native)", ""),
            industry=values.get("industry", ""),
            coverage=values.get("coverage", values.get("status", "")),
            monitor=values.get("monitor", ""),
        ))
    return rows


def load_focus(workspace: Path, max_chars: int = 16_000) -> str:
    """读 COVERAGE.md 的 `## Focus` 区（Focus 已合并进 COVERAGE，文件顶部）。"""
    try:
        text = (workspace / "COVERAGE.md").read_text(encoding="utf-8-sig")
    except OSError:
        return ""
    m = re.search(r"^##[ \t]*Focus[ \t]*$(.*?)(?=^##[ \t]*Coverage[ \t]*$|\Z)", text, re.M | re.S)
    return (m.group(1).strip() if m else "")[:max_chars]


def build_context(workspace: Path) -> dict:
    coverage = load_coverage(workspace)
    industries = sorted({row.industry for row in coverage if row.industry})
    return {
        "coverage": [asdict(row) | {"is_core": row.is_core} for row in coverage],
        "covered_industries": industries,
        "focus": load_focus(workspace),
    }


def coverage_lookup(context: dict) -> tuple[dict[str, dict], dict[str, dict]]:
    by_ticker: dict[str, dict] = {}
    by_name: dict[str, dict] = {}
    for row in context.get("coverage", []):
        ticker = str(row.get("ticker", "")).strip().lower()
        if ticker:
            by_ticker[ticker] = row
        for field in ("company_en", "company_native"):
            name = str(row.get(field, "")).strip().lower()
            if name:
                by_name[name] = row
    return by_ticker, by_name
