<!--
DOCUMENTATION SCOPE: This file contains technical deep dives into specific complex topics.
DO NOT include here: General architecture or basic API usage.
-->

# Technical Deep Dives

## Browser Automation Patterns

### Playwright Session Management
We use `playwright.async_api` to manage the browser lifecycle.

```python
class BrowserSession:
    async def __aenter__(self):
        # Starts Playwright, launches Chromium (headless)
        # Injects saved cookies into the context
        # Navigates to the base URL
        return self

    async def call_api(self, endpoint, data):
        # Uses page.evaluate() to execute fetch() in the browser context
        # This bypasses CORS and complex header signing requirements
        # by reusing the browser's authenticated state.
```

### Why page.evaluate()?
Instead of trying to replicate all headers and signatures in Python's `httpx`, we execute the network request *inside* the browser using JavaScript's `fetch`. This ensures:
1.  All cookies are attached automatically.
2.  Origin/Referer headers are correct.
3.  Google's internal request signatures are handled by their client-side scripts if necessary (though `batchexecute` usually only needs cookies + CSRF).

## Async Polling for Generation

Content generation (podcasts, videos) takes significant time (1-5 minutes).

### Strategy: Exponential Backoff
We implement a robust polling mechanism:

1.  **Initial call**: Triggers generation, returns an `artifact_id`.
2.  **Poll Loop**: Calls `get_status(artifact_id)`.
3.  **Backoff**: `sleep(delay)` where delay increases (2s -> 3s -> 4.5s -> ... max 10s).
4.  **Timeout**: Raises `GenerationTimeoutError` if it exceeds 300s (5 mins).
5.  **Completion**: Returns the final artifact with the download URL.

```python
async def poll_until_ready(artifact_id):
    delay = 2.0
    while True:
        status = await check_status(artifact_id)
        if status.is_ready: break
        await asyncio.sleep(delay)
        delay = min(delay * 1.5, 10.0)
```
