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


# =============================================================================
# Notebook Command Tests
# =============================================================================


class TestNotebookListCommand:
    """Tests for the 'notebooks list' CLI command."""

    def test_list_notebooks_not_authenticated(self) -> None:
        """List command exits when not authenticated."""
        with patch("pynotebooklm.cli.AuthManager") as mock_auth_cls:
            mock_auth = MagicMock()
            mock_auth.is_authenticated.return_value = False
            mock_auth_cls.return_value = mock_auth

            result = runner.invoke(app, ["notebooks", "list"])

            assert result.exit_code == 1
            assert "Not authenticated" in result.output

    def test_list_notebooks_success(self) -> None:
        """List command shows notebooks table."""
        from pynotebooklm.models import Notebook

        with (
            patch("pynotebooklm.cli.AuthManager") as mock_auth_cls,
            patch("pynotebooklm.cli.BrowserSession") as mock_session_cls,
            patch("pynotebooklm.cli.NotebookManager") as mock_nm_cls,
        ):
            mock_auth = MagicMock()
            mock_auth.is_authenticated.return_value = True
            mock_auth_cls.return_value = mock_auth

            mock_session = MagicMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            mock_session_cls.return_value = mock_session

            mock_nm = MagicMock()
            mock_nm.list = AsyncMock(
                return_value=[
                    Notebook(id="nb_123", name="Test Notebook", source_count=5)
                ]
            )
            mock_nm_cls.return_value = mock_nm

            result = runner.invoke(app, ["notebooks", "list"])

            assert result.exit_code == 0
            assert "Test Notebook" in result.output

    def test_list_notebooks_empty(self) -> None:
        """List command handles empty list."""
        with (
            patch("pynotebooklm.cli.AuthManager") as mock_auth_cls,
            patch("pynotebooklm.cli.BrowserSession") as mock_session_cls,
            patch("pynotebooklm.cli.NotebookManager") as mock_nm_cls,
        ):
            mock_auth = MagicMock()
            mock_auth.is_authenticated.return_value = True
            mock_auth_cls.return_value = mock_auth

            mock_session = MagicMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            mock_session_cls.return_value = mock_session

            mock_nm = MagicMock()
            mock_nm.list = AsyncMock(return_value=[])
            mock_nm_cls.return_value = mock_nm

            result = runner.invoke(app, ["notebooks", "list"])

            assert result.exit_code == 0
            assert "No notebooks found" in result.output

    def test_list_notebooks_short_view(self) -> None:
        """List command with --short shows only IDs and names."""
        from pynotebooklm.models import Notebook

        with (
            patch("pynotebooklm.cli.AuthManager") as mock_auth_cls,
            patch("pynotebooklm.cli.BrowserSession") as mock_session_cls,
            patch("pynotebooklm.cli.NotebookManager") as mock_nm_cls,
        ):
            mock_auth = MagicMock()
            mock_auth.is_authenticated.return_value = True
            mock_auth_cls.return_value = mock_auth

            mock_session = MagicMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            mock_session_cls.return_value = mock_session

            mock_nm = MagicMock()
            mock_nm.list = AsyncMock(
                return_value=[
                    Notebook(id="nb_short_123", name="Short View Test", source_count=3)
                ]
            )
            mock_nm_cls.return_value = mock_nm

            result = runner.invoke(app, ["notebooks", "list", "--short"])

            assert result.exit_code == 0
            assert "nb_short_123" in result.output
            assert "Short View Test" in result.output

    def test_list_notebooks_detailed_view(self) -> None:
        """List command with --detailed shows timestamps."""
        from pynotebooklm.models import Notebook

        with (
            patch("pynotebooklm.cli.AuthManager") as mock_auth_cls,
            patch("pynotebooklm.cli.BrowserSession") as mock_session_cls,
            patch("pynotebooklm.cli.NotebookManager") as mock_nm_cls,
        ):
            mock_auth = MagicMock()
            mock_auth.is_authenticated.return_value = True
            mock_auth_cls.return_value = mock_auth

            mock_session = MagicMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            mock_session_cls.return_value = mock_session

            mock_nm = MagicMock()
            mock_nm.list = AsyncMock(
                return_value=[
                    Notebook(
                        id="nb_detailed_456",
                        name="Detailed View Test",
                        source_count=7,
                        created_at=datetime(2024, 6, 15, 10, 30),
                    )
                ]
            )
            mock_nm_cls.return_value = mock_nm

            result = runner.invoke(app, ["notebooks", "list", "--detailed"])

            assert result.exit_code == 0
            assert "nb_detailed_456" in result.output
            assert "Detailed View Test" in result.output
            assert "2024-06-15" in result.output

    def test_list_notebooks_detailed_view_no_created_at(self) -> None:
        """List command with --detailed handles missing created_at."""
        from pynotebooklm.models import Notebook

        with (
            patch("pynotebooklm.cli.AuthManager") as mock_auth_cls,
            patch("pynotebooklm.cli.BrowserSession") as mock_session_cls,
            patch("pynotebooklm.cli.NotebookManager") as mock_nm_cls,
        ):
            mock_auth = MagicMock()
            mock_auth.is_authenticated.return_value = True
            mock_auth_cls.return_value = mock_auth

            mock_session = MagicMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            mock_session_cls.return_value = mock_session

            mock_nm = MagicMock()
            mock_nm.list = AsyncMock(
                return_value=[
                    Notebook(
                        id="nb_no_date",
                        name="No Date Notebook",
                        source_count=0,
                        created_at=None,
                    )
                ]
            )
            mock_nm_cls.return_value = mock_nm

            result = runner.invoke(app, ["notebooks", "list", "--detailed"])

            assert result.exit_code == 0
            assert "Unknown" in result.output


