import unittest

from email_intel.brief import render_brief_html
from email_intel.parse import Email


class BriefTests(unittest.TestCase):
    def test_brief_has_five_light_sections_and_multiple_meetings(self):
        email = Email(folder="e1", path="/tmp/e1", sender="Broker", outlook_link="https://example.com/e1")
        reviews = [{
        "_email_id": "e1",
        "items": [
            {"bucket": "core", "company": "CoreCo", "what_changed": "guidance up", "priority": "high"},
            {"bucket": "other_coverage", "company": "WatchCo", "what_changed": "margin down", "priority": "medium"},
            {"bucket": "new_idea", "company": "NewCo", "what_changed": "orders inflect", "priority": "high"},
            {"bucket": "industry_signal", "industry": "Defense", "what_changed": "budget expands", "priority": "medium"},
        ],
        "meetings": [
            {"title": "Company A meeting", "topic": "Demand", "recommendation": "high"},
            {"title": "Company B meeting", "topic": "Supply", "recommendation": "low"},
        ],
        }]
        output = render_brief_html([email], reviews, "2026-08-24")
        for heading in ("Core Watch", "Other Coverage", "New Ideas", "Industry &amp; Sell-side Signals", "Meetings"):
            self.assertIn(heading, output)
        self.assertIn("Company A meeting", output)
        self.assertIn("Company B meeting", output)
        self.assertIn("https://example.com/e1", output)
