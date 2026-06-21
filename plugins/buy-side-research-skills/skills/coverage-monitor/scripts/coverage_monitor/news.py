from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from html import unescape
from pathlib import Path
import re
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from .coverage import CoverageEntry
from .signals import assess_snapshot


@dataclass(frozen=True)
class NewsItem:
    title: str
    url: str
    source: str = ""
    summary: str = ""
    tier: str = ""
    published_at: str = ""
    query: str = ""


@dataclass(frozen=True)
class ImportantMoverExplainer:
    summary: str
    confidence: str
    evidence: list[NewsItem]
    filings_evidence: list[NewsItem]


# ── helpers ────────────────────────────────────────────

def _dedupe_news(items: list[NewsItem], max_results: int | None = None) -> list[NewsItem]:
    seen: set[str] = set()
    deduped: list[NewsItem] = []
    for item in items:
        if not item.url or item.source == "search_link" or item.url in seen:
            continue
        seen.add(item.url)
        deduped.append(item)
        if max_results is not None and len(deduped) >= max_results:
            break
    return deduped


def _source_host(url: str) -> str:
    return urlparse(url).netloc.lower()


def _fetch_text(url: str, timeout: int = 12) -> str:
    request = Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
    with urlopen(request, timeout=timeout) as response:
        data = response.read(600_000)
    return data.decode("utf-8", errors="ignore")