class TestNotebookDescribeCommand:
    """Tests for the 'notebooks describe' CLI command."""

    def test_describe_notebook_not_authenticated(self) -> None:
        """Describe notebook exits when not authenticated."""
        with patch("pynotebooklm.cli.AuthManager") as mock_auth_cls:
            mock_auth = MagicMock()
            mock_auth.is_authenticated.return_value = False
            mock_auth_cls.return_value = mock_auth

            result = runner.invoke(app, ["notebooks", "describe", "nb_123"])

            assert result.exit_code == 1
            assert "Not authenticated" in result.output

    def test_describe_notebook_success(self) -> None:
        """Describe notebook shows summary and topics."""
        with (
            patch("pynotebooklm.cli.AuthManager") as mock_auth_cls,
            patch("pynotebooklm.cli.BrowserSession") as mock_session_cls,
        ):
            mock_auth = MagicMock()
            mock_auth.is_authenticated.return_value = True
            mock_auth_cls.return_value = mock_auth

            mock_session = MagicMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            mock_session_cls.return_value = mock_session

            # Mock the API response
            mock_api_instance = MagicMock()
            mock_api_instance.get_notebook_summary = AsyncMock(
                return_value=[
                    [
                        None,
                        None,
                        "This is the notebook summary.",
                        [
                            ["Topic 1"],
                            ["Topic 2"],
                        ],
                    ]
                ]
            )

            with patch(
                "pynotebooklm.api.NotebookLMAPI", return_value=mock_api_instance
            ):
                result = runner.invoke(app, ["notebooks", "describe", "nb_123"])

            assert result.exit_code == 0
            assert "Summary for Notebook nb_123" in result.output
            assert "This is the notebook summary." in result.output
            assert "Topic 1" in result.output
            assert "Topic 2" in result.output

    def test_describe_notebook_no_result(self) -> None:
        """Describe notebook handles no result."""
        with (
            patch("pynotebooklm.cli.AuthManager") as mock_auth_cls,
            patch("pynotebooklm.cli.BrowserSession") as mock_session_cls,
        ):
            mock_auth = MagicMock()
            mock_auth.is_authenticated.return_value = True
            mock_auth_cls.return_value = mock_auth

            mock_session = MagicMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            mock_session_cls.return_value = mock_session

            mock_api_instance = MagicMock()
            mock_api_instance.get_notebook_summary = AsyncMock(return_value=None)

            with patch(
                "pynotebooklm.api.NotebookLMAPI", return_value=mock_api_instance
            ):
                result = runner.invoke(app, ["notebooks", "describe", "nb_123"])

            assert result.exit_code == 1
            assert "Failed to get notebook description" in result.output


