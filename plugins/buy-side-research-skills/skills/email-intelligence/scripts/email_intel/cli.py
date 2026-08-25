"""Email Intelligence CLI: scan -> review -> rank -> brief -> optional delivery."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

from .ai_review import review_batch
from .brief import render_brief_html, render_brief_html_v2, render_email_markdown, render_panel_html_v2
from .classify import normalize_reviews
from .context import build_context
from .parse import filter_new, scan_email_dirs
from .state import last_events, load_state, mark_seen, save_state, update_events


def _workspace_from_script() -> Path:
    return Path(__file__).resolve().parents[3]


def _default_base() -> str:
    configured = os.environ.get("EMAIL_INTELLIGENCE_BASE")
    if configured:
        return configured
    return str(Path.home() / "OneDrive - Hel Ved Capital Management Limited" / "Email-AI")


def _brief_path(workspace: Path, now: datetime | None = None) -> Path:
    """渲染输出固定为单一文件（覆盖，不生成时间戳变体）——as-of 已写入 scope-note。"""
    output_dir = workspace / "daily" / "email"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir / f"{now:%Y%m%d}-email-brief.html"


def _archive_reviews(workspace: Path, now: datetime, fresh: list, raw: list, normalized: list) -> Path:
    """结构化存储：review 原始输出 + 归一化结果 + 邮件元数据——可复现/审计/二次处理。"""
    out = Path(workspace) / ".cache" / "email-intelligence" / "reviews"
    out.mkdir(parents=True, exist_ok=True)
    payload = {
        "run_at": now.isoformat(),
        "emails": [{"key": e.key, "subject": e.subject, "sender": e.sender,
                    "received_at": e.received_at, "outlook_link": e.outlook_link} for e in fresh],
        "raw_reviews": raw,
        "normalized": normalized,
    }
    f = out / f"{now.strftime('%Y%m%d-%H%M%S')}.json"
    f.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    return f


def review(base: str, workspace: Path, dry_run: bool = False, all_: bool = False,
           send: bool = True) -> int:
    now = datetime.now().astimezone()
    emails = scan_email_dirs(base)
    if not emails:
        print(f"no emails found: {base}")
        return 0

    state = load_state(workspace)
    fresh = emails if all_ else filter_new(emails, set(state.get("seen", [])))
    print(f"scan={len(emails)} new={len(fresh)}")
    if not fresh:
        print("no new emails")
        return 0

    context = build_context(workspace)
    # 跨天事件追踪：把历史事件基线传给 AI（判断 delta_vs_last），brief 用它标跟进
    events_baseline = last_events(state)
    context["last_events"] = events_baseline
    raw_reviews = review_batch(fresh, context, workspace)
    reviews = normalize_reviews(raw_reviews, context)
    archive = _archive_reviews(workspace, now, fresh, raw_reviews, reviews)
    print(f"archive={archive}")
    print(f"reviewed={len(reviews)}")
    if not reviews:
        print("review failed: no email was classified; state was not advanced", file=sys.stderr)
        return 2

    # %Z 时区名在部分客户端/系统会有编码乱码（??????），改用偏移量
    now_label = f"{now.strftime('%Y-%m-%d %H:%M')} ({now.strftime('%z')[:3]}:{now.strftime('%z')[3:]})"
    html = render_brief_html_v2(
        fresh,
        reviews,
        now_label,
        f"覆盖窗口 {state.get('last_run') or '—'} → {now.strftime('%Y-%m-%d %H:%M')}",
        last_events=events_baseline,
        covered_industries=context.get("covered_industries"),
    )
    output = _brief_path(workspace, now)
    output.write_text(html, encoding="utf-8")
    print(f"brief={output} ({len(html)} bytes)")
    panel = render_panel_html_v2(
        fresh, reviews, now_label,
        f"覆盖窗口 {state.get('last_run') or '—'} → {now.strftime('%Y-%m-%d %H:%M')}",
        last_events=events_baseline,
        covered_industries=context.get("covered_industries"),
    )
    panel_out = output.with_name(f"{now:%Y%m%d}-email-panel.html")
    panel_out.write_text(panel, encoding="utf-8")
    print(f"panel={panel_out} ({len(panel)} bytes)")

    delivery_ok = dry_run or not send
    if not dry_run and send:
        coverage_runtime = workspace / ".scripts" / "coverage-monitor"
        if str(coverage_runtime) not in sys.path:
            sys.path.insert(0, str(coverage_runtime))
        try:
            from coverage_monitor.delivery import send_email, workspace_env
            # 正文 = markdown 摘要（与 coverage-monitor 日报同款）；完整面板 = body_html（本地留档，不挂附件）
            text = render_email_markdown(
                fresh, reviews, now_label,
                f"覆盖窗口 {state.get('last_run') or '—'} → {now.strftime('%Y-%m-%d %H:%M')}",
            )
            gaps = send_email(
                f"Email Intelligence Brief — {now_label}",
                text,
                body_html=html,
                env=workspace_env(workspace),
            )
        except Exception as exc:
            gaps = [f"delivery_error: {exc}"]
        print("delivery_gaps=" + ("; ".join(gaps) if gaps else "NONE"))
        delivery_ok = not gaps
        if delivery_ok:
            state["last_sent"] = now_label

    completed = {str(review.get("_email_id") or "") for review in reviews}
    mark_seen(state, [email.key for email in fresh if email.key in completed])
    update_events(state, reviews, now_label)
    state["last_run"] = now_label
    save_state(workspace, state)
    if send and not dry_run and not delivery_ok:
        return 3
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Review saved sell-side emails and generate a buy-side brief")
    subparsers = parser.add_subparsers(dest="command", required=True)
    review_parser = subparsers.add_parser("review")
    review_parser.add_argument("--base", default=_default_base(), help="Email-AI preservation directory")
    review_parser.add_argument("--workspace", default=str(_workspace_from_script()), help="Research workspace root")
    review_parser.add_argument("--dry-run", action="store_true", help="Generate the brief without sending email")
    review_parser.add_argument("--all", action="store_true", dest="all_", help="Ignore incremental state")
    review_parser.add_argument("--no-send", action="store_true", help="Do not deliver email")
    args = parser.parse_args(argv)
    if args.command == "review":
        return review(
            base=args.base,
            workspace=Path(args.workspace).expanduser().resolve(),
            dry_run=args.dry_run,
            all_=args.all_,
            send=not args.no_send,
        )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
