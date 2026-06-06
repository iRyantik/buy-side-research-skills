import json
import sys
import tempfile
import unittest
from pathlib import Path


RUNTIME_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RUNTIME_ROOT))

from buy_side_research_runtime.hooks import HookDispatcher, generate_host_configs
from buy_side_research_runtime.source_intake import SourceIntake


class HooksRegistryTest(unittest.TestCase):
    def test_host_configs_map_each_event_to_same_event(self):
        configs = generate_host_configs()

        self.assertTrue(configs["claude"]["hooks"]["PreToolUse"])
        codex_subagent = configs["codex"]["hooks"]["SubagentStop"][0]["hooks"][0]["command"]
        self.assertIn("--event SubagentStop", codex_subagent)
        self.assertNotIn("--event PostToolUse", codex_subagent)

    def test_deployed_host_configs_match_registry_generator(self):
        payload = RUNTIME_ROOT / "workspace_payload"
        configs = generate_host_configs()

        self.assertEqual(
            configs["claude"],
            json.loads((payload / ".claude" / "settings.json").read_text(encoding="utf-8")),
        )
        self.assertEqual(
            configs["codex"],
            json.loads((payload / ".codex" / "hooks.json").read_text(encoding="utf-8")),
        )

    def test_every_registered_legacy_rule_is_in_workspace_payload(self):
        dispatcher = HookDispatcher()
        rules_root = RUNTIME_ROOT / "workspace_payload" / ".claude" / "hooks" / "rules"

        for rule in dispatcher.registry["rules"]:
            module = rule["module"]
            if module.startswith("legacy:rules."):
                relative = module.removeprefix("legacy:rules.").replace(".", "/") + ".py"
                self.assertTrue((rules_root / relative).is_file(), module)

    def test_dispatcher_uses_registry_for_event_selection(self):
        dispatcher = HookDispatcher()

        stop_rules = dispatcher.rule_names("Stop")
        pre_rules = dispatcher.rule_names("PreToolUse")

        self.assertIn("source_intake_enqueue", stop_rules)
        self.assertNotIn("source_intake_enqueue", pre_rules)

    def test_source_intake_hook_enqueues_pdf_candidate_without_converting(self):
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)
            pdf = workspace / "download.pdf"
            pdf.write_bytes(b"%PDF candidate")
            dispatcher = HookDispatcher()

            dispatcher.dispatch(
                "Stop",
                {
                    "cwd": str(workspace),
                    "candidate_paths": [str(pdf)],
                    "tool_input": {"url": "https://example.com/report.pdf"},
                },
            )

            queued = SourceIntake(workspace).queued()
            self.assertEqual(1, len(queued))
            self.assertEqual(str(pdf), queued[0]["source"])
            self.assertTrue(pdf.exists())
            self.assertFalse(any(workspace.glob("**/document.md")))


if __name__ == "__main__":
    unittest.main()
