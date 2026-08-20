
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
    python evidence_ledger.py delete <TICKER> <claim_id>

  Artifact-scoped (legacy):
    python evidence_ledger.py init  <artifact.md>      # deprecated — use ticker
    python evidence_ledger.py add   <artifact.md> ...   # deprecated

The ticker ledger is stored as:
  .cache/evidence/<TICKER>.evidence.json
"""

import json
import os
import re
import sys
import argparse
from datetime import datetime, timezone
from pathlib import Path

EVIDENCE_SUBDIR = "evidence"
LEDGER_DIRNAME = ".cache"

CLAIM_TYPES = {"factual", "statistical", "citation", "entity", "causal", "temporal"}
STATUSES = {"verified", "plausible", "unverified", "disputed", "fabrication_risk"}
ANCHOR_RE = re.compile(r'\[(S\d+|I\d+)\]\(([^)]+)\)')
LEDGER_SCHEMA_VERSION = 3


def extract_anchors(content: str) -> dict:
    """Full-content anchor scan: code blocks and ## Resources included.

    Single source of truth, shared with the evidence_ledger_floor hook (Rule 0),
    so auto/lint/scan and the hook can never drift apart again. The old code
    stripped ``` / ~~~ blocks and the Resources section before scanning — that
    is how anchors living only in a tone-tracker code block (the S12 class)
    went missing.
    """
    anchor_map = {}
    for m in ANCHOR_RE.finditer(content):
        code, url = m.group(1), m.group(2)
        if code not in anchor_map:
            anchor_map[code] = url
    return anchor_map


def _anchor_contexts(content: str) -> dict:
    """Map anchor code → (first-pass text, nearest preceding heading).

    Gives auto-created claims raw material for quote-matching in
    verify-claim.py --claim-text.
    """
    contexts = {}
    current_heading = ""
    for line in content.splitlines():
        m = re.match(r'^\s{0,3}#{1,6}\s+(.*)$', line)
        if m:
            current_heading = m.group(1).strip()
        for code in re.findall(r'\[(S\d+|I\d+)\]', line):
            if code not in contexts:
                contexts[code] = (_anchor_sentence(line, code), current_heading)
    return contexts


def _anchor_sentence(line: str, code: str) -> str:
    """First-pass claim text: the line around the anchor, cleaned, ≤200 chars."""
    s = re.sub(r'\[(?:S\d+|I\d+)\]\([^)]+\)', code, line)
    s = re.sub(r'[#*_`>|\[\]]', '', s).strip()
    return s[:200]

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
    """Resolve <artifact_dir>/.cache/evidence/<TICKER>.evidence.json"""
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
    """Legacy: <dir>/.cache/evidence/<artifact-filename>.evidence.json"""
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
        old = ledger["claims"][idx]
        old_provs = list(old.get("provenances", []))  # capture before payload keys overwrite
        for k, v in entry.items():
            old[k] = v
        # merge semantics: attempts are history (keep unless payload replaces);
        # provenances are membership tags — always union with what's tracked
        # (whole-claim replace used to drop attempts + provenances)
        old.setdefault("attempts", [])
        merged_prov = old_provs + entry.get("provenances", [])
        old["provenances"] = []
        for p in merged_prov:
            if p not in old["provenances"]:
                old["provenances"].append(p)
        print(f"Updated claim {entry['id']}")
    else:
        entry.setdefault("attempts", [])
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
    artifact_codes = set(extract_anchors(content).keys())

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
    # Filter claims to this artifact only (ledger is shared per ticker)
    artifact_name = os.path.basename(artifact_path)
    artifact_claims = [c for c in ledger["claims"]
                       if artifact_name in (c.get("provenances") or [])]
    ledger_codes = {c.get("source", "") for c in artifact_claims}
    missing = artifact_codes - ledger_codes
    extra = ledger_codes - artifact_codes

    issues = []
    if missing:
        issues.append(f"  {len(missing)} anchor(s) in artifact NOT in ledger: {sorted(missing)[:10]}")
    if extra:
        issues.append(f"  {len(extra)} source(s) in ledger NOT in artifact: {sorted(extra)[:10]}")
    fab_risks = [c for c in artifact_claims if c.get("status") == "fabrication_risk"]
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
    anchor_map = extract_anchors(content)

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
            entry.setdefault("attempts", [])
            if provenance and provenance not in entry["provenances"]:
                entry["provenances"].append(provenance)
            ledger["claims"].append(entry)
            updated += 1
    _save_ledger(ledger_path, ledger)
    print(f"Batch: {updated} claim(s) updated in {ticker}")


