.DEFAULT_GOAL := help
.PHONY: help test update uninstall

PYTHON ?= python3

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "} {printf "  %-10s %s\n", $$1, $$2}'

test: ## Run ruff, then the installer, vault plugin, prose-linter and generator test suites
	ruff check scripts plugins/obsidian/scripts skills/prose/scripts skills/makefile-generator/scripts skills/pyproject-generator/scripts
	$(PYTHON) -m unittest discover -s scripts -p 'test_*.py'
	$(PYTHON) -m unittest discover -s plugins/obsidian/scripts -p 'test_*.py'
	$(PYTHON) skills/prose/scripts/test_unslop_lint.py
	$(PYTHON) -m unittest discover -s skills/makefile-generator/scripts -p 'test_*.py'
	$(PYTHON) -m unittest discover -s skills/pyproject-generator/scripts -p 'test_*.py'

update: ## Checkout the newest release tag and reinstall with the remembered plugin selection
	git fetch --tags origin
	git checkout --detach $$(git describe --tags --abbrev=0 origin/main)
	sh install.sh

uninstall: ## Remove agentkit wiring from every tool; user content and caches stay
	$(PYTHON) scripts/install.py --uninstall
