"""How agentkit itself reaches each tool: a native plugin where the tool supports one,
plain skill links otherwise, and the retraction when a recorded native install stops being right.

The shared ~/.agents/skills root is read natively by every reader among codex, cursor, kilo and
opencode, so a native self-delivery for one reader duplicates every skill the moment another
reader still needs the root. A reader therefore gets the native channel only when it is the
root's only selected reader."""

import json
import shutil
from pathlib import Path

import actions
import release

NATIVE_CHANNEL = {"claude", "codex", "cursor"}
MARKETPLACE = "agentkit"


def delivery_modes(selected: set[str], preference: str,
                   installed: set[str] | None = None) -> dict[str, str]:
    """plugin where a native channel exists and no shared-root reader is rivalled; links otherwise.

    Rivalry counts every reader selected now or recorded by an earlier install, so a narrowed
    --tools run cannot go native while other installed tools still read the shared root."""
    readers = (selected | (installed or set())) & actions.AGENTS_SKILLS_READERS
    modes = {}
    for tool in selected:
        native = tool in NATIVE_CHANNEL and preference != "links"
        if tool in readers and readers != {tool}:
            native = False
        modes[tool] = "plugin" if native else "links"
    return modes


def state_path() -> Path:
    return actions.STATE / "delivery.json"


def read_state() -> dict:
    try:
        value = actions.read_json(state_path())
    except (OSError, TypeError, ValueError):
        return {}
    return value if isinstance(value, dict) else {}


def preference(requested: str | None) -> str:
    """The delivery preference for this run: the flag, else the remembered one, else native."""
    return requested or read_state().get("preference") or "native"


def self_repository() -> str:
    return actions.run(["git", "-C", str(actions.REPO), "remote", "get-url", "origin"])


def cursor_ref(installer: actions.Installer) -> str | None:
    """The tag the main clone sits on, so Cursor never runs newer skills than the rest of the machine."""
    tag = release.exact_tag(actions.REPO)
    if tag:
        return tag
    if not installer.dry_run:
        actions.run(["git", "-C", str(actions.REPO), "fetch", "-q", "--tags", "origin"])
    latest = release.latest_tag(actions.REPO)
    if latest:
        print(f"PENDING: this tree is unreleased, so the Cursor clone pins the newest tag {latest}")
    return latest


def cursor_clone() -> Path:
    return actions.HOME / ".cursor/plugins/local/agentkit"


def attempt(installer: actions.Installer, tool: str, repository: str) -> str:
    if tool == "cursor":
        ref = cursor_ref(installer)
        if not ref:
            print("PENDING: no release tag to pin a Cursor clone on; installing Cursor skills as links")
            return "links"
        try:
            installer.checkout(MARKETPLACE, {"repository": repository},
                               destination=cursor_clone(), ref=ref)
        except (RuntimeError, ValueError) as error:
            print(f"PENDING: Cursor clone failed ({error}); installing Cursor skills as links")
            return "links"
        print(f"Cursor: agentkit clone pinned at {ref}; reload Cursor to load it")
        return "plugin"
    if installer.native_plugin(tool, MARKETPLACE, repository, MARKETPLACE):
        return "plugin"
    return "links"


def remove_native(installer: actions.Installer, tool: str, repository: str | None) -> None:
    if tool == "cursor":
        clone = cursor_clone()
        if not clone.exists():
            return
        try:
            origin = actions.run(["git", "-C", str(clone), "remote", "get-url", "origin"])
        except RuntimeError:
            origin = None
        if repository and origin == repository:
            print(f"Remove {clone}")
            if not installer.dry_run:
                shutil.rmtree(clone)
        else:
            print(f"PENDING: {clone} is not this repository's clone; remove it yourself")
        return
    if not shutil.which(tool):
        print(f"PENDING: remove the agentkit plugin from {tool} yourself")
        return
    verb = "uninstall" if tool == "claude" else "remove"
    print(f"Remove native {tool} plugin {MARKETPLACE}@{MARKETPLACE}")
    if not installer.dry_run:
        try:
            actions.run([tool, "plugin", verb, f"{MARKETPLACE}@{MARKETPLACE}"])
        except RuntimeError as error:
            print(f"PENDING: {tool} plugin removal failed ({error})")


def resolve(installer: actions.Installer, selected: set[str], wanted: str | None) -> dict[str, str]:
    """Attempt the planned channels, fall back to links, undo dropped ones, and record the result.

    Tools absent from this run keep their recorded delivery, so a narrowed --tools run neither
    retracts their native installs nor loses the rivalry their readers create."""
    chosen = preference(wanted)
    recorded = read_state().get("resolved", {})
    plan = delivery_modes(selected, chosen, set(recorded))
    readers = (selected | set(recorded)) & actions.AGENTS_SKILLS_READERS
    for tool, mode in plan.items():
        if mode == "links" and tool in NATIVE_CHANNEL and tool in readers and readers != {tool}:
            rivals = ", ".join(sorted(readers - {tool}))
            print(f"agentkit stays as skills for {tool} because {rivals} also reads "
                  "~/.agents/skills and a native plugin would load every skill twice")
    try:
        repository = self_repository()
    except RuntimeError:
        print("PENDING: this clone has no git origin, so agentkit installs as skills everywhere")
        plan = dict.fromkeys(selected, "links")
        repository = None
    resolved = dict(recorded)
    for tool in selected:
        resolved[tool] = attempt(installer, tool, repository) if plan[tool] == "plugin" else "links"
    for tool, was in recorded.items():
        if was == "plugin" and resolved[tool] == "links":
            remove_native(installer, tool, repository)
    if not installer.dry_run:
        state_path().parent.mkdir(parents=True, exist_ok=True)
        state_path().write_text(json.dumps({"preference": chosen, "resolved": resolved},
                                           indent=2) + "\n", encoding="utf-8")
    return resolved


def cleanup(installer: actions.Installer) -> None:
    """Undo every native self-install the state records; used by uninstall."""
    try:
        repository = self_repository()
    except RuntimeError:
        repository = None
    for tool, was in read_state().get("resolved", {}).items():
        if was == "plugin":
            remove_native(installer, tool, repository)
    if not installer.dry_run:
        state_path().unlink(missing_ok=True)
