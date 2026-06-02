"""Hook: every research artifact with [S#]/[I#] anchors must have an evidence ledger.
If the ledger is missing or contains fabrication_risk claims without override, block.
"""
import re, sys, os, json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import block, warn

_ARTIFACT_RE = re.compile(r'^\d{4}-\d{2}-\d{2}-.+\.md$')
ANCHOR_RE = re.compile(r'\[(?:S|I|LBG|P)\d+\]\([^)]+\)')

LEDGER_DIR = "_cache/evidence"


def _find_ledger(artifact_path: str) -> str | None:
    """Find the evidence ledger for a given artifact."""
    artifact_dir = os.path.dirname(artifact_path)
    artifact_name = os.path.basename(artifact_path)
    candidates = [
        os.path.join(artifact_dir, LEDGER_DIR, artifact_name + ".evidence.json"),
        os.path.join(artifact_dir, LEDGER_DIR, artifact_name + ".evidence.json"),
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return None


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
        # Remove Resources section
        body = body.split('## Resources')[0] if '## Resources' in body else body

        anchors = ANCHOR_RE.findall(body)
        if not anchors:
            continue  # No source anchors → nothing to check

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

        # Check fabrication_risk
        fab_risks = [c for c in ledger.get("claims", []) if c.get("status") == "fabrication_risk"]
        if fab_risks:
            block(f"Blocked by evidence_ledger_floor: {display} has {len(fab_risks)} "
                  f"FABRICATION_RISK claim(s) in ledger: "
                  f"{', '.join(c.get('id','?') for c in fab_risks[:5])}. "
                  f"Either verify the source or remove the claim from the artifact.")

        # Warn if low coverage (less than 50% verified)
        stats = ledger.get("stats", {})
        total = stats.get("total_claims", 0)
        verified = stats.get("verified", 0)
        plausible = stats.get("plausible", 0)
        if total > 5 and (verified + plausible) < total * 0.5:
            warn(f"evidence_ledger_floor: {display} has low coverage: "
                 f"{verified + plausible}/{total} verified+plausible ({int((verified+plausible)/total*100)}%). "
                 f"Consider upgrading more claims from unverified.")

    sys.exit(0)
