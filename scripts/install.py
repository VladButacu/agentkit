"""Install shared skills and upstream plugin dependencies without replacing native state."""

import argparse
import json
import os
import re
import shutil
import sys
import time
from pathlib import Path

import actions
import choices
import instruction_block


def opencode_key(settings: dict) -> str:
    """The config key OpenCode expects for plugin entries, v1 or v2."""
    if "plugin" in settings:
        return "plugin"
    if "plugins" in settings:
        return "plugins"
    if "permission" in settings:
        return "plugin"
    if "permissions" in settings:
        return "plugins"
    if shutil.which("opencode"):
        version = actions.run(["opencode", "--version"])
        major = re.search(r"\b(\d+)\.\d+\.\d+", version)
        if not major:
            raise ValueError("Cannot determine OpenCode configuration version")
        return "plugins" if int(major[1]) >= 2 else "plugin"
    raise ValueError("OpenCode version unknown; install its CLI before configuring plugins")


def instruction_files(selected: set[str]) -> dict[Path, str]:
    """Each selected tool's global instruction file and the agentkit text it carries."""
    source = actions.REPO / "AGENTS.md"
    files = {}
    if "codex" in selected:
        # Codex cannot import a file, so it gets a copy that every install refreshes.
        files[actions.CODEX / "AGENTS.md"] = source.read_text(encoding="utf-8")
    if "claude" in selected:
        files[actions.CLAUDE / "CLAUDE.md"] = "@" + source.as_posix().replace(" ", "\\ ")
    return files


UPDATE_CHECK_PERIOD = 24 * 3600


def check_update() -> int:
    """Print one notice line when the local clone is behind upstream."""
    marker = actions.STATE / "update-check.json"
    now = time.time()
    try:
        if marker.exists():
            cached = json.loads(marker.read_text())
            if now - cached.get("checked", 0) < UPDATE_CHECK_PERIOD:
                if cached.get("behind"):
                    print(cached["message"])
                return 0
        actions.run(["git", "-C", str(actions.REPO), "fetch", "-q", "origin"])
        behind = int(actions.run(["git", "-C", str(actions.REPO), "rev-list", "--count",
                          "HEAD..@{upstream}"]) or 0)
        message = f"agentkit is {behind} commits behind upstream. Run: make -C {actions.REPO} update"
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text(json.dumps({"checked": now, "behind": behind,
                                      "message": message if behind else ""}))
        if behind:
            print(message)
    except (TypeError, ValueError, RuntimeError, OSError):
        # A session hook must stay silent when git, the network or the clone is missing.
        return 0
    return 0


def update_hook() -> dict:
    # Exec form runs without a shell, so it works under bash and PowerShell alike.
    return {"type": "command", "command": sys.executable,
            "args": [str(actions.REPO / "scripts/install.py"), "--check-update"]}


def is_update_hook(hook: dict) -> bool:
    words = [str(hook.get("command", ""))] + [str(arg) for arg in hook.get("args", [])]
    return " ".join(words).endswith("install.py --check-update")


def without_update_hooks(sessions: list) -> list:
    return [entry for entry in sessions
            if not any(is_update_hook(hook) for hook in entry.get("hooks", []))]


def local_notes() -> Path:
    """Machine-personal additions to AGENTS.md, kept outside every clone."""
    return actions.CONFIG / "agentkit/AGENTS.local.md"


def move_local_notes(installer: actions.Installer) -> None:
    old, new = actions.REPO / "AGENTS.local.md", local_notes()
    if not old.is_file():
        return
    if new.exists():
        print(f"PENDING: merge {old} into {new}, then delete {old}")
        return
    print(f"Move {old} to {new}")
    if not installer.dry_run:
        new.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(old, new)


def is_managed_root(path: Path) -> bool:
    """A skill root this installer registers: inside this repository or a plugin checkout."""
    return path.is_relative_to(actions.REPO.resolve()) or path.is_relative_to((actions.DATA / "plugins").resolve())


def companion_skills(manifest: dict) -> dict[str, Path]:
    """agentkit skills that ship only with a selected plugin."""
    found = {}
    for entry in manifest.values():
        if entry.get("companion"):
            found.update(actions.skills(actions.REPO / entry["companion"]))
    return found