class TestNotebookCreateCommand:
    """Tests for the 'notebooks create' CLI command."""

    def test_create_notebook_success(self) -> None:
        """Create command succeeds."""
        from pynotebooklm.models import Notebook

        with (
            patch("pynotebooklm.cli.AuthManager") as mock_auth_cls,
            patch("pynotebooklm.cli.BrowserSession") as mock_session_cls,
            patch("pynotebooklm.cli.NotebookManager") as mock_nm_cls,
        ):
            mock_auth = MagicMock()
            mock_auth_cls.return_value = mock_auth

            mock_session = MagicMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            mock_session_cls.return_value = mock_session

            mock_nm = MagicMock()
            mock_nm.create = AsyncMock(
                return_value=Notebook(id="new_nb", name="My New Notebook")
            )
            mock_nm_cls.return_value = mock_nm

            result = runner.invoke(app, ["notebooks", "create", "My New Notebook"])

            assert result.exit_code == 0
            assert "Created notebook" in result.output
            assert "My New Notebook" in result.output


class TestNotebookDeleteCommand:
    """Tests for the 'notebooks delete' CLI command."""

    def test_delete_notebook_with_force(self) -> None:
        """Delete command works with --force flag."""
        with (
            patch("pynotebooklm.cli.AuthManager") as mock_auth_cls,
            patch("pynotebooklm.cli.BrowserSession") as mock_session_cls,
            patch("pynotebooklm.cli.NotebookManager") as mock_nm_cls,
        ):
            mock_auth = MagicMock()
            mock_auth_cls.return_value = mock_auth

            mock_session = MagicMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            mock_session_cls.return_value = mock_session

            mock_nm = MagicMock()
            mock_nm.delete = AsyncMock(return_value=True)
            mock_nm_cls.return_value = mock_nm

            result = runner.invoke(app, ["notebooks", "delete", "nb_123", "--force"])

            assert result.exit_code == 0
            assert "Deleted notebook" in result.output


