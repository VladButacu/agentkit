"""Checks for the shape of the vault template that vault-setup copies."""

import json
import unittest
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parents[1] / "vault-setup/vault"


class TemplateChecks(unittest.TestCase):
    def test_root_holds_only_the_start_page_rules_and_system_folder(self):
        notes = {path.name for path in TEMPLATE.iterdir() if not path.name.startswith(".")} - {"gitignore"}
        self.assertEqual(notes, {"Home.md", "AGENTS.md", "CLAUDE.md", "90 System"})

    def test_home_is_bookmarked(self):
        bookmarks = json.loads((TEMPLATE / ".obsidian/bookmarks.json").read_text())
        self.assertEqual([item["path"] for item in bookmarks["items"]], ["Home.md"])


if __name__ == "__main__":
    unittest.main()
