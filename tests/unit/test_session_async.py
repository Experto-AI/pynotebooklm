"""
Additional unit tests for BrowserSession async methods.

These tests verify browser lifecycle management, RPC calls,
and API calls using mocked Playwright components.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pynotebooklm.auth import AuthManager
from pynotebooklm.exceptions import (
    APIError,
    AuthenticationError,
    BrowserError,
    SessionError,
)
from pynotebooklm.models import AuthState, Cookie
from pynotebooklm.session import BrowserSession, PersistentBrowserSession, _BrowserPool

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
def mock_auth_manager(tmp_path: Path, mock_auth_state: AuthState) -> AuthManager:
    """Create a mock authenticated AuthManager."""
    auth_path = tmp_path / ".pynotebooklm" / "auth.json"
    auth_path.parent.mkdir(parents=True)
    auth_path.write_text(mock_auth_state.model_dump_json())
    return AuthManager(auth_path=auth_path)


# =============================================================================
# Context Manager Tests
# =============================================================================


class TestBrowserSessionContextManager:
    """Tests for async context manager methods."""

    @pytest.mark.asyncio
    async def test_aenter_success(self, mock_auth_manager: AuthManager) -> None:
        """__aenter__ launches browser and returns session."""
        session = BrowserSession(mock_auth_manager)

        mock_page = AsyncMock()
        mock_page.url = "https://notebooklm.google.com/"
        mock_page.goto = AsyncMock()
        mock_page.set_default_timeout = MagicMock()
        mock_page.evaluate = AsyncMock(return_value="csrf_token")
        mock_page.close = AsyncMock()

        mock_context = AsyncMock()
        mock_context.add_cookies = AsyncMock()
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_context.route = AsyncMock()
        mock_context.close = AsyncMock()

        mock_browser = AsyncMock()
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_browser.close = AsyncMock()

        mock_playwright = MagicMock()
        mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_playwright.stop = AsyncMock()

        with patch("pynotebooklm.session.async_playwright") as mock_async_pw:
            mock_pw_instance = AsyncMock()
            mock_pw_instance.start = AsyncMock(return_value=mock_playwright)
            mock_async_pw.return_value = mock_pw_instance

            result = await session.__aenter__()

            assert result is session
            assert session._page is not None
            assert session.csrf_token == "csrf_token"

    @pytest.mark.asyncio
    async def test_aenter_redirected_to_login(
        self, mock_auth_manager: AuthManager
    ) -> None:
        """__aenter__ raises AuthenticationError when redirected to login."""
        session = BrowserSession(mock_auth_manager)

        mock_page = AsyncMock()
        mock_page.url = "https://accounts.google.com/signin"  # Redirected
        mock_page.goto = AsyncMock()
        mock_page.set_default_timeout = MagicMock()
        mock_page.close = AsyncMock()

        mock_context = AsyncMock()
        mock_context.add_cookies = AsyncMock()
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_context.route = AsyncMock()
        mock_context.close = AsyncMock()

        mock_browser = AsyncMock()
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_browser.close = AsyncMock()

        mock_playwright = MagicMock()
        mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_playwright.stop = AsyncMock()

        with patch("pynotebooklm.session.async_playwright") as mock_async_pw:
            mock_pw_instance = AsyncMock()
            mock_pw_instance.start = AsyncMock(return_value=mock_playwright)
            mock_async_pw.return_value = mock_pw_instance

            with pytest.raises(AuthenticationError) as exc_info:
                await session.__aenter__()

            assert "expired" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_aenter_browser_launch_failure(
        self, mock_auth_manager: AuthManager
    ) -> None:
        """__aenter__ raises BrowserError when browser fails to launch."""
        session = BrowserSession(mock_auth_manager)

        mock_playwright = MagicMock()
        mock_playwright.chromium.launch = AsyncMock(
            side_effect=Exception("Failed to launch")
        )
        mock_playwright.stop = AsyncMock()

        with patch("pynotebooklm.session.async_playwright") as mock_async_pw:
            mock_pw_instance = AsyncMock()
            mock_pw_instance.start = AsyncMock(return_value=mock_playwright)
            mock_async_pw.return_value = mock_pw_instance

            with pytest.raises(BrowserError):
                await session.__aenter__()

    @pytest.mark.asyncio
    async def test_persistent_aenter_success(
        self, mock_auth_manager: AuthManager
    ) -> None:
        """PersistentBrowserSession starts using a pooled context."""
        session = PersistentBrowserSession(mock_auth_manager)

        mock_page = AsyncMock()
        mock_page.url = "https://notebooklm.google.com/"
        mock_page.goto = AsyncMock()
        mock_page.set_default_timeout = MagicMock()
        mock_page.evaluate = AsyncMock(return_value="csrf_token")
        mock_page.close = AsyncMock()

        mock_context = AsyncMock()
        mock_context.clear_cookies = AsyncMock()
        mock_context.add_cookies = AsyncMock()
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_context.close = AsyncMock()

        mock_pool = AsyncMock()
        mock_pool.acquire_context = AsyncMock(return_value=mock_context)
        mock_pool.browser = AsyncMock()
        mock_pool.playwright = AsyncMock()

        with patch(
            "pynotebooklm.session.PersistentBrowserSession._get_pool",
            AsyncMock(return_value=mock_pool),
        ):
            result = await session.__aenter__()

            assert result is session
            assert session._page is not None
            assert session.csrf_token == "csrf_token"

    @pytest.mark.asyncio
    async def test_aexit_cleanup(self, mock_auth_manager: AuthManager) -> None:
        """__aexit__ cleans up browser resources."""
        session = BrowserSession(mock_auth_manager)

        # Set up mock resources - save refs before cleanup
        mock_page = AsyncMock()
        mock_page.close = AsyncMock()
        mock_context = AsyncMock()
        mock_context.close = AsyncMock()
        mock_browser = AsyncMock()
        mock_browser.close = AsyncMock()
        mock_playwright = AsyncMock()
        mock_playwright.stop = AsyncMock()

        session._page = mock_page
        session._context = mock_context
        session._browser = mock_browser
        session._playwright = mock_playwright

        await session.__aexit__(None, None, None)

        mock_page.close.assert_called_once()
        mock_context.close.assert_called_once()
        mock_browser.close.assert_called_once()
        mock_playwright.stop.assert_called_once()
        assert session._page is None
        assert session._context is None
        assert session._browser is None
        assert session._playwright is None


# =============================================================================
# Cleanup Tests
# =============================================================================


class TestBrowserSessionCleanup:
    """Tests for _cleanup method."""

    @pytest.mark.asyncio
    async def test_cleanup_handles_errors(self, mock_auth_manager: AuthManager) -> None:
        """_cleanup handles exceptions gracefully."""
        session = BrowserSession(mock_auth_manager)

        # Set up mock resources that raise on close
        session._page = AsyncMock()
        session._page.close = AsyncMock(side_effect=Exception("Page error"))
        session._context = AsyncMock()
        session._context.close = AsyncMock(side_effect=Exception("Context error"))
        session._browser = AsyncMock()
        session._browser.close = AsyncMock(side_effect=Exception("Browser error"))
        session._playwright = AsyncMock()
        session._playwright.stop = AsyncMock(side_effect=Exception("Playwright error"))

        # Should not raise
        await session._cleanup()

        # Resources should still be set to None
        assert session._page is None
        assert session._context is None
        assert session._browser is None
        assert session._playwright is None

    @pytest.mark.asyncio
    async def test_cleanup_partial_resources(
        self, mock_auth_manager: AuthManager
    ) -> None:
        """_cleanup handles partially initialized resources."""
        session = BrowserSession(mock_auth_manager)

        # Only page is set - save ref before cleanup
        mock_page = AsyncMock()
        mock_page.close = AsyncMock()
        session._page = mock_page
        session._context = None
        session._browser = None
        session._playwright = None

        await session._cleanup()

        mock_page.close.assert_called_once()
        assert session._page is None


# =============================================================================
# Extract CSRF Token Tests
# =============================================================================


class TestBrowserSessionExtractCsrf:
    """Tests for _extract_csrf_token method."""

    @pytest.mark.asyncio
    async def test_extract_csrf_token_success(
        self, mock_auth_manager: AuthManager
    ) -> None:
        """_extract_csrf_token returns token when found."""
        session = BrowserSession(mock_auth_manager)

        mock_page = AsyncMock()
        mock_page.evaluate = AsyncMock(return_value="csrf_token_value")
        session._page = mock_page

        result = await session._extract_csrf_token()

        assert result == "csrf_token_value"

    @pytest.mark.asyncio
    async def test_extract_csrf_token_no_page(
        self, mock_auth_manager: AuthManager
    ) -> None:
        """_extract_csrf_token returns None when page not set."""
        session = BrowserSession(mock_auth_manager)
        session._page = None

        result = await session._extract_csrf_token()

        assert result is None

    @pytest.mark.asyncio
    async def test_extract_csrf_token_not_found(
        self, mock_auth_manager: AuthManager
    ) -> None:
        """_extract_csrf_token returns None when token not in page."""
        session = BrowserSession(mock_auth_manager)

        mock_page = AsyncMock()
        mock_page.evaluate = AsyncMock(return_value=None)
        session._page = mock_page

        result = await session._extract_csrf_token()

        assert result is None

    @pytest.mark.asyncio
    async def test_extract_csrf_token_error(
        self, mock_auth_manager: AuthManager
    ) -> None:
        """_extract_csrf_token returns None on error."""
        session = BrowserSession(mock_auth_manager)

        mock_page = AsyncMock()
        mock_page.evaluate = AsyncMock(side_effect=Exception("JS error"))
        session._page = mock_page

        result = await session._extract_csrf_token()

        assert result is None


# =============================================================================
# Auth Validity & CSRF Cache Tests
# =============================================================================


class TestBrowserSessionAuthAndCsrf:
    """Tests for auth validity checks and CSRF caching."""

    @pytest.mark.asyncio
    async def test_check_auth_validity_expired(self) -> None:
        auth = MagicMock()
        auth.is_authenticated.return_value = True
        auth.is_expired.return_value = True

        session = BrowserSession(auth)
        session._page = AsyncMock()
        session._page.url = "https://notebooklm.google.com/"

        with pytest.raises(AuthenticationError):
            await session._check_auth_validity()

    @pytest.mark.asyncio
    async def test_check_auth_validity_redirect(self) -> None:
        auth = MagicMock()
        auth.is_authenticated.return_value = True
        auth.is_expired.return_value = False

        session = BrowserSession(auth)
        session._page = AsyncMock()
        session._page.url = "https://accounts.google.com/signin"

        with pytest.raises(AuthenticationError):
            await session._check_auth_validity()

    @pytest.mark.asyncio
    async def test_ensure_csrf_token_uses_cache(self) -> None:
        session = BrowserSession(MagicMock())
        session._page = AsyncMock()
        session._csrf_token = "cached"
        session._csrf_cached_at = datetime.now()

        with patch.object(session, "_extract_csrf_token", AsyncMock()) as extractor:
            await session._ensure_csrf_token()
            extractor.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_ensure_csrf_token_refreshes(self) -> None:
        session = BrowserSession(MagicMock())
        session._page = AsyncMock()
        session._csrf_token = "old"
        session._csrf_cached_at = datetime.now() - timedelta(seconds=600)

        with patch.object(
            session, "_extract_csrf_token", AsyncMock(return_value="new")
        ) as extractor:
            await session._ensure_csrf_token()
            extractor.assert_awaited_once()
            assert session._csrf_token == "new"

    @pytest.mark.asyncio
    async def test_ensure_csrf_token_no_page(self) -> None:
        session = BrowserSession(MagicMock())
        session._page = None
        session._csrf_token = "token"
        await session._ensure_csrf_token()
        assert session._csrf_token == "token"


# =============================================================================
# Refresh Session Tests
# =============================================================================


class TestBrowserSessionRefresh:
    """Tests for auth refresh behavior."""

    @pytest.mark.asyncio
    async def test_refresh_session_recreates_context(self) -> None:
        auth = MagicMock()
        auth.is_authenticated.return_value = True
        auth.is_expired.return_value = False
        auth.get_cookies.return_value = []
        auth.refresh = AsyncMock()

        session = BrowserSession(auth, block_resources=False)
        session._browser = AsyncMock()
        session._context = AsyncMock()
        session._page = AsyncMock()

        session._context.close = AsyncMock()
        session._page.close = AsyncMock()

        new_context = AsyncMock()
        new_context.add_cookies = AsyncMock()
        new_page = AsyncMock()
        new_page.url = "https://notebooklm.google.com/"
        new_page.goto = AsyncMock()
        new_page.set_default_timeout = MagicMock()
        new_context.new_page = AsyncMock(return_value=new_page)
        session._browser.new_context = AsyncMock(return_value=new_context)

        with patch.object(
            session, "_extract_csrf_token", AsyncMock(return_value="csrf")
        ):
            await session._refresh_session()

        auth.refresh.assert_awaited_once()
        session._browser.new_context.assert_awaited_once()
        new_page.goto.assert_awaited_once()
        assert session._csrf_token == "csrf"

    @pytest.mark.asyncio
    async def test_refresh_session_requires_browser(self) -> None:
        auth = MagicMock()
        auth.is_authenticated.return_value = True
        auth.is_expired.return_value = False
        auth.refresh = AsyncMock()

        session = BrowserSession(auth)
        session._browser = None

        with pytest.raises(SessionError):
            await session._refresh_session()

    @pytest.mark.asyncio
    async def test_refresh_session_auth_failure(self) -> None:
        auth = MagicMock()
        auth.is_authenticated.return_value = True
        auth.is_expired.return_value = False
        auth.get_cookies.return_value = []
        auth.refresh = AsyncMock()

        session = BrowserSession(auth, block_resources=True)
        session._browser = AsyncMock()
        session._context = AsyncMock()
        session._page = AsyncMock()

        session._context.close = AsyncMock()
        session._page.close = AsyncMock()

        new_context = AsyncMock()
        new_context.add_cookies = AsyncMock()
        new_page = AsyncMock()
        new_page.url = "https://accounts.google.com/"
        new_page.goto = AsyncMock()
        new_page.set_default_timeout = MagicMock()
        new_context.new_page = AsyncMock(return_value=new_page)
        session._browser.new_context = AsyncMock(return_value=new_context)

        with patch.object(session, "_apply_resource_blocking", AsyncMock()):
            with pytest.raises(AuthenticationError):
                await session._refresh_session()


# =============================================================================
# Resource Blocking Tests
# =============================================================================


class TestRouteBlocking:
    """Tests for resource blocking logic."""

    @pytest.mark.asyncio
    async def test_route_request_blocks_resources(self) -> None:
        session = BrowserSession(MagicMock())
        route = AsyncMock()
        request = MagicMock()
        request.resource_type = "stylesheet"

        await session._route_request(route, request)

        route.abort.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_route_request_allows_other_resources(self) -> None:
        session = BrowserSession(MagicMock())
        route = AsyncMock()
        request = MagicMock()
        request.resource_type = "document"

        await session._route_request(route, request)

        route.continue_.assert_awaited_once()


# =============================================================================
# Browser Pool Tests
# =============================================================================


class TestBrowserPool:
    """Tests for the shared browser pool."""

    @pytest.mark.asyncio
    async def test_pool_acquire_release_and_shutdown(self) -> None:
        mock_context = AsyncMock()
        mock_context.is_closed = MagicMock(return_value=False)
        mock_context.close = AsyncMock()

        mock_browser = AsyncMock()
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_browser.close = AsyncMock()

        mock_playwright = MagicMock()
        mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_playwright.stop = AsyncMock()

        mock_pw_instance = AsyncMock()
        mock_pw_instance.start = AsyncMock(return_value=mock_playwright)

        with patch(
            "pynotebooklm.session.async_playwright", return_value=mock_pw_instance
        ):
            pool = _BrowserPool(
                headless=True,
                launch_args=[],
                context_options={},
                block_resources=False,
                max_contexts=1,
            )

            context = await pool.acquire_context(AsyncMock())
            assert context is mock_context

            await pool.release_context(context)
            await pool.shutdown()

        mock_context.close.assert_awaited()
        mock_browser.close.assert_awaited_once()
        mock_playwright.stop.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_pool_release_context_closed(self) -> None:
        pool = _BrowserPool(
            headless=True,
            launch_args=[],
            context_options={},
            block_resources=False,
            max_contexts=1,
        )
        context = MagicMock()
        context.is_closed.return_value = True
        await pool.release_context(context)

    @pytest.mark.asyncio
    async def test_pool_acquire_from_queue(self) -> None:
        pool = _BrowserPool(
            headless=True,
            launch_args=[],
            context_options={},
            block_resources=False,
            max_contexts=1,
        )
        pool._browser = AsyncMock()
        queued_context = AsyncMock()
        pool._contexts.put_nowait(queued_context)
        context = await pool.acquire_context(AsyncMock())
        assert context is queued_context


class TestPersistentBrowserSessionPool:
    """Tests for PersistentBrowserSession pool lifecycle."""

    @pytest.mark.asyncio
    async def test_shutdown_pool(self) -> None:
        mock_pool = AsyncMock()
        PersistentBrowserSession._pool = mock_pool
        await PersistentBrowserSession.shutdown_pool()
        mock_pool.shutdown.assert_awaited_once()
        assert PersistentBrowserSession._pool is None


# =============================================================================
# RPC Call Tests
# =============================================================================


class TestBrowserSessionCallRpc:
    """Tests for call_rpc method."""

    @pytest.mark.asyncio
    async def test_call_rpc_success(self, mock_auth_manager: AuthManager) -> None:
        """call_rpc returns parsed response data."""
        session = BrowserSession(mock_auth_manager)
        session._csrf_token = "csrf_token"
        session._csrf_cached_at = datetime.now()

        mock_page = AsyncMock()
        mock_page.url = "https://notebooklm.google.com/"
        # Simulate successful RPC response with properly formatted text
        # The response format is: anti-XSSI prefix, byte count, then JSON
        # The inner data at [0][2] is a JSON-encoded string that gets parsed
        inner_data = '{"notebooks":[]}'
        # Build the outer JSON: [["wrb.fr", "rpc_id", "<json-string>", null, ...]]
        import json

        outer_json = json.dumps(
            [["wrb.fr", "rpc_id", inner_data, None, None, None, "generic"]]
        )
        response_text = ")]}'\n" + "12345\n" + outer_json
        mock_page.evaluate = AsyncMock(
            return_value={
                "ok": True,
                "status": 200,
                "text": response_text,
            }
        )
        session._page = mock_page

        result = await session.call_rpc("wXbhsf", [None, 1])

        assert result == {"notebooks": []}

    @pytest.mark.asyncio
    async def test_call_rpc_no_page(self, mock_auth_manager: AuthManager) -> None:
        """call_rpc raises SessionError when page not set."""
        session = BrowserSession(mock_auth_manager)
        session._page = None

        with pytest.raises(SessionError):
            await session.call_rpc("wXbhsf", [])

    @pytest.mark.asyncio
    async def test_call_rpc_api_error(self, mock_auth_manager: AuthManager) -> None:
        """call_rpc raises APIError on fetch failure."""
        session = BrowserSession(mock_auth_manager)
        session._csrf_token = "csrf_token"
        session._csrf_cached_at = datetime.now()

        mock_page = AsyncMock()
        mock_page.url = "https://notebooklm.google.com/"
        mock_page.evaluate = AsyncMock(
            return_value={
                "ok": False,
                "status": 500,
                "statusText": "Internal Server Error",
                "text": "Error",
            }
        )
        session._page = mock_page

        with pytest.raises(APIError):
            await session.call_rpc("wXbhsf", [])

    @pytest.mark.asyncio
    async def test_call_rpc_exception(self, mock_auth_manager: AuthManager) -> None:
        """call_rpc wraps exceptions in APIError."""
        session = BrowserSession(mock_auth_manager)
        session._csrf_token = "csrf_token"
        session._csrf_cached_at = datetime.now()

        mock_page = AsyncMock()
        mock_page.url = "https://notebooklm.google.com/"
        mock_page.evaluate = AsyncMock(side_effect=Exception("Network error"))
        session._page = mock_page

        with pytest.raises(APIError):
            await session.call_rpc("wXbhsf", [])


# =============================================================================
# API Call Tests
# =============================================================================


class TestBrowserSessionCallApi:
    """Tests for call_api method."""

    @pytest.mark.asyncio
    async def test_call_api_success(self, mock_auth_manager: AuthManager) -> None:
        """call_api returns JSON response."""
        session = BrowserSession(mock_auth_manager)
        session._csrf_token = "csrf_token"
        session._csrf_cached_at = datetime.now()

        mock_page = AsyncMock()
        mock_page.url = "https://notebooklm.google.com/"
        mock_page.evaluate = AsyncMock(
            return_value={
                "ok": True,
                "status": 200,
                "json": {"data": "value"},
                "text": "",
            }
        )
        session._page = mock_page

        result = await session.call_api("https://example.com/api")

        assert result == {"data": "value"}

    @pytest.mark.asyncio
    async def test_call_api_no_page(self, mock_auth_manager: AuthManager) -> None:
        """call_api raises SessionError when page not set."""
        session = BrowserSession(mock_auth_manager)
        session._page = None

        with pytest.raises(SessionError):
            await session.call_api("https://example.com/api")

    @pytest.mark.asyncio
    async def test_call_api_with_data(self, mock_auth_manager: AuthManager) -> None:
        """call_api sends POST data correctly."""
        session = BrowserSession(mock_auth_manager)
        session._csrf_token = "csrf_token"
        session._csrf_cached_at = datetime.now()

        mock_page = AsyncMock()
        mock_page.url = "https://notebooklm.google.com/"
        mock_page.evaluate = AsyncMock(
            return_value={
                "ok": True,
                "status": 200,
                "json": {"success": True},
                "text": "",
            }
        )
        session._page = mock_page

        result = await session.call_api(
            "https://example.com/api",
            method="POST",
            data={"key": "value"},
        )

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_call_api_with_headers(self, mock_auth_manager: AuthManager) -> None:
        """call_api passes custom headers."""
        session = BrowserSession(mock_auth_manager)
        session._csrf_token = "csrf_token"
        session._csrf_cached_at = datetime.now()

        mock_page = AsyncMock()
        mock_page.url = "https://notebooklm.google.com/"
        mock_page.evaluate = AsyncMock(
            return_value={
                "ok": True,
                "status": 200,
                "json": {},
                "text": "",
            }
        )
        session._page = mock_page

        await session.call_api(
            "https://example.com/api",
            headers={"X-Custom": "header"},
        )

        # Verify evaluate was called with headers
        call_args = mock_page.evaluate.call_args
        assert "X-Custom" in str(call_args)

    @pytest.mark.asyncio
    async def test_call_api_error(self, mock_auth_manager: AuthManager) -> None:
        """call_api raises APIError on failure."""
        session = BrowserSession(mock_auth_manager)
        session._csrf_token = "csrf_token"
        session._csrf_cached_at = datetime.now()

        mock_page = AsyncMock()
        mock_page.url = "https://notebooklm.google.com/"
        mock_page.evaluate = AsyncMock(
            return_value={
                "ok": False,
                "status": 404,
                "json": None,
                "text": "Not Found",
            }
        )
        session._page = mock_page

        with pytest.raises(APIError) as exc_info:
            await session.call_api("https://example.com/api")

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_call_api_exception(self, mock_auth_manager: AuthManager) -> None:
        """call_api wraps exceptions in APIError."""
        session = BrowserSession(mock_auth_manager)
        session._csrf_token = "csrf_token"
        session._csrf_cached_at = datetime.now()

        mock_page = AsyncMock()
        mock_page.url = "https://notebooklm.google.com/"
        mock_page.evaluate = AsyncMock(side_effect=Exception("Network error"))
        session._page = mock_page

        with pytest.raises(APIError):
            await session.call_api("https://example.com/api")

    @pytest.mark.asyncio
    async def test_call_api_null_json(self, mock_auth_manager: AuthManager) -> None:
        """call_api returns empty dict when json is null."""
        session = BrowserSession(mock_auth_manager)
        session._csrf_token = "csrf_token"
        session._csrf_cached_at = datetime.now()

        mock_page = AsyncMock()
        mock_page.url = "https://notebooklm.google.com/"
        mock_page.evaluate = AsyncMock(
            return_value={
                "ok": True,
                "status": 200,
                "json": None,
                "text": "",
            }
        )
        session._page = mock_page

        result = await session.call_api("https://example.com/api")

        assert result == {}


# =============================================================================
# Auto-Refresh Call Tests
# =============================================================================


class TestBrowserSessionAutoRefresh:
    """Tests for auto-refresh behavior on API calls."""

    @pytest.mark.asyncio
    async def test_call_api_raw_auto_refresh(self) -> None:
        auth = MagicMock()
        auth.is_authenticated.return_value = True
        auth.is_expired.return_value = False

        session = BrowserSession(auth, auto_refresh=True)
        session._page = AsyncMock()
        session._page.url = "https://notebooklm.google.com/"
        session._csrf_token = "token"
        session._csrf_cached_at = datetime.now()

        response_auth = {"ok": True, "status": 200, "text": "accounts.google.com"}
        response_ok = {"ok": True, "status": 200, "text": "ok"}
        session._page.evaluate = AsyncMock(side_effect=[response_auth, response_ok])

        with patch.object(session, "_refresh_session", AsyncMock()) as refresh_mock:
            result = await session.call_api_raw("https://example.com")

        refresh_mock.assert_awaited_once()
        assert result == "ok"

    @pytest.mark.asyncio
    async def test_call_api_auto_refresh(self) -> None:
        auth = MagicMock()
        auth.is_authenticated.return_value = True
        auth.is_expired.return_value = False

        session = BrowserSession(auth, auto_refresh=True)
        session._page = AsyncMock()
        session._page.url = "https://notebooklm.google.com/"
        session._csrf_token = "token"
        session._csrf_cached_at = datetime.now()

        response_auth = {
            "ok": True,
            "status": 200,
            "json": {},
            "text": "accounts.google.com",
        }
        response_ok = {"ok": True, "status": 200, "json": {"ok": True}, "text": ""}
        session._page.evaluate = AsyncMock(side_effect=[response_auth, response_ok])

        with patch.object(session, "_refresh_session", AsyncMock()) as refresh_mock:
            result = await session.call_api("https://example.com")

        refresh_mock.assert_awaited_once()
        assert result == {"ok": True}

    @pytest.mark.asyncio
    async def test_call_rpc_auto_refresh_on_response(self) -> None:
        auth = MagicMock()
        auth.is_authenticated.return_value = True
        auth.is_expired.return_value = False

        session = BrowserSession(auth, auto_refresh=True)
        session._page = AsyncMock()
        session._page.url = "https://notebooklm.google.com/"
        session._csrf_token = "token"
        session._csrf_cached_at = datetime.now()

        response_auth = {"ok": True, "status": 200, "text": "accounts.google.com"}
        inner_data = '{"notebooks":[]}'
        outer_json = json.dumps(
            [["wrb.fr", "rpc_id", inner_data, None, None, None, "generic"]]
        )
        response_ok = {
            "ok": True,
            "status": 200,
            "text": ")]}'\n123\n" + outer_json,
        }
        session._page.evaluate = AsyncMock(side_effect=[response_auth, response_ok])

        with patch.object(session, "_refresh_session", AsyncMock()) as refresh_mock:
            result = await session.call_rpc("rpc_id", [])

        refresh_mock.assert_awaited_once()
        assert result == {"notebooks": []}
