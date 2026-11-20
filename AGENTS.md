# Working on agentkit

agentkit ships skills, subagents, global rules and an installer to Claude Code, Codex, Cursor, Kiro, Kilo and OpenCode. This file is the rulebook for changing agentkit itself and is never installed. [`CONTRIBUTING.md`](CONTRIBUTING.md) owns the gate (`make test`), pull request titles, sign-off, releases and the paths the tools depend on.

## Shipped and internal

Everything a user's tools receive lives in the shipped paths. Everything else exists only to develop agentkit.

| Shipped | Internal |
| --- | --- |
| `instructions/` (`global.md` is the rulebook every tool gets, and the other files are guides it points to) | `AGENTS.md` |
| `skills/`, `agents/`, `plugins/` | `CONTRIBUTING.md`, `CHANGELOG.md`, `.github/` |
| `scripts/` (installer, hooks, update check), `install.sh`, the Makefile's `update` and `uninstall` targets | `test_*.py` beside the code they check, the Makefile's `test` target |
| `.claude-plugin/`, `.codex-plugin/`, `.cursor-plugin/`, `.agents/plugins/` | `pyrightconfig.json`, `release-please-config.json`, `.release-please-manifest.json` |

- A rule for agentkit's users goes in `instructions/global.md` or a skill. A rule for changing agentkit goes here.
- The repository root is the plugin root, so it has no `CLAUDE.md`: `claude plugin validate` warns about one there, and Claude Code reads this file natively.
- Develop in a clone or worktree other than `~/.agentkit`. That clone is the live install, and its tools import `instructions/global.md` from it.

## Skills and subagents

- Skills are domain routers in `skills/<domain>/SKILL.md`, and the vault router is in `features/obsidian/vault/`. Each router routes to plain files in its `references/`, and no `SKILL.md` lives there. A router's description stays under 300 characters and lists the same files as `references/`. Scripts and templates sit under `<router>/scripts/<leaf>/` and `<router>/templates/<leaf>/`. `scripts/test_metadata.py` checks all of it. [`instructions/skill-composition.md`](instructions/skill-composition.md) settles overlaps and lists which skills dispatch which subagent.
- A router whose only trigger is a person typing its name sets `disable-model-invocation: true`, and its `agents/openai.yaml` sets `allow_implicit_invocation: false` for Codex. Model-invoked routers have no `openai.yaml`. A manual-only leaf goes in `repo-ops`, and a model-invoked leaf never does.
- Subagents live in `agents/<name>.md`, in Claude Code's dialect, with `readonly: true` for Cursor and no `model`, so each runs on the dispatching session's model. Claude Code and Cursor load them from the native plugin. `scripts/subagents.py` renders a copy for every other tool, and for Claude Code and Cursor when they get linked skills. `scripts/test_metadata.py` checks the frontmatter.
- Add a subagent only for independent judgement, verbose output the caller does not need, a hard tool restriction or real parallel work. A skill that dispatches one says what to do when it is not installed.
