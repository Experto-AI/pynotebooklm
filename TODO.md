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

**Key insight:** Research in NotebookLM is always performed in the context of a notebook.
Results are stored on NotebookLM's servers and persist in the notebook automatically.

### Bug Fix (2026-01-10) ✅ RESOLVED
**Problem:** Research appeared to "work" (returned quickly) but nothing showed up in NotebookLM.
**Root Cause:** RPC payload structure was incorrect. Fixed based on `jacob-bd/notebooklm-mcp`:
- Fast Research (`Ljjv0c`): `[[query, source_type], None, 1, notebook_id]`
- Deep Research (`QA9ei`): `[None, [1], [query, source_type], 5, notebook_id]`
- Source types: 1=web, 2=drive

**Research is async!** Returns a `task_id`, poll with `e3bVqc` to get results.

### Research Discovery
- [x] Create `src/pynotebooklm/research.py`:
  - [x] `ResearchDiscovery.start_research(notebook_id, query, source, mode)` - RPC: `Ljjv0c` (fast), `QA9ei` (deep)
  - [x] `ResearchDiscovery.poll_research(notebook_id)` - RPC: `e3bVqc` to get async results
  - [x] `ResearchDiscovery.import_research_sources(notebook_id, task_id, sources)` - RPC: `LBwxtb`
  - [x] Backward-compatible `start_web_research()` wrapper

### CLI Implementation
- [x] Update `src/pynotebooklm/cli.py`:
  - [x] Add `pynotebooklm research start <notebook_id> <topic> [--deep] [--source web|drive]`
  - [x] Add `pynotebooklm research poll <notebook_id>` - poll for results

### Testing
- [x] Create `tests/integration/test_research.py` (updated with 29 new tests)

### Phase 3 Verification
- [x] `make check` passes (275 tests)
- [x] CLI commands implemented and functional
- [x] **MANUAL TEST REQUIRED:** `pynotebooklm research start <notebook_id> "topic"` → verify in NotebookLM web UI

### Notes (from UI Investigation 2026-01-09)
- **Drive Sync**: Per-source operation (via source context menu), not notebook-wide. Move to sources module if needed.
- **Topic Suggestions**: Generated as part of chat responses, not separate RPC. Move to Phase 5 (Chat).
 
 
 ---
 
 ## Phase 4: Mind Maps ✅ COMPLETE
 
 **Milestone:** User can visualize research connections before writing
 
 **Key insight (from jacob-bd/notebooklm-mcp analysis, 2026-01-10):**
 Mind maps use a **2-step creation process**:
 1. **Generate**: RPC `yyryJe` creates the mind map JSON structure from sources
 2. **Save**: RPC `CYK0Xb` saves the generated JSON to a notebook
 
 ### RPC Details (from analysis_repos/jacob-bd-notebooklm-mcp/docs/API_REFERENCE.md):
 - `yyryJe` = Generate Mind Map
   - Params: `[sources_nested, None, None, None, None, ["interactive_mindmap", [["[CONTEXT]", ""]], ""], None, [2, None, [1]]]`
   - `sources_nested`: `[[[source_id1]], [[source_id2]], ...]`
   - Response: `[json_mind_map_string, None, [generation_id1, generation_id2, generation_number]]`
 - `CYK0Xb` = Save Mind Map
   - Params: `[notebook_id, json_mind_map_string, [2, None, None, 5, [[source_id1], [source_id2]]], None, "Mind Map Title"]`
   - Response: `[mind_map_id, saved_json, metadata, None, saved_title]`
 - `cFji9` = List Mind Maps
   - Params: `[notebook_id]`
   - Response: `[[[mind_map_id, [id, json, metadata, None, title]], ...], [timestamp]]`
 
 ### Mind Map JSON Structure:
 ```json
 {"name": "Root Topic", "children": [
   {"name": "Category 1", "children": [
     {"name": "Subcategory 1.1"},
     {"name": "Subcategory 1.2"}
   ]},
   {"name": "Category 2", "children": [...]}
 ]}
 ```
 
 ### Mind Map Generator
 - [x] Create `src/pynotebooklm/mindmaps.py`:
   - [x] `MindMapGenerator.__init__(session)` - Initialize with BrowserSession
   - [x] `MindMapGenerator.generate(source_ids)` - RPC: `yyryJe` (Step 1: generates JSON)
   - [x] `MindMapGenerator.save(notebook_id, mind_map_json, source_ids, title)` - RPC: `CYK0Xb` (Step 2: saves to notebook)
   - [x] `MindMapGenerator.create(notebook_id, source_ids, title)` - Convenience wrapper (generate + save)
   - [x] `MindMapGenerator.list(notebook_id)` - RPC: `cFji9`
   - [x] `MindMapGenerator.get(notebook_id, mindmap_id)` - Get specific mind map from list
   - [x] `export_to_opml(mind_map_json)` - Convert JSON to OPML format (standalone function)
   - [x] `export_to_freemind(mind_map_json)` - Convert JSON to FreeMind XML (standalone function)
   - [x] Add Pydantic models: `MindMap`, `MindMapNode`, `MindMapGenerateResult`
 
 ### CLI Implementation
 - [x] Update `src/pynotebooklm/cli.py`:
   - [x] Add `mindmap_app` typer group
   - [x] Add `pynotebooklm mindmap create <notebook_id> [--title]` (auto-uses all sources)
   - [x] Add `pynotebooklm mindmap list <notebook_id>`
   - [x] Add `pynotebooklm mindmap export <notebook_id> <mindmap_id> --format json|opml|freemind [--output]`
 
 ### Testing
 - [x] Create `tests/integration/test_mindmaps.py`:
   - [x] Test generate, save, create flow (5 tests)
   - [x] Test list mind maps (5 tests)
   - [x] Test export to different formats (10 tests)
   - [x] Test error handling (empty sources, invalid notebook, etc.)
   - [x] Create `tests/unit/test_cli_mindmap.py` for CLI coverage
   - [x] Total: 38 new integration tests + CLI unit tests
 
 ### Phase 4 Verification
 - [x] `make check` passes (362 tests total)
 - [x] `pynotebooklm mindmap create <notebook_id>` implemented
 - [x] `pynotebooklm mindmap list <notebook_id>` implemented
 - [x] `pynotebooklm mindmap export <notebook_id> <mindmap_id> --format opml` implemented
 
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
