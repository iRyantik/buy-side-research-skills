from coverage_monitor.coverage import CoverageEntry, parse_coverage_markdown, render_coverage_markdown
from coverage_monitor.tiering import derive_coverage_status, derive_monitor_status, should_trigger_core_review


def test_parse_coverage_table_uses_semantic_status_fields():
    text = """# Coverage Map

## Coverage
| Ticker | Company | Industry | Coverage | Monitor | Last Review | Next Trigger | Notes |
|---|---|---|---|---|---|---|---|
| SPCX US | SpaceX | aerospace | Core Coverage | Core Watch | 2026-05-22 | news | listed |
"""
    rows = parse_coverage_markdown(text)
    assert len(rows) == 1
    assert rows[0].ticker == "SPCX US"
    assert rows[0].coverage_status == "Core Coverage"
    assert rows[0].monitor_status == "Core Watch"


def test_parse_prefers_coverage_section_over_contract_table():
    text = """# Coverage Map

## Coverage Contract
| Field | Values | Contract |
|---|---|---|
| Coverage | Core Coverage / Building Coverage / Radar | contract |

## Coverage
| Ticker | Company | Industry | Coverage | Monitor | Last Review | Next Trigger | Notes |
|---|---|---|---|---|---|---|---|
| 6777 JP | Santec | optical-module-equipment | Core Coverage | Core Watch | 2026-06-15 | earnings | core |
"""
    rows = parse_coverage_markdown(text)
    assert len(rows) == 1
    assert rows[0].ticker == "6777 JP"
    assert rows[0].company == "Santec"


def test_render_normalized_columns_use_new_contract_only():
    rows = parse_coverage_markdown("""## Coverage
| Ticker | Company | Industry | Coverage | Monitor | Last Review | Next Trigger | Notes |
|---|---|---|---|---|---|---|---|
| 6777 JP | Santec | optical-module-equipment | Core Coverage | Core Watch | 2026-06-15 | earnings | core |
""")
    output = render_coverage_markdown(rows)
    assert "| Ticker | Company | Industry | Coverage | Monitor | Last Review | Next Trigger | Notes |" in output
    assert "Research Tier" not in output
    assert "Alert Tier" not in output
    assert "| 6777 JP | Santec | optical-module-equipment | Core Coverage | Core Watch | 2026-06-15 | earnings | core |" in output


def test_coverage_status_defaults_to_building_and_core_requires_review_gate():
    entry = CoverageEntry(
        ticker="MYCR SS",
        company="Mycronic",
        last_review="2026-06-01",
        next_trigger="2026-07-15 earnings",
        notes="conviction unknown",
        quickread_artifact_count=1,
        deepwork_artifact_count=1,
        has_research_memory=True,
    )
    assert derive_coverage_status(entry, today="2026-06-20", artifact_count=3) == "Building Coverage"
    assert should_trigger_core_review(entry, today="2026-06-20")

    entry.notes = "High conviction"
    entry.next_trigger = ""
    assert derive_coverage_status(entry, today="2026-06-20", artifact_count=3) == "Building Coverage"
    assert not should_trigger_core_review(entry, today="2026-06-20")


def test_monitor_status_is_separate_from_coverage_status():
    entry = CoverageEntry(ticker="6777 JP", company="Santec", coverage_status="Core Coverage")
    assert derive_monitor_status(entry) == "Core Watch"
    entry.coverage_status = "Building Coverage"
    assert derive_monitor_status(entry) == "Daily Watch"
