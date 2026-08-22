"""日报 5 区块 HTML 渲染（复用 mock 样式，真数据）。

结构：hero + tab-nav（5 tabs）+ 5 tab-panels。
数据来自 snapshot（行情/估值/财报日）+ news_map。
"""

from __future__ import annotations

import html as _h
from typing import Any

from .coverage import CoverageEntry
from .brief import _display_name, _fwd_ntm_pe, _fmt_pct, _fmt_price, _fmt_cap, filter_entries, _universe_sorted, _STATUS_ORDER, _health_summary
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
.section-head p{margin:6px 0 0;max-width:840px;color:var(--muted);line-height:1.68}
.card{border:1px solid var(--line);border-radius:24px;background:var(--card);box-shadow:0 14px 44px rgba(15,23,42,.08);padding:18px}
.table-card{overflow-x:auto;overflow-y:auto;max-height:72vh;-webkit-overflow-scrolling:touch;border:1px solid var(--line);border-radius:24px;background:var(--card);box-shadow:0 14px 44px rgba(15,23,42,.07)}
.table-card table{min-width:1000px;width:100%;border-collapse:collapse;font-size:12px}
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
.core-watch-card{border:1px solid var(--line);border-radius:24px;background:rgba(255,255,255,.94);box-shadow:0 14px 44px rgba(15,23,42,.08);padding:18px;margin-bottom:14px}
.core-title-line{display:flex;align-items:center;justify-content:space-between;gap:12px}
.core-title-left{display:contents}
.core-day{flex-shrink:0}
.core-ticker{font-size:19px;font-weight:950;letter-spacing:-.045em}
.core-name{color:var(--ink);font-size:19px;font-weight:800;letter-spacing:-.02em}
.core-industry{color:var(--muted);font-size:19px;font-weight:950;letter-spacing:-.045em}
.core-day.pos{color:var(--green)}
.core-day.neg{color:var(--red)}
.pill{display:inline-flex;align-items:center;border-radius:999px;padding:3px 10px;font-size:12px;font-weight:950;border:1px solid rgba(99,102,241,.18)}
.pill.status.thesis{background:var(--blue-soft);color:#1d4ed8}
.pill.status.modeled{background:var(--green-soft);color:var(--green)}
.pill.status.quickread{background:var(--amber-soft);color:var(--amber)}
.pill.status.screened{background:var(--slate-soft);color:var(--slate)}
.core-quote-grid{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:8px;margin-top:14px}
.core-quote-item{border:1px solid var(--line);border-radius:14px;background:rgba(248,250,252,.8);padding:10px 11px}
.core-quote-item span{display:block;color:var(--muted);font-size:11px;font-weight:800;text-transform:uppercase;letter-spacing:.06em}
.core-quote-item b{display:block;margin-top:4px;font-size:15px}
.news-line{margin-top:10px;padding:10px 12px;border:1px solid var(--line);border-radius:14px;background:rgba(248,250,252,.7);font-size:13px;color:#334155}
.minor-multiples{margin-top:8px;font-size:12px;color:var(--muted)}
/* Core Watch 估值气泡：每个口径一个胶囊，贵/便宜染色 */
.core-valuation{margin-top:12px;padding-top:10px;border-top:1px dashed var(--line);display:flex;flex-wrap:wrap;gap:6px;font-size:12px}
.news-line{font-size:12.5px}.news-tag{display:inline-block;padding:1px 7px;border-radius:8px;background:rgba(59,130,246,.12);color:#2563eb;font-size:11px;font-weight:800;margin-right:2px}
.val-bubble{display:inline-flex;align-items:baseline;gap:5px;border-radius:999px;padding:3px 11px;border:1px solid var(--line);background:var(--card);color:var(--ink);white-space:nowrap;font-weight:650}
.val-bubble-label{color:var(--muted);font-size:10.5px;font-weight:800;letter-spacing:.3px}
.val-bubble .val-note{color:var(--amber);font-weight:800;font-size:10px}
.val-bubble.val-rich{border-color:rgba(211,59,59,.5);background:var(--red-soft);color:var(--red)}
.val-bubble.val-cheap{border-color:rgba(15,159,110,.5);background:var(--green-soft);color:var(--green)}
.grid-2{display:grid;grid-template-columns:repeat(auto-fill,minmax(340px,1fr));gap:14px}
.grid-3{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:14px}
.mover-card{border:1px solid var(--line);border-radius:24px;background:rgba(255,255,255,.94);box-shadow:0 14px 44px rgba(15,23,42,.08);padding:18px}
.mover-card.important{border-left:4px solid var(--amber)}
.mover-card.minor{border-left:4px solid rgba(100,116,139,.35)}
.mover-card.minor .core-ticker,.mover-card.minor .core-name,.mover-card.minor .core-industry,.mover-card.minor .core-day{font-size:16px}
.mover-card.minor .core-quote-item b{font-size:13px}
.mover-detail{margin-top:12px;padding-top:12px;border-top:1px solid var(--line)}
.mover-reason{margin-bottom:6px;font-size:13px;font-weight:700;color:var(--ink)}
.mover-links{margin:6px 0 0;padding-left:18px;font-size:12px;line-height:1.7;color:#334155}
.mover-links a{color:var(--blue);text-decoration:none}
details{border:1px solid var(--line);border-radius:16px;background:rgba(255,255,255,.72);padding:10px 12px;margin-top:8px}
summary{cursor:pointer;font-weight:950;color:#1e3a8a}
ul{margin:10px 0 0;padding-left:18px;color:#334155;line-height:1.7}
.health-line{border:1px solid var(--line);border-radius:18px;background:rgba(255,255,255,.9);padding:14px 18px;font-size:14px;font-weight:700}
.health-line .bad{color:var(--amber)}
.grid-2 .core-watch-card{margin-bottom:0}
/* ── 响应式：手机（≤640px）紧凑 + 表格隐藏次要列 + 安全区 ── */
@media(max-width:640px){
main{width:calc(100vw - 20px);margin:16px auto 32px}
h2{font-size:16px}
.hero{font-size:12px;padding:6px 10px}
.tab-nav{margin:12px 0 20px;padding:6px 8px;gap:8px}
.tab-button{padding:7px 11px;font-size:12px}
.card,.core-watch-card,.mover-card{padding:12px;border-radius:18px}
.core-ticker,.core-name,.core-industry{font-size:16px}
.core-quote-grid{grid-template-columns:repeat(3,minmax(0,1fr));gap:6px}
.core-quote-item{padding:7px 8px}
.core-quote-item b{font-size:13px}
.table-card{max-height:58vh;border-radius:16px}  /* 保留容器滚动 → 表头 sticky 冻结 */
.table-card table{min-width:420px;font-size:11.5px}
th,td{padding:4px 2px;height:28px}
td.m,th.m{display:none}  /* 表格次要列：手机上隐藏（核心列保留） */
.news-line{font-size:12px;padding:8px 10px}
.health-line{font-size:13px;padding:12px 14px}
body{padding-bottom:env(safe-area-inset-bottom)}
}
"""


def _ret_class(v: Any) -> str:
    if v is None:
        return "ret na"
    return "ret pos" if float(v) >= 0 else "ret neg"


def _val_cell_html(row: dict[str, Any], field: str, vs_field: str) -> str:
    val = row.get(field)
    if val is None:
        return '<span class="val-na">—</span>'
    vs = row.get(vs_field)
    cls = rich_class(vs)
    text = fmt_cell(val, vs)
    if cls == "rich":
        return f'<span class="val-rich">{text}</span>'
    if cls == "cheap":
        return f'<span class="val-cheap">{text}</span>'
    return f"<span>{text}</span>"


def _market_grp(ticker: str) -> str:
    '''ticker → 市场组（美股/亚盘/欧盘），用于时点摘要。'''
    t = (ticker or "").upper()
    if t.endswith((".US",)):
        return "美股"
    if t.endswith((".L", ".DE", ".PA", ".OL", ".ST", ".MI", ".MC", ".HE", ".AS", ".KL", ".TO")):
        return "欧盘"
    if t.endswith((".KS", ".KQ", ".T", ".JP", ".SS", ".SZ", ".SH", ".HK", ".TW", ".TT", ".CN")):
        return "亚盘"
    return ""


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
        _g = _market_grp(e.ticker or "")
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
            return f"<span title='行情数据早于今日'>{short} 旧</span>"
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
) -> str:
    ents = filter_entries(entries, report_type)
    rt_label = {"us": "美股盘后", "asia": "亚盘盘后", "eu": "欧盘盘后"}.get(report_type, report_type)
    core_count = sum(1 for e in ents if e.monitor_status == "Core")
    review_map = review_map or {}
    _protect = protect_names(entries)

    # ── 估值表 ──
    uni_rows = []
    last_ind = None
    for e in _universe_sorted(ents, snapshots):
        if e.industry != last_ind:
            uni_rows.append(f'<tr class="industry-row"><td colspan="13">{_h.escape(e.industry or "Other")}</td></tr>')
            last_ind = e.industry
        snap = snapshots.get(e.ticker or e.company, {})
        vrow = snap.get("valuation") or {}
        pe_n_extra = fwd_extra(vrow, "PE")
        ev_n_extra = fwd_extra(vrow, "EV/EBITDA")
        _fwd_pe = _fwd_ntm_pe(snap, estimates, e.ticker or e.company)
        _pe_ntm_val = _fwd_pe if _fwd_pe is not None else vrow.get("pe_ntm")
        _pe_ntm_extra = "L1 fwd" if _fwd_pe is not None else pe_n_extra
        uni_rows.append(
            "<tr>"
            f"<td>{_h.escape(_display_name(e))}</td>"
            f"<td class='m'>{_h.escape(e.ticker or '')}</td>"
            f"<td class='m'>{_h.escape(e.industry or '—')}</td>"
            f'<td class="{_ret_class(snap.get("price_move_pct"))}">{_fmt_pct(snap.get("price_move_pct"))}</td>'
            f'<td class="{_ret_class(vrow.get("ret_1m"))}">{_fmt_pct(vrow.get("ret_1m"))}</td>'
            f'<td class="{_ret_class(vrow.get("ret_ytd"))}">{_fmt_pct(vrow.get("ret_ytd"))}</td>'
            f'<td class="{_ret_class(vrow.get("ret_1y"))}">{_fmt_pct(vrow.get("ret_1y"))}</td>'
            f"<td class='m'>{_val_cell_html(vrow, 'pe_ttm', 'pe_ttm_vs_5y')}</td>"
            f"<td>{_h.escape(fmt_cell(_pe_ntm_val, extra=_pe_ntm_extra))}</td>"
            f"<td class='m'>{_val_cell_html(vrow, 'ev_ttm', 'ev_ttm_vs_5y')}</td>"
            f"<td>{_h.escape(fmt_cell(vrow.get('ev_ntm'), extra=ev_n_extra)) or '—'}</td>"
            f"<td class='m'>{_h.escape(str(snap.get('next_earnings') or '—'))}</td>"
            f"<td class='m'>{_h.escape(e.coverage_status or '—')}</td>"
            f"<td class='m'>{_quote_time_cell(snap)}</td>"
            "</tr>"
        )

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

    # ── Core Watch：Status 核心到边缘 + 财报临近置顶 ──
    core_html = ""
    core_ents = [e for e in ents if e.monitor_status == "Core"]

    def _core_key(e):
        _snap = snapshots.get(e.ticker or e.company, {})
        _st = _STATUS_ORDER.get((e.coverage_status or "").strip(), 9)
        _nc = str(_snap.get("next_earnings") or "9999-99-99")
        return (_st, _nc)

    for e in sorted(core_ents, key=_core_key):
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
        minor = ""
        core_html += (
            f"<div class='core-watch-card'><div class='core-title-line'><div class='core-title-left'>"
            f"<span class='core-ticker'>{_h.escape(e.ticker or '')}</span>"
            f"<span class='core-name'>{_h.escape(_display_name(e))}</span>"
            f"<span class='core-industry'>{_h.escape(e.industry or '')}</span>"
            f"<span class='pill status {str(e.coverage_status or '').lower()}'>{_h.escape(e.coverage_status or '')}</span>"
            f"</div><span class='{day_cls}'>{_fmt_pct(snap.get('price_move_pct'))}</span></div>"
            f"<div class='core-quote-grid'>"
            f"<div class='core-quote-item'><span>Price</span><b>{_fmt_price(snap)}</b></div>"
            f"<div class='core-quote-item'><span>Cap</span><b>{_fmt_cap(snap.get('market_cap'))}</b></div>"
            f"<div class='core-quote-item'><span>1m</span><b>{_fmt_pct(vrow.get('ret_1m'))}</b></div>"
            f"<div class='core-quote-item'><span>YTD</span><b>{_fmt_pct(vrow.get('ret_ytd'))}</b></div>"
            f"<div class='core-quote-item'><span>1y</span><b>{_fmt_pct(vrow.get('ret_1y'))}</b></div>"
            f"<div class='core-quote-item'><span>Next</span><b>{_h.escape(str(snap.get('next_earnings') or '—'))}</b></div>"
            f"</div>{val_line}{minor}{head}</div>"
        )
    if core_html:
        core_html = f"<div class='grid-2'>{core_html}</div>"
    else:
        core_html = "<div class='health-line'>无 Core 名单。</div>"

    # ── Review Queue：7 天内显示；7-30 天表格内折叠 ──
    rq_entries, rq_mid = [], []
    for e in ents:
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

    body = f"""
<!doctype html><html lang="zh-Hans"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Daily Brief {today} · {rt_label}</title>
<style>{_CSS}</style></head><body><main>
<section class="hero">
  <span class="hero-date">{today} · {rt_label} · 数据来源：FMP</span>{_tz_summary(ents, snapshots)}
  <span class="hero-stat">{len(ents)} names</span>
  <span class="hero-stat">{core_count} Core Watch</span>
  <span class="hero-stat">{len(important)} movers</span>
  <span class="hero-stat">{len(rq_entries)} actions</span>
</section>
<nav class="tab-nav">
  <a class="tab-button" href="#review">Review Queue</a>
  <a class="tab-button" href="#universe">Valuation Universe</a>
  <a class="tab-button" href="#movers">Movers</a>
  <a class="tab-button" href="#core">Core Watch</a>
  <a class="tab-button" href="#health">Data Health</a>
</nav>
<section id="review" class="tab-panel"><div class="section-head"><h2>Review Queue</h2>
<p>财报临近（&lt;7 天）。</p></div>
<div class="table-card"><table><thead><tr><th>触发</th><th>Company</th><th>Ticker</th><th>Status</th><th>触发详情</th></tr></thead>
<tbody>{rq_rows}{rq_fold}</tbody></table></div></section>
<section id="universe" class="tab-panel"><div class="section-head"><h2>Valuation Universe</h2>
<p>括号 = 相对 5y 中位%。加粗/红 = 贵（&gt;+30%）· 绿 = 便宜（&lt;-30%）。`fwd x` = 你的 fwd 假设。</p></div>
<div class="table-card"><table><thead><tr><th>Company</th><th class='m'>Ticker</th><th class='m'>Industry</th><th>Today</th><th>1m</th><th>YTD</th><th>1y</th><th class='m'>PE_TTM</th><th>PE_NTM</th><th class='m'>EV/EBITDA_TTM</th><th>EV/EBITDA_NTM</th><th class='m'>Next_Call</th><th class='m'>Status</th><th class='m'>行情时间</th></tr></thead>
<tbody>{''.join(uni_rows)}</tbody></table></div></section>
<section id="movers" class="tab-panel"><div class="section-head"><h2>Movers</h2></div>{mover_html}</section>
<section id="core" class="tab-panel"><div class="section-head"><h2>Core Watch</h2></div>{core_html}</section>
<section id="health" class="tab-panel"><div class="section-head"><h2>Data Health</h2></div>{health}</section>
</main></body></html>"""
    return body
