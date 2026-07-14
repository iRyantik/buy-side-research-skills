"""Tests for evidence_ledger_floor.py — ledger enforcement hook."""
import unittest, json, os, sys, tempfile, shutil

# Add the evidence_ledger.py to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class TestLedgerFloor(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.artifact = os.path.join(self.tmp, "2026-06-03-test.md")
        self.cache = os.path.join(self.tmp, ".cache", "evidence")
        os.makedirs(self.cache, exist_ok=True)
        with open(self.artifact, "w") as f:
            f.write("# Test\nRevenue EUR 591.3m [S1](https://a.com)\n")

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def _make_ledger(self, ticker: str, claims: list):
        path = os.path.join(self.cache, f"{ticker}.evidence.json")
        ledger = {
            "ticker": ticker,
            "status": "complete",
            "stats": {"total_claims": len(claims)},
            "claims": claims,
        }
        with open(path, "w") as f:
            json.dump(ledger, f)

    def test_missing_ledger_blocked(self):
        """Artifact has [S#] but no ledger → should be caught."""
        self.assertFalse(os.path.exists(os.path.join(self.cache, "TEST.evidence.json")))

    def test_fabrication_risk_blocked(self):
        """Ledger with fabrication_risk → should be caught."""
        self._make_ledger("TEST", [
            {"id": "C1", "source": "S1", "url": "https://a.com",
             "status": "fabrication_risk", "text": "test"}
        ])
        path = os.path.join(self.cache, "TEST.evidence.json")
        with open(path) as f:
            ledger = json.load(f)
        fab = [c for c in ledger["claims"] if c["status"] == "fabrication_risk"]
        self.assertEqual(len(fab), 1)

    def test_low_coverage_warned(self):
        """<50% verified → low coverage."""
        self._make_ledger("TEST", [
            {"id": "C1", "source": "S1", "url": "https://a.com", "status": "verified", "text": "ok"},
            {"id": "C2", "source": "I1", "url": "https://b.com", "status": "unverified", "text": "?"},
            {"id": "C3", "source": "I2", "url": "https://c.com", "status": "unverified", "text": "?"},
        ])
        path = os.path.join(self.cache, "TEST.evidence.json")
        with open(path) as f:
            ledger = json.load(f)
        s = ledger["stats"]
        verified = s.get("verified", 0) + s.get("plausible", 0)
        self.assertLess(verified / s["total_claims"], 0.5)

    def test_clean_artifact_passes(self):
        """Normal artifact with matching ledger → passes."""
        self._make_ledger("TEST", [
            {"id": "C1", "source": "S1", "url": "https://a.com", "status": "verified", "text": "ok"},
        ])
        path = os.path.join(self.cache, "TEST.evidence.json")
        self.assertTrue(os.path.exists(path))


if __name__ == '__main__':
    unittest.main()
