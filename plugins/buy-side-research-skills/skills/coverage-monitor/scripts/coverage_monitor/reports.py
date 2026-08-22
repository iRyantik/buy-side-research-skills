from __future__ import annotations

from collections import defaultdict
from datetime import date
from html import escape
from typing import Any

from .coverage import CoverageEntry
from .brief import _display_name
from .news import ImportantMoverExplainer, NewsItem, pick_lead_news, translate_zh
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


def _format_return_hover(snapshot: dict[str, Any]) -> str:
    """Build title attribute for return cell: 1m / YTD / 1y."""
    parts = []
    for label, key in [("1m", "ret_1m"), ("YTD", "ret_ytd"), ("1y", "ret_1y")]:
        v = snapshot.get(key)
        if v is not None:
            parts.append(f"{label} {v:+.1f}%")
    return " · ".join(parts) if parts else ""


def _universe_sort_key(entry: CoverageEntry, snapshots: dict[str, dict[str, Any]]) -> tuple[Any, ...]:
    coverage_rank = {"Core": 0, "Building": 1, "Radar": 2}
    monitor_rank = {"Core": 0, "Daily": 1}
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
    mapping = {"Core": "core", "Building": "building", "Radar": "radar"}
    return mapping.get(value, "unknown")


def _monitor_slug(value: str) -> str:
    mapping = {"Core": "core-watch", "Daily": "daily-watch"}
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


def _metric_ret(snapshot: dict[str, Any], key: str, label: str) -> str:
    """Render a mover-card metric for a return column with color."""
    v = snapshot.get(key)
    if v is None:
        return f'<div class="snapshot-item"><b>n/a</b><span>{label}</span></div>'
    c = "pos" if v >= 0 else "neg"
    return f'<div class="snapshot-item"><b class="ret {c}">{v:+.1f}%</b><span>{label}</span></div>'


def _display_names(entry: CoverageEntry) -> tuple[str, str | None]:
    primary = (entry.company_native or "").strip() or (entry.company or "").strip()
    secondary = (entry.company or "").strip()
    if not secondary:
        return primary, None
    if primary.strip().casefold() == secondary.strip().casefold():
        return secondary, None
    if primary and primary != secondary:
        return primary, secondary
    return secondary, None


def _company_identity_html(entry: CoverageEntry, extra_class: str = "") -> str:
    primary, secondary = _display_names(entry)
    if not primary:
        return ""
    secondary_html = f'<span class="company-en">{escape(secondary)}</span>' if secondary else ""
    class_attr = f' class="{extra_class}"' if extra_class else ""
    return f'<span{class_attr}>{escape(primary)}{secondary_html}</span>'


# Currency + decimal rules by market suffix
_MARKET_PRICE_RULES: dict[str, tuple[str, int]] = {
    ".T":   ("¥",   0),   # JPY — no decimals
    ".KS":  ("₩",   0),   # KRW
    ".KQ":  ("₩",   0),   # KOSDAQ
    ".TW":  ("NT$",  1),   # TWD
    ".HK":  ("HK$",  2),   # HKD
    ".SS":  ("¥",   2),   # CNY Shanghai
    ".SZ":  ("¥",   2),   # CNY Shenzhen
    ".ST":  ("kr",   1),   # SEK
    ".DE":  ("€",   2),   # EUR Xetra
    ".AS":  ("€",   2),   # EUR Amsterdam
    ".NA":  ("€",   2),   # EUR Amsterdam (alt)
    ".L":   ("£",   2),   # GBP London
    ".KL":  ("RM",   2),   # MYR
    ".US":  ("$",   2),   # USD
}


def _format_cap(market_cap: float | None) -> str:
    """Format market cap: ¥25.3tn / $36.7B / ₩18.5tn."""
    if market_cap is None:
        return ""
    if market_cap >= 1e12:
        return f"{market_cap/1e12:.1f}tn"
    if market_cap >= 1e9:
        return f"{market_cap/1e9:.1f}B"
    if market_cap >= 1e6:
        return f"{market_cap/1e6:.0f}M"
    return f"{market_cap:.0f}"


def _format_price(quote_ticker: str, price: float | None) -> str:
    """Format price with currency symbol and market-appropriate decimals."""
    if price is None:
        return "n/a"
    # Default: USD with 2 decimals
    symbol, decimals = "$", 2
    for suffix, (sym, dec) in _MARKET_PRICE_RULES.items():
        if quote_ticker.upper().endswith(suffix):
            symbol, decimals = sym, dec
            break
    # For large values, use comma separators
    if price >= 10_000:
        return f"{symbol}{price:,.{decimals}f}"
    return f"{symbol}{price:.{decimals}f}"


def _headline_link(item: NewsItem) -> str:
    if not item.url:
        return escape(item.title)
    return f'<a href="{escape(item.url)}">{escape(item.title)}</a>'


def _mover_explanation(entry: CoverageEntry, snapshot: dict[str, Any]) -> str:
    assessment = assess_snapshot(snapshot)
    if not assessment:
        return ""
    label = "重要异动" if assessment.is_important else "普通异动"
    return f"{label}——{entry.company} 今日触发 mover 阈值。"


def should_alert_intraday(entry: CoverageEntry, snapshot: dict[str, Any]) -> bool:
    if entry.monitor_status != "Core":
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


def _core_watch_sort_key(entry: CoverageEntry, snapshots: dict[str, dict[str, Any]]) -> tuple:
    """Core Watch: sort by |return| descending — most notable first."""
    move = _today_return(entry, snapshots)
    return (1 if move is None else 0, -abs(move or 0.0))


