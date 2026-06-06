import json
import sys
import tempfile
import unittest
from pathlib import Path


RUNTIME_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RUNTIME_ROOT))

from buy_side_research_runtime.financial_data import (
    FactCandidate,
    FactsRepository,
    LegacyMigrator,
    Period,
    resolve_period_ids,
)


class FactsRepositoryTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "_cache" / "financial-data" / "internal"
        self.repo = FactsRepository(self.root, entity={"ticker": "ACME", "currency": "USD"})
        self.repo.upsert_period(Period("FY2024", "FY2024", "2024-12-31", "annual"))
        self.repo.upsert_period(Period("Q1-2025", "Q1 2025", "2025-03-31", "interim"))

    def tearDown(self):
        self.temp.cleanup()

    def test_lower_trust_fact_does_not_overwrite_and_conflict_is_retained(self):
        self.repo.merge(
            [
                FactCandidate(
                    "income_statement.revenue",
                    "FY2024",
                    100,
                    "USD",
                    "USD",
                    {},
                    "official-1",
                    "official_web",
                    "disclosed",
                    1.0,
                )
            ]
        )
        self.repo.merge(
            [
                FactCandidate(
                    "income_statement.revenue",
                    "FY2024",
                    90,
                    "USD",
                    "USD",
                    {},
                    "provider-1",
                    "provider_api",
                    "disclosed",
                    0.8,
                )
            ]
        )

        store = self.repo.load()
        self.assertEqual(100, store["facts"][0]["value"])
        self.assertEqual(1, len(store["quality"]["conflicts"]))

    def test_market_snapshot_is_separate_and_read_model_merges_latest(self):
        self.repo.merge(
            [
                FactCandidate(
                    "income_statement.revenue",
                    "FY2024",
                    100,
                    "USD",
                    "USD",
                    {},
                    "official-1",
                    "official_web",
                    "disclosed",
                    1.0,
                )
            ]
        )
        self.repo.append_snapshot("market", {"as_of": "2026-06-06", "price": 12.5})

        view = self.repo.render_actuals()

        self.assertEqual(100, view["income_statement"]["latest_fy"]["revenue"]["value"])
        self.assertEqual(12.5, view["market_data"]["price"])
        self.assertEqual("2026-06-06", view["market_data"]["as_of"])
        self.assertEqual("generated-read-model", view["_write_policy"])
        self.assertTrue((self.root / "market-snapshots.jsonl").exists())

    def test_commit_writes_canonical_store_not_dynamic_period_keys(self):
        self.repo.merge([])
        self.repo.commit()

        store = json.loads((self.root / "facts-store.json").read_text(encoding="utf-8"))

        self.assertEqual(1, store["schema_version"])
        self.assertIn("periods", store)
        self.assertIn("facts", store)
        self.assertNotIn("FY2024", store)


class PeriodSelectionTest(unittest.TestCase):
    def setUp(self):
        self.periods = [
            Period(f"FY{year}", f"FY{year}", f"{year}-12-31", "annual")
            for year in range(2018, 2026)
        ]
        self.periods.append(Period("Q1-2026", "Q1 2026", "2026-03-31", "interim"))

    def test_lite_accepts_arbitrary_explicit_range(self):
        selected = resolve_period_ids(self.periods, "lite", "FY2019", "FY2022")
        self.assertEqual(["FY2019", "FY2020", "FY2021", "FY2022"], selected)

    def test_default_lite_and_full_windows(self):
        lite = resolve_period_ids(self.periods, "lite", None, None)
        full = resolve_period_ids(self.periods, "full", None, None)

        self.assertEqual(["FY2025", "Q1-2026"], lite)
        self.assertEqual(["FY2021", "FY2022", "FY2023", "FY2024", "FY2025", "Q1-2026"], full)

    def test_deprecated_three_year_window_uses_available_complete_fy_not_calendar_year(self):
        selected = resolve_period_ids(
            self.periods, "lite", None, None, complete_years=3
        )

        self.assertEqual(["FY2023", "FY2024", "FY2025", "Q1-2026"], selected)


class LegacyMigratorTest(unittest.TestCase):
    def test_migrates_v2_dynamic_v3_and_full_v1_shapes(self):
        samples = [
            {
                "_schema": "actuals-resolved v2.2",
                "latest_fy_period": "FY2024",
                "income_statement": {
                    "latest_fy": {
                        "revenue": {"value": 100, "source_layer": "official_web"}
                    }
                },
            },
            {
                "_schema": "actuals-resolved v3.0",
                "_aliases": {"latest_fy": "FY2024"},
                "FY2024": {
                    "income_statement": {
                        "revenue": {"value": 100, "source_layer": "official_web"}
                    }
                },
            },
            {
                "schema_version": 1,
                "statements": {
                    "income_statement": [
                        {"concept": "revenue", "values": {"FY2024": 100}}
                    ]
                },
                "source_map": {"source_provider": "provider_api"},
            },
            {
                "_schema": "hybrid",
                "_aliases": {"latest_fy": "FY2024"},
                "latest_fy_period": "FY2024",
                "income_statement": {
                    "latest_fy": {
                        "revenue": {"value": 100, "source_layer": "official_web"}
                    }
                },
                "FY2024": {"income_statement": {"net_income": {"value": 10}}},
            },
        ]

        for sample in samples:
            with self.subTest(keys=list(sample)):
                result = LegacyMigrator().convert(sample, {"ticker": "ACME"})
                metrics = {fact.metric for fact in result.facts}
                self.assertIn("income_statement.revenue", metrics)
                self.assertTrue(result.periods)


if __name__ == "__main__":
    unittest.main()
