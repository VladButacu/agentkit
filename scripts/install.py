"""Install shared skills and upstream plugin dependencies without replacing native state."""

import argparse
import datetime
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HOME = Path.home()
DATA = Path(os.environ.get("XDG_DATA_HOME", HOME / ".local/share")) / "agentkit"
STATE = Path(os.environ.get("XDG_STATE_HOME", HOME / ".local/state")) / "agentkit"
CODEX = Path(os.environ.get("CODEX_HOME", HOME / ".codex"))
CLAUDE = Path(os.environ.get("CLAUDE_CONFIG_DIR", HOME / ".claude"))
CONFIG = Path(os.environ.get("XDG_CONFIG_HOME", HOME / ".config"))
TOOLS = {"codex": CODEX, "claude": CLAUDE, "kiro-ide": HOME / ".kiro",
         "kiro-cli": HOME / ".kiro", "crew": HOME / ".kiro/crew",
         "cursor": HOME / ".cursor", "kilo": HOME / ".kilo",
         "opencode": CONFIG / "opencode"}
KIRO_IDE = (Path("/Applications/Kiro.app"), HOME / "Applications/Kiro.app")


def run(args: list[str]) -> str:
    try:
        result = subprocess.run(args, text=True, capture_output=True,
                                stdin=subprocess.DEVNULL, check=False, timeout=600)
    except subprocess.TimeoutExpired as error:
        raise RuntimeError(f"Command timed out after {error.timeout}s: {args[0]}") from error
    if result.returncode:
        # Native errors can contain private configuration. Leave inspection to the user.
        shown = " ".join([args[0]] + [arg for arg in args[1:] if not arg.startswith("-")][:2])
        raise RuntimeError(f"Command failed ({result.returncode}): {shown}")
    return result.stdout.strip()


def read_json(path: Path) -> dict:
    value = json.loads(path.read_text()) if path.exists() else {}
    if not isinstance(value, dict):
        raise TypeError(f"Expected a JSON object: {path}")
    return value


