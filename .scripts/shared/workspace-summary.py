#!/usr/bin/env python3
"""Print a quick summary of workspace coverage for new sessions.

Usage:
    python workspace-summary.py            # human-readable
    python workspace-summary.py --json     # machine-readable
    python workspace-summary.py --recent 7 # last N days only
"""

import argparse, json, os, sys, time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def find_workspace_root():
    p = Path.cwd()
    for _ in range(10):
        if (p / ".claude" / "hooks" / "hook_entry.py").exists():
            return p
        if p.parent == p: break
        p = p.parent
    return None


def scan(workspace, recent_days=0):
    cutoff = time.time() - recent_days * 86400 if recent_days else 0

    companies = {}
    industries = {}
    recent = []

    ind_dir = workspace / "industry"
    if not ind_dir.is_dir():
        return companies, industries, recent

    # Scan companies
    for comp_dir in sorted(ind_dir.glob("*/companies/*")):
        if not comp_dir.is_dir():
            continue
        artifacts = []
        for f in sorted(comp_dir.glob("*.md")):
            if f.name != "RESEARCH.md" and ".cache" not in str(f):
                mtime = f.stat().st_mtime
                artifacts.append((f.name, mtime))
                if mtime > cutoff:
                    recent.append((mtime, str(f.relative_to(workspace))))

        industry = comp_dir.parent.parent.name
        companies.setdefault(industry, {})[comp_dir.name] = len(artifacts)

    # Scan industries
    for ind in sorted(ind_dir.iterdir()):
        if not ind.is_dir():
            continue
        pan_count = 0
        pan_dir = ind / "panorama"
        if pan_dir.is_dir():
            for skill_dir in pan_dir.iterdir():
                if skill_dir.is_dir():
                    pan_count += len(list(skill_dir.glob("*.md")))
        industries[ind.name] = pan_count

    return companies, industries, recent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--recent", type=int, default=7, help="Days for recent activity (default 7)")
    args = parser.parse_args()

    ws = find_workspace_root()
    if not ws:
        print("Not in a CC research workspace.")
        return

    companies, industries, recent = scan(ws, args.recent)

    if args.json:
        data = {
            "workspace": str(ws),
            "companies": {ind: {c: n for c, n in comp.items()} for ind, comp in companies.items()},
            "industries": {ind: n for ind, n in industries.items()},
            "recent": sorted(recent, reverse=True)[:20],
        }
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return

    print(f"Workspace: {ws}")
    print()

    total_companies = sum(len(c) for c in companies.values())
    total_panorama = sum(industries.values())
    print(f"覆盖：{len(industries)} 个行业 | {total_companies} 家公司 | {total_panorama} 份行业研究")
    print()

    # Companies by industry
    for ind, comps in sorted(companies.items()):
        pancount = industries.get(ind, 0)
        print(f"  {ind} ({len(comps)} 公司, {pancount} 行业研究)")
        for cname, n in sorted(comps.items()):
            print(f"    {cname} ({n} artifacts)")
    print()

    # Recent activity
    recent_sorted = sorted(recent, reverse=True)
    if recent_sorted:
        print(f"=== Recent ({args.recent}d) ===")
        for mtime, path in recent_sorted[:10]:
            days = (time.time() - mtime) / 86400
            print(f"  {days:.0f}d ago  {path}")
    else:
        print("No recent activity.")


if __name__ == "__main__":
    main()
