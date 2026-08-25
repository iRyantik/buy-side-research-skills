"""日报 5 区块 HTML 渲染（复用 mock 样式，真数据）。

结构：hero + tab-nav（5 tabs）+ 5 tab-panels。
数据来自 snapshot（行情/估值/财报日）+ news_map。
"""

from __future__ import annotations

import html as _h
from typing import Any

from .coverage import CoverageEntry
from .candidates import score_candidates
from .brief import _display_name, _fwd_ntm_pe, _fmt_pct, _fmt_price, _fmt_cap, filter_entries, _universe_sorted, _STATUS_ORDER, _health_summary, scope_note, entry_market
from .news import pick_lead_news, protect_names, tag_news_title, translate_zh
from .valuation import fmt_cell, fwd_extra, rich_class

_CSS = """
:root{--ink:#132238;--muted:#64748b;--line:rgba(148,163,184,.34);--card:rgba(255,255,255,.88);--blue:#2563eb;--green:#0f9f6e;--red:#d33b3b;--amber:#b7791f;--slate:#475569;--blue-soft:#dbeafe;--green-soft:#dff7eb;--red-soft:#ffe4e6;--amber-soft:#fff7d6;--slate-soft:#e2e8f0;--shadow:0 22px 70px rgba(15,23,42,.12)}
*{box-sizing:border-box}
body{margin:0;color:var(--ink);font-family:"Noto Sans SC","Microsoft YaHei","PingFang SC",sans-serif;background:radial-gradient(circle at top left,#d9eef4 0,#f7fafc 38%,#edf2f6 100%);font-variant-numeric:tabular-nums}
a{color:inherit}
main{width:min(1440px,calc(100vw - 36px));margin:28px auto 48px}
.hero{display:flex;align-items:center;gap:12px;flex-wrap:wrap;border:1px solid var(--line);border-radius:12px;padding:8px 16px;background:rgba(255,255,255,.88);box-shadow:0 4px 12px rgba(15,23,42,.06);font-size:13px}
.hero-date{color:var(--muted);font-weight:700;margin-right:auto}
.hero-stat{color:var(--ink);font-weight:800}
h2{margin:0;font-size:18px;letter-spacing:-.03em}
.tab-nav{position:sticky;top:0;z-index:20;margin:18px 0 32px;display:flex;gap:12px;overflow-x:auto;padding:8px 10px;border:1px solid var(--line);border-radius:16px;background:rgba(255,255,255,.92);backdrop-filter:blur(18px);box-shadow:0 4px 16px rgba(15,23,42,.06)}
.tab-panel{scroll-margin-top:80px;margin-bottom:32px}
.tab-button{display:inline-block;border-radius:12px;padding:8px 14px;color:var(--muted);font-weight:800;font-size:13px;text-decoration:none;white-space:nowrap}
.tab-button:hover{background:rgba(19,34,56,.06);color:var(--ink)}
.section-head{display:flex;justify-content:space-between;align-items:flex-end;gap:18px;margin:18px 2px 12px}
.section-head p{margin:6px 0 0;max-width:840px;color:var(--muted);line-height:1.68;font-size:11.5px}
.card{border:1px solid var(--line);border-radius:24px;background:var(--card);box-shadow:0 14px 44px rgba(15,23,42,.08);padding:18px}
.table-card{overflow-x:auto;overflow-y:auto;max-height:72vh;-webkit-overflow-scrolling:touch;border:1px solid var(--line);border-radius:24px;background:var(--card);box-shadow:0 14px 44px rgba(15,23,42,.07)}
/* 邮件版表格：完整展开（邮件客户端容器滚动不可靠），页面滚动查看 */
.email-flat{max-height:none!important;overflow:visible!important}
.table-card table{min-width:1100px;width:100%;border-collapse:collapse;font-size:12px;table-layout:fixed}
.table-card th,.table-card td{overflow-wrap:anywhere}
.table-card td:first-child,.table-card th:first-child{min-width:92px}
.table-card td:nth-child(2),.table-card th:nth-child(2){min-width:110px}
th,td{padding:5px 5px;border-bottom:1px solid rgba(148,163,184,.18);text-align:left;vertical-align:middle;height:30px}
th{color:var(--muted);font-size:10px;text-transform:uppercase;letter-spacing:.06em;background:rgba(248,250,252,.82);position:sticky;top:0;z-index:3;box-shadow:0 1px 0 rgba(148,163,184,.25)}
td:first-child,th:first-child{padding-left:8px}
tr:last-child td{border-bottom:0}
tr.industry-row td{background:rgba(37,99,235,.06);font-weight:950;color:#1e3a8a;letter-spacing:.05em;font-size:11px;text-transform:uppercase}
.ret.pos{color:var(--green);font-weight:650}
.ret.neg{color:var(--red);font-weight:650}
.ret.na{color:var(--muted);font-weight:400}
.val-rich{color:var(--red);font-weight:850}
.val-cheap{color:var(--green);font-weight:850}
.val-na{color:var(--muted)}
.core-watch-card{border:1px solid var(--line);border-radius:18px;background:rgba(255,255,255,.94);box-shadow:0 14px 44px rgba(15,23,42,.08);padding:12px;margin-bottom:12px}
.core-title-line{display:flex;align-items:center;justify-content:space-between;gap:10px;flex-wrap:wrap}
.core-title-left{display:flex;align-items:center;flex-wrap:wrap;gap:6px;min-width:0}
.core-day{flex-shrink:0}
.core-ticker{font-size:13px;font-weight:950;letter-spacing:-.045em;min-width:0;overflow-wrap:anywhere}
.core-name{color:var(--ink);font-size:13px;font-weight:800;letter-spacing:-.02em;min-width:0;overflow-wrap:anywhere}
.core-industry{color:var(--muted);font-size:13px;font-weight:950;letter-spacing:-.045em;min-width:0;overflow-wrap:anywhere}
.core-day.pos{color:var(--green)}
.core-day.neg{color:var(--red)}
.pill{display:inline-flex;align-items:center;border-radius:999px;padding:2px 7px;font-size:10px;font-weight:950;border:1px solid rgba(99,102,241,.18)}
.pill.status.thesis{background:var(--blue-soft);color:#1d4ed8}
.pill.status.modeled{background:var(--green-soft);color:var(--green)}
.pill.status.quickread{background:var(--amber-soft);color:var(--amber)}
.pill.status.screened{background:var(--slate-soft);color:var(--slate)}
.core-quote-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:5px;margin-top:10px}
.core-quote-item{border:1px solid var(--line);border-radius:10px;background:rgba(248,250,252,.8);padding:6px 8px}
.core-quote-item span{display:block;color:var(--muted);font-size:9.5px;font-weight:800;text-transform:uppercase;letter-spacing:.06em}
.core-quote-item b{display:block;margin-top:4px;font-size:12px;overflow-wrap:anywhere}
.news-line{margin-top:8px;padding:6px 9px;border:1px solid var(--line);border-radius:10px;background:rgba(248,250,252,.7);font-size:11px;color:#334155;overflow-wrap:anywhere}
.news-line a,.mover-links a,.mover-detail a{word-break:break-word;overflow-wrap:anywhere}
.minor-multiples{margin-top:8px;font-size:12px;color:var(--muted)}
/* Core Watch 估值气泡：每个口径一个胶囊，贵/便宜染色 */
.core-valuation{margin-top:10px;padding-top:8px;border-top:1px dashed var(--line);display:flex;flex-wrap:wrap;gap:5px;font-size:10.5px}
.news-line{font-size:11px}.news-tag{display:inline-block;padding:1px 6px;border-radius:6px;background:rgba(59,130,246,.12);color:#2563eb;font-size:9.5px;font-weight:800;margin-right:2px}
.val-bubble{display:inline-flex;align-items:baseline;gap:4px;border-radius:999px;padding:2px 8px;border:1px solid var(--line);background:var(--card);color:var(--ink);white-space:nowrap;font-weight:650;max-width:100%;overflow:hidden;text-overflow:ellipsis}
.val-bubble-label{color:var(--muted);font-size:9px;font-weight:800;letter-spacing:.3px}
.val-bubble .val-note{color:var(--amber);font-weight:800;font-size:10px}
.val-bubble.val-rich{border-color:rgba(211,59,59,.5);background:var(--red-soft);color:var(--red)}
.val-bubble.val-cheap{border-color:rgba(15,159,110,.5);background:var(--green-soft);color:var(--green)}
.grid-2{display:grid;grid-template-columns:repeat(auto-fill,minmax(340px,1fr));gap:14px}
.grid-3{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:14px}
.mover-card{border:1px solid var(--line);border-radius:18px;background:rgba(255,255,255,.94);box-shadow:0 14px 44px rgba(15,23,42,.08);padding:12px}
.mover-card.important{border-left:4px solid var(--amber)}
.mover-card.minor{border-left:4px solid rgba(100,116,139,.35)}
.mover-card.minor .core-ticker,.mover-card.minor .core-name,.mover-card.minor .core-industry,.mover-card.minor .core-day{font-size:13px}
.mover-card.minor .core-quote-item b{font-size:11px}
.mover-detail{margin-top:10px;padding-top:10px;border-top:1px solid var(--line)}
.mover-reason{margin-bottom:5px;font-size:11px;font-weight:700;color:var(--ink)}
.mover-links{margin:5px 0 0;padding-left:14px;font-size:10.5px;line-height:1.7;color:#334155}
.mover-links a{color:var(--blue);text-decoration:none}
details{border:1px solid var(--line);border-radius:16px;background:rgba(255,255,255,.72);padding:10px 12px;margin-top:8px}
summary{cursor:pointer;font-weight:950;color:#1e3a8a}
/* Core Watch 行业分组头：扁平 + 折叠箭头 + 计数徽章 */
.industry-group{border:0;background:none;padding:0;margin-top:12px;border-top:1px dashed var(--line)}
.industry-group summary{display:flex;align-items:center;gap:8px;padding:8px 2px;list-style:none}
.industry-group summary::-webkit-details-marker{display:none}
.industry-group summary::before{content:"▸";color:var(--blue);font-size:11px;transition:transform .15s}
.industry-group[open] summary::before{transform:rotate(90deg)}
.industry-group .ig-name{font-weight:950;color:#1e3a8a;font-size:13px;text-transform:uppercase;letter-spacing:.04em;overflow-wrap:anywhere}
.industry-group .ig-count{color:var(--muted);font-size:10.5px;font-weight:800;background:var(--slate-soft);padding:1px 8px;border-radius:999px}
.industry-group .grid-2{margin-top:4px}
ul{margin:10px 0 0;padding-left:18px;color:#334155;line-height:1.7}
.health-line{border:1px solid var(--line);border-radius:18px;background:rgba(255,255,255,.9);padding:14px 18px;font-size:14px;font-weight:700}
/* 日报顶部作用域说明：前端=收盘市场，Universe/Review Queue=全量 */
.scope-note{color:var(--muted);font-size:12px;line-height:1.65;border-left:3px solid var(--blue);background:rgba(37,99,235,.05);padding:8px 12px;margin:12px 0 0;border-radius:0 10px 10px 0}
/* Research Candidates：信号卡片（分数徽章 + 信号胶囊 + 新闻锚点） */
.cand-note{color:var(--muted);font-size:11.5px;margin:2px 0 10px}
.cand-card{border:1px solid var(--line);border-radius:18px;background:rgba(255,255,255,.94);box-shadow:0 14px 44px rgba(15,23,42,.08);padding:12px}
.cand-head{display:flex;align-items:center;gap:6px;flex-wrap:wrap}
.cand-head b{font-size:14px}
.cand-score{background:var(--blue-soft);color:#1d4ed8;border-radius:999px;padding:1px 8px;font-size:11px;font-weight:900}
.cand-ticker{color:var(--muted);font-size:12px}
.cand-pills{margin-top:6px;font-size:0}
.cand-pill{display:inline-block;border-radius:999px;padding:1px 8px;font-size:11px;font-weight:650;margin:0 4px 4px 0}
.cand-news{margin-top:4px;font-size:12px}
.cand-news a{color:var(--blue);text-decoration:none}
.health-line .bad{color:var(--amber)}
.grid-2 .core-watch-card{margin-bottom:0}
/* ── 响应式：手机（≤640px）紧凑 + 表格隐藏次要列 + 安全区 ── */
@media(max-width:640px){
/* 邮件版 Core Watch 两列 grid：手机上单列 */
.em-grid,.em-grid tbody,.em-grid tr,.em-grid td{display:block;width:100%!important;padding:0!important}
main{width:calc(100vw - 20px);margin:16px auto 32px}
h2{font-size:16px}
.hero{font-size:12px;padding:6px 10px}
.tab-nav{margin:12px 0 20px;padding:6px 8px;gap:8px}
.tab-button{padding:7px 11px;font-size:12px}
.card,.core-watch-card,.mover-card{padding:12px;border-radius:18px}
.core-ticker,.core-name,.core-industry{font-size:13px}
.core-quote-grid{grid-template-columns:repeat(3,minmax(0,1fr));gap:6px}
.core-quote-item{padding:7px 8px}
.core-quote-item b{font-size:13px}
.table-card{max-height:none;overflow:visible}  /* 手机：表格完整展开，页面滚动（容器滚动在移动端邮件不可靠） */
.table-card.email-flat{max-height:none!important;overflow:visible!important}
.table-card table{min-width:330px;font-size:11.5px;table-layout:auto}
.table-card td:first-child,.table-card th:first-child{min-width:0}
.table-card td:nth-child(2),.table-card th:nth-child(2){min-width:0}
.table-card td,.table-card th{width:14.3%}  /* 手机 7 列均等 */
th,td{padding:4px 2px;height:28px}
td.m,th.m{display:none}  /* 表格次要列：手机上隐藏（核心列保留） */
.news-line{font-size:12px;padding:8px 10px}
/* 行情时间"旧"标记：左边蓝条 + 浅蓝底（Universe 行情时间列） */
.qt-old{display:inline-block;background:rgba(59,130,246,.1);border-left:3px solid #2563eb;color:#1d4ed8;border-radius:0 6px 6px 0;padding:0 5px;font-weight:750;white-space:nowrap}
.health-line{font-size:13px;padding:12px 14px}
body{padding-bottom:env(safe-area-inset-bottom)}
}
"""


