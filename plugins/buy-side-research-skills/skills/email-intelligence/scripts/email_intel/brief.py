"""Render a lightweight, Outlook-compatible five-section Email Brief."""

from __future__ import annotations

import html
import re
from collections import defaultdict
from datetime import date, datetime

from .parse import Email


BLUE = "#2563eb"
GREEN = "#0f9f6e"
RED = "#d33b3b"
AMBER = "#b7791f"
MUTED = "#64748b"
INK = "#132238"
BODY_BG = "#edf2f6"
CARD_BG = "#ffffff"
BORDER = "#d8e0ea"


# section 元数据：WYT = 01（单独渲染），Industry = 02（单独），其余按 bucket
_BUCKET_META = {
    "core": ("03", "Core Watch"),
    "other_coverage": ("04", "Other Coverage"),
    "new_idea": ("05", "New Ideas"),
}


def _e(value) -> str:
    return html.escape(str(value or ""), quote=True)


def _pill(text: str, color: str) -> str:
    return (f"<span style='display:inline-block;border:1px solid {color}33;border-radius:999px;"
            f"padding:1px 7px;font-size:10px;font-weight:800;color:{color};'>{_e(text)}</span>")


def _section_head(number: str, title: str) -> str:
    return (f"<div style='font-size:18px;line-height:26px;font-weight:900;color:{INK};"
            f"letter-spacing:-.03em'>{number} · {_e(title)}</div>")


def _email_map(emails: list[Email]) -> dict[str, Email]:
    return {email.key: email for email in emails}


def _source_link(email: Email | None) -> str:
    if not email:
        return ""
    label = email.sender or "Original email"
    if email.outlook_link:
        return f"<a href='{_e(email.outlook_link)}' style='color:{BLUE};text-decoration:none'>↗ {_e(label)}</a>"
    return _e(label)


def _merge_items(reviews: list[dict]) -> list[dict]:
    merged: dict[str, dict] = {}
    for review in reviews:
        email_id = review.get("_email_id", "")
        for item in review.get("items") or []:
            one = dict(item)
            one["_email_ids"] = [email_id]
            # 同公司（无论事件）合一条：company 名一致即合并，多条券商/summary 并排
            cname = str(one.get("company") or "").strip().lower()
            key = f"co:{cname}" if cname else (one.get("merge_key") or f"{email_id}:{len(merged)}")
            if key not in merged:
                merged[key] = one
                continue
            current = merged[key]
            if email_id and email_id not in current["_email_ids"]:
                current["_email_ids"].append(email_id)
            if not current.get("why_it_matters") and one.get("why_it_matters"):
                current["why_it_matters"] = one["why_it_matters"]
            if current.get("priority") != "high" and one.get("priority") == "high":
                current["priority"] = "high"
            # summary 拼接（同公司不同事件/券商 → 一条，要点合并）
            s1, s2 = str(current.get("summary") or ""), str(one.get("summary") or "")
            if s2 and s2 not in s1:
                current["summary"] = (s1 + "；" + s2) if s1 else s2
    return list(merged.values())


def _merge_meetings(reviews: list[dict]) -> list[dict]:
    meetings: dict[str, dict] = {}
    for review in reviews:
        email_id = review.get("_email_id", "")
        for meeting in review.get("meetings") or []:
            one = dict(meeting)
            one["_email_id"] = email_id
            key = "|".join(str(one.get(k) or "").lower() for k in ("title", "company", "date", "time"))
            meetings.setdefault(key or f"{email_id}:{len(meetings)}", one)
    rank = {"high": 0, "medium": 1, "low": 2}
    return sorted(meetings.values(), key=lambda item: (rank.get(str(item.get("recommendation")), 9), str(item.get("date") or "")))


def _company_text(e) -> str:
    return e.get("company") or e.get("ticker") or (e.get("industry") or "Signal")


_BROKER_MAP = {
    # 发件券商域 → 机构名（broker 配对）
    "ubs.com": "UBS", "bernsteinsg.com": "Bernstein", "morganstanley.com": "Morgan Stanley",
    "jefferies.com": "Jefferies", "nomura.com": "Nomura", "bofa.com": "BofA", "citi.com": "Citi",
    "mailservice.cjsc.com.cn": "长江证券", "cjsc.com.cn": "长江证券", "cjsc.com.hk": "长江证券",
    "guangfa.com.cn": "广发证券", "gfgroup.com.hk": "广发证券",
    "gs.com": "Goldman Sachs", "mail.marquee.gs.com": "Goldman Sachs", "alerts.publishing.gs.com": "Goldman Sachs",
    "clsa.com": "CLSA", "research.meritco-group.com": "久谦", "meritco-group.com": "久谦",
    "thirdbridge.com": "Third Bridge", "eci.com": "ECI", "newsletter.cioe.cn": "CIOE",
}



def _norm_time(raw) -> str:
    """会议时间规范化 → 保留带时区，去掉冗余秒/重复日期。"""
    t = str(raw or "").strip()
    if not t:
        return ""
    t = re.sub(r"(\d{1,2}):(\d{2}):(\d{2})", r"\1:\2", t)      # 去掉秒 19:00:00→19:00
    return t


def _broker_label(sender: str, broker: str = "") -> str:
    """机构名：优先 deep 提取的 broker 字段；缺失则 sender 域精确配对（+子域兜底）。"""
    if broker:
        return broker.strip()
    s = (sender or "").strip()
    if "@" not in s:
        return s
    d = s.rsplit("@", 1)[1].lower()
    if d in _BROKER_MAP:
        return _BROKER_MAP[d]
    parts = d.split(".")
    if len(parts) > 2 and ".".join(parts[-2:]) in _BROKER_MAP:
        return _BROKER_MAP[".".join(parts[-2:])]
    return s


def _links_group(source_ids: list, emails: dict) -> str:
    out = []
    for key in source_ids:
        em = emails.get(key)
        if not em:
            continue
        label = _broker_label(em.sender, getattr(em, 'broker', ''))
        if em.outlook_link:
            out.append(f"<a class='src' href='{_e(em.outlook_link)}'>{_e(label)}</a>")
        else:
            out.append(f"<span class='src' style='color:#94a3b8'>{_e(label)}</span>")
    return " · ".join(out)


def _status_pill(tier: str) -> str:
    cls = {"Modeled": "st-modeled", "Quickread": "st-quickread", "Screened": "st-screened",
           "Uncovered": "st-uncovered", "Thesis": "st-thesis"}.get(tier or "", "st-screened")
    return f"<span class='st {cls}'>{_e(tier or 'Screened')}</span>"


def _meeting_line_v2(m: dict, emails: dict, embed: bool = False) -> str:
    """会议卡固定槽位：标题|机构 / 形式·语言|时间 / 讲者·看点·主持 / related chips。

    每个字段有固定位置；字段缺失时该槽留白（不压缩/不上移其他字段），所有卡布局一致。
    （不显示"限 N 位"席位，只保留 线上/线下 + 中文/英文。）
    """
    title = m.get("title") or m.get("company") or "Meeting"
    em = emails.get(str(m.get("_email_id") or ""))
    reg = str(m.get("registration") or "")
    org = _e(_broker_label(em.sender, getattr(em, 'broker', ''))) if em else ''
    link_title = (f"<a class='src' style='font-weight:800;color:#2563eb' href='{_e(reg)}'>{_e(title)}</a>"
                  if reg.startswith("http") else
                  f"<span style='font-weight:800;color:#2563eb'>{_e(title)}</span>")
    org_html = (f"<a class='src' href='{_e(em.outlook_link)}'>{org}</a>"
                if (em and em.outlook_link) else
                (f"<span class='src' style='color:#94a3b8'>{org}</span>" if org else ""))
    # 行2：形式(线上/线下) · 语言(中文/英文)——只这两个，去限席
    fmt = " · ".join(x for x in [m.get("format") or "", m.get("language") or ""] if x)
    time_s = _norm_time(m.get("time"))
    # 行3：讲者·看点·主持
    parts = []
    if m.get("participants"):
        parts.append("讲者：" + _e(str(m["participants"])))
    agenda = m.get("agenda_items") or []
    if agenda:
        parts.append("看点：" + _e("·".join(str(x) for x in list(agenda)[:3])))
    if m.get("host_person"):
        parts.append("主持：" + _e(m["host_person"]))
    ppl = " · ".join(parts)
    # 行4：related chips
    rel = m.get("related_tickers") or []
    chips = "".join(f"<span class='chip'>{_e(str(x))}</span>" for x in list(rel)[:6])

    return (
        f"<div class='m-line'><span class='m-cell'>{link_title}</span><span class='m-cell m-end'>{org_html}</span></div>"
        f"<div class='m-line'><span class='m-cell m-sub'>{_e(fmt)}</span><span class='m-cell m-end m-time'>{_e(time_s)}</span></div>"
        f"<div class='m-line'><span class='m-cell m-sub'>{_e(ppl)}</span><span class='m-cell'></span></div>"
        f"<div class='m-line'><span class='m-cell'>{chips}</span><span class='m-cell'></span></div>"
    )


def _industry_card_v2(industry: str, sec: dict, emails: dict) -> str:
    blocks = [f"<div class='card ind-card'><div class='card-title'><b>{_e(industry)}</b> "
              f"<span class='small' style='color:#64748b;font-weight:800'>"
              f"{len(sec['industry']) + len(sec['company'])} 条 · {len(sec['meeting'])} 场</span></div>"]
    if sec["industry"]:
        blocks.append("<div class='small grouplabel'>行业面</div>")
        for item in sec["industry"]:
            src = _links_group(item.get("_email_ids", []), emails)
            body = item.get("what_changed") or item.get("summary")
            if str(body or "").startswith("首次出现"):
                body = item.get("summary")
            if not body:
                continue  # 无内容的行业面行不渲染空行
            blocks.append(f"<div class='m-line'><span class='m-cell'>· {_e(str(body))}</span>"
                          f"<span class='m-cell m-end'>{src}</span></div>")
    if sec["company"]:
        blocks.append("<div class='small grouplabel'>公司变化</div>")
        for item in sec["company"]:
            tier = item.get("coverage_status") or ""
            core = "<span class='core-pill'>Core</span>" if tier in ("Modeled", "Thesis") else ""
            name = item.get("company") or _company_text(item)
            tick = f"<b>{_e(name)} ({_e(item['ticker'])})</b>" if item.get("ticker") else f"<b>{_e(name)}</b>"
            _st = _status_pill(tier) if tier else ""
            src = _links_group(item.get("_email_ids", []), emails)
            body = item.get("what_changed") or item.get("summary")
            if str(body or "").startswith("首次出现"):
                body = item.get("summary")
            brief = _e(str(body or ""))
            blocks.append(f"<div class='m-line'><span class='m-cell'>· {tick} {_st}{core} {brief}</span>"
                          f"<span class='m-cell m-end'>{src}</span></div>")
    if sec["meeting"]:
        blocks.append("<div class='small grouplabel'>会议</div>")
        for m in sec["meeting"]:
            blocks.append(_meeting_line_v2(m, emails))
    blocks.append("</div>")
    return "\n".join(b for b in blocks if b)