class TestNotebookGetCommand:
    """Tests for the 'notebooks get' CLI command."""

    def test_get_notebook_not_authenticated(self) -> None:
        """Get notebook exits when not authenticated."""
        with patch("pynotebooklm.cli.AuthManager") as mock_auth_cls:
            mock_auth = MagicMock()
            mock_auth.is_authenticated.return_value = False
            mock_auth_cls.return_value = mock_auth

            result = runner.invoke(app, ["notebooks", "get", "nb_123"])

            assert result.exit_code == 1
            assert "Not authenticated" in result.output

    def test_get_notebook_success(self) -> None:
        """Get notebook shows detailed information."""
        from pynotebooklm.models import Notebook, Source, SourceStatus, SourceType

        with (
            patch("pynotebooklm.cli.AuthManager") as mock_auth_cls,
            patch("pynotebooklm.cli.BrowserSession") as mock_session_cls,
            patch("pynotebooklm.cli.NotebookManager") as mock_nm_cls,
        ):
            mock_auth = MagicMock()
            mock_auth.is_authenticated.return_value = True
            mock_auth_cls.return_value = mock_auth

            mock_session = MagicMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            mock_session_cls.return_value = mock_session

            mock_nm = MagicMock()
            mock_nm.get = AsyncMock(
                return_value=Notebook(
                    id="nb_123",
                    name="Test Notebook",
                    source_count=2,
                    created_at=datetime(2024, 1, 1, 12, 0),
                    updated_at=datetime(2024, 1, 15, 14, 30),
                    sources=[
                        Source(
                            id="src_1",
                            title="Web Source",
                            type=SourceType.URL,
                            status=SourceStatus.READY,
                            source_type_code=5,
                        ),
                        Source(
                            id="src_2",
                            title="Doc Source",
                            type=SourceType.DRIVE,
                            status=SourceStatus.READY,
                            source_type_code=1,
                            is_fresh=True,
                        ),
                    ],
                )
            )
            mock_nm_cls.return_value = mock_nm

            result = runner.invoke(app, ["notebooks", "get", "nb_123"])

            assert result.exit_code == 0
            assert "Test Notebook" in result.output
            assert "nb_123" in result.output
            assert "Web Source" in result.output
            assert "Doc Source" in result.output

    def test_get_notebook_no_sources(self) -> None:
        """Get notebook handles notebook with no sources."""
        from pynotebooklm.models import Notebook

        with (
            patch("pynotebooklm.cli.AuthManager") as mock_auth_cls,
            patch("pynotebooklm.cli.BrowserSession") as mock_session_cls,
            patch("pynotebooklm.cli.NotebookManager") as mock_nm_cls,
        ):
            mock_auth = MagicMock()
            mock_auth.is_authenticated.return_value = True
            mock_auth_cls.return_value = mock_auth

            mock_session = MagicMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            mock_session_cls.return_value = mock_session

            mock_nm = MagicMock()
            mock_nm.get = AsyncMock(
                return_value=Notebook(
                    id="nb_empty",
                    name="Empty Notebook",
                    source_count=0,
                    sources=[],
                )
            )
            mock_nm_cls.return_value = mock_nm

            result = runner.invoke(app, ["notebooks", "get", "nb_empty"])

            assert result.exit_code == 0
            assert "Empty Notebook" in result.output
            assert "No sources" in result.output


class TestNotebookRenameCommand:
    """Tests for the 'notebooks rename' CLI command."""

    def test_rename_notebook_not_authenticated(self) -> None:
        """Rename notebook exits when not authenticated."""
        with patch("pynotebooklm.cli.AuthManager") as mock_auth_cls:
            mock_auth = MagicMock()
            mock_auth.is_authenticated.return_value = False
            mock_auth_cls.return_value = mock_auth

            result = runner.invoke(app, ["notebooks", "rename", "nb_123", "New Name"])

            assert result.exit_code == 1
            assert "Not authenticated" in result.output

    def test_rename_notebook_with_force(self) -> None:
        """Rename notebook works with --force flag."""
        from pynotebooklm.models import Notebook

        with (
            patch("pynotebooklm.cli.AuthManager") as mock_auth_cls,
            patch("pynotebooklm.cli.BrowserSession") as mock_session_cls,
            patch("pynotebooklm.cli.NotebookManager") as mock_nm_cls,
        ):
            mock_auth = MagicMock()
            mock_auth.is_authenticated.return_value = True
            mock_auth_cls.return_value = mock_auth

            mock_session = MagicMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            mock_session_cls.return_value = mock_session

            mock_nm = MagicMock()
            mock_nm.get = AsyncMock(return_value=Notebook(id="nb_123", name="Old Name"))
            mock_nm.rename = AsyncMock(
                return_value=Notebook(id="nb_123", name="New Name")
            )
            mock_nm_cls.return_value = mock_nm

            result = runner.invoke(
                app, ["notebooks", "rename", "nb_123", "New Name", "--force"]
            )

            assert result.exit_code == 0
            assert "Renamed notebook" in result.output
            assert "Old Name" in result.output
            assert "New Name" in result.output

    def test_rename_notebook_abort_without_force(self) -> None:
        """Rename notebook aborts when user declines confirmation."""
        from pynotebooklm.models import Notebook

        with (
            patch("pynotebooklm.cli.AuthManager") as mock_auth_cls,
            patch("pynotebooklm.cli.BrowserSession") as mock_session_cls,
            patch("pynotebooklm.cli.NotebookManager") as mock_nm_cls,
        ):
            mock_auth = MagicMock()
            mock_auth.is_authenticated.return_value = True
            mock_auth_cls.return_value = mock_auth

            mock_session = MagicMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            mock_session_cls.return_value = mock_session

            mock_nm = MagicMock()
            mock_nm.get = AsyncMock(return_value=Notebook(id="nb_123", name="Old Name"))
            mock_nm_cls.return_value = mock_nm

            # Simulate user typing 'n' to decline
            result = runner.invoke(
                app, ["notebooks", "rename", "nb_123", "New Name"], input="n\n"
            )

            assert result.exit_code == 0
            assert "Aborted" in result.output


