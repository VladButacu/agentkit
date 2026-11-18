"""Guards for the distribution artifacts: plugin manifests, marketplaces and SKILL.md frontmatter."""

import re
import unittest
from pathlib import Path

import actions
import choices

PLUGIN_MANIFESTS = [".claude-plugin/plugin.json", ".codex-plugin/plugin.json",
                    ".cursor-plugin/plugin.json"]
NAME_PATTERN = re.compile(r"[a-z][a-z0-9-]*")
SKILL_KEYS = {"name", "description", "metadata", "license", "allowed-tools", "disable-model-invocation"}
SKILL_LINES = 500
READ_ONLY_TOOLS = {"Read", "Glob", "Grep"}
AGENT_KEYS = {"name", "description", "tools", "readonly"}
AUTOINVOKE = "opencode/autoinvoke: true"


def skill_roots() -> list[Path]:
    roots = [path.parent for path in (actions.REPO / "skills").glob("*/SKILL.md")]
    return roots + [path.parent for path in (actions.REPO / "plugins/obsidian").glob("*/SKILL.md")]


def frontmatter(path: Path) -> dict[str, str]:
    """Top-level frontmatter keys; indented continuation lines belong to their parent."""
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        raise AssertionError(f"Missing frontmatter block: {path}")
    fields = {}
    for line in lines[1:]:
        if line.strip() == "---":
            return fields
        if line[:1].isspace() or ":" not in line:
            continue
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip()
    raise AssertionError(f"Frontmatter block never closes: {path}")


class MetadataChecks(unittest.TestCase):
    def test_plugin_versions_match_release_manifest(self):
        version = actions.read_json(actions.REPO / ".release-please-manifest.json")["."]
        for name in PLUGIN_MANIFESTS:
            with self.subTest(manifest=name):
                plugin = actions.read_json(actions.REPO / name)
                self.assertEqual(plugin["name"], "agentkit")
                self.assertEqual(plugin["version"], version)
                skills = Path(plugin["skills"])
                # Every marketplace entry sources the plugin from the repository root.
                self.assertTrue(actions.REPO.joinpath(skills).is_dir(),
                                f"skills path from {name} does not exist")

    def test_claude_marketplace_structure(self):
        data = actions.read_json(actions.REPO / ".claude-plugin/marketplace.json")
        self.assertTrue(data.get("name"))
        self.assertTrue(data.get("owner", {}).get("name"))
        for plugin in data.get("plugins", []):
            with self.subTest(plugin=plugin.get("name")):
                for field in ("name", "source", "description"):
                    self.assertTrue(plugin.get(field), f"marketplace entry misses {field}")

    def test_agents_marketplace_structure(self):
        data = actions.read_json(actions.REPO / ".agents/plugins/marketplace.json")
        self.assertTrue(data.get("name"))
        self.assertTrue(data.get("interface", {}).get("displayName"))
        for plugin in data.get("plugins", []):
            with self.subTest(plugin=plugin.get("name")):
                self.assertTrue(plugin.get("name"))
                source = plugin.get("source")
                if isinstance(source, dict):
                    self.assertTrue(source.get("source") or source.get("url"))
                else:
                    self.assertTrue(source)

    def test_skill_frontmatter_valid(self):
        roots = skill_roots()
        self.assertGreater(len(roots), 10)
        for skill in roots:
            with self.subTest(skill=skill.name):
                fields = frontmatter(skill / "SKILL.md")
                self.assertEqual(fields.get("name"), skill.name)
                self.assertRegex(fields["name"], NAME_PATTERN)
                self.assertLessEqual(set(fields), SKILL_KEYS)
                description = fields.get("description")
                self.assertTrue(description, "description is required")
                self.assertLessEqual(len(description or ""), 1024)
                lines = (skill / "SKILL.md").read_text(encoding="utf-8").count("\n")
                self.assertLessEqual(lines, SKILL_LINES)

    def test_invocation_mode_agrees_across_tools(self):
        """A skill only a person starts says so to Claude, Codex and OpenCode alike; every other skill
        carries no Codex policy file, so no description is ever repeated there."""
        for skill in skill_roots():
            with self.subTest(skill=skill.name):
                text = (skill / "SKILL.md").read_text(encoding="utf-8")
                policy = skill / "agents/openai.yaml"
                if frontmatter(skill / "SKILL.md").get("disable-model-invocation") == "true":
                    self.assertIn("allow_implicit_invocation: false", policy.read_text(encoding="utf-8"))
                    self.assertNotIn(AUTOINVOKE, text)
                else:
                    self.assertFalse(policy.exists(), "a model-invoked skill needs no openai.yaml")
                    self.assertIn(AUTOINVOKE, text)

    def test_subagents_are_valid_and_reviewers_read_only(self):
        agents = sorted((actions.REPO / "agents").glob("*.md"))
        self.assertTrue(agents)
        for agent in agents:
            with self.subTest(agent=agent.stem):
                fields = frontmatter(agent)
                self.assertEqual(fields.get("name"), agent.stem)
                self.assertRegex(fields["name"], NAME_PATTERN)
                for key in ("description", "tools"):
                    self.assertTrue(fields.get(key), f"{key} is required")
                # The installer renders these keys for every tool; a model would pin one vendor's id,
                # so each subagent runs on the model of the session that dispatches it.
                self.assertLessEqual(set(fields), AGENT_KEYS)
                tools = {tool.strip() for tool in fields["tools"].split(",")}
                # Claude Code enforces read-only through tools and Cursor through readonly; both must agree.
                self.assertEqual(fields.get("readonly") == "true", tools <= READ_ONLY_TOOLS)
                if agent.stem.endswith("-reviewer"):
                    self.assertLessEqual(tools, READ_ONLY_TOOLS)

    def test_schema_fields_match_validator(self):
        schema = actions.read_json(actions.REPO / "plugins/manifest.schema.json")
        properties = set(schema["$defs"]["plugin"]["properties"])
        self.assertEqual(properties, choices.MANIFEST_FIELDS)


if __name__ == "__main__":
    unittest.main()
