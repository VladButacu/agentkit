---
name: repo-bootstrap
description: Use when setting up or standardizing agentic development configuration in a project repository, covering the instruction file, skills layout and local overrides. Skip repositories that already follow the layout unless asked to audit them.
disable-model-invocation: false
metadata:
  opencode/autoinvoke: true
---

# Repo bootstrap

Bring a project repository to the house layout for agent-facing configuration. The layout is project-agnostic: it says where things live, never what the project's rules are.

## Inspect first

Read what already exists: instruction files, skills directories, hooks, CI. Preserve all of it; this skill fills gaps and standardizes placement, it does not rewrite project rules. Obtain the user's confirmation for anything you would delete or move.

## Layout

1. `AGENTS.md` at the root is the single rulebook. Keep in it only what is specific to this project; the agent's global instructions already carry the house writing, verification and process rules. Useful sections: what this project is, its non-negotiables, how it is built and verified (its gate, its commands), a skills table, and where things live.
2. `CLAUDE.md` contains a single pointer line, `@AGENTS.md`, so Claude Code reads the same rulebook. Other tools read `AGENTS.md` natively.
3. `.agents/skills/<name>/SKILL.md` is the only place skills are written. Codex and OpenCode read it directly. Other tools read their own directory, such as `.claude/skills` for Claude Code and `.kiro/skills` for Kiro, and each one the project uses gets a local link to `.agents/skills`. The repository's setup command creates these links, and `.gitignore` lists them. Use a relative symlink on macOS and Linux (`ln -sfn ../.agents/skills .claude/skills`) and a directory junction on Windows (`cmd /c mklink /J .claude\skills .agents\skills`), which needs no admin rights. Never commit these links, because Git for Windows checks committed symlinks out as plain text files unless symlink support is turned on. Never copy a skill into a tool-specific directory.
4. `AGENTS.local.md` holds per-machine overrides. Add it to `.gitignore` and mention it in `AGENTS.md`. If the repository keeps local secrets or env files that agent worktrees need (for example `.env.local`), add a `.worktreeinclude` naming them so new worktrees stay runnable.
5. Skills wrap the repository's own commands, typically `make` targets; they teach when to run what, and the targets stay the source of truth for how.
6. Enforcement hooks the repository already has (pre-commit gates, version syncing) stay exactly as they are. This layout prescribes no hook; a repository that wants a new one adds it to its own hooks directory as a project decision.

## Verify

Run the project's verification gate. Confirm from a fresh session that an agent sees the skills table and the `AGENTS.md` rules.
