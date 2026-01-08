# PyNotebookLM - Project Documentation

## Executive Summary

**Goal**: Build a production-grade Python library for NotebookLM integration, then wrap it with a DeterminAgent adapter to enable deterministic content creation flows.

**Approach**: Two-phase development

1. **Phase 1**: Build `pynotebooklm` - A standalone Python library (This project)
2. **Phase 2**: Build `NotebookLMAdapter` - A DeterminAgent adapter wrapping the library (Separate project)

**Key Requirements**:

- ✅ All 31 tools from jacob-bd (Content Generation, Source Management, Research, Mind Maps)
- ✅ Production-grade code quality (Pydantic v2, type safety, comprehensive testing)
- ✅ Browser automation for auth and API interaction (Playwright)
- ✅ Deterministic behavior for DeterminAgent workflows
- ✅ Clean architecture with proper separation of concerns

---

## Project Status

### Current Phase: **Phase 1 Complete** ✅

| Phase | Description | Status |
|-------|-------------|--------|
| **Phase 1** | Foundation & Project Setup | ✅ Complete |
| **Phase 2** | Notebook & Source Management | 🔄 Not Started |
| **Phase 3** | Content Generation | ⏳ Planned |
| **Phase 4** | Research & Analysis | ⏳ Planned |
| **Phase 5** | Mind Maps & Advanced Features | ⏳ Planned |
| **Phase 6** | Production Readiness | ⏳ Planned |

### What's Implemented

#### Core Infrastructure ✅

- **`pyproject.toml`** - Poetry configuration with all dependencies
- **`src/pynotebooklm/__init__.py`** - Public API exports
- **`src/pynotebooklm/models.py`** - Pydantic v2 schemas for all data models
- **`src/pynotebooklm/exceptions.py`** - Complete exception hierarchy
- **`src/pynotebooklm/auth.py`** - AuthManager with login/logout/refresh
- **`src/pynotebooklm/session.py`** - BrowserSession with RPC support

#### Testing Infrastructure ✅

- **85 unit tests** passing
- **pytest-asyncio** for async tests
- **Coverage** configured
- **CI/CD** via GitHub Actions

#### CLI Commands ✅

```bash
python -m pynotebooklm.auth login   # Interactive browser login
python -m pynotebooklm.auth check   # Check authentication status
python -m pynotebooklm.auth logout  # Clear saved cookies
```

---

## Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                     User Applications                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Python API   │  │ CLI Tool     │  │ DeterminAgent Adapter│  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└───────────────────────────┬────────────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────────────┐
│                    pynotebooklm Library                        │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                   NotebookLMClient                       │  │
│  │  (Main entry point - combines all managers)              │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────┐    │
│  │ NotebookMgr  │ │ SourceMgr    │ │ ContentGenerator     │    │
│  │ - create     │ │ - add_url    │ │ - audio_podcast      │    │
│  │ - list       │ │ - add_youtube│ │ - video_overview     │    │
│  │ - get        │ │ - add_drive  │ │ - infographic        │    │
│  │ - rename     │ │ - add_text   │ │ - slide_deck         │    │
│  │ - delete     │ │ - delete     │ │ - poll_status        │    │
│  └──────────────┘ └──────────────┘ └──────────────────────┘    │
│                                                                │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────┐    │
│  │ Research     │ │ MindMapGen   │ │ StudyTools           │    │
│  │ - query      │ │ - create     │ │ - flashcards         │    │
│  │ - search_web │ │ - list       │ │ - quiz               │    │
│  │ - import     │ │ - export_xml │ │ - briefing           │    │
│  └──────────────┘ └──────────────┘ └──────────────────────┘    │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                   Core Infrastructure ✅                 │  │
│  │  ┌────────────┐  ┌───────────────┐  ┌─────────────────┐  │  │
│  │  │ AuthMgr ✅ │  │ BrowserSession│  │ NotebookLMAPI   │  │  │
│  │  │ - login    │  │ ✅            │  │ (TODO)          │  │  │
│  │  │ - cookies  │  │ - context mgr │  │ - call_rpc      │  │  │
│  │  │ - refresh  │  │ - page.eval() │  │ - parse_response│  │  │
│  │  └────────────┘  └───────────────┘  └─────────────────┘  │  │
│  └──────────────────────────────────────────────────────────┘  │
└───────────────────────────┬────────────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────────────┐
│                    Browser Layer                               │
│  ┌──────────────────────┐  ┌─────────────────────────────────┐ │
│  │ Playwright/Chromium  │  │ ~/.pynotebooklm/                │ │
│  │ - headless mode      │  │   ├── auth.json (cookies)       │ │
│  │ - cookie injection   │  │   └── chrome_profile/           │ │
│  │ - page.evaluate()    │  │       └── (session persistence) │ │
│  └──────────────────────┘  └─────────────────────────────────┘ │
└───────────────────────────┬────────────────────────────────────┘
                            │
                            ▼
                  ┌───────────────────┐
                  │ NotebookLM Web UI │
                  │ (Google internal  │
                  │  RPC endpoints)   │
                  └───────────────────┘
