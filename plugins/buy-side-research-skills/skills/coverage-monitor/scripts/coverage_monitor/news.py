from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from html import unescape
import os
from pathlib import Path
import json
import re
import shutil
import subprocess
from typing import Protocol
from urllib.parse import parse_qs, quote_plus, unquote, urlparse
from urllib.request import Request, urlopen

from .coverage import CoverageEntry
from .signals import assess_snapshot
from .tickers import build_ticker_runtime


OFFICIAL_DOMAINS = (
    "sec.gov",
    "hkexnews.hkex.com.hk",
    "edinet-fsa.go.jp",
    "dart.fss.or.kr",
    "englishdart.fss.or.kr",
    "mops.twse.com.tw",
)


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


class SearchProvider(Protocol):
    def search(self, query: str, max_results: int) -> list[NewsItem]:
        ...


class CodexCliSearchProvider:
    def __init__(self, timeout_seconds: int = 180, model: str = "gpt-5.4", working_dir: Path | None = None):
        self.timeout_seconds = timeout_seconds
        self.model = model
        self.working_dir = working_dir
        self.executable = _resolve_codex_executable()

    def search(self, query: str, max_results: int) -> list[NewsItem]:
        prompt = (
            "Use live web search to find stock or industry news. Return ONLY valid JSON with a top-level "
            "`results` array. Each result must include title, url, source, snippet, and published_at.\n"
            f"Query: {query}\n"
            f"Limit: {max_results}\n"
        )
        command = [
            self.executable,
            "--search",
            "exec",
            "--model",
            self.model,
            "--skip-git-repo-check",
            "--ephemeral",
            "--color",
            "never",
        ]
        if self.working_dir is not None:
            command.extend(["--cd", str(self.working_dir)])
        command.append("-")
        completed = subprocess.run(
            command,
            input=prompt,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=self.timeout_seconds,
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError(completed.stderr.strip() or completed.stdout.strip() or f"exit {completed.returncode}")
        payload = _parse_results_json_from_text(completed.stdout)
        return _search_results_from_payload(payload, query=query, max_results=max_results)


class HtmlSearchProvider:
    def search(self, query: str, max_results: int) -> list[NewsItem]:
        items = _ddg_links(query, max_results=max_results)
        if items:
            return items
        return _bing_links(query, max_results=max_results)


def _resolve_search_provider() -> SearchProvider:
    provider_name = str(os.environ.get("COVERAGE_MONITOR_SEARCH_PROVIDER", "html")).strip().lower()
    if provider_name == "codex_cli":
        try:
            return CodexCliSearchProvider()
        except Exception:
            return HtmlSearchProvider()
    return HtmlSearchProvider()


def _fetch_text(url: str, timeout: int = 8) -> str:
    request = Request(url, headers={"User-Agent": "Mozilla/5.0 coverage-monitor"})
    with urlopen(request, timeout=timeout) as response:  # nosec - user-controlled research sources
        data = response.read(600_000)
    return data.decode("utf-8", errors="ignore")


def _fetch_text_playwright(url: str, timeout: int = 8000) -> str:
    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("playwright_unavailable") from exc
    with sync_playwright() as playwright:  # pragma: no cover - optional dependency
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="networkidle", timeout=timeout)
        content = page.content()
        browser.close()
    return content


def _fetch_text_with_fallbacks(url: str, timeout: int = 8) -> str:
    try:
        return _fetch_text(url, timeout=timeout)
    except Exception:
        return _fetch_text_playwright(url, timeout=max(timeout * 1000, 8000))


