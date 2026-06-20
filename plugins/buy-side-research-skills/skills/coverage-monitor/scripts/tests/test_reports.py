from coverage_monitor.coverage import CoverageEntry
from coverage_monitor.reports import render_daily_markdown, should_alert_intraday


def test_daily_report_has_fixed_five_sections():
    text = render_daily_markdown(
        entries=[CoverageEntry(ticker="MYCR.ST", company="Mycronic", industry="optical-module-equipment", research_tier="T1", alert_tier="A1")],
        snapshots={},
        today="2026-06-20",
        gaps=["WECOM_WEBHOOK_URL missing"],
    )
    for heading in [
        "## 1. Top Alerts",
        "## 2. Industry Coverage",
        "## 3. Upcoming Triggers",
        "## 4. Data & Monitor Gaps",
        "## 5. Appendix: Full Watchlist Snapshot",
    ]:
        assert heading in text


def test_intraday_alert_only_for_a1_material_events():
    entry = CoverageEntry(ticker="MYCR.ST", company="Mycronic", alert_tier="A1")
    assert should_alert_intraday(entry, {"price_move_pct": 8.0, "headline": "earnings released"})
    entry.alert_tier = "A2"
    assert not should_alert_intraday(entry, {"price_move_pct": 8.0, "headline": "earnings released"})
