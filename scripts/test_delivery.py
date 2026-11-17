"""How agentkit itself reaches each tool: native plugin channels versus skill links."""

import contextlib
import io
import json
import shutil
import unittest
from pathlib import Path
from unittest.mock import patch

import actions
import delivery
import install
from test_install import NO_DREAM, InstallerFixture

REPOSITORY = "https://example.com/agentkit.git"


def table(answers: dict, calls: list | None = None, default=""):
    """A fake actions.run answering by exact argument, recording every call."""

    def run(args):
        if calls is not None:
            calls.append(list(args))
        if args[:2] == ["git", "init"]:
            Path(args[-1]).mkdir(parents=True, exist_ok=True)
        for key, value in answers.items():
            if key in args:
                if isinstance(value, Exception):
                    raise value
                return value
        if isinstance(default, Exception):
            raise default
        return default

    return run


class DeliveryModeChecks(unittest.TestCase):
    def test_delivery_modes_follow_the_sole_reader_rule(self):
        self.assertEqual(delivery.delivery_modes({"codex"}, "native"), {"codex": "plugin"})
        self.assertEqual(delivery.delivery_modes({"codex", "claude"}, "native"),
                         {"codex": "plugin", "claude": "plugin"})
        self.assertEqual(delivery.delivery_modes({"codex", "cursor"}, "native"),
                         {"codex": "links", "cursor": "links"})
        self.assertEqual(delivery.delivery_modes({"cursor", "kilo"}, "native"),
                         {"cursor": "links", "kilo": "links"})
        self.assertEqual(delivery.delivery_modes({"codex", "kilo"}, "native"),
                         {"codex": "links", "kilo": "links"})
        self.assertEqual(delivery.delivery_modes({"claude"}, "links"), {"claude": "links"})


