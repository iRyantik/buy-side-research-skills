import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path


RUNTIME_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RUNTIME_ROOT))

from buy_side_research_runtime.deployment import (
    DeploymentManager,
    ManifestError,
    build_release_payload,
    discover_runtime_source,
    sync_hosts,
    verify_release_payload,
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class DeploymentManagerTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.payload = self.root / "payload"
        self.workspace = self.root / "workspace"
        self.payload.mkdir()
        self.workspace.mkdir()

    def tearDown(self):
        self.temp.cleanup()

    def _write_manifest(self, assets):
        path = self.payload / "managed-assets.json"
        path.write_text(
            json.dumps({"runtime_version": "6.0.0", "assets": assets}, indent=2),
            encoding="utf-8",
        )
        return path

    def test_plan_uses_only_explicit_manifest_assets(self):
        (self.payload / "wanted.txt").write_text("managed", encoding="utf-8")
        (self.payload / "ignored.txt").write_text("must not deploy", encoding="utf-8")
        manifest = self._write_manifest(
            [{"source": "wanted.txt", "target": ".research-runtime/wanted.txt"}]
        )

        plan = DeploymentManager(self.payload, self.workspace, manifest).plan()

        self.assertEqual([".research-runtime/wanted.txt"], [item.target for item in plan.add])
        self.assertFalse((self.workspace / "ignored.txt").exists())

    def test_manifest_rejects_forbidden_payload_files(self):
        (self.payload / "fixture.pdf").write_bytes(b"%PDF")
        manifest = self._write_manifest(
            [{"source": "fixture.pdf", "target": ".research-runtime/fixture.pdf"}]
        )

        with self.assertRaises(ManifestError):
            DeploymentManager(self.payload, self.workspace, manifest).plan()

    def test_update_preserves_user_modified_stale_managed_file(self):
        stale = self.workspace / ".research-runtime" / "old.py"
        stale.parent.mkdir(parents=True)
        stale.write_text("user changed", encoding="utf-8")
        installed = {
            "runtime_version": "5.0.0",
            "assets": [
                {
                    "target": ".research-runtime/old.py",
                    "sha256": hashlib.sha256(b"original").hexdigest(),
                }
            ],
        }
        state = self.workspace / ".research-runtime" / "installed-manifest.json"
        state.write_text(json.dumps(installed), encoding="utf-8")
        manifest = self._write_manifest([])

        plan = DeploymentManager(self.payload, self.workspace, manifest).plan()

        self.assertEqual([], plan.remove)
        self.assertEqual([".research-runtime/old.py"], [item.target for item in plan.conflict])
        self.assertEqual("user changed", stale.read_text(encoding="utf-8"))

    def test_apply_installs_asset_and_records_hash(self):
        (self.payload / "entry.py").write_text("print('ok')\n", encoding="utf-8")
        manifest = self._write_manifest(
            [{"source": "entry.py", "target": "_scripts/runtime-manager.py"}]
        )
        manager = DeploymentManager(self.payload, self.workspace, manifest)

        manager.apply(manager.plan())

        target = self.workspace / "_scripts" / "runtime-manager.py"
        state = json.loads(
            (self.workspace / ".research-runtime" / "installed-manifest.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertTrue(target.exists())
        self.assertEqual(_sha256(target), state["assets"][0]["sha256"])
        self.assertEqual(str(self.payload.resolve()), state["source"]["payload_root"])
        self.assertEqual(str(manifest.resolve()), state["source"]["manifest"])

    def test_verify_reports_modified_and_missing_assets(self):
        (self.payload / "one.txt").write_text("one", encoding="utf-8")
        (self.payload / "two.txt").write_text("two", encoding="utf-8")
        manifest = self._write_manifest(
            [
                {"source": "one.txt", "target": ".research-runtime/one.txt"},
                {"source": "two.txt", "target": ".research-runtime/two.txt"},
            ]
        )
        manager = DeploymentManager(self.payload, self.workspace, manifest)
        manager.apply(manager.plan())
        (self.workspace / ".research-runtime" / "one.txt").write_text("changed", encoding="utf-8")
        (self.workspace / ".research-runtime" / "two.txt").unlink()

        report = manager.verify_installed()

        self.assertEqual([".research-runtime/two.txt"], report["missing"])
        self.assertEqual([".research-runtime/one.txt"], report["modified"])
        self.assertEqual("failed", report["status"])

    def test_apply_does_not_adopt_unmanaged_conflict(self):
        (self.payload / "entry.py").write_text("managed", encoding="utf-8")
        target = self.workspace / "_scripts" / "entry.py"
        target.parent.mkdir(parents=True)
        target.write_text("user version", encoding="utf-8")
        manifest = self._write_manifest(
            [{"source": "entry.py", "target": "_scripts/entry.py"}]
        )
        manager = DeploymentManager(self.payload, self.workspace, manifest)
        plan = manager.plan()

        manager.apply(plan)

        installed = json.loads(manager.installed_path.read_text(encoding="utf-8"))
        self.assertEqual("user version", target.read_text(encoding="utf-8"))
        self.assertEqual([], installed["assets"])

    def test_adopt_requires_explicit_conflict_target_and_records_backup(self):
        (self.payload / "entry.py").write_text("managed", encoding="utf-8")
        target = self.workspace / "_scripts" / "entry.py"
        target.parent.mkdir(parents=True)
        target.write_text("legacy runtime", encoding="utf-8")
        manifest = self._write_manifest(
            [{"source": "entry.py", "target": "_scripts/entry.py"}]
        )
        manager = DeploymentManager(self.payload, self.workspace, manifest)

        report = manager.adopt_conflicts(["_scripts/entry.py"])

        self.assertEqual("ok", report["status"])
        self.assertTrue((Path(report["backup_root"]) / "_scripts" / "entry.py").is_file())
        plan = manager.plan()
        self.assertEqual([], [item.target for item in plan.conflict])
        self.assertEqual(["_scripts/entry.py"], [item.target for item in plan.update])

    def test_adopt_rejects_global_or_unmanaged_targets(self):
        manifest = self._write_manifest([])
        manager = DeploymentManager(self.payload, self.workspace, manifest)

        with self.assertRaises(ManifestError):
            manager.adopt_conflicts([])
        with self.assertRaises(ManifestError):
            manager.adopt_conflicts(["_scripts/user.py"])

    def test_discovers_manifest_from_runtime_directory(self):
        runtime = self.root / "plugin" / "runtime"
        runtime.mkdir(parents=True)
        manifest = runtime / "managed-assets.json"
        manifest.write_text('{"assets": []}', encoding="utf-8")

        payload_root, found_manifest = discover_runtime_source(start=runtime / "nested")

        self.assertEqual(runtime.resolve(), payload_root)
        self.assertEqual(manifest.resolve(), found_manifest)

    def test_build_and_verify_release_payload_rejects_payload_pollution(self):
        plugin = self.root / "plugin"
        for name in (".claude-plugin", ".codex-plugin", "skills", "runtime"):
            (plugin / name).mkdir(parents=True)
        (plugin / "README.md").write_text("# plugin\n", encoding="utf-8")
        (plugin / ".claude-plugin" / "plugin.json").write_text("{}", encoding="utf-8")
        (plugin / ".codex-plugin" / "plugin.json").write_text("{}", encoding="utf-8")
        (plugin / "skills" / "stock-quickread").mkdir(parents=True)
        (plugin / "skills" / "stock-quickread" / "SKILL.md").write_text("skill", encoding="utf-8")
        (plugin / "runtime" / "payload.txt").write_text("payload", encoding="utf-8")
        (plugin / "runtime" / "tests").mkdir()
        (plugin / "runtime" / "tests" / "test_should_not_ship.py").write_text("x", encoding="utf-8")
        (plugin / "runtime" / "managed-assets.json").write_text(
            json.dumps(
                {
                    "runtime_version": "dev",
                    "assets": [{"source": "payload.txt", "target": ".research-runtime/payload.txt"}],
                }
            ),
            encoding="utf-8",
        )

        report = build_release_payload(plugin, version="6.0.0-rc.1", dist_root=self.root / "dist")

        self.assertEqual("ok", report["status"])
        release_root = Path(report["release_root"])
        self.assertFalse((release_root / "runtime" / "tests").exists())
        self.assertEqual("ok", verify_release_payload(release_root)["status"])

    def test_update_hosts_dry_run_reports_targets_without_writing(self):
        release = self.root / "release"
        for name in (".claude-plugin", ".codex-plugin", "skills", "runtime"):
            (release / name).mkdir(parents=True)
        (release / "README.md").write_text("# plugin\n", encoding="utf-8")
        (release / ".claude-plugin" / "plugin.json").write_text("{}", encoding="utf-8")
        (release / ".codex-plugin" / "plugin.json").write_text("{}", encoding="utf-8")
        (release / "skills" / "stock-quickread").mkdir(parents=True)
        (release / "skills" / "stock-quickread" / "SKILL.md").write_text("skill", encoding="utf-8")
        (release / "runtime" / "payload.txt").write_text("payload", encoding="utf-8")
        (release / "runtime" / "managed-assets.json").write_text(
            json.dumps(
                {
                    "runtime_version": "6.0.0-rc.1",
                    "assets": [{"source": "payload.txt", "target": ".research-runtime/payload.txt"}],
                }
            ),
            encoding="utf-8",
        )
        home = self.root / "home"
        (home / ".claude" / "plugins" / "cache" / "buy-side-research-skills").mkdir(parents=True)
        (home / ".codex" / "plugins" / "cache" / "buy-side-research-skills").mkdir(parents=True)

        report = sync_hosts(release, home=home, dry_run=True)

        self.assertEqual("dry-run", report["status"])
        self.assertEqual("would-update", report["hosts"]["claude"]["status"])
        self.assertEqual("would-update", report["hosts"]["codex"]["status"])
        self.assertFalse(
            (
                home
                / ".codex"
                / "plugins"
                / "cache"
                / "buy-side-research-skills"
                / "buy-side-research-skills"
                / "6.0.0-rc.1"
            ).exists()
        )


if __name__ == "__main__":
    unittest.main()
