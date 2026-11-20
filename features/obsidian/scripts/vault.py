"""The knowledge vault: where it is, its layout and the properties its notes carry.

Standard library only."""

import os
import re
from pathlib import Path

# The vault layout. The vault's own AGENTS.md describes what each area holds.
INBOX, NOTES, CATEGORIES = "00 Inbox", "10 Notes", "20 Categories"
SYSTEM = "90 System"
# Retired notes keep their names and history.
ARCHIVE = f"{SYSTEM}/Archive"


def home() -> Path:
    return Path(os.environ["HOME"]) if os.environ.get("HOME") else Path.home()


def config_dir() -> Path:
    return Path(os.environ.get("XDG_CONFIG_HOME") or home() / ".config")


def state_dir() -> Path:
    return Path(os.environ.get("XDG_STATE_HOME") or home() / ".local/state") / "agentkit/vault"


def locate() -> Path | None:
    """The vault named in AGENTS.local.md, else ~/knowledge; None unless it is a set-up vault."""
    notes = config_dir() / "agentkit/AGENTS.local.md"
    path = home() / "knowledge"
    if notes.is_file():
        named = re.search(r"^Knowledge vault:\s*(.+?)\s*$", notes.read_text(encoding="utf-8"), re.MULTILINE)
        if named:
            path = Path(named[1]).expanduser()
    return path if (path / ".obsidian").is_dir() and (path / "AGENTS.md").is_file() else None


def clean(value: str) -> str:
    return value.strip().strip("'\"").replace("[[", "").replace("]]", "")


def properties(path: Path) -> dict[str, list[str]]:
    """The simple YAML frontmatter notes use: scalars, inline lists and block lists."""
    with path.open(encoding="utf-8", errors="replace") as handle:
        head = handle.read(4096)
    end = head.find("\n---", 3)
    if not head.startswith("---") or end < 0:
        return {}
    found: dict[str, list[str]] = {}
    key = None
    for line in head[3:end].splitlines():
        item = re.match(r"\s+-\s+(.*)", line)
        if item and key:
            found[key].append(clean(item[1]))
            continue
        pair = re.match(r"([\w-]+):\s*(.*)", line)
        if pair:
            key, value = pair[1], pair[2].strip()
            if value.startswith("[") and value.endswith("]"):
                found[key] = [clean(part) for part in value[1:-1].split(",") if part.strip()]
            else:
                found[key] = [clean(value)] if value else []
    return found
