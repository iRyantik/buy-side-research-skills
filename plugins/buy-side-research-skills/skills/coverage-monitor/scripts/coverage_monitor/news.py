from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from html import unescape
from pathlib import Path
import json
import sys
import re
from urllib.parse import urlparse, quote
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

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


# ---- 页面/低信息量过滤（阶段1 新闻质量）----
# 1A 标题黑名单：行情数据/异动提示/荐股/行情页等"股票网站页面"特征（多语言）
_PAGE_TITLE_PATTERNS = (
    r"主力资金", r"主力净", r"融资余额", r"融资净", r"大宗交易", r"龙虎榜",
    r"异动快报", r"触及涨停板", r"触及跌停板", r"跌停", r"涨停",
    r"行情快报", r"股票行情",
    r"個股概覽", r"股價走勢", r"即時報價", r"盤後速報",
    r"复盘", r"復盤", r"早评", r"早評",
    r"投资分析", r"投資分析", r"투자분석",
    r"e종목", r"討論牆", r"爆料",
    r"限售股解禁", r"市盈率",
    r"Stock Market Today", r"Dow Drops", r"Stocks to Buy", r"Should You Buy",
    r"回顧",
)
_PAGE_TITLE_RE = re.compile("|".join(_PAGE_TITLE_PATTERNS))

# 1B 来源黑名单：聚合/SEO 发布站（source 字段子串匹配）
_PAGE_SOURCE_BLACKLIST = (
    "investing.com", "investing", "seekingalpha", "seeking alpha", "benzinga",
    "motley fool", "fool.com", "zacks", "marketscreener", "247wallst",
    "marketbeat", "gurufocus", "insidermonkey", "tipranks", "stocktwits",
    "yahoo", "longport",
)


def _is_page_item(item: NewsItem) -> bool:
    """命中页面/低信息量特征则 True（应丢弃）：标题黑名单 + 来源黑名单。"""
    if _PAGE_TITLE_RE.search(item.title or ""):
        return True
    src = (item.source or "").lower()
    for bad in _PAGE_SOURCE_BLACKLIST:
        if bad in src:
            return True
    return False


def _filter_page_items(items: list[NewsItem]) -> list[NewsItem]:
    """丢弃页面条目，保留真新闻；记录丢弃量。"""
    kept = [it for it in items if not _is_page_item(it)]
    dropped = len(items) - len(kept)
    if dropped:
        print(f"[news] 页面过滤丢弃 {dropped}/{len(items)} 条", file=sys.stderr)
    return kept


def _source_host(url: str) -> str:
    return urlparse(url).netloc.lower()

# ── Google News RSS（免费无 key，韩/日/台/A 股覆盖主力层）──
_GN_LOCALE = {
    (".SS", ".SZ", ".SH", ".CN"): ("zh-CN", "CN", "CN:zh-Hans"),
    (".TW", ".TT"): ("zh-TW", "TW", "TW:zh-Hant"),
    (".HK",): ("zh-HK", "HK", "HK:zh-Hant"),
    (".KS", ".KQ"): ("ko", "KR", "KR:ko"),
    (".T", ".JP"): ("ja", "JP", "JP:ja"),
}
_GN_DEFAULT = ("en-US", "US", "US:en")


def _gn_locale_for(ticker: str) -> tuple[str, str, str]:
    for suffixes, loc in _GN_LOCALE.items():
        if any(ticker.endswith(s) for s in suffixes):
            return loc
    return _GN_DEFAULT


def _strip_gn_source(title: str) -> str:
    """Google News 标题格式 `标题 - 来源 - 来源`：剥掉尾部重复/来源段。"""
    parts = [p.strip() for p in title.split(" - ")]
    while len(parts) >= 2 and parts[-1] == parts[-2]:
        parts.pop()
    if len(parts) >= 2 and len(parts[-1]) <= 14 and " " not in parts[-1]:
        parts.pop()
    return " - ".join(parts)


def _gn_news(query: str, ticker: str, max_items: int = 8, timeout: int = 12) -> list[NewsItem]:
    """Google News RSS search；query 自动 URL-encode，限 7 天内。"""
    from urllib.parse import quote
    hl, gl, ceid = _gn_locale_for(ticker)
    url = (f"https://news.google.com/rss/search?q={quote(query)}%20when%3A7d"
           f"&hl={hl}&gl={gl}&ceid={ceid}")
    req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(req, timeout=timeout) as resp:
        data = resp.read(500_000).decode("utf-8", errors="ignore")
    root = ET.fromstring(data)
    items: list[NewsItem] = []
    for it in root.findall(".//item")[:max_items]:
        title = (it.findtext("title") or "").strip()
        if not title:
            continue
        link = (it.findtext("link") or "").strip()
        if not link:
            continue
        pub = (it.findtext("pubDate") or "")[:16]
        src = (it.findtext("source") or "").strip() or "google-news"
        items.append(NewsItem(
            title=_strip_gn_source(title), url=link,
            source=src, summary="", published_at=pub))
    return items


