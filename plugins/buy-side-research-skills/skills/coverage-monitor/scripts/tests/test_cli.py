from pathlib import Path

from coverage_monitor.cli import build_universe


def test_build_universe_from_coverage_and_artifacts(tmp_path: Path):
    (tmp_path / "COVERAGE.md").write_text(
        """## Coverage
| Ticker | Company | Industry | Coverage | Monitor | Last Review | Next Trigger | Notes |
|---|---|---|---|---|---|---|---|
| MYCR SS | Mycronic | optical-module-equipment | Core Coverage | Core Watch | 2026-06-01 | Q2 results |  |
""",
        encoding="utf-8",
    )
    company_dir = tmp_path / "industry" / "optical-module-equipment" / "companies" / "mycronic"
    company_dir.mkdir(parents=True)
    (company_dir / "2026-05-30-stock-quickread-mycronic.md").write_text("# Mycronic", encoding="utf-8")

    universe = build_universe(tmp_path, today="2026-06-20")
    assert universe.entries[0].ticker == "MYCR SS"
    assert universe.entries[0].coverage_status == "Core Coverage"
    assert universe.entries[0].monitor_status == "Core Watch"
    assert universe.entries[0].source_path.endswith("industry/optical-module-equipment/companies/mycronic")


def test_build_universe_does_not_add_unregistered_dirs_when_coverage_exists(tmp_path: Path):
    (tmp_path / "COVERAGE.md").write_text(
        """## Coverage
| Ticker | Company | Industry | Coverage | Monitor | Last Review | Next Trigger | Notes |
|---|---|---|---|---|---|---|---|
| SPCX US | SpaceX | aerospace | Core Coverage | Core Watch | 2026-05-22 | news |  |
""",
        encoding="utf-8",
    )
    company_dir = tmp_path / "industry" / "aerospace" / "companies" / "spacex"
    company_dir.mkdir(parents=True)
    (company_dir / "2026-05-22-stock-quickread-spacex.md").write_text("# SpaceX", encoding="utf-8")
    unregistered = tmp_path / "industry" / "aerospace" / "companies" / "unregistered"
    unregistered.mkdir(parents=True)
    (unregistered / "2026-05-20-stock-quickread-unregistered.md").write_text("# unregistered", encoding="utf-8")

    universe = build_universe(tmp_path, today="2026-06-20")
    assert [entry.company for entry in universe.entries] == ["SpaceX"]
    assert universe.entries[0].ticker == "SPCX US"
    assert universe.entries[0].coverage_status == "Core Coverage"
    assert "unregistered_company_dir:industry/aerospace/companies/unregistered" in universe.gaps


def test_build_universe_discovers_company_without_coverage_row(tmp_path: Path):
    company_dir = tmp_path / "industry" / "semicap" / "companies" / "santec"
    company_dir.mkdir(parents=True)
    (company_dir / "2026-06-01-stock-quickread-santec.md").write_text("# santec", encoding="utf-8")

    universe = build_universe(tmp_path, today="2026-06-20")
    assert universe.entries[0].company == "santec"
    assert universe.entries[0].coverage_status == "Building Coverage"
    assert universe.entries[0].monitor_status == "Daily Watch"


def test_build_universe_flags_core_review_due_from_deepwork_artifacts(tmp_path: Path):
    (tmp_path / "COVERAGE.md").write_text(
        """## Coverage
| Ticker | Company | Industry | Coverage | Monitor | Last Review | Next Trigger | Notes |
|---|---|---|---|---|---|---|---|
| SPCX US | SpaceX | aerospace | Building Coverage | Daily Watch | 2026-06-18 | launch cadence update |  |
""",
        encoding="utf-8",
    )
    company_dir = tmp_path / "industry" / "aerospace" / "companies" / "spacex"
    company_dir.mkdir(parents=True)
    (company_dir / "2026-06-15-stock-quickread-spacex.md").write_text("# quickread", encoding="utf-8")
    (company_dir / "2026-06-18-alpha-thesis-spacex.md").write_text("# thesis", encoding="utf-8")
    (company_dir / "RESEARCH.md").write_text("# research\n", encoding="utf-8")

    universe = build_universe(tmp_path, today="2026-06-20")

    assert universe.entries[0].coverage_status == "Building Coverage"
    assert "core_review_due:SPCX US" in universe.gaps
