# PyNotebookLM TODO - Actionable Checklist Roadmap

<!--
✅ DOCUMENTATION SCOPE: This file is the actionable task checklist for development. It should contain:
- Phase-based TODO items with checkboxes for tracking progress
- Specific implementation tasks (create files, write functions, tests)
- Verification steps for each phase
- Current work-in-progress items

DO NOT include here: Architectural rationale, detailed technical explanations, or design decisions. Those belong in plan.md. Keep this file focused on "what needs to be done" not "why" or "how".
-->

## Phase 1: Foundation & Project Setup ✅ COMPLETE

**Milestone:** User can authenticate and see cookies saved

### Project Setup
- [x] Initialize Poetry project with `pyproject.toml`
- [x] Configure dependencies: playwright, pydantic v2, httpx, asyncio
- [x] Set up linting: ruff, mypy (strict mode)
- [x] Set up formatting: black, isort
- [x] Create `.github/workflows/ci.yml` for CI/CD
- [x] Create `README.md` with basic project description

### Core Models
- [x] Create `src/pynotebooklm/__init__.py` with public API exports
- [x] Create `src/pynotebooklm/models.py`:
  - [x] `Notebook` model
  - [x] `Source` model
  - [x] `Artifact` model
  - [x] `ChatMessage` model
  - [x] Request/Response models for each operation
- [x] Create `src/pynotebooklm/exceptions.py`:
  - [x] `PyNotebookLMError` (base)
  - [x] `AuthenticationError`
  - [x] `NotebookNotFoundError`
  - [x] `SourceError`
  - [x] `GenerationError`
  - [x] `GenerationTimeoutError`
  - [x] `RateLimitError`
  - [x] `APIError`

### Authentication
- [x] Create `src/pynotebooklm/auth.py`:
  - [x] `AuthManager.__init__()` - load existing cookies
  - [x] `AuthManager.login()` - open browser for user login
  - [x] `AuthManager.is_authenticated()` - check cookie validity
  - [x] `AuthManager.get_cookies()` - return cookies for session
  - [x] `AuthManager.refresh()` - refresh/re-extract cookies
  - [x] `AuthManager._save_cookies()` - persist to `~/.pynotebooklm/auth.json`
  - [x] `AuthManager._load_cookies()` - load from file

### Browser Session
- [x] Create `src/pynotebooklm/session.py`:
  - [x] `BrowserSession.__aenter__()` - launch Playwright, inject cookies
  - [x] `BrowserSession.__aexit__()` - close browser
  - [x] `BrowserSession.call_api()` - execute fetch via page.evaluate()
  - [x] `BrowserSession._extract_csrf_token()` - get token from page HTML

### Testing
- [x] Create `tests/unit/test_auth.py`
- [x] Create `tests/unit/test_session.py`
- [x] Create `tests/fixtures/mock_cookies.json`

### Phase 1 Verification
- [x] `poetry run pytest tests/unit/ -v` passes (85 tests)
- [x] `poetry run python -m pynotebooklm.auth login` opens browser
- [x] `poetry run python -m pynotebooklm.auth check` shows authentication status
- [ ] `~/.pynotebooklm/auth.json` file exists with cookies (requires manual login)

---

## Phase 2: Notebook & Source Management ✅ COMPLETE

**Milestone:** User can create notebook, add sources, and list them

### Low-Level API
- [x] Create `src/pynotebooklm/api.py`:
  - [x] `NotebookLMAPI.__init__()` - initialize with session
  - [x] `NotebookLMAPI.list_notebooks()` - list all notebooks
  - [x] `NotebookLMAPI.create_notebook()` - create new notebook
  - [x] `NotebookLMAPI.get_notebook()` - get notebook details
  - [x] `NotebookLMAPI.rename_notebook()` - rename notebook
  - [x] `NotebookLMAPI.delete_notebook()` - delete notebook
  - [x] `NotebookLMAPI.add_url_source()` - add URL source
  - [x] `NotebookLMAPI.add_youtube_source()` - add YouTube source
  - [x] `NotebookLMAPI.add_text_source()` - add text source
  - [x] `NotebookLMAPI.add_drive_source()` - add Drive source
  - [x] `NotebookLMAPI.delete_source()` - delete source
  - [x] `NotebookLMAPI.list_drive_docs()` - list Drive docs
  - [x] Response parsing utilities (`parse_notebook_response`, `parse_source_response`)

