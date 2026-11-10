---
name: makefile-generator
description: Use when creating or standardizing a Makefile for a Python, MCP, Node.js/Electron or Java/Gradle project.
allowed-tools: Read, Write, Glob, AskUserQuestion
user-invocable: true
---

# Makefile Generator

Generates standardized Makefiles for the supported project types.

## Usage

Invoke this skill when:
- Creating a new repository
- Initializing a new service/module
- Standardizing an existing Makefile

## Project Types Supported

| Type | Package Manager | Use Case |
|------|-----------------|----------|
| `python-library` | UV | PyPI packages, shared libraries |
| `python-service` | UV | FastAPI services, workers |
| `mcp-server` | UV + private index | Model Context Protocol servers |
| `python-service-db` | UV + Alembic | Services with database migrations |
| `electron-frontend` | npm | Electron UI applications |
| `electron-backend` | UV + PyInstaller | Python backends for Electron apps |
| `java-gradle` | Gradle | JVM projects, plugins |

## Generation Process

### Step 1: Gather Requirements

Ask the user for:
1. **Project type** (from table above)
2. **Project slug** (e.g., `my-service`, used in Docker image names)
3. **Venv prompt name** (short name for shell prompt, e.g., `ms` for management-service)
4. **Service port** (if applicable, for `run` target)
5. **Docker support** (yes/no for services)
6. **Private package index** (a private registry, when the project needs one)
7. **Documentation** (mkdocs for libraries)
8. **PyPI publishing** (for libraries)

### Step 2: Generate from Template

Use the appropriate template from `templates/` and customize:
- Replace `{{SERVICE_SLUG}}` with project slug
- Replace `{{VENV_PROMPT}}` with venv prompt name
- Replace `{{SERVICE_PORT}}` with port number
- Include/exclude optional sections based on requirements

## Universal Patterns (All Templates)

### Header Section
```makefile
SHELL := /bin/bash
UV := uv

# Variables
PYTHON_VERSION ?= $(shell python3 --version 2>/dev/null | grep -o '3\.[0-9]*' || echo "3.12")

# Venv settings - CI-aware paths
ifeq ($(CI),true)
VENV := /app/.venv
else
VENV := .venv
endif
BIN := $(VENV)/bin
```

### Color Definitions
```makefile
# Colors for terminal output
RED    = $(shell tput setaf 1 2>/dev/null || echo "")
GREEN  = $(shell tput setaf 2 2>/dev/null || echo "")
YELLOW = $(shell tput setaf 3 2>/dev/null || echo "")
BLUE   = $(shell tput setaf 4 2>/dev/null || echo "")
CYAN   = $(shell tput setaf 6 2>/dev/null || echo "")
NC     = $(shell tput sgr0 2>/dev/null || echo "")
```

### Help System
```makefile
.DEFAULT_GOAL := help

help: ## Show this help message
	@echo "$(BLUE){{PROJECT_NAME}} - Development Makefile$(NC)"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "$(CYAN)Targets:$(NC)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)
```

### Tool Variables
```makefile
BIN := $(VENV)/bin
RUFF := $(BIN)/ruff
PYTEST := $(BIN)/pytest
```

