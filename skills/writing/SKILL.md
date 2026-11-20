---
name: writing
description: >-
  Use when drafting or revising prose a person reads (docs, website copy, blog posts, emails, applications), writing AGENTS.md, CLAUDE.md or other agent-facing docs, or turning a changelog into release notes. Skip code comments and commit messages.
metadata:
  opencode/autoinvoke: true
---

# Writing Workflow Router

You are handling a task related to writing. **Do not rely on generic defaults.**
Identify the user's specific intent from the routing table below and **read the
corresponding file(s)** before taking action.

## Routing Table

| User Intent / Trigger | Reference File to Read |
| :--- | :--- |
| Drafting or revising any prose a person will read: documentation, website copy, blog posts, articles, case studies, emails, letters, applications | `references/prose.md` |
| Turning a changelog entry into user-facing release notes or a release post | `references/release-notes.md` |
| Writing or improving AGENTS.md, CLAUDE.md or agent-facing reference documents, or choosing how a skill is invoked | `references/writing-for-agents.md` |

## Rules
1. **Load selectively:** Open ONLY the file(s) that match the current request. Never bulk-read the entire `references/` directory.
2. **Compose when needed:** If a task spans multiple rows, read those specific files in order and follow both.
3. **Re-route on pivot:** If the conversation shifts to another domain, trigger the appropriate domain skill rather than guessing.
