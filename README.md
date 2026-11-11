# agentkit

[![CI](https://github.com/VladButacu/agentkit/actions/workflows/ci.yml/badge.svg)](https://github.com/VladButacu/agentkit/actions/workflows/ci.yml)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/VladButacu/agentkit/badge)](https://scorecard.dev/viewer/?uri=github.com/VladButacu/agentkit)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**agentkit** gives every coding agent on your machine the same instructions, skills and plugins.

The goal is a unified surface for all your coding tools. You edit a rule or a skill once in this repository, and each installed tool receives it in the form it already reads. Tools that are not installed get nothing.

## Supported tools

| Tool | Skills | Native plugins | Plugin paths | Instruction file | Update hook | Custom agent |
| --- | :---: | :---: | :---: | :---: | :---: | :---: |
| <picture><source media="(prefers-color-scheme: dark)" srcset="assets/logos/codex-dark.svg"><img src="assets/logos/codex.svg" width="24" height="24" alt=""></picture> **Codex** | ✅ | ✅ | | ✅ | | |
| <img src="assets/logos/claude-code.svg" width="24" height="24" alt=""> **Claude Code** | ✅ | ✅ | | ✅ | ✅ | |
| <img src="assets/logos/opencode.svg" width="24" height="24" alt=""> **OpenCode** | ✅ | | ✅ | | | |
| <img src="assets/logos/cursor.svg" width="24" height="24" alt=""> **Cursor** | ✅ | | | | | |
| <img src="assets/logos/kilo-code.svg" width="24" height="24" alt=""> **Kilo Code** | ✅ | | | | | |
| <img src="assets/logos/kiro.svg" width="24" height="24" alt=""> **Kiro IDE** | ✅ | | | | | |
| <img src="assets/logos/kiro.svg" width="24" height="24" alt=""> **Kiro CLI** | ✅ | | | | | ✅ |
| <img src="assets/logos/kiro-crew.svg" width="24" height="24" alt=""> **Kiro Crew** | ✅ | | | | | |

## Install

Requires git and Python 3.11 or later, on macOS, Linux or Windows.

Ask your coding agent to do it:

```text
Install agentkit from github.com/VladButacu/agentkit and follow its README.
```

Or run it yourself. On macOS and Linux:

```sh
git clone https://github.com/VladButacu/agentkit ~/.agentkit
sh ~/.agentkit/install.sh
```

On Windows, in PowerShell:

```powershell
git clone https://github.com/VladButacu/agentkit $HOME\.agentkit
py $HOME\.agentkit\scripts\install.py
```

The installer asks up to three questions and remembers the answers. When an agent runs it, the installer stops with the question, and the agent reruns it with the matching flag.

| Question | Flag |
| --- | --- |
| Which optional plugins to install, including the Obsidian knowledge vault. A plugin added in an update is asked about once | `--plugins superpowers,ponytail`, `all` or `none` |
| With the Obsidian plugin: which agent CLI and model run the nightly vault dream, and when | `--dream codex --dream-model <id> --dream-time 03:00`, `--dream-command '<command>'` or `--dream none` |
| What to do with an `AGENTS.md` or `CLAUDE.md` you already wrote | `--instructions keep`, `append` or `replace` (yours is backed up first) |

Any clone location works. To limit the install to some tools, pass `--tools codex,claude`. If you move the clone, run the installer again.

### Plugin only

Claude Code, Codex and Cursor can load agentkit as a plugin instead. This carries the skills only, without the instruction files, the third-party plugins or the other tools. Uninstall the plugin before switching to the full setup, since both deliver the same skills.

```sh
# Claude Code
claude plugin marketplace add VladButacu/agentkit
claude plugin install agentkit@agentkit

# Cursor: clone into the local plugin folder, then run Developer: Reload Window
git clone https://github.com/VladButacu/agentkit ~/.cursor/plugins/local/agentkit
```

## What the installer changes

| What | Where |
| --- | --- |
| Skills | Linked into each installed tool's skills folder: `~/.agents/skills` for Codex, Cursor, Kilo Code and OpenCode, `~/.claude/skills`, `~/.kiro/skills`, and Kiro Crew's `extra_paths` |
| Instructions | A marked `agentkit:begin` block in `~/.claude/CLAUDE.md` that imports this repository's `AGENTS.md`, and a copy in `~/.codex/AGENTS.md` |
| Plugins | Native plugins in Codex and Claude Code, linked skills elsewhere, checkouts in `~/.local/share/agentkit/plugins/` |
| Desloppify CLI | An isolated venv, only when `desloppify` is not already installed |
| Update hook | A Claude Code `SessionStart` hook that checks once a day whether the clone is behind upstream |
| Python launcher | `~/.local/share/agentkit/bin/python`, which every hook and schedule below starts. It picks the first Python 3.11 or later each time, so upgrading Python breaks nothing |
| Vault hooks | With the Obsidian plugin: lifecycle hooks in Claude Code, Codex, Cursor, Kiro CLI and Kiro Crew, and the nightly dream in launchd, a systemd user timer or Task Scheduler |
| Claude settings | Removes `skillOverrides` entries that hide agentkit skills |

Links are symlinks on macOS and Linux and directory junctions on Windows, so neither needs admin rights. Where no link can be made, the skill is copied and refreshed on every run.

The installer only replaces files and links it created. It backs up every file it rewrites to `~/.local/state/agentkit/backups/` and prints a `PENDING` line for anything that needs you.

The update hook means code you pull into the clone runs in your Claude sessions. Delete its entry in `~/.claude/settings.json` to turn it off.

## Skills

Each skill lives in `skills/<name>/SKILL.md` and has one job. Agents load a skill when its description matches the task.

| Skill | What it does |
| --- | --- |
| `codebase-design` | Shapes module interfaces, boundaries and test seams, and untangles tightly coupled code |
| `desloppify` | Runs Desloppify health scans and works through the cleanup queue |
| `domain-modeling` | Settles ambiguous domain terms, keeps a project glossary and records architecture decisions |
| `grill-me` | Questions a plan or design until its assumptions and trade-offs are settled |
| `makefile-generator` | Creates or standardizes a Makefile for Python, MCP, Node.js/Electron or Java/Gradle projects |
| `prose` | Drafts or revises anything a person reads, with an evidence pass and a voice pass |
| `pyproject-generator` | Creates or standardizes `pyproject.toml` for Python libraries, services, MCP servers or Electron backends |
| `release-notes` | Turns a changelog entry into user-facing release notes |
| `repo-bootstrap` | Sets up a project repository with `AGENTS.md` as the rulebook, a one-line `CLAUDE.md`, skills in `.agents/skills/` and a gitignored `AGENTS.local.md` |
| `research` | Investigates a question across primary sources, delegating where it helps |
| `retro` | Reviews a coding session for recurring mistakes and friction, and proposes fixes to the setup |
| `to-spec` | Writes an implementation specification from decisions already made |
| `to-tickets` | Publishes an approved plan as tracker issues or local tickets with acceptance criteria and dependencies |
| `writing-for-agents` | Improves `AGENTS.md`, `CLAUDE.md` and other agent-facing documents |

## Plugins

The optional plugins are listed in `plugins/manifest.json`:

| Plugin | Role | Install |
| --- | --- | --- |
| Superpowers | planning, TDD, debugging, review, branch delivery | native plugin in Codex and Claude Code, skills elsewhere |
| Ponytail | smallest complete implementation, YAGNI | native plugin in Codex and Claude Code, skills elsewhere |
| FEX | frontend design and quality orchestration | native plugin in Codex and Claude Code only |
| Obsidian | a knowledge vault you and your agents share; see below | native plugin in Codex and Claude Code, skills elsewhere, plus agentkit's vault skills |
| Desloppify | the CLI behind the `desloppify` skill | installed when no `desloppify` executable exists |

Plugins are not pinned. Each install fetches their current upstream version, so trust the authors accordingly. Native plugins in Codex and Claude Code update through their own marketplace. `plugins/manifest.schema.json` describes the fields for adding a plugin.

### Obsidian knowledge vault

Choosing `obsidian` installs [kepano's Obsidian skills](https://github.com/kepano/obsidian-skills) for Obsidian Markdown, Bases, Canvas, the Obsidian CLI and Defuddle, together with five agentkit skills from `plugins/obsidian/`:

| Skill | What it does |
| --- | --- |
| `vault-setup` | Creates or adopts the vault: layout, conventions file, templates, git and the path in `AGENTS.local.md` |
| `vault-capture` | Files decisions, findings and sources into the vault and links them into existing notes |
| `vault-recall` | Answers from the vault with citations before an agent researches from scratch |
| `vault-lint` | Checks the vault for orphans, missing properties, duplicates and stale claims, and proposes convention changes |
| `vault-dream` | Files what recent sessions learned that nobody captured, corrects drifted notes and keeps the index small |

The vault is a plain folder of Markdown in its own git repository, `~/knowledge` unless `AGENTS.local.md` names another path. It opens on `Home.md`:

| Area | What it is for you |
| --- | --- |
| `Home.md` | Your start page, bookmarked in Obsidian. **Needs you** lists what agents filed on their own: tick `approved` to accept an item, or delete it to reject it. Below it are recent notes, categories and the current focus. The optional community plugin Homepage opens it at every launch |
| `00 Inbox/` | Notes and proposed merges, deletions or edits that wait for your approval |
| `10 Notes/` | The knowledge itself |
| `20 Categories/` | One hub per category, listing its notes |
| `30 Clippings/`, `40 Daily/` | Your sources and daily notes, which agents leave alone |
| `90 System/` | Templates, views, attachments and the agents' log |
 Agents work on the files directly and use the Obsidian CLI for backlinks and link-safe renames while Obsidian is running. The vault's own `AGENTS.md` holds its conventions, and you and your agents grow it together.

Agents use the vault without being reminded:

| When | What happens | Tools |
| --- | --- | --- |
| A session starts | The session learns where the vault is, what it is for, the index in `Home.md` and the latest `log.md` entries | Claude Code, Codex, Cursor, Kiro CLI, Kiro Crew |
| You send a prompt | Notes whose names or descriptions match the prompt are pointed out, found by a local keyword search with no model call | Claude Code, Codex, Kiro CLI, Kiro Crew |
| The agent stops after real work | It is asked once to file anything worth keeping, at most every 30 minutes | Claude Code, Codex, Cursor |
| Every night | The dream reads a digest of the day's Claude Code, Codex and Kiro sessions, applies what you approved, files what the sessions missed into `00 Inbox/`, tidies the vault and commits | Whichever agent CLI you chose |

The dream runs with the agent CLI and model you pick: `claude`, `codex`, `opencode`, `kilo`, `kiro-cli` or `cursor-agent`, or any other headless agent through `--dream-command`, which receives the prompt as its last argument or in place of `{prompt}`. Your operating system's scheduler starts it and it uses that model's credits on each run. Its log is in `~/.local/state/agentkit/vault/dream.log`. Codex asks you to trust new hooks once, in `/hooks`. OpenCode and Kilo Code get the skills but no hooks.

## Update and uninstall

```sh
make -C ~/.agentkit update      # pull and reinstall with your saved answers
make -C ~/.agentkit uninstall   # remove everything the installer created
```

On Windows, update with `git -C $HOME\.agentkit pull --ff-only` followed by the install command, and uninstall with `py $HOME\.agentkit\scripts\install.py --uninstall`.

Uninstalling leaves your own files and text in place. An instruction file you chose to replace is removed rather than restored, and your original is in the backups folder. Plugin-only installs are removed by their tool, for example `claude plugin uninstall agentkit`.

## Machine-specific notes

Put notes for one machine, such as cluster names or budgets, in `~/.config/agentkit/AGENTS.local.md`. Agents read it when it is there. The installer moves an `AGENTS.local.md` it finds in the clone to that path.

## Contributing

`make test` runs ruff, the installer tests, the vault plugin tests and the prose linter tests, and CI runs it on Ubuntu and Windows. [`CONTRIBUTING.md`](CONTRIBUTING.md) covers pull request titles, the required commit sign-off and how releases are cut.

## License

MIT. Skills adapted from third-party work keep their notices in `THIRD-PARTY-NOTICES.md` and their own `LICENSE` files.
