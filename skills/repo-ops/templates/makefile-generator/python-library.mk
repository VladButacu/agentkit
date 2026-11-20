# Python Library Makefile Template
# Variables to replace: {{LIBRARY_NAME}}, {{VENV_PROMPT}}

SHELL := /bin/bash
UV := uv

# Variables
PYTHON_VERSION ?= $(shell python3 --version 2>/dev/null | grep -o '3\.[0-9]*' || echo "3.12")
ifeq ($(CI),true)
VENV := /app/.venv
else
VENV := .venv
endif
BIN := $(VENV)/bin
LIBRARY_NAME := {{LIBRARY_NAME}}
RUFF := $(BIN)/ruff
PYTEST := $(BIN)/pytest

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
.PHONY: help install dev-install update-deps test docs docs-serve clean dist-clean build check-dist publish check-lockfile

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
	@echo "$(BLUE){{LIBRARY_NAME}} - Development Makefile$(NC)"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "$(CYAN)Targets:$(NC)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# ============================================================================
# Installation
# ============================================================================

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

update-deps: ## Update dependencies and regenerate uv.lock
	@echo "$(CYAN)Updating dependencies...$(NC)"
	@$(UV) lock --upgrade || { echo "$(RED)Error: Failed to update deps.$(NC)"; exit 1; }
	@echo "$(GREEN)Dependencies updated.$(NC)"

# ============================================================================
# Testing
# ============================================================================

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
	@$(PYTEST) --cov={{LIBRARY_NAME}} --cov-report=term-missing || { \
		echo "$(RED)Tests failed.$(NC)"; \
		exit 1; \
	}
	@echo "$(GREEN)All tests passed.$(NC)"

# ============================================================================
# Documentation
# ============================================================================

docs: ## Build documentation
	@echo "$(YELLOW)Building documentation...$(NC)"
	@$(BIN)/mkdocs build || { echo "$(RED)Documentation build failed.$(NC)"; exit 1; }
	@echo "$(GREEN)Documentation built in site/$(NC)"

docs-serve: ## Serve documentation locally
	@echo "$(YELLOW)Serving documentation at http://localhost:8000$(NC)"
	@$(BIN)/mkdocs serve

# ============================================================================
# Building & Publishing
# ============================================================================

build: clean ## Build distribution packages
	@echo "$(YELLOW)Building package...$(NC)"
	@$(BIN)/python -m build || { echo "$(RED)Build failed.$(NC)"; exit 1; }
	@echo "$(GREEN)Package built in dist/$(NC)"

check-dist: build ## Check distribution packages
	@echo "$(YELLOW)Checking distribution packages...$(NC)"
	@$(BIN)/twine check dist/* || { echo "$(RED)Distribution check failed.$(NC)"; exit 1; }
	@echo "$(GREEN)Distribution packages are valid.$(NC)"

publish: check-dist ## Publish to PyPI (requires TWINE_USERNAME and TWINE_PASSWORD)
	@echo "$(YELLOW)Publishing to PyPI...$(NC)"
	@$(BIN)/twine upload dist/* || { echo "$(RED)Publish failed.$(NC)"; exit 1; }
	@echo "$(GREEN)Package published to PyPI.$(NC)"

# ============================================================================
# Cleanup
# ============================================================================

clean: ## Remove build artifacts and caches
	@echo "$(YELLOW)Cleaning up...$(NC)"
	@find . -type f -name '*.py[co]' -delete
	@find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
	@rm -rf .pytest_cache .ruff_cache .coverage htmlcov build dist *.egg-info site/
	@echo "$(GREEN)Clean complete.$(NC)"

dist-clean: clean ## Full clean including venv
	@echo "$(RED)Performing full clean...$(NC)"
	@rm -rf $(VENV) uv.lock
	@echo "$(GREEN)Full clean complete.$(NC)"