### Core Targets (Python)
```makefile
check-lockfile: ## Verify uv.lock exists
	@if [ ! -f "uv.lock" ]; then \
		echo "$(YELLOW)No uv.lock found, generating...$(NC)"; \
		$(UV) lock; \
	fi

install: $(VENV)/pyvenv.cfg check-lockfile ## Install production dependencies
	@echo "$(CYAN)Installing production dependencies...$(NC)"
	@$(UV) sync --locked --no-dev || { echo "$(RED)Error: Failed to install.$(NC)"; exit 1; }
	@echo "$(GREEN)Production dependencies installed.$(NC)"

dev-install: $(VENV)/pyvenv.cfg check-lockfile ## Install development dependencies
	@echo "$(CYAN)Installing development dependencies...$(NC)"
	@$(UV) sync --locked --all-extras || { echo "$(RED)Error: Failed to install dev deps.$(NC)"; exit 1; }
	@echo "$(GREEN)Development dependencies installed.$(NC)"

test: check-lockfile dev-install ## Run linters and tests with coverage
	@echo "$(YELLOW)Running Ruff format...$(NC)"
	@$(RUFF) format . || { \
		echo "$(RED)Formatting failed.$(NC)"; \
		exit 1; \
	}
	@echo "$(YELLOW)Running Ruff linter...$(NC)"
	@$(RUFF) check . --fix || { \
		echo "$(RED)Linting failed.$(NC)"; \
		exit 1; \
	}
	@echo "$(YELLOW)Running Python tests with coverage...$(NC)"
	@$(PYTEST) --cov={{PACKAGE}} --cov-report=term-missing || { \
		echo "$(RED)Tests failed.$(NC)"; \
		exit 1; \
	}
	@echo "$(GREEN)All tests passed.$(NC)"

clean: ## Remove build artifacts and caches
	@echo "$(YELLOW)Cleaning up...$(NC)"
	@find . -type f -name '*.py[co]' -delete
	@find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
	@rm -rf .pytest_cache .ruff_cache .coverage htmlcov build dist *.egg-info
	@echo "$(GREEN)Clean complete.$(NC)"

dist-clean: clean ## Full clean including venv
	@echo "$(RED)Performing full clean...$(NC)"
	@rm -rf $(VENV) uv.lock
	@echo "$(GREEN)Full clean complete.$(NC)"
```

## Optional Sections

### Docker Support
Include for containerized services:
```makefile
docker-build: ## Build Docker image
	@echo "$(CYAN)Building Docker image $(IMAGE_NAME):$(IMAGE_TAG)...$(NC)"
	@DOCKER_BUILDKIT=1 docker build -t $(IMAGE_NAME):$(IMAGE_TAG) .
	@echo "$(GREEN)Docker image built$(NC)"
```

### Alembic Migrations
Include for database services:
```makefile
revision: ## Generate new migration (message="description")
	@if [ -z "$(message)" ]; then echo "Error: message= required"; exit 1; fi
	@$(BIN)/alembic revision --autogenerate -m "$(message)"

upgrade: ## Apply migrations to head
	@$(BIN)/alembic upgrade head

downgrade: ## Rollback one migration
	@$(BIN)/alembic downgrade -1
```

### Private index auth
Include when a private package index is used:
```makefile
check-index-auth: ## Verify INDEX_TOKEN is set
	@if [ -z "$$INDEX_TOKEN" ]; then \
		echo "$(RED)Error: INDEX_TOKEN not set$(NC)"; exit 1; \
	fi
```

### PyPI Publishing
Include for libraries:
```makefile
build: clean ## Build distribution packages
	@$(BIN)/python -m build

publish: build ## Publish to PyPI
	@$(BIN)/twine upload dist/*
```

## Validation Checklist

Before finalizing, verify:
- [ ] `SHELL := /bin/bash` is set
- [ ] `.DEFAULT_GOAL := help` is set
- [ ] All phony targets listed in `.PHONY`
- [ ] Colors work on systems without tput
- [ ] CI-aware venv path
- [ ] Error handling with `|| { echo "..."; exit 1; }`
- [ ] Consistent emoji/spacing in output
- [ ] `##` comments for help extraction
- [ ] `check-lockfile` target for uv.lock verification
- [ ] `test` target depends on `check-lockfile dev-install`
- [ ] `test` runs format (in-place), lint (with --fix), then pytest
- [ ] Tool variables (`RUFF`, `PYTEST`) defined for cleaner targets

## Files

- [templates/python-library.mk](templates/python-library.mk) - Python library template
- [templates/python-service.mk](templates/python-service.mk) - Python service template
- [templates/mcp-server.mk](templates/mcp-server.mk) - MCP server template
- [templates/python-service-db.mk](templates/python-service-db.mk) - Service with DB template
- [templates/electron-frontend.mk](templates/electron-frontend.mk) - Electron frontend template
- [templates/electron-backend.mk](templates/electron-backend.mk) - Electron backend template
- [templates/java-gradle.mk](templates/java-gradle.mk) - Java/Gradle template
