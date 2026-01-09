"""
Additional unit tests for AuthManager async methods.

These tests verify browser-based authentication flows
using mocked Playwright components.
"""

from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pynotebooklm.auth import (
    AuthManager,
    _main_check,
    _main_login,
    _main_logout,
)
from pynotebooklm.exceptions import AuthenticationError, BrowserError
from pynotebooklm.models import AuthState, Cookie

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_auth_state() -> AuthState:
    """Create a mock valid auth state."""
    return AuthState(
        cookies=[
            Cookie(name="SID", value="test_sid", domain=".google.com", path="/"),
            Cookie(name="HSID", value="test_hsid", domain=".google.com", path="/"),
            Cookie(name="SSID", value="test_ssid", domain=".google.com", path="/"),
            Cookie(name="APISID", value="test_apisid", domain=".google.com", path="/"),
            Cookie(
                name="SAPISID", value="test_sapisid", domain=".google.com", path="/"
            ),
        ],
        csrf_token="test_csrf_token",
        authenticated_at=datetime.now(),
        expires_at=datetime.now() + timedelta(days=14),
    )


@pytest.fixture
def authenticated_auth_path(tmp_path: Path, mock_auth_state: AuthState) -> Path:
    """Create a temp auth file with valid auth state."""
    auth_path = tmp_path / ".pynotebooklm" / "auth.json"
    auth_path.parent.mkdir(parents=True)
    auth_path.write_text(mock_auth_state.model_dump_json())
    return auth_path


# =============================================================================
# Login Method Tests
# =============================================================================


class TestAuthManagerLogin:
    """Tests for the login method."""

    @pytest.mark.asyncio
    async def test_login_browser_error(self, tmp_path: Path) -> None:
        """Login raises BrowserError on playwright failure."""
        auth_path = tmp_path / ".pynotebooklm" / "auth.json"
        auth = AuthManager(auth_path=auth_path)

        with patch("pynotebooklm.auth.async_playwright") as mock_async_pw:
            mock_async_pw.return_value.__aenter__ = AsyncMock(
                side_effect=Exception("Failed to launch browser")
            )
            mock_async_pw.return_value.__aexit__ = AsyncMock(return_value=None)

            with pytest.raises(BrowserError):
                await auth.login()


# =============================================================================
# Refresh Method Tests
# =============================================================================


class TestAuthManagerRefresh:
    """Tests for the refresh method."""

    @pytest.mark.asyncio
    async def test_refresh_calls_login_when_not_authenticated(
        self, tmp_path: Path
    ) -> None:
        """Refresh calls login when not authenticated."""
        auth_path = tmp_path / ".pynotebooklm" / "auth.json"
        auth = AuthManager(auth_path=auth_path)

        with patch.object(auth, "login", new_callable=AsyncMock) as mock_login:
            await auth.refresh()
            mock_login.assert_called_once()

    @pytest.mark.asyncio
    async def test_refresh_falls_back_to_login_on_expired_cookies(
        self, authenticated_auth_path: Path
    ) -> None:
        """Refresh calls login when cookies have expired during refresh."""
        auth = AuthManager(auth_path=authenticated_auth_path)

        mock_page = AsyncMock()
        # Redirected to login page means cookies expired
        mock_page.url = "https://accounts.google.com/signin"
        mock_page.goto = AsyncMock()

        mock_context = AsyncMock()
        mock_context.add_cookies = AsyncMock()
        mock_context.new_page = AsyncMock(return_value=mock_page)

        mock_browser = AsyncMock()
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_browser.close = AsyncMock()

        mock_playwright = MagicMock()
        mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)

        with patch("pynotebooklm.auth.async_playwright") as mock_async_pw:
            mock_async_pw.return_value.__aenter__ = AsyncMock(
                return_value=mock_playwright
            )
            mock_async_pw.return_value.__aexit__ = AsyncMock(return_value=None)

            with patch.object(auth, "login", new_callable=AsyncMock) as mock_login:
                await auth.refresh()
                mock_login.assert_called_once()

    @pytest.mark.asyncio
    async def test_refresh_error(self, authenticated_auth_path: Path) -> None:
        """Refresh raises AuthenticationError on failure."""
        auth = AuthManager(auth_path=authenticated_auth_path)

        with patch("pynotebooklm.auth.async_playwright") as mock_async_pw:
            mock_async_pw.return_value.__aenter__ = AsyncMock(
                side_effect=Exception("Network error")
            )
            mock_async_pw.return_value.__aexit__ = AsyncMock(return_value=None)

            with pytest.raises(AuthenticationError):
                await auth.refresh()


