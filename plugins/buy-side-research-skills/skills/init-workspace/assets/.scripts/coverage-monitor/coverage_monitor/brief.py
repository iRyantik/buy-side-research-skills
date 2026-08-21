"""日报 5 区块渲染（盘前 am 全量 / 亚盘 asia / 欧盘 eu）。

区块：① Review Queue ② 估值表 ③ Movers ④ Core Watch ⑤ Data Health。
数据全部来自 FMP（行情/涨跌/估值/财报日/news），snapshot 里已含估值原料。
"""

from __future__ import annotations

import datetime
import re
from typing import Any

from .coverage import CoverageEntry
from .news import pick_lead_news, protect_names, tag_news_title, translate_zh
from .valuation import fmt_cell, fwd_extra, rich_class

# 市场 → report_type 归属
_MARKET_OF = {
    ".SZ": "asia", ".SH": "asia", ".CN": "asia", ".T": "asia", ".JP": "asia",
    ".KS": "asia", ".KQ": "asia", ".TW": "asia", ".TT": "asia", ".HK": "asia",
    ".DE": "eu", ".MI": "eu", ".MC": "eu", ".LN": "eu", ".FR": "eu",
    ".L": "eu", ".HE": "eu", ".PA": "eu", ".ST": "eu", ".OL": "eu",
    ".AS": "eu", ".KL": "eu", ".MY": "eu", ".NS": "eu", ".AX": "eu",
    ".CA": "eu", ".TO": "eu",
    ".SS": "asia", ".US": "us", "": "us",
}


def _market_of(ticker: str) -> str:
    for suffix, mkt in _MARKET_OF.items():
        if suffix and ticker.endswith(suffix):
            return mkt
    return "us"


def filter_entries(entries: list[CoverageEntry], report_type: str) -> list[CoverageEntry]:
    """am 全量；asia 只亚盘；eu 只欧股。"""
    if report_type == "am":
        return entries
    return [e for e in entries if _market_of(e.ticker or "") == report_type]


_ZH_SUFFIXES = (".SS", ".SZ", ".SH", ".HK", ".TW", ".TT", ".CN")


def _fwd_ntm_pe(snap: dict, estimates: dict | None, ticker: str) -> float | None:
    """L1 forward EPS → PE_NTM（price ÷ forward.eps）；无 forward/eps 返回 None。

    调用方 fallback 到现有 vrow.pe_ntm（已是 consensus epsAvg 口径）。"""
    fwd = None
    if estimates:
        fwd = (estimates.get(ticker) or {}).get("forward")
    eps = (fwd or {}).get("metrics", {}).get("eps") if fwd else None
    price = snap.get("last_price")
    if not eps or not price:
        return None
    try:
        return round(float(price) / float(eps), 1)
    except (TypeError, ValueError, ZeroDivisionError):
        return None


def _display_name(entry: CoverageEntry) -> str:
    """中文市场（CN/HK/TW）显示中文名；其他市场显示 EN 名。

    不能用"含汉字"判断——日文公司名（ニッポン高度紙工業、三井化学）也是汉字，
    会误当中文。按 ticker 市场后缀 + 多 ticker 的 CH/HK 标记判定。
    """
    t = (entry.ticker or "").strip().upper()
    zh = any(t.endswith(s) for s in _ZH_SUFFIXES) or " CH " in f" {t} " or " HK " in f" {t} "
    if zh:
        return (entry.company_native or "").strip() or entry.company or t
    return entry.company or t


_STATUS_ORDER = {"Thesis": 0, "Modeled": 1, "Quickread": 2, "Screened": 3, "Terminated": 4}


def _health_summary(gaps: list[str]) -> str:
    """Data Health 一行汇总：按类别统计 gap。"""
    n_quote = sum(1 for g in gaps if "quote" in g.lower() or "no data" in g.lower())
    n_news = sum(1 for g in gaps if "news" in g.lower())
    n_val = sum(1 for g in gaps if any(k in g.lower() for k in ("estimates", "valuation", "consensus", "key_metrics", "ratios")))
    parts = []
    if n_quote:
        parts.append(f"{n_quote} 家行情拉不到")
    if n_news:
        parts.append(f"{n_news} 家无新闻")
    if n_val:
        parts.append(f"{n_val} 家缺估值/consensus")
    return " · ".join(parts) if parts else "数据完整"