def _company_card_v2(item: dict, emails: dict, meeting: dict | None, light: bool = False) -> str:
    name = item.get("company") or _company_text(item)
    if item.get("ticker"):
        name = f"{name} ({item['ticker']})"
    tier = item.get("coverage_status") or ""
    st = _status_pill(tier) if tier else ""
    core = "<span class='core-pill'>Core</span>" if tier in ("Modeled", "Thesis") else ""
    src = _links_group(item.get("_email_ids", []), emails)
    summary = _e(str(item.get("summary") or item.get("what_changed") or ""))
    meeting_block = _meeting_line_v2(meeting, emails) if meeting else ""
    return (f"<div class='card ind-card'>"
            f"<div class='m-line'><span class='m-cell'><b>{_e(name)}</b> {st}{core}</span>"
            f"<span class='m-cell m-end'>{src}</span></div>"
            f"<div class='m-line'><span class='m-cell'>{summary}</span><span class='m-cell'></span></div>"
            f"{meeting_block}</div>")


def _wyt_rows_v2(items: list, emails: dict) -> str:
    top = sorted(items, key=lambda i: {"high": 0, "medium": 1, "low": 2}.get(str(i.get("priority")), 9))[:3]
    seq = ["❶", "❷", "❸"]
    rows = []
    for i, item in enumerate(top):
        if not (item.get("summary") or item.get("what_changed")):
            continue
        name = item.get("company") or _company_text(item)
        src = _links_group(item.get("_email_ids", []), emails)
        body = _e(str(item.get("summary") or item.get("what_changed")))
        rows.append(
            f"<div class='wyt-row'><div class='wyt-head'>{seq[i]} {_e(name)}</div>"
            f"<div class='m-line'><span class='m-cell'>{body}</span>"
            f"<span class='m-cell m-end'>{src}</span></div></div>")
    return "<div class='card'>" + "<hr class='sep'>".join(rows) + "</div>"


# v1 card（兼容 render_brief_html 旧入口）
def _item_card(item: dict, emails: dict[str, Email], bar: str, followup: bool = False) -> str:
    company = item.get("company") or item.get("industry") or "Signal"
    ticker = item.get("ticker") or item.get("coverage_ticker") or ""
    event = str(item.get("event_type") or item.get("kind") or "UPDATE").upper()
    action = str(item.get("action") or "note").upper()
    priority = str(item.get("priority") or "medium").upper()
    sources = [_source_link(emails.get(key)) for key in item.get("_email_ids", [])]
    sources = [source for source in sources if source]
    meta = " &nbsp; ".join(part for part in [_pill(event, bar), _pill(action, bar), _pill(priority, bar)] if part)
    delta_line = f"<div style='margin-top:5px;font-size:12.5px;line-height:20px;color:#9a3412'><b>新增：</b>{_e(item['delta_vs_last'])}</div>" if item.get("delta_vs_last") else ""
    source_line = f"<div style='margin-top:7px'>{' · '.join(sources)}</div>" if sources else ""
    return f"""
<table role='presentation' width='100%' cellpadding='0' cellspacing='0' border='0' style='border:1px solid {BORDER};background:{CARD_BG};border-radius:14px'>
<tr><td width='4' style='background:{bar}'></td><td style='padding:12px 14px'>
<div style='font-size:14px;line-height:21px;font-weight:900;color:{INK}'>{_e(company)}{f" <span style='color:{MUTED};font-size:11px'>({_e(ticker)})</span>" if ticker else ""}</div>
<div style='margin-top:4px'>{meta}</div>
<div style='font-size:12.5px;line-height:20px;color:#334155;margin-top:7px'>{_e(item.get('what_changed') or '—')}</div>
{delta_line}{source_line}
</td></tr></table>"""


def render_email_markdown(emails: list[Email], reviews: list[dict], now_label: str,
                          window_label: str = "") -> str:
    """邮件正文 markdown：WYT + 按行业聚合 + meetings（源机构名）。"""
    email_by_id = _email_map(emails)
    # 从 deep 提取把 broker（机构名）挂到邮件对象，渲染来源标签用
    _broker_by_email = {}
    for _r in reviews:
        _b = _r.get("broker")
        if _b and _r.get("_email_id"):
            _broker_by_email.setdefault(_r["_email_id"], _b)
    for _em in emails:
        try:
            _em.broker = _broker_by_email.get(_em.key, "")
        except Exception:
            pass
    items = _merge_items(reviews)
    meetings = _merge_meetings(reviews)
    srcs = lambda ids: " · ".join(dict.fromkeys(str(_broker_label(email_by_id[k].sender)) for k in ids if k in email_by_id))
    out = [f"# Email Intelligence Brief — {now_label}", "", f"> {window_label}", ""]
    top = sorted(items, key=lambda i: {"high": 0, "medium": 1, "low": 2}.get(str(i.get("priority")), 9))[:3]
    if top:
        out.append("**值得花时间**")
        out.append("")
        for it in top:
            print("")
        for it in top:
            name = it.get("company") or _company_text(it)
            out.append(f"- **{name}** — {str(it.get('summary') or it.get('what_changed') or '')}（{srcs(it.get('_email_ids', []))}）")
        out.append("")
    by_industry: dict[str, dict] = defaultdict(lambda: {"industry": [], "company": [], "meeting": []})
    for it in items:
        ind = it.get("industry") or "Other"
        by_industry[ind]["company" if str(it.get("bucket")) != "industry_signal" else "industry"].append(it)
    for m in meetings:
        by_industry[m.get("industry") or "Other"]["meeting"].append(m)
    out.append("**行业**")
    out.append("")
    for ind, sec in sorted(by_industry.items(), key=lambda kv: -sum(len(v) for v in kv[1].values())):
        out.append(f"### {ind}")
        for it in sec["industry"]:
            body = str(it.get("what_changed") or it.get("summary") or "")
            if body.startswith("首次出现"):
                body = str(it.get("summary") or "")
            if body:
                out.append(f"- {body}（{srcs(it.get('_email_ids', []))}）")
        for it in sec["company"]:
            name = it.get("company") or _company_text(it)
            out.append(f"- **{name}** — {str(it.get('summary') or it.get('what_changed') or '')}（{srcs(it.get('_email_ids', []))}）")
        for m in sec["meeting"]:
            out.append(f"- 🗓 {m.get('title')} · {m.get('date')} {m.get('time')} · {m.get('host') or ''}")
        out.append("")
    if meetings:
        out.append(f"**Meetings（{len(meetings)} 场）**")
        out.append("")
        for m in meetings:
            out.append(f"- {m.get('title')} — {m.get('date')} {m.get('time')} · {m.get('host') or ''}（{srcs([m.get('_email_id')])}）")
    return "\n".join(out).rstrip()


_CSS_V2 = """
body{margin:0;font-family:"Noto Sans SC","Microsoft YaHei","PingFang SC",sans-serif;font-variant-numeric:tabular-nums;background:#f6f8fb;color:#1e293b}
main{margin:24px 0 40px}
.scope-note{border-left:3px solid #2563eb;background:#f4f8ff;color:#64748b;font-size:12px;line-height:1.65;padding:8px 12px;margin:0 0 18px;border-radius:0 10px 10px 0}
.section-head h2{margin:0;font-size:19px;letter-spacing:-.03em}
.section-head{margin:22px 0 10px}
.card{border:1px solid #d8dee9;border-radius:14px;padding:16px;margin-bottom:14px;background:#ffffff}
.card-title b{font-size:14px}
.tk{color:#64748b;font-size:12px}
.tk a{color:#2563eb;text-decoration:none}
.txt{font-size:13.5px;line-height:1.75;color:#334155;margin-top:7px}
.small{font-size:11.5px;color:#94a3b8;line-height:1.65;margin-top:6px}
.src{color:#2563eb;text-decoration:none;font-weight:650;font-size:11.5px}
.st{display:inline-flex;align-items:center;height:19px;border-radius:999px;padding:0 7px;font-size:10px;font-weight:950;line-height:1;border:1px solid rgba(99,102,241,.18);margin:0 4px 4px 0}
.st-modeled{background:#dff7eb;color:#0f9f6e}
.st-quickread{background:#fff7d6;color:#b7791f}
.st-screened{background:#e2e8f0;color:#475569}
.st-uncovered{background:#ffe4e6;color:#d33b3b}
.chip{display:inline-block;border-radius:8px;background:#f1f5f9;border:1px solid #e2e8f0;color:#475569;padding:1px 7px;font-size:11px;margin:2px 3px 2px 0}
.sep{border:0;border-top:1px solid #eef2f7;margin:9px 0}
.wyt-row{padding:8px 0}
.wyt-head{font-size:15px;font-weight:800;color:#132238}
.wyt-update{font-size:14px;line-height:1.7;color:#334155;margin-top:4px}
.ind-card{flex:1 1 280px;box-sizing:border-box;margin-bottom:0}
.line{display:flex;justify-content:space-between;align-items:baseline;gap:12px;margin-top:7px}
.line-main{font-size:13.5px;line-height:1.7;color:#334155}
.line-links{white-space:nowrap;flex-shrink:0;text-align:right;font-size:11.5px}
.line-grid{display:grid;grid-template-columns:1fr 130px 1fr;align-items:center;gap:8px;margin-top:7px}
.line-grid .line-main{min-width:0}
.line-mid{text-align:center;font-weight:750;font-size:13.5px;color:#334155;white-space:nowrap}
.line-end{align-items:flex-end}
.links-row{text-align:right;font-size:11.5px;margin-top:4px}
.gapnote{font-size:11.5px;color:#94a3b8;margin-top:10px}
.grouplabel{color:#1e293b;font-weight:800;margin-top:10px;padding-top:6px;border-top:1px solid #e2e8f0}
.core-pill{display:inline-flex;align-items:center;height:19px;border-radius:999px;padding:0 7px;background:#7c3aed;color:#fff;font-size:10px;font-weight:950;line-height:1;margin:0 4px 4px 0}
.card-meeting{margin-top:8px;padding:8px 0 2px;border-top:1px dashed #e2e8f0;color:#64748b}
.m-line{display:flex;justify-content:space-between;align-items:baseline;gap:12px;margin-top:5px;flex-wrap:nowrap}
.m-cell{min-width:0;font-size:13.5px;line-height:1.6;color:#334155;overflow-wrap:break-word;word-break:break-word}
.m-cell.m-end{text-align:right;flex-shrink:0;white-space:nowrap;margin-left:auto}
.m-cell.m-sub{font-size:12px;color:#64748b;min-height:16px}
.m-cell.m-time{font-weight:800;color:#132238;font-size:12px}

@media (max-width:640px){
  .card{padding:10px}
}

.indust-grid{display:grid;grid-template-columns:repeat(2,1fr)}
.indust-grid.cols-4{grid-template-columns:repeat(4,1fr)}
.indust-grid.cols-3{grid-template-columns:repeat(3,1fr)}
.ind-card{margin-bottom:0}
@media (max-width:640px){.indust-grid,.indust-grid.cols-4,.indust-grid.cols-3{grid-template-columns:1fr}}"""



