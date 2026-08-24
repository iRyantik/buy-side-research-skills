import tempfile
import unittest
from pathlib import Path

from email_intel.context import build_context, load_coverage


class ContextTests(unittest.TestCase):
    def test_load_coverage_supports_status_and_core(self):
        tmp_path = Path(tempfile.mkdtemp())
        (tmp_path / "COVERAGE.md").write_text(
        """# Coverage Map

## Coverage

| Ticker | Company (EN) | Company (Native) | Industry | Status | Monitor |
|---|---|---|---|---|---|
| HWM.US | Howmet | Howmet | Aerospace | Quickread | Core |
| RHM.DE | Rheinmetall | Rheinmetall | Defense | Screened | Daily |
""",
            encoding="utf-8",
        )
        rows = load_coverage(tmp_path)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0].ticker, "HWM.US")
        self.assertEqual(rows[0].coverage, "Quickread")
        self.assertTrue(rows[0].is_core)


    def test_build_context_reads_focus(self):
        tmp_path = Path(tempfile.mkdtemp())
        (tmp_path / "COVERAGE.md").write_text(
            "## Focus\n## Current Lens\n- More interested in: non-AI\n\n"
            "## Coverage\n| Ticker | Company (EN) | Industry | Coverage | Monitor |\n"
            "|---|---|---|---|---|\n| HWM.US | Howmet | Aerospace | Building | Core |\n",
            encoding="utf-8",
        )
        context = build_context(tmp_path)
        self.assertEqual(context["covered_industries"], ["Aerospace"])
        self.assertIn("non-AI", context["focus"])
