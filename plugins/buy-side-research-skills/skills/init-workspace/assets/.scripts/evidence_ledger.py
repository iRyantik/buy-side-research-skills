
import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
#!/usr/bin/env python3
"""Evidence Ledger — claim-to-source traceability for buy-side research.

Usage:
  Ticker-scoped (primary — permanent ledger per ticker, cross-artifact reuse):
    python evidence_ledger.py init <TICKER>
    python evidence_ledger.py add  <TICKER> <json_payload>
    python evidence_ledger.py status <TICKER>
    python evidence_ledger.py lint  <artifact.md> -t <TICKER>
    python evidence_ledger.py scan  <artifact.md> -t <TICKER>
    python evidence_ledger.py batch <TICKER> <json_payload>

  Artifact-scoped (legacy):
    python evidence_ledger.py init  <artifact.md>      # deprecated — use ticker
    python evidence_ledger.py add   <artifact.md> ...   # deprecated

The ticker ledger is stored as:
  _cache/evidence/<TICKER>.evidence.json
"""

import json
import os
import re
import sys
import argparse
from datetime import datetime, timezone
from pathlib import Path

EVIDENCE_SUBDIR = "evidence"
LEDGER_DIRNAME = "_cache"

CLAIM_TYPES = {"factual", "statistical", "citation", "entity", "causal", "temporal"}
STATUSES = {"verified", "plausible", "unverified", "disputed", "fabrication_risk"}
ANCHOR_RE = re.compile(r'\[(?:S|I)\d+\]\(([^)]+)\)')
LEDGER_SCHEMA_VERSION = 3

# Method → tier mapping (lower tier = higher trust)
METHOD_TIERS = {
    "actuals": 0,
    "WebFetch": 1,
    "Playwright": 2,
    "curl": 3,
    "WebSearch": 4,   # AI summary, lowest trust
    "unknown": 4,
}


# --- Path resolution ---
def _ticker_to_ledger_path(artifact_path: str, ticker: str) -> Path:
    """Resolve <artifact_dir>/_cache/evidence/<TICKER>.evidence.json"""
    ap = Path(artifact_path).resolve()
    if ap.is_file():
        ap = ap.parent
    elif ap.is_dir():
        pass  # path is already a directory — use as-is
    else:
        # Path doesn't exist yet — assume it's a directory if no extension, or use parent if has extension
        if ap.suffix:
            ap = ap.parent
    ledger_dir = ap / LEDGER_DIRNAME / EVIDENCE_SUBDIR
    ledger_dir.mkdir(parents=True, exist_ok=True)
    ledger_path = ledger_dir / (ticker + ".evidence.json")
    _validate_ledger_path(ledger_path)
    return ledger_path


def _validate_ledger_path(ledger_path: Path):
    """Guard: ledger_path must be a .json file, never a directory."""
    if ledger_path.suffix != ".json":
        print(f"ERROR: ledger path must end with .json, got: {ledger_path}", file=sys.stderr)
        sys.exit(1)
    if ledger_path.is_dir():
        print(f"ERROR: ledger path is a directory, not a file: {ledger_path}", file=sys.stderr)
        print(f"Remove it: rm -rf {ledger_path}", file=sys.stderr)
        sys.exit(1)


def _artifact_path_to_ledger_path(artifact_path: str) -> Path:
    """Legacy: <dir>/_cache/evidence/<artifact-filename>.evidence.json"""
    ap = Path(artifact_path).resolve()
    if ap.is_dir():
        print(f"ERROR: '{artifact_path}' is a directory, not a file path.", file=sys.stderr)
        print("Use ticker mode: evidence_ledger.py init <DIR> -t <TICKER>", file=sys.stderr)
        sys.exit(1)
    if not ap.suffix:
        print(f"ERROR: '{artifact_path}' has no file extension — looks like a ticker, not a file.", file=sys.stderr)
        print("Use ticker mode: evidence_ledger.py init <TICKER> -t <TICKER>", file=sys.stderr)
        sys.exit(1)
    ledger_dir = ap.parent / LEDGER_DIRNAME / EVIDENCE_SUBDIR
    ledger_dir.mkdir(parents=True, exist_ok=True)
    ledger_path = ledger_dir / (ap.name + ".evidence.json")
    _validate_ledger_path(ledger_path)
    return ledger_path


