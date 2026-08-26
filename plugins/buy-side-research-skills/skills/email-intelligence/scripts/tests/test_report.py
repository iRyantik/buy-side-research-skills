import unittest

from email_intel.report import _prune_readthrough


class PruneReadthroughTests(unittest.TestCase):
    def test_prunes_other_company_benefit_clause_on_company_card(self):
        item = {"company": "韩华海洋", "bucket": "core"}
        text = ("UBS纪要指出，FPSO供给紧张下韩华海洋有望成为新的一级供应商，"
                "为纽威股份提供下一增长点；2026年行业约6个新FPSO订单多授予SBM，"
                "相关阀门采购可能于2026年底启动。")
        others = {"纽威股份", "SBM"}
        out = _prune_readthrough(text, item, others)
        self.assertEqual(out, "UBS纪要指出，FPSO供给紧张下韩华海洋有望成为新的一级供应商")

    def test_keeps_industry_signal_full(self):
        item = {"company": "纽威股份", "bucket": "industry_signal"}
        text = "为纽威股份提供下一增长点；2026年行业约6个新FPSO订单多授予SBM。"
        self.assertEqual(_prune_readthrough(text, item, {"纽威股份"}), text)

    def test_keeps_when_beneficiary_is_primary(self):
        item = {"company": "纽威股份", "bucket": "core"}
        text = "FPSO供给紧张下，韩华海洋有望成为新一级供应商，为纽威股份提供下一增长点。"
        self.assertEqual(_prune_readthrough(text, item, {"纽威股份"}), text)