class Installer:
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.backup = STATE / "backups" / datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f")

    def write_json(self, path: Path, value: dict) -> None:
        if path.exists() and read_json(path) == value:
            return
        if path.is_symlink():
            raise ValueError(f"Refusing to rewrite symlinked native configuration: {path}")
        print(f"Update {path}")
        if self.dry_run:
            return
        if path.exists():
            destination = self.backup / path.relative_to(HOME)
            destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            shutil.copy2(path, destination)
            destination.chmod(0o600)
        path.parent.mkdir(parents=True, exist_ok=True)
        mode = stat.S_IMODE(path.stat().st_mode) if path.exists() else 0o600
        with tempfile.NamedTemporaryFile(mode="w", dir=path.parent, delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(json.dumps(value, indent=2) + "\n")
        temporary.chmod(mode)
        temporary.replace(path)

    def checkout(self, name: str, entry: dict) -> Path:
        repository = entry["repository"]
        if not repository.startswith("https://"):
            raise ValueError(f"Expected an https repository URL for {name}")
        destination = DATA / "plugins" / name
        if destination.exists() and not (destination / ".git").exists():
            # Regenerable cache from an earlier layout of this installer.
            print(f"Replace stale cache {destination}")
            if self.dry_run:
                print(f"Fetch {name} from {repository}")
                return destination
            shutil.rmtree(destination)
        if destination.exists():
            if run(["git", "-C", str(destination), "remote", "get-url", "origin"]) != repository:
                raise ValueError(f"Checkout origin differs from manifest: {destination}")
            if run(["git", "-C", str(destination), "status", "--porcelain"]):
                raise ValueError(f"Local dependency edits must be resolved first: {destination}")
            print(f"Update {name} from {repository}")
            if self.dry_run:
                return destination
            # Upstream owns the version: move to whatever HEAD points at now.
            run(["git", "-C", str(destination), "fetch", "--depth", "1", "origin", "HEAD"])
            run(["git", "-C", str(destination), "reset", "--hard", "FETCH_HEAD"])
            return destination
        print(f"Fetch {name} from {repository}")
        if self.dry_run:
            return destination
        destination.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=destination.parent) as directory:
            temporary = Path(directory) / "source"
            run(["git", "init", "-q", str(temporary)])
            run(["git", "-C", str(temporary), "remote", "add", "origin", repository])
            run(["git", "-C", str(temporary), "fetch", "--depth", "1", "origin", "HEAD"])
            run(["git", "-C", str(temporary), "reset", "-q", "--hard", "FETCH_HEAD"])
            if not run(["git", "-C", str(temporary), "rev-parse", "HEAD"]):
                raise ValueError(f"Dependency fetch failed: {name}")
            temporary.rename(destination)
        return destination

    def sync_links(self, root: Path, sources: dict[str, Path]) -> None:
        managed = ((REPO / "skills").resolve(), (DATA / "plugins").resolve())
        for name, source in sources.items():
            target = root / name
            if not (target.exists() or target.is_symlink()):
                continue
            if target.is_symlink() and target.resolve() == source.resolve():
                continue
            # Only foreign content is protected; our own links retire below.
            origin = target.resolve() if target.is_symlink() else None
            if origin is None or not any(origin.is_relative_to(base) for base in managed):
                raise ValueError(f"Refusing to replace existing content: {target}")
        keep = {source.resolve() for source in sources.values()}
        stale = []
        if root.is_dir():
            for target in root.iterdir():
                if not target.is_symlink() or target.resolve() in keep:
                    continue
                if any(target.resolve().is_relative_to(base) for base in managed):
                    stale.append(target)
        for target in stale:
            print(f"Remove retired link {target}")
            if not self.dry_run:
                target.unlink()
        for name, source in sources.items():
            target = root / name
            if target.is_symlink():
                continue
            print(f"Link {target}")
            if not self.dry_run:
                root.mkdir(parents=True, exist_ok=True)
                target.symlink_to(source, target_is_directory=source.is_dir())

    def native_plugin(self, tool: str, name: str, repository: str, marketplace: str) -> bool:
        if tool == "codex":
            import tomllib
            config = CODEX / "config.toml"
            settings = tomllib.loads(config.read_text()) if config.exists() else {}
            installed = {key: value.get("enabled", False)
                         for key, value in settings.get("plugins", {}).items()
                         if isinstance(value, dict)}
        else:
            installed = read_json(CLAUDE / "settings.json").get("enabledPlugins", {})
        enabled = [key for key, value in installed.items() if value and key.split("@")[0] == name]
        if len(enabled) > 1:
            raise ValueError(f"Multiple enabled {name} plugins in {tool}; choose one native installation")
        if enabled:
            print(f"Keep native {tool} plugin {enabled[0]}; its marketplace owns updates")
            return True
        if not shutil.which(tool):
            print(f"PENDING: {tool} CLI unavailable; installing {name} as skills only")
            return False
        marketplace = marketplace or name
        print(f"Install native {tool} plugin {name}@{marketplace} from {repository}")
        if not self.dry_run:
            try:
                run([tool, "plugin", "marketplace", "add", repository])
                verb = "add" if tool == "codex" else "install"
                run([tool, "plugin", verb, f"{name}@{marketplace}"])
            except RuntimeError as error:
                # A missing marketplace or CLI feature must not block the skills fallback.
                print(f"PENDING: native {tool} install failed ({error}); using skills fallback")
                return False
        print(f"PENDING: review native hook trust if prompted, then start a new {tool} session")
        return True

    def desloppify(self, source: Path) -> None:
        if shutil.which("desloppify"):
            print("Keep installed Desloppify CLI; upstream owns its version")
            return
        environment = DATA / "desloppify"
        command = environment / "bin/desloppify"
        link = HOME / ".local/bin/desloppify"
        foreign = (link.exists() or link.is_symlink()) and (
            not link.is_symlink() or link.resolve() != command)
        if foreign:
            raise ValueError(f"Refusing to replace existing executable: {link}")
        print("Install isolated Desloppify CLI from upstream HEAD; no upstream setup or hooks")
        if not self.dry_run:
            if environment.exists() and not (environment / "pyvenv.cfg").exists():
                shutil.rmtree(environment)
            if not command.exists():
                run([sys.executable, "-m", "venv", str(environment)])
            run([str(environment / "bin/python"), "-m", "pip", "install", "--upgrade",
                 str(source) + "[full]"])
            run([str(command), "--version"])
            link.parent.mkdir(parents=True, exist_ok=True)
            if not link.is_symlink():
                link.symlink_to(command)


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
        version = run(["opencode", "--version"])
        major = re.search(r"\b(\d+)\.\d+\.\d+", version)
        if not major:
            raise ValueError("Cannot determine OpenCode configuration version")
        return "plugins" if int(major[1]) >= 2 else "plugin"
    raise ValueError("OpenCode version unknown; install its CLI before configuring plugins")


