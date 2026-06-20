from __future__ import annotations

from collections import defaultdict
from html import escape
from typing import Any

from .coverage import CoverageEntry


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


def should_alert_intraday(entry: CoverageEntry, snapshot: dict[str, Any]) -> bool:
    if entry.alert_tier.strip().upper() != "A1":
        return False
    move = abs(float(snapshot.get("price_move_pct") or 0.0))
    if move >= 5.0:
        return True
    headline = str(snapshot.get("headline") or "").lower()
    return any(keyword in headline for keyword in ALERT_KEYWORDS)


def render_daily_markdown(
    entries: list[CoverageEntry],
    snapshots: dict[str, dict[str, Any]],
    today: str,
    gaps: list[str],
) -> str:
    grouped: dict[str, list[CoverageEntry]] = defaultdict(list)
    for entry in entries:
        grouped[entry.industry or "unclassified"].append(entry)

    lines = [
        f"# Daily Coverage Brief - {today}",
        "",
        "## 1. Top Alerts",
    ]
    alert_lines = []
    for entry in entries:
        snapshot = snapshots.get(entry.ticker or entry.company, {})
        if entry.alert_tier == "A1":
            if snapshot:
                alert_lines.append(
                    f"- `{entry.ticker or entry.company}` {entry.company}: {snapshot.get('price_move_pct', 0)}% | {snapshot.get('headline') or entry.next_trigger or 'watch core coverage'}"
                )
            else:
                alert_lines.append(f"- `{entry.ticker or entry.company}` {entry.company}: no live snapshot, keep on manual watch")
    if not alert_lines:
        alert_lines.append("- No A1 alerts triggered in this run.")
    lines.extend(alert_lines)
    lines.extend(["", "## 2. Industry Coverage"])

    for industry in sorted(grouped):
        lines.append(f"### {industry}")
        for entry in sorted(grouped[industry], key=lambda item: (item.research_tier, item.company.lower())):
            lines.append(
                f"- `{entry.ticker or 'NO-TICKER'}` {entry.company} | {entry.research_tier or 'NA'} / {entry.alert_tier or 'NA'} | {entry.stage or 'NA'} | {entry.next_trigger or 'no trigger'}"
            )
    lines.extend(["", "## 3. Upcoming Triggers"])
    trigger_rows = [entry for entry in entries if entry.next_trigger.strip()]
    if trigger_rows:
        for entry in sorted(trigger_rows, key=lambda item: item.next_trigger.lower()):
            lines.append(f"- `{entry.ticker or 'NO-TICKER'}` {entry.company}: {entry.next_trigger}")
    else:
        lines.append("- No upcoming triggers recorded.")
    lines.extend(["", "## 4. Data & Monitor Gaps"])
    if gaps:
        for gap in gaps:
            lines.append(f"- {gap}")
    else:
        lines.append("- No material data or monitor gaps in this run.")

    lines.extend(
        [
            "",
            "## 5. Appendix: Full Watchlist Snapshot",
            "",
            "| Ticker | Company | Industry | Research Tier | Alert Tier | Stage | Last Review | Next Trigger | Monitor |",
            "|---|---|---|---|---|---|---|---|---|",
        ]
    )
    for entry in entries:
        lines.append(
            f"| {entry.ticker or ''} | {entry.company} | {entry.industry} | {entry.research_tier} | {entry.alert_tier} | {entry.stage} | {entry.last_review} | {entry.next_trigger} | {entry.monitor} |"
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


def render_html(markdown_text: str, title: str) -> str:
    return (
        "<!doctype html>\n"
        "<html><head><meta charset=\"utf-8\">"
        f"<title>{escape(title)}</title>"
        "<style>body{font-family:Georgia,serif;max-width:980px;margin:40px auto;padding:0 20px;line-height:1.5;color:#1d1d1f;background:#f5f1e8}"
        "pre{white-space:pre-wrap;font-family:'SFMono-Regular',Consolas,monospace;background:#fffdf8;padding:24px;border:1px solid #d9cfb8;border-radius:12px}</style>"
        "</head><body>"
        f"<pre>{escape(markdown_text)}</pre>"
        "</body></html>"
    )
