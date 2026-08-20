"""Hook: every research artifact with [S#]/[I#] anchors must have an evidence ledger.
If the ledger is missing or contains fabrication_risk claims without override, block.
Also checks: tier-gap (WebSearch-only → play missing Playwright) and image audit.

== Agent Action Routing Table ==
| gate | action | agent fix |
|---|---|---|
| image_missing | goto_step_5_download | Execute Step 5a-5f for each missing file |
| ledger_missing | goto_step_2_init_ledger | Run `python .scripts/evidence_ledger.py init <artifact> -t <TICKER>` |
| ledger_corrupted | goto_step_2_init_ledger | Delete and re-init the ledger |
| fabrication_risk | goto_step_4_verify | Verify or delete the flagged claim |
| tier_gap | goto_step_4_verify | Each [I#] must have ≥1 WebFetch/Playwright/curl attempt |
| unprocessed_claim | goto_step_4_verify | Every anchored claim needs non-unverified status + attempt record ([S#]: WebFetch/actuals cross-check; [I#]: tier 1-2). Dead sources: corroborate or remove anchor+claim |

If the ledger is missing or contains fabrication_risk claims without override, block.
Also checks: tier-gap (WebSearch-only → play missing Playwright) and image audit.
"""
import re, sys, os, json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import block, warn

_ARTIFACT_RE = re.compile(r'^\d{8}-.+\.md$')
IMAGE_RE = re.compile(r'!\[[^\]]*\]\(([^)]+)\)')

# Anchor extraction: single source of truth shared with evidence_ledger.py
# (auto/lint/scan scan the SAME full content — code blocks + Resources — so
# Rule 0 and the CLI can never drift apart again; the old per-file strip logic
# is exactly how anchors inside a tone-tracker code block went missing).
try:
    sys.path.insert(0, os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        ".scripts"))
    from evidence_ledger import extract_anchors as _extract_anchors
except ImportError:
    _extract_anchors = None


def _anchor_map(text: str) -> dict:
    """Canonical anchor map; emergency inline fallback keeps full-scan semantics."""
    if _extract_anchors is not None:
        return _extract_anchors(text)
    anchor_map = {}
    for m in re.finditer(r'\[(S\d+|I\d+)\]\(([^)]+)\)', text):
        code, url = m.group(1), m.group(2)
        if code not in anchor_map:
            anchor_map[code] = url
    return anchor_map

LEDGER_DIR = ".cache/evidence"

# Methods that count as "actually verified" (shared tooling or direct page access)
DIRECT_ACCESS_METHODS = {"verify-claim.py", "download-image.py", "actuals-to-appendix.py",
                         "WebFetch", "Playwright", "curl", "actuals", "web-extract.py", "pdf-extract.py"}
SUMMARY_METHODS = {"WebSearch", "unknown"}


def _find_ledger(artifact_path: str) -> str | None:
    """Find the evidence ledger for a given artifact.

    Checks both artifact-stem naming (<artifact>.md.evidence.json) and
    ticker-based naming (<TICKER>.evidence.json) as a fallback.
    """
    artifact_dir = os.path.dirname(artifact_path)
    artifact_name = os.path.basename(artifact_path)
    candidates = [
        os.path.join(artifact_dir, LEDGER_DIR, artifact_name + ".evidence.json"),
    ]
    # Also check for ticker-named ledgers in the same directory
    try:
        ledger_dir = os.path.join(artifact_dir, LEDGER_DIR)
        if os.path.isdir(ledger_dir):
            for f in os.listdir(ledger_dir):
                if f.endswith(".evidence.json"):
                    fp = os.path.join(ledger_dir, f)
                    if fp not in candidates:
                        candidates.append(fp)
    except OSError:
        pass
    for c in candidates:
        if os.path.exists(c):
            return c
    return None


def _check_image_exists(artifact_path: str, display: str):
    """Rule: every .cache/images/* reference must exist on disk."""
    with open(artifact_path, "r", encoding="utf-8") as f:
        text = f.read()
    images = IMAGE_RE.findall(text)
    missing = []
    artifact_dir = os.path.dirname(artifact_path)
    for img in images:
        if not img.startswith(".cache/images/") and not img.startswith("./.cache/"):
            continue
        img_path = os.path.join(artifact_dir, img)
        if not os.path.exists(img_path):
            missing.append(img)
    if missing:
        block(f"Blocked by evidence_ledger_floor: {display} references "
              f"{len(missing)} image(s) not on disk: "
              f"{', '.join(missing[:3])}. Download them before writing.")


