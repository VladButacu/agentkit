---
name: vault-capture
description: Use when durable knowledge comes up (a decision, finding, gotcha or research result), or the user asks to save, note or file something or a source in the knowledge vault. Skip transient task state and anything a repository's own docs should hold.
disable-model-invocation: false
metadata:
  opencode/autoinvoke: true
---

# Vault capture

Files knowledge into the Obsidian vault so it compounds: each capture updates the notes that already cover the subject and links new notes into them. Corrections to how agents should behave belong in `AGENTS.md` or the tool's memory, not here.

1. Locate the vault as [`vault-setup`](../vault-setup/SKILL.md#locate-the-vault) describes and read its `AGENTS.md`. It owns the note format and the write rules, and wins where it differs from this skill.
2. Put the knowledge into words.
   - A finding from the session: state it in one to three sentences with its evidence, and check it with the user when it is their judgement rather than a fact you verified.
   - A source to keep: save it to `30 Clippings/<Title>.md` from `90 System/Templates/Clipping.md`. For a URL, `defuddle parse <url> --md` gives clean Markdown; otherwise use the web fetch tool.
3. Find where it belongs. Search the descriptions (`rg -n -i '^description:.*<term>' <vault>`) and then the full text (`rg -l -i '<term>' <vault> --glob '*.md'`) for each key term, and read the matching notes. Done when you know every note to update and every note to create.
4. Write it.
   - Update the notes that already cover the subject, within the rules in the vault's `AGENTS.md`, and bump their `updated`.
   - Create a note only for a subject no note covers, from `90 System/Templates/Note.md`, with `created_by` set to your tool's name. It goes in `10 Notes/` when the user asked for this capture, and in `00 Inbox/` with `approved: false` when you are filing it on your own.
   - Check each claim about a path, repository or command before filing it. One that no longer holds becomes history, with what replaced it, or is left out.
   - A change the write rules reserve for the user (a merge, deletion, rename or edit to their note) becomes a proposal in `00 Inbox/` from `90 System/Templates/Proposal.md`.
   - Link first mentions both ways: the new note to related notes, and related notes back to it.
   - Create the category note in `20 Categories/` from `90 System/Templates/Category.md` when you introduce a category.
   - For Obsidian syntax (callouts, embeds, properties), use the `obsidian-markdown` skill when it is installed.
5. Append the entry to `90 System/log.md`, commit only the files you wrote, and push when a remote exists.
6. Report the notes created and updated as absolute paths, and say which wait in `00 Inbox/` for the user.

Done when each new fact sits in exactly one note, and every note you created has a description, a category and a link to or from an existing note.
