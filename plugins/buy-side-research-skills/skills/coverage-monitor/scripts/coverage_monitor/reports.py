from __future__ import annotations

from collections import defaultdict
from html import escape
from typing import Any

from .coverage import CoverageEntry
from .news import ImportantMoverExplainer, NewsItem
from .signals import assess_snapshot, quote_exception_status, summarize_data_health


ALERT_KEYWORDS = (
    "earnings",
    "guidance",
    "warning",
    "acquisition",
    "contract",
    "results",
    "order",
    "backlog",
)


def _today_return(entry: CoverageEntry, snapshots: dict[str, dict[str, Any]]) -> float | None:
    snapshot = snapshots.get(entry.ticker or entry.company, {})
    if "price_move_pct" not in snapshot:
        return None
    try:
        return float(snapshot.get("price_move_pct") or 0.0)
    except (TypeError, ValueError):
        return None


def _format_today_return(value: float | None) -> str:
    return "—" if value is None else f"{value:+.2f}%"


def _universe_sort_key(entry: CoverageEntry, snapshots: dict[str, dict[str, Any]]) -> tuple[Any, ...]:
    coverage_rank = {"Core Coverage": 0, "Building Coverage": 1, "Radar": 2}
    monitor_rank = {"Core Watch": 0, "Daily Watch": 1}
    move = _today_return(entry, snapshots)
    return (
        entry.industry.lower(),
        coverage_rank.get(entry.coverage_status, 9),
        monitor_rank.get(entry.monitor_status, 9),
        1 if move is None else 0,
        -abs(move or 0.0),
        (entry.ticker or entry.company).lower(),
    )


def _coverage_slug(value: str) -> str:
    mapping = {
        "Core Coverage": "core",
        "Building Coverage": "building",
        "Radar": "radar",
    }
    return mapping.get(value, "unknown")


def _monitor_slug(value: str) -> str:
    mapping = {
        "Core Watch": "core-watch",
        "Daily Watch": "daily-watch",
    }
    return mapping.get(value, "unknown")


def _market_label(entry: CoverageEntry) -> str:
    ticker = entry.ticker.strip()
    if not ticker or ticker.lower() == "ipo pending":
        return "n/a"
    parts = ticker.split()
    return parts[-1].upper() if len(parts) > 1 else "n/a"


def _return_class(value: float | None) -> str:
    if value is None:
        return "na"
    return "pos" if value >= 0 else "neg"


def _float_metric(snapshot: dict[str, Any], field: str) -> float | None:
    try:
        value = snapshot.get(field)
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _format_metric(value: float | None, suffix: str = "", digits: int = 2, na: str = "n/a") -> str:
    if value is None:
        return na
    return f"{value:+.{digits}f}{suffix}" if suffix == "%" else f"{value:.{digits}f}{suffix}"


def _headline_link(item: NewsItem) -> str:
    if not item.url:
        return escape(item.title)
    return f'<a href="{escape(item.url)}">{escape(item.title)}</a>'


def _mover_explanation(entry: CoverageEntry, snapshot: dict[str, Any]) -> str:
    assessment = assess_snapshot(snapshot)
    if not assessment:
        return "价格有波动，但还没到本轮 daily mover 的 material threshold。"
    label = "重要异动" if assessment.is_important else "普通异动"
    return f"{label}触发项：{' / '.join(assessment.highlight_tags or assessment.trigger_tags)}。"


def should_alert_intraday(entry: CoverageEntry, snapshot: dict[str, Any]) -> bool:
    if entry.monitor_status != "Core Watch":
        return False
    assessment = assess_snapshot(snapshot)
    if assessment and assessment.is_important:
        return True
    headline = str(snapshot.get("headline") or "").lower()
    return any(keyword in headline for keyword in ALERT_KEYWORDS)


def _mover_entries(entries: list[CoverageEntry], snapshots: dict[str, dict[str, Any]]) -> list[tuple[CoverageEntry, dict[str, Any], Any]]:
    movers: list[tuple[CoverageEntry, dict[str, Any], Any]] = []
    for entry in entries:
        snapshot = snapshots.get(entry.ticker or entry.company, {})
        assessment = assess_snapshot(snapshot)
        if not assessment:
            continue
        movers.append((entry, snapshot, assessment))
    return sorted(
        movers,
        key=lambda item: (
            0 if item[2].is_important else 1,
            -abs(float(item[1].get("price_move_pct") or 0.0)),
            (item[0].ticker or item[0].company).lower(),
        ),
    )