def _industry_visible(ind: str, covered: list | None) -> bool:
    """Industry 卡是否显示：ind ∈ covered_industries，或与某覆盖行业 token 重合（相关行业）。"""
    if not covered:
        return True
    if ind in covered:
        return True
    ind_tokens = set(str(ind).lower().replace(" ", "-").split("-"))
    for c in covered:
        c_tokens = set(str(c).lower().split("-"))
        if ind_tokens & c_tokens:
            return True
    return False


def render_brief_html_v2(emails: list, reviews: list, now_label: str, window_label: str = "",
                         last_events: dict | None = None, covered_industries: list | None = None) -> str:
    email_by_id = _email_map(emails)
    # 从 deep 提取把 broker（机构名）挂到邮件对象，渲染来源标签用
    _broker_by_email = {}
    for _r in reviews:
        _b = _r.get("broker")
        if _b and _r.get("_email_id"):
            _broker_by_email.setdefault(_r["_email_id"], _b)
    for _em in emails:
        try:
            _em.broker = _broker_by_email.get(_em.key, "")
        except Exception:
            pass
    items = _merge_items(reviews)
    meetings = _merge_meetings(reviews)
    by_industry: dict[str, dict] = {}
    for item in items:
        ind = item.get("industry") or "Other"
        sec = by_industry.setdefault(ind, {"industry": [], "company": [], "meeting": []})
        if str(item.get("bucket") or "industry_signal") == "industry_signal":
            sec["industry"].append(item)
        else:
            sec["company"].append(item)
    for m in meetings:
        ind = m.get("industry") or "Other"
        by_industry.setdefault(ind, {"industry": [], "company": [], "meeting": []})["meeting"].append(m)

    blocks = ["<div class='section-head'><h2>01 · Worth Your Time</h2></div>",
              _wyt_rows_v2(items, email_by_id)]
    blocks.append("<div class='section-head'><h2>02 · Industry</h2></div><div class='indust-grid'>")
    for ind, sec in sorted(by_industry.items(),
                           key=lambda kv: -sum(len(v) for v in kv[1].values())):
        if not _industry_visible(ind, covered_industries):
            continue   # 无关行业省略（只留覆盖 + 相关）
        blocks.append(_industry_card_v2(ind, sec, email_by_id))
    blocks.append("</div>")

    for bucket, (num, title) in _BUCKET_META.items():
        rows = [i for i in items if str(i.get("bucket")) == bucket]
        if not rows:
            continue
        grid_cols = 'cols-3' if bucket == 'core' else 'cols-4'
        blocks.append(f"<div class='section-head'><h2>{num} · {title}</h2></div><div class='indust-grid {grid_cols}'>")
        for item in rows:
            mt = None
            for m in meetings:
                if m.get("company") and str(m["company"]).lower() in str(item.get("company") or "").lower():
                    mt = m
                    break
            blocks.append(_company_card_v2(item, email_by_id, mt,
                                           light=(bucket == "other_coverage")))
        blocks.append("</div>")

    filtered = [m for m in meetings if str(m.get("recommendation")) == "skip"]
    kept = [m for m in meetings if str(m.get("recommendation")) != "skip"]
    blocks.append("<div class='section-head'><h2>06 · Meetings</h2></div>")
    if kept:
        by_date: dict[str, list] = {}
        for m in kept:
            by_date.setdefault(str(m.get("date") or "TBD"), []).append(m)
        for date_key in sorted(by_date):
            blocks.append(f"<div class='small grouplabel' style='font-weight:800;color:#132238'>{str(date_key)}</div>")
            blocks.append("<div class='indust-grid cols-4' style='gap:10px'>")
            for m in by_date[date_key]:
                blocks.append("<div class='card ind-card'>" + _meeting_line_v2(m, email_by_id) + "</div>")
            blocks.append("</div>")
    blocks.append(f"<div class='small'>共 {len(meetings)} 场 · 已过滤 {len(filtered)} 场（行业不相关/无价值）· "
                  f"统计：{len(items)} 信号 · {len(emails)} 封</div>")
    body = "\n".join(b for b in blocks if b)
    return f"""<!doctype html><html lang="zh-Hans"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Email Intelligence Brief · {_e(now_label)}</title>
<style>{_CSS_V2}</style></head><body><main>
<div class="scope-note">Email Intelligence · {_e(now_label)} · {_e(window_label)} · as-of {_e(now_label[:10])} · 数据来源：OneDrive/Email-AI 卖方邮件</div>
{body}
</main></body></html>"""


# ------------------- v0 旧入口（单栏，保留兼容） -------------------
_SECTION_META = {
    "core": ("01", "Core Watch", BLUE),
    "other_coverage": ("02", "Other Coverage", "#64748b"),
    "new_idea": ("03", "New Ideas", GREEN),
    "industry_signal": ("04", "Industry & Sell-side Signals", AMBER),
}


def _meeting_card(meeting: dict, emails: dict[str, Email]) -> str:
    recommendation = str(meeting.get("recommendation") or "medium").lower()
    color = {"high": GREEN, "medium": AMBER, "low": MUTED}.get(recommendation, MUTED)
    details = []
    for label, key in (("日期", "date"), ("时段", "time"), ("主办", "host"), ("形式", "format"), ("地点", "location"), ("讲者", "participants")):
        if meeting.get(key):
            details.append(f"<b>{label}</b> {_e(meeting[key])}")
    source = _source_link(emails.get(meeting.get("_email_id", "")))
    return f"""
<table role='presentation' width='100%' cellpadding='0' cellspacing='0' border='0' style='border:1px solid {BORDER};background:{CARD_BG};border-radius:14px'>
<tr><td width='4' style='background:{color}'></td><td style='padding:12px 14px'>
<div style='font-size:14px;line-height:21px;font-weight:900;color:{INK}'>{_e(meeting.get('title') or meeting.get('company') or 'Meeting')}</div>
<div style='margin-top:4px'>{_pill(f"{recommendation.upper()} PRIORITY", color)}</div>
<div style='font-size:12px;line-height:20px;color:#334155;margin-top:7px'>{' &nbsp;·&nbsp; '.join(details)}</div>
<div style='font-size:12px;line-height:19px;color:{MUTED};margin-top:5px'><b>推荐：</b>{_e(meeting.get('reason') or '—')}</div>
{f"<div style='margin-top:7px'>{source}</div>" if source else ''}
</td></tr></table>"""


def render_brief_html(emails: list, reviews: list, now_label: str, window_label: str = "",
                      last_events: dict | None = None) -> str:
    """v0 单栏入口（保留兼容，不再默认使用）。"""
    email_by_id = _email_map(emails)
    # 从 deep 提取把 broker（机构名）挂到邮件对象，渲染来源标签用
    _broker_by_email = {}
    for _r in reviews:
        _b = _r.get("broker")
        if _b and _r.get("_email_id"):
            _broker_by_email.setdefault(_r["_email_id"], _b)
    for _em in emails:
        try:
            _em.broker = _broker_by_email.get(_em.key, "")
        except Exception:
            pass
    items = _merge_items(reviews)
    meetings = _merge_meetings(reviews)
    last_events = last_events or {}
    sections: dict[str, list[dict]] = defaultdict(list)
    for item in items:
        sections[item.get("bucket", "industry_signal")].append(item)
    priority_rank = {"high": 0, "medium": 1, "low": 2}
    for bucket in sections:
        sections[bucket].sort(key=lambda item: priority_rank.get(str(item.get("priority")), 9))

    top_items = sorted(items, key=lambda item: priority_rank.get(str(item.get("priority")), 9))[:3]
    top_lines = "".join(
        f"<li style='margin:4px 0'><b>{_e(item.get('company') or item.get('industry') or 'Signal')}：</b>{_e(item.get('what_changed'))}</li>"
        for item in top_items if item.get("what_changed")
    ) or "<li>本窗口没有需要优先处理的新变化。</li>"

    blocks = [f"""
<tr><td style='padding:16px 28px 7px'>
<table role='presentation' width='100%' style='background:#f8fafc;border:1px solid {BORDER};border-radius:14px'><tr><td style='padding:12px 14px'>
<div style='font-size:12px;font-weight:900;color:{INK}'>WORTH YOUR TIME</div>
<ul style='margin:6px 0 0;padding-left:18px;font-size:12.5px;line-height:20px;color:#334155'>{top_lines}</ul>
</td></tr></table></td></tr>"""]

    for bucket in ("core", "other_coverage", "new_idea", "industry_signal"):
        rows = sections.get(bucket, [])
        if not rows:
            continue
        number, title, color = _SECTION_META[bucket]
        blocks.append(f"<tr><td style='padding:20px 28px 7px'>{_section_head(number, title)}</td></tr>")
        for item in rows:
            followup = bool(item.get("merge_key") and item["merge_key"] in last_events)
            blocks.append(f"<tr><td style='padding:6px 28px'>{_item_card(item, email_by_id, color, followup)}</td></tr>")

    if meetings:
        blocks.append(f"<tr><td style='padding:20px 28px 7px'>{_section_head('05', 'Meetings')}</td></tr>")
        for meeting in meetings:
            blocks.append(f"<tr><td style='padding:6px 28px'>{_meeting_card(meeting, email_by_id)}</td></tr>")

    return f"""<!doctype html>
<html lang='zh-Hans'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
<title>Email Intelligence Brief · {_e(now_label)}</title>
<style>body,table,td,a{{-webkit-text-size-adjust:100%;-ms-text-size-adjust:100%}}table,td{{mso-table-lspace:0;mso-table-rspace:0}}table{{border-collapse:collapse!important}}@media(max-width:620px){{.container{{width:100%!important}}}}</style>
</head><body style="margin:0;padding:0;background:{BODY_BG};color:{INK};font-family:-apple-system,'Segoe UI','Microsoft YaHei',Arial,sans-serif">
<table role='presentation' width='100%' cellpadding='0' cellspacing='0' border='0'><tr><td align='center' style='padding:20px 8px 36px'>
<table role='presentation' class='container' width='920' cellpadding='0' cellspacing='0' border='0' style='width:100%;max-width:920px'>
<tr><td style='padding:16px 18px;background:{CARD_BG};border:1px solid {BORDER};border-radius:12px'>
<div style='font-size:11px;font-weight:900;letter-spacing:1px;color:{BLUE}'>AI EMAIL INTELLIGENCE</div>
<div style='font-size:22px;line-height:29px;font-weight:900;margin-top:6px'>What deserves your attention</div>
<div style='font-size:12px;line-height:19px;color:{MUTED};margin-top:3px'>{_e(window_label)}</div>
<div style='font-size:12px;line-height:19px;color:{MUTED};font-weight:800;margin-top:8px'>{len(items)} signals · {len(meetings)} meetings · {len(emails)} emails</div>
</td></tr>{''.join(blocks)}</table></td></tr></table></body></html>"""