# =============================================================================
# Store Cookies Tests
# =============================================================================


class TestStoreCookies:
    """Tests for _store_cookies method."""

    @pytest.mark.asyncio
    async def test_store_cookies_filters_google_domain(self, tmp_path: Path) -> None:
        """_store_cookies only stores google.com domain cookies."""
        auth_path = tmp_path / ".pynotebooklm" / "auth.json"
        auth = AuthManager(auth_path=auth_path)

        mock_page = AsyncMock()
        mock_page.evaluate = AsyncMock(return_value=None)

        cookies = [
            {"name": "SID", "value": "val", "domain": ".google.com", "path": "/"},
            {"name": "other", "value": "val", "domain": ".example.com", "path": "/"},
        ]

        await auth._store_cookies(cookies, mock_page)

        assert auth._auth_state is not None
        # Only google.com cookie should be stored
        assert len(auth._auth_state.cookies) == 1
        assert auth._auth_state.cookies[0].name == "SID"

    @pytest.mark.asyncio
    async def test_store_cookies_extracts_csrf(self, tmp_path: Path) -> None:
        """_store_cookies extracts CSRF token from page."""
        auth_path = tmp_path / ".pynotebooklm" / "auth.json"
        auth = AuthManager(auth_path=auth_path)

        mock_page = AsyncMock()
        mock_page.evaluate = AsyncMock(return_value="extracted_csrf_token")

        cookies = [
            {"name": "SID", "value": "val", "domain": ".google.com", "path": "/"},
        ]

        await auth._store_cookies(cookies, mock_page)

        assert auth._auth_state is not None
        assert auth._auth_state.csrf_token == "extracted_csrf_token"


# =============================================================================
# Extract CSRF Token Tests
# =============================================================================


class TestExtractCsrfToken:
    """Tests for _extract_csrf_token method."""

    @pytest.mark.asyncio
    async def test_extract_csrf_token_success(self, tmp_path: Path) -> None:
        """_extract_csrf_token returns token when found."""
        auth_path = tmp_path / ".pynotebooklm" / "auth.json"
        auth = AuthManager(auth_path=auth_path)

        mock_page = AsyncMock()
        mock_page.evaluate = AsyncMock(return_value="csrf_token_value")

        result = await auth._extract_csrf_token(mock_page)

        assert result == "csrf_token_value"

    @pytest.mark.asyncio
    async def test_extract_csrf_token_not_found(self, tmp_path: Path) -> None:
        """_extract_csrf_token returns None when not found."""
        auth_path = tmp_path / ".pynotebooklm" / "auth.json"
        auth = AuthManager(auth_path=auth_path)

        mock_page = AsyncMock()
        mock_page.evaluate = AsyncMock(return_value=None)

        result = await auth._extract_csrf_token(mock_page)

        assert result is None

    @pytest.mark.asyncio
    async def test_extract_csrf_token_error(self, tmp_path: Path) -> None:
        """_extract_csrf_token returns None on error."""
        auth_path = tmp_path / ".pynotebooklm" / "auth.json"
        auth = AuthManager(auth_path=auth_path)

        mock_page = AsyncMock()
        mock_page.evaluate = AsyncMock(side_effect=Exception("Page error"))

        result = await auth._extract_csrf_token(mock_page)

        assert result is None


