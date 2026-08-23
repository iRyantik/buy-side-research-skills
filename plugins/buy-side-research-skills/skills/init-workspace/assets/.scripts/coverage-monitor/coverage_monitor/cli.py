from __future__ import annotations

import argparse
from dataclasses import replace
import json
from datetime import datetime
import os
from pathlib import Path
import re
import time
from typing import Sequence

from .coverage import (
    CoverageEntry,
    CoverageUniverse,
    discover_company_directories,
    extract_date_prefix,
    list_markdown_artifacts,
    normalize_company_token,
    parse_coverage_markdown,
    render_coverage_markdown,
)
from .delivery import send_email, workspace_env
from .market_data import collect_snapshots
from .news import ImportantMoverExplainer, NewsItem, collect_company_news, collect_industry_readthroughs
from .reports import render_alert_markdown, render_daily_markdown, render_dashboard_html, render_email_body, render_email_body_html, should_alert_intraday
from .state import build_event_id, load_state, save_state
from .tiering import derive_coverage_status, derive_monitor_status, should_trigger_core_review


QUICKREAD_ARTIFACT_TOKENS = ("stock-quickread",)
DEEPWORK_ARTIFACT_TOKENS = (
    "alpha-thesis",
    "peer-deep-dive",
    "earnings-setup",
    "scenario-model",
    "driver-map",
    "catalyst-map",
    "moat-analysis",
    "consensus-map",
    "dcf-model",
    "3-statement-model",
    "bear-pre-mortem",
    "capital-allocation",
    "company-history",
    "pair-trade",
)


def _workspace_root(path: str | Path | None) -> Path:
    workspace = Path(path or ".").resolve()
    return workspace


def _relative_posix(path: Path, workspace: Path) -> str:
    try:
        return path.relative_to(workspace).as_posix()
    except ValueError:
        return path.as_posix()


def _artifact_inventory(company_dir: Path) -> tuple[int, str, str, int, int, bool]:
    artifacts = [artifact for artifact in list_markdown_artifacts(company_dir) if artifact.name.lower() != "index.md"]
    if not artifacts:
        return 0, "", "", 0, 0, (company_dir / "RESEARCH.md").exists()
    dated = [artifact for artifact in artifacts if extract_date_prefix(artifact.name)]
    latest = sorted(dated or artifacts, key=lambda item: item.name)[-1]
    names = [artifact.name.lower() for artifact in artifacts]
    quickread_count = sum(any(token in name for token in QUICKREAD_ARTIFACT_TOKENS) for name in names)
    deepwork_count = sum(any(token in name for token in DEEPWORK_ARTIFACT_TOKENS) for name in names)
    return (
        len(artifacts),
        latest.name,
        extract_date_prefix(latest.name),
        quickread_count,
        deepwork_count,
        (company_dir / "RESEARCH.md").exists(),
    )