def skills(root: Path) -> dict[str, Path]:
    return {path.parent.name: path.parent for path in sorted(root.glob("*/SKILL.md"))}


MANIFEST_FIELDS = {"repository", "marketplace", "skills", "opencode", "cli", "description"}


def validate_manifest(manifest: dict) -> None:
    # Enforces plugins/manifest.schema.json; keep both in sync.
    if not isinstance(manifest, dict):
        raise TypeError("Plugin manifest must be a JSON object")
    for name, entry in manifest.items():
        if name == "$schema":
            continue
        if not re.fullmatch(r"[a-z][a-z0-9-]*", name):
            raise ValueError(f"Invalid plugin name in manifest: {name}")
        if not isinstance(entry, dict):
            raise TypeError(f"Manifest entry must be an object: {name}")
        unknown = set(entry) - MANIFEST_FIELDS
        if unknown:
            raise ValueError(f"Unknown manifest fields for {name}: {', '.join(sorted(unknown))}")
        # Mirrors the repository pattern in plugins/manifest.schema.json.
        repository = entry.get("repository")
        if not isinstance(repository, str) or not re.fullmatch(r"https://[^/\s]+/[^\s]+\.git", repository):
            raise ValueError(f"Invalid repository URL for {name}: {repository}")


UPDATE_CHECK_PERIOD = 24 * 3600


def check_update() -> int:
    """Print one notice line when the local clone is behind upstream."""
    marker = STATE / "update-check.json"
    now = time.time()
    try:
        if marker.exists():
            cached = json.loads(marker.read_text())
            if now - cached.get("checked", 0) < UPDATE_CHECK_PERIOD:
                if cached.get("behind"):
                    print(cached["message"])
                return 0
        run(["git", "-C", str(REPO), "fetch", "-q", "origin"])
        behind = int(run(["git", "-C", str(REPO), "rev-list", "--count",
                          "HEAD..@{upstream}"]) or 0)
        message = f"agentkit is {behind} commits behind upstream. Run: make -C {REPO} update"
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text(json.dumps({"checked": now, "behind": behind,
                                      "message": message if behind else ""}))
        if behind:
            print(message)
    except (TypeError, ValueError, RuntimeError, OSError):
        # A session hook must stay silent when git, the network or the clone is missing.
        return 0
    return 0


def store_selection(plugins: set[str]) -> None:
    STATE.mkdir(parents=True, exist_ok=True)
    (STATE / "plugins.json").write_text(json.dumps({"selected": sorted(plugins)}))


