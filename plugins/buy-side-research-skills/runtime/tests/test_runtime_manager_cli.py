import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path


RUNTIME_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RUNTIME_ROOT))

from buy_side_research_runtime.cli.runtime_manager import main


class RuntimeManagerCliTest(unittest.TestCase):
    def test_plan_auto_discovers_runtime_source(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            runtime = root / "runtime"
            workspace = root / "workspace"
            (runtime / "payload").mkdir(parents=True)
            workspace.mkdir()
            (runtime / "payload" / "asset.txt").write_text("managed", encoding="utf-8")
            (runtime / "managed-assets.json").write_text(
                json.dumps(
                    {
                        "runtime_version": "test",
                        "assets": [
                            {
                                "source": "payload/asset.txt",
                                "target": ".research-runtime/asset.txt",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            output = io.StringIO()

            with contextlib.redirect_stdout(output):
                status = main(
                    ["plan", "--workspace", str(workspace), "--runtime-root", str(runtime)]
                )

            self.assertEqual(0, status)
            self.assertEqual(
                [".research-runtime/asset.txt"],
                [item["target"] for item in json.loads(output.getvalue())["add"]],
            )

    def test_adopt_cli_requires_explicit_target(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            runtime = root / "runtime"
            workspace = root / "workspace"
            runtime.mkdir()
            workspace.mkdir()
            (runtime / "asset.txt").write_text("managed", encoding="utf-8")
            (workspace / "_scripts").mkdir()
            (workspace / "_scripts" / "asset.txt").write_text("legacy", encoding="utf-8")
            (runtime / "managed-assets.json").write_text(
                json.dumps(
                    {
                        "runtime_version": "test",
                        "assets": [{"source": "asset.txt", "target": "_scripts/asset.txt"}],
                    }
                ),
                encoding="utf-8",
            )
            output = io.StringIO()

            with contextlib.redirect_stdout(output):
                status = main(
                    [
                        "adopt",
                        "--workspace",
                        str(workspace),
                        "--runtime-root",
                        str(runtime),
                        "--target",
                        "_scripts/asset.txt",
                    ]
                )

            self.assertEqual(0, status)
            self.assertEqual("ok", json.loads(output.getvalue())["status"])

    def test_update_hosts_cli_dry_run(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            release = root / "release"
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
            home = root / "home"
            (home / ".codex" / "plugins" / "cache" / "buy-side-research-skills").mkdir(parents=True)
            output = io.StringIO()

            with contextlib.redirect_stdout(output):
                status = main(
                    [
                        "update-hosts",
                        "--source",
                        str(release),
                        "--home",
                        str(home),
                        "--dry-run",
                    ]
                )

            report = json.loads(output.getvalue())
            self.assertEqual(0, status)
            self.assertEqual("dry-run", report["status"])
            self.assertEqual("would-update", report["hosts"]["codex"]["status"])


if __name__ == "__main__":
    unittest.main()
