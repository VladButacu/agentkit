.DEFAULT_GOAL := help
.PHONY: help test update uninstall

PYTHON ?= python3

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "} {printf "  %-10s %s\n", $$1, $$2}'

test: ## Run ruff, then the installer, vault plugin and prose-linter test suites
	ruff check scripts plugins/obsidian/scripts skills/prose/scripts
	$(PYTHON) -m unittest discover -s scripts -p 'test_*.py'
	$(PYTHON) -m unittest discover -s plugins/obsidian/scripts -p 'test_*.py'
	$(PYTHON) skills/prose/scripts/test_unslop_lint.py

update: ## Pull upstream and re-run the installer with the remembered plugin selection
	git pull --ff-only
	sh install.sh

uninstall: ## Remove agentkit wiring from every tool; user content and caches stay
	$(PYTHON) scripts/install.py --uninstall
