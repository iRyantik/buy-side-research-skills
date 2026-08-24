"""Render a lightweight, Outlook-compatible five-section Email Brief."""

from __future__ import annotations

import html
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


_SECTION_META = {
    "core": ("01", "Core Watch", BLUE),
    "other_coverage": ("02", "Other Coverage", "#64748b"),
    "new_idea": ("03", "New Ideas", GREEN),
    "industry_signal": ("04", "Industry & Sell-side Signals", AMBER),
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


def _item_card(item: dict, emails: dict[str, Email], bar: str, followup: bool = False) -> str:
    company = item.get("company") or item.get("industry") or "Signal"
    ticker = item.get("ticker") or item.get("coverage_ticker") or ""
    event = str(item.get("event_type") or item.get("kind") or "UPDATE").upper()
    action = str(item.get("action") or "note").upper()
    priority = str(item.get("priority") or "medium").upper()
    sources = [_source_link(emails.get(key)) for key in item.get("_email_ids", [])]
    sources = [source for source in sources if source]
    meta = " &nbsp; ".join(part for part in [_pill(event, bar), _pill(action, bar), _pill(priority, bar)] if part)
    followup_line = ""
    if followup:
        followup_line = f"<div style='margin-top:5px;color:{MUTED};font-size:11.5px'>↺ 该事件此前已有 broker 提及</div>"
    delta_line = ""
    if item.get("delta_vs_last"):
        delta_line = f"<div style='margin-top:5px;font-size:12.5px;line-height:20px;color:#9a3412'><b>新增：</b>{_e(item['delta_vs_last'])}</div>"
    focus_line = ""
    if item.get("focus_reason"):
        focus_line = f"<div style='margin-top:5px;color:{MUTED}'><b>Focus：</b>{_e(item['focus_reason'])}</div>"
    impact_line = ""
    if item.get("why_it_matters"):
        impact_line = f"<div style='margin-top:5px;color:{MUTED}'><b>Why it matters：</b>{_e(item['why_it_matters'])}</div>"
    reason_line = ""
    if item.get("action_reason"):
        reason_line = f"<div style='margin-top:5px;color:{MUTED}'><b>Action：</b>{_e(item['action_reason'])}</div>"
    source_line = f"<div style='margin-top:7px'>{' · '.join(sources)}</div>" if sources else ""
    return f"""
<table role='presentation' width='100%' cellpadding='0' cellspacing='0' border='0' style='border:1px solid {BORDER};background:{CARD_BG};border-radius:14px'>
<tr><td width='4' style='background:{bar}'></td><td style='padding:12px 14px'>
<div style='font-size:14px;line-height:21px;font-weight:900;color:{INK}'>{_e(company)}{f" <span style='color:{MUTED};font-size:11px'>({_e(ticker)})</span>" if ticker else ""}</div>
<div style='margin-top:4px'>{meta}</div>
<div style='font-size:12.5px;line-height:20px;color:#334155;margin-top:7px'>{_e(item.get('what_changed') or '—')}</div>
{followup_line}{delta_line}{impact_line}{focus_line}{reason_line}{source_line}
</td></tr></table>"""


def _meeting_card(meeting: dict, emails: dict[str, Email]) -> str:
    recommendation = str(meeting.get("recommendation") or "medium").lower()
    color = {"high": GREEN, "medium": AMBER, "low": MUTED}.get(recommendation, MUTED)
    details = []
    for label, key in (("时间", "date"), ("时段", "time"), ("主办", "host"), ("形式", "format"), ("地点", "location"), ("讲者", "participants")):
        if meeting.get(key):
            details.append(f"<b>{label}</b> {_e(meeting[key])}")
    source = _source_link(emails.get(meeting.get("_email_id", "")))
    return f"""
<table role='presentation' width='100%' cellpadding='0' cellspacing='0' border='0' style='border:1px solid {BORDER};background:{CARD_BG};border-radius:14px'>
<tr><td width='4' style='background:{color}'></td><td style='padding:12px 14px'>
<div style='font-size:14px;line-height:21px;font-weight:900;color:{INK}'>{_e(meeting.get('title') or meeting.get('company') or 'Meeting')}</div>
<div style='margin-top:4px'>{_pill(f"{recommendation.upper()} PRIORITY", color)}</div>
<div style='font-size:12px;line-height:20px;color:#334155;margin-top:7px'>{' &nbsp;·&nbsp; '.join(details)}</div>
<div style='font-size:12.5px;line-height:20px;color:#334155;margin-top:5px'><b>主题：</b>{_e(meeting.get('topic') or '—')}</div>
<div style='font-size:12px;line-height:19px;color:{MUTED};margin-top:5px'><b>推荐：</b>{_e(meeting.get('reason') or '—')}</div>
{f"<div style='margin-top:7px'>{source}</div>" if source else ''}
</td></tr></table>"""


def render_brief_html(emails: list[Email], reviews: list[dict], now_label: str, window_label: str = "",
                      last_events: dict | None = None) -> str:
    email_by_id = _email_map(emails)
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

    reviewed_ids = {review.get("_email_id") for review in reviews}
    filtered = sum(1 for review in reviews if not review.get("items") and not review.get("meetings"))
    missing = len(emails) - len(reviewed_ids)
    blocks.append(f"""
<tr><td style='padding:20px 28px 28px'>
<div style='font-size:11px;line-height:18px;color:{MUTED};border-top:1px solid {BORDER};padding-top:10px'>
Processed {len(emails)} emails · filtered {filtered} · review failures {missing}
</div></td></tr>""")

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
