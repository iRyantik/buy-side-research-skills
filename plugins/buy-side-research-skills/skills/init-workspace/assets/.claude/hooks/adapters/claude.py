"""Claude Code adapter — maps native payload to unified HookContext."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import (
    load_stdin_payload, get_tool_name, get_tool_input, get_hook_event,
    get_workspace_root, get_candidate_paths, get_last_assistant_message,
    is_artifact_like, get_markdown_targets,
)

# Claude Code write-like tool names
WRITE_TOOLS = {"Write", "Edit", "MultiEdit"}

def build_context(payload: dict) -> dict:
    """Build unified HookContext from Claude Code raw payload."""
    root = get_workspace_root(payload)
    tool = get_tool_name(payload)
    event = get_hook_event(payload)
    candidates = get_candidate_paths(payload)
    assistant_text = get_last_assistant_message(payload)

    # Build targets (files only — never scan conversation messages)
    # Stop events: only inline target
    if event == "Stop":
        targets = []
    else:
        targets = get_markdown_targets(payload)

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
