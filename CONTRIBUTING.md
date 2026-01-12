# Contributing to PyNotebookLM

Thanks for contributing! This guide outlines the workflow for changes and releases.

## Development Setup

1. Install dependencies:
   ```bash
   poetry install
   ```
2. Install Playwright browsers:
   ```bash
   make setup-playwright
   ```

## Quality Checks

- Run unit tests:
  ```bash
  make test-unit
  ```
- Run full test suite with coverage:
  ```bash
  make test-cov
  ```
- Run linting and type checks:
  ```bash
  make check
  ```

## Style Guidelines

- Python formatting uses Black; linting uses Ruff.
- Type hints are required; MyPy runs in strict mode.
- Keep code changes focused and add tests for new behavior.

## Documentation

- Update `README.md` for user-facing changes.
- Update `docs/` for API or workflow changes.

## Pull Request Process

1. Create a feature branch from `main`.
2. Ensure tests and checks pass locally.
3. Include a concise summary and any relevant context in the PR description.

## Code of Conduct

Please be respectful and constructive in all interactions.