def _html_title(html_text: str) -> str:
    match = re.search(r"<title[^>]*>(.*?)</title>", html_text, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return ""
    return unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", match.group(1))).strip())


def _meta_description(html_text: str) -> str:
    match = re.search(
        r'<meta[^>]+(?:name|property)=["\'](?:description|og:description)["\'][^>]+content=["\'](.*?)["\']',
        html_text, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return ""
    return unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", match.group(1))).strip())


def _fetch_text_with_fallbacks(url: str, timeout: int = 15) -> str:
    """HTTP GET first; falls to Playwright on exception or Cloudflare challenge page."""
    try:
        text = _fetch_text(url, timeout=timeout)
        if _is_cloudflare_challenge(text):
            raise RuntimeError("Cloudflare challenge detected")
        return text
    except Exception:
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(url, wait_until="domcontentloaded", timeout=max(timeout * 1000, 15000))
                page.wait_for_timeout(3000)
                content = page.content()
                browser.close()
            return content
        except Exception:
            raise


def _is_cloudflare_challenge(html_text: str) -> bool:
    """Detect Cloudflare JS challenge or bot-block pages."""
    lower = html_text[:2000].lower()
    cf_markers = (
        "just a moment",           # Cloudflare JS challenge
        "cf-browser-verify",       # Cloudflare browser check
        "attention required!",     # Cloudflare block
        "please enable cookies",   # common CF message
        "#cf-challenge-running",   # legacy CF challenge
    )
    return any(marker in lower for marker in cf_markers)


# ── company news (headlines only — agent handles Core Watch via WebSearch) ──

def collect_company_news(
    entries: list[CoverageEntry],
    snapshots: dict[str, dict],
    today: str | None = None,
) -> tuple[dict[str, list[NewsItem]], list[str], list[str]]:
    """Collect yfinance headlines. Returns (news_map, gaps, agent_needed_keys).

    News search is agent-driven — this function only collects what's available
    from yfinance snapshots. The caller should use WebSearch/Longbridge for
    Core Watch stocks that need real news.
    """
    result: dict[str, list[NewsItem]] = {}
    gaps: list[str] = []
    agent_needed: list[str] = []

    for entry in entries:
        key = entry.ticker or entry.company
        if not key:
            continue

        snapshot = snapshots.get(key, {})
        items: list[NewsItem] = []

        # yfinance headline (free)
        if snapshot.get("headline") and snapshot.get("url"):
            items.append(NewsItem(
                title=str(snapshot["headline"]), url=str(snapshot["url"]),
                source="yfinance", summary="Latest provider headline.",
                published_at=str(snapshot.get("published_at") or ""),
            ))

        # Core Watch or important mover — agent must search via WebSearch
        assessment = assess_snapshot(snapshot) if snapshot else None
        if entry.monitor_status == "Core" or (assessment and assessment.is_important):
            agent_needed.append(key)

        result[key] = items
        if not items and entry.monitor_status == "Core":
            gaps.append(f"{key}: no_yfinance_headline — agent should search via WebSearch")

    return result, sorted(set(gaps)), sorted(set(agent_needed))


def build_important_mover_explainer(
    entry: CoverageEntry,
    snapshot: dict,
    evidence: list[NewsItem],
    filings_evidence: list[NewsItem],
) -> ImportantMoverExplainer:
    assessment = assess_snapshot(snapshot)
    highlights = ", ".join(assessment.highlight_tags or assessment.trigger_tags) if assessment else "material move"
    move = float(snapshot.get("price_move_pct") or 0.0)
    direction = "上涨" if move >= 0 else "下跌"
    if filings_evidence and len(evidence) >= 2:
        confidence = "High"
    elif filings_evidence or len(evidence) >= 2:
        confidence = "Medium"
    else:
        confidence = "Low"
    top_evidence = "；".join(item.title for item in evidence[:2]) or "暂无明确外部新闻证据"
    official_text = "已找到官方/披露线索。" if filings_evidence else "暂未锁定官方/披露线索。"
    summary = (
        f"{entry.company} 当日{direction}，触发 {highlights}。"
        f"当前最相关的外部证据包括：{top_evidence}。{official_text}"
    )
    return ImportantMoverExplainer(
        summary=summary,
        confidence=confidence,
        evidence=_dedupe_news(evidence, max_results=5),
        filings_evidence=_dedupe_news(filings_evidence, max_results=3),
    )


# ── Playwright headline scraper (fallback for P1 no-RSS sources) ──

def _scrape_headlines(url: str, max_items: int = 5) -> list[tuple[str, str, str]]:
    """Use headless Playwright to extract article headlines from a homepage.
    Returns list of (title, url, published_at)."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return []

    results: list[tuple[str, str, str]] = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=20000)
            page.wait_for_timeout(3000)

            # Extract article-like links: <a> wrapping <h2>/<h3> or with headline classes
            links = page.evaluate("""() => {
                const results = [];
                const seen = new Set();
                // Find all <a> with substantial text or wrapping a heading
                const candidates = document.querySelectorAll('a');
                for (const a of candidates) {
                    const text = (a.textContent || '').trim();
                    if (text.length < 20 || text.length > 300) continue;
                    const href = a.href;
                    if (!href || href === location.href || href.startsWith('javascript:')) continue;
                    // Skip nav/footer links
                    if (a.closest('nav, footer, .nav, .footer, .menu, .sidebar')) continue;
                    const key = href;
                    if (seen.has(key)) continue;
                    seen.add(key);
                    // Prefer links with heading children
                    const hasHeading = a.querySelector('h1, h2, h3, h4');
                    results.push({title: text, url: href, score: hasHeading ? 2 : 1});
                }
                // Sort: heading-wrapped first, then by position
                return results.sort((a, b) => b.score - a.score).slice(0, 20);
            }""")

            for item in links[:max_items]:
                title = item.get("title", "").strip()
                article_url = item.get("url", "")
                if title and article_url:
                    results.append((title, article_url, ""))

            browser.close()
    except Exception:
        pass
    return results


# ── RSS feed parsing ───────────────────────────────────

def _is_substack_url(url: str) -> bool:
    return "substack.com" in urlparse(url).netloc.lower()


def _get_rss_feed_url(source_url: str) -> str | None:
    """Determine RSS feed URL for a source. Substack appends /feed;
    other sites try RSS auto-discovery from homepage HTML.
    Returns None if no feed found.
    """
    if _is_substack_url(source_url):
        return source_url.rstrip("/") + "/feed"

    # Try RSS auto-discovery from homepage
    try:
        html = _fetch_text(source_url, timeout=12)
    except Exception:
        return None

    # <link rel="alternate" type="application/rss+xml" href="...">
    for pattern in (
        r'<link[^>]+type=[\"\']application/rss\+xml[\"\'][^>]+href=[\"\']([^\"\']+)[\"\']',
        r'<link[^>]+href=[\"\']([^\"\']+)[\"\'][^>]+type=[\"\']application/rss\+xml[\"\']',
    ):
        m = re.search(pattern, html, re.IGNORECASE)
        if m:
            feed_url = m.group(1)
            if feed_url.startswith("/"):
                from urllib.parse import urljoin
                feed_url = urljoin(source_url, feed_url)
            return feed_url
    return None


def _parse_rss_items(feed_text: str) -> list[tuple[str, str, str]]:
    """Parse RSS 2.0 or Atom feed. Returns list of (title, url, published_at)."""
    items: list[tuple[str, str, str]] = []

    # Extract all <item> or <entry> blocks
    # RSS 2.0: <item><title>...</title><link>...</link><pubDate>...</pubDate></item>
    # Atom: <entry><title>...</title><link href="..."/><published>...</published></entry>
    item_blocks = re.findall(r'<item[>\s](.*?)</item>', feed_text, re.DOTALL)
    if not item_blocks:
        item_blocks = re.findall(r'<entry[>\s](.*?)</entry>', feed_text, re.DOTALL)

    for block in item_blocks:
        # Title (handle CDATA)
        title_m = re.search(r'<title[^>]*>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>', block, re.DOTALL)
        title = title_m.group(1).strip() if title_m else ""
        # Clean HTML entities
        title = unescape(title).replace("&apos;", "'").replace("&amp;", "&")

        # URL: RSS <link>text</link> or Atom <link href="..."/>
        url = ""
        link_m = re.search(r'<link[^>]*>(.*?)</link>', block, re.DOTALL)
        if link_m:
            url = link_m.group(1).strip()
        if not url:
            link_m = re.search(r'<link[^>]+href=[\"\']([^\"\']+)[\"\']', block)
            if link_m:
                url = link_m.group(1).strip()

        # Date: RSS <pubDate> or Atom <published>/<updated>
        date_str = ""
        for tag in ("pubDate", "published", "updated", "dc:date"):
            date_m = re.search(f'<{tag}>(.*?)</{tag}>', block)
            if date_m:
                date_str = date_m.group(1).strip()
                break

        if title and len(title) > 10:  # skip feed-level titles
            items.append((title, url, date_str))

    return items


def _parse_date_to_str(date_str: str) -> str:
    """Convert various date formats to 'MM-DD HH:MM' string."""
    if not date_str:
        return ""
    try:
        from email.utils import parsedate_to_datetime
        dt = parsedate_to_datetime(date_str)
        return dt.strftime("%m-%d %H:%M")
    except Exception:
        pass
    # Try ISO format
    try:
        from datetime import datetime as dt_mod
        dt = dt_mod.fromisoformat(date_str.replace("Z", "+00:00").replace("+00:00", "+00:00"))
        return dt.strftime("%m-%d %H:%M")
    except Exception:
        return date_str[:16]


# ── industry read-throughs ──────────────────────────────

@dataclass
class SourceResult:
    """Result from fetching a single industry source."""
    source_name: str
    source_url: str
    tier: str
    articles: list[NewsItem]       # today's articles (RSS items within 48h)
    has_rss: bool = False
    is_dry: bool = False           # RSS available but no recent articles
    needs_agent: bool = False      # P1 with no RSS — agent should domain-search
    gap_msg: str = ""


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
    for line in lines[start + 1:]:
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


def _fetch_one_source(industry: str, source: dict[str, str], today: str | None = None) -> SourceResult:
    """Fetch a single industry source via RSS feed.
    Returns SourceResult with today's articles, status flags, and gap info."""
    from datetime import datetime as dt_mod, timedelta, timezone

    source_name = source.get("来源", "")
    source_url = source.get("URL", "")
    tier = source.get("Tier", "P1")
    host = _source_host(source_url)

    # Resolve reference date
    if today:
        ref_date = dt_mod.fromisoformat(today).date()
    else:
        ref_date = dt_mod.now(timezone.utc).date()
    cutoff = ref_date - timedelta(days=1)  # 48h window for weekends

    # Try RSS
    rss_url = _get_rss_feed_url(source_url)
    if not rss_url:
        # P1 without RSS → try Playwright headline scrape, then fallback to agent
        if tier == "P1":
            scraped = _scrape_headlines(source_url, max_items=5)
            if scraped:
                articles = []
                for title, article_url, _date in scraped:
                    articles.append(NewsItem(
                        title=title, url=article_url,
                        source=source_name or host, tier=tier,
                    ))
                return SourceResult(
                    source_name=source_name or host, source_url=source_url, tier=tier,
                    articles=articles, has_rss=False, is_dry=False,
                )
            return SourceResult(
                source_name=source_name or host, source_url=source_url, tier=tier,
                articles=[], has_rss=False, needs_agent=True,
                gap_msg=f"{industry}: P1_NO_RSS_NO_PLAYWRIGHT:{source_name or source_url}",
            )
        # P0/P2 without RSS → just note
        return SourceResult(
            source_name=source_name or host, source_url=source_url, tier=tier,
            articles=[], has_rss=False, is_dry=True,
            gap_msg=f"{industry}: NO_RSS:{source_name or source_url} (tier={tier})",
        )

    # Fetch and parse RSS
    try:
        feed_text = _fetch_text_with_fallbacks(rss_url)
        all_items = _parse_rss_items(feed_text)
    except Exception as exc:
        return SourceResult(
            source_name=source_name or host, source_url=source_url, tier=tier,
            articles=[], has_rss=True, is_dry=True,
            gap_msg=f"{industry}: RSS_FETCH_FAIL:{source_name or source_url} ({exc.__class__.__name__})",
        )

    # Filter to recent articles
    articles: list[NewsItem] = []
    for title, article_url, date_str in all_items:
        parsed_date = _parse_date_to_str(date_str)
        is_recent = False
        if date_str:
            try:
                from email.utils import parsedate_to_datetime
                dt = parsedate_to_datetime(date_str)
                if dt.date() >= cutoff:
                    is_recent = True
            except Exception:
                pass
        if is_recent:
            articles.append(NewsItem(
                title=title,
                url=article_url or source_url,
                source=source_name or host,
                tier=tier,
                published_at=parsed_date,
            ))

    if articles:
        return SourceResult(
            source_name=source_name or host, source_url=source_url, tier=tier,
            articles=articles, has_rss=True, is_dry=False,
        )

    # RSS available but no recent articles
    if tier == "P1":
        latest_info = ""
        if all_items:
            latest_info = f" (latest: {all_items[0][0][:60]} @ {_parse_date_to_str(all_items[0][2])})"
        return SourceResult(
            source_name=source_name or host, source_url=source_url, tier=tier,
            articles=[], has_rss=True, is_dry=True, needs_agent=True,
            gap_msg=f"{industry}: P1_DRY:{source_name or source_url}{latest_info}",
        )

    return SourceResult(
        source_name=source_name or host, source_url=source_url, tier=tier,
        articles=[], has_rss=True, is_dry=True,
    )


def collect_industry_readthroughs(
    workspace: Path,
    today: str | None = None,
    max_workers: int = 8,
) -> tuple[dict[str, list[NewsItem]], dict[str, list[SourceResult]], list[str]]:
    """Fetch industry sources via RSS feed. Returns (articles_by_industry, source_results_by_industry, gaps).
    Parallel fetch — wall clock = slowest single source.
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    industry_root = workspace / "industry"
    if not industry_root.exists():
        return {}, {}, ["industry_dir_missing"]

    # Collect all fetchable (industry, source) pairs
    tasks: list[tuple[str, dict[str, str]]] = []
    industry_sources: dict[str, list[dict[str, str]]] = {}
    for research_md in sorted(industry_root.glob("*/RESEARCH.md")):
        industry = research_md.parent.name
        sources = []
        for source in parse_daily_signal_sources(research_md):
            url = source.get("URL", "")
            if not url or url.startswith("varies by"):
                continue
            sources.append(source)
            tasks.append((industry, source))
        industry_sources[industry] = sources

    if not tasks:
        return {}, {}, ["no_fetchable_sources"]

    gaps: list[str] = []
    results_by_industry: dict[str, list[SourceResult]] = {}

    with ThreadPoolExecutor(max_workers=min(max_workers, len(tasks))) as pool:
        futures = {pool.submit(_fetch_one_source, ind, src, today): (ind, src) for ind, src in tasks}
        for future in as_completed(futures):
            result = future.result()
            industry = futures[future][0]
            results_by_industry.setdefault(industry, []).append(result)
            if result.gap_msg:
                gaps.append(result.gap_msg)

    # Build articles dict (only sources with real articles)
    articles_by_industry: dict[str, list[NewsItem]] = {}
    for industry, results in results_by_industry.items():
        all_articles: list[NewsItem] = []
        for r in results:
            all_articles.extend(r.articles)
        articles_by_industry[industry] = _dedupe_news(all_articles, max_results=30)

    # Check: any industry where ALL P1 sources need agent intervention?
    for industry in sorted(industry_sources):
        if industry not in results_by_industry:
            gaps.append(f"{industry}: no_industry_readthrough_found")
            continue
        results = results_by_industry[industry]
        p1_results = [r for r in results if r.tier == "P1"]
        if p1_results and all(r.needs_agent for r in p1_results):
            domains = [_source_host(r.source_url) for r in p1_results]
            if domains:
                gaps.append(f"{industry}: ALL_P1_NEEDS_AGENT — domain-search: {', '.join(domains)}")

    return articles_by_industry, results_by_industry, sorted(set(gaps))
