"""
Authentication manager for PyNotebookLM.

This module handles cookie-based authentication with Google NotebookLM,
including browser-based login, cookie persistence, and session validation.
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, cast

from playwright.async_api import Browser, Page, async_playwright
from playwright.async_api import Error as PlaywrightError

from .exceptions import AuthenticationError, BrowserError
from .models import AuthState, Cookie

logger = logging.getLogger(__name__)

# Default configuration directory
DEFAULT_CONFIG_DIR = Path.home() / ".pynotebooklm"
DEFAULT_AUTH_FILE = DEFAULT_CONFIG_DIR / "auth.json"

# NotebookLM URLs
NOTEBOOKLM_URL = "https://notebooklm.google.com"
GOOGLE_ACCOUNTS_URL = "https://accounts.google.com"

# Essential cookies for authentication
ESSENTIAL_COOKIES = {"SID", "HSID", "SSID", "APISID", "SAPISID"}

# Cookie validity duration (conservative estimate)
COOKIE_VALIDITY_DAYS = 14


class AuthManager:
    """
    Manages authentication state for NotebookLM.

    This class handles:
    - Interactive browser-based login
    - Cookie extraction and persistence
    - Authentication state validation
    - Cookie refresh when needed

    Example:
        >>> auth = AuthManager()
        >>> if not auth.is_authenticated():
        ...     await auth.login()
        >>> cookies = auth.get_cookies()
    """

    def __init__(
        self,
        auth_path: Path | str | None = None,
        headless: bool = False,
    ) -> None:
        """
        Initialize the authentication manager.

        Args:
            auth_path: Path to store authentication state.
                      Defaults to ~/.pynotebooklm/auth.json
            headless: Whether to run browser in headless mode for login.
                     Set to False for interactive login (recommended).
        """
        self.auth_path = Path(auth_path) if auth_path else DEFAULT_AUTH_FILE
        self.headless = headless
        self._auth_state: AuthState | None = None

        # Ensure config directory exists
        self.auth_path.parent.mkdir(parents=True, exist_ok=True)

        # Try to load existing auth state
        self._load_cookies()

    def _load_cookies(self) -> None:
        """Load authentication state from file."""
        if not self.auth_path.exists():
            logger.debug("No existing auth file found at %s", self.auth_path)
            self._auth_state = None
            return

        try:
            data = json.loads(self.auth_path.read_text())
            self._auth_state = AuthState.model_validate(data)
            logger.info(
                "Loaded auth state from %s (authenticated: %s)",
                self.auth_path,
                self._auth_state.is_valid(),
            )
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning("Failed to load auth state: %s", e)
            self._auth_state = None

    def _save_cookies(self) -> None:
        """Persist authentication state to file."""
        if self._auth_state is None:
            return

        try:
            self.auth_path.write_text(self._auth_state.model_dump_json(indent=2))
            logger.info("Saved auth state to %s", self.auth_path)
        except OSError as e:
            logger.error("Failed to save auth state: %s", e)
            raise AuthenticationError(f"Failed to save authentication: {e}") from e

    def is_authenticated(self) -> bool:
        """
        Check if current authentication state is valid.

        Returns:
            True if authenticated with valid cookies, False otherwise.
        """
        if self._auth_state is None:
            return False
        return self._auth_state.is_valid()

    def get_cookies(self) -> list[dict[str, Any]]:
        """
        Get cookies in Playwright-compatible format.

        Returns:
            List of cookie dictionaries for Playwright context.

        Raises:
            AuthenticationError: If not authenticated.
        """
        if not self.is_authenticated():
            raise AuthenticationError("Not authenticated. Please login first.")

        assert self._auth_state is not None
        return [
            {
                "name": c.name,
                "value": c.value,
                "domain": c.domain,
                "path": c.path,
                "expires": c.expires,
                "httpOnly": c.http_only,
                "secure": c.secure,
                "sameSite": c.same_site,
            }
            for c in self._auth_state.cookies
        ]

    def get_csrf_token(self) -> str | None:
        """
        Get the CSRF token (SNlM0e) if available.

        Returns:
            CSRF token string or None if not available.
        """
        if self._auth_state is None:
            return None
        return self._auth_state.csrf_token

    async def login(self, timeout: int = 300) -> None:
        """
        Perform interactive browser-based login to NotebookLM.

        Opens a browser window for the user to login with their Google account.
        Waits for successful authentication and extracts cookies.

        Args:
            timeout: Maximum time to wait for login in seconds.

        Raises:
            AuthenticationError: If login fails or times out.
            BrowserError: If browser automation fails.
        """
        logger.info("Starting interactive login flow...")

        try:
            async with async_playwright() as p:
                # Launch browser
                browser = await p.chromium.launch(
                    headless=self.headless,
                    args=[
                        "--no-sandbox",
                        "--disable-setuid-sandbox",
                        "--disable-dev-shm-usage",
                    ],
                )

                try:
                    context = await browser.new_context(
                        viewport={"width": 1280, "height": 800},
                        user_agent=(
                            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                            "AppleWebKit/537.36 (KHTML, like Gecko) "
                            "Chrome/120.0.0.0 Safari/537.36"
                        ),
                    )

                    page = await context.new_page()

                    # Navigate to NotebookLM
                    await page.goto(NOTEBOOKLM_URL, wait_until="networkidle")

                    # Wait for user to complete login
                    await self._wait_for_authentication(page, browser, timeout)

                    # Extract cookies (Playwright returns TypedDict, cast for compatibility)
                    cookies = await context.cookies()
                    await self._store_cookies(cast(list[dict[str, Any]], cookies), page)

                    logger.info("Login successful!")

                finally:
                    await browser.close()

        except Exception as e:
            if isinstance(e, AuthenticationError | BrowserError):
                raise
            logger.error("Login failed: %s", e)
            raise BrowserError(f"Browser automation failed: {e}") from e

    async def _wait_for_authentication(
        self, page: Page, browser: Browser, timeout: int
    ) -> None:
        """
        Wait for the user to complete authentication.

        Args:
            page: Playwright page object.
            browser: Playwright browser object.
            timeout: Maximum wait time in seconds.

        Raises:
            AuthenticationError: If authentication times out or fails.
        """
        logger.info(
            "Please login with your Google account in the browser window. "
            "You have %d seconds to complete login.",
            timeout,
        )

        start_time = datetime.now()
        check_interval = 2  # seconds

        while (datetime.now() - start_time).seconds < timeout:
            try:
                # Check if browser or page was closed
                if not browser.is_connected() or page.is_closed():
                    raise AuthenticationError(
                        "Browser or page was closed before login completed"
                    )

                # Check if we're on NotebookLM main page (indicates successful login)
                current_url = page.url
                if (
                    NOTEBOOKLM_URL in current_url
                    and "accounts.google.com" not in current_url
                ):
                    # Verify we have the essential cookies
                    context = page.context
                    cookies = await context.cookies()
                    cookie_names = {c["name"] for c in cookies}

                    if ESSENTIAL_COOKIES.issubset(cookie_names):
                        logger.info("Authentication detected!")
                        return

                await page.wait_for_timeout(check_interval * 1000)
            except PlaywrightError as e:
                # Catch "Target closed" errors which occur if user closes browser/tab
                if "closed" in str(e).lower():
                    raise AuthenticationError(
                        "Browser or page was closed before login completed"
                    ) from e
                raise

        raise AuthenticationError(
            f"Login timed out after {timeout} seconds. Please try again."
        )

    async def _store_cookies(self, cookies: list[dict[str, Any]], page: Page) -> None:
        """
        Store extracted cookies and CSRF token.

        Args:
            cookies: List of cookie dictionaries from Playwright.
            page: Playwright page for CSRF token extraction.
        """
        # Convert to Cookie models
        cookie_models = []
        for c in cookies:
            # Filter to essential and related cookies
            if c.get("domain", "").endswith("google.com"):
                cookie_models.append(
                    Cookie(
                        name=c["name"],
                        value=c["value"],
                        domain=c["domain"],
                        path=c.get("path", "/"),
                        expires=c.get("expires"),
                        http_only=c.get("httpOnly", False),
                        secure=c.get("secure", False),
                        same_site=c.get("sameSite", "Lax"),
                    )
                )

        # Try to extract CSRF token from page
        csrf_token = await self._extract_csrf_token(page)

        # Calculate expiration
        now = datetime.now()
        expires_at = now + timedelta(days=COOKIE_VALIDITY_DAYS)

        # Create and save auth state
        self._auth_state = AuthState(
            cookies=cookie_models,
            csrf_token=csrf_token,
            authenticated_at=now,
            expires_at=expires_at,
        )

        self._save_cookies()
        logger.info(
            "Stored %d cookies, expires at %s",
            len(cookie_models),
            expires_at.isoformat(),
        )

    async def _extract_csrf_token(self, page: Page) -> str | None:
        """
        Extract CSRF token (SNlM0e) from page HTML.

        Args:
            page: Playwright page object.

        Returns:
            CSRF token string or None if not found.
        """
        try:
            # Try to find SNlM0e token in page scripts
            token = await page.evaluate(
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
            if token:
                logger.debug("Extracted CSRF token")
            return cast(str | None, token)
        except Exception as e:
            logger.warning("Failed to extract CSRF token: %s", e)
            return None

    async def refresh(self) -> None:
        """
        Refresh authentication by re-extracting cookies.

        Opens browser, navigates to NotebookLM (using existing cookies),
        and re-extracts fresh cookies.

        Raises:
            AuthenticationError: If refresh fails.
        """
        if not self.is_authenticated():
            # No existing auth, need full login
            await self.login()
            return

        logger.info("Refreshing authentication...")

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=["--no-sandbox", "--disable-setuid-sandbox"],
                )

                try:
                    context = await browser.new_context()
                    # Playwright expects SetCookieParam which matches our dict format
                    await context.add_cookies(self.get_cookies())  # type: ignore[arg-type]

                    page = await context.new_page()
                    await page.goto(NOTEBOOKLM_URL, wait_until="networkidle")

                    # Check if still authenticated
                    current_url = page.url
                    if "accounts.google.com" in current_url:
                        # Cookies expired, need full login
                        logger.warning("Cookies expired, full login required")
                        await browser.close()
                        await self.login()
                        return

                    # Re-extract cookies (cast for type compatibility)
                    cookies = await context.cookies()
                    await self._store_cookies(cast(list[dict[str, Any]], cookies), page)
                    logger.info("Authentication refreshed successfully")

                finally:
                    await browser.close()

        except Exception as e:
            logger.error("Refresh failed: %s", e)
            raise AuthenticationError(f"Failed to refresh authentication: {e}") from e

    def logout(self) -> None:
        """
        Clear authentication state.

        Removes stored cookies and resets auth state.
        """
        self._auth_state = None
        if self.auth_path.exists():
            self.auth_path.unlink()
            logger.info("Removed auth file: %s", self.auth_path)
        logger.info("Logged out successfully")


# =============================================================================
# CLI Entry Point
# =============================================================================


async def _main_login() -> None:
    """CLI entry point for login."""
    import sys

    auth = AuthManager()
    await auth.login()
    print("✓ Login successful!")
    print(f"  Auth file: {auth.auth_path}")
    sys.exit(0)


async def _main_check() -> None:
    """CLI entry point for checking auth status."""
    import sys

    auth = AuthManager()
    if auth.is_authenticated():
        print("✓ Authenticated: True")
        print(f"  Auth file: {auth.auth_path}")
        if auth._auth_state and auth._auth_state.expires_at:
            print(f"  Expires: {auth._auth_state.expires_at.isoformat()}")
        sys.exit(0)
    else:
        print("✗ Authenticated: False")
        print("  Run 'python -m pynotebooklm.auth login' to authenticate")
        sys.exit(1)


async def _main_logout() -> None:
    """CLI entry point for logout."""
    auth = AuthManager()
    auth.logout()
    print("✓ Logged out successfully")


if __name__ == "__main__":
    import asyncio
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m pynotebooklm.auth [login|check|logout]")
        sys.exit(1)

    command = sys.argv[1]

    if command == "login":
        asyncio.run(_main_login())
    elif command == "check":
        asyncio.run(_main_check())
    elif command == "logout":
        asyncio.run(_main_logout())
    else:
        print(f"Unknown command: {command}")
        print("Usage: python -m pynotebooklm.auth [login|check|logout]")
        sys.exit(1)
