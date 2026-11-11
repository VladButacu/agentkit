---
name: vault-lint
description: Use when the user asks to check, clean up or review the Obsidian knowledge vault, or after a large batch of captures.
disable-model-invocation: false
metadata:
  opencode/autoinvoke: true
---

# Vault lint

Keeps the vault healthy as it grows and proposes how its conventions should change.

1. Locate the vault as [`vault-setup`](../vault-setup/SKILL.md#locate-the-vault) describes and read its `AGENTS.md`.
2. Run every check, read-only. `Templates/`, `Daily/`, `Attachments/` and `log.md` are out of scope. With Obsidian running, the `obsidian` commands below read its link index; without it, derive the same answer with `rg`.
   - **Missing properties**: notes outside `Clippings/` and `Categories/` without `description`, `categories` or `created` (`rg --files-without-match '^description:' <vault> --glob '*.md'` and the same for the other two).
   - **Missing categories**: values in `categories` with no note in `Categories/`.
   - **Orphans**: `obsidian orphans`. Notes no other note links to.
   - **Unresolved links**: `obsidian unresolved format=json`. A link to a note that does not exist yet is allowed. Report it as a page candidate when three or more notes use it.
   - **Duplicates**: notes whose names or descriptions cover the same subject.
   - **Contradictions and stale claims**: read the notes in each category together and compare their claims and `updated` dates.
   - **Convention drift**: patterns the notes repeat that `AGENTS.md` does not describe, and rules in it that the notes do not follow.
   Done when every check has run and each finding names its notes.
3. Report the findings grouped by fix, each with the change you propose. Changes to `AGENTS.md`, merges, deletions, renames and edits to the owner's notes are proposals for the user to decide.
4. Apply the fixes the user approves, following the vault's `AGENTS.md`. Append a `lint` entry to `log.md`, commit only the files you changed as `lint: <summary>`, and push when a remote exists.
