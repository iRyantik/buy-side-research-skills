from coverage_monitor.signals import assess_snapshot, quote_exception_status, summarize_data_health


def test_assess_snapshot_uses_stricter_thresholds():
    ordinary = assess_snapshot({"price_move_pct": 5.4, "volume_ratio": 3.1, "gap_pct": 7.2})
    assert ordinary is not None
    assert ordinary.is_mover
    assert not ordinary.is_important
    assert "Return >= 5%" in ordinary.trigger_tags
    assert "Volume >= 3.0x" in ordinary.trigger_tags
    assert "Gap >= 7%" in ordinary.trigger_tags

    important = assess_snapshot({"price_move_pct": 8.6, "volume_ratio": 4.4, "gap_pct": 10.8})
    assert important is not None
    assert important.is_important
    assert "Return >= 8%" in important.highlight_tags
    assert "Volume >= 4.0x" in important.highlight_tags
    assert "Gap >= 10%" in important.highlight_tags


def test_assess_snapshot_ignores_20d_high_low_without_material_thresholds():
    assessment = assess_snapshot(
        {
            "price_move_pct": 1.2,
            "volume_ratio": 1.1,
            "gap_pct": 1.5,
            "near_20d_high": True,
            "near_20d_low": False,
        }
    )
    assert assessment is None


def test_quote_exception_status_is_exception_only():
    assert quote_exception_status({"market_time": "2026-06-20"}, report_day="2026-06-21") is None
    assert quote_exception_status({"quote_status": "Partial"}, report_day="2026-06-21") == "Partial"
    assert quote_exception_status({"quote_status": "No Data"}, report_day="2026-06-21") == "No Data"
    assert quote_exception_status({"market_time": "2026-06-10"}, report_day="2026-06-21") == "Stale"


def test_summarize_data_health_groups_lightweight_counts():
    summary = summarize_data_health(
        [
            "AAA US: no_company_news_found",
            "BBB US: filing_unavailable",
            "CCC US: empty_quote_history",
            "DDD US: source_fetch_failed:https://example.com (HTTPError)",
            "EEE US: weak_search_results",
        ]
    )
    assert "1 no-data ticker" in summary
    assert "1 filing unavailable" in summary
    assert "2 weak news fetch" in summary
    assert "1 source fetch failed" in summary
