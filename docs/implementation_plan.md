<!--
DOCUMENTATION SCOPE: This file contains the detailed implementation roadmap broken down by phases.
DO NOT include here: Daily TODOs (use TODO.md) or architectural decisions.
-->

# Implementation Plan

This document outlines the phased implementation plan for the `pynotebooklm` library.

## Phase 1: Foundation & Project Setup
**Goal:** User can authenticate and see cookies saved.
**Status:** ✅ Complete

### Key Components
- Project structure and dependencies (Poetry, Playwright).
- `AuthManager` for handling Google login and cookie persistence.
- `BrowserSession` for managing the Playwright context.
- CI/CD pipeline setup.

### Verification
- Unit tests pass: `pytest tests/unit/ -v`
- Manual auth works: `pynotebooklm auth login`

## Phase 2: Notebook & Source Management
**Goal:** User can create notebook, add sources, and list them.
**Status:** ✅ Complete

### Key Components
- `NotebookLMAPI`: Low-level RPC wrapper.
- `NotebookManager`: High-level CRUD for notebooks.
- `SourceManager`: Handling URL, Text, and Drive sources.
- Integration tests against real NotebookLM.

### Verification
- Integration tests pass: `make test-integration`
- CLI commands verify functionality:
  ```bash
  pynotebooklm notebooks list
  pynotebooklm notebooks create "My Project"
  pynotebooklm sources add <id> "https://example.com"
  pynotebooklm notebooks delete <id>
  ```

## Phase 3: Content Generation
**Goal:** User can generate a podcast from a notebook.
**Status:** 🚧 Planned

### Key Components
- `ContentGenerator` class.
- Support for Audio (Podcast), Video, Infographic, and Slides.
- Async polling mechanism for long-running generation tasks.

### Verification
- `pytest tests/integration/test_content.py`
- Manual test: Generate a deep dive podcast and download the audio.

## Phase 4: Research & Analysis
**Goal:** User can query notebook and import research.
**Status:** 🚧 Planned

### Key Components
- `ResearchDiscovery` class.
- Query/Chat interface with citation parsing.
- Web and Drive research capabilities.
- Streaming response handling.

### Verification
- `pytest tests/integration/test_research.py`
- Manual test: Ask a question to a notebook and verify citations.

## Phase 5: Mind Maps & Advanced Features
**Goal:** All 31 tools implemented and tested.
**Status:** 🚧 Planned

### Key Components
- `MindMapGenerator`: Create and export mind maps.
- `StudyTools`: Flashcards, Quizzes, Briefings.
- Studio management (delete artifacts).

### Verification
- `pytest tests/integration/test_mindmaps.py`
- `pytest tests/integration/test_study.py`

## Phase 6: Production Readiness
**Goal:** Library is pip-installable and documented.
**Status:** 🚧 Planned

### Key Components
- Unified `NotebookLMClient`.
- Complete CLI interface.
- Docker support (`Dockerfile`, `docker-compose.yml`).
- Comprehensive documentation (`mkdocs`).

### Verification
- `pip install .` works.
- Docker container runs successfully.
- Documentation is live and accurate.
