# PyNotebookLM Makefile
# Cross-platform development commands
# 
# Primary target: Linux/WSL
# Secondary: Windows (via WSL or Git Bash)
#
# Usage:
#   make setup                - Initialize Poetry environment and dependencies
#   make check                - Run all checks (lint, typecheck, test)
#   make test                 - Run all tests
#   make test-unit            - Run unit tests only
#   make test-integration     - Run integration tests only
#   make test-cov             - Run tests with coverage
#   make lint                 - Run linting
#   make lint-fix             - Fix linting issues
#   make typecheck            - Run type checking
#   make format               - Format code with black
#   make build                - Build distribution package
#   make clean                - Remove build artifacts

.PHONY: setup test test-unit test-integration test-cov lint lint-fix typecheck format check build clean help

# Default Python command
PYTHON ?= poetry run python

help:
	@echo "PyNotebookLM Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make setup                - Initialize Poetry environment and dependencies"
	@echo "  make setup-playwright     - Install Playwright browsers"
	@echo ""
	@echo "Quality Checks (via poetry run):"
	@echo "  make test                 - Run all tests"
	@echo "  make test-unit            - Run unit tests only"
	@echo "  make test-integration     - Run integration tests only"
	@echo "  make test-cov             - Run tests with coverage"
	@echo "  make lint                 - Check linting (no changes)"
	@echo "  make lint-fix             - Fix linting issues"
	@echo "  make typecheck            - Run type checking"
	@echo "  make format               - Format code with black"
	@echo "  make check                - Run all checks (lint, typecheck, test)"
	@echo ""
	@echo "Build:"
	@echo "  make build                - Build distribution package"
	@echo "  make clean                - Remove build artifacts"

# Setup development environment
setup:
	@poetry install
	@echo "✅ Dependencies installed!"
	@echo "Run 'make setup-playwright' to install Playwright browsers"

# Install Playwright browsers
setup-playwright:
	@poetry run playwright install chromium
	@echo "✅ Playwright browsers installed!"

# Run all tests
test:
	@$(PYTHON) -m pytest tests/ -v --tb=short

# Run unit tests only
test-unit:
	@$(PYTHON) -m pytest tests/unit/ -v --tb=short

# Run integration tests only
test-integration:
	@$(PYTHON) -m pytest tests/integration/ -v --tb=short

# Run tests with coverage (90% total, 80% per-file threshold)
test-cov:
	@$(PYTHON) -m pytest tests/ -v --cov=src/pynotebooklm --cov-report=term-missing --cov-report=html --cov-report=json
	@$(PYTHON) scripts/check_coverage.py --total 90 --file 80
	@echo "📊 Coverage report: htmlcov/index.html"

# Run linting (check only)
lint:
	@$(PYTHON) -m ruff check src tests
	@$(PYTHON) -m ruff format --check src tests
	@echo "✅ Linting passed!"

# Run linting with auto-fix
lint-fix:
	@$(PYTHON) -m ruff check src tests --fix
	@$(PYTHON) -m ruff format src tests
	@echo "✅ Linting fixed!"

# Run type checking
typecheck:
	@$(PYTHON) -m mypy src --show-error-codes
	@echo "✅ Type checking passed!"

# Format code with black
format:
	@$(PYTHON) -m black src tests
	@echo "✅ Formatting done!"

# Run all checks
check: lint typecheck test
	@echo ""
	@echo "🎉 All checks passed!"

# Build distribution
build:
	@rm -rf dist/ build/ *.egg-info/
	@poetry build
	@echo "✅ Build complete! See dist/"

# Clean build artifacts
clean:
	rm -rf dist/ build/ *.egg-info/
	rm -rf .pytest_cache/ .mypy_cache/ .ruff_cache/
	rm -rf htmlcov/ .coverage coverage.json
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Cleaned!"

# Bump version
# Usage: make bump-version 0.1.1
SUPPORTED_COMMANDS := bump-version
SUPPORTS_MAKE_ARGS := $(findstring $(firstword $(MAKECMDGOALS)), $(SUPPORTED_COMMANDS))
ifneq "$(SUPPORTS_MAKE_ARGS)" ""
  VERSION_ARG := $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))
  $(eval $(VERSION_ARG):;@:)
endif

bump-version:
	@if [ -z "$(VERSION_ARG)" ]; then echo "Error: version argument required (e.g. make bump-version 0.1.1)"; exit 1; fi
	@poetry version $(VERSION_ARG)
	@sed -i 's/__version__ = "[^"]*"/__version__ = "$(VERSION_ARG)"/' src/pynotebooklm/__init__.py
	@echo "✅ Version bumped to $(VERSION_ARG)"

