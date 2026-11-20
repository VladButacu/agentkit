---
name: inquiry
description: >-
  Use for substantial investigation across primary sources (check the vault first), comparing options, or the history or trend of something, and for reviewing a coding session that went wrong or an agent that repeats a mistake. Skip simple documentation lookups.
metadata:
  opencode/autoinvoke: true
---

# Inquiry Workflow Router

You are handling a task related to investigation or session review. **Do not rely on generic defaults.**
Identify the user's specific intent from the routing table below and **read the
corresponding file(s)** before taking action.

## Routing Table

| User Intent / Trigger | Reference File to Read |
| :--- | :--- |
| Look into X, compare A and B, what is the state of X, what changed in X, or a question that needs several primary sources | `references/research.md` |
| Review a past or current coding session, the agent repeats a mistake, burns context, ignores its rules or loops | `references/retro.md` |

## Rules
1. **Load selectively:** Open ONLY the file(s) that match the current request. Never bulk-read the entire `references/` directory.
2. **Compose when needed:** Read at most one workflow row. Other rows may join it.
3. **Re-route on pivot:** If the conversation shifts to another domain, trigger the appropriate domain skill rather than guessing.