# ------------------- Panel (附件增强版) -------------------
_CSS_PANEL = """
:root{--ink:#132238;--muted:#64748b;--line:rgba(148,163,184,.34);--card:rgba(255,255,255,.88);--blue:#2563eb;--green:#0f9f6e;--red:#d33b3b;--amber:#b7791f;--slate:#475569;--blue-soft:#dbeafe;--green-soft:#dff7eb;--red-soft:#ffe4e6;--amber-soft:#fff7d6;--slate-soft:#e2e8f0;--shadow:0 22px 70px rgba(15,23,42,.12)}
body{margin:0;color:var(--ink);font-family:"Noto Sans SC","Microsoft YaHei","PingFang SC",sans-serif;background:radial-gradient(1200px 500px at 8% -4%,rgba(37,99,235,.07),transparent 60%),radial-gradient(1000px 500px at 100% 0%,rgba(15,159,110,.06),transparent 55%),var(--slate-soft)}
main{width:min(1440px,calc(100vw - 36px));margin:28px auto 48px}
.hero{display:flex;align-items:center;gap:12px;flex-wrap:wrap;border:1px solid var(--line);border-radius:12px;padding:8px 16px;background:var(--card);box-shadow:0 4px 12px rgba(15,23,42,.06);font-size:13px}
.hero-date{color:var(--muted);font-weight:700;margin-right:auto}
.hero-stat{color:var(--ink);font-weight:800}
.scope-note{color:var(--muted);font-size:12px;line-height:1.65;border-left:3px solid var(--blue);background:rgba(37,99,235,.05);padding:8px 12px;margin:12px 0;border-radius:0 10px 10px 0}
.tab-nav{position:sticky;top:0;z-index:20;margin:18px 0 32px;display:flex;gap:10px;overflow-x:auto;padding:8px 10px;border-radius:16px;background:rgba(255,255,255,.92);box-shadow:0 4px 16px rgba(15,23,42,.06)}
.tab-button{display:inline-block;border-radius:12px;padding:8px 14px;color:var(--muted);font-weight:800;font-size:13px;text-decoration:none;white-space:nowrap}
.tab-button:hover{background:rgba(19,34,56,.06);color:var(--ink)}
.tab-panel{scroll-margin-top:80px;margin-bottom:32px}
.section-head{display:flex;justify-content:space-between;align-items:flex-end;gap:18px;margin:18px 2px 12px}
.section-head h2{margin:0;font-size:18px;letter-spacing:-.03em}
.card{border:1px solid var(--line);border-radius:18px;background:var(--card);box-shadow:0 14px 44px rgba(15,23,42,.08);padding:16px}
.card-title b{font-size:14px}
.txt{font-size:13.5px;line-height:1.7;color:#334155;margin-top:7px}
.small{font-size:12px;color:var(--muted);line-height:1.65;margin-top:6px}
.src{color:var(--blue);text-decoration:none;font-weight:650;font-size:12px}
.st{display:inline-flex;align-items:center;height:19px;border-radius:999px;padding:0 7px;font-size:10px;font-weight:950;line-height:1;border:1px solid rgba(99,102,241,.18);margin:0 4px 4px 0}
.st-modeled{background:var(--green-soft);color:var(--green)}
.st-quickread{background:var(--amber-soft);color:var(--amber)}
.st-screened{background:var(--slate-soft);color:var(--slate)}
.st-uncovered{background:var(--red-soft);color:var(--red)}
.st-thesis{background:var(--blue-soft);color:#1d4ed8}
.core-pill{display:inline-flex;align-items:center;height:19px;border-radius:999px;padding:0 7px;background:#7c3aed;color:#fff;font-size:10px;font-weight:950;line-height:1;margin:0 4px 4px 0}
.chip{display:inline-block;border-radius:8px;background:rgba(248,250,252,.9);border:1px solid var(--line);color:var(--slate);padding:1px 7px;font-size:11px;margin:2px 3px 2px 0}
.indust-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:14px}
.indust-grid.cols-4{grid-template-columns:repeat(4,1fr)}
.indust-grid.cols-3{grid-template-columns:repeat(3,1fr)}
.ind-card{flex:1 1 280px;box-sizing:border-box}
.line{display:flex;justify-content:space-between;align-items:baseline;gap:12px;margin-top:6px}
.line-main{font-size:13.5px;line-height:1.65;color:#334155}
.line-links{white-space:nowrap;flex-shrink:0;text-align:right;font-size:12px}
.grouplabel{color:var(--ink);font-weight:800;margin-top:10px;padding-top:6px;border-top:1px solid var(--line)}
.sep{border:0;border-top:1px solid var(--line);margin:10px 0}
.card-meeting{margin-top:10px;padding-top:8px;border-top:1px dashed var(--line);color:var(--muted)}
.m-line{display:flex;justify-content:space-between;align-items:baseline;gap:12px;margin-top:5px;flex-wrap:nowrap}
.m-cell{min-width:0;font-size:13.5px;line-height:1.6;color:#334155;overflow-wrap:break-word;word-break:break-word}
.m-cell.m-end{text-align:right;flex-shrink:0;white-space:nowrap;margin-left:auto}
.m-cell.m-sub{font-size:12px;color:#64748b;min-height:16px}
.m-cell.m-time{font-weight:800;color:#132238;font-size:12px}

.filter-row{display:flex;flex-wrap:wrap;align-items:center;gap:6px;margin:0 0 12px}
.filter-label{font-size:12px;font-weight:800;color:var(--muted)}
.filter-chip{display:inline-block;border-radius:999px;padding:4px 12px;font-size:12px;font-weight:700;border:1px solid var(--line);background:#fff;color:var(--slate);cursor:pointer}
.filter-chip.on{background:var(--blue);border-color:var(--blue);color:#fff}
.filter-clear{font-size:12px;color:var(--blue);cursor:pointer;font-weight:700}
.date-group-label{font-size:13.5px;font-weight:800;color:var(--ink);margin:16px 2px 8px}
.meeting-card.hidden{display:none}
.health-line{border:1px solid var(--line);border-radius:18px;background:rgba(255,255,255,.9);padding:14px 18px;font-size:12.5px;color:var(--muted)}
@media (max-width:640px){main{width:calc(100vw - 20px)}.card{padding:12px}.indust-grid,.indust-grid.cols-4,.indust-grid.cols-3{grid-template-columns:1fr}}

.indust-grid{display:grid;grid-template-columns:repeat(2,1fr)}
.indust-grid.cols-4{grid-template-columns:repeat(4,1fr)}
.indust-grid.cols-3{grid-template-columns:repeat(3,1fr)}
.meet-skip{opacity:.55}
@media (max-width:640px){.indust-grid,.indust-grid.cols-4,.indust-grid.cols-3{grid-template-columns:1fr}}"""


def _meeting_card_panel(m: dict, emails: dict, skip: bool = False) -> str:
    cls = "card ind-card meeting-card meet-skip" if skip else "card ind-card meeting-card"
    ind = _e(str(m.get("industry") or ""))
    return (f"<div class='{cls}' data-ind='{ind}'>" + _meeting_line_v2(m, emails) + "</div>")


_PANEL_SCRIPT = """<script>
(function(){
  var chips=document.querySelectorAll('.filter-chip');
  var cards=document.querySelectorAll('.meeting-card');
  chips.forEach(function(chip){
    chip.addEventListener('click',function(){
      var ind=chip.getAttribute('data-ind');
      chips.forEach(function(c){c.classList.remove('on')});
      chip.classList.add('on');
      cards.forEach(function(card){
        card.classList.toggle('hidden', card.getAttribute('data-ind')!==ind);
      });
    });
  });
  var clear=document.getElementById('filterClear');
  if(clear){clear.addEventListener('click',function(){
    chips.forEach(function(c){c.classList.remove('on')});
    cards.forEach(function(c){c.classList.remove('hidden')});
  });}
})();
</script>"""


