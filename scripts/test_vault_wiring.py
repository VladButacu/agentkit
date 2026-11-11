"""Checks for the Obsidian vault wiring: lifecycle hooks in each tool and the dream schedule."""

import json
import os
import plistlib
import shutil
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import actions
import choices
import install
import vault_schedule
from test_install import InstallerFixture

FOUND = {"claude": "/bin/claude", "codex": "/bin/codex", "opencode": "/bin/opencode"}


def ours(entries: list) -> list:
    return [entry for entry in entries if "vault_hook.py" in json.dumps(entry)]


class HookWiringChecks(InstallerFixture):
    def claude_hooks(self):
        return actions.read_json(self.claude / "settings.json").get("hooks", {})

    def test_hooks_reach_every_tool_with_a_hook_surface(self):
        self.install()
        hooks = self.claude_hooks()
        for event, argument in (("SessionStart", "start"), ("UserPromptSubmit", "prompt"), ("Stop", "stop")):
            (entry,) = ours(hooks[event])
            self.assertEqual(entry["hooks"][0]["args"][1:], [argument, "--tool", "claude"])
        codex = actions.read_json(self.codex / "hooks.json")["hooks"]
        self.assertEqual(sorted(codex), ["SessionStart", "Stop", "UserPromptSubmit"])
        self.assertIn("--tool codex", codex["Stop"][0]["hooks"][0]["command"])
        cursor = actions.read_json(self.home / ".cursor/hooks.json")
        self.assertEqual(cursor["version"], 1)
        self.assertEqual(sorted(cursor["hooks"]), ["sessionStart", "stop"])
        self.assertEqual(cursor["hooks"]["stop"][0]["loop_limit"], 1)
        crew = actions.read_json(self.home / ".kiro/crew/config.json")["agent"]["kiro_hooks"]
        for event in ("agentSpawn", "userPromptSubmit"):
            (shim,) = [entry["command"] for entry in crew[event]]
            self.assertTrue(os.path.isabs(shim) and os.path.isfile(shim))
            if os.name != "nt":
                self.assertTrue(os.access(shim, os.X_OK))
                self.assertIn("--tool kiro", Path(shim).read_text())
        agent = actions.read_json(self.home / ".kiro/agents/agentkit.json")
        self.assertEqual(sorted(agent["hooks"]), ["agentSpawn", "userPromptSubmit"])

    def test_hooks_start_through_the_launcher_not_the_install_time_python(self):
        self.install()
        launcher = str(actions.python_launcher())
        written = [self.claude / "settings.json", self.codex / "hooks.json", self.home / ".cursor/hooks.json",
                   *(self.data / "hooks").iterdir()]
        for path in written:
            text = path.read_text()
            self.assertNotIn(json.dumps(sys.executable)[1:-1], text, path)
            self.assertIn(json.dumps(launcher)[1:-1] if path.suffix == ".json" else launcher, text, path)
        self.assertTrue(actions.python_launcher().is_file())
        install.uninstall(actions.Installer())
        self.assertFalse(actions.python_launcher().exists())

    def test_deselecting_the_plugin_removes_only_our_hooks(self):
        foreign = {"hooks": [{"type": "command", "command": "echo mine"}]}
        settings = actions.read_json(self.claude / "settings.json")
        settings["hooks"] = {"Stop": [foreign]}
        self.put(self.claude / "settings.json", settings)
        self.put(self.home / ".cursor/hooks.json", {"version": 1, "hooks": {"stop": [{"command": "./mine.sh"}]}})
        self.install()
        self.install(requested="ponytail")
        hooks = self.claude_hooks()
        self.assertEqual(hooks["Stop"], [foreign])
        self.assertNotIn("UserPromptSubmit", hooks)
        self.assertFalse((self.codex / "hooks.json").exists())
        self.assertEqual(actions.read_json(self.home / ".cursor/hooks.json")["hooks"],
                         {"stop": [{"command": "./mine.sh"}]})
        crew = actions.read_json(self.home / ".kiro/crew/config.json")["agent"]
        self.assertFalse(crew.get("kiro_hooks"))
        self.assertNotIn("hooks", actions.read_json(self.home / ".kiro/agents/agentkit.json"))
        self.assertFalse(any((self.data / "hooks").glob("vault-*")))

    def test_uninstall_removes_the_hooks(self):
        self.install()
        install.uninstall(actions.Installer())
        self.assertEqual(ours([entry for entries in self.claude_hooks().values() for entry in entries]), [])
        self.assertFalse((self.codex / "hooks.json").exists())
        self.assertFalse((self.home / ".cursor/hooks.json").exists())
        self.assertFalse(any((self.data / "hooks").glob("vault-*")))


