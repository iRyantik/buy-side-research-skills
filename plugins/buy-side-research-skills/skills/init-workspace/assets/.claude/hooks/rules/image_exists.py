"""Rule: image references in markdown must point to existing local files."""
import re, sys, os
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import block

IMAGE_RE = re.compile(r'!\[.*?\]\((_cache/images/[^)]+)\)')

def check(ctx: dict):
    for target in ctx.get("targets", []):
        if target.get("kind") != "file":
            continue
        text = target.get("text", "")
        if not _is_artifact(target.get("display", "")):
            continue
        display = target.get("display", "unknown")
        # Resolve image paths relative to the markdown file's directory
        md_dir = os.path.dirname(target.get("path", "")) if target.get("path") else ctx.get("cwd", "")
        for m in IMAGE_RE.finditer(text):
            img_path = m.group(1)
            full = os.path.normpath(os.path.join(md_dir, img_path))
            if not os.path.isfile(full):
                block(
                    f"Blocked by image_exists: {display} references {img_path} "
                    f"but file does not exist. Download image first: "
                    f"1. company IR Media Kit -> 2. web search product photo -> 3. skip if unavailable."
                )
