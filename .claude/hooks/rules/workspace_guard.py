"""Rule 1: Workspace path/naming guard."""
import sys, os, re
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import is_under, get_relative_display, is_topic_artifact_root_file, block

# Legacy root paths that are forbidden
LEGACY_ROOTS = re.compile(r'^(screens|peers|quickreads|cross-market)/')

# Company-level skills that require company qualifier in artifact name
COMPANY_SKILLS = {
    'stock-quickread', 'company-history', 'driver-map',
    'alpha-thesis', 'consensus-map', 'earnings-setup', 'bear-pre-mortem',
}

# Topic root artifact naming: YYYY-MM-DD-slug.md
DATE_PREFIX_RE = re.compile(r'^\d{4}-\d{2}-\d{2}-[a-z0-9][a-z0-9\-]*\.(md|html)$')

def check(ctx: dict):
    """Entry point called by hook_entry. Blocking errors call block()."""
    root = ctx["cwd"]
    for path in ctx.get("candidate_paths", []):
        rel = get_relative_display(path, root)

        # Rule 1: Must be inside workspace root
        if not is_under(path, root):
            block(f"Blocked by workspace_guard: write target escapes workspace root ({rel})")

        # Rule 2: No legacy root paths
        if LEGACY_ROOTS.match(rel.replace('\\', '/')):
            block(f"Blocked by workspace_guard: legacy root paths not allowed ({rel})")

        # Rule 3: Topic root artifacts must be date-prefixed (except index.md)
        if is_topic_artifact_root_file(path, root):
            leaf = Path(path).name
            if leaf.lower() == "index.md":
                continue
            if not DATE_PREFIX_RE.match(leaf):
                block(f"Blocked by workspace_guard: topic root artifact must be date-prefixed ({rel})")

        # Rule 4: Company-level skill artifacts must include company qualifier
        leaf = Path(path).name
        if DATE_PREFIX_RE.match(leaf):
            slug = leaf.rsplit('.', 1)[0]  # remove extension
            # Extract artifact base name (strip date prefix)
            parts = slug.split('-', 3)  # YYYY, MM, DD, rest
            if len(parts) >= 4:
                artifact = parts[3]
                for skill in COMPANY_SKILLS:
                    if artifact == skill:
                        block(f"Blocked by workspace_guard: company-level artifact '{skill}' requires company qualifier, e.g. '{skill}-<company>' ({rel})")
