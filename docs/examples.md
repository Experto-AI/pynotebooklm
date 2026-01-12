# Code Examples

This guide provides detailed walkthroughs of the example scripts included with PyNotebookLM. Each example demonstrates specific features and patterns for building production-ready automation with NotebookLM.

## Quick Start

All examples are located in the `examples/` directory. To run any example:

```bash
# Make sure you're authenticated first
poetry run pynotebooklm auth login

# Run an example
poetry run python examples/01_basic_usage.py
```

## Example Files

### 01_basic_usage.py - Core Operations

**Purpose:** Introduction to fundamental PyNotebookLM operations.

**What it demonstrates:**
- Creating and listing notebooks
- Adding sources (URLs, YouTube, text, Google Drive)
- Querying notebooks
- Deleting resources with confirmation

**Key patterns:**
- Using async context managers (`async with NotebookLMClient()`)
- Error handling with try/except
- Rich console output for better UX

**Code walkthrough:**

```python
async with NotebookLMClient() as client:
    # Create a notebook
    notebook = await client.notebooks.create("My Research Project")
    
    # Add sources
    source = await client.sources.add_url(
        notebook.id, 
        "https://www.python.org"
    )
    
    # Query the notebook
    response = await client.chat.query(
        notebook.id,
        "What is Python?"
    )
```

**When to use:** Start here if you're new to PyNotebookLM.

---

### 02_research_workflow.py - Discovery & Import

**Purpose:** Automate web research and source discovery.

**What it demonstrates:**
- Starting fast and deep research sessions
- Polling for research completion
- Importing discovered sources
- Handling long-running operations

**Key patterns:**
- Polling with exponential backoff
- Task completion detection
- Bulk source import

**Code walkthrough:**

```python
# Start deep research
task = await client.research.start_research(
    notebook_id,
    "artificial intelligence ethics",
    mode="deep",
    source="web"
)

# Poll until complete (with timeout)
timeout = 300  # 5 minutes
while timeout > 0:
    result = await client.research.poll_research(notebook_id)
    if result.status == "completed":
        break
    await asyncio.sleep(5)
    timeout -= 5

# Import discovered sources
sources = await client.research.import_research_sources(
    notebook_id,
    result.task_id,
    result.sources
)
```

**When to use:** Automating content research pipelines.

---

### 03_content_generation.py - Multi-Modal Content

**Purpose:** Generate audio, video, infographics, and slide decks.

**What it demonstrates:**
- Creating audio overviews (podcasts) with different formats
- Generating videos with visual style customization
- Creating infographics with orientation options
- Building slide decks
- Polling studio artifacts for completion

**Key patterns:**
- Studio artifact status polling
- Download URL extraction
- Format/style parameter configuration

**Code walkthrough:**

```python
# Generate audio (podcast)
audio = await client.content.create_audio(
    notebook_id,
    source_ids,
    format="deep_dive",  # conversational format
    length="default",
    language="en"
)

# Poll for completion
while True:
    artifacts = await client.content.poll_status(notebook_id)
    audio_artifact = next(a for a in artifacts if a.id == audio.artifact_id)
    if audio_artifact.status == "completed":
        console.print(f"Download: {audio_artifact.download_url}")
        break
    await asyncio.sleep(10)
```

**When to use:** Building content generation workflows.

---

### 04_study_tools.py - Educational Content

**Purpose:** Create flashcards, quizzes, and data tables.

**What it demonstrates:**
- Generating flashcards with difficulty levels
- Creating quizzes with custom question counts
- Extracting structured data into tables
- Study artifact management

**Key patterns:**
- Difficulty parameter configuration
- Custom prompts for data extraction
- Multi-language support

**Code walkthrough:**

```python
# Create flashcards
flashcards = await client.study.create_flashcards(
    notebook_id,
    source_ids,
    difficulty="hard",
    card_count=20
)

# Create quiz
quiz = await client.study.create_quiz(
    notebook_id,
    source_ids,
    question_count=10,
    difficulty=2  # medium
)

# Extract data table
table = await client.study.create_data_table(
    notebook_id,
    source_ids,
    description="Extract all dates and events mentioned",
    language="en"
)
```

**When to use:** Building educational automation or study aids.

---

### 05_mind_maps.py - Visualization

**Purpose:** Generate and export mind maps from notebook sources.

**What it demonstrates:**
- Creating mind maps from all sources
- Listing existing mind maps
- Exporting to JSON, OPML, and FreeMind formats
- Mind map structure parsing

**Key patterns:**
- Two-step generation (generate + save)
- Format conversion utilities
- File I/O for exports

**Code walkthrough:**

```python
# Create mind map
mind_map = await client.mindmaps.create(
    notebook_id,
    source_ids,
    title="Research Overview"
)

# Export to different formats
import json

# JSON export
json_data = mind_map.data
with open("mindmap.json", "w") as f:
    json.dump(json_data, f, indent=2)

# OPML export
from pynotebooklm.mindmaps import export_to_opml
opml_xml = export_to_opml(json_data)
with open("mindmap.opml", "w") as f:
    f.write(opml_xml)

# FreeMind export
from pynotebooklm.mindmaps import export_to_freemind
freemind_xml = export_to_freemind(json_data)
with open("mindmap.mm", "w") as f:
    f.write(freemind_xml)
```

**When to use:** Visualizing research connections and hierarchies.

---

### 06_batch_operations.py - Concurrent Operations

**Purpose:** Perform multiple operations efficiently with concurrency.

**What it demonstrates:**
- Batch creating notebooks in parallel
- Adding multiple sources concurrently
- Bulk deletion operations
- Rate limiting and chunking strategies

**Key patterns:**
- Using `asyncio.gather()` for parallel execution
- Progress tracking with rich.progress
- Error handling for each operation
- Chunking large batches to respect rate limits

