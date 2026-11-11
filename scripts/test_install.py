"""Isolated filesystem checks. Never starts agents, plugins or MCP servers."""

import contextlib
import io
import json
import pathlib
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import actions
import choices
import install
import instruction_block

NO_DREAM = {"runner": "none"}


def crew_root_count(entries: list[dict]) -> int:
    """agentkit's skills plus each plugin's skills folder and companion folder."""
    return 1 + sum(bool(e.get("skills")) + bool(e.get("companion")) for e in entries)


class InstallerFixture(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.home = Path(self.directory.name)
        self.repo = self.home / "repo"
        self.data = self.home / "data"
        self.sources = {}
        manifest = json.loads((actions.REPO / "plugins/manifest.json").read_text())
        self.local = {"skills", "opencode", "cli"}
        for name, entry in manifest.items():
            if name == "$schema":
                continue
            if entry.get("companion"):
                self.skill(self.repo / entry["companion"] / f"{name}-companion")
            if not self.local & entry.keys():
                continue
            source = self.data / "plugins" / name
            self.sources[name] = source
            if entry.get("skills"):
                self.skill(source / entry["skills"] / name)
        self.skill(self.repo / "skills/prose")
        self.skill(self.repo / "skills/makefile-generator")
        (self.repo / "AGENTS.md").write_text("Personal instructions\n")
        self.put(self.repo / "plugins/manifest.json", manifest)
        self.codex = self.home / ".codex"
        self.codex.mkdir()
        (self.codex / "config.toml").write_text(
            'approval_policy = "on-request"\n[plugins."superpowers@test"]\nenabled = true\n'
            '[plugins."ponytail@test"]\nenabled = true\n[plugins."fex@test"]\nenabled = true\n'
        )
        self.claude = self.home / ".claude"
        self.put(self.claude / "settings.json", {
            "permissions": {"deny": ["Bash(git push *)"]},
            "skillOverrides": {"prose": "off", "other": "off"},
            "enabledPlugins": {"superpowers@test": True, "ponytail@test": True, "fex@test": True},
        })
        self.config = self.home / ".config"
        self.put(self.config / "opencode/opencode.json", {"permissions": [{"effect": "deny"}], "mcp": {"servers": {}}})
        self.tools = {"codex": self.codex, "claude": self.claude,
                      "kiro-ide": self.home / ".kiro", "kiro-cli": self.home / ".kiro",
                      "crew": self.home / ".kiro/crew", "cursor": self.home / ".cursor",
                      "kilo": self.home / ".kilo", "opencode": self.config / "opencode"}
        for key, value in {"REPO": self.repo, "HOME": self.home, "DATA": self.data,
                           "STATE": self.home / "state", "CODEX": self.codex,
                           "CLAUDE": self.claude, "CONFIG": self.config, "TOOLS": self.tools,
                           "KIRO_IDE": ()}.items():
            replacement = patch.object(actions, key, value)
            replacement.start()
            self.addCleanup(replacement.stop)
        self.output = contextlib.redirect_stdout(io.StringIO())
        self.output.__enter__()
        self.addCleanup(self.output.__exit__, None, None, None)

    def skill(self, path):
        path.mkdir(parents=True)
        (path / "SKILL.md").write_text("---\nname: example\ndescription: Test fixture\n---\n")

    def put(self, path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value))

    def install(self, dry=False, requested: str | None = "all", tools=None, instructions=None,
                dream: dict | None = NO_DREAM):
        with patch.object(actions.Installer, "checkout", side_effect=lambda name, entry: self.sources[name]), \
             patch.object(actions.Installer, "desloppify"), \
             patch.object(shutil, "which", return_value=None):
            install.install(actions.Installer(dry), set(self.tools) if tools is None else tools,
                           requested, instructions, dream)

    def snapshot(self):
        return {str(path.relative_to(self.home)): ("link", str(path.resolve())) if actions.is_link(path)
                else ("file", path.read_bytes()) for path in self.home.rglob("*")
                if actions.is_link(path) or path.is_file()}


