"""Isolated filesystem checks. Never starts agents, plugins or MCP servers."""

import contextlib
import importlib.util
import io
import json
import pathlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("installer", Path(__file__).with_name("install.py"))
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class InstallationChecks(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.home = Path(self.directory.name)
        self.repo = self.home / "repo"
        self.data = self.home / "data"
        self.sources = {}
        manifest = json.loads((module.REPO / "plugins/manifest.json").read_text())
        self.local = {"skills", "opencode", "cli"}
        for name, entry in manifest.items():
            if name == "$schema":
                continue
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
            replacement = patch.object(module, key, value)
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

    def install(self, dry=False, requested: str | None = "all"):
        with patch.object(module.Installer, "checkout", side_effect=lambda name, entry: self.sources[name]), \
             patch.object(module.Installer, "desloppify"), \
             patch.object(module.shutil, "which", return_value=None):
            module.install(module.Installer(dry), set(self.tools), requested)
    def snapshot(self):
        return {str(path.relative_to(self.home)): ("link", str(path.readlink())) if path.is_symlink()
                else ("file", path.read_bytes()) for path in self.home.rglob("*")
                if path.is_symlink() or path.is_file()}

    def test_all_tools_preserve_settings_and_second_install_changes_nothing(self):
        before = (self.codex / "config.toml").read_bytes()
        self.install()
        self.assertEqual(before, (self.codex / "config.toml").read_bytes())
        settings = module.read_json(self.claude / "settings.json")
        self.assertEqual(settings["skillOverrides"], {"other": "off"})
        self.assertEqual(settings["permissions"], {"deny": ["Bash(git push *)"]})
        manifest = json.loads((module.REPO / "plugins/manifest.json").read_text())
        entries = [e for e in manifest.values() if isinstance(e, dict)]
        opencode = module.read_json(self.config / "opencode/opencode.json")
        self.assertEqual(opencode["permissions"], [{"effect": "deny"}])
        self.assertEqual(len(opencode["plugins"]), sum(1 for e in entries if e.get("opencode")))
        self.assertEqual(len(module.read_json(self.home / ".kiro/crew/config.json")["skills"]["extra_paths"]),
                         1 + sum(1 for e in entries if e.get("skills")))
        self.assertTrue((self.home / ".kiro/skills/prose").is_symlink())
        self.assertTrue((self.home / ".kilo/skills/ponytail").is_symlink())
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
        (self.home / "state/plugins.json").write_text('{"selected": ["ponytail"]}')
        self.install(requested=None)
        crew_paths = module.read_json(self.home / ".kiro/crew/config.json")["skills"]["extra_paths"]
        self.assertTrue(any("/ponytail/skills" in path for path in crew_paths))
        self.assertFalse(any("/superpowers" in path for path in crew_paths))
        plugins = module.read_json(self.config / "opencode/opencode.json")["plugins"]
        self.assertEqual([value for value in plugins if "ponytail" in value],
                         [str(self.sources["ponytail"] / ".opencode/plugins")])
        self.assertFalse(any("superpowers" in value for value in plugins))
        self.assertTrue((self.home / ".kiro/skills/ponytail").is_symlink())
        self.assertFalse((self.home / ".kiro/skills/brainstorming").exists())

    def test_install_asks_for_selection_when_none_stored(self):
        with patch.object(module.sys.stdin, "isatty", return_value=False), \
             patch.object(module.Installer, "checkout", side_effect=lambda name, entry: self.sources[name]), \
             patch.object(module.Installer, "desloppify"), \
             patch.object(module.shutil, "which", return_value=None), \
             self.assertRaises(ValueError) as raised:
            module.install(module.Installer(), set(self.tools))
        self.assertIn("--plugins", str(raised.exception))
        self.assertIn("superpowers", str(raised.exception))

    def test_plugin_selection_validates_names(self):
        manifest = {"superpowers": {"repository": "https://example.com/s.git", "description": "d"}}
        with self.assertRaises(ValueError):
            module.select_plugins(manifest, "spiderpowers")
        module.store_selection(set())
        self.assertEqual(module.select_plugins(manifest, None), set())

    def test_check_update_prints_only_when_behind_and_caches(self):
        commands = []

        def fake_run(args):
            commands.append(" ".join(args))
            if "rev-list" in args:
                return "3"
            return "url"

        with patch.object(module, "run", side_effect=fake_run):
            module.check_update()
        self.assertEqual(len([c for c in commands if "fetch" in c]), 1)
        marker = self.home / "state/update-check.json"
        self.assertTrue(marker.exists())
        with patch.object(module, "run", side_effect=fake_run) as again, \
             contextlib.redirect_stdout(io.StringIO()) as output:
            module.check_update()
        self.assertIn("3 commits behind", output.getvalue())
        self.assertEqual(len([c for c in again.call_args_list
                              if "fetch" in c.args[0]]), 0)

    def test_uninstall_dry_run_changes_nothing(self):
        self.install()
        snapshot = self.snapshot()
        module.uninstall(module.Installer(dry_run=True))
        self.assertEqual(snapshot, self.snapshot())

    def test_uninstall_removes_wiring_and_keeps_user_content(self):
        foreign_skill = self.claude / "skills/personal"
        self.skill(foreign_skill)
        foreign_hook = {"matcher": "startup", "hooks": [{"type": "command", "command": "echo hi"}]}
        settings = module.read_json(self.claude / "settings.json")
        settings.setdefault("hooks", {}).setdefault("SessionStart", []).append(foreign_hook)
        (self.claude / "settings.json").write_text(json.dumps(settings))
        crew = self.home / ".kiro/crew/config.json"
        self.install()
        crew_config = module.read_json(crew)
        crew_config["skills"]["extra_paths"].append(str(self.home / "my-skills"))
        crew.write_text(json.dumps(crew_config))
        module.uninstall(module.Installer())
        for root in (self.home / ".agents/skills", self.claude / "skills",
                     self.home / ".kiro/skills", self.home / ".cursor/skills",
                     self.home / ".kilo/skills"):
            self.assertTrue(all(not t.is_symlink() for t in root.iterdir()), root)
        self.assertTrue(foreign_skill.is_dir())
        self.assertFalse((self.codex / "AGENTS.md").exists())
        self.assertFalse((self.claude / "CLAUDE.md").exists())
        sessions = module.read_json(self.claude / "settings.json")["hooks"]["SessionStart"]
        self.assertEqual(sessions, [foreign_hook])
        self.assertEqual(module.read_json(crew)["skills"]["extra_paths"], [str(self.home / "my-skills")])
        self.assertEqual(module.read_json(self.config / "opencode/opencode.json")["plugins"], [])
        self.assertFalse((self.home / ".kiro/agents/agentkit.json").exists())
        self.assertTrue((self.data / "plugins/superpowers").is_dir())

    def test_claude_update_hook_registered_once_and_foreign_hooks_kept(self):
        foreign = {"matcher": "startup", "hooks": [{"type": "command", "command": "echo hi"}]}
        settings = module.read_json(self.claude / "settings.json")
        settings.setdefault("hooks", {}).setdefault("SessionStart", []).append(foreign)
        (self.claude / "settings.json").write_text(json.dumps(settings))
        self.install()
        self.install()
        sessions = module.read_json(self.claude / "settings.json")["hooks"]["SessionStart"]
        ours = [entry for entry in sessions
                if any(str(hook.get("command", "")).endswith("install.py --check-update")
                       for hook in entry.get("hooks", []))]
        self.assertEqual(len(ours), 1)
        self.assertIn(foreign, sessions)

    def test_manifest_validation_rejects_bad_entries(self):
        with self.assertRaises(ValueError):
            module.validate_manifest({"Bad-Name": {"repository": "https://example.com/x.git"}})
        with self.assertRaises(ValueError):
            module.validate_manifest({"x": {"marketplace": "y"}})
        with self.assertRaises(ValueError):
            module.validate_manifest({"x": {"repository": "https://example.com/x.git", "extra": True}})
        with self.assertRaises(ValueError):
            module.validate_manifest({"x": {"repository": "git@example.com/x.git"}})
        module.validate_manifest({"$schema": "./manifest.schema.json",
                                  "x": {"repository": "https://example.com/x.git"}})

    def test_checkout_dry_run_survives_stale_cache(self):
        stale = self.data / "plugins/superpowers"
        self.assertTrue(stale.is_dir())  # fixture cache has no .git, so it counts as stale
        (stale / "notagit").write_text("leftover")
        with patch.object(module, "run", side_effect=RuntimeError("must not touch git")):
            destination = module.Installer(dry_run=True).checkout("superpowers", {"repository": "https://e.com/x.git"})
        self.assertEqual(destination, stale)
        self.assertTrue((stale / "notagit").exists())

    def test_checkout_clones_when_absent(self):
        commands = []

        def fake_run(args):
            commands.append(" ".join(args))
            if args[0] == "git" and args[1] == "init":
                pathlib.Path(args[-1]).mkdir(parents=True, exist_ok=True)
            return "revision"

        with patch.object(module, "run", side_effect=fake_run):
            module.Installer().checkout("example", {"repository": "https://e.com/x.git"})
        self.assertTrue(any("git init" in c for c in commands))
        self.assertTrue(any("remote add origin https://e.com/x.git" in c for c in commands))
        self.assertTrue(any("fetch" in c and "HEAD" in c for c in commands))

    def test_kiro_ide_and_cli_detected_separately(self):
        (self.home / ".kiro").mkdir(exist_ok=True)
        with patch.object(module.shutil, "which", return_value=None):
            selected = module.detect_tools()
            self.assertNotIn("kiro-ide", selected)
            self.assertNotIn("kiro-cli", selected)
        with patch.object(module.shutil, "which",
                          side_effect=lambda name: "/bin/kiro-cli" if name == "kiro-cli" else None):
            selected = module.detect_tools()
            self.assertIn("kiro-cli", selected)
            self.assertNotIn("kiro-ide", selected)
        with patch.object(module.shutil, "which",
                          side_effect=lambda name: "/bin/kiro" if name == "kiro" else None):
            selected = module.detect_tools()
            self.assertIn("kiro-ide", selected)
            self.assertNotIn("kiro-cli", selected)

    def test_kilo_detected_by_cli_config_or_extension(self):
        with patch.object(module.shutil, "which",
                          side_effect=lambda name: "/bin/kilo" if name == "kilo" else None):
            self.assertIn("kilo", module.detect_tools())
        with patch.object(module.shutil, "which", return_value=None):
            self.assertNotIn("kilo", module.detect_tools())
            (self.config / "kilo").mkdir(parents=True)
            self.assertIn("kilo", module.detect_tools())
            (self.config / "kilo").rmdir()
            (self.home / ".vscode/extensions/kilocode.kilo-code-1.0.0").mkdir(parents=True)
            self.assertIn("kilo", module.detect_tools())

    def test_write_json_backs_up_and_refuses_unexpected_shapes(self):
        path = self.home / ".config/opencode/opencode.json"
        self.assertEqual(module.read_json(path)["permissions"], [{"effect": "deny"}])
        installer = module.Installer()
        installer.write_json(path, {"permissions": [{"effect": "deny"}], "plugins": []})
        backups = list((self.home / "state/backups").rglob("opencode.json"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(module.read_json(backups[0])["permissions"], [{"effect": "deny"}])
        (self.config / "opencode/opencode.jsonc").write_text('{"plugin": ["x"]}\n')
        with self.assertRaises(ValueError):
            self.install()

    def test_native_plugin_failure_falls_back_to_skills(self):
        (self.codex / "config.toml").write_text('approval_policy = "on-request"\n')
        with patch.object(module.shutil, "which", return_value="/usr/bin/codex"), \
             patch.object(module, "run", side_effect=RuntimeError("marketplace unavailable")):
            result = module.Installer().native_plugin(
                "codex", "superpowers", "https://example.com/superpowers.git", "superpowers-dev")
        self.assertFalse(result)

    def test_desloppify_keeps_existing_cli(self):
        with patch.object(module.shutil, "which", return_value="/usr/bin/desloppify"):
            module.Installer().desloppify(self.sources["desloppify"])
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

        with patch.object(module, "run", side_effect=fake_run):
            module.Installer().checkout("example", entry)
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
            with patch.object(module, "run", side_effect=lambda args, table=commands: table[" ".join(args)]), \
                 self.assertRaises(ValueError):
                module.Installer().checkout("example", entry)


    def test_manifest_bump_repoints_managed_plugin_roots(self):
        self.install()
        stale = str(self.data / "plugins/superpowers/deadbeef0000/skills")
        old_skill = self.home / ".kiro/skills/superpowers"
        old_skill.parent.mkdir(parents=True, exist_ok=True)
        old_skill.unlink()
        old_skill.symlink_to(self.data / "plugins/superpowers/deadbeef0000/skills/superpowers")
        crew = self.home / ".kiro/crew/config.json"
        config = module.read_json(crew)
        config["skills"]["extra_paths"] = [stale] + config["skills"]["extra_paths"]
        crew.write_text(json.dumps(config))
        opencode = self.config / "opencode/opencode.json"
        settings = module.read_json(opencode)
        settings["plugins"] = [str(self.data / "plugins/superpowers/deadbeef0000")] + settings["plugins"]
        opencode.write_text(json.dumps(settings))
        self.install()
        manifest = json.loads((module.REPO / "plugins/manifest.json").read_text())
        entries = [e for e in manifest.values() if isinstance(e, dict)]
        crew_paths = module.read_json(crew)["skills"]["extra_paths"]
        self.assertNotIn(stale, crew_paths)
        self.assertEqual(len(crew_paths), 1 + sum(1 for e in entries if e.get("skills")))
        plugins = module.read_json(opencode)["plugins"]
        self.assertFalse(any("deadbeef" in value for value in plugins))
        self.assertEqual(len(plugins), sum(1 for e in entries if e.get("opencode")))
        self.assertEqual(old_skill.readlink(),
                         self.sources["superpowers"] / "skills/superpowers")

    def test_retirement_removes_only_owned_links(self):
        root = self.home / ".agents/skills"
        root.mkdir(parents=True)
        (root / "retired").symlink_to(self.repo / "skills/retired")
        self.skill(root / "personal")
        module.Installer().sync_links(root, module.skills(self.repo / "skills"))
        self.assertFalse((root / "retired").is_symlink())
        self.assertTrue((root / "personal/SKILL.md").exists())

    def test_collision_refuses_to_replace_user_content(self):
        root = self.home / ".agents/skills"
        self.skill(root / "prose")
        snapshot = self.snapshot()
        with self.assertRaises(ValueError):
            module.Installer().sync_links(root, module.skills(self.repo / "skills"))
        self.assertEqual(snapshot, self.snapshot())


if __name__ == "__main__":
    unittest.main()
