from __future__ import annotations

import argparse
from dataclasses import replace
from datetime import datetime
import os
from pathlib import Path
import re
import time
from typing import Sequence

from .coverage import (
    CoverageEntry,
    CoverageUniverse,
    discover_company_directories,
    extract_date_prefix,
    list_markdown_artifacts,
    normalize_company_token,
    parse_coverage_markdown,
    render_coverage_markdown,
)
from .delivery import send_email, workspace_env
from .market_data import collect_snapshots
from .news import collect_company_news, collect_industry_readthroughs
from .reports import render_alert_markdown, render_daily_markdown, render_dashboard_html, should_alert_intraday
from .state import build_event_id, load_state, save_state
from .tiering import derive_coverage_status, derive_monitor_status, should_trigger_core_review


QUICKREAD_ARTIFACT_TOKENS = ("stock-quickread",)
DEEPWORK_ARTIFACT_TOKENS = (
    "alpha-thesis",
    "peer-deep-dive",
    "earnings-setup",
    "scenario-model",
    "driver-map",
    "catalyst-map",
    "moat-analysis",
    "consensus-map",
    "dcf-model",
    "3-statement-model",
    "bear-pre-mortem",
    "capital-allocation",
    "company-history",
    "pair-trade",
)


def _workspace_root(path: str | Path | None) -> Path:
    workspace = Path(path or ".").resolve()
    return workspace


def _relative_posix(path: Path, workspace: Path) -> str:
    try:
        return path.relative_to(workspace).as_posix()
    except ValueError:
        return path.as_posix()


def _artifact_inventory(company_dir: Path) -> tuple[int, str, str, int, int, bool]:
    artifacts = [artifact for artifact in list_markdown_artifacts(company_dir) if artifact.name.lower() != "index.md"]
    if not artifacts:
        return 0, "", "", 0, 0, (company_dir / "RESEARCH.md").exists()
    dated = [artifact for artifact in artifacts if extract_date_prefix(artifact.name)]
    latest = sorted(dated or artifacts, key=lambda item: item.name)[-1]
    names = [artifact.name.lower() for artifact in artifacts]
    quickread_count = sum(any(token in name for token in QUICKREAD_ARTIFACT_TOKENS) for name in names)
    deepwork_count = sum(any(token in name for token in DEEPWORK_ARTIFACT_TOKENS) for name in names)
    return (
        len(artifacts),
        latest.name,
        extract_date_prefix(latest.name),
        quickread_count,
        deepwork_count,
        (company_dir / "RESEARCH.md").exists(),
    )