def render_panel_html_v2(emails: list, reviews: list, now_label: str, window_label: str = "",
                         last_events: dict | None = None, covered_industries: list | None = None) -> str:
    email_by_id = _email_map(emails)
    # 从 deep 提取把 broker（机构名）挂到邮件对象，渲染来源标签用
    _broker_by_email = {}
    for _r in reviews:
        _b = _r.get("broker")
        if _b and _r.get("_email_id"):
            _broker_by_email.setdefault(_r["_email_id"], _b)
    for _em in emails:
        try:
            _em.broker = _broker_by_email.get(_em.key, "")
        except Exception:
            pass
    items = _merge_items(reviews)
    meetings = _merge_meetings(reviews)
    filtered = [m for m in meetings if str(m.get("recommendation")) == "skip"]
    kept = [m for m in meetings if str(m.get("recommendation")) != "skip"]
    industries = sorted({str(m.get("industry") or "") for m in meetings} - {""})

    by_industry = {}
    for item in items:
        ind = item.get("industry") or "Other"
        sec = by_industry.setdefault(ind, {"industry": [], "company": [], "meeting": []})
        if str(item.get("bucket") or "industry_signal") == "industry_signal":
            sec["industry"].append(item)
        else:
            sec["company"].append(item)

    blocks = []
    blocks.append(f"""<div class="hero"><span class="hero-date">Email Intelligence · {_e(now_label)}</span>
<span class="hero-stat">{len(emails)} 封 · {len(items)} 信号 · {len(meetings)} 场</span>
<span class="hero-stat">过滤：{len(filtered)} 场不相关/无价值</span>
<span class="hero-stat">as-of {_e(now_label[:10])} · 数据来源：OneDrive/Email-AI 卖方邮件</span></div>
""")
    blocks.append("""<nav class="tab-nav">
<a class="tab-button" href="#t01">Worth Your Time</a>
<a class="tab-button" href="#t02">Industry</a>
<a class="tab-button" href="#t03">Core Watch</a>
<a class="tab-button" href="#t04">Other Coverage</a>
<a class="tab-button" href="#t05">New Ideas</a>
<a class="tab-button" href="#t06">Meetings</a>
</nav>""")
    blocks.append(f"<section class='tab-panel' id='t01'><div class='section-head'><h2>01 · Worth Your Time</h2></div>{_wyt_rows_v2(items, email_by_id)}</section>")
    blocks.append("<section class='tab-panel' id='t02'><div class='section-head'><h2>02 · Industry</h2></div><div class='indust-grid'>")
    for ind, sec in sorted(by_industry.items(), key=lambda kv: -sum(len(v) for v in kv[1].values())):
        if not _industry_visible(ind, covered_industries):
            continue
        blocks.append(_industry_card_v2(ind, sec, email_by_id))
    blocks.append("</div></section>")
    for bucket, (num, title) in _BUCKET_META.items():
        rows = [i for i in items if str(i.get("bucket")) == bucket]
        if not rows:
            continue
        gc = 'cols-3' if bucket == 'core' else 'cols-4'
        blocks.append(f"<section class='tab-panel' id='t{num[1]}'><div class='section-head'><h2>{num} · {title}</h2></div><div class='indust-grid {gc}'>")
        for item in rows:
            mt = None
            for m in meetings:
                if m.get("company") and str(m["company"]).lower() in str(item.get("company") or "").lower():
                    mt = m
                    break
            blocks.append(_company_card_v2(item, email_by_id, mt, light=(bucket == "other_coverage")))
        blocks.append("</div></section>")
    chips = "".join(f"<button class='filter-chip' data-ind='{_e(x)}'>{_e(x)}</button>" for x in industries)
    blocks.append(f"""<section class='tab-panel' id='t06'><div class='section-head'><h2>06 · Meetings</h2></div>
<div class="filter-row"><span class="filter-label">行业筛选：</span>{chips}<span class="filter-clear" id="filterClear">清除</span></div>""")

    def _date_block(date, ms, skip=False):
        rows = "\n".join(_meeting_card_panel(m, email_by_id, skip) for m in ms)
        return f"<div class='date-group-label'>{_e(date)}</div><div class='indust-grid cols-4' style='gap:10px'>{rows}</div>"

    dates = sorted({str(m.get("date") or "TBD") for m in kept})
    for d in dates:
        day_kept = [m for m in kept if str(m.get("date") or "TBD") == d]
        blocks.append(_date_block(d, day_kept))
    skip_dates = sorted({str(m.get("date") or "TBD") for m in filtered})
    for d in skip_dates:
        day_skip = [m for m in filtered if str(m.get("date") or "TBD") == d]
        blocks.append(_date_block(d, day_skip, skip=True))
    blocks.append("</section>")
    body = "\n".join(b for b in blocks if b)
    return f"""<!doctype html><html lang="zh-Hans"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Email Intelligence Panel · {_e(now_label)}</title>
<style>{_CSS_PANEL}</style></head><body><main>
{body}
</main>
{_PANEL_SCRIPT}
</body></html>"""


# ---------------------------------------------------------------------------
# Canonical v3 renderers.  They intentionally override the experimental v2
# functions above while keeping the public API stable for the CLI and plugins.
# ---------------------------------------------------------------------------
from .report import build_report as _build_report_v3


_PALETTE_V3 = {
    "ink": "#172033",
    "muted": "#667085",
    "link": "#1D4ED8",
    "page_bg": "#EEF2F6",
    "card": "#FFFFFF",
    "border": "#D6DEE8",
    "worth": "#1E3A5F",
    "industry": "#2F6B8A",
    "core": "#6B5AA6",
    "other": "#667085",
    "ideas": "#0F766E",
    "meetings": "#4F46E5",
    "recommend": "#15803D",
    "consider": "#B54708",
    "skip": "#98A2B3",
    "status_core_bg": "#F0ECFF",
    "status_core_text": "#5B4A91",
    "status_core_border": "#CFC5F5",
    "status_screened_bg": "#EEF2F6",
    "status_screened_text": "#475467",
    "status_screened_border": "#CDD5DF",
    "status_quickread_bg": "#FFF4D6",
    "status_quickread_text": "#8A5A00",
    "status_quickread_border": "#E8C96A",
    "industry_soft": "#EDF4F7",
    "rule": "#E4E9F0",
}


def _source_v3(fact: dict) -> str:
    label = _e(fact.get("broker") or "来源邮件")
    url = str(fact.get("url") or "")
    if url:
        return f"<a href='{_e(url)}' style='color:{_PALETTE_V3['link']};text-decoration:none;font-weight:700'>{label}</a>"
    return f"<span style='color:{_PALETTE_V3['link']};font-weight:700'>{label}</span>"


def _registration_url_v3(meeting: dict) -> str:
    url = str(meeting.get("registration") or "").strip()
    if not url.lower().startswith(("https://", "http://")):
        return ""
    return url


def _meeting_title_v3(meeting: dict) -> str:
    title = _e(meeting.get("title") or meeting.get("company") or "Meeting")
    url = _registration_url_v3(meeting)
    if not url:
        return title
    return f"<a style='color:{_PALETTE_V3['link']};text-decoration:none' href='{_e(url)}' class='meeting-title-link'>{title}</a>"


def _meeting_date_v3(value: object) -> date | None:
    text = str(value or "").strip()
    match = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", text)
    if match:
        try:
            return date.fromisoformat(match.group(1))
        except ValueError:
            pass
    for pattern in ("%d %B %Y", "%d %b %Y", "%B %d, %Y", "%b %d, %Y"):
        try:
            return datetime.strptime(text, pattern).date()
        except ValueError:
            continue
    return None


def _meeting_time_v3(value: object) -> tuple[int, int]:
    text = str(value or "").strip().upper()
    if not text or "TBD" in text:
        return (99, 99)
    match = re.search(r"(?<!\d)(\d{1,2})(?::(\d{2}))?\s*(AM|PM)?", text)
    if not match:
        return (99, 99)
    hour = int(match.group(1))
    minute = int(match.group(2) or 0)
    marker = match.group(3)
    if marker == "AM" and hour == 12:
        hour = 0
    elif marker == "PM" and hour < 12:
        hour += 12
    return (hour, minute) if hour < 24 and minute < 60 else (99, 99)


def _ordered_meetings_v3(meetings: list[dict], now_label: str) -> list[dict]:
    as_of = _meeting_date_v3(now_label) or date.today()
    recommendation_rank = {"recommend": 0, "high": 0, "consider": 1, "medium": 1, "low": 2, "skip": 3}

    def key(meeting: dict):
        meeting_date = _meeting_date_v3(meeting.get("date"))
        rec = recommendation_rank.get(str(meeting.get("recommendation") or "").lower(), 2)
        start = _meeting_time_v3(meeting.get("time"))
        title = str(meeting.get("title") or "").lower()
        if meeting_date is None:
            return (1, 0, rec, start, title)
        if meeting_date >= as_of:
            return (0, meeting_date.toordinal(), rec, start, title)
        return (2, -meeting_date.toordinal(), rec, start, title)

    return sorted(meetings, key=key)


def _match_norm_v3(value: object) -> str:
    return re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "", str(value or "").casefold())


def _industry_label_v3(value: object, covered_industries: list | None = None) -> str:
    raw = str(value or "").strip() or "Other"
    identity = _match_norm_v3(raw)
    for covered in covered_industries or []:
        label = str(covered or "").strip()
        if label and _match_norm_v3(label) == identity:
            return label
    return raw


def _industry_groups_v3(items: list[dict], covered_industries: list | None = None) -> list[tuple[str, list[dict]]]:
    groups: dict[str, tuple[str, list[dict]]] = {}
    for item in items:
        label = _industry_label_v3(item.get("industry"), covered_industries)
        identity = _match_norm_v3(label) or label.casefold()
        if identity not in groups:
            groups[identity] = (label, [])
        groups[identity][1].append(item)
    return list(groups.values())


def _industry_labels_v3(values: list[object], covered_industries: list | None = None) -> list[str]:
    labels: list[str] = []
    seen: set[str] = set()
    for value in values:
        label = _industry_label_v3(value, covered_industries)
        identity = _match_norm_v3(label) or label.casefold()
        if identity not in seen:
            seen.add(identity)
            labels.append(label)
    return labels


def _identity_values_v3(values: list[object]) -> set[str]:
    out: set[str] = set()
    for value in values:
        raw = str(value or "").strip()
        if not raw:
            continue
        normalized = _match_norm_v3(raw)
        if normalized:
            out.add(normalized)
        if "." in raw:
            base = _match_norm_v3(raw.split(".", 1)[0])
            if base:
                out.add(base)
    return out


def _industry_matches_v3(industry: object, meeting_industry: object) -> bool:
    target = _match_norm_v3(industry)
    raw = str(meeting_industry or "")
    if not target or not raw:
        return False
    candidates = {_match_norm_v3(raw)}
    candidates.update(_match_norm_v3(part) for part in re.split(r"\s*(?:&|/|\+|\||,|\band\b)\s*", raw, flags=re.I))
    return target in (candidates - {""})


