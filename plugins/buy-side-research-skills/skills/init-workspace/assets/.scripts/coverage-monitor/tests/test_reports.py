from coverage_monitor.coverage import CoverageEntry
from coverage_monitor.news import ImportantMoverExplainer, NewsItem
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
                company_native="太空探索技术公司",
                industry="aerospace",
                coverage_status="Core Coverage",
                monitor_status="Core Watch",
            )
        ],
        snapshots={"SPCX US": {"price_move_pct": 8.2, "volume_ratio": 4.2, "gap_pct": 10.2, "last_price": 200, "market_time": "2026-06-21"}},
        today="2026-06-21",
        gaps=[],
        company_news={"SPCX US": [NewsItem(title="SpaceX news", url="https://example.com", source="example")]},
        mover_explainers={
            "SPCX US": ImportantMoverExplainer(
                summary="公司级证据与官方披露都支持这次异动。",
                confidence="High",
                evidence=[NewsItem(title="SpaceX news", url="https://example.com", source="example")],
                filings_evidence=[NewsItem(title="Q2 results", url="https://example.com/ir", source="official")],
            )
        },
        industry_readthroughs={"aerospace": [NewsItem(title="Aerospace read-through", url="https://example.com/a", source="example", tier="P1")]},
    )
    for text in ["Daily Coverage Dashboard", "Movers", "Core Watch", "Industry Tape", "Universe"]:
        assert text in html
    assert "Data Health" not in html
    assert "Confidence" not in html
    assert 'id="universeTable"' in html
    assert "Today" in html
    assert 'data-coverage="core"' in html
    assert "Core Coverage" in html
    assert "Core Watch" in html
    assert "太空探索技术公司" in html
    assert "SpaceX" in html
    assert "Evidence (2)" in html
    assert "Q2 results" in html
    assert "Filings (" not in html


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


def test_dashboard_html_only_lists_threshold_movers_and_highlights_important():
    entries = [
        CoverageEntry(ticker="AAA US", company="Alpha", industry="aerospace", coverage_status="Building Coverage", monitor_status="Daily Watch"),
        CoverageEntry(ticker="BBB US", company="Beta", company_native="贝塔", industry="aerospace", coverage_status="Core Coverage", monitor_status="Core Watch"),
        CoverageEntry(ticker="CCC US", company="Gamma", industry="aerospace", coverage_status="Radar", monitor_status="Daily Watch"),
    ]
    snapshots = {
        "AAA US": {"price_move_pct": 5.2, "volume_ratio": 3.1, "gap_pct": 7.4, "market_time": "2026-06-21"},
        "BBB US": {"price_move_pct": 8.4, "volume_ratio": 4.3, "gap_pct": 10.6, "market_time": "2026-06-21"},
        "CCC US": {"price_move_pct": 2.0, "volume_ratio": 1.1, "gap_pct": 1.2, "near_20d_high": True, "market_time": "2026-06-21"},
    }
    html = render_dashboard_html(
        entries=entries,
        snapshots=snapshots,
        today="2026-06-21",
        gaps=[],
        mover_explainers={
            "BBB US": ImportantMoverExplainer(
                summary="Beta 有强公司级催化。",
                confidence="High",
                evidence=[NewsItem(title="Beta contract win", url="https://example.com/beta", source="example")],
                filings_evidence=[],
            )
        },
    )
    movers_html = html.split('<section id="movers"', 1)[1].split('<section id="core"', 1)[0]
    assert "AAA US" in movers_html
    assert "BBB US" in movers_html
    assert "CCC US" not in movers_html
    assert "Important Move" not in movers_html
    assert "贝塔" in movers_html
    assert "Beta 有强公司级催化。" in movers_html


def test_dashboard_html_shows_exception_only_quote_status():
    entries = [
        CoverageEntry(ticker="AAA US", company="Alpha", industry="aerospace", coverage_status="Core Coverage", monitor_status="Core Watch"),
        CoverageEntry(ticker="BBB US", company="Beta", industry="aerospace", coverage_status="Building Coverage", monitor_status="Daily Watch"),
    ]
    snapshots = {
        "AAA US": {"price_move_pct": 6.0, "volume_ratio": 3.4, "gap_pct": 7.2, "quote_status": "Partial", "market_time": "2026-06-21"},
        "BBB US": {"market_time": "2026-06-21"},
    }
    html = render_dashboard_html(entries=entries, snapshots=snapshots, today="2026-06-21", gaps=["BBB US: weak_search_results"])
    universe_html = html.split('<section id="universe"', 1)[1]
    assert "Partial" in universe_html
    assert "Quote status: Partial" in html
    assert "OK" not in html


def test_dashboard_html_dedupes_identical_native_and_english_names():
    html = render_dashboard_html(
        entries=[
            CoverageEntry(
                ticker="6777 JP",
                company="santec",
                company_native="santec",
                industry="optical-module-equipment",
                coverage_status="Core Coverage",
                monitor_status="Core Watch",
            )
        ],
        snapshots={"6777 JP": {"last_price": 5170, "market_time": "2026-06-21"}},
        today="2026-06-21",
        gaps=[],
    )
    assert "santec</span>" in html
    card_html = html.split('<section id="core"', 1)[1].split('<section id="industry"', 1)[0]
    assert '<span class="company-en">' not in card_html


def test_intraday_alert_only_for_core_watch_material_events():
    entry = CoverageEntry(ticker="MYCR SS", company="Mycronic", monitor_status="Core Watch")
    assert should_alert_intraday(entry, {"price_move_pct": 8.0, "volume_ratio": 4.0, "gap_pct": 10.0, "headline": "earnings released"})
    entry.monitor_status = "Daily Watch"
    assert not should_alert_intraday(entry, {"price_move_pct": 8.0, "volume_ratio": 4.0, "gap_pct": 10.0, "headline": "earnings released"})