def cmd_auto(artifact_path: str, ticker: str):
    """Scan artifact, auto-create pending entries for new anchors.

    Full-content scan (code blocks + Resources included — anchors in a tone
    tracker or Resources-only sources are evidence too). New claim IDs continue
    from the highest existing ID, never colliding and never reusing. Each new
    claim gets a first-pass text (anchor line) + section (nearest heading) so
    quote-matching in verify-claim.py --claim-text has raw material.
    """
    if not os.path.exists(artifact_path):
        print(f"ERROR: artifact not found: {artifact_path}", file=sys.stderr)
        sys.exit(1)
    with open(artifact_path, "r", encoding="utf-8") as f:
        content = f.read()
    anchor_map = extract_anchors(content)
    contexts = _anchor_contexts(content)

    ledger_path = _ticker_to_ledger_path(artifact_path, ticker)
    ledger = _load_ledger(ledger_path) if ledger_path.exists() else None
    if not ledger:
        print(f"ERROR: No ledger for {ticker}. Run init first.", file=sys.stderr)
        sys.exit(1)

    existing_sources = {c["source"] for c in ledger["claims"]}
    # next ID = max existing numeric ID + 1 — immune to prior ID collisions
    ids = [int(m.group(1)) for c in ledger["claims"]
           if (m := re.match(r'^C(\d+)$', c.get("id", "")))]
    next_id = max(ids) + 1 if ids else 1
    new_count = 0
    for code, url in anchor_map.items():
        if code in existing_sources:
            continue
        text, section = contexts.get(code, ("", ""))
        cid = f"C{next_id}"
        entry = {
            "id": cid, "source": code, "url": url, "text": text,
            "section": section, "type": "factual", "status": "unverified",
            "method": None, "tier": None, "quote": "",
            "checked_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "provenances": [os.path.basename(artifact_path)],
            "attempts": []
        }
        ledger["claims"].append(entry)
        new_count += 1
        next_id += 1

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

    tier = att.get("tier")
    if tier is not None and (not isinstance(tier, int) or tier < 0):
        print(f"ERROR: tier must be an int (0-4), got: {tier!r}", file=sys.stderr)
        sys.exit(1)

    claim.setdefault("attempts", []).append({
        "tier": tier,
        "method": att.get("method"),
        "result": att.get("result", "unknown"),
        "at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    })
    _save_ledger(ledger_path, ledger)
    print(f"[{cid}] attempt logged: tier={att.get('tier')} method={att.get('method')} result={att.get('result')}")


# verify-claim tier label → ledger attempt tier (hook Rule 4 accepts tier 1 or 2)
_STAGING_TIER_MAP = {
    "WebFetch": 1,
    "curl": 1,
    "browser-harness CDP": 2,
    "Playwright": 2,
}


def cmd_apply_staging(path: str, ticker: str):
    """Merge .cache/evidence/<TICKER>.verify-staging.json into the ticker ledger.

    For each claim, if a staging entry matches its URL:
      - matched (page text substantiates the claim) → upgrade status/method/tier/
        text + log a tier attempt
      - reachable only (page up, claim text not found — verify-claim --claim-text)
        → keep unverified, log result "reachable_no_match" (tier counts, coverage
        floor still gates)
      - unverified/error → keep status, log the failed attempt
    Unmatched staging entries are reported as unreferenced (verified URLs not used
    in the artifact). Claims with no staging entry stay untouched — coverage floor
    still gates honest completeness.
    """
    ledger_path = _ticker_to_ledger_path(path, ticker)
    if not ledger_path.exists():
        print(f"ERROR: No ledger for {ticker}. Run init first.", file=sys.stderr)
        sys.exit(1)
    staging_path = ledger_path.with_name(ticker + ".verify-staging.json")
    if not staging_path.exists():
        print(f"ERROR: No staging file at {staging_path}. Run verify-claim.py --ledger first.", file=sys.stderr)
        sys.exit(1)
    with open(staging_path, "r", encoding="utf-8") as f:
        staging = json.load(f)

    ledger = _load_ledger(ledger_path)
    by_url = {e["url"]: e for e in staging.get("entries", [])}
    upgraded = failed_attempts = untouched = 0
    unreferenced = [e for e in staging.get("entries", [])
                    if not any(c.get("url") == e["url"] for c in ledger["claims"])]

    for claim in ledger["claims"]:
        entry = by_url.get(claim.get("url", ""))
        if not entry:
            untouched += 1
            continue
        # schema 2 stores tier as int; schema 1 falls back to the method label map
        tier = entry.get("tier")
        if not isinstance(tier, int):
            tier = _STAGING_TIER_MAP.get(entry.get("method", ""), None)
        # matched: verified entry whose page text substantiates the claim.
        # Legacy entries (no matched key) count as matched — reachable-only is
        # the new strict path that must stay unverified.
        status = entry.get("status")
        claim_matched = status == "verified" and entry.get("matched") is not False
        if claim_matched and tier is not None:
            claim["status"] = "verified"
            claim["method"] = entry.get("method") or "verify-claim.py"
            claim["tier"] = tier
            if entry.get("text"):
                claim["text"] = entry["text"]
            claim["checked_at"] = entry.get("checked_at", claim.get("checked_at"))
            upgraded += 1
        else:
            failed_attempts += 1
        # log/refresh the attempt entry (dedup by method+tier+result)
        attempts = claim.setdefault("attempts", [])
        if claim_matched and tier is not None:
            result_label = "ok"
        elif status == "reachable":
            result_label = "reachable_no_match"
        else:
            result_label = (entry.get("error") or "failed")[:80]
        attempt = {"tier": tier, "method": "verify-claim.py", "result": result_label,
                   "at": entry.get("checked_at", "")}
        if not any(a.get("method") == "verify-claim.py" and a.get("tier") == tier
                   and a.get("result") == result_label for a in attempts):
            attempts.append(attempt)

    _save_ledger(ledger_path, ledger)
    print(f"apply-staging {ticker}: {upgraded} upgraded, {failed_attempts} failed-attempt logged, {untouched} untouched")
    if unreferenced:
        print(f"  {len(unreferenced)} staged URL(s) not referenced by any claim:")
        for e in unreferenced[:5]:
            print(f"    {e['url'][:90]} — {e['status']}")


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

    tier = v.get("tier", claim.get("tier"))
    if tier is not None and (not isinstance(tier, int) or tier < 0):
        print(f"ERROR: tier must be an int (0-4), got: {tier!r}", file=sys.stderr)
        sys.exit(1)

    claim["status"] = "verified"
    claim["method"] = v.get("method", claim.get("method"))
    claim["tier"] = tier
    if v.get("text"):
        claim["text"] = v["text"]
    if v.get("quote"):
        claim["quote"] = v["quote"]
    if v.get("section"):
        claim["section"] = v["section"]
    claim["checked_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # log the verification attempt — hook Rule 4 requires tier 1-2 attempts
    # for [I#] claims; verify alone used to leave attempts empty and the hook
    # kept blocking even after a successful verify
    attempts = claim.setdefault("attempts", [])
    attempt = {"tier": tier, "method": claim.get("method") or "verify",
               "result": "ok", "at": claim["checked_at"]}
    if not any(a.get("tier") == tier and a.get("method") == attempt["method"]
               and a.get("result") == "ok" for a in attempts):
        attempts.append(attempt)

    _save_ledger(ledger_path, ledger)
    print(f"[{cid}] verified — tier={claim['tier']} method={claim['method']}")


def cmd_delete(path: str, claim_id: str, ticker: str = ""):
    """Delete a claim from the ledger by ID (no more hand-editing JSON)."""
    if ticker:
        ledger_path = _ticker_to_ledger_path(path, ticker)
    else:
        ledger_path = _artifact_path_to_ledger_path(path)
    if not ledger_path.exists():
        print(f"ERROR: No ledger found at {ledger_path}", file=sys.stderr)
        sys.exit(1)
    ledger = _load_ledger(ledger_path)
    claim = next((c for c in ledger["claims"] if c["id"] == claim_id), None)
    if not claim:
        print(f"ERROR: claim {claim_id} not found", file=sys.stderr)
        sys.exit(1)
    ledger["claims"].remove(claim)
    _save_ledger(ledger_path, ledger)
    print(f"Deleted {claim_id}: [{claim['source']}]({claim['url'][:60]}...)")


def _infer_ticker(path_s: str) -> str:
    """Infer ticker from artifact path: industry/<slug>/companies/<ticker>/..."""
    parts = Path(path_s).parts
    if "companies" in parts:
        idx = list(parts).index("companies")
        if idx + 1 < len(parts):
            return parts[idx + 1]
    return ""


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
    p_scan.add_argument("-t", "--ticker", help="Ticker (inferred from path if omitted)")

    p_batch = sub.add_parser("batch", help="Batch upgrade claims")
    p_batch.add_argument("path", help="Artifact path (for dir resolution)")
    p_batch.add_argument("-t", "--ticker", help="Ticker (inferred from path if omitted)")
    p_batch.add_argument("payload", help="JSON payload: {claims:[{id,status,method,...}], provenance:''}")

    p_auto = sub.add_parser("auto", help="Auto-create pending claims from artifact anchors")
    p_auto.add_argument("artifact", help="Artifact .md path")
    p_auto.add_argument("-t", "--ticker", help="Ticker (inferred from path if omitted)")

    p_attempt = sub.add_parser("attempt", help="Log verification attempt")
    p_attempt.add_argument("path", help="Artifact path (for dir)")
    p_attempt.add_argument("-t", "--ticker", help="Ticker (inferred from path if omitted)")
    p_attempt.add_argument("payload", help='JSON: {"claim_id":"C4","tier":1,"method":"WebFetch","result":"403"}')

    p_verify = sub.add_parser("verify", help="Mark claim as verified")
    p_verify.add_argument("path", help="Artifact path (for dir)")
    p_verify.add_argument("-t", "--ticker", help="Ticker (inferred from path if omitted)")
    p_verify.add_argument("payload", help='JSON: {"claim_id":"C4","tier":2,"method":"Playwright","text":"...","quote":"..."}')

    p_apply = sub.add_parser("apply-staging",
                             help="Merge verify-claim staging file into ledger (by URL)")
    p_apply.add_argument("path", help="Artifact path or company dir")
    p_apply.add_argument("-t", "--ticker", help="Ticker (inferred from path if omitted)")

    p_delete = sub.add_parser("delete", help="Delete a claim from the ledger")
    p_delete.add_argument("path", help="Ticker or artifact path")
    p_delete.add_argument("claim_id", help="Claim ID, e.g. C19")
    p_delete.add_argument("-t", "--ticker", help="Ticker override")

    args = parser.parse_args()
    ticker = getattr(args, "ticker", None) or ""
    if not ticker:
        path_val = getattr(args, "path", None) or getattr(args, "artifact", None) or ""
        ticker = _infer_ticker(path_val)

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
    elif args.command == "apply-staging":
        cmd_apply_staging(args.path, ticker)
    elif args.command == "delete":
        cmd_delete(args.path, args.claim_id, ticker)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
