"""Where agentkit and each tool keep their files, and every write, link and native command
the installer makes, each honouring dry-run.

Other modules read the paths as `actions.NAME` at call time, so tests can redirect them."""

import datetime
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
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
# Tools that read ~/.agents/skills natively.
AGENTS_SKILLS_READERS = {"codex", "cursor", "kilo", "opencode"}
KIRO_IDE = (Path("/Applications/Kiro.app"), HOME / "Applications/Kiro.app")


# A copy cannot be read like a link, so it records its source here instead.
MARKER = ".agentkit-source"
# IO_REPARSE_TAG_MOUNT_POINT. The stat module names it only on Windows.
JUNCTION_TAG = 0xA0000003


def is_link(path: Path) -> bool:
    """A symlink or a Windows directory junction."""
    if path.is_symlink():
        return True
    try:
        return getattr(os.lstat(path), "st_reparse_tag", 0) == JUNCTION_TAG
    except OSError:
        return False


def present(path: Path) -> bool:
    """Anything at path, including a link whose target is gone."""
    return path.exists() or is_link(path)


def link_origin(path: Path) -> Path | None:
    """What a link or an agentkit copy stands for; None for anything else."""
    if is_link(path):
        return path.resolve()
    marker = path / MARKER
    if path.is_dir() and marker.is_file():
        return Path(marker.read_text(encoding="utf-8").strip()).resolve()
    return None


def remove_link(path: Path) -> None:
    """Remove a link without touching its target, or an agentkit copy."""
    if is_link(path):
        # On Windows, os.unlink also removes directory junctions and directory symlinks.
        path.unlink()
    else:
        shutil.rmtree(path)


def make_link(source: Path, target: Path) -> None:
    if os.name == "nt":
        # Junctions need neither Developer Mode nor admin rights, unlike symlinks.
        import _winapi
        _winapi.CreateJunction(str(source.resolve()), str(target))
    else:
        target.symlink_to(source, target_is_directory=True)


def create_link(source: Path, target: Path) -> bool:
    """Point target at the source directory. Returns False when it had to copy."""
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        make_link(source, target)
        return True
    except OSError:
        copy_dir(source, target)
        return False


def copy_dir(source: Path, target: Path) -> None:
    """Replace target with a marked copy of source, swapped in only once complete."""
    staging = Path(tempfile.mkdtemp(prefix=f".{target.name}.", dir=target.parent))
    try:
        shutil.copytree(source, staging, dirs_exist_ok=True)
        (staging / MARKER).write_text(f"{source.resolve()}\n", encoding="utf-8")
        if present(target):
            remove_link(target)
        staging.rename(target)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise


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
    value = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    if not isinstance(value, dict):
        raise TypeError(f"Expected a JSON object: {path}")
    return value


def skills(root: Path) -> dict[str, Path]:
    return {path.parent.name: path.parent for path in sorted(root.glob("*/SKILL.md"))}


def owned(path: Path) -> bool:
    """A link or copy this installer made for a repository or plugin skill."""
    origin = link_origin(path)
    managed = ((REPO / "skills").resolve(), (DATA / "plugins").resolve())
    return origin is not None and any(origin.is_relative_to(base) for base in managed)


class Installer:
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.backup = STATE / "backups" / datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f")

    def write_json(self, path: Path, value: dict) -> None:
        if path.exists() and read_json(path) == value:
            return
        self.write_text(path, json.dumps(value, indent=2) + "\n")

    def write_text(self, path: Path, text: str) -> None:
        """Atomically rewrite a native file, backing up the previous version first."""
        if path.is_file() and not path.is_symlink() and path.read_text(encoding="utf-8") == text:
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
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(text)
        temporary.chmod(mode)
        temporary.replace(path)

    def remove_file(self, path: Path) -> None:
        print(f"Remove {path}")
        if not self.dry_run:
            path.unlink()

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
        """Link each skill directory into root and retire our links nothing uses."""
        for name in sources:
            target = root / name
            # Only foreign content is protected; our own links and copies retire below.
            if present(target) and not owned(target):
                raise ValueError(f"Refusing to replace existing content: {target}")
        keep = {source.resolve() for source in sources.values()}
        stale = [target for target in (root.iterdir() if root.is_dir() else ())
                 if owned(target) and link_origin(target) not in keep]
        for target in stale:
            print(f"Remove retired link {target}")
            if not self.dry_run:
                remove_link(target)
        for name, source in sources.items():
            target = root / name
            if is_link(target) and link_origin(target) == source.resolve():
                continue
            # An owned copy is refreshed every run, and becomes a link once links work.
            print(f"Link {target}")
            if self.dry_run:
                continue
            if present(target):
                remove_link(target)
            if not create_link(source, target):
                print(f"PENDING: links are unavailable here, so {target} is a copy; "
                      "rerun the installer after each update")

    def native_plugin(self, tool: str, name: str, repository: str, marketplace: str) -> bool:
        if tool == "codex":
            import tomllib
            config = CODEX / "config.toml"
            settings = tomllib.loads(config.read_text(encoding="utf-8")) if config.exists() else {}
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
        windows = os.name == "nt"
        scripts = environment / ("Scripts" if windows else "bin")
        command = scripts / ("desloppify.exe" if windows else "desloppify")
        link = HOME / ".local/bin/desloppify"
        foreign = not windows and present(link) and (
            not link.is_symlink() or link.resolve() != command)
        if foreign:
            raise ValueError(f"Refusing to replace existing executable: {link}")
        print("Install isolated Desloppify CLI from upstream HEAD; no upstream setup or hooks")
        if not self.dry_run:
            if environment.exists() and not (environment / "pyvenv.cfg").exists():
                shutil.rmtree(environment)
            if not command.exists():
                run([sys.executable, "-m", "venv", str(environment)])
            run([str(scripts / ("python.exe" if windows else "python")), "-m", "pip",
                 "install", "--upgrade", str(source) + "[full]"])
            run([str(command), "--version"])
            if windows:
                # Windows has no ~/.local/bin convention on PATH, and file symlinks need privileges.
                print(f"PENDING: add {scripts} to PATH to run desloppify")
            elif not link.is_symlink():
                link.parent.mkdir(parents=True, exist_ok=True)
                link.symlink_to(command)
