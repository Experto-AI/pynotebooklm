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

## Phase 3: Research Discovery
**Goal:** User can perform web searches and gather sources.
**Status:** ✅ Complete

### Key Components
- `ResearchDiscovery` class (`src/pynotebooklm/research.py`).
- `start_research()`, `poll_research()`, `import_research_sources()`.
- Backward-compatible `start_web_research()` wrapper.
- Research is async; `start_research()` returns a `task_id`, `poll_research()` returns results.
- CLI commands: `research start`, `research poll`.

### Verification
- `pytest tests/integration/test_research.py`.
- CLI: `pynotebooklm research start <notebook_id> "topic"` returns task ID.
- CLI: `pynotebooklm research poll <notebook_id>` shows status and results.
- CLI: `pynotebooklm research import <notebook_id>` imports discovered sources to notebook.

## Phase 4: Mind Maps
**Goal:** User can visualize research connections.
**Status:** ✅ Complete

### Key Components
- `MindMapGenerator` class.
- Create, list, and export mind maps (XML/OPML).

### Verification
- `pytest tests/integration/test_mindmaps.py`

## Phase 5: Chat, Writing & Tone
**Goal:** User can write blog posts with specific tone.
**Status:** ✅ Complete

### Key Components
- `ChatSession` for querying notebooks.
- Tone/style configuration.
- Briefing document generation.

### Verification
- `pytest tests/integration/test_chat.py`

## Phase 6: Multi-modal Content Generation
**Goal:** Generate Audio, Video, Slides, Infographics.
**Status:** ✅ Complete

### Key Components
- `ContentGenerator` class for all content types.
- Async polling for long-running tasks with `poll_status()`.
- Studio artifact management with `delete()`.
- CLI commands: `generate audio`, `generate video`, `generate infographic`, `generate slides`.
- Studio management: `studio status`, `studio delete`, `studio list`.

### Verification
- `pytest tests/unit/test_content.py` (54 tests)
- CLI commands documented in README.md

## Phase 7: Study Tools
**Goal:** Generate flashcards, quizzes, and data tables.
**Status:** ✅ Complete

### Key Components
- `StudyManager` class.
- CLI commands: `study flashcards`, `study quiz`, `study table`.

### Verification
- `pytest tests/unit/test_study.py`

## Phase 8: Production Readiness
**Goal:** Library is pip-installable and documented.
**Status:** ✅ Complete

### Key Components
- Unified `NotebookLMClient`.
- Docker support.
- Documentation (`mkdocs`).

### Verification
- `pip install .` works.
- Docker container runs.

## Phase 9: Research Import Feature
**Goal:** User can automatically import discovered research sources into notebook.
**Status:** ✅ Complete

### Key Components
- `research import` CLI command for explicit source import.
- `--auto-import` flag for `research poll` command.
- Deep research report import as text source.
- Support for `--indices` to import specific sources.

### Verification
- `pytest tests/unit/test_cli_research.py` (20 tests)
- CLI: `pynotebooklm research import <notebook_id>` imports sources.
- CLI: `pynotebooklm research poll <notebook_id> --auto-import` polls and imports.

## Phase 10: Stabilization & Optimization
**Goal:** High reliability, improved performance, and ecosystem integration.
**Status:** 🚧 In Progress

### Key Components

#### Reliability Improvements
- **Exponential Backoff**: `retry.py` module with `RetryStrategy` class and `with_retry()` decorator.
- **Automatic Cookie Refresh**: Enhanced `BrowserSession` and `AuthManager` to detect and refresh expired cookies.
- **Enhanced Error Handling**: Better streaming response parsing, debug logging via `PYNOTEBOOKLM_DEBUG`.

#### Performance Optimizations
- **Persistent Browser Context**: `PersistentBrowserSession` class to reuse browser instances.
- **CSRF Token Caching**: Cache tokens for 5 minutes to avoid repeated extraction.
- **Batch Operations**: `batch_delete()`, `batch_add_urls()`, and parallel RPC calls.

#### Examples & Documentation
- **Library Examples**: 7 complete examples covering basic usage, research, content generation, study tools, mind maps, batch operations, and error handling.
- **Automation Scripts**: Research pipeline, content batch generator, notebook backup, and artifact cleanup.
- **Advanced Documentation**: `advanced_usage.md`, `faq.md`, `examples.md` with comprehensive guides.

#### Publishing & Release
- **PyPI Preparation**: Updated `pyproject.toml`, `CHANGELOG.md`, `CONTRIBUTING.md`.
- **GitHub Release Workflow**: Automated publishing on version tags.
- **Documentation Site**: Deploy mkdocs to GitHub Pages.

### Verification
- All existing tests pass (`make check`).
- Coverage remains >90%.
- Examples run successfully.
- Performance benchmarks: browser startup <500ms, RPC latency <200ms.
- Package installs and CLI works: `pip install dist/*.whl`.