def build_universe(workspace: Path, today: str | None = None) -> CoverageUniverse:
    coverage_path = workspace / "COVERAGE.md"
    gaps: list[str] = []
    rows: list[CoverageEntry] = []
    if coverage_path.exists():
        rows = parse_coverage_markdown(coverage_path.read_text(encoding="utf-8"))
    else:
        gaps.append("COVERAGE.md missing")

    merged: dict[str, CoverageEntry] = {}

    has_coverage_rows = bool(rows)

    def row_key(entry: CoverageEntry) -> str:
        company_token = normalize_company_token(entry.company)
        industry_token = normalize_company_token(entry.industry)
        if company_token:
            return f"{industry_token}:{company_token}"
        if entry.source_path.strip():
            return entry.source_path.strip().lower()
        return entry.ticker.strip().upper()

    def upsert(entry: CoverageEntry) -> None:
        key = row_key(entry)
        if not key:
            return
        if key not in merged:
            merged[key] = replace(entry)
            return
        current = merged[key]
        for field in (
            "ticker",
            "company",
            "industry",
            "coverage_status",
            "monitor_status",
            "last_review",
            "next_trigger",
            "notes",
            "source_path",
            "latest_artifact",
        ):
            value = getattr(entry, field)
            if value and not getattr(current, field):
                setattr(current, field, value)
        current.artifact_count = max(current.artifact_count, entry.artifact_count)

    for row in rows:
        upsert(row)

    for company_dir in discover_company_directories(workspace):
        (
            artifact_count,
            latest_artifact,
            artifact_date,
            quickread_count,
            deepwork_count,
            has_research_memory,
        ) = _artifact_inventory(company_dir)
        relative_path = _relative_posix(company_dir, workspace)
        industry = company_dir.parents[1].name if len(company_dir.parents) >= 2 else ""
        slug = company_dir.name
        matched_key = ""
        for key, entry in merged.items():
            if entry.source_path and entry.source_path == relative_path:
                matched_key = key
                break
            normalized_slug = normalize_company_token(slug)
            normalized_company = normalize_company_token(entry.company)
            company_parts = {part for part in re.split(r"[^a-z0-9]+", normalized_company) if part}
            if normalized_company == normalized_slug or normalized_slug in company_parts or normalized_company.endswith(f"-{normalized_slug}"):
                matched_key = key
                break
        if matched_key:
            entry = merged[matched_key]
            entry.source_path = relative_path
            entry.industry = entry.industry or industry
            entry.latest_artifact = latest_artifact or entry.latest_artifact
            entry.artifact_count = max(entry.artifact_count, artifact_count)
            entry.quickread_artifact_count = max(entry.quickread_artifact_count, quickread_count)
            entry.deepwork_artifact_count = max(entry.deepwork_artifact_count, deepwork_count)
            entry.has_research_memory = entry.has_research_memory or has_research_memory
            if artifact_date and not entry.last_review:
                entry.last_review = artifact_date
            continue
        if has_coverage_rows:
            gaps.append(f"unregistered_company_dir:{relative_path}")
            continue
        upsert(
            CoverageEntry(
                ticker="",
                company=slug,
                industry=industry,
                source_path=relative_path,
                latest_artifact=latest_artifact,
                last_review=artifact_date,
                artifact_count=artifact_count,
                quickread_artifact_count=quickread_count,
                deepwork_artifact_count=deepwork_count,
                has_research_memory=has_research_memory,
            )
        )

    entries = list(merged.values())
    for entry in entries:
        entry.coverage_status = entry.coverage_status or derive_coverage_status(
            entry, today=today, artifact_count=entry.artifact_count
        )
        entry.monitor_status = entry.monitor_status or derive_monitor_status(entry)
        if not entry.last_review and entry.latest_artifact:
            entry.last_review = extract_date_prefix(entry.latest_artifact)
        if entry.coverage_status != "Core" and should_trigger_core_review(entry, today=today):
            gaps.append(f"core_review_due:{entry.ticker or entry.company}")
    coverage_rank = {"Core": 0, "Building": 1, "Radar": 2}
    monitor_rank = {"Core": 0, "Daily": 1}
    entries.sort(
        key=lambda item: (
            item.industry.lower(),
            coverage_rank.get(item.coverage_status, 9),
            monitor_rank.get(item.monitor_status, 9),
            item.company.lower(),
        )
    )
    return CoverageUniverse(entries=entries, gaps=gaps)


def _doctor(workspace: Path) -> int:
    universe = build_universe(workspace)
    print(f"workspace={workspace}")
    print(f"entries={len(universe.entries)}")
    if universe.gaps:
        print("gaps=" + "; ".join(universe.gaps))
    # Check enrichment JSON presence
    import glob as _glob
    enrichment_files = sorted(_glob.glob(str(workspace / ".cache" / "coverage-monitor" / "enrichment-*.json")))
    print(f"enrichment_files={len(enrichment_files)}")
    if enrichment_files:
        latest = enrichment_files[-1]
        import json
        try:
            raw = json.loads(Path(latest).read_text(encoding="utf-8"))
            keys = [k for k in ("mover_explainers", "core_watch_news", "industry_summaries") if raw.get(k)]
            print(f"latest_enrichment={latest} sections={','.join(keys)}")
        except Exception:
            print(f"latest_enrichment={latest} (parse error)")
    # Check daily state cache
    state_path = _daily_state_path(workspace)
    print(f"daily_state={'present' if state_path.exists() else 'missing'}")
    # Delivery env
    environment = workspace_env(workspace)
    missing_env = [name for name in ("SMTP_HOST", "SMTP_USER", "SMTP_PASSWORD", "COVERAGE_EMAIL_TO") if not environment.get(name)]
    if missing_env:
        print("delivery_gaps=" + ", ".join(missing_env))
    return 0