def select_plugins(manifest: dict, requested: str | None, persist: bool = True) -> set[str]:
    names = set(manifest)
    catalog = ", ".join(f"{name} ({entry.get('description', 'no description')})"
                        for name, entry in sorted(manifest.items()))
    if requested:
        wanted = {name.strip() for name in requested.split(",") if name.strip()}
        if wanted == {"all"}:
            chosen = set(names)
        elif wanted == {"none"}:
            chosen = set()
        else:
            unknown = wanted - names
            if unknown:
                raise ValueError(f"Unknown plugins: {', '.join(sorted(unknown))}. Available: {catalog}")
            chosen = wanted
        if persist:
            store_selection(chosen)
        return chosen
    stored = STATE / "plugins.json"
    if stored.exists():
        try:
            saved = json.loads(stored.read_text()).get("selected", [])
        except (TypeError, ValueError):
            saved = []
        chosen = {name for name in saved if name in names}
        if chosen or saved == []:
            return chosen
    if sys.stdin.isatty():
        print("Select the third-party plugins to install:")
        chosen = set()
        for name, entry in sorted(manifest.items()):
            answer = input(f"  {name} ({entry.get('description', '')}) [Y/n] ").strip().lower()
            if answer not in ("n", "no"):
                chosen.add(name)
        if persist:
            store_selection(chosen)
        return chosen
    # No stored choice and no terminal: make the choice explicit instead of
    # installing everything unasked. The question comes from the process.
    raise ValueError(
        "Choose the third-party plugins to install. Available: " + catalog +
        ". Rerun with --plugins <comma-separated-names>, --plugins all or --plugins none.")


def kiro_ide_installed() -> bool:
    """The Kiro IDE app, which shares ~/.kiro with the CLI and Crew."""
    return bool(shutil.which("kiro")) or any(path.exists() for path in KIRO_IDE)


def kilo_installed() -> bool:
    """Kilo Code CLI, its config tree, or an IDE extension that has not run yet."""
    editors = (".vscode", ".vscode-insiders", ".cursor", ".windsurf")
    extensions = [match for editor in editors
                  for match in (HOME / editor / "extensions").glob("kilocode.kilo-code-*")]
    return bool(shutil.which("kilo") or (HOME / ".kilo").exists()
                or (CONFIG / "kilo").exists() or extensions)


def detect_tools() -> set[str]:
    """Tools present on this machine; the three Kiro tools are detected separately."""
    binaries = {"crew": "kirocrew", "kiro-cli": "kiro-cli"}
    selected = set()
    for name, root in TOOLS.items():
        if name == "kilo":
            if kilo_installed():
                selected.add(name)
        elif name == "kiro-ide":
            if kiro_ide_installed():
                selected.add(name)
        elif name == "kiro-cli":
            if shutil.which("kiro-cli"):
                selected.add(name)
        elif shutil.which(binaries.get(name, name)) or root.exists():
            selected.add(name)
    return selected


