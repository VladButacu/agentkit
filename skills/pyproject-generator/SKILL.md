---
name: pyproject-generator
description: Use when creating or standardizing pyproject.toml for a Python library, service, MCP server or Electron backend. Skip projects whose pyproject.toml already follows a template and that do not ask for changes.
allowed-tools: Read, Write, Glob, AskUserQuestion, Bash
disable-model-invocation: true
---

# pyproject.toml Generator

The templates in `templates/` are the source of truth for the build system, lint, test and coverage configuration. This skill picks a type, collects the values the template needs, and renders it with `scripts/render_template.py`. Do not copy configuration into the answer or add sections by hand: the type already carries them.

## Project types

| Type | Build system | Use case | Carries |
|------|--------------|----------|---------|
| `python-library` | hatchling | PyPI packages, shared libraries | hatch version and sdist, mypy |
| `python-service` | setuptools | FastAPI services, workers | package discovery |
| `mcp-server` | setuptools | Model Context Protocol servers | private index, API and metrics ports |
| `python-service-db` | setuptools | Services with database (Alembic) | private index |
| `electron-backend` | hatchling | Python backends for Electron apps | macOS and Windows dependency groups, pyright |

Choose the type whose row matches the project. If none fits, stop and ask the user rather than adapting a template by hand.

## Steps

1. **Check for an existing pyproject.toml.** If the project already has one, render to a temporary path, show the user the diff, and wait for approval before replacing it.
2. **List the values.** Run `python3 scripts/render_template.py list <type>`. It prints the placeholders the template needs and nothing else.
3. **Ask for each value.** Ask only for what the list printed. Use this meaning for each placeholder:

   | Placeholder | Ask for |
   |-------------|---------|
   | `PROJECT_NAME` | The distribution name, such as `my-service`. |
   | `PACKAGE_NAME` | The import name, lowercase with underscores, such as `my_service`. |
   | `VERSION` | The starting version, such as `0.1.0`. |
   | `DESCRIPTION` | One line describing the project. |
   | `MAINTAINER_NAME`, `MAINTAINER_EMAIL`, `HOMEPAGE_URL` | The maintainer and project link. |
   | `PYTHON_VERSION` | The version the library supports, such as `3.12`. Used by `python-library` only. |
   | `PYTHON_CONSTRAINT` | The version range, such as `~=3.12.10` or `>=3.12,<3.13`. |
   | `PRIVATE_INDEX_NAME`, `PRIVATE_INDEX_URL`, `PRIVATE_PACKAGE` | The private registry and the package it serves. Used by `mcp-server` and `python-service-db`. |
   | `API_PORT`, `MCP_PORT`, `METRICS_PORT` | The ports the server listens on. Used by `mcp-server`. |

   The coverage threshold is not a value. Each template sets `fail_under` for its type (see below).
4. **Render.** Run `python3 scripts/render_template.py render <type> --set KEY=VALUE ... --out <path>`, with `pyproject.toml` or the temporary path from step 1. The script fails when a value is missing or unused, so fix the names it reports and run it again. Do not write the file by hand when the script fails.
5. **Check it parses.** Run `uv lock --check` in a project directory that has a `uv.lock`, or `python3 -c "import tomllib, pathlib; tomllib.loads(pathlib.Path('pyproject.toml').read_text())"` otherwise. Fix any error it reports.

## Coverage thresholds

| Project type | Default `fail_under` |
|--------------|----------------------|
| `python-library` | 60% |
| `mcp-server` | 75% |
| `python-service` and `python-service-db` | 90% |
| `electron-backend` | 65% |

These are starting points that every project of a type shares, so the numbers mean the same across the team. Keep them unless the project has a recorded reason to differ, and record that reason in the project's own docs.

## Reviewing a template change

These rules apply when someone edits a file in `templates/`. Each one protects a behaviour the generated projects depend on.

- The build backend matches the type: services use setuptools because their package is discovered from `app/`, and libraries use hatchling because it builds the wheel and sdist from the version file.
- Runtime and dev dependencies sit in separate groups: installing production dependencies with `--no-dev` must not pull in test tooling.
- The pytest `asyncio_mode` is `strict`: async tests then need an explicit marker, so a test is never silently skipped or run in the wrong loop.
- The ruff ignore list is short and each entry is an intentional team choice: a broad ignore hides the rule for every file in the project.

## Verify

Run the renderer's tests from this skill's folder with `python3 -m unittest discover -s scripts -p 'test_*.py'`. Run the parse check on the generated file. Done when the render succeeds, the file parses, and no `{{` remains in the output.
