"""What to install: the tools on this machine, the plugins the user chose, and what to do
with instruction files the user wrote."""

import json
import re
import shutil
import sys
from pathlib import Path

import actions
import instruction_block

MANIFEST_FIELDS = {"repository", "marketplace", "skills", "opencode", "cli", "companion", "description"}


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
        if "companion" in entry and not is_repository_folder(entry["companion"]):
            raise ValueError(f"Companion for {name} must be a folder inside this repository: {entry['companion']}")


def is_repository_folder(value: object) -> bool:
    """A non-empty relative path that stays inside the repository."""
    return (isinstance(value, str) and bool(value) and not Path(value).is_absolute()
            and not value.startswith(("/", "\\")) and ".." not in Path(value).parts)


def store_selection(plugins: set[str], offered: set[str]) -> None:
    """Remember the chosen plugins and every plugin the user has been asked about."""
    actions.STATE.mkdir(parents=True, exist_ok=True)
    (actions.STATE / "plugins.json").write_text(json.dumps(
        {"selected": sorted(plugins), "offered": sorted(offered)}))


def catalog(manifest: dict, names: set[str]) -> str:
    return ", ".join(f"{name} ({manifest[name].get('description', 'no description')})"
                     for name in sorted(names))


def ask_plugins(manifest: dict, names: set[str]) -> set[str]:
    print("Select the third-party plugins to install:")
    chosen = set()
    for name in sorted(names):
        answer = input(f"  {name} ({manifest[name].get('description', '')}) [Y/n] ").strip().lower()
        if answer not in ("n", "no"):
            chosen.add(name)
    return chosen


def stored_selection() -> tuple[set[str], set[str]] | None:
    """The saved (selected, offered) plugins. A selection saved before offers were recorded
    counts its own plugins as offered."""
    stored = actions.STATE / "plugins.json"
    if not stored.exists():
        return None
    try:
        saved = json.loads(stored.read_text())
    except ValueError:
        return None
    if not isinstance(saved, dict):
        return None
    selected = set(saved.get("selected", []))
    return selected, set(saved.get("offered", selected))


def select_plugins(manifest: dict, requested: str | None, persist: bool = True) -> set[str]:
    names = set(manifest)
    if requested:
        wanted = {name.strip() for name in requested.split(",") if name.strip()}
        if wanted == {"all"}:
            chosen = set(names)
        elif wanted == {"none"}:
            chosen = set()
        else:
            unknown = wanted - names
            if unknown:
                raise ValueError(f"Unknown plugins: {', '.join(sorted(unknown))}. "
                                 f"Available: {catalog(manifest, names)}")
            chosen = wanted
        if persist:
            store_selection(chosen, names)
        return chosen
    saved = stored_selection()
    selected, offered = (set(), set()) if saved is None else (saved[0] & names, saved[1])
    unasked = names - offered
    if not unasked:
        return selected
    if sys.stdin.isatty():
        chosen = selected | ask_plugins(manifest, unasked)
        if persist:
            store_selection(chosen, offered | names)
        return chosen
    # No terminal: make the choice explicit instead of installing anything unasked.
    # The question comes from the process.
    if saved is None:
        raise ValueError(
            "Choose the third-party plugins to install. Available: " + catalog(manifest, names) +
            ". Rerun with --plugins <comma-separated-names>, --plugins all or --plugins none.")
    keep = ",".join(sorted(selected)) or "none"
    raise ValueError(
        f"New plugins to choose: {catalog(manifest, unasked)}. Rerun with "
        f"--plugins {','.join(sorted(selected | unasked))} to add them, or "
        f"--plugins {keep} to skip them.")


def kiro_ide_installed() -> bool:
    """The Kiro IDE app, which shares ~/.kiro with the CLI and Crew."""
    return bool(shutil.which("kiro")) or any(path.exists() for path in actions.KIRO_IDE)


def kilo_installed() -> bool:
    """Kilo Code CLI, its config tree, or an IDE extension that has not run yet."""
    editors = (".vscode", ".vscode-insiders", ".cursor", ".windsurf")
    extensions = [match for editor in editors
                  for match in (actions.HOME / editor / "extensions").glob("kilocode.kilo-code-*")]
    return bool(shutil.which("kilo") or (actions.HOME / ".kilo").exists()
                or (actions.CONFIG / "kilo").exists() or extensions)


def detect_tools() -> set[str]:
    """Tools present on this machine; the three Kiro tools are detected separately."""
    binaries = {"crew": "kirocrew", "kiro-cli": "kiro-cli"}
    selected = set()
    for name, root in actions.TOOLS.items():
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


