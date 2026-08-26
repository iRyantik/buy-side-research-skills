import json
import os
import sys
import tempfile
import time
import types
import unittest
from pathlib import Path
from unittest import mock

from email_intel.cli import review


MINIMAL_REPORT = {
    "items": [],
    "meetings": [],
    "sections": {"industry_signal": [], "core": [], "other_coverage": [], "new_idea": []},
    "stats": {"emails": 1, "signals": 0, "meetings": 0},
}


def _write_email(root: Path, name: str = "e1") -> Path:
    d = root / name
    d.mkdir(parents=True)
    (d / "meta.txt").write_text(
        f"subject: Test {name}\nfrom: research@ubs.com\nmessage_id: {name}\n",
        encoding="utf-8",
    )
    body = d / "body.txt"
    body.write_text("x" * 500, encoding="utf-8")
    old = time.time() - 120
    os.utime(body, (old, old))
    (d / "outlook.link.txt").write_text("https://example.com/e", encoding="utf-8")
    return d


def _fake_delivery(send_results):
    module = types.ModuleType("coverage_monitor.delivery")
    module.send_email = mock.Mock(side_effect=send_results)
    module.workspace_env = lambda workspace, env=None: {
        "SMTP_HOST": "smtp.test", "SMTP_USER": "u@test", "SMTP_PASSWORD": "p",
        "COVERAGE_EMAIL_TO": "t@test",
    }
    sys.modules["coverage_monitor.delivery"] = module
    return module


class CliTests(unittest.TestCase):
    def _run(self, base, ws, *, dry_run=False, send=False, reviews=None):
        reviews = reviews or [{"_email_id": "e1", "items": [], "meetings": [], "status": "ok"}]
        with mock.patch("email_intel.cli.review_batch", return_value=reviews) as rb, \
             mock.patch("email_intel.cli.build_report", return_value=MINIMAL_REPORT):
            return review(str(base), ws, dry_run=dry_run, send=send), rb

    def test_dry_run_does_not_advance_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ws = root / "ws"; ws.mkdir()
            base = root / "inbox"
            _write_email(base)
            rc, _ = self._run(base, ws, dry_run=True)
            self.assertEqual(rc, 0)
            state_path = ws / ".cache" / "email-intelligence" / "state.json"
            self.assertFalse(state_path.exists())
            self.assertTrue(list((ws / "daily" / "email").glob("*-email-brief.html")))

    def test_failed_review_is_not_marked_seen(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ws = root / "ws"; ws.mkdir()
            base = root / "inbox"
            _write_email(base)
            rc, _ = self._run(base, ws, reviews=[
                {"_email_id": "e1", "items": [], "meetings": [],
                 "status": "failed", "filter_reason": "extract_failed"},
            ])
            self.assertEqual(rc, 0)
            state = json.loads((ws / ".cache" / "email-intelligence" / "state.json").read_text(encoding="utf-8"))
            self.assertEqual(state.get("seen"), [])

    def test_successful_review_is_marked_seen(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ws = root / "ws"; ws.mkdir()
            base = root / "inbox"
            _write_email(base)
            rc, _ = self._run(base, ws)
            self.assertEqual(rc, 0)
            state = json.loads((ws / ".cache" / "email-intelligence" / "state.json").read_text(encoding="utf-8"))
            self.assertEqual(state.get("seen"), ["e1"])
            self.assertEqual(state.get("last_run", "")[:10], "2026-08-26")

    def test_delivery_failure_goes_to_outbox_and_retries(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ws = root / "ws"; ws.mkdir()
            base = root / "inbox"
            _write_email(base)
            fake = _fake_delivery([["smtp_error"], []])
            rc, _ = self._run(base, ws, send=True)
            self.assertEqual(rc, 3)
            outbox = ws / ".cache" / "email-intelligence" / "outbox"
            pending = list(outbox.glob("*.json"))
            self.assertEqual(len(pending), 1)
            state = json.loads((ws / ".cache" / "email-intelligence" / "state.json").read_text(encoding="utf-8"))
            self.assertEqual(state.get("seen"), ["e1"])

            # 第二次运行：无新邮件，只重试 outbox
            rc2, _ = self._run(base, ws, send=True)
            self.assertEqual(rc2, 0)
            self.assertEqual(list(outbox.glob("*.json")), [])
            state2 = json.loads((ws / ".cache" / "email-intelligence" / "state.json").read_text(encoding="utf-8"))
            self.assertIn("last_sent", state2)
            self.assertEqual(fake.send_email.call_count, 2)