def _normalize_coverage(workspace: Path, today: str | None, dry_run: bool) -> int:
    universe = build_universe(workspace, today=today)
    output = render_coverage_markdown(universe.entries)
    if dry_run:
        print(output)
        return 0
    (workspace / "COVERAGE.md").write_text(output, encoding="utf-8")
    print(f"wrote={workspace / 'COVERAGE.md'}")
    return 0


def _write_report_files(workspace: Path, stem: str, markdown_text: str, html_text: str) -> tuple[Path, Path]:
    # 日报归 daily/：html 留根目录（用户只看 html），md 收进 daily/md/ 子目录保持根目录干净
    report_dir = workspace / "daily"
    md_dir = report_dir / "md"
    report_dir.mkdir(parents=True, exist_ok=True)
    md_dir.mkdir(parents=True, exist_ok=True)
    markdown_path = md_dir / f"{stem}.md"
    html_path = report_dir / f"{stem}.html"
    markdown_path.write_text(markdown_text, encoding="utf-8")
    html_path.write_text(html_text, encoding="utf-8")
    return markdown_path, html_path


def _load_enrichment_json(path: Path) -> dict:
    """Load agent enrichment JSON. Supports unified format:
    {"mover_explainers": {ticker: {summary, confidence, evidence, filings_evidence}},
     "core_watch_news": {ticker: [{title, url, summary, source}]},
     "industry_summaries": {industry: "一句话总结"}}
    Also backward-compat with old explainers-only flat format.
    """
    import json
    if not path.exists():
        return {}
    raw = json.loads(path.read_text(encoding="utf-8"))

    # Unified format
    if "mover_explainers" in raw or "core_watch_news" in raw or "industry_summaries" in raw or "core_watch_summaries" in raw:
        result: dict = {}
        # Parse mover explainers
        explainers: dict[str, ImportantMoverExplainer] = {}
        for key, obj in raw.get("mover_explainers", {}).items():
            evidence = [NewsItem(**item) for item in obj.get("evidence", [])]
            filings = [NewsItem(**item) for item in obj.get("filings_evidence", [])]
            explainers[key] = ImportantMoverExplainer(
                summary=obj.get("summary", ""),
                confidence=obj.get("confidence", "Low"),
                evidence=evidence,
                filings_evidence=filings,
            )
        result["mover_explainers"] = explainers
        # Parse core watch news
        core_news: dict[str, list[NewsItem]] = {}
        for key, items in raw.get("core_watch_news", {}).items():
            core_news[key] = [NewsItem(**item) for item in items]
        result["core_watch_news"] = core_news
        # Parse industry summaries
        result["industry_summaries"] = raw.get("industry_summaries", {})
        # Parse core watch stock summaries
        result["core_watch_summaries"] = raw.get("core_watch_summaries", {})
        # Parse industry web searches
        search_results: dict[str, list[NewsItem]] = {}
        for key, items in raw.get("industry_searches", {}).items():
            search_results[key] = [NewsItem(**item) for item in items]
        result["industry_searches"] = search_results
        return result

    # Backward-compat: flat explainers-only format
    explainers: dict[str, ImportantMoverExplainer] = {}
    for key, obj in raw.items():
        evidence = [NewsItem(**item) for item in obj.get("evidence", [])]
        filings = [NewsItem(**item) for item in obj.get("filings_evidence", [])]
        explainers[key] = ImportantMoverExplainer(
            summary=obj.get("summary", ""),
            confidence=obj.get("confidence", "Low"),
            evidence=evidence,
            filings_evidence=filings,
        )
    return {"mover_explainers": explainers}


