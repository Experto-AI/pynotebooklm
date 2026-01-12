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
 
 ## Phase 5: Chat, Writing & Tone ✅ COMPLETE
 
 **Milestone:** User can write the blog post with specific tone handling
 
 ### Query & Writer Engine
 - [x] Create `src/pynotebooklm/chat.py` (or add to `notebooks.py`):
   - [x] `ChatSession.query(notebook_id, question)` - write text (`notebook_query`)
   - [x] `ChatSession.configure(notebook_id, config)` - set tone/style (`chat_configure`)
   - [x] `ChatSession.get_citation(citation_id)` - retrieve refs
   - [x] `ChatSession.get_notebook_summary(notebook_id)` (`notebook_describe`)
   - [x] `ChatSession.get_source_summary(notebook_id, source_id)` (`source_describe`)
   - [x] `ChatSession.create_briefing(notebook_id)` - generate structured blog/brief (`briefing_create`)
   - [x] `ChatSession.list_artifacts(notebook_id)` - list studio artifacts
 
 ### CLI Implementation
 - [x] Update `src/pynotebooklm/cli.py`:
   - [x] Add `pynotebooklm query ask <notebook_id> <question>`
   - [x] Add `pynotebooklm query configure <notebook_id>` (Set tone)
   - [x] Add `pynotebooklm query summary <notebook_id>`
   - [x] Add `pynotebooklm query briefing <notebook_id>`
   - [x] Add `pynotebooklm studio list <notebook_id>`
 
 ### Testing
 - [x] Create `tests/integration/test_chat.py`
 
 ### Phase 5 Verification
 - [x] `make test-integration-chat` passes
 - [x] `pynotebooklm query configure <notebook_id> --style "Professional Blog"` updates settings
 - [x] `pynotebooklm query ask <notebook_id> "Write a blog post based on the sources"` returns text
 - [x] `pynotebooklm query briefing <notebook_id>`
 - [x] `pynotebooklm query summary <notebook_id>` 
 
 ---
 
 ## Phase 6: Multi-modal Content Generation
 
 **Milestone:** User can generate Audio, Video, Slides, and Infographics (Optional for Blog)
 
 **Key insight (from jacob-bd/notebooklm-mcp analysis, 2026-01-10):**
 All studio content uses the same RPC `R7cb6c` with different type codes:
 - `STUDIO_TYPE_AUDIO = 1` - Audio Overviews (podcasts)
 - `STUDIO_TYPE_VIDEO = 3` - Video Overviews
 - `STUDIO_TYPE_INFOGRAPHIC = 7` - Infographics
 - `STUDIO_TYPE_SLIDE_DECK = 8` - Slide Decks
 
 ### RPC Details (from analysis_repos/jacob-bd-notebooklm-mcp):
 - `R7cb6c` = Create Studio Content
   - Audio params: `[[2], notebook_id, [None, None, 1, sources_nested, None, None, [None, [focus, length, None, sources_simple, lang, None, format]]]]`
   - Video params: `[[2], notebook_id, [None, None, 3, sources_nested, None, None, None, None, [None, None, [sources_simple, lang, focus, None, format, style]]]]`
   - Infographic params: `[[2], notebook_id, [None, None, 7, sources_nested, ...10 nulls..., [[focus, lang, None, orientation, detail_level]]]]`
   - Slide deck params: `[[2], notebook_id, [None, None, 8, sources_nested, ...12 nulls..., [[focus, lang, format, length]]]]`
 - `gArtLc` = Poll Studio Status
   - Params: `[[2], notebook_id, 'NOT artifact.status = "ARTIFACT_STATUS_SUGGESTED"']`
   - Status codes: 1=in_progress, 3=completed
 - `V5N4be` = Delete Studio Artifact
   - Params: `[[2], artifact_id]`
 
 ### Audio Options:
 | Option | Values |
 |--------|--------|
 | **Formats** | 1=Deep Dive (conversation), 2=Brief, 3=Critique, 4=Debate |
 | **Lengths** | 1=Short, 2=Default, 3=Long |
 | **Languages** | BCP-47 codes: "en", "es", "fr", "de", "ja", etc. |
 
 ### Video Options:
 | Option | Values |
 |--------|--------|
 | **Formats** | 1=Explainer, 2=Brief |
 | **Visual Styles** | 1=Auto-select, 2=Custom, 3=Classic, 4=Whiteboard, 5=Kawaii, 6=Anime, 7=Watercolor, 8=Retro print, 9=Heritage, 10=Paper-craft |
 | **Languages** | BCP-47 codes |
 
 ### Infographic Options:
 | Option | Values |
 |--------|--------|
 | **Orientations** | 1=Landscape (16:9), 2=Portrait (9:16), 3=Square (1:1) |
 | **Detail Levels** | 1=Concise, 2=Standard, 3=Detailed |
 | **Languages** | BCP-47 codes |
 
 ### Slide Deck Options:
 | Option | Values |
 |--------|--------|
 | **Formats** | 1=Detailed Deck, 2=Presenter Slides |
 | **Lengths** | 1=Short, 3=Default |
 | **Languages** | BCP-47 codes |
 
 ### Content Generator
 - [x] Create `src/pynotebooklm/content.py`:
   - [x] `ContentGenerator.__init__(session)` - Initialize with BrowserSession
   - [x] `ContentGenerator.create_audio(notebook_id, source_ids, format, length, language, focus)` - RPC: `R7cb6c` type=1
   - [x] `ContentGenerator.create_video(notebook_id, source_ids, format, style, language, focus)` - RPC: `R7cb6c` type=3
   - [x] `ContentGenerator.create_infographic(notebook_id, source_ids, orientation, detail, language, focus)` - RPC: `R7cb6c` type=7
   - [x] `ContentGenerator.create_slides(notebook_id, source_ids, format, length, language, focus)` - RPC: `R7cb6c` type=8
   - [x] `ContentGenerator.poll_status(notebook_id)` - RPC: `gArtLc`
   - [x] `ContentGenerator.delete(artifact_id)` - RPC: `V5N4be`
   - [x] Add Pydantic models: `AudioFormat`, `VideoFormat`, `VideoStyle`, `InfographicOrientation`, `SlideDeckFormat`
   - [x] Add `StudioArtifact` result model with type-specific URLs
 
 ### CLI Implementation
 - [x] Update `src/pynotebooklm/cli.py`:
   - [x] Add `generate_app` typer group
   - [x] Add `pynotebooklm generate audio <notebook_id> [--format] [--length] [--language] [--focus]`
   - [x] Add `pynotebooklm generate video <notebook_id> [--format] [--style] [--language] [--focus]`
   - [x] Add `pynotebooklm generate infographic <notebook_id> [--orientation] [--detail] [--language] [--focus]`
   - [x] Add `pynotebooklm generate slides <notebook_id> [--format] [--length] [--language] [--focus]`
   - [x] Add `pynotebooklm studio status <notebook_id>` - Show all artifacts with status
   - [x] Add `pynotebooklm studio delete <artifact_id>` - Delete artifact (with confirmation)
 
 ### Testing
 - [x] Create `tests/unit/test_content.py`:
   - [x] Test audio creation with all format/length combinations (12 tests)
   - [x] Test video creation with format/style combinations (16 tests)
   - [x] Test infographic creation (9 tests)
   - [x] Test slide deck creation (4 tests)
   - [x] Test poll_status parsing (5 tests)
   - [x] Test delete artifact (3 tests)
   - [x] Test error handling (5 tests)
   - [x] Total: ~54 new unit tests
 - [x] Create `tests/unit/test_cli_content.py`:
   - [x] Test CLI commands for all content types (8 tests)
 
 ### Phase 6 Verification
 - [x] `make check` passes
 - [x] `pynotebooklm generate audio <notebook_id>` triggers generation
 - [x] `pynotebooklm generate video <notebook_id>` triggers generation
 - [x] `pynotebooklm studio status <notebook_id>` shows progress
 - [x] `pynotebooklm studio delete <artifact_id>` deletes artifact
 
 ---
 
 ## Phase 7: Study Tools
 
 **Milestone:** User can generate additional study aids
 
 **Key insight (from jacob-bd/notebooklm-mcp analysis, 2026-01-10):**
 Study tools use the same `R7cb6c` RPC with different type codes:
 - `STUDIO_TYPE_FLASHCARDS = 4` - Flashcards (shares type with Quiz)
 - `STUDIO_TYPE_DATA_TABLE = 9` - Data Tables
 
 Quiz uses the same type code 4 as flashcards, differentiated by options structure.
 
 ### RPC Details (from analysis_repos/jacob-bd-notebooklm-mcp/docs/API_REFERENCE.md):
 - `R7cb6c` = Create Studio Content (same RPC as audio/video/infographics)
 
 **Flashcard params:**
 ```
 [[2], notebook_id, [null, null, 4, sources_nested, null*5, [null, [1, null*5, [difficulty, card_count]]]]]
 ```
 - Difficulty codes: 1=Easy, 2=Medium, 3=Hard
 - Card count: 2=Default
 
 **Quiz params (same type code 4, format code 2 distinguishes it):**
 ```
 [[2], notebook_id, [null, null, 4, sources_nested, null*5, [null, [2, null*6, [question_count, difficulty]]]]]
 ```
 - Format code 2 at first position indicates Quiz (vs 1 for Flashcards)
 - Question count: Integer (default: 2)
 - Difficulty: Integer (default: 2)
 
 **Data Table params:**
 ```
 [[2], notebook_id, [null, null, 9, sources_nested, null*14, [null, [description, language]]]]
 ```
 - Description: Required string describing what data to extract
 - Language: BCP-47 code (default: "en")
 
 ### Study Manager
 - [x] Create `src/pynotebooklm/study.py`:
   - [x] Add Pydantic models: `FlashcardDifficulty`, `FlashcardCreateResult`, `QuizCreateResult`, `DataTableCreateResult`
   - [x] `StudyManager.__init__(session)` - Initialize with BrowserSession
   - [x] `StudyManager.create_flashcards(notebook_id, source_ids, difficulty, card_count)` - RPC: `R7cb6c` type=4
   - [x] `StudyManager.create_quiz(notebook_id, source_ids, question_count, difficulty)` - RPC: `R7cb6c` type=4, format=2
   - [x] `StudyManager.create_data_table(notebook_id, source_ids, description, language)` - RPC: `R7cb6c` type=9
   - Note: `briefing_create` already implemented in Phase 5 (chat.py)
   - Note: Results can be polled via `ContentGenerator.poll_status()` as they use same studio system
 
 ### Difficulty/Option Enums
 | Option | Values |
 |--------|--------|
 | **Flashcard Difficulty** | easy (1), medium (2), hard (3) |
 | **Quiz Question Count** | Integer (default: 2) |
 | **Quiz Difficulty** | Integer (default: 2) |
 | **Data Table Language** | BCP-47 codes: "en", "es", "fr", etc. |
 
 ### CLI Implementation
 - [x] Update `src/pynotebooklm/cli.py`:
   - [x] Add `study_app` typer group
   - [x] Add `pynotebooklm study flashcards <notebook_id> [--difficulty easy|medium|hard]`
   - [x] Add `pynotebooklm study quiz <notebook_id> [--questions N] [--difficulty N]`
   - [x] Add `pynotebooklm study table <notebook_id> --description "..." [--language en]`
 
 ### Testing
 - [x] Create `tests/unit/test_study.py`:
   - [x] Test flashcard creation with all difficulty levels (6 tests)
   - [x] Test quiz creation options
   - [x] Test data table creation
 - [x] Create `tests/unit/test_cli_study.py`
 - [x] Verify coverage > 80% (aiming for 90%)
 - [x] Run `make check`
 - [x] Update documentation
 
 ### Phase 7 Verification
 - [x] `make check` passes
 - [x] `pynotebooklm study flashcards <notebook_id>` triggers generation
 - [x] `pynotebooklm study quiz <notebook_id>` triggers generation
 - [x] `pynotebooklm study table <notebook_id> --description "..."` triggers generation
 - [x] `pynotebooklm studio status <notebook_id>` shows study artifacts
 
 ---
 
 ## Phase 8: Production Readiness ✅ COMPLETE
 
 **Milestone:** Library is pip-installable, documented, and Dockerized
 
 ### Client Unification
 - [x] Create `src/pynotebooklm/client.py`:
   - [x] Unified `NotebookLMClient` exposing all managers
   - [x] Async context manager support
   - [x] `NotebookLMClient.save_auth_tokens()` (`save_auth_tokens`)
 
 ### CLI Polish
 - [x] Ensure all commands have nice output (spinners, tables)
 - [x] Add `[tool.poetry.scripts]` entry
 
 ### Docker Support
 - [x] Create `Dockerfile` & `docker-compose.yml`
 
 ### Documentation
 - [x] Create complete `docs/` structure (index, quickstart, api-ref)
 - [x] Configure `mkdocs`
 
 ### Global Verification
 - [x] `pip install .` works
 - [x] Full test suite passes
 - [x] Docker container runs
 
 ---
 
 ## Phase 9: Research Import Feature
 
 **Milestone:** User can automatically import discovered research sources into notebook
 
 **Problem:** When creating research (deep or standard), the discovered sources are not 
 automatically joined to the notebook. In the web UI, users must "click a button" to import 
 them. This phase adds a CLI command and enhanced workflow to automate this.
 
 ### Key insight (from jacob-bd/notebooklm-mcp analysis, 2026-01-10):
 Research in NotebookLM is a 3-step process:
 1. **Start Research** - `Ljjv0c` (fast) or `QA9ei` (deep) - discovers web/drive sources
 2. **Poll Results** - `e3bVqc` - wait until status=completed, get discovered sources
 3. **Import Sources** - `LBwxtb` - explicitly adds sources to the notebook
 
 The `import_research_sources()` method exists in `research.py` but has no CLI command.
 
 ### RPC Details (from API_REFERENCE.md):
 - `LBwxtb` = Import Research Sources
   - Params: `[null, [1], task_id, notebook_id, [sources]]`
   - Each web source: `[null, null, ["url", "title"], null x8, 2]`
   - Each drive source: `[[doc_id, mime_type, 1, title], null x9, 2]`
   - Response: Array of created sources with source_id, title
 
 ### Research Import CLI
 - [x] Add `pynotebooklm research import <notebook_id>` command:
   - [x] Poll research, verify completed
   - [x] Import all discovered sources (or specific ones with `--indices`)
   - [x] For deep research, optionally import report as text source
   - [x] Show import summary with count and URLs
 
 ### Enhanced Workflow (Optional)
 - [x] Add `--auto-import` flag to `research poll`:
   - [x] If research completed, automatically imports sources
   - [x] Shows combined status + import result
 
 ### Testing
 - [x] Create `tests/unit/test_cli_research.py`:
   - [x] Test research import command with all inputs
   - [x] Test import with specific indices
   - [x] Test import of deep research with report
   - [x] Test error handling (not completed, no research)
 - [x] Add to `tests/unit/test_research.py`:
   - [x] Test import_research_sources method
 - [x] Verify coverage > 90%
 
 ### Phase 9 Verification
 - [x] `make check` passes
 - [x] `pynotebooklm research import <notebook_id>` imports all sources
 - [x] `pynotebooklm research import <notebook_id> --indices 0,1,2` imports specific sources
 - [x] `pynotebooklm research poll <notebook_id> --auto-import` polls and auto-imports
 - [x] Sources appear in notebook after import
 
 ---
 
 ## Phase 10: Stabilization & Optimization
 
 **Milestone:** High reliability, improved performance, and ecosystem integration
 
 ### Reliability Improvements
 
 #### Exponential Backoff for RPC Calls
 - [x] Create `src/pynotebooklm/retry.py`:
   - [x] `RetryStrategy` class with configurable max_attempts, base_delay, max_delay
   - [x] `with_retry()` decorator for async functions
   - [x] Exponential backoff algorithm with jitter
   - [x] Retry on transient errors (APIError with 5xx, RateLimitError)
   - [x] Do not retry on AuthenticationError or NotebookNotFoundError
 - [x] Update `BrowserSession.call_rpc()`:
   - [x] Wrap call with `@with_retry()` decorator
   - [x] Log retry attempts at INFO level
 - [x] Add configuration via environment variables:
   - [x] `PYNOTEBOOKLM_MAX_RETRIES` (default: 3)
   - [x] `PYNOTEBOOKLM_BASE_DELAY` (default: 1.0 seconds)
   - [x] `PYNOTEBOOKLM_MAX_DELAY` (default: 60.0 seconds)
 
