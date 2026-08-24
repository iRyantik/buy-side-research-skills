"""Email Intelligence CLI: scan -> review -> rank -> brief -> optional delivery."""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

from .ai_review import review_batch
from .brief import render_brief_html
from .classify import normalize_reviews
from .context import build_context
from .parse import filter_new, scan_email_dirs
from .state import load_state, mark_seen, save_state


def _workspace_from_script() -> Path:
    return Path(__file__).resolve().parents[3]


def _default_base() -> str:
    configured = os.environ.get("EMAIL_INTELLIGENCE_BASE")
    if configured:
        return configured
    return str(Path.home() / "OneDrive - Hel Ved Capital Management Limited" / "Email-AI")


def _brief_path(workspace: Path, now: datetime) -> Path:
    output_dir = workspace / "daily" / "email"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir / f"{now:%Y%m%d}-email-brief-{now:%H%M}.html"


def review(base: str, workspace: Path, dry_run: bool = False, all_: bool = False,
           send: bool = True) -> int:
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
    raw_reviews = review_batch(fresh, context, workspace)
    reviews = normalize_reviews(raw_reviews, context)
    print(f"reviewed={len(reviews)}")
    if not reviews:
        print("review failed: no email was classified; state was not advanced", file=sys.stderr)
        return 2

    now = datetime.now().astimezone()
    now_label = now.strftime("%Y-%m-%d %H:%M %Z")
    html = render_brief_html(
        fresh,
        reviews,
        now_label,
        f"覆盖窗口 {state.get('last_run') or '—'} → {now.strftime('%Y-%m-%d %H:%M')}",
    )
    output = _brief_path(workspace, now)
    output.write_text(html, encoding="utf-8")
    print(f"brief={output} ({len(html)} bytes)")

    delivery_ok = dry_run or not send
    if not dry_run and send:
        coverage_runtime = workspace / ".scripts" / "coverage-monitor"
        if str(coverage_runtime) not in sys.path:
            sys.path.insert(0, str(coverage_runtime))
        try:
            from coverage_monitor.delivery import send_email, workspace_env
            gaps = send_email(
                f"Email Intelligence Brief — {now_label}",
                "Email Intelligence Brief（HTML 正文）。",
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
