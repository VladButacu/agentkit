# Electron Backend (Python) Makefile Template
# Variables to replace: {{APP_NAME}}, {{VENV_PROMPT}}

SHELL := /bin/bash
UV := uv

# Variables
PYTHON_VERSION ?= $(shell python3 --version 2>/dev/null | grep -o '3\.[0-9]*' || echo "3.12")
VENV := .venv

# Platform-specific binary paths
ifeq ($(OS),Windows_NT)
BIN := $(VENV)/Scripts
PYTHON := $(BIN)/python.exe
RUFF := $(BIN)/ruff.exe
PYTEST := $(BIN)/pytest.exe
else
BIN := $(VENV)/bin
PYTHON := $(BIN)/python
RUFF := $(BIN)/ruff
PYTEST := $(BIN)/pytest
endif

# Colors for terminal output
RED    = $(shell tput setaf 1 2>/dev/null || echo "")
GREEN  = $(shell tput setaf 2 2>/dev/null || echo "")
YELLOW = $(shell tput setaf 3 2>/dev/null || echo "")
BLUE   = $(shell tput setaf 4 2>/dev/null || echo "")
CYAN   = $(shell tput setaf 6 2>/dev/null || echo "")
NC     = $(shell tput sgr0 2>/dev/null || echo "")

# Default target
.DEFAULT_GOAL := help

# Phony targets
.PHONY: help install install-macos install-windows dev-install build-install update-deps test \
        compile-backend check-lockfile clean dist-clean

# ============================================================================
# Virtual Environment
# ============================================================================

$(VENV)/pyvenv.cfg:
	@echo "$(CYAN)Creating virtual environment...$(NC)"
	@$(UV) venv $(VENV) --prompt {{VENV_PROMPT}} --python $(shell which python3) || { \
		echo "$(RED)Error: Failed to create virtual environment.$(NC)"; exit 1; \
	}

# ============================================================================
# Help
# ============================================================================

help: ## Show this help message
	@echo "$(BLUE){{APP_NAME}} Backend - Development Makefile$(NC)"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "$(CYAN)Targets:$(NC)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# ============================================================================
# Installation
# ============================================================================

install: $(VENV)/pyvenv.cfg ## Install production dependencies
	@echo "$(CYAN)Installing production dependencies...$(NC)"
	@$(UV) sync --locked --no-dev || { echo "$(RED)Error: Failed to install.$(NC)"; exit 1; }
	@echo "$(GREEN)Production dependencies installed.$(NC)"

install-macos: $(VENV)/pyvenv.cfg ## Install production + macOS-specific dependencies
	@echo "$(CYAN)Installing production + macOS dependencies...$(NC)"
	@$(UV) sync --locked --no-dev --group macos || { echo "$(RED)Error: Failed to install.$(NC)"; exit 1; }
	@echo "$(GREEN)macOS dependencies installed.$(NC)"

install-windows: $(VENV)/pyvenv.cfg ## Install production + Windows-specific dependencies
	@echo "$(CYAN)Installing production + Windows dependencies...$(NC)"
	@$(UV) sync --locked --no-dev --group windows || { echo "$(RED)Error: Failed to install.$(NC)"; exit 1; }
	@echo "$(GREEN)Windows dependencies installed.$(NC)"

dev-install: $(VENV)/pyvenv.cfg ## Install development + all platform dependencies
	@echo "$(CYAN)Installing development dependencies...$(NC)"
	@$(UV) sync --locked --group dev --group build --group macos --group windows || { echo "$(RED)Error: Failed to install.$(NC)"; exit 1; }
	@echo "$(GREEN)Development dependencies installed.$(NC)"

build-install: $(VENV)/pyvenv.cfg ## Install only build dependencies (no test/lint)
	@echo "$(CYAN)Installing build dependencies...$(NC)"
	@$(UV) sync --locked --no-dev --group build --group macos || { echo "$(RED)Error: Failed to install.$(NC)"; exit 1; }
	@echo "$(GREEN)Build dependencies installed.$(NC)"

update-deps: $(VENV)/pyvenv.cfg ## Update dependencies and regenerate uv.lock
	@echo "$(CYAN)Updating dependencies...$(NC)"
	@$(UV) lock --upgrade || { echo "$(RED)Error: Failed to update deps.$(NC)"; exit 1; }
	@echo "$(GREEN)Dependencies updated.$(NC)"

check-lockfile: ## Verify pyproject and uv.lock are in sync
	@echo "$(CYAN)Checking lockfile drift...$(NC)"
	@$(UV) lock --check || { echo "$(RED)Error: uv.lock is out of sync. Run 'make update-deps'.$(NC)"; exit 1; }
	@echo "$(GREEN)Lockfile is in sync.$(NC)"

# ============================================================================
# Testing & Linting
# ============================================================================

test: check-lockfile dev-install ## Run linters and tests with coverage
	@echo "$(YELLOW)Running Ruff format...$(NC)"
	@$(RUFF) format . || { echo "$(RED)Format check failed.$(NC)"; exit 1; }
	@echo "$(YELLOW)Running Ruff linter...$(NC)"
	@$(RUFF) check . --fix || { echo "$(RED)Lint check failed.$(NC)"; exit 1; }
	@echo "$(YELLOW)Running tests...$(NC)"
	@$(PYTEST) tests -n auto --dist worksteal --cov=app || { echo "$(RED)Tests failed.$(NC)"; exit 1; }
	@echo "$(GREEN)All tests passed.$(NC)"

# ============================================================================
# Building
# ============================================================================

compile-backend: build-install ## Compile Python backend with PyInstaller
	@echo "$(CYAN)Compiling Python backend with PyInstaller...$(NC)"
	@$(PYTHON) -m PyInstaller {{APP_NAME}}-backend.spec \
		--noconfirm \
		--log-level WARN \
		--distpath dist \
		--workpath build/pyinstaller || { \
		echo "$(RED)PyInstaller compilation failed.$(NC)"; exit 1; \
	}
	@echo "$(GREEN)Backend compiled to dist/{{APP_NAME}}-backend$(NC)"

# ============================================================================
# Cleanup
# ============================================================================

clean: ## Remove build artifacts and caches
	@echo "$(YELLOW)Cleaning backend...$(NC)"
	@rm -rf .pytest_cache .ruff_cache .coverage
	@rm -rf htmlcov coverage.xml
	@rm -rf build dist *.egg-info
	@find . -type f -name '*.pyc' -delete
	@find . -type d -name '__pycache__' -delete
	@echo "$(GREEN)Backend clean complete.$(NC)"

dist-clean: clean ## Full clean including venv and lock file
	@echo "$(RED)Performing full backend clean...$(NC)"
	@rm -rf $(VENV) uv.lock
	@echo "$(GREEN)Full clean complete.$(NC)"
