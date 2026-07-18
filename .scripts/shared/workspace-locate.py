#!/usr/bin/env python3
"""Scan workspace for companies/industries matching a keyword.

Usage:
    python workspace-locate.py <keyword>                  # search both
    python workspace-locate.py <keyword> --company        # companies only
    python workspace-locate.py <keyword> --industry       # industries only
    python workspace-locate.py <keyword> --json           # machine-readable

Returns: matched paths, existing artifacts, research context.
"""

import argparse, json, os, sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def find_workspace_root():
    """Walk up to find a CC research workspace (has .claude/hooks/)."""
    p = Path.cwd()
    for _ in range(10):
        if (p / ".claude" / "hooks" / "hook_entry.py").exists():
            return p
        if p.parent == p:
            break
        p = p.parent
    return None


def _load_coverage(workspace):
    """Parse COVERAGE.md into ticker->{en,native,industry} map."""
    cov_path = workspace / "COVERAGE.md"
    if not cov_path.is_file():
        return {}
    mapping = {}
    for line in cov_path.read_text(encoding="utf-8").split("\n"):
        line = line.strip()
        if not line.startswith("|") or "---" in line:
            continue
        parts = [p.strip() for p in line.split("|") if p.strip()]
        if len(parts) < 4 or parts[0] in ("Ticker", "Field"):
            continue
        ticker = parts[0]
        en = parts[1] if len(parts) > 1 else ""
        native = parts[2] if len(parts) > 2 else ""
        industry = parts[3] if len(parts) > 3 else ""
        mapping[ticker] = {"en": en, "native": native, "industry": industry}
    return mapping


def scan_companies(workspace, keyword):
    """Find company dirs matching keyword in dir name, COVERAGE EN/Native name, or ticker."""
    keyword_lower = keyword.lower()
    coverage = _load_coverage(workspace)
    matches = []
    companies_dir = workspace / "industry"
    if not companies_dir.is_dir():
        return matches

    for comp_dir in sorted(companies_dir.glob("*/companies/*")):
        if not comp_dir.is_dir():
            continue
        name_lower = comp_dir.name.lower()

        # Match directory name
        if keyword_lower in name_lower:
            matches.append(_build_company_entry(comp_dir, workspace))
            continue

        # Match COVERAGE entries
        ticker = comp_dir.name.split("-")[0] if "-" in comp_dir.name else comp_dir.name
        # Try with dot notation too (e.g. "688531.CH")
        for tk, info in coverage.items():
            tk_lower = tk.lower()
            if keyword_lower in tk_lower or keyword_lower in info["en"].lower() or keyword_lower in info["native"]:
                # Check if this ticker matches our dir's ticker
                dir_ticker_norm = comp_dir.name.split("-")[0].replace(".", " ").upper()
                cov_ticker_norm = tk.replace(".", " ").upper()
                if dir_ticker_norm == cov_ticker_norm or ticker.replace(".", "") in tk.replace(".", ""):
                    matches.append(_build_company_entry(comp_dir, workspace))
                    break

    return matches


def _build_company_entry(comp_dir, workspace):
    artifacts = []
    for f in sorted(comp_dir.glob("*.md")):
        if f.name != "RESEARCH.md" and ".cache" not in str(f):
            artifacts.append(f.name)
    return {
        "path": str(comp_dir.relative_to(workspace)),
        "name": comp_dir.name,
        "industry": comp_dir.parent.parent.name,
        "artifacts": artifacts,
    }


def scan_industries(workspace, keyword):
    """Find industry dirs matching keyword."""
    keyword_lower = keyword.lower()
    matches = []
    ind_dir = workspace / "industry"
    if not ind_dir.is_dir():
        return matches

    for ind in sorted(ind_dir.iterdir()):
        if not ind.is_dir():
            continue
        name = ind.name.lower().replace("-", " ")
        if keyword_lower in name:
            artifacts = []
            for f in sorted(ind.glob("*.md")):
                if ".cache" not in str(f):
                    artifacts.append(f.name)
            # Also scan panorama
            panorama = {}
            pan_dir = ind / "panorama"
            if pan_dir.is_dir():
                for skill_dir in sorted(pan_dir.iterdir()):
                    if skill_dir.is_dir():
                        mds = [f.name for f in skill_dir.glob("*.md")]
                        if mds:
                            panorama[skill_dir.name] = mds
            matches.append({
                "path": str(ind.relative_to(workspace)),
                "name": ind.name,
                "artifacts": artifacts,
                "panorama": panorama,
            })
    return matches


def scan_background(workspace, company_matches, industry_matches):
    """Collect background from existing research."""
    bg = []
    for c in company_matches:
        for a in c["artifacts"]:
            if "stock-quickread" in a or "teach-in" in a or "driver-map" in a:
                bg.append(f'{c["path"]}/{a}')
    for ind in industry_matches:
        for a in ind["artifacts"]:
            if "industry-landscape" in a or "teach-in" in a:
                bg.append(f'{ind["path"]}/{a}')
        for skill, files in ind.get("panorama", {}).items():
            for f in files:
                bg.append(f'{ind["path"]}/panorama/{skill}/{f}')
    return bg


def main():
    parser = argparse.ArgumentParser(description="Locate workspace company/industry by keyword")
    parser.add_argument("keyword", help="Search keyword (company name, ticker, industry)")
    parser.add_argument("--company", action="store_true", help="Company search only")
    parser.add_argument("--industry", action="store_true", help="Industry search only")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()

    ws = find_workspace_root()

    if not ws:
        if args.json:
            print(json.dumps({"workspace": None, "error": "not in a workspace"}))
        else:
            print("Not in a CC research workspace. Output will go to current directory.")
        return

    search_companies = not args.industry
    search_industries = not args.company

    companies = scan_companies(ws, args.keyword) if search_companies else []
    industries = scan_industries(ws, args.keyword) if search_industries else []
    background = scan_background(ws, companies, industries)

    if args.json:
        print(json.dumps({
            "workspace": str(ws),
            "companies": companies,
            "industries": industries,
            "background": background,
        }, ensure_ascii=False, indent=2))
        return

    print(f"Workspace: {ws}")
    print()

    if companies:
        print(f"=== Companies ({len(companies)}) ===")
        for c in companies:
            print(f"  {c['path']}")
            if c['artifacts']:
                for a in c['artifacts'][:5]:
                    print(f"    - {a}")
                if len(c['artifacts']) > 5:
                    print(f"    ... and {len(c['artifacts'])-5} more")
        print()

    if industries:
        print(f"=== Industries ({len(industries)}) ===")
        for ind in industries:
            print(f"  {ind['path']}")
            if ind.get('panorama'):
                for skill, files in ind['panorama'].items():
                    print(f"    panorama/{skill}/ ({len(files)} files)")
        print()

    if background:
        print(f"=== Background ({len(background)} artifacts) ===")
        for b in background[:10]:
            print(f"  {b}")
        if len(background) > 10:
            print(f"  ... and {len(background)-10} more")
        print()

    if not companies and not industries:
        print(f"No match for '{args.keyword}'")
        print("Output will go to current directory.")


if __name__ == "__main__":
    main()