def _gn_company_queries(entry: CoverageEntry) -> list[str]:
    """GN 查询：native 名 + EN 名，均不带 ticker 后缀（`012450.KS` 会拖垮命中）。

    Google News 会把 `代码.交易所` 当实体/噪音做 AND 匹配，实测 `한화에어로스페이스 012450.KS`
    0 条 vs 纯名 8 条。名字全空时才退化用裸 ticker 代码。
    """
    native = (entry.company_native or "").strip()
    en = (entry.company or "").strip()
    ticker = (entry.ticker or "").strip()
    queries = []
    if native:
        queries.append(native)
    if en and en != native:
        queries.append(en)
    if not queries:
        queries.append(ticker.split(".")[0] if "." in ticker else ticker)
    return queries


# ── 新闻标签（财报/订单/股价/分析师/并购；无匹配 → ""）──
_NEWS_TAG_RULES = [
    ("财报", r"earnings|실적|결산|业绩|财报|中报|半年报|年报|季报|盈喜|盈警|guidance|profit"),
    ("订单", r"수주|contract|订单|合同|中标|签约|签订|award|order"),
    ("股价", r"주가|특징주|股价|stock|share price"),
    ("分析师", r"analyst|목표주가|target price|目标价|rating"),
    ("并购", r"인수|acquisition|merger|并购|합병|takeover"),
]


def tag_news_title(title: str) -> str:
    """标题关键词打标签；无匹配返回空串。"""
    for tag, pat in _NEWS_TAG_RULES:
        if re.search(pat, title, re.I):
            return tag
    return ""


# ── 2B 事件方向映射：标题 → 利好/利空/中性（供 2C 方向一致性校验）──
_POSITIVE_PATTERNS = re.compile(
    r"净利.*增|利润.*增|同比.*增|增长|上扬|飙升|暴增|大增|创纪录|新高|上调|超预期"
    r"|beat|raised|upgrade|outperform|盈喜"
    r"|수주|계약|증가|급증|호조|확대|수출|신규|대규모|상승|기대|공급계약"
    r"|订单|中标|合同|签约|签订|获批|放量"
)
_NEGATIVE_PATTERNS = re.compile(
    r"下调|目标价.*下调|下调至|诉讼|公诉|기소|뇌물|혐의|하향|급락|부진|적자|손실|해지|취소|조정|우려|악재"
    r"|리콜|제재|과징금|규제|lawsuit|probe|investigation|cut|downgrade|withdraw|cancel|delay|검토"
    r"|下滑|亏损|暴跌|跌停|解禁|盈警|净利.*减|利润.*减|减持|终止|不及预期"
)
_TAG_DIRECTION = {
    "财报": None,
    "订单": "positive",
    "分析师": None,
    "股价": None,
    "并购": None,
}


def event_direction(title: str, tag: str = "") -> str | None:
    """事件方向：positive / negative / neutral。

    先扫方向关键词（正负都有 → neutral 混合），无关键词时按 tag 默认（订单=利好）。
    """
    title = title or ""
    pos = _POSITIVE_PATTERNS.search(title)
    neg = _NEGATIVE_PATTERNS.search(title)
    if pos and neg:
        return "neutral"
    if neg:
        return "negative"
    if pos:
        return "positive"
    return _TAG_DIRECTION.get(tag or "") or "neutral"


_KANA = re.compile(r"[぀-ヿ]")       # 平/片假名 → 日文
_HANGUL = re.compile(r"[가-힯]")   # 谚文 → 韩文
_ZH_HAN = re.compile(r"[一-鿿]")   # 汉字
_TR_CACHE_PATH = Path(__file__).resolve().parent.parent.parent.parent / ".cache" / "coverage-monitor" / "translation-cache.json"
_tr_cache: dict[str, str] = {}


def _load_tr_cache() -> dict[str, dict]:
    global _tr_cache
    if not _tr_cache:
        try:
            if _TR_CACHE_PATH.exists():
                raw = json.loads(_TR_CACHE_PATH.read_text(encoding="utf-8"))
                # 兼容旧格式 {text: str} → {text: {"t": ..., "src": "gtx"}}
                _tr_cache = {k: ({"t": v, "src": "gtx"} if isinstance(v, str) else v)
                             for k, v in raw.items()}
        except Exception:
            _tr_cache = {}
    return _tr_cache


