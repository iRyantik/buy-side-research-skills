"""Hook: after writing a research artifact, remind agent to update RESEARCH.md.

This is a WARN-level hook — it never blocks, only suggests.
"""
import os, re, sys, datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import warn

ARTIFACT_RE = re.compile(r'^(\d{8})-[\w\[\]-]+\.md$')


def _find_research_md(artifact_path: str) -> str | None:
    """Map artifact path → corresponding RESEARCH.md (company level preferred)."""
    artifact_dir = os.path.dirname(os.path.abspath(artifact_path))
    # Try company level first
    company_rm = os.path.join(artifact_dir, "RESEARCH.md")
    if os.path.exists(company_rm):
        return company_rm
    # Try industry level (go up from companies/<ticker>/ to industry/)
    up = os.path.dirname(os.path.dirname(artifact_dir))
    industry_rm = os.path.join(up, "RESEARCH.md")
    if os.path.exists(industry_rm):
        return industry_rm
    return None


def check(ctx):
    for t in ctx.get("targets", []):
        if t.get("kind") != "file":
            continue
        path = t.get("path") or ""
        display = t.get("display", "unknown")
        leaf = os.path.basename(path)

        # Only match YYYYMMDD-skill-*.md artifacts
        if not ARTIFACT_RE.match(leaf):
            continue

        rm_path = _find_research_md(path)
        if not rm_path:
            continue

        # Check if RESEARCH.md was updated today
        try:
            mtime = os.path.getmtime(rm_path)
            mdate = datetime.date.fromtimestamp(mtime)
            today = datetime.date.today()
            if mdate < today:
                warn(f"research_memory_gate: {display} written, "
                     f"but RESEARCH.md ({os.path.basename(os.path.dirname(rm_path))}) "
                     f"last updated {mdate}. Consider updating RESEARCH.md.")
        except OSError:
            pass

    sys.exit(0)
