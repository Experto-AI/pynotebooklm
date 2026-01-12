# Frequently Asked Questions (FAQ)

## Authentication & Cookies

### Q: How long do authentication cookies last?
**A:** Typically 2-4 weeks. When cookies expire, you'll get an `AuthenticationError`. You can re-authenticate with `pynotebooklm auth login` or enable auto-refresh with `BrowserSession(auto_refresh=True)` for long-running sessions.

### Q: Where are cookies stored?
**A:** Cookies are stored in `~/.pynotebooklm/auth.json`. This file contains sensitive session data - never share it or commit it to version control.

### Q: Can I use PyNotebookLM with Google Workspace accounts?
**A:** PyNotebookLM is primarily tested with personal Google accounts. Workspace accounts may work but haven't been extensively tested. Some organizations may block automated access.

### Q: What happens if I'm not authenticated?
**A:** You'll receive an `AuthenticationError` when trying to use any client method. Run `pynotebooklm auth login` first.

### Q: Can I use environment variables for authentication?
**A:** Not currently recommended for production. The browser-based authentication flow is the most reliable method.

## Rate Limiting

### Q: What are the rate limits?
**A:** NotebookLM has internal rate limits that vary by operation. The exact limits aren't publicly documented. PyNotebookLM automatically handles rate limits with exponential backoff.

### Q: How does retry logic work?
**A:** When a rate limit (429) or transient error (5xx) occurs, PyNotebookLM:
1. Waits using exponential backoff (1s, 2s, 4s, ...)
2. Adds random jitter to prevent thundering herd
3. Retries up to 3 times by default
4. Throws the error if all retries fail

### Q: Can I customize retry behavior?
**A:** Yes! Set environment variables:
```bash
export PYNOTEBOOKLM_MAX_RETRIES=5
export PYNOTEBOOKLM_BASE_DELAY=2.0
export PYNOTEBOOKLM_MAX_DELAY=60.0
```

Or use custom retry strategy:
```python
from pynotebooklm.retry import RetryStrategy, with_retry

@with_retry(RetryStrategy(max_attempts=5, base_delay=2.0))
async def my_function():
    # Your code here
    pass
```

## Content Generation

### Q: How long does content generation take?
**A:** 
- **Audio overviews**: 60-180 seconds
- **Video overviews**: 120-300 seconds
- **Infographics**: 60-120 seconds
- **Slide decks**: 60-180 seconds
- **Flashcards/Quiz**: 30-60 seconds

Use `pynotebooklm studio status <notebook_id>` to check progress.

### Q: Why is my content generation stuck "in progress"?
**A:** Content generation is asynchronous. It can take several minutes. If it's stuck for > 10 minutes:
1. Check if you have enough sources (minimum 1-2 recommended)
2. Verify your network connection
3. Try again - internal API might have had a temporary issue

### Q: Can I download generated content?
**A:** Yes! When generation completes, use:
```bash
pynotebooklm studio status <notebook_id>
```
This shows download URLs for audio (MP3), video (MP4), infographics (PDF), etc.

### Q: How many sources do I need for content generation?
**A:** Minimum 1 source, but 2-5 sources provide better results. Too many sources (> 50) may make generation slower.

## Research Discovery

### Q: What's the difference between standard and deep research?
**A:**
- **Standard**: Fast (~15-30s), finds 5-10 sources, good for quick research
- **Deep**: Comprehensive (~60-120s), finds 10-20 sources, includes detailed report

### Q: Can I search Google Drive with research?
**A:** Yes! Use `--source drive` flag:
```bash
pynotebooklm research start <notebook_id> "topic" --source drive
```

### Q: How do I import discovered sources?
**A:** Two methods:

1. Automatic import while polling:
```bash
pynotebooklm research poll <notebook_id> --auto-import
```

2. Manual import after research completes:
```bash
pynotebooklm research import <notebook_id>
```

### Q: Can I import specific sources, not all?
**A:** Yes! Use the `--indices` flag:
```bash
pynotebooklm research import <notebook_id> --indices 0,1,2
```

## Performance

### Q: Why is browser startup slow?
**A:** First startup takes 3-5 seconds as Playwright launches Chrome. This is normal. For better performance, reuse the client within a single async context:

