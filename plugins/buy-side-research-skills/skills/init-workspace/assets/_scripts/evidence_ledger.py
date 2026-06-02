#!/usr/bin/env python3
"""Evidence Ledger — claim-to-source traceability for buy-side research artifacts.

Usage:
  python evidence_ledger.py init <artifact.md>
  python evidence_ledger.py add <artifact.md> <json_payload>
  python evidence_ledger.py status <artifact.md>
  python evidence_ledger.py lint <artifact.md>
  python evidence_ledger.py export <artifact.md>

The ledger is stored alongside the artifact as:
  _cache/evidence/<artifact-filename>.evidence.json
"""

import json
import os
import re
import sys
import argparse
from datetime import datetime, timezone
from pathlib import Path

LEDGER_DIRNAME = "_cache"
EVIDENCE_SUBDIR = "evidence"

# --- Claim types (from Doublecheck methodology) ---
CLAIM_TYPES = {"factual", "statistical", "citation", "entity", "causal", "temporal"}

# --- Confidence statuses ---
STATUSES = {"verified", "plausible", "unverified", "disputed", "fabrication_risk"}

# --- Source anchor regex (same as common.py) ---
ANCHOR_RE = re.compile(r'\[(?P<code>[SPILBGR]+\d+)\]\((?P<target>[^)]+)\)')

LEDGER_SCHEMA_VERSION = 1


def _artifact_path_to_ledger_path(artifact_path: str) -> Path:
    """Resolve <artifact>.md → <dir>/_cache/evidence/<name>.evidence.json"""
    ap = Path(artifact_path).resolve()
    ledger_dir = ap.parent / LEDGER_DIRNAME / EVIDENCE_SUBDIR
    ledger_dir.mkdir(parents=True, exist_ok=True)
    return ledger_dir / (ap.name + ".evidence.json")


def _load_ledger(ledger_path: Path) -> dict:
    if ledger_path.exists():
        with open(ledger_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "schema_version": LEDGER_SCHEMA_VERSION,
        "artifact": "",
        "created": "",
        "updated": "",
        "status": "draft",
        "stats": {
            "total_claims": 0,
            "verified": 0,
            "plausible": 0,
            "unverified": 0,
            "disputed": 0,
            "fabrication_risk": 0,
        },
        "claims": [],
    }


