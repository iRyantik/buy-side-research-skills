import unittest

from email_intel.classify import classify_item, normalize_reviews


CONTEXT = {
    "coverage": [
        {"ticker": "HWM.US", "company_en": "Howmet", "company_native": "Howmet", "industry": "Aerospace", "coverage": "Modeled", "monitor": "Core", "is_core": True},
        {"ticker": "RHM.DE", "company_en": "Rheinmetall", "company_native": "Rheinmetall", "industry": "Defense", "coverage": "Screened", "monitor": "Daily", "is_core": False},
    ]
}


class ClassifyTests(unittest.TestCase):
    def test_coverage_routing_is_deterministic(self):
        self.assertEqual(classify_item({"ticker": "HWM.US"}, CONTEXT), "core")
        self.assertEqual(classify_item({"company": "Rheinmetall"}, CONTEXT), "other_coverage")


    def test_new_idea_requires_change_focus_and_action_not_initiation(self):
        candidate = {
            "kind": "company_update", "event_type": "earnings", "company": "NewCo",
            "what_changed": "订单增速转正", "focus_fit": "moderate", "action": "research",
        }
        self.assertEqual(classify_item(candidate, CONTEXT), "new_idea")
        self.assertEqual(classify_item(candidate | {"event_type": "initiation"}, CONTEXT), "industry_signal")
        self.assertEqual(classify_item(candidate | {"focus_fit": "weak"}, CONTEXT), "industry_signal")


    def test_normalize_keeps_multiple_items_and_meetings(self):
        reviews = [{"_email_id": "e1", "items": [{"ticker": "HWM.US"}, {"ticker": "RHM.DE"}], "meetings": [{"title": "A"}, {"title": "B"}]}]
        normalized = normalize_reviews(reviews, CONTEXT)
        self.assertEqual([item["bucket"] for item in normalized[0]["items"]], ["core", "other_coverage"])
        self.assertEqual(len(normalized[0]["meetings"]), 2)
