"""DuckDuckGo HTML search — no API key, no JS, pure HTTP GET.

Usage:
  from search import ddg_search, ddg_search_news
  results = ddg_search("罗博特科 300757 股价", max_results=8)
  news = ddg_search_news("Robo-Technik 300757 stock", max_results=8)

Returns list[dict] with keys: title, url, snippet, source
"""

from __future__ import annotations

import html as _html
import re
from urllib.parse import parse_qs, quote_plus, urlparse

import requests

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 stock-monitor/0.1"

# ── title-pattern filters ──────────────────────────────

_NEWS_BLACKLIST = [
    # English patterns
    r"(?i)\bstock price quote\b",
    r"(?i)\bhistorical data\b",
    r"(?i)\bcompany profile\b",
    r"(?i)\bstock overview\b",
    r"(?i)\bcompany information\b",
    r"(?i)\bstatistics & valuation\b",
    r"(?i)\bstock forecast\b",
    # Chinese patterns — quote pages
    r"股票(?:历史数据|股价_股价行情|行情_走势图)",
    r"(?:最新价格|实时走势图|股价分析预测)",
    r"公司简介",
    r"股票吧行情",
    r"个股行情",
    r"股票行情(?!.*(?:跌|涨|停|异动|主力|资金|公告|减持|增持|收购|合同|订单|业绩|利润))",
    r"_股票行情_",
    r"股票(?:消息公告|行情分析|行情报价)",
    # English quote pages by domain pattern in title
    r"(?i)stock price \|.*quote",
    r"(?i)stock price.*barron",
    r"(?i)stock price.*morningstar",
    r"(?i)stock price.*marketwatch",
]


def _is_news_title(title: str) -> bool:
    """Filter out stock quote pages, profile pages, and other non-news."""
    for pattern in _NEWS_BLACKLIST:
        if re.search(pattern, title):
            return False
    # Skip very short titles (usually nav links)
    if len(title.strip()) < 10:
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
        # Extract snippet (next <a class="result__snippet">)
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
    """DDG search with title-pattern news filtering."""
    raw = ddg_search(query, max_results=max_results, timeout=timeout)
    return [r for r in raw if _is_news_title(r["title"])]


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