# --- Load / Save ---
def _load_ledger(ledger_path: Path) -> dict:
    if ledger_path.exists():
        with open(ledger_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "schema_version": LEDGER_SCHEMA_VERSION,
        "ticker": "",
        "artifacts": [],
        "created": "",
        "updated": "",
        "status": "draft",
        "stats": {"total_claims": 0},
        "claims": [],
    }


def _save_ledger(ledger_path: Path, ledger: dict):
    _validate_ledger_path(ledger_path)
    if ledger_path.is_dir():
        print(f"ERROR: cannot save — ledger path is an existing directory: {ledger_path}", file=sys.stderr)
        print(f"Remove it with: rm -rf {ledger_path}", file=sys.stderr)
        sys.exit(1)
    ledger["updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    counts = {s: 0 for s in STATUSES}
    for c in ledger.get("claims", []):
        s = c.get("status", "unverified")
        if s in counts:
            counts[s] += 1
    ledger["stats"] = {"total_claims": len(ledger["claims"]), **counts}
    if counts["fabrication_risk"] > 0:
        ledger["status"] = "needs_review"
    elif counts["unverified"] > counts.get("verified", 0) * 0.5:
        ledger["status"] = "low_confidence"
    elif len(ledger["claims"]) == 0:
        ledger["status"] = "draft"
    else:
        ledger["status"] = "complete"
    with open(ledger_path, "w", encoding="utf-8") as f:
        json.dump(ledger, f, indent=2, ensure_ascii=False)


# --- Commands ---
def cmd_init(path: str, ticker: str = ""):
    if ticker:
        ledger_path = _ticker_to_ledger_path(path, ticker)
    else:
        ledger_path = _artifact_path_to_ledger_path(path)
    if ledger_path.exists():
        print(f"Already exists: {ledger_path}")
        sys.exit(1)
    ledger = _load_ledger(ledger_path)
    if ticker:
        ledger["ticker"] = ticker
    ledger["created"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    _save_ledger(ledger_path, ledger)
    print(f"Created: {ledger_path}")


def cmd_add(path: str, payload: str, ticker: str = ""):
    if ticker:
        ledger_path = _ticker_to_ledger_path(path, ticker)
    else:
        ledger_path = _artifact_path_to_ledger_path(path)
    ledger = _load_ledger(ledger_path)
    try:
        entry = json.loads(payload)
    except json.JSONDecodeError as e:
        print(f"ERROR: invalid JSON: {e}", file=sys.stderr)
        sys.exit(1)
    required = ["id", "text", "source", "url", "status"]
    missing = [k for k in required if k not in entry]
    if missing:
        print(f"ERROR: missing fields: {missing}", file=sys.stderr)
        sys.exit(1)
    if entry["status"] not in STATUSES:
        print(f"ERROR: invalid status '{entry['status']}'", file=sys.stderr)
        sys.exit(1)
    entry.setdefault("type", "factual")
    entry.setdefault("method", "unknown")
    entry.setdefault("quote", "")
    entry.setdefault("section", "")
    entry.setdefault("checked_at", datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
    entry.setdefault("provenances", [])

    existing = [c for c in ledger["claims"] if c["id"] == entry["id"]]
    if existing:
        idx = ledger["claims"].index(existing[0])
        ledger["claims"][idx] = entry
        print(f"Updated claim {entry['id']}")
    else:
        ledger["claims"].append(entry)
        ledger["claims"].sort(key=lambda c: c.get("id", ""))
        print(f"Added claim {entry['id']}")
    _save_ledger(ledger_path, ledger)


def cmd_status(path: str, ticker: str = ""):
    if ticker:
        ledger_path = _ticker_to_ledger_path(path, ticker)
    else:
        ledger_path = _artifact_path_to_ledger_path(path)
    if not ledger_path.exists():
        print("No ledger found.")
        sys.exit(1)
    ledger = _load_ledger(ledger_path)
    s = ledger["stats"]
    print(f"Ticker:   {ledger.get('ticker', '?')}")
    print(f"Status:   {ledger.get('status', '?')}")
    print(f"Claims:   {s['total_claims']}")
    for st in STATUSES:
        if st in s:
            print(f"  {st}:{' ' * (20 - len(st))}{s[st]}")
    total = s["total_claims"]
    if total > 0:
        cov = (s.get("verified", 0) + s.get("plausible", 0)) / total * 100
        print(f"  Coverage: {cov:.0f}%")


def cmd_lint(artifact_path: str, ticker: str = ""):
    if not os.path.exists(artifact_path):
        print(f"ERROR: artifact not found: {artifact_path}", file=sys.stderr)
        sys.exit(1)
    with open(artifact_path, "r", encoding="utf-8") as f:
        content = f.read()
    body = content.split("## Resources")[0] if "## Resources" in content else content
    body = re.sub(r'```[^\n]*\n.*?```', '', body, flags=re.DOTALL)
    body = re.sub(r'~~~[^\n]*\n.*?~~~', '', body, flags=re.DOTALL)
    anchors = re.findall(r'\[((?:S|I)\d+)\]', body)
    artifact_codes = {f"{code}" for code in anchors}

    if not artifact_codes:
        print("WARNING: No [S#] or [I#] anchors found in artifact body.")
        return

    if ticker:
        ledger_path = _ticker_to_ledger_path(artifact_path, ticker)
    else:
        ledger_path = _artifact_path_to_ledger_path(artifact_path)
    if not ledger_path.exists():
        print(f"ERROR: No ledger found at {ledger_path}")
        sys.exit(1)

    ledger = _load_ledger(ledger_path)
    ledger_codes = {c.get("source", "") for c in ledger["claims"]}
    missing = artifact_codes - ledger_codes
    extra = ledger_codes - artifact_codes

    issues = []
    if missing:
        issues.append(f"  {len(missing)} anchor(s) in artifact NOT in ledger: {sorted(missing)[:10]}")
    if extra:
        issues.append(f"  {len(extra)} source(s) in ledger NOT in artifact: {sorted(extra)[:10]}")
    fab_risks = [c for c in ledger["claims"] if c.get("status") == "fabrication_risk"]
    if fab_risks:
        issues.append(f"  {len(fab_risks)} FABRICATION_RISK: {[c['id'] for c in fab_risks]}")

    if issues:
        print(f"ERROR: Lint failed for {ledger.get('ticker', '?')}:")
        for issue in issues:
            print(issue)
        sys.exit(1)
    else:
        print(f"OK: {len(artifact_codes)} anchor(s) tracked. No fabrication risks.")


def cmd_scan(artifact_path: str, ticker: str):
    """Scan artifact for [S#]/[I#], cross-ref with ticker ledger, output new claims."""
    if not os.path.exists(artifact_path):
        print(f"ERROR: artifact not found: {artifact_path}", file=sys.stderr)
        sys.exit(1)
    with open(artifact_path, "r", encoding="utf-8") as f:
        content = f.read()
    body = content.split("## Resources")[0] if "## Resources" in content else content
    body = re.sub(r'```[^\n]*\n.*?```', '', body, flags=re.DOTALL)
    body = re.sub(r'~~~[^\n]*\n.*?~~~', '', body, flags=re.DOTALL)

    # Extract all [S#](url) and [I#](url) anchors
    anchors = re.findall(r'\[(S\d+|I\d+)\]\(([^)]+)\)', body)
    anchor_map = {}
    for code, url in anchors:
        if code not in anchor_map:
            anchor_map[code] = url

    ledger_path = _ticker_to_ledger_path(artifact_path, ticker)
    ledger = _load_ledger(ledger_path) if ledger_path.exists() else None
    known_sources = {c["source"] for c in ledger["claims"]} if ledger else set()

    new_anchors = {k: v for k, v in anchor_map.items() if k not in known_sources}
    known = {k: v for k, v in anchor_map.items() if k in known_sources}

    print(f"Artifact: {os.path.basename(artifact_path)}")
    print(f"Ticker:   {ticker}")
    print(f"Anchors:  {len(anchor_map)} total ({len(known)} known, {len(new_anchors)} new)")
    if known:
        print("  Known (skip):")
        for code in sorted(known):
            print(f"    [{code}]({known[code][:60]}...)")
    if new_anchors:
        print("  New (needs verification):")
        for code in sorted(new_anchors):
            print(f"    [{code}]({new_anchors[code][:80]}...)")


def cmd_batch(ticker_path: str, ticker: str, payload: str):
    """Batch upgrade claims in ticker ledger."""
    ledger_path = _ticker_to_ledger_path(ticker_path, ticker)
    if not ledger_path.exists():
        print(f"ERROR: ledger not found: {ledger_path}", file=sys.stderr)
        sys.exit(1)
    ledger = _load_ledger(ledger_path)
    try:
        batch = json.loads(payload)
    except json.JSONDecodeError as e:
        print(f"ERROR: invalid JSON: {e}", file=sys.stderr)
        sys.exit(1)

    claims = batch.get("claims", [])
    provenance = batch.get("provenance", "")
    updated = 0
    for entry in claims:
        eid = entry.get("id", "")
        existing = [c for c in ledger["claims"] if c["id"] == eid]
        if existing:
            idx = ledger["claims"].index(existing[0])
            for k, v in entry.items():
                ledger["claims"][idx][k] = v
            if provenance and provenance not in ledger["claims"][idx].get("provenances", []):
                ledger["claims"][idx].setdefault("provenances", []).append(provenance)
            updated += 1
        else:
            entry.setdefault("provenances", [])
            if provenance and provenance not in entry["provenances"]:
                entry["provenances"].append(provenance)
            ledger["claims"].append(entry)
            updated += 1
    _save_ledger(ledger_path, ledger)
    print(f"Batch: {updated} claim(s) updated in {ticker}")


def cmd_auto(artifact_path: str, ticker: str):
    """Scan artifact, auto-create pending entries for new anchors."""
    if not os.path.exists(artifact_path):
        print(f"ERROR: artifact not found: {artifact_path}", file=sys.stderr)
        sys.exit(1)
    with open(artifact_path, "r", encoding="utf-8") as f:
        content = f.read()
    body = content.split("## Resources")[0] if "## Resources" in content else content
    body = re.sub(r'```[^\n]*\n.*?```', '', body, flags=re.DOTALL)
    body = re.sub(r'~~~[^\n]*\n.*?~~~', '', body, flags=re.DOTALL)

    anchors = re.findall(r'\[(S\d+|I\d+)\]\(([^)]+)\)', body)
    anchor_map = {}
    for code, url in anchors:
        if code not in anchor_map:
            anchor_map[code] = url

    ledger_path = _ticker_to_ledger_path(artifact_path, ticker)
    ledger = _load_ledger(ledger_path) if ledger_path.exists() else None
    if not ledger:
        print(f"ERROR: No ledger for {ticker}. Run init first.", file=sys.stderr)
        sys.exit(1)

    existing = {c["source"] for c in ledger["claims"]}
    new_count = 0
    for code, url in anchor_map.items():
        if code in existing:
            continue
        cid = f"C{len(ledger['claims']) + new_count + 1}"
        entry = {
            "id": cid, "source": code, "url": url, "text": "",
            "section": "", "type": "factual", "status": "unverified",
            "method": None, "tier": None, "quote": "",
            "checked_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "provenances": [os.path.basename(artifact_path)],
            "attempts": []
        }
        ledger["claims"].append(entry)
        new_count += 1

    if new_count:
        ledger["claims"].sort(key=lambda c: c.get("id", ""))
        _save_ledger(ledger_path, ledger)
        print(f"Auto-created {new_count} pending claims:")
        for c in ledger["claims"][-new_count:]:
            print(f"  {c['id']}: [{c['source']}]({c['url'][:60]}...) — unverified")
    else:
        print(f"All {len(anchor_map)} anchors already tracked. Nothing to add.")


def cmd_attempt(artifact_path: str, ticker: str, payload: str):
    """Log a verification attempt on a claim without changing its status.
    payload: {"claim_id": "C4", "tier": 1, "method": "WebFetch", "result": "403"}
    """
    ledger_path = _ticker_to_ledger_path(artifact_path, ticker)
    if not ledger_path.exists():
        print(f"ERROR: No ledger found", file=sys.stderr)
        sys.exit(1)
    ledger = _load_ledger(ledger_path)
    try:
        att = json.loads(payload)
    except json.JSONDecodeError as e:
        print(f"ERROR: invalid JSON: {e}", file=sys.stderr)
        sys.exit(1)

    cid = att.get("claim_id", "")
    claim = next((c for c in ledger["claims"] if c["id"] == cid), None)
    if not claim:
        print(f"ERROR: claim {cid} not found", file=sys.stderr)
        sys.exit(1)

    claim.setdefault("attempts", []).append({
        "tier": att.get("tier"),
        "method": att.get("method"),
        "result": att.get("result", "unknown"),
        "at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    })
    _save_ledger(ledger_path, ledger)
    print(f"[{cid}] attempt logged: tier={att.get('tier')} method={att.get('method')} result={att.get('result')}")


def cmd_verify(artifact_path: str, ticker: str, payload: str):
    """Mark a claim as verified after successful tier verification.
    payload: {"claim_id": "C4", "tier": 2, "method": "Playwright", "text": "...", "quote": "...", "section": "§3"}
    """
    ledger_path = _ticker_to_ledger_path(artifact_path, ticker)
    if not ledger_path.exists():
        print(f"ERROR: No ledger found", file=sys.stderr)
        sys.exit(1)
    ledger = _load_ledger(ledger_path)
    try:
        v = json.loads(payload)
    except json.JSONDecodeError as e:
        print(f"ERROR: invalid JSON: {e}", file=sys.stderr)
        sys.exit(1)

    cid = v.get("claim_id", "")
    claim = next((c for c in ledger["claims"] if c["id"] == cid), None)
    if not claim:
        print(f"ERROR: claim {cid} not found", file=sys.stderr)
        sys.exit(1)

    claim["status"] = "verified"
    claim["method"] = v.get("method", claim.get("method"))
    claim["tier"] = v.get("tier", claim.get("tier"))
    if v.get("text"):
        claim["text"] = v["text"]
    if v.get("quote"):
        claim["quote"] = v["quote"]
    if v.get("section"):
        claim["section"] = v["section"]
    claim["checked_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    _save_ledger(ledger_path, ledger)
    print(f"[{cid}] verified — tier={claim['tier']} method={claim['method']}")


def main():
    parser = argparse.ArgumentParser(description="Evidence Ledger for research artifacts")
    sub = parser.add_subparsers(dest="command")

    p_init = sub.add_parser("init", help="Create ticker ledger")
    p_init.add_argument("path", help="Ticker (e.g. BESI.NA) or artifact path")
    p_init.add_argument("-t", "--ticker", help="Ticker override")

    p_add = sub.add_parser("add", help="Add claim to ledger")
    p_add.add_argument("path", help="Ticker or artifact path")
    p_add.add_argument("payload", help="JSON payload")
    p_add.add_argument("-t", "--ticker", help="Ticker override")

    p_status = sub.add_parser("status", help="Coverage statistics")
    p_status.add_argument("path", help="Ticker or artifact path")
    p_status.add_argument("-t", "--ticker", help="Ticker override")

    p_lint = sub.add_parser("lint", help="Verify [S#] in artifact tracked")
    p_lint.add_argument("artifact", help="Artifact .md path")
    p_lint.add_argument("-t", "--ticker", help="Ticker for ledger")

    p_scan = sub.add_parser("scan", help="Scan artifact for new anchors vs ticker ledger")
    p_scan.add_argument("artifact", help="Artifact .md path")
    p_scan.add_argument("-t", "--ticker", required=True, help="Ticker")

    p_batch = sub.add_parser("batch", help="Batch upgrade claims")
    p_batch.add_argument("path", help="Artifact path (for dir resolution)")
    p_batch.add_argument("-t", "--ticker", required=True, help="Ticker")
    p_batch.add_argument("payload", help="JSON payload: {claims:[{id,status,method,...}], provenance:''}")

    p_auto = sub.add_parser("auto", help="Auto-create pending claims from artifact anchors")
    p_auto.add_argument("artifact", help="Artifact .md path")
    p_auto.add_argument("-t", "--ticker", required=True, help="Ticker")

    p_attempt = sub.add_parser("attempt", help="Log verification attempt")
    p_attempt.add_argument("path", help="Artifact path (for dir)")
    p_attempt.add_argument("-t", "--ticker", required=True, help="Ticker")
    p_attempt.add_argument("payload", help='JSON: {"claim_id":"C4","tier":1,"method":"WebFetch","result":"403"}')

    p_verify = sub.add_parser("verify", help="Mark claim as verified")
    p_verify.add_argument("path", help="Artifact path (for dir)")
    p_verify.add_argument("-t", "--ticker", required=True, help="Ticker")
    p_verify.add_argument("payload", help='JSON: {"claim_id":"C4","tier":2,"method":"Playwright","text":"...","quote":"..."}')

    args = parser.parse_args()
    ticker = getattr(args, "ticker", None) or ""

    if args.command == "init":
        cmd_init(args.path, ticker)
    elif args.command == "add":
        cmd_add(args.path, args.payload, ticker)
    elif args.command == "status":
        cmd_status(args.path, ticker)
    elif args.command == "lint":
        cmd_lint(args.artifact, ticker)
    elif args.command == "scan":
        cmd_scan(args.artifact, ticker)
    elif args.command == "batch":
        cmd_batch(args.path, ticker, args.payload)
    elif args.command == "auto":
        cmd_auto(args.artifact, ticker)
    elif args.command == "attempt":
        cmd_attempt(args.path, ticker, args.payload)
    elif args.command == "verify":
        cmd_verify(args.path, ticker, args.payload)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
