import unittest

from email_intel.identity import company_key, industry_key, industry_label, normalize_ticker


class IdentityTests(unittest.TestCase):
    def test_normalize_ticker_aliases_to_fmp_suffix(self):
        self.assertEqual(normalize_ticker("300316.CH"), "300316.SZ")
        self.assertEqual(normalize_ticker("603011.CH"), "603011.SS")
        self.assertEqual(normalize_ticker("6525.JP"), "6525.T")
        self.assertEqual(normalize_ticker("BA.LN"), "BA.L")
        self.assertEqual(normalize_ticker("HO.FP"), "HO.PA")
        self.assertEqual(normalize_ticker("KOG.NO"), "KOG.OL")
        self.assertEqual(normalize_ticker("603011.SH"), "603011.SS")

    def test_normalize_ticker_keeps_canonical_and_bare(self):
        self.assertEqual(normalize_ticker("300316.SZ"), "300316.SZ")
        self.assertEqual(normalize_ticker("HWM"), "HWM")
        self.assertEqual(normalize_ticker(" 603011.SS "), "603011.SS")
        self.assertEqual(normalize_ticker(""), "")

    def test_industry_keys_ignore_space_and_hyphen(self):
        self.assertEqual(
            industry_key("Semiconductor Equipment"),
            industry_key("Semiconductor-Equipment"),
        )

    def test_industry_label_prefers_coverage_spelling(self):
        self.assertEqual(
            industry_label("Semiconductor-Equipment", ["Semiconductor Equipment"]),
            "Semiconductor Equipment",
        )
        self.assertEqual(
            industry_label("Semiconductor Equipment", ["Semiconductor-Equipment"]),
            "Semiconductor-Equipment",
        )

    def test_company_key_normalizes_case_and_space(self):
        self.assertEqual(company_key("  Melrose Industries  "), company_key("melrose industries"))
