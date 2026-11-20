"""Removes the knowledge vault's lifecycle hooks that earlier releases registered in each tool's own
hook configuration. The vault now reaches agents through the vault skill and the nightly dream, so
nothing registers hooks anymore. Hooks another tool or the user wrote are left as they are."""

import json
from pathlib import Path

import actions

LEGACY_SCRIPT = "vault_hook.py"


def is_ours(entry: object) -> bool:
    """Entries an earlier release wrote: they ran vault_hook.py, directly or through a launcher in our hooks folder."""
    text = json.dumps(entry)
    return LEGACY_SCRIPT in text or json.dumps(str(actions.DATA / "hooks"))[1:-1] in text


def without_ours(hooks: dict) -> dict:
    """The hook map with our entries dropped and empty events removed."""
    kept = {event: [item for item in items if not is_ours(item)] for event, items in hooks.items()}
    return {event: items for event, items in kept.items() if items}


def claude(installer: actions.Installer) -> None:
    path = actions.CLAUDE / "settings.json"
    if not path.exists():
        return
    settings = actions.read_json(path)
    hooks = without_ours(settings.get("hooks", {}))
    settings.pop("hooks", None)
    if hooks:
        settings["hooks"] = hooks
    installer.write_json(path, settings)


def hook_file(installer: actions.Installer, path: Path, base: dict) -> None:
    """Update a hooks.json that holds only hooks; delete it when ours were all it held."""
    if not path.exists():
        return
    data = actions.read_json(path)
    data["hooks"] = without_ours(data.get("hooks", {}))
    if not data["hooks"] and set(data) <= {"hooks", *base}:
        installer.remove_file(path)
    else:
        installer.write_json(path, data)


def kiro(installer: actions.Installer) -> None:
    for path in (actions.DATA / "hooks").glob("vault-*.*"):
        installer.remove_file(path)
    crew = actions.HOME / ".kiro/crew/config.json"
    if crew.exists():
        settings = actions.read_json(crew)
        agent = settings.get("agent", {})
        hooks = without_ours(agent.get("kiro_hooks", {}))
        agent.pop("kiro_hooks", None)
        if hooks:
            agent["kiro_hooks"] = hooks
        if agent or "agent" in settings:
            settings["agent"] = agent
        installer.write_json(crew, settings)
    spec = actions.kiro_agent_file()
    if spec.exists() and actions.read_json(spec).get("name") == "agentkit":
        agent = actions.read_json(spec)
        agent.pop("hooks", None)
        installer.write_json(spec, agent)


def remove(installer: actions.Installer) -> None:
    """Drop our hooks from every tool, installed or not, so nothing stale runs a deleted script."""
    claude(installer)
    hook_file(installer, actions.CODEX / "hooks.json", {})
    hook_file(installer, actions.HOME / ".cursor/hooks.json", {"version": 1})
    kiro(installer)
