from __future__ import annotations

from hashlib import sha1
import json
from pathlib import Path


DEFAULT_STATE = {
    "last_daily_report_date": "",
    "sent_event_ids": [],
    "last_intraday_run_at": "",
}


def state_path(workspace: Path) -> Path:
    return workspace / ".cache" / "coverage-monitor" / "state.json"


def load_state(workspace: Path) -> dict:
    path = state_path(workspace)
    if not path.exists():
        return dict(DEFAULT_STATE)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return dict(DEFAULT_STATE)
    merged = dict(DEFAULT_STATE)
    merged.update({key: value for key, value in data.items() if key in DEFAULT_STATE})
    return merged


def save_state(workspace: Path, state: dict) -> Path:
    path = state_path(workspace)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = dict(DEFAULT_STATE)
    payload.update(state)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def build_event_id(ticker: str, event_type: str, event_marker: str) -> str:
    digest = sha1(event_marker.encode("utf-8")).hexdigest()[:12]
    return f"{ticker}|{event_type}|{digest}"