def ask_instruction_mode(path: Path) -> str:
    print(f"WARNING: {path} already holds your own instructions.\n"
          "  keep     leave it as it is, without agentkit's instructions\n"
          "  append   add agentkit's instructions below yours\n"
          "  replace  use only agentkit's instructions; yours are backed up first")
    answer = input("Choose keep, append or replace [keep]: ").strip().lower() or "keep"
    if answer not in instruction_block.MODES:
        raise ValueError(f"Unknown choice for {path}: {answer}")
    return answer


def choose_instruction_modes(paths: list[Path], requested: str | None, store: Path, persist: bool) -> dict[Path, str]:
    """The mode for each foreign file. Only keep is remembered: the other two leave a block."""
    foreign = [path for path in paths if instruction_block.is_foreign(path)]
    kept = set(json.loads(store.read_text(encoding="utf-8")).get("keep", [])) if store.exists() else set()
    modes = {}
    for path in foreign:
        if requested:
            modes[path] = requested
        elif str(path) in kept:
            modes[path] = "keep"
        elif sys.stdin.isatty():
            modes[path] = ask_instruction_mode(path)
        else:
            # No terminal: the question comes from the process, as with plugin selection.
            raise ValueError(
                f"{path} already holds your own instructions. Rerun with --instructions keep "
                "(leave it), --instructions append (add agentkit's below yours) or "
                "--instructions replace (yours are backed up first).")
    if persist and modes:
        kept = (kept - {str(path) for path in modes}) | {
            str(path) for path, mode in modes.items() if mode == "keep"}
        store.parent.mkdir(parents=True, exist_ok=True)
        store.write_text(json.dumps({"keep": sorted(kept)}), encoding="utf-8")
    return modes


DREAM_TIME = "03:00"


def dream_question(available: dict[str, str]) -> str:
    found = ", ".join(sorted(available)) or "none of the supported agent CLIs"
    example = min(available) if available else "<cli>"
    return ("Choose how the nightly vault dream runs: which agent CLI, which model and when. "
            f"Found here: {found}. Rerun with --dream {example} (or another found CLI), optionally "
            f"--dream-model <model id> (default: the CLI's own default) and --dream-time HH:MM "
            f"(default {DREAM_TIME}). Use --dream-command '<command>' to run any other agent CLI, "
            "which gets the prompt as its last argument or in place of {prompt}. Use --dream none to skip it.")


def ask_dream(available: dict[str, str]) -> dict:
    names = "/".join([*sorted(available), "command", "none"])
    runner = input(f"Run the nightly vault dream with [{names}] (none): ").strip().lower() or "none"
    if runner == "none":
        return {"runner": "none"}
    answer: dict[str, str | None] = {"runner": runner}
    if runner == "command":
        answer["command"] = input("Command that runs your agent headless: ").strip()
    else:
        answer["model"] = input("Model id (blank for the CLI's default): ").strip() or None
    answer["time"] = input(f"Time of day, HH:MM ({DREAM_TIME}): ").strip() or DREAM_TIME
    return answer


def validate_dream(requested: dict, available: dict[str, str]) -> dict:
    runner = requested.get("runner")
    if runner == "none":
        return {"runner": "none"}
    time = requested.get("time") or DREAM_TIME
    if not re.fullmatch(r"([01]\d|2[0-3]):[0-5]\d", time):
        raise ValueError(f"Dream time must be HH:MM in 24-hour time: {time}")
    if runner == "command":
        if not requested.get("command"):
            raise ValueError("--dream command needs the command itself: pass --dream-command '<command>'")
        return {"runner": "command", "command": requested["command"], "time": time}
    if runner not in available:
        raise ValueError(f"No {runner} agent CLI found on this machine. {dream_question(available)}")
    return {"runner": runner, "model": requested.get("model") or None, "time": time}


def choose_dream(requested: dict | None, available: dict[str, str], store: Path, persist: bool) -> dict:
    """How the dream runs: the answer given now, else the saved one, else the user's answer."""
    if requested is None and store.exists():
        return json.loads(store.read_text(encoding="utf-8"))
    if requested is None:
        if not sys.stdin.isatty():
            # No terminal: the question comes from the process, as with plugin selection.
            raise ValueError(dream_question(available))
        requested = ask_dream(available)
    dream = validate_dream(requested, available)
    if persist:
        store.parent.mkdir(parents=True, exist_ok=True)
        store.write_text(json.dumps(dream), encoding="utf-8")
    return dream
