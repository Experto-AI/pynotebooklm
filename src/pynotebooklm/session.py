"""
Browser session management for PyNotebookLM.

This module provides the BrowserSession class for managing Playwright browser
contexts and making API calls to NotebookLM's internal endpoints.
"""

import json
import logging
import urllib.parse
from typing import Any

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

logger = logging.getLogger(__name__)

# NotebookLM API configuration
NOTEBOOKLM_URL = "https://notebooklm.google.com"
BATCH_EXECUTE_URL = f"{NOTEBOOKLM_URL}/_/LabsTailwindUi/data/batchexecute"

# Anti-XSSI prefix used by Google APIs
ANTI_XSSI_PREFIX = ")]}'\n"


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
    ) -> None:
        """
        Initialize the browser session.

        Args:
            auth: AuthManager instance with valid authentication.
            headless: Whether to run browser in headless mode.
            timeout: Default timeout for page operations in milliseconds.
        """
        self.auth = auth
        self.headless = headless
        self.timeout = timeout

        # These are set in __aenter__
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None
        self._csrf_token: str | None = None

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
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                ],
            )

            # Create context with cookies
            logger.debug("Creating browser context with cookies...")
            self._context = await self._browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent=(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
            )

            # Add cookies (Playwright expects SetCookieParam which matches our dict format)
            await self._context.add_cookies(self.auth.get_cookies())  # type: ignore[arg-type]

            # Create page and navigate
            self._page = await self._context.new_page()
            self._page.set_default_timeout(self.timeout)

            logger.debug("Navigating to NotebookLM...")
            await self._page.goto(NOTEBOOKLM_URL, wait_until="load")

            # Verify we're authenticated
            if "accounts.google.com" in self._page.url:
                raise AuthenticationError(
                    "Cookies expired or invalid. Please login again."
                )

            # Extract CSRF token
            self._csrf_token = await self._extract_csrf_token()
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

        # Build the request payload
        payload = self._encode_payload(rpc_id, params)

        logger.debug("Calling RPC %s with params: %s", rpc_id, params)

        try:
            # Execute fetch via page.evaluate
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

            # Parse and return response
            return self._parse_response(response)

        except Exception as e:
            if isinstance(e, APIError | RateLimitError):
                raise
            logger.error("RPC call failed: %s", e)
            raise APIError(f"RPC call failed: {e}") from e

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

        # In batchexecute responses, line 0 is often a byte count and line 1 is data.
        # But sometimes the byte count is missing or multiple chunks are present.
        target_line = lines[0]
        if target_line.isdigit() and len(lines) > 1:
            target_line = lines[1]

        try:
            # Parse the data line
            data = json.loads(target_line)

            # Navigate nested structure to get actual response
            # Response is usually at data[0][2] but wrapped in another string
            if isinstance(data, list) and len(data) > 0:
                inner = data[0]
                if isinstance(inner, list) and len(inner) > 2:
                    result_str = inner[2]
                    if isinstance(result_str, str):
                        return json.loads(result_str)
                    return result_str

            return data

        except (json.JSONDecodeError, IndexError, TypeError) as e:
            logger.error("Failed to parse response: %s", e)
            raise APIError(f"Failed to parse response: {e}") from e

    async def call_api_raw(
        self,
        endpoint: str,
        method: str = "GET",
        body: str | None = None,
        headers: dict[str, str] | None = None,
    ) -> str:
        """
        Make a raw API call via the browser context.

        Args:
            endpoint: API endpoint URL.
            method: HTTP method.
            body: Request body string.
            headers: Additional headers.

        Returns:
            Raw response text.

        Raises:
            SessionError: If session not active.
            APIError: If request fails.
        """
        if self._page is None:
            raise SessionError("Browser session not active")

        try:
            response = await self._page.evaluate(
                """
                async (args) => {
                    const options = {
                        method: args.method,
                        headers: args.headers || {},
                        credentials: 'include',
                    };

                    if (args.body) {
                        options.body = args.body;
                    }

                    const response = await fetch(args.endpoint, options);

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
                },
            )

            if not response.get("ok"):
                raise APIError(
                    f"API request failed: {response.get('statusText')}",
                    status_code=response.get("status"),
                    response_body=response.get("text"),
                )

            return str(response.get("text", ""))

        except APIError:
            raise
        except Exception as e:
            raise APIError(f"API call failed: {e}") from e

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

        try:
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

            if not response.get("ok"):
                raise APIError(
                    "API request failed",
                    status_code=response.get("status"),
                    response_body=response.get("text"),
                )

            return response.get("json") or {}

        except APIError:
            raise
        except Exception as e:
            raise APIError(f"API call failed: {e}") from e