```

---

## Technology Stack

| Component | Choice | Rationale |
|-----------|--------|-----------|
| **Python** | 3.10+ | Match DeterminAgent requirements |
| **Browser Automation** | Playwright | Python-native, auto-wait, headless performance |
| **Type Safety** | Pydantic v2 | Runtime validation, JSON serialization |
| **Async** | asyncio | Browser ops are async; modern Python |
| **HTTP** | httpx | Async HTTP client |
| **Testing** | pytest + pytest-asyncio | Standard, good async support |
| **Packaging** | Poetry | Modern dependency management |
| **CLI** | Typer | Easy CLI from type hints |
| **Linting** | Ruff | Fast, comprehensive linting |
| **Formatting** | Black + isort | Standard Python formatting |
| **Type Checking** | mypy (strict) | Catch type errors at dev time |

---

## Directory Structure

```
pynotebooklm/
├── src/
│   └── pynotebooklm/
│       ├── __init__.py           # Public API exports ✅
│       ├── auth.py               # AuthManager ✅
│       ├── session.py            # BrowserSession ✅
│       ├── models.py             # Pydantic schemas ✅
│       ├── exceptions.py         # Custom exceptions ✅
│       ├── api.py                # Low-level RPC wrapper (TODO)
│       ├── client.py             # NotebookLMClient (TODO)
│       ├── notebooks.py          # NotebookManager (TODO)
│       ├── sources.py            # SourceManager (TODO)
│       ├── content.py            # ContentGenerator (TODO)
│       ├── research.py           # ResearchDiscovery (TODO)
│       ├── mindmaps.py           # MindMapGenerator (TODO)
│       ├── study.py              # Flashcards, quizzes (TODO)
│       └── cli.py                # CLI interface (TODO)
├── tests/
│   ├── unit/                     # Unit tests ✅
│   │   ├── test_auth.py          ✅
│   │   ├── test_session.py       ✅
│   │   ├── test_models.py        ✅
│   │   └── test_exceptions.py    ✅
│   ├── integration/              # Integration tests (TODO)
│   └── fixtures/                 # Test fixtures ✅
├── docs/                         # mkdocs documentation (TODO)
├── examples/                     # Usage examples (TODO)
├── .github/workflows/ci.yml      # CI/CD ✅
├── pyproject.toml                # Project configuration ✅
├── README.md                     # Project README ✅
├── plan.md                       # Detailed implementation plan
├── decisions.md                  # Architectural decisions
└── TODO.md                       # Actionable checklist
```

---

## Implemented Components

### Models (`src/pynotebooklm/models.py`) ✅

**Enums:**
- `SourceType`: url, youtube, drive, text
- `SourceStatus`: processing, ready, failed
- `ArtifactType`: audio, video, infographic, slides, mindmap, flashcards, briefing, quiz, data_table
- `ArtifactStatus`: pending, generating, ready, failed
- `PodcastStyle`: deep_dive, briefing, learning_guide
- `ChatRole`: user, assistant

**Core Models:**
- `Source`: id, type, title, url, status, created_at
- `Notebook`: id, name, created_at, sources, source_count
- `Artifact`: id, type, status, url, progress, error_message, created_at
- `ChatMessage`: role, content, citations, created_at

**Request/Response Models:**
- `CreateNotebookRequest` / `CreateNotebookResponse`
- `AddSourceRequest` / `AddSourceResponse`
- `GeneratePodcastRequest` / `GeneratePodcastResponse`
- `QueryRequest` / `QueryResponse`
- `GenerateContentRequest` / `GenerateContentResponse`
- `ArtifactStatusRequest` / `ArtifactStatusResponse`

### Exceptions (`src/pynotebooklm/exceptions.py`) ✅

```python
PyNotebookLMError          # Base exception
├── AuthenticationError    # Cookie expired/invalid
├── NotebookNotFoundError  # Notebook doesn't exist
├── SourceError            # Source add/processing failed
├── GenerationError        # Content generation failed
│   └── GenerationTimeoutError  # Generation exceeded timeout
├── RateLimitError         # Too many requests
├── APIError               # Internal API returned error
├── BrowserError           # Playwright launch/navigation failed
└── SessionError           # Session not initialized/closed
```

### AuthManager (`src/pynotebooklm/auth.py`) ✅

```python
class AuthManager:
    def __init__(auth_path: Path | str | None = None, headless: bool = False)
    def is_authenticated() -> bool
    def get_cookies() -> list[dict]
    def get_csrf_token() -> str | None
    async def login(timeout: int = 300)
    async def refresh()
    def logout()
