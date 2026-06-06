"""Single-source hook dispatch and host config generation."""

from __future__ import annotations

import importlib
import json
import os
from pathlib import Path
from typing import Any

from ..source_intake import SourceIntake


EVENTS = ("PreToolUse", "PostToolUse", "Stop", "SubagentStop")


def _registry_path() -> Path:
    return Path(__file__).with_name("hooks.registry.yaml")


def generate_host_configs() -> dict[str, dict[str, Any]]:
    """Generate Claude and Codex hook configs from the supported event set."""
    claude_hooks = {}
    codex_hooks = {}
    for event in EVENTS:
        claude_hooks[event] = [
            {
                "matcher": "",
                "hooks": [
                    {
                        "type": "command",
                        "command": [
                            "python",
                            ".claude/hooks/hook_entry.py",
                            "--runtime",
                            "claude",
                            "--event",
                            event,
                        ],
                    }
                ],
            }
        ]
        codex_hooks[event] = [
            {
                "matcher": "",
                "hooks": [
                    {
                        "type": "command",
                        "command": f"python .claude/hooks/hook_entry.py --runtime codex --event {event}",
                    }
                ],
            }
        ]
    return {"claude": {"hooks": claude_hooks}, "codex": {"hooks": codex_hooks}}


def normalize_context(event: str, payload: dict[str, Any]) -> dict[str, Any]:
    cwd = str(payload.get("cwd") or payload.get("workspace_root") or os.getcwd())
    tool_input = payload.get("tool_input") or payload.get("toolInput") or {}
    candidates = list(payload.get("candidate_paths") or [])
    for key in ("file_path", "path", "download_path", "downloadPath", "output_path"):
        value = tool_input.get(key)
        if value:
            path = Path(value)
            candidates.append(str(path if path.is_absolute() else Path(cwd) / path))
    targets = []
    for raw in dict.fromkeys(candidates):
        path = Path(raw)
        if path.is_file() and path.suffix.lower() in {".md", ".html"}:
            try:
                text = path.read_text(encoding="utf-8")
            except OSError:
                continue
            targets.append({"kind": "file", "path": str(path), "display": str(path), "text": text})
    return {
        "event": event,
        "cwd": cwd,
        "candidate_paths": list(dict.fromkeys(candidates)),
        "targets": targets,
        "tool_input": tool_input,
        "raw_payload": payload,
    }


class HookDispatcher:
    def __init__(self, registry_path: Path | None = None):
        self.registry_path = registry_path or _registry_path()
        self.registry = json.loads(self.registry_path.read_text(encoding="utf-8"))

    def rule_names(self, event: str) -> list[str]:
        return [
            rule["name"]
            for rule in self.registry["rules"]
            if event in rule.get("events", [])
        ]

    def dispatch(self, event: str, payload: dict[str, Any]) -> None:
        context = normalize_context(event, payload)
        for rule in self.registry["rules"]:
            if event not in rule.get("events", []):
                continue
            module_name = rule["module"]
            if module_name == "builtin:source_intake_enqueue":
                self._enqueue_sources(context)
                continue
            if module_name.startswith("legacy:"):
                try:
                    module = importlib.import_module(module_name.removeprefix("legacy:"))
                except ImportError:
                    continue
                module.check(context)

    @staticmethod
    def _enqueue_sources(context: dict[str, Any]) -> None:
        intake = SourceIntake(Path(context["cwd"]))
        url = context["tool_input"].get("url")
        for raw in context["candidate_paths"]:
            path = Path(raw)
            if path.is_file() and path.suffix.lower() not in {".md", ".html"}:
                intake.enqueue(path, source_url=url)
