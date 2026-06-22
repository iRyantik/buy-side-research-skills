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

# ── content-based news scoring ──────────────────────────

def _news_score(title: str, snippet: str = "", url: str = "") -> int:
    """Score a DDG result: higher = more likely real news. Threshold >= 25."""
    score = 0

    # ── 正向信号 (positive signals) ──
    NEG_SIGNALS = (
        '跌','涨','涨停','跌停','异动','主力','资金','减持','增持',
        '收购','合同','订单','签约','宣布','发布','获批','上市','暴跌','飙升',
        '净卖出','净买入','板块跌幅','跳空','翻倍','新高','新低',
        'announces','launches','wins','secures','signs','raises',
        'cuts','slumps','surges','jumps','drops','beats','misses',
        'contract','order','backlog','IPO','acquires','partners',
        'guidance','earnings','revenue','profit','dividend',
    )
    for w in NEG_SIGNALS:
        if w in title:
            score += 35
            break  # one strong signal is enough

    if len(title.strip()) > 30:
        score += 10
    if len(snippet) > 80:
        score += 15
    if re.search(r'[\d,.]+[万亿兆千百亿]|[\d,.]+[BMK]b?|[\d,.]+%|¥[\d,]+|₩[\d,]+|\$[\d,]+|USD [\d,]+', title):
        score += 10

    # ── 负向信号 (negative signals) ──
    if re.search(r'(?i)\bstock price (?:quote|overview|news & analysis)\b', title):
        score -= 60
    if re.search(r'(?i)\b(?:company profile|historical data|stock forecast)\b', title):
        score -= 50
    if re.search(r'股票(?:历史数据|行情_走势图|行情_新浪|行情_九方|行情分析|股价行情|消息公告)', title):
        score -= 50
    if re.search(r'(?:最新价格|行情_走势图|实时走势图)', title):
        score -= 50
    if re.search(r'_股票(?:行情|股价)_', title):
        score -= 40
    if len(title) < 20 and len(snippet) < 40:
        score -= 30
    # URL-based: clear quote pages get heavy penalty
    if re.search(r'/(?:quote|equities|stocks/quotes|finance/beta/quote)/', url):
        score -= 25
    elif '/stock/' in url and not re.search(r'/news|/article|/story|/press', url):
        score -= 15
    if re.search(r'(?i)stock price.*(?:quote|chart|overview)', title):
        score -= 25

    return score


def _is_news_title(title: str, snippet: str = "", url: str = "") -> bool:
    """Score-based: >= 30 = keep as news."""
    if len(title.strip()) < 10:
        return False
    return _news_score(title, snippet, url) >= 20


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
    """DDG search with content-based news scoring."""
    raw = ddg_search(query, max_results=max_results * 2, timeout=timeout)
    return [r for r in raw if _is_news_title(r["title"], r.get("snippet", ""), r.get("url", ""))][:max_results]


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