def _daily_state_path(workspace: Path) -> Path:
    return workspace / ".cache" / "coverage-monitor" / "daily-state.json"


def _save_daily_state(
    workspace: Path,
    entries: list[CoverageEntry],
    snapshots: dict[str, dict],
    company_news: dict[str, list[NewsItem]],
    industry_readthroughs: dict[str, list[NewsItem]],
    gaps: list[str],
    run_day: str,
) -> None:
    import json
    from dataclasses import asdict

    state_path = _daily_state_path(workspace)
    state_path.parent.mkdir(parents=True, exist_ok=True)

    def _serialize_news_items(news_dict: dict[str, list[NewsItem]]) -> dict[str, list[dict]]:
        return {k: [asdict(item) for item in v] for k, v in news_dict.items()}

    state_path.write_text(
        json.dumps(
            {
                "run_day": run_day,
                "entries": [asdict(e) for e in entries],
                "snapshots": snapshots,
                "company_news": _serialize_news_items(company_news),
                "industry_readthroughs": _serialize_news_items(industry_readthroughs),
                "gaps": gaps,
            },
            ensure_ascii=False,
            default=str,
        ),
        encoding="utf-8",
    )


def _load_daily_state(workspace: Path) -> dict | None:
    import json

    state_path = _daily_state_path(workspace)
    if not state_path.exists():
        return None
    raw = json.loads(state_path.read_text(encoding="utf-8"))
    # Rebuild CoverageEntry objects
    entries = [CoverageEntry(**e) for e in raw.get("entries", [])]
    # Rebuild NewsItem objects
    def _deserialize_news_items(raw_news: dict) -> dict[str, list[NewsItem]]:
        return {k: [NewsItem(**item) for item in v] for k, v in raw_news.items()}

    return {
        "run_day": raw["run_day"],
        "entries": entries,
        "snapshots": raw["snapshots"],
        "company_news": _deserialize_news_items(raw.get("company_news", {})),
        "industry_readthroughs": _deserialize_news_items(raw.get("industry_readthroughs", {})),
        "gaps": raw.get("gaps", []),
    }
def _apply_ai_review(workspace: Path, path: str, review_map: dict, entries: list) -> None:
    """注入 agent AI 审查输出：translations → 翻译缓存（src=ai，按原文 key）；review_map → AI 优先覆盖。"""
    try:
        out = json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[ai_review] 读取失败 {path}: {e} → 跳过", file=sys.stderr)
        return
    tr = out.get("translations") or {}
    if tr:
        cache_path = workspace / ".cache" / "coverage-monitor" / "translation-cache.json"
        cache: dict = {}
        try:
            if cache_path.exists():
                cache = json.loads(cache_path.read_text(encoding="utf-8"))
        except Exception:
            cache = {}
        n = 0
        for orig, zh in tr.items():
            orig = (orig or "").strip()
            zh = (zh or "").strip()
            if orig and zh:
                cache[orig] = {"t": zh, "src": "ai"}
                n += 1
        try:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
            print(f"[ai_review] 翻译缓存写入 {n} 条（src=ai）")
        except Exception as e:
            print(f"[ai_review] 翻译缓存写入失败: {e}", file=sys.stderr)
    ai_rm = out.get("review_map") or {}
    if isinstance(ai_rm, dict):
        for k, v in ai_rm.items():
            if isinstance(v, dict):
                review_map[k] = v
        print(f"[ai_review] review_map 覆盖 {len(ai_rm)} 家（AI 优先）")


