from coverage_monitor.coverage import CoverageEntry, parse_coverage_markdown, render_coverage_markdown
from coverage_monitor.tiering import derive_alert_tier, derive_research_tier


def test_parse_legacy_coverage_table():
    text = """# Coverage Map

| 行业 | 公司 | Ticker | 主行业 | 文件位置 | 最新 artifact | 状态 |
|---|---|---|---|---|---|---|
| optical-module-equipment | Mycronic | MYCR.ST | equipment | industry/optical-module-equipment/companies/mycronic | 2026-05-30-stock-quickread-mycronic.md | active |
"""
    rows = parse_coverage_markdown(text)
    assert rows[0].ticker == "MYCR.ST"
    assert rows[0].company == "Mycronic"
    assert rows[0].industry == "optical-module-equipment"
    assert rows[0].stage == "active"


def test_render_normalized_columns():
    rows = parse_coverage_markdown("""## Coverage
| Ticker | Company | Industry | Research Tier | Alert Tier | Stage | Last Review | Next Trigger | Monitor | Notes |
|---|---|---|---|---|---|---|---|---|---|
| 6777.T | santec | optical-module-equipment | T1 | A1 | active | 2026-06-01 | earnings | yes | core |
""")
    output = render_coverage_markdown(rows)
    assert "| Ticker | Company | Industry | Research Tier | Alert Tier | Stage | Last Review | Next Trigger | Monitor | Notes |" in output
    assert "| 6777.T | santec | optical-module-equipment | T1 | A1 | active | 2026-06-01 | earnings | yes | core |" in output


def test_research_tier_uses_artifacts_trigger_and_recency_not_conviction():
    entry = CoverageEntry(
        ticker="MYCR.ST",
        company="Mycronic",
        stage="active",
        last_review="2026-06-01",
        next_trigger="2026-07-15 earnings",
        notes="conviction unknown",
    )
    assert derive_research_tier(entry, today="2026-06-20", artifact_count=3) == "T1"

    entry.notes = "High conviction"
    entry.next_trigger = ""
    assert derive_research_tier(entry, today="2026-06-20", artifact_count=3) == "T2"


def test_alert_tier_is_separate_from_research_tier():
    entry = CoverageEntry(ticker="6777.T", company="santec", research_tier="T1", monitor="yes")
    assert derive_alert_tier(entry) == "A1"
    entry.monitor = "daily"
    assert derive_alert_tier(entry) == "A2"
    entry.monitor = "no"
    assert derive_alert_tier(entry) == "A3"
