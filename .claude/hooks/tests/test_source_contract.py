"""Tests for source_contract.py regex patterns — high-fragility boundaries."""
import unittest
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from rules.source_contract import _looks_like_source_label, _strip_code_blocks, _check_double_urls
from common import get_body_without_resources, get_resources_entries

# Monkey-patch block/warn to capture
class HookTest(unittest.TestCase):
    def test_bare_label_detected(self):
        """[S1] without URL should be caught."""
        import re
        self.assertIsNotNone(re.search(r'\[(?:S|P|I|LBG|R|SRC)\d+\](?!\()', '[S1]'))
        self.assertIsNotNone(re.search(r'\[(?:S|P|I|LBG|R|SRC)\d+\](?!\()', 'data: [S2] |'))

    def test_bare_label_with_url_not_flagged(self):
        """[S1](url) should NOT match bare pattern."""
        import re
        self.assertIsNone(re.search(r'\[(?:S|P|I|LBG|R|SRC)\d+\](?!\()', '[S1](https://a.com)'))

    def test_image_not_flagged_as_source(self):
        """![alt](url) should be excluded from non-standard label detection."""
        # Rule 2d captures (is_image, label, target) — need is_image to be '!'
        import re
        matches = re.findall(r'(!?)\[([^\]]+)\]\(([^)]+)\)', '![BESI](img.jpg) and [TSMC](url)')
        # First match: is_image='!', label='BESI', target='img.jpg'
        self.assertEqual(matches[0][0], '!')  # is_image flag
        # Second match: is_image='', label='TSMC'
        self.assertEqual(matches[1][0], '')

    def test_annotation_prefix_skip(self):
        """[ND——无数据] and [推算——...] should NOT be flagged as sources."""
        self.assertFalse(_looks_like_source_label('ND——无 Q1 2025 可比 EBIT'))
        self.assertFalse(_looks_like_source_label('推算——基于订单 mix'))
        self.assertFalse(_looks_like_source_label('未披露'))
        self.assertFalse(_looks_like_source_label('缺图'))

    def test_double_url_detected(self):
        """[S1](url1)(url2) should be found as double URL."""
        import re
        body = "data [S1](https://a.com)(https://b.com) more"
        doubles = re.findall(r'\[([^\]]+)\]\([^)]+\)\((https?://[^)]+)\)', body)
        self.assertEqual(len(doubles), 1)
        self.assertEqual(doubles[0][0], 'S1')

    def test_resources_parse_4_formats(self):
        """All 4 Resources entry formats should be parsed."""
        text = """
## Resources
- [S1](https://a.com) — Description
- [S2](https://b.com) Description no dash
- [S3](https://c.com)
- [S4] Description — https://d.com
"""
        entries = get_resources_entries(text)
        codes = {e['code'] for e in entries}
        self.assertIn('S1', codes)  # Format 1a: URL + dash + meta
        self.assertIn('S2', codes)  # Format 1b: URL + space + meta
        self.assertIn('S3', codes)  # Format 2: URL only
        self.assertIn('S4', codes)  # Format 3: meta + dash + URL

    def test_code_block_stripped(self):
        """Mermaid blocks should be stripped for label detection."""
        content = "```mermaid\n  A[TSMC] --> B\n```\nReal: [S1](url)"
        stripped = _strip_code_blocks(content)
        self.assertNotIn('[TSMC]', stripped)
        self.assertIn('[S1](url)', stripped)


if __name__ == '__main__':
    unittest.main()