#### Automatic Cookie Refresh
- [x] Update `BrowserSession`:
  - [x] Add `_check_auth_validity()` method to detect expired cookies
  - [x] Detect "accounts.google.com" redirects during RPC calls
  - [x] Add `auto_refresh: bool` parameter to constructor (default: False)
  - [x] When auth fails and auto_refresh=True:
    - [x] Call `auth.refresh()` to re-login
    - [x] Recreate browser context with new cookies
    - [x] Retry failed RPC call once
- [x] Update `AuthManager`:
  - [x] Add `is_expired()` method to check cookie age
  - [x] Add `refresh_threshold` (default: 14 days)
  - [x] Log warning when cookies are close to expiration
 
#### Enhanced Error Handling
- [x] Improve streaming response parsing in `session.py`:
  - [x] Handle partial/incomplete JSON responses gracefully
  - [x] Add timeout for streaming endpoints (default: 120s)
  - [x] Better error messages for malformed responses
- [x] Add request/response logging:
  - [x] Create `PYNOTEBOOKLM_DEBUG` environment variable
  - [x] Log full request payloads when enabled
  - [x] Log full response bodies when enabled
  - [x] Sanitize sensitive data (cookies, tokens) in logs
- [x] Add telemetry and metrics (optional):
  - [x] Track RPC call durations
  - [x] Track success/failure rates
  - [x] Export to structured logs (JSON format)
 
 ### Performance Optimizations
 
