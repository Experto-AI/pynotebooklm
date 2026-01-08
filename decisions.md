# PyNotebookLM Architectural Decisions

## Decision 1: Integration Approach

### Chosen: Python Library + Browser Automation

**Why:**
- Zero variable costs (no API calls to paid services)
- Full feature access (all 31 tools from NotebookLM)
- Deterministic execution control for DeterminAgent workflows
- Reusable as standalone library or in other projects

### Alternatives Considered

| Alternative | Why Rejected |
|-------------|--------------|
| **Official Enterprise API** | Enterprise-only, limited to CRUD (no podcasts, videos, infographics) |
| **MCP Server Wrapper** | Adds latency, extra deployment complexity, doesn't fit DeterminAgent model |
| **A2A via Agentspace** | Requires Google Enterprise subscription, overkill for content creation |

---

## Decision 2: Browser Automation Framework

### Chosen: Playwright

**Why:**
- Python-native (no Node.js dependency like Puppeteer)
- Superior headless performance vs Selenium
- Built-in auto-wait eliminates flaky tests
- Better multi-browser support

### Alternatives Considered

| Alternative | Why Rejected |
|-------------|--------------|
| **Selenium** | Slower, manual waits needed, larger footprint |
| **Puppeteer (pyppeteer)** | Node.js dependency, Python port less maintained |
| **Chrome DevTools Protocol direct** | Lower-level, more complex, less portable |

---

## Decision 3: Architecture Pattern

### Chosen: Hybrid (khengyun architecture + jacob-bd features)

**Why:**
- **From khengyun**: FastMCP v2 patterns, Pydantic v2 validation, Docker support, comprehensive testing
- **From jacob-bd**: Complete 31-tool inventory, RPC protocol details, API endpoint discovery
- **From Podcastfy**: Podcast generation workflow patterns
- Combines production maturity with feature completeness

### Source Projects Analyzed

| Project | Adopted | Avoided |
|---------|---------|---------|
| **khengyun/notebooklm-mcp** | FastMCP v2, Pydantic, Docker, multi-transport | Selenium (replaced with Playwright) |
| **jacob-bd/notebooklm-mcp** | 31 tools, RPC protocol, endpoints | "Vibe-coded" structure, weak typing |
| **souzatharsis/podcastfy** | Podcast workflow patterns | Different focus (local gen) |
| **Open Notebook** | REST API design inspiration | Not a NotebookLM wrapper |

---

## Decision 4: Authentication Strategy

### Chosen: Cookie-based with Chrome Profile Persistence

**Why:**
- Proven approach (used by jacob-bd and khengyun)
- Enables headless operation after initial login
- No OAuth complexity or API key management
- Works with existing Google accounts

### Trade-offs Accepted

| Trade-off | Mitigation |
|-----------|------------|
| Cookies expire (2-4 weeks) | Health checks, clear re-auth prompts |
| Requires initial manual login | One-time setup, GUI browser opens |
| May violate ToS | Not for enterprise use; accept risk |

---

## Decision 5: Async-First API Design

### Chosen: Async-native with Optional Sync Wrappers

**Why:**
- Browser operations are inherently async
- Better performance for long-running operations (podcast generation)
- Modern Python best practice
- Compatible with asyncio ecosystem

### API Pattern

```python
# Async (recommended)
async with NotebookLMClient() as client:
    notebooks = await client.notebooks.list()

# Sync wrapper (convenience)
client = NotebookLMClient()
notebooks = client.notebooks.list_sync()
```

---

## Decision 6: Type Safety

### Chosen: Pydantic v2 + mypy Strict Mode

**Why:**
- Runtime validation catches API changes
- IDE autocompletion for better DX
- Self-documenting schemas
- Easy JSON serialization

### Models

```python
class Notebook(BaseModel):
    id: str
    name: str
    created_at: datetime
    sources: list[Source] = []

class Source(BaseModel):
    id: str
    type: Literal["url", "youtube", "drive", "text"]
    title: str
    status: Literal["processing", "ready", "failed"]
```

---

## Decision 7: Project Structure

### Chosen: src Layout with Poetry

**Why:**
- Prevents accidental imports from project root
- Clean separation of package code and tests
- Poetry provides modern dependency management
- Works well with CI/CD

### Structure

```
pynotebooklm/
├── src/
│   └── pynotebooklm/
│       ├── __init__.py
│       ├── client.py
│       ├── auth.py
│       ├── session.py
│       ├── models.py
│       ├── notebooks.py
│       ├── sources.py
│       ├── content.py
│       ├── research.py
│       └── mindmaps.py
├── tests/
├── docs/
├── pyproject.toml
└── README.md
```

---

## Risk Acknowledgments

| Risk | Impact | Mitigation |
|------|--------|------------|
| NotebookLM API changes | High | Health checks, version locking, daily CI tests |
| Cookie expiry | Medium | Clear error messages, `--reauth` CLI flag |
| Rate limiting | Medium | Exponential backoff, request caching |
| Browser automation failures | Medium | Retry logic, multiple browser engine support |