class InstallationChecks(InstallerFixture):
    def test_all_tools_preserve_settings_and_second_install_changes_nothing(self):
        before = (self.codex / "config.toml").read_bytes()
        self.install()
        self.assertEqual(before, (self.codex / "config.toml").read_bytes())
        settings = actions.read_json(self.claude / "settings.json")
        self.assertEqual(settings["skillOverrides"], {"other": "off"})
        self.assertEqual(settings["permissions"], {"deny": ["Bash(git push *)"]})
        manifest = json.loads((actions.REPO / "plugins/manifest.json").read_text())
        entries = [e for e in manifest.values() if isinstance(e, dict)]
        opencode = actions.read_json(self.config / "opencode/opencode.json")
        self.assertEqual(opencode["permissions"], [{"effect": "deny"}])
        self.assertEqual(len(opencode["plugins"]), sum(1 for e in entries if e.get("opencode")))
        self.assertEqual(len(actions.read_json(self.home / ".kiro/crew/config.json")["skills"]["extra_paths"]),
                         crew_root_count(entries))
        self.assertTrue(actions.is_link(self.home / ".kiro/skills/prose"))
        self.assertTrue(actions.is_link(self.home / ".kilo/skills/ponytail"))
        self.assertFalse((self.home / ".kilo/skills/prose").exists())
        self.assertFalse((self.home / ".agents/skills/superpowers").exists())
        # Marketplace-only plugins get no local checkout and no loose skill links.
        self.assertNotIn("fex", self.sources)
        self.assertFalse((self.home / ".kiro/skills/fex").exists())
        self.assertFalse((self.data / "plugins/fex").exists())
        snapshot = self.snapshot()
        self.install()
        self.assertEqual(snapshot, self.snapshot())

    def test_dry_run_makes_no_changes(self):
        snapshot = self.snapshot()
        self.install(dry=True)
        self.assertEqual(snapshot, self.snapshot())

    def test_plugin_selection_filters_every_surface(self):
        (self.home / "state").mkdir(exist_ok=True)
        manifest = json.loads((actions.REPO / "plugins/manifest.json").read_text())
        choices.store_selection({"ponytail"}, set(manifest) - {"$schema"})
        self.install(requested=None)
        crew_paths = actions.read_json(self.home / ".kiro/crew/config.json")["skills"]["extra_paths"]
        # Compare path parts: Windows writes these paths with backslashes.
        crew_parts = [Path(path).parts for path in crew_paths]
        self.assertTrue(any(parts[-2:] == ("ponytail", "skills") for parts in crew_parts))
        self.assertFalse(any("superpowers" in parts for parts in crew_parts))
        plugins = actions.read_json(self.config / "opencode/opencode.json")["plugins"]
        self.assertEqual([value for value in plugins if "ponytail" in value],
                         [str(self.sources["ponytail"] / ".opencode/plugins")])
        self.assertFalse(any("superpowers" in value for value in plugins))
        self.assertTrue(actions.is_link(self.home / ".kiro/skills/ponytail"))
        self.assertFalse((self.home / ".kiro/skills/brainstorming").exists())

    def test_install_asks_for_selection_when_none_stored(self):
        with patch.object(sys.stdin, "isatty", return_value=False), \
             patch.object(actions.Installer, "checkout", side_effect=lambda name, entry: self.sources[name]), \
             patch.object(actions.Installer, "desloppify"), \
             patch.object(shutil, "which", return_value=None), \
             self.assertRaises(ValueError) as raised:
            install.install(actions.Installer(), set(self.tools))
        self.assertIn("--plugins", str(raised.exception))
        self.assertIn("superpowers", str(raised.exception))

    def test_companion_skills_follow_their_plugin(self):
        manifest = json.loads((actions.REPO / "plugins/manifest.json").read_text())
        name, entry = next((name, entry) for name, entry in manifest.items()
                           if isinstance(entry, dict) and entry.get("companion"))
        skill = f"{name}-companion"
        roots = (self.home / ".agents/skills", self.claude / "skills", self.home / ".kiro/skills")
        crew = self.home / ".kiro/crew/config.json"
        folder = (self.repo / entry["companion"]).resolve()

        def crew_roots():
            return {Path(path).resolve() for path in actions.read_json(crew)["skills"]["extra_paths"]}

        self.install()
        for root in roots:
            self.assertTrue(actions.is_link(root / skill), root)
        self.assertIn(folder, crew_roots())
        self.install(requested="ponytail")
        for root in roots:
            self.assertFalse(actions.present(root / skill), root)
        self.assertNotIn(folder, crew_roots())

    def test_local_notes_move_from_the_clone_to_the_config_folder(self):
        notes = self.config / "agentkit/AGENTS.local.md"
        (self.repo / "AGENTS.local.md").write_text("flavour: zorp\n")
        self.install(dry=True)
        self.assertFalse(notes.exists())
        self.install()
        self.assertEqual(notes.read_text(), "flavour: zorp\n")
        self.assertFalse((self.repo / "AGENTS.local.md").exists())
        (self.repo / "AGENTS.local.md").write_text("flavour: quux\n")
        with contextlib.redirect_stdout(io.StringIO()) as output:
            self.install()
        self.assertIn("PENDING", output.getvalue())
        self.assertEqual(notes.read_text(), "flavour: zorp\n")
        self.assertTrue((self.repo / "AGENTS.local.md").exists())

    def test_check_update_prints_only_when_behind_and_caches(self):
        commands = []

        def fake_run(args):
            commands.append(" ".join(args))
            if "rev-list" in args:
                return "3"
            return "url"

        with patch.object(actions, "run", side_effect=fake_run):
            install.check_update()
        self.assertEqual(len([c for c in commands if "fetch" in c]), 1)
        marker = self.home / "state/update-check.json"
        self.assertTrue(marker.exists())
        with patch.object(actions, "run", side_effect=fake_run) as again, \
             contextlib.redirect_stdout(io.StringIO()) as output:
            install.check_update()
        self.assertIn("3 commits behind", output.getvalue())
        self.assertEqual(len([c for c in again.call_args_list
                              if "fetch" in c.args[0]]), 0)

    def test_uninstall_dry_run_changes_nothing(self):
        self.install()
        snapshot = self.snapshot()
        install.uninstall(actions.Installer(dry_run=True))
        self.assertEqual(snapshot, self.snapshot())

    def test_uninstall_removes_wiring_and_keeps_user_content(self):
        foreign_skill = self.claude / "skills/personal"
        self.skill(foreign_skill)
        foreign_hook = {"matcher": "startup", "hooks": [{"type": "command", "command": "echo hi"}]}
        settings = actions.read_json(self.claude / "settings.json")
        settings.setdefault("hooks", {}).setdefault("SessionStart", []).append(foreign_hook)
        (self.claude / "settings.json").write_text(json.dumps(settings))
        crew = self.home / ".kiro/crew/config.json"
        self.install()
        crew_config = actions.read_json(crew)
        crew_config["skills"]["extra_paths"].append(str(self.home / "my-skills"))
        crew.write_text(json.dumps(crew_config))
        install.uninstall(actions.Installer())
        for root in (self.home / ".agents/skills", self.claude / "skills",
                     self.home / ".kiro/skills", self.home / ".cursor/skills",
                     self.home / ".kilo/skills"):
            self.assertTrue(all(not actions.is_link(t) for t in root.iterdir()), root)
        self.assertTrue(foreign_skill.is_dir())
        self.assertFalse((self.codex / "AGENTS.md").exists())
        self.assertFalse((self.claude / "CLAUDE.md").exists())
        sessions = actions.read_json(self.claude / "settings.json")["hooks"]["SessionStart"]
        self.assertEqual(sessions, [foreign_hook])
        self.assertEqual(actions.read_json(crew)["skills"]["extra_paths"], [str(self.home / "my-skills")])
        self.assertEqual(actions.read_json(self.config / "opencode/opencode.json")["plugins"], [])
        self.assertFalse((self.home / ".kiro/agents/agentkit.json").exists())
        self.assertTrue((self.data / "plugins/superpowers").is_dir())

    def test_claude_update_hook_registered_once_and_foreign_hooks_kept(self):
        foreign = {"matcher": "startup", "hooks": [{"type": "command", "command": "echo hi"}]}
        settings = actions.read_json(self.claude / "settings.json")
        settings.setdefault("hooks", {}).setdefault("SessionStart", []).append(foreign)
        (self.claude / "settings.json").write_text(json.dumps(settings))
        self.install()
        self.install()
        sessions = actions.read_json(self.claude / "settings.json")["hooks"]["SessionStart"]
        ours = [hook for entry in sessions for hook in entry.get("hooks", [])
                if install.is_update_hook(hook)]
        self.assertEqual(ours, [install.update_hook()])
        self.assertIn(foreign, sessions)

    def test_checkout_dry_run_survives_stale_cache(self):
        stale = self.data / "plugins/superpowers"
        self.assertTrue(stale.is_dir())  # fixture cache has no .git, so it counts as stale
        (stale / "notagit").write_text("leftover")
        with patch.object(actions, "run", side_effect=RuntimeError("must not touch git")):
            destination = actions.Installer(dry_run=True).checkout("superpowers", {"repository": "https://e.com/x.git"})
        self.assertEqual(destination, stale)
        self.assertTrue((stale / "notagit").exists())

    def test_checkout_clones_when_absent(self):
        commands = []

        def fake_run(args):
            commands.append(" ".join(args))
            if args[0] == "git" and args[1] == "init":
                pathlib.Path(args[-1]).mkdir(parents=True, exist_ok=True)
            return "revision"

        with patch.object(actions, "run", side_effect=fake_run):
            actions.Installer().checkout("example", {"repository": "https://e.com/x.git"})
        self.assertTrue(any("git init" in c for c in commands))
        self.assertTrue(any("remote add origin https://e.com/x.git" in c for c in commands))
        self.assertTrue(any("fetch" in c and "HEAD" in c for c in commands))

    def test_kiro_ide_and_cli_detected_separately(self):
        (self.home / ".kiro").mkdir(exist_ok=True)
        with patch.object(shutil, "which", return_value=None):
            selected = choices.detect_tools()
            self.assertNotIn("kiro-ide", selected)
            self.assertNotIn("kiro-cli", selected)
        with patch.object(shutil, "which",
                          side_effect=lambda name: "/bin/kiro-cli" if name == "kiro-cli" else None):
            selected = choices.detect_tools()
            self.assertIn("kiro-cli", selected)
            self.assertNotIn("kiro-ide", selected)
        with patch.object(shutil, "which",
                          side_effect=lambda name: "/bin/kiro" if name == "kiro" else None):
            selected = choices.detect_tools()
            self.assertIn("kiro-ide", selected)
            self.assertNotIn("kiro-cli", selected)

    def test_kilo_detected_by_cli_config_or_extension(self):
        with patch.object(shutil, "which",
                          side_effect=lambda name: "/bin/kilo" if name == "kilo" else None):
            self.assertIn("kilo", choices.detect_tools())
        with patch.object(shutil, "which", return_value=None):
            self.assertNotIn("kilo", choices.detect_tools())
            (self.config / "kilo").mkdir(parents=True)
            self.assertIn("kilo", choices.detect_tools())
            (self.config / "kilo").rmdir()
            (self.home / ".vscode/extensions/kilocode.kilo-code-1.0.0").mkdir(parents=True)
            self.assertIn("kilo", choices.detect_tools())

    def test_write_json_backs_up_and_refuses_unexpected_shapes(self):
        path = self.home / ".config/opencode/opencode.json"
        self.assertEqual(actions.read_json(path)["permissions"], [{"effect": "deny"}])
        installer = actions.Installer()
        installer.write_json(path, {"permissions": [{"effect": "deny"}], "plugins": []})
        backups = list((self.home / "state/backups").rglob("opencode.json"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(actions.read_json(backups[0])["permissions"], [{"effect": "deny"}])
        (self.config / "opencode/opencode.jsonc").write_text('{"plugin": ["x"]}\n')
        with self.assertRaises(ValueError):
            self.install()

    def test_native_plugin_failure_falls_back_to_skills(self):
        (self.codex / "config.toml").write_text('approval_policy = "on-request"\n')
        with patch.object(shutil, "which", return_value="/usr/bin/codex"), \
             patch.object(actions, "run", side_effect=RuntimeError("marketplace unavailable")):
            result = actions.Installer().native_plugin(
                "codex", "superpowers", "https://example.com/superpowers.git", "superpowers-dev")
        self.assertFalse(result)

    def test_desloppify_keeps_existing_cli(self):
        with patch.object(shutil, "which", return_value="/usr/bin/desloppify"):
            actions.Installer().desloppify(self.sources["desloppify"])
        self.assertFalse((self.data / "desloppify").exists())

    def test_checkout_refreshes_existing_repo_from_upstream_head(self):
        destination = self.data / "plugins/example"
        (destination / ".git").mkdir(parents=True)
        entry = {"repository": "https://example.com/example.git"}
        commands = []

        def fake_run(args):
            commands.append(" ".join(args))
            if args[3:] == ["remote", "get-url", "origin"]:
                return entry["repository"]
            return "" if args[3:] == ["status", "--porcelain"] else "revision"

        with patch.object(actions, "run", side_effect=fake_run):
            actions.Installer().checkout("example", entry)
        self.assertTrue(any("fetch" in c and "HEAD" in c for c in commands))
        self.assertTrue(any("reset" in c and "FETCH_HEAD" in c for c in commands))

    def test_checkout_refuses_edited_or_foreign_repositories(self):
        destination = self.data / "plugins/example"
        (destination / ".git").mkdir(parents=True)
        entry = {"repository": "https://example.com/example.git"}
        for remote, status in (("https://other.example/x.git", ""),
                               ("https://example.com/example.git", " M file")):
            commands = {" ".join(["git", "-C", str(destination), "remote", "get-url", "origin"]): remote,
                        " ".join(["git", "-C", str(destination), "status", "--porcelain"]): status}
            with patch.object(actions, "run", side_effect=lambda args, table=commands: table[" ".join(args)]), \
                 self.assertRaises(ValueError):
                actions.Installer().checkout("example", entry)


    def test_manifest_bump_repoints_managed_plugin_roots(self):
        self.install()
        stale = str(self.data / "plugins/superpowers/deadbeef0000/skills")
        old_skill = self.home / ".kiro/skills/superpowers"
        old_skill.parent.mkdir(parents=True, exist_ok=True)
        actions.remove_link(old_skill)
        retired = self.data / "plugins/superpowers/deadbeef0000/skills/superpowers"
        self.skill(retired)
        actions.create_link(retired, old_skill)
        crew = self.home / ".kiro/crew/config.json"
        config = actions.read_json(crew)
        config["skills"]["extra_paths"] = [stale] + config["skills"]["extra_paths"]
        crew.write_text(json.dumps(config))
        opencode = self.config / "opencode/opencode.json"
        settings = actions.read_json(opencode)
        settings["plugins"] = [str(self.data / "plugins/superpowers/deadbeef0000")] + settings["plugins"]
        opencode.write_text(json.dumps(settings))
        self.install()
        manifest = json.loads((actions.REPO / "plugins/manifest.json").read_text())
        entries = [e for e in manifest.values() if isinstance(e, dict)]
        crew_paths = actions.read_json(crew)["skills"]["extra_paths"]
        self.assertNotIn(stale, crew_paths)
        self.assertEqual(len(crew_paths), crew_root_count(entries))
        plugins = actions.read_json(opencode)["plugins"]
        self.assertFalse(any("deadbeef" in value for value in plugins))
        self.assertEqual(len(plugins), sum(1 for e in entries if e.get("opencode")))
        self.assertEqual(old_skill.resolve(),
                         (self.sources["superpowers"] / "skills/superpowers").resolve())

    def test_retirement_removes_only_owned_links(self):
        root = self.home / ".agents/skills"
        retired = self.repo / "skills/retired"
        self.skill(retired)
        actions.create_link(retired, root / "retired")
        shutil.rmtree(retired)
        self.skill(root / "personal")
        actions.Installer().sync_links(root, actions.skills(self.repo / "skills"))
        self.assertFalse(actions.present(root / "retired"))
        self.assertTrue((root / "personal/SKILL.md").exists())

    def instruction_block(self, body):
        return instruction_block.block(self.repo / "AGENTS.md", body)

    def test_instruction_files_carry_agentkit_block_and_refresh(self):
        self.install()
        pointer = "@" + (self.repo / "AGENTS.md").as_posix().replace(" ", "\\ ")
        self.assertEqual((self.claude / "CLAUDE.md").read_text(), self.instruction_block(pointer))
        self.assertEqual((self.codex / "AGENTS.md").read_text(),
                         self.instruction_block("Personal instructions"))
        (self.repo / "AGENTS.md").write_text("Revised instructions\n")
        self.install()
        self.assertEqual((self.codex / "AGENTS.md").read_text(),
                         self.instruction_block("Revised instructions"))

    def test_foreign_instructions_need_a_choice_before_anything_changes(self):
        (self.codex / "AGENTS.md").write_text("My codex rules\n")
        snapshot = self.snapshot()
        with patch.object(sys.stdin, "isatty", return_value=False), \
             self.assertRaises(ValueError) as raised:
            self.install()
        self.assertIn("--instructions", str(raised.exception))
        # Only the installer's own state may hold the plugin answer given before the question.
        after = {path: value for path, value in self.snapshot().items() if not path.startswith("state")}
        self.assertEqual(snapshot, after)

    def test_foreign_instructions_keep_append_and_replace(self):
        mine = "My codex rules\n"
        (self.codex / "AGENTS.md").write_text(mine)
        self.install(instructions="keep")
        self.assertEqual((self.codex / "AGENTS.md").read_text(), mine)
        self.install(instructions="append")
        self.assertEqual((self.codex / "AGENTS.md").read_text(),
                         f"{mine}\n{self.instruction_block('Personal instructions')}")
        install.uninstall(actions.Installer())
        self.assertEqual((self.codex / "AGENTS.md").read_text(), mine)
        self.install(instructions="replace")
        self.assertEqual((self.codex / "AGENTS.md").read_text(),
                         self.instruction_block("Personal instructions"))
        backups = list((self.home / "state/backups").rglob("AGENTS.md"))
        self.assertIn(mine, [path.read_text() for path in backups])
        install.uninstall(actions.Installer())
        self.assertFalse((self.codex / "AGENTS.md").exists())

    def test_legacy_instruction_symlinks_become_blocks(self):
        try:
            (self.codex / "AGENTS.md").symlink_to(self.repo / "AGENTS.md")
        except OSError:
            self.skipTest("file symlinks need privileges on this machine")
        self.install()
        self.assertFalse((self.codex / "AGENTS.md").is_symlink())
        self.assertEqual((self.codex / "AGENTS.md").read_text(),
                         self.instruction_block("Personal instructions"))

    def test_only_installed_tools_receive_content(self):
        before = self.snapshot()
        self.install(tools=set())
        self.assertEqual(before, self.snapshot())
        self.install(tools={"codex"})
        changed = {path for path, value in self.snapshot().items() if before.get(path) != value}
        roots = {Path(path).parts[0] for path in changed}
        self.assertLessEqual(roots, {".agents", ".codex", "data", "state"}, changed)
        self.assertTrue(actions.is_link(self.home / ".agents/skills/prose"))
        shutil.rmtree(self.home / ".agents")
        self.install(tools={"claude"})
        self.assertFalse((self.home / ".agents").exists())
        self.assertTrue(actions.is_link(self.claude / "skills/prose"))

    def test_skills_fall_back_to_marked_copies_that_uninstall_removes(self):
        with patch.object(actions, "make_link", side_effect=OSError("no link privilege")):
            self.install()
        copy = self.home / ".kiro/skills/prose"
        self.assertFalse(actions.is_link(copy))
        self.assertTrue((copy / actions.MARKER).is_file())
        (self.repo / "skills/prose/SKILL.md").write_text("revised")
        with patch.object(actions, "make_link", side_effect=OSError("no link privilege")):
            self.install()
        self.assertEqual((copy / "SKILL.md").read_text(), "revised")
        install.uninstall(actions.Installer())
        self.assertFalse(actions.present(copy))

    def test_collision_refuses_to_replace_user_content(self):
        root = self.home / ".agents/skills"
        self.skill(root / "prose")
        snapshot = self.snapshot()
        with self.assertRaises(ValueError):
            actions.Installer().sync_links(root, actions.skills(self.repo / "skills"))
        self.assertEqual(snapshot, self.snapshot())


if __name__ == "__main__":
    unittest.main()
