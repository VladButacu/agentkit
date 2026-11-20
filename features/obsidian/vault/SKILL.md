---
name: vault
description: >-
  Use first for questions about past decisions, earlier findings or how something was set up, and before researching from scratch. Also saves notes when asked, runs the dream, lints or prunes the vault, or creates it. Skip what the code answers.
metadata:
  opencode/autoinvoke: true
---

# Vault Workflow Router

You are handling a task related to the Obsidian knowledge vault. **Do not rely on generic defaults.**
Identify the user's specific intent from the routing table below and **read the
corresponding file(s)** before taking action.

## Routing Table

| User Intent / Trigger | Reference File to Read |
| :--- | :--- |
| A question about past decisions, earlier findings or how something was set up, before researching a topic from scratch, or the user asks what they know, noted or decided | `references/vault-recall.md` |
| The user asks to save, note or file something in the vault | `references/vault-capture.md` |
| The scheduled vault dream runs, or the user asks to consolidate or tidy the vault from recent sessions | `references/vault-dream.md` |
| The user asks to check, clean up or review the vault, or after a large batch of captures | `references/vault-lint.md` |
| The user asks to prune or retire obsolete notes, or to check whether notes are still true | `references/vault-prune.md` |
| Creating or adopting the vault, or another vault file cannot locate it | `references/vault-setup.md` |

## Rules
1. **Load selectively:** Open ONLY the file(s) that match the current request. Never bulk-read the entire `references/` directory.
2. **Compose when needed:** Read at most one workflow row. Other rows may join it.
3. **Re-route on pivot:** If the conversation shifts to another domain, trigger the appropriate domain skill rather than guessing.
