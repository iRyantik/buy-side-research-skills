"""Render a lightweight, Outlook-compatible six-section Email Brief."""

from __future__ import annotations

import html
import re
from collections import defaultdict
from datetime import date, datetime

from .parse import Email


def _e(value) -> str:
    return html.escape(str(value or ""), quote=True)


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
