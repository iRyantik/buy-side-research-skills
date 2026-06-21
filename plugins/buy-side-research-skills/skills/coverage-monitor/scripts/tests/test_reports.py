from coverage_monitor.coverage import CoverageEntry
from coverage_monitor.news import NewsItem
from coverage_monitor.reports import render_daily_markdown, render_dashboard_html, should_alert_intraday


def test_daily_report_has_fixed_five_sections():
    text = render_daily_markdown(
        entries=[
            CoverageEntry(
                ticker="MYCR SS",
                company="Mycronic",
                industry="optical-module-equipment",
                coverage_status="Core Coverage",
                monitor_status="Core Watch",
            )
        ],
        snapshots={},
        today="2026-06-20",
        gaps=["SMTP_HOST missing"],
    )
    for heading in [
        "## 1. Executive Snapshot",
        "## 2. Price Movers & Explanations",
        "## 3. Core Watch Company News",
        "## 4. Industry Read-Throughs",
        "## 5. Coverage Gaps",
    ]:
        assert heading in text
    assert "T1" not in text
    assert "A1" not in text


def test_dashboard_html_uses_four_tab_dashboard_shell():
    html = render_dashboard_html(
        entries=[
            CoverageEntry(
                ticker="SPCX US",
                company="SpaceX",
                industry="aerospace",
                coverage_status="Core Coverage",
                monitor_status="Core Watch",
            )
        ],
        snapshots={"SPCX US": {"price_move_pct": 5.2, "volume_ratio": 1.5, "gap_pct": 0.2, "last_price": 200, "market_time": "2026-06-21"}},
        today="2026-06-21",
        gaps=[],
        company_news={"SPCX US": [NewsItem(title="SpaceX news", url="https://example.com", source="example")]},
        industry_readthroughs={"aerospace": [NewsItem(title="Aerospace read-through", url="https://example.com/a", source="example", tier="P1")]},
    )
    for text in ["Daily Coverage Dashboard", "Movers", "Core Watch", "Industry Tape", "Universe"]:
        assert text in html
    assert 'class="tab-button active" data-tab="movers"' in html
    assert 'id="universeTable"' in html
    assert "Today Return" in html
    assert 'data-coverage="core"' in html
    assert "Core Coverage" in html
    assert "Core Watch" in html


def test_dashboard_html_orders_universe_with_semantic_priority_before_abs_return():
    entries = [
        CoverageEntry(
            ticker="AAA US",
            company="Alpha",
            industry="aerospace",
            coverage_status="Building Coverage",
            monitor_status="Daily Watch",
        ),
        CoverageEntry(
            ticker="BBB US",
            company="Beta",
            industry="aerospace",
            coverage_status="Core Coverage",
            monitor_status="Core Watch",
        ),
        CoverageEntry(
            ticker="CCC US",
            company="Gamma",
            industry="aerospace",
            coverage_status="Building Coverage",
            monitor_status="Daily Watch",
        ),
        CoverageEntry(
            ticker="DDD US",
            company="Delta",
            industry="aerospace",
            coverage_status="Radar",
            monitor_status="Daily Watch",
        ),
    ]
    html = render_dashboard_html(
        entries=entries,
        snapshots={
            "AAA US": {"price_move_pct": 5.0},
            "BBB US": {"price_move_pct": 1.0},
            "CCC US": {"price_move_pct": 9.0},
            "DDD US": {"price_move_pct": 12.0},
        },
        today="2026-06-21",
        gaps=[],
    )
    universe_html = html.split('id="universeTable"', 1)[1]
    ordered = [universe_html.index(ticker) for ticker in ("BBB US", "CCC US", "AAA US", "DDD US")]
    assert ordered == sorted(ordered)


def test_intraday_alert_only_for_core_watch_material_events():
    entry = CoverageEntry(ticker="MYCR SS", company="Mycronic", monitor_status="Core Watch")
    assert should_alert_intraday(entry, {"price_move_pct": 8.0, "headline": "earnings released"})
    entry.monitor_status = "Daily Watch"
    assert not should_alert_intraday(entry, {"price_move_pct": 8.0, "headline": "earnings released"})