def _company_matches_v3(item: dict, meeting: dict) -> bool:
    item_ids = _identity_values_v3([
        item.get("ticker"), item.get("coverage_ticker"), item.get("company"),
    ])
    related = meeting.get("related_tickers") or []
    if isinstance(related, str):
        related = [related]
    meeting_ids = _identity_values_v3([
        meeting.get("ticker"), meeting.get("company"), *list(related),
    ])
    if item_ids & meeting_ids:
        return True
    names_a = [_match_norm_v3(item.get("company"))]
    names_b = [_match_norm_v3(meeting.get("company")), *[_match_norm_v3(x) for x in related]]
    return any(a and b and min(len(a), len(b)) >= 5 and (a in b or b in a) for a in names_a for b in names_b)


def _is_embeddable_meeting_v3(meeting: dict, now_label: str) -> bool:
    if str(meeting.get("recommendation") or "").lower() not in {"recommend", "high"}:
        return False
    meeting_date = _meeting_date_v3(meeting.get("date"))
    as_of = _meeting_date_v3(now_label) or date.today()
    return meeting_date is None or meeting_date >= as_of


def _related_meetings_v3(item: dict, meetings: list[dict], now_label: str) -> list[dict]:
    ordered = _ordered_meetings_v3(meetings, now_label)
    if item.get("company") or item.get("ticker") or item.get("coverage_ticker"):
        return [m for m in ordered if _is_embeddable_meeting_v3(m, now_label) and _company_matches_v3(item, m)]
    return [m for m in ordered if _is_embeddable_meeting_v3(m, now_label)
            and _industry_matches_v3(item.get("industry"), m.get("industry"))]


def _related_industry_meetings_v3(industry: str, items: list[dict], meetings: list[dict], now_label: str) -> list[dict]:
    company_items = [item for item in items if item.get("company") or item.get("ticker")]
    related = []
    seen = set()
    for meeting in _ordered_meetings_v3(meetings, now_label):
        if not _is_embeddable_meeting_v3(meeting, now_label):
            continue
        if not (_industry_matches_v3(industry, meeting.get("industry"))
                or any(_company_matches_v3(item, meeting) for item in company_items)):
            continue
        key = (meeting.get("title"), meeting.get("date"), meeting.get("time"), meeting.get("registration"))
        if key not in seen:
            seen.add(key)
            related.append(meeting)
    return related


def _meeting_group_label_v3(value: object, now_label: str) -> str:
    raw = str(value or "").strip()
    meeting_date = _meeting_date_v3(raw)
    if meeting_date is None:
        return "日期待定"
    as_of = _meeting_date_v3(now_label) or date.today()
    return f"已过期｜{raw}" if meeting_date < as_of else raw


def _meeting_accent_v3(meeting: dict) -> str:
    recommendation = str(meeting.get("recommendation") or "").lower()
    if recommendation in {"recommend", "high"}:
        return _PALETTE_V3["recommend"]
    if recommendation in {"consider", "medium"}:
        return _PALETTE_V3["consider"]
    return _PALETTE_V3["skip"]


def _meeting_meta_v3(meeting: dict) -> str:
    when = " ".join(_e(x) for x in (meeting.get("date"), meeting.get("time")) if x)
    return " · ".join(x for x in (when, _e(meeting.get("format")), _e(meeting.get("language"))) if x)


def _status_badges_v3(item: dict) -> str:
    badges: list[tuple[str, str, str]] = []
    if str(item.get("bucket") or "").lower() == "core":
        badges.append(("Core", "status-core", f"background:{_PALETTE_V3['status_core_bg']};color:{_PALETTE_V3['status_core_text']};border-color:{_PALETTE_V3['status_core_border']}"))
    status = str(item.get("coverage_status") or "").strip()
    if status:
        slug = re.sub(r"[^a-z0-9]+", "-", status.lower()).strip("-") or "other"
        palette = {
            "screened": f"background:{_PALETTE_V3['status_screened_bg']};color:{_PALETTE_V3['status_screened_text']};border-color:{_PALETTE_V3['status_screened_border']}",
            "quickread": f"background:{_PALETTE_V3['status_quickread_bg']};color:{_PALETTE_V3['status_quickread_text']};border-color:{_PALETTE_V3['status_quickread_border']}",
        }.get(slug, f"background:{_PALETTE_V3['status_screened_bg']};color:{_PALETTE_V3['status_screened_text']};border-color:{_PALETTE_V3['status_screened_border']}")
        badges.append((status, f"status-{slug}", palette))
    return " ".join(
        f"<span style='display:inline-block;margin-left:5px;padding:1px 6px;border:1px solid;border-radius:999px;font-size:10px;line-height:15px;font-weight:800;vertical-align:1px;{style}' class='status-badge {cls}'>{_e(label)}</span>"
        for label, cls, style in badges
    )


def _fact_rows_outlook(item: dict) -> str:
    rows = []
    for fact in item.get("facts") or []:
        text = _e(fact.get("text"))
        why = _e(fact.get("why_it_matters"))
        extra = ""
        if why:
            extra += f"<div style='margin-top:4px;color:{_PALETTE_V3['muted']}'><b>意义：</b>{why}</div>"
        rows.append(
            f"<tr class='fact-row'><td class='fact-cell' valign='top' style='padding:7px 10px 7px 0;font-size:13px;line-height:20px;color:{_PALETTE_V3['ink']};word-break:break-word'>"
            f"<span style='color:{_PALETTE_V3['skip']}'>•</span> {text}{extra}</td>"
            f"<td class='source-cell' width='112' valign='top' align='right' style='padding:7px 0;font-size:11px;line-height:20px;white-space:nowrap'>{_source_v3(fact)}</td></tr>"
        )
    return "".join(rows) or f"<tr><td style='padding:6px 0;color:{_PALETTE_V3['skip']}'>暂无可展示内容</td></tr>"


def _outlook_section(number: str, title: str, content: str, color: str) -> str:
    return (
        "<tr><td style='padding:18px 0 8px'>"
        f"<table role='presentation' width='100%' cellpadding='0' cellspacing='0'><tr>"
        f"<td width='5' bgcolor='{color}' style='background:{color}'></td>"
        f"<td style='padding:5px 9px;font-size:17px;line-height:24px;font-weight:900;color:{_PALETTE_V3['ink']}'>{number} · {_e(title)}</td>"
        "</tr></table></td></tr>"
        f"<tr><td>{content}</td></tr>"
    )


def _outlook_meeting(m: dict) -> str:
    sources = m.get("sources") or []
    source = _source_v3(sources[0]) if sources else _e(m.get("broker"))
    meta = _meeting_meta_v3(m)
    details = []
    if m.get("participants"):
        details.append("讲者：" + _e(m["participants"]))
    if m.get("agenda_items"):
        details.append("看点：" + " · ".join(_e(x) for x in list(m["agenda_items"])[:3]))
    if m.get("host_person"):
        details.append("主持：" + _e(m["host_person"]))
    detail_line = " · ".join(details)
    accent = _meeting_accent_v3(m)
    return (
        f"<table role='presentation' width='100%' cellpadding='0' cellspacing='0' border='0' style='margin:0 0 10px;border:1px solid {_PALETTE_V3['border']};border-left:4px solid {accent};background:{_PALETTE_V3['card']}'>"
        f"<tr><td class='meeting-title-cell' valign='top' style='padding:9px 8px 3px 10px;font-size:13px;line-height:20px;font-weight:800;color:{_PALETTE_V3['link']};word-break:break-word'>{_meeting_title_v3(m)}</td>"
        f"<td class='meeting-broker' width='112' valign='top' align='right' style='padding:9px 10px 3px 0;font-size:11px;line-height:20px;white-space:normal'>{source}</td></tr>"
        f"<tr><td colspan='2' style='padding:2px 10px 9px;font-size:11.5px;line-height:18px;color:{_PALETTE_V3['muted']}'><b style='color:{_PALETTE_V3['ink']}'>{meta}</b>"
        + (f"<br>{detail_line}" if detail_line else "") + "</td></tr></table>"
    )


def _outlook_related_meetings(meetings: list[dict]) -> str:
    if not meetings:
        return ""
    rows = []
    for meeting in meetings:
        sources = meeting.get("sources") or []
        source = _source_v3(sources[0]) if sources else _e(meeting.get("broker"))
        rows.append(
            f"<tr><td valign='top' style='padding:5px 8px 5px 0;font-size:11.5px;line-height:17px;color:{_PALETTE_V3['link']};word-break:break-word'>"
            f"{_meeting_title_v3(meeting)}<div style='color:{_PALETTE_V3['muted']}'>{_meeting_meta_v3(meeting)}</div></td>"
            f"<td width='105' valign='top' align='right' style='padding:5px 0;font-size:10.5px;line-height:17px'>{source}</td></tr>"
        )
    return (f"<div class='related-meetings' style='margin-top:9px;padding-top:7px;border-top:1px solid {_PALETTE_V3['border']}'>"
            f"<div style='margin-bottom:2px;font-size:11px;font-weight:900;color:{_PALETTE_V3['recommend']}'>推荐会议</div>"
            "<table role='presentation' width='100%' cellpadding='0' cellspacing='0' border='0'>"
            + "".join(rows) + "</table></div>")


def _outlook_item_card(item: dict, color: str | None = None, related_meetings: list[dict] | None = None) -> str:
    color = color or _PALETTE_V3["industry"]
    name = _e(item.get("company") or item.get("industry") or "Signal")
    ticker = _e(item.get("ticker"))
    title = name + (f" <span style='color:{_PALETTE_V3['muted']};font-size:11px'>({ticker})</span>" if ticker else "") + _status_badges_v3(item)
    return (
        "<table role='presentation' width='100%' cellpadding='0' cellspacing='0' border='0' "
        f"style='margin:0 0 10px;border:1px solid {_PALETTE_V3['border']};background:{_PALETTE_V3['card']}'>"
        f"<tr><td width='4' bgcolor='{color}' style='background:{color}'></td>"
        "<td style='padding:10px 12px'>"
        f"<div style='font-size:14px;line-height:21px;font-weight:800;color:{_PALETTE_V3['ink']}'>{title}</div>"
        "<table role='presentation' width='100%' cellpadding='0' cellspacing='0' border='0' style='margin-top:3px'>"
        f"{_fact_rows_outlook(item)}</table>{_outlook_related_meetings(related_meetings or [])}</td></tr></table>"
    )


