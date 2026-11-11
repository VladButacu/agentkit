"""Unit checks for the instruction block, the plugin and instruction-file questions and the link helpers,
on isolated filesystems."""

import contextlib
import io
import subprocess
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


class PluginChoiceChecks(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        state = patch.object(actions, "STATE", Path(directory.name) / "state")
        state.start()
        self.addCleanup(state.stop)
        output = contextlib.redirect_stdout(io.StringIO())
        output.__enter__()
        self.addCleanup(output.__exit__, None, None, None)

    def test_plugin_selection_validates_names(self):
        manifest = {"superpowers": {"repository": "https://example.com/s.git", "description": "d"}}
        with self.assertRaises(ValueError):
            choices.select_plugins(manifest, "spiderpowers")
        choices.store_selection(set(), set(manifest))
        self.assertEqual(choices.select_plugins(manifest, None), set())

    def test_new_plugin_is_asked_about_despite_a_saved_selection(self):
        manifest = {"old": {"repository": "https://example.com/o.git", "description": "o"},
                    "new": {"repository": "https://example.com/n.git", "description": "n"}}
        # A selection saved before offers were recorded counts its plugins as offered.
        actions.STATE.mkdir(exist_ok=True)
        (actions.STATE / "plugins.json").write_text('{"selected": ["old"]}')
        with patch.object(sys.stdin, "isatty", return_value=False), \
             self.assertRaises(ValueError) as raised:
            choices.select_plugins(manifest, None)
        message = str(raised.exception)
        self.assertIn("new (n)", message)
        self.assertNotIn("old (o)", message)
        self.assertIn("--plugins new,old", message)
        self.assertIn("--plugins old ", message)
        with patch.object(sys.stdin, "isatty", return_value=True), \
             patch("builtins.input", return_value="n"):
            self.assertEqual(choices.select_plugins(manifest, None), {"old"})
        with patch.object(sys.stdin, "isatty", return_value=False):
            self.assertEqual(choices.select_plugins(manifest, None), {"old"})

    def test_manifest_validation_rejects_bad_entries(self):
        with self.assertRaises(ValueError):
            choices.validate_manifest({"Bad-Name": {"repository": "https://example.com/x.git"}})
        with self.assertRaises(ValueError):
            choices.validate_manifest({"x": {"marketplace": "y"}})
        with self.assertRaises(ValueError):
            choices.validate_manifest({"x": {"repository": "https://example.com/x.git", "extra": True}})
        with self.assertRaises(ValueError):
            choices.validate_manifest({"x": {"repository": "git@example.com/x.git"}})
        for companion in ("../outside", "/absolute", ""):
            with self.assertRaises(ValueError):
                choices.validate_manifest({"x": {"repository": "https://example.com/x.git",
                                                 "companion": companion}})
        choices.validate_manifest({"$schema": "./manifest.schema.json",
                                  "x": {"repository": "https://example.com/x.git"}})


class LauncherChecks(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        data = patch.object(actions, "DATA", Path(directory.name) / "data")
        data.start()
        self.addCleanup(data.stop)
        output = contextlib.redirect_stdout(io.StringIO())
        output.__enter__()
        self.addCleanup(output.__exit__, None, None, None)

    def run_launcher(self, *args: str) -> str:
        return subprocess.run([str(actions.python_launcher()), *args], capture_output=True, text=True,
                              check=True, timeout=60).stdout.strip()

    def test_launcher_finds_a_python_after_the_install_time_one_is_gone(self):
        with patch.object(sys, "executable", str(Path(tempfile.gettempdir()) / "removed/python3.99")):
            actions.Installer().write_launcher()
        self.assertEqual(self.run_launcher("-c", "import sys; print(sys.version_info >= (3, 11))"), "True")

    def test_launcher_passes_arguments_and_stdin_through(self):
        actions.Installer().write_launcher()
        result = subprocess.run([str(actions.python_launcher()), "-c",
                                 "import sys; print(sys.argv[1], sys.stdin.read())", "flonk"],
                                input="zibble", capture_output=True, text=True, check=True, timeout=60)
        self.assertEqual(result.stdout.strip(), "flonk zibble")

    def test_dry_run_writes_no_launcher(self):
        actions.Installer(dry_run=True).write_launcher()
        self.assertFalse(actions.python_launcher().exists())


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