```python
async with NotebookLMClient() as client:
    # Multiple operations here
    await client.notebooks.list()
    await client.sources.add_url(...)
    # Browser stays open for all operations
```

### Q: Can I make operations faster?
**A:** Yes:
1. **Reuse client context** - keeps browser open
2. **Use batch operations** - multiple calls in one session
3. **For bulk operations** - consider parallel execution with `asyncio.gather()`

### Q: Is there a way to keep browser open between scripts?
**A:** Not currently. Each script invocation starts a new browser session. For long-running operations, wrap everything in a single async context.

## Errors & Debugging

### Q: I'm getting "Browser automation failed"
**A:** This usually means Playwright browser isn't installed:
```bash
playwright install chromium
```

Or your system is missing dependencies. On Linux:
```bash
sudo apt-get install -y \
    libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdrm2 libxkbcommon0 libxcomposite1 \
    libxdamage1 libxfixes3 libxrandr2 libgbm1 libasound2
```

### Q: How do I enable debug logging?
**A:** Set environment variable:
```bash
export PYNOTEBOOKLM_DEBUG=1
```

Or in Python:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Q: I'm getting "Session not active" errors
**A:** You're trying to call methods outside the async context manager. Use:
```python
async with NotebookLMClient() as client:
    # All operations here
```

### Q: What does "CSRF token not found" mean?
**A:** Rare error indicating the page structure changed or cookies are invalid. Try:
1. Re-authenticate: `pynotebooklm auth login`
2. Clear cookies: `rm ~/.pynotebooklm/auth.json` then login again
3. Report bug if persistent

## Notebooks & Sources

### Q: What types of sources are supported?
**A:**
- **URLs**: Any public webpage
- **YouTube**: Videos (auto-detected from URL)
- **Google Drive**: Docs, Sheets, PDFs (requires Drive permission)
- **Text**: Plain text snippets, notes, summaries

### Q: Can I add local files?
**A:** Not directly. Workaround: add as text source by reading file content:
```python
with open("file.txt") as f:
    content = f.read()
await client.sources.add_text(notebook_id, "My File", content)
```

### Q: How many notebooks/sources can I have?
**A:** NotebookLM doesn't publish hard limits. In practice:
- **Notebooks**: 100+ is fine
- **Sources per notebook**: 50+ works, but generation slows down

### Q: Can I organize notebooks into folders?
**A:** NotebookLM doesn't support folders natively. Use naming conventions:
```python
await client.notebooks.create("Project A - Research")
await client.notebooks.create("Project A - Analysis")
await client.notebooks.create("Project B - Planning")
```

## Docker & Deployment

### Q: Can I run PyNotebookLM in Docker?
**A:** Yes! A Dockerfile is provided. Note that authentication requires browser access, so you'll need to:
1. Authenticate on host machine first
2. Mount `~/.pynotebooklm/auth.json` into container
```bash
docker run -v ~/.pynotebooklm:/root/.pynotebooklm pynotebooklm
```

### Q: Can I deploy PyNotebookLM as a web service?
**A:** Possible, but challenging. Each request needs a browser context. Consider:
- **Serverless**: Cold starts are slow (~5s)
- **Long-running service**: Better performance, but needs state management
- **Cookie rotation**: Implement automatic refresh every 2 weeks

### Q: Is PyNotebookLM production-ready?
**A:** For automated workflows, yes. For high-traffic web services, consider:
- Rate limiting (NotebookLM enforces limits)
- Cookie refresh automation
- Error handling and retry logic
- Cost of browser automation (memory/CPU)

## Contributing & Support

### Q: How do I report bugs?
**A:** Open an issue on GitHub with:
- Error message and stack trace
- Steps to reproduce
- Python version and OS
- Log output (with `PYNOTEBOOKLM_DEBUG=1`)

### Q: Can I contribute?
**A:** Yes! See `CONTRIBUTING.md` for guidelines.

### Q: Is this library officially supported by Google?
**A:** No. This is an unofficial library using NotebookLM's internal APIs. It may break if Google changes their API.

### Q: Will Google block my account?
**A:** Unlikely if used reasonably. Don't:
- Make thousands of requests per hour
- Share your account cookies
- Automate on behalf of many users

### Q: Where can I get help?
**A:** 
1. Check this FAQ and documentation
2. Search GitHub issues
3. Open a new issue with details
4. Review examples in `examples/` directory
