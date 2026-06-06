"""Runtime manager public CLI."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ..deployment import (
    DeploymentManager,
    build_release_payload,
    discover_runtime_source,
    sync_hosts,
    verify_release_payload,
    verify_workspace,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage the buy-side research workspace runtime")
    parser.add_argument(
        "command",
        choices=(
            "init",
            "update",
            "repair",
            "plan",
            "verify",
            "adopt",
            "update-hosts",
            "build-release",
            "verify-release",
        ),
    )
    parser.add_argument("--workspace", default=".")
    parser.add_argument("--payload-root")
    parser.add_argument("--manifest")
    parser.add_argument("--runtime-root")
    parser.add_argument("--source", help="Release payload root for host sync or release verification")
    parser.add_argument("--home", help="Host home directory override for tests/dry-runs")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--target", action="append", default=[], help="Explicit conflict target to adopt")
    parser.add_argument("--plugin-root", help="Plugin dev repo root for build-release")
    parser.add_argument("--version", default="6.0.0-rc.2")
    parser.add_argument("--dist-root")
    return parser


def _default_plugin_root() -> Path:
    return Path(__file__).resolve().parents[3]


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    workspace = Path(args.workspace).resolve()
    if args.command == "build-release":
        report = build_release_payload(
            Path(args.plugin_root).resolve() if args.plugin_root else _default_plugin_root(),
            version=args.version,
            dist_root=Path(args.dist_root).resolve() if args.dist_root else None,
        )
        print(json.dumps(report, indent=2))
        return 0 if report["status"] == "ok" else 1
    if args.command == "verify-release":
        if not args.source:
            raise SystemExit("verify-release requires --source <release-payload-root>")
        report = verify_release_payload(Path(args.source))
        print(json.dumps(report, indent=2))
        return 0 if report["status"] == "ok" else 1
    if args.command == "update-hosts":
        if not args.source:
            raise SystemExit("update-hosts requires --source <release-payload-root>")
        report = sync_hosts(
            Path(args.source),
            home=Path(args.home).resolve() if args.home else None,
            dry_run=args.dry_run,
        )
        print(json.dumps(report, indent=2))
        return 0 if report["status"] in {"ok", "dry-run"} else 1
    if args.command == "verify":
        report = verify_workspace(workspace)
        print(json.dumps(report, indent=2))
        return 0 if report["status"] == "ok" else 1
    if args.payload_root or args.manifest:
        if not args.payload_root or not args.manifest:
            raise SystemExit("--payload-root and --manifest must be provided together")
        payload_root, manifest = Path(args.payload_root), Path(args.manifest)
    else:
        payload_root, manifest = discover_runtime_source(start=workspace, runtime_root=args.runtime_root)
    manager = DeploymentManager(payload_root, workspace, manifest)
    plan = manager.plan()
    if args.command == "plan":
        print(json.dumps(plan.as_dict(), indent=2))
        return 0
    if args.command == "adopt":
        report = manager.adopt_conflicts(args.target, dry_run=args.dry_run)
        print(json.dumps(report, indent=2))
        return 0
    manager.apply(plan)
    report = {"status": "conflicts" if plan.conflict else "ok", "plan": plan.as_dict()}
    print(json.dumps(report, indent=2))
    return 0 if not plan.conflict else 2


if __name__ == "__main__":
    raise SystemExit(main())
