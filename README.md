# PyNotebookLM

<!--
📄 DOCUMENTATION SCOPE: This file is the user-facing README for the project. It should contain:
- Installation instructions, quick start guides, and usage examples
- Feature highlights and CLI command references
- How-to-run development commands (tests, linting, etc.)
- Project structure overview for end users

DO NOT include here: Detailed implementation plans, architectural decisions, or internal technical details. Those belong in plan.md.
-->

[![CI](https://img.shields.io/github/actions/workflow/status/victor/pynotebooklm/ci.yml?branch=main)](https://github.com/victor/pynotebooklm/actions)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Production-grade Python library for **Google NotebookLM** automation with 31 tools.

## Features

- 🔐 **Secure Authentication** - Browser-based Google login with cookie persistence
- 📓 **Notebook Management** - Create, list, rename, and delete notebooks
- 📰 **Source Management** - Add URLs, YouTube videos, Google Drive docs, and text
- 🎙️ **Content Generation** - Create podcasts, videos, infographics, and slides
- 🔍 **Research & Analysis** - Query notebooks and discover related sources
- 🧠 **Mind Maps** - Generate and export mind maps
- 📚 **Study Tools** - Create flashcards, quizzes, and briefing documents

## Installation

```bash
pip install pynotebooklm
```

Or with Poetry:

```bash
poetry add pynotebooklm
```

### Install Playwright Browsers

After installing, you need to install the Playwright browser:

```bash
playwright install chromium
```

## Quick Start

### 1. Authenticate

First, login to NotebookLM with your Google account:

```bash
pynotebooklm auth login
```

This opens a browser window for you to login. Cookies are saved to `~/.pynotebooklm/auth.json`.

### 2. Verify Authentication

```bash
pynotebooklm auth check
```

### 3. Use the Library

```python
import asyncio
from pynotebooklm import AuthManager, BrowserSession

async def main():
    auth = AuthManager()
    
    if not auth.is_authenticated():
        print("Please run: pynotebooklm auth login")
        return
    
    async with BrowserSession(auth) as session:
        # List notebooks
        result = await session.call_rpc("wXbhsf", [None, 1, None, [2]])
        print(f"Notebooks: {result}")

asyncio.run(main())
```

## CLI Commands

```bash
# Authentication
pynotebooklm auth login    # Login with Google account
pynotebooklm auth check    # Check authentication status
pynotebooklm auth logout   # Clear saved authentication

# Notebooks (coming in Phase 2)
pynotebooklm notebooks list
pynotebooklm notebooks create "My Notebook"
pynotebooklm notebooks delete <notebook_id>

# Sources (coming in Phase 2)
pynotebooklm sources add <notebook_id> <url>

# Content Generation (coming in Phase 3)
pynotebooklm generate podcast <notebook_id>
```

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/victor/pynotebooklm.git
cd pynotebooklm

# Install dependencies
poetry install

# Install Playwright browsers
poetry run playwright install chromium
```

### Running Tests

```bash
# Run all unit tests
poetry run pytest tests/unit/ -v

# Run with coverage
poetry run pytest tests/unit/ -v --cov=src/pynotebooklm

# Run specific test file
poetry run pytest tests/unit/test_auth.py -v
```

### Linting and Formatting

```bash
# Lint with ruff
poetry run ruff check src tests

# Format with black
poetry run black src tests

# Type check with mypy
poetry run mypy src
```

## Project Structure

```
pynotebooklm/
├── src/
│   └── pynotebooklm/
│       ├── __init__.py        # Public API exports
│       ├── auth.py            # Authentication manager
│       ├── session.py         # Browser session management
│       ├── models.py          # Pydantic data models
│       ├── exceptions.py      # Custom exceptions
│       └── cli.py             # CLI interface (coming soon)
├── tests/
│   ├── unit/                  # Unit tests
│   ├── integration/           # Integration tests
│   └── fixtures/              # Test fixtures
├── pyproject.toml             # Project configuration
└── README.md
```

## How It Works

PyNotebookLM uses browser automation (Playwright) to interact with NotebookLM's internal APIs:

1. **Authentication**: Opens a browser for Google login, extracts cookies
2. **Session**: Creates a headless browser session with injected cookies
3. **API Calls**: Executes `fetch()` requests via `page.evaluate()` in browser context
4. **RPC Protocol**: Communicates using NotebookLM's internal RPC format

This approach provides:
- ✅ Full feature access (all 31 tools)
- ✅ No API keys needed
- ✅ Works with consumer Google accounts
- ⚠️ Requires browser automation
- ⚠️ Cookie refresh needed every 2-4 weeks

## Roadmap

- [x] **Phase 1**: Foundation & Authentication
- [ ] **Phase 2**: Notebook & Source Management
- [ ] **Phase 3**: Content Generation (Podcasts, Videos)
- [ ] **Phase 4**: Research & Analysis
- [ ] **Phase 5**: Mind Maps & Study Tools
- [ ] **Phase 6**: CLI & Production Readiness

## License

MIT License - see [LICENSE](LICENSE) for details.

## Disclaimer

This is an unofficial library. It uses NotebookLM's internal APIs which may change without notice. Use at your own risk.
