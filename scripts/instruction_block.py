"""The agentkit block inside a tool's global instruction file, such as ~/.codex/AGENTS.md."""

from pathlib import Path
from typing import Protocol

BEGIN = "<!-- agentkit:begin"
END = "<!-- agentkit:end -->"
MODES = ("keep", "append", "replace")


class Writer(Protocol):
    dry_run: bool

    def write_text(self, path: Path, text: str) -> None: ...

    def remove_file(self, path: Path) -> None: ...


def block(source: Path, body: str) -> str:
    return (f"{BEGIN} from {source.as_posix()}. Install replaces everything up to the end marker. -->\n"
            f"{body.rstrip()}\n{END}\n")


def split(text: str) -> tuple[str, str] | None:
    """The text before and after the agentkit block, or None when there is none."""
    start = text.find(BEGIN)
    end = text.find(END, start) if start >= 0 else -1
    if end < 0:
        return None
    return text[:start], text[end + len(END):].lstrip("\n")


def render(existing: str | None, source: Path, body: str, mode: str) -> str | None:
    """The new file text, or None when a foreign file must stay as it is."""
    ours = block(source, body)
    if existing is None:
        return ours
    parts = split(existing)
    if parts:
        return parts[0] + ours + (f"\n{parts[1]}" if parts[1] else "")
    if mode == "replace":
        return ours
    if mode == "append":
        return f"{existing.rstrip()}\n\n{ours}" if existing.strip() else ours
    return None


def strip(existing: str) -> str | None:
    """The file text without the agentkit block, or None when it has none."""
    parts = split(existing)
    if parts is None:
        return None
    kept = [part.strip("\n") for part in parts if part.strip()]
    return "\n\n".join(kept) + "\n" if kept else ""


def legacy_link(path: Path, source: Path) -> bool:
    """The instruction symlink that earlier versions of the installer created."""
    return path.is_symlink() and path.resolve() == source.resolve()


def is_foreign(path: Path) -> bool:
    """The user's own instruction file, which agentkit changes only when told how."""
    return (path.is_file() and not path.is_symlink()
            and split(path.read_text(encoding="utf-8")) is None)


def sync(writer: Writer, path: Path, source: Path, body: str, mode: str) -> None:
    legacy = legacy_link(path, source)
    if legacy:
        writer.remove_file(path)
    elif path.is_symlink():
        print(f"PENDING: {path} is a symlink you manage; agentkit leaves it alone")
        return
    existing = path.read_text(encoding="utf-8") if path.is_file() and not legacy else None
    text = render(existing, source, body, mode)
    if text is None:
        print(f"Keep your {path}; rerun with --instructions append or replace to change it")
    elif legacy and writer.dry_run:
        print(f"Update {path}")
    else:
        writer.write_text(path, text)


def remove(writer: Writer, path: Path, source: Path) -> None:
    """Take the agentkit block out, deleting the file when nothing else is left."""
    if legacy_link(path, source):
        writer.remove_file(path)
    elif path.is_file() and not path.is_symlink():
        rest = strip(path.read_text(encoding="utf-8"))
        if rest == "":
            writer.remove_file(path)
        elif rest is not None:
            writer.write_text(path, rest)
