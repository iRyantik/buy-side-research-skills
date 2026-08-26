import unittest

from email_intel.classify import classify_item, normalize_reviews


CONTEXT = {
    "coverage": [
        {"ticker": "HWM.US", "company_en": "Howmet", "company_native": "Howmet", "industry": "Aerospace", "coverage": "Modeled", "monitor": "Core", "is_core": True},
        {"ticker": "RHM.DE", "company_en": "Rheinmetall", "company_native": "Rheinmetall", "industry": "Defense", "coverage": "Screened", "monitor": "Daily", "is_core": False},
    ],
    "covered_industries": ["Aerospace", "Defense"],
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
        self.assertEqual(classify_item(candidate | {"event_type": "initiation", "industry": "Aerospace"}, CONTEXT), "industry_signal")
        self.assertEqual(classify_item(candidate | {"focus_fit": "weak", "industry": "Cloud/AI"}, CONTEXT), "filtered")

    def test_focus_only_noncoverage_does_not_fall_into_industry(self):
        item = {
            "kind": "company_update", "event_type": "initiation", "company": "Alibaba",
            "ticker": "9988.HK", "industry": "Cloud/AI", "focus_fit": "strong",
            "what_changed": "AI infrastructure update", "action": "watch",
        }
        self.assertEqual(classify_item(item, CONTEXT), "filtered")

    def test_covered_industry_and_explicit_coverage_readthrough_are_kept(self):
        self.assertEqual(classify_item({"company": "Melrose", "industry": "Aerospace"}, CONTEXT), "industry_signal")
        self.assertEqual(classify_item({
            "company": "SupplierCo", "industry": "Cloud/AI", "related_tickers": ["HWM.US"]
        }, CONTEXT), "industry_signal")


    def test_normalize_keeps_multiple_items_and_meetings(self):
        reviews = [{"_email_id": "e1", "items": [{"ticker": "HWM.US"}, {"ticker": "RHM.DE"}], "meetings": [{"title": "A"}, {"title": "B"}]}]
        normalized = normalize_reviews(reviews, CONTEXT)
        self.assertEqual([item["bucket"] for item in normalized[0]["items"]], ["core", "other_coverage"])
        self.assertEqual(len(normalized[0]["meetings"]), 2)

    def test_normalize_drops_filtered_items(self):
        reviews = [{"_email_id": "e1", "items": [{
            "company": "Alibaba", "industry": "Cloud/AI", "event_type": "initiation",
            "focus_fit": "strong", "what_changed": "AI update", "action": "watch",
        }], "meetings": []}]
        normalized = normalize_reviews(reviews, CONTEXT)
        self.assertEqual(normalized[0]["items"], [])