def _ret_class(v: Any) -> str:
    if v is None:
        return "ret na"
    return "ret pos" if float(v) >= 0 else "ret neg"


def _val_2line(val, note: str = "", rich: str = "", email: bool = False) -> str:
    """估值单元格两行显示：第一行值，第二行 vs5y/标注（均等列宽下容纳完整信息）。"""
    if val is None and not note:
        return "—"
    v = f"{val}x" if isinstance(val, (int, float)) else (val or "—")
    color = "#d33b3b" if rich == "rich" else ("#0f9f6e" if rich == "cheap" else "#132238")
    note_color = "#d33b3b" if rich == "rich" else ("#0f9f6e" if rich == "cheap" else "#94a3b8")
    _note = f"<span style='display:block;font-size:9px;color:{note_color};font-weight:600'>{_h.escape(note)}</span>" \
        if note else "<span style='display:block;font-size:9px;color:#94a3b8'>&nbsp;</span>"
    return (f"<span style='display:block;font-size:11px;font-weight:650;color:{color};white-space:nowrap'>{v}</span>"
            f"{_note}")


def _vs_note(row: dict, vs_field: str) -> str:
    """vs5y 对比 → 第二行小字括号文本（对齐 PC 版，如 '(+187%)'）。"""
    v = row.get(vs_field)
    return f"({v:+.0f}%)" if v is not None else ""


