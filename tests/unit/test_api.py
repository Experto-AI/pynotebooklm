"""
Unit tests for the NotebookLMAPI class and response parsing utilities.

These tests verify API wrapper functionality, RPC call handling,
and response parsing without requiring actual browser automation.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from pynotebooklm.api import (
    NotebookLMAPI,
    parse_notebook_response,
    parse_source_response,
)
from pynotebooklm.exceptions import APIError, NotebookNotFoundError, SourceError
from pynotebooklm.models import SourceStatus, SourceType

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_session() -> MagicMock:
    """Create a mock BrowserSession."""
    session = MagicMock()
    session.call_rpc = AsyncMock()
    return session


@pytest.fixture
def api(mock_session: MagicMock) -> NotebookLMAPI:
    """Create a NotebookLMAPI with mock session."""
    return NotebookLMAPI(mock_session)


# =============================================================================
# API Initialization Tests
# =============================================================================


class TestAPIInit:
    """Tests for NotebookLMAPI initialization."""

    def test_init_stores_session(self, mock_session: MagicMock) -> None:
        """API stores the session reference."""
        api = NotebookLMAPI(mock_session)
        assert api._session is mock_session


# =============================================================================
# Notebook Operation Tests
# =============================================================================


class TestListNotebooks:
    """Tests for list_notebooks method."""

    @pytest.mark.asyncio
    async def test_list_notebooks_returns_list(
        self, api: NotebookLMAPI, mock_session: MagicMock
    ) -> None:
        """list_notebooks returns list of notebooks."""
        mock_session.call_rpc.return_value = [
            [
                ["nb1", "Notebook 1", 1234567890],
                ["nb2", "Notebook 2", 1234567891],
            ]
        ]

        result = await api.list_notebooks()

        assert len(result) == 2
        mock_session.call_rpc.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_notebooks_empty(
        self, api: NotebookLMAPI, mock_session: MagicMock
    ) -> None:
        """list_notebooks returns empty list when no notebooks."""
        mock_session.call_rpc.return_value = [[]]

        result = await api.list_notebooks()

        assert result == []

    @pytest.mark.asyncio
    async def test_list_notebooks_handles_non_list(
        self, api: NotebookLMAPI, mock_session: MagicMock
    ) -> None:
        """list_notebooks handles non-list response."""
        mock_session.call_rpc.return_value = None

        result = await api.list_notebooks()

        assert result == []


class TestCreateNotebook:
    """Tests for create_notebook method."""

    @pytest.mark.asyncio
    async def test_create_notebook_success(
        self, api: NotebookLMAPI, mock_session: MagicMock
    ) -> None:
        """create_notebook calls RPC with correct params."""
        mock_session.call_rpc.return_value = ["nb123", "Test Notebook"]

        result = await api.create_notebook("Test Notebook")

        assert result == ["nb123", "Test Notebook"]
        mock_session.call_rpc.assert_called_once_with(
            "CCqFvf", ["Test Notebook", None, None, [2], []]
        )


class TestGetNotebook:
    """Tests for get_notebook method."""

    @pytest.mark.asyncio
    async def test_get_notebook_success(
        self, api: NotebookLMAPI, mock_session: MagicMock
    ) -> None:
        """get_notebook returns notebook data."""
        mock_session.call_rpc.return_value = ["nb123", "Test", 12345, []]

        result = await api.get_notebook("nb123")

        assert result[0] == "nb123"

    @pytest.mark.asyncio
    async def test_get_notebook_not_found(
        self, api: NotebookLMAPI, mock_session: MagicMock
    ) -> None:
        """get_notebook raises NotebookNotFoundError on 404."""
        mock_session.call_rpc.side_effect = APIError("Not found", status_code=404)

        with pytest.raises(NotebookNotFoundError):
            await api.get_notebook("nonexistent")

    @pytest.mark.asyncio
    async def test_get_notebook_not_found_message(
        self, api: NotebookLMAPI, mock_session: MagicMock
    ) -> None:
        """get_notebook raises NotebookNotFoundError on 'not found' message."""
        mock_session.call_rpc.side_effect = APIError("Notebook not found")

        with pytest.raises(NotebookNotFoundError):
            await api.get_notebook("nonexistent")


class TestRenameNotebook:
    """Tests for rename_notebook method."""

    @pytest.mark.asyncio
    async def test_rename_notebook_success(
        self, api: NotebookLMAPI, mock_session: MagicMock
    ) -> None:
        """rename_notebook calls RPC with correct params."""
        mock_session.call_rpc.return_value = {"success": True}

        await api.rename_notebook("nb123", "New Name")

        mock_session.call_rpc.assert_called_once_with(
            "cBavhb", ["nb123", "New Name", [2]]
        )

    @pytest.mark.asyncio
    async def test_rename_notebook_not_found(
        self, api: NotebookLMAPI, mock_session: MagicMock
    ) -> None:
        """rename_notebook raises NotebookNotFoundError."""
        mock_session.call_rpc.side_effect = APIError("not found")

        with pytest.raises(NotebookNotFoundError):
            await api.rename_notebook("nonexistent", "New Name")


class TestDeleteNotebook:
    """Tests for delete_notebook method."""

    @pytest.mark.asyncio
    async def test_delete_notebook_success(
        self, api: NotebookLMAPI, mock_session: MagicMock
    ) -> None:
        """delete_notebook returns True on success."""
        mock_session.call_rpc.return_value = {}

        result = await api.delete_notebook("nb123")

        assert result is True

    @pytest.mark.asyncio
    async def test_delete_notebook_not_found(
        self, api: NotebookLMAPI, mock_session: MagicMock
    ) -> None:
        """delete_notebook raises NotebookNotFoundError."""
        mock_session.call_rpc.side_effect = APIError("not found")

        with pytest.raises(NotebookNotFoundError):
            await api.delete_notebook("nonexistent")


# =============================================================================
# Source Operation Tests
# =============================================================================


class TestAddUrlSource:
    """Tests for add_url_source method."""

    @pytest.mark.asyncio
    async def test_add_url_source_success(
        self, api: NotebookLMAPI, mock_session: MagicMock
    ) -> None:
        """add_url_source returns source data."""
        mock_session.call_rpc.return_value = [
            "src123",
            "Example",
            1,
            "https://example.com",
        ]

        result = await api.add_url_source("nb123", "https://example.com")

        assert result[0] == "src123"

    @pytest.mark.asyncio
    async def test_add_url_source_notebook_not_found(
        self, api: NotebookLMAPI, mock_session: MagicMock
    ) -> None:
        """add_url_source raises NotebookNotFoundError."""
        mock_session.call_rpc.side_effect = APIError("not found")

        with pytest.raises(NotebookNotFoundError):
            await api.add_url_source("nonexistent", "https://example.com")

    @pytest.mark.asyncio
    async def test_add_url_source_invalid_url(
        self, api: NotebookLMAPI, mock_session: MagicMock
    ) -> None:
        """add_url_source raises SourceError on invalid URL."""
        mock_session.call_rpc.side_effect = APIError("invalid url format")

        with pytest.raises(SourceError):
            await api.add_url_source("nb123", "not-a-url")


class TestAddYoutubeSource:
    """Tests for add_youtube_source method."""

    @pytest.mark.asyncio
    async def test_add_youtube_source_success(
        self, api: NotebookLMAPI, mock_session: MagicMock
    ) -> None:
        """add_youtube_source returns source data."""
        mock_session.call_rpc.return_value = ["src123", "Video Title", 2]

        result = await api.add_youtube_source(
            "nb123", "https://youtube.com/watch?v=dQw4w9WgXcQ"
        )

        assert result[0] == "src123"

    @pytest.mark.asyncio
    async def test_add_youtube_source_invalid_url(
        self, api: NotebookLMAPI, mock_session: MagicMock
    ) -> None:
        """add_youtube_source raises SourceError on invalid URL."""
        with pytest.raises(SourceError) as exc_info:
            await api.add_youtube_source("nb123", "https://example.com")

        assert "Invalid YouTube URL" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_add_youtube_source_notebook_not_found(
        self, api: NotebookLMAPI, mock_session: MagicMock
    ) -> None:
        """add_youtube_source raises NotebookNotFoundError."""
        mock_session.call_rpc.side_effect = APIError("not found")

        with pytest.raises(NotebookNotFoundError):
            await api.add_youtube_source(
                "nonexistent", "https://youtube.com/watch?v=dQw4w9WgXcQ"
            )

    @pytest.mark.asyncio
    async def test_add_youtube_source_api_error(
        self, api: NotebookLMAPI, mock_session: MagicMock
    ) -> None:
        """add_youtube_source raises SourceError on API error."""
        mock_session.call_rpc.side_effect = APIError("Video unavailable")

        with pytest.raises(SourceError):
            await api.add_youtube_source(
                "nb123", "https://youtube.com/watch?v=dQw4w9WgXcQ"
            )


class TestAddTextSource:
    """Tests for add_text_source method."""

    @pytest.mark.asyncio
    async def test_add_text_source_success(
        self, api: NotebookLMAPI, mock_session: MagicMock
    ) -> None:
        """add_text_source returns source data."""
        mock_session.call_rpc.return_value = ["src123", "My Note"]

        result = await api.add_text_source("nb123", "Content here", "My Note")

        assert result[0] == "src123"
        mock_session.call_rpc.assert_called_once_with(
            "dqfPBf", ["nb123", "My Note", "Content here", [2]]
        )

    @pytest.mark.asyncio
    async def test_add_text_source_default_title(
        self, api: NotebookLMAPI, mock_session: MagicMock
    ) -> None:
        """add_text_source uses default title when not provided."""
        mock_session.call_rpc.return_value = ["src123", "Untitled Text"]

        await api.add_text_source("nb123", "Content here")

        mock_session.call_rpc.assert_called_once_with(
            "dqfPBf", ["nb123", "Untitled Text", "Content here", [2]]
        )

    @pytest.mark.asyncio
    async def test_add_text_source_notebook_not_found(
        self, api: NotebookLMAPI, mock_session: MagicMock
    ) -> None:
        """add_text_source raises NotebookNotFoundError."""
        mock_session.call_rpc.side_effect = APIError("not found")

        with pytest.raises(NotebookNotFoundError):
            await api.add_text_source("nonexistent", "Content")

    @pytest.mark.asyncio
    async def test_add_text_source_error(
        self, api: NotebookLMAPI, mock_session: MagicMock
    ) -> None:
        """add_text_source raises SourceError on failure."""
        mock_session.call_rpc.side_effect = APIError("Content too long")

        with pytest.raises(SourceError):
            await api.add_text_source("nb123", "Content")


class TestAddDriveSource:
    """Tests for add_drive_source method."""

    @pytest.mark.asyncio
    async def test_add_drive_source_success(
        self, api: NotebookLMAPI, mock_session: MagicMock
    ) -> None:
        """add_drive_source returns source data."""
        mock_session.call_rpc.return_value = ["src123", "Drive Doc", 3]

        result = await api.add_drive_source("nb123", "drive_doc_id")

        assert result[0] == "src123"

    @pytest.mark.asyncio
    async def test_add_drive_source_notebook_not_found(
        self, api: NotebookLMAPI, mock_session: MagicMock
    ) -> None:
        """add_drive_source raises NotebookNotFoundError."""
        mock_session.call_rpc.side_effect = APIError("not found")

        with pytest.raises(NotebookNotFoundError):
            await api.add_drive_source("nonexistent", "drive_id")

    @pytest.mark.asyncio
    async def test_add_drive_source_error(
        self, api: NotebookLMAPI, mock_session: MagicMock
    ) -> None:
        """add_drive_source raises SourceError on failure."""
        mock_session.call_rpc.side_effect = APIError("Permission denied")

        with pytest.raises(SourceError):
            await api.add_drive_source("nb123", "drive_id")


class TestDeleteSource:
    """Tests for delete_source method."""

    @pytest.mark.asyncio
    async def test_delete_source_success(
        self, api: NotebookLMAPI, mock_session: MagicMock
    ) -> None:
        """delete_source returns True on success."""
        mock_session.call_rpc.return_value = {}

        result = await api.delete_source("nb123", "src456")

        assert result is True

    @pytest.mark.asyncio
    async def test_delete_source_notebook_not_found(
        self, api: NotebookLMAPI, mock_session: MagicMock
    ) -> None:
        """delete_source raises NotebookNotFoundError for notebook."""
        mock_session.call_rpc.side_effect = APIError("notebook not found")

        with pytest.raises(NotebookNotFoundError):
            await api.delete_source("nonexistent", "src456")

    @pytest.mark.asyncio
    async def test_delete_source_source_not_found(
        self, api: NotebookLMAPI, mock_session: MagicMock
    ) -> None:
        """delete_source raises SourceError for source."""
        mock_session.call_rpc.side_effect = APIError("source not found")

        with pytest.raises(SourceError):
            await api.delete_source("nb123", "nonexistent")


class TestListDriveDocs:
    """Tests for list_drive_docs method."""

    @pytest.mark.asyncio
    async def test_list_drive_docs_success(
        self, api: NotebookLMAPI, mock_session: MagicMock
    ) -> None:
        """list_drive_docs returns list of documents."""
        mock_session.call_rpc.return_value = [
            ["doc1", "Document 1"],
            ["doc2", "Document 2"],
        ]

        result = await api.list_drive_docs()

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_list_drive_docs_empty(
        self, api: NotebookLMAPI, mock_session: MagicMock
    ) -> None:
        """list_drive_docs returns empty list."""
        mock_session.call_rpc.return_value = None

        result = await api.list_drive_docs()

        assert result == []


# =============================================================================
# YouTube ID Extraction Tests
# =============================================================================


class TestExtractYoutubeId:
    """Tests for _extract_youtube_id method."""

    def test_standard_watch_url(self, api: NotebookLMAPI) -> None:
        """Extracts ID from standard watch URL."""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        assert api._extract_youtube_id(url) == "dQw4w9WgXcQ"

    def test_short_url(self, api: NotebookLMAPI) -> None:
        """Extracts ID from short URL."""
        url = "https://youtu.be/dQw4w9WgXcQ"
        assert api._extract_youtube_id(url) == "dQw4w9WgXcQ"

    def test_embed_url(self, api: NotebookLMAPI) -> None:
        """Extracts ID from embed URL."""
        url = "https://www.youtube.com/embed/dQw4w9WgXcQ"
        assert api._extract_youtube_id(url) == "dQw4w9WgXcQ"

    def test_v_url(self, api: NotebookLMAPI) -> None:
        """Extracts ID from /v/ URL."""
        url = "https://www.youtube.com/v/dQw4w9WgXcQ"
        assert api._extract_youtube_id(url) == "dQw4w9WgXcQ"

    def test_invalid_url(self, api: NotebookLMAPI) -> None:
        """Returns None for non-YouTube URL."""
        url = "https://example.com/video"
        assert api._extract_youtube_id(url) is None

    def test_url_with_extra_params(self, api: NotebookLMAPI) -> None:
        """Extracts ID from URL with extra parameters."""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=120"
        assert api._extract_youtube_id(url) == "dQw4w9WgXcQ"


# =============================================================================
# Response Parsing Tests
# =============================================================================


class TestParseNotebookResponse:
    """Tests for parse_notebook_response function."""

    def test_parse_basic_notebook(self) -> None:
        """Parses basic notebook structure."""
        data = ["nb123", "Test Notebook", 1704067200000]

        notebook = parse_notebook_response(data)

        assert notebook.id == "nb123"
        assert notebook.name == "Test Notebook"
        assert notebook.created_at is not None

    def test_parse_notebook_with_sources(self) -> None:
        """Parses notebook with sources."""
        data = [
            "nb123",
            "Test Notebook",
            1704067200000,
            [
                ["src1", "Source 1", 1, "https://example.com", 1],
            ],
        ]

        notebook = parse_notebook_response(data)

        assert notebook.id == "nb123"
        assert len(notebook.sources) == 1

    def test_parse_notebook_missing_name(self) -> None:
        """Uses default name when missing."""
        data = ["nb123", None]

        notebook = parse_notebook_response(data)

        assert notebook.name == "Untitled"

    def test_parse_notebook_invalid_format(self) -> None:
        """Raises APIError on invalid format."""
        with pytest.raises(APIError):
            parse_notebook_response("not a list")

    def test_parse_notebook_too_short(self) -> None:
        """Raises APIError when data too short."""
        with pytest.raises(APIError):
            parse_notebook_response(["nb123"])

    def test_parse_notebook_seconds_timestamp(self) -> None:
        """Parses timestamp in seconds."""
        data = ["nb123", "Test", 1704067200]  # Seconds, not milliseconds

        notebook = parse_notebook_response(data)

        assert notebook.created_at is not None


class TestParseSourceResponse:
    """Tests for parse_source_response function."""

    def test_parse_url_source(self) -> None:
        """Parses URL source type."""
        data = ["src123", "Example Site", 1, "https://example.com", 1]

        source = parse_source_response(data)

        assert source.id == "src123"
        assert source.type == SourceType.URL
        assert source.url == "https://example.com"
        assert source.status == SourceStatus.READY

    def test_parse_youtube_source(self) -> None:
        """Parses YouTube source type."""
        data = ["src123", "Video Title", 2, "https://youtube.com/watch?v=abc", 1]

        source = parse_source_response(data)

        assert source.type == SourceType.YOUTUBE

    def test_parse_drive_source(self) -> None:
        """Parses Drive source type."""
        data = ["src123", "Doc Title", 3, "drive_id", 1]

        source = parse_source_response(data)

        assert source.type == SourceType.DRIVE

    def test_parse_text_source(self) -> None:
        """Parses text source type."""
        data = ["src123", "Note Title", 0]

        source = parse_source_response(data)

        assert source.type == SourceType.TEXT

    def test_parse_source_processing_status(self) -> None:
        """Parses processing status."""
        data = ["src123", "Title", 1, "url", 0]

        source = parse_source_response(data)

        assert source.status == SourceStatus.PROCESSING

    def test_parse_source_failed_status(self) -> None:
        """Parses failed status."""
        data = ["src123", "Title", 1, "url", 2]

        source = parse_source_response(data)

        assert source.status == SourceStatus.FAILED

    def test_parse_source_ready_string_status(self) -> None:
        """Parses 'ready' string status."""
        data = ["src123", "Title", 1, "url", "ready"]

        source = parse_source_response(data)

        assert source.status == SourceStatus.READY

    def test_parse_source_invalid_format(self) -> None:
        """Raises APIError on invalid format."""
        with pytest.raises(APIError):
            parse_source_response("not a list")

    def test_parse_source_too_short(self) -> None:
        """Raises APIError when data too short."""
        with pytest.raises(APIError):
            parse_source_response(["src123"])

    def test_parse_source_missing_title(self) -> None:
        """Uses default title when missing."""
        data = ["src123", None]

        source = parse_source_response(data)

        assert source.title == "Untitled"
