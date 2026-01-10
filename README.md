# PyNotebookLM

<!--
📄 DOCUMENTATION SCOPE: This file is the user-facing README for the project. It should contain:
- Installation instructions, quick start guides, and usage examples
- Feature highlights and CLI command references
- How-to-run development commands (tests, linting, etc.)
- Project structure overview for end users

DO NOT include here: Detailed implementation plans, architectural decisions, or internal technical details. Those belong in `docs/architecture.md` and `docs/implementation_plan.md`.
-->

[![CI](https://img.shields.io/github/actions/workflow/status/victor/pynotebooklm/ci.yml?branch=main)](https://github.com/victor/pynotebooklm/actions)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

Production-grade Python library for **Google NotebookLM** automation.

## Features

- 🔐 **Secure Authentication** - Browser-based Google login with cookie persistence
- 📓 **Notebook Management** - Create, list, rename, and delete notebooks
- 📰 **Source Management** - Add URLs, YouTube videos, Google Drive docs, and text
- 🔍 **Research & Analysis** - Query notebooks and discover related sources
- 🧠 **Mind Maps** - Generate, save, list, and export mind maps (JSON/OPML/FreeMind)
- 🎙️ **Content Generation** - Create audio overviews (podcasts), videos, infographics, and slides
- 📚 **Study Tools** - Create flashcards, quizzes, and briefing documents (coming soon)

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

### Authentication

```bash
pynotebooklm auth login              # Login with Google account (opens browser)
pynotebooklm auth check              # Check authentication status
pynotebooklm auth logout             # Clear saved authentication
```

### Notebooks

```bash
pynotebooklm notebooks list                        # List all notebooks
pynotebooklm notebooks list --detailed             # With source count and dates
pynotebooklm notebooks create "My Notebook"        # Create a new notebook
pynotebooklm notebooks delete <notebook_id>        # Delete a notebook
pynotebooklm notebooks delete <notebook_id> -f     # Delete without confirmation
```

### Sources

```bash
pynotebooklm sources list <notebook_id>                    # List sources in notebook
pynotebooklm sources add <notebook_id> <url>               # Add URL source
pynotebooklm sources delete <notebook_id> <source_id>      # Delete a source
pynotebooklm sources delete <notebook_id> <source_id> -f   # Delete without confirmation
```

### Research Discovery

```bash
pynotebooklm research start <notebook_id> "topic"              # Fast web research
pynotebooklm research start <notebook_id> "topic" --deep       # Deep research (more comprehensive)
pynotebooklm research start <notebook_id> "topic" --source drive   # Search Google Drive
pynotebooklm research poll <notebook_id>                       # Check status and get results
```

### Mind Maps

```bash
pynotebooklm mindmap create <notebook_id>                      # Create from all sources
pynotebooklm mindmap create <notebook_id> --title "My Map"     # With custom title
pynotebooklm mindmap list <notebook_id>                        # List existing maps
pynotebooklm mindmap export <notebook_id> <map_id> -f json     # Export to JSON
pynotebooklm mindmap export <notebook_id> <map_id> -f opml     # Export to OPML
pynotebooklm mindmap export <notebook_id> <map_id> -f freemind # Export to FreeMind (.mm)
```

### Chat & Query

```bash
pynotebooklm query ask <notebook_id> "question"                # Ask a question
pynotebooklm query summary <notebook_id>                       # Get AI summary
pynotebooklm query briefing <notebook_id>                      # Create briefing document
pynotebooklm query configure <notebook_id> --goal learning     # Set conversation goal
pynotebooklm query configure <notebook_id> --length longer     # Set response length
```

### Content Generation

```bash
# Audio Overview (Podcast)
pynotebooklm generate audio <notebook_id>                      # Generate with defaults
pynotebooklm generate audio <notebook_id> --format deep_dive   # Format: deep_dive, brief, critique, debate
pynotebooklm generate audio <notebook_id> --length short       # Length: short, default, long
pynotebooklm generate audio <notebook_id> --language es        # Language: en, es, fr, de, ja, etc.
pynotebooklm generate audio <notebook_id> --focus "key topics" # Focus prompt for AI

# Video Overview
pynotebooklm generate video <notebook_id>                      # Generate with defaults
pynotebooklm generate video <notebook_id> --format explainer   # Format: explainer, brief
pynotebooklm generate video <notebook_id> --style anime        # Style: auto_select, classic, whiteboard, kawaii, anime, watercolor, retro_print, heritage, paper_craft

# Infographic
pynotebooklm generate infographic <notebook_id>                    # Generate with defaults
pynotebooklm generate infographic <notebook_id> --orientation portrait  # Orientation: landscape, portrait, square
pynotebooklm generate infographic <notebook_id> --detail detailed  # Detail: concise, standard, detailed

# Slide Deck
pynotebooklm generate slides <notebook_id>                         # Generate with defaults
pynotebooklm generate slides <notebook_id> --format presenter_slides  # Format: detailed_deck, presenter_slides
pynotebooklm generate slides <notebook_id> --length short          # Length: short, default
```

### Studio (Artifact Management)

```bash
pynotebooklm studio list <notebook_id>             # List all artifacts (Briefings, Audio, Video, etc.)
pynotebooklm studio status <notebook_id>           # Detailed status with download URLs
pynotebooklm studio delete <artifact_id>           # Delete an artifact (with confirmation)
pynotebooklm studio delete <artifact_id> --force   # Delete without confirmation
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
├── src/pynotebooklm/
│   ├── __init__.py        # Public API exports
│   ├── auth.py            # Authentication manager
│   ├── session.py         # Browser session management
│   ├── api.py             # Low-level RPC wrapper
│   ├── notebooks.py       # Notebook management
│   ├── sources.py         # Source management
│   ├── research.py        # Research discovery
│   ├── mindmaps.py        # Mind map generation
│   ├── content.py         # Content generation (audio, video, etc.)
│   ├── chat.py            # Chat and query functionality
│   ├── models.py          # Pydantic data models
│   ├── exceptions.py      # Custom exceptions
│   └── cli.py             # CLI interface
├── tests/
│   ├── unit/              # Unit tests (457)
│   ├── integration/       # Integration tests (192)
│   └── fixtures/          # Mock responses
└── docs/                  # Documentation
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
- [x] **Phase 2**: Notebook & Source Management
- [x] **Phase 3**: Research Discovery
- [x] **Phase 4**: Mind Maps
- [x] **Phase 5**: Chat, Writing & Tone
- [x] **Phase 6**: Content Generation (Audio, Video, Infographics, Slides)
- [ ] **Phase 7**: Study Tools
- [ ] **Phase 8**: Production Readiness

## License

Apache License 2.0 - see [LICENSE](LICENSE) for details.

## Disclaimer

This is an unofficial library. It uses NotebookLM's internal APIs which may change without notice. Use at your own risk.
