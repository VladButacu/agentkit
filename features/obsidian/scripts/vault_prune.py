"""Retiring vault notes: finds those that look obsolete and moves approved ones into the archive.

Standard library only. `vault-prune` reads the candidates; the dream applies approved archive proposals.
Usage: vault_prune.py candidates [--days N]"""

import argparse
import datetime
import json
import re
import sys
from pathlib import Path

import vault

STALE_DAYS = 180
# Absolute or home-relative paths in code spans. A bare `/clear` is a command, so a path needs a second part.
PATH_SPAN = re.compile(r"`(~/[^`\s]+|/[^`\s/]+/[^`\s]+)`")
LINK = re.compile(r"\[\[([^\]|#]+)")


def day(value: str) -> datetime.date | None:
    try:
        return datetime.date.fromisoformat(value)
    except ValueError:
        return None


def last_touched(path: Path, meta: dict[str, list[str]]) -> datetime.date:
    dates = [found for key in ("updated", "created", "reviewed")
             if (found := day(" ".join(meta.get(key, []))))]
    return max(dates, default=datetime.date.fromtimestamp(path.stat().st_mtime))


def missing_paths(text: str) -> list[str]:
    found = dict.fromkeys(path for path in PATH_SPAN.findall(text) if not Path(path).expanduser().exists())
    return list(found)


def linked_names(root: Path) -> dict[str, set[str]]:
    """For each note file, the names of the notes it links to."""
    links = {}
    for folder in (vault.NOTES, vault.INBOX, vault.CATEGORIES):
        for path in (root / folder).rglob("*.md"):
            links[str(path)] = {name.strip() for name in LINK.findall(path.read_text(encoding="utf-8", errors="replace"))}
    home = root / "Home.md"
    if home.is_file():
        links[str(home)] = {name.strip() for name in LINK.findall(home.read_text(encoding="utf-8", errors="replace"))}
    return links


def candidates(root: Path, today: datetime.date, days: int = STALE_DAYS) -> list[dict]:
    """Notes untouched for `days` or naming a path that no longer exists, with what makes them suspect."""
    links = linked_names(root)
    found = []
    for path in sorted((root / vault.NOTES).rglob("*.md")):
        age = (today - last_touched(path, vault.properties(path))).days
        gone = missing_paths(path.read_text(encoding="utf-8", errors="replace"))
        if age < days and not gone:
            continue
        orphan = not any(path.stem in names for other, names in links.items() if other != str(path))
        found.append({"note": path.stem, "path": path.relative_to(root).as_posix(), "age_days": age,
                      "orphan": orphan, "missing_paths": gone})
    return sorted(found, key=lambda item: (not item["missing_paths"], -item["age_days"], item["note"]))


def archive(root: Path, note: Path, today: datetime.date, reason: str) -> Path:
    """Moves a note into the archive under its own name and records when and why. Links by name still resolve."""
    target = root / vault.ARCHIVE / note.name
    if target.exists():
        raise FileExistsError(target)
    added = [f"archived: {today.isoformat()}"]
    if reason.strip():
        added.append(f'archived_reason: "{vault.clean(reason).replace(chr(34), chr(39))}"')
    text = note.read_text(encoding="utf-8")
    end = text.find("\n---", 3)
    if text.startswith("---\n") and end >= 0:
        text = text[:end] + "\n" + "\n".join(added) + text[end:]
    else:
        text = "---\n" + "\n".join(added) + "\n---\n" + text
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    note.unlink()
    return target


def apply_approved(root: Path) -> set[str]:
    """Archives the target of each approved `action: archive` proposal, deletes the proposal and returns the
    paths it touched. A proposal whose target is not exactly one note in the notes folder stays for the agent."""
    touched: set[str] = set()
    inbox = root / vault.INBOX
    for proposal in sorted(inbox.glob("*.md")) if inbox.is_dir() else []:
        meta = vault.properties(proposal)
        if meta.get("approved") != ["true"] or meta.get("kind") != ["proposal"] or meta.get("action") != ["archive"]:
            continue
        matches = list((root / vault.NOTES).rglob(f"{' '.join(meta.get('target', []))}.md"))
        if len(matches) != 1:
            continue
        note = matches[0]
        try:
            moved = archive(root, note, datetime.date.today(), " ".join(meta.get("description", [])))
        except FileExistsError:
            continue
        proposal.unlink()
        touched |= {proposal.relative_to(root).as_posix(), note.relative_to(root).as_posix(),
                    moved.relative_to(root).as_posix()}
    return touched


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    scan = commands.add_parser("candidates", help="print the notes that look obsolete as JSON")
    scan.add_argument("--days", type=int, default=STALE_DAYS)
    args = parser.parse_args(argv)
    root = vault.locate()
    if root is None:
        print("No knowledge vault found.", file=sys.stderr)
        return 1
    print(json.dumps(candidates(root, datetime.date.today(), args.days), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
