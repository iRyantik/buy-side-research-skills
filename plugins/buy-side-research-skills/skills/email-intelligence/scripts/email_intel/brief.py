"""Render a lightweight, Outlook-compatible five-section Email Brief."""

from __future__ import annotations

import html
import re
from collections import defaultdict

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
            key = one.get("merge_key") or f"{email_id}:{len(merged)}"
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
    """会议行统一制式：标题蓝链+形式语言席位 | 机构；讲者看点主持 | 时间黑粗；相关 chips。"""
    title = m.get("title") or m.get("company") or "Meeting"
    em = emails.get(str(m.get("_email_id") or ""))
    reg = str(m.get("registration") or "")
    org = _e(_broker_label(em.sender, getattr(em, 'broker', ''))) if em else ''
    # 标题链接：仅当有真实报名链接才可点；没有就不 fallback（保持纯文本）
    if reg.startswith("http"):
        link_title = f"<a class='src' style='font-weight:800;color:#2563eb' href='{_e(reg)}'>{_e(title)}</a>"
    else:
        link_title = f"<span style='font-weight:800;color:#2563eb'>{_e(title)}</span>"
    extra = " · ".join(x for x in [m.get("format") or "", m.get("language") or "",
                                   ("限 " + str(m["seats_limit"])) if m.get("seats_limit") else ""] if x)
    org_link = (f"<a class='src' href='{_e(em.outlook_link)}'>{org}</a>"
                if (em and em.outlook_link) else
                (f"<span class='src' style='color:#94a3b8'>{org}</span>" if org else ""))
    line1 = f"<div class='line'><div class='line-main'>· {link_title}"
    if extra:
        line1 += f" · {_e(extra)}"
    line1 += f"</div><div class='line-links'>{org_link}</div></div>"
    parts = []
    if m.get("participants"):
        parts.append("讲者：" + _e(str(m["participants"])))
    agenda = m.get("agenda_items") or []
    if agenda:
        parts.append("看点：" + _e("·".join(str(x) for x in list(agenda)[:3])))
    if m.get("host_person"):
        parts.append("主持：" + _e(m["host_person"]))
    time_s = " · ".join(x for x in [_norm_time(m.get("time")), _norm_time(m.get("time_end"))] if x)
    # 行2：讲者/看点/主持 左 + 时间 右（黑粗）——时间**独立渲染**，不依赖讲者/看点（即使只有时间也显示）
    line2 = ""
    if parts or time_s:
        left = " · ".join(parts) if parts else ""
        time_cell = (f"<div class='line-links' style='font-weight:800;color:#132238;font-size:12px'>{_e(time_s)}</div>"
                     if time_s else "")
        line2 = (f"<div class='line' style='margin-top:0'><div class='line-main' "
                 f"style='font-size:12px;color:#132238;margin:0;padding-left:14px'>{_e(left)}</div>"
                 f"{time_cell}</div>")
    rel = m.get("related_tickers") or []
    line3 = ""
    if rel:
        chips = "".join(f"<span class='chip'>{_e(str(x))}</span>" for x in list(rel)[:6])
        line3 = f"<div class='small' style='margin:2px 0 0;padding-left:14px;color:#132238'>{chips}</div>"
    return line1 + line2 + line3


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
            blocks.append(f"<div class='line'><div class='line-main'>· {_e(str(body))}</div>"
                          f"<div class='line-links'>{src}</div></div>")
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
            blocks.append(f"<div class='line'><div class='line-main'>· {tick} {_st}{core} {brief}</div>"
                          f"<div class='line-links'>{src}</div></div>")
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
    return (f"<div class='card ind-card'><div class='card-title'><b>{_e(name)}</b> {st}{core} "
            f"<span style='float:right'>{src}</span></div><div class='txt'>{summary}</div>"
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
            f"<div class='line'><div class='line-main'>{body}</div>"
            f"<div class='line-links'>{src}</div></div></div>")
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
.indust-grid{display:flex;flex-wrap:wrap;gap:12px}
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
.grouplabel{color:#64748b;font-weight:750;margin-top:8px}
.core-pill{display:inline-flex;align-items:center;height:19px;border-radius:999px;padding:0 7px;background:#7c3aed;color:#fff;font-size:10px;font-weight:950;line-height:1;margin:0 4px 4px 0}
.card-meeting{margin-top:8px;padding:8px 0 2px;border-top:1px dashed #e2e8f0;color:#64748b}
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
.indust-grid{display:flex;flex-wrap:wrap;gap:14px}
.ind-card{flex:1 1 280px;box-sizing:border-box}
.line{display:flex;justify-content:space-between;align-items:baseline;gap:12px;margin-top:6px}
.line-main{font-size:13.5px;line-height:1.65;color:#334155}
.line-links{white-space:nowrap;flex-shrink:0;text-align:right;font-size:12px}
.grouplabel{color:var(--muted);font-weight:750;margin-top:8px}
.sep{border:0;border-top:1px solid var(--line);margin:10px 0}
.card-meeting{margin-top:10px;padding-top:8px;border-top:1px dashed var(--line);color:var(--muted)}
.filter-row{display:flex;flex-wrap:wrap;align-items:center;gap:6px;margin:0 0 12px}
.filter-label{font-size:12px;font-weight:800;color:var(--muted)}
.filter-chip{display:inline-block;border-radius:999px;padding:4px 12px;font-size:12px;font-weight:700;border:1px solid var(--line);background:#fff;color:var(--slate);cursor:pointer}
.filter-chip.on{background:var(--blue);border-color:var(--blue);color:#fff}
.filter-clear{font-size:12px;color:var(--blue);cursor:pointer;font-weight:700}
.date-group-label{font-size:13.5px;font-weight:800;color:var(--ink);margin:16px 2px 8px}
.meeting-card.hidden{display:none}
.health-line{border:1px solid var(--line);border-radius:18px;background:rgba(255,255,255,.9);padding:14px 18px;font-size:12.5px;color:var(--muted)}
@media (max-width:640px){main{width:calc(100vw - 20px)}.card{padding:12px}.indust-grid{grid-template-columns:1fr}}

.indust-grid{display:grid;grid-template-columns:repeat(2,1fr)}
.indust-grid.cols-4{grid-template-columns:repeat(4,1fr)}
.indust-grid.cols-3{grid-template-columns:repeat(3,1fr)}
.meet-skip{opacity:.55}
@media (max-width:640px){.indust-grid,.indust-grid.cols-4,.indust-grid.cols-3{grid-template-columns:1fr}}"""


def _meeting_card_panel(m: dict, emails: dict, skip: bool = False) -> str:
    cls = "card ind-card meeting-card meet-skip" if skip else "card ind-card meeting-card"
    ind = _e(str(m.get("industry") or ""))
    return (f"<div class='{cls}' data-ind='{ind}'>" + _meeting_line_v2(m, emails) + "</div>")


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
</main></body></html>"""