# =============================================================================
# CLI Entry Point Tests
# =============================================================================


class TestAuthCLIEntryPoints:
    """Tests for auth module CLI entry points."""

    @pytest.mark.asyncio
    async def test_main_login(self, tmp_path: Path) -> None:
        """_main_login calls login and prints success."""
        auth_path = tmp_path / ".pynotebooklm" / "auth.json"

        with patch("pynotebooklm.auth.AuthManager") as mock_auth_cls:
            mock_auth = MagicMock()
            mock_auth.auth_path = auth_path
            mock_auth.login = AsyncMock()
            mock_auth_cls.return_value = mock_auth

            with patch("builtins.print"):
                with pytest.raises(SystemExit) as exc_info:
                    await _main_login()

                assert exc_info.value.code == 0
                mock_auth.login.assert_called_once()

    @pytest.mark.asyncio
    async def test_main_check_authenticated(
        self, authenticated_auth_path: Path, mock_auth_state: AuthState
    ) -> None:
        """_main_check exits 0 when authenticated."""
        with patch("pynotebooklm.auth.AuthManager") as mock_auth_cls:
            mock_auth = MagicMock()
            mock_auth.is_authenticated.return_value = True
            mock_auth.auth_path = authenticated_auth_path
            mock_auth._auth_state = mock_auth_state
            mock_auth_cls.return_value = mock_auth

            with patch("builtins.print"):
                with pytest.raises(SystemExit) as exc_info:
                    await _main_check()

                assert exc_info.value.code == 0

    @pytest.mark.asyncio
    async def test_main_check_not_authenticated(self, tmp_path: Path) -> None:
        """_main_check exits 1 when not authenticated."""
        with patch("pynotebooklm.auth.AuthManager") as mock_auth_cls:
            mock_auth = MagicMock()
            mock_auth.is_authenticated.return_value = False
            mock_auth_cls.return_value = mock_auth

            with patch("builtins.print"):
                with pytest.raises(SystemExit) as exc_info:
                    await _main_check()

                assert exc_info.value.code == 1

    @pytest.mark.asyncio
    async def test_main_logout(self, tmp_path: Path) -> None:
        """_main_logout calls logout and prints success."""
        with patch("pynotebooklm.auth.AuthManager") as mock_auth_cls:
            mock_auth = MagicMock()
            mock_auth_cls.return_value = mock_auth

            with patch("builtins.print"):
                await _main_logout()

                mock_auth.logout.assert_called_once()


# =============================================================================
# Auth Module Callable Tests
# =============================================================================


class TestAuthModuleCallables:
    """Tests verifying that auth module functions are callable."""

    def test_main_login_is_callable(self) -> None:
        """_main_login is a callable coroutine function."""
        import pynotebooklm.auth

        assert callable(pynotebooklm.auth._main_login)

    def test_main_check_is_callable(self) -> None:
        """_main_check is a callable coroutine function."""
        import pynotebooklm.auth

        assert callable(pynotebooklm.auth._main_check)

    def test_main_logout_is_callable(self) -> None:
        """_main_logout is a callable coroutine function."""
        import pynotebooklm.auth

        assert callable(pynotebooklm.auth._main_logout)


# =============================================================================
# Save Cookies Error Handling Tests
# =============================================================================


class TestSaveCookiesErrors:
    """Tests for _save_cookies error handling."""

    def test_save_cookies_raises_on_os_error(self, tmp_path: Path) -> None:
        """_save_cookies raises AuthenticationError on OSError."""
        auth_path = tmp_path / "readonly_dir" / "auth.json"
        auth = AuthManager(auth_path=auth_path)

        # Set up auth state
        auth._auth_state = AuthState(
            cookies=[
                Cookie(name="SID", value="test", domain=".google.com", path="/"),
            ],
            authenticated_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=14),
        )

        # Make the directory read-only to trigger OSError
        auth_path.parent.chmod(0o444)

        try:
            from pynotebooklm.exceptions import AuthenticationError

            with pytest.raises(AuthenticationError):
                auth._save_cookies()
        finally:
            # Restore permissions for cleanup
            auth_path.parent.chmod(0o755)


