# Advanced Usage Guide

This guide covers advanced features and patterns for production use of PyNotebookLM.

## Table of Contents

1. [Retry Strategies & Error Handling](#retry-strategies-error-handling)
2. [Persistent Sessions for Performance](#persistent-sessions-for-performance)
3. [Batch Operations](#batch-operations)
4. [Custom Logging & Debugging](#custom-logging-debugging)
5. [Production Deployment Patterns](#production-deployment-patterns)

---

## Retry Strategies & Error Handling

### Automatic Retry with Exponential Backoff

PyNotebookLM includes built-in retry logic for transient errors:

```python
from pynotebooklm import NotebookLMClient
from pynotebooklm.retry import RetryStrategy, with_retry

# Default retry (3 attempts, 1s base delay)
async with NotebookLMClient() as client:
    notebooks = await client.notebooks.list()  # Auto-retries on failure
```

### Custom Retry Strategy

Configure retry behavior for specific operations:

```python
from pynotebooklm.retry import RetryStrategy, with_retry

# Aggressive retry for critical operations
aggressive_retry = RetryStrategy(
    max_attempts=5,       # Try 5 times
    base_delay=0.5,       # Start with 500ms
    max_delay=30.0,       # Cap at 30 seconds
    exponential_base=2.0, # Double each time
    jitter=True          # Add randomness
)

@with_retry(aggressive_retry)
async def critical_operation():
    async with NotebookLMClient() as client:
        return await client.notebooks.create("Important Notebook")

# Use it
result = await critical_operation()
```

### Environment-Based Configuration

Configure retry via environment variables:

```bash
export PYNOTEBOOKLM_MAX_RETRIES=5
export PYNOTEBOOKLM_BASE_DELAY=2.0
export PYNOTEBOOKLM_MAX_DELAY=60.0
```

```python
from pynotebooklm import NotebookLMClient
from pynotebooklm.retry import RetryStrategy

# Reads from environment
strategy = RetryStrategy()  # Uses env vars
```

### Error Classification

PyNotebookLM categorizes errors for appropriate handling:

**Retryable Errors:**
- `RateLimitError` - Always retried
- `APIError` with 5xx status codes (500, 502, 503, 504)

**Non-Retryable Errors:**
- `AuthenticationError` - Requires re-login
- `NotebookNotFoundError` - Resource doesn't exist
- `APIError` with 4xx status codes (400, 401, 403, 404)

### Comprehensive Error Handling Pattern

```python
from pynotebooklm import NotebookLMClient
from pynotebooklm.exceptions import (
    AuthenticationError,
    RateLimitError,
    APIError,
    NotebookNotFoundError,
    GenerationTimeoutError,
)
import logging

logger = logging.getLogger(__name__)

async def robust_notebook_operation(notebook_id: str):
    """Example of comprehensive error handling."""
    try:
        async with NotebookLMClient() as client:
            # Your operation
            result = await client.chat.query(
                notebook_id=notebook_id,
                question="What are the key points?"
            )
            return result
            
    except AuthenticationError:
        logger.error("Authentication failed. Re-login required.")
        # Trigger re-authentication flow
        raise
        
    except NotebookNotFoundError:
        logger.error(f"Notebook {notebook_id} not found")
        # Handle missing notebook
        return None
        
    except RateLimitError as e:
        logger.warning(f"Rate limited. Retry after {e.retry_after}s")
        # Could implement custom backoff here
        raise
        
    except GenerationTimeoutError as e:
        logger.error(f"Operation timed out after {e.timeout}s")
        # Implement timeout handling (e.g., poll separately)
        raise
        
    except APIError as e:
        if e.status_code and 500 <= e.status_code < 600:
            logger.error(f"Server error {e.status_code}. Will retry automatically")
        else:
            logger.error(f"API error {e.status_code}: {e}")
        raise
        
    except Exception as e:
        logger.exception("Unexpected error in notebook operation")
        raise
```

### Automatic Cookie Refresh

Enable auto-refresh to re-login when cookies expire during a session:

```python
from pynotebooklm import AuthManager, BrowserSession

auth = AuthManager()
async with BrowserSession(auth, auto_refresh=True) as session:
    result = await session.call_rpc("wXbhsf", [None, 1])
```

---

## Persistent Sessions for Performance

### Problem: Browser Startup Overhead

Each `async with NotebookLMClient()` launches a new browser (~3-5s overhead).

### Solution: Reuse Client Context

**❌ Slow (multiple browser launches):**
```python
# Bad: Launches browser 3 times
await get_notebooks()
await create_notebook("Test")
await add_source(notebook_id, url)
```

**✅ Fast (single browser session):**
```python
async with NotebookLMClient() as client:
    # Single browser launch for all operations
    notebooks = await client.notebooks.list()
    new_nb = await client.notebooks.create("Test")
    source = await client.sources.add_url(new_nb.id, "https://example.com")
```

### PersistentBrowserSession (Shared Browser)

Reuse a shared browser instance across client sessions:

```python
from pynotebooklm import NotebookLMClient, PersistentBrowserSession

async with NotebookLMClient(session_class=PersistentBrowserSession) as client:
    notebooks = await client.notebooks.list()
    await client.sources.add_url(notebooks[0].id, "https://example.com")

# Optional: shutdown shared browser when the app exits
await PersistentBrowserSession.shutdown_pool()
```

### Long-Running Service Pattern

For services that handle multiple requests:

```python
import asyncio
from contextlib import asynccontextmanager
from pynotebooklm import NotebookLMClient

class NotebookLMService:
    """Service wrapper for long-running applications."""
    
    def __init__(self):
        self.client: NotebookLMClient | None = None
        
    async def start(self):
        """Initialize service and create client."""
        self.client = NotebookLMClient()
        await self.client.__aenter__()
        
    async def stop(self):
        """Cleanup service and close browser."""
        if self.client:
            await self.client.__aexit__(None, None, None)
            
    async def create_notebook(self, name: str):
        """Create notebook using persistent client."""
        if not self.client:
            raise RuntimeError("Service not started")
        return await self.client.notebooks.create(name)
        
    async def query_notebook(self, notebook_id: str, question: str):
        """Query notebook using persistent client."""
        if not self.client:
            raise RuntimeError("Service not started")
        return await self.client.chat.query(notebook_id, question)

# Usage
service = NotebookLMService()
await service.start()

try:
    # Handle multiple requests without browser restarts
    nb1 = await service.create_notebook("Notebook 1")
    nb2 = await service.create_notebook("Notebook 2")
    result = await service.query_notebook(nb1.id, "Question")
finally:
    await service.stop()
```

### FastAPI Integration Example

```python
from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from pynotebooklm import NotebookLMClient
from pynotebooklm.exceptions import PyNotebookLMError

# Global client instance
notebooklm_client: NotebookLMClient | None = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage NotebookLM client lifecycle."""
    global notebooklm_client
    
    # Startup
    notebooklm_client = NotebookLMClient()
    await notebooklm_client.__aenter__()
    
    yield
    
    # Shutdown
    if notebooklm_client:
        await notebooklm_client.__aexit__(None, None, None)

app = FastAPI(lifespan=lifespan)

@app.post("/notebooks/create")
async def create_notebook(name: str):
    """Create a new notebook."""
    try:
        if not notebooklm_client:
            raise HTTPException(status_code=500, detail="Client not initialized")
            
        notebook = await notebooklm_client.notebooks.create(name)
        return {"id": notebook.id, "name": notebook.name}
        
    except PyNotebookLMError as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/notebooks/{notebook_id}/query")
async def query_notebook(notebook_id: str, question: str):
    """Query a notebook."""
    try:
        if not notebooklm_client:
            raise HTTPException(status_code=500, detail="Client not initialized")
            
        response = await notebooklm_client.chat.query(notebook_id, question)
        return {"answer": response.text}
        
    except PyNotebookLMError as e:
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Batch Operations

### Concurrent Operations with asyncio.gather

Process multiple operations in parallel:

```python
import asyncio
from pynotebooklm import NotebookLMClient

async def batch_create_notebooks(names: list[str]):
    """Create multiple notebooks concurrently."""
    async with NotebookLMClient() as client:
        # Create all notebooks in parallel
        tasks = [
            client.notebooks.create(name)
            for name in names
        ]
        notebooks = await asyncio.gather(*tasks)
        return notebooks

# Usage
names = ["Research 1", "Research 2", "Research 3"]
notebooks = await batch_create_notebooks(names)
```

### Batch Source Addition

Add multiple URLs to a notebook:

```python
async def batch_add_sources(notebook_id: str, urls: list[str]):
    """Add multiple URL sources concurrently."""
    async with NotebookLMClient() as client:
        tasks = [
            client.sources.add_url(notebook_id, url)
            for url in urls
        ]
        sources = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter successful additions
        successful = [s for s in sources if not isinstance(s, Exception)]
        failed = [s for s in sources if isinstance(s, Exception)]
        
        return successful, failed

# Usage
urls = [
    "https://example.com/article1",
    "https://example.com/article2",
    "https://example.com/article3",
]
successful, failed = await batch_add_sources(notebook_id, urls)
print(f"Added {len(successful)} sources, {len(failed)} failed")
```

### Built-In Batch Helpers

Use the built-in batch helpers for common workflows:

```python
async with NotebookLMClient() as client:
    await client.sources.batch_add_urls(notebook_id, urls)
    await client.notebooks.batch_delete(notebook_ids, confirm=True)
```

### Rate-Limited Batch Processing

Process large batches with rate limiting:

```python
import asyncio
from typing import TypeVar, Callable, Any

T = TypeVar('T')

async def rate_limited_batch(
    items: list[T],
    async_func: Callable[[T], Any],
    batch_size: int = 5,
    delay: float = 1.0,
):
    """Process items in batches with delay between batches."""
    results = []
    
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        
        # Process batch concurrently
        batch_results = await asyncio.gather(
            *[async_func(item) for item in batch],
            return_exceptions=True
        )
        results.extend(batch_results)
        
        # Delay between batches
        if i + batch_size < len(items):
            await asyncio.sleep(delay)
            
    return results

# Usage
async def process_url(url: str):
    async with NotebookLMClient() as client:
        notebook = await client.notebooks.create(f"Analysis: {url}")
        await client.sources.add_url(notebook.id, url)
        return notebook

urls = ["url1", "url2", "url3", "url4", "url5", "url6", "url7"]
results = await rate_limited_batch(urls, process_url, batch_size=3, delay=2.0)
```

---

## Custom Logging & Debugging

### Enable Debug Logging

```bash
export PYNOTEBOOKLM_DEBUG=1
```

Or in code:

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Now all PyNotebookLM operations log detailed info
async with NotebookLMClient() as client:
    await client.notebooks.list()  # Logs RPC calls, responses, etc.
```

### Custom Logger Configuration

```python
import logging

# Create custom logger
logger = logging.getLogger('pynotebooklm')
logger.setLevel(logging.INFO)

# Add custom handler (e.g., file logging)
handler = logging.FileHandler('notebooklm.log')
handler.setFormatter(
    logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
)
logger.addHandler(handler)
```

### Request/Response Logging

Log all RPC calls for debugging:

```python
from pynotebooklm import NotebookLMClient
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async with NotebookLMClient() as client:
    # All RPC calls logged with DEBUG level
    notebooks = await client.notebooks.list()
```

### Telemetry Logs

Enable structured telemetry logs for RPC timing and success rates:

```bash
export PYNOTEBOOKLM_TELEMETRY=1
```

---

## Production Deployment Patterns

### Docker Deployment

**Dockerfile:**
```dockerfile
FROM python:3.11-slim

# Install Playwright dependencies
RUN apt-get update && apt-get install -y \
    libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdrm2 libxkbcommon0 libxcomposite1 \
    libxdamage1 libxfixes3 libxrandr2 libgbm1 libasound2 \
    && rm -rf /var/lib/apt/lists/*

# Install PyNotebookLM
RUN pip install pynotebooklm playwright
RUN playwright install chromium --with-deps

# Copy application code
WORKDIR /app
COPY . .

CMD ["python", "app.py"]
```

**Usage:**
```bash
# Build
docker build -t pynotebooklm-app .

# Run (mount auth file)
docker run -v ~/.pynotebooklm:/root/.pynotebooklm pynotebooklm-app
```

### Health Checks

Implement health checks for services:

```python
from pynotebooklm import NotebookLMClient
from pynotebooklm.exceptions import AuthenticationError

async def health_check():
    """Check if NotebookLM service is healthy."""
    try:
        async with NotebookLMClient() as client:
            # Simple operation to verify connectivity
            await client.notebooks.list()
            return {"status": "healthy"}
    except AuthenticationError:
        return {"status": "unhealthy", "reason": "authentication_failed"}
    except Exception as e:
        return {"status": "unhealthy", "reason": str(e)}
```

### Graceful Shutdown

Handle shutdown signals properly:

```python
import signal
import asyncio

class GracefulShutdown:
    def __init__(self):
        self.shutdown_event = asyncio.Event()
        
    def signal_handler(self, signum, frame):
        print(f"Received signal {signum}, initiating shutdown...")
        self.shutdown_event.set()

graceful = GracefulShutdown()
signal.signal(signal.SIGINT, graceful.signal_handler)
signal.signal(signal.SIGTERM, graceful.signal_handler)

# In async main
async def main():
    service = NotebookLMService()
    await service.start()
    
    try:
        # Wait for shutdown signal
        await graceful.shutdown_event.wait()
    finally:
        await service.stop()
```

### Cookie Refresh Automation

Automate cookie refresh to prevent expiration:

```python
import asyncio
from datetime import datetime, timedelta
from pynotebooklm.auth import AuthManager

async def cookie_refresh_worker():
    """Background task to refresh cookies every 2 weeks."""
    auth = AuthManager()
    
    while True:
        # Wait 13 days (refresh before 14-day expiration)
        await asyncio.sleep(13 * 24 * 60 * 60)
        
        try:
            print("Refreshing authentication cookies...")
            await auth.refresh()
            print("Cookies refreshed successfully")
        except Exception as e:
            print(f"Failed to refresh cookies: {e}")

# Run as background task
asyncio.create_task(cookie_refresh_worker())
```

---

## Best Practices Summary

1. **Always use async context managers** - Ensures proper cleanup
2. **Reuse client instances** - Avoid repeated browser launches
3. **Implement retry logic** - Handle transient errors gracefully
4. **Use batch operations** - Process multiple items efficiently
5. **Enable logging** - Debug issues with detailed logs
6. **Handle errors specifically** - Catch appropriate exception types
7. **Monitor cookie expiration** - Implement refresh automation
8. **Rate limit batch operations** - Avoid overwhelming the API
9. **Implement health checks** - Monitor service availability
10. **Test error scenarios** - Ensure robust error handling

See `examples/07_error_handling.py` for complete code examples.
