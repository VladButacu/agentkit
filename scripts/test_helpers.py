"""Unit checks for the instruction block, the instruction-file questions and the link helpers,
on isolated filesystems."""

import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import actions
import choices
import instruction_block as block

SOURCE = Path("/clone/AGENTS.md")


class InstructionBlockChecks(unittest.TestCase):
    def test_render_creates_refreshes_and_respects_the_mode(self):
        ours = block.block(SOURCE, "rules v1")
        self.assertEqual(block.render(None, SOURCE, "rules v1", "keep"), ours)
        mine = "# Mine\n\nmy rule\n"
        self.assertIsNone(block.render(mine, SOURCE, "rules v1", "keep"))
        self.assertEqual(block.render(mine, SOURCE, "rules v1", "replace"), ours)
        appended = block.render(mine, SOURCE, "rules v1", "append")
        assert appended is not None
        self.assertEqual(appended, f"{mine}\n{ours}")
        # Once our block is present, refreshes touch only the block whatever the mode.
        refreshed = block.render(appended + "\nafter\n", SOURCE, "rules v2", "keep")
        self.assertEqual(refreshed, f"{mine}\n{block.block(SOURCE, 'rules v2')}\nafter\n")

    def test_strip_returns_the_user_text_only(self):
        mine = "# Mine\n\nmy rule\n"
        appended = block.render(mine, SOURCE, "rules", "append")
        assert appended is not None
        self.assertEqual(block.strip(appended), mine)
        self.assertEqual(block.strip(block.block(SOURCE, "rules")), "")
        self.assertIsNone(block.strip(mine))


class ChoiceChecks(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.store = self.root / "state/instructions.json"
        self.mine = self.root / "AGENTS.md"
        self.mine.write_text("my rule\n")
        self.ours = self.root / "CLAUDE.md"
        self.ours.write_text(block.block(SOURCE, "rules"))
        self.absent = self.root / "missing.md"
        self.paths = [self.mine, self.ours, self.absent]
        output = contextlib.redirect_stdout(io.StringIO())
        output.__enter__()
        self.addCleanup(output.__exit__, None, None, None)

    def choose(self, requested=None, tty=False, answer=""):
        with patch.object(sys.stdin, "isatty", return_value=tty), \
             patch("builtins.input", return_value=answer):
            return choices.choose_instruction_modes(self.paths, requested, self.store, persist=True)

    def test_without_a_terminal_the_question_comes_from_the_process(self):
        with self.assertRaises(ValueError) as raised:
            self.choose()
        self.assertIn("--instructions append", str(raised.exception))
        self.assertFalse(self.store.exists())

    def test_only_foreign_files_are_asked_about(self):
        self.assertEqual(self.choose(requested="append"), {self.mine: "append"})
        self.assertEqual(self.choose(tty=True, answer="replace"), {self.mine: "replace"})
        with self.assertRaises(ValueError):
            self.choose(tty=True, answer="merge")

    def test_keep_is_remembered_until_another_mode_is_requested(self):
        self.assertEqual(self.choose(tty=True), {self.mine: "keep"})
        self.assertEqual(self.choose(), {self.mine: "keep"})
        self.assertEqual(self.choose(requested="append"), {self.mine: "append"})
        with self.assertRaises(ValueError):
            self.choose()


class LinkChecks(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        self.source = root / "source/skill"
        self.source.mkdir(parents=True)
        (self.source / "SKILL.md").write_text("v1")
        self.target = root / "tool/skills/skill"

    def test_link_points_at_the_source_and_removal_keeps_it(self):
        self.assertTrue(actions.create_link(self.source, self.target))
        self.assertTrue(actions.is_link(self.target))
        self.assertEqual(actions.link_origin(self.target), self.source.resolve())
        actions.remove_link(self.target)
        self.assertFalse(actions.present(self.target))
        self.assertTrue((self.source / "SKILL.md").exists())

    def test_copy_fallback_is_marked_with_its_source(self):
        with patch.object(actions, "make_link", side_effect=OSError("no link privilege")):
            self.assertFalse(actions.create_link(self.source, self.target))
        self.assertFalse(actions.is_link(self.target))
        self.assertEqual((self.target / "SKILL.md").read_text(), "v1")
        self.assertEqual(actions.link_origin(self.target), self.source.resolve())
        self.assertEqual([p.name for p in self.target.parent.iterdir()], ["skill"])
        actions.remove_link(self.target)
        self.assertFalse(actions.present(self.target))
        self.assertTrue((self.source / "SKILL.md").exists())

    def test_plain_directories_have_no_origin(self):
        self.target.mkdir(parents=True)
        self.assertIsNone(actions.link_origin(self.target))


if __name__ == "__main__":
    unittest.main()
