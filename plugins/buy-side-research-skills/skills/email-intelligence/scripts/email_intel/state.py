"""Incremental email-review state."""

from __future__ import annotations

import json
from pathlib import Path


def state_path(workspace: Path) -> Path:
    path = workspace / ".cache" / "email-intelligence" / "state.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def load_state(workspace: Path) -> dict:
    try:
        return json.loads(state_path(workspace).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"seen": [], "last_run": "", "last_sent": ""}


def save_state(workspace: Path, state: dict) -> None:
    state_path(workspace).write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def mark_seen(state: dict, keys: list[str]) -> None:
    seen = set(state.get("seen", []))
    seen.update(key for key in keys if key)
    state["seen"] = sorted(seen)[-5_000:]