class DreamChoiceChecks(InstallerFixture):
    def choose(self, requested=None, tty=False, answers=()):
        with patch.object(shutil, "which", side_effect=FOUND.get), \
             patch.object(sys.stdin, "isatty", return_value=tty), \
             patch("builtins.input", side_effect=list(answers)):
            return choices.choose_dream(requested, vault_schedule.available(),
                                        actions.STATE / "dream.json", persist=True)

    def test_without_a_terminal_the_question_names_every_found_runner(self):
        with self.assertRaises(ValueError) as raised:
            self.choose()
        message = str(raised.exception)
        for part in ("--dream claude", "codex", "opencode", "--dream-model", "--dream-time",
                     "--dream-command", "--dream none"):
            self.assertIn(part, message)
        self.assertNotIn("kilo", message)

    def test_answers_are_validated_and_remembered(self):
        for bad in ({"runner": "zorp"}, {"runner": "kilo"}, {"runner": "claude", "time": "25:00"},
                    {"runner": "command"}):
            with self.assertRaises(ValueError):
                self.choose(bad)
        self.assertEqual(self.choose({"runner": "codex", "model": "m1"}),
                         {"runner": "codex", "model": "m1", "time": "03:00"})
        self.assertEqual(self.choose(), {"runner": "codex", "model": "m1", "time": "03:00"})
        self.assertEqual(self.choose({"runner": "command", "command": "quux-agent --fast", "time": "01:10"}),
                         {"runner": "command", "command": "quux-agent --fast", "time": "01:10"})
        self.assertEqual(self.choose({"runner": "none"}), {"runner": "none"})

    def test_terminal_questions(self):
        self.assertEqual(self.choose(tty=True, answers=["claude", "m2", "04:15"]),
                         {"runner": "claude", "model": "m2", "time": "04:15"})
        (actions.STATE / "dream.json").unlink()
        self.assertEqual(self.choose(tty=True, answers=[""]), {"runner": "none"})

    def test_the_question_waits_for_the_obsidian_plugin(self):
        with patch.object(sys.stdin, "isatty", return_value=False):
            self.install(requested="ponytail", dream=None)
            with self.assertRaises(ValueError):
                self.install(requested="obsidian", dream=None)


class ScheduleChecks(InstallerFixture):
    def setUp(self):
        super().setUp()
        self.calls = []
        for target, name, effect in ((actions, "run", self.record), (shutil, "which", FOUND.get)):
            replacement = patch.object(target, name, side_effect=effect)
            replacement.start()
            self.addCleanup(replacement.stop)

    def record(self, argv):
        self.calls.append(argv)
        return ""

    def sync(self, dream, platform, dry=False):
        vault_schedule.sync(actions.Installer(dry), dream, platform=platform)

    def plist(self):
        return self.home / f"Library/LaunchAgents/{vault_schedule.LABEL}.plist"

    def test_launchd_agent_runs_the_dream_daily_and_is_replaced_on_change(self):
        self.sync({"runner": "claude", "model": "m2", "time": "03:30"}, "darwin")
        plist = plistlib.loads(self.plist().read_bytes())
        self.assertEqual(plist["StartCalendarInterval"], {"Hour": 3, "Minute": 30})
        self.assertEqual(plist["ProgramArguments"][0], str(actions.python_launcher()))
        self.assertEqual(plist["ProgramArguments"][2:], ["run", "--config", str(actions.STATE / "dream-runner.json")])
        self.assertIn(str(Path("/bin/claude").parent), plist["EnvironmentVariables"]["PATH"].split(os.pathsep))
        self.assertEqual(json.loads((actions.STATE / "dream-runner.json").read_text()),
                         {"runner": "claude", "model": "m2", "executable": "/bin/claude"})
        self.assertTrue(any(call[:2] == ["launchctl", "bootstrap"] for call in self.calls))
        self.calls.clear()
        self.sync({"runner": "claude", "model": "m2", "time": "03:30"}, "darwin")
        self.assertEqual(self.calls, [])
        self.sync({"runner": "none"}, "darwin")
        self.assertTrue(any(call[:2] == ["launchctl", "bootout"] for call in self.calls))
        self.assertFalse(self.plist().exists())
        self.assertFalse((actions.STATE / "dream-runner.json").exists())

    def test_own_command_is_stored_for_the_runner(self):
        self.sync({"runner": "command", "command": "quux-agent --fast", "time": "01:10"}, "darwin")
        self.assertEqual(json.loads((actions.STATE / "dream-runner.json").read_text()),
                         {"runner": "command", "command": "quux-agent --fast"})

    def test_systemd_timer_on_linux(self):
        self.sync({"runner": "codex", "model": "m1", "time": "02:05"}, "linux")
        units = self.config / "systemd/user"
        self.assertIn("OnCalendar=*-*-* 02:05:00", (units / f"{vault_schedule.UNIT}.timer").read_text())
        self.assertIn("vault_dream.py", (units / f"{vault_schedule.UNIT}.service").read_text())
        self.assertIn(["systemctl", "--user", "enable", "--now", f"{vault_schedule.UNIT}.timer"], self.calls)
        self.sync({"runner": "none"}, "linux")
        self.assertFalse((units / f"{vault_schedule.UNIT}.timer").exists())

    def test_task_scheduler_on_windows(self):
        self.sync({"runner": "opencode", "model": None, "time": "02:05"}, "win32")
        (create,) = [call for call in self.calls if "/Create" in call]
        self.assertEqual(create[create.index("/ST") + 1], "02:05")
        self.assertIn("vault_dream.py", create[create.index("/TR") + 1])
        self.sync({"runner": "none"}, "win32")
        self.assertTrue(any("/Delete" in call for call in self.calls))

    def test_dry_run_schedules_nothing(self):
        self.sync({"runner": "claude", "model": None, "time": "03:00"}, "darwin", dry=True)
        self.assertEqual(self.calls, [])
        self.assertFalse((actions.STATE / "dream-runner.json").exists())


if __name__ == "__main__":
    unittest.main()
