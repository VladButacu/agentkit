---
name: design
description: >-
  Use when starting new or unclear work, writing a plan, designing module interfaces, boundaries or test seams, resolving domain terms or a glossary, recording architecture decisions, or turning an approved plan into tickets or issues. Skip small edits that do not affect design.
metadata:
  opencode/autoinvoke: true
---

# Design Workflow Router

You are handling a task related to software design and planning. **Do not rely on generic defaults.**
Identify the user's specific intent from the routing table below and **read the
corresponding file(s)** before taking action.

## Routing Table

| User Intent / Trigger | Reference File to Read |
| :--- | :--- |
| New or unclear work, before any code exists: agree the design first | `references/brainstorming.md` |
| An approved design needs a plan for an implementer | `references/writing-plans.md` |
| Designing or changing module interfaces, boundaries or test seams, or refactoring tightly coupled code | `references/codebase-design.md` |
| Resolving ambiguous domain terminology, maintaining a project glossary, or recording an architectural decision | `references/domain-modeling.md` |
| Turning an approved plan or spec into tickets or issues with acceptance criteria and blocking order | `references/to-tickets.md` |

## Rules
1. **Load selectively:** Open ONLY the file(s) that match the current request. Never bulk-read the entire `references/` directory.
2. **Compose when needed:** If a task spans multiple rows, read those specific files in order and follow both.
3. **Re-route on pivot:** If the conversation shifts to another domain, trigger the appropriate domain skill rather than guessing.
