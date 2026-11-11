"""Registers the knowledge vault's lifecycle hook in each tool's own hook configuration, and removes
it again when the obsidian plugin is deselected or agentkit is uninstalled. Hooks another tool or
the user wrote are left as they are."""

import json
import os
import shlex
import subprocess
from pathlib import Path

import actions

HOOK = Path("plugins/obsidian/scripts/vault_hook.py")
CLAUDE_EVENTS = {"SessionStart": "start", "UserPromptSubmit": "prompt", "Stop": "stop"}
CODEX_EVENTS = CLAUDE_EVENTS
# Cursor cannot add context on prompt submit.
CURSOR_EVENTS = {"sessionStart": "start", "stop": "stop"}
# Kiro has no stop hook that can continue a turn.
KIRO_EVENTS = {"agentSpawn": "start", "userPromptSubmit": "prompt"}


def script() -> Path:
    return actions.REPO / HOOK


def is_ours(entry: object) -> bool:
    """Our hook entries: they run vault_hook.py, directly or through a launcher in our hooks folder."""
    text = json.dumps(entry)
    return "vault_hook.py" in text or json.dumps(str(actions.DATA / "hooks"))[1:-1] in text


def command_line(event: str, tool: str) -> str:
    argv = [str(actions.python_launcher()), str(script()), event, "--tool", tool]
    return subprocess.list2cmdline(argv) if os.name == "nt" else shlex.join(argv)


def merge(hooks: dict, events: dict[str, str], entry, enabled: bool) -> dict:
    """The hook map with our entries replaced, or dropped, and empty events removed."""
    merged = {}
    for event in dict.fromkeys([*hooks, *events]):
        # Ours goes first, so other installers appending their own hooks keep a stable order.
        kept = [entry(events[event])] if enabled and event in events else []
        kept += [item for item in hooks.get(event, []) if not is_ours(item)]
        if kept:
            merged[event] = kept
    return merged


def claude(installer: actions.Installer, enabled: bool) -> None:
    path = actions.CLAUDE / "settings.json"
    if not path.exists() and not enabled:
        return
    settings = actions.read_json(path)
    hooks = merge(settings.get("hooks", {}), CLAUDE_EVENTS, lambda event: {"hooks": [
        {"type": "command", "command": str(actions.python_launcher()), "args": [str(script()), event, "--tool", "claude"]}]},
        enabled)
    settings.pop("hooks", None)
    if hooks:
        settings["hooks"] = hooks
    installer.write_json(path, settings)


def hook_file(installer: actions.Installer, path: Path, base: dict, events: dict[str, str], entry,
              enabled: bool) -> bool:
    """Update a hooks.json that holds only hooks; delete it when ours were all it held."""
    if not path.exists() and not enabled:
        return False
    data = actions.read_json(path) or dict(base)
    hooks = merge(data.get("hooks", {}), events, entry, enabled)
    data["hooks"] = hooks
    if not hooks and set(data) <= {"hooks", *base}:
        if path.exists():
            installer.remove_file(path)
        return False
    before = actions.read_json(path)
    installer.write_json(path, data)
    return before != data


def shims(installer: actions.Installer, enabled: bool) -> dict[str, str]:
    """Kiro needs an existing absolute file per hook, so each event gets a small launcher."""
    folder = actions.DATA / "hooks"
    found = {}
    for event, argument in KIRO_EVENTS.items():
        path = folder / (f"vault-{argument}.cmd" if os.name == "nt" else f"vault-{argument}.sh")
        if not enabled:
            if path.exists():
                installer.remove_file(path)
            continue
        line = command_line(argument, "kiro")
        installer.write_text(path, f"@{line}\r\n" if os.name == "nt" else f"#!/bin/sh\nexec {line}\n")
        if not installer.dry_run and os.name != "nt":
            path.chmod(0o755)
        found[event] = str(path)
    return found


def kiro(installer: actions.Installer, selected: set[str], enabled: bool) -> None:
    commands = shims(installer, enabled and bool({"crew", "kiro-cli"} & selected))
    by_argument = {KIRO_EVENTS[event]: command for event, command in commands.items()}
    crew = actions.HOME / ".kiro/crew/config.json"
    if "crew" in selected and crew.exists():
        settings = actions.read_json(crew)
        agent = settings.get("agent", {})
        hooks = merge(agent.get("kiro_hooks", {}), KIRO_EVENTS,
                      lambda argument: {"command": by_argument[argument]}, enabled)
        agent.pop("kiro_hooks", None)
        if hooks:
            agent["kiro_hooks"] = hooks
        if agent or "agent" in settings:
            settings["agent"] = agent
        installer.write_json(crew, settings)
    spec = Path(os.environ.get("KIRO_AGENT_CONFIG_DIR", actions.HOME / ".kiro/agents")) / "agentkit.json"
    if "kiro-cli" in selected and spec.exists() and actions.read_json(spec).get("name") == "agentkit":
        agent = actions.read_json(spec)
        agent.pop("hooks", None)
        if enabled:
            agent["hooks"] = {event: [{"command": command}] for event, command in commands.items()}
        installer.write_json(spec, agent)


def sync(installer: actions.Installer, selected: set[str], enabled: bool) -> None:
    if not enabled:
        # Remove from every tool, installed or not, so nothing stale is left behind.
        selected = set(actions.TOOLS)
    if "claude" in selected:
        claude(installer, enabled)
    if "codex" in selected and hook_file(
            installer, actions.CODEX / "hooks.json", {}, CODEX_EVENTS,
            lambda event: {"hooks": [{"type": "command", "command": command_line(event, "codex")}]}, enabled):
        print("PENDING: open /hooks in Codex and trust the agentkit vault hooks")
    if "cursor" in selected:
        hook_file(installer, actions.HOME / ".cursor/hooks.json", {"version": 1}, CURSOR_EVENTS,
                  lambda event: {"command": command_line(event, "cursor"),
                                 **({"loop_limit": 1} if event == "stop" else {})}, enabled)
    kiro(installer, selected, enabled)