def render_daily_markdown(
    entries: list[CoverageEntry],
    snapshots: dict[str, dict[str, Any]],
    today: str,
    gaps: list[str],
    company_news: dict[str, list[NewsItem]] | None = None,
    industry_readthroughs: dict[str, list[NewsItem]] | None = None,
    important_explainers: dict[str, ImportantMoverExplainer] | None = None,
) -> str:
    grouped: dict[str, list[CoverageEntry]] = defaultdict(list)
    for entry in entries:
        grouped[entry.industry or "unclassified"].append(entry)
    company_news = company_news or {}
    industry_readthroughs = industry_readthroughs or {}
    important_explainers = important_explainers or {}
    core_entries = [entry for entry in entries if entry.monitor_status == "Core Watch"]
    movers = _mover_entries(entries, snapshots)
    health_summary = summarize_data_health(gaps)

    lines = [
        f"# Daily Coverage Brief — {today}",
        "",
        "## 1. Executive Snapshot",
        f"- Coverage: {len(entries)} names | Core Watch: {len(core_entries)}",
        f"- Material movers: {len(movers)} | data issues: {len(gaps)}",
    ]
    if movers:
        top_entry, top_snapshot, top_assessment = movers[0]
        label = "important" if top_assessment.is_important else "ordinary"
        lines.append(
            f"- Top move: `{top_entry.ticker or top_entry.company}` {top_entry.company} "
            f"{top_snapshot.get('price_move_pct', 0):+.2f}% ({label})"
        )
    if health_summary:
        lines.append(f"- Data Health: {'; '.join(health_summary)}")
    lines.extend(["", "## 2. Price Movers & Explanations"])
    if movers:
        for entry, snapshot, assessment in movers:
            move = float(snapshot.get("price_move_pct") or 0)
            volume = snapshot.get("volume_ratio", "n/a")
            gap = snapshot.get("gap_pct", "n/a")
            lines.append(
                f"- `{entry.ticker or entry.company}` {entry.company}: {move:+.2f}% | vol {volume}x | gap {gap:+.2f}% "
                f"| {' / '.join(assessment.highlight_tags or assessment.trigger_tags)}"
            )
            if assessment.is_important and (entry.ticker or entry.company) in important_explainers:
                explainer = important_explainers[entry.ticker or entry.company]
                lines.append(f"  - summary: {explainer.summary}")
                lines.append(f"  - confidence: {explainer.confidence}")
    else:
        lines.append("- No material movers in this run.")

    lines.extend(["", "## 3. Core Watch Company News"])
    for entry in core_entries:
        key = entry.ticker or entry.company
        items = company_news.get(key, [])
        if not items:
            lines.append(f"- `{key}` {entry.company}: no company news found.")
            continue
        first = items[0]
        lines.append(f"- `{key}` {entry.company}: [{first.title}]({first.url})")
        status = quote_exception_status(snapshots.get(key, {}), report_day=today)
        if status:
            lines.append(f"  - Quote status: {status}")

    lines.extend(["", "## 4. Industry Read-Throughs"])
    for industry in sorted(grouped):
        lines.append(f"### {industry}")
        items = industry_readthroughs.get(industry, [])
        if items:
            for item in items[:5]:
                tier = f" ({item.tier})" if item.tier else ""
                lines.append(f"- [{item.title}]({item.url}){tier}")
        else:
            lines.append("- No industry read-through item collected.")

    lines.extend(["", "## 5. Coverage Gaps"])
    if gaps:
        for gap_item in gaps[:80]:
            lines.append(f"- {gap_item}")
        if len(gaps) > 80:
            lines.append(f"- ... {len(gaps) - 80} more gaps")
    else:
        lines.append("- No material data or monitor gaps in this run.")

    lines.extend(
        [
            "",
            "## Universe",
            "",
            "| Ticker | Company | Industry | Today Return | Coverage | Monitor | Last Review | Next Trigger |",
            "|---|---|---|---|---|---|---|---|",
        ]
    )
    for entry in sorted(entries, key=lambda item: _universe_sort_key(item, snapshots)):
        key = entry.ticker or entry.company
        status = quote_exception_status(snapshots.get(key, {}), report_day=today)
        status_suffix = f" ({status})" if status else ""
        lines.append(
            f"| {entry.ticker or ''} | {entry.company} | {entry.industry} | {_format_today_return(_today_return(entry, snapshots))}{status_suffix} | {entry.coverage_status} | {entry.monitor_status} | {entry.last_review} | {entry.next_trigger} |"
        )
    return "\n".join(lines) + "\n"


