"""Incremental email-review state (atomic writes, recency-capped seen list)."""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path


_SEEN_CAP = 20_000


def state_path(workspace: Path) -> Path:
    path = workspace / ".cache" / "email-intelligence" / "state.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def load_state(workspace: Path) -> dict:
    try:
        return json.loads(state_path(workspace).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {"seen": [], "last_run": "", "last_sent": "", "events": {}}
    except (OSError, json.JSONDecodeError) as exc:
        # 损坏的 state 不能静默当全新状态继续（可能重扫旧邮件），先备份再重建。
        corrupt = state_path(workspace)
        try:
            backup = corrupt.with_name(
                f"state.corrupt-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json.bak"
            )
            corrupt.replace(backup)
            print(f"[email-intel] state 损坏已备份到 {backup}: {exc.__class__.__name__}", file=sys.stderr)
        except OSError:
            pass
        return {"seen": [], "last_run": "", "last_sent": "", "events": {}}


def save_state(workspace: Path, state: dict) -> None:
    target = state_path(workspace)
    temp = target.with_name(target.name + ".tmp")
    temp.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temp, target)


def mark_seen(state: dict, keys: list[str]) -> None:
    # 保持插入顺序，按“最近处理”截断；旧的按字典序截断会随机丢掉任意邮件。
    seen = list(dict.fromkeys([*(state.get("seen") or []), *keys]))
    state["seen"] = seen[-_SEEN_CAP:]


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
    # merge_key 在信号（items[]）级，不在邮件级——双层遍历才能建跨天基线
    for r in reviews:
        for item in r.get("items") or []:
            key = item.get("merge_key")
            if not key:
                continue
            ev = events.get(key, {})
            seen_days = ev.get("last_seen", "")[:10]
            today = now_label[:10]
            # company/event_type 兜底链：item 级 → 邮件级 → 既有值（AI 偶漏 item.company）
            ev["company"] = item.get("company") or r.get("company") or ev.get("company") or ""
            ev["event_type"] = item.get("event_type") or ev.get("event_type") or ""
            if item.get("delta_vs_last"):
                ev["what_changed"] = item["delta_vs_last"]  # 最新增量作为新基线
            elif item.get("what_changed") and seen_days != today:
                ev["what_changed"] = item["what_changed"]
            ev["brokers"] = sorted(set(ev.get("brokers", [])) | {str(r.get("_email_id") or "")})
            ev.setdefault("first_seen", now_label)
            ev["last_seen"] = now_label
            events[key] = ev
