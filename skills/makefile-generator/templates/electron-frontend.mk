# Electron Frontend Makefile Template
# Variables to replace: {{APP_NAME}}

SHELL := /bin/bash

# Variables
NODE_MODULES := node_modules
NPM_BIN := $(NODE_MODULES)/.bin

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
.PHONY: help install dev prod test lint format build build-mac build-win build-linux clean dist-clean

# ============================================================================
# Help
# ============================================================================

help: ## Show this help message
	@echo "$(BLUE){{APP_NAME}} Frontend - Development Makefile$(NC)"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "$(CYAN)Targets:$(NC)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# ============================================================================
# Installation
# ============================================================================

ensure-node-modules:
	@if [ ! -d "$(NODE_MODULES)" ]; then \
		echo "$(YELLOW)node_modules missing; running npm install$(NC)"; \
		npm install; \
	fi

install: ## Install Node.js dependencies
	@echo "$(CYAN)Installing Node.js dependencies...$(NC)"
	@npm install
	@echo "$(GREEN)Node.js dependencies installed.$(NC)"

# ============================================================================
# Running
# ============================================================================

dev: ensure-node-modules ## Start in dev mode (dev-tools, auto-reload)
	@echo "$(CYAN)Starting {{APP_NAME}} in development mode...$(NC)"
	@npm run start

prod: ensure-node-modules ## Start locally as production (no dev-tools)
	@echo "$(CYAN)Starting {{APP_NAME}} in production mode...$(NC)"
	@npm run start:prod

# ============================================================================
# Testing & Linting
# ============================================================================

lint: ## Run frontend linters
	@echo "$(CYAN)Running frontend linters...$(NC)"
	@npm run lint 2>/dev/null || echo "$(YELLOW)No lint script configured$(NC)"

format: ## Format frontend code
	@echo "$(CYAN)Formatting frontend code...$(NC)"
	@npm run format 2>/dev/null || echo "$(YELLOW)No format script configured$(NC)"

test: ## Run frontend tests
	@echo "$(CYAN)Running frontend tests...$(NC)"
	@npm test 2>/dev/null || echo "$(YELLOW)No tests configured yet$(NC)"

# ============================================================================
# Building
# ============================================================================

build: ## Build production package for current platform
	@echo "$(CYAN)Building {{APP_NAME}} for current platform...$(NC)"
	@npm run build
	@echo "$(GREEN)Build complete. Check dist/ folder.$(NC)"

build-mac: ## Build production macOS DMG
	@echo "$(CYAN)Building {{APP_NAME}} for macOS...$(NC)"
	@CSC_IDENTITY_AUTO_DISCOVERY=false npm run build:mac -- --publish never
	@echo "$(GREEN)macOS build complete.$(NC)"

build-win: ## Build production Windows installer
	@echo "$(CYAN)Building {{APP_NAME}} for Windows...$(NC)"
	@npm run build:win -- --publish never
	@echo "$(GREEN)Windows build complete.$(NC)"

build-linux: ## Build production Linux AppImage
	@echo "$(CYAN)Building {{APP_NAME}} for Linux...$(NC)"
	@npm run build:linux -- --publish never
	@echo "$(GREEN)Linux build complete.$(NC)"

# ============================================================================
# Cleanup
# ============================================================================

clean: ## Remove build artifacts
	@echo "$(YELLOW)Cleaning frontend...$(NC)"
	@rm -rf dist out
	@echo "$(GREEN)Frontend clean complete.$(NC)"

dist-clean: clean ## Full clean including node_modules
	@echo "$(RED)Performing full frontend clean...$(NC)"
	@rm -rf $(NODE_MODULES)
	@echo "$(GREEN)Frontend full clean complete.$(NC)"