def render_daily_markdown(
    entries: list[CoverageEntry],
    snapshots: dict[str, dict[str, Any]],
    today: str,
    gaps: list[str],
    company_news: dict[str, list[NewsItem]] | None = None,
    industry_readthroughs: dict[str, list[NewsItem]] | None = None,
    mover_explainers: dict[str, ImportantMoverExplainer] | None = None,
    industry_summaries: dict[str, str] | None = None,
    industry_searches: dict[str, list[NewsItem]] | None = None,
    core_watch_summaries: dict[str, str] | None = None,
) -> str:
    grouped: dict[str, list[CoverageEntry]] = defaultdict(list)
    for entry in entries:
        grouped[entry.industry or "unclassified"].append(entry)
    company_news = company_news or {}
    industry_readthroughs = industry_readthroughs or {}
    mover_explainers = mover_explainers or {}
    industry_summaries = industry_summaries or {}
    industry_searches = industry_searches or {}
    core_watch_summaries = core_watch_summaries or {}
    core_entries = sorted(
        [e for e in entries if e.monitor_status == "Core"],
        key=lambda e: _core_watch_sort_key(e, snapshots),
    )
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
                f"- `{entry.ticker or entry.company}` {entry.company}: {move:+.2f}% | vol {volume}x | gap {gap:+.2f}%"
            )
            key = entry.ticker or entry.company
            if key in mover_explainers:
                explainer = mover_explainers[key]
                lines.append(f"  - {explainer.summary}")
                if explainer.evidence:
                    for ev in explainer.evidence[:8]:
                        lines.append(f"  - [{ev.title}]({ev.url})")
    else:
        lines.append("- No material movers in this run.")

    lines.extend(["", "## 3. Core Watch Company News"])
    for entry in core_entries:
        key = entry.ticker or entry.company
        items = company_news.get(key, [])
        move = _today_return(entry, snapshots)
        move_str = _format_today_return(move)
        status = quote_exception_status(snapshots.get(key, {}), report_day=today)
        status_dot = " ·" if status else ""
        summary = core_watch_summaries.get(key, "")
        if not items:
            lines.append(f"- `{key}` {entry.company} ({move_str}{status_dot}): no company news found.")
            continue
        lines.append(f"- `{key}` {entry.company} ({move_str}{status_dot}):")
        if summary:
            lines.append(f"  {summary}")
        for item in items[:6]:
            lines.append(f"  - [{item.title}]({item.url})")

    lines.extend(["", "## 4. Industry Read-Throughs"])
    for industry in sorted(grouped):
        summary = industry_summaries.get(industry, "")
        heading = f"### {industry}"
        if summary:
            heading += f" — {summary}"
        lines.append(heading)
        items = industry_readthroughs.get(industry, [])
        if items:
            # Group articles by source
            by_source: dict[str, list[NewsItem]] = {}
            for item in items:
                by_source.setdefault(item.source, []).append(item)
            for source_name, source_items in by_source.items():
                lines.append(f"- **{source_name}** ({len(source_items)} 篇):")
                for article in source_items[:5]:
                    date_str = f" ({article.published_at})" if article.published_at else ""
                    lines.append(f"  - [{article.title}]({article.url}){date_str}")
        search_items = industry_searches.get(industry, [])
        if search_items:
            lines.append(f"- **Web 搜索** ({len(search_items)} 条):")
            for si in search_items[:6]:
                date_str = f" ({si.published_at})" if si.published_at else ""
                lines.append(f"  - [{si.title}]({si.url}){date_str}")
        if not items and not search_items:
            lines.append("- 今日无行业 read-through 内容。")

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
            "| Ticker | Company | Industry | Today | 1m | YTD | 1y | Coverage | Monitor | Last Review | Next Trigger |",
            "|---|---|---|---|---|---|---|---|---|---|---|",
        ]
    )
    for entry in sorted(entries, key=lambda item: _universe_sort_key(item, snapshots)):
        key = entry.ticker or entry.company
        status = quote_exception_status(snapshots.get(key, {}), report_day=today)
        status_dot = " ·" if status else ""
        s = snapshots.get(entry.ticker or entry.company, {})
        ret_1m = _format_today_return(s.get("ret_1m")).replace("%","") if s.get("ret_1m") is not None else "—"
        ret_ytd = _format_today_return(s.get("ret_ytd")).replace("%","") if s.get("ret_ytd") is not None else "—"
        ret_1y = _format_today_return(s.get("ret_1y")).replace("%","") if s.get("ret_1y") is not None else "—"
        lines.append(
            f"| {entry.ticker or ''}{status_dot} | {entry.company} | {entry.industry} | {_format_today_return(_today_return(entry, snapshots))} | {ret_1m} | {ret_ytd} | {ret_1y} | {entry.coverage_status} | {entry.monitor_status} | {entry.last_review} | {entry.next_trigger} |"
        )
    return "\n".join(lines) + "\n"


