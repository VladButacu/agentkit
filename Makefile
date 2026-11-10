.DEFAULT_GOAL := help
.PHONY: help test update uninstall

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "} {printf "  %-8s %s\n", $$1, $$2}'

test: ## Run ruff, then the installer and prose-linter test suites
	ruff check scripts skills/prose/scripts
	python3 scripts/test_install.py
	python3 skills/prose/scripts/test_unslop_lint.py

update: ## Pull upstream and re-run the installer with the remembered plugin selection
	git pull --ff-only
	sh install.sh

uninstall: ## Remove agentkit wiring from every tool; user content and caches stay
	python3 scripts/install.py --uninstall
