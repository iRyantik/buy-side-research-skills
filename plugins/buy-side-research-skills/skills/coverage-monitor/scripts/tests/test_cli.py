from pathlib import Path

from coverage_monitor.cli import build_universe


def test_build_universe_from_coverage_and_artifacts(tmp_path: Path):
    (tmp_path / "COVERAGE.md").write_text(
        """## Coverage
| Ticker | Company | Industry | Research Tier | Alert Tier | Stage | Last Review | Next Trigger | Monitor | Notes |
|---|---|---|---|---|---|---|---|---|---|
| MYCR.ST | Mycronic | optical-module-equipment |  |  | active | 2026-06-01 | Q2 results | yes |  |
""",
        encoding="utf-8",
    )
    company_dir = tmp_path / "industry" / "optical-module-equipment" / "companies" / "mycronic"
    company_dir.mkdir(parents=True)
    (company_dir / "2026-05-30-stock-quickread-mycronic.md").write_text("# Mycronic", encoding="utf-8")

    universe = build_universe(tmp_path, today="2026-06-20")
    assert universe.entries[0].ticker == "MYCR.ST"
    assert universe.entries[0].research_tier == "T1"
    assert universe.entries[0].alert_tier == "A1"
    assert universe.entries[0].source_path.endswith("industry/optical-module-equipment/companies/mycronic")


def test_build_universe_discovers_company_without_coverage_row(tmp_path: Path):
    company_dir = tmp_path / "industry" / "semicap" / "companies" / "santec"
    company_dir.mkdir(parents=True)
    (company_dir / "2026-06-01-stock-quickread-santec.md").write_text("# santec", encoding="utf-8")

    universe = build_universe(tmp_path, today="2026-06-20")
    assert universe.entries[0].company == "santec"
    assert universe.entries[0].research_tier == "T3"
    assert universe.entries[0].alert_tier == "A3"