def _write_ai_review_input(workspace: Path, mover_entries: list, company_news: dict,
                           review_map: dict, run_day: str, entries: list | None = None) -> None:
    """导出 AI 审查任务包：movers（新闻候选 + 当前 review）+ 全部待翻译标题（movers + Core Watch）。"""
    pack: dict = {"today": run_day, "movers": []}
    seen_titles: set = set()
    titles: list = []
    for ticker, company, snap in mover_entries:
        items = company_news.get(ticker, []) or []
        news = []
        for it in items[:12]:
            t = (it.title or "").strip()
            if t and t not in seen_titles:
                seen_titles.add(t)
                titles.append(t)
            news.append({"title": t, "url": it.url, "source": getattr(it, "source", ""),
                         "snippet": (getattr(it, "summary", "") or "")[:160]})
        pack["movers"].append({
            "ticker": ticker, "company": company,
            "price_move_pct": (snap or {}).get("price_move_pct"),
            "market_cap": (snap or {}).get("market_cap"),
            "current_summary": (review_map.get(ticker) or {}).get("summary", ""),
            "news": news,
        })
    # Core Watch 新闻标题也纳入翻译（展示给用户）
    for e in entries or []:
        if getattr(e, "monitor_status", "") == "Core":
            for it in (company_news.get(e.ticker or e.company, []) or [])[:6]:
                t = (it.title or "").strip()
                if t and t not in seen_titles:
                    seen_titles.add(t)
                    titles.append(t)
    pack["titles_to_translate"] = titles
    out_path = workspace / ".cache" / "coverage-monitor" / "ai-review-input.json"
    try:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(pack, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"[ai_review] 任务包已导出: {out_path}（{len(pack['movers'])} 家 movers，{len(titles)} 条待翻译标题）")
    except Exception as e:
        print(f"[ai_review] 任务包导出失败: {e}", file=sys.stderr)


def _clean_gaps_for_enrichment(gaps: list[str], enrichment: dict, entries: list[CoverageEntry], snapshots: dict) -> list[str]:
    """Remove gaps that enrichment has resolved, add agent work summary."""
    core_news = set(enrichment.get("core_watch_news", {}).keys())
    mover_exps = set(enrichment.get("mover_explainers", {}).keys())
    industry_sums = set(enrichment.get("industry_summaries", {}).keys())
    all_covered = core_news | mover_exps

    cleaned: list[str] = []
    for gap in gaps:
        # Skip resolved yfinance headline gaps
        if gap.endswith(": no_yfinance_headline — agent should search via WebSearch"):
            ticker = gap.split(":")[0].strip()
            if ticker in core_news:
                continue
        # Skip resolved agent_news_search_needed entries
        if gap.startswith("agent_news_search_needed:"):
            needed = {t.strip() for t in gap.split(":", 1)[1].split(",")}
            still_needed = needed - all_covered
            if still_needed:
                cleaned.append(f"agent_news_search_needed: {', '.join(sorted(still_needed))}")
            continue
        cleaned.append(gap)

    # Summarize what agent did / still needs to do
    core_watch = [e for e in entries if e.monitor_status == "Core"]
    unresolved_news = {e.ticker or e.company for e in core_watch} - core_news

    # Movers that triggered but don't have an explainer yet
    from .signals import assess_snapshot  # local import, already imported at top
    mover_tickers = set()
    for entry in entries:
        snapshot = snapshots.get(entry.ticker or entry.company, {})
        if assess_snapshot(snapshot):
            mover_tickers.add(entry.ticker or entry.company)
    unresolved_explainers = mover_tickers - mover_exps

    # Count industries needing domain search
    domain_search_industries = [g for g in cleaned if "ALL_P1_NEEDS_AGENT" in g]
    parts = []
    if core_news:
        parts.append(f"core_watch_news={len(core_news)}")
    if mover_exps:
        parts.append(f"mover_explainers={len(mover_exps)}")
    if industry_sums:
        parts.append(f"industry_summaries={len(industry_sums)}")
    if unresolved_news:
        parts.append(f"pending_core_news={len(unresolved_news)}")
    if unresolved_explainers:
        parts.append(f"pending_explainers={len(unresolved_explainers)}")
    if domain_search_industries:
        parts.append(f"pending_domain_search={len(domain_search_industries)}")
    cleaned.append(f"agent_work: {', '.join(parts) if parts else 'none'}")

    return cleaned