### Notebook Manager
- [x] Create `src/pynotebooklm/notebooks.py`:
  - [x] `NotebookManager.list()` - RPC ID: `wXbhsf`
  - [x] `NotebookManager.create(name)` - RPC ID: `CCqFvf`
  - [x] `NotebookManager.get(notebook_id)` - get details
  - [x] `NotebookManager.rename(notebook_id, new_name)`
  - [x] `NotebookManager.delete(notebook_id, confirm=False)`
  - [x] `NotebookManager.exists(notebook_id)` - check existence

### Source Manager
- [x] Create `src/pynotebooklm/sources.py`:
  - [x] `SourceManager.add_url(notebook_id, url)` - RPC ID: `izAoDd`
  - [x] `SourceManager.add_youtube(notebook_id, url)` - auto-detect YouTube URLs
  - [x] `SourceManager.add_drive(notebook_id, doc_id)`
  - [x] `SourceManager.add_text(notebook_id, content, title)`
  - [x] `SourceManager.list_sources(notebook_id)` - list sources in notebook
  - [x] `SourceManager.delete(notebook_id, source_id)`
  - [x] `SourceManager.list_drive()` - list available Drive docs

### Testing
- [x] Create `tests/integration/test_notebooks.py` (17 tests)
- [x] Create `tests/integration/test_sources.py` (23 tests)
- [x] Create `tests/fixtures/mock_rpc_responses.py`

### Phase 2 Verification
- [x] `make test-integration` passes (all notebook & source tests)
- [x] `poetry run python -m pynotebooklm notebooks list`
- [x] `poetry run python -m pynotebooklm notebooks create "My Project"`
- [x] `poetry run python -m pynotebooklm notebooks delete <id>`
- [x] `poetry run python -m pynotebooklm sources list <notebook_id>`
- [x] `poetry run python -m pynotebooklm sources add <notebook_id> "https://example.com"`

---

## Phase 3: Content Generation

**Milestone:** User can generate a podcast from a notebook

### Content Generator
- [ ] Create `src/pynotebooklm/content.py`:
  - [ ] `ContentGenerator.generate_podcast(notebook_id, style)` - RPC ID: `R7cb6c`
  - [ ] `ContentGenerator.generate_video(notebook_id, style)`
  - [ ] `ContentGenerator.generate_infographic(notebook_id, orientation)`
  - [ ] `ContentGenerator.generate_slides(notebook_id)`
  - [ ] `ContentGenerator.get_status(artifact_id)` - RPC ID: `gArtLc`
  - [ ] `ContentGenerator._poll_until_ready()` - exponential backoff polling

### Polling Implementation
- [ ] Implement exponential backoff (2s → 3s → 4.5s → 10s max)
- [ ] Handle timeout (default 300s)
- [ ] Handle generation failure status
- [ ] Return download URL when ready

### Testing
- [ ] Create `tests/integration/test_content.py`
- [ ] Test with timeout handling
- [ ] Test with mock status responses

### Phase 3 Verification
- [ ] `make test-integration-content` passes (once tests created)
- [ ] `pynotebooklm generate podcast <notebook_id>` starts generation
- [ ] `pynotebooklm generate status <artifact_id>` checks progress
- [ ] Download URL is provided once generation is 100%

---

## Phase 4: Research & Analysis

**Milestone:** User can query notebook and import research

### Research Discovery
- [ ] Create `src/pynotebooklm/research.py`:
  - [ ] `ResearchDiscovery.query(notebook_id, question)` - ask question
  - [ ] `ResearchDiscovery.describe(notebook_id)` - AI summary of notebook
  - [ ] `ResearchDiscovery.describe_source(notebook_id, source_id)` - source summary
  - [ ] `ResearchDiscovery.start_web_research(topic)` - start discovery
  - [ ] `ResearchDiscovery.start_drive_research(topic)` - search Drive
  - [ ] `ResearchDiscovery.get_research_status(research_id)`
  - [ ] `ResearchDiscovery.import_sources(notebook_id, source_ids)`
  - [ ] `ResearchDiscovery.sync_drive_sources(notebook_id)` - refresh Drive docs
  - [ ] `ResearchDiscovery.configure_chat(notebook_id, config)` - set chat style

### Streaming Response Handling
- [ ] Handle streaming chat responses
- [ ] Accumulate chunks until complete
- [ ] Parse citations from response

### Testing
- [ ] Create `tests/integration/test_research.py`

### Phase 4 Verification
- [ ] `make test-integration-research` passes
- [ ] `pynotebooklm query <notebook_id> "What is this about?"` returns answer
- [ ] `pynotebooklm research start "Topic"` returns a research ID
- [ ] Citations are included in the query response