def install(installer: Installer, selected: set[str], requested: str | None = None) -> None:
    manifest = read_json(REPO / "plugins/manifest.json")
    validate_manifest(manifest)
    manifest.pop("$schema", None)
    plugins = select_plugins(manifest, requested, persist=not installer.dry_run)
    manifest = {name: entry for name, entry in manifest.items() if name in plugins}
    local = {"skills", "opencode", "cli"}

    def plugin_skills(name: str, entry: dict) -> dict[str, Path]:
        # FEX-style plugins keep their skills namespaced inside the native plugin.
        if not entry.get("skills") or name not in sources:
            return {}
        return skills(sources[name] / entry["skills"])

    sources = {name: installer.checkout(name, entry)
               for name, entry in manifest.items() if local & entry.keys()}
    own = skills(REPO / "skills")
    # Shared roots contain only our skills, avoiding plugin/global duplicate discovery.
    installer.sync_links(HOME / ".agents/skills", own)
    claude_own = own
    if "claude" in selected:
        path = CLAUDE / "settings.json"
        settings = read_json(path)
        # Any repository skill must not stay overridden, whatever it is named.
        for name in own:
            settings.get("skillOverrides", {}).pop(name, None)
        # When agentkit itself runs as a Claude plugin, its skills already load
        # natively and symlinking them again would duplicate every skill.
        plugin_mode = any(key.split("@")[0] == "agentkit"
                          for key, value in settings.get("enabledPlugins", {}).items() if value)
        claude_own = {} if plugin_mode else own
        # A session-start notice when the clone is behind upstream; only ours is managed.
        command = f"python3 {REPO / 'scripts/install.py'} --check-update"
        sessions = settings.setdefault("hooks", {}).setdefault("SessionStart", [])
        sessions[:] = [entry for entry in sessions
                       if not any(str(hook.get("command", "")).endswith("install.py --check-update")
                                  for hook in entry.get("hooks", []))]
        sessions.append({"matcher": "startup",
                         "hooks": [{"type": "command", "command": command}]})
        installer.write_json(path, settings)
    for tool in selected & {"codex", "claude"}:
        root = TOOLS[tool]
        instruction = root / ("AGENTS.md" if tool == "codex" else "CLAUDE.md")
        if not (instruction.exists() or instruction.is_symlink()) or (
            instruction.is_symlink() and instruction.resolve() == REPO / "AGENTS.md"
        ):
            installer.sync_links(root, {instruction.name: REPO / "AGENTS.md"})
        else:
            print(f"PENDING: preserve existing instructions {instruction}; adoption needs review")
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
        installer.sync_links(HOME / ".cursor/skills", all_plugin_skills)
        print("Cursor: skills installed; native hooks/marketplace UI are not configured by this fallback")
    if "kilo" in selected:
        # Kilo reads ~/.agents/skills natively; these are plugin skill fallbacks only.
        installer.sync_links(HOME / ".kilo/skills", all_plugin_skills)
        print("Kilo Code: skills installed; native hooks/marketplace UI are not configured by this fallback")
    if {"kiro-ide", "kiro-cli"} & selected:
        installer.sync_links(HOME / ".kiro/skills", own | all_plugin_skills)
        print("Kiro: selected plugin skills only, without native plugin lifecycle hooks")
    if "kiro-cli" in selected:
        agents = Path(os.environ.get("KIRO_AGENT_CONFIG_DIR", HOME / ".kiro/agents"))
        agent = agents / "agentkit.json"
        if not agent.exists():
            installer.write_json(agent, {
                "name": "agentkit", "description": "Kiro CLI agent for agentkit: shared instructions and skills",
                "resources": [f"file://{REPO / 'AGENTS.md'}", "file://.kiro/steering/**/*.md",
                              "skill://~/.kiro/skills/*/SKILL.md"],
                "tools": ["*"], "allowedTools": [], "includeMcpJson": True,
            })
        print("Kiro CLI: select `kiro-cli --agent agentkit`; existing agents preserved")
    if "crew" in selected:
        path = HOME / ".kiro/crew/config.json"
        settings = read_json(path)
        extra = settings.setdefault("skills", {}).setdefault("extra_paths", [])
        roots = [REPO / "skills"] + [sources[name] / entry["skills"]
                                     for name, entry in manifest.items()
                                     if entry.get("skills") and name in sources]
        current = {root.resolve() for root in roots}
        plugins_root = (DATA / "plugins").resolve()
        # Drop roots from earlier installs; keep user-added paths.
        extra[:] = [value for value in extra
                    if Path(value).expanduser().resolve() in current
                    or not Path(value).expanduser().resolve().is_relative_to(plugins_root)]
        for root in roots:
            if not any(Path(value).expanduser().resolve() == root.resolve() for value in extra):
                extra.append(str(root))
        installer.write_json(path, settings)
        print("Crew: external skill roots configured; native projections and specialist scopes preserved")
    if "opencode" in selected:
        path = CONFIG / "opencode/opencode.json"
        if path.with_suffix(".jsonc").exists():
            # A schema-only companion cannot override plugins. Preserve real JSONC for review.
            companion = read_json(path.with_suffix(".jsonc"))
            if set(companion) - {"$schema"}:
                raise ValueError("OpenCode JSONC needs a reviewed structural edit; refusing to guess precedence")
        settings = read_json(path)
        key = opencode_key(settings)
        entries = settings.setdefault(key, [])
        if not isinstance(entries, list):
            raise ValueError(f"OpenCode {key} section must be a list: {path}")
        # Repoint registrations from older manifest revisions; keep foreign ones.
        managed_root = str(DATA / "plugins")
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

