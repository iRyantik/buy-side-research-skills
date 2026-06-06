import json
import sys
import tempfile
import unittest
from pathlib import Path


RUNTIME_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RUNTIME_ROOT))

from buy_side_research_runtime.financial_data.pipeline import FinancialDataPipeline, FinancialRequest


class FakeProvider:
    name = "fake-provider"

    def fetch(self, request):
        return {
            "status": "success",
            "provider": self.name,
            "company": {"ticker": request["ticker"], "currency": "USD"},
            "income_statement": [
                {
                    "concept": "Revenue",
                    "label": "Revenue",
                    "values": {
                        "FY2020": 80,
                        "FY2021": 90,
                        "FY2022": 100,
                        "FY2023": 110,
                        "FY2024": 120,
                        "FY2025": 130,
                    },
                }
            ],
            "market_data": {"as_of": "2026-06-06", "price": 25},
        }


class UnicodeProvider:
    name = "unicode-provider"

    def fetch(self, request):
        return {
            "status": "success",
            "provider": self.name,
            "company": {"ticker": request["ticker"], "currency": "KRW"},
            "income_statement": [
                {"label": "영업손익", "values": {"FY2024": 10}},
                {"label": "营业额", "values": {"FY2024": 100}},
            ],
            "balance_sheet": [
                {"label": "자산총계", "values": {"FY2024": 500}},
                {"label": "现金及现金等价物", "values": {"FY2024": 50}},
            ],
        }


class UnmappableProvider:
    name = "unmappable-provider"

    def fetch(self, request):
        return {
            "status": "success",
            "provider": self.name,
            "company": {"ticker": request["ticker"], "currency": "USD"},
            "income_statement": [
                {"label": "non standard operating label", "values": {"FY2024": 1}},
            ],
        }


class FinancialDataPipelineTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.company = Path(self.temp.name) / "industry" / "test" / "companies" / "acme"
        self.company.mkdir(parents=True)
        self.pipeline = FinancialDataPipeline(self.company, FakeProvider())

    def tearDown(self):
        self.temp.cleanup()

    def test_lite_explicit_range_is_independent_from_profile(self):
        result = self.pipeline.fetch(
            FinancialRequest("ACME", "us", "lite", "FY2020", "FY2023")
        )

        store = json.loads(Path(result.facts_store).read_text(encoding="utf-8"))
        self.assertEqual(["FY2020", "FY2021", "FY2022", "FY2023"], [p["period_id"] for p in store["periods"]])
        self.assertEqual(4, len(store["facts"]))

    def test_full_default_uses_five_fy_and_writes_evidence_pack(self):
        result = self.pipeline.fetch(FinancialRequest("ACME", "us", "full"))

        store = json.loads(Path(result.facts_store).read_text(encoding="utf-8"))
        self.assertEqual(["FY2021", "FY2022", "FY2023", "FY2024", "FY2025"], [p["period_id"] for p in store["periods"]])
        self.assertTrue(Path(result.raw_pack).joinpath("provider-payload.json").exists())
        manifest = json.loads(Path(result.cache_pack).joinpath("run-manifest.json").read_text(encoding="utf-8"))
        self.assertEqual("full", manifest["profile"])
        self.assertEqual("fake-provider", manifest["provider"])

    def test_pipeline_generates_read_model_but_provider_never_writes_it(self):
        result = self.pipeline.fetch(FinancialRequest("ACME", "us", "lite"))

        view = json.loads(Path(result.actuals_view).read_text(encoding="utf-8"))
        self.assertEqual("generated-read-model", view["_write_policy"])
        self.assertEqual(130, view["income_statement"]["latest_fy"]["revenue"]["value"])

    def test_unicode_provider_labels_map_to_canonical_facts(self):
        result = FinancialDataPipeline(self.company, UnicodeProvider()).fetch(
            FinancialRequest("ACME", "kr", "lite")
        )

        store = json.loads(Path(result.facts_store).read_text(encoding="utf-8"))
        metrics = {fact["metric"] for fact in store["facts"]}
        self.assertIn("income_statement.operating_income", metrics)
        self.assertIn("income_statement.revenue", metrics)
        self.assertIn("balance_sheet.total_assets", metrics)
        self.assertIn("balance_sheet.cash", metrics)

    def test_unmappable_provider_returns_explicit_no_canonical_facts(self):
        result = FinancialDataPipeline(self.company, UnmappableProvider()).fetch(
            FinancialRequest("ACME", "hk", "lite")
        )

        manifest = json.loads(Path(result.cache_pack).joinpath("run-manifest.json").read_text(encoding="utf-8"))
        self.assertEqual("no-canonical-facts", result.status)
        self.assertEqual("no-canonical-facts", manifest["canonical_status"])
        self.assertIn("no mappable canonical facts", result.reason)
        self.assertFalse(Path(result.actuals_view).exists())


if __name__ == "__main__":
    unittest.main()
