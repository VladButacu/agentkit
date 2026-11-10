---
name: pyproject-generator
description: Use when creating or standardizing pyproject.toml for a Python library, service, MCP server or Electron backend.
allowed-tools: Read, Write, Glob, AskUserQuestion
user-invocable: true
---

# pyproject.toml Generator

Generates standardized pyproject.toml files for the supported project types.

## Usage

Invoke this skill when:
- Creating a new Python project
- Initializing a new service/module
- Standardizing an existing pyproject.toml

## Project Types Supported

| Type | Build System | Use Case |
|------|--------------|----------|
| `python-library` | hatchling | PyPI packages, shared libraries |
| `python-service` | setuptools | FastAPI services, workers |
| `mcp-server` | setuptools | Model Context Protocol servers |
| `python-service-db` | setuptools | Services with database (Alembic) |
| `electron-backend` | hatchling | Python backends for Electron apps |

## Generation Process

### Step 1: Gather Requirements

Ask the user for:
1. **Project type** (from table above)
2. **Project name** (e.g., `my-service`)
3. **Version** (e.g., `0.1.0`)
4. **Description** (one-line summary)
5. **Python version constraint** (e.g., `~=3.12.10`, `==3.12.*`, `>=3.12,<3.13`)
6. **Private PyPI** (GitLab registry or public PyPI only)
7. **Core dependencies** (FastAPI, database, MCP, etc.)
8. **Coverage threshold** (default varies by type)

### Step 2: Generate from Template

Use the appropriate template from `templates/` and customize:
- Replace `{{PROJECT_NAME}}` with project name
- Replace `{{MAINTAINER_NAME}}` and `{{MAINTAINER_EMAIL}}` with the maintainer
- Replace `{{VERSION}}` with version
- Replace `{{DESCRIPTION}}` with description
- Adjust Python version constraint
- Include/exclude optional sections based on requirements

## Universal Patterns (All Templates)

### Project Metadata
```toml
[project]
name = "{{PROJECT_NAME}}"
version = "{{VERSION}}"
description = "{{DESCRIPTION}}"
authors = [{ name = "{{MAINTAINER_NAME}}", email = "{{MAINTAINER_EMAIL}}" }]
readme = "README.md"
requires-python = "{{PYTHON_CONSTRAINT}}"
classifiers = [
    "Programming Language :: Python :: 3.12",
    "Framework :: FastAPI",
    "Operating System :: OS Independent",
]
```

### Ruff Configuration
```toml
[tool.ruff]
line-length = 88
target-version = "py312"

[tool.ruff.lint]
select = ["ALL"]
ignore = [
    "D100", "D101", "D102", "D103", "D104",  # Docstrings
    "D203", "D205", "D213",                   # Docstring style
    "D400", "D401", "D415",                   # Docstring format
    "TD002", "TD003", "FIX002",               # TODOs
    "S104",                                   # Hardcoded bind
    "E501",                                   # Line too long
    "COM812",                                 # Trailing comma
    "ERA001",                                 # Commented code
    "ANN001", "ANN201", "ANN401",             # Type annotations
    "INP001",                                 # Implicit namespace
    "EM101", "EM102",                         # Exception messages
    "TRY003",                                 # Long exception
    "G004",                                   # Logging f-string
    "PLR0913",                                # Too many arguments
]

[tool.ruff.lint.per-file-ignores]
"tests/**/*.py" = ["S101", "S105", "S106", "SLF001", "PLR2004", "PLC0415"]
"scripts/**/*.py" = ["ALL"]

[tool.ruff.lint.flake8-bugbear]
extend-immutable-calls = ["AsyncMock", "MagicMock"]

[tool.ruff.format]
preview = true
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
line-ending = "auto"
```

### Pytest Configuration
```toml
[tool.pytest.ini_options]
pythonpath = [".", "app"]
asyncio_mode = "strict"
asyncio_default_fixture_loop_scope = "function"
testpaths = ["tests"]
addopts = "--cov-report=xml:coverage.xml --cov-report=term-missing"
markers = [
    "asyncio: marks tests as async tests",
]
```

### Coverage Configuration
```toml
[tool.coverage.run]
source = ["app"]
omit = ["*/tests/*", "*/test_*", "*/__pycache__/*", "*/site-packages/*"]

[tool.coverage.report]
fail_under = {{COVERAGE_THRESHOLD}}
show_missing = true
skip_covered = true
```

## Optional Sections

### Private package index
Include when the project uses a private index:
```toml
[[tool.uv.index]]
name = "{{PRIVATE_INDEX_NAME}}"
url = "{{PRIVATE_INDEX_URL}}"

[tool.uv.sources]
{{PRIVATE_PACKAGE}} = { index = "{{PRIVATE_INDEX_NAME}}" }
```

### Setuptools Package Discovery
Include for services:
```toml
[tool.setuptools.packages.find]
where = ["app"]
```

### Hatch Build Configuration
Include for libraries:
```toml
[tool.hatch.version]
path = "{{PACKAGE_NAME}}/__init__.py"

[tool.hatch.build.targets.wheel]
packages = ["{{PACKAGE_NAME}}"]

[tool.hatch.build.targets.sdist]
include = [
    "/{{PACKAGE_NAME}}",
    "/tests",
    "/README.md",
    "/CHANGELOG.md",
]
```

### Platform-Specific Groups (Electron Backend)
Include for cross-platform apps:
```toml
[dependency-groups]
macos = [
    "mlx-whisper>=0.4.3 ; platform_machine == 'arm64'",
]
windows = []
```

### MyPy Configuration
Include for libraries:
```toml
[tool.mypy]
python_version = "3.12"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
strict_equality = true
show_error_codes = true
```

## Validation Checklist

Before finalizing, verify:
- [ ] Correct build system (hatchling vs setuptools)
- [ ] Python version constraint matches requirements
- [ ] Dependencies are properly categorized (runtime vs dev)
- [ ] Coverage threshold is appropriate for project type
- [ ] Package discovery points to correct directory
- [ ] Ruff ignore rules match team conventions
- [ ] Pytest asyncio mode is set correctly

## Coverage Thresholds by Type

| Project Type | Default Threshold |
|--------------|-------------------|
| Library | 60% |
| MCP Server | 75% |
| Service | 90% |
| Electron Backend | 65% |

## Files

- [templates/python-library.toml](templates/python-library.toml) - Python library template
- [templates/python-service.toml](templates/python-service.toml) - Python service template
- [templates/mcp-server.toml](templates/mcp-server.toml) - MCP server template
- [templates/python-service-db.toml](templates/python-service-db.toml) - Service with DB template
- [templates/electron-backend.toml](templates/electron-backend.toml) - Electron backend template
