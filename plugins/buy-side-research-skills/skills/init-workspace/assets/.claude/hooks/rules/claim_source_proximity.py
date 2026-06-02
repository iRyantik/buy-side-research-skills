"""Check: strong claims (exclusive, confirmed, monopoly, only) must have a source anchor in the same section."""
import re, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import block, warn
import os as _os
_ARTIFACT_RE = __import__("re").compile(r"^\d{4}-\d{2}-\d{2}-.+\.md$")
def _is_artifact(fp): return bool(_ARTIFACT_RE.match(_os.path.basename(fp)))

STRONG_CLAIM = re.compile(
    r'(?i)(独家|唯一供应商|唯一|仅有的|垄断|exclusive|sole supplier|only vendor|confirmed|certified|验证过的唯一|全球独家|独占)'
)
SOURCE_ANCHOR = re.compile(r'\[(?:S\d+|I\d+|LBG\d+|P\d+|SRC\d+)\]')

SECTION_BOUNDARY = re.compile(r'^##\s', re.MULTILINE)

def check(ctx):
    for t in ctx.get("targets", []):
        text = t.get("text", "")
        if not text:
            continue
        path = t.get("path", "") or ""
        leaf = os.path.basename(path) if path else ""
        if not _is_artifact(leaf):
            continue

        # Split into sections
        sections = SECTION_BOUNDARY.split(text)
        issues = []
        for si, section in enumerate(sections):
            if not STRONG_CLAIM.search(section):
                continue
            if SOURCE_ANCHOR.search(section):
                continue
            # Extract the claim
            claim = STRONG_CLAIM.search(section).group(0)
            heading = section.split('\n')[0][:80] if section.strip() else '(top)'
            issues.append(f"{claim} in section '{heading}'")

        if issues:
            warn(f"claim_source_proximity: {t.get('display','?')} has strong claims without source anchors: {', '.join(issues[:3])}.")

sys.exit(0)
