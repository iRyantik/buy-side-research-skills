from coverage_monitor.coverage import CoverageEntry
from coverage_monitor.news import (
    NewsItem,
    build_company_search_queries,
    build_important_mover_explainer,
    collect_company_news,
)


class SearchLinkOnlyProvider:
    def search(self, query: str, max_results: int) -> list[NewsItem]:
        return [NewsItem(title=f"Search: {query}", url="https://www.bing.com/search?q=test", source="search_link")]


def test_build_company_search_queries_follow_today_style():
    entry = CoverageEntry(ticker="SPCX US", company="SpaceX")
    queries = build_company_search_queries(entry, "2026-06-21")
    assert any("after:2026-06-21" in query for query in queries)
    assert any("earnings guidance" in query for query in queries)
    assert any("SPCX US" in query or "SpaceX" in query for query in queries)


def test_build_important_mover_explainer_prefers_official_evidence():
    entry = CoverageEntry(ticker="BBB US", company="Beta")
    explainer = build_important_mover_explainer(
        entry,
        {"price_move_pct": 8.4, "volume_ratio": 4.1, "gap_pct": 10.4},
        [
            NewsItem(title="Beta contract win", url="https://example.com/news", source="trade"),
            NewsItem(title="Beta contract update", url="https://example.com/news", source="trade"),
        ],
        [NewsItem(title="Beta Q2 results", url="https://beta.example.com/ir/q2", source="official", summary="official release")],
    )
    assert explainer.confidence == "High"
    assert explainer.filings_evidence
    assert "Beta" in explainer.summary


def test_collect_company_news_does_not_treat_search_link_as_success():
    entry = CoverageEntry(ticker="MYCR SS", company="Mycronic", monitor_status="Core Watch")
    company_news, explainers, gaps = collect_company_news(
        [entry],
        {"MYCR SS": {"price_move_pct": 8.2, "volume_ratio": 4.0, "gap_pct": 10.1}},
        today="2026-06-21",
        provider=SearchLinkOnlyProvider(),
    )
    assert company_news["MYCR SS"] == []
    assert "MYCR SS" not in explainers
    assert any("no_company_news_found" in gap for gap in gaps)
