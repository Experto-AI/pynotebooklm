"""
Unit tests for the AuthManager class.

These tests verify authentication state management, cookie persistence,
and validation logic without requiring actual browser automation.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from pynotebooklm.auth import AuthManager
from pynotebooklm.exceptions import AuthenticationError
from pynotebooklm.models import AuthState, Cookie

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def temp_auth_dir(tmp_path: Path) -> Path:
    """Create a temporary directory for auth files."""
    auth_dir = tmp_path / ".pynotebooklm"
    auth_dir.mkdir(parents=True)
    return auth_dir


@pytest.fixture
def mock_auth_state() -> AuthState:
    """Create a mock valid auth state."""
    return AuthState(
        cookies=[
            Cookie(
                name="SID",
                value="test_sid",
                domain=".google.com",
                path="/",
            ),
            Cookie(
                name="HSID",
                value="test_hsid",
                domain=".google.com",
                path="/",
            ),
            Cookie(
                name="SSID",
                value="test_ssid",
                domain=".google.com",
                path="/",
            ),
            Cookie(
                name="APISID",
                value="test_apisid",
                domain=".google.com",
                path="/",
            ),
            Cookie(
                name="SAPISID",
                value="test_sapisid",
                domain=".google.com",
                path="/",
            ),
        ],
        csrf_token="test_csrf_token",
        authenticated_at=datetime.now(),
        expires_at=datetime.now() + timedelta(days=14),
    )


@pytest.fixture
def mock_cookies_path(tmp_path: Path) -> Path:
    """Path to mock cookies file."""
    return tmp_path / ".pynotebooklm" / "auth.json"


# =============================================================================
# AuthState Model Tests
# =============================================================================


class TestAuthState:
    """Tests for the AuthState model."""

    def test_is_valid_with_all_required_cookies(
        self, mock_auth_state: AuthState
    ) -> None:
        """Auth state is valid when all essential cookies are present."""
        assert mock_auth_state.is_valid() is True

    def test_is_valid_without_cookies(self) -> None:
        """Auth state is invalid without cookies."""
        state = AuthState(cookies=[])
        assert state.is_valid() is False

    def test_is_valid_missing_required_cookie(self) -> None:
        """Auth state is invalid when missing required cookies."""
        state = AuthState(
            cookies=[
                Cookie(name="SID", value="test", domain=".google.com", path="/"),
                Cookie(name="HSID", value="test", domain=".google.com", path="/"),
                # Missing SSID
            ],
            authenticated_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=14),
        )
        assert state.is_valid() is False

    def test_is_valid_expired(self, mock_auth_state: AuthState) -> None:
        """Auth state is invalid when expired."""
        mock_auth_state.expires_at = datetime.now() - timedelta(days=1)
        assert mock_auth_state.is_valid() is False


# =============================================================================
# AuthManager Initialization Tests
# =============================================================================


class TestAuthManagerInit:
    """Tests for AuthManager initialization."""

    def test_creates_config_directory(self, tmp_path: Path) -> None:
        """AuthManager creates the config directory if it doesn't exist."""
        auth_path = tmp_path / "new_dir" / "auth.json"
        AuthManager(auth_path=auth_path)
        assert auth_path.parent.exists()

    def test_loads_existing_auth_state(
        self, mock_cookies_path: Path, mock_auth_state: AuthState
    ) -> None:
        """AuthManager loads existing auth state from file."""
        mock_cookies_path.parent.mkdir(parents=True)
        mock_cookies_path.write_text(mock_auth_state.model_dump_json())

        auth = AuthManager(auth_path=mock_cookies_path)
        assert auth.is_authenticated() is True

    def test_handles_missing_auth_file(self, tmp_path: Path) -> None:
        """AuthManager handles missing auth file gracefully."""
        auth_path = tmp_path / ".pynotebooklm" / "auth.json"
        auth = AuthManager(auth_path=auth_path)
        assert auth.is_authenticated() is False

    def test_handles_corrupted_auth_file(self, mock_cookies_path: Path) -> None:
        """AuthManager handles corrupted auth file gracefully."""
        mock_cookies_path.parent.mkdir(parents=True)
        mock_cookies_path.write_text("not valid json {{{")

        auth = AuthManager(auth_path=mock_cookies_path)
        assert auth.is_authenticated() is False

    def test_handles_invalid_auth_schema(self, mock_cookies_path: Path) -> None:
        """AuthManager handles invalid auth schema gracefully."""
        mock_cookies_path.parent.mkdir(parents=True)
        mock_cookies_path.write_text('{"invalid": "schema"}')

        auth = AuthManager(auth_path=mock_cookies_path)
        # Should not crash, but auth state may be invalid
        assert auth.is_authenticated() is False


# =============================================================================
# AuthManager Cookie Management Tests
# =============================================================================


