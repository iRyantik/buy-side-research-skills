"""Tests for evidence_ledger_floor.py — ledger enforcement hook.

Real tests: each case builds an artifact + ledger on disk, then invokes
evidence_ledger_floor.check() with a synthetic ctx (same shape the host
adapter produces) and asserts the exit code — 0 = pass, 2 = block.
"""
import unittest, json, os, sys, tempfile, shutil

WS = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(WS, ".claude", "hooks"))

import importlib.util
spec = importlib.util.spec_from_file_location(
    "evidence_ledger_floor",
    os.path.join(WS, ".claude", "hooks", "rules", "evidence_ledger_floor.py"))
elf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(elf)

ARTIFACT_NAME = "20260820-stock-quickread-Test.md"


class TestLedgerFloor(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.artifact = os.path.join(self.tmp, ARTIFACT_NAME)
        self.cache = os.path.join(self.tmp, ".cache", "evidence")
        os.makedirs(self.cache, exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def _artifact_text(self, anchors=("S1",)):
        lines = ["# Test"]
        for code in anchors:
            lines.append(f"Revenue claim with {code}. [{code}](https://example.com/{code})")
        return "\n".join(lines)

    def _write_artifact(self, anchors=("S1",)):
        with open(self.artifact, "w", encoding="utf-8") as f:
            f.write(self._artifact_text(anchors))

    def _make_ledger(self, claims):
        ledger = {"ticker": "TEST", "status": "complete",
                  "stats": {"total_claims": len(claims)}, "claims": claims}
        with open(os.path.join(self.cache, "TEST.evidence.json"), "w", encoding="utf-8") as f:
            json.dump(ledger, f)

    def _claim(self, cid, source, status, attempts=None):
        return {"id": cid, "source": source, "url": f"https://example.com/{source}",
                "text": "t", "status": status, "provenances": [], "attempts": attempts or []}

    def _run_check(self):
        """Run the hook; return exit code (0 = pass, 2 = block)."""
        with open(self.artifact, "r", encoding="utf-8") as f:
            text = f.read()
        ctx = {"targets": [{"kind": "file", "path": self.artifact,
                            "display": ARTIFACT_NAME, "text": text}]}
        try:
            elf.check(ctx)
            return 0
        except SystemExit as e:
            return e.code or 0

    def test_missing_ledger_blocked(self):
        """Artifact has [S#] but no ledger → block (Rule 2)."""
        self._write_artifact()
        self.assertEqual(self._run_check(), 2)

    def test_fabrication_risk_blocked(self):
        """Ledger with fabrication_risk claim → block (Rule 3)."""
        self._write_artifact()
        self._make_ledger([self._claim("C1", "S1", "fabrication_risk")])
        self.assertEqual(self._run_check(), 2)

    def test_unprocessed_claim_blocked(self):
        """Anchored claim still unverified → block (Rule 5)."""
        self._write_artifact()
        self._make_ledger([self._claim("C1", "S1", "unverified",
                                       [{"tier": 1, "method": "WebFetch", "result": "failed"}])])
        self.assertEqual(self._run_check(), 2)

    def test_missing_attempt_blocked(self):
        """Plausible claim with zero attempt records → block (Rule 5) —
        the SMC-style gap the old coverage quota never caught."""
        self._write_artifact()
        self._make_ledger([self._claim("C1", "S1", "plausible")])
        self.assertEqual(self._run_check(), 2)

    def test_clean_artifact_passes(self):
        """Every anchored claim non-unverified with attempt → pass."""
        self._write_artifact()
        self._make_ledger([self._claim("C1", "S1", "verified",
                                       [{"tier": 1, "method": "WebFetch", "result": "ok"}])])
        self.assertEqual(self._run_check(), 0)

    def test_dead_link_resolution_passes(self):
        """Dead source resolved by removing anchor+claim → pass."""
        self._write_artifact(anchors=("S1", "S2"))
        self._make_ledger([
            self._claim("C1", "S1", "verified",
                        [{"tier": 1, "method": "WebFetch", "result": "ok"}]),
            self._claim("C2", "S2", "verified",
                        [{"tier": 1, "method": "WebFetch", "result": "ok"}]),
        ])
        self.assertEqual(self._run_check(), 0)

    def test_stale_claim_does_not_gate(self):
        """Claim whose source is not anchored in THIS artifact → no gate."""
        self._write_artifact()
        self._make_ledger([
            self._claim("C1", "S1", "verified",
                        [{"tier": 1, "method": "WebFetch", "result": "ok"}]),
            self._claim("C9", "S9", "unverified"),  # orphaned — not in artifact
        ])
        self.assertEqual(self._run_check(), 0)


if __name__ == '__main__':
    unittest.main()