def _run_daily(workspace: Path, today: str | None, dry_run: bool, enrichment_path: Path | None = None, skip_fetch: bool = False, report_type: str = "us", ai_review: str = "", ai_review_input: bool = False, force_weekend: bool = False) -> int:
    from concurrent.futures import ThreadPoolExecutor

    # 周末跳过：launchd 的 Weekday 数组在 macOS 上不可靠（实测周六仍触发），脚本层兜底。
    # 周六/周日不生成日报（市场休市，数据不新鲜）；--weekend 可强制（手动补跑）。
    if not force_weekend:
        from datetime import date as _date
        _c = _date.fromisoformat(today) if today else _date.today()
        if _c.weekday() >= 6:
            print(f"[coverage-monitor] {_c} 是周日，跳过日报（交易日才发）")
            return 0

    if skip_fetch:
        cached = _load_daily_state(workspace)
        if cached is None:
            print("error: --skip-fetch used but no cached daily state found")
            return 2
        run_day = cached["run_day"]
        entries = cached["entries"]
        snapshots = cached["snapshots"]
        company_news = cached["company_news"]
        industry_readthroughs = cached["industry_readthroughs"]
        gaps = cached["gaps"]
    else:
        run_day = today or datetime.now().date().isoformat()
        universe = build_universe(workspace, today=run_day)
        entries = universe.entries

        # snapshots and industry_readthroughs are fully independent — run them in parallel
        with ThreadPoolExecutor(max_workers=2) as pool:
            fut_snapshots = pool.submit(collect_snapshots, entries, today=run_day)
            fut_industry = pool.submit(collect_industry_readthroughs, workspace, today=run_day)
            snapshots, snapshot_gaps = fut_snapshots.result()
            industry_readthroughs, _source_results, industry_gaps = fut_industry.result()

        company_news, company_news_gaps, agent_needed = collect_company_news(entries, snapshots, today=run_day)
        gaps = sorted(set(universe.gaps + snapshot_gaps + company_news_gaps + industry_gaps))
        if agent_needed:
            gaps.append(f"agent_news_search_needed: {', '.join(agent_needed)}")
        _save_daily_state(workspace, entries, snapshots, company_news, industry_readthroughs, gaps, run_day)

    enrichment = _load_enrichment_json(enrichment_path) if enrichment_path else {}
    mover_explainers = enrichment.get("mover_explainers", {})
    industry_summaries = enrichment.get("industry_summaries", {})
    industry_searches = enrichment.get("industry_searches", {})
    core_watch_summaries = enrichment.get("core_watch_summaries", {})
    merged_company_news = dict(company_news)
    # Enrichment adds to script results, doesn't replace
    for key, items in enrichment.get("core_watch_news", {}).items():
        if key not in merged_company_news or not merged_company_news[key]:
            merged_company_news[key] = items
        else:
            # Script (DDG) has results — enrichment appends
            existing_urls = {item.url for item in merged_company_news[key] if item.url}
            for item in items:
                if item.url not in existing_urls:
                    merged_company_news[key].append(item)
    # Clean gaps based on enrichment coverage
    gaps = _clean_gaps_for_enrichment(gaps, enrichment, entries, snapshots)

    # estimates 覆盖健康（integration plan §6）：缺 estimate = 无 forward 且无 consensus
    try:
        _est_path = workspace / ".cache" / "estimates" / "estimates-resolved.json"
        if _est_path.exists():
            _ed = json.loads(_est_path.read_text(encoding="utf-8"))
            _n_missing = 0
            for _e in entries:
                _en = _ed.get(_e.ticker or _e.company) or {}
                _has = bool(_en.get("forward")) or bool((_en.get("consensus") or {}).get("periods"))
                if not _has:
                    _n_missing += 1
            if _n_missing:
                gaps.insert(0, f"estimates_missing: {_n_missing} 家缺 estimate（无 forward 且无 consensus）")
    except Exception:
        pass

    from .brief import render_brief_markdown
    from .brief_html import render_brief_html
    from .mover_review import review_movers

    # Movers Agent review：重要/普通异动股，Agent 读 news 筛噪音 + 总结原因 + 挑高相关链接
    from .signals import assess_snapshot as _assess
    mover_entries = [(e.ticker or e.company, e.company, snapshots.get(e.ticker or e.company, {}))
                     for e in entries if _assess(snapshots.get(e.ticker or e.company, {}))]
    review_map = review_movers(mover_entries, merged_company_news, run_day, entries)

    # ── Agent AI 审查/翻译注入：--ai-review <file> 优先覆盖，--ai-review-input 导出任务包 ──
    if ai_review:
        _apply_ai_review(workspace, ai_review, review_map, entries)
    if ai_review_input:
        _write_ai_review_input(workspace, mover_entries, merged_company_news, review_map, run_day, entries)

    # estimates-resolved.json（L1 forward / L2 consensus）→ 估值列 L1 优先
    _estimates: dict = {}
    try:
        _ep = workspace / ".cache" / "estimates" / "estimates-resolved.json"
        if _ep.exists():
            _estimates = json.loads(_ep.read_text(encoding="utf-8"))
    except Exception:
        _estimates = {}

    markdown_text = render_brief_markdown(
        entries, snapshots, run_day, gaps, merged_company_news, report_type=report_type, review_map=review_map,
        estimates=_estimates,
    )
    html_text = render_brief_html(
        entries, snapshots, run_day, gaps, merged_company_news, report_type=report_type, review_map=review_map,
        estimates=_estimates,
    )
    if dry_run:
        print(markdown_text)
        return 0
    stem = f"{run_day.replace('-', '')}-brief-{report_type}"
    markdown_path, html_path = _write_report_files(workspace, stem, markdown_text, html_text)
    delivery_gaps = []
    _mkt = {"us": "US Post-Market", "asia": "Asia Close", "eu": "Europe Close"}.get(report_type, report_type)
    email_body = render_email_body(
        entries, snapshots, run_day,
        mover_explainers, core_watch_summaries, industry_summaries, gaps,
        review_map=review_map, news_map=merged_company_news,
    )
    email_body_html = render_email_body_html(
        entries, snapshots, run_day,
        mover_explainers, core_watch_summaries, industry_summaries, gaps,
        review_map=review_map, news_map=merged_company_news,
    )
    delivery_gaps.extend(
        send_email(
            f"Daily Coverage Brief — {_mkt} ({run_day})",
            email_body, email_body_html,
            env=workspace_env(workspace),
            attachments=[html_path],
        )
    )
    state = load_state(workspace)
    state["last_daily_report_date"] = run_day
    save_state(workspace, state)
    print(f"markdown={markdown_path}")
    print(f"html={html_path}")
    if delivery_gaps:
        print("delivery_gaps=" + "; ".join(delivery_gaps))
    return 0