# =============================================================================
# Login Method Success Tests
# =============================================================================


class TestLoginSuccess:
    """Tests for successful login flow."""

    @pytest.mark.asyncio
    async def test_login_success(self, tmp_path: Path) -> None:
        """Login extracts cookies and saves auth state on success."""
        auth_path = tmp_path / ".pynotebooklm" / "auth.json"
        auth = AuthManager(auth_path=auth_path)

        # Mock page with successful auth - use MagicMock for sync methods
        mock_page = MagicMock()
        mock_page.url = "https://notebooklm.google.com/"
        mock_page.goto = AsyncMock()
        mock_page.is_closed = MagicMock(return_value=False)  # Sync method
        mock_page.wait_for_timeout = AsyncMock()
        mock_page.evaluate = AsyncMock(return_value="csrf_token")
        mock_page.context = MagicMock()
        mock_page.context.cookies = AsyncMock(
            return_value=[
                {"name": "SID", "value": "sid", "domain": ".google.com", "path": "/"},
                {"name": "HSID", "value": "hsid", "domain": ".google.com", "path": "/"},
                {"name": "SSID", "value": "ssid", "domain": ".google.com", "path": "/"},
                {
                    "name": "APISID",
                    "value": "apisid",
                    "domain": ".google.com",
                    "path": "/",
                },
                {
                    "name": "SAPISID",
                    "value": "sapisid",
                    "domain": ".google.com",
                    "path": "/",
                },
            ]
        )

        mock_context = AsyncMock()
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_context.cookies = mock_page.context.cookies

        mock_browser = MagicMock()
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_browser.close = AsyncMock()
        mock_browser.is_connected = MagicMock(return_value=True)  # Sync method

        mock_playwright = MagicMock()
        mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)

        with patch("pynotebooklm.auth.async_playwright") as mock_async_pw:
            mock_async_pw.return_value.__aenter__ = AsyncMock(
                return_value=mock_playwright
            )
            mock_async_pw.return_value.__aexit__ = AsyncMock(return_value=None)

            await auth.login(timeout=10)

        assert auth.is_authenticated() is True
        assert auth._auth_state is not None
        assert auth._auth_state.csrf_token == "csrf_token"

    @pytest.mark.asyncio
    async def test_login_reraises_auth_error(self, tmp_path: Path) -> None:
        """Login re-raises AuthenticationError without wrapping."""
        auth_path = tmp_path / ".pynotebooklm" / "auth.json"
        auth = AuthManager(auth_path=auth_path)

        mock_page = AsyncMock()
        mock_page.url = "https://notebooklm.google.com/"
        mock_page.goto = AsyncMock()
        mock_page.is_closed.return_value = False

        mock_context = AsyncMock()
        mock_context.new_page = AsyncMock(return_value=mock_page)

        mock_browser = AsyncMock()
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_browser.close = AsyncMock()
        mock_browser.is_connected.return_value = True

        mock_playwright = MagicMock()
        mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)

        with patch("pynotebooklm.auth.async_playwright") as mock_async_pw:
            mock_async_pw.return_value.__aenter__ = AsyncMock(
                return_value=mock_playwright
            )
            mock_async_pw.return_value.__aexit__ = AsyncMock(return_value=None)

            # Mock _wait_for_authentication to raise AuthenticationError
            with patch.object(
                auth,
                "_wait_for_authentication",
                side_effect=AuthenticationError("Test auth error"),
            ):
                with pytest.raises(AuthenticationError, match="Test auth error"):
                    await auth.login()


# =============================================================================
# Wait For Authentication Tests
# =============================================================================


