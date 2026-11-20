# Java/Gradle Makefile Template
# Variables to replace: {{PLUGIN_SLUG}}

SHELL := /bin/bash

# Variables
GRADLE := ./gradlew
PLUGIN_SLUG := {{PLUGIN_SLUG}}
JAVA_HOME := $(shell /usr/libexec/java_home 2>/dev/null || echo "/opt/homebrew/opt/openjdk")
export JAVA_HOME
export PATH := $(JAVA_HOME)/bin:$(PATH)

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
.PHONY: help dev-install test test-integration build update clean dist-clean

# ============================================================================
# Gradle Wrapper
# ============================================================================

gradlew:
	@if [ ! -f "$(GRADLE)" ]; then \
		echo "$(YELLOW)Creating Gradle wrapper...$(NC)"; \
		if ! command -v gradle > /dev/null; then \
			echo "$(YELLOW)Installing Gradle via Homebrew...$(NC)"; \
			brew install gradle || { echo "$(RED)Error: Failed to install Gradle.$(NC)"; exit 1; }; \
		fi; \
		gradle wrapper || { echo "$(RED)Error: Failed to create Gradle wrapper.$(NC)"; exit 1; }; \
		echo "$(GREEN)✓ Gradle wrapper created$(NC)"; \
	fi

# ============================================================================
# Help
# ============================================================================

help: ## Show this help message
	@echo "$(BLUE)Plugin [$(PLUGIN_SLUG)] - Development Makefile$(NC)"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "$(CYAN)Targets:$(NC)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# ============================================================================
# Installation
# ============================================================================

dev-install: gradlew ## Install development dependencies
	@echo "$(YELLOW)Installing development dependencies...$(NC)"
	@$(GRADLE) build -x test || { echo "$(RED)Error: Failed to install dependencies.$(NC)"; exit 1; }
	@echo "$(GREEN)✓ Development dependencies installed.$(NC)"

# ============================================================================
# Testing
# ============================================================================

test: gradlew ## Run unit tests (excludes integration tests)
	@echo "$(YELLOW)Running unit tests...$(NC)"
	@$(GRADLE) test --tests '*Test' --tests '!*IntegrationTest' || { echo "$(RED)Error: Tests failed.$(NC)"; exit 1; }
	@echo "$(GREEN)✓ All unit tests passed.$(NC)"

test-integration: gradlew build ## Run integration tests
	@echo "$(YELLOW)Running integration tests (requires Docker)...$(NC)"
	@$(GRADLE) test --tests '*IntegrationTest' || { echo "$(RED)Error: Integration tests failed.$(NC)"; exit 1; }
	@echo "$(GREEN)✓ All integration tests passed.$(NC)"

# ============================================================================
# Building
# ============================================================================

build: gradlew ## Build the project JAR (excludes integration tests)
	@echo "$(YELLOW)Building $(PLUGIN_SLUG)...$(NC)"
	@$(GRADLE) build -x test || { echo "$(RED)Error: Build failed.$(NC)"; exit 1; }
	@echo "$(GREEN)✓ Build successful.$(NC)"

shadow-jar: gradlew ## Build shaded/uber JAR
	@echo "$(YELLOW)Building shaded JAR...$(NC)"
	@$(GRADLE) shadowJar || { echo "$(RED)Error: Shadow JAR build failed.$(NC)"; exit 1; }
	@echo "$(GREEN)✓ Shaded JAR built at build/libs/$(NC)"

# ============================================================================
# Dependencies
# ============================================================================

update: gradlew ## Update dependencies
	@echo "$(YELLOW)Updating dependencies...$(NC)"
	@$(GRADLE) build --refresh-dependencies || { echo "$(RED)Error: Failed to update dependencies.$(NC)"; exit 1; }
	@echo "$(GREEN)✓ Dependencies updated.$(NC)"

# ============================================================================
# Cleanup
# ============================================================================

clean: ## Remove build artifacts and cache
	@echo "$(YELLOW)Cleaning up...$(NC)"
	@$(GRADLE) clean 2>/dev/null || true
	@echo "$(GREEN)Clean complete.$(NC)"

dist-clean: clean ## Clean everything including Gradle cache
	@echo "$(RED)Performing full clean...$(NC)"
	@rm -rf ~/.gradle/caches/modules-2/files-2.1/* 2>/dev/null || true
	@echo "$(GREEN)Full clean complete.$(NC)"