def _collect_intraday_alerts(entries: list[CoverageEntry], snapshots: dict[str, dict], sent_event_ids: set[str]) -> tuple[list[CoverageEntry], list[str]]:
    alert_entries: list[CoverageEntry] = []
    new_event_ids: list[str] = []
    for entry in entries:
        snapshot = snapshots.get(entry.ticker or entry.company, {})
        if not should_alert_intraday(entry, snapshot):
            continue
        if snapshot.get("headline"):
            event_type = "headline"
            marker = str(snapshot.get("headline"))
        else:
            event_type = "price_move"
            marker = f"{snapshot.get('market_time', '')}|{snapshot.get('price_move_pct', 0)}"
        event_id = build_event_id(entry.ticker or entry.company, event_type, marker)
        if event_id in sent_event_ids:
            continue
        alert_entries.append(entry)
        new_event_ids.append(event_id)
    return alert_entries, new_event_ids


def _run_intraday(workspace: Path, dry_run: bool, once: bool, interval_minutes: int) -> int:
    while True:
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        universe = build_universe(workspace, today=datetime.now().date().isoformat())
        snapshots, snapshot_gaps = collect_snapshots(universe.entries, today=datetime.now().date().isoformat())
        state = load_state(workspace)
        sent_event_ids = set(state.get("sent_event_ids", []))
        alert_entries, new_event_ids = _collect_intraday_alerts(universe.entries, snapshots, sent_event_ids)
        if alert_entries:
            markdown_text = render_alert_markdown(alert_entries, snapshots, now)
            if dry_run:
                print(markdown_text)
            else:
                send_email(f"Intraday Coverage Alerts {now}", markdown_text, env=workspace_env(workspace))
                state["sent_event_ids"] = sorted(sent_event_ids.union(new_event_ids))
                state["last_intraday_run_at"] = now
                save_state(workspace, state)
        else:
            print("no_intraday_alerts")
        if snapshot_gaps:
            print("snapshot_gaps=" + "; ".join(snapshot_gaps))
        if dry_run or once:
            return 0
        time.sleep(max(interval_minutes, 1) * 60)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run coverage monitoring from workspace coverage state.")
    parser.add_argument("--workspace", default=".", help="Workspace root path.")
    workspace_parent = argparse.ArgumentParser(add_help=False)
    workspace_parent.add_argument("--workspace", default=".", help="Workspace root path.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("doctor", parents=[workspace_parent], help="Check coverage-monitor workspace readiness.")

    normalize = subparsers.add_parser("normalize-coverage", parents=[workspace_parent], help="Normalize COVERAGE.md to the canonical table.")
    normalize.add_argument("--dry-run", action="store_true", help="Print normalized coverage without writing.")
    normalize.add_argument("--today", default="", help="Override the reference date (YYYY-MM-DD).")

    daily = subparsers.add_parser("daily", parents=[workspace_parent], help="Generate the daily coverage brief.")
    daily.add_argument("--dry-run", action="store_true", help="Render without writing or sending.")
    daily.add_argument("--today", default="", help="Override the report date (YYYY-MM-DD).")
    daily.add_argument("--enrichment", default="", help="Path to agent enrichment JSON (mover explainers, core watch news, industry summaries).")
    daily.add_argument("--explainers", default="", help="(deprecated) Use --enrichment instead.")
    daily.add_argument("--skip-fetch", action="store_true", help="Skip data fetching; re-render from cached daily state.")
    daily.add_argument("--ai-review-input", action="store_true", help="Write .cache/coverage-monitor/ai-review-input.json (movers + news + titles) for agent review.")
    daily.add_argument("--ai-review", default="", help="Path to agent AI review output JSON {review_map, translations}.")
    daily.add_argument("--weekend", action="store_true", help="允许周末生成日报（默认周末跳过）")
    daily.add_argument("--report-type", default="us", choices=("us", "asia", "eu"),
                       help="Report coverage: am=亚洲盘前全量 / asia=亚盘盘后 / eu=欧盘盘后.")

    intraday = subparsers.add_parser("intraday", parents=[workspace_parent], help="Run intraday alert monitoring.")
    intraday.add_argument("--dry-run", action="store_true", help="Evaluate alerts without sending.")
    intraday.add_argument("--once", action="store_true", help="Run one pass and exit.")
    intraday.add_argument("--interval-minutes", type=int, default=15, help="Polling interval for looping mode.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    workspace = _workspace_root(args.workspace)
    if not workspace.exists():
        print(f"workspace_not_found={workspace}")
        return 2

    try:
        if args.command == "doctor":
            return _doctor(workspace)
        if args.command == "normalize-coverage":
            return _normalize_coverage(workspace, today=args.today or None, dry_run=args.dry_run)
        if args.command == "daily":
            enrichment_file = Path(args.enrichment or args.explainers) if (args.enrichment or args.explainers) else None
            return _run_daily(workspace, today=args.today or None, dry_run=args.dry_run,
                              enrichment_path=enrichment_file, skip_fetch=args.skip_fetch,
                              report_type=args.report_type,
                              ai_review=args.ai_review, ai_review_input=args.ai_review_input,
                              force_weekend=args.weekend)
        if args.command == "intraday":
            return _run_intraday(workspace, dry_run=args.dry_run, once=args.once or args.dry_run, interval_minutes=args.interval_minutes)
    except UnicodeDecodeError:
        return 2
    return 0