class TestWaitForAuthentication:
    """Tests for _wait_for_authentication method."""

    @pytest.mark.asyncio
    async def test_wait_for_authentication_success(self, tmp_path: Path) -> None:
        """_wait_for_authentication returns when authenticated."""
        auth_path = tmp_path / ".pynotebooklm" / "auth.json"
        auth = AuthManager(auth_path=auth_path)

        mock_context = AsyncMock()
        mock_context.cookies = AsyncMock(
            return_value=[
                {"name": "SID", "value": "sid"},
                {"name": "HSID", "value": "hsid"},
                {"name": "SSID", "value": "ssid"},
                {"name": "APISID", "value": "apisid"},
                {"name": "SAPISID", "value": "sapisid"},
            ]
        )

        # Use MagicMock for sync methods is_closed/is_connected
        mock_page = MagicMock()
        mock_page.url = "https://notebooklm.google.com/notebook/abc"
        mock_page.is_closed = MagicMock(return_value=False)
        mock_page.context = mock_context
        mock_page.wait_for_timeout = AsyncMock()

        mock_browser = MagicMock()
        mock_browser.is_connected = MagicMock(return_value=True)

        # Should complete without timeout
        await auth._wait_for_authentication(mock_page, mock_browser, timeout=10)

    @pytest.mark.asyncio
    async def test_wait_for_authentication_browser_closed(self, tmp_path: Path) -> None:
        """_wait_for_authentication raises when browser closed."""
        auth_path = tmp_path / ".pynotebooklm" / "auth.json"
        auth = AuthManager(auth_path=auth_path)

        mock_page = MagicMock()
        mock_page.url = "https://accounts.google.com/signin"
        mock_page.is_closed = MagicMock(return_value=False)
        mock_page.wait_for_timeout = AsyncMock()

        mock_browser = MagicMock()
        mock_browser.is_connected = MagicMock(
            return_value=False
        )  # Browser disconnected

        with pytest.raises(AuthenticationError, match="closed"):
            await auth._wait_for_authentication(mock_page, mock_browser, timeout=10)

    @pytest.mark.asyncio
    async def test_wait_for_authentication_page_closed(self, tmp_path: Path) -> None:
        """_wait_for_authentication raises when page closed."""
        auth_path = tmp_path / ".pynotebooklm" / "auth.json"
        auth = AuthManager(auth_path=auth_path)

        mock_page = MagicMock()
        mock_page.url = "https://accounts.google.com/signin"
        mock_page.is_closed = MagicMock(return_value=True)  # Page closed

        mock_browser = MagicMock()
        mock_browser.is_connected = MagicMock(return_value=True)

        with pytest.raises(AuthenticationError, match="closed"):
            await auth._wait_for_authentication(mock_page, mock_browser, timeout=10)

    @pytest.mark.asyncio
    async def test_wait_for_authentication_timeout(self, tmp_path: Path) -> None:
        """_wait_for_authentication raises on timeout."""
        auth_path = tmp_path / ".pynotebooklm" / "auth.json"
        auth = AuthManager(auth_path=auth_path)

        mock_context = AsyncMock()
        mock_context.cookies = AsyncMock(return_value=[])  # No cookies

        mock_page = MagicMock()
        mock_page.url = "https://accounts.google.com/signin"
        mock_page.is_closed = MagicMock(return_value=False)
        mock_page.context = mock_context
        mock_page.wait_for_timeout = AsyncMock()

        mock_browser = MagicMock()
        mock_browser.is_connected = MagicMock(return_value=True)

        with pytest.raises(AuthenticationError, match="timed out"):
            await auth._wait_for_authentication(mock_page, mock_browser, timeout=1)

    @pytest.mark.asyncio
    async def test_wait_for_authentication_playwright_closed_error(
        self, tmp_path: Path
    ) -> None:
        """_wait_for_authentication handles PlaywrightError for closed."""
        from playwright.async_api import Error as PlaywrightError

        auth_path = tmp_path / ".pynotebooklm" / "auth.json"
        auth = AuthManager(auth_path=auth_path)

        mock_page = MagicMock()
        mock_page.url = "https://accounts.google.com/signin"
        mock_page.is_closed = MagicMock(side_effect=PlaywrightError("Target closed"))

        mock_browser = MagicMock()
        mock_browser.is_connected = MagicMock(return_value=True)

        with pytest.raises(AuthenticationError, match="closed"):
            await auth._wait_for_authentication(mock_page, mock_browser, timeout=10)