def _save_tr_cache() -> None:
    try:
        _TR_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        _TR_CACHE_PATH.write_text(json.dumps(_tr_cache, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass


# ── 翻译：agent 注入（src=ai 缓存）优先 → Google Translate gtx 机械兜底 ──

def _gtx_translate(text: str, timeout: int = 10) -> str:
    """Google Translate 免费 gtx 接口（机械翻译 fallback）。"""
    try:
        url = ("https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=zh-CN&dt=t"
               f"&q={quote(text)}")
        req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(req, timeout=timeout) as resp:
            data = resp.read(500_000).decode("utf-8", errors="ignore")
        parts = json.loads(data)[0]
        out = "".join(p[0] for p in parts if p and p[0])
        if out and out.strip():
            return out.strip()
    except Exception:
        pass
    return text


def protect_names(entries) -> tuple[str, ...]:
    """从 entries 提取公司名保护名单（native + EN，长名优先）。

    翻译前占位保护、翻译后还原，防止 AI/机械翻译把公司名音译错乱
    （如 Kencoa Aerospace → Kencore）。"""
    names = set()
    for e in entries or []:
        for n in (getattr(e, "company_native", ""), getattr(e, "company", "")):
            n = (n or "").strip()
            if len(n) >= 3:
                names.add(n)
    return tuple(sorted(names, key=len, reverse=True))


def _protect_text(text: str, protect: tuple) -> str:
    for i, n in enumerate(protect):
        if n in text:
            text = text.replace(n, "{{N%d}}" % i)
    return text


def _restore_text(text: str, protect: tuple) -> str:
    for i, n in enumerate(protect):
        text = text.replace("{{N%d}}" % i, n)
    return text


def translate_zh(text: str, timeout: int = 10, protect: tuple = ()) -> str:
    """标题 → 简体中文。agent 翻译（src=ai 缓存）优先 → Google Translate gtx 机械兜底。

    agent 翻译通过 `daily --ai-review-input` 导出任务包 → claude CLI/主 agent 翻译 →
    `daily --ai-review <out>` 写入缓存（src=ai，按原文 key）。
    公司名（protect 名单）翻译前占位保护、翻译后还原，避免音译错乱。
    日文（含假名）/ 韩文（含谚文）/ 英文 → 翻译；已是中文（含汉字且无假名谚文）→ 原样。
    失败降级返回原文（honest degrade）。带磁盘缓存避免重复请求（ai 条目优先于 gtx）。"""
    text = (text or "").strip()
    if not text:
        return text
    if _ZH_HAN.search(text) and not _KANA.search(text) and not _HANGUL.search(text):
        return text  # 已含汉字且无日/韩特征 → 视为中文，不翻
    key = _protect_text(text, protect)
    cache = _load_tr_cache()
    entry = cache.get(key) or cache.get(text)  # 兼容 agent 按原文写入的 AI 翻译
    if entry is not None:
        return _restore_text(entry.get("t", "") if isinstance(entry, dict) else entry, protect)
    t = _gtx_translate(key, timeout)
    cache[key] = {"t": t, "src": "gtx"}
    _save_tr_cache()
    return _restore_text(t, protect)


def pick_lead_news(items: list) -> NewsItem:
    """主新闻 = 第一条带标签的（财报/订单等信号强）；没有则取第一条。"""
    if not items:
        raise ValueError("pick_lead_news called with empty list")
    for it in items:
        if tag_news_title(it.title):
            return it
    return items[0]


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


# ── company news: DDG HTML search per stock ──────────────

def _ddg_company_queries(entry: CoverageEntry) -> list[str]:
    """Build DDG search queries: native language + English."""
    queries = []
    native = (entry.company_native or "").strip()
    en = (entry.company or "").strip()
    ticker = (entry.ticker or "").strip()
    # Native language query
    if native and ticker:
        queries.append(f"{native} {ticker}")
    elif native:
        queries.append(native)
    # English query
    if en and ticker:
        queries.append(f"{en} {ticker} news")
    elif en:
        queries.append(f"{en} news")
    return queries


def build_company_search_queries(entry: CoverageEntry, today: str | None = None) -> list[str]:
    queries = _ddg_company_queries(entry)
    if today:
        enriched: list[str] = []
        for query in queries:
            enriched.append(f"{query} after:{today}")
            enriched.append(f"{query} earnings guidance after:{today}")
        return enriched
    return queries


def collect_company_news(
    entries: list[CoverageEntry],
    snapshots: dict[str, dict],
    today: str | None = None,
    ddg_enabled: bool = True,
) -> tuple[dict[str, list[NewsItem]], list[str], list[str]]:
    """Collect news via DDG HTML search for Core Watch + Mover stocks.
    Returns (news_map, gaps, agent_needed_keys).

    DDG search runs per stock — script does the raw news gathering.
    Agent still needed for Chinese/English summaries via enrichment.
    """
    result: dict[str, list[NewsItem]] = {}
    gaps: list[str] = []
    agent_needed: list[str] = []

    for entry in entries:
        key = entry.ticker or entry.company
        if not key:
            continue

        snapshot = snapshots.get(key, {})
        assessment = assess_snapshot(snapshot) if snapshot else None
        needs_news = entry.monitor_status == "Core" or (assessment and assessment.is_mover)

        if not needs_news:
            continue

        items: list[NewsItem] = []

        # FMP news 首层（美股覆盖；非美股返回空 → DDG fallback）
        try:
            import sys as _sys, os as _os
            _fd = _os.path.join(_os.path.dirname(__file__), "..", "..", "financial-data", "providers")
            if _fd not in _sys.path:
                _sys.path.insert(0, _os.path.abspath(_fd))
            from fmp_provider import fetch as _fmp_fetch
            fr = _fmp_fetch({"identifier": entry.ticker, "items": ["news"], "periods": "latest"})
            for n in fr.get("news", [])[:5]:
                items.append(NewsItem(
                    title=str(n.get("title") or ""), url=str(n.get("url") or n.get("site") or ""),
                    source="fmp", summary=str(n.get("text") or ""),
                    published_at=str(n.get("publishedDate") or ""),
                ))
        except Exception:
            pass  # FMP news unavailable → DDG

        # Google News RSS（FMP 无新闻时主力层：韩/日/台/A 股覆盖好，免费无 key）
        if ddg_enabled and not items:
            try:
                for q in _gn_company_queries(entry):
                    items.extend(_gn_news(q, entry.ticker or ""))
            except Exception as _gn_e:
                gaps.append(f"{key}: gn_failed — {type(_gn_e).__name__}: {_gn_e}")  # honest fail → DDG

        # DDG bilingual search（GN 已有新闻则不搜）
        if ddg_enabled and not items:
            try:
                import sys, os
                _shared = os.path.join(os.path.dirname(__file__), "..", "..", "shared")
                if _shared not in sys.path:
                    sys.path.insert(0, os.path.abspath(_shared))
                from search import ddg_multi_search
                queries = build_company_search_queries(entry, today) or _ddg_company_queries(entry)
                if queries:
                    raw = ddg_multi_search(queries, max_results_per=20, dedup=True)
                    for r in raw:
                        items.append(NewsItem(
                            title=r["title"], url=r["url"],
                            source=r.get("source", "ddg"),
                            summary=r.get("snippet", ""),
                        ))
            except Exception:
                pass  # DDG unavailable → honest gap

        # yfinance news 列表 fallback（比 headline 单条覆盖好）
        if not items and entry.ticker:
            try:
                from .tickers import build_ticker_runtime
                import yfinance as yf
                ytr = build_ticker_runtime(entry.ticker, entry.company)
                if ytr.is_quoteable:
                    yf_items = yf.Ticker(ytr.quote_ticker).news or []
                    for n in yf_items[:6]:
                        t = str(n.get("title") or "")
                        u = str(n.get("link") or "")
                        if t and u:
                            items.append(NewsItem(
                                title=t, url=u, source="yfinance",
                                summary="", published_at=str(n.get("providerPublishTime") or ""),
                            ))
            except Exception:
                pass
        # 单条 headline 最后兜底
        if not items and snapshot.get("headline") and snapshot.get("url"):
            items.append(NewsItem(
                title=str(snapshot["headline"]), url=str(snapshot["url"]),
                source="yfinance", summary="Latest provider headline.",
                published_at=str(snapshot.get("published_at") or ""),
            ))

        items = _dedupe_news(items, max_results=10)
        items = _filter_page_items(items)  # 阶段1：丢弃页面/低信息量（标题黑名单+来源黑名单）
        if items:
            agent_needed.append(key)  # still needs agent to write Chinese summary
        else:
            gaps.append(f"{key}: no_news_found — GN/DDG/yfinance all empty")

        result[key] = items

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