#### Browser Startup Time
- [x] Implement persistent browser context:
  - [x] Add `PersistentBrowserSession` class
  - [x] Reuse single browser instance across multiple operations
  - [x] Add context pooling for concurrent requests
- [x] Optimize Playwright configuration:
  - [x] Disable unnecessary browser features (images, CSS when not needed)
  - [x] Use faster page load strategies (`--disable-extensions`)
- [x] Add caching for CSRF tokens:
  - [x] Cache token for 5 minutes
  - [x] Refresh token only when expired
 
#### Batch Operations
- [x] Add batch notebook operations:
  - [x] `NotebookManager.batch_delete(notebook_ids)` - delete multiple notebooks
  - [x] `SourceManager.batch_add_urls(notebook_id, urls)` - add multiple URLs
  - [x] Parallel RPC calls with asyncio.gather()
- [x] Optimize research polling:
  - [x] Add `poll_with_backoff()` - exponential backoff between polls
  - [x] Configurable poll interval (default: 5s)
 
 ### Code Examples & Documentation
 
 #### Library Usage Examples
 - [x] Create `examples/` directory:
   - [x] `examples/01_basic_usage.py` - Create notebook, add sources, query
   - [x] `examples/02_research_workflow.py` - Start research, poll, import sources
   - [x] `examples/03_content_generation.py` - Generate audio, video, slides
   - [x] `examples/04_study_tools.py` - Create flashcards, quiz, data tables
   - [x] `examples/05_mind_maps.py` - Generate and export mind maps
   - [x] `examples/06_batch_operations.py` - Process multiple notebooks
   - [x] `examples/07_error_handling.py` - Proper exception handling patterns
 - [x] Each example must include:
   - [x] Docstring explaining the use case
   - [x] Error handling with try/except
   - [x] Rich console output (using `rich` library)
 
