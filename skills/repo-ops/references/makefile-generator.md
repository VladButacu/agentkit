# Makefile Generator

The templates in `templates/makefile-generator/` are the source of truth for every target. This skill picks a type, collects the values the template needs, and renders it with `scripts/makefile-generator/render_template.py`. Do not copy target bodies into the answer or add sections by hand: the type already carries its sections.

## Project types

| Type | Package manager | Use case | Carries |
|------|-----------------|----------|---------|
| `python-library` | UV | PyPI packages, shared libraries | docs, build, publish |
| `python-service` | UV | FastAPI services, workers | docker-build, run |
| `mcp-server` | UV + private index | Model Context Protocol servers | index auth, docker-build, run |
| `python-service-db` | UV + Alembic | Services with database migrations | revision, upgrade, downgrade, docker-build |
| `electron-frontend` | npm | Electron UI applications | dev, build per platform |
| `electron-backend` | UV + PyInstaller | Python backends for Electron apps | compile-backend, install per platform |
| `java-gradle` | Gradle | JVM projects, plugins | shadow-jar, update |

Choose the type whose row matches the project. If none fits, stop and ask the user rather than adapting a template by hand.

## Steps

1. **Check for an existing Makefile.** If the project already has one, render to a temporary path, show the user the diff, and wait for approval before replacing it.
2. **List the values.** Run `python3 scripts/makefile-generator/render_template.py list <type>`. It prints the placeholders the template needs and nothing else.
3. **Ask for each value.** Ask only for what the list printed. Use this meaning for each placeholder:

   | Placeholder | Ask for |
   |-------------|---------|
   | `SERVICE_SLUG`, `LIBRARY_NAME`, `APP_NAME`, `PLUGIN_SLUG` | The project slug. It names Docker images and build output, so use lowercase with hyphens. |
   | `VENV_PROMPT` | A short name for the shell prompt, such as `ms` for management-service. |
   | `SERVICE_PORT`, `API_PORT`, `MCP_PORT`, `METRICS_PORT` | Each port the service listens on. |

4. **Render.** Run `python3 scripts/makefile-generator/render_template.py render <type> --set KEY=VALUE ... --out <path>`, with `Makefile` or the temporary path from step 1. The script fails when a value is missing or unused, so fix the names it reports and run it again. Do not write a Makefile by hand when the script fails.
5. **Check it parses.** Run `make -n help`. This dry run reads the whole Makefile without running any target. Fix any error it reports.

## Reviewing a template change

These rules apply when someone edits a file in `templates/makefile-generator/`. Each one protects a behaviour the generated Makefiles depend on.

- `SHELL := /bin/bash` and `.DEFAULT_GOAL := help`: the `help` target and the pipelines in later targets need bash, and a bare `make` should show the targets rather than run one.
- A `##` comment on every target: the `help` target builds its list from those comments.
- Every `.PHONY` target listed: a directory or file with a target's name would otherwise stop the target from running.
- `|| { echo "..."; exit 1; }` on each command that can fail: otherwise make reports success after a failed install or test.
- The `CI`-aware venv path: when `CI=true` the venv moves to `/app/.venv`, so a fixed path would ignore the CI setting.
- `test` depends on the lockfile check and the dev install, then runs format, lint and pytest in that order: a test run against a stale lockfile would test the wrong dependencies, and a lint pass after tests would miss files the tests changed.

## Verify

Run the renderer's tests from this skill's folder with `python3 -m unittest discover -s scripts -p 'test_*.py'`. Run `make -n help` on the generated Makefile. Done when the render succeeds, the dry run parses, and no `{{` remains in the output.