# =============================================================================
# Source Command Tests
# =============================================================================


class TestSourceAddCommand:
    """Tests for the 'sources add' CLI command."""

    def test_add_source_success(self) -> None:
        """Add source command succeeds."""
        from pynotebooklm.models import Source, SourceType

        with (
            patch("pynotebooklm.cli.AuthManager") as mock_auth_cls,
            patch("pynotebooklm.cli.BrowserSession") as mock_session_cls,
            patch("pynotebooklm.cli.SourceManager") as mock_sm_cls,
        ):
            mock_auth = MagicMock()
            mock_auth_cls.return_value = mock_auth

            mock_session = MagicMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            mock_session_cls.return_value = mock_session

            mock_sm = MagicMock()
            mock_sm.add_url = AsyncMock(
                return_value=Source(id="src_123", title="Example", type=SourceType.URL)
            )
            mock_sm_cls.return_value = mock_sm

            result = runner.invoke(
                app, ["sources", "add", "nb_123", "https://example.com"]
            )

            assert result.exit_code == 0
            assert "Added source" in result.output


class TestSourceListCommand:
    """Tests for the 'sources list' CLI command."""

    def test_list_sources_success(self) -> None:
        """List sources command shows table."""
        from pynotebooklm.models import Source, SourceType

        with (
            patch("pynotebooklm.cli.AuthManager") as mock_auth_cls,
            patch("pynotebooklm.cli.BrowserSession") as mock_session_cls,
            patch("pynotebooklm.cli.SourceManager") as mock_sm_cls,
        ):
            mock_auth = MagicMock()
            mock_auth_cls.return_value = mock_auth

            mock_session = MagicMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            mock_session_cls.return_value = mock_session

            mock_sm = MagicMock()
            mock_sm.list_sources = AsyncMock(
                return_value=[
                    Source(id="src_123", title="Test Source", type=SourceType.URL)
                ]
            )
            mock_sm_cls.return_value = mock_sm

            result = runner.invoke(app, ["sources", "list", "nb_123"])

            assert result.exit_code == 0
            assert "Test Source" in result.output

    def test_list_sources_empty(self) -> None:
        """List sources handles empty list."""
        with (
            patch("pynotebooklm.cli.AuthManager") as mock_auth_cls,
            patch("pynotebooklm.cli.BrowserSession") as mock_session_cls,
            patch("pynotebooklm.cli.SourceManager") as mock_sm_cls,
        ):
            mock_auth = MagicMock()
            mock_auth_cls.return_value = mock_auth

            mock_session = MagicMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            mock_session_cls.return_value = mock_session

            mock_sm = MagicMock()
            mock_sm.list_sources = AsyncMock(return_value=[])
            mock_sm_cls.return_value = mock_sm

            result = runner.invoke(app, ["sources", "list", "nb_123"])

            assert result.exit_code == 0
            assert "No sources found" in result.output

    def test_list_sources_with_freshness_check(self) -> None:
        """List sources with --check-freshness shows freshness column."""
        from pynotebooklm.models import Source, SourceType

        with (
            patch("pynotebooklm.cli.AuthManager") as mock_auth_cls,
            patch("pynotebooklm.cli.BrowserSession") as mock_session_cls,
            patch("pynotebooklm.cli.SourceManager") as mock_sm_cls,
        ):
            mock_auth = MagicMock()
            mock_auth_cls.return_value = mock_auth

            mock_session = MagicMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            mock_session_cls.return_value = mock_session

            mock_sm = MagicMock()
            mock_sm.list_sources = AsyncMock(
                return_value=[
                    Source(
                        id="src_123",
                        title="Fresh Drive",
                        type=SourceType.DRIVE,
                        is_fresh=True,
                    ),
                    Source(
                        id="src_456",
                        title="Stale Drive",
                        type=SourceType.DRIVE,
                        is_fresh=False,
                    ),
                ]
            )
            mock_sm_cls.return_value = mock_sm

            result = runner.invoke(
                app, ["sources", "list", "nb_123", "--check-freshness"]
            )

            assert result.exit_code == 0
            assert "Fresh" in result.output
            assert "stale" in result.output
            # Should call list_sources with check_freshness=True
            mock_sm.list_sources.assert_called_once_with("nb_123", check_freshness=True)

    def test_list_sources_freshness_shows_stale_hint(self) -> None:
        """List sources with stale sources shows sync hint."""
        from pynotebooklm.models import Source, SourceType

        with (
            patch("pynotebooklm.cli.AuthManager") as mock_auth_cls,
            patch("pynotebooklm.cli.BrowserSession") as mock_session_cls,
            patch("pynotebooklm.cli.SourceManager") as mock_sm_cls,
        ):
            mock_auth = MagicMock()
            mock_auth_cls.return_value = mock_auth

            mock_session = MagicMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            mock_session_cls.return_value = mock_session

            mock_sm = MagicMock()
            mock_sm.list_sources = AsyncMock(
                return_value=[
                    Source(
                        id="src_stale",
                        title="Stale Drive",
                        type=SourceType.DRIVE,
                        is_fresh=False,
                    ),
                ]
            )
            mock_sm_cls.return_value = mock_sm

            result = runner.invoke(
                app, ["sources", "list", "nb_123", "--check-freshness"]
            )

            assert result.exit_code == 0
            assert "stale Drive source" in result.output
            assert "pynotebooklm sources sync" in result.output

    def test_list_sources_without_freshness_flag(self) -> None:
        """List sources without --check-freshness does not check freshness."""
        from pynotebooklm.models import Source, SourceType

        with (
            patch("pynotebooklm.cli.AuthManager") as mock_auth_cls,
            patch("pynotebooklm.cli.BrowserSession") as mock_session_cls,
            patch("pynotebooklm.cli.SourceManager") as mock_sm_cls,
        ):
            mock_auth = MagicMock()
            mock_auth_cls.return_value = mock_auth

            mock_session = MagicMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            mock_session_cls.return_value = mock_session

            mock_sm = MagicMock()
            mock_sm.list_sources = AsyncMock(
                return_value=[Source(id="src_123", title="Test", type=SourceType.DRIVE)]
            )
            mock_sm_cls.return_value = mock_sm

            result = runner.invoke(app, ["sources", "list", "nb_123"])

            assert result.exit_code == 0
            # Should call list_sources with check_freshness=False
            mock_sm.list_sources.assert_called_once_with(
                "nb_123", check_freshness=False
            )