def _val_cell_html(row: dict[str, Any], field: str, vs_field: str, email: bool = False) -> str:
    val = row.get(field)
    if val is None:
        if email:
            return "<span>NA</span>"
        return '<span class="val-na">NA</span>'
    vs = row.get(vs_field)
    cls = rich_class(vs)
    text = fmt_cell(val, vs)
    if email:
        # 邮件版：内联颜色（邮件客户端 class 样式不可靠）
        color = "#d33b3b" if cls == "rich" else ("#0f9f6e" if cls == "cheap" else "#132238")
        return f'<span style="color:{color};font-weight:650">{text}</span>'
    if cls == "rich":
        return f'<span class="val-rich">{text}</span>'
    if cls == "cheap":
        return f'<span class="val-cheap">{text}</span>'
    return f"<span>{text}</span>"


def _market_grp(entry: CoverageEntry) -> str:
    '''entry → 市场组（美股/亚盘/欧盘），用于时点摘要。复用 entry_market：注册 market 优先，否则按首上市地推断。'''
    return {"us": "美股", "asia": "亚盘", "eu": "欧盘"}.get(entry_market(entry), "")


def _tz_summary(ents, snapshots) -> str:
    '''各市场最新行情时点摘要，如「美股 08-21 16:00 · 亚盘 08-22 15:30」。'''
    _best: dict[str, str] = {}
    for e in ents or []:
        _s = snapshots.get(e.ticker or e.company, {}) or {}
        _qt = (_s.get("quote_time") or "").strip()
        if not _qt or _qt == "live":
            _qt = (_s.get("market_time") or "").strip()
        if not _qt:
            continue
        _g = _market_grp(e)
        if _g and _qt > _best.get(_g, ""):
            _best[_g] = _qt
    if not _best:
        return ""
    _parts = " · ".join(f"{g} {v[:16]}" for g, v in sorted(_best.items()))
    return f"<span class='hero-stat'> · 时点：{_parts}</span>"


def _quote_time_cell(snap: dict) -> str:
    '''行情时间单元格：FMP quote 无精确时间(恒 live)，fallback 采集日；早于今天标旧。'''
    from datetime import date as _d
    qt = (snap.get("quote_time") or "").strip()
    if not qt or qt == "live":
        qt = (snap.get("market_time") or "").strip()
    if not qt:
        return "—"
    short = qt[:16]
    try:
        if qt[:10] < _d.today().isoformat():
            return f"<span class='qt-old' title='行情数据早于今日'>{short} 旧</span>"
    except Exception:
        pass
    return short


def _val_bubble(row: dict[str, Any], label: str, field: str,
                vs_field: str | None = None, extra: str | None = None,
                note: str | None = None) -> str:
    """Core Watch 估值气泡：`[PE_TTM 33.0x (+187%)]`，贵红/便宜绿，None 段返回空串。

    extra 接在值后（如 `fwd 15x`）；note 是小注记（如 P/FCF 的 `OCF`）。
    """
    val = row.get(field)
    if val is None:
        return ""
    cls = rich_class(row.get(vs_field)) if vs_field else ""
    text = f"{val}x"
    if extra:
        text += f" {extra}"
    elif vs_field and row.get(vs_field) is not None:
        text += f" ({row[vs_field]:+.0f}%)"
    if note:
        text += f" <span class='val-note'>{_h.escape(note)}</span>"
    cls_attr = f" val-{cls}" if cls else ""
    return (f"<span class='val-bubble{cls_attr}'>"
            f"<span class='val-bubble-label'>{_h.escape(label)}</span> {text}</span>")


