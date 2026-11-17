"""Guards for the distribution artifacts: plugin manifests, marketplaces and SKILL.md frontmatter."""

import re
import unittest
from pathlib import Path

import actions
import choices

PLUGIN_MANIFESTS = [".claude-plugin/plugin.json", ".codex-plugin/plugin.json",
                    ".cursor-plugin/plugin.json"]
NAME_PATTERN = re.compile(r"[a-z][a-z0-9-]*")


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
        roots = [path.parent for path in (actions.REPO / "skills").glob("*/SKILL.md")]
        roots += [path.parent for path in (actions.REPO / "plugins/obsidian").glob("*/SKILL.md")]
        self.assertGreater(len(roots), 10)
        for skill in roots:
            with self.subTest(skill=skill.name):
                fields = frontmatter(skill / "SKILL.md")
                self.assertEqual(fields.get("name"), skill.name)
                self.assertRegex(fields["name"], NAME_PATTERN)
                description = fields.get("description")
                self.assertTrue(description, "description is required")
                self.assertLessEqual(len(description or ""), 1024)

    def test_schema_fields_match_validator(self):
        schema = actions.read_json(actions.REPO / "plugins/manifest.schema.json")
        properties = set(schema["$defs"]["plugin"]["properties"])
        self.assertEqual(properties, choices.MANIFEST_FIELDS)


if __name__ == "__main__":
    unittest.main()
