#!/usr/bin/env python3
"""Check local tickets against the to-tickets template and dependency order.

    validate_tickets.py FOLDER

FOLDER holds one Markdown file per ticket, named NN-slug.md, numbered from 01 with
blockers before the tickets they gate. Each Blocked by value lists ticket numbers
separated by commas, or reads "None (can start immediately)". Exits 1 on any problem.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

NONE = "None (can start immediately)"
FILE_NAME = re.compile(r"^(\d{2})-[a-z0-9]+(?:-[a-z0-9]+)*\.md$")
HEADING = re.compile(r"^# (\d{2}): \S", re.MULTILINE)
BLOCKED_BY = re.compile(r"^\*\*Blocked by:\*\* (.+)$", re.MULTILINE)
STATUS = re.compile(r"^\*\*Status:\*\* \S", re.MULTILINE)
CRITERION = re.compile(r"^- \[ \] \S", re.MULTILINE)
FENCE = re.compile(r"^\s*```", re.MULTILINE)
# A path has at least one slash and ends in a short extension, so "and/or" does not match.
PATH = re.compile(r"(?<![\w.])(?:\.{1,2}/|/)?[\w.-]+(?:/[\w.-]+)+\.[A-Za-z0-9]{1,5}\b")
BLOCKER_NUMBER = re.compile(r"(\d{2})\b")


def check_tickets(texts: dict[str, str]) -> list[str]:
    """Return one message per problem, each prefixed with the ticket file it concerns."""
    if not texts:
        return ["no tickets found"]
    problems = []
    numbers = {}
    for name, text in sorted(texts.items()):
        match = FILE_NAME.match(name)
        if match is None:
            problems.append(f"{name}: file name must be NN-slug.md")
            continue
        numbers[name] = int(match.group(1))
        problems.extend(f"{name}: {problem}" for problem in check_ticket(int(match.group(1)), text))
    problems.extend(check_numbering(numbers, texts))
    return problems


def check_ticket(number: int, text: str) -> list[str]:
    problems = []
    heading = HEADING.search(text)
    if heading is None:
        problems.append("heading must be '# NN: title'")
    elif int(heading.group(1)) != number:
        problems.append(f"heading number {heading.group(1)} does not match file number {number:02d}")
    if STATUS.search(text) is None:
        problems.append("missing **Status:** line")
    if CRITERION.search(text) is None:
        problems.append("needs at least one acceptance criterion as '- [ ] ...'")
    path = PATH.search(text)
    if path:
        problems.append(f"contains a file path: {path.group(0)}")
    if FENCE.search(text):
        problems.append("contains a code fence; tickets describe behaviour, not code")
    return problems


def check_numbering(numbers: dict[str, int], texts: dict[str, str]) -> list[str]:
    problems = []
    if sorted(numbers.values()) != list(range(1, len(numbers) + 1)):
        problems.append("ticket numbers must be consecutive from 01")
    by_number = {number: name for name, number in numbers.items()}
    for name, number in sorted(numbers.items()):
        match = BLOCKED_BY.search(texts[name])
        if match is None:
            problems.append(f"{name}: missing **Blocked by:** line")
            continue
        if match.group(1).strip() == NONE:
            continue
        for item in match.group(1).split(","):
            blocker = BLOCKER_NUMBER.match(item.strip())
            if blocker is None:
                problems.append(f"{name}: blocker '{item.strip()}' must start with a ticket number")
                continue
            blocker_number = int(blocker.group(1))
            if blocker_number not in by_number:
                problems.append(f"{name}: blocker {blocker_number:02d} does not exist")
            elif blocker_number >= number:
                problems.append(f"{name}: blocker {blocker_number:02d} must come before ticket {number:02d}")
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check local tickets against the to-tickets template.")
    parser.add_argument("folder", type=Path)
    args = parser.parse_args(argv)
    texts = {path.name: path.read_text(encoding="utf-8") for path in sorted(args.folder.glob("*.md"))}
    problems = check_tickets(texts)
    for problem in problems:
        print(problem)
    if problems:
        return 1
    print(f"{len(texts)} ticket(s) OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
