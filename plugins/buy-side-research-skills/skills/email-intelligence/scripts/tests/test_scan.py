import os
import tempfile
import time
import unittest
from pathlib import Path

from email_intel.parse import scan_email_dirs


def _write_email(root: Path, name: str, body: str = "body", age_seconds: int = 120) -> Path:
    d = root / name
    d.mkdir(parents=True)
    (d / "meta.txt").write_text(
        f"subject: Test {name}\nfrom: research@ubs.com\nmessage_id: {name}\n",
        encoding="utf-8",
    )
    body_path = d / "body.txt"
    body_path.write_text(body, encoding="utf-8")
    old = time.time() - age_seconds
    os.utime(body_path, (old, old))
    (d / "outlook.link.txt").write_text("https://example.com/e", encoding="utf-8")
    return d


class ScanTests(unittest.TestCase):
    def test_recent_body_is_marked_unstable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_email(root, "e1", age_seconds=1)
            emails = scan_email_dirs(root)
            self.assertEqual(len(emails), 1)
            self.assertFalse(emails[0].parse_ok)
            self.assertIn("being written", emails[0].parse_error)

    def test_missing_body_is_marked_unstable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d = root / "e1"
            d.mkdir()
            (d / "meta.txt").write_text("subject: T\nfrom: research@ubs.com\nmessage_id: e1\n", encoding="utf-8")
            emails = scan_email_dirs(root)
            self.assertEqual(len(emails), 1)
            self.assertFalse(emails[0].parse_ok)
            self.assertIn("missing or empty body.txt", emails[0].parse_error)

    def test_stable_email_is_ready(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_email(root, "e1", body="x" * 500)
            emails = scan_email_dirs(root)
            self.assertEqual(len(emails), 1)
            self.assertTrue(emails[0].parse_ok)
            self.assertGreaterEqual(len(emails[0].body_text), 500)