class TestSourceDeleteCommand:
    """Tests for the 'sources delete' CLI command."""

    def test_delete_source_with_force(self) -> None:
        """Delete source works with --force."""
        with (
            patch("pynotebooklm.cli.AuthManager") as mock_auth_cls,
            patch("pynotebooklm.cli.BrowserSession") as mock_session_cls,
            patch("pynotebooklm.cli.SourceManager") as mock_sm_cls,
        ):
            mock_auth = MagicMock()
            mock_auth_cls.return_value = mock_auth

            mock_session = MagicMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            mock_session_cls.return_value = mock_session

            mock_sm = MagicMock()
            mock_sm.delete = AsyncMock(return_value=True)
            mock_sm_cls.return_value = mock_sm

            result = runner.invoke(
                app, ["sources", "delete", "nb_123", "src_456", "--force"]
            )

            assert result.exit_code == 0
            assert "Deleted source" in result.output


# =============================================================================
# Research Command Tests
# =============================================================================


class TestResearchStartCommand:
    """Tests for the 'research start' CLI command."""

    def test_start_research_not_authenticated(self) -> None:
        """Start research exits when not authenticated."""
        with patch("pynotebooklm.cli.AuthManager") as mock_auth_cls:
            mock_auth = MagicMock()
            mock_auth.is_authenticated.return_value = False
            mock_auth_cls.return_value = mock_auth

            result = runner.invoke(app, ["research", "start", "nb_123", "AI trends"])

            assert result.exit_code == 1
            assert "Not authenticated" in result.output

    def test_start_research_success(self) -> None:
        """Start research command succeeds."""
        from pynotebooklm.research import ResearchSession, ResearchStatus

        with (
            patch("pynotebooklm.cli.AuthManager") as mock_auth_cls,
            patch("pynotebooklm.cli.BrowserSession") as mock_session_cls,
            patch("pynotebooklm.cli.ResearchDiscovery") as mock_rd_cls,
        ):
            mock_auth = MagicMock()
            mock_auth.is_authenticated.return_value = True
            mock_auth_cls.return_value = mock_auth

            mock_session = MagicMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            mock_session_cls.return_value = mock_session

            mock_rd = MagicMock()
            mock_rd.start_research = AsyncMock(
                return_value=ResearchSession(
                    task_id="task_123",
                    notebook_id="nb_123",
                    query="AI trends",
                    mode="fast",
                    source="web",
                    status=ResearchStatus.IN_PROGRESS,
                )
            )
            mock_rd_cls.return_value = mock_rd

            result = runner.invoke(app, ["research", "start", "nb_123", "AI trends"])

            assert result.exit_code == 0
            assert "Started research" in result.output
            assert "task_123" in result.output