def _save_ledger(ledger_path: Path, ledger: dict):
    ledger["updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    # Recompute stats
    counts = {s: 0 for s in STATUSES}
    for c in ledger["claims"]:
        s = c.get("status", "unverified")
        if s in counts:
            counts[s] += 1
    ledger["stats"] = {"total_claims": len(ledger["claims"]), **counts}
    if counts["fabrication_risk"] > 0:
        ledger["status"] = "needs_review"
    elif counts["unverified"] > ledger["stats"]["verified"] * 0.5:
        ledger["status"] = "low_confidence"
    elif len(ledger["claims"]) == 0:
        ledger["status"] = "draft"
    else:
        ledger["status"] = "complete"

    with open(ledger_path, "w", encoding="utf-8") as f:
        json.dump(ledger, f, indent=2, ensure_ascii=False)


def cmd_init(artifact_path: str):
    ledger_path = _artifact_path_to_ledger_path(artifact_path)
    if ledger_path.exists():
        print(f"Ledger already exists: {ledger_path}")
        sys.exit(1)
    ledger = _load_ledger(ledger_path)
    ledger["artifact"] = os.path.basename(artifact_path)
    ledger["created"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    _save_ledger(ledger_path, ledger)
    print(f"Created: {ledger_path}")


def cmd_add(artifact_path: str, payload: str):
    ledger_path = _artifact_path_to_ledger_path(artifact_path)
    ledger = _load_ledger(ledger_path)
    try:
        entry = json.loads(payload)
    except json.JSONDecodeError as e:
        print(f"ERROR: invalid JSON payload: {e}", file=sys.stderr)
        sys.exit(1)

    required = ["id", "text", "source", "url", "status"]
    missing = [k for k in required if k not in entry]
    if missing:
        print(f"ERROR: missing required fields: {missing}", file=sys.stderr)
        sys.exit(1)

    if entry["status"] not in STATUSES:
        print(f"ERROR: invalid status '{entry['status']}'. Allowed: {STATUSES}", file=sys.stderr)
        sys.exit(1)

    if "type" in entry and entry["type"] not in CLAIM_TYPES:
        print(f"ERROR: invalid claim type '{entry['type']}'", file=sys.stderr)
        sys.exit(1)

    # Fill defaults
    entry.setdefault("type", "factual")
    entry.setdefault("method", "unknown")
    entry.setdefault("quote", "")
    entry.setdefault("section", "")
    entry.setdefault("checked_at",
        datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))

    # If ID already exists, update; otherwise append
    existing = [c for c in ledger["claims"] if c["id"] == entry["id"]]
    if existing:
        idx = ledger["claims"].index(existing[0])
        ledger["claims"][idx] = entry
        print(f"Updated claim {entry['id']}")
    else:
        ledger["claims"].append(entry)
        # Keep sorted by ID
        ledger["claims"].sort(key=lambda c: c.get("id", ""))
        print(f"Added claim {entry['id']}")

    _save_ledger(ledger_path, ledger)


def cmd_status(artifact_path: str):
    ledger_path = _artifact_path_to_ledger_path(artifact_path)
    if not ledger_path.exists():
        print("No ledger found. Run 'init' first.")
        sys.exit(1)
    ledger = _load_ledger(ledger_path)
    s = ledger["stats"]
    print(f"Artifact: {ledger.get('artifact', '?')}")
    print(f"Status:   {ledger.get('status', '?')}")
    print(f"Claims:   {s['total_claims']}")
    print(f"  verified:         {s['verified']}")
    print(f"  plausible:        {s['plausible']}")
    print(f"  unverified:       {s['unverified']}")
    print(f"  disputed:         {s['disputed']}")
    print(f"  fabrication_risk: {s['fabrication_risk']}")
    if s["total_claims"] > 0:
        coverage = (s["verified"] + s["plausible"]) / s["total_claims"] * 100
        print(f"  Coverage: {coverage:.0f}% (verified+plausible/total)")


def cmd_lint(artifact_path: str):
    ledger_path = _artifact_path_to_ledger_path(artifact_path)
    if not os.path.exists(artifact_path):
        print(f"ERROR: artifact not found: {artifact_path}", file=sys.stderr)
        sys.exit(1)

    with open(artifact_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Find all [S#] and [I#] anchors in artifact body
    body = content.split("## Resources")[0] if "## Resources" in content else content
    anchors = ANCHOR_RE.findall(body)
    artifact_codes = {f"{code}" for code, _ in anchors}

    if not artifact_codes:
        print("WARNING: No [S#] or [I#] anchors found in artifact body.")
        return

    if not ledger_path.exists():
        print(f"ERROR: No ledger found. Every [S#]/[I#] in artifact must have a ledger entry.")
        print(f"  Missing ledger for {len(artifact_codes)} anchor(s): {sorted(artifact_codes)[:10]}")
        sys.exit(1)

    ledger = _load_ledger(ledger_path)
    ledger_codes = {c.get("source", "") for c in ledger["claims"]}

    missing = artifact_codes - ledger_codes
    extra = ledger_codes - artifact_codes

    issues = []
    if missing:
        issues.append(f"  {len(missing)} anchor(s) in artifact but NOT in ledger: {sorted(missing)[:10]}")
    if extra:
        issues.append(f"  {len(extra)} source(s) in ledger but NOT in artifact: {sorted(extra)[:10]}")

    # Check for fabrication_risk entries
    fab_risks = [c for c in ledger["claims"] if c.get("status") == "fabrication_risk"]
    if fab_risks:
        issues.append(f"  {len(fab_risks)} FABRICATION_RISK claim(s): {[c['id'] for c in fab_risks]}")

    if issues:
        print(f"ERROR: Lint failed for {ledger.get('artifact', '?')}:")
        for issue in issues:
            print(issue)
        sys.exit(1)
    else:
        print(f"OK: {len(artifact_codes)} anchor(s) all tracked in ledger. No fabrication risks.")


def cmd_export(artifact_path: str):
    """Export ledger as compact summary for display."""
    ledger_path = _artifact_path_to_ledger_path(artifact_path)
    if not ledger_path.exists():
        print("No ledger found.")
        sys.exit(1)
    ledger = _load_ledger(ledger_path)
    print(json.dumps({
        "artifact": ledger["artifact"],
        "status": ledger["status"],
        "stats": ledger["stats"],
        "claims_summary": [
            {
                "id": c["id"],
                "source": c["source"],
                "status": c["status"],
                "text": c["text"][:80]
            }
            for c in ledger["claims"]
        ]
    }, indent=2, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description="Evidence Ledger for research artifacts")
    sub = parser.add_subparsers(dest="command")

    p_init = sub.add_parser("init", help="Create new evidence ledger")
    p_init.add_argument("artifact", help="Path to artifact .md file")

    p_add = sub.add_parser("add", help="Add or update a claim")
    p_add.add_argument("artifact", help="Path to artifact .md file")
    p_add.add_argument("payload", help="JSON payload: {id,text,source,url,status,type?,method?,quote?,section?}")

    p_status = sub.add_parser("status", help="Show coverage statistics")
    p_status.add_argument("artifact", help="Path to artifact .md file")

    p_lint = sub.add_parser("lint", help="Check all [S#] in artifact have ledger entries")
    p_lint.add_argument("artifact", help="Path to artifact .md file")

    p_export = sub.add_parser("export", help="Export ledger summary as JSON")
    p_export.add_argument("artifact", help="Path to artifact .md file")

    args = parser.parse_args()
    if args.command == "init":
        cmd_init(args.artifact)
    elif args.command == "add":
        cmd_add(args.artifact, args.payload)
    elif args.command == "status":
        cmd_status(args.artifact)
    elif args.command == "lint":
        cmd_lint(args.artifact)
    elif args.command == "export":
        cmd_export(args.artifact)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
