# Changelog

## 1.0.0

Initial public release.

- One installer wiring skills, third-party plugins and update notices into
  Codex, Claude Code, OpenCode, Cursor, Kilo Code, Kiro IDE, Kiro CLI and
  Kiro Crew, with an uninstall that removes all of it.
- Plugin selection at install time (`--plugins`), remembered per machine.
- Baseline skills: `prose`, `codebase-design`, `domain-modeling`, `grill-me`,
  `makefile-generator`, `pyproject-generator`, `release-notes`, `research`,
  `repo-bootstrap`, `retro`, `to-spec`, `to-tickets`, `writing-for-agents`,
  plus the Desloppify skill and CLI.
- Third-party plugin manifest with a JSON schema, tracking upstream HEAD.
- Claude Code session hook printing an update notice when the clone is behind.
- The repository is also installable as a Claude Code and Codex plugin for
  skills-only setups.
