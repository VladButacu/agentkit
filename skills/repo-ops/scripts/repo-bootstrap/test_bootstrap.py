"""Repository layout checks. Run with: python3 -m unittest discover -s skills/repo-ops/scripts/repo-bootstrap"""

import contextlib
import io
import os
import tempfile
import unittest
from pathlib import Path

from bootstrap import apply, findings, main

LINK = ".claude/skills"
POSIX = os.name != "nt"


def messages(root, links=(LINK,)):
    return [finding.message for finding in findings(root, list(links))]


def fixture_project(root):
    """A project that follows the layout, so every check passes."""
    (root / "AGENTS.md").write_text("Rules. See AGENTS.local.md for overrides.\n", encoding="utf-8")
    (root / "CLAUDE.md").write_text("@AGENTS.md\n", encoding="utf-8")
    (root / ".agents" / "skills").mkdir(parents=True)
    (root / ".gitignore").write_text(f"AGENTS.local.md\n{LINK}\n", encoding="utf-8")
    if POSIX:
        (root / ".claude").mkdir()
        os.symlink(os.path.join("..", ".agents", "skills"), root / LINK, target_is_directory=True)


class LayoutChecks(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.root = Path(self.folder.name)

    def tearDown(self):
        self.folder.cleanup()

    def test_complete_project_has_no_findings(self):
        fixture_project(self.root)
        if not POSIX:
            self.skipTest("link fixture needs symlinks")
        self.assertEqual(messages(self.root), [])

    def test_empty_project_reports_every_gap(self):
        found = messages(self.root)
        self.assertTrue(any("AGENTS.md is missing" in m for m in found), found)
        self.assertTrue(any("CLAUDE.md" in m for m in found), found)
        self.assertTrue(any(".agents/skills" in m for m in found), found)
        self.assertTrue(any("AGENTS.local.md" in m and ".gitignore" in m for m in found), found)
        self.assertTrue(any(LINK in m for m in found), found)

    def test_apply_creates_what_it_can_and_leaves_agents_md_to_the_author(self):
        apply(self.root, [LINK])
        self.assertEqual((self.root / "CLAUDE.md").read_text(encoding="utf-8"), "@AGENTS.md\n")
        self.assertTrue((self.root / ".agents" / "skills").is_dir())
        self.assertFalse((self.root / "AGENTS.md").exists())
        remaining = messages(self.root)
        self.assertEqual(remaining, ["AGENTS.md is missing; write the project's rulebook"], remaining)

    @unittest.skipUnless(POSIX, "link fixture needs symlinks")
    def test_apply_link_resolves_to_the_shared_skills_folder(self):
        apply(self.root, [LINK])
        self.assertEqual((self.root / LINK).resolve(), (self.root / ".agents" / "skills").resolve())

    def test_apply_is_idempotent_and_keeps_existing_gitignore_lines(self):
        (self.root / ".gitignore").write_text("node_modules/\n", encoding="utf-8")
        apply(self.root, [LINK])
        apply(self.root, [LINK])
        lines = (self.root / ".gitignore").read_text(encoding="utf-8").splitlines()
        self.assertEqual(lines.count("AGENTS.local.md"), 1)
        self.assertEqual(lines.count(LINK), 1)
        self.assertEqual(lines[0], "node_modules/")

    def test_existing_claude_md_with_other_content_is_not_overwritten(self):
        (self.root / "CLAUDE.md").write_text("# Project notes\n\nDo things.\n", encoding="utf-8")
        apply(self.root, [LINK])
        self.assertEqual((self.root / "CLAUDE.md").read_text(encoding="utf-8"), "# Project notes\n\nDo things.\n")
        self.assertTrue(any("CLAUDE.md must contain only" in m for m in messages(self.root)))

    def test_agents_md_must_mention_local_overrides(self):
        fixture_project(self.root)
        (self.root / "AGENTS.md").write_text("Rules only.\n", encoding="utf-8")
        self.assertTrue(any("AGENTS.local.md" in m and "AGENTS.md" in m for m in messages(self.root)))

    @unittest.skipUnless(POSIX, "link fixture needs symlinks")
    def test_link_pointing_elsewhere_is_reported_not_removed(self):
        fixture_project(self.root)
        (self.root / LINK).unlink()
        (self.root / "other").mkdir()
        os.symlink("../other", self.root / LINK, target_is_directory=True)
        found = messages(self.root)
        self.assertTrue(any("does not point to .agents/skills" in m for m in found), found)
        apply(self.root, [LINK])
        self.assertTrue(os.path.islink(self.root / LINK))
        self.assertEqual(os.readlink(self.root / LINK), "../other")

    def test_env_file_without_worktreeinclude_is_reported_not_created(self):
        fixture_project(self.root)
        (self.root / ".env.local").write_text("SECRET=1\n", encoding="utf-8")
        found = messages(self.root)
        self.assertTrue(any(".worktreeinclude" in m for m in found), found)
        apply(self.root, [LINK])
        self.assertFalse((self.root / ".worktreeinclude").exists())


class Command(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.root = Path(self.folder.name)

    def tearDown(self):
        self.folder.cleanup()

    def run_main(self, argv):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            status = main(argv)
        return status, output.getvalue()

    def test_check_exits_one_when_something_is_missing(self):
        status, output = self.run_main(["check", "--root", str(self.root)])
        self.assertEqual(status, 1)
        self.assertIn("CLAUDE.md", output)

    @unittest.skipUnless(POSIX, "link fixture needs symlinks")
    def test_check_exits_zero_on_a_complete_project(self):
        fixture_project(self.root)
        status, output = self.run_main(["check", "--root", str(self.root)])
        self.assertEqual(status, 0, output)
        self.assertIn("layout OK", output)


if __name__ == "__main__":
    unittest.main()
