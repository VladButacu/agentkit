# Repo bootstrap

Bring a project repository to the house layout for agent-facing configuration. The layout is project-agnostic: it says where things live, never what the project's rules are.

## Inspect first

Read what already exists: instruction files, skills directories, hooks, CI. Preserve all of it; this skill fills gaps and standardizes placement, it does not rewrite project rules. Obtain the user's confirmation for anything you would delete or move.

## Layout

1. `AGENTS.md` at the root is the single rulebook. Keep in it only what is specific to this project; the agent's global instructions already carry the house writing, verification and process rules. Useful sections: what this project is, its non-negotiables, how it is built and verified (its gate, its commands), a skills table, and where things live.
2. `CLAUDE.md` contains a single pointer line, `@AGENTS.md`, so Claude Code reads the same rulebook. Other tools read `AGENTS.md` natively.
3. `.agents/skills/<name>/SKILL.md` is the only place skills are written. Codex and OpenCode read it directly. Other tools read their own directory, such as `.claude/skills` for Claude Code and `.kiro/skills` for Kiro, and each one the project uses gets a local link to `.agents/skills`. Pass each directory with `--link`, as described under Run. `scripts/repo-bootstrap/bootstrap.py apply` creates the links, a relative symlink on macOS and Linux and a directory junction on Windows, and lists them in `.gitignore`. Never commit these links, because Git for Windows checks committed symlinks out as plain text files unless symlink support is turned on. Never copy a skill into a tool-specific directory.
4. `AGENTS.local.md` holds per-machine overrides. Add it to `.gitignore` and mention it in `AGENTS.md`. If the repository keeps local secrets or env files that agent worktrees need (for example `.env.local`), add a `.worktreeinclude` naming them so new worktrees stay runnable.
5. Skills wrap the repository's own commands, typically `make` targets; they teach when to run what, and the targets stay the source of truth for how.
6. Enforcement hooks the repository already has (pre-commit gates, version syncing) stay exactly as they are. This layout prescribes no hook; a repository that wants a new one adds it to its own hooks directory as a project decision.

## Run

From this skill's folder, run `python3 scripts/repo-bootstrap/bootstrap.py check --root <project>`. It lists every gap and exits 1 while any remain. Run `apply` with the same arguments to make the parts that need no decision about project content, such as the `CLAUDE.md` pointer, the shared folder, the links and `.gitignore` entries. It never overwrites an existing file, so anything it reports as "must contain only" or "remove it by hand" stays with you. Write `AGENTS.md` yourself, then run `check` until it prints `layout OK`. With no `--link`, the check asks for no tool directory. Claude Code users pass `--link .claude/skills`, and every other tool the project uses gets its own `--link`, for example `--link .kiro/skills`.

## Verify

Run the project's verification gate. Confirm from a fresh session that an agent sees the skills table and the `AGENTS.md` rules.
