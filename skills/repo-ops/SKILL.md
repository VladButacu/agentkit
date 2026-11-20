---
name: repo-ops
description: >-
  Use only when the user names it: ship changes as a pull request, scan code health with Desloppify, bootstrap agentic repo config, or generate a Makefile or pyproject.toml from templates. Manual only.
license: See references/desloppify/LICENSE (OSNL 0.2) for the Desloppify reference
disable-model-invocation: true
---

# Repo Ops Workflow Router

You are handling a task related to repository operations. Only the user starts this skill. **Do not rely on generic defaults.**
Identify the user's specific intent from the routing table below and **read the
corresponding file(s)** before taking action.

## Routing Table

| User Intent / Trigger | Reference File to Read |
| :--- | :--- |
| Current changes are ready to go out as a pull request, from branch to green CI | `references/ship.md` |
| Codebase health scan, technical-debt assessment or systematic cleanup with Desloppify | `references/desloppify.md` |
| Set up or standardize agentic configuration in a project repository: instruction file, skills layout, local overrides | `references/repo-bootstrap.md` |
| Create or standardize a Makefile for a Python, MCP, Node.js/Electron or Java/Gradle project | `references/makefile-generator.md` |
| Create or standardize pyproject.toml for a Python library, service, MCP server or Electron backend | `references/pyproject-generator.md` |

## Rules
1. **Load selectively:** Open ONLY the file(s) that match the current request. Never bulk-read the entire `references/` directory.
2. **Compose when needed:** Read at most one workflow row. Other rows may join it.
3. **Re-route on pivot:** If the conversation shifts to another domain, trigger the appropriate domain skill rather than guessing.
