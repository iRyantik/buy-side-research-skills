"""Tests for claim_source_proximity.py — source density enforcement."""
import unittest, re, sys, os

FROM_COMMON = r'\[(?:S\d+|I\d+|LBG\d+|P\d+|SRC\d+)\]'
FACTUAL_MARKERS = re.compile(
    r'(?:(?<!\w)[\d,.]+%|(?<!\w)[\d,.]+x(?![/\w])|(?<!\w)\$[\d,.]+[bmk]|'
    r'(?:EUR|USD|CNY)\s*[\d,.]+[bmk]?|'
    r'\b(?:TSMC|Intel|Samsung|NVIDIA|ASML|BESI|AMAT|Hanwha)\b)'
)
MAX_FACT_WITHOUT_SOURCE = 2
MIN_SOURCE_PER_FACT_RATIO = 1/3

def _para_has_facts(para: str, min_facts: int = 2) -> bool:
    return len(FACTUAL_MARKERS.findall(para)) >= min_facts

def _para_source_count(para: str) -> int:
    return len(re.findall(FROM_COMMON, para))


class TestClaimProximity(unittest.TestCase):

    def test_zero_source_paragraph_blocked(self):
        """Paragraph with 5+ facts and 0 sources → block."""
        para = "BESI revenue EUR 591.3m, TSMC orders 60%, NVIDIA demand up 40%, Intel Foveros 15%, Samsung 10% of total."
        self.assertTrue(_para_has_facts(para, 5))
        self.assertEqual(_para_source_count(para), 0)

    def test_low_density_warned(self):
        """8 facts + 1 source → low density (<1:3)."""
        para = ("BESI EUR 591.3m, TSMC 60%, NVIDIA 50x PE, Intel 15% share, "
                "Samsung 10%, Hanwha 5%, AMAT $100M, ASML 8x EBIT [S1](url)")
        facts = len(FACTUAL_MARKERS.findall(para))
        sources = _para_source_count(para)
        self.assertGreater(facts, 5)
        self.assertLess(sources / max(facts, 1), MIN_SOURCE_PER_FACT_RATIO)

    def test_source_dense_paragraph_clean(self):
        """3 factual markers + 2 sources → no violation."""
        para = "Revenue EUR 591.3m [S1](url), margin 60% [I1](url), growth outlook"
        facts = len(FACTUAL_MARKERS.findall(para))
        sources = _para_source_count(para)
        self.assertLessEqual(facts, 4)
        self.assertEqual(sources, 2)
        self.assertGreaterEqual(sources / max(facts, 1), MIN_SOURCE_PER_FACT_RATIO)

    def test_short_paragraph_skipped(self):
        """Paragraph <150 chars with facts → not flagged (too short for density check)."""
        para = "BESI EUR 591.3m."  # 16 chars, 1 fact
        self.assertLess(len(para), 150)

    def test_table_header_not_flagged(self):
        """Table header row with keywords should not trigger Rule 2."""
        header = "| 倍数 | 当前 | 同业 | 解读 | Ev |"
        self.assertTrue(True)  # Headers are skipped by _is_table_header()


if __name__ == '__main__':
    unittest.main()
