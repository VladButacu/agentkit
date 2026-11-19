"""Checks for the first-install wizard: the next unanswered question, given the answers so far."""

import json
import unittest
from pathlib import Path

import actions
import choices
import install
import wizard
from test_install import InstallerFixture

CLIS = {"codex": "/bin/codex", "claude": "/bin/claude"}


class WizardChecks(InstallerFixture):
    def setUp(self):
        super().setUp()
        actions.STATE.mkdir(parents=True)

    def step(self, plugins=None, dream=None, instructions=None, foreign=(), available=CLIS):
        manifest = install.load_manifest()
        return wizard.next_step(manifest, {"plugins": plugins, "dream": dream, "instructions": instructions},
                                list(foreign), available)

    def test_a_fresh_install_asks_for_plugins_first(self):
        step = self.step()
        self.assertEqual((step["step"], step["flag"]), ("plugins", "--plugins"))
        values = {option["value"] for option in step["options"]}
        self.assertIn("obsidian", values)
        self.assertNotIn("superpowers", values)

    def test_plugins_without_the_vault_finish_the_wizard(self):
        step = self.step(plugins="ponytail")
        self.assertEqual(step["step"], "done")
        self.assertEqual(step["run_with"], ["--plugins", "ponytail"])

    def test_an_unknown_plugin_is_an_error(self):
        with self.assertRaises(ValueError):
            self.step(plugins="nope")

    def test_the_vault_asks_for_tool_then_model_then_time(self):
        step = self.step(plugins="obsidian")
        self.assertEqual(step["step"], "dream_tool")
        self.assertEqual([option["value"] for option in step["options"]],
                         ["claude", "codex", "command", "none"])
        step = self.step(plugins="obsidian", dream={"runner": "codex"})
        self.assertEqual((step["step"], step["flag"]), ("dream_model", "--dream-model"))
        step = self.step(plugins="obsidian", dream={"runner": "codex", "model": "default"})
        self.assertEqual((step["step"], step["flag"]), ("dream_time", "--dream-time"))
        step = self.step(plugins="obsidian", dream={"runner": "codex", "model": "default", "time": "03:00"})
        self.assertEqual(step["step"], "done")
        self.assertEqual(step["run_with"], ["--plugins", "obsidian", "--dream", "codex",
                                            "--dream-model", "default", "--dream-time", "03:00"])

    def test_a_command_runner_asks_for_the_command_not_a_model(self):
        step = self.step(plugins="obsidian", dream={"runner": "command"})
        self.assertEqual(step["step"], "dream_command")
        step = self.step(plugins="obsidian", dream={"runner": "command", "command": "my-agent", "time": "04:30"})
        self.assertEqual(step["step"], "done")

    def test_no_dream_finishes_without_model_or_time(self):
        self.assertEqual(self.step(plugins="obsidian", dream={"runner": "none"})["step"], "done")

    def test_bad_dream_answers_are_errors(self):
        with self.assertRaises(ValueError):
            self.step(plugins="obsidian", dream={"runner": "opencode", "model": "default", "time": "03:00"})
        with self.assertRaises(ValueError):
            self.step(plugins="obsidian", dream={"runner": "codex", "model": "default", "time": "3am"})

    def test_a_stored_selection_and_dream_are_not_asked_again(self):
        choices.store_selection({"obsidian"}, set(install.load_manifest()) - {"superpowers"})
        (actions.STATE / "dream.json").write_text(json.dumps({"runner": "none"}))
        self.assertEqual(self.step()["step"], "done")

    def test_a_plugin_added_later_is_asked_about_alone(self):
        choices.store_selection({"obsidian"}, {"obsidian"})
        step = self.step()
        self.assertEqual(step["step"], "plugins")
        self.assertNotIn("obsidian", {option["value"] for option in step["options"]})

    def test_an_instruction_file_of_the_user_asks_keep_append_or_replace(self):
        foreign = [Path("/tmp/CLAUDE.md")]
        step = self.step(plugins="none", foreign=foreign)
        self.assertEqual((step["step"], step["flag"]), ("instructions", "--instructions"))
        self.assertEqual([option["value"] for option in step["options"]], ["keep", "append", "replace"])
        step = self.step(plugins="none", instructions="keep", foreign=foreign)
        self.assertEqual(step["run_with"], ["--plugins", "none", "--instructions", "keep"])

    def test_a_remembered_keep_is_not_asked_again(self):
        foreign = [Path("/tmp/CLAUDE.md")]
        (actions.STATE / "instructions.json").write_text(json.dumps({"keep": [str(foreign[0])]}))
        self.assertEqual(self.step(plugins="none", foreign=foreign)["step"], "done")

    def test_the_model_default_word_means_the_cli_default(self):
        dream = choices.validate_dream({"runner": "codex", "model": "default", "time": "03:00"}, CLIS)
        self.assertIsNone(dream["model"])


if __name__ == "__main__":
    unittest.main()