def _universe_sorted(entries: list[CoverageEntry],
                     snapshots: dict[str, dict[str, Any]]) -> list[CoverageEntry]:
    """估值表排序：行业 → Status 核心到边缘 → Today/1m/YTD/1y 降序（先涨后跌，同则比更右列）
    → 估值升序（PE_NTM 正数小到大，无/负垫底）→ next call 从近到远。"""
    def _num(v: Any) -> float:
        try:
            f = float(v)
            return f if f == f else 0.0  # NaN → 0
        except (TypeError, ValueError):
            return 0.0

    def _key(e: CoverageEntry) -> tuple:
        snap = snapshots.get(e.ticker or e.company, {})
        vrow = snap.get("valuation") or {}
        st = _STATUS_ORDER.get((e.coverage_status or "").strip(), 9)
        today = _num(snap.get("price_move_pct"))
        r1m, rytd, r1y = _num(vrow.get("ret_1m")), _num(vrow.get("ret_ytd")), _num(vrow.get("ret_1y"))
        val = _num(vrow.get("pe_ntm"))
        val_key = val if val > 0 else 1e18  # 正数升序；无/负 PE 垫底
        nc = str(snap.get("next_earnings") or "9999-99-99")
        return (e.industry or "", st, -today, -r1m, -rytd, -r1y, val_key, nc)
    return sorted(entries, key=_key)


def _fmt_pct(v: Any, digits: int = 1) -> str:
    if v is None:
        return "—"
    try:
        return f"{float(v):.{digits}f}%"
    except (TypeError, ValueError):
        return "—"


def _fmt_price(snap: dict[str, Any]) -> str:
    p = snap.get("last_price")
    if p is None:
        return "—"
    try:
        f = float(p)
        if f >= 1000:
            return f"{f:,.0f}"
        return f"{f:.2f}"
    except (TypeError, ValueError):
        return "—"


def _fmt_cap(v: Any) -> str:
    if not v:
        return "—"
    try:
        f = float(v)
        if f >= 1e12:
            return f"{f / 1e12:.1f}tn"
        if f >= 1e9:
            return f"{f / 1e9:.1f}bn"
        if f >= 1e6:
            return f"{f / 1e6:.1f}m"
        return f"{f:.0f}"
    except (TypeError, ValueError):
        return "—"


