# PyNotebookLM Scripts

Utility scripts for development and release management.

## Available Scripts

### Version Management

- **`bump_version.py`** - Synchronize version numbers across `pyproject.toml` and `src/pynotebooklm/__init__.py`
  ```bash
  # Check version sync status
  python scripts/bump_version.py --check
  
  # Bump to new version
  python scripts/bump_version.py 0.2.0
  ```

### Quality Checks

- **`check_coverage.py`** - Verify test coverage thresholds after running pytest with coverage
  ```bash
  python scripts/check_coverage.py --total 90 --file 80
  ```

### Documentation

- **`validate_links.py`** - Validate links in markdown documentation (for when `docs/` is added)
  ```bash
  python scripts/validate_links.py
  ```

## Recommended Usage

Most development commands are wrapped by the `Makefile` for convenience:

```bash
make setup              # Install dependencies
make setup-playwright   # Install Playwright browsers
make check              # Run all checks (lint, typecheck, test)
make test               # Run all tests
make test-unit          # Run unit tests only
make test-cov           # Run tests with coverage
make lint               # Check linting
make typecheck          # Run type checking
make build              # Build package
```
