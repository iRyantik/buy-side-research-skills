"""Claude Code adapter — maps native payload to unified HookContext."""
import sys, os
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import (
    load_stdin_payload, get_tool_name, get_tool_input, get_hook_event,
    get_workspace_root, get_candidate_paths, get_last_assistant_message,
    is_artifact_like, get_markdown_targets, scan_recent_mtime,
)

# Claude Code write-like tool names
WRITE_TOOLS = {"Write", "Edit", "MultiEdit", "Bash"}

def build_context(payload: dict) -> dict:
    """Build unified HookContext from Claude Code raw payload."""
    root = get_workspace_root(payload)
    tool = get_tool_name(payload)
    event = get_hook_event(payload)
    candidates = get_candidate_paths(payload)
    assistant_text = get_last_assistant_message(payload)

    # Bash writes: scan mtime for files agent created via Python/shell/redirect
    if tool == "Bash":
        bash_writes = scan_recent_mtime(root, since_seconds=15.0)
        if bash_writes:
            candidates = list(set(candidates + bash_writes))

    # Build targets
    targets = get_markdown_targets(payload)
    # For Bash: re-scan mtime-found files into targets
    if tool == "Bash" and bash_writes:
        for fp in bash_writes:
            if fp not in [t.get("path", "") for t in targets]:
                try:
                    text = Path(fp).read_text(encoding="utf-8")
                    targets.append({"kind": "file", "path": fp, "display": str(Path(fp).relative_to(root)), "text": text})
                except Exception:
                    pass

    return {
        "runtime": "claude",
        "event": event,
        "tool_name": tool,
        "cwd": root,
        "session_id": payload.get("session_id", ""),
        "candidate_paths": candidates,
        "assistant_text": assistant_text,
        "targets": targets,
        "raw_payload": payload,
        "is_write_intent": tool in WRITE_TOOLS,
    }
