# Python Service with Database Makefile Template
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
.PHONY: help install dev-install update-deps test test-integration clean dist-clean run docker-build \
        revision upgrade downgrade

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

install: $(VENV)/pyvenv.cfg uv.lock ## Install production dependencies
	@echo "$(CYAN)Installing production dependencies...$(NC)"
	@$(UV) sync --locked --no-dev || { echo "$(RED)Error: Failed to install.$(NC)"; exit 1; }
	@echo "$(GREEN)Production dependencies installed.$(NC)"

dev-install: $(VENV)/pyvenv.cfg ## Install development dependencies
	@echo "$(CYAN)Installing development dependencies...$(NC)"
	@$(UV) sync --locked --group dev || { echo "$(RED)Error: Failed to install dev deps.$(NC)"; exit 1; }
	@echo "$(GREEN)Development dependencies installed.$(NC)"

update-deps: ## Update dependencies and regenerate uv.lock
	@echo "$(CYAN)Updating dependencies...$(NC)"
	@$(UV) lock --upgrade || { echo "$(RED)Error: Failed to update deps.$(NC)"; exit 1; }
	@echo "$(GREEN)Dependencies updated.$(NC)"

# ============================================================================
# Testing
# ============================================================================

test: ## Run linters and tests with coverage
	@echo "$(YELLOW)Running Ruff format...$(NC)"
	@$(BIN)/ruff format . --check || { echo "$(RED)Format check failed.$(NC)"; exit 1; }
	@echo "$(YELLOW)Running Ruff linter...$(NC)"
	@$(BIN)/ruff check . || { echo "$(RED)Lint check failed.$(NC)"; exit 1; }
	@echo "$(YELLOW)Running tests...$(NC)"
	@$(BIN)/pytest tests/unit --cov=app || { echo "$(RED)Tests failed.$(NC)"; exit 1; }
	@echo "$(GREEN)All tests passed.$(NC)"

test-integration: ## Run integration tests
	@echo "$(YELLOW)Running integration tests...$(NC)"
	@$(BIN)/pytest tests/integration --cov=app || { echo "$(RED)Integration tests failed.$(NC)"; exit 1; }

# ============================================================================
# Database Migrations (Alembic)
# ============================================================================

revision: ## Generate new migration (use message="description")
	@echo "$(BLUE)Generating Alembic revision...$(NC)"
	@if [ -z "$(message)" ]; then \
		echo "$(RED)Error: Please provide a message using message=\"Your message\"$(NC)"; \
		exit 1; \
	fi
	@set -a; [ -f .env ] && source .env; set +a
	@$(BIN)/alembic revision --autogenerate -m "$(message)"

upgrade: ## Apply migrations to head
	@echo "$(BLUE)Applying migrations...$(NC)"
	@set -a; [ -f .env ] && source .env; set +a
	@$(BIN)/alembic upgrade head

downgrade: ## Rollback one migration
	@echo "$(YELLOW)Downgrading database...$(NC)"
	@set -a; [ -f .env ] && source .env; set +a
	@$(BIN)/alembic downgrade -1

# ============================================================================
# Running
# ============================================================================

run: upgrade ## Run the FastAPI application (applies migrations first)
	@echo "$(YELLOW)Running application on port {{SERVICE_PORT}}...$(NC)"
	@$(BIN)/uvicorn app.main:app --host 0.0.0.0 --port {{SERVICE_PORT}} --reload --proxy-headers --forwarded-allow-ips='*'

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
	@rm -rf .pytest_cache .ruff_cache .coverage coverage.xml htmlcov
	@rm -rf build dist *.egg-info
	@find . -type f -name '*.pyc' -delete
	@find . -type d -name '__pycache__' -delete
	@echo "$(GREEN)Clean complete.$(NC)"

dist-clean: clean ## Full clean including venv and lock file
	@echo "$(RED)Performing full clean...$(NC)"
	@rm -rf $(VENV) uv.lock
	@echo "$(GREEN)Full clean complete.$(NC)"
