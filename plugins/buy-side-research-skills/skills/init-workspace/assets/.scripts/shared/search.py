"""DuckDuckGo HTML search — no API key, no JS, pure HTTP GET.

Two-stage: URL coarse filter (script) → Agent fine review (enrichment).

Usage:
  from search import ddg_search, ddg_search_news
  results = ddg_search("罗博特科 300757 股价", max_results=8)
  news = ddg_search_news("Robo-Technik 300757 stock", max_results=8)
"""

from __future__ import annotations

import html as _html
import re
from urllib.parse import parse_qs, quote_plus, urlparse

import requests

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 stock-monitor/0.1"

# ── URL-level coarse filter ─────────────────────────────

_QUOTE_URL_PATTERNS = [
    r'/(?:quote|equities|stocks/quotes|finance/beta/quote|stocks/[A-Z]+)/',
    r'/stock/[^/]+$',
    r'/corp/go\.php',
    r'/investing/stocks/',
    r'/nkd/company/',
    r'/data/equities/tearsheet/',
    r'stockanalysis\.com/(?:stocks|quote)/',
]


def _is_quote_page(url: str) -> bool:
    """Hard URL filter: obvious stock quote / company profile pages."""
    for pattern in _QUOTE_URL_PATTERNS:
        if re.search(pattern, url):
            return True
    return False


def _is_news_result(title: str, url: str = "") -> bool:
    """Lightweight: URL filter only. Agent does fine-grained review."""
    if len(title.strip()) < 10:
        return False
    if _is_quote_page(url):
        return False
    return True


# ── DDG HTML parsing ───────────────────────────────────

def _decode_ddg_url(raw_url: str) -> str:
    """Decode DuckDuckGo redirect URL to the real target."""
    parsed = urlparse(raw_url)
    qs = parse_qs(parsed.query)
    real = qs.get("uddg", [raw_url])[0]
    if real.startswith("http"):
        return real
    return raw_url


def _parse_ddg_html(html_text: str, max_results: int) -> list[dict]:
    """Parse DuckDuckGo HTML search results."""
    results: list[dict] = []
    for m in re.finditer(
        r'<a[^>]*class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
        html_text,
        re.DOTALL,
    ):
        raw_url = m.group(1)
        url = _decode_ddg_url(raw_url)
        title_raw = m.group(2)
        title = _html.unescape(re.sub(r"<[^>]+>", "", title_raw)).strip()
        if not title:
            continue
        snippet = ""
        sm = re.search(
            r'<a[^>]*class="result__snippet"[^>]*>(.*?)</a>',
            html_text[m.end():m.end() + 2000],
            re.DOTALL,
        )
        if sm:
            snippet = _html.unescape(re.sub(r"<[^>]+>", "", sm.group(1))).strip()
        source = urlparse(url).netloc.replace("www.", "")
        results.append({"title": title, "url": url, "snippet": snippet, "source": source})
        if len(results) >= max_results:
            break
    return results


# ── public API ─────────────────────────────────────────

def ddg_search(query: str, max_results: int = 10, timeout: int = 15) -> list[dict]:
    """Raw DDG HTML search — no filtering. Returns [{title, url, snippet, source}]."""
    url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
    resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=timeout)
    resp.raise_for_status()
    return _parse_ddg_html(resp.text, max_results)


def ddg_search_news(query: str, max_results: int = 10, timeout: int = 15) -> list[dict]:
    """DDG search with URL-level coarse filter. Agent does fine review."""
    raw = ddg_search(query, max_results=max_results * 2, timeout=timeout)
    return [r for r in raw if _is_news_result(r["title"], r.get("url", ""))][:max_results]


def ddg_multi_search(
    queries: list[str],
    max_results_per: int = 8,
    timeout: int = 15,
    dedup: bool = True,
) -> list[dict]:
    """Run multiple DDG queries, merge and deduplicate results."""
    seen: set[str] = set()
    results: list[dict] = []
    for query in queries:
        for r in ddg_search_news(query, max_results=max_results_per, timeout=timeout):
            key = r["url"]
            if dedup and key in seen:
                continue
            seen.add(key)
            results.append(r)
    return results