# =============================================================================
# Refresh Success Tests
# =============================================================================


class TestRefreshSuccess:
    """Tests for successful refresh flow."""

    @pytest.mark.asyncio
    async def test_refresh_success(self, authenticated_auth_path: Path) -> None:
        """Refresh updates cookies when still authenticated."""
        auth = AuthManager(auth_path=authenticated_auth_path)

        mock_page = AsyncMock()
        mock_page.url = "https://notebooklm.google.com/"
        mock_page.goto = AsyncMock()
        mock_page.evaluate = AsyncMock(return_value="new_csrf_token")

        mock_context = AsyncMock()
        mock_context.add_cookies = AsyncMock()
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_context.cookies = AsyncMock(
            return_value=[
                {
                    "name": "SID",
                    "value": "new_sid",
                    "domain": ".google.com",
                    "path": "/",
                },
            ]
        )

        mock_browser = AsyncMock()
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_browser.close = AsyncMock()

        mock_playwright = MagicMock()
        mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)

        with patch("pynotebooklm.auth.async_playwright") as mock_async_pw:
            mock_async_pw.return_value.__aenter__ = AsyncMock(
                return_value=mock_playwright
            )
            mock_async_pw.return_value.__aexit__ = AsyncMock(return_value=None)

            await auth.refresh()

        # Should have updated CSRF token
        assert auth._auth_state is not None
        assert auth._auth_state.csrf_token == "new_csrf_token"


# =============================================================================
# Auth Module __main__ Block Tests
# =============================================================================


class TestAuthMainBlock:
    """Tests for the __main__ block of auth module."""

    def test_auth_main_login_command(self) -> None:
        """Auth main runs login command."""
        import asyncio
        import runpy

        with patch.object(asyncio, "run") as mock_run:
            with patch("sys.argv", ["auth", "login"]):
                try:
                    runpy.run_module("pynotebooklm.auth", run_name="__main__")
                except SystemExit:
                    pass
                mock_run.assert_called_once()

    def test_auth_main_check_command(self) -> None:
        """Auth main runs check command."""
        import asyncio
        import runpy

        with patch.object(asyncio, "run") as mock_run:
            with patch("sys.argv", ["auth", "check"]):
                try:
                    runpy.run_module("pynotebooklm.auth", run_name="__main__")
                except SystemExit:
                    pass
                mock_run.assert_called_once()

    def test_auth_main_logout_command(self) -> None:
        """Auth main runs logout command."""
        import asyncio
        import runpy

        with patch.object(asyncio, "run") as mock_run:
            with patch("sys.argv", ["auth", "logout"]):
                try:
                    runpy.run_module("pynotebooklm.auth", run_name="__main__")
                except SystemExit:
                    pass
                mock_run.assert_called_once()

    def test_auth_main_no_args(self) -> None:
        """Auth main prints usage when no args."""
        import runpy

        with patch("sys.argv", ["auth"]):
            with pytest.raises(SystemExit) as exc_info:
                runpy.run_module("pynotebooklm.auth", run_name="__main__")
            assert exc_info.value.code == 1

    def test_auth_main_unknown_command(self) -> None:
        """Auth main prints error for unknown command."""
        import runpy

        with patch("sys.argv", ["auth", "unknown"]):
            with pytest.raises(SystemExit) as exc_info:
                runpy.run_module("pynotebooklm.auth", run_name="__main__")
            assert exc_info.value.code == 1