def build_universe(workspace: Path, today: str | None = None) -> CoverageUniverse:
    coverage_path = workspace / "COVERAGE.md"
    gaps: list[str] = []
    rows: list[CoverageEntry] = []
    if coverage_path.exists():
        rows = parse_coverage_markdown(coverage_path.read_text(encoding="utf-8"))
    else:
        gaps.append("COVERAGE.md missing")

    merged: dict[str, CoverageEntry] = {}

    has_coverage_rows = bool(rows)

    def row_key(entry: CoverageEntry) -> str:
        company_token = normalize_company_token(entry.company)
        industry_token = normalize_company_token(entry.industry)
        if company_token:
            return f"{industry_token}:{company_token}"
        if entry.source_path.strip():
            return entry.source_path.strip().lower()
        return entry.ticker.strip().upper()

    def upsert(entry: CoverageEntry) -> None:
        key = row_key(entry)
        if not key:
            return
        if key not in merged:
            merged[key] = replace(entry)
            return
        current = merged[key]
        for field in (
            "ticker",
            "company",
            "industry",
            "coverage_status",
            "monitor_status",
            "last_review",
            "next_trigger",
            "notes",
            "source_path",
            "latest_artifact",
        ):
            value = getattr(entry, field)
            if value and not getattr(current, field):
                setattr(current, field, value)
        current.artifact_count = max(current.artifact_count, entry.artifact_count)

    for row in rows:
        upsert(row)

    for company_dir in discover_company_directories(workspace):
        (
            artifact_count,
            latest_artifact,
            artifact_date,
            quickread_count,
            deepwork_count,
            has_research_memory,
        ) = _artifact_inventory(company_dir)
        relative_path = _relative_posix(company_dir, workspace)
        industry = company_dir.parents[1].name if len(company_dir.parents) >= 2 else ""
        slug = company_dir.name
        matched_key = ""
        for key, entry in merged.items():
            if entry.source_path and entry.source_path == relative_path:
                matched_key = key
                break
            normalized_slug = normalize_company_token(slug)
            normalized_company = normalize_company_token(entry.company)
            company_parts = {part for part in re.split(r"[^a-z0-9]+", normalized_company) if part}
            if normalized_company == normalized_slug or normalized_slug in company_parts or normalized_company.endswith(f"-{normalized_slug}"):
                matched_key = key
                break
        if matched_key:
            entry = merged[matched_key]
            entry.source_path = relative_path
            entry.industry = entry.industry or industry
            entry.latest_artifact = latest_artifact or entry.latest_artifact
            entry.artifact_count = max(entry.artifact_count, artifact_count)
            entry.quickread_artifact_count = max(entry.quickread_artifact_count, quickread_count)
            entry.deepwork_artifact_count = max(entry.deepwork_artifact_count, deepwork_count)
            entry.has_research_memory = entry.has_research_memory or has_research_memory
            if artifact_date and not entry.last_review:
                entry.last_review = artifact_date
            continue
        if has_coverage_rows:
            gaps.append(f"unregistered_company_dir:{relative_path}")
            continue
        upsert(
            CoverageEntry(
                ticker="",
                company=slug,
                industry=industry,
                source_path=relative_path,
                latest_artifact=latest_artifact,
                last_review=artifact_date,
                artifact_count=artifact_count,
                quickread_artifact_count=quickread_count,
                deepwork_artifact_count=deepwork_count,
                has_research_memory=has_research_memory,
            )
        )

    entries = list(merged.values())
    for entry in entries:
        entry.coverage_status = entry.coverage_status or derive_coverage_status(
            entry, today=today, artifact_count=entry.artifact_count
        )
        entry.monitor_status = entry.monitor_status or derive_monitor_status(entry)
        if not entry.last_review and entry.latest_artifact:
            entry.last_review = extract_date_prefix(entry.latest_artifact)
        if entry.coverage_status != "Core Coverage" and should_trigger_core_review(entry, today=today):
            gaps.append(f"core_review_due:{entry.ticker or entry.company}")
    coverage_rank = {"Core Coverage": 0, "Building Coverage": 1, "Radar": 2}
    monitor_rank = {"Core Watch": 0, "Daily Watch": 1}
    entries.sort(
        key=lambda item: (
            item.industry.lower(),
            coverage_rank.get(item.coverage_status, 9),
            monitor_rank.get(item.monitor_status, 9),
            item.company.lower(),
        )
    )
    return CoverageUniverse(entries=entries, gaps=gaps)


def _doctor(workspace: Path) -> int:
    universe = build_universe(workspace)
    print(f"workspace={workspace}")
    print(f"entries={len(universe.entries)}")
    if universe.gaps:
        print("gaps=" + "; ".join(universe.gaps))
    environment = workspace_env(workspace)
    missing_env = [name for name in ("SMTP_HOST", "SMTP_USER", "SMTP_PASSWORD", "COVERAGE_EMAIL_TO") if not environment.get(name)]
    if missing_env:
        print("delivery_gaps=" + ", ".join(missing_env))
    return 0


def _normalize_coverage(workspace: Path, today: str | None, dry_run: bool) -> int:
    universe = build_universe(workspace, today=today)
    output = render_coverage_markdown(universe.entries)
    if dry_run:
        print(output)
        return 0
    (workspace / "COVERAGE.md").write_text(output, encoding="utf-8")
    print(f"wrote={workspace / 'COVERAGE.md'}")
    return 0


def _write_report_files(workspace: Path, stem: str, markdown_text: str, html_text: str) -> tuple[Path, Path]:
    report_dir = workspace / "reports" / "coverage-monitor"
    report_dir.mkdir(parents=True, exist_ok=True)
    markdown_path = report_dir / f"{stem}.md"
    html_path = report_dir / f"{stem}.html"
    markdown_path.write_text(markdown_text, encoding="utf-8")
    html_path.write_text(html_text, encoding="utf-8")
    return markdown_path, html_path


def _run_daily(workspace: Path, today: str | None, dry_run: bool) -> int:
    run_day = today or datetime.now().date().isoformat()
    universe = build_universe(workspace, today=run_day)
    snapshots, snapshot_gaps = collect_snapshots(universe.entries)
    company_news, company_news_gaps = collect_company_news(universe.entries, snapshots)
    industry_readthroughs, industry_gaps = collect_industry_readthroughs(workspace)
    gaps = sorted(set(universe.gaps + snapshot_gaps + company_news_gaps + industry_gaps))
    markdown_text = render_daily_markdown(universe.entries, snapshots, run_day, gaps, company_news, industry_readthroughs)
    html_text = render_dashboard_html(universe.entries, snapshots, run_day, gaps, company_news, industry_readthroughs)
    if dry_run:
        print(markdown_text)
        return 0
    stem = f"{run_day}-daily-coverage-brief"
    markdown_path, html_path = _write_report_files(workspace, stem, markdown_text, html_text)
    delivery_gaps = []
    email_body = "\n".join(markdown_text.splitlines()[:18]) + "\n\nFull dashboard HTML is attached."
    delivery_gaps.extend(
        send_email(
            f"Daily Coverage Brief {run_day}",
            email_body,
            None,
            env=workspace_env(workspace),
            attachments=[html_path],
        )
    )
    state = load_state(workspace)
    state["last_daily_report_date"] = run_day
    save_state(workspace, state)
    print(f"markdown={markdown_path}")
    print(f"html={html_path}")
    if delivery_gaps:
        print("delivery_gaps=" + "; ".join(delivery_gaps))
    return 0


