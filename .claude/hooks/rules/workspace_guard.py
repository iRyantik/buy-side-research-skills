"""Rule 1: Workspace path/naming guard + root whitelist."""
import sys, os, re
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import is_under, get_relative_display, is_topic_artifact_root_file, block, warn

LEGACY_ROOTS = re.compile(r'^(screens|peers|quickreads|cross-market)/')

COMPANY_SKILLS = {
    'stock-quickread', 'company-history', 'driver-map',
    'alpha-thesis', 'consensus-map', 'earnings-setup', 'bear-pre-mortem',
}

DATE_PREFIX_RE = re.compile(r'^\d{8}-[a-z0-9A-Z\[\]][a-z0-9A-Z\[\]\-_]*\.(md|html)$')

ROOT_WHITELIST = frozenset({
    "industry", ".cache", ".scripts", ".claude", ".codex",
    ".references", "COVERAGE.md", "CLAUDE.md", "AGENTS.md", ".env", ".gitignore",
    "daily",
})

# External dev roots explicitly allowed for writes (plugin dev repo).
# Keep in sync with the installed workspace copy of this file.
ALLOWED_EXTERNAL_ROOTS = (
    r"C:\Users\yuzhe\dev\buy-side-research-skills",
    # Claude memory / session 目录（各 workspace 的 memory 都在下面，放行合理）
    str(Path.home() / ".claude" / "projects"),
)


def _check_root_whitelist(path: str, root: str) -> bool:
    """Check if path is allowed at workspace root level. Returns True if OK."""
    rel = get_relative_display(path, root).replace("\\", "/")
    top = rel.split("/")[0] if rel else ""
    if top.startswith("."):
        top = "." + top.split("/")[0] if "/" in top else top
    # Normalize: if rel is just a filename, check against whitelist
    if "/" not in rel:
        return rel in ROOT_WHITELIST
    # If in a subdirectory, check the top-level directory
    return top in ROOT_WHITELIST


def check(ctx: dict):
    """Entry point called by hook_entry."""
    root = ctx["cwd"]
    paths = ctx.get("candidate_paths", [])
    event = ctx.get("event", "")

    for path in paths:
        if not path:
            continue
        rel = get_relative_display(path, root)

        # Rule 0: Explicitly allowed external dev roots (plugin dev repo)
        # bypass workspace-root and naming rules entirely.
        if any(is_under(path, r) for r in ALLOWED_EXTERNAL_ROOTS):
            continue

        # Rule 1: Must be inside workspace root
        if not is_under(path, root):
            block(f"Blocked by workspace_guard: write target escapes workspace root ({rel})")

        # Rule 2: No legacy root paths
        if LEGACY_ROOTS.match(rel.replace('\\', '/')):
            block(f"Blocked by workspace_guard: legacy root paths not allowed ({rel})")

        # Rule 3: Root-level whitelist — warn on PostToolUse, block on PreToolUse
        if not _check_root_whitelist(path, root):
            msg = f"workspace_guard: file outside allowed paths ({rel}). Allowed: industry/, .cache/, .scripts/, .claude/, .codex/, .references/, CLAUDE.md, AGENTS.md, COVERAGE.md, .env, .gitignore"
            if event == "PreToolUse":
                block(f"Blocked by {msg}")
            else:
                warn(f"Warning: {msg}")

        # Rule 4: Topic root artifacts must be date-prefixed (except RESEARCH.md)
        if is_topic_artifact_root_file(path, root):
            leaf = Path(path).name
            if leaf.lower() == "research.md":
                continue
            if not DATE_PREFIX_RE.match(leaf):
                block(f"Blocked by workspace_guard: topic root artifact must be date-prefixed ({rel})")

        # Rule 5: Company-level skill artifacts must include company qualifier
        leaf = Path(path).name
        if DATE_PREFIX_RE.match(leaf):
            slug = leaf.rsplit('.', 1)[0]
            parts = slug.split('-', 3)
            if len(parts) >= 4:
                artifact = parts[3]
                for skill in COMPANY_SKILLS:
                    if artifact == skill:
                        block(f"Blocked by workspace_guard: company-level artifact '{skill}' requires company qualifier, e.g. '{skill}-<company>' ({rel})")
