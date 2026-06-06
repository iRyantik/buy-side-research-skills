import json
import unittest
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = Path(__file__).resolve().parents[4]
RUNTIME_ROOT = PLUGIN_ROOT / "runtime"


class PayloadContractTest(unittest.TestCase):
    def test_ingest_is_not_an_active_skill(self):
        self.assertFalse((PLUGIN_ROOT / "skills" / "ingest" / "SKILL.md").exists())

    def test_financial_data_implementation_lives_in_runtime(self):
        legacy = PLUGIN_ROOT / "skills" / "financial-data" / "scripts"
        self.assertFalse(any((legacy / "providers").glob("*.py")))

    def test_manifest_is_explicit_and_contains_three_public_clis(self):
        manifest = json.loads((RUNTIME_ROOT / "managed-assets.json").read_text(encoding="utf-8"))
        targets = {item["target"] for item in manifest["assets"]}

        self.assertIn("_scripts/source-intake.py", targets)
        self.assertIn("_scripts/financial-data.py", targets)
        self.assertIn("_scripts/runtime-manager.py", targets)
        self.assertIn("_scripts/ingest.py", targets)
        self.assertIn("_scripts/shared/to-markdown.py", targets)
        self.assertIn("_scripts/financial-data/financial_data.py", targets)
        self.assertNotIn("trees", manifest)

    def test_manifest_sources_exclude_deployment_pollution(self):
        manifest = json.loads((RUNTIME_ROOT / "managed-assets.json").read_text(encoding="utf-8"))
        forbidden = {".pyc", ".pdf", ".db"}

        for item in manifest["assets"]:
            source = item["source"].replace("\\", "/")
            self.assertNotIn("/tests/", f"/{source}/")
            self.assertNotIn("/_tmp/", f"/{source}/")
            self.assertNotIn("__pycache__", source)
            self.assertNotIn(Path(source).suffix.lower(), forbidden)
            self.assertTrue((RUNTIME_ROOT / source).is_file(), source)

    def test_cpr_means_commit_push_release_not_payload(self):
        checked = [
            REPO_ROOT / "docs" / "release.md",
            PLUGIN_ROOT / "skills" / "update-agent-runtime" / "SKILL.md",
            PLUGIN_ROOT / "skills" / "update-agent-runtime" / "SKILL.en.md",
        ]
        for path in checked:
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("Candidate Packaged Release", text, str(path))
            self.assertNotIn("verify-cpr", text, str(path))
        self.assertIn("commit -> push -> release", (REPO_ROOT / "docs" / "release.md").read_text(encoding="utf-8"))

    def test_consumers_do_not_claim_direct_actuals_view_write(self):
        patterns = [
            "writes _cache/financial-data/internal/actuals-resolved.json",
            "writes structured actuals to `_cache/financial-data/internal/actuals-resolved.json`",
        ]
        for path in list((PLUGIN_ROOT / "skills").rglob("*.md")) + list((RUNTIME_ROOT / "workspace_payload").rglob("*.md")):
            text = path.read_text(encoding="utf-8")
            for pattern in patterns:
                self.assertNotIn(pattern, text, str(path))


if __name__ == "__main__":
    unittest.main()