def render_brief_html(
    entries: list[CoverageEntry],
    snapshots: dict[str, dict[str, Any]],
    today: str,
    gaps: list[str],
    news_map: dict[str, list[Any]],
    report_type: str = "am",
    review_map: dict[str, dict] | None = None,
    estimates: dict | None = None,
    email: bool = False,
) -> str:
    # 作用域契约（全量 vs 部分）：本报告 = 刚收盘市场。
    #   "部分" = 只显示收盘市场，走 filter_entries → ents；
    #   "全量" = 跨所有市场，直接用完整 entries。
    # 注意：`us` 也是部分（只美股），`am` 才是全量。
    #   - Research Candidates → 部分（ents）：数据信号按收盘市场打分
    #   - Movers             → 部分（ents）：只显示收盘市场的 ±5%/±8% 异动
    #   - Core Watch         → 部分（ents）：只显示收盘市场的 Core 名单
    #   - Review Queue       → 全量（entries）：财报是未来事件，跨市场
    #   - Valuation Universe → 全量（entries）：估值参考表跨市场
    #   - Data Health        → 全局（gaps，本身跨市场，不做市场过滤）
    ents = filter_entries(entries, report_type)
    rt_label = {"us": "美股盘后", "asia": "亚盘盘后", "eu": "欧盘盘后"}.get(report_type, report_type)
    # 顶部作用域说明（前端=收盘市场，Universe/Review Queue=全量）
    _scope = scope_note(report_type, "Candidates / Movers / Core Watch")
    core_count = sum(1 for e in ents if e.monitor_status == "Core")
    review_map = review_map or {}
    _protect = protect_names(entries)

    # ── 估值表（email 版涨跌/估值用内联颜色，邮件客户端 class 样式不可靠）──
    def _uni_rows_html(email_mode: bool = False) -> list:
        rows: list = []
        last_ind = None
        # Universe 全量（所有市场估值参考表）
        for e in _universe_sorted(entries, snapshots):
            if e.industry != last_ind:
                rows.append(f'<tr class="industry-row"><td colspan="14">{_h.escape(e.industry or "Other")}</td></tr>')
                last_ind = e.industry
            snap = snapshots.get(e.ticker or e.company, {})
            vrow = snap.get("valuation") or {}
            pe_n_extra = fwd_extra(vrow, "PE")
            ev_n_extra = fwd_extra(vrow, "EV/EBITDA")
            _fwd_pe = _fwd_ntm_pe(snap, estimates, e.ticker or e.company)
            _pe_ntm_val = _fwd_pe if _fwd_pe is not None else vrow.get("pe_ntm")
            _pe_ntm_extra = "L1 fwd" if _fwd_pe is not None else pe_n_extra

            def _ret_td(v: Any, m_cls: str = "") -> str:
                _t = _fmt_pct(v)
                if email_mode:
                    if v is None:
                        return f"<td>{_t}</td>"
                    c = "#0f9f6e" if float(v) >= 0 else "#d33b3b"
                    _m = " class='m'" if m_cls else ""
                    return f"<td{_m} style='color:{c};font-weight:650'>{_t}</td>"
                return f'<td class="{m_cls}{_ret_class(v)}">{_t}</td>'

            rows.append(
                "<tr>"
                f"<td>{_h.escape(_display_name(e))}</td>"
                f"<td class='m'>{_h.escape(e.ticker or '')}</td>"
                f"<td class='m'>{_h.escape(e.industry or '—')}</td>"
                + _ret_td(snap.get("price_move_pct"))
                + _ret_td(vrow.get("ret_1m"))
                + _ret_td(vrow.get("ret_ytd"))
                + _ret_td(vrow.get("ret_1y"))
                + f"<td>{_val_2line(vrow.get('pe_ttm'), _vs_note(vrow, 'pe_ttm_vs_5y'), rich_class(vrow.get('pe_ttm_vs_5y')), email_mode)}</td>"
                + f"<td>{_val_2line(_pe_ntm_val, _pe_ntm_extra, '', email_mode)}</td>"
                + f"<td class='m'>{_h.escape(str(snap.get('next_earnings') or '—'))}</td>"
                + f"<td class='m'>{_h.escape(e.coverage_status or '—')}</td>"
                + f"<td class='m'>{_quote_time_cell(snap)}</td>"
                + "</tr>"
            )
        return rows

    uni_rows = _uni_rows_html(False)

    # ── Movers ──
    movers = [(e, snapshots.get(e.ticker or e.company, {})) for e in ents
              if snapshots.get(e.ticker or e.company, {}).get("price_move_pct") is not None]
    important = [(e, s) for e, s in movers if abs(float(s["price_move_pct"])) >= 8]
    minor = [(e, s) for e, s in movers if 5 <= abs(float(s["price_move_pct"])) < 8]

    def _mover_card(e: CoverageEntry, s: dict, imp: bool) -> str:
        vrow = s.get("valuation") or {}
        day_cls = "core-day pos" if float(s["price_move_pct"]) >= 0 else "core-day neg"
        rv = review_map.get(e.ticker or e.company) or {}
        det = ""
        if rv.get("summary"):
            links_html = "".join(
                f"<li><a href='{_h.escape(l['url'])}' target='_blank'>{_h.escape(translate_zh(l['title'], protect=_protect)[:60])}</a></li>"
                for l in rv.get("links", [])[:5])
            det = (f"<div class='mover-detail'><div class='mover-reason'>📌 {_h.escape(rv['summary'])}</div>"
                   + (f"<ul class='mover-links'>{links_html}</ul>" if links_html else "") + "</div>")
        elif imp:
            items = news_map.get(e.ticker or e.company, [])
            if items:
                det = (f"<div class='mover-detail'><a href='{_h.escape(items[0].url or '#')}' target='_blank'>"
                       f"{_h.escape(items[0].title[:80])}</a></div>")
        return (
            f"<div class='mover-card {'important' if imp else 'minor'}'>"
            f"<div class='core-title-line'><div class='core-title-left'>"
            f"<span class='core-ticker'>{_h.escape(e.ticker or '')}</span>"
            f"<span class='core-name'>{_h.escape(_display_name(e))}</span>"
            f"<span class='core-industry'>{_h.escape(e.industry or '')}</span>"
            f"</div><span class='{day_cls}'>{_fmt_pct(s['price_move_pct'])}</span></div>"
            f"<div class='core-quote-grid'>"
            f"<div class='core-quote-item'><span>Price</span><b>{_fmt_price(s)}</b></div>"
            f"<div class='core-quote-item'><span>Cap</span><b>{_fmt_cap(s.get('market_cap'))}</b></div>"
            f"<div class='core-quote-item'><span>1m</span><b>{_fmt_pct(vrow.get('ret_1m'))}</b></div>"
            f"<div class='core-quote-item'><span>YTD</span><b>{_fmt_pct(vrow.get('ret_ytd'))}</b></div>"
            f"<div class='core-quote-item'><span>Vol</span><b>{s.get('volume_ratio') or '—'}</b></div>"
            f"<div class='core-quote-item'><span>Gap</span><b>{s.get('gap_pct') or '—'}</b></div>"
            f"</div>{det}</div>"
        )

    mover_html = ""
    if important:
        mover_html += f"<div class='section-head'><h2>重要（±8%）</h2></div><div class='grid-2'>" + "".join(
            _mover_card(e, s, True) for e, s in important) + "</div>"
    if minor:
        mover_html += f"<div class='section-head'><h2>普通（±5%）</h2></div><div class='grid-3'>" + "".join(
            _mover_card(e, s, False) for e, s in minor) + "</div>"
    if not important and not minor:
        mover_html = "<div class='health-line'>无 ±5% 异动。</div>"

    # ── Research Candidates：数据信号驱动的研究优先级（Movers 后）──
    cands = score_candidates(ents, snapshots, news_map, today)

    def _cand_pill(text: str, email_mode: bool) -> str:
        """信号胶囊：按信号类型染色（异动跟涨跌、低估绿、贵红、财报蓝、新闻琥珀、放量灰）。"""
        color = "#475569"
        bg = "#f1f5f9"
        if text.startswith("异动"):
            pos = "+" in text
            color = "#0f9f6e" if pos else "#d33b3b"
            bg = "#dff7eb" if pos else "#ffe4e6"
        elif text.startswith("深度低估"):
            color, bg = "#0f9f6e", "#dff7eb"
        elif text.startswith("深度贵"):
            color, bg = "#d33b3b", "#ffe4e6"
        elif text.startswith("财报"):
            color, bg = "#1d4ed8", "#dbeafe"
        elif text.startswith("重大新闻"):
            color, bg = "#b7791f", "#fff7d6"
        if email_mode:
            return (f"<span style='display:inline-block;border-radius:999px;padding:1px 8px;"
                    f"font-size:11px;color:{color};background:{bg};margin:0 4px 4px 0'>{_h.escape(text)}</span>")
        return (f"<span class='cand-pill' style='color:{color};background:{bg}'>{_h.escape(text)}</span>")

    def _cands_html(email_mode: bool) -> str:
        if not cands:
            return "<div class='health-line'>今日无强信号标的。</div>"
        cards = []
        for c in cands:
            e = c["entry"]
            pills = "".join(_cand_pill(t, email_mode) for _, t in c["signals"])
            news = ""
            if c["news"]:
                tl = translate_zh(c["news"].title, protect=_protect)
                news = (f"<a href='{_h.escape(c['news'].url)}' target='_blank'>📰 {_h.escape(tl[:60])}</a>")
            if email_mode:
                cards.append(
                    f"<div style='border:1px solid #d8dee9;border-radius:12px;padding:12px;margin-bottom:12px;background:#ffffff'>"
                    f"<div><b style='font-size:14px'>{_h.escape(_display_name(e))}</b> "
                    f"<span style='color:#64748b;font-size:12px'>{_h.escape(e.ticker or '')}</span> "
                    f"<span style='display:inline-block;border-radius:999px;padding:1px 8px;font-size:11px;"
                    f"color:#1d4ed8;background:#dbeafe;margin-left:4px'>{c['score']}</span></div>"
                    f"<div style='margin-top:6px;font-size:0'>{pills}</div>"
                    + (f"<div style='margin-top:4px;font-size:12px'>{news}</div>" if news else "")
                    + "</div>")
            else:
                cards.append(
                    f"<div class='cand-card'>"
                    f"<div class='cand-head'><span class='cand-score'>{c['score']}</span>"
                    f"<b>{_h.escape(_display_name(e))}</b> "
                    f"<span class='cand-ticker'>{_h.escape(e.ticker or '')}</span></div>"
                    f"<div class='cand-pills'>{pills}</div>"
                    + (f"<div class='cand-news'>{news}</div>" if news else "")
                    + "</div>")
        if email_mode:
            return "".join(cards)
        return f"<div class='grid-3'>{''.join(cards)}</div>"

    # ── Core Watch：按行业分组（组内 Status 核心到边缘 + 财报临近置顶，组间公司数降序）──
    core_html = ""
    core_ents = [e for e in ents if e.monitor_status == "Core"]

    def _core_key(e):
        _snap = snapshots.get(e.ticker or e.company, {})
        _st = _STATUS_ORDER.get((e.coverage_status or "").strip(), 9)
        _nc = str(_snap.get("next_earnings") or "9999-99-99")
        return (_st, _nc)

    def _core_card(e) -> str:
        snap = snapshots.get(e.ticker or e.company, {})
        vrow = snap.get("valuation") or {}
        day_cls = "core-day pos" if (snap.get("price_move_pct") or 0) >= 0 else "core-day neg"
        items = news_map.get(e.ticker or e.company, [])
        if items:
            _lead = pick_lead_news(items)
            _tag = tag_news_title(_lead.title)
            _tag_s = f"<span class='news-tag'>{_h.escape(_tag)}</span> " if _tag else ""
            _tl = translate_zh(_lead.title, protect=_protect)
            head = (f"<div class='news-line'>📰 {_tag_s}<a href='{_h.escape(_lead.url or '#')}' target='_blank'>"
                    f"{_h.escape(_tl[:100])}</a></div>")
        else:
            head = "<div class='news-line'>无新闻</div>"
        # 估值气泡（全口径，universe 同源）：None 段自动跳过，贵/便宜染色，P/FCF OCF 注记
        _vrow_c = vrow
        _fwd_pe = _fwd_ntm_pe(snap, estimates, e.ticker or e.company)
        if _fwd_pe is not None:
            _vrow_c = dict(vrow)
            _vrow_c["pe_ntm"] = _fwd_pe
        bubbles = [
            _val_bubble(_vrow_c, "PE_TTM", "pe_ttm", "pe_ttm_vs_5y"),
            _val_bubble(_vrow_c, "PE_NTM", "pe_ntm",
                        extra=("L1 fwd" if _fwd_pe is not None else fwd_extra(vrow, "PE"))),
            _val_bubble(_vrow_c, "EV/EBITDA_TTM", "ev_ttm", "ev_ttm_vs_5y"),
            _val_bubble(_vrow_c, "EV/EBITDA_NTM", "ev_ntm", extra=fwd_extra(vrow, "EV/EBITDA")),
            _val_bubble(_vrow_c, "PS", "ps", "ps_5y"),
            _val_bubble(_vrow_c, "PB", "pb", "pb_5y"),
            _val_bubble(_vrow_c, "P/FCF", "pfcf", "pfcf_5y",
                        note="OCF" if vrow.get("pfcf_note") else None),
        ]
        bubbles = [b for b in bubbles if b]
        val_line = f"<div class='core-valuation'>{''.join(bubbles)}</div>" if bubbles else ""
        return (
            f"<div class='core-watch-card'><div class='core-title-line'><div class='core-title-left'>"
            f"<span class='core-ticker'>{_h.escape(e.ticker or '')}</span>"
            f"<span class='core-name'>{_h.escape(_display_name(e))}</span>"
            f"<span class='pill status {str(e.coverage_status or '').lower()}'>{_h.escape(e.coverage_status or '')}</span>"
            f"</div><span class='{day_cls}'>{_fmt_pct(snap.get('price_move_pct'))}</span></div>"
            f"<div class='core-quote-grid'>"
            f"<div class='core-quote-item'><span>Price</span><b>{_fmt_price(snap)}</b></div>"
            f"<div class='core-quote-item'><span>Cap</span><b>{_fmt_cap(snap.get('market_cap'))}</b></div>"
            f"<div class='core-quote-item'><span>1m</span><b>{_fmt_pct(vrow.get('ret_1m'))}</b></div>"
            f"<div class='core-quote-item'><span>YTD</span><b>{_fmt_pct(vrow.get('ret_ytd'))}</b></div>"
            f"<div class='core-quote-item'><span>1y</span><b>{_fmt_pct(vrow.get('ret_1y'))}</b></div>"
            f"<div class='core-quote-item'><span>Next</span><b>{_h.escape(str(snap.get('next_earnings') or '—'))}</b></div>"
            f"</div>{val_line}{head}</div>"
        )

    groups: dict[str, list] = {}
    for e in core_ents:
        groups.setdefault(e.industry or "Other", []).append(e)
    for ind in sorted(groups, key=lambda k: -len(groups[k])):
        ents_sorted = sorted(groups[ind], key=_core_key)
        cards = "".join(_core_card(e) for e in ents_sorted)
        core_html += (f"<details class='industry-group' open>"
                      f"<summary><span class='ig-name'>{_h.escape(ind)}</span>"
                      f"<span class='ig-count'>{len(ents_sorted)} 家</span></summary>"
                      f"<div class='grid-2'>{cards}</div></details>")
    if not groups:
        core_html = "<div class='health-line'>无 Core 名单。</div>"

    # ── Review Queue：7 天内显示；7-30 天表格内折叠 ──
    rq_entries, rq_mid = [], []
    # Review Queue 全量（财报是未来事件，跨市场）
    for e in entries:
        nd = snapshots.get(e.ticker or e.company, {}).get("next_earnings")
        if nd:
            from datetime import date as _d
            try:
                days = (_d.fromisoformat(str(nd)[:10]) - _d.fromisoformat(today)).days
                if 0 <= days <= 7:
                    rq_entries.append((days, nd, e))
                elif 7 < days <= 30:
                    rq_mid.append((days, nd, e))
            except ValueError:
                pass
    rq_entries.sort(key=lambda x: x[0])  # 财报日从近到远
    rq_rows = "".join(
        f"<tr><td>财报</td><td>{_h.escape(_display_name(e))}</td>"
        f"<td>{_h.escape(e.ticker or '')}</td>"
        f"<td>{_h.escape(e.coverage_status or '—')}</td>"
        f"<td>~{days} 天后（{nd}）</td></tr>"
        for days, nd, e in rq_entries)
    if not rq_rows:
        rq_rows = "<tr><td>—</td><td>无临近事件</td><td>—</td><td>—</td><td>未来 7 天无财报</td></tr>"
    rq_fold = ""
    if rq_mid:
        rq_mid.sort(key=lambda x: x[0])
        mid_rows = "".join(
            f"<tr><td>财报</td><td>{_h.escape(_display_name(e))}</td>"
            f"<td>{_h.escape(e.ticker or '')}</td>"
            f"<td>{_h.escape(e.coverage_status or '—')}</td>"
            f"<td>~{days} 天后（{nd}）</td></tr>"
            for days, nd, e in rq_mid)
        # 表格内折叠：td colspan 包 details，展开结构与 7 天内一致
        rq_fold = (f"<tr><td colspan='5'><details><summary>7-30 天财报（{len(rq_mid)} 家）</summary>"
                   f"<table><tbody>{mid_rows}</tbody></table></details></td></tr>")

    # ── Data Health ──
    health = ""
    if gaps:
        items = "".join(f"<li>{_h.escape(g[:90])}</li>" for g in gaps[:15])
        health = f"<details><summary>{_health_summary(gaps)}</summary><ul>{items}</ul></details>"
    else:
        health = "<div class='health-line'>数据完整。</div>"

    if email:
        # ── 邮件版：无 hero/tab/Data Health；mover/core 用简单块级 + 内联样式（邮件客户端 CSS 兼容）──
        def _em_quote_cell(label: str, value: str, color: str = "#132238") -> str:
            """邮件版行情小格子（inline-block 3 个一行自动换行，不依赖 media query）。"""
            return (f"<span style='display:inline-block;width:32%;border:1px solid #e2e8f0;border-radius:8px;"
                    f"padding:4px 6px;margin:2px;box-sizing:border-box;text-align:center'>"
                    f"<span style='display:block;font-size:9px;color:#64748b;font-weight:800;letter-spacing:.05em'>{_h.escape(label)}</span>"
                    f"<span style='font-size:12px;font-weight:700;color:{color}'>{value}</span></span>")

        def _em_quote_grid(snap: dict, vrow: dict) -> str:
            """邮件版行情格（3×2，涨跌红绿）：Price/Cap/1m/YTD(+Vol/Gap for movers)。"""
            cells = [_em_quote_cell("Price", _fmt_price(snap)),
                     _em_quote_cell("Cap", _fmt_cap(snap.get("market_cap")))]
            for label, val in (("1m", vrow.get("ret_1m")), ("YTD", vrow.get("ret_ytd"))):
                if val is None:
                    continue
                c = "#0f9f6e" if float(val) >= 0 else "#d33b3b"
                cells.append(_em_quote_cell(label, _fmt_pct(val), c))
            for label, val in (("Vol", snap.get("volume_ratio")), ("Gap", snap.get("gap_pct"))):
                if val is not None:
                    cells.append(_em_quote_cell(label, _h.escape(str(val))))
            return f"<div style='margin-top:6px;font-size:0'>{''.join(cells)}</div>"

        def _em_two_col(cards: list) -> str:
            """两列 table 布局（邮件客户端兼容），手机 media 转单列。"""
            _rows = []
            for i in range(0, len(cards), 2):
                _pair = cards[i:i + 2]
                _tds = "".join(f"<td width='50%' valign='top' style='padding:4px'>{c}</td>" for c in _pair)
                if len(_pair) == 1:
                    _tds += "<td width='50%' valign='top' style='padding:4px'></td>"
                _rows.append(f"<tr>{_tds}</tr>")
            return (f"<table role='presentation' width='100%' cellpadding='0' cellspacing='0' class='em-grid'>"
                    f"<tbody>{''.join(_rows)}</tbody></table>") if _rows else ""

        def _em_mover_card(e: CoverageEntry, s: dict, imp: bool) -> str:
            vrow = s.get("valuation") or {}
            day_color = "#0f9f6e" if float(s["price_move_pct"]) >= 0 else "#d33b3b"
            rv = review_map.get(e.ticker or e.company) or {}
            quote = _em_quote_grid(s, vrow)
            det = ""
            if rv.get("summary"):
                links = "".join(
                    f"<li style='margin:2px 0'><a style='color:#2563eb' href='{_h.escape(l['url'])}'>{_h.escape(translate_zh(l['title'], protect=_protect)[:50])}</a></li>"
                    for l in rv.get("links", [])[:4])
                det = (f"<div style='margin-top:8px;font-size:12px;color:#132238'><b>📌 {_h.escape(rv['summary'])}</b></div>"
                       + (f"<ul style='margin:6px 0 0;padding-left:16px;font-size:12px'>{links}</ul>" if links else ""))
            elif imp:
                items = news_map.get(e.ticker or e.company, [])
                if items:
                    det = (f"<div style='margin-top:8px;font-size:12px'><a style='color:#2563eb' href='{_h.escape(items[0].url or '#')}'>"
                           f"{_h.escape(items[0].title[:70])}</a></div>")
            return (f"<div style='border:1px solid #d8dee9;border-radius:12px;padding:12px;margin-bottom:12px;background:#ffffff'>"
                    f"<div><b style='font-size:14px'>{_h.escape(_display_name(e))}</b> "
                    f"<span style='color:#64748b;font-size:12px'>{_h.escape(e.ticker or '')}</span> "
                    f"<span style='color:#94a3b8;font-size:12px'>{_h.escape(e.industry or '')}</span> "
                    f"<span style='font-size:13px;font-weight:700;color:{day_color}'>{_fmt_pct(s['price_move_pct'])}</span></div>"
                    f"{quote}{det}</div>")

        def _em_val_bubble(row: dict, label: str, field: str,
                           vs_field: str | None = None, extra: str | None = None) -> str:
            """邮件版估值胶囊（内联样式，不依赖 flex）。"""
            val = row.get(field)
            if val is None:
                return ""
            text = f"{label} {val}x"
            if extra:
                text += f" {extra}"
            elif vs_field and row.get(vs_field) is not None:
                text += f" ({row.get(vs_field)}%)"
            _vs = row.get(vs_field)
            color = "#d33b3b" if _vs is not None and _vs > 30 else ("#0f9f6e" if _vs is not None and _vs < -30 else "#132238")
            return (f"<span style='display:inline-block;border:1px solid #d8dee9;border-radius:999px;"
                    f"padding:1px 7px;font-size:11px;background:#f8fafc;color:{color};margin:0 4px 4px 0'>{_h.escape(text)}</span>")

        def _em_core_card(e: CoverageEntry) -> str:
            snap = snapshots.get(e.ticker or e.company, {})
            vrow = snap.get("valuation") or {}
            day_color = "#0f9f6e" if (snap.get("price_move_pct") or 0) >= 0 else "#d33b3b"
            # 行情行：价格 / 市值 / 1m / YTD（文本流式，邮件安全）
            quote = _em_quote_grid(snap, vrow)
            # 估值行：关键口径胶囊（L1 fwd 优先）
            _vrow_c = vrow
            _fwd_pe = _fwd_ntm_pe(snap, estimates, e.ticker or e.company)
            if _fwd_pe is not None:
                _vrow_c = dict(vrow)
                _vrow_c["pe_ntm"] = _fwd_pe
            est = "".join(x for x in [
                _em_val_bubble(_vrow_c, "PE_TTM", "pe_ttm", "pe_ttm_vs_5y"),
                _em_val_bubble(_vrow_c, "PE_NTM", "pe_ntm",
                               extra=("L1 fwd" if _fwd_pe is not None else None)),
                _em_val_bubble(_vrow_c, "EV/EBITDA_TTM", "ev_ttm", "ev_ttm_vs_5y"),
                _em_val_bubble(_vrow_c, "EV/EBITDA_NTM", "ev_ntm"),
            ] if x)
            est_line = f"<div style='margin-top:5px;font-size:0'>{est}</div>" if est else ""
            items = news_map.get(e.ticker or e.company, [])
            if items:
                _lead = pick_lead_news(items)
                _tl = translate_zh(_lead.title, protect=_protect)
                head = (f"<div style='margin-top:4px;font-size:12px;color:#334155'><a style='color:#2563eb' href='{_h.escape(_lead.url or '#')}'>"
                        f"{_h.escape(_tl[:80])}</a></div>")
            else:
                head = "<div style='margin-top:4px;font-size:12px;color:#94a3b8'>无新闻</div>"
            return (f"<div style='border:1px solid #d8dee9;border-radius:12px;padding:12px;margin-bottom:12px;background:#ffffff'>"
                    f"<b style='font-size:13px'>{_h.escape(_display_name(e))}</b> "
                    f"<span style='color:#64748b;font-size:12px'>{_h.escape(e.ticker or '')}</span> "
                    f"<span style='font-size:11px;background:#e2e8f0;border-radius:8px;padding:1px 7px;color:#475569'>{_h.escape(e.coverage_status or '')}</span> "
                    f"<span style='font-size:12px;font-weight:700;color:{day_color}'>{_fmt_pct(snap.get('price_move_pct'))}</span>"
                    f"{quote}"
                    f"{est_line}{head}</div>")

        # 邮件版：mover 单列（内容长，两列在手机邮件客户端不可靠）；core 两列（用户验证 OK）
        em_movers = "".join(
            [_em_mover_card(e, s, True) for e, s in important] +
            [_em_mover_card(e, s, False) for e, s in minor])
        if not em_movers:
            em_movers = "<div class='health-line'>无 ±5% 异动。</div>"
        em_core = "".join(_em_core_card(e) for e in sorted(core_ents, key=_core_key))
        if not em_core:
            em_core = "<div class='health-line'>无 Core 名单。</div>"
        body = f"""<!doctype html><html lang="zh-Hans"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Daily Brief {today} · {rt_label}</title>
<style>{_CSS}</style></head><body><main>
<div style="border-left:3px solid #2563eb;background:#f4f8ff;color:#64748b;font-size:12px;line-height:1.65;padding:8px 12px;margin:0 0 18px;border-radius:0 10px 10px 0">{_h.escape(_scope)}</div>
<div id="candidates" style="margin-bottom:24px"><div class="section-head"><h2>Research Candidates</h2></div>
<p style='color:#64748b;font-size:11px;margin:2px 0 8px'>评分：异动 ±8% +2 · ±5% +1 · 深度低估（估值 vs 5y ≤-30%）+2 · 深度贵 +1 · 财报 7 天内 +1 · 重大新闻 +1 · 放量 ≥2x +1 ｜ 总分 ≥3 入选 Top 5</p>
{_cands_html(True)}</div>
<div id="movers" style="margin-bottom:24px"><div class="section-head"><h2>Movers</h2></div>{em_movers}</div>
<div id="core" style="margin-bottom:24px"><div class="section-head"><h2>Core Watch</h2></div>{em_core}</div>
<div id="review" style="margin-bottom:24px"><div class="section-head"><h2>Review Queue</h2>
<p>财报临近（&lt;7 天）。</p></div>
<div class="table-card email-flat"><table><thead><tr><th>触发</th><th>Company</th><th>Ticker</th><th>Status</th><th>触发详情</th></tr></thead>
<tbody>{rq_rows}{rq_fold}</tbody></table></div></div>
<div id="universe" style="margin-bottom:24px"><div class="section-head"><h2>Valuation Universe</h2>
<p>括号 = 相对 5y 中位%。红 = 贵（&gt;+30%）· 绿 = 便宜（&lt;-30%）· fwd = 前瞻假设</p></div>
<div class="table-card email-flat"><table><thead><tr><th>Company</th><th class='m'>Ticker</th><th class='m'>Industry</th><th>Today</th><th>1m</th><th>YTD</th><th>1y</th><th>PE_TTM</th><th>PE_NTM</th><th class='m'>Next_Call</th><th class='m'>Status</th><th class='m'>行情时间</th></tr></thead>
<tbody>{''.join(_uni_rows_html(True))}</tbody></table></div></div>
</main></body></html>"""
    else:
        body = f"""
<!doctype html><html lang="zh-Hans"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Daily Brief {today} · {rt_label}</title>
<style>{_CSS}</style></head><body><main>
<section class="hero">
  <span class="hero-date">{today} · {rt_label} · 数据来源：FMP</span>{_tz_summary(entries, snapshots)}
  <span class="hero-stat">{len(ents)} names</span>
  <span class="hero-stat">{core_count} Core Watch</span>
  <span class="hero-stat">{len(important)} movers</span>
  <span class="hero-stat">{len(rq_entries)} actions</span>
</section>
<div class="scope-note">{_h.escape(_scope)}</div>
<nav class="tab-nav">
  <a class="tab-button" href="#candidates">Candidates</a>
  <a class="tab-button" href="#movers">Movers</a>
  <a class="tab-button" href="#core">Core Watch</a>
  <a class="tab-button" href="#review">Review Queue</a>
  <a class="tab-button" href="#universe">Valuation Universe</a>
  <a class="tab-button" href="#health">Data Health</a>
</nav>
<section id="candidates" class="tab-panel"><div class="section-head"><h2>Research Candidates</h2></div>
<p class='cand-note'>评分：异动 ±8% +2 · ±5% +1 · 深度低估（估值 vs 5y ≤-30%）+2 · 深度贵 +1 · 财报 7 天内 +1 · 重大新闻 +1 · 放量 ≥2x +1 ｜ 总分 ≥3 入选 Top 5</p>
{_cands_html(False)}</section>
<section id="movers" class="tab-panel"><div class="section-head"><h2>Movers</h2></div>{mover_html}</section>
<section id="core" class="tab-panel"><div class="section-head"><h2>Core Watch</h2></div>{core_html}</section>
<section id="review" class="tab-panel"><div class="section-head"><h2>Review Queue</h2>
<p>财报临近（&lt;7 天）。</p></div>
<div class="table-card"><table><thead><tr><th>触发</th><th>Company</th><th>Ticker</th><th>Status</th><th>触发详情</th></tr></thead>
<tbody>{rq_rows}{rq_fold}</tbody></table></div></section>
<section id="universe" class="tab-panel"><div class="section-head"><h2>Valuation Universe</h2>
<p>括号 = 相对 5y 中位%。红 = 贵（&gt;+30%）· 绿 = 便宜（&lt;-30%）· fwd = 前瞻假设</p></div>
<div class="table-card"><table><thead><tr><th>Company</th><th class='m'>Ticker</th><th class='m'>Industry</th><th>Today</th><th>1m</th><th>YTD</th><th>1y</th><th>PE_TTM</th><th>PE_NTM</th><th class='m'>Next_Call</th><th class='m'>Status</th><th class='m'>行情时间</th></tr></thead>
<tbody>{''.join(uni_rows)}</tbody></table></div></section>
<section id="health" class="tab-panel"><div class="section-head"><h2>Data Health</h2></div>{health}</section>
</main></body></html>"""
    return body