def check(ctx):
    for t in ctx.get("targets", []):
        if t.get("kind") != "file":
            continue
        path = t.get("path") or ""
        display = t.get("display", "unknown")
        leaf = os.path.basename(path) if path else ""
        if not _ARTIFACT_RE.match(leaf):
            continue

        text = t.get("text", "")
        if not text:
            continue

        # Full-content anchor scan (code blocks + Resources included — same
        # semantics as evidence_ledger.py auto/lint/scan)
        anchor_map = _anchor_map(text)
        if not anchor_map:
            continue

        # Rule 1: Image audit (checked first — independent of ledger)
        _check_image_exists(path, display)

        # Rule 2: Ledger must exist
        ledger_path = _find_ledger(path)
        if not ledger_path:
            block(f"Blocked by evidence_ledger_floor: {display} has {len(anchor_map)} source anchor(s) "
                  f"but no evidence ledger found at {os.path.dirname(path)}/{LEDGER_DIR}/. "
                  f"Run: evidence_ledger.py init <artifact> to create one.")

        try:
            with open(ledger_path, "r", encoding="utf-8") as f:
                ledger = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            block(f"Blocked by evidence_ledger_floor: {display} "
                  f"ledger is corrupted: {e}. Re-init with evidence_ledger.py.")

        claims = ledger.get("claims", [])

        # Rule 0: Artifact-Ledger alignment — every [S#]/[I#] must be in ledger
        ledger_codes = {c.get("source", "") for c in claims}
        artifact_codes = set(anchor_map.keys())
        missing = artifact_codes - ledger_codes
        if missing:
            block(f"Blocked by evidence_ledger_floor: {display} references "
                  f"{', '.join(sorted(missing)[:5])} "
                  f"which are NOT in the evidence ledger. "
                  f"Run: evidence_ledger.py auto + attempt + verify before writing.")

        # Rule 3: fabrication_risk → block
        fab_risks = [c for c in claims if c.get("status") == "fabrication_risk"]
        if fab_risks:
            block(f"Blocked by evidence_ledger_floor: {display} has {len(fab_risks)} "
                  f"FABRICATION_RISK claim(s) in ledger: "
                  f"{', '.join(c.get('id','?') for c in fab_risks[:5])}. "
                  f"Either verify the source or remove the claim from the artifact.")

        # Rule 4: Attempts check — every [I#] claim must have Tier 1-2 attempt
        tier_gap_claims = []
        for c in claims:
            if not c.get("source", "").startswith("I"):
                continue  # [S#] company disclosure may have actuals fallback
            attempts = c.get("attempts", [])

            def _int_tier(a):
                t = a.get("tier")
                if isinstance(t, str):
                    return int(t) if t.isdigit() else None
                return t if isinstance(t, int) else None

            has_tier1 = any(_int_tier(a) == 1 and a.get("result") != "failed" for a in attempts)
            has_tier2 = any(_int_tier(a) == 2 and a.get("result") != "failed" for a in attempts)
            if not (has_tier1 or has_tier2):
                tier_gap_claims.append(c["id"])
        if tier_gap_claims:
            block(f"Blocked by evidence_ledger_floor: {display} has {len(tier_gap_claims)} "
                  f"[I#] claim(s) with no Tier 1-2 verification attempt: "
                  f"{', '.join(tier_gap_claims[:5])}. "
                  f"Must try WebFetch + Playwright before accepting any [I#] source. "
                  f"Run: evidence_ledger.py auto + attempt + verify")

        # Rule 5: Disposition gate — every claim this artifact anchors must have
        # left 'unverified' AND carry an attempt record. Replaces the old coverage
        # quota (≥80% verified+plausible): a quota could be met by mass-marking
        # claims plausible with zero evidence, and it punished honest dead-link
        # handling. Scoped to this artifact's codes — stale claims from other
        # artifacts of the same ticker do not gate this write.
        artifact_claims = [c for c in claims if c.get("source", "") in artifact_codes]
        unprocessed = [c.get("id", "?") for c in artifact_claims if c.get("status") == "unverified"]
        no_attempt = [c.get("id", "?") for c in artifact_claims if not c.get("attempts")]
        if unprocessed or no_attempt:
            parts = []
            if unprocessed:
                parts.append(f"{len(unprocessed)} unverified: {', '.join(unprocessed[:5])}")
            if no_attempt:
                parts.append(f"{len(no_attempt)} no attempt record: {', '.join(no_attempt[:5])}")
            block(f"Blocked by evidence_ledger_floor: {display} — {'; '.join(parts)}. "
                  f"Every anchored claim needs a non-unverified status AND an attempt record "
                  f"([S#]: one WebFetch/actuals cross-check; [I#]: tier 1-2, Rule 4). "
                  f"Dead sources: corroborate or remove the anchor + claim. "
                  f"Run: evidence_ledger.py verify <dir> -t <TICKER> (per-claim JSON).")

    sys.exit(0)
