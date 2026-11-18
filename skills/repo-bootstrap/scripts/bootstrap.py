#!/usr/bin/env python3
"""Check and apply the agent-configuration layout in a project repository.

    bootstrap.py check [--root PATH] [--link PATH ...]
    bootstrap.py apply [--root PATH] [--link PATH ...]

check lists what is missing. apply makes the missing parts that can be made without
choosing project content, never overwrites an existing file, and lists what remains.
--link names a tool skills directory that must point at .agents/skills (default .claude/skills).
"""

from __future__ import annotations

import argparse
import os
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from functools import partial
from pathlib import Path

SHARED_SKILLS = ".agents/skills"
LOCAL_OVERRIDES = "AGENTS.local.md"
POINTER = "@AGENTS.md"
WORKTREE_SECRETS = ".env.local"
DEFAULT_LINKS = [".claude/skills"]


@dataclass(frozen=True)
class Finding:
    message: str
    fix: Callable[[], None] | None = None


def findings(root: Path, links: list[str]) -> list[Finding]:
    """Return every gap in the layout. Only findings with a fix can be applied."""
    found = []
    agents = root / "AGENTS.md"
    if not agents.is_file():
        found.append(Finding("AGENTS.md is missing; write the project's rulebook"))
    elif LOCAL_OVERRIDES not in agents.read_text(encoding="utf-8"):
        found.append(Finding(f"AGENTS.md does not mention {LOCAL_OVERRIDES}, where local overrides live"))
    found.extend(claude_pointer(root))
    found.extend(shared_skills(root))
    found.extend(gitignore(root, [LOCAL_OVERRIDES, *links]))
    for link in links:
        found.extend(tool_link(root, link))
    found.extend(worktree_include(root))
    return found


def apply(root: Path, links: list[str]) -> tuple[list[str], list[Finding]]:
    """Run every available fix, then return the messages fixed and the findings that remain."""
    fixed = []
    for finding in findings(root, links):
        if finding.fix is not None:
            finding.fix()
            fixed.append(finding.message)
    return fixed, findings(root, links)


def claude_pointer(root: Path) -> list[Finding]:
    path = root / "CLAUDE.md"
    if not path.exists():
        return [Finding(f"CLAUDE.md is missing; it should hold the single line {POINTER}",
                        partial(write_text, path, POINTER + "\n"))]
    if path.read_text(encoding="utf-8").strip() != POINTER:
        return [Finding(f"CLAUDE.md must contain only {POINTER}; move its content into AGENTS.md by hand")]
    return []


def shared_skills(root: Path) -> list[Finding]:
    path = root / SHARED_SKILLS
    if path.is_dir():
        return []
    return [Finding(f"{SHARED_SKILLS} is missing", partial(path.mkdir, parents=True, exist_ok=True))]


def gitignore(root: Path, entries: list[str]) -> list[Finding]:
    path = root / ".gitignore"
    lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    return [Finding(f".gitignore does not list {entry}", partial(append_line, path, entry))
            for entry in entries if entry not in lines]


def tool_link(root: Path, link: str) -> list[Finding]:
    path = root / link
    target = root / SHARED_SKILLS
    if os.path.lexists(path):
        if path.exists() and path.resolve() == target.resolve():
            return []
        return [Finding(f"{link} exists but does not point to {SHARED_SKILLS}; remove it by hand")]
    return [Finding(f"{link} is missing", partial(create_link, path, target))]


def worktree_include(root: Path) -> list[Finding]:
    if not (root / WORKTREE_SECRETS).exists():
        return []
    path = root / ".worktreeinclude"
    if path.is_file() and WORKTREE_SECRETS in [line.strip() for line in path.read_text(encoding="utf-8").splitlines()]:
        return []
    return [Finding(f"{WORKTREE_SECRETS} exists but .worktreeinclude does not name it")]


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def append_line(path: Path, line: str) -> None:
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    if text and not text.endswith("\n"):
        text += "\n"
    write_text(path, text + line + "\n")


def create_link(path: Path, target: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if os.name == "nt":
        # A junction needs neither Developer Mode nor admin rights, unlike a symlink.
        subprocess.run(["cmd", "/c", "mklink", "/J", str(path), str(target)], check=True)
    else:
        path.symlink_to(os.path.relpath(target, path.parent), target_is_directory=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check and apply the agent-configuration layout.")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("check", "apply"):
        command = commands.add_parser(name)
        command.add_argument("--root", type=Path, default=Path.cwd())
        command.add_argument("--link", action="append", dest="links")
    args = parser.parse_args(argv)
    links = args.links or DEFAULT_LINKS
    if args.command == "apply":
        fixed, remaining = apply(args.root, links)
        for message in fixed:
            print(f"fixed: {message}")
    else:
        remaining = findings(args.root, links)
    for finding in remaining:
        print(finding.message)
    if remaining:
        return 1
    print("layout OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