class TestResearchPollCommand:
    """Tests for the 'research poll' CLI command."""

    def test_poll_research_not_authenticated(self) -> None:
        """Poll research exits when not authenticated."""
        with patch("pynotebooklm.cli.AuthManager") as mock_auth_cls:
            mock_auth = MagicMock()
            mock_auth.is_authenticated.return_value = False
            mock_auth_cls.return_value = mock_auth

            result = runner.invoke(app, ["research", "poll", "nb_123"])

            assert result.exit_code == 1
            assert "Not authenticated" in result.output

    def test_poll_research_no_active_research(self) -> None:
        """Poll research handles no active research."""
        from pynotebooklm.research import ResearchSession, ResearchStatus

        with (
            patch("pynotebooklm.cli.AuthManager") as mock_auth_cls,
            patch("pynotebooklm.cli.BrowserSession") as mock_session_cls,
            patch("pynotebooklm.cli.ResearchDiscovery") as mock_rd_cls,
        ):
            mock_auth = MagicMock()
            mock_auth.is_authenticated.return_value = True
            mock_auth_cls.return_value = mock_auth

            mock_session = MagicMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            mock_session_cls.return_value = mock_session

            mock_rd = MagicMock()
            mock_rd.poll_research = AsyncMock(
                return_value=ResearchSession(
                    task_id="",
                    notebook_id="nb_123",
                    query="",
                    status=ResearchStatus.NO_RESEARCH,
                )
            )
            mock_rd_cls.return_value = mock_rd

            result = runner.invoke(app, ["research", "poll", "nb_123"])

            assert result.exit_code == 0
            assert "No active research" in result.output

    def test_poll_research_with_results(self) -> None:
        """Poll research shows results table."""
        from pynotebooklm.research import (
            ResearchResult,
            ResearchSession,
            ResearchStatus,
        )

        with (
            patch("pynotebooklm.cli.AuthManager") as mock_auth_cls,
            patch("pynotebooklm.cli.BrowserSession") as mock_session_cls,
            patch("pynotebooklm.cli.ResearchDiscovery") as mock_rd_cls,
        ):
            mock_auth = MagicMock()
            mock_auth.is_authenticated.return_value = True
            mock_auth_cls.return_value = mock_auth

            mock_session = MagicMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            mock_session_cls.return_value = mock_session

            mock_rd = MagicMock()
            mock_rd.poll_research = AsyncMock(
                return_value=ResearchSession(
                    task_id="task_123",
                    notebook_id="nb_123",
                    query="AI trends",
                    mode="fast",
                    source="web",
                    status=ResearchStatus.COMPLETED,
                    source_count=2,
                    results=[
                        ResearchResult(
                            index=0,
                            title="AI Article",
                            url="https://example.com/ai",
                            result_type_name="web",
                        ),
                        ResearchResult(
                            index=1,
                            title="ML Article",
                            url="https://example.com/ml",
                            result_type_name="web",
                        ),
                    ],
                )
            )
            mock_rd_cls.return_value = mock_rd

            result = runner.invoke(app, ["research", "poll", "nb_123"])

            assert result.exit_code == 0
            assert "AI Article" in result.output
            assert "completed" in result.output

    def test_poll_research_in_progress(self) -> None:
        """Poll research shows in_progress status."""
        from pynotebooklm.research import ResearchSession, ResearchStatus

        with (
            patch("pynotebooklm.cli.AuthManager") as mock_auth_cls,
            patch("pynotebooklm.cli.BrowserSession") as mock_session_cls,
            patch("pynotebooklm.cli.ResearchDiscovery") as mock_rd_cls,
        ):
            mock_auth = MagicMock()
            mock_auth.is_authenticated.return_value = True
            mock_auth_cls.return_value = mock_auth

            mock_session = MagicMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_cls.return_value = mock_session

            mock_rd = MagicMock()
            mock_rd.poll_research = AsyncMock(
                return_value=ResearchSession(
                    task_id="t1",
                    notebook_id="nb1",
                    query="q",
                    status=ResearchStatus.IN_PROGRESS,
                )
            )
            mock_rd_cls.return_value = mock_rd

            result = runner.invoke(app, ["research", "poll", "nb_123"])
            assert "in_progress" in result.output