def _outlook_industry_rows(items: list[dict], *, show_company: bool = False) -> str:
    rows = []
    for item in items:
        prefix = _e(item.get("company")) if show_company else ""
        if show_company and item.get("ticker"):
            prefix += f" ({_e(item['ticker'])})"
        for fact in item.get("facts") or []:
            lead = f"<b>{prefix}｜</b>" if prefix else ""
            rows.append(f"<tr class='fact-row'><td class='fact-cell' valign='top' style='padding:7px 10px 7px 0;font-size:13px;line-height:20px;color:{_PALETTE_V3['ink']};word-break:break-word'>"
                        f"<span style='color:{_PALETTE_V3['skip']}'>•</span> {lead}{_e(fact.get('text'))}</td>"
                        f"<td class='source-cell' width='112' valign='top' align='right' style='padding:7px 0;font-size:11px;line-height:20px;white-space:nowrap'>{_source_v3(fact)}</td></tr>")
    return "".join(rows)


def _outlook_company_rows(items: list[dict]) -> str:
    blocks = []
    for item in items:
        name = _e(item.get("company") or item.get("ticker") or "Company")
        if item.get("ticker"):
            name += f" <span style='color:{_PALETTE_V3['muted']};font-size:10.5px'>({_e(item['ticker'])})</span>"
        blocks.append(f"<tr><td colspan='2' class='industry-company-name' style='padding:7px 0 2px;font-size:12px;line-height:18px;font-weight:900;color:{_PALETTE_V3['ink']}'>{name}{_status_badges_v3(item)}</td></tr>")
        blocks.append(_outlook_industry_rows([item]))
    return "".join(blocks)


def _outlook_industry_card(industry: str, items: list[dict], related_meetings: list[dict] | None = None) -> str:
    industry_items = [item for item in items if not (item.get("company") or item.get("ticker"))]
    company_items = [item for item in items if item.get("company") or item.get("ticker")]
    blocks = []
    if industry_items:
        blocks.append(f"<div class='industry-subhead' style='margin:2px 0 3px;font-size:12px;font-weight:900;color:{_PALETTE_V3['industry']}'>行业观点</div>")
        blocks.append("<table role='presentation' width='100%' cellpadding='0' cellspacing='0' border='0'>" + _outlook_industry_rows(industry_items) + "</table>")
    if company_items:
        blocks.append(f"<div class='industry-subhead' style='margin:8px 0 3px;padding-top:7px;border-top:2px solid {_PALETTE_V3['border']};font-size:12px;font-weight:900;color:{_PALETTE_V3['other']}'>公司动态</div>")
        blocks.append("<table role='presentation' width='100%' cellpadding='0' cellspacing='0' border='0'>" + _outlook_company_rows(company_items) + "</table>")
    blocks.append(_outlook_related_meetings(related_meetings or []))
    return (f"<div style='margin:0 0 6px;padding:6px 9px;background:{_PALETTE_V3['industry_soft']};border-left:4px solid {_PALETTE_V3['industry']};font-size:14px;font-weight:900;color:{_PALETTE_V3['industry']}'>{_e(industry)}</div>"
            f"<table role='presentation' width='100%' cellpadding='0' cellspacing='0' border='0' style='margin:0 0 12px;border:1px solid {_PALETTE_V3['border']};background:{_PALETTE_V3['card']}'><tr><td style='padding:9px 12px'>"
            + "".join(blocks) + "</td></tr></table>")


def render_brief_html_v2(emails: list, reviews: list, now_label: str, window_label: str = "",
                         last_events: dict | None = None, covered_industries: list | None = None,
                         report: dict | None = None) -> str:
    """Outlook body: one column, presentation tables and inline CSS only."""
    report = report or _build_report_v3(emails, reviews, last_events=last_events)
    sections = report["sections"]
    empty = f"<div style='padding:10px 12px;border:1px dashed {_PALETTE_V3['border']};color:{_PALETTE_V3['muted']};font-size:12px'>本窗口无新增内容</div>"
    ordered_meetings = _ordered_meetings_v3(report["meetings"], now_label)
    top = report["items"][:3]
    wyt = "".join(_outlook_item_card(i, _PALETTE_V3["worth"], _related_meetings_v3(i, ordered_meetings, now_label)) for i in top) or empty
    industry = ""
    for name, rows in _industry_groups_v3(sections["industry_signal"], covered_industries):
        industry += _outlook_industry_card(name, rows, _related_industry_meetings_v3(name, rows, ordered_meetings, now_label))
    industry = industry or empty
    core = "".join(_outlook_item_card(i, _PALETTE_V3["core"], _related_meetings_v3(i, ordered_meetings, now_label)) for i in sections["core"]) or empty
    other = "".join(_outlook_item_card(i, _PALETTE_V3["other"], _related_meetings_v3(i, ordered_meetings, now_label)) for i in sections["other_coverage"]) or empty
    ideas = "".join(_outlook_item_card(i, _PALETTE_V3["ideas"], _related_meetings_v3(i, ordered_meetings, now_label)) for i in sections["new_idea"]) or empty
    meetings = "".join(_outlook_meeting(m) for m in ordered_meetings if str(m.get("recommendation")) != "skip") or empty
    body = "".join([
        _outlook_section("01", "Worth Your Time", wyt, _PALETTE_V3["worth"]),
        _outlook_section("02", "Industry", industry, _PALETTE_V3["industry"]),
        _outlook_section("03", "Core Watch", core, _PALETTE_V3["core"]),
        _outlook_section("04", "Other Coverage", other, _PALETTE_V3["other"]),
        _outlook_section("05", "New Ideas", ideas, _PALETTE_V3["ideas"]),
        _outlook_section("06", "Meetings", meetings, _PALETTE_V3["meetings"]),
    ])
    stats = report["stats"]
    return f"""<!doctype html><html lang='zh-Hans'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
<title>Email Intelligence Brief · {_e(now_label)}</title>
<style>body,table,td,a{{-webkit-text-size-adjust:100%;-ms-text-size-adjust:100%}}table,td{{mso-table-lspace:0;mso-table-rspace:0}}.container{{width:100%!important;max-width:680px!important}}@media(max-width:700px){{.fact-row .fact-cell,.fact-row .source-cell,.meeting-main,.meeting-right{{display:block!important;width:auto!important;text-align:left!important;padding-left:0!important;padding-right:0!important}}.fact-row .source-cell{{padding-top:0!important;white-space:normal!important}}}}</style></head>
<body style="margin:0;padding:0;background:{_PALETTE_V3['page_bg']};color:{_PALETTE_V3['ink']};font-family:'Segoe UI','Microsoft YaHei',Arial,sans-serif">
<table role='presentation' width='100%' cellpadding='0' cellspacing='0' border='0'><tr><td align='center' style='padding:12px 6px 30px'>
<table role='presentation' class='container' width='100%' cellpadding='0' cellspacing='0' border='0' style='width:100%;max-width:680px;table-layout:fixed'>
<tr><td style='padding:12px 14px;background:{_PALETTE_V3['card']};border:1px solid {_PALETTE_V3['border']};border-left:4px solid {_PALETTE_V3['worth']};font-size:11.5px;line-height:18px;color:{_PALETTE_V3['muted']}'>
Email Intelligence · {_e(now_label)} · {_e(window_label)}<br><b style='color:{_PALETTE_V3['ink']}'>{stats['emails']} 封 · {stats['signals']} 信号 · {stats['meetings']} 场会议</b></td></tr>
{body}</table></td></tr></table></body></html>"""


_PANEL_V3_CSS = """
:root{--ink:%(ink)s;--muted:%(muted)s;--line:%(border)s;--link:%(link)s;--bg:%(page_bg)s;--card:%(card)s;--industry:%(industry)s;--other:%(other)s;--recommend:%(recommend)s;--skip:%(skip)s;--industry-soft:%(industry_soft)s;--rule:%(rule)s}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font-family:"Segoe UI","Microsoft YaHei",sans-serif}main{width:min(1440px,calc(100vw - 28px));margin:18px auto 44px}
.hero,.nav{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:12px 16px;margin-bottom:14px}.hero{font-size:13px;font-weight:700}.nav{position:sticky;top:0;z-index:2;display:flex;gap:8px;overflow:auto}.nav a{padding:7px 11px;color:var(--muted);text-decoration:none;font-weight:800;white-space:nowrap}
.section{margin:28px 0}.section h2{font-size:19px;margin:0 0 12px;padding-left:10px;border-left:5px solid var(--accent,var(--industry))}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(360px,1fr));gap:14px}.industry-grid{grid-template-columns:repeat(auto-fit,minmax(520px,1fr))}.meeting-grid{grid-template-columns:repeat(2,minmax(0,1fr))}
.card{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:15px;box-shadow:0 10px 30px rgba(23,32,51,.06)}.card-title{font-size:14px;font-weight:900;margin-bottom:8px}.fact{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:12px;border-top:1px solid var(--rule);padding:8px 0;font-size:13px;line-height:1.65}.fact:first-of-type{border-top:0}.source{color:var(--link);text-decoration:none;font-weight:750;white-space:nowrap;font-size:11.5px}.why{color:var(--muted);font-size:11.5px;margin-top:3px}
.group-label{font-size:14px;font-weight:900;color:var(--industry);background:var(--industry-soft);border-left:4px solid var(--industry);padding:6px 9px;margin:0 0 9px}.industry-subhead{font-size:12px;font-weight:900;margin:8px 0 3px;padding-top:7px;border-top:2px solid var(--line)}.industry-subhead:first-of-type{border-top:0;padding-top:0;color:var(--industry)}.industry-company{padding:3px 0 5px}.industry-company-name{font-size:12px;line-height:18px;font-weight:900;color:var(--ink);margin:3px 0 1px}.related-meetings{margin-top:10px;padding-top:8px;border-top:1px solid var(--line)}.related-label{font-size:11px;font-weight:900;color:var(--recommend);margin-bottom:3px}.related-meeting{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:10px;padding:5px 0;font-size:11.5px;line-height:1.45}.related-title{color:var(--link);font-weight:800;overflow-wrap:anywhere}.related-meta{color:var(--muted)}.meeting-card{border-left:4px solid var(--meeting-accent,var(--skip));padding:12px 14px}.meeting-heading{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:12px;align-items:start}.meeting-title{font-size:14px;line-height:1.45;font-weight:900;color:var(--link);overflow-wrap:anywhere}.meeting-title-link{color:var(--link);text-decoration:none}.meeting-broker{text-align:right;white-space:nowrap;font-size:11.5px}.meeting-meta{font-size:12px;line-height:1.55;color:var(--ink);font-weight:800;margin-top:5px;overflow-wrap:anywhere}.meeting-details{font-size:11.5px;line-height:1.55;color:var(--muted);margin-top:3px}.date-label{font-size:14px;font-weight:900;margin:18px 2px 8px;color:var(--ink)}.chips{margin:0 0 12px}.chip{border:1px solid var(--line);border-radius:999px;background:var(--card);padding:4px 10px;margin:2px;font-size:11px;color:var(--muted)}.empty{border:1px dashed var(--line);background:var(--card);padding:18px;color:var(--muted);border-radius:14px}
@media(max-width:640px){main{width:calc(100vw - 16px)}.industry-grid,.grid,.meeting-grid{grid-template-columns:1fr}.fact{grid-template-columns:1fr}.source{white-space:normal;text-align:left}.nav{border-radius:10px}.card{padding:12px}.meeting-card{padding:11px 12px}.meeting-heading{gap:8px}.meeting-broker{white-space:normal}}
""" % _PALETTE_V3


