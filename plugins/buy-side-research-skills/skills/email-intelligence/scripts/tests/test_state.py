import json
import tempfile
import unittest
from pathlib import Path

from email_intel.state import load_state, mark_seen, save_state, update_events


class StateTests(unittest.TestCase):
    def test_mark_seen_preserves_recent_order_and_caps(self):
        state = {"seen": []}
        mark_seen(state, ["a", "b", "c"])
        self.assertEqual(state["seen"], ["a", "b", "c"])
        mark_seen(state, ["c", "d"])
        self.assertEqual(state["seen"], ["a", "b", "c", "d"])

    def test_update_events_handles_empty_reviews(self):
        state = {"events": {}}
        update_events(state, [{"_email_id": "e1", "items": []}], "2026-08-26 09:30 (+08:00)")
        self.assertEqual(state["events"], {})

    def test_update_events_records_item_without_crash(self):
        state = {"events": {}}
        update_events(
            state,
            [{"_email_id": "e1", "items": [{"merge_key": "k1", "company": "Co", "what_changed": "x"}]}],
            "2026-08-26 09:30 (+08:00)",
        )
        self.assertEqual(state["events"]["k1"]["last_seen"], "2026-08-26 09:30 (+08:00)")

    def test_save_state_is_atomic(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp) / "ws"
            ws.mkdir()
            save_state(ws, {"seen": ["a"], "last_run": "x"})
            state = load_state(ws)
            self.assertEqual(state["seen"], ["a"])
            tmp_path = ws / ".cache" / "email-intelligence" / "state.json.tmp"
            self.assertFalse(tmp_path.exists())

    def test_corrupt_state_is_backed_up(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp) / "ws"
            target = ws / ".cache" / "email-intelligence" / "state.json"
            target.parent.mkdir(parents=True)
            target.write_text("{not json", encoding="utf-8")
            state = load_state(ws)
            self.assertEqual(state.get("seen"), [])
            backups = list(target.parent.glob("state.corrupt-*.json.bak"))
            self.assertEqual(len(backups), 1)
            self.assertEqual(backups[0].read_text(encoding="utf-8"), "{not json")