def _collect_intraday_alerts(entries: list[CoverageEntry], snapshots: dict[str, dict], sent_event_ids: set[str]) -> tuple[list[CoverageEntry], list[str]]:
    alert_entries: list[CoverageEntry] = []
    new_event_ids: list[str] = []
    for entry in entries:
        snapshot = snapshots.get(entry.ticker or entry.company, {})
        if not should_alert_intraday(entry, snapshot):
            continue
        if snapshot.get("headline"):
            event_type = "headline"
            marker = str(snapshot.get("headline"))
        else:
            event_type = "price_move"
            marker = f"{snapshot.get('market_time', '')}|{snapshot.get('price_move_pct', 0)}"
        event_id = build_event_id(entry.ticker or entry.company, event_type, marker)
        if event_id in sent_event_ids:
            continue
        alert_entries.append(entry)
        new_event_ids.append(event_id)
    return alert_entries, new_event_ids


def _run_intraday(workspace: Path, dry_run: bool, once: bool, interval_minutes: int) -> int:
    while True:
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        universe = build_universe(workspace, today=datetime.now().date().isoformat())
        snapshots, snapshot_gaps = collect_snapshots(universe.entries)
        state = load_state(workspace)
        sent_event_ids = set(state.get("sent_event_ids", []))
        alert_entries, new_event_ids = _collect_intraday_alerts(universe.entries, snapshots, sent_event_ids)
        if alert_entries:
            markdown_text = render_alert_markdown(alert_entries, snapshots, now)
            if dry_run:
                print(markdown_text)
            else:
                send_email(f"Intraday Coverage Alerts {now}", markdown_text, env=workspace_env(workspace))
                state["sent_event_ids"] = sorted(sent_event_ids.union(new_event_ids))
                state["last_intraday_run_at"] = now
                save_state(workspace, state)
        else:
            print("no_intraday_alerts")
        if snapshot_gaps:
            print("snapshot_gaps=" + "; ".join(snapshot_gaps))
        if dry_run or once:
            return 0
        time.sleep(max(interval_minutes, 1) * 60)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run coverage monitoring from workspace coverage state.")
    parser.add_argument("--workspace", default=".", help="Workspace root path.")
    workspace_parent = argparse.ArgumentParser(add_help=False)
    workspace_parent.add_argument("--workspace", default=".", help="Workspace root path.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("doctor", parents=[workspace_parent], help="Check coverage-monitor workspace readiness.")

    normalize = subparsers.add_parser("normalize-coverage", parents=[workspace_parent], help="Normalize COVERAGE.md to the canonical table.")
    normalize.add_argument("--dry-run", action="store_true", help="Print normalized coverage without writing.")
    normalize.add_argument("--today", default="", help="Override the reference date (YYYY-MM-DD).")

    daily = subparsers.add_parser("daily", parents=[workspace_parent], help="Generate the daily coverage brief.")
    daily.add_argument("--dry-run", action="store_true", help="Render without writing or sending.")
    daily.add_argument("--today", default="", help="Override the report date (YYYY-MM-DD).")

    intraday = subparsers.add_parser("intraday", parents=[workspace_parent], help="Run intraday alert monitoring.")
    intraday.add_argument("--dry-run", action="store_true", help="Evaluate alerts without sending.")
    intraday.add_argument("--once", action="store_true", help="Run one pass and exit.")
    intraday.add_argument("--interval-minutes", type=int, default=15, help="Polling interval for looping mode.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    workspace = _workspace_root(args.workspace)
    if not workspace.exists():
        print(f"workspace_not_found={workspace}")
        return 2

    try:
        if args.command == "doctor":
            return _doctor(workspace)
        if args.command == "normalize-coverage":
            return _normalize_coverage(workspace, today=args.today or None, dry_run=args.dry_run)
        if args.command == "daily":
            return _run_daily(workspace, today=args.today or None, dry_run=args.dry_run)
        if args.command == "intraday":
            return _run_intraday(workspace, dry_run=args.dry_run, once=args.once or args.dry_run, interval_minutes=args.interval_minutes)
    except UnicodeDecodeError:
        return 2
    return 0