def install(installer: actions.Installer, selected: set[str], requested: str | None = None,
            instruction_mode: str | None = None) -> None:
    if not selected:
        print("No supported tool found, so there is nothing to install. Choose tools with --tools.")
        return
    print(f"Installing for: {', '.join(sorted(selected))}")
    if skipped := sorted(actions.TOOLS.keys() - selected):
        print(f"Skipping, not installed or not chosen: {', '.join(skipped)}")
    manifest = actions.read_json(actions.REPO / "plugins/manifest.json")
    choices.validate_manifest(manifest)
    manifest.pop("$schema", None)
    plugins = choices.select_plugins(manifest, requested, persist=not installer.dry_run)
    manifest = {name: entry for name, entry in manifest.items() if name in plugins}
    files = instruction_files(selected)
    modes = choices.choose_instruction_modes(list(files), instruction_mode, actions.STATE / "instructions.json",
                                     persist=not installer.dry_run)
    # Every question is answered before anything changes.
    move_local_notes(installer)
    local = {"skills", "opencode", "cli"}

    def plugin_skills(name: str, entry: dict) -> dict[str, Path]:
        # FEX-style plugins keep their skills namespaced inside the native plugin.
        if not entry.get("skills") or name not in sources:
            return {}
        return actions.skills(sources[name] / entry["skills"])

    sources = {name: installer.checkout(name, entry)
               for name, entry in manifest.items() if local & entry.keys()}
    companions = companion_skills(manifest)
    own = actions.skills(actions.REPO / "skills") | companions
    if selected & actions.AGENTS_SKILLS_READERS:
        # Shared roots contain only our skills, avoiding plugin/global duplicate discovery.
        installer.sync_links(actions.HOME / ".agents/skills", own)
    claude_own = own
    if "claude" in selected:
        path = actions.CLAUDE / "settings.json"
        settings = actions.read_json(path)
        # Any repository skill must not stay overridden, whatever it is named.
        for name in own:
            settings.get("skillOverrides", {}).pop(name, None)
        # When agentkit itself runs as a Claude plugin, its skills/ folder already loads
        # natively and symlinking it again would duplicate every skill. The plugin does
        # not carry companion skills.
        plugin_mode = any(key.split("@")[0] == "agentkit"
                          for key, value in settings.get("enabledPlugins", {}).items() if value)
        claude_own = companions if plugin_mode else own
        # A session-start notice when the clone is behind upstream; only ours is managed.
        sessions = settings.setdefault("hooks", {}).setdefault("SessionStart", [])
        sessions[:] = without_update_hooks(sessions) + [
            {"matcher": "startup", "hooks": [update_hook()]}]
        installer.write_json(path, settings)
    for path, body in files.items():
        instruction_block.sync(installer, path, actions.REPO / "AGENTS.md", body, modes.get(path, "keep"))
    for tool in selected & {"codex", "claude"}:
        root = actions.TOOLS[tool]
        fallback = {}
        for name, entry in manifest.items():
            if entry.get("marketplace") and not installer.native_plugin(
                    tool, name, entry["repository"], entry["marketplace"]):
                fallback.update(plugin_skills(name, entry))
        installer.sync_links(root / "skills",
                             claude_own | fallback if tool == "claude" else fallback)
    all_plugin_skills = {}
    for name, entry in manifest.items():
        all_plugin_skills.update(plugin_skills(name, entry))
    if "cursor" in selected:
        # Cursor reads ~/.agents/skills natively; these are plugin skill fallbacks only.
        installer.sync_links(actions.HOME / ".cursor/skills", all_plugin_skills)
        print("Cursor: skills installed; native hooks/marketplace UI are not configured by this fallback")
    if "kilo" in selected:
        # Kilo reads ~/.agents/skills natively; these are plugin skill fallbacks only.
        installer.sync_links(actions.HOME / ".kilo/skills", all_plugin_skills)
        print("Kilo Code: skills installed; native hooks/marketplace UI are not configured by this fallback")
    if {"kiro-ide", "kiro-cli"} & selected:
        installer.sync_links(actions.HOME / ".kiro/skills", own | all_plugin_skills)
        print("Kiro: selected plugin skills only, without native plugin lifecycle hooks")
    if "kiro-cli" in selected:
        agents = Path(os.environ.get("KIRO_AGENT_CONFIG_DIR", actions.HOME / ".kiro/agents"))
        agent = agents / "agentkit.json"
        if not agent.exists():
            installer.write_json(agent, {
                "name": "agentkit", "description": "Kiro CLI agent for agentkit: shared instructions and skills",
                "resources": [f"file://{(actions.REPO / 'AGENTS.md').as_posix()}", "file://.kiro/steering/**/*.md",
                              "skill://~/.kiro/skills/*/SKILL.md"],
                "tools": ["*"], "allowedTools": [], "includeMcpJson": True,
            })
        print("Kiro CLI: select `kiro-cli --agent agentkit`; existing agents preserved")
    if "crew" in selected:
        path = actions.HOME / ".kiro/crew/config.json"
        settings = actions.read_json(path)
        extra = settings.setdefault("skills", {}).setdefault("extra_paths", [])
        roots = ([actions.REPO / "skills"]
                 + [actions.REPO / entry["companion"] for entry in manifest.values() if entry.get("companion")]
                 + [sources[name] / entry["skills"] for name, entry in manifest.items()
                    if entry.get("skills") and name in sources])
        current = {root.resolve() for root in roots}
        # Drop roots from earlier installs or deselected plugins; keep user-added paths.
        extra[:] = [value for value in extra
                    if Path(value).expanduser().resolve() in current
                    or not is_managed_root(Path(value).expanduser().resolve())]
        for root in roots:
            if not any(Path(value).expanduser().resolve() == root.resolve() for value in extra):
                extra.append(str(root))
        installer.write_json(path, settings)
        print("Crew: external skill roots configured; native projections and specialist scopes preserved")
    if "opencode" in selected:
        path = actions.CONFIG / "opencode/opencode.json"
        if path.with_suffix(".jsonc").exists():
            # A schema-only companion cannot override plugins. Preserve real JSONC for review.
            companion = actions.read_json(path.with_suffix(".jsonc"))
            if set(companion) - {"$schema"}:
                raise ValueError("OpenCode JSONC needs a reviewed structural edit; refusing to guess precedence")
        settings = actions.read_json(path)
        key = opencode_key(settings)
        entries = settings.setdefault(key, [])
        if not isinstance(entries, list):
            raise ValueError(f"OpenCode {key} section must be a list: {path}")
        # Repoint registrations from older manifest revisions; keep foreign ones.
        managed_root = str(actions.DATA / "plugins")
        entries[:] = [value for value in entries
                      if not (isinstance(value, str) and value.startswith(managed_root))]
        for name, entry in manifest.items():
            if not entry.get("opencode") or name not in sources:
                continue
            target = sources[name] / entry["opencode"] if entry["opencode"] != "." else sources[name]
            if key == "plugin" and target.is_dir():
                scripts = sorted(target.glob("*.mjs"))
                if scripts:
                    target = scripts[0]
            if not any(name in (value if isinstance(value, str) else value.get("package", "")) for value in entries):
                entries.append(str(target))
        installer.write_json(path, settings)
    for name, entry in manifest.items():
        if entry.get("cli"):
            installer.desloppify(sources[name])


