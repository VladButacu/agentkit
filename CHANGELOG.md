# Changelog

## [0.2.0](https://github.com/VladButacu/agentkit/compare/v0.1.0...v0.2.0) (2026-11-10)


### Features

* support Windows and ask before changing instruction files ([4b7064a](https://github.com/VladButacu/agentkit/commit/4b7064a7e3ed3c5f7667ea2806e5f024c7b8064e))
* support Windows and ask before changing instruction files ([137da52](https://github.com/VladButacu/agentkit/commit/137da520680ceee39c533841631b2e70ed53e385))
* support Windows and ask before changing instruction files ([8374f1e](https://github.com/VladButacu/agentkit/commit/8374f1e6eb932a86d8068520f5a16baf2156a5d8))


### Bug Fixes

* tag releases as vX.Y.Z so release-please finds v0.1.0 ([4b7064a](https://github.com/VladButacu/agentkit/commit/4b7064a7e3ed3c5f7667ea2806e5f024c7b8064e))

## 0.1.0

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
