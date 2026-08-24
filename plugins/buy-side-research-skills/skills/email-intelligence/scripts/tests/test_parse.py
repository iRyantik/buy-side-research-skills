import unittest

from email_intel.parse import parse_meta


class ParseTests(unittest.TestCase):
    def test_parse_meta_keeps_colons_in_values(self):
        parsed = parse_meta("SUBJECT: Update: Q2\nFROM: analyst@example.com\nRECEIVED_AT: 2026-08-24T09:30:00Z")
        self.assertEqual(parsed["subject"], "Update: Q2")
        self.assertEqual(parsed["sender"], "analyst@example.com")
        self.assertTrue(parsed["received_at"].endswith("Z"))
