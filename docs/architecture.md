<!--
DOCUMENTATION SCOPE: This file contains high-level architecture decisions, component diagrams, and core data models.
DO NOT include here: Implementation details, specific tool lists, or protocol specifics.
-->

# Architecture & Design

## High-Level Architecture

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
│  │  │ - cookies  │  │ - refresh     │  │ - parse_response│  │  │
│  │  │ - save     │  │ - failover    │  │ - handle_error  │  │  │
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

## Data Models (Pydantic)

High-level representation of the core entities.

```python
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
    progress: float = 0.0

class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    citations: list[str] = []
```

## Exception Hierarchy

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
