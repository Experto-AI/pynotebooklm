"""
Unit tests for the CLI module.

These tests verify CLI command functionality using Click's testing utilities,
without requiring actual browser automation.
"""

from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from typer.testing import CliRunner

from pynotebooklm.cli import app
from pynotebooklm.models import AuthState, Cookie

runner = CliRunner()


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
# Login Command Tests
# =============================================================================


class TestLoginCommand:
    """Tests for the 'login' CLI command."""

    def test_login_success(self, tmp_path: Path) -> None:
        """Login command succeeds when login() works."""
        auth_path = tmp_path / ".pynotebooklm" / "auth.json"

        with patch("pynotebooklm.cli.AuthManager") as mock_auth_cls:
            mock_auth = MagicMock()
            mock_auth.auth_path = auth_path
            mock_auth.login = AsyncMock()
            mock_auth_cls.return_value = mock_auth

            result = runner.invoke(app, ["login"])

            assert result.exit_code == 0
            assert "Login successful" in result.output
            mock_auth.login.assert_called_once()

    def test_login_with_custom_timeout(self, tmp_path: Path) -> None:
        """Login command accepts custom timeout."""
        auth_path = tmp_path / ".pynotebooklm" / "auth.json"

        with patch("pynotebooklm.cli.AuthManager") as mock_auth_cls:
            mock_auth = MagicMock()
            mock_auth.auth_path = auth_path
            mock_auth.login = AsyncMock()
            mock_auth_cls.return_value = mock_auth

            result = runner.invoke(app, ["login", "--timeout", "600"])

            assert result.exit_code == 0
            mock_auth.login.assert_called_once_with(timeout=600)

    def test_login_failure(self, tmp_path: Path) -> None:
        """Login command exits with error on failure."""
        with patch("pynotebooklm.cli.AuthManager") as mock_auth_cls:
            mock_auth = MagicMock()
            mock_auth.login = AsyncMock(side_effect=Exception("Login failed"))
            mock_auth_cls.return_value = mock_auth

            result = runner.invoke(app, ["login"])

            assert result.exit_code == 1
            assert "Login failed" in result.output


# =============================================================================
# Check Command Tests
# =============================================================================


class TestCheckCommand:
    """Tests for the 'check' CLI command."""

    def test_check_authenticated(
        self, authenticated_auth_path: Path, mock_auth_state: AuthState
    ) -> None:
        """Check command shows success when authenticated."""
        with patch("pynotebooklm.cli.AuthManager") as mock_auth_cls:
            mock_auth = MagicMock()
            mock_auth.is_authenticated.return_value = True
            mock_auth.auth_path = authenticated_auth_path
            mock_auth._auth_state = mock_auth_state
            mock_auth_cls.return_value = mock_auth

            result = runner.invoke(app, ["check"])

            assert result.exit_code == 0
            assert "Authenticated: True" in result.output

    def test_check_not_authenticated(self, tmp_path: Path) -> None:
        """Check command shows failure when not authenticated."""
        with patch("pynotebooklm.cli.AuthManager") as mock_auth_cls:
            mock_auth = MagicMock()
            mock_auth.is_authenticated.return_value = False
            mock_auth_cls.return_value = mock_auth

            result = runner.invoke(app, ["check"])

            assert result.exit_code == 1
            assert "Authenticated: False" in result.output

    def test_check_shows_expiry(
        self, authenticated_auth_path: Path, mock_auth_state: AuthState
    ) -> None:
        """Check command shows expiry date when authenticated."""
        with patch("pynotebooklm.cli.AuthManager") as mock_auth_cls:
            mock_auth = MagicMock()
            mock_auth.is_authenticated.return_value = True
            mock_auth.auth_path = authenticated_auth_path
            mock_auth._auth_state = mock_auth_state
            mock_auth_cls.return_value = mock_auth

            result = runner.invoke(app, ["check"])

            assert result.exit_code == 0
            assert "Expires:" in result.output


# =============================================================================
# Logout Command Tests
# =============================================================================


class TestLogoutCommand:
    """Tests for the 'logout' CLI command."""

    def test_logout_success(self, tmp_path: Path) -> None:
        """Logout command succeeds."""
        with patch("pynotebooklm.cli.AuthManager") as mock_auth_cls:
            mock_auth = MagicMock()
            mock_auth_cls.return_value = mock_auth

            result = runner.invoke(app, ["auth", "logout"])

            assert result.exit_code == 0
            assert "Logged out" in result.output
            mock_auth.logout.assert_called_once()
