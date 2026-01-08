# PyNotebookLM - Original Requirements and Notes

## Executive Summary

**Goal**: Build a production-grade Python library for NotebookLM integration, then wrap it with a DeterminAgent adapter to enable deterministic content creation flows.

**Approach**: Two-phase development
1. **Phase 1**: Build `pynotebooklm` - A standalone Python library (similar to khengyun's architecture) (This project, build here)
2. **Phase 2**: Build `NotebookLMAdapter` - A DeterminAgent adapter wrapping the library (Other project, do NOT build here)

NOTE: DeterminAgent is another project that i have already build.

**Key Requirements**:
- ✅ All 31 tools from jacob-bd (Content Generation, Source Management, Research, Mind Maps)
- ✅ Production-grade code quality (Pydantic, type safety, comprehensive testing)
- ✅ Browser automation for auth and API interaction
- ✅ Deterministic behavior for DeterminAgent workflows
- ✅ Clean architecture (avoid "vibe-coded" patterns)

---

## Compared MCP Projects

| Project | Repository | Language | Tools | Approach | Status |
|---------|-----------|----------|-------|----------|--------|
| **jacob-bd** | https://github.com/jacob-bd/notebooklm-mcp | Python | 31 | Browser-based (Chrome DevTools Protocol) | Active |
| **khengyun** | https://github.com/khengyun/notebooklm-mcp | Python | 8 | Browser-based (Selenium) with FastMCP v2 | Production |
| **PleasePrompto** | https://github.com/PleasePrompto/notebooklm-mcp | TypeScript | 16 | Browser-based (Playwright) + Library mgmt | Stable |

---

## ⚠️ CRITICAL CLARIFICATION: jacob-bd "API Reversal" vs Actual Implementation

### The Question
You correctly identified a potential contradiction: jacob-bd claims to use "API reversal" (undocumented internal APIs) rather than web browsers. Let's verify this.

### What jacob-bd Actually Claims
From their README: *"This tool uses Google's internal APIs and Chrome DevTools Protocol to interact with NotebookLM"*

### What jacob-bd Actually Does
**Browser-Based with Chrome DevTools Protocol (CDP)**:

```python
# From jacob-bd source structure:
- Uses Chrome DevTools Protocol (CDP)
- Communicates via WebSocket to Chrome
- Extracts cookies from Chrome DevTools Network tab
- Makes fetch() calls through Chrome context
- Parses responses from Chrome's JavaScript context
```

**NOT Pure HTTP API Calls**:
- ❌ Does NOT make raw HTTP requests to NotebookLM servers
- ❌ Does NOT use undocumented REST endpoints
- ✅ DOES use browser automation through Chrome DevTools
- ✅ DOES extract auth from Chrome cookies
- ✅ DOES make API calls FROM within the browser context

### Why This Distinction Matters

**jacob-bd's "API Reversal" actually means:**
1. Open Chrome with NotebookLM
2. Log in (user provides cookies via DevTools)
3. Use Chrome's JavaScript context to make fetch() calls to NotebookLM's internal endpoints
4. These endpoints ARE real APIs but are undocumented (reverse-engineered)
5. Calls originate FROM the browser context (not direct HTTP)

**This is fundamentally Browser Automation**, not "pure API reversal"

### Verification Evidence

From the technical analysis of jacob-bd's codebase:
```python
# jacob-bd uses this pattern:
page.evaluate("""
    async () => {
        const response = await fetch('https://notebooklm.google.com/_/...',  {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload)
        });
        return await response.json();
    }
""")

# This is browser automation, not raw HTTP
```

### So Why Does jacob-bd Market It As "API Reversal"?

**Technical correctness**: They discovered the internal API endpoints through Chrome DevTools
**Marketing clarity**: "Browser automation" sounds more limited than "API reversal"
**Practical difference**: They don't need Selenium/Playwright overhead - Chrome DevTools Protocol is lighter
**Reality**: Still requires Chrome and cookies, still browser-dependent

### Recommended Approach for Your Project

**Choose Browser Automation (Selenium or Playwright)** over "API reversal" because:

1. **More transparent**: Explicitly browser-based, no confusion
2. **More flexible**: Can fallback if APIs change
3. **Better documented**: Selenium/Playwright have extensive docs
4. **More portable**: Works across different Chrome versions
5. **Easier to debug**: Standard browser automation tools

**Hybrid Architecture**:
```
Primary: HTTP API calls (faster, lighter)
         └─ For basic operations (list, create, query)

Fallback: Browser automation (Selenium/Playwright)
          └─ For complex operations (content generation)
          └─ For anti-bot detection handling
```

---

---

## 1. Integration Approach Analysis

### Option A: Official NotebookLM Enterprise API ❌
**Verdict**: Not viable for your use case

**Pros**:
- Officially supported
- Production-ready
- No browser automation needed

**Cons**:
- ❌ Enterprise only (requires Google Cloud account, billing)
- ❌ Limited functionality (notebook CRUD only, no content generation)
- ❌ No free tier access to advanced features
- ❌ Missing 80% of jacob-bd's tools (no podcasts, videos, infographics)

### Option B: MCP Server Integration ❌
**Verdict**: Adds unnecessary complexity

**Pros**:
- Protocol standardization
- Reusable across MCP clients

**Cons**:
- ❌ Adds latency (subprocess communication)
- ❌ DeterminAgent doesn't use MCP protocol
- ❌ Extra deployment complexity (running separate server)
- ❌ Doesn't fit deterministic flow model
- ❌ Would need adapter anyway to integrate with DeterminAgent

### Option C: A2A (Agent-to-Agent) via Agentspace ❌
**Verdict**: Enterprise-only, wrong abstraction level

**Pros**:
- Google's official multi-agent protocol
- Built-in coordination

**Cons**:
- ❌ Requires Google Agentspace (Enterprise subscription)
- ❌ Not designed for deterministic workflows
- ❌ Overkill for content creation use case
- ❌ Limited control over execution order

### Option D: Python Library + DeterminAgent Adapter ✅ (RECOMMENDED)
**Verdict**: Best fit for requirements

**Pros**:
- ✅ Consistent with DeterminAgent architecture (follows Claude/Gemini/Copilot pattern)
- ✅ Zero variable costs (browser automation, no API calls)
- ✅ Full feature access (all 31 tools)
- ✅ Deterministic execution control
- ✅ Reusable library (can be used standalone or in other projects)
- ✅ Clean separation of concerns (library logic separate from adapter integration)

**Cons**:
- ⚠️ Requires browser automation (Playwright/Puppeteer)
- ⚠️ Cookie-based auth expires every 2-4 weeks
- ⚠️ Depends on undocumented NotebookLM internal APIs
- ⚠️ May break if Google changes NotebookLM UI/API

**Mitigation**:
- Use Playwright (more stable than Puppeteer for headless)
- Implement robust error handling and retry logic
- Version lock the library, add update notifications
- Monitor NotebookLM for breaking changes

---

## Comprehensive Feature Matrix Comparison

### What Each Implementation Can Do

| **Feature Category** | **PleasePrompto** | **jacob-bd** | **khengyun** |
|---|---|---|---|
| **Total Tools/Features** | 16 | 31 | 8 |
| | | | |
| **QUERY & RESEARCH** | | | |
| Ask Questions/Query | ✅ | ✅ | ✅ |
| Multi-turn Conversation | ✅ | ✅ | ✅ |
| AI Research Discovery | ❌ | ✅ Web/Drive research | ✅ (basic) |
| Get Citations | ✅ | ✅ | ✅ |
| | | | |
| **NOTEBOOK MANAGEMENT** | | | |
| Create Notebooks | ❌ | ✅ | ✅ |
| List/Browse Notebooks | ✅ | ✅ | ✅ |
| Rename Notebooks | ❌ | ✅ | ❌ |
| Delete Notebooks | ❌ | ✅ | ❌ |
| Save & Tag Notebooks | ✅ | ❌ | ❌ |
| Custom Notebook Library | ✅ | ❌ | ❌ |
| Notebook Analytics | ✅ | ❌ | ❌ |
| | | | |
| **SOURCE MANAGEMENT** | | | |
| Add URLs | ❌ | ✅ | ❌ |
| Add YouTube Videos | ❌ | ✅ | ❌ |
| Add Google Drive Docs | ❌ | ✅ | ❌ |
| Add Text/Paste Content | ❌ | ✅ | ❌ |
| PDFs | ❌ | ✅ (via Drive) | ✅ (native) |
| Web Content | ❌ | ✅ | ✅ (native) |
| Academic Papers | ❌ | ✅ | ✅ (via URL/PDF) |
| Sync/Update Sources | ❌ | ✅ Freshness tracking | ❌ |
| Delete Sources | ❌ | ✅ | ❌ |
| Source Summaries | ❌ | ✅ | ❌ |
| | | | |
| **CONTENT GENERATION** | | | |
| 🎙️ Audio Podcasts | ❌ | ✅ Multiple formats | ✅ |
| 🎥 Videos | ❌ | ✅ | ✅ |
| 🎨 Infographics | ❌ | ✅ | ❌ |
| 🎪 Slide Decks | ❌ | ✅ | ❌ |
| 🧠 Mind Maps | ❌ | ✅ | ❌ |
| 📇 Flashcards | ❌ | ✅ | ✅ |
| 📋 Briefing Documents | ❌ | ✅ | ❌ |
| 📝 Quiz Questions | ❌ | ❌ (implied) | ✅ |
| Studio Artifact Management | ❌ | ✅ | ❌ |
| | | | |
| **CONFIGURATION & CONTROL** | | | |
| Profile Switching (Minimal/Standard/Full) | ✅ | ❌ | ❌ |
| Chat Goal Configuration | ❌ | ✅ | ❌ |
| Response Length Control | ❌ | ✅ | ❌ |
| Chat Style Configuration | ❌ | ✅ | ❌ |
| | | | |
| **AUTHENTICATION & SESSION** | | | |
| Account Switching | ✅ | ❌ | ✅ |
| Session Management | ✅ | ❌ | ❌ |
| Cookie-Based Auth | ✅ | ✅ | ✅ |
| Setup/Re-auth | ✅ | ✅ | ✅ |
| | | | |
| **DEPLOYMENT & INTEGRATION** | | | |
| STDIO Protocol | ✅ | ✅ | ✅ |
| HTTP Protocol | ❌ | ❌ | ✅ |
| SSE Protocol | ❌ | ❌ | ✅ |
| Docker Support | ❌ | ❌ | ✅ Docker Compose |
| LangGraph Integration | ❌ | ❌ | ✅ (examples) |
| CrewAI Integration | ❌ | ❌ | ✅ (examples) |
| CLI Interface | ✅ | ✅ | ✅ |
| Programmatic API | ❌ | ✅ | ✅ |

### Quick Decision Matrix

**Choose PleasePrompto if you need:**
- ✅ Simple query-focused research tool
- ✅ Save and organize notebooks with metadata/tags
- ✅ Quick setup with minimal configuration
- ❌ Content creation (no audio, video, infographics)
- ❌ Add sources directly (no source management)

**Choose jacob-bd if you need:**
- ✅ Maximum feature breadth (31 tools)
- ✅ Create audio podcasts, videos, infographics, slides, mind maps
- ✅ Add YouTube videos, Google Drive docs, URLs, text
- ✅ Research discovery and bulk imports
- ✅ Studio artifact management
- ⚠️ Still in active development (may have bugs)
- ⚠️ Requires cookie refresh every 2-4 weeks

**Choose khengyun if you need:**
- ✅ Production-ready (v2.0.11, 102 commits, mature)
- ✅ Modern deployment (Docker, HTTP/SSE protocols)
- ✅ Podcast and quiz generation
- ✅ Clean, maintainable codebase with comprehensive tests
- ✅ Framework integrations (LangGraph, CrewAI)
- ❌ Fewer content creation tools than jacob-bd (no video, infographics, mind maps, slides)
- ❌ No direct source management UI (works with NotebookLM native sources)

### Recommendation for Your Project: **Combine jacob-bd's Features with khengyun's Architecture**

- **Feature Set**: Use jacob-bd as reference for all 31 tools
- **Architecture**: Follow khengyun's production-grade patterns (FastMCP v2, Pydantic, Docker, tests)
- **Implementation**: Build a hybrid approach (browser automation + resilience)
- **Quality**: Exceed both in code quality and maintainability

---

## 2. Recommended Architecture

### 2.1 System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     DeterminAgent Workflow                       │
│                          (LangGraph)                             │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        │ Python API call
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│              NotebookLMAdapter (DeterminAgent Layer)             │
│  - Implements ProviderAdapter interface                          │
│  - Maps DeterminAgent calls → NotebookLM library                 │
│  - Handles serialization/deserialization                         │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        │ Library calls
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                    pynotebooklm Library                            │
│                                                                   │
│  ┌──────────────────┐  ┌──────────────────┐  ┌───────────────┐ │
│  │  NotebookLM      │  │  Source          │  │  Content      │ │
│  │  Client          │  │  Manager         │  │  Generator    │ │
│  │  (Core API)      │  │  (Add sources)   │  │  (Podcasts)   │ │
│  └──────────────────┘  └──────────────────┘  └───────────────┘ │
│                                                                   │
│  ┌──────────────────┐  ┌──────────────────┐  ┌───────────────┐ │
│  │  Research        │  │  Mind Map        │  │  Auth         │ │
│  │  Discovery       │  │  Generator       │  │  Manager      │ │
│  └──────────────────┘  └──────────────────┘  └───────────────┘ │
│                                                                   │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        │ Browser automation
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Playwright/Browser                             │
│  - Cookie-based authentication                                    │
│  - Internal NotebookLM API calls                                  │
│  - Headless Chrome session management                             │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Library Architecture (`pynotebooklm`)

**Technology Stack**:
- **Python**: 3.10+ (match DeterminAgent)
- **Browser Automation**: Playwright (more robust than Puppeteer)
- **Type Safety**: Pydantic v2 (schemas and validation)
- **Async**: asyncio (browser operations are async)
- **HTTP**: httpx (async HTTP client for API calls)
- **Testing**: pytest + pytest-asyncio
- **Packaging**: Poetry 

**Directory Structure**:
```
pynotebooklm/
├── src/
│   └── pynotebooklm/
│       ├── __init__.py           # Public API exports
│       ├── client.py             # NotebookLMClient (main entry point)
│       ├── auth.py               # Authentication manager
│       ├── session.py            # Browser session management
│       ├── api.py                # Internal API wrapper
│       ├── models.py             # Pydantic schemas
│       ├── exceptions.py         # Custom exceptions
│       ├── notebooks.py          # Notebook management
│       ├── sources.py            # Source management
│       ├── content.py            # Content generation
│       ├── research.py           # Research discovery
│       └── mindmaps.py           # Mind map generation
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── docs/
├── examples/
├── pyproject.toml
└── README.md
```

**Core Classes**:

```python
# Main entry point
class NotebookLMClient:
    def __init__(self, auth_path: str = "~/.notebooklm/auth.json"):
        self.auth = AuthManager(auth_path)
        self.session = BrowserSession(self.auth)
        self.notebooks = NotebookManager(self.session)
        self.sources = SourceManager(self.session)
        self.content = ContentGenerator(self.session)
        self.research = ResearchDiscovery(self.session)
        self.mindmaps = MindMapGenerator(self.session)

    # High-level methods
    async def create_notebook(self, name: str) -> Notebook
    async def add_youtube_source(self, notebook_id: str, url: str) -> Source
    async def generate_podcast(self, notebook_id: str, style: str) -> Artifact
    ...

# Authentication
class AuthManager:
    async def login(self, headless: bool = False)
    async def refresh_tokens(self)
    def is_authenticated(self) -> bool

# Browser session
class BrowserSession:
    async def __aenter__(self)
    async def __aexit__(self)
    async def call_api(self, endpoint: str, method: str, data: dict) -> dict
```

**Pydantic Models**:
```python
class Notebook(BaseModel):
    id: str
    name: str
    created_at: datetime
    sources: list[Source] = []

class Source(BaseModel):
    id: str
    type: Literal["url", "youtube", "drive", "text"]
    url: Optional[str]
    title: str
    status: Literal["processing", "ready", "failed"]

class Artifact(BaseModel):
    id: str
    type: Literal["audio", "video", "infographic", "slides", "mindmap"]
    status: Literal["generating", "ready", "failed"]
    url: Optional[str]
    progress: float  # 0.0 to 1.0
```

### 2.3 DeterminAgent Adapter

**Integration Pattern**: Follow existing adapter structure

```python
# determinagent/adapters/notebooklm.py

from determinagent.adapters.base import ProviderAdapter
from notebooklm import NotebookLMClient, Notebook
import asyncio

class NotebookLMAdapter(ProviderAdapter):
    provider_name: str = "notebooklm"

    def __init__(self):
        self.client = NotebookLMClient()
        # Run async operations in sync context
        self._loop = asyncio.new_event_loop()

    def build_command(self, prompt: str, model: str, ...) -> list[str]:
        # NotebookLM doesn't use CLI, so this is a no-op
        # We'll override execute() instead
        raise NotImplementedError("NotebookLM uses direct Python API")

    def execute(self, prompt: str, tool: str, **kwargs) -> str:
        """
        Execute NotebookLM tool synchronously

        Args:
            prompt: User instruction
            tool: Tool name (e.g., "generate_podcast", "add_youtube_source")
            **kwargs: Tool-specific parameters

        Returns:
            JSON string with result
        """
        # Parse tool from prompt or kwargs
        # Map to client method
        # Execute and return result

        result = self._loop.run_until_complete(
            self._execute_async(prompt, tool, **kwargs)
        )
        return json.dumps(result)

    async def _execute_async(self, prompt: str, tool: str, **kwargs):
        # Route to appropriate client method
        if tool == "generate_podcast":
            return await self.client.content.generate_podcast(**kwargs)
        elif tool == "add_youtube_source":
            return await self.client.sources.add_youtube(**kwargs)
        # ... map all 31 tools

    def parse_output(self, raw_output: str) -> str:
        # Parse JSON response
        data = json.loads(raw_output)
        return data.get("result", str(data))

    def handle_error(self, returncode: int, stderr: str) -> Exception:
        # Map library exceptions to DeterminAgent exceptions
        return ExecutionError(f"NotebookLM error: {stderr}")
```

**Integration with DeterminAgent**:

```python
# Add to determinagent/agent.py ADAPTERS registry
ADAPTERS = {
    "claude": ClaudeAdapter,
    "copilot": CopilotAdapter,
    "gemini": GeminiAdapter,
    "codex": CodexAdapter,
    "notebooklm": NotebookLMAdapter,  # NEW
}
```

**Usage in Flows**:

```python
# flows/content_creation/main.py

from determinagent import UnifiedAgent
from langgraph.graph import StateGraph

# Initialize NotebookLM agent
notebooklm = UnifiedAgent(
    provider="notebooklm",
    role="content_generator",
    instructions="Generate high-quality content from research sources"
)

# Use in workflow
result = notebooklm.send(
    prompt="Generate a podcast from notebook 'AI Research 2026'",
    tool="generate_podcast",
    notebook_id="abc123",
    style="deep_dive"
)
```

---

## 3. Implementation Phases

### Phase 1: Foundation 

**Deliverables**:
- ✅ Project setup (repo, CI/CD, dependencies)
- ✅ Authentication flow (Playwright, cookie extraction)
- ✅ Browser session management
- ✅ Core Pydantic models
- ✅ Basic NotebookLMClient structure

**Tasks**:
1. Initialize Python project with Poetry/Hatch
2. Set up Playwright for browser automation
3. Implement AuthManager with login flow
4. Implement BrowserSession with context management
5. Define core Pydantic schemas (Notebook, Source, Artifact)
6. Write unit tests for auth and session management

**Technical Focus**: Get browser automation working reliably with headless Chrome

### Phase 2: Notebook & Source Management 

**Deliverables**:
- ✅ Notebook CRUD (create, list, get, rename, delete)
- ✅ Source management (add URL, YouTube, Drive, text)
- ✅ Source status polling (wait for processing to complete)
- ✅ Error handling and retries

**Tools Implemented** (10/31):
- notebook_create
- notebook_list
- notebook_get
- notebook_rename
- notebook_delete
- notebook_add_url
- notebook_add_text
- notebook_add_drive
- source_list_drive
- source_delete

**Technical Focus**: Reverse-engineer NotebookLM's internal API endpoints

### Phase 3: Content Generation 

**Deliverables**:
- ✅ Audio podcast generation
- ✅ Video overview creation
- ✅ Infographic generation
- ✅ Slide deck creation
- ✅ Async status polling for long-running operations

**Tools Implemented** (5/31):
- audio_overview_create
- video_overview_create
- infographic_create
- slide_deck_create
- studio_status

**Technical Focus**: Handle async operations (polling, progress tracking)

### Phase 4: Research & Analysis 

**Deliverables**:
- ✅ Notebook query (ask questions)
- ✅ Research discovery (web/Drive)
- ✅ Research import
- ✅ Source descriptions and summaries
- ✅ Chat configuration

**Tools Implemented** (8/31):
- notebook_query
- notebook_describe
- research_start
- research_status
- research_import
- source_describe
- source_sync_drive
- chat_configure

**Technical Focus**: Implement streaming responses for queries

### Phase 5: Mind Maps & Advanced Features 

**Deliverables**:
- ✅ Mind map generation
- ✅ Flashcard creation
- ✅ Briefing document generation
- ✅ Studio artifact management
- ✅ All 31 tools complete

**Tools Implemented** (8/31):
- mindmap_create
- flashcard_create
- briefing_create
- studio_delete
- save_auth_tokens
- (remaining tools as needed)

**Technical Focus**: Export formats (FreeMind, OPML, XML for mind maps)

### Phase 6: DeterminAgent Integration 

**Deliverables**:
- ✅ NotebookLMAdapter implementation
- ✅ Tool routing and parameter mapping
- ✅ Sync/async bridge for DeterminAgent
- ✅ Integration tests with DeterminAgent

**Tasks**:
1. Create NotebookLMAdapter class
2. Map all 31 tools to adapter methods
3. Implement execute() with async bridge
4. Add to DeterminAgent ADAPTERS registry
5. Write integration tests
6. Update DeterminAgent documentation

### Phase 7: Testing & Documentation 

**Deliverables**:
- ✅ 90%+ test coverage
- ✅ Comprehensive API documentation
- ✅ Example flows (content creation workflow)
- ✅ Troubleshooting guide
- ✅ Migration guide from existing MCP implementations

**Tasks**:
1. Write comprehensive unit tests
2. Write integration tests with real NotebookLM
3. Generate API documentation (Sphinx/mkdocs)
4. Create example content creation flow
5. Write README and usage guides
6. Performance benchmarking

---

## 5. Combining Best Practices from Existing Projects

### From **khengyun/notebooklm-mcp** (Architecture) ✅

**Adopt**:
- ✅ FastMCP v2 patterns (decorator-based, clean structure) - adapt for Python library
- ✅ Pydantic v2 for all data models
- ✅ Comprehensive type hints (mypy strict mode)
- ✅ Docker support for deployment
- ✅ Multiple transport options (adapt: sync/async API)
- ✅ Testing infrastructure (pytest, coverage tracking)
- ✅ CI/CD with GitHub Actions

**Code Pattern Example**:
```python
# khengyun uses FastMCP decorators, we adapt for library:

from pydantic import BaseModel, Field

class GeneratePodcastRequest(BaseModel):
    notebook_id: str = Field(..., description="Notebook ID")
    style: Literal["deep_dive", "briefing"] = Field("deep_dive")
    format: Literal["audio", "video"] = Field("audio")

class GeneratePodcastResponse(BaseModel):
    artifact_id: str
    status: str
    url: Optional[str] = None
    estimated_time_seconds: int

# Clean, typed interface
async def generate_podcast(
    self,
    request: GeneratePodcastRequest
) -> GeneratePodcastResponse:
    # Implementation
```

### From **jacob-bd/notebooklm-mcp** (Features) ✅

**Adopt**:
- ✅ Complete tool inventory (all 31 tools mapped)
- ✅ Multi-source support (YouTube URL parsing, Drive integration)
- ✅ Studio artifact management patterns
- ✅ Research discovery workflows
- ✅ Cookie-based auth approach (proven to work)

**Avoid**:
- ❌ "Vibe-coded" structure (no clear module separation)
- ❌ Lack of type hints and validation
- ❌ Minimal error handling
- ❌ Hardcoded values and magic strings
- ❌ Insufficient testing

**Code Pattern Example** (what to adopt):
```python
# jacob-bd has good tool inventory - adopt the functionality:

TOOLS = {
    "notebook_create": {...},
    "notebook_list": {...},
    "audio_overview_create": {...},
    # ... all 31 tools
}

# But improve the implementation:

class ContentGenerator:
    """Professional content generation with proper error handling"""

    async def generate_podcast(
        self,
        notebook_id: str,
        style: PodcastStyle = PodcastStyle.DEEP_DIVE,
        timeout: int = 300
    ) -> Artifact:
        """
        Generate audio podcast from notebook sources.

        Args:
            notebook_id: ID of notebook with sources
            style: Podcast style (deep_dive, briefing, etc.)
            timeout: Max generation time in seconds

        Returns:
            Artifact: Generated podcast metadata with URL

        Raises:
            NotebookNotFoundError: Notebook doesn't exist
            InsufficientSourcesError: Need at least 1 source
            GenerationTimeoutError: Generation exceeded timeout
        """
        # Validate inputs
        if not await self._notebook_exists(notebook_id):
            raise NotebookNotFoundError(notebook_id)

        # Submit generation request
        artifact = await self._submit_generation(
            notebook_id, "audio_overview", {"style": style.value}
        )

        # Poll for completion with timeout
        return await self._poll_artifact_status(
            artifact.id,
            timeout=timeout
        )
```

### From **PleasePrompto/notebooklm-mcp** (Patterns) ✅

**Adopt**:
- ✅ Library management concept (save, tag, search notebooks)
- ✅ Session continuity patterns
- ✅ Profile-based configuration (minimal/standard/full)

**Code Pattern Example**:
```python
# Adopt library management concept:

class NotebookLibrary:
    """Manage saved notebooks with metadata"""

    async def save(
        self,
        notebook_id: str,
        tags: list[str] = [],
        description: str = ""
    ):
        """Save notebook to library with metadata"""

    async def search(self, query: str, tags: list[str] = []) -> list[Notebook]:
        """Search library by tags or description"""

    async def get_stats(self) -> LibraryStats:
        """Get library statistics"""
```

---

## 6. Technical Deep Dives

### 6.1 Browser Automation Strategy

**Playwright vs Puppeteer vs Selenium**:

| | Playwright | Puppeteer | Selenium |
|---|---|---|---|
| Language | Python native | Node.js (pyppeteer) | Python native |
| Performance | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| Headless | Excellent | Good | Fair |
| Auto-wait | Built-in | Manual | Manual |
| **Verdict** | ✅ Use this | ❌ | ❌ |

**Implementation Pattern**:
```python
from playwright.async_api import async_playwright, Browser, Page

class BrowserSession:
    def __init__(self, auth: AuthManager):
        self.auth = auth
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None

    async def __aenter__(self):
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )

        # Load auth cookies
        context = await self.browser.new_context(
            cookies=self.auth.get_cookies()
        )
        self.page = await context.new_page()

        # Navigate to NotebookLM
        await self.page.goto('https://notebooklm.google.com')
        return self

    async def __aexit__(self, *args):
        await self.browser.close()

    async def call_api(
        self,
        endpoint: str,
        method: str = "POST",
        data: dict = None
    ) -> dict:
        """
        Call NotebookLM internal API via browser context
        """
        # Use page.evaluate to make fetch() calls with cookies
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

### 6.2 Authentication Flow

**Cookie Extraction Strategy**:

1. **Initial Setup**: Launch browser with GUI for user login
2. **Cookie Storage**: Save cookies to `~/.notebooklm/auth.json`
3. **Reuse**: Load cookies for subsequent headless sessions
4. **Refresh**: Detect expiry (401 responses), prompt re-auth

```python
class AuthManager:
    def __init__(self, auth_path: str = "~/.notebooklm/auth.json"):
        self.auth_path = Path(auth_path).expanduser()
        self.auth_path.parent.mkdir(parents=True, exist_ok=True)

    async def login(self, headless: bool = False):
        """
        Perform initial login and save cookies

        Args:
            headless: If False, launch GUI browser for user to login
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=headless)
            context = await browser.new_context()
            page = await context.new_page()

            # Navigate to NotebookLM
            await page.goto('https://notebooklm.google.com')

            if not headless:
                # Wait for user to complete login
                print("Please log in to NotebookLM in the browser window...")
                await page.wait_for_url('**/notebooks**', timeout=300000)

            # Extract cookies
            cookies = await context.cookies()
            self._save_cookies(cookies)

            await browser.close()

    def is_authenticated(self) -> bool:
        """Check if auth.json exists and is not expired"""
        if not self.auth_path.exists():
            return False

        # Check expiry (cookies typically last 2-4 weeks)
        auth_data = self._load_cookies()
        # ... expiry logic
        return True

    def get_cookies(self) -> list[dict]:
        """Load cookies for browser context"""
        return self._load_cookies()
```

### 6.3 Internal API Discovery

**Reverse Engineering Approach**:

1. Open Chrome DevTools Network tab
2. Perform actions in NotebookLM UI
3. Capture XHR/Fetch requests
4. Identify API endpoints and payloads

**Example Endpoints** (discovered from jacob-bd):
```
POST /api/notebooks/create
  Body: {"name": "My Notebook"}

POST /api/notebooks/{id}/sources/add
  Body: {"type": "url", "url": "https://..."}

POST /api/notebooks/{id}/studio/audio
  Body: {"style": "deep_dive"}

GET /api/notebooks/{id}/studio/status/{artifact_id}
```

**API Wrapper Pattern**:
```python
class NotebookLMAPI:
    """Low-level API wrapper"""

    BASE_URL = "https://notebooklm.google.com"

    def __init__(self, session: BrowserSession):
        self.session = session

    async def create_notebook(self, name: str) -> dict:
        """Raw API call to create notebook"""
        return await self.session.call_api(
            f"{self.BASE_URL}/api/notebooks/create",
            method="POST",
            data={"name": name}
        )

    async def generate_audio(
        self,
        notebook_id: str,
        style: str
    ) -> dict:
        """Raw API call to generate audio"""
        return await self.session.call_api(
            f"{self.BASE_URL}/api/notebooks/{notebook_id}/studio/audio",
            method="POST",
            data={"style": style}
        )
```

### 6.4 Async Operations & Polling

**Challenge**: Content generation (podcasts, videos) takes 1-5 minutes

**Solution**: Polling with exponential backoff

```python
async def _poll_artifact_status(
    self,
    artifact_id: str,
    timeout: int = 300,
    initial_delay: float = 2.0,
    max_delay: float = 10.0,
    backoff_factor: float = 1.5
) -> Artifact:
    """
    Poll artifact status until complete or timeout

    Strategy: Exponential backoff (2s → 3s → 4.5s → 6.75s → 10s max)
    """
    start_time = asyncio.get_event_loop().time()
    delay = initial_delay

    while True:
        # Check timeout
        elapsed = asyncio.get_event_loop().time() - start_time
        if elapsed > timeout:
            raise GenerationTimeoutError(
                f"Artifact {artifact_id} generation exceeded {timeout}s"
            )

        # Poll status
        status = await self.api.get_artifact_status(artifact_id)

        if status["status"] == "ready":
            return Artifact(**status)
        elif status["status"] == "failed":
            raise GenerationFailedError(status.get("error", "Unknown"))

        # Wait with exponential backoff
        await asyncio.sleep(delay)
        delay = min(delay * backoff_factor, max_delay)
```

---

## 7. Risk Mitigation

### Risk 1: NotebookLM API Changes
**Impact**: High (breaks integration)
**Probability**: Medium (Google iterates frequently)

**Mitigation**:
- Version lock library releases
- Add automated integration tests (daily CI runs against real NotebookLM)
- Implement API change detection (monitor response schemas)
- Maintain changelog of known working versions
- Create fallback mechanisms for critical tools

### Risk 2: Authentication Expiry
**Impact**: Medium (interrupts workflows)
**Probability**: High (cookies expire every 2-4 weeks)

**Mitigation**:
- Implement auth health checks before operations
- Provide clear error messages prompting re-auth
- Add `--reauth` CLI flag for quick refresh
- Consider automated cookie refresh (risky, may violate ToS)

### Risk 3: Browser Automation Failures
**Impact**: High (no fallback)
**Probability**: Low-Medium (headless Chrome issues)

**Mitigation**:
- Comprehensive error handling with retries
- Support multiple browser engines (Chromium, Firefox)
- Implement logging for debugging
- Test on multiple platforms (Linux, macOS, Windows)

### Risk 4: Rate Limiting
**Impact**: Medium (slows workflows)
**Probability**: Medium (NotebookLM has daily limits)

**Mitigation**:
- Implement rate limit detection (HTTP 429 responses)
- Add exponential backoff retry logic
- Cache notebook/source metadata to reduce API calls
- Document known rate limits in user guide

### Risk 5: Development Effort Overrun
**Impact**: Medium (delays timeline)
**Probability**: High (420h is aggressive)

**Mitigation**:
- **Phase 1-2 validation sprint** (4 weeks, 140h) - Prove core concepts
- Prioritize features: Start with notebooks, sources, podcasts (80% value)
- Defer advanced features (mind maps, research discovery) to Phase 5
- Option to wrap jacob-bd if API reverse engineering blocks progress

---

## 8. Success Criteria

### Phase 1-2 (Foundation + Notebooks) Success:
- ✅ Can authenticate headlessly with saved cookies
- ✅ Can create, list, and delete notebooks
- ✅ Can add URL and YouTube sources
- ✅ 90%+ test coverage for implemented features
- ✅ < 2 second latency for notebook operations

### Phase 3 (Content Generation) Success:
- ✅ Can generate audio podcasts (end-to-end)
- ✅ Can poll status with proper timeout handling
- ✅ Generated artifacts have valid download URLs
- ✅ < 5 minute generation time for standard podcasts

### Phase 6 (DeterminAgent Integration) Success:
- ✅ NotebookLMAdapter works in DeterminAgent workflows
- ✅ Can use NotebookLM in LangGraph flows
- ✅ Example content creation flow works end-to-end
- ✅ Documented in DeterminAgent CLI-REFERENCE.md

### Overall Project Success:
- ✅ All 31 tools implemented and tested
- ✅ 90%+ test coverage
- ✅ Comprehensive documentation
- ✅ Production-ready code quality (Pydantic, type hints, error handling)
- ✅ Can create deterministic content workflows in DeterminAgent

---

## 9. Next Steps

### Immediate 
1. **Validate approach**: Review this plan, ask clarifying questions
2. **Set up environment**: Create GitHub repo, initialize Python project
3. **Proof of concept**: Implement basic Playwright auth flow 

### Short Term 
1. **Phase 1**: Foundation (authentication, session management)
2. **Phase 2**: Notebook & source management
3. **Checkpoint**: Review progress, decide continue vs pivot

### Medium Term 
1. **Phase 3**: Content generation (podcasts, videos, infographics)
2. **Phase 4**: Research & analysis tools

### Long Term 
1. **Phase 5**: Mind maps & advanced features
2. **Phase 6**: DeterminAgent integration
3. **Phase 7**: Testing & documentation
4. **Release**: v1.0.0 of pynotebooklm library

---

## 10. Alternative: Hybrid Approach

If full custom implementation proves too ambitious:

**Plan B: Wrapper + Refactor Strategy**
1. Fork jacob-bd/notebooklm-mcp
2. Refactor with clean architecture (Pydantic, type hints, tests)
3. Extract core functionality into library layer
4. Build DeterminAgent adapter on top
5. Contribute improvements back to jacob-bd

**Tradeoff**: Inherit some technical debt, but faster to production

---

## Summary

**Recommended Path**: Build custom Python library (`pynotebooklm`) with production-grade architecture, then wrap with DeterminAgent adapter.

**Key Technologies**: Playwright, Pydantic, asyncio, httpx, pytest
**Critical Success Factor**: API reverse engineering in Phases 1-2

**Decision Point**: After Phase 2, evaluate progress:
- ✅ On track → Continue with Phases 3-7
- ⚠️ Struggling → Pivot to Plan B (wrap jacob-bd)

---

---

## 11. APPENDIX: Technical Implementation Details

### 11.1 NotebookLM Internal API Endpoints (from jacob-bd)

**Base URL**: `https://notebooklm.google.com/_/LabsTailwindUi/data/batchexecute`

**Request Format** (RPC Protocol):
```python
# URL-encoded payload
body = f"f.req={urllib.parse.quote(json_payload)}&at={csrf_token}&"

# JSON payload structure
json_payload = json.dumps([
    [[rpc_id, params, None, "generic"]]
], separators=(',', ':'))
```

**Key RPC Endpoints** (Discovered from jacob-bd):

| Operation | RPC ID | Parameters | Response |
|-----------|--------|------------|----------|
| List Notebooks | `wXbhsf` | `[null, 1, null, [2]]` | Array of notebooks |
| Create Notebook | `CCqFvf` | `[title, null, null, [2], [...]]` | Created notebook |
| Query/Chat | Streaming | `[sources, query, history, [2], conv_id]` | Streaming text chunks |
| Add URL Source | `izAoDd` | `[[source_data], notebook_id, [2]]` | Source object |
| Create Audio Podcast | `R7cb6c` | `[notebook_id, style_params, [...]]` | Artifact ID |
| Poll Generation Status | `gArtLc` | `[notebook_id, artifact_id]` | Status + download URL |

**Response Parsing Pattern**:
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

### 11.2 Authentication Implementation

**Essential Cookies to Extract**:
- `SID`, `HSID`, `SSID` - Google authentication tokens
- `APISID`, `SAPISID` - API-specific tokens
- `__Secure-*PSID` - Secure persistent session ID

**Additional Tokens from Page HTML**:
```javascript
// Extract via page.evaluate() or Selenium
const snlm0e = document.querySelector('script')?.textContent?.match(/SNlM0e":"([^"]+)/)?.[1];
const fdrfje = document.querySelector('script')?.textContent?.match(/FdrFJe":"([^"]+)/)?.[1];

// Cookie header format
Cookie: SID=...; HSID=...; SSID=...; APISID=...; SAPISID=...; __Secure-1PSID=...; __Secure-3PSID=...
```

**Cookie Lifespan**: 2-4 weeks (requires re-extraction after expiry)

### 11.3 Browser Automation Patterns (from khengyun)

**Anti-Detection Setup** (Selenium):
```python
import undetected_chromedriver as uc

options = uc.ChromeOptions()
options.add_argument(f"--user-data-dir={profile_path}")
options.add_argument("--no-first-run")
options.add_argument("--no-default-browser-check")
options.add_argument("--headless=new")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option("useAutomationExtension", False)

driver = uc.Chrome(options=options, version_main=None)
driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
```

**Element Selectors with Fallbacks**:
```python
# Chat input - try multiple selectors
selectors = [
    "textarea[placeholder*='Ask']",
    "textarea[data-testid*='chat']",
    "[contenteditable='true'][role='textbox']",
]

for selector in selectors:
    try:
        element = WebDriverWait(driver, 2).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
        )
        break
    except TimeoutException:
        continue
```

### 11.4 Comprehensive Tool Catalog (31 Tools)

**Category Breakdown**:

**Notebooks (6)**:
- `notebook_list`, `notebook_create`, `notebook_get`, `notebook_describe`, `notebook_rename`, `notebook_delete`

**Sources (7)**:
- `notebook_add_url`, `notebook_add_text`, `notebook_add_drive`, `source_describe`, `source_list_drive`, `source_sync_drive`, `source_delete`

**Query & Analysis (2)**:
- `notebook_query`, `chat_configure`

**Research (3)**:
- `research_start`, `research_status`, `research_import`

**Studio Content Generation (13)**:
- Audio: `audio_overview_create`
- Video: `video_overview_create`
- Visual: `infographic_create`, `slide_deck_create`
- Documents: `briefing_create`
- Study: `flashcard_create`, `quiz_create`
- Analysis: `data_table_create`
- Knowledge: `mindmap_create`, `mindmap_list`
- Metadata: `studio_status`, `studio_delete`
- Auth: `save_auth_tokens`

### 11.5 Error Response Patterns

**Consistent Response Format**:
```python
# Success
{
    "status": "success",
    "data": {...},
    "metadata": {...}
}

# Error
{
    "status": "error",
    "error": "Human-readable message",
    "error_type": "AuthenticationError|APIError|ValidationError|RateLimitError",
    "details": {...}
}

# Confirmation Required
{
    "status": "error",
    "error": "Action requires confirmation",
    "warning": "This action is IRREVERSIBLE",
    "required_parameter": "confirm=True"
}
```

### 11.6 Testing Infrastructure (from khengyun)

**Fixture Pattern**:
```python
@pytest.fixture
def mock_auth_tokens():
    return {
        "cookies": {
            "SID": "mock_sid",
            "HSID": "mock_hsid",
            # ... other cookies
        },
        "csrf_token": "mock_csrf",
        "session_id": "mock_session"
    }

@pytest.fixture
async def async_client(mock_auth_tokens):
    client = AsyncMock(spec=NotebookLMClient)
    await client.start()
    yield client
    await client.close()
```

**Mock API Responses**:
```python
# Real response format with anti-XSSI prefix
response_text = """)]}'
6
[[[\"wrb.fr\",null,\"[[\\\"nb1\\\",\\\"Test\\\"]]\"]]
"""
```

### 11.7 Deployment Architecture

**Docker Prerequisites**:
- Python 3.11+
- Chrome/Chromium browser
- Chrome profile directory (persistent across restarts)

**Production Requirements**:
- Health check endpoint
- Rate limiter with persistent state
- Auth token cache with expiry detection
- Logging to files (not just stdout)
- Signal handling for graceful shutdown

### 11.8 Technical Complexity Assessment

**High Complexity**:
- API protocol reverse engineering (RPC structure, response parsing)
- Browser automation setup (anti-detection, element selectors)
- Authentication flow (cookie extraction, token management)

**Medium Complexity**:
- Tool implementations (31 different operations)
- Async polling for content generation
- Error handling and retries

**Low Complexity*:
- MCP server integration (FastMCP is well-documented)
- Configuration management (Pydantic)
- Testing infrastructure (standard pytest patterns)

---

## 12. Reverse‑Engineering Notebook LM API – Difficulty & Recommendations

### 12.1 Difficulty Assessment

| Aspect | Difficulty | Why? | Typical effort |
|--------|------------|------|----------------|
| **Understanding the authentication flow** | ★★★★ (hard) | Requires extracting Chrome cookies, handling token refresh, and sometimes solving re‑CAPTCHA or multi‑factor prompts. | 1‑2 days of trial & error; stable solution needs robust cookie‑management code. |
| **Locating internal endpoints** | ★★★★ (hard) | Endpoints are hidden in the web UI JavaScript; they can change with each UI release. | Ongoing research; a few weeks to map the most common calls (list notebooks, add source, generate content). |
| **Stability / maintenance** | ★★★★★ (very hard) | Google can change the UI or the internal API at any time, breaking the connector. | Continuous monitoring; expect breakages roughly every 2‑4 weeks (when cookies expire or UI updates). |
| **Automation tooling** | ★★ (moderate) | Playwright/Chrome CDP are well‑documented; the code to drive them is straightforward once the endpoints are known. | A few hours to set up a reliable Playwright wrapper. |
| **Legal / policy considerations** | ★★ (moderate) | Reverse‑engineering a Google product may violate terms of service. | Review Google’s policies; consider using the **Enterprise API** if you need a supported solution. |

**Overall rating:** **Hard / Semi‑automatic** – you can automate the workflow **once** the endpoints are discovered, but the discovery and long‑term maintenance require significant manual effort.

### 12.2 What Can Be Automated?

| Task | Automation level |
|------|------------------|
| **Browser launch & login (or cookie injection)** | Fully automatable with Playwright (headless or headed). |
| **Calling internal endpoints** | Fully automatable **once** you know the URL, method, and payload schema. |
| **Polling for async generation (e.g., podcast, video)** | Fully automatable – just repeat the same `fetch` call until `status === "ready"` or timeout. |
| **Error handling & retries** | Automatable, but you need to anticipate the error shapes (e.g., 401, 429, “session expired”). |
| **Detecting API changes** | Semi‑automatic – you can write a health‑check that validates a known endpoint and alerts you if the response shape changes. |

### 12.3 Recommendations

1. **Start with Playwright** and build a thin wrapper that loads saved cookies and provides a generic `call_api(endpoint, method, payload)` helper.
2. **Document each discovered endpoint** (URL, method, request/response schema) in a markdown file inside the repo – this will be your “API spec”.
3. **Add health‑check tests** that run nightly and alert you if any endpoint returns an unexpected status or schema.
4. **Consider a fallback** to UI‑only automation if a critical endpoint breaks.
5. **If you need a guaranteed SLA**, evaluate the **Enterprise Notebook LM API** or an alternative open‑source solution like **Open Notebook**.

---

## Resources & References

- **Official Notebook LM Enterprise API** – https://cloud.google.com/notebooklm
- **jacob‑bd notebooklm‑mcp** – https://github.com/jacob-bd/notebooklm-mcp
- **khengyun notebooklm‑mcp** – https://github.com/khengyun/notebooklm-mcp
- **PleasePrompto notebooklm‑mcp** – https://github.com/PleasePrompto/notebooklm-mcp
- **AutoContent API (unofficial)** – https://autocontentapi.com
- **notebooklm‑kit (TypeScript SDK)** – https://github.com/notebooklm-kit/notebooklm-kit
- **Apify “To NotebookLM” API** – https://apify.com/notebooklm
- **Open Notebook (open‑source alternative)** – https://github.com/open-notebook/open-notebook
- **Google Gemini documentation** – https://developers.google.com/gemini
- **Playwright documentation** – https://playwright.dev/python/docs/intro

---

**Questions for Review**:
2. Any specific tools from jacob-bd's 31 that are "must-haves" for MVP?
3. Should we prioritize DeterminAgent integration earlier (swap Phase 4 and 6)?
4. Preference for async-first API or sync wrapper with async internals?
