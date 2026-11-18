"""agentkit's subagents, rendered for each tool from the Markdown sources in agents/.

Claude Code and Cursor load agents/ from agentkit's native plugin, so they get a rendered copy only when
agentkit reaches them as linked skills. Every other tool reads agents only from its own folder. No copy
names a model, so each subagent runs on the model of the session that dispatches it.
"""

import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import actions

MARKER = "agentkit: generated from agents/"
READ_ONLY = frozenset({"Read", "Glob", "Grep"})
# Tools whose native agentkit plugin already loads agents/.
PLUGIN_LOADS_AGENTS = {"claude", "cursor"}


@dataclass(frozen=True)
class Agent:
    name: str
    description: str
    tools: tuple[str, ...]
    body: str

    @property
    def read_only(self) -> bool:
        return bool(self.tools) and set(self.tools) <= READ_ONLY


def parse(path: Path) -> Agent:
    """A source agent: flat `key: value` frontmatter in Claude Code's dialect, then the prompt."""
    _, head, body = path.read_text(encoding="utf-8").split("---\n", 2)
    fields = {key.strip(): value.strip()
              for key, _, value in (line.partition(":") for line in head.splitlines()) if value}
    tools = tuple(tool.strip() for tool in fields.get("tools", "").split(",") if tool.strip())
    return Agent(fields["name"], fields["description"], tools, body.strip() + "\n")


def sources() -> list[Agent]:
    return [parse(path) for path in sorted((actions.REPO / "agents").glob("*.md"))]


def markdown(agent: Agent, head: list[str]) -> str:
    return "---\n" + "\n".join(head) + f"\n---\n\n<!-- {MARKER}{agent.name}.md; install replaces this file -->\n\n{agent.body}"


def described(agent: Agent) -> list[str]:
    return [f"name: {agent.name}", f"description: {json.dumps(agent.description)}"]


def claude(agent: Agent) -> str:
    return markdown(agent, described(agent) + ([f"tools: {', '.join(agent.tools)}"] if agent.tools else []))


def cursor(agent: Agent) -> str:
    return markdown(agent, described(agent) + (["readonly: true"] if agent.read_only else []))


def kiro(agent: Agent) -> str:
    tools = [tool.lower() for tool in agent.tools]
    return markdown(agent, described(agent) + ([f"tools: {json.dumps(tools)}"] if tools else []))


def opencode(agent: Agent) -> str:
    """OpenCode's first config format, which Kilo shares and OpenCode's current one still reads."""
    head = [f"description: {json.dumps(agent.description)}", "mode: subagent"]
    return markdown(agent, head + (["permission:", "  edit: deny", "  bash: deny"] if agent.read_only else []))


def codex(agent: Agent) -> str:
    # A Codex agent cannot narrow its parent's sandbox, so read-only rests on no shell plus the prompt.
    lines = [f"# {MARKER}{agent.name}.md; install replaces this file", f"name = {json.dumps(agent.name)}",
             f"description = {json.dumps(agent.description)}", f"developer_instructions = {json.dumps(agent.body)}"]
    return "\n".join(lines + (["", "[features]", "shell_tool = false"] if agent.read_only else [])) + "\n"


RENDER: dict[str, Callable[[Agent], str]] = {
    "claude": claude, "cursor": cursor, "codex": codex, "kiro-ide": kiro, "kiro-cli": kiro,
    "opencode": opencode, "kilo": opencode}


def folders() -> dict[str, tuple[Path, str]]:
    """Each tool's user-level agent folder and the file suffix it reads."""
    kiro_folder = (actions.kiro_agent_file().parent, ".md")
    return {"claude": (actions.CLAUDE / "agents", ".md"), "cursor": (actions.HOME / ".cursor/agents", ".md"),
            "codex": (actions.CODEX / "agents", ".toml"), "kiro-ide": kiro_folder, "kiro-cli": kiro_folder,
            "opencode": (actions.CONFIG / "opencode/agents", ".md"), "kilo": (actions.CONFIG / "kilo/agents", ".md")}


def targets(selected: set[str], modes: dict[str, str]) -> dict[Path, str]:
    """Every rendered agent file the selected tools need, with its text."""
    places, agents, found = folders(), sources(), {}
    for tool in sorted(selected & RENDER.keys()):
        if tool in PLUGIN_LOADS_AGENTS and modes.get(tool) == "plugin":
            continue
        folder, suffix = places[tool]
        found |= {folder / f"{agent.name}{suffix}": RENDER[tool](agent) for agent in agents}
    return found


def ours(path: Path) -> bool:
    return path.is_file() and not path.is_symlink() and MARKER in path.read_text(encoding="utf-8", errors="replace")


def prune(installer: actions.Installer, tools: set[str], keep: dict[Path, str]) -> None:
    """Removes rendered agents in these tools' folders that are not in `keep`; the user's own files stay."""
    places = folders()
    for folder, suffix in sorted({places[tool] for tool in tools & RENDER.keys()}):
        for path in sorted(folder.glob(f"*{suffix}")) if folder.is_dir() else []:
            if path not in keep and ours(path):
                installer.remove_file(path)


def sync(installer: actions.Installer, selected: set[str], modes: dict[str, str]) -> None:
    wanted = targets(selected, modes)
    prune(installer, selected, wanted)
    for path, text in wanted.items():
        if path.exists() and not ours(path):
            print(f"PENDING: {path} is an agent you wrote; agentkit leaves it alone")
            continue
        installer.write_text(path, text)


def remove(installer: actions.Installer) -> None:
    prune(installer, set(RENDER), {})
