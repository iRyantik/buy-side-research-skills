"""Check: artifact image references must resolve to a file in the workspace image pool.

PostToolUse warn-only rule (never blocks). Catches the recurring "图片加载不出来"
class at write time: hand-typed relative paths (cache/ vs .cache/, wrong ../ depth),
absolute paths (Typora paste from another machine), '/' rooted paths, and refs to
files that were never downloaded.

Canonical pool: <workspace>/.cache/images/ (download-image.py, cross-skill shared).
Repair path the agent should take (message tells it):
  python .scripts/shared/image-path-check.py --fix    # migrate + rewrite refs
  python .scripts/shared/download-image.py <url> --output <slug>   # missing image
  or replace the ref with a [缺图] marker if the image is truly unavailable.
"""
import re, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from common import warn

IMG_RE = re.compile(r'!\[[^\]]*\]\(([^)]+)\)')
IMG_EXT = re.compile(r'\.(png|jpe?g|webp|gif|svg|ico)$', re.IGNORECASE)
SKIP_PREFIX = ("http://", "https://", "data:", "mailto:")


def _resolve(workspace: str, md_path: str, target: str):
    """Return (resolved_abs, kind) — kind in REL/ROOTED/ABSOLUTE. None if unresolvable."""
    t = target.strip()
    if re.match(r'^[A-Za-z]:[\\/]', t):
        return t, "ABSOLUTE"
    if t.startswith("/"):
        return os.path.normpath(os.path.join(workspace, t.lstrip("/"))), "ROOTED"
    return os.path.normpath(os.path.join(os.path.dirname(md_path), t)), "REL"


def check(ctx):
    root = ctx.get("cwd", "") or ""
    for t in ctx.get("targets", []):
        text = t.get("text", "")
        path = t.get("path", "") or ""
        if not text or not path:
            continue
        if ".cache" in path.replace("\\", "/").split("/"):
            continue
        for m in IMG_RE.finditer(text):
            target = m.group(1).strip()
            if not IMG_EXT.search(target):
                continue
            if target.lower().startswith(SKIP_PREFIX):
                continue
            resolved, kind = _resolve(root, path, target)
            if os.path.isfile(resolved):
                continue
            lineno = text.count("\n", 0, m.start()) + 1
            hint = "run image-path-check.py --fix to repair" if kind == "REL" else "absolute//-rooted ref never resolves on this machine — point at workspace .cache/images/ or mark [缺图]"
            warn(f"image_path_integrity: {t.get('display', path)} L{lineno}: image missing: {target} — {hint}")
