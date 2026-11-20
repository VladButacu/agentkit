# MCP Server Makefile Template
# Variables to replace: {{SERVICE_SLUG}}, {{VENV_PROMPT}}, {{MCP_PORT}}, {{API_PORT}}, {{METRICS_PORT}}

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
.PHONY: help install dev-install update-deps test test-integration test-e2e clean dist-clean run docker-build check-index-auth

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
# Authentication
# ============================================================================

check-index-auth: ## Verify INDEX_TOKEN is set for the private package index
	@echo "$(GREEN)Checking private index authentication...$(NC)"
	@if [ -z "$$INDEX_TOKEN" ]; then \
		echo "$(RED)Error: INDEX_TOKEN environment variable is not set$(NC)"; \
		echo "Set it to the private index access token"; \
		exit 1; \
	fi
	@echo "$(GREEN)✓ Private index authentication configured$(NC)"

# ============================================================================
# Installation
# ============================================================================

install: check-index-auth $(VENV)/pyvenv.cfg uv.lock ## Install production dependencies
	@echo "$(CYAN)Installing production dependencies...$(NC)"
	@$(UV) sync --locked --no-dev || { echo "$(RED)Error: Failed to install.$(NC)"; exit 1; }
	@echo "$(GREEN)Production dependencies installed.$(NC)"

dev-install: check-gitlab-auth $(VENV)/pyvenv.cfg ## Install development dependencies
	@echo "$(CYAN)Installing development dependencies...$(NC)"
	@$(UV) sync --locked --group dev || { echo "$(RED)Error: Failed to install dev deps.$(NC)"; exit 1; }
	@echo "$(GREEN)Development dependencies installed.$(NC)"

update-deps: check-gitlab-auth ## Update dependencies and regenerate uv.lock
	@echo "$(CYAN)Updating dependencies...$(NC)"
	@$(UV) lock --upgrade || { echo "$(RED)Error: Failed to update deps.$(NC)"; exit 1; }
	@echo "$(GREEN)Dependencies updated.$(NC)"

# ============================================================================
# Testing
# ============================================================================

test: ## Run linters and tests with coverage
	@echo "$(YELLOW)Running Ruff format...$(NC)"
	@$(BIN)/ruff format . || { echo "$(RED)Format check failed.$(NC)"; exit 1; }
	@echo "$(YELLOW)Running Ruff linter...$(NC)"
	@$(BIN)/ruff check . --fix || { echo "$(RED)Lint check failed.$(NC)"; exit 1; }
	@echo "$(YELLOW)Running tests...$(NC)"
	@$(BIN)/pytest tests/unit --cov=app || { echo "$(RED)Tests failed.$(NC)"; exit 1; }
	@echo "$(GREEN)All tests passed.$(NC)"

test-integration: ## Run integration tests
	@echo "$(YELLOW)Running integration tests...$(NC)"
	@$(BIN)/pytest tests/integration --cov=app --cov-fail-under=0 || { echo "$(RED)Integration tests failed.$(NC)"; exit 1; }

test-e2e: ## Run end-to-end tests
	@echo "$(YELLOW)Running end-to-end tests...$(NC)"
	@$(BIN)/pytest tests/e2e --cov=app --cov-fail-under=0 || { echo "$(RED)E2E tests failed.$(NC)"; exit 1; }

# ============================================================================
# Running
# ============================================================================

run: ## Run dual server (MCP: {{MCP_PORT}}, FastAPI: {{API_PORT}}, Metrics: {{METRICS_PORT}})
	@echo "$(YELLOW)Running dual server (MCP: {{MCP_PORT}}, FastAPI: {{API_PORT}}, Metrics: {{METRICS_PORT}})...$(NC)"
	@$(BIN)/python -m app.main

# ============================================================================
# Docker
# ============================================================================

docker-build: check-gitlab-auth ## Build Docker image with GitLab token
	@echo "$(CYAN)Building Docker image $(IMAGE_NAME):$(IMAGE_TAG)...$(NC)"
	@DOCKER_BUILDKIT=1 docker build \
		--secret id=gitlab_token,env=GITLAB_TOKEN \
		--build-arg PYTHON_VERSION=$(PYTHON_VERSION) \
		-t $(IMAGE_NAME):$(IMAGE_TAG) \
		.
	@echo "$(GREEN)Docker image built: $(IMAGE_NAME):$(IMAGE_TAG)$(NC)"

# ============================================================================
# Cleanup
# ============================================================================

clean: ## Remove build artifacts and caches
	@echo "$(YELLOW)Cleaning up...$(NC)"
	@rm -rf .pytest_cache .ruff_cache .coverage coverage.xml htmlcov tests/htmlcov
	@rm -rf build dist *.egg-info
	@find . -type f -name '*.pyc' -delete
	@find . -type d -name '__pycache__' -delete
	@echo "$(GREEN)Clean complete.$(NC)"

dist-clean: clean ## Full clean including venv and lock file
	@echo "$(RED)Performing full clean...$(NC)"
	@rm -rf $(VENV) uv.lock
	@echo "$(GREEN)Full clean complete.$(NC)"
