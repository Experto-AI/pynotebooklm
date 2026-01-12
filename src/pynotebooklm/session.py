"""
Browser session management for PyNotebookLM.

This module provides the BrowserSession class for managing Playwright browser
contexts and making API calls to NotebookLM's internal endpoints.
"""

import asyncio
import json
import logging
import os
import re
import time
import urllib.parse
from collections.abc import Awaitable, Callable
from datetime import datetime, timedelta
from typing import Any, Literal

from playwright.async_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
    async_playwright,
)

from .auth import AuthManager
from .exceptions import (
    APIError,
    AuthenticationError,
    BrowserError,
    RateLimitError,
    SessionError,
)
from .retry import with_retry

logger = logging.getLogger(__name__)

# NotebookLM API configuration
NOTEBOOKLM_URL = "https://notebooklm.google.com"
BATCH_EXECUTE_URL = f"{NOTEBOOKLM_URL}/_/LabsTailwindUi/data/batchexecute"

# Anti-XSSI prefix used by Google APIs
ANTI_XSSI_PREFIX = ")]}'\n"

DEBUG_ENV_VAR = "PYNOTEBOOKLM_DEBUG"
TELEMETRY_ENV_VAR = "PYNOTEBOOKLM_TELEMETRY"
DEFAULT_STREAMING_TIMEOUT_MS = 120000
DEFAULT_CSRF_TTL_SECONDS = 300

AUTH_REDIRECT_MARKERS = ("accounts.google.com", "ServiceLogin")


def _env_flag(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}


def _sanitize_headers(headers: dict[str, str]) -> dict[str, str]:
    sanitized = {}
    for key, value in headers.items():
        if key.lower() in {"cookie", "authorization"}:
            sanitized[key] = "[REDACTED]"
        else:
            sanitized[key] = value
    return sanitized


def _sanitize_text(text: str) -> str:
    if not text:
        return text
    text = re.sub(r"(at=)[^&]+", r"\1[REDACTED]", text)
    text = re.sub(
        r"(?i)(sid|hsid|ssid|apisid|sapisid)=([^;\s]+)", r"\1=[REDACTED]", text
    )
    return text


def _log_if_debug(log_fn: Callable[[str], None], message: str) -> None:
    if _env_flag(DEBUG_ENV_VAR):
        log_fn(message)


