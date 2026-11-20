.DEFAULT_GOAL := help
.PHONY: help test update uninstall

PYTHON ?= python3

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "} {printf "  %-10s %s\n", $$1, $$2}'

test: ## Run ruff and pyright, then the installer, obsidian feature, prose-linter, generator and ticket and layout test suites
	ruff check scripts features/obsidian/scripts skills/writing/scripts skills/design/scripts skills/repo-ops/scripts
	pyright
	$(PYTHON) -m unittest discover -s scripts -p 'test_*.py'
	$(PYTHON) -m unittest discover -s features/obsidian/scripts -p 'test_*.py'
	$(PYTHON) skills/writing/scripts/prose/test_unslop_lint.py
	$(PYTHON) -m unittest discover -s skills/repo-ops/scripts/makefile-generator -p 'test_*.py'
	$(PYTHON) -m unittest discover -s skills/repo-ops/scripts/pyproject-generator -p 'test_*.py'
	$(PYTHON) -m unittest discover -s skills/design/scripts/to-tickets -p 'test_*.py'
	$(PYTHON) -m unittest discover -s skills/repo-ops/scripts/repo-bootstrap -p 'test_*.py'

update: ## Checkout the newest release tag and reinstall with the remembered plugin selection
	git fetch --tags origin
	git checkout --detach $$(git describe --tags --abbrev=0 origin/main)
	sh install.sh

uninstall: ## Remove agentkit wiring from every tool; user content and caches stay
	$(PYTHON) scripts/install.py --uninstall
