"""Rule: Prevent Bash commands from writing files outside workspace root.

Catches patterns like:
    python -c "open('/path/outside/workspace', 'w')..."
    python -c "...shutil.copy(...)"
    curl -o /outside/workspace ...
    git clone /outside/workspace ...

Does NOT block: read-only operations, or writes inside workspace.
"""
import sys, os, re
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import block

# Non-workspace paths that should never receive writes from Bash
FORBIDDEN_ROOTS = [
    r"C:\\Users\\[^\\]+\\dev\\buyside",
    r"C:\\Users\\[^\\]+\\dev\\buy-side-research-skills",
    r"C:\\Users\\[^\\]+\\Desktop\\buy-side-research-skills",
    r"C:\\Program Files",
    r"C:\\Program Files \(x86\)",
    r"C:\\Windows",
    r"C:\\Users\\[^\\]+\\.claude\\plugins\\cache",
    r"C:\\Users\\[^\\]+\\.claude\\plugins\\marketplaces",
]

# Write operations to scan for
WRITE_PATTERNS = [
    r"open\(['\"]([^'\"]+)['\"],\s*['\"]w",
    r"\.write_text\(['\"]([^'\"]+)['\"]",
    r"\.write_bytes\(['\"]([^'\"]+)['\"]",
    r"shutil\.(copy|copy2|copytree|move)\(",
    r"curl\s+.*\s+-o\s+\"?(C:\\Users[^\"\s]+)",
    r"wget\s+.*\s+-O\s+\"?(C:\\Users[^\"\s]+)",
    r"git\s+clone\s+.*\s+(C:\\Users[^\"\s]+)",
]


def check(ctx: dict):
    """Entry point called by hook_entry for PostToolUse(Bash) or PreToolUse(Bash)."""
    tool_name = ctx.get("tool_name", "")
    if tool_name.lower() != "bash":
        return

    command = ctx.get("tool_input", {}).get("command", "")
    if not command:
        return

    workspace_root = ctx.get("cwd", "")
    ws = Path(workspace_root).resolve()

    # Normalize path separators for matching
    cmd_normalized = command.replace("\\\\", "\\")

    # Check for forbidden root patterns in write operations
    for pattern in FORBIDDEN_ROOTS:
        if not re.search(pattern, cmd_normalized):
            continue
        # Found a forbidden path — check if there's a write operation
        for wpat in WRITE_PATTERNS:
            if re.search(wpat, cmd_normalized):
                block(
                    f"Blocked by bash_workspace_guard: Bash command references non-workspace path "
                    f"with a write operation. Use Python in the workspace to generate files, "
                    f"then copy them to the target manually."
                )

    # Also catch raw Python file writes to arbitrary paths outside workspace
    # Pattern: Path('C:/Users/...') or open('C:/Users/...', 'w')
    path_refs = re.findall(r"['\"]([A-Z]:\\[^'\"]+)['\"]", cmd_normalized)
    for path_ref in path_refs:
        try:
            p = Path(path_ref).resolve()
            # Skip if under workspace
            try:
                p.relative_to(ws)
                continue
            except ValueError:
                pass
            # Skip temp dirs
            if any(t in str(p).lower() for t in ["\\temp\\", "\\tmp\\", "appdata\\local\\temp"]):
                continue
            # Check for write intent
            for wpat in WRITE_PATTERNS:
                if re.search(wpat, cmd_normalized):
                    block(
                        f"Blocked by bash_workspace_guard: command writes to '{path_ref}' "
                        f"outside workspace ({ws}). Manual copy after generation is allowed."
                    )
        except Exception:
            pass
