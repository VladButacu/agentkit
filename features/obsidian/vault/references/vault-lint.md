# Vault lint

Keeps the vault healthy as it grows and proposes how its conventions should change.

1. Locate the vault as [`vault-setup`](vault-setup.md#locate-the-vault) describes and read its `AGENTS.md`.
2. Run every check, read-only. `30 Clippings/`, `40 Daily/` and `90 System/` are out of scope, apart from `log.md` for the inbox check. With Obsidian running, the `obsidian` commands below read its link index; without it, derive the same answer with `rg`.
   - **Missing properties**: notes in `10 Notes/` and `00 Inbox/` without `description`, `categories` or `created` (`rg --files-without-match '^description:' '<vault>/10 Notes' --glob '*.md'` and the same for the other two).
   - **Missing categories**: values in `categories` with no note in `20 Categories/`.
   - **Stale inbox**: items in `00 Inbox/` older than 14 days. List them for the user rather than deciding them.
   - **Misplaced files**: notes at the vault root other than `Home.md`, `AGENTS.md` and `CLAUDE.md`.
   - **Orphans**: `obsidian orphans`. Notes no other note links to.
   - **Unresolved links**: `obsidian unresolved format=json`. A link to a note that does not exist yet is allowed. Report it as a page candidate when three or more notes use it.
   - **Duplicates**: notes whose names or descriptions cover the same subject.
   - **Contradictions and stale claims**: read the notes in each category together and compare their claims and `updated` dates. Notes that look obsolete go to `vault-prune`, which verifies and retires them.
   - **Convention drift**: patterns the notes repeat that `AGENTS.md` does not describe, and rules in it that the notes do not follow.
   Run the duplicates, contradictions and convention-drift checks through the `blind-reviewer` subagent. Give it the vault as the artifact, those three checks as its scope, and the vault's `AGENTS.md` as its rubric, so the whole-vault read stays out of this context. When the subagent is not installed, run the checks yourself.
   Done when every check has run and each finding names its notes.
3. Report the findings grouped by fix, each with the change you propose. Changes to `AGENTS.md`, merges, deletions, renames and edits to the owner's notes are proposals: write each to `00 Inbox/` from `90 System/Templates/Proposal.md` when you will not be in the conversation to ask.
4. Apply the fixes the user approves, following the vault's `AGENTS.md`. Append a `lint` entry to `90 System/log.md` and commit as the vault's `AGENTS.md` describes, with the message `lint: <summary>`.