def uninstall(installer: actions.Installer) -> None:
    """Remove everything the installer created; user content and caches stay."""
    for root in (actions.HOME / ".agents/skills", actions.CLAUDE / "skills", actions.HOME / ".kiro/skills",
                 actions.HOME / ".cursor/skills", actions.HOME / ".kilo/skills", actions.CODEX / "skills"):
        if not root.is_dir():
            continue
        for target in sorted(root.iterdir()):
            if actions.owned(target):
                print(f"Remove {target}")
                if not installer.dry_run:
                    actions.remove_link(target)
    for path in (actions.CODEX / "AGENTS.md", actions.CLAUDE / "CLAUDE.md"):
        instruction_block.remove(installer, path, actions.REPO / "AGENTS.md")
    path = actions.CLAUDE / "settings.json"
    if path.exists():
        settings = actions.read_json(path)
        sessions = settings.get("hooks", {}).get("SessionStart", [])
        kept = without_update_hooks(sessions)
        if kept != sessions:
            settings["hooks"]["SessionStart"] = kept
            if not kept:
                settings["hooks"].pop("SessionStart")
                if not settings["hooks"]:
                    settings.pop("hooks")
            installer.write_json(path, settings)
    crew = actions.HOME / ".kiro/crew/config.json"
    if crew.exists():
        settings = actions.read_json(crew)
        extra = settings.get("skills", {}).get("extra_paths", [])
        settings["skills"]["extra_paths"] = [value for value in extra
                                             if not is_managed_root(Path(value).expanduser().resolve())]
        installer.write_json(crew, settings)
    path = actions.CONFIG / "opencode/opencode.json"
    if path.exists():
        settings = actions.read_json(path)
        key = opencode_key(settings)
        entries = settings.get(key, [])
        settings[key] = [value for value in entries
                         if not (isinstance(value, str)
                                 and value.startswith(str(actions.DATA / "plugins")))]
        installer.write_json(path, settings)
    agent = actions.HOME / ".kiro/agents/agentkit.json"
    if agent.exists():
        print(f"Remove {agent}")
        if not installer.dry_run:
            agent.unlink()
    print("Left in place for you: ~/.local/share/agentkit, ~/.local/state/agentkit "
          "(contains your backups), ~/.config/agentkit (your machine notes), and the clone itself. An agentkit plugin installed "
          "through a marketplace is removed by that tool, for example "
          "`claude plugin uninstall agentkit`.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Plan without writes, downloads or plugin commands")
    parser.add_argument("--tools", help="Comma-separated targets; default: detected installations")
    parser.add_argument("--plugins", help="Third-party plugins to install: comma-separated names, all, or none; remembered for later runs")
    parser.add_argument("--instructions", choices=instruction_block.MODES,
                        help="What to do with your own existing Codex AGENTS.md or Claude CLAUDE.md: "
                             "keep it, append agentkit's instructions, or replace it after a backup")
    parser.add_argument("--check-update", action="store_true", help="Print one notice when this clone is behind upstream; meant for session hooks")
    parser.add_argument("--uninstall", action="store_true", help="Remove everything the installer created; user content and caches stay")
    args = parser.parse_args()
    if args.check_update:
        return check_update()
    if args.uninstall:
        try:
            uninstall(actions.Installer(args.dry_run))
        except (TypeError, ValueError, RuntimeError, OSError) as error:
            print(error, file=sys.stderr)
            return 1
        return 0
    selected = set(args.tools.split(",")) if args.tools else choices.detect_tools()
    if unknown := selected - actions.TOOLS.keys():
        parser.error(f"Unknown tools: {', '.join(sorted(unknown))}")
    try:
        install(actions.Installer(args.dry_run), selected, args.plugins, args.instructions)
    except (TypeError, ValueError, RuntimeError, OSError) as error:
        print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
