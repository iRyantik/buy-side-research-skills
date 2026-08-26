"""Email Intelligence CLI: scan -> review -> rank -> brief -> optional delivery."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import uuid
from datetime import datetime
import zoneinfo
from pathlib import Path

from .ai_review import review_batch
from .brief import render_brief_html_v2, render_email_markdown, render_panel_html_v2
from .classify import normalize_reviews
from .context import build_context
from .parse import filter_new, scan_email_dirs
from .report import build_report, validate_report
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


def _archive_reviews(workspace: Path, now: datetime, fresh: list, raw: list, normalized: list,
                     metrics: dict | None = None, unstable: list | None = None) -> Path:
    """结构化存储：review 原始输出 + 归一化结果 + 邮件元数据——可复现/审计/二次处理。"""
    out = Path(workspace) / ".cache" / "email-intelligence" / "reviews"
    out.mkdir(parents=True, exist_ok=True)
    payload = {
        "run_at": now.isoformat(),
        "emails": [{"key": e.key, "subject": e.subject, "sender": e.sender,
                    "received_at": e.received_at, "outlook_link": e.outlook_link} for e in fresh],
        "raw_reviews": raw,
        "normalized": normalized,
        "metrics": metrics or {},
        "unstable_emails": [{"key": e.key, "error": e.parse_error} for e in (unstable or [])],
    }
    f = out / f"{now.strftime('%Y%m%d-%H%M%S')}.json"
    f.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    return f


def _archive_report(workspace: Path, now: datetime, report: dict) -> Path:
    """Immutable canonical report consumed by every presentation surface."""
    out = workspace / ".cache" / "email-intelligence" / "reports"
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"{now.strftime('%Y%m%d-%H%M%S')}-report.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    return path


def _outbox_dir(workspace: Path) -> Path:
    path = workspace / ".cache" / "email-intelligence" / "outbox"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _enqueue_delivery(workspace: Path, subject: str, text: str, html_path: Path,
                      panel_path: Path, error: str) -> Path:
    payload = {
        "created_at": datetime.now().isoformat(),
        "subject": subject,
        "text": text,
        "html_path": str(html_path),
        "panel_path": str(panel_path),
        "attempts": 1,
        "last_error": error,
    }
    path = _outbox_dir(workspace) / f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    return path


def _pending_deliveries(workspace: Path) -> list[Path]:
    return sorted(_outbox_dir(workspace).glob("*.json"))


def _attempt_outbox(workspace: Path, env: dict) -> tuple[list[str], list[str]]:
    """重试未送出的 brief；成功删除 outbox 项，失败保留并累计 gap。"""
    gaps: list[str] = []
    delivered: list[str] = []
    for path in _pending_deliveries(workspace):
        try:
            item = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            gaps.append(f"outbox_unreadable:{path.name}:{exc.__class__.__name__}")
            continue
        try:
            from coverage_monitor.delivery import send_email
            html_path = Path(item.get("html_path") or "")
            body_html = html_path.read_text(encoding="utf-8") if html_path.exists() else None
            item_gaps = send_email(
                item.get("subject", "Email Intelligence Brief"),
                item.get("text", ""),
                body_html=body_html,
                env=env,
                attachments=[Path(item["panel_path"])] if item.get("panel_path") else None,
            )
        except Exception as exc:
            item_gaps = [f"delivery_error: {exc}"]
        if not item_gaps:
            try:
                path.unlink()
                delivered.append(path.name)
            except OSError:
                gaps.append(f"outbox_remove_failed:{path.name}")
        else:
            item["attempts"] = int(item.get("attempts") or 0) + 1
            item["last_error"] = "; ".join(item_gaps)
            path.write_text(json.dumps(item, ensure_ascii=False, indent=1), encoding="utf-8")
            gaps.extend(item_gaps)
    return gaps, delivered


def review(base: str, workspace: Path, dry_run: bool = False, all_: bool = False,
           send: bool = True) -> int:
    # 报告时区配置化（REPORT_TZ env / 默认 Asia/Shanghai 东八）——不依赖运行机（Mac/UTC-7 vs 东八）
    now = datetime.now(zoneinfo.ZoneInfo(os.environ.get("REPORT_TZ") or "Asia/Shanghai"))
    now_label = f"{now.strftime('%Y-%m-%d %H:%M')} ({now.strftime('%z')[:3]}:{now.strftime('%z')[3:]})"
    emails = scan_email_dirs(base)
    if not emails:
        print(f"no emails found: {base}")
        return 0

    state = load_state(workspace)
    ready = [e for e in emails if e.parse_ok]
    unstable = [e for e in emails if not e.parse_ok]
    print(f"scan={len(emails)} ready={len(ready)} unstable={len(unstable)}")
    fresh = ready if all_ else filter_new(ready, set(state.get("seen", [])))
    print(f"new={len(fresh)}")

    delivery_gaps: list[str] = []
    if send and not dry_run:
        coverage_runtime = workspace / ".scripts" / "coverage-monitor"
        if str(coverage_runtime) not in sys.path:
            sys.path.insert(0, str(coverage_runtime))
        from coverage_monitor.delivery import workspace_env
        env = workspace_env(workspace)
        outbox_gaps, outbox_delivered = _attempt_outbox(workspace, env)
        delivery_gaps.extend(outbox_gaps)
        if outbox_delivered:
            state["last_sent"] = now_label
            print(f"outbox_delivered={len(outbox_delivered)}")

    if not fresh:
        print("no new emails")
        if delivery_gaps:
            print("delivery_gaps=" + "; ".join(delivery_gaps))
            return 3
        return 0

    context = build_context(workspace)
    # 跨天事件追踪：把历史事件基线传给 AI（判断 delta_vs_last），brief 用它标跟进
    events_baseline = last_events(state)
    context["last_events"] = events_baseline
    metrics = {"calls": 0, "elapsed": 0.0}
    started = time.monotonic()
    raw_reviews = review_batch(fresh, context, workspace, metrics=metrics)
    metrics["elapsed"] = round(time.monotonic() - started, 1)
    reviews = normalize_reviews(raw_reviews, context)
    archive = _archive_reviews(workspace, now, fresh, raw_reviews, reviews, metrics, unstable)
    print(f"archive={archive}")
    print(f"reviewed={len(reviews)}")
    if not reviews:
        print("review failed: no email was classified; state was not advanced", file=sys.stderr)
        return 2

    report = build_report(fresh, reviews, last_events=events_baseline)
    report_issues = validate_report(report)
    if report_issues:
        print(f"report_issues={len(report_issues)}")
        for issue in report_issues[:5]:
            print(f"  - {issue}")
    report_archive = _archive_report(workspace, now, report)
    print(f"report={report_archive}")
    html = render_brief_html_v2(
        fresh,
        reviews,
        now_label,
        f"覆盖窗口 {state.get('last_run') or '—'} → {now.strftime('%Y-%m-%d %H:%M')}",
        last_events=events_baseline,
        covered_industries=context.get("covered_industries"),
        report=report,
    )
    output = _brief_path(workspace, now)
    output.write_text(html, encoding="utf-8")
    print(f"brief={output} ({len(html)} bytes)")
    panel = render_panel_html_v2(
        fresh, reviews, now_label,
        f"覆盖窗口 {state.get('last_run') or '—'} → {now.strftime('%Y-%m-%d %H:%M')}",
        last_events=events_baseline,
        covered_industries=context.get("covered_industries"),
        report=report,
    )
    panel_out = output.with_name(f"{now:%Y%m%d}-email-panel.html")
    panel_out.write_text(panel, encoding="utf-8")
    print(f"panel={panel_out} ({len(panel)} bytes)")

    delivery_ok = dry_run or not send
    if not dry_run and send:
        try:
            from coverage_monitor.delivery import send_email, workspace_env
            # 正文 = lightweight Outlook HTML + markdown fallback；完整 panel 同步作为附件发送。
            text = render_email_markdown(
                fresh, reviews, now_label,
                f"覆盖窗口 {state.get('last_run') or '—'} → {now.strftime('%Y-%m-%d %H:%M')}",
                last_events=events_baseline,
                report=report,
            )
            gaps = send_email(
                f"Email Intelligence Brief — {now_label}",
                text,
                body_html=html,
                env=workspace_env(workspace),
                attachments=[panel_out],
            )
            if gaps:
                _enqueue_delivery(workspace, f"Email Intelligence Brief — {now_label}",
                                  text, output, panel_out, "; ".join(gaps))
                delivery_gaps.extend(gaps)
        except Exception as exc:
            _enqueue_delivery(workspace, f"Email Intelligence Brief — {now_label}",
                              text if "text" in locals() else "",
                              output, panel_out, f"delivery_error: {exc}")
            delivery_gaps.append(f"delivery_error: {exc}")
        print("delivery_gaps=" + ("; ".join(delivery_gaps) if delivery_gaps else "NONE"))
        delivery_ok = not delivery_gaps
        if delivery_ok:
            state["last_sent"] = now_label

    if not dry_run:
        completed = {str(review.get("_email_id") or "") for review in reviews
                     if review.get("status") == "ok"}
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