**Code walkthrough:**

```python
# Batch add URLs with progress tracking
tasks = [
    client.sources.add_url(notebook_id, url)
    for url in urls
]

# Execute concurrently
results = []
for coro in asyncio.as_completed(tasks):
    try:
        result = await coro
        results.append(result)
    except PyNotebookLMError as e:
        console.print(f"Error: {e}")

# Rate-limited batch operations (chunking)
chunk_size = 5  # Process 5 at a time
for i in range(0, len(urls), chunk_size):
    chunk = urls[i:i + chunk_size]
    tasks = [client.sources.add_url(notebook_id, url) for url in chunk]
    await asyncio.gather(*tasks, return_exceptions=True)
    await asyncio.sleep(1)  # Rate limit pause
```

**When to use:** Processing large datasets or automating bulk operations.

---

### 07_error_handling.py - Production Patterns

**Purpose:** Demonstrate robust error handling for production systems.

**What it demonstrates:**
- Comprehensive exception handling
- Retry strategies with custom configuration
- Graceful degradation
- Logging and debugging patterns

**Key patterns:**
- Type-specific exception handling
- Using RetryStrategy for transient errors
- Cleanup in finally blocks
- Structured error logging

**Code walkthrough:**

```python
from pynotebooklm.exceptions import (
    AuthenticationError,
    NotebookNotFoundError,
    RateLimitError,
    APIError
)

try:
    async with NotebookLMClient() as client:
        notebook = await client.notebooks.create(name)
        
except AuthenticationError:
    # Don't retry - cookies expired
    console.print("Please run: pynotebooklm auth login")
    
except NotebookNotFoundError:
    # Resource doesn't exist - don't retry
    console.print("Notebook not found")
    
except RateLimitError as e:
    # Retry after delay
    console.print(f"Rate limited. Retry after {e.retry_after}s")
    await asyncio.sleep(e.retry_after)
    
except APIError as e:
    # Check if retryable (5xx errors)
    if e.status_code and 500 <= e.status_code < 600:
        # Retry with backoff
        await retry_with_backoff(operation)
    else:
        raise  # Don't retry 4xx errors
```

**When to use:** Building production-grade automation systems.

---

## Common Patterns

### Async Context Manager Pattern

Always use the async context manager to ensure proper cleanup:

```python
async with NotebookLMClient() as client:
    # Your operations here
    pass
# Browser session automatically closed
```

### Progress Tracking Pattern

Use rich.progress for long-running operations:

```python
from rich.progress import Progress, SpinnerColumn, TextColumn

with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
    task = progress.add_task("Processing...", total=100)
    for i in range(100):
        # Do work
        progress.advance(task)
```

### Error Handling Pattern

Handle specific exceptions and provide actionable feedback:

```python
try:
    result = await client.notebooks.create(name)
except AuthenticationError:
    console.print("[red]Not authenticated. Run: pynotebooklm auth login[/red]")
    return
except PyNotebookLMError as e:
    console.print(f"[red]Error: {e}[/red]")
    raise
```

### Retry Pattern

Use the built-in retry decorator or RetryStrategy:

```python
from pynotebooklm.retry import RetryStrategy, with_retry

# Configure retry strategy
strategy = RetryStrategy(
    max_attempts=5,
    base_delay=2.0,
    max_delay=60.0
)

# Apply to a function
@with_retry(strategy)
async def flaky_operation():
    # Operation that might fail transiently
    pass
```

## Best Practices

1. **Always authenticate before operations**
   ```bash
   poetry run pynotebooklm auth login
   poetry run pynotebooklm auth check
   ```

2. **Use environment variables for configuration**
   ```bash
   export PYNOTEBOOKLM_MAX_RETRIES=5
   export PYNOTEBOOKLM_BASE_DELAY=2.0
   export PYNOTEBOOKLM_DEBUG=1  # Enable debug logging
   ```

3. **Rate limit batch operations**
   - Process in chunks (5-10 items at a time)
   - Add delays between chunks
   - Handle failures gracefully

4. **Clean up resources**
   - Delete test notebooks after use
   - Remove unused sources
   - Clear old studio artifacts

5. **Log operations for debugging**
   ```python
   import logging
   logging.basicConfig(level=logging.INFO)
   logger = logging.getLogger(__name__)
   
   logger.info(f"Created notebook: {notebook.id}")
   logger.error(f"Failed to add source: {e}")
   ```

## Running Examples

### Prerequisites

1. Install dependencies:
   ```bash
   poetry install
   ```

2. Authenticate:
   ```bash
   poetry run pynotebooklm auth login
   ```

3. Verify authentication:
   ```bash
   poetry run pynotebooklm auth check
   ```

### Running Individual Examples

```bash
# Basic usage
poetry run python examples/01_basic_usage.py

# Research workflow
poetry run python examples/02_research_workflow.py

# Content generation
poetry run python examples/03_content_generation.py

# Study tools
poetry run python examples/04_study_tools.py

# Mind maps
poetry run python examples/05_mind_maps.py

# Batch operations
poetry run python examples/06_batch_operations.py

# Error handling
poetry run python examples/07_error_handling.py
```

### Customizing Examples

All examples are designed to be modified for your use case:

1. Edit source URLs, notebook names, etc.
2. Adjust parameters (difficulty, format, length)
3. Add custom error handling
4. Integrate with your existing workflows

## Further Reading

- [Advanced Usage Guide](advanced_usage.md) - Retry strategies, persistent sessions, performance tuning
- [FAQ](faq.md) - Common issues and solutions
- [API Reference](api_reference.md) - Complete API documentation
- [Architecture](architecture.md) - How PyNotebookLM works internally