```

**Features:**
- Browser-based Google login with Playwright
- Cookie extraction and persistence to `~/.pynotebooklm/auth.json`
- CSRF token (SNlM0e) extraction from page HTML
- Cookie validity checking (essential cookies: SID, HSID, SSID, APISID, SAPISID)

### BrowserSession (`src/pynotebooklm/session.py`) ✅

```python
class BrowserSession:
    def __init__(auth: AuthManager, headless: bool = True, timeout: int = 30000)
    async def __aenter__() -> BrowserSession
    async def __aexit__(...)
    async def call_rpc(rpc_id: str, params: list[Any], timeout: int | None = None) -> Any
    async def call_api(endpoint: str, method: str = "GET", data: dict | None = None) -> dict
```

**Features:**
- Async context manager for browser lifecycle
- Cookie injection on session start
- RPC payload encoding (Google's batchexecute format)
- Anti-XSSI prefix removal from responses
- CSRF token extraction and usage

---

## Complete Tool Inventory (31 Tools)

### Notebooks (6 tools)
| Tool | Description | Phase | Status |
|------|-------------|-------|--------|
| `notebook_list` | List all notebooks in account | 2 | ⏳ |
| `notebook_create` | Create new notebook with name | 2 | ⏳ |
| `notebook_get` | Get notebook details by ID | 2 | ⏳ |
| `notebook_describe` | AI summary of notebook contents | 4 | ⏳ |
| `notebook_rename` | Rename existing notebook | 2 | ⏳ |
| `notebook_delete` | Delete notebook (requires confirmation) | 2 | ⏳ |

### Sources (7 tools)
| Tool | Description | Phase | Status |
|------|-------------|-------|--------|
| `notebook_add_url` | Add web URL as source | 2 | ⏳ |
| `notebook_add_text` | Add plain text as source | 2 | ⏳ |
| `notebook_add_drive` | Add Google Drive document | 2 | ⏳ |
| `source_describe` | AI summary of single source | 4 | ⏳ |
| `source_list_drive` | List available Drive documents | 2 | ⏳ |
| `source_sync_drive` | Sync/update Drive sources | 4 | ⏳ |
| `source_delete` | Remove source from notebook | 2 | ⏳ |

### Query & Chat (2 tools)
| Tool | Description | Phase | Status |
|------|-------------|-------|--------|
| `notebook_query` | Ask question, get AI answer with citations | 4 | ⏳ |
| `chat_configure` | Set chat style, response length, goals | 4 | ⏳ |

### Research (3 tools)
| Tool | Description | Phase | Status |
|------|-------------|-------|--------|
| `research_start` | Start web/Drive research on topic | 4 | ⏳ |
| `research_status` | Check research discovery progress | 4 | ⏳ |
| `research_import` | Import discovered sources to notebook | 4 | ⏳ |

### Content Generation (7 tools)
| Tool | Description | Phase | Status |
|------|-------------|-------|--------|
| `audio_overview_create` | Generate podcast (deep dive, briefing) | 3 | ⏳ |
| `video_overview_create` | Generate video explainer | 3 | ⏳ |
| `infographic_create` | Generate infographic image | 3 | ⏳ |
| `slide_deck_create` | Generate presentation slides | 3 | ⏳ |
| `studio_status` | Check generation progress | 3 | ⏳ |
| `studio_delete` | Delete generated artifact | 5 | ⏳ |
| `save_auth_tokens` | Explicitly save current auth state | 1 | ✅ |

### Study Tools (4 tools)
| Tool | Description | Phase | Status |
|------|-------------|-------|--------|
| `flashcard_create` | Generate study flashcards | 5 | ⏳ |
| `quiz_create` | Generate quiz questions | 5 | ⏳ |
| `briefing_create` | Generate briefing document | 5 | ⏳ |
| `data_table_create` | Generate data analysis table | 5 | ⏳ |

### Mind Maps (2 tools)
| Tool | Description | Phase | Status |
|------|-------------|-------|--------|
| `mindmap_create` | Generate mind map from sources | 5 | ⏳ |
| `mindmap_list` | List existing mind maps | 5 | ⏳ |

---

## Technical Deep Dives

### NotebookLM Internal API Protocol

**Base URL:** `https://notebooklm.google.com/_/LabsTailwindUi/data/batchexecute`