class NativeDeliveryChecks(InstallerFixture):
    def plain_install(self, tools, delivery_preference=None):
        with patch.object(actions.Installer, "desloppify"), \
             patch.object(actions.Installer, "checkout",
                          side_effect=lambda name, entry, **extra: self.sources[name]), \
             patch.object(actions, "run", side_effect=table(
                 {"get-url": REPOSITORY}, default=RuntimeError("no git"))), \
             patch.object(shutil, "which", return_value=None):
            install.install(actions.Installer(False), tools, "all", None, NO_DREAM,
                            delivery_preference)

    def captured_install(self, tools, delivery_preference=None):
        with contextlib.redirect_stdout(io.StringIO()) as output:
            self.plain_install(tools, delivery_preference)
        return output.getvalue()

    def test_claude_native_self_links_only_companions(self):
        with patch.object(actions.Installer, "native_plugin", return_value=True):
            self.plain_install(set(self.tools))
        self.assertTrue(actions.is_link(self.claude / "skills/obsidian-companion"))
        self.assertFalse((self.claude / "skills/prose").exists())
        self.assertTrue(actions.is_link(self.home / ".agents/skills/prose"))
        resolved = actions.read_json(self.home / "state/delivery.json")["resolved"]
        self.assertEqual(resolved["claude"], "plugin")

    def test_shared_root_empty_when_sole_reader_is_native(self):
        with patch.object(actions.Installer, "native_plugin", return_value=True):
            self.plain_install({"codex"})
        self.assertFalse((self.home / ".agents/skills/prose").exists())
        self.assertTrue(actions.is_link(self.codex / "skills/obsidian-companion"))
        resolved = actions.read_json(self.home / "state/delivery.json")["resolved"]
        self.assertEqual(resolved["codex"], "plugin")

    def test_rival_reader_forces_links_for_everyone(self):
        attempts = []

        def record(name, result):
            attempts.append(name)
            return result

        with patch.object(actions.Installer, "native_plugin",
                          side_effect=lambda tool, name, *rest: record(name, True)), \
             patch.object(actions.Installer, "checkout",
                          side_effect=lambda name, entry, **extra: record(name, self.sources[name])), \
             patch.object(actions, "run", side_effect=table(
                 {"get-url": REPOSITORY}, default=RuntimeError("no git"))), \
             contextlib.redirect_stdout(io.StringIO()) as captured:
            install.install(actions.Installer(False), {"codex", "cursor"}, "all", None, NO_DREAM)
        self.assertNotIn("agentkit", attempts)
        self.assertTrue(actions.is_link(self.home / ".agents/skills/prose"))
        self.assertIn("would load every skill twice", captured.getvalue())

    def test_cursor_native_clone_pinned_to_the_current_tag(self):
        calls = []
        answers = {"--exact-match": "v0.4.1", "get-url": REPOSITORY, "--verify": "",
                   "rev-parse": "deadbeef"}
        with patch.object(actions, "run", side_effect=table(answers, calls)), \
             patch.object(actions.Installer, "desloppify"), \
             patch.object(shutil, "which", return_value=None):
            install.install(actions.Installer(False), {"cursor"}, "all", None, NO_DREAM)
        clone = self.home / ".cursor/plugins/local/agentkit"
        self.assertTrue(clone.exists())
        self.assertTrue(any("fetch" in call and "v0.4.1" in call for call in calls))
        resolved = actions.read_json(self.home / "state/delivery.json")["resolved"]
        self.assertEqual(resolved["cursor"], "plugin")

    def test_cursor_native_falls_back_without_tags(self):
        answers = {"--exact-match": RuntimeError("untagged"), "--abbrev=0": RuntimeError("no tags"),
                   "get-url": REPOSITORY, "--verify": "", "rev-parse": "deadbeef"}
        with patch.object(actions, "run", side_effect=table(answers)), \
             patch.object(actions.Installer, "desloppify"), \
             patch.object(shutil, "which", return_value=None):
            install.install(actions.Installer(False), {"cursor"}, "all", None, NO_DREAM)
        self.assertFalse((self.home / ".cursor/plugins/local/agentkit").exists())
        self.assertTrue(actions.is_link(self.home / ".agents/skills/prose"))
        resolved = actions.read_json(self.home / "state/delivery.json")["resolved"]
        self.assertEqual(resolved["cursor"], "links")

    def test_precondition_loss_retracts_native(self):
        (self.home / "state").mkdir(parents=True, exist_ok=True)
        (self.home / "state/delivery.json").write_text(json.dumps(
            {"preference": "native", "resolved": {"codex": "plugin"}}))
        calls = []
        answers = {"get-url": REPOSITORY, "--verify": "", "rev-parse": "deadbeef"}
        with patch.object(actions, "run", side_effect=table(answers, calls)), \
             patch.object(actions.Installer, "desloppify"), \
             patch.object(actions.Installer, "checkout",
                          side_effect=lambda name, entry, **extra: self.sources[name]), \
             patch.object(shutil, "which",
                          side_effect=lambda name: "/usr/bin/codex" if name == "codex" else None):
            install.install(actions.Installer(False), {"codex", "kilo"}, "all", None, NO_DREAM)
        self.assertIn(["codex", "plugin", "remove", "agentkit@agentkit"], calls)
        self.assertTrue(actions.is_link(self.home / ".agents/skills/prose"))

    def test_delivery_preference_links_skips_native_attempts(self):
        attempts = []
        with patch.object(actions.Installer, "native_plugin",
                          side_effect=lambda tool, name, *rest: attempts.append(name) or True):
            self.plain_install({"claude"}, delivery_preference="links")
        self.assertNotIn("agentkit", attempts)
        self.assertTrue(actions.is_link(self.claude / "skills/prose"))

    def test_recorded_readers_survive_a_narrowed_run(self):
        self.plain_install({"cursor", "kilo"})
        with patch.object(actions.Installer, "native_plugin",
                          side_effect=lambda tool, name, *rest: tool == "codex"):
            self.plain_install({"codex"})
        resolved = actions.read_json(self.home / "state/delivery.json")["resolved"]
        self.assertEqual(resolved["codex"], "links")
        self.assertEqual(resolved["cursor"], "links")
        self.assertEqual(resolved["kilo"], "links")
        self.assertTrue(actions.is_link(self.home / ".agents/skills/prose"))

    def test_custom_checkout_destination_refuses_foreign_folder(self):
        clone = self.home / ".cursor/plugins/local/agentkit"
        clone.mkdir(parents=True)
        (clone / "mine.txt").write_text("user content")
        with patch.object(actions, "run", side_effect=table({"get-url": REPOSITORY})), \
             self.assertRaises(ValueError):
            actions.Installer().checkout(
                "agentkit", {"repository": REPOSITORY}, destination=clone, ref="v0.4.1")
        self.assertTrue((clone / "mine.txt").exists())

    def test_uninstall_removes_native_delivery(self):
        (self.home / "state").mkdir(parents=True, exist_ok=True)
        (self.home / "state/delivery.json").write_text(json.dumps(
            {"preference": "native", "resolved": {"claude": "plugin", "cursor": "plugin"}}))
        clone = self.home / ".cursor/plugins/local/agentkit"
        clone.mkdir(parents=True)
        (clone / ".git").mkdir()
        calls = []
        with patch.object(actions, "run", side_effect=table({"get-url": REPOSITORY}, calls)), \
             patch.object(shutil, "which",
                          side_effect=lambda name: "/usr/bin/claude" if name == "claude" else None):
            install.uninstall(actions.Installer(False))
        self.assertFalse(clone.exists())
        self.assertIn(["claude", "plugin", "uninstall", "agentkit@agentkit"], calls)
        self.assertFalse((self.home / "state/delivery.json").exists())


if __name__ == "__main__":
    unittest.main()