def render_alert_markdown(entries: list[CoverageEntry], snapshots: dict[str, dict[str, Any]], now_label: str) -> str:
    lines = [f"# Intraday Coverage Alerts - {now_label}", ""]
    for entry in entries:
        snapshot = snapshots.get(entry.ticker or entry.company, {})
        lines.append(
            f"- `{entry.ticker or entry.company}` {entry.company}: {snapshot.get('price_move_pct', 0)}% | {snapshot.get('headline') or entry.next_trigger or 'material move'}"
        )
    return "\n".join(lines) + "\n"


def render_dashboard_html(
    entries: list[CoverageEntry],
    snapshots: dict[str, dict[str, Any]],
    today: str,
    gaps: list[str],
    company_news: dict[str, list[NewsItem]] | None = None,
    industry_readthroughs: dict[str, list[NewsItem]] | None = None,
    important_explainers: dict[str, ImportantMoverExplainer] | None = None,
) -> str:
    company_news = company_news or {}
    industry_readthroughs = industry_readthroughs or {}
    important_explainers = important_explainers or {}
    core_entries = [entry for entry in entries if entry.monitor_status == "Core Watch"]
    movers = _mover_entries(entries, snapshots)
    grouped: dict[str, list[CoverageEntry]] = defaultdict(list)
    for entry in entries:
        grouped[entry.industry or "unclassified"].append(entry)
    industry_list = sorted(grouped)
    market_values = sorted({_market_label(entry) for entry, _, _ in movers if _market_label(entry) != "n/a"})
    health_summary = summarize_data_health(gaps)

    mover_cards: list[str] = []
    for entry, snapshot, assessment in movers:
        move = _today_return(entry, snapshots)
        volume = _float_metric(snapshot, "volume_ratio")
        gap = _float_metric(snapshot, "gap_pct")
        ret_class = _return_class(move)
        key = entry.ticker or entry.company
        trigger_pills = "".join(f'<span class="pill trigger">{escape(tag)}</span>' for tag in (assessment.highlight_tags or assessment.trigger_tags))
        importance_pill = '<span class="pill importance">Important Move</span>' if assessment.is_important else '<span class="pill importance ordinary">Mover</span>'
        explainer = important_explainers.get(key)
        explainer_block = ""
        if explainer:
            evidence_html = "".join(
                f"<li>{_headline_link(item)}<span> · {escape(item.source or 'source')}</span></li>" for item in explainer.evidence[:5]
            ) or "<li>No external evidence retained.</li>"
            filing_html = "".join(
                f"<li>{_headline_link(item)}<span> · {escape(item.source or 'official')}</span></li>" for item in explainer.filings_evidence[:3]
            ) or "<li>No filing / official release captured.</li>"
            explainer_block = f"""
                <div class="explainer">
                  <div class="explainer-top">
                    <span class="pill confidence">{escape(explainer.confidence)}</span>
                    <span class="confidence-label">Confidence</span>
                  </div>
                  <p class="body-copy">{escape(explainer.summary)}</p>
                  <details open><summary>News / Evidence</summary><ul>{evidence_html}</ul></details>
                  <details><summary>Filings / Official</summary><ul>{filing_html}</ul></details>
                </div>
            """
        else:
            fallback_news = company_news.get(key, [])
            evidence_html = "".join(
                f"<li>{_headline_link(item)}<span> · {escape(item.source or 'source')}</span></li>" for item in fallback_news[:4]
            ) or "<li>No direct company evidence collected.</li>"
            explainer_block = f'<details><summary>News / Evidence</summary><ul>{evidence_html}</ul></details>'
        mover_cards.append(
            f"""
            <article class="mover-card mover {'important-move' if assessment.is_important else ''}" data-market="{escape(_market_label(entry))}" data-industry="{escape(entry.industry)}" data-return="{escape(str(move or 0.0))}">
              <div class="ticker-block">
                <div class="ticker">{escape(entry.ticker or entry.company)}</div>
                <div class="company">{escape(entry.company)} · {escape(entry.industry)}</div>
                <div class="return {ret_class}">{escape(_format_today_return(move))}</div>
                <div class="chip-row">
                  <span class="pill coverage {escape(_coverage_slug(entry.coverage_status))}">{escape(entry.coverage_status)}</span>
                  <span class="pill monitor {escape(_monitor_slug(entry.monitor_status))}">{escape(entry.monitor_status)}</span>
                  {importance_pill}
                </div>
                <div class="chip-row">{trigger_pills}</div>
              </div>
              <div>
                <div class="metric-row">
                  <div class="metric"><b>{escape(_format_metric(volume, "x", digits=2))}</b><span>volume ratio</span></div>
                  <div class="metric"><b>{escape(_format_metric(gap, "%", digits=2))}</b><span>gap</span></div>
                  <div class="metric"><b>{escape(str(snapshot.get("last_price") or "n/a"))}</b><span>last price</span></div>
                  <div class="metric"><b>{escape(str(snapshot.get("market_time") or today))}</b><span>market time</span></div>
                </div>
                <p class="body-copy">{escape(_mover_explanation(entry, snapshot))}</p>
                {explainer_block}
              </div>
            </article>
            """
        )

    core_cards: list[str] = []
    for entry in core_entries:
        key = entry.ticker or entry.company
        news_items = company_news.get(key, [])
        news_html = "".join(
            f"<li><a href=\"{escape(item.url)}\">{escape(item.title)}</a><span> · {escape(item.source or 'source')}</span></li>"
            for item in news_items[:6]
        ) or "<li>No company news found in this run.</li>"
        status = quote_exception_status(snapshots.get(key, {}), report_day=today)
        status_line = f'<p class="status-line">Quote status: {escape(status)}</p>' if status else ""
        core_cards.append(
            f"""
            <article class="card">
              <span class="pill coverage {escape(_coverage_slug(entry.coverage_status))}">{escape(entry.coverage_status)}</span>
              <h3>{escape(entry.ticker or entry.company)} · {escape(entry.company)}</h3>
              <p class="body-copy">核心监控位默认每天搜公司级 news / results / contract / order。当前下一触发点：{escape(entry.next_trigger or 'pending update')}。</p>
              {status_line}
              <details open><summary>News / Evidence</summary><ul>{news_html}</ul></details>
            </article>
            """
        )

    industry_sections: list[str] = []
    for industry in industry_list:
        items = industry_readthroughs.get(industry, [])
        linked_names = ", ".join(entry.company for entry in sorted(grouped[industry], key=lambda item: _universe_sort_key(item, snapshots))[:8])
        sources_html = "".join(
            f"""
            <div class="source-line">
              <b><a href="{escape(item.url)}">{escape(item.title)}</a></b>
              <span>{escape(item.source or 'source')} {escape(item.tier or '')}</span>
            </div>
            """
            for item in items[:12]
        ) or '<div class="source-line"><b>No source item collected.</b><span>Fallback search also returned nothing durable.</span></div>'
        industry_sections.append(
            f"""
            <article class="card industry-card">
              <div>
                <div class="industry-name">{escape(industry)}</div>
                <div class="chip-row">
                  <span class="pill monitor core-watch">Tracked names</span>
                  <span class="pill">{escape(str(len(grouped[industry])))}</span>
                </div>
              </div>
              <div>
                <p class="body-copy">今日行业 read-through 覆盖 {escape(linked_names or 'n/a')}。Substack / trade media / official source 全扫；没有新内容时才 fallback general news。</p>
                <div class="source-stack">{sources_html}</div>
              </div>
            </article>
            """
        )

    gap_items = "".join(f"<li>{escape(gap)}</li>" for gap in gaps[:100]) or "<li>No material gap in this run.</li>"
    health_items = "".join(f"<li>{escape(item)}</li>" for item in health_summary) or "<li>No material data issue summary in this run.</li>"
    universe_rows: list[str] = []
    for entry in sorted(entries, key=lambda item: _universe_sort_key(item, snapshots)):
        key = entry.ticker or entry.company
        move = _today_return(entry, snapshots)
        ret_class = _return_class(move)
        status = quote_exception_status(snapshots.get(key, {}), report_day=today)
        status_html = f' <span class="pill status">{escape(status)}</span>' if status else ""
        universe_rows.append(
            f"""
            <tr data-industry="{escape(entry.industry)}" data-coverage="{escape(_coverage_slug(entry.coverage_status))}" data-monitor="{escape(_monitor_slug(entry.monitor_status))}">
              <td>{escape(entry.ticker or '')}</td>
              <td>{escape(entry.company)}</td>
              <td>{escape(entry.industry)}</td>
              <td><span class="ret {ret_class}">{escape(_format_today_return(move))}</span>{status_html}</td>
              <td>{escape(entry.coverage_status)}</td>
              <td>{escape(entry.monitor_status)}</td>
              <td>{escape(entry.last_review)}</td>
              <td>{escape(entry.next_trigger)}</td>
            </tr>
            """
        )

    return f"""<!doctype html>
<html lang="zh-Hans">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Daily Coverage Dashboard {escape(today)}</title>
<style>
:root {{
  --ink: #132238;
  --muted: #64748b;
  --line: rgba(148,163,184,.34);
  --card: rgba(255,255,255,.88);
  --blue: #2563eb;
  --green: #0f9f6e;
  --red: #d33b3b;
  --amber: #b7791f;
  --slate: #475569;
  --blue-soft: #dbeafe;
  --green-soft: #dff7eb;
  --red-soft: #ffe4e6;
  --amber-soft: #fff7d6;
  --slate-soft: #e2e8f0;
  --shadow: 0 22px 70px rgba(15,23,42,.12);
}}
* {{ box-sizing:border-box; }}
body {{
  margin: 0;
  color: var(--ink);
  font-family: "Noto Sans SC", "Microsoft YaHei", "PingFang SC", sans-serif;
  background: radial-gradient(circle at top left,#d9eef4 0,#f7fafc 38%,#edf2f6 100%);
  font-variant-numeric: tabular-nums;
}}
a {{ color: inherit; }}
main {{ width: min(1440px, calc(100vw - 36px)); margin: 28px auto 48px; }}
.hero {{
  position: relative;
  overflow: hidden;
  border: 1px solid var(--line);
  border-radius: 32px;
  padding: 32px;
  background:
    linear-gradient(135deg,rgba(255,255,255,.96),rgba(255,255,255,.66)),
    radial-gradient(circle at 88% 18%,rgba(37,99,235,.16),transparent 28%);
  box-shadow: var(--shadow);
}}
.hero-top {{
  position: relative;
  z-index: 1;
  display: flex;
  justify-content: space-between;
  gap: 24px;
  align-items: flex-start;
}}
.eyebrow {{
  color: var(--blue);
  letter-spacing: .16em;
  text-transform: uppercase;
  font-size: 12px;
  font-weight: 900;
}}
h1 {{ margin: 10px 0; font-size: clamp(34px,5vw,60px); line-height: 1.02; letter-spacing: -.055em; }}
h2 {{ margin: 0; font-size: 25px; letter-spacing: -.04em; }}
h3 {{ margin: 10px 0 12px; font-size: 22px; letter-spacing: -.04em; }}
.subtitle {{ max-width: 880px; color: var(--muted); font-size: 15px; line-height: 1.78; }}
.status-badge {{
  border: 1px solid rgba(37,99,235,.22);
  background: rgba(219,234,254,.85);
  color: #1d4ed8;
  border-radius: 999px;
  padding: 9px 13px;
  font-size: 14px;
  font-weight: 900;
  white-space: nowrap;
}}
.kpi-grid {{
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: repeat(4,minmax(0,1fr));
  gap: 14px;
  margin-top: 28px;
}}
.kpi {{
  border: 1px solid var(--line);
  border-radius: 22px;
  background: rgba(255,255,255,.72);
  padding: 18px;
}}
.kpi .label {{ color: var(--muted); font-size: 12px; font-weight: 900; text-transform: uppercase; letter-spacing: .08em; }}
.kpi .value {{ margin-top: 8px; font-size: 31px; font-weight: 950; letter-spacing: -.04em; }}
.kpi .hint {{ margin-top: 5px; color: var(--muted); font-size: 12px; }}
.health-card {{
  margin-top: 16px;
  border: 1px solid var(--line);
  border-radius: 18px;
  background: rgba(255,255,255,.72);
  padding: 14px 16px;
}}
.health-card h3 {{ margin: 0 0 6px; font-size: 16px; }}
.health-card ul {{ margin: 0; padding-left: 18px; }}
.tab-nav {{
  position: sticky;
  top: 0;
  z-index: 20;
  margin: 18px 0;
  display: flex;
  gap: 10px;
  padding: 10px;
  border: 1px solid var(--line);
  border-radius: 22px;
  background: rgba(255,255,255,.82);
  backdrop-filter: blur(18px);
  box-shadow: 0 10px 35px rgba(15,23,42,.08);
  overflow-x: auto;
}}
.tab-button {{
  border: 0;
  border-radius: 16px;
  padding: 12px 18px;
  background: transparent;
  color: var(--muted);
  font-weight: 950;
  cursor: pointer;
  white-space: nowrap;
}}
.tab-button.active {{ color: white; background: #132238; box-shadow: 0 12px 24px rgba(19,34,56,.24); }}
.tab-panel {{ display: none; }}
.tab-panel.active {{ display: block; animation: rise .22s ease-out; }}
@keyframes rise {{ from {{ opacity: 0; transform: translateY(8px); }} to {{ opacity: 1; transform: translateY(0); }} }}
.section-head {{
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 18px;
  margin: 18px 2px 12px;
}}
.section-head p {{ margin: 6px 0 0; max-width: 840px; color: var(--muted); line-height: 1.68; }}
.filter-bar {{
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  padding: 12px;
  margin-bottom: 14px;
  border: 1px solid var(--line);
  border-radius: 20px;
  background: rgba(255,255,255,.72);
}}
select, input {{
  border: 1px solid var(--line);
  border-radius: 14px;
  padding: 10px 12px;
  background: white;
  color: var(--ink);
  font-weight: 800;
  min-width: 160px;
}}
.grid-2 {{ display: grid; grid-template-columns: repeat(2,minmax(0,1fr)); gap: 14px; }}
.stack {{ display: grid; gap: 14px; }}
.card, .mover-card {{
  border: 1px solid var(--line);
  border-radius: 24px;
  background: var(--card);
  box-shadow: 0 14px 44px rgba(15,23,42,.08);
  padding: 18px;
}}
.mover-card {{ display: grid; grid-template-columns: 220px 1fr; gap: 18px; margin-bottom: 14px; }}
.important-move {{ border-color: rgba(183,121,31,.32); box-shadow: 0 16px 48px rgba(183,121,31,.12); }}
.ticker-block {{ border-right: 1px solid var(--line); padding-right: 16px; }}
.ticker {{ font-size: 24px; font-weight: 950; letter-spacing: -.04em; }}
.company {{ margin-top: 6px; color: var(--muted); line-height: 1.45; }}
.return {{ display: inline-flex; margin-top: 13px; border-radius: 999px; padding: 8px 11px; font-size: 20px; font-weight: 950; }}
.return.pos, .up, .ret.pos {{ color: var(--green); background: var(--green-soft); }}
.return.neg, .down, .ret.neg {{ color: var(--red); background: var(--red-soft); }}
.ret.na {{ color: var(--muted); font-weight: 800; background: transparent; }}
.metric-row {{ display: grid; grid-template-columns: repeat(4,minmax(0,1fr)); gap: 10px; margin: 10px 0 12px; }}
.metric {{
  border: 1px solid var(--line);
  border-radius: 16px;
  background: rgba(248,250,252,.78);
  padding: 11px;
}}
.metric b {{ display: block; font-size: 15px; }}
.metric span {{ display: block; margin-top: 4px; color: var(--muted); font-size: 12px; font-weight: 800; }}
.body-copy {{ color: #334155; font-size: 15px; line-height: 1.75; margin: 0 0 12px; }}
details {{
  border: 1px solid var(--line);
  border-radius: 16px;
  background: rgba(255,255,255,.72);
  padding: 10px 12px;
  margin-top: 8px;
}}
summary {{ cursor: pointer; font-weight: 950; color: #1e3a8a; }}
ul {{ margin: 10px 0 0; padding-left: 18px; color: #334155; line-height: 1.7; }}
.chip-row {{ display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; }}
.pill {{
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  padding: 7px 10px;
  font-size: 12px;
  font-weight: 950;
  border: 1px solid rgba(99,102,241,.18);
  text-decoration: none;
}}
.pill.coverage.core {{ background: var(--blue-soft); color: #1d4ed8; }}
.pill.coverage.building {{ background: var(--amber-soft); color: var(--amber); }}
.pill.coverage.radar {{ background: var(--slate-soft); color: var(--slate); }}
.pill.monitor.core-watch {{ background: var(--green-soft); color: var(--green); }}
.pill.monitor.daily-watch {{ background: var(--slate-soft); color: var(--slate); }}
.pill.importance {{ background: var(--amber-soft); color: var(--amber); }}
.pill.importance.ordinary {{ background: var(--slate-soft); color: var(--slate); }}
.pill.trigger {{ background: rgba(255,255,255,.82); color: #334155; }}
.pill.status {{ background: rgba(248,250,252,.9); color: #475569; margin-left: 6px; }}
.pill.confidence {{ background: var(--blue-soft); color: #1d4ed8; }}
.explainer {{ margin-top: 10px; }}
.explainer-top {{ display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }}
.confidence-label {{ color: var(--muted); font-size: 12px; font-weight: 900; text-transform: uppercase; }}
.status-line {{ color: var(--muted); font-size: 13px; margin: 0 0 10px; }}
.table-card {{
  overflow: hidden;
  border: 1px solid var(--line);
  border-radius: 24px;
  background: var(--card);
  box-shadow: 0 14px 44px rgba(15,23,42,.07);
}}
table {{ width: 100%; border-collapse: collapse; font-size: 14.5px; }}
th, td {{
  padding: 13px 14px;
  border-bottom: 1px solid rgba(148,163,184,.22);
  text-align: left;
  vertical-align: top;
}}
th {{
  color: var(--muted);
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: .08em;
  background: rgba(248,250,252,.82);
  white-space: nowrap;
}}
tr:last-child td {{ border-bottom: 0; }}
#universeTable tr[data-coverage="core"] td:nth-child(5) {{ color: #1d4ed8; font-weight: 950; }}
#universeTable tr[data-coverage="building"] td:nth-child(5) {{ color: var(--amber); font-weight: 950; }}
#universeTable tr[data-coverage="radar"] td:nth-child(5) {{ color: var(--slate); font-weight: 950; }}
#universeTable tr[data-monitor="core-watch"] td:nth-child(6) {{ color: var(--green); font-weight: 950; }}
#universeTable tr[data-monitor="daily-watch"] td:nth-child(6) {{ color: var(--slate); font-weight: 900; }}
.industry-card {{ display: grid; grid-template-columns: 260px 1fr; gap: 18px; align-items: start; }}
.industry-name {{ font-size: 22px; font-weight: 950; letter-spacing: -.04em; }}
.source-stack {{ display: flex; flex-direction: column; gap: 8px; margin-top: 12px; }}
.source-line {{ border: 1px solid var(--line); background: rgba(255,255,255,.72); border-radius: 14px; padding: 10px; }}
.source-line b {{ display: block; }}
.source-line span {{ display: block; color: var(--muted); font-size: 12px; margin-top: 3px; }}
@media (max-width: 960px) {{
  .hero-top, .section-head {{ flex-direction: column; align-items: flex-start; }}
  .kpi-grid, .grid-2 {{ grid-template-columns: 1fr; }}
  .mover-card, .industry-card {{ grid-template-columns: 1fr; }}
  .ticker-block {{ border-right: 0; border-bottom: 1px solid var(--line); padding: 0 0 14px; }}
  .metric-row {{ grid-template-columns: repeat(2,minmax(0,1fr)); }}
}}
</style>
</head>
<body>
<main>
  <section class="hero">
    <div class="hero-top">
      <div>
        <div class="eyebrow">Coverage Monitor Daily</div>
        <h1>Daily Coverage Dashboard</h1>
        <div class="subtitle">
          English handles structure; 中文负责判断解释。日报只做日终 coverage monitoring，不做仓位/P&amp;L，不把研究 memo 重新写一遍。
        </div>
      </div>
      <div class="status-badge">{escape(today)} · workspace coverage</div>
    </div>
    <div class="kpi-grid">
      <div class="kpi"><div class="label">Coverage Universe</div><div class="value">{len(entries)}</div><div class="hint">COVERAGE.md registered names</div></div>
      <div class="kpi"><div class="label">Material Movers</div><div class="value">{len(movers)}</div><div class="hint">return / volume / gap trigger</div></div>
      <div class="kpi"><div class="label">Core Watch</div><div class="value">{len(core_entries)}</div><div class="hint">daily company search list</div></div>
      <div class="kpi"><div class="label">Data Issues</div><div class="value">{len(gaps)}</div><div class="hint">quote / source / delivery gaps</div></div>
    </div>
    <div class="health-card">
      <h3>Data Health</h3>
      <ul>{health_items}</ul>
    </div>
  </section>

  <nav class="tab-nav" aria-label="Dashboard tabs">
    <button class="tab-button active" data-tab="movers">Movers</button>
    <button class="tab-button" data-tab="core">Core Watch</button>
    <button class="tab-button" data-tab="industry">Industry Tape</button>
    <button class="tab-button" data-tab="universe">Universe</button>
  </nav>

  <section id="movers" class="tab-panel active">
    <div class="section-head">
      <div>
        <h2>Movers</h2>
        <p>只放命中本轮 material threshold 的名字。先给 return / volume ratio / gap，再压一句中文解释，重要异动额外给 evidence 与 filing layer。</p>
      </div>
    </div>
    <div class="filter-bar">
      <select id="marketFilter"><option value="all">Market · All</option>{''.join(f'<option value="{escape(market)}">{escape(market)}</option>' for market in market_values)}</select>
      <select id="industryFilter"><option value="all">Industry · All</option>{''.join(f'<option value="{escape(industry)}">{escape(industry)}</option>' for industry in industry_list)}</select>
      <select id="sortMode"><option value="abs">Sort · Abs return</option><option value="up">Only up</option><option value="down">Only down</option></select>
    </div>
    {''.join(mover_cards) or '<article class="card">No material movers in this run.</article>'}
  </section>

  <section id="core" class="tab-panel">
    <div class="section-head">
      <div>
        <h2>Core Watch</h2>
        <p>Core Coverage / Core Watch 名单每天都搜公司级 news，不等价格异动。没有 material update 也应留下 evidence log。</p>
      </div>
    </div>
    <div class="grid-2">{''.join(core_cards) or '<article class="card">No Core Watch companies registered.</article>'}</div>
  </section>

  <section id="industry" class="tab-panel">
    <div class="section-head">
      <div>
        <h2>Industry Tape</h2>
        <p>按行业扫 Daily Signal Sources。Substack / trade media / official 都扫；都没有新东西时，再 fallback general news。</p>
      </div>
    </div>
    <div class="stack">{''.join(industry_sections) or '<article class="card">No industry read-through source configured.</article>'}</div>
  </section>

  <section id="universe" class="tab-panel">
    <div class="section-head">
      <div>
        <h2>Universe</h2>
        <p>覆盖全部注册名字。这里只在异常时展示 quote status，不把状态系统做成正文主角。</p>
      </div>
    </div>
    <div class="filter-bar">
      <select id="universeIndustry"><option value="all">Industry · All</option>{''.join(f'<option value="{escape(industry)}">{escape(industry)}</option>' for industry in industry_list)}</select>
      <select id="universeCoverage"><option value="all">Coverage · All</option><option value="core">Core Coverage</option><option value="building">Building Coverage</option><option value="radar">Radar</option></select>
      <input id="universeSearch" placeholder="Search ticker / company">
    </div>
    <article class="card">
      <span class="pill coverage core">Coverage Contract</span>
      <h3>Coverage is the displayed research state</h3>
      <p class="body-copy">展示层和底层都只保留 `Coverage` + `Monitor` 语义字段，不再保留旧 T/A contract。不同状态直接用含义名字显示。</p>
      <details><summary>Coverage Gaps ({len(gaps)})</summary><ul>{gap_items}</ul></details>
    </article>
    <div class="table-card">
      <table id="universeTable">
        <thead><tr><th>Ticker</th><th>Company</th><th>Industry</th><th>Today Return</th><th>Coverage</th><th>Monitor</th><th>Last Review</th><th>Next Trigger</th></tr></thead>
        <tbody>{''.join(universe_rows)}</tbody>
      </table>
    </div>
  </section>
</main>
<script>
const buttons = Array.from(document.querySelectorAll(".tab-button"));
const panels = Array.from(document.querySelectorAll(".tab-panel"));
buttons.forEach((button) => {{
  button.addEventListener("click", () => {{
    buttons.forEach((b) => b.classList.remove("active"));
    panels.forEach((p) => p.classList.remove("active"));
    button.classList.add("active");
    document.getElementById(button.dataset.tab).classList.add("active");
  }});
}});

const marketFilter = document.getElementById("marketFilter");
const industryFilter = document.getElementById("industryFilter");
const sortMode = document.getElementById("sortMode");
const movers = Array.from(document.querySelectorAll(".mover"));
function applyMoverFilters() {{
  if (!marketFilter || !industryFilter || !sortMode) return;
  const market = marketFilter.value;
  const industry = industryFilter.value;
  const mode = sortMode.value;
  movers.forEach((card) => {{
    const ret = Number(card.dataset.return || "0");
    const okMarket = market === "all" || card.dataset.market === market;
    const okIndustry = industry === "all" || card.dataset.industry === industry;
    const okMode = mode === "abs" || (mode === "up" && ret > 0) || (mode === "down" && ret < 0);
    card.style.display = okMarket && okIndustry && okMode ? "grid" : "none";
  }});
}}
[marketFilter, industryFilter, sortMode].forEach((node) => node && node.addEventListener("change", applyMoverFilters));

const universeIndustry = document.getElementById("universeIndustry");
const universeCoverage = document.getElementById("universeCoverage");
const universeSearch = document.getElementById("universeSearch");
const universeRows = Array.from(document.querySelectorAll("#universeTable tbody tr"));
function applyUniverseFilters() {{
  if (!universeIndustry || !universeCoverage || !universeSearch) return;
  const industry = universeIndustry.value;
  const coverage = universeCoverage.value;
  const needle = universeSearch.value.trim().toLowerCase();
  universeRows.forEach((row) => {{
    const okIndustry = industry === "all" || row.dataset.industry === industry;
    const okCoverage = coverage === "all" || row.dataset.coverage === coverage;
    const okSearch = !needle || row.innerText.toLowerCase().includes(needle);
    row.style.display = okIndustry && okCoverage && okSearch ? "" : "none";
  }});
}}
[universeIndustry, universeCoverage, universeSearch].forEach((node) => node && node.addEventListener("input", applyUniverseFilters));
</script>
</body>
</html>"""