class TestAuthManagerCookies:
    """Tests for cookie management methods."""

    def test_get_cookies_when_authenticated(
        self, mock_cookies_path: Path, mock_auth_state: AuthState
    ) -> None:
        """get_cookies returns cookies in Playwright format."""
        mock_cookies_path.parent.mkdir(parents=True)
        mock_cookies_path.write_text(mock_auth_state.model_dump_json())

        auth = AuthManager(auth_path=mock_cookies_path)
        cookies = auth.get_cookies()

        assert len(cookies) == 5
        assert all("name" in c for c in cookies)
        assert all("value" in c for c in cookies)
        assert all("domain" in c for c in cookies)

    def test_get_cookies_raises_when_not_authenticated(self, tmp_path: Path) -> None:
        """get_cookies raises AuthenticationError when not authenticated."""
        auth_path = tmp_path / ".pynotebooklm" / "auth.json"
        auth = AuthManager(auth_path=auth_path)

        with pytest.raises(AuthenticationError):
            auth.get_cookies()

    def test_get_csrf_token(
        self, mock_cookies_path: Path, mock_auth_state: AuthState
    ) -> None:
        """get_csrf_token returns the stored CSRF token."""
        mock_cookies_path.parent.mkdir(parents=True)
        mock_cookies_path.write_text(mock_auth_state.model_dump_json())

        auth = AuthManager(auth_path=mock_cookies_path)
        assert auth.get_csrf_token() == "test_csrf_token"

    def test_get_csrf_token_returns_none_when_not_authenticated(
        self, tmp_path: Path
    ) -> None:
        """get_csrf_token returns None when not authenticated."""
        auth_path = tmp_path / ".pynotebooklm" / "auth.json"
        auth = AuthManager(auth_path=auth_path)
        assert auth.get_csrf_token() is None


# =============================================================================
# AuthManager Logout Tests
# =============================================================================


class TestAuthManagerLogout:
    """Tests for logout functionality."""

    def test_logout_clears_auth_state(
        self, mock_cookies_path: Path, mock_auth_state: AuthState
    ) -> None:
        """logout() clears the authentication state."""
        mock_cookies_path.parent.mkdir(parents=True)
        mock_cookies_path.write_text(mock_auth_state.model_dump_json())

        auth = AuthManager(auth_path=mock_cookies_path)
        assert auth.is_authenticated() is True

        auth.logout()
        assert auth.is_authenticated() is False
        assert not mock_cookies_path.exists()

    def test_logout_handles_missing_file(self, tmp_path: Path) -> None:
        """logout() handles missing auth file gracefully."""
        auth_path = tmp_path / ".pynotebooklm" / "auth.json"
        auth = AuthManager(auth_path=auth_path)
        auth.logout()  # Should not raise


# =============================================================================
# Cookie Model Tests
# =============================================================================


class TestCookieModel:
    """Tests for the Cookie model."""

    def test_cookie_serialization(self) -> None:
        """Cookie model serializes correctly."""
        cookie = Cookie(
            name="SID",
            value="test_value",
            domain=".google.com",
            path="/",
            expires=1234567890.0,
            http_only=True,
            secure=True,
            same_site="Strict",
        )

        data = cookie.model_dump()
        assert data["name"] == "SID"
        assert data["value"] == "test_value"
        assert data["domain"] == ".google.com"
        assert data["http_only"] is True
        assert data["secure"] is True
        assert data["same_site"] == "Strict"

    def test_cookie_deserialization(self) -> None:
        """Cookie model deserializes correctly."""
        data = {
            "name": "HSID",
            "value": "test_value",
            "domain": ".google.com",
            "path": "/",
        }

        cookie = Cookie.model_validate(data)
        assert cookie.name == "HSID"
        assert cookie.value == "test_value"
        assert cookie.http_only is False  # default
        assert cookie.same_site == "Lax"  # default


# =============================================================================
# Save Cookies Tests
# =============================================================================


class TestSaveCookies:
    """Tests for cookie persistence."""

    def test_save_cookies_creates_file(self, tmp_path: Path) -> None:
        """_save_cookies creates the auth file."""
        auth_path = tmp_path / ".pynotebooklm" / "auth.json"
        auth = AuthManager(auth_path=auth_path)

        # Manually set auth state
        auth._auth_state = AuthState(
            cookies=[
                Cookie(name="SID", value="test", domain=".google.com", path="/"),
                Cookie(name="HSID", value="test", domain=".google.com", path="/"),
                Cookie(name="SSID", value="test", domain=".google.com", path="/"),
            ],
            authenticated_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=14),
        )

        auth._save_cookies()

        assert auth_path.exists()
        data = json.loads(auth_path.read_text())
        assert len(data["cookies"]) == 3

    def test_save_cookies_skips_when_no_state(self, tmp_path: Path) -> None:
        """_save_cookies does nothing when auth state is None."""
        auth_path = tmp_path / ".pynotebooklm" / "auth.json"
        auth = AuthManager(auth_path=auth_path)
        auth._save_cookies()  # Should not raise
        assert not auth_path.exists()
