# PyNotebookLM TODO - Actionable Checklist Roadmap

<!--
✅ DOCUMENTATION SCOPE: This file is the actionable task checklist for development. It should contain:
- Phase-based TODO items with checkboxes for tracking progress
- Specific implementation tasks (create files, write functions, tests)
- Verification steps for each phase
- Current work-in-progress items

DO NOT include here: Architectural rationale, detailed technical explanations, or design decisions. Those belong in `docs/architecture.md` and `docs/implementation_plan.md`. Keep this file focused on "what needs to be done" not "why" or "how".
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

## Phase 3: Research Discovery ✅ COMPLETE
 
 **Milestone:** User can perform web searches and gather sources for the blog
 
 ### Research Discovery
 - [x] Create `src/pynotebooklm/research.py`:
   - [x] `ResearchDiscovery.start_web_research(topic)` (`research_start`)
   - [x] `ResearchDiscovery.get_status(research_id)` (`research_status`)
   - [x] `ResearchDiscovery.import_research_results(notebook_id, results)` (`research_import`)
   - [x] `ResearchDiscovery.sync_drive_sources(notebook_id)` (`source_sync_drive`)
   - [x] `ResearchDiscovery.suggest_topics(notebook_id)`
 
 ### CLI Implementation
 - [x] Update `src/pynotebooklm/cli.py`:
   - [x] Add `pynotebooklm research start <topic>`
   - [x] Add `pynotebooklm research status <research_id>`
   - [x] Add `pynotebooklm research import <notebook_id> <research_id>`
   - [x] Add `pynotebooklm research sync <notebook_id>`
 
 ### Testing
 - [x] Create `tests/integration/test_research.py` (35 tests)
 
 ### Phase 3 Verification
 - [x] `make check` passes (277 tests)
 - [x] `pynotebooklm research start "Latest AI news"` returns research ID
 - [x] `pynotebooklm research status <research_id>` shows findings
 - [x] `pynotebooklm research import <notebook_id> <research_id>` adds sources
 - [x] `pynotebooklm research sync <notebook_id>` updates Drive sources
 
 
 ---
 
 ## Phase 4: Mind Maps
 
 **Milestone:** User can visualize research connections before writing
 
 ### Mind Map Generator
 - [ ] Create `src/pynotebooklm/mindmaps.py`:
   - [ ] `MindMapGenerator.create(notebook_id)` (`mindmap_create`)
   - [ ] `MindMapGenerator.list(notebook_id)` (`mindmap_list`)
   - [ ] `MindMapGenerator.export(notebook_id, format)` - XML/OPML (`mindmap_export_xml/opml`)
 
 ### CLI Implementation
 - [ ] Update `src/pynotebooklm/cli.py`:
   - [ ] Add `pynotebooklm mindmap create <notebook_id>`
   - [ ] Add `pynotebooklm mindmap list <notebook_id>`
   - [ ] Add `pynotebooklm mindmap export <mindmap_id>`
 
 ### Testing
 - [ ] Create `tests/integration/test_mindmaps.py`
 
 ### Phase 4 Verification
 - [ ] `make test-integration-mindmaps` passes
 - [ ] `pynotebooklm mindmap create <notebook_id>` succeeds
 - [ ] `pynotebooklm mindmap list <notebook_id>` shows created maps
 - [ ] `pynotebooklm mindmap export <mindmap_id> --format pdf` saves file
 
 ---
 
 ## Phase 5: Chat, Writing & Tone
 
 **Milestone:** User can write the blog post with specific tone handling
 
 ### Query & Writer Engine
 - [ ] Create `src/pynotebooklm/chat.py` (or add to `notebooks.py`):
   - [ ] `ChatSession.query(notebook_id, question)` - write text (`notebook_query`)
   - [ ] `ChatSession.configure(notebook_id, config)` - set tone/style (`chat_configure`)
   - [ ] `ChatSession.get_citation(citation_id)` - retrieve refs
   - [ ] `ChatSession.get_notebook_summary(notebook_id)` (`notebook_describe`)
   - [ ] `ChatSession.get_source_summary(notebook_id, source_id)` (`source_describe`)
   - [ ] `ChatSession.create_briefing(notebook_id)` - generate structured blog/brief (`briefing_create`)
 
 ### CLI Implementation
 - [ ] Update `src/pynotebooklm/cli.py`:
   - [ ] Add `pynotebooklm query <notebook_id> <question>`
   - [ ] Add `pynotebooklm query configure <notebook_id>` (Set tone)
   - [ ] Add `pynotebooklm query summary <notebook_id>`
   - [ ] Add `pynotebooklm query briefing <notebook_id>`
 
 ### Testing
 - [ ] Create `tests/integration/test_chat.py`
 
 ### Phase 5 Verification
 - [ ] `make test-integration-chat` passes
 - [ ] `pynotebooklm query configure <notebook_id> --style "Professional Blog"` updates settings
 - [ ] `pynotebooklm query <notebook_id> "Write a blog post based on the sources"` returns text
 - [ ] `pynotebooklm query briefing <notebook_id>` returns structured document
 
 ---
 
 ## Phase 6: Multi-modal Content Generation
 
 **Milestone:** User can generate Audio, Video, Slides, and Infographics (Optional for Blog)
 
 ### Content Generator
 - [ ] Create `src/pynotebooklm/content.py`:
   - [ ] `ContentGenerator.generate_audio(notebook_id)` - Podcast (`audio_overview_create`)
   - [ ] `ContentGenerator.generate_video(notebook_id)` - (`video_overview_create`)
   - [ ] `ContentGenerator.generate_infographic(notebook_id)` - (`infographic_create`)
   - [ ] `ContentGenerator.generate_slides(notebook_id)` - (`slide_deck_create`)
   - [ ] `ContentGenerator.get_status(notebook_id)` - (`studio_status`)
   - [ ] `ContentGenerator.get_download_url(notebook_id)`
   - [ ] `ContentGenerator.delete(artifact_id)` - (`studio_delete`)
   - [ ] Implement exponential backoff polling
 
 ### CLI Implementation
 - [ ] Update `src/pynotebooklm/cli.py`:
   - [ ] Add `pynotebooklm generate audio|video|slides|infographic <notebook_id>`
   - [ ] Add `pynotebooklm studio status <notebook_id>`
 
 ### Testing
 - [ ] Create `tests/integration/test_content.py`
 
 ### Phase 6 Verification
 - [ ] `make test-integration-content` passes
 - [ ] `pynotebooklm generate audio <notebook_id>` triggers generation
 - [ ] `pynotebooklm studio status <notebook_id>` shows progress
 
 ---
 
 ## Phase 7: Study Tools
 
 **Milestone:** User can generate additional study aids
 
 ### Study Manager
 - [ ] Create `src/pynotebooklm/study.py`:
   - [ ] `StudyManager.create_flashcards(notebook_id)` (`flashcard_create`)
   - [ ] `StudyManager.create_quiz(notebook_id)` (`quiz_create`)
   - [ ] `StudyManager.create_data_table(notebook_id)` (`data_table_create`)
   - Note: `briefing_create` moved to Phase 5
 
 ### CLI Implementation
 - [ ] Update `src/pynotebooklm/cli.py`:
   - [ ] Add `pynotebooklm study flashcards <notebook_id>`
   - [ ] Add `pynotebooklm study quiz <notebook_id>`
   - [ ] Add `pynotebooklm study table <notebook_id>`
 
 ### Testing
 - [ ] Create `tests/integration/test_study.py`
 
 ### Phase 7 Verification
 - [ ] `make test-integration-study` passes
 - [ ] `pynotebooklm study flashcards <notebook_id>` returns cards
 - [ ] `pynotebooklm study quiz <notebook_id>` returns quiz questions
 
 ---
 
 ## Phase 8: Production Readiness
 
 **Milestone:** Library is pip-installable, documented, and Dockerized
 
 ### Client Unification
 - [ ] Create `src/pynotebooklm/client.py`:
   - [ ] Unified `NotebookLMClient` exposing all managers
   - [ ] Async context manager support
   - [ ] `NotebookLMClient.save_auth_tokens()` (`save_auth_tokens`)
 
 ### CLI Polish
 - [ ] Ensure all commands have nice output (spinners, tables)
 - [ ] Add `[tool.poetry.scripts]` entry
 
 ### Docker Support
 - [ ] Create `Dockerfile` & `docker-compose.yml`
 
 ### Documentation
 - [ ] Create complete `docs/` structure (index, quickstart, api-ref)
 - [ ] Configure `mkdocs`
 
 ### Global Verification
 - [ ] `pip install .` works
 - [ ] Full test suite passes
 - [ ] Docker container runs
 
 ---
 
 ## Post-Release / Future
 
 - [ ] **Phase 9**: Additional content types (Video, Slides - subject to availability)
 - [ ] **Maintenance**: Daily CI checks
 - [ ] **Integration**: DeterminAgent adapter
