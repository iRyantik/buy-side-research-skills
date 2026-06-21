from __future__ import annotations

from dataclasses import dataclass
import base64
from html import unescape
from pathlib import Path
import re
from typing import Any
from urllib.parse import parse_qs, quote_plus, urlparse
from urllib.request import Request, urlopen

from .coverage import CoverageEntry
from .tickers import build_ticker_runtime


@dataclass(frozen=True)
class NewsItem:
    title: str
    url: str
    source: str = ""
    summary: str = ""
    tier: str = ""


def _fetch_text(url: str, timeout: int = 8) -> str:
    request = Request(url, headers={"User-Agent": "Mozilla/5.0 coverage-monitor"})
    with urlopen(request, timeout=timeout) as response:  # nosec - user-controlled research sources
        data = response.read(500_000)
    return data.decode("utf-8", errors="ignore")


def _html_title(html_text: str) -> str:
    match = re.search(r"<title[^>]*>(.*?)</title>", html_text, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return ""
    title = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", match.group(1))).strip()
    return unescape(title)


def _ddg_links(query: str, max_results: int = 3) -> list[NewsItem]:
    url = f"https://duckduckgo.com/html/?q={quote_plus(query)}"
    try:
        html_text = _fetch_text(url)
    except Exception:
        return []
    items: list[NewsItem] = []
    for match in re.finditer(r'class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', html_text, flags=re.IGNORECASE | re.DOTALL):
        href = unescape(match.group(1))
        title = unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", match.group(2))).strip())
        if title and href:
            items.append(NewsItem(title=title, url=href, source=urlparse(href).netloc))
        if len(items) >= max_results:
            break
    return items


def _bing_links(query: str, max_results: int = 3) -> list[NewsItem]:
    url = f"https://www.bing.com/search?q={quote_plus(query)}"
    try:
        html_text = _fetch_text(url)
    except Exception:
        return []
    items: list[NewsItem] = []
    for block in re.findall(r'<li class="b_algo".*?</li>', html_text, flags=re.IGNORECASE | re.DOTALL):
        match = re.search(r"<h2[^>]*>\s*<a[^>]*href=\"([^\"]+)\"[^>]*>(.*?)</a>", block, flags=re.IGNORECASE | re.DOTALL)
        if not match:
            continue
        href = _decode_bing_url(unescape(match.group(1)))
        title = unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", match.group(2))).strip())
        if title and href:
            items.append(NewsItem(title=title, url=href, source=urlparse(href).netloc))
        if len(items) >= max_results:
            break
    return items


def _decode_bing_url(href: str) -> str:
    parsed = urlparse(href)
    encoded = parse_qs(parsed.query).get("u", [""])[0]
    if not encoded.startswith("a1"):
        return href
    payload = encoded[2:]
    try:
        padding = "=" * (-len(payload) % 4)
        return base64.urlsafe_b64decode((payload + padding).encode("ascii")).decode("utf-8", errors="ignore")
    except Exception:
        return href


def _search_links(query: str, max_results: int = 3) -> list[NewsItem]:
    items = _ddg_links(query, max_results=max_results)
    if items:
        return items
    items = _bing_links(query, max_results=max_results)
    if items:
        return items
    return [
        NewsItem(
            title=f"Search: {query}",
            url=f"https://www.bing.com/search?q={quote_plus(query)}",
            source="search_link",
            summary="Search fallback; no direct HTML result parsed.",
        )
    ]


def _relevant_news_items(items: list[NewsItem], entry: CoverageEntry) -> list[NewsItem]:
    runtime = build_ticker_runtime(entry.ticker, entry.company)
    raw_tokens = [entry.company, *(runtime.search_aliases or ())]
    tokens: set[str] = set()
    for raw in raw_tokens:
        for token in re.findall(r"[a-z0-9]+", raw.lower()):
            if len(token) >= 3 and token not in {"news", "stock", "latest", "results", "company"}:
                tokens.add(token)
    filtered = []
    for item in items:
        haystack = f"{item.title} {item.url}".lower()
        if any(token in haystack for token in tokens):
            filtered.append(item)
    if filtered:
        return filtered
    query = " ".join([*(runtime.search_aliases[:2] or (entry.company,)), "stock news results contract order latest"])
    return [NewsItem(title=f"Search: {query}", url=f"https://www.bing.com/search?q={quote_plus(query)}", source="search_link")]



def parse_daily_signal_sources(research_md: Path) -> list[dict[str, str]]:
    if not research_md.exists():
        return []
    lines = research_md.read_text(encoding="utf-8").splitlines()
    start = None
    for index, line in enumerate(lines):
        if line.strip().lower() == "### daily signal sources":
            start = index
            break
    if start is None:
        return []
    table_lines = []
    for line in lines[start + 1 :]:
        if table_lines and not line.lstrip().startswith("|"):
            break
        if line.lstrip().startswith("|"):
            table_lines.append(line)
    if len(table_lines) < 3:
        return []
    headers = [cell.strip() for cell in table_lines[0].strip().strip("|").split("|")]
    sources: list[dict[str, str]] = []
    for line in table_lines[2:]:
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < len(headers):
            cells += [""] * (len(headers) - len(cells))
        row = dict(zip(headers, cells))
        if row.get("URL"):
            sources.append(row)
    return sources


def collect_company_news(entries: list[CoverageEntry], snapshots: dict[str, dict[str, Any]]) -> tuple[dict[str, list[NewsItem]], list[str]]:
    result: dict[str, list[NewsItem]] = {}
    gaps: list[str] = []
    for entry in entries:
        if entry.monitor_status != "Core Watch":
            continue
        key = entry.ticker or entry.company
        items: list[NewsItem] = []
        snapshot = snapshots.get(key, {})
        if snapshot.get("headline") and snapshot.get("url"):
            items.append(NewsItem(title=str(snapshot["headline"]), url=str(snapshot["url"]), source="yfinance", summary="Latest provider headline."))
        runtime = build_ticker_runtime(entry.ticker, entry.company)
        query = " ".join([*(runtime.search_aliases[:2] or (entry.company,)), "stock news results contract order latest"])
        for item in _relevant_news_items(_search_links(query, max_results=5), entry):
            if item.url not in {existing.url for existing in items}:
                items.append(item)
        if not items:
            gaps.append(f"{entry.company}: no_company_news_found")
        result[key] = items[:4]
    return result, gaps


def collect_industry_readthroughs(workspace: Path) -> tuple[dict[str, list[NewsItem]], list[str]]:
    industry_root = workspace / "industry"
    result: dict[str, list[NewsItem]] = {}
    gaps: list[str] = []
    if not industry_root.exists():
        return result, ["industry_dir_missing"]
    for research_md in sorted(industry_root.glob("*/RESEARCH.md")):
        industry = research_md.parent.name
        sources = parse_daily_signal_sources(research_md)
        items: list[NewsItem] = []
        for source in sources:
            url = source.get("URL", "")
            if not url or url == "varies by company":
                continue
            try:
                title = _html_title(_fetch_text(url))
            except Exception as exc:
                gaps.append(f"{industry}: source_fetch_failed:{source.get('来源') or url} ({exc.__class__.__name__})")
                continue
            if title:
                items.append(
                    NewsItem(
                        title=title,
                        url=url,
                        source=source.get("来源", "") or urlparse(url).netloc,
                        summary=source.get("Use For", ""),
                        tier=source.get("Tier", ""),
                    )
                )
            if len(items) >= 8:
                break
        if not items:
            fallback_items = _search_links(f"{industry} industry news latest", max_results=5)
            items.extend(fallback_items)
            if not fallback_items:
                gaps.append(f"{industry}: no_industry_readthrough_found")
        result[industry] = items
    return result, gaps
