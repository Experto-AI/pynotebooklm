"""
Additional unit tests for BrowserSession async methods.

These tests verify browser lifecycle management, RPC calls,
and API calls using mocked Playwright components.
"""

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
from pynotebooklm.session import BrowserSession

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
# RPC Call Tests
# =============================================================================


class TestBrowserSessionCallRpc:
    """Tests for call_rpc method."""

    @pytest.mark.asyncio
    async def test_call_rpc_success(self, mock_auth_manager: AuthManager) -> None:
        """call_rpc returns parsed response data."""
        session = BrowserSession(mock_auth_manager)
        session._csrf_token = "csrf_token"

        mock_page = AsyncMock()
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

        mock_page = AsyncMock()
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

        mock_page = AsyncMock()
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

        mock_page = AsyncMock()
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

        mock_page = AsyncMock()
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

        mock_page = AsyncMock()
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

        mock_page = AsyncMock()
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

        mock_page = AsyncMock()
        mock_page.evaluate = AsyncMock(side_effect=Exception("Network error"))
        session._page = mock_page

        with pytest.raises(APIError):
            await session.call_api("https://example.com/api")

    @pytest.mark.asyncio
    async def test_call_api_null_json(self, mock_auth_manager: AuthManager) -> None:
        """call_api returns empty dict when json is null."""
        session = BrowserSession(mock_auth_manager)

        mock_page = AsyncMock()
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
