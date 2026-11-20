#!/usr/bin/env python3
"""Check local tickets against the to-tickets template and dependency order.

    validate_tickets.py FOLDER

FOLDER holds one Markdown file per ticket, named NN-slug.md, numbered from 01 with
blockers before the tickets they gate. Each Blocked by value lists two-digit ticket
numbers separated by commas, semicolons or "and", or reads "None (can start immediately)".
Other Markdown files in FOLDER are skipped. Exits 1 on any problem.
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
BLOCKER_SEPARATOR = re.compile(r",|;|\band\b")
BLOCKER_NUMBER = re.compile(r"[0-9]{2}")


def is_ticket_file(name: str) -> bool:
    return FILE_NAME.match(name) is not None


def check_tickets(texts: dict[str, str]) -> list[str]:
    """Return one message per problem, each prefixed with the ticket file it concerns."""
    tickets = {name: text for name, text in texts.items() if is_ticket_file(name)}
    if not tickets:
        return ["no tickets found"]
    problems = []
    numbers = {}
    for name, text in sorted(tickets.items()):
        match = FILE_NAME.match(name)
        assert match is not None, "check_tickets keeps only ticket file names"
        number = int(match.group(1))
        numbers[name] = number
        problems.extend(f"{name}: {problem}" for problem in check_ticket(number, text))
    problems.extend(check_numbering(numbers, tickets))
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
        for item in BLOCKER_SEPARATOR.split(match.group(1)):
            item = item.strip()
            if BLOCKER_NUMBER.fullmatch(item) is None:
                problems.append(f"{name}: blocker '{item}' must be a two-digit ticket number")
                continue
            blocker_number = int(item)
            if blocker_number not in by_number:
                problems.append(f"{name}: blocker {blocker_number:02d} does not exist")
            elif blocker_number >= number:
                problems.append(f"{name}: blocker {blocker_number:02d} must come before ticket {number:02d}")
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check local tickets against the to-tickets template.")
    parser.add_argument("folder", type=Path)
    args = parser.parse_args(argv)
    texts = {}
    for path in sorted(args.folder.glob("*.md")):
        if is_ticket_file(path.name):
            texts[path.name] = path.read_text(encoding="utf-8")
        else:
            print(f"skipped {path.name}")
    problems = check_tickets(texts)
    for problem in problems:
        print(problem)
    if problems:
        return 1
    print(f"{len(texts)} ticket(s) OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