def render_email_body(
    entries: list[CoverageEntry],
    snapshots: dict[str, dict[str, Any]],
    today: str,
    mover_explainers: dict[str, ImportantMoverExplainer] | None = None,
    core_watch_summaries: dict[str, str] | None = None,
    industry_summaries: dict[str, str] | None = None,
    gaps: list[str] | None = None,
    review_map: dict[str, dict] | None = None,
    news_map: dict[str, list] | None = None,
) -> str:
    """Plain-text email body — movers(归因原因) + upcoming earnings + Core Watch(lead news) + industries."""
    mover_explainers = mover_explainers or {}
    core_watch_summaries = core_watch_summaries or {}
    industry_summaries = industry_summaries or {}
    review_map = review_map or {}
    news_map = news_map or {}

    movers = _mover_entries(entries, snapshots)
    core_entries = sorted(
        [e for e in entries if e.monitor_status == "Core"],
        key=lambda e: _core_watch_sort_key(e, snapshots),
    )
    grouped: dict[str, list[CoverageEntry]] = defaultdict(list)
    for entry in entries:
        grouped[entry.industry or "unclassified"].append(entry)

    lines = [f"Daily Coverage Brief — {today}", ""]

    # All movers with full explanation + 1 evidence link
    if movers:
        lines.append(f"━━━ Price Movers ({len(movers)}) ━━━")
        for entry, _snapshot, _assessment in movers:
            move = _today_return(entry, snapshots)
            ticker = entry.ticker or entry.company
            expl = review_map.get(ticker) or mover_explainers.get(ticker)
            lines.append(f"{ticker} {_display_name(entry)} {_format_today_return(move)}")
            if isinstance(expl, dict):
                lines.append(f"  {expl.get('summary', '')}")
                for l in (expl.get("links") or [])[:2]:
                    _lt = translate_zh(l.get("title", ""))
                    _lu = l.get("url", "")
                    lines.append(f"  -> [{_lt}]({_lu})" if _lu else f"  -> {_lt}")
            elif expl:
                lines.append(f"  {expl.summary}")
                if expl.evidence:
                    ev = expl.evidence[0]
                    lines.append(f"  -> {ev.title} ({ev.url})")
            lines.append("")

    # Upcoming Earnings (next 7 days)
    earn = []
    for e in entries:
        nd = (snapshots.get(e.ticker or e.company, {}) or {}).get("next_earnings")
        if not nd:
            continue
        try:
            _d = (date.fromisoformat(str(nd)) - date.fromisoformat(str(today))).days
            if 0 <= _d <= 7:
                earn.append((_d, str(nd), e))
        except Exception:
            continue
    if earn:
        lines.append(f"━━━ Upcoming Earnings (next 7 days) ━━━")
        for _d, nd, e in sorted(earn, key=lambda x: (x[0], x[1])):
            lines.append(f"{e.ticker or e.company} {_display_name(e)} — {nd} ({_d}d)")
        lines.append("")

    # All Core Watch with lead news（news_map 实时，非 enrichment）
    if core_entries:
        lines.append(f"━━━ Core Watch ({len(core_entries)}) ━━━")
        for entry in core_entries:
            move = _today_return(entry, snapshots)
            ticker = entry.ticker or entry.company
            lines.append(f"{ticker} {_display_name(entry)} {_format_today_return(move)}")
            items = news_map.get(ticker, [])
            if items:
                _lead = pick_lead_news(items)
                _t = translate_zh(_lead.title) if getattr(_lead, "title", "") else ""
                _lu = getattr(_lead, "url", "") or ""
                lines.append(f"  📰 [{_t}]({_lu})" if _lu else f"  📰 {_t}")
            lines.append("")

    # All industries with full summaries
    if industry_summaries:
        lines.append(f"━━━ Industry ({len(industry_summaries)}) ━━━")
        for industry in sorted(grouped):
            s = industry_summaries.get(industry, "")
            if s:
                lines.append(f"{industry}")
                lines.append(f"  {s}")
                lines.append("")

    lines.append("Full dashboard HTML attached.")
    return "\n".join(lines)


