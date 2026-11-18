"""Checks for the subagents the installer renders for each tool from agents/."""

import tomllib
import unittest

import actions
import install
import subagents
from test_install import InstallerFixture


class SubagentChecks(InstallerFixture):
    def rendered(self) -> dict:
        return {"claude": self.claude / "agents/blind-reviewer.md",
                "cursor": self.home / ".cursor/agents/blind-reviewer.md",
                "codex": self.codex / "agents/blind-reviewer.toml",
                "kiro": self.home / ".kiro/agents/blind-reviewer.md",
                "opencode": self.config / "opencode/agents/blind-reviewer.md",
                "kilo": self.config / "kilo/agents/blind-reviewer.md"}

    def test_every_tool_gets_a_read_only_reviewer_on_the_session_model(self):
        self.install()
        files = self.rendered()
        for tool, path in files.items():
            with self.subTest(tool=tool):
                text = path.read_text()
                self.assertIn("Judge the artifact against the rubric.", text)
                self.assertIn(subagents.MARKER, text)
                self.assertNotIn("model", text)
        codex = tomllib.loads(files["codex"].read_text())
        self.assertEqual(codex["name"], "blind-reviewer")
        self.assertEqual(codex["description"], 'Judges an artifact "blind"')
        self.assertIn("Judge the artifact", codex["developer_instructions"])
        self.assertIs(codex["features"]["shell_tool"], False)
        self.assertIn("tools: Read, Glob, Grep", files["claude"].read_text())
        self.assertIn("readonly: true", files["cursor"].read_text())
        self.assertIn('tools: ["read", "glob", "grep"]', files["kiro"].read_text())
        for tool in ("opencode", "kilo"):
            text = files[tool].read_text()
            for line in ("mode: subagent", "  edit: deny", "  bash: deny"):
                self.assertIn(line, text, tool)

    def test_every_agent_reaches_every_tool(self):
        self.install()
        for tool, path in self.rendered().items():
            with self.subTest(tool=tool):
                scout = path.with_name(f"scout{path.suffix}")
                self.assertIn("Report what answers the question.", scout.read_text())

    def test_an_agent_dropped_from_the_repository_is_removed_everywhere(self):
        self.install()
        (self.repo / "agents/scout.md").unlink()
        self.install()
        for tool, path in self.rendered().items():
            with self.subTest(tool=tool):
                self.assertFalse(path.with_name(f"scout{path.suffix}").exists())
                self.assertTrue(path.exists())

    def test_a_native_plugin_carries_its_own_copy(self):
        modes = {"claude": "plugin", "cursor": "plugin", "codex": "plugin"}
        wanted = subagents.targets({"claude", "cursor", "codex"}, modes)
        self.assertEqual(sorted(path.name for path in wanted), ["blind-reviewer.toml", "scout.toml"])

    def test_switching_to_the_native_plugin_drops_the_rendered_copy(self):
        self.install()
        subagents.sync(actions.Installer(), {"claude"}, {"claude": "plugin"})
        self.assertFalse(self.rendered()["claude"].exists())
        self.assertTrue(self.rendered()["codex"].exists())

    def test_an_agent_of_the_same_name_the_user_wrote_stays(self):
        mine = self.rendered()["opencode"]
        mine.parent.mkdir(parents=True)
        mine.write_text("my own reviewer\n")
        self.install()
        self.assertEqual(mine.read_text(), "my own reviewer\n")

    def test_uninstall_removes_only_rendered_agents(self):
        self.install()
        mine = self.home / ".cursor/agents/my-own.md"
        mine.write_text("mine\n")
        install.uninstall(actions.Installer())
        for path in self.rendered().values():
            self.assertFalse(path.exists(), path)
        self.assertTrue(mine.exists())


if __name__ == "__main__":
    unittest.main()
