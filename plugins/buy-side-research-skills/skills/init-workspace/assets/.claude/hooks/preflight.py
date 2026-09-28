"""Preflight: simulate the workspace hook chain against a target file.

Usage:
  python .claude/hooks/preflight.py <artifact.md>
  python .claude/hooks/preflight.py <artifact.md> --event PreToolUse

Default runs PostToolUse (source_contract / table_render_integrity /
mermaid_syntax / evidence_ledger_floor / ... — the rules that burned
artifact writes). --event PreToolUse runs the write gate
(workspace_guard / financial_data_gate / pre_write_gate) using the file's
current content as the would-be written content.

Exit code: 0 = hooks clean/soft, 2 = hooks would block, 1 = runner error.
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def _workspace_root() -> str:
    env_root = os.environ.get("CLAUDE_PROJECT_DIR", "")
    if env_root and os.path.isdir(os.path.join(env_root, "industry")):
        return env_root
    return os.path.dirname(os.path.dirname(HERE))


def _build_payload(event: str, path: str, content: str) -> dict:
    root = _workspace_root()
    return {
        "cwd": root,
        "session_id": "preflight",
        "hook_event_name": "PreToolUse" if event == "PreToolUse" else "PostToolUse",
        "tool_name": "Write" if event == "PreToolUse" else "PostToolUse",
        "tool_input": {"file_path": os.path.abspath(path), "content": content},
        "last_assistant_message": "",
        "targets": [],
    }


def main() -> int:
    args = sys.argv[1:]
    path = next((a for a in args if not a.startswith("--")), None)
    event = "PostToolUse"
    if "--event" in args:
        try:
            event = args[args.index("--event") + 1]
        except IndexError:
            pass
    if event not in ("PreToolUse", "PostToolUse"):
        print(f"preflight: unknown event {event!r} (use PreToolUse|PostToolUse)")
        return 1
    if not path:
        print("preflight: usage: python .claude/hooks/preflight.py <artifact.md> "
              "[--event PreToolUse|PostToolUse]")
        return 1
    path = os.path.abspath(path)
    if not os.path.isfile(path):
        print(f"preflight: no such file: {path}")
        return 1
    try:
        with open(path, encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print(f"preflight: cannot read {path}: {e}")
        return 1
    payload = _build_payload(event, path, content)
    cmd = [sys.executable, os.path.join(HERE, "hook_entry.py"),
           "--runtime", "claude", "--event", event]
    env = {**os.environ}
    env.setdefault("PYTHONIOENCODING", "utf-8")
    proc = subprocess.run(cmd, input=json.dumps(payload),
                          capture_output=True, text=True, encoding="utf-8", env=env)
    if proc.stdout:
        sys.stdout.write(proc.stdout)
    if proc.stderr:
        sys.stderr.write(proc.stderr)
    return proc.returncode


if __name__ == "__main__":
    sys.exit(main())