def render_email_body_html(
    entries: list[CoverageEntry],
    snapshots: dict[str, dict[str, Any]],
    today: str,
    mover_explainers: dict[str, ImportantMoverExplainer] | None = None,
    core_watch_summaries: dict[str, str] | None = None,
    industry_summaries: dict[str, str] | None = None,
    gaps: list[str] | None = None,
    review_map: dict[str, dict] | None = None,
    news_map: dict[str, list] | None = None,
) -> str:
    """HTML email body — 链接用 <a href>（邮件客户端渲染成文字链接，非裸 URL）。"""
    from html import escape as _esc

    mover_explainers = mover_explainers or {}
    core_watch_summaries = core_watch_summaries or {}
    industry_summaries = industry_summaries or {}
    review_map = review_map or {}
    news_map = news_map or {}

    movers = _mover_entries(entries, snapshots)
    core_entries = sorted(
        [e for e in entries if e.monitor_status == "Core"],
        key=lambda e: _core_watch_sort_key(e, snapshots),
    )
    grouped: dict[str, list[CoverageEntry]] = defaultdict(list)
    for entry in entries:
        grouped[entry.industry or "unclassified"].append(entry)

    out: list[str] = []
    out.append(f"<b>Daily Coverage Brief — {_esc(today)}</b>")

    if movers:
        out.append("<br><b>━━━ Price Movers (" + str(len(movers)) + ") ━━━</b>")
        for entry, _snapshot, _assessment in movers:
            move = _today_return(entry, snapshots)
            ticker = entry.ticker or entry.company
            expl = review_map.get(ticker) or mover_explainers.get(ticker)
            out.append(f"{_esc(ticker)} {_esc(_display_name(entry))} {_format_today_return(move)}")
            if isinstance(expl, dict):
                out.append("&nbsp;&nbsp;" + _esc(expl.get("summary", "")))
                for l in (expl.get("links") or [])[:2]:
                    _lt = translate_zh(l.get("title", ""))
                    _lu = l.get("url", "")
                    if _lu:
                        out.append(f"&nbsp;&nbsp;<a href=\"{_esc(_lu)}\">{_esc(_lt)}</a>")
            elif expl:
                out.append("&nbsp;&nbsp;" + _esc(expl.summary))
                if expl.evidence:
                    ev = expl.evidence[0]
                    out.append(f"&nbsp;&nbsp;<a href=\"{_esc(ev.url)}\">{_esc(ev.title)}</a>")
            out.append("<br>")  # 每家后空行分隔

    earn = []
    for e in entries:
        nd = (snapshots.get(e.ticker or e.company, {}) or {}).get("next_earnings")
        if not nd:
            continue
        try:
            _d = (date.fromisoformat(str(nd)) - date.fromisoformat(str(today))).days
            if 0 <= _d <= 7:
                earn.append((_d, str(nd), e))
        except Exception:
            continue
    if earn:
        out.append("<br><b>━━━ Upcoming Earnings (next 7 days) ━━━</b>")
        for _d, nd, e in sorted(earn, key=lambda x: (x[0], x[1])):
            out.append(f"{_esc(e.ticker or e.company)} {_esc(_display_name(e))} — {_esc(nd)} ({_d}d)")

    if core_entries:
        out.append("<br><b>━━━ Core Watch (" + str(len(core_entries)) + ") ━━━</b>")
        for entry in core_entries:
            move = _today_return(entry, snapshots)
            ticker = entry.ticker or entry.company
            _vrow = (snapshots.get(ticker, {}) or {}).get("valuation") or {}
            _r = []
            for _lbl, _f in (("1m", "ret_1m"), ("YTD", "ret_ytd"), ("1y", "ret_1y")):
                _v = _vrow.get(_f)
                if _v is not None:
                    _r.append(f"{_lbl} {_format_today_return(_v)}")
            _val = []
            if _vrow.get("pe_ntm"):
                _val.append(f"PE_NTM {_vrow['pe_ntm']}x")
            if _vrow.get("ev_ntm"):
                _val.append(f"EV/EBITDA_NTM {_vrow['ev_ntm']}x")
            _tail = (" | " + " ".join(_r)) if _r else ""
            _val_s = (" | " + " ".join(_val)) if _val else ""
            out.append(f"{_esc(ticker)} {_esc(_display_name(entry))} {_format_today_return(move)}{_esc(_tail)}{_esc(_val_s)}")
            items = news_map.get(ticker, [])
            if items:
                _lead = pick_lead_news(items)
                _t = translate_zh(_lead.title) if getattr(_lead, "title", "") else ""
                _lu = getattr(_lead, "url", "") or ""
                if _lu:
                    out.append(f"&nbsp;&nbsp;📰 <a href=\"{_esc(_lu)}\">{_esc(_t)}</a>")
                else:
                    out.append("&nbsp;&nbsp;📰 " + _esc(_t))
            out.append("<br>")  # 每家公司后空行分隔

    if industry_summaries:
        out.append("<br><b>━━━ Industry (" + str(len(industry_summaries)) + ") ━━━</b>")
        for industry in sorted(grouped):
            s = industry_summaries.get(industry, "")
            if s:
                out.append(f"<b>{_esc(industry)}</b><br>&nbsp;&nbsp;{_esc(s)}")

    out.append("<br>Full dashboard HTML attached.")
    return "<div style='font-family:-apple-system,Segoe UI,Noto Sans SC,sans-serif;font-size:13px;line-height:1.7'>" + "<br>".join(out) + "</div>"


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
    mover_explainers: dict[str, ImportantMoverExplainer] | None = None,
    industry_summaries: dict[str, str] | None = None,
    industry_searches: dict[str, list[NewsItem]] | None = None,
    core_watch_summaries: dict[str, str] | None = None,
) -> str:
    company_news = company_news or {}
    industry_readthroughs = industry_readthroughs or {}
    mover_explainers = mover_explainers or {}
    industry_summaries = industry_summaries or {}
    industry_searches = industry_searches or {}
    core_watch_summaries = core_watch_summaries or {}
    core_entries = sorted(
        [e for e in entries if e.monitor_status == "Core"],
        key=lambda e: _core_watch_sort_key(e, snapshots),
    )
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
        explainer = mover_explainers.get(key)
        source_names: list[str] = []
        evidence_items: list[NewsItem] = []
        if explainer:
            seen_evidence: set[tuple[str, str]] = set()
            for item in [*explainer.evidence, *explainer.filings_evidence]:
                dedupe_key = ((item.url or "").strip(), item.title.strip())
                if dedupe_key in seen_evidence:
                    continue
                seen_evidence.add(dedupe_key)
                evidence_items.append(item)
                if item.source:
                    source_names.append(item.source)
            body_text = explainer.summary
        else:
            fallback_news = company_news.get(key, [])
            evidence_items.extend(fallback_news[:8])
            for item in fallback_news[:8]:
                if item.source:
                    source_names.append(item.source)
            body_text = _mover_explanation(entry, snapshot) or "未抓到足够直接证据，保留到后续补查。"

        evidence_html = "".join(
            f"<li>{_headline_link(item)}<span> · {escape(item.source or 'source')}</span></li>" for item in evidence_items
        ) or "<li>No direct company evidence collected.</li>"
        source_line = ""
        unique_sources = [name for name in dict.fromkeys(source_names) if name]
        if unique_sources:
            source_line = f'<div class="source-inline">Sources · {escape("、".join(unique_sources[:6]))}</div>'

        m_price = _format_price(snapshot.get("quote_ticker", ""), _float_metric(snapshot, "last_price"))
        m_cap = snapshot.get("market_cap")
        m_pe = snapshot.get("pe_trailing")
        primary_name_html = _company_identity_html(entry, extra_class="company-name")
        snapshot_tiles = [
            f'<div class="snapshot-item"><b>{escape(m_price)}</b><span>Price</span></div>',
            f'<div class="snapshot-item"><b>{escape(_format_cap(m_cap) if m_cap else "n/a")}</b><span>Cap</span></div>',
            f'<div class="snapshot-item"><b>{escape(f"{m_pe:.1f}x" if m_pe is not None else "n/a")}</b><span>PE</span></div>',
            f'<div class="snapshot-item"><b>{escape(_format_metric(volume, "x", digits=2))}</b><span>Vol</span></div>',
            f'<div class="snapshot-item"><b>{escape(_format_metric(gap, "%", digits=2))}</b><span>Gap</span></div>',
            _metric_ret(snapshot, "ret_1m", "1m"),
            _metric_ret(snapshot, "ret_ytd", "YTD"),
            _metric_ret(snapshot, "ret_1y", "1y"),
        ]
        mover_cards.append(
            f"""
            <article class="coverage-card mover-card {'important' if assessment.is_important else ''}" data-market="{escape(_market_label(entry))}" data-industry="{escape(entry.industry)}" data-return="{escape(str(move or 0.0))}">
              <div class="identity-bar">
                <div class="identity-copy">
                  <div class="ticker-line">
                    <span class="ticker">{escape(entry.ticker or entry.company)}</span>
                  </div>
                  <div class="company-line">{primary_name_html} · {escape(entry.industry)} · <span class="pill coverage {escape(_coverage_slug(entry.coverage_status))}">{escape(entry.coverage_status)}</span> <span class="pill monitor {escape(_monitor_slug(entry.monitor_status))}">{escape(entry.monitor_status)}</span></div>
                </div>
                <div class="day-return-pill {ret_class}">{escape(_format_today_return(move))}</div>
              </div>
              <div class="card-body">
                <div class="fact-rail">
                  <div class="rail-group">
                    <div class="rail-label">Market Snapshot</div>
                    <div class="snapshot-grid">{''.join(snapshot_tiles)}</div>
                  </div>
                </div>
                <div class="detail-body">
                  <div class="rail-label">Why It Moved</div>
                  <p class="body-copy">{escape(body_text)}</p>
                  {source_line}
                  <details class="evidence-box">
                    <summary>Evidence ({len(evidence_items)})</summary>
                    <ul>{evidence_html}</ul>
                  </details>
                </div>
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
            for item in news_items[:10]
        ) or "<li>No company news found in this run.</li>"
        s = snapshots.get(key, {})
        ret_class = _return_class(_today_return(entry, snapshots))
        status = quote_exception_status(s, report_day=today)
        status_dot = ' <span class="status-dot" title="Quote: ' + escape(status) + '"></span>' if status else ""
        stock_summary = core_watch_summaries.get(key, "")
        summary_line = f'<p class=\"body-copy\">{escape(stock_summary)}</p>' if stock_summary else ""
        primary_name_html = _company_identity_html(entry, extra_class="core-company")
        price_str = _format_price(s.get("quote_ticker", ""), s.get("last_price"))
        cap = s.get("market_cap")
        pe = s.get("pe_trailing")
        quote_status_line = f'<div class="status-line">Quote status: {escape(status)}</div>' if status else ""
        quote_blocks = [
            f'<div class="core-quote-item"><span>Price</span><b>{escape(price_str)}</b></div>',
            f'<div class="core-quote-item"><span>Cap</span><b>{escape(_format_cap(cap) if cap else "n/a")}</b></div>',
            f'<div class="core-quote-item"><span>PE</span><b>{escape(f"{pe:.1f}x" if pe is not None else "n/a")}</b></div>',
        ]
        return_blocks = []
        for rk, rl in [("ret_1m", "1m"), ("ret_ytd", "YTD"), ("ret_1y", "1y")]:
            v = s.get(rk)
            c = "na" if v is None else ("pos" if v >= 0 else "neg")
            value = "—" if v is None else f"{v:+.1f}%"
            return_blocks.append(f'<div class="return-cell {c}"><span>{rl}</span><b>{escape(value)}</b></div>')

        core_cards.append(
            f"""
            <article class="core-watch-card">
              <div class="core-head">
                <div>
                  <div class="core-ticker-line">
                    <span class="core-ticker">{escape(entry.ticker or entry.company)}</span>
                    <span class="core-return {escape(ret_class)}">{escape(_format_today_return(_today_return(entry, snapshots)))}</span>
                  </div>
                  <div class="core-company-line">{primary_name_html} · {escape(entry.industry)}{status_dot}</div>
                </div>
              </div>
              <div class="core-quote-grid">{''.join(quote_blocks)}</div>
              <div class="return-strip">{''.join(return_blocks)}</div>
              {summary_line}
              {quote_status_line}
              <details><summary>News ({len(news_items)})</summary><ul>{news_html}</ul></details>
            </article>
            """
        )

    industry_sections: list[str] = []
    for industry in industry_list:
        items = industry_readthroughs.get(industry, [])
        linked_names = ", ".join(entry.company for entry in sorted(grouped[industry], key=lambda item: _universe_sort_key(item, snapshots))[:8])
        # Group by source
        by_source: dict[str, list[NewsItem]] = {}
        for item in items:
            by_source.setdefault(item.source, []).append(item)
        sources_html_parts: list[str] = []
        for source_name, source_items in by_source.items():
            article_html = "".join(
                f"""<div class="source-line">
                  <b><a href="{escape(a.url)}">{escape(a.title)}</a></b>
                  <span>{'· ' + escape(a.published_at) if a.published_at else ''}</span>
                </div>"""
                for a in source_items[:5]
            )
            sources_html_parts.append(
                f'<details class="source-group"><summary>{escape(source_name)} ({len(source_items)} 篇)</summary>{article_html}</details>'
            )
        sources_html = "".join(sources_html_parts[:20]) if sources_html_parts else ""
        # Add WebSearch results
        search_items = industry_searches.get(industry, [])
        if search_items:
            search_html = "".join(
                f"""<div class="source-line search-result">
                  <b><a href="{escape(si.url)}">{escape(si.title)}</a></b>
                  <span>Web · {escape(si.source or '')} {'· ' + escape(si.published_at) if si.published_at else ''}</span>
                </div>"""
                for si in search_items[:8]
            )
            sources_html += f'<details><summary>Web 搜索 ({len(search_items)} 条)</summary>{search_html}</details>'
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
                <p class="body-copy">{escape(industry_summaries.get(industry) or "")}</p>
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
        status_html = f' <span class="status-dot" title="Quote: {escape(status)}"></span>' if status else ""
        trigger = entry.next_trigger or ""
        ret_snapshot = snapshots.get(entry.ticker or entry.company, {})
        def _ret_td(key: str) -> str:
            v = ret_snapshot.get(key)
            if v is None: return "<td class=\"ret na\">—</td>"
            c = "pos" if v >= 0 else "neg"
            dec = 2 if key == "price_move_pct" else 1
            return f"<td class=\"ret {c}\">{v:+.{dec}f}%</td>"
        universe_rows.append(
            f"""
            <tr data-industry="{escape(entry.industry)}" data-coverage="{escape(_coverage_slug(entry.coverage_status))}" data-monitor="{escape(_monitor_slug(entry.monitor_status))}">
              <td>{escape(entry.ticker or '')}{status_html}</td>
              <td>{escape(entry.company)}</td>
              <td>{escape(entry.industry)}</td>
              {_ret_td("price_move_pct")}
              {_ret_td("ret_1m")}
              {_ret_td("ret_ytd")}
              {_ret_td("ret_1y")}
              <td class="narrow">{escape(entry.coverage_status)}</td>
              <td class="narrow">{escape(entry.monitor_status)}</td>
              <td class="narrow">{escape(entry.last_review)}</td>
              <td>{escape(trigger)}</td>
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
  display: flex;
  align-items: center;
  gap: 12px;
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 8px 16px;
  background: rgba(255,255,255,.88);
  box-shadow: 0 4px 12px rgba(15,23,42,.06);
  font-size: 13px;
  flex-wrap: wrap;
}}
.hero-date {{ color: var(--muted); font-weight: 700; margin-right: auto; }}
.hero-stat {{ color: var(--ink); font-weight: 800; font-variant-numeric: tabular-nums; }}
.eyebrow {{
  color: var(--blue);
  letter-spacing: .16em;
  text-transform: uppercase;
  font-size: 12px;
  font-weight: 900;
}}
h1 {{ display: none; }}
h2 {{ margin: 0; font-size: 18px; letter-spacing: -.03em; }}
h3 {{ margin: 8px 0 2px; font-size: 20px; letter-spacing: -.04em; }}
.subtitle {{ display: none; }}
.tab-nav {{
  position: sticky;
  top: 0;
  z-index: 20;
  margin: 18px 0 32px;
  display: flex;
  gap: 12px;
  padding: 8px 10px;
  border: 1px solid var(--line);
  border-radius: 16px;
  background: rgba(255,255,255,.92);
  backdrop-filter: blur(18px);
  box-shadow: 0 4px 16px rgba(15,23,42,.06);
  overflow-x: auto;
}}
.tab-panel {{ scroll-margin-top: 80px; }}
.tab-button {{
  display: inline-block;
  border-radius: 12px;
  padding: 8px 14px;
  color: var(--muted);
  font-weight: 800;
  font-size: 13px;
  text-decoration: none;
  white-space: nowrap;
}}
.tab-button:hover {{ background: rgba(19,34,56,.06); color: var(--ink); }}
.section-head {{
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 18px;
  margin: 18px 2px 12px;
}}
.section-head p {{ margin: 6px 0 0; max-width: 840px; color: var(--muted); line-height: 1.68; }}
.grid-2 {{ display: grid; grid-template-columns: repeat(2,minmax(0,1fr)); gap: 14px; }}
.stack {{ display: grid; gap: 14px; }}
.card {{
  border: 1px solid var(--line);
  border-radius: 24px;
  background: var(--card);
  box-shadow: 0 14px 44px rgba(15,23,42,.08);
  padding: 18px;
}}
.coverage-card {{
  overflow: hidden;
  border: 1px solid var(--line);
  border-left: 4px solid rgba(37,99,235,.35);
  border-radius: 24px;
  background: rgba(255,255,255,.94);
  box-shadow: 0 18px 52px rgba(15,23,42,.09);
}}
.coverage-card.mover-card {{ margin-bottom: 14px; }}
.coverage-card.important {{ border-left-color: var(--amber); }}
.identity-bar {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  padding: 18px 22px;
  border-bottom: 1px solid var(--line);
  background: linear-gradient(90deg, rgba(37,99,235,.08), rgba(255,255,255,.96) 54%);
}}
.coverage-card.important .identity-bar {{
  background: linear-gradient(90deg, rgba(183,121,31,.12), rgba(255,255,255,.96) 54%);
}}
.ticker-line {{
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 10px 14px;
}}
.ticker {{
  font-size: 34px;
  font-weight: 950;
  letter-spacing: -.055em;
  line-height: 1;
}}
.company-name {{
  color: var(--ink);
  font-size: 18px;
  font-weight: 780;
  letter-spacing: -.02em;
}}
.company-en {{
  color: var(--muted);
  font-size: .84em;
  font-weight: 650;
}}
.company-en::before {{
  content: "·";
  margin: 0 7px;
  color: var(--muted);
}}
.industry-line {{
  margin-top: 4px;
  color: var(--muted);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: .04em;
}}
.day-return-pill {{
  min-width: 116px;
  border-radius: 14px;
  padding: 10px 14px;
  text-align: center;
  font-size: 28px;
  font-weight: 900;
  letter-spacing: -.05em;
}}
.day-return-pill.pos {{ color: var(--green); background: var(--green-soft); }}
.day-return-pill.neg {{ color: var(--red); background: var(--red-soft); }}
.day-return-pill.na {{ color: var(--muted); background: rgba(226,232,240,.55); }}
.card-body {{
  display: grid;
  grid-template-columns: 330px minmax(0,1fr);
}}
.fact-rail {{
  display: grid;
  gap: 10px;
  padding: 12px 14px;
  border-right: 1px solid var(--line);
  background: rgba(248,250,252,.68);
}}
.rail-group {{ display: grid; gap: 8px; }}
.rail-label {{
  color: var(--muted);
  font-size: 11px;
  font-weight: 900;
  letter-spacing: .12em;
  text-transform: uppercase;
}}
.snapshot-grid {{
  display: grid;
  grid-template-columns: repeat(4,minmax(0,1fr));
  gap: 6px;
}}
.snapshot-item {{
  border: 1px solid var(--line);
  border-radius: 12px;
  background: rgba(255,255,255,.86);
  padding: 7px 9px;
}}
.snapshot-item b {{
  display: block;
  font-size: 13px;
  line-height: 1.2;
}}
.snapshot-item span {{
  display: block;
  margin-top: 2px;
  color: var(--muted);
  font-size: 10px;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: .06em;
}}
.detail-body {{
  display: grid;
  gap: 8px;
  padding: 14px 18px;
}}
.tag-row {{
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}}
.tag-chip {{
  display: inline-flex;
  align-items: center;
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(248,250,252,.94);
  border: 1px solid var(--line);
  color: #334155;
  font-size: 11px;
  font-weight: 850;
}}
.source-inline {{
  color: var(--muted);
  font-size: 13px;
}}
.evidence-box {{ margin-top: 0; }}
.ret.pos, .ret.neg {{ font-weight: 600; }}
.ret.pos {{ color: var(--green); background: var(--green-soft); }}
.ret.neg {{ color: var(--red); background: var(--red-soft); }}
.ret.na {{ color: var(--muted); font-weight: 400; }}
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
.chip-row {{ display: flex; flex-wrap: wrap; gap: 8px; margin-top: 6px; }}
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
.pill.trigger {{ background: rgba(255,255,255,.82); color: #334155; }}
.pill.status {{ background: rgba(248,250,252,.9); color: #475569; margin-left: 6px; }}
.status-dot {{
  display: inline-block;
  width: 6px; height: 6px;
  border-radius: 50%;
  background: var(--amber);
  margin-left: 3px;
  vertical-align: middle;
  cursor: help;
}}
.core-watch-card {{
  border: 1px solid var(--line);
  border-radius: 24px;
  background: rgba(255,255,255,.94);
  box-shadow: 0 14px 44px rgba(15,23,42,.08);
  padding: 18px;
}}
.core-ticker-line {{
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 14px;
}}
.core-ticker {{
  font-size: 24px;
  font-weight: 950;
  letter-spacing: -.045em;
}}
.core-return {{
  font-size: 18px;
  font-weight: 900;
  letter-spacing: -.04em;
}}
.core-return.pos {{ color: var(--green); }}
.core-return.neg {{ color: var(--red); }}
.core-return.na {{ color: var(--muted); }}
.core-company-line {{
  margin-top: 4px;
  color: var(--ink);
  font-size: 16px;
  font-weight: 760;
}}
.core-industry {{
  margin-top: 2px;
  color: var(--muted);
  font-size: 12px;
}}
.core-quote-grid {{
  display: grid;
  grid-template-columns: repeat(3,minmax(0,1fr));
  gap: 8px;
  margin-top: 12px;
}}
.core-quote-item {{
  border: 1px solid var(--line);
  border-radius: 14px;
  background: rgba(248,250,252,.8);
  padding: 10px 11px;
}}
.core-quote-item span {{
  display: block;
  color: var(--muted);
  font-size: 11px;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: .06em;
}}
.core-quote-item b {{
  display: block;
  margin-top: 4px;
  font-size: 15px;
}}
.coverage-row {{ margin-top: 10px; }}
.return-strip {{
  display: grid;
  grid-template-columns: repeat(3,minmax(0,1fr));
  gap: 8px;
  margin: 10px 0 12px;
}}
.return-cell {{
  border-radius: 14px;
  border: 1px solid var(--line);
  background: rgba(248,250,252,.8);
  padding: 10px 11px;
}}
.return-cell span {{
  display: block;
  color: var(--muted);
  font-size: 11px;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: .06em;
}}
.return-cell b {{
  display: block;
  margin-top: 4px;
  font-size: 14px;
}}
.return-cell.pos b {{ color: var(--green); }}
.return-cell.neg b {{ color: var(--red); }}
.return-cell.na b {{ color: var(--muted); }}
.status-line {{ color: var(--muted); font-size: 13px; margin: 0 0 10px; }}
.table-card {{
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  border: 1px solid var(--line);
  border-radius: 24px;
  background: var(--card);
  box-shadow: 0 14px 44px rgba(15,23,42,.07);
}}
.table-card table {{ min-width: 900px; width: 100%; border-collapse: collapse; font-size: 12px; }}
th, td {{
  padding: 3px 5px;
  border-bottom: 1px solid rgba(148,163,184,.18);
  text-align: left;
  vertical-align: middle;
  height: 28px;
}}
th {{
  color: var(--muted);
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: .06em;
  background: rgba(248,250,252,.82);
}}
td:first-child, th:first-child {{ padding-left: 12px; }}  /* Ticker — clear card border radius */
td:nth-child(1) {{ white-space: nowrap; }}       /* Ticker */
td:nth-child(4) {{ white-space: nowrap; }}       /* Return */
td:nth-child(8) {{ white-space: normal; word-break: break-word; }}
tr:last-child td {{ border-bottom: 0; }}
.gaps-footer {{
  margin: 20px 0 8px;
  font-size: 12px;
  color: var(--muted);
}}
.gaps-footer summary {{
  cursor: pointer;
  color: var(--slate);
  font-weight: 700;
}}
.gaps-footer ul {{ margin: 8px 0 0; padding-left: 18px; font-size: 12px; }}
#universeTable tr[data-coverage="core"] td:nth-child(8) {{ color: #1d4ed8; font-weight: 950; }}
#universeTable tr[data-coverage="building"] td:nth-child(8) {{ color: var(--amber); font-weight: 950; }}
#universeTable tr[data-coverage="radar"] td:nth-child(8) {{ color: var(--slate); font-weight: 950; }}
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
  .grid-2 {{ grid-template-columns: 1fr; }}
  .card-body, .industry-card {{ grid-template-columns: 1fr; }}
  .fact-rail {{ border-right: 0; border-bottom: 1px solid var(--line); }}
}}
@media (max-width: 720px) {{
  .identity-bar {{ flex-direction: column; align-items: flex-start; }}
  .day-return-pill {{ min-width: 0; }}
  .snapshot-grid {{ grid-template-columns: repeat(2,minmax(0,1fr)); }}
}}
@media (max-width: 520px) {{
  .core-quote-grid, .return-strip {{ grid-template-columns: 1fr; }}
}}
</style>
</head>
<body>
<main>
  <section class="hero">
    <span class="eyebrow">Coverage Monitor</span>
    <span class="hero-date">{escape(today)}</span>
    <span class="hero-stat">{len(entries)} names</span>
    <span class="hero-stat">{len(movers)} movers</span>
    <span class="hero-stat">{len(core_entries)} Core Watch</span>
    <span class="hero-stat">{len(gaps)} gaps</span>
  </section>

  <nav class="tab-nav" aria-label="Dashboard tabs">
    <a class="tab-button" href="#movers">Movers</a>
    <a class="tab-button" href="#core">Core Watch</a>
    <a class="tab-button" href="#industry">Industry Tape</a>
    <a class="tab-button" href="#universe">Universe</a>
  </nav>

  <section id="movers" class="tab-panel">
    <div class="section-head">
      <div>
        <h2>Movers</h2>
      </div>
    </div>
    {''.join(mover_cards) or '<article class="card">No material movers in this run.</article>'}
  </section>

  <section id="core" class="tab-panel">
    <div class="section-head">
      <div>
        <h2>Core Watch</h2>
      </div>
    </div>
    <div class="grid-2">{''.join(core_cards) or '<article class="card">No Core Watch companies registered.</article>'}</div>
  </section>

  <section id="industry" class="tab-panel">
    <div class="section-head">
      <div>
        <h2>Industry Tape</h2>
      </div>
    </div>
    <div class="stack">{''.join(industry_sections) or '<article class="card">No industry read-through source configured.</article>'}</div>
  </section>

  <section id="universe" class="tab-panel">
    <div class="section-head">
      <div>
        <h2>Universe</h2>
      </div>
    </div>
    <div class="table-card">
      <table id="universeTable">
        <thead><tr><th>Ticker</th><th>Company</th><th>Industry</th><th>Today</th><th>1m</th><th>YTD</th><th>1y</th><th>Coverage</th><th>Monitor</th><th>Last Review</th><th>Next Trigger</th></tr></thead>
        <tbody>{''.join(universe_rows)}</tbody>
      </table>
    </div>
  </section>
  <section class="gaps-footer">
    <details><summary>Coverage Gaps ({len(gaps)})</summary><ul>{gap_items}</ul></details>
  </section>
</main>
</body>
</html>"""
