# Contributing

Contributions are welcome! Please follow these steps to set up your development environment.

## Development Setup

1. **Clone the repository:**

   ```bash
   git clone https://github.com/victor/pynotebooklm.git
   cd pynotebooklm
   ```

2. **Install dependencies using Poetry:**

   ```bash
   poetry install
   ```

3. **Install Playwright browsers:**

   ```bash
   poetry run playwright install chromium
   ```

## Running Tests

Run the full test suite:

```bash
make check
```

Or individual tests:

```bash
poetry run pytest tests/unit/
```

## Linting and Formatting

We use `ruff` for linting and `black` for formatting.

```bash
poetry run ruff check src tests
poetry run black src tests
poetry run mypy src
```

## Adding New Features

If you want to add support for a new NotebookLM tool:

1. Identify the RPC ID and payload structure (see `docs/internal_protocol.md`).
2. Add the corresponding method to `src/pynotebooklm/api.py`.
3. Create or update a manager/service class.
4. Add CLI commands in `src/pynotebooklm/cli.py`.
5. Add unit and integration tests.
