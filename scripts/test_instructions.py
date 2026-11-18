"""Checks for the global instruction files and the Kiro CLI agent the installer writes."""

import sys
import unittest
from unittest.mock import patch

import actions
import install
import instruction_block
from test_install import InstallerFixture


class InstructionChecks(InstallerFixture):
    def instruction_block(self, body):
        return instruction_block.block(self.repo / "instructions/global.md", body)

    def test_instruction_files_carry_agentkit_block_and_refresh(self):
        self.install()
        pointer = "@" + (self.repo / "instructions/global.md").as_posix().replace(" ", "\\ ")
        self.assertEqual((self.claude / "CLAUDE.md").read_text(), self.instruction_block(pointer))
        self.assertEqual((self.codex / "AGENTS.md").read_text(),
                         self.instruction_block("Personal instructions"))
        (self.repo / "instructions/global.md").write_text("Revised instructions\n")
        self.install()
        self.assertEqual((self.codex / "AGENTS.md").read_text(),
                         self.instruction_block("Revised instructions"))

    def test_kiro_agent_loads_the_global_rules_not_the_repository_rulebook(self):
        agent = self.home / ".kiro/agents/agentkit.json"
        internal = f"file://{(self.repo / 'AGENTS.md').as_posix()}"
        self.put(agent, {"name": "agentkit", "resources": [internal, "file://mine.md"], "tools": ["*"]})
        self.install()
        resources = actions.read_json(agent)["resources"]
        self.assertEqual(resources, [f"file://{(self.repo / 'instructions/global.md').as_posix()}", "file://mine.md"])

    def test_uninstall_removes_the_kiro_agent_from_a_custom_directory(self):
        custom = self.home / "kiro-agents"
        with patch.dict("os.environ", {"KIRO_AGENT_CONFIG_DIR": str(custom)}):
            self.install()
            self.assertTrue((custom / "agentkit.json").exists())
            install.uninstall(actions.Installer())
        self.assertFalse((custom / "agentkit.json").exists())

    def test_foreign_instructions_need_a_choice_before_anything_changes(self):
        (self.codex / "AGENTS.md").write_text("My codex rules\n")
        snapshot = self.snapshot()
        with patch.object(sys.stdin, "isatty", return_value=False), \
             self.assertRaises(ValueError) as raised:
            self.install()
        self.assertIn("--instructions", str(raised.exception))
        # Only the installer's own state may hold the plugin answer given before the question.
        after = {path: value for path, value in self.snapshot().items() if not path.startswith("state")}
        self.assertEqual(snapshot, after)

    def test_foreign_instructions_keep_append_and_replace(self):
        mine = "My codex rules\n"
        (self.codex / "AGENTS.md").write_text(mine)
        self.install(instructions="keep")
        self.assertEqual((self.codex / "AGENTS.md").read_text(), mine)
        self.install(instructions="append")
        self.assertEqual((self.codex / "AGENTS.md").read_text(),
                         f"{mine}\n{self.instruction_block('Personal instructions')}")
        install.uninstall(actions.Installer())
        self.assertEqual((self.codex / "AGENTS.md").read_text(), mine)
        self.install(instructions="replace")
        self.assertEqual((self.codex / "AGENTS.md").read_text(),
                         self.instruction_block("Personal instructions"))
        backups = list((self.home / "state/backups").rglob("AGENTS.md"))
        self.assertIn(mine, [path.read_text() for path in backups])
        install.uninstall(actions.Installer())
        self.assertFalse((self.codex / "AGENTS.md").exists())

    def test_legacy_instruction_symlinks_become_blocks(self):
        try:
            (self.codex / "AGENTS.md").symlink_to(self.repo / "AGENTS.md")
        except OSError:
            self.skipTest("file symlinks need privileges on this machine")
        self.install()
        self.assertFalse((self.codex / "AGENTS.md").is_symlink())
        self.assertEqual((self.codex / "AGENTS.md").read_text(),
                         self.instruction_block("Personal instructions"))


if __name__ == "__main__":
    unittest.main()