class BrowserSession:
    """
    Manages a Playwright browser session for NotebookLM API calls.

    This class provides an async context manager for browser lifecycle
    and methods for making API calls via page.evaluate().

    Example:
        >>> auth = AuthManager()
        >>> async with BrowserSession(auth) as session:
        ...     result = await session.call_rpc("wXbhsf", [None, 1, None, [2]])
        ...     print(result)

    Attributes:
        auth: AuthManager instance for cookie management.
        headless: Whether to run browser in headless mode.
    """

    def __init__(
        self,
        auth: AuthManager,
        headless: bool = True,
        timeout: int = 60000,
        auto_refresh: bool = False,
        block_resources: bool = True,
        streaming_timeout: int = DEFAULT_STREAMING_TIMEOUT_MS,
        csrf_cache_ttl: int = DEFAULT_CSRF_TTL_SECONDS,
        wait_until: Literal[
            "commit", "domcontentloaded", "load", "networkidle"
        ] = "load",
    ) -> None:
        """
        Initialize the browser session.

        Args:
            auth: AuthManager instance with valid authentication.
            headless: Whether to run browser in headless mode.
            timeout: Default timeout for page operations in milliseconds.
            auto_refresh: Whether to refresh cookies on auth failures.
            block_resources: Block images/fonts/media to speed page load.
            streaming_timeout: Timeout for streaming endpoints (milliseconds).
            csrf_cache_ttl: Cache TTL for CSRF tokens (seconds).
            wait_until: Playwright wait_until strategy for page navigation.
        """
        self.auth = auth
        self.headless = headless
        self.timeout = timeout
        self.auto_refresh = auto_refresh
        self.block_resources = block_resources
        self.streaming_timeout = streaming_timeout
        self.csrf_cache_ttl = timedelta(seconds=csrf_cache_ttl)
        self.wait_until = wait_until

        # These are set in __aenter__
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None
        self._csrf_token: str | None = None
        self._csrf_cached_at: datetime | None = None
        self._rpc_calls = 0
        self._rpc_failures = 0

    def _launch_args(self) -> list[str]:
        """Return Chromium launch args optimized for speed."""
        return [
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
            "--disable-extensions",
            "--disable-gpu",
        ]

    def _context_options(self) -> dict[str, Any]:
        """Return BrowserContext options."""
        return {
            "viewport": {"width": 1280, "height": 800},
            "user_agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        }

    async def _apply_resource_blocking(self, context: BrowserContext) -> None:
        """Block non-essential resources for faster page loads."""
        await context.route("**/*", self._route_request)

    async def _route_request(self, route: Any, request: Any) -> None:
        if request.resource_type in {"image", "media", "font", "stylesheet"}:
            await route.abort()
        else:
            await route.continue_()

    def _is_authenticated_page(self) -> bool:
        if self._page is None:
            return False
        return not any(marker in self._page.url for marker in AUTH_REDIRECT_MARKERS)

    async def _check_auth_validity(self) -> None:
        """Raise AuthenticationError if cookies appear invalid."""
        if self.auth.is_expired():
            raise AuthenticationError("Authentication expired. Please login again.")
        if not self._is_authenticated_page():
            raise AuthenticationError("Cookies expired or invalid. Please login again.")

    async def _ensure_csrf_token(self) -> None:
        """Refresh CSRF token if cache has expired."""
        if self._page is None:
            return
        if self._csrf_token and self._csrf_cached_at:
            if datetime.now() - self._csrf_cached_at <= self.csrf_cache_ttl:
                return
        self._csrf_token = await self._extract_csrf_token()
        self._csrf_cached_at = datetime.now()

    async def _refresh_session(self) -> None:
        """Refresh cookies and recreate the browser context."""
        await self.auth.refresh()
        if self._browser is None:
            raise SessionError("Browser not active")

        if self._page:
            await self._page.close()
            self._page = None
        if self._context:
            await self._context.close()
            self._context = None

        self._context = await self._browser.new_context(**self._context_options())
        if self.block_resources:
            await self._apply_resource_blocking(self._context)
        await self._context.add_cookies(self.auth.get_cookies())  # type: ignore[arg-type]

        self._page = await self._context.new_page()
        self._page.set_default_timeout(self.timeout)
        await self._page.goto(NOTEBOOKLM_URL, wait_until=self.wait_until)

        if not self._is_authenticated_page():
            raise AuthenticationError("Cookies expired or invalid after refresh.")

        self._csrf_token = await self._extract_csrf_token()
        self._csrf_cached_at = datetime.now()

    def _response_indicates_auth_failure(self, text: str) -> bool:
        return any(marker in text for marker in AUTH_REDIRECT_MARKERS)

    def _emit_telemetry(self, rpc_id: str, duration_ms: float, success: bool) -> None:
        if not _env_flag(TELEMETRY_ENV_VAR):
            return
        payload = {
            "event": "rpc_call",
            "rpc_id": rpc_id,
            "duration_ms": round(duration_ms, 2),
            "success": success,
            "total_calls": self._rpc_calls,
            "total_failures": self._rpc_failures,
        }
        logger.info(json.dumps(payload))

    async def __aenter__(self) -> "BrowserSession":
        """
        Enter the async context manager.

        Launches browser, injects cookies, and navigates to NotebookLM.

        Returns:
            Self for use in async with statements.

        Raises:
            AuthenticationError: If not authenticated.
            BrowserError: If browser launch fails.
        """
        if not self.auth.is_authenticated():
            raise AuthenticationError(
                "Not authenticated. Please run 'pynotebooklm auth login' first."
            )

        try:
            logger.debug("Starting Playwright...")
            self._playwright = await async_playwright().start()

            logger.debug("Launching browser (headless=%s)...", self.headless)
            self._browser = await self._playwright.chromium.launch(
                headless=self.headless,
                args=self._launch_args(),
            )

            # Create context with cookies
            logger.debug("Creating browser context with cookies...")
            self._context = await self._browser.new_context(**self._context_options())
            if self.block_resources:
                await self._apply_resource_blocking(self._context)

            # Add cookies (Playwright expects SetCookieParam which matches our dict format)
            await self._context.add_cookies(self.auth.get_cookies())  # type: ignore[arg-type]

            # Create page and navigate
            self._page = await self._context.new_page()
            self._page.set_default_timeout(self.timeout)

            logger.debug("Navigating to NotebookLM...")
            await self._page.goto(NOTEBOOKLM_URL, wait_until=self.wait_until)

            # Verify we're authenticated
            if not self._is_authenticated_page():
                raise AuthenticationError(
                    "Cookies expired or invalid. Please login again."
                )

            # Extract CSRF token
            self._csrf_token = await self._extract_csrf_token()
            self._csrf_cached_at = datetime.now()
            logger.info(
                "Browser session ready (CSRF token: %s)", bool(self._csrf_token)
            )

            return self

        except AuthenticationError:
            await self._cleanup()
            raise
        except Exception as e:
            await self._cleanup()
            logger.error("Failed to start browser session: %s", e)
            raise BrowserError(f"Failed to start browser session: {e}") from e

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Exit the async context manager and cleanup resources."""
        await self._cleanup()

    async def _cleanup(self) -> None:
        """Clean up browser resources."""
        if self._page:
            try:
                await self._page.close()
            except Exception:
                pass
            self._page = None

        if self._context:
            try:
                await self._context.close()
            except Exception:
                pass
            self._context = None

        if self._browser:
            try:
                await self._browser.close()
            except Exception:
                pass
            self._browser = None

        if self._playwright:
            try:
                await self._playwright.stop()
            except Exception:
                pass
            self._playwright = None

        self._csrf_token = None
        self._csrf_cached_at = None
        logger.debug("Browser session cleaned up")

    async def _extract_csrf_token(self) -> str | None:
        """
        Extract CSRF token (SNlM0e) from page.

        Returns:
            CSRF token string or None if not found.
        """
        if self._page is None:
            return None

        try:
            token = await self._page.evaluate(
                """
                () => {
                    const scripts = document.querySelectorAll('script');
                    for (const script of scripts) {
                        const match = script.textContent?.match(/SNlM0e":"([^"]+)/);
                        if (match) return match[1];
                    }
                    return null;
                }
                """
            )
            return str(token) if token else None
        except Exception as e:
            logger.warning("Failed to extract CSRF token: %s", e)
            return None

    @property
    def page(self) -> Page:
        """Get the current page, raising if session not active."""
        if self._page is None:
            raise SessionError("Browser session not active. Use 'async with' context.")
        return self._page

    @property
    def csrf_token(self) -> str | None:
        """Get the CSRF token."""
        return self._csrf_token

    async def ensure_csrf_token(self) -> None:
        """Ensure the CSRF token is refreshed if cache expired."""
        await self._ensure_csrf_token()

    @with_retry()
    async def call_rpc(
        self,
        rpc_id: str,
        params: list[Any],
        timeout: int | None = None,
    ) -> Any:
        """
        Call a NotebookLM internal RPC endpoint.

        Args:
            rpc_id: The RPC function ID (e.g., "wXbhsf" for list notebooks).
            params: Parameters to pass to the RPC function.
            timeout: Optional timeout in milliseconds.

        Returns:
            Parsed response data from the RPC call.

        Raises:
            SessionError: If session not active.
            APIError: If the API returns an error.
            RateLimitError: If rate limited.
        """
        if self._page is None:
            raise SessionError("Browser session not active")

        logger.debug("Calling RPC %s with params: %s", rpc_id, params)

        attempt_refresh = self.auto_refresh
        last_error: Exception | None = None

        for attempt in range(2 if attempt_refresh else 1):
            duration_ms = 0.0
            try:
                await self._check_auth_validity()
                await self._ensure_csrf_token()

                # Build the request payload
                payload = self._encode_payload(rpc_id, params)
                _log_if_debug(
                    logger.debug,
                    f"RPC payload {rpc_id}: {_sanitize_text(payload)}",
                )

                self._rpc_calls += 1
                start_time = time.perf_counter()
                response = await self._page.evaluate(
                    """
                    async (payload) => {
                        const response = await fetch(payload.url, {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/x-www-form-urlencoded',
                            },
                            body: payload.body,
                            credentials: 'include',
                        });

                        return {
                            ok: response.ok,
                            status: response.status,
                            statusText: response.statusText,
                            text: await response.text(),
                        };
                    }
                    """,
                    {
                        "url": BATCH_EXECUTE_URL,
                        "body": payload,
                    },
                )
                duration_ms = (time.perf_counter() - start_time) * 1000

                response_text = str(response.get("text", ""))
                _log_if_debug(
                    logger.debug,
                    f"RPC response {rpc_id}: {_sanitize_text(response_text)}",
                )

                if self._response_indicates_auth_failure(response_text):
                    raise AuthenticationError("Authentication expired during RPC call.")

                result = self._parse_response(response)
                self._emit_telemetry(rpc_id, duration_ms, True)
                return result

            except AuthenticationError as e:
                last_error = e
                if attempt_refresh and attempt == 0:
                    logger.info("Authentication failed; attempting auto-refresh.")
                    await self._refresh_session()
                    continue
                raise
            except Exception as e:
                if isinstance(e, APIError | RateLimitError):
                    self._rpc_failures += 1
                    self._emit_telemetry(rpc_id, duration_ms, False)
                    raise
                last_error = e
                self._rpc_failures += 1
                self._emit_telemetry(rpc_id, duration_ms, False)
                logger.error("RPC call failed: %s", e)
                raise APIError(f"RPC call failed: {e}") from e

        if last_error:
            raise last_error
        raise APIError("RPC call failed unexpectedly")

    def _encode_payload(self, rpc_id: str, params: list[Any]) -> str:
        """
        Encode RPC parameters into request body format.

        Args:
            rpc_id: The RPC function ID.
            params: Parameters for the RPC call.

        Returns:
            URL-encoded request body string.
        """
        # Build the JSON payload structure
        # Format: [[[rpc_id, json_params, null, "generic"]]]
        json_params = json.dumps(params, separators=(",", ":"))
        inner = [[rpc_id, json_params, None, "generic"]]
        full_payload = json.dumps([inner], separators=(",", ":"))

        # URL encode the payload
        encoded = urllib.parse.quote(full_payload)

        # Build the request body
        body_parts = [
            f"f.req={encoded}",
        ]

        # Add CSRF token if available
        if self._csrf_token:
            body_parts.append(f"at={urllib.parse.quote(self._csrf_token)}")

        return "&".join(body_parts)

    def _parse_response(self, response: dict[str, Any]) -> Any:
        """
        Parse RPC response data.

        Args:
            response: Raw response dict with status and text.

        Returns:
            Parsed response data.

        Raises:
            APIError: If response indicates an error.
            RateLimitError: If rate limited.
        """
        status = response.get("status", 0)
        text = response.get("text", "")

        # Check for rate limiting
        if status == 429:
            raise RateLimitError("Rate limit exceeded", retry_after=60)

        # Check for errors
        if not response.get("ok", False):
            raise APIError(
                f"API returned error: {response.get('statusText', 'Unknown')}",
                status_code=status,
                response_body=text,
            )

        # Remove anti-XSSI prefix
        if text.startswith(ANTI_XSSI_PREFIX):
            text = text[len(ANTI_XSSI_PREFIX) :]

        # Get all non-empty lines
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        if not lines:
            raise APIError("Empty response from API")

        # Remove byte count lines
        data_lines = [line for line in lines if not line.isdigit()]
        if not data_lines:
            snippet = text[:200]
            raise APIError(f"No data lines found in response: {snippet}")

        def unwrap_payload(data: Any) -> Any:
            if isinstance(data, list) and len(data) > 0:
                inner = data[0]
                if isinstance(inner, list) and len(inner) > 2:
                    result_str = inner[2]
                    if isinstance(result_str, str):
                        return json.loads(result_str)
                    return result_str
            return data

        buffer = ""
        last_error: Exception | None = None
        for line in data_lines:
            buffer += line
            try:
                parsed = json.loads(buffer)
                return unwrap_payload(parsed)
            except json.JSONDecodeError as e:
                last_error = e
                # Likely incomplete chunk; keep buffering.
                if e.msg.lower().startswith("unterminated") or e.msg.lower().startswith(
                    "expecting"
                ):
                    continue
                # Reset buffer for malformed chunk.
                buffer = ""
                continue
            except (IndexError, TypeError) as e:
                last_error = e
                buffer = ""

        snippet = _sanitize_text(text[:300])
        if last_error:
            logger.error("Failed to parse response: %s", last_error)
            raise APIError(
                f"Failed to parse response: {last_error} (snippet: {snippet})"
            )
        raise APIError(f"Failed to parse response (snippet: {snippet})")

    def parse_streaming_response(self, response_text: str) -> list[Any]:
        """
        Parse streaming responses into JSON chunks.

        Handles partial/incomplete chunks gracefully by buffering lines.
        """
        if not response_text:
            return []

        if response_text.startswith(")]}'"):
            response_text = response_text[4:]

        lines = [line.strip() for line in response_text.split("\n") if line.strip()]
        chunks: list[Any] = []
        buffer = ""

        for line in lines:
            if line.isdigit():
                continue
            buffer += line
            try:
                chunks.append(json.loads(buffer))
                buffer = ""
            except json.JSONDecodeError as e:
                if e.msg.lower().startswith("unterminated") or e.msg.lower().startswith(
                    "expecting"
                ):
                    continue
                logger.debug(
                    "Skipping malformed streaming chunk: %s", _sanitize_text(line[:200])
                )
                buffer = ""

        if buffer:
            logger.debug(
                "Dropped incomplete streaming chunk: %s", _sanitize_text(buffer[:200])
            )

        return chunks

    async def call_api_raw(
        self,
        endpoint: str,
        method: str = "GET",
        body: str | None = None,
        headers: dict[str, str] | None = None,
        timeout_ms: int | None = None,
    ) -> str:
        """
        Make a raw API call via the browser context.

        Args:
            endpoint: API endpoint URL.
            method: HTTP method.
            body: Request body string.
            headers: Additional headers.
            timeout_ms: Timeout in milliseconds for streaming endpoints.

        Returns:
            Raw response text.

        Raises:
            SessionError: If session not active.
            APIError: If request fails.
        """
        if self._page is None:
            raise SessionError("Browser session not active")

        attempt_refresh = self.auto_refresh
        for attempt in range(2 if attempt_refresh else 1):
            try:
                await self._check_auth_validity()
                await self._ensure_csrf_token()

                sanitized_headers = _sanitize_headers(headers or {})
                _log_if_debug(
                    logger.debug,
                    f"API raw request {method} {endpoint} headers={sanitized_headers} body={_sanitize_text(body or '')}",
                )

                response = await self._page.evaluate(
                    """
                    async (args) => {
                        const controller = new AbortController();
                        const timeoutId = args.timeoutMs
                            ? setTimeout(() => controller.abort(), args.timeoutMs)
                            : null;

                        const options = {
                            method: args.method,
                            headers: args.headers || {},
                            credentials: 'include',
                            signal: controller.signal,
                        };

                        if (args.body) {
                            options.body = args.body;
                        }

                        let response;
                        try {
                            response = await fetch(args.endpoint, options);
                        } catch (error) {
                            return {
                                ok: false,
                                status: 0,
                                statusText: error && error.name ? error.name : 'FetchError',
                                text: '',
                            };
                        } finally {
                            if (timeoutId) {
                                clearTimeout(timeoutId);
                            }
                        }

                        return {
                            ok: response.ok,
                            status: response.status,
                            statusText: response.statusText,
                            text: await response.text().catch(() => ''),
                        };
                    }
                    """,
                    {
                        "endpoint": endpoint,
                        "method": method,
                        "body": body,
                        "headers": headers or {},
                        "timeoutMs": timeout_ms or self.streaming_timeout,
                    },
                )

                response_text = str(response.get("text", ""))
                _log_if_debug(
                    logger.debug,
                    f"API raw response {endpoint}: {_sanitize_text(response_text)}",
                )

                if self._response_indicates_auth_failure(response_text):
                    raise AuthenticationError("Authentication expired during API call.")

                if not response.get("ok"):
                    raise APIError(
                        f"API request failed: {response.get('statusText')}",
                        status_code=response.get("status"),
                        response_body=response_text,
                    )

                return response_text

            except AuthenticationError:
                if attempt_refresh and attempt == 0:
                    logger.info("Authentication failed; attempting auto-refresh.")
                    await self._refresh_session()
                    continue
                raise
            except APIError:
                raise
            except Exception as e:
                raise APIError(f"API call failed: {e}") from e

        raise APIError("API call failed after refresh")

    async def call_api(
        self,
        endpoint: str,
        method: str = "GET",
        data: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """
        Make a generic API call via the browser context.

        Args:
            endpoint: API endpoint URL.
            method: HTTP method.
            data: Request body data.
            headers: Additional headers.

        Returns:
            Parsed JSON response.

        Raises:
            SessionError: If session not active.
            APIError: If request fails.
        """
        if self._page is None:
            raise SessionError("Browser session not active")

        attempt_refresh = self.auto_refresh
        for attempt in range(2 if attempt_refresh else 1):
            try:
                await self._check_auth_validity()
                await self._ensure_csrf_token()

                sanitized_headers = _sanitize_headers(headers or {})
                _log_if_debug(
                    logger.debug,
                    f"API request {method} {endpoint} headers={sanitized_headers} data={data}",
                )

                response = await self._page.evaluate(
                    """
                    async (args) => {
                        const options = {
                            method: args.method,
                            headers: args.headers || {},
                            credentials: 'include',
                        };

                        if (args.data) {
                            options.body = JSON.stringify(args.data);
                            options.headers['Content-Type'] = 'application/json';
                        }

                        const response = await fetch(args.endpoint, options);

                        return {
                            ok: response.ok,
                            status: response.status,
                            json: await response.json().catch(() => null),
                            text: await response.text().catch(() => ''),
                        };
                    }
                    """,
                    {
                        "endpoint": endpoint,
                        "method": method,
                        "data": data,
                        "headers": headers or {},
                    },
                )

                response_text = str(response.get("text", ""))
                _log_if_debug(
                    logger.debug,
                    f"API response {endpoint}: {_sanitize_text(response_text)}",
                )

                if self._response_indicates_auth_failure(response_text):
                    raise AuthenticationError("Authentication expired during API call.")

                if not response.get("ok"):
                    raise APIError(
                        "API request failed",
                        status_code=response.get("status"),
                        response_body=response_text,
                    )

                return response.get("json") or {}

            except AuthenticationError:
                if attempt_refresh and attempt == 0:
                    logger.info("Authentication failed; attempting auto-refresh.")
                    await self._refresh_session()
                    continue
                raise
            except APIError:
                raise
            except Exception as e:
                raise APIError(f"API call failed: {e}") from e

        raise APIError("API call failed after refresh")


class _BrowserPool:
    def __init__(
        self,
        headless: bool,
        launch_args: list[str],
        context_options: dict[str, Any],
        block_resources: bool,
        max_contexts: int,
    ) -> None:
        self._headless = headless
        self._launch_args = launch_args
        self._context_options = context_options
        self._block_resources = block_resources
        self._max_contexts = max_contexts
        self._lock = asyncio.Lock()
        self._contexts: asyncio.Queue[BrowserContext] = asyncio.Queue()
        self._context_count = 0
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None

    @property
    def browser(self) -> Browser | None:
        return self._browser

    @property
    def playwright(self) -> Playwright | None:
        return self._playwright

    async def ensure_browser(self) -> None:
        async with self._lock:
            if self._browser is not None:
                return
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=self._headless,
                args=self._launch_args,
            )

    async def acquire_context(
        self, apply_blocking: Callable[[BrowserContext], Awaitable[None]]
    ) -> BrowserContext:
        await self.ensure_browser()
        if not self._contexts.empty():
            return await self._contexts.get()

        async with self._lock:
            if self._browser is None:
                raise BrowserError("Browser not initialized")
            if self._context_count < self._max_contexts:
                context = await self._browser.new_context(**self._context_options)
                if self._block_resources:
                    await apply_blocking(context)
                self._context_count += 1
                return context

        return await self._contexts.get()

    async def release_context(self, context: BrowserContext) -> None:
        # BrowserContext in Playwright doesn't have is_closed()
        # but we can try/except or just let the queue handle it.
        # However, to avoid mypy error we can check if it has it or use getattr.
        if getattr(context, "is_closed", lambda: False)():
            return
        await self._contexts.put(context)

    async def shutdown(self) -> None:
        async with self._lock:
            while not self._contexts.empty():
                context = await self._contexts.get()
                try:
                    await context.close()
                except Exception:
                    pass
            self._context_count = 0
            if self._browser:
                try:
                    await self._browser.close()
                except Exception:
                    pass
                self._browser = None
            if self._playwright:
                try:
                    await self._playwright.stop()
                except Exception:
                    pass
                self._playwright = None


class PersistentBrowserSession(BrowserSession):
    """
    Browser session that reuses a shared browser instance across contexts.

    This reduces startup time for repeated operations and supports
    concurrent contexts via a simple pool.
    """

    _pool: _BrowserPool | None = None
    _pool_lock = asyncio.Lock()

    def __init__(
        self,
        auth: AuthManager,
        headless: bool = True,
        timeout: int = 60000,
        auto_refresh: bool = False,
        block_resources: bool = True,
        streaming_timeout: int = DEFAULT_STREAMING_TIMEOUT_MS,
        csrf_cache_ttl: int = DEFAULT_CSRF_TTL_SECONDS,
        wait_until: Literal[
            "commit", "domcontentloaded", "load", "networkidle"
        ] = "load",
        max_contexts: int = 3,
    ) -> None:
        super().__init__(
            auth=auth,
            headless=headless,
            timeout=timeout,
            auto_refresh=auto_refresh,
            block_resources=block_resources,
            streaming_timeout=streaming_timeout,
            csrf_cache_ttl=csrf_cache_ttl,
            wait_until=wait_until,
        )
        self.max_contexts = max_contexts
        self._pool_ref: _BrowserPool | None = None

    @classmethod
    async def _get_pool(cls, session: "PersistentBrowserSession") -> _BrowserPool:
        async with cls._pool_lock:
            if cls._pool is None:
                cls._pool = _BrowserPool(
                    headless=session.headless,
                    launch_args=session._launch_args(),
                    context_options=session._context_options(),
                    block_resources=session.block_resources,
                    max_contexts=session.max_contexts,
                )
            return cls._pool

    @classmethod
    async def shutdown_pool(cls) -> None:
        if cls._pool is None:
            return
        await cls._pool.shutdown()
        cls._pool = None

    async def __aenter__(self) -> "PersistentBrowserSession":
        if not self.auth.is_authenticated():
            raise AuthenticationError(
                "Not authenticated. Please run 'pynotebooklm auth login' first."
            )

        try:
            pool = await self._get_pool(self)
            self._pool_ref = pool
            self._context = await pool.acquire_context(self._apply_resource_blocking)
            self._browser = pool.browser
            self._playwright = pool.playwright

            try:
                await self._context.clear_cookies()
            except Exception:
                pass
            await self._context.add_cookies(self.auth.get_cookies())  # type: ignore[arg-type]

            self._page = await self._context.new_page()
            self._page.set_default_timeout(self.timeout)

            logger.debug("Navigating to NotebookLM (persistent session)...")
            await self._page.goto(NOTEBOOKLM_URL, wait_until=self.wait_until)

            if not self._is_authenticated_page():
                raise AuthenticationError(
                    "Cookies expired or invalid. Please login again."
                )

            self._csrf_token = await self._extract_csrf_token()
            self._csrf_cached_at = datetime.now()
            logger.info(
                "Persistent browser session ready (CSRF token: %s)",
                bool(self._csrf_token),
            )

            return self

        except AuthenticationError:
            await self._cleanup()
            raise
        except Exception as e:
            await self._cleanup()
            logger.error("Failed to start persistent browser session: %s", e)
            raise BrowserError(
                f"Failed to start persistent browser session: {e}"
            ) from e

    async def _cleanup(self) -> None:
        if self._page:
            try:
                await self._page.close()
            except Exception:
                pass
            self._page = None

        if self._context and self._pool_ref:
            try:
                await self._pool_ref.release_context(self._context)
            except Exception:
                pass
            self._context = None
        self._pool_ref = None

        self._csrf_token = None
        self._csrf_cached_at = None

        logger.debug("Persistent browser session cleaned up")
