#!/usr/bin/env python3
"""Validate workspace artifact + company directory naming against CLAUDE.md §3.2/§3.3.

Company directory rule (CLAUDE.md §3.3):
    <TICKER.MARKET>-<Company-Name>
    CN/HK/TW tickers → Chinese name; all other markets → English name.

Usage:
    python workspace-validate-names.py          # list violations
    python workspace-validate-names.py --fix    # auto-rename (prompt first)
    python workspace-validate-names.py --json   # machine-readable
"""

import argparse, json, os, re, sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CJK_RE = re.compile(r'[一-鿿]')
# Markets where the directory name must be Chinese (CLAUDE.md §3.3)
CJK_REQUIRED_MARKETS = {"SH", "SZ", "BJ", "CN", "HK", "TT", "TW"}
COMPANY_DIR_RE = re.compile(r'^([^.]+)\.([A-Z]{2})-')


def find_workspace_root():
    p = Path.cwd()
    for _ in range(10):
        if (p / ".claude" / "hooks" / "hook_entry.py").exists():
            return p
        if p.parent == p: break
        p = p.parent
    return None


def scan_violations(workspace):
    """Find files that don't follow naming conventions."""
    violations = []

    # Rule: company artifact = YYYYMMDD-[skill]-[Company-Name][-variant].ext
    # Variant suffix: _briefing_zh, _qa_en, EN, v2, etc.

    skills = [
        'stock-quickread', 'driver-map', 'driver-model', 'consensus-map',
        'catalyst-map', 'scenario-model', 'mechanism-insight', 'mechanism-map',
        'moat-analysis', 'alpha-thesis', 'company-history', 'boss-brief',
        'market-sizing', 'earnings-call', 'management-commentary',
        'quarterly-tracker', 'research-note', 'meeting-minutes',
        'peer-deep-dive', 'industry-landscape', 'candidate-screener',
        'teach-in', 'capital-allocation', 'model-update', 'post-earnings-quick',
        'information-impact', 'pair-trade', 'bear-pre-mortem'
    ]

    ind_dir = workspace / "industry"
    if not ind_dir.is_dir():
        return violations

    for f in sorted(ind_dir.glob("**/*.md")):
        if ".cache" in str(f) or f.name == "RESEARCH.md":
            continue

        name = f.stem
        rel = str(f.relative_to(workspace))

        # Check 1: date format should be YYYYMMDD not YYYY-MM-DD
        if re.match(r'\d{4}-\d{2}-\d{2}-', name) and not re.match(r'\d{8}-', name):
            violations.append(("OLD_DATE", rel, name,
                               "Date format YYYY-MM-DD should be YYYYMMDD"))
            continue

        # Check 2: company artifacts should have bracket format
        if '/companies/' in rel:
            if not re.match(r'\d{8}-\[.*\]-\[.*\]', name):
                # Still has skill name? Try to find it
                date_match = re.match(r'\d{8}-(.+)', name)
                if date_match:
                    rest = date_match.group(1)
                    has_skill = any(s in rest for s in skills)
                    if has_skill:
                        violations.append(("NO_BRACKETS", rel, name,
                                           "Should use bracket format: YYYYMMDD-[skill]-[Company]"))
            else:
                # Check skill name is recognized
                m = re.match(r'\d{8}-\[([^\]]+)\]', name)
                if m:
                    skill = m.group(1)
                    if skill not in skills:
                        violations.append(("UNKNOWN_SKILL", rel, name,
                                           f"Skill '{skill}' not in recognized list"))

        # Check 3: panorama artifacts
        if '/panorama/' in rel:
            if not re.match(r'\d{8}-', name):
                violations.append(("PANORAMA_DATE", rel, name,
                                   "Panorama artifact should start with YYYYMMDD"))

    # Rule: company directory = <TICKER.MARKET>-<Company-Name> (CLAUDE.md §3.2/§3.3)
    # CN/HK/TW (SH/SZ/BJ/CN/HK/TT/TW) must use a Chinese name; other markets English.
    for root in sorted(ind_dir.glob("*/companies")):
        if not root.is_dir():
            continue
        for d in sorted(p for p in root.iterdir() if p.is_dir()):
            if d.name.startswith("."):
                continue
            rel = str(d.relative_to(workspace))
            m = COMPANY_DIR_RE.match(d.name)
            if not m:
                continue  # nonstandard (private-*, legacy single-letter market) — not covered
            market = m.group(2).upper()
            name_part = d.name[m.end():]
            if market in CJK_REQUIRED_MARKETS and not CJK_RE.search(name_part):
                violations.append(("DIR_CN_NAME_MISSING", rel, d.name,
                                   f"Market {market} requires Chinese company name (CLAUDE.md §3.3)"))
            elif market not in CJK_REQUIRED_MARKETS and CJK_RE.search(name_part):
                violations.append(("DIR_CN_NAME_UNEXPECTED", rel, d.name,
                                   f"Market {market} should use English company name (CLAUDE.md §3.3)"))

    return violations


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fix", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    ws = find_workspace_root()
    if not ws:
        print("Not in a workspace.")
        return

    violations = scan_violations(ws)

    if args.json:
        print(json.dumps([{"type": t, "file": f, "name": n, "detail": d}
                          for t, f, n, d in violations],
                         ensure_ascii=False, indent=2))
        return

    if not violations:
        print("All artifacts follow naming conventions.")
        return

    print(f"Violations: {len(violations)}\n")
    by_type = {}
    for t, f, n, d in violations:
        by_type.setdefault(t, []).append((f, d))
    for typ, items in sorted(by_type.items()):
        print(f"=== {typ} ({len(items)}) ===")
        for f, d in items[:10]:
            print(f"  {f}")
            print(f"    {d}")
        if len(items) > 10:
            print(f"  ... and {len(items)-10} more")
        print()

    if args.fix:
        print("Auto-fix not implemented — rename manually or use question-sharpener.")


if __name__ == "__main__":
    main()