def render_brief_markdown(
    entries: list[CoverageEntry],
    snapshots: dict[str, dict[str, Any]],
    today: str,
    gaps: list[str],
    news_map: dict[str, list[Any]],
    report_type: str = "am",
    review_map: dict[str, dict] | None = None,
    estimates: dict | None = None,
) -> str:
    """渲染 5 区块 markdown。"""
    ents = filter_entries(entries, report_type)
    lines: list[str] = []
    today_dt = datetime.date.fromisoformat(today) if today else datetime.date.today()
    review_map = review_map or {}

    # ── 头部 ──
    rt_label = {"am": "亚洲盘前", "asia": "亚盘盘后", "eu": "欧盘盘后"}.get(report_type, report_type)
    lines.append(f"# Daily Brief · {today}（{rt_label}）")
    lines.append("")
    lines.append(f"**覆盖 {len(ents)} 家 · 数据源 FMP**")
    lines.append("")

    # ── ① Review Queue：财报临近 <14d ──
    lines.append("## ① Review Queue")
    lines.append("")
    lines.append("| 触发 | Company | Ticker | Status | 触发详情 |")
    lines.append("|---|---|---|---|---|")
    rq_entries, rq_mid = [], []
    for e in ents:
        snap = snapshots.get(e.ticker or e.company, {})
        nd = snap.get("next_earnings")
        if nd:
            try:
                nd_dt = datetime.date.fromisoformat(str(nd)[:10])
                days = (nd_dt - today_dt).days
                if 0 <= days <= 7:
                    rq_entries.append((days, nd, e))
                elif 7 < days <= 30:
                    rq_mid.append((days, nd, e))
            except (ValueError, TypeError):
                pass
    for days, nd, e in sorted(rq_entries, key=lambda x: x[0]):  # 从近到远
        lines.append(f"| 财报 | {_display_name(e)} | {e.ticker} | {e.coverage_status or '—'} | ~{days} 天后财报（{nd}） |")
    if not rq_entries:
        lines.append("| — | 无临近事件 | — | — | 未来 7 天无财报 |")
    if rq_mid:
        lines.append("")
        lines.append(f"<details><summary>7-30 天财报（{len(rq_mid)} 家）</summary>")
        lines.append("")
        lines.append("| 触发 | Company | Ticker | Status | 触发详情 |")
        lines.append("|---|---|---|---|---|")
        for days, nd, e in sorted(rq_mid, key=lambda x: x[0]):
            lines.append(f"| 财报 | {_display_name(e)} | {e.ticker} | {e.coverage_status or '—'} | ~{days} 天后财报（{nd}） |")
        lines.append("</details>")
    lines.append("")

    # ── ② 估值表（全市场）──
    lines.append("## ② Valuation Universe")
    lines.append("")
    lines.append("| Company | Ticker | Industry | Today | 1m | YTD | 1y | PE_TTM | PE_NTM | EV/EBITDA_TTM | EV/EBITDA_NTM | Next_Call | Status |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    last_ind = None
    for e in _universe_sorted(ents, snapshots):
        if e.industry != last_ind:
            lines.append(f"| **{e.industry or 'Other'}** | | | | | | | | | | | | |")
            last_ind = e.industry
        snap = snapshots.get(e.ticker or e.company, {})
        vrow = snap.get("valuation") or {}
        pe_t = fmt_cell(vrow.get("pe_ttm"), vrow.get("pe_ttm_vs_5y"))
        pe_n = fmt_cell(vrow.get("pe_ntm"), extra=fwd_extra(vrow, "PE"))
        _fwd_pe = _fwd_ntm_pe(snap, estimates, e.ticker or e.company)
        if _fwd_pe is not None:
            pe_n = fmt_cell(_fwd_pe, extra="L1 fwd")
        ev_t = fmt_cell(vrow.get("ev_ttm"), vrow.get("ev_ttm_vs_5y"))
        ev_n = fmt_cell(vrow.get("ev_ntm"), extra=fwd_extra(vrow, "EV/EBITDA"))
        # 贵/便宜染色（PE TTM vs 5y 优先，其次 EV）
        if rich_class(vrow.get("pe_ttm_vs_5y")) == "rich":
            pe_t = f"**{pe_t}**"
        elif rich_class(vrow.get("ev_ttm_vs_5y")) == "rich":
            ev_t = f"**{ev_t}**"
        nd = snap.get("next_earnings") or ""
        lines.append(
            f"| {_display_name(e)} | {e.ticker} | {e.industry or '—'} | "
            f"{_fmt_pct(snap.get('price_move_pct'))} | {_fmt_pct(vrow.get('ret_1m'))} | "
            f"{_fmt_pct(vrow.get('ret_ytd'))} | {_fmt_pct(vrow.get('ret_1y'))} | "
            f"{pe_t} | {pe_n} | {ev_t} | {ev_n} | {nd or '—'} | {e.coverage_status or '—'} |"
        )
    lines.append("")
    lines.append("> **列口径**：PE_TTM=最近 4 季 trailing PE · PE_NTM=consensus 未来 12 月（价格÷epsAvg）· "
                 "EV/EBITDA_TTM=企业价值÷EBITDA · EV/EBITDA_NTM=(市值+净债)÷NTM EBITDA。"
                 "**括号 = 相对 5y 中位**：`+36%` = 比自身 5 年中位高 36%。"
                 "**`fwd 15x`** = 你的研究 fwd 假设（driver-map/模型），与 consensus 差异即潜在 alpha。"
                 "`—`=该口径无数据。")
    lines.append("")

    # ── ③ Movers：重要 ±8% / 普通 ±5% ──
    movers = [(e, snapshots.get(e.ticker or e.company, {})) for e in ents
              if snapshots.get(e.ticker or e.company, {}).get("price_move_pct") is not None]
    important = [(e, s) for e, s in movers if abs(float(s["price_move_pct"])) >= 8]
    minor = [(e, s) for e, s in movers if 5 <= abs(float(s["price_move_pct"])) < 8]

    lines.append("## ③ Movers")
    lines.append("")
    if important:
        lines.append("**重要（±8%）**")
        lines.append("")
        lines.append("| 公司 | Ticker | 涨跌 | Price | 涨跌原因 + 证据 |")
        lines.append("|---|---|---|---|---|")
        for e, s in important:
            rv = review_map.get(e.ticker or e.company) or {}
            if rv.get("summary"):
                links = " ".join(f"[[{i + 1}]]({l['url']})" for i, l in enumerate(rv.get("links", [])[:4]))
                expl = f"{rv['summary']} {links}" if links else rv["summary"]
            else:
                _items = news_map.get(e.ticker or e.company, [])
                expl = f"[{_items[0].title[:35]}]({_items[0].url})" if _items else "原因未明"
            lines.append(f"| {_display_name(e)} | {e.ticker} | {_fmt_pct(s['price_move_pct'], 1)} | {_fmt_price(s)} | {expl} |")
        lines.append("")
    if minor:
        lines.append("**普通（±5%）**")
        lines.append("")
        lines.append("| 公司 | Ticker | 涨跌 | Price | Cap | 1m | YTD | 原因/证据 |")
        lines.append("|---|---|---|---|---|---|---|---|")
        for e, s in minor:
            rv = review_map.get(e.ticker or e.company) or {}
            expl = rv.get("summary") or ""
            if rv.get("links"):
                expl += " " + " ".join(f"[[{i + 1}]]({l['url']})" for i, l in enumerate(rv["links"][:2]))
            lines.append(f"| {_display_name(e)} | {e.ticker} | {_fmt_pct(s['price_move_pct'], 1)} | {_fmt_price(s)} | "
                         f"{_fmt_cap(s.get('market_cap'))} | {_fmt_pct(s.get('ret_1m'))} | {_fmt_pct(s.get('ret_ytd'))} | "
                         f"{expl or '—'} |")
        lines.append("")
    if not important and not minor:
        lines.append("> 无 ±5% 异动。")
        lines.append("")

    # ── ④ Core Watch：Core 名单（一行两家） ──
    _protect = protect_names(entries)
    core = [e for e in ents if e.monitor_status == "Core"]
    lines.append("## ④ Core Watch")
    lines.append("")
    if core:
        def _core_key(e):
            _snap = snapshots.get(e.ticker or e.company, {})
            return (_STATUS_ORDER.get((e.coverage_status or "").strip(), 9),
                    str(_snap.get("next_earnings") or "9999-99-99"))

        def _core_cell(e):
            snap = snapshots.get(e.ticker or e.company, {})
            vrow = snap.get("valuation") or {}
            items = news_map.get(e.ticker or e.company, [])
            parts = [f"**{_display_name(e)} · {e.ticker}（{e.coverage_status or '—'}）**"]
            snap_parts = [f"Price {_fmt_price(snap)}", f"Cap {_fmt_cap(snap.get('market_cap'))}",
                          f"1m {_fmt_pct(vrow.get('ret_1m'))}", f"YTD {_fmt_pct(vrow.get('ret_ytd'))}",
                          f"1y {_fmt_pct(vrow.get('ret_1y'))}", f"Next {snap.get('next_earnings') or '—'}"]
            parts.append("Snapshot：" + " · ".join(snap_parts))
            # 主估值行（universe 同口径），全空不显示
            if any(vrow.get(f) is not None for f in ("pe_ttm", "pe_ntm", "ev_ttm", "ev_ntm")):
                pe_t = fmt_cell(vrow.get("pe_ttm"), vrow.get("pe_ttm_vs_5y"))
                pe_n = fmt_cell(vrow.get("pe_ntm"), extra=fwd_extra(vrow, "PE"))
                _fwd_pe = _fwd_ntm_pe(snap, estimates, e.ticker or e.company)
                if _fwd_pe is not None:
                    pe_n = fmt_cell(_fwd_pe, extra="L1 fwd")
                ev_t = fmt_cell(vrow.get("ev_ttm"), vrow.get("ev_ttm_vs_5y"))
                ev_n = fmt_cell(vrow.get("ev_ntm"), extra=fwd_extra(vrow, "EV/EBITDA"))
                parts.append(f"Valuation：PE_TTM {pe_t} · PE_NTM {pe_n} · EV/EBITDA_TTM {ev_t} · EV/EBITDA_NTM {ev_n}")
            # 次要倍数（None 跳过；P/FCF 口径注记）
            minor_parts = []
            for lbl, k, k5 in (("PS", "ps", "ps_5y"), ("PB", "pb", "pb_5y"), ("P/FCF", "pfcf", "pfcf_5y")):
                v = vrow.get(k)
                if v is None:
                    continue
                v5 = vrow.get(k5)
                note = " [OCF]" if (k == "pfcf" and vrow.get("pfcf_note")) else ""
                minor_parts.append(f"{lbl} {v}x{note}" + (f" (5y {v5})" if v5 is not None else ""))
            if minor_parts:
                parts.append("Multiples：" + " · ".join(minor_parts))
            if items:
                _tag = tag_news_title(pick_lead_news(items).title)
                _tag_s = f"【{_tag}】" if _tag else ""
                _t = translate_zh(pick_lead_news(items).title, protect=_protect).replace("|", "\\|").replace("<br>", " ")
                parts.append(f"📰 {_tag_s}[{_t[:60]}]({pick_lead_news(items).url})")
            else:
                parts.append("无新闻")
            return "<br>".join(parts)

        _ordered = sorted(core, key=_core_key)
        lines.append("| | |")
        lines.append("|---|---|")
        for _i in range(0, len(_ordered), 2):
            _row = [f"<br>{_core_cell(_ordered[_i])}<br>"]
            if _i + 1 < len(_ordered):
                _row.append(f"<br>{_core_cell(_ordered[_i + 1])}<br>")
            else:
                _row.append("")
            lines.append("| " + " | ".join(_row) + " |")
        lines.append("")
    else:
        lines.append("> 无 Core 名单。")
        lines.append("")

    # ── ⑤ Data Health ──
    lines.append("## ⑤ Data Health")
    lines.append("")
    if gaps:
        lines.append(f"<details><summary>{_health_summary(gaps)}</summary>")
        lines.append("")
        for g in gaps[:15]:
            lines.append(f"- {g}")
        lines.append("</details>")
    else:
        lines.append("> 数据完整。")
    lines.append("")
    return "\n".join(lines)