**Request Format (RPC Protocol):**
```python
# URL-encoded payload
body = f"f.req={urllib.parse.quote(json_payload)}&at={csrf_token}&"

# JSON payload structure
json_payload = json.dumps([
    [[rpc_id, params, None, "generic"]]
], separators=(',', ':'))
```

**Response Parsing:**
```python
# 1. Remove anti-XSSI prefix
content = response.text.removeprefix(")]}'")

# 2. Split byte-delimited lines
lines = content.strip().split('\n')

# 3. Extract data (skip byte count line)
data = json.loads(lines[1])

# 4. Navigate nested structure
result = data[0][2]  # Actual response is nested
```

**Key RPC Endpoints (from jacob-bd):**

| Operation | RPC ID | Parameters | Response |
|-----------|--------|------------|----------|
| List Notebooks | `wXbhsf` | `[null, 1, null, [2]]` | Array of notebooks |
| Create Notebook | `CCqFvf` | `[title, null, null, [2], [...]]` | Created notebook |
| Query/Chat | (streaming) | `[sources, query, history, [2], conv_id]` | Streaming text chunks |
| Add URL Source | `izAoDd` | `[[source_data], notebook_id, [2]]` | Source object |
| Create Audio Podcast | `R7cb6c` | `[notebook_id, style_params, [...]]` | Artifact ID |
| Poll Generation Status | `gArtLc` | `[notebook_id, artifact_id]` | Status + download URL |

### Authentication Flow

**Essential Cookies to Extract:**
- `SID`, `HSID`, `SSID` - Google authentication tokens
- `APISID`, `SAPISID` - API-specific tokens
- `__Secure-*PSID` - Secure persistent session ID

**Additional Tokens from Page HTML:**
```javascript
// Extract via page.evaluate()
const snlm0e = document.querySelector('script')?.textContent?.match(/SNlM0e":"([^"]+)/)?.[1];
```

**Cookie Lifespan:** 2-4 weeks (requires re-extraction after expiry)

---

## Architectural Decisions

### Decision 1: Integration Approach

**Chosen: Python Library + Browser Automation**

- Zero variable costs (no API calls to paid services)
- Full feature access (all 31 tools)
- Deterministic execution control for DeterminAgent workflows
- Reusable as standalone library

### Decision 2: Browser Automation Framework

**Chosen: Playwright**