#### Automation Scripts
- [x] Create `scripts/automation/`:
  - [x] `scripts/automation/research_pipeline.py` - End-to-end research automation
  - [x] `scripts/automation/content_batch_generator.py` - Generate content for multiple notebooks
  - [x] `scripts/automation/backup_notebooks.py` - Export all notebooks to JSON
  - [x] `scripts/automation/cleanup_old_artifacts.py` - Delete old studio artifacts
- [x] Add README for each script with usage instructions
 
 #### Documentation Updates
 - [x] Create `docs/advanced_usage.md`:
   - [x] Retry strategies and error handling
   - [x] Persistent sessions for performance
   - [x] Batch operations best practices
 - [x] Create `docs/faq.md`:
   - [x] Common errors and solutions
   - [x] Cookie expiration handling
   - [x] Rate limiting guidance
 - [x] Create `docs/examples.md`:
   - [x] Link to all example files
   - [x] Explained code walkthroughs
 - [x] Update `docs/api_reference.md`:
   - [x] Add all Phase 6-9 APIs
   - [x] Include retry and error handling options
 
 ### Testing & Quality
 
 #### Retry Logic Tests
 - [x] Create `tests/unit/test_retry.py`:
   - [x] Test exponential backoff calculation
   - [x] Test retry on transient errors
   - [x] Test no retry on permanent errors
   - [x] Test max attempts respected
 - [x] Update existing tests to mock retries
 