---

## Phase 5: Mind Maps & Advanced Features

**Milestone:** All 31 tools implemented and tested

### Mind Map Generator
- [ ] Create `src/pynotebooklm/mindmaps.py`:
  - [ ] `MindMapGenerator.create(notebook_id)`
  - [ ] `MindMapGenerator.list(notebook_id)`
  - [ ] `MindMapGenerator.export_xml(mindmap_id)` - FreeMind format
  - [ ] `MindMapGenerator.export_opml(mindmap_id)` - OPML format

### Study Tools
- [ ] Create `src/pynotebooklm/study.py`:
  - [ ] `StudyTools.create_flashcards(notebook_id, difficulty)`
  - [ ] `StudyTools.create_quiz(notebook_id, question_count)`
  - [ ] `StudyTools.create_briefing(notebook_id)`
  - [ ] `StudyTools.create_data_table(notebook_id)`

### Studio Management
- [ ] Add `ContentGenerator.delete(artifact_id)` - delete generated content
- [ ] Add `AuthManager.save_tokens()` - explicitly save auth state

### Testing
- [ ] Create `tests/integration/test_mindmaps.py`
- [ ] Create `tests/integration/test_study.py`

### Phase 5 Verification
- [ ] `make test-integration-mindmaps` passes
- [ ] `make test-integration-study` passes
- [ ] `pynotebooklm mindmaps list <notebook_id>` lists mind maps
- [ ] `pynotebooklm study flashcards <notebook_id>` returns flashcards

---

## Phase 6: Production Readiness

**Milestone:** Library is pip-installable and documented

### Client Unification
- [ ] Create `src/pynotebooklm/client.py`:
  - [ ] `NotebookLMClient.__init__()` - initialize all managers
  - [ ] `NotebookLMClient.__aenter__()` - async context manager
  - [ ] `NotebookLMClient.__aexit__()` - cleanup
  - [ ] Expose `notebooks`, `sources`, `content`, `research`, `mindmaps`, `study`

### CLI Interface
- [x] Create `src/pynotebooklm/cli.py` with Typer base
- [x] Phase 1: `pynotebooklm auth login|check|logout`
- [x] Phase 2: `pynotebooklm notebooks list|create|delete`
- [x] Phase 2: `pynotebooklm sources add|list`
- [ ] Phase 3: `pynotebooklm generate podcast <notebook_id>`
- [ ] Phase 4: `pynotebooklm query <notebook_id> <question>`
- [ ] Add `[tool.poetry.scripts]` entry in pyproject.toml

### Docker Support
- [ ] Create `Dockerfile`:
  - [ ] Base image with Python 3.11
  - [ ] Install Playwright and browsers
  - [ ] Volume mount for `~/.pynotebooklm`
- [ ] Create `docker-compose.yml`
- [ ] Test headless operation in container

### Documentation
- [ ] Create `docs/index.md` - overview
- [ ] Create `docs/quickstart.md` - getting started
- [ ] Create `docs/authentication.md` - auth setup
- [ ] Create `docs/api-reference.md` - full API docs
- [ ] Create `docs/tools.md` - all 31 tools explained
- [ ] Create `docs/examples.md` - usage examples
- [ ] Configure `mkdocs.yml`

### Examples
- [ ] Create `examples/basic_usage.py`
- [ ] Create `examples/podcast_generation.py`
- [ ] Create `examples/research_workflow.py`
- [ ] Create `examples/batch_processing.py`

### Final Testing
- [ ] Run full test suite with coverage
- [ ] Ensure 80%+ code coverage
- [ ] Test installation via `pip install .`
- [ ] Test CLI commands work
- [ ] Test Docker build and run

### Phase 6 Verification
- [ ] `pip install .` works
- [ ] `pynotebooklm --version` shows version
- [ ] `pynotebooklm notebooks list` works
- [ ] `docker build -t pynotebooklm .` succeeds
- [ ] `mkdocs serve` shows documentation

---

## Post-Release

### Maintenance
- [ ] Set up daily CI tests against real NotebookLM (detect API changes)
- [ ] Create CHANGELOG.md
- [ ] Tag v1.0.0 release
- [ ] Publish to PyPI

### DeterminAgent Integration (Separate Project)
- [ ] Create `NotebookLMAdapter` class
- [ ] Map all 31 tools to adapter methods
- [ ] Implement sync/async bridge
- [ ] Add to DeterminAgent ADAPTERS registry
- [ ] Write integration tests
