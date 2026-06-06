import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest import mock


RUNTIME_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RUNTIME_ROOT))

from buy_side_research_runtime.cli.financial_data import build_parser, infer_market, main, migrate_actuals


class FinancialCliTest(unittest.TestCase):
    def test_fetch_parser_accepts_profile_and_arbitrary_time_range(self):
        args = build_parser().parse_args(
            ["fetch", "ACME", "--profile", "lite", "--from", "FY2018", "--to", "2025-12-31"]
        )

        self.assertEqual("lite", args.profile)
        self.assertEqual("FY2018", args.from_value)
        self.assertEqual("2025-12-31", args.to_value)

    def test_deprecated_periods_option_is_parsed_without_calendar_math(self):
        args = build_parser().parse_args(["fetch", "ACME", "--periods", "3Y"])

        self.assertEqual("3Y", args.periods)
        self.assertIsNone(args.from_value)

    def test_infers_market_from_common_ticker_shapes(self):
        self.assertEqual("jp", infer_market("6278"))
        self.assertEqual("tw", infer_market("2330"))
        self.assertEqual("tw", infer_market("2330.TW"))
        self.assertEqual("hk", infer_market("0522.HK"))
        self.assertEqual("kr", infer_market("064350.KS"))
        self.assertEqual("cn", infer_market("688097.SS"))
        self.assertEqual("us", infer_market("DELL"))

    def test_fetch_from_fresh_workspace_creates_default_company_root(self):
        with tempfile.TemporaryDirectory() as temp:
            captured = {}

            class FakePipeline:
                def __init__(self, company_root, provider):
                    captured["company_root"] = Path(company_root)
                    captured["provider"] = provider

                def fetch(self, request):
                    captured["request"] = request

                    class Result:
                        status = "success"
                        facts_store = "facts-store.json"
                        actuals_view = "actuals-resolved.json"
                        raw_pack = "raw"
                        cache_pack = "cache"
                        selected_periods = ["FY2024"]
                        reason = ""

                    return Result()

            with (
                mock.patch(
                    "buy_side_research_runtime.cli.financial_data.load_provider",
                    return_value=object(),
                ),
                mock.patch(
                    "buy_side_research_runtime.cli.financial_data.FinancialDataPipeline",
                    FakePipeline,
                ),
                redirect_stdout(StringIO()),
            ):
                rc = main(["fetch", "6278", "--profile", "lite", "--workspace", temp])

            self.assertEqual(0, rc)
            self.assertEqual("jp", captured["request"].market)
            self.assertEqual("6278", captured["request"].ticker)
            self.assertEqual(
                Path(temp).resolve() / "industry" / "uncategorized" / "companies" / "6278",
                captured["company_root"],
            )

    def test_migration_backs_up_legacy_actuals_and_generates_read_model(self):
        with tempfile.TemporaryDirectory() as temp:
            company = Path(temp) / "industry" / "test" / "companies" / "acme"
            internal = company / "_cache" / "financial-data" / "internal"
            internal.mkdir(parents=True)
            actuals = internal / "actuals-resolved.json"
            actuals.write_text(
                json.dumps(
                    {
                        "_schema": "actuals-resolved v3.0",
                        "_aliases": {"latest_fy": "FY2024"},
                        "FY2024": {
                            "income_statement": {
                                "revenue": {"value": 100, "source_layer": "official_web"}
                            }
                        },
                        "segments": [{"name": "Core", "revenue": 80}],
                        "market_data": {"as_of": "2025-01-02", "price": 12},
                        "consensus": {"as_of": "2025-01-02", "eps": 2},
                        "source_map": {"S1": {"url": "https://example.com/filing"}},
                    }
                ),
                encoding="utf-8",
            )

            result = migrate_actuals(company)

            self.assertTrue(Path(result["facts_store"]).exists())
            self.assertTrue(Path(result["backup"]).exists())
            view = json.loads(actuals.read_text(encoding="utf-8"))
            self.assertEqual("generated-read-model", view["_write_policy"])
            self.assertEqual("Core", view["segments"][0]["name"])
            self.assertEqual(12, view["market_data"]["price"])
            self.assertEqual(2, view["consensus"]["eps"])
            store = json.loads(Path(result["facts_store"]).read_text(encoding="utf-8"))
            sources = {item["source_id"]: item for item in store["sources"]}
            self.assertEqual("https://example.com/filing", sources["S1"]["url"])


if __name__ == "__main__":
    unittest.main()
