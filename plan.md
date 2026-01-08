# PyNotebookLM - Detailed Technical Implementation Plan

Production-grade Python library for NotebookLM automation with 31 tools.

---

## Research Summary

### Projects Analyzed

| Project | Stars | Tools | Approach | Key Strengths | Key Weaknesses |
|---------|-------|-------|----------|---------------|----------------|
| **[khengyun/notebooklm-mcp](https://github.com/khengyun/notebooklm-mcp)** | ~100 | 8 | Selenium + FastMCP v2 | Production-ready, Docker, Pydantic v2, multi-transport | Fewer features |
| **[jacob-bd/notebooklm-mcp](https://github.com/jacob-bd/notebooklm-mcp)** | ~200 | 31 | Chrome DevTools Protocol | Complete feature set, RPC protocol details | "Vibe-coded", weak typing |
| **[souzatharsis/podcastfy](https://github.com/souzatharsis/podcastfy)** | ~5k | N/A | Local LLM + TTS | Podcast workflow, 100+ LLM support, multi-language | Not a NotebookLM wrapper |
| **[PleasePrompto/notebooklm-mcp](https://github.com/PleasePrompto/notebooklm-mcp)** | ~50 | 16 | Playwright | Notebook library management | No content generation |

### What to Adopt from Each

**From khengyun:**
- FastMCP v2 decorator patterns (adapt for library)
- Pydantic v2 for all data models
- Docker support with persistent Chrome profile
- Multiple transports (STDIO, HTTP, SSE) - adapt for sync/async API
- Comprehensive testing infrastructure

**From jacob-bd:**
- Complete 31-tool inventory
- RPC protocol implementation details
- Internal API endpoint discovery
- Cookie-based auth approach

**From Podcastfy:**
- Async polling patterns for long-running generation
- Multi-format content customization

**From PleasePrompto:**
- Notebook library/tagging concepts
- Session continuity patterns

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
│  │                   Core Infrastructure                    │  │
│  │  ┌────────────┐  ┌───────────────┐  ┌─────────────────┐  │  │
│  │  │ AuthMgr    │  │ BrowserSession│  │ NotebookLMAPI   │  │  │
│  │  │ - login    │  │ - context mgr │  │ - call_rpc      │  │  │
│  │  │ - cookies  │  │ - page.eval() │  │ - parse_response│  │  │
│  │  │ - refresh  │  │ - retry logic │  │ - handle_error  │  │  │
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

---

## Directory Structure

```
pynotebooklm/
├── src/
│   └── pynotebooklm/
│       ├── __init__.py           # Public API exports
│       ├── client.py             # NotebookLMClient (main entry point)
│       ├── auth.py               # AuthManager (cookie extraction/persistence)
│       ├── session.py            # BrowserSession (Playwright context manager)
│       ├── api.py                # NotebookLMAPI (low-level RPC wrapper)
│       ├── models.py             # Pydantic schemas
│       ├── exceptions.py         # Custom exceptions
│       ├── notebooks.py          # NotebookManager
│       ├── sources.py            # SourceManager
│       ├── content.py            # ContentGenerator
│       ├── research.py           # ResearchDiscovery
│       ├── mindmaps.py           # MindMapGenerator
│       ├── study.py              # Flashcards, quizzes, briefings
│       └── cli.py                # CLI interface
├── tests/
│   ├── unit/                     # Fast tests with mocks
│   ├── integration/              # Tests against real NotebookLM
│   └── fixtures/                 # Mock responses
├── docs/                         # mkdocs documentation
├── examples/                     # Usage examples
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
└── README.md
```

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
const fdrfje = document.querySelector('script')?.textContent?.match(/FdrFJe":"([^"]+)/)?.[1];
```

**Cookie Lifespan:** 2-4 weeks (requires re-extraction after expiry)

### Browser Automation Patterns

**Playwright Session Setup:**
```python
from playwright.async_api import async_playwright

class BrowserSession:
    async def __aenter__(self):
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        context = await self.browser.new_context(
            cookies=self.auth.get_cookies()
        )
        self.page = await context.new_page()
        await self.page.goto('https://notebooklm.google.com')
        return self

    async def call_api(self, endpoint: str, method: str, data: dict) -> dict:
        """Call NotebookLM internal API via browser context"""
        result = await self.page.evaluate(f"""
            async () => {{
                const response = await fetch('{endpoint}', {{
                    method: '{method}',
                    headers: {{'Content-Type': 'application/json'}},
                    body: {json.dumps(data)}
                }});
                return await response.json();
            }}
        """)
        return result
```

### Async Polling for Content Generation

**Challenge:** Podcast/video generation takes 1-5 minutes

**Solution:** Polling with exponential backoff
```python
async def poll_artifact_status(
    artifact_id: str,
    timeout: int = 300,
    initial_delay: float = 2.0,
    max_delay: float = 10.0,
    backoff_factor: float = 1.5
) -> Artifact:
    """
    Poll artifact status until complete or timeout
    Strategy: Exponential backoff (2s → 3s → 4.5s → 10s max)
    """
    start_time = asyncio.get_event_loop().time()
    delay = initial_delay

    while True:
        elapsed = asyncio.get_event_loop().time() - start_time
        if elapsed > timeout:
            raise GenerationTimeoutError(f"Exceeded {timeout}s")

        status = await api.get_artifact_status(artifact_id)

        if status["status"] == "ready":
            return Artifact(**status)
        elif status["status"] == "failed":
            raise GenerationFailedError(status.get("error"))

        await asyncio.sleep(delay)
        delay = min(delay * backoff_factor, max_delay)
```

---

## Pydantic Models

```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Literal, Optional

class Notebook(BaseModel):
    id: str
    name: str
    created_at: datetime
    sources: list["Source"] = []

class Source(BaseModel):
    id: str
    type: Literal["url", "youtube", "drive", "text"]
    url: Optional[str] = None
    title: str
    status: Literal["processing", "ready", "failed"]

class Artifact(BaseModel):
    id: str
    type: Literal["audio", "video", "infographic", "slides", "mindmap", "flashcards", "briefing"]
    status: Literal["generating", "ready", "failed"]
    url: Optional[str] = None
    progress: float = 0.0  # 0.0 to 1.0

class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    citations: list[str] = []

class GeneratePodcastRequest(BaseModel):
    notebook_id: str = Field(..., description="Notebook ID")
    style: Literal["deep_dive", "briefing", "learning_guide"] = "deep_dive"

class GeneratePodcastResponse(BaseModel):
    artifact_id: str
    status: str
    url: Optional[str] = None
```

---

## Complete Tool Inventory (31 Tools)

### Notebooks (6 tools)
| Tool | Description | Phase |
|------|-------------|-------|
| `notebook_list` | List all notebooks in account | 2 |
| `notebook_create` | Create new notebook with name | 2 |
| `notebook_get` | Get notebook details by ID | 2 |
| `notebook_describe` | AI summary of notebook contents | 4 |
| `notebook_rename` | Rename existing notebook | 2 |
| `notebook_delete` | Delete notebook (requires confirmation) | 2 |

### Sources (7 tools)
| Tool | Description | Phase |
|------|-------------|-------|
| `notebook_add_url` | Add web URL as source | 2 |
| `notebook_add_text` | Add plain text as source | 2 |
| `notebook_add_drive` | Add Google Drive document | 2 |
| `source_describe` | AI summary of single source | 4 |
| `source_list_drive` | List available Drive documents | 2 |
| `source_sync_drive` | Sync/update Drive sources | 4 |
| `source_delete` | Remove source from notebook | 2 |

### Query & Chat (2 tools)
| Tool | Description | Phase |
|------|-------------|-------|
| `notebook_query` | Ask question, get AI answer with citations | 4 |
| `chat_configure` | Set chat style, response length, goals | 4 |

### Research (3 tools)
| Tool | Description | Phase |
|------|-------------|-------|
| `research_start` | Start web/Drive research on topic | 4 |
| `research_status` | Check research discovery progress | 4 |
| `research_import` | Import discovered sources to notebook | 4 |

### Content Generation (7 tools)
| Tool | Description | Phase |
|------|-------------|-------|
| `audio_overview_create` | Generate podcast (deep dive, briefing) | 3 |
| `video_overview_create` | Generate video explainer | 3 |
| `infographic_create` | Generate infographic image | 3 |
| `slide_deck_create` | Generate presentation slides | 3 |
| `studio_status` | Check generation progress | 3 |
| `studio_delete` | Delete generated artifact | 5 |
| `save_auth_tokens` | Explicitly save current auth state | 1 |

### Study Tools (4 tools)
| Tool | Description | Phase |
|------|-------------|-------|
| `flashcard_create` | Generate study flashcards | 5 |
| `quiz_create` | Generate quiz questions | 5 |
| `briefing_create` | Generate briefing document | 5 |
| `data_table_create` | Generate data analysis table | 5 |

### Mind Maps (2 tools)
| Tool | Description | Phase |
|------|-------------|-------|
| `mindmap_create` | Generate mind map from sources | 5 |
| `mindmap_list` | List existing mind maps | 5 |

---

## Phase 1: Foundation & Project Setup

**Milestone:** User can authenticate and see cookies saved

### Files to Create
- `pyproject.toml` - Poetry configuration
- `src/pynotebooklm/__init__.py` - Public API exports
- `src/pynotebooklm/models.py` - All Pydantic schemas
- `src/pynotebooklm/exceptions.py` - Custom exceptions
- `src/pynotebooklm/auth.py` - AuthManager class
- `src/pynotebooklm/session.py` - BrowserSession class
- `tests/unit/test_auth.py`
- `tests/unit/test_session.py`
- `.github/workflows/ci.yml` - CI/CD setup

### Verification
```bash
# Unit tests pass
pytest tests/unit/ -v

# Manual auth test
python -m pynotebooklm.auth login   # Browser opens
python -m pynotebooklm.auth check   # Shows "Authenticated: True"
ls ~/.pynotebooklm/auth.json        # Cookie file exists
```

---

## Phase 2: Notebook & Source Management

**Milestone:** User can create notebook, add sources, and list them

### Files to Create
- `src/pynotebooklm/api.py` - Low-level RPC wrapper
- `src/pynotebooklm/notebooks.py` - NotebookManager class
- `src/pynotebooklm/sources.py` - SourceManager class
- `tests/integration/test_notebooks.py`
- `tests/integration/test_sources.py`

### Tools Implemented (10/31)
`notebook_list`, `notebook_create`, `notebook_get`, `notebook_rename`, `notebook_delete`, `notebook_add_url`, `notebook_add_text`, `notebook_add_drive`, `source_list_drive`, `source_delete`

### Verification
```bash
pytest tests/integration/test_notebooks.py -v

# Manual test
python -c "
from pynotebooklm import NotebookLMClient
import asyncio

async def test():
    async with NotebookLMClient() as client:
        # List notebooks
        notebooks = await client.notebooks.list()
        print(f'Found {len(notebooks)} notebooks')
        
        # Create a test notebook
        nb = await client.notebooks.create('Test Notebook')
        print(f'Created: {nb.name} ({nb.id})')
        
        # Add a source
        src = await client.sources.add_url(nb.id, 'https://example.com')
        print(f'Added source: {src.title}')
        
        # Delete test notebook
        await client.notebooks.delete(nb.id, confirm=True)

asyncio.run(test())
"
```

---

## Phase 3: Content Generation

**Milestone:** User can generate a podcast from a notebook

### Files to Create
- `src/pynotebooklm/content.py` - ContentGenerator class
- `tests/integration/test_content.py`

### Tools Implemented (5/31)
`audio_overview_create`, `video_overview_create`, `infographic_create`, `slide_deck_create`, `studio_status`

### Verification
```bash
pytest tests/integration/test_content.py -v --timeout=600

# Manual test (requires notebook with sources)
python -c "
from pynotebooklm import NotebookLMClient
import asyncio

async def test():
    async with NotebookLMClient() as client:
        notebook_id = 'YOUR_NOTEBOOK_ID'  # Must have sources
        
        # Generate podcast
        artifact = await client.content.generate_podcast(
            notebook_id, 
            style='deep_dive'
        )
        print(f'Generating: {artifact.id}')
        
        # Poll until ready
        while artifact.status == 'generating':
            await asyncio.sleep(5)
            artifact = await client.content.get_status(artifact.id)
            print(f'Progress: {artifact.progress*100:.0f}%')
        
        print(f'Download: {artifact.url}')

asyncio.run(test())
"
```

---

## Phase 4: Research & Analysis

**Milestone:** User can query notebook and import research

### Files to Create
- `src/pynotebooklm/research.py` - ResearchDiscovery class
- `tests/integration/test_research.py`

### Tools Implemented (8/31)
`notebook_query`, `notebook_describe`, `research_start`, `research_status`, `research_import`, `source_describe`, `source_sync_drive`, `chat_configure`

### Verification
```bash
pytest tests/integration/test_research.py -v

# Manual query test
python -c "
from pynotebooklm import NotebookLMClient
import asyncio

async def test():
    async with NotebookLMClient() as client:
        response = await client.research.query(
            notebook_id='YOUR_ID',
            question='What are the main topics discussed?'
        )
        print(f'Answer: {response.content}')
        print(f'Citations: {response.citations}')

asyncio.run(test())
"
```

---

## Phase 5: Mind Maps & Advanced Features

**Milestone:** All 31 tools implemented and tested

### Files to Create
- `src/pynotebooklm/mindmaps.py` - MindMapGenerator class
- `src/pynotebooklm/study.py` - Flashcards, quizzes, briefings
- `tests/integration/test_mindmaps.py`
- `tests/integration/test_study.py`

### Tools Implemented (8/31)
`mindmap_create`, `mindmap_list`, `flashcard_create`, `quiz_create`, `briefing_create`, `data_table_create`, `studio_delete`, `save_auth_tokens`

### Verification
```bash
pytest tests/integration/test_mindmaps.py tests/integration/test_study.py -v
```

---

## Phase 6: Production Readiness

**Milestone:** Library is pip-installable and documented

### Files to Create
- `src/pynotebooklm/client.py` - NotebookLMClient (unified entry)
- `src/pynotebooklm/cli.py` - CLI interface
- `Dockerfile`
- `docker-compose.yml`
- `docs/index.md`
- `docs/quickstart.md`
- `docs/api-reference.md`
- `examples/basic_usage.py`
- `examples/podcast_generation.py`
- `examples/research_workflow.py`

### Verification
```bash
# Package installation
pip install .
pynotebooklm --version

# CLI works
pynotebooklm auth login
pynotebooklm notebooks list

# Docker works
docker build -t pynotebooklm .
docker run -v ~/.pynotebooklm:/root/.pynotebooklm pynotebooklm notebooks list

# Docs build
mkdocs build && mkdocs serve
```

---

## Error Handling Strategy

### Exception Hierarchy
```python
class PyNotebookLMError(Exception):
    """Base exception"""

class AuthenticationError(PyNotebookLMError):
    """Cookie expired or invalid"""

class NotebookNotFoundError(PyNotebookLMError):
    """Notebook ID doesn't exist"""

class SourceError(PyNotebookLMError):
    """Source add/processing failed"""

class GenerationError(PyNotebookLMError):
    """Content generation failed"""

class GenerationTimeoutError(GenerationError):
    """Generation exceeded timeout"""

class RateLimitError(PyNotebookLMError):
    """Too many requests"""

class APIError(PyNotebookLMError):
    """Internal API returned error"""
```

### Retry Logic
```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type(RateLimitError)
)
async def call_api_with_retry(self, endpoint, data):
    ...
```

---

## Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| API changes | High | Daily CI tests against real NotebookLM, version locking |
| Cookie expiry | Medium | Health checks, clear re-auth prompts, `--reauth` flag |
| Rate limiting | Medium | Exponential backoff, request caching |
| Browser failures | Medium | Retry logic, multiple browser engine support |

---

## Decision Point: After Phase 2

Evaluate progress:
- ✅ **On track** → Continue to Phase 3
- ⚠️ **API issues** → Document workarounds, continue cautiously
- ❌ **Major blockers** → Consider Plan B: fork jacob-bd and refactor

---

## References

- **jacob-bd/notebooklm-mcp**: https://github.com/jacob-bd/notebooklm-mcp (tools, RPC protocol)
- **khengyun/notebooklm-mcp**: https://github.com/khengyun/notebooklm-mcp (architecture, testing)
- **Podcastfy**: https://github.com/souzatharsis/podcastfy (async patterns)
- **Playwright docs**: https://playwright.dev/python/docs/intro
- **Pydantic v2 docs**: https://docs.pydantic.dev/latest/