def _panel_related_meetings(meetings: list[dict]) -> str:
    if not meetings:
        return ""
    rows = []
    for meeting in meetings:
        sources = meeting.get("sources") or []
        source = _source_v3(sources[0]) if sources else _e(meeting.get("broker"))
        rows.append(f"<div class='related-meeting'><div><div class='related-title'>{_meeting_title_v3(meeting)}</div><div class='related-meta'>{_meeting_meta_v3(meeting)}</div></div><div>{source}</div></div>")
    return "<div class='related-meetings'><div class='related-label'>推荐会议</div>" + "".join(rows) + "</div>"


def _panel_card(item: dict, related_meetings: list[dict] | None = None) -> str:
    title = _e(item.get("company") or item.get("industry") or "Signal")
    if item.get("ticker"):
        title += f" <span style='color:{_PALETTE_V3['muted']};font-size:11px'>({_e(item['ticker'])})</span>"
    title += _status_badges_v3(item)
    facts = []
    for fact in item.get("facts") or []:
        why = f"<div class='why'>意义：{_e(fact.get('why_it_matters'))}</div>" if fact.get("why_it_matters") else ""
        facts.append(f"<div class='fact'><div>• {_e(fact.get('text'))}{why}</div><div>{_source_v3(fact)}</div></div>")
    return f"<article class='card'><div class='card-title'>{title}</div>{''.join(facts)}{_panel_related_meetings(related_meetings or [])}</article>"


def _panel_meeting(m: dict) -> str:
    source = _source_v3((m.get("sources") or [{}])[0])
    meta = _meeting_meta_v3(m)
    details = []
    if m.get("participants"):
        details.append(f"讲者：{_e(m['participants'])}")
    if m.get("agenda_items"):
        details.append(f"看点：{' · '.join(_e(x) for x in list(m['agenda_items'])[:3])}")
    detail_line = " · ".join(details)
    return (f"<article class='card meeting-card' data-ind='{_e(m.get('industry'))}' style='--meeting-accent:{_meeting_accent_v3(m)}'>"
            f"<div class='meeting-heading'><div class='meeting-title'>{_meeting_title_v3(m)}</div><div class='meeting-broker'>{source}</div></div>"
            f"<div class='meeting-meta'>{meta}</div>" + (f"<div class='meeting-details'>{detail_line}</div>" if detail_line else "") + "</article>")


def _panel_industry_facts(items: list[dict], *, show_company: bool = False) -> str:
    facts = []
    for item in items:
        prefix = _e(item.get("company")) if show_company else ""
        if show_company and item.get("ticker"):
            prefix += f" ({_e(item['ticker'])})"
        for fact in item.get("facts") or []:
            lead = f"<b>{prefix}｜</b>" if prefix else ""
            facts.append(f"<div class='fact'><div>• {lead}{_e(fact.get('text'))}</div><div>{_source_v3(fact)}</div></div>")
    return "".join(facts)


def _panel_industry_companies(items: list[dict]) -> str:
    blocks = []
    for item in items:
        name = _e(item.get("company") or item.get("ticker") or "Company")
        if item.get("ticker"):
            name += f" <span style='color:{_PALETTE_V3['muted']};font-size:10.5px'>({_e(item['ticker'])})</span>"
        blocks.append(f"<div class='industry-company'><div class='industry-company-name'>{name}{_status_badges_v3(item)}</div>{_panel_industry_facts([item])}</div>")
    return "".join(blocks)


def _panel_industry_card(industry: str, items: list[dict], related_meetings: list[dict] | None = None) -> str:
    industry_items = [item for item in items if not (item.get("company") or item.get("ticker"))]
    company_items = [item for item in items if item.get("company") or item.get("ticker")]
    blocks = []
    if industry_items:
        blocks.append("<div class='industry-subhead'>行业观点</div>" + _panel_industry_facts(industry_items))
    if company_items:
        blocks.append(f"<div class='industry-subhead' style='color:{_PALETTE_V3['other']}'>公司动态</div>" + _panel_industry_companies(company_items))
    return f"<article class='card'><div class='group-label'>{_e(industry)}</div>{''.join(blocks)}{_panel_related_meetings(related_meetings or [])}</article>"


def render_panel_html_v2(emails: list, reviews: list, now_label: str, window_label: str = "",
                         last_events: dict | None = None, covered_industries: list | None = None,
                         report: dict | None = None) -> str:
    report = report or _build_report_v3(emails, reviews, last_events=last_events)
    sections = report["sections"]
    empty = "<div class='empty'>本窗口无新增内容</div>"
    blocks = [f"<div class='hero'>Email Intelligence · {_e(now_label)}　{report['stats']['emails']} 封 · {report['stats']['signals']} 信号 · {report['stats']['meetings']} 场会议</div>",
              "<nav class='nav'><a href='#s01'>Worth Your Time</a><a href='#s02'>Industry</a><a href='#s03'>Core Watch</a><a href='#s04'>Other Coverage</a><a href='#s05'>New Ideas</a><a href='#s06'>Meetings</a></nav>"]
    ordered_meetings = _ordered_meetings_v3(report["meetings"], now_label)
    def section(num, title, content, cls="grid", accent=None):
        accent = accent or _PALETTE_V3["industry"]
        blocks.append(f"<section class='section' id='s{num}' style='--accent:{accent}'><h2>{num} · {title}</h2><div class='{cls}'>{content or empty}</div></section>")
    section("01", "Worth Your Time", "".join(_panel_card(i, _related_meetings_v3(i, ordered_meetings, now_label)) for i in report["items"][:3]), accent=_PALETTE_V3["worth"])
    industry_html = "".join(_panel_industry_card(ind, rows, _related_industry_meetings_v3(ind, rows, ordered_meetings, now_label)) for ind, rows in _industry_groups_v3(sections["industry_signal"], covered_industries))
    section("02", "Industry", industry_html, "grid industry-grid", accent=_PALETTE_V3["industry"])
    section("03", "Core Watch", "".join(_panel_card(i, _related_meetings_v3(i, ordered_meetings, now_label)) for i in sections["core"]), accent=_PALETTE_V3["core"])
    section("04", "Other Coverage", "".join(_panel_card(i, _related_meetings_v3(i, ordered_meetings, now_label)) for i in sections["other_coverage"]), accent=_PALETTE_V3["other"])
    section("05", "New Ideas", "".join(_panel_card(i, _related_meetings_v3(i, ordered_meetings, now_label)) for i in sections["new_idea"]), accent=_PALETTE_V3["ideas"])
    kept = [m for m in ordered_meetings if str(m.get("recommendation")) != "skip"]
    focus = _industry_labels_v3(
        [*list(covered_industries or []), *[m.get("industry") for m in kept if m.get("industry")]],
        covered_industries,
    )[:12]
    chips = "<div class='chips'>" + "".join(f"<button class='chip' data-filter='{_e(x)}'>{_e(x)}</button>" for x in focus) + "<button class='chip' data-filter=''>全部</button></div>"
    by_date: dict[str, list[dict]] = defaultdict(list)
    for meeting in kept:
        by_date[_meeting_group_label_v3(meeting.get("date"), now_label)].append(meeting)
    meeting_html = chips + "".join(f"<div class='date-label'>{_e(date)}</div><div class='grid meeting-grid'>{''.join(_panel_meeting(m) for m in rows)}</div>" for date, rows in by_date.items())
    section("06", "Meetings", meeting_html, "", accent=_PALETTE_V3["meetings"])
    script = """<script>document.querySelectorAll('[data-filter]').forEach(function(b){b.onclick=function(){var f=b.dataset.filter;document.querySelectorAll('.meeting-card').forEach(function(c){c.style.display=!f||c.dataset.ind===f?'':'none'})}});</script>"""
    return f"<!doctype html><html lang='zh-Hans'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Email Intelligence Panel · {_e(now_label)}</title><style>{_PANEL_V3_CSS}</style></head><body><main>{''.join(blocks)}</main>{script}</body></html>"


def render_email_markdown(emails: list[Email], reviews: list[dict], now_label: str,
                          window_label: str = "", last_events: dict | None = None,
                          report: dict | None = None) -> str:
    report = report or _build_report_v3(emails, reviews, last_events=last_events)
    out = [f"# Email Intelligence Brief — {now_label}", "", f"> {window_label}", ""]
    labels = [("01", "Worth Your Time", report["items"][:3]), ("02", "Industry", report["sections"]["industry_signal"]),
              ("03", "Core Watch", report["sections"]["core"]), ("04", "Other Coverage", report["sections"]["other_coverage"]),
              ("05", "New Ideas", report["sections"]["new_idea"])]
    for num, title, rows in labels:
        out += [f"## {num} · {title}", ""]
        if not rows:
            out += ["本窗口无新增内容", ""]
            continue
        for item in rows:
            name = item.get("company") or item.get("industry") or "Signal"
            out.append(f"- **{name}**")
            for fact in item.get("facts") or []:
                out.append(f"  - {fact.get('text')}（{fact.get('broker')}）")
        out.append("")
    out += ["## 06 · Meetings", ""]
    for m in _ordered_meetings_v3(report["meetings"], now_label):
        if str(m.get("recommendation")) == "skip":
            continue
        title = str(m.get("title") or "Meeting")
        registration = _registration_url_v3(m)
        title_text = f"[{title}]({registration})" if registration else f"**{title}**"
        out.append(f"- {title_text} — {m.get('date','')} {m.get('time','')} · {' · '.join(m.get('brokers') or [])}")
    if not report["meetings"]:
        out.append("本窗口无新增内容")
    return "\n".join(out).rstrip()
