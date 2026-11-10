"""What to install: the tools on this machine, the plugins the user chose, and what to do
with instruction files the user wrote."""

import json
import re
import shutil
import sys
from pathlib import Path

import actions
import instruction_block

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


def store_selection(plugins: set[str]) -> None:
    actions.STATE.mkdir(parents=True, exist_ok=True)
    (actions.STATE / "plugins.json").write_text(json.dumps({"selected": sorted(plugins)}))


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
    stored = actions.STATE / "plugins.json"
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