def _html_title(html_text: str) -> str:
    match = re.search(r"<title[^>]*>(.*?)</title>", html_text, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return ""
    title = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", match.group(1))).strip()
    return unescape(title)


def _meta_description(html_text: str) -> str:
    match = re.search(
        r'<meta[^>]+(?:name|property)=["\'](?:description|og:description)["\'][^>]+content=["\'](.*?)["\']',
        html_text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if not match:
        return ""
    description = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", match.group(1))).strip()
    return unescape(description)


def _enrich_result(item: NewsItem) -> NewsItem:
    if not item.url or item.source == "search_link":
        return item
    try:
        html_text = _fetch_text_with_fallbacks(item.url)
    except Exception:
        return item
    title = _html_title(html_text) or item.title
    summary = item.summary or _meta_description(html_text)
    return NewsItem(
        title=title,
        url=item.url,
        source=item.source,
        summary=summary,
        tier=item.tier,
        published_at=item.published_at,
        query=item.query,
    )


def _normalize_result_url(raw_url: str) -> str:
    if raw_url.startswith("//"):
        raw_url = f"https:{raw_url}"
    elif raw_url.startswith("/"):
        raw_url = f"https://duckduckgo.com{raw_url}"
    parsed = urlparse(raw_url)
    if "duckduckgo.com" in parsed.netloc and parsed.path.startswith("/l/"):
        target = parse_qs(parsed.query).get("uddg", [""])[0]
        if target:
            return unquote(target)
    return raw_url


def _ddg_links(query: str, max_results: int = 5) -> list[NewsItem]:
    url = f"https://duckduckgo.com/html/?q={quote_plus(query)}"
    try:
        html_text = _fetch_text(url)
    except Exception:
        return []
    items: list[NewsItem] = []
    for match in re.finditer(r'class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', html_text, flags=re.IGNORECASE | re.DOTALL):
        href = _normalize_result_url(unescape(match.group(1)))
        title = unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", match.group(2))).strip())
        if title and href:
            items.append(NewsItem(title=title, url=href, source=urlparse(href).netloc, query=query))
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
        import base64

        padding = "=" * (-len(payload) % 4)
        return base64.urlsafe_b64decode((payload + padding).encode("ascii")).decode("utf-8", errors="ignore")
    except Exception:
        return href


def _bing_links(query: str, max_results: int = 5) -> list[NewsItem]:
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
            items.append(NewsItem(title=title, url=href, source=urlparse(href).netloc, query=query))
        if len(items) >= max_results:
            break
    return items


def _parse_results_json_from_text(text: str) -> dict:
    stripped = text.strip()
    decoder = json.JSONDecoder()
    try:
        parsed = json.loads(stripped)
        if isinstance(parsed, dict) and isinstance(parsed.get("results"), list):
            return parsed
    except json.JSONDecodeError:
        pass
    for index, char in enumerate(stripped):
        if char != "{":
            continue
        try:
            parsed, _ = decoder.raw_decode(stripped[index:])
            if isinstance(parsed, dict) and isinstance(parsed.get("results"), list):
                return parsed
        except json.JSONDecodeError:
            continue
    raise RuntimeError(f"invalid_search_json:{stripped[:300]}")


def _search_results_from_payload(payload: dict, query: str, max_results: int) -> list[NewsItem]:
    items: list[NewsItem] = []
    for row in payload.get("results", []):
        if not isinstance(row, dict):
            continue
        url = str(row.get("url", "")).strip()
        title = str(row.get("title", "")).strip()
        if not url or not title:
            continue
        source = str(row.get("source", "")).strip() or urlparse(url).netloc or "web"
        snippet = str(row.get("snippet", "")).strip()
        published = str(row.get("published_at", "") or "").strip()
        items.append(NewsItem(title=title, url=url, source=source, summary=snippet, published_at=published, query=query))
        if len(items) >= max_results:
            break
    return items


def _resolve_codex_executable() -> str:
    for name in ("codex.exe", "codex.cmd", "codex"):
        path = shutil.which(name)
        if path:
            return path
    raise RuntimeError("codex_cli_unavailable")


def _dedupe_news(items: list[NewsItem], max_results: int | None = None) -> list[NewsItem]:
    seen_urls: set[str] = set()
    deduped: list[NewsItem] = []
    for item in items:
        if not item.url or item.source == "search_link" or item.url in seen_urls:
            continue
        seen_urls.add(item.url)
        deduped.append(item)
        if max_results is not None and len(deduped) >= max_results:
            break
    return deduped


def _token_set(entry: CoverageEntry) -> set[str]:
    runtime = build_ticker_runtime(entry.ticker, entry.company)
    raw_tokens = [entry.company, *(runtime.search_aliases or ())]
    tokens: set[str] = set()
    for raw in raw_tokens:
        for token in re.findall(r"[a-z0-9]+", raw.lower()):
            if len(token) >= 3 and token not in {"news", "stock", "latest", "results", "company"}:
                tokens.add(token)
    return tokens


def _relevant_news_items(items: list[NewsItem], entry: CoverageEntry) -> list[NewsItem]:
    tokens = _token_set(entry)
    filtered = []
    for item in items:
        haystack = f"{item.title} {item.summary} {item.url}".lower()
        if any(token in haystack for token in tokens):
            filtered.append(item)
    return filtered or items


def _is_official_like_item(item: NewsItem) -> bool:
    parsed = urlparse(item.url)
    domain = parsed.netloc.lower()
    title = f"{item.title} {item.summary}".lower()
    if any(source in domain for source in OFFICIAL_DOMAINS):
        return True
    if any(token in domain for token in ("investor", "ir.", "newsroom", "press", "relations")):
        return True
    if any(token in title for token in ("results", "press release", "investor", "filing", "8-k", "annual report", "quarterly report")):
        return True
    return False


def _source_host(url: str) -> str:
    return urlparse(url).netloc.lower()


def build_company_search_queries(entry: CoverageEntry, today: str) -> list[str]:
    runtime = build_ticker_runtime(entry.ticker, entry.company)
    alias_text = " ".join(runtime.search_aliases[:2] or (entry.company,))
    queries = [
        f"{entry.ticker} {runtime.quote_ticker} {entry.company} stock news after:{today}",
        f"{alias_text} earnings guidance order backlog contract results",
    ]
    return list(dict.fromkeys(query.strip() for query in queries if query.strip()))


def _build_official_search_queries(entry: CoverageEntry, today: str) -> list[str]:
    runtime = build_ticker_runtime(entry.ticker, entry.company)
    alias_text = " ".join(runtime.search_aliases[:2] or (entry.company,))
    queries = [
        f"{alias_text} investor relations results after:{today}",
        f"{alias_text} press release filing annual report quarterly report after:{today}",
    ]
    return list(dict.fromkeys(query.strip() for query in queries if query.strip()))


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


def _search_all(provider: SearchProvider, queries: list[str], max_results: int) -> list[NewsItem]:
    items: list[NewsItem] = []
    for query in queries:
        try:
            items.extend(provider.search(query, max_results=max_results))
        except Exception:
            continue
    return items


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


def collect_company_news(
    entries: list[CoverageEntry],
    snapshots: dict[str, dict],
    today: str | None = None,
    provider: SearchProvider | None = None,
) -> tuple[dict[str, list[NewsItem]], dict[str, ImportantMoverExplainer], list[str]]:
    provider = provider or _resolve_search_provider()
    result: dict[str, list[NewsItem]] = {}
    explainers: dict[str, ImportantMoverExplainer] = {}
    gaps: list[str] = []
    for entry in entries:
        key = entry.ticker or entry.company
        if not key:
            continue
        snapshot = snapshots.get(key, {})
        assessment = assess_snapshot(snapshot)
        if entry.monitor_status != "Core Watch" and not (assessment and assessment.is_important):
            continue
        snapshot_items: list[NewsItem] = []
        if snapshot.get("headline") and snapshot.get("url"):
            snapshot_items.append(
                NewsItem(
                    title=str(snapshot["headline"]),
                    url=str(snapshot["url"]),
                    source="yfinance",
                    summary="Latest provider headline.",
                    published_at=str(snapshot.get("published_at") or ""),
                )
            )
        day_label = today or datetime.now().date().isoformat()
        general_items = _search_all(provider, build_company_search_queries(entry, day_label), max_results=5)
        general_items = _relevant_news_items(general_items, entry)
        official_items: list[NewsItem] = []
        if assessment and assessment.is_important:
            official_items = _search_all(provider, _build_official_search_queries(entry, day_label), max_results=4)
            official_items = [
                _enrich_result(item)
                for item in _relevant_news_items(official_items, entry)
                if _is_official_like_item(item)
            ]
        merged_items = _dedupe_news([*snapshot_items, *general_items, *official_items], max_results=6)
        if not merged_items:
            gaps.append(f"{key}: no_company_news_found")
        result[key] = merged_items
        if len(merged_items) <= 1:
            gaps.append(f"{key}: weak_search_results")
        if assessment and assessment.is_important:
            official_deduped = _dedupe_news(official_items, max_results=3)
            if not official_deduped:
                gaps.append(f"{key}: filing_unavailable")
            if merged_items or official_deduped:
                explainers[key] = build_important_mover_explainer(entry, snapshot, merged_items, official_deduped)
    return result, explainers, sorted(set(gaps))


def _source_search_queries(industry: str, source: dict[str, str], today: str) -> list[str]:
    url = source.get("URL", "")
    host = _source_host(url)
    source_name = source.get("来源", "") or host
    queries = [
        f"{industry} {source_name} after:{today}",
        f"site:{host} {industry} latest",
    ]
    return [query for query in dict.fromkeys(queries) if query.strip()]


def collect_industry_readthroughs(
    workspace: Path,
    today: str | None = None,
    provider: SearchProvider | None = None,
) -> tuple[dict[str, list[NewsItem]], list[str]]:
    provider = provider or _resolve_search_provider()
    industry_root = workspace / "industry"
    result: dict[str, list[NewsItem]] = {}
    gaps: list[str] = []
    if not industry_root.exists():
        return result, ["industry_dir_missing"]
    day_label = today or datetime.now().date().isoformat()
    for research_md in sorted(industry_root.glob("*/RESEARCH.md")):
        industry = research_md.parent.name
        sources = parse_daily_signal_sources(research_md)
        items: list[NewsItem] = []
        for source in sources:
            url = source.get("URL", "")
            if not url or url == "varies by company":
                continue
            host = _source_host(url)
            try:
                html_text = _fetch_text_with_fallbacks(url)
                title = _html_title(html_text)
            except Exception as exc:
                gaps.append(f"{industry}: source_fetch_failed:{source.get('来源') or url} ({exc.__class__.__name__})")
                continue
            if title:
                items.append(
                    NewsItem(
                        title=title,
                        url=url,
                        source=source.get("来源", "") or host,
                        summary=_meta_description(html_text) or source.get("Use For", ""),
                        tier=source.get("Tier", ""),
                    )
                )
        if not items:
            fallback_items = _search_all(provider, [f"{industry} industry news latest after:{day_label}"], max_results=5)
            items.extend(_dedupe_news(fallback_items, max_results=5))
            if not items:
                gaps.append(f"{industry}: no_industry_readthrough_found")
        result[industry] = _dedupe_news(items, max_results=12)
    return result, sorted(set(gaps))