#### Integration Tests for Edge Cases
- [x] Create `tests/integration/test_reliability.py`:
  - [x] Test cookie expiration handling
  - [x] Test rate limit recovery
  - [x] Test network timeout handling
 
 ### Publishing & Release
 
#### PyPI Release Preparation
- [x] Update `pyproject.toml`:
  - [x] Verify all dependencies and version constraints
  - [x] Add project URLs (homepage, documentation, repository, issues)
  - [x] Add classifiers (Python 3.10+, Development Status, License)
  - [x] Add keywords for discoverability
- [x] Create `CHANGELOG.md`:
  - [x] Document all changes from v0.1.0
  - [x] Follow Keep a Changelog format
  - [x] Include breaking changes, new features, bug fixes
- [x] Create `CONTRIBUTING.md`:
  - [x] Development setup instructions
  - [x] Code style guidelines
  - [x] Pull request process
  - [x] Code of conduct
- [x] Update `README.md`:
  - [x] Add PyPI installation badge
  - [x] Add documentation link
  - [x] Add quick start section
  - [x] Add troubleshooting section
- [x] Create GitHub Release workflow:
  - [x] `.github/workflows/release.yml` for automated PyPI publishing
  - [x] Triggered on version tags (v*)
  - [x] Build and publish to PyPI using trusted publishing
- [x] Create documentation site:
  - [x] Deploy mkdocs to GitHub Pages
  - [x] Update `.github/workflows/docs.yml`
 
 ### Phase 10 Verification
 - [x] `make check` passes with all new code
 - [x] Coverage remains above 90%
 - [ ] All examples run successfully
 - [ ] Documentation is complete and accurate
 - [x] Package builds successfully: `poetry build`
 - [x] Package installs from dist: `pip install dist/*.whl`
 - [x] All CLI commands work after install
 
 ---
