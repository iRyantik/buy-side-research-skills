"""Hook: every research artifact with [S#]/[I#] anchors must have an evidence ledger.
If the ledger is missing or contains fabrication_risk claims without override, block.
Also checks: tier-gap (WebSearch-only → play missing Playwright) and image audit.
"""
import re, sys, os, json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import block, warn

_ARTIFACT_RE = re.compile(r'^\d{4}-\d{2}-\d{2}-.+\.md$')
ANCHOR_RE = re.compile(r'\[(?:S|I|LBG|P)\d+\]\([^)]+\)')
IMAGE_RE = re.compile(r'!\[[^\]]*\]\(([^)]+)\)')

LEDGER_DIR = "_cache/evidence"

# Methods that count as "actually opened a page" (not AI summary)
DIRECT_ACCESS_METHODS = {"WebFetch", "Playwright", "curl", "actuals"}
SUMMARY_METHODS = {"WebSearch", "unknown"}


def _find_ledger(artifact_path: str) -> str | None:
    """Find the evidence ledger for a given artifact."""
    artifact_dir = os.path.dirname(artifact_path)
    artifact_name = os.path.basename(artifact_path)
    candidates = [
        os.path.join(artifact_dir, LEDGER_DIR, artifact_name + ".evidence.json"),
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return None


def _check_image_exists(artifact_path: str, display: str):
    """Rule: every _cache/images/* reference must exist on disk."""
    with open(artifact_path, "r", encoding="utf-8") as f:
        text = f.read()
    images = IMAGE_RE.findall(text)
    missing = []
    artifact_dir = os.path.dirname(artifact_path)
    for img in images:
        if not img.startswith("_cache/images/") and not img.startswith("./_cache/"):
            continue
        img_path = os.path.join(artifact_dir, img)
        if not os.path.exists(img_path):
            missing.append(img)
    if missing:
        block(f"Blocked by evidence_ledger_floor: {display} references {len(missing)} "
              f"image(s) that don't exist on disk: {', '.join(missing[:5])}. "
              f"Download product images before writing the artifact.")


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

        # Strip code blocks for anchor extraction
        body = re.sub(r'```[^\n]*\n.*?```', '', text, flags=re.DOTALL)
        body = re.sub(r'~~~[^\n]*\n.*?~~~', '', body, flags=re.DOTALL)
        body = body.split('## Resources')[0] if '## Resources' in body else body

        anchors = ANCHOR_RE.findall(body)
        if not anchors:
            continue

        # Rule 1: Image audit (checked first — independent of ledger)
        _check_image_exists(path, display)

        # Rule 2: Ledger must exist
        ledger_path = _find_ledger(path)
        if not ledger_path:
            block(f"Blocked by evidence_ledger_floor: {display} has {len(anchors)} source anchor(s) "
                  f"but no evidence ledger found at {os.path.dirname(path)}/{LEDGER_DIR}/. "
                  f"Run: evidence_ledger.py init <artifact> to create one.")

        try:
            with open(ledger_path, "r", encoding="utf-8") as f:
                ledger = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            block(f"Blocked by evidence_ledger_floor: {display} has corrupted ledger: {e}")

        claims = ledger.get("claims", [])

        # Rule 0: Artifact-Ledger alignment — every [S#]/[I#] must be in ledger
        ledger_codes = {c.get("source", "") for c in claims}
        artifact_codes = set()
        for m in re.finditer(r'\[(S\d+|I\d+)\]', body):
            artifact_codes.add(m.group(1))
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
            has_tier1 = any(a.get("tier") == 1 and a.get("result") != "failed" for a in attempts)
            has_tier2 = any(a.get("tier") == 2 and a.get("result") != "failed" for a in attempts)
            if not (has_tier1 or has_tier2):
                tier_gap_claims.append(c["id"])
        if tier_gap_claims:
            block(f"Blocked by evidence_ledger_floor: {display} has {len(tier_gap_claims)} "
                  f"[I#] claim(s) with no Tier 1-2 verification attempt: "
                  f"{', '.join(tier_gap_claims[:5])}. "
                  f"Must try WebFetch + Playwright before accepting any [I#] source. "
                  f"Run: evidence_ledger.py auto + attempt + verify")

        # Rule 5: Low coverage → warn
        stats = ledger.get("stats", {})
        total = stats.get("total_claims", 0)
        verified = stats.get("verified", 0)
        plausible = stats.get("plausible", 0)
        if total > 5 and (verified + plausible) < total * 0.5:
            warn(f"evidence_ledger_floor: {display} has low coverage: "
                 f"{verified + plausible}/{total} verified+plausible ({int((verified+plausible)/total*100)}%). "
                 f"Consider upgrading more claims from unverified.")

    sys.exit(0)
