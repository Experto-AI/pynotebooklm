"""
Unit tests for the BrowserSession class.

These tests verify session management, RPC encoding/parsing,
and error handling without requiring actual browser automation.
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from pynotebooklm.auth import AuthManager
from pynotebooklm.exceptions import (
    APIError,
    AuthenticationError,
    RateLimitError,
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


@pytest.fixture
def unauthenticated_auth_manager(tmp_path: Path) -> AuthManager:
    """Create an unauthenticated AuthManager."""
    auth_path = tmp_path / ".pynotebooklm" / "auth.json"
    return AuthManager(auth_path=auth_path)


# =============================================================================
# BrowserSession Initialization Tests
# =============================================================================


class TestBrowserSessionInit:
    """Tests for BrowserSession initialization."""

    def test_init_stores_auth_manager(self, mock_auth_manager: AuthManager) -> None:
        """BrowserSession stores the auth manager."""
        session = BrowserSession(mock_auth_manager)
        assert session.auth is mock_auth_manager

    def test_init_default_headless(self, mock_auth_manager: AuthManager) -> None:
        """BrowserSession defaults to headless mode."""
        session = BrowserSession(mock_auth_manager)
        assert session.headless is True

    def test_init_custom_headless(self, mock_auth_manager: AuthManager) -> None:
        """BrowserSession accepts custom headless setting."""
        session = BrowserSession(mock_auth_manager, headless=False)
        assert session.headless is False

    def test_init_default_timeout(self, mock_auth_manager: AuthManager) -> None:
        """BrowserSession has default timeout."""
        session = BrowserSession(mock_auth_manager)
        assert session.timeout == 60000

    def test_init_custom_timeout(self, mock_auth_manager: AuthManager) -> None:
        """BrowserSession accepts custom timeout."""
        session = BrowserSession(mock_auth_manager, timeout=60000)
        assert session.timeout == 60000


# =============================================================================
# Payload Encoding Tests
# =============================================================================


class TestPayloadEncoding:
    """Tests for RPC payload encoding."""

    def test_encode_payload_basic(self, mock_auth_manager: AuthManager) -> None:
        """_encode_payload creates properly formatted requests."""
        session = BrowserSession(mock_auth_manager)
        session._csrf_token = "test_token"

        payload = session._encode_payload("wXbhsf", [None, 1, None, [2]])

        # Should contain f.req parameter
        assert "f.req=" in payload
        # Should contain CSRF token
        assert "at=" in payload
        # Should be URL encoded
        assert "%5B" in payload or "%5D" in payload  # encoded brackets

    def test_encode_payload_without_csrf(self, mock_auth_manager: AuthManager) -> None:
        """_encode_payload works without CSRF token."""
        session = BrowserSession(mock_auth_manager)
        session._csrf_token = None

        payload = session._encode_payload("wXbhsf", [None, 1])

        assert "f.req=" in payload
        assert "at=" not in payload

    def test_encode_payload_complex_params(
        self, mock_auth_manager: AuthManager
    ) -> None:
        """_encode_payload handles complex parameters."""
        session = BrowserSession(mock_auth_manager)
        session._csrf_token = "token"

        params = ["string", 123, {"key": "value"}, [1, 2, 3], None]
        payload = session._encode_payload("rpc_id", params)

        # Verify it's a string
        assert isinstance(payload, str)
        # Verify it contains the rpc_id
        assert "rpc_id" in payload


# =============================================================================
# Response Parsing Tests
# =============================================================================


class TestResponseParsing:
    """Tests for RPC response parsing."""

    def test_parse_response_success(self, mock_auth_manager: AuthManager) -> None:
        """_parse_response handles successful responses."""
        session = BrowserSession(mock_auth_manager)

        # Mock response with anti-XSSI prefix - simulating real NotebookLM format
        # Format: anti-XSSI prefix, then byte count line, then JSON array
        inner_data = '{"notebooks":[]}'
        json_line = json.dumps(
            [["wrb.fr", "rpc_id", inner_data, None, None, None, "generic"]]
        )
        response = {
            "ok": True,
            "status": 200,
            "text": f")]}}'\n12345\n{json_line}",
        }

        result = session._parse_response(response)
        assert result is not None

    def test_parse_response_rate_limit(self, mock_auth_manager: AuthManager) -> None:
        """_parse_response raises RateLimitError on 429."""
        session = BrowserSession(mock_auth_manager)

        response = {
            "ok": False,
            "status": 429,
            "text": "",
        }

        with pytest.raises(RateLimitError):
            session._parse_response(response)

    def test_parse_response_api_error(self, mock_auth_manager: AuthManager) -> None:
        """_parse_response raises APIError on failure."""
        session = BrowserSession(mock_auth_manager)

        response = {
            "ok": False,
            "status": 500,
            "statusText": "Internal Server Error",
            "text": "Error",
        }

        with pytest.raises(APIError) as exc_info:
            session._parse_response(response)

        assert exc_info.value.status_code == 500

    def test_parse_response_invalid_format(
        self, mock_auth_manager: AuthManager
    ) -> None:
        """_parse_response raises APIError on invalid format."""
        session = BrowserSession(mock_auth_manager)

        response = {
            "ok": True,
            "status": 200,
            "text": ")]}'\n",  # Missing data line
        }

        with pytest.raises(APIError):
            session._parse_response(response)

    def test_parse_streaming_response_handles_partial(
        self, mock_auth_manager: AuthManager
    ) -> None:
        """parse_streaming_response buffers partial JSON lines."""
        session = BrowserSession(mock_auth_manager)

        response_text = ")]}'\n10\n[1,2\n,3]\n"
        chunks = session.parse_streaming_response(response_text)

        assert chunks == [[1, 2, 3]]

    def test_parse_response_no_data_lines(self, mock_auth_manager: AuthManager) -> None:
        session = BrowserSession(mock_auth_manager)

        response = {
            "ok": True,
            "status": 200,
            "text": ")]}'\n123\n",
        }

        with pytest.raises(APIError):
            session._parse_response(response)

    def test_parse_response_malformed_json(
        self, mock_auth_manager: AuthManager
    ) -> None:
        session = BrowserSession(mock_auth_manager)

        response = {
            "ok": True,
            "status": 200,
            "text": ")]}'\nabc\n{not-json}",
        }

        with pytest.raises(APIError):
            session._parse_response(response)

    def test_parse_streaming_response_handles_empty(
        self, mock_auth_manager: AuthManager
    ) -> None:
        session = BrowserSession(mock_auth_manager)
        assert session.parse_streaming_response("") == []

    def test_parse_streaming_response_skips_malformed(
        self, mock_auth_manager: AuthManager
    ) -> None:
        session = BrowserSession(mock_auth_manager)
        response_text = ")]}'\n5\n{bad}\n"
        chunks = session.parse_streaming_response(response_text)
        assert chunks == []


# =============================================================================
# Session Property Tests
# =============================================================================


class TestSessionProperties:
    """Tests for session property access."""

    def test_page_raises_when_not_active(self, mock_auth_manager: AuthManager) -> None:
        """page property raises SessionError when not in context."""
        session = BrowserSession(mock_auth_manager)

        with pytest.raises(SessionError):
            _ = session.page

    def test_csrf_token_none_initially(self, mock_auth_manager: AuthManager) -> None:
        """csrf_token is None before session starts."""
        session = BrowserSession(mock_auth_manager)
        assert session.csrf_token is None

    def test_is_authenticated_page_without_page(
        self, mock_auth_manager: AuthManager
    ) -> None:
        session = BrowserSession(mock_auth_manager)
        assert session._is_authenticated_page() is False


# =============================================================================
# Context Manager Authorization Tests
# =============================================================================


class TestContextManagerAuth:
    """Tests for context manager authentication checks."""

    @pytest.mark.asyncio
    async def test_aenter_raises_when_not_authenticated(
        self, unauthenticated_auth_manager: AuthManager
    ) -> None:
        """__aenter__ raises AuthenticationError when not authenticated."""
        session = BrowserSession(unauthenticated_auth_manager)

        with pytest.raises(AuthenticationError):
            async with session:
                pass


# =============================================================================
# RPC Call Tests (with mocking)
# =============================================================================


class TestRpcCalls:
    """Tests for RPC call functionality."""

    def test_call_rpc_raises_when_not_active(
        self, mock_auth_manager: AuthManager
    ) -> None:
        """call_rpc raises SessionError when session not active."""
        session = BrowserSession(mock_auth_manager)

        # The method is async, we need to await it
        import asyncio

        with pytest.raises(SessionError):
            asyncio.get_event_loop().run_until_complete(session.call_rpc("wXbhsf", []))

    def test_call_api_raises_when_not_active(
        self, mock_auth_manager: AuthManager
    ) -> None:
        """call_api raises SessionError when session not active."""
        session = BrowserSession(mock_auth_manager)

        import asyncio

        with pytest.raises(SessionError):
            asyncio.get_event_loop().run_until_complete(
                session.call_api("https://example.com")
            )


# =============================================================================
# Exception Tests
# =============================================================================


class TestExceptions:
    """Tests for exception handling."""

    def test_api_error_with_status_code(self) -> None:
        """APIError includes status code in message."""
        error = APIError("Test error", status_code=404)
        assert "404" in str(error)
        assert error.status_code == 404

    def test_api_error_with_response_body(self) -> None:
        """APIError stores response body."""
        error = APIError("Test error", response_body="Detail message")
        assert error.response_body == "Detail message"

    def test_rate_limit_error_with_retry_after(self) -> None:
        """RateLimitError includes retry_after."""
        error = RateLimitError("Rate limited", retry_after=60)
        assert error.retry_after == 60
        assert "60 seconds" in str(error)

    def test_session_error_message(self) -> None:
        """SessionError has correct message."""
        error = SessionError("Custom message")
        assert error.message == "Custom message"


class TestSessionHelpers:
    """Tests for helper utilities."""

    def test_response_indicates_auth_failure(
        self, mock_auth_manager: AuthManager
    ) -> None:
        session = BrowserSession(mock_auth_manager)
        assert session._response_indicates_auth_failure(
            "https://accounts.google.com/ServiceLogin"
        )
        assert session._response_indicates_auth_failure("accounts.google.com")
        assert not session._response_indicates_auth_failure("ok")

    def test_emit_telemetry_logs(
        self, mock_auth_manager: AuthManager, monkeypatch, caplog
    ) -> None:
        session = BrowserSession(mock_auth_manager)
        monkeypatch.setenv("PYNOTEBOOKLM_TELEMETRY", "1")
        with caplog.at_level(logging.INFO):
            session._emit_telemetry("rpc_id", 12.3, True)
        assert "rpc_call" in caplog.text

    def test_sanitize_headers(self) -> None:
        from pynotebooklm import session as session_module

        headers = {"Cookie": "secret", "Authorization": "token", "X": "ok"}
        sanitized = session_module._sanitize_headers(headers)
        assert sanitized["Cookie"] == "[REDACTED]"
        assert sanitized["Authorization"] == "[REDACTED]"
        assert sanitized["X"] == "ok"

    def test_sanitize_text(self) -> None:
        from pynotebooklm import session as session_module

        text = "at=token&SID=abc"
        sanitized = session_module._sanitize_text(text)
        assert "REDACTED" in sanitized

    def test_log_if_debug(self, monkeypatch) -> None:
        from pynotebooklm import session as session_module

        monkeypatch.setenv("PYNOTEBOOKLM_DEBUG", "1")
        messages: list[str] = []

        def recorder(message: str) -> None:
            messages.append(message)

        session_module._log_if_debug(recorder, "hello")
        assert messages == ["hello"]
