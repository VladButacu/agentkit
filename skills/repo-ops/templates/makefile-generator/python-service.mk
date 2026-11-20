# Python Service Makefile Template
# Variables to replace: {{SERVICE_SLUG}}, {{VENV_PROMPT}}, {{SERVICE_PORT}}

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
SERVICE_SLUG := {{SERVICE_SLUG}}
IMAGE_NAME := {{SERVICE_SLUG}}
IMAGE_TAG ?= latest
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
.PHONY: help install dev-install update-deps test test-integration clean dist-clean run docker-build check-lockfile

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
	@echo "$(BLUE)Service [$(SERVICE_SLUG)] - Development Makefile$(NC)"
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
	@$(PYTEST) tests/unit --cov=app --cov-report=term-missing || { \
		echo "$(RED)Tests failed.$(NC)"; \
		exit 1; \
	}
	@echo "$(GREEN)All tests passed.$(NC)"

test-integration: ## Run integration tests
	@echo "$(YELLOW)Running integration tests...$(NC)"
	@$(PYTEST) tests/integration --cov=app --cov-report=term-missing || { \
		echo "$(RED)Integration tests failed.$(NC)"; \
		exit 1; \
	}

# ============================================================================
# Running
# ============================================================================

run: ## Run the FastAPI application
	@echo "$(YELLOW)Running application on port {{SERVICE_PORT}}...$(NC)"
	@$(BIN)/uvicorn app.main:app --host 0.0.0.0 --port {{SERVICE_PORT}} --reload

# ============================================================================
# Docker
# ============================================================================

docker-build: ## Build Docker image
	@echo "$(CYAN)Building Docker image $(IMAGE_NAME):$(IMAGE_TAG)...$(NC)"
	@DOCKER_BUILDKIT=1 docker build \
		--build-arg PYTHON_VERSION=$(PYTHON_VERSION) \
		-t $(IMAGE_NAME):$(IMAGE_TAG) \
		.
	@echo "$(GREEN)Docker image built: $(IMAGE_NAME):$(IMAGE_TAG)$(NC)"

# ============================================================================
# Cleanup
# ============================================================================

clean: ## Remove build artifacts and caches
	@echo "$(YELLOW)Cleaning up...$(NC)"
	@find . -type f -name '*.py[co]' -delete
	@find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
	@rm -rf .pytest_cache .ruff_cache .coverage coverage.xml htmlcov
	@rm -rf build dist *.egg-info
	@echo "$(GREEN)Clean complete.$(NC)"

dist-clean: clean ## Full clean including venv and lock file
	@echo "$(RED)Performing full clean...$(NC)"
	@rm -rf $(VENV) uv.lock
	@echo "$(GREEN)Full clean complete.$(NC)"