class TestStudioCommand:
    """Tests for studio commands."""

    def test_studio_list_success(self) -> None:
        """Studio list command shows artifacts."""
        with (
            patch("pynotebooklm.cli.AuthManager") as mock_auth_cls,
            patch("pynotebooklm.cli.BrowserSession") as mock_session_cls,
            patch("pynotebooklm.cli.ChatSession") as mock_chat_cls,
        ):
            mock_auth = MagicMock()
            mock_auth.is_authenticated.return_value = True
            mock_auth_cls.return_value = mock_auth

            mock_session = MagicMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_cls.return_value = mock_session

            mock_chat = MagicMock()
            mock_chat.list_artifacts = AsyncMock(
                return_value=[
                    {
                        "id": "a1",
                        "title": "Art 1",
                        "type": "Report",
                        "status": "completed",
                    }
                ]
            )
            mock_chat_cls.return_value = mock_chat

            result = runner.invoke(app, ["studio", "list", "nb_123"])

            assert result.exit_code == 0
            assert "Art 1" in result.output
            assert "Report" in result.output

    def test_studio_list_empty(self) -> None:
        """Studio list handles empty response."""
        with (
            patch("pynotebooklm.cli.AuthManager") as mock_auth_cls,
            patch("pynotebooklm.cli.BrowserSession") as mock_session_cls,
            patch("pynotebooklm.cli.ChatSession") as mock_chat_cls,
        ):
            mock_auth = MagicMock()
            mock_auth.is_authenticated.return_value = True
            mock_auth_cls.return_value = mock_auth

            mock_session = MagicMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_cls.return_value = mock_session

            mock_chat = MagicMock()
            mock_chat.list_artifacts = AsyncMock(return_value=[])
            mock_chat_cls.return_value = mock_chat

            result = runner.invoke(app, ["studio", "list", "nb_123"])

            assert result.exit_code == 0
            assert "No studio artifacts found" in result.output