- Python-native (no Node.js dependency like Puppeteer)
- Superior headless performance vs Selenium
- Built-in auto-wait eliminates flaky tests

### Decision 3: Architecture Pattern

**Chosen: Hybrid (khengyun architecture + jacob-bd features)**

- **From khengyun**: FastMCP v2 patterns, Pydantic v2, Docker, testing
- **From jacob-bd**: Complete 31-tool inventory, RPC protocol details

### Decision 4: Authentication Strategy

**Chosen: Cookie-based with Chrome Profile Persistence**

- Proven approach (used by jacob-bd and khengyun)
- Enables headless operation after initial login
- No OAuth complexity or API key management

### Decision 5: Async-First API Design

**Chosen: Async-native with Optional Sync Wrappers**

- Browser operations are inherently async
- Better performance for long-running operations (podcast generation)
- Modern Python best practice

### Decision 6: Type Safety

**Chosen: Pydantic v2 + mypy Strict Mode**

- Runtime validation catches API changes
- IDE autocompletion for better DX
- Self-documenting schemas

---

## Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| API changes | High | Daily CI tests against real NotebookLM, version locking |
| Cookie expiry | Medium | Health checks, clear re-auth prompts, `--reauth` flag |
| Rate limiting | Medium | Exponential backoff, request caching |
| Browser failures | Medium | Retry logic, multiple browser engine support |

---

## Next Steps

### Phase 2: Notebook & Source Management

**Milestone:** User can create notebook, add sources, and list them

**Files to Create:**
- `src/pynotebooklm/api.py` - Low-level RPC wrapper
- `src/pynotebooklm/notebooks.py` - NotebookManager class
- `src/pynotebooklm/sources.py` - SourceManager class
- `tests/integration/test_notebooks.py`
- `tests/integration/test_sources.py`

**Tools to Implement (10/31):**
`notebook_list`, `notebook_create`, `notebook_get`, `notebook_rename`, `notebook_delete`, `notebook_add_url`, `notebook_add_text`, `notebook_add_drive`, `source_list_drive`, `source_delete`

---

## Research Sources & References

### Compared MCP Projects

| Project | Tools | Approach | What We Adopted |
|---------|-------|----------|-----------------|
| **[jacob-bd/notebooklm-mcp](https://github.com/jacob-bd/notebooklm-mcp)** | 31 | Chrome DevTools Protocol | 31 tools, RPC protocol, endpoints |
| **[khengyun/notebooklm-mcp](https://github.com/khengyun/notebooklm-mcp)** | 8 | Selenium + FastMCP v2 | Architecture, Pydantic v2, Docker, testing |
| **[PleasePrompto/notebooklm-mcp](https://github.com/PleasePrompto/notebooklm-mcp)** | 16 | Playwright | Library management concept |
| **[souzatharsis/podcastfy](https://github.com/souzatharsis/podcastfy)** | N/A | Local LLM + TTS | Async polling patterns |

### External References

- **Playwright docs**: https://playwright.dev/python/docs/intro
- **Pydantic v2 docs**: https://docs.pydantic.dev/latest/
- **Official Notebook LM Enterprise API**: https://cloud.google.com/notebooklm

---

## API Reverse-Engineering Notes

### Difficulty Assessment

| Aspect | Difficulty | Notes |
|--------|------------|-------|
| Understanding auth flow | ★★★★ | Requires extracting Chrome cookies, handling token refresh |
| Locating internal endpoints | ★★★★ | Endpoints hidden in web UI JavaScript; can change |
| Stability / maintenance | ★★★★★ | Google can change API at any time |
| Automation tooling | ★★ | Playwright is well-documented |

**Overall:** Hard / Semi-automatic – automation works once endpoints are discovered, but discovery and maintenance require ongoing effort.

### What Can Be Automated

| Task | Automation Level |
|------|------------------|
| Browser launch & login | Fully automatable with Playwright |
| Calling internal endpoints | Fully automatable once URL/method/payload known |
| Polling for async generation | Fully automatable |
| Error handling & retries | Automatable with proper error shapes |
| Detecting API changes | Semi-automatic via health checks |
