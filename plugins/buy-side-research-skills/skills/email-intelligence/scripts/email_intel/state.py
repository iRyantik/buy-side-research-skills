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
        return {"seen": [], "last_run": "", "last_sent": "", "events": {}}


def save_state(workspace: Path, state: dict) -> None:
    state_path(workspace).write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def mark_seen(state: dict, keys: list[str]) -> None:
    seen = set(state.get("seen", []))
    seen.update(key for key in keys if key)
    state["seen"] = sorted(seen)[-5_000:]


def last_events(state: dict, max_events: int = 200) -> dict:
    """跨天追踪基线：{merge_key: {company, event_type, what_changed}}——供 AI 判断增量。"""
    out = {}
    for key, ev in (state.get("events", {}) or {}).items():
        out[key] = {
            "company": ev.get("company"),
            "event_type": ev.get("event_type"),
            "what_changed": ev.get("what_changed"),
        }
        if len(out) >= max_events:
            break
    return out


def update_events(state: dict, reviews: list[dict], now_label: str) -> None:
    """按 merge_key 累积事件：记录 first/last_seen、brokers、最新 what_changed。"""
    events = state.setdefault("events", {})
    for r in reviews:
        key = r.get("merge_key")
        if not key:
            continue
        ev = events.get(key, {})
        seen_days = ev.get("last_seen", "")[:10]
        today = now_label[:10]
        ev["company"] = r.get("company") or ev.get("company")
        ev["event_type"] = r.get("event_type") or ev.get("event_type")
        if r.get("delta_vs_last"):
            ev["what_changed"] = r["delta_vs_last"]  # 最新增量作为新基线
        elif r.get("what_changed") and seen_days != today:
            ev["what_changed"] = r["what_changed"]
        ev["brokers"] = sorted(set(ev.get("brokers", [])) | {str(r.get("_email_id") or "")})
        ev.setdefault("first_seen", now_label)
        ev["last_seen"] = now_label
        events[key] = ev
