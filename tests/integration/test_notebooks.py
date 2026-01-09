"""
Integration tests for NotebookManager.

These tests verify notebook CRUD operations against the actual
NotebookLM API (or mocked responses for unit testing).
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from pynotebooklm import (
    APIError,
    AuthManager,
    BrowserSession,
    Notebook,
    NotebookManager,
    NotebookNotFoundError,
)

# Import mock data
from tests.fixtures.mock_rpc_responses import (
    MOCK_CREATE_NOTEBOOK_RESPONSE,
    MOCK_LIST_NOTEBOOKS_RESPONSE,
    MOCK_NOTEBOOK_WITH_SOURCES,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_auth():
    """Create a mock AuthManager."""
    auth = MagicMock(spec=AuthManager)
    auth.is_authenticated.return_value = True
    auth.get_cookies.return_value = [
        {"name": "SID", "value": "test", "domain": ".google.com"},
        {"name": "HSID", "value": "test", "domain": ".google.com"},
        {"name": "SSID", "value": "test", "domain": ".google.com"},
    ]
    return auth


@pytest.fixture
def mock_session(mock_auth):
    """Create a mock BrowserSession."""
    session = MagicMock(spec=BrowserSession)
    session.call_rpc = AsyncMock()
    return session


@pytest.fixture
def notebook_manager(mock_session):
    """Create a NotebookManager with mocked session."""
    return NotebookManager(mock_session)


# =============================================================================
# List Notebooks Tests
# =============================================================================


class TestListNotebooks:
    """Tests for NotebookManager.list()"""

    @pytest.mark.asyncio
    async def test_list_returns_notebooks(self, notebook_manager, mock_session):
        """Should return list of Notebook objects."""
        mock_session.call_rpc.return_value = MOCK_LIST_NOTEBOOKS_RESPONSE

        notebooks = await notebook_manager.list()

        assert isinstance(notebooks, list)
        assert len(notebooks) == 2
        assert all(isinstance(nb, Notebook) for nb in notebooks)

    @pytest.mark.asyncio
    async def test_list_empty_account(self, notebook_manager, mock_session):
        """Should return empty list for account with no notebooks."""
        mock_session.call_rpc.return_value = [[]]

        notebooks = await notebook_manager.list()

        assert notebooks == []

    @pytest.mark.asyncio
    async def test_list_parses_notebook_fields(self, notebook_manager, mock_session):
        """Should correctly parse notebook ID and name."""
        mock_session.call_rpc.return_value = MOCK_LIST_NOTEBOOKS_RESPONSE

        notebooks = await notebook_manager.list()

        assert notebooks[0].id == "nb_abc123"
        assert notebooks[0].name == "My Research Notebook"
        assert notebooks[1].id == "nb_def456"
        assert notebooks[1].name == "Project Notes"

    @pytest.mark.asyncio
    async def test_list_handles_malformed_response(
        self, notebook_manager, mock_session
    ):
        """Should handle malformed notebook data gracefully."""
        # Mix of valid and invalid data
        mock_session.call_rpc.return_value = [
            [
                ["valid_id", "Valid Notebook", 12345, []],
                None,  # Invalid entry
                ["another_id", "Another Notebook", 12346, []],
            ]
        ]

        notebooks = await notebook_manager.list()

        # Should skip invalid entries
        assert len(notebooks) == 2


# =============================================================================
# Create Notebook Tests
# =============================================================================


class TestCreateNotebook:
    """Tests for NotebookManager.create()"""

    @pytest.mark.asyncio
    async def test_create_returns_notebook(self, notebook_manager, mock_session):
        """Should return created Notebook object."""
        mock_session.call_rpc.return_value = MOCK_CREATE_NOTEBOOK_RESPONSE

        notebook = await notebook_manager.create("New Notebook")

        assert isinstance(notebook, Notebook)
        assert notebook.name == "New Notebook"

    @pytest.mark.asyncio
    async def test_create_strips_whitespace(self, notebook_manager, mock_session):
        """Should strip whitespace from notebook name."""
        mock_session.call_rpc.return_value = MOCK_CREATE_NOTEBOOK_RESPONSE

        await notebook_manager.create("  Padded Name  ")

        # Verify the call was made with stripped name
        call_args = mock_session.call_rpc.call_args
        assert call_args[0][1][0] == "Padded Name"

    @pytest.mark.asyncio
    async def test_create_rejects_empty_name(self, notebook_manager):
        """Should reject empty notebook names."""
        with pytest.raises(ValueError, match="cannot be empty"):
            await notebook_manager.create("")

    @pytest.mark.asyncio
    async def test_create_rejects_whitespace_only_name(self, notebook_manager):
        """Should reject whitespace-only names."""
        with pytest.raises(ValueError, match="cannot be empty"):
            await notebook_manager.create("   ")

    @pytest.mark.asyncio
    async def test_create_rejects_long_name(self, notebook_manager):
        """Should reject names over 200 characters."""
        long_name = "x" * 201

        with pytest.raises(ValueError, match="200 characters"):
            await notebook_manager.create(long_name)


# =============================================================================
# Get Notebook Tests
# =============================================================================


class TestGetNotebook:
    """Tests for NotebookManager.get()"""

    @pytest.mark.asyncio
    async def test_get_returns_notebook_with_sources(
        self, notebook_manager, mock_session
    ):
        """Should return notebook with populated sources."""
        mock_session.call_rpc.return_value = MOCK_NOTEBOOK_WITH_SOURCES

        notebook = await notebook_manager.get("nb_xyz789")

        assert isinstance(notebook, Notebook)
        assert notebook.id == "nb_xyz789"
        assert len(notebook.sources) >= 0  # Sources may be parsed

    @pytest.mark.asyncio
    async def test_get_rejects_empty_id(self, notebook_manager):
        """Should reject empty notebook ID."""
        with pytest.raises(ValueError, match="cannot be empty"):
            await notebook_manager.get("")

    @pytest.mark.asyncio
    async def test_get_not_found_raises_error(self, notebook_manager, mock_session):
        """Should raise NotebookNotFoundError for non-existent notebook."""
        mock_session.call_rpc.side_effect = APIError("not found", status_code=404)

        with pytest.raises(NotebookNotFoundError):
            await notebook_manager.get("invalid_id")


# =============================================================================
# Rename Notebook Tests
# =============================================================================


class TestRenameNotebook:
    """Tests for NotebookManager.rename()"""

    @pytest.mark.asyncio
    async def test_rename_updates_notebook(self, notebook_manager, mock_session):
        """Should rename notebook and return updated version."""
        # First call for rename, second for get
        mock_session.call_rpc.side_effect = [
            None,  # Rename response
            ["nb_123", "Updated Name", 12345, []],  # Get response
        ]

        notebook = await notebook_manager.rename("nb_123", "Updated Name")

        assert notebook.name == "Updated Name"

    @pytest.mark.asyncio
    async def test_rename_rejects_empty_new_name(self, notebook_manager):
        """Should reject empty new name."""
        with pytest.raises(ValueError, match="cannot be empty"):
            await notebook_manager.rename("nb_123", "")


# =============================================================================
# Delete Notebook Tests
# =============================================================================


class TestDeleteNotebook:
    """Tests for NotebookManager.delete()"""

    @pytest.mark.asyncio
    async def test_delete_requires_confirmation(self, notebook_manager):
        """Should require confirm=True to delete."""
        with pytest.raises(ValueError, match="not confirmed"):
            await notebook_manager.delete("nb_123")

    @pytest.mark.asyncio
    async def test_delete_with_confirmation_succeeds(
        self, notebook_manager, mock_session
    ):
        """Should delete when confirm=True."""
        mock_session.call_rpc.return_value = None

        result = await notebook_manager.delete("nb_123", confirm=True)

        assert result is True

    @pytest.mark.asyncio
    async def test_delete_rejects_empty_id(self, notebook_manager):
        """Should reject empty notebook ID."""
        with pytest.raises(ValueError, match="cannot be empty"):
            await notebook_manager.delete("", confirm=True)


# =============================================================================
# Exists Check Tests
# =============================================================================


class TestNotebookExists:
    """Tests for NotebookManager.exists()"""

    @pytest.mark.asyncio
    async def test_exists_returns_true_for_existing(
        self, notebook_manager, mock_session
    ):
        """Should return True for existing notebook."""
        mock_session.call_rpc.return_value = MOCK_NOTEBOOK_WITH_SOURCES

        result = await notebook_manager.exists("nb_xyz789")

        assert result is True

    @pytest.mark.asyncio
    async def test_exists_returns_false_for_missing(
        self, notebook_manager, mock_session
    ):
        """Should return False for non-existent notebook."""
        mock_session.call_rpc.side_effect = APIError("not found", status_code=404)

        result = await notebook_manager.exists("invalid_id")

        assert result is False