def uninstall(installer: Installer) -> None:
    """Remove everything the installer created; user content and caches stay."""
    repo_skills = (REPO / "skills").resolve()
    plugins = (DATA / "plugins").resolve()
    for root in (HOME / ".agents/skills", CLAUDE / "skills", HOME / ".kiro/skills",
                 HOME / ".cursor/skills", HOME / ".kilo/skills", CODEX / "skills"):
        if not root.is_dir():
            continue
        for target in sorted(root.iterdir()):
            origin = target.resolve() if target.is_symlink() else None
            if origin and (origin.is_relative_to(repo_skills) or origin.is_relative_to(plugins)):
                print(f"Remove {target}")
                if not installer.dry_run:
                    target.unlink()
    for instruction in (CODEX / "AGENTS.md", CLAUDE / "CLAUDE.md"):
        if instruction.is_symlink() and instruction.resolve() == (REPO / "AGENTS.md").resolve():
            print(f"Remove {instruction}")
            if not installer.dry_run:
                instruction.unlink()
    path = CLAUDE / "settings.json"
    if path.exists():
        settings = read_json(path)
        sessions = settings.get("hooks", {}).get("SessionStart", [])
        kept = [entry for entry in sessions
                if not any(str(hook.get("command", "")).endswith("install.py --check-update")
                           for hook in entry.get("hooks", []))]
        if kept != sessions:
            settings["hooks"]["SessionStart"] = kept
            if not kept:
                settings["hooks"].pop("SessionStart")
                if not settings["hooks"]:
                    settings.pop("hooks")
            installer.write_json(path, settings)
    crew = HOME / ".kiro/crew/config.json"
    if crew.exists():
        settings = read_json(crew)
        extra = settings.get("skills", {}).get("extra_paths", [])
        settings["skills"]["extra_paths"] = [value for value in extra
                                             if not (Path(value).expanduser().resolve() == repo_skills
                                                     or Path(value).expanduser().resolve().is_relative_to(plugins))]
        installer.write_json(crew, settings)
    path = CONFIG / "opencode/opencode.json"
    if path.exists():
        settings = read_json(path)
        key = opencode_key(settings)
        entries = settings.get(key, [])
        settings[key] = [value for value in entries
                         if not (isinstance(value, str)
                                 and value.startswith(str(DATA / "plugins")))]
        installer.write_json(path, settings)
    agent = HOME / ".kiro/agents/agentkit.json"
    if agent.exists():
        print(f"Remove {agent}")
        if not installer.dry_run:
            agent.unlink()
    print("Left in place for you: ~/.local/share/agentkit, ~/.local/state/agentkit "
          "(contains your backups), and the clone itself. An agentkit plugin installed "
          "through a marketplace is removed by that tool, for example "
          "`claude plugin uninstall agentkit`.")



def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Plan without writes, downloads or plugin commands")
    parser.add_argument("--tools", help="Comma-separated targets; default: detected installations")
    parser.add_argument("--plugins", help="Third-party plugins to install: comma-separated names, all, or none; remembered for later runs")
    parser.add_argument("--check-update", action="store_true", help="Print one notice when this clone is behind upstream; meant for session hooks")
    parser.add_argument("--uninstall", action="store_true", help="Remove everything the installer created; user content and caches stay")
    args = parser.parse_args()
    if args.check_update:
        return check_update()
    if args.uninstall:
        try:
            uninstall(Installer(args.dry_run))
        except (TypeError, ValueError, RuntimeError, OSError) as error:
            print(error, file=sys.stderr)
            return 1
        return 0
    selected = set(args.tools.split(",")) if args.tools else detect_tools()
    if unknown := selected - TOOLS.keys():
        parser.error(f"Unknown tools: {', '.join(sorted(unknown))}")
    try:
        install(Installer(args.dry_run), selected, args.plugins)
    except (TypeError, ValueError, RuntimeError, OSError) as error:
        print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
