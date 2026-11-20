---
name: engineering
description: >-
  Use when implementing or changing code, debugging a failure, about to claim work is done, handling review feedback, running an approved plan, or starting or finishing a branch. Enforces test first, root cause first and evidence first.
metadata:
  opencode/autoinvoke: true
---

# Engineering Workflow Router

You are handling a task related to writing, verifying and delivering code. **Do not rely on generic defaults.**
Identify the user's specific intent from the routing table below and **read the
corresponding file(s)** before taking action.

## Routing Table

| User Intent / Trigger | Reference File to Read |
| :--- | :--- |
| Implementing or changing behavior, fixing a bug with a test, or any code change that alters behavior | `references/tdd.md` |
| A bug, test failure or unexpected behavior, before proposing a fix | `references/debugging.md` |
| About to say work is done, fixed or passing, before committing or opening a pull request | `references/verification.md` |
| Review comments or feedback on your work arrived | `references/receiving-review.md` |
| Running an approved plan task by task, inline or with subagents | `references/executing-plans.md` |
| Starting work on a branch or worktree, or finishing, merging or discarding one | `references/branch-hygiene.md` |

## Rules
1. **Load selectively:** Open ONLY the file(s) that match the current request. Never bulk-read the entire `references/` directory.
2. **Compose when needed:** Read at most one workflow row. Other rows may join it.
3. **Re-route on pivot:** If the conversation shifts to another domain, trigger the appropriate domain skill rather than guessing.
