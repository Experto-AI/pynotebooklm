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
                ["Notebook 1", [], "nb1", 1234567890, None],
                ["Notebook 2", [], "nb2", 1234567891, None],
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
        mock_session.call_rpc.return_value = ["Test Notebook", [], "nb123"]

        result = await api.create_notebook("Test Notebook")

        assert result == ["Test Notebook", [], "nb123"]
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
        mock_session.call_rpc.return_value = ["Test", [], "nb123", 12345]

        result = await api.get_notebook("nb123")

        assert result[2] == "nb123"
        mock_session.call_rpc.assert_called_once_with(
            "rLM1Ne", ["nb123", None, [2], None, 0]
        )

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
        data = ["Test Notebook", [], "nb123", 1704067200000]

        notebook = parse_notebook_response(data)

        assert notebook.id == "nb123"
        assert notebook.name == "Test Notebook"
        assert notebook.created_at is not None

    def test_parse_notebook_with_sources(self) -> None:
        """Parses notebook with sources."""
        data = [
            "Test Notebook",
            [
                ["src1", "Source 1", 1, "https://example.com", 1],
            ],
            "nb123",
            1704067200000,
        ]

        notebook = parse_notebook_response(data)

        assert notebook.id == "nb123"
        assert len(notebook.sources) == 1

    def test_parse_notebook_missing_name(self) -> None:
        """Uses default name when missing."""
        data = [None, [], "nb123"]

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
        data = ["Test", [], "nb123", 1704067200]  # Seconds, not milliseconds

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

    def test_parse_source_list_id(self) -> None:
        """Parses source ID when wrapped in a list."""
        data = [["src_wrapped"], "Title", 1, "url", 1]
        source = parse_source_response(data)
        assert source.id == "src_wrapped"


class TestApiInternalHelpers:
    """Tests for internal helper methods of NotebookLMAPI."""

    def test_parse_timestamp_list(self) -> None:
        """Parses timestamp provided as a list."""
        from pynotebooklm.api import _parse_timestamp

        ts = 1704067200.0
        result = _parse_timestamp([ts])
        assert result is not None
        assert result.timestamp() == ts

    def test_parse_timestamp_ms(self) -> None:
        """Parses timestamp in milliseconds."""
        from pynotebooklm.api import _parse_timestamp

        ts_ms = 1704067200000.0
        result = _parse_timestamp(ts_ms)
        assert result is not None
        assert result.timestamp() == 1704067200.0

    def test_parse_timestamp_invalid(self) -> None:
        """Handles invalid timestamp formats."""
        from pynotebooklm.api import _parse_timestamp

        assert _parse_timestamp(None) is None
        assert _parse_timestamp("not a ts") is None
        assert _parse_timestamp([]) is None

    def test_unwrap_add_source_response_complex(self, api: NotebookLMAPI) -> None:
        """Tests unwrapping of deeply nested source response."""
        nested = [[[["id"], "Title"]]]
        result = api._unwrap_add_source_response(nested)
        assert result == [["id"], "Title"]

    def test_unwrap_add_source_response_invalid(self, api: NotebookLMAPI) -> None:
        """Handles unexpected response structure."""
        assert api._unwrap_add_source_response(None) is None
        assert api._unwrap_add_source_response([]) == []
        assert api._unwrap_add_source_response([[]]) == [[]]


class TestParseNotebookResponseDetailed:
    """Extra tests for parse_notebook_response."""

    def test_parse_notebook_with_metadata(self) -> None:
        """Parses notebook using metadata at index 5."""
        # [name, sources, id, ts3, ts4, [..., ..., ..., ..., ..., created_ts, ..., ..., updated_ts]]
        meta = [None, None, None, None, None, 1700000000, None, None, 1710000000]
        data = ["Test", [], "nb123", None, None, meta]

        notebook = parse_notebook_response(data)
        assert notebook.created_at is not None
        assert notebook.updated_at is not None
        assert notebook.created_at.timestamp() == 1700000000
        assert notebook.updated_at.timestamp() == 1710000000

    def test_parse_notebook_nested_list(self) -> None:
        """Handles notebook data wrapped in extra list."""
        data = [["Test", [], "nb123"]]
        notebook = parse_notebook_response(data)
        assert notebook.id == "nb123"


class TestPhase5ApiOps:
    """Tests for Phase 5 API operations."""

    @pytest.mark.asyncio
    async def test_configure_chat_custom(
        self, api: NotebookLMAPI, mock_session: MagicMock
    ) -> None:
        """configure_chat handles custom goal and prompt."""
        mock_session.call_rpc.return_value = {}
        await api.configure_chat("nb_id", goal=2, custom_prompt="Be helpful")

        mock_session.call_rpc.assert_called_once()
        args = mock_session.call_rpc.call_args[0][1]
        # Params: [notebook_id, [[None, None, None, None, None, None, None, [[2, "Be helpful"], [1]]]]]
        assert args[0] == "nb_id"
        assert args[1][0][7][0] == [2, "Be helpful"]

    @pytest.mark.asyncio
    async def test_get_source_guide(
        self, api: NotebookLMAPI, mock_session: MagicMock
    ) -> None:
        """get_source_guide calls correct RPC."""
        mock_session.call_rpc.return_value = {}
        await api.get_source_guide("src_id")
        mock_session.call_rpc.assert_called_once_with("tr032e", [[[["src_id"]]]])

    @pytest.mark.asyncio
    async def test_create_studio_artifact(
        self, api: NotebookLMAPI, mock_session: MagicMock
    ) -> None:
        """create_studio_artifact calls correct RPC."""
        mock_session.call_rpc.return_value = {}
        await api.create_studio_artifact("nb_id", 2, ["params"])
        mock_session.call_rpc.assert_called_once_with(
            "R7cb6c", [[2], "nb_id", ["params"]]
        )

    @pytest.mark.asyncio
    async def test_list_studio_artifacts_parsing(
        self, api: NotebookLMAPI, mock_session: MagicMock
    ) -> None:
        """list_studio_artifacts parses various statuses."""
        # Status 1 -> in_progress, 2 -> completed, 3 -> completed
        mock_session.call_rpc.return_value = [
            [
                ["id1", "Title 1", 2, None, 1],
                ["id2", "Title 2", 1, None, 2],
                ["id3", "Title 3", 3, None, 3],
                ["id4", "Title 4", 2, None, 99],
            ]
        ]

        results = await api.list_studio_artifacts("nb_id")
        assert len(results) == 4
        assert results[0]["status"] == "in_progress"
        assert results[1]["status"] == "completed"
        assert results[2]["status"] == "completed"
        assert results[3]["status"] == "unknown"

    @pytest.mark.asyncio
    async def test_query_notebook_full(
        self, api: NotebookLMAPI, mock_session: MagicMock
    ) -> None:
        """query_notebook builds correct request and handles CSRF."""
        mock_session.ensure_csrf_token = AsyncMock()
        mock_session.csrf_token = "test_token"
        mock_session.call_api_raw = AsyncMock(return_value="response")

        result = await api.query_notebook("nb_id", "query", source_ids=["s1"])

        assert result["raw_response"] == "response"
        mock_session.call_api_raw.assert_called_once()
        call_kwargs = mock_session.call_api_raw.call_args[1]
        assert "at=test_token" in call_kwargs["body"]
        assert "f.req=" in call_kwargs["body"]
        assert "s1" in call_kwargs["body"]


# =============================================================================
# Phase 11 Features Tests
# =============================================================================


class TestCheckSourceFreshness:
    """Tests for check_source_freshness method."""

    @pytest.mark.asyncio
    async def test_check_source_freshness_fresh(
        self, api: NotebookLMAPI, mock_session: MagicMock
    ) -> None:
        """check_source_freshness returns True for fresh sources."""
        mock_session.call_rpc.return_value = [["src123", True]]

        result = await api.check_source_freshness("src123")

        assert result is True
        mock_session.call_rpc.assert_called_once_with("yR9Yof", [None, ["src123"], [2]])

    @pytest.mark.asyncio
    async def test_check_source_freshness_stale(
        self, api: NotebookLMAPI, mock_session: MagicMock
    ) -> None:
        """check_source_freshness returns False for stale sources."""
        mock_session.call_rpc.return_value = [["src123", False]]

        result = await api.check_source_freshness("src123")

        assert result is False

    @pytest.mark.asyncio
    async def test_check_source_freshness_api_error(
        self, api: NotebookLMAPI, mock_session: MagicMock
    ) -> None:
        """check_source_freshness returns None on API error."""
        mock_session.call_rpc.side_effect = APIError("Not applicable")

        result = await api.check_source_freshness("non_drive_src")

        assert result is None

    @pytest.mark.asyncio
    async def test_check_source_freshness_invalid_response(
        self, api: NotebookLMAPI, mock_session: MagicMock
    ) -> None:
        """check_source_freshness returns None on invalid response."""
        mock_session.call_rpc.return_value = []

        result = await api.check_source_freshness("src123")

        assert result is None

    @pytest.mark.asyncio
    async def test_check_source_freshness_empty_inner(
        self, api: NotebookLMAPI, mock_session: MagicMock
    ) -> None:
        """check_source_freshness returns None when inner array is missing."""
        mock_session.call_rpc.return_value = [[]]

        result = await api.check_source_freshness("src123")

        assert result is None


class TestSyncSource:
    """Tests for sync_source method."""

    @pytest.mark.asyncio
    async def test_sync_source_success(
        self, api: NotebookLMAPI, mock_session: MagicMock
    ) -> None:
        """sync_source returns True on success."""
        mock_session.call_rpc.return_value = {}

        result = await api.sync_source("src123")

        assert result is True
        mock_session.call_rpc.assert_called_once_with("FLmJqe", [None, ["src123"], [2]])


class TestGetSourceText:
    """Tests for get_source_text method."""

    @pytest.mark.asyncio
    async def test_get_source_text_success(
        self, api: NotebookLMAPI, mock_session: MagicMock
    ) -> None:
        """get_source_text extracts content from source."""
        mock_session.call_rpc.return_value = [
            [
                ["src123"],
                "My Document",
                [None, None, None, None, 1],
            ],  # metadata at index 2
            None,
            None,
            [[[0, 100, "This is the content"]]],  # content blocks at index 3
        ]

        result = await api.get_source_text("src123")

        assert result["title"] == "My Document"
        assert result["content"] == "This is the content"
        assert result["source_type"] == "google_docs"
        assert result["char_count"] == 19

    @pytest.mark.asyncio
    async def test_get_source_text_empty_content(
        self, api: NotebookLMAPI, mock_session: MagicMock
    ) -> None:
        """get_source_text handles missing content blocks."""
        mock_session.call_rpc.return_value = [
            [["src123"], "Empty Doc"],
            None,
            None,
            None,  # No content blocks
        ]

        result = await api.get_source_text("src123")

        assert result["content"] == ""
        assert result["char_count"] == 0


class TestSourceTypeMap:
    """Tests for SOURCE_TYPE_MAP constant."""

    def test_source_type_map_values(self) -> None:
        """SOURCE_TYPE_MAP contains expected type mappings."""
        from pynotebooklm.api import SOURCE_TYPE_MAP

        assert SOURCE_TYPE_MAP[1] == "google_docs"
        assert SOURCE_TYPE_MAP[2] == "google_slides_sheets"
        assert SOURCE_TYPE_MAP[3] == "pdf"
        assert SOURCE_TYPE_MAP[4] == "pasted_text"
        assert SOURCE_TYPE_MAP[5] == "web_page"
        assert SOURCE_TYPE_MAP[9] == "youtube"


class TestParseSourceResponseWithMetadata:
    """Tests for parse_source_response with new metadata format."""

    def test_parse_source_with_metadata_list(self) -> None:
        """Parses source with metadata at index 2."""
        # Format: [id, title, metadata_list, ...]
        # metadata_list: [drive_id?, ..., ..., ..., type_code, ...]
        data = [
            ["src123"],
            "Google Doc",
            [
                None,
                None,
                None,
                None,
                1,
                None,
                None,
                ["https://example.com"],
            ],  # type_code=1 at pos 4
        ]

        source = parse_source_response(data)

        assert source.id == "src123"
        assert source.type == SourceType.DRIVE  # google_docs maps to DRIVE
        assert source.source_type_code == 1
        assert source.url == "https://example.com"

    def test_parse_source_youtube_from_metadata(self) -> None:
        """Parses YouTube source from metadata type code."""
        data = [
            "src123",
            "Video Title",
            [None, None, None, None, 9, None, None, ["https://youtube.com/v/abc"]],
        ]

        source = parse_source_response(data)

        assert source.type == SourceType.YOUTUBE
        assert source.source_type_code == 9

    def test_parse_source_web_page_from_metadata(self) -> None:
        """Parses web page source from metadata type code."""
        data = [
            "src123",
            "Web Page",
            [None, None, None, None, 5, None, None, ["https://example.com"]],
        ]

        source = parse_source_response(data)

        assert source.type == SourceType.URL
        assert source.source_type_code == 5

    def test_parse_source_pasted_text_from_metadata(self) -> None:
        """Parses pasted text source from metadata type code."""
        data = [
            "src123",
            "My Notes",
            [None, None, None, None, 4],
        ]

        source = parse_source_response(data)

        assert source.type == SourceType.TEXT
        assert source.source_type_code == 4

    def test_parse_source_generated_text_from_metadata(self) -> None:
        """Parses generated text source from metadata type code 8."""
        data = [
            "src123",
            "Generated Notes",
            [None, None, None, None, 8],
        ]

        source = parse_source_response(data)

        assert source.type == SourceType.TEXT
        assert source.source_type_code == 8

    def test_parse_source_unknown_type_defaults_to_text(self) -> None:
        """Unknown type codes default to TEXT type."""
        data = [
            "src123",
            "Unknown",
            [None, None, None, None, 99],  # Unknown type
        ]

        source = parse_source_response(data)

        assert source.type == SourceType.TEXT
        assert source.source_type_code == 99

    def test_parse_source_pdf_from_metadata(self) -> None:
        """Parses PDF source from metadata type code."""
        data = [
            "src123",
            "Document.pdf",
            [None, None, None, None, 3, None, None, ["https://example.com/doc.pdf"]],
        ]

        source = parse_source_response(data)

        assert source.type == SourceType.URL  # PDFs come from URLs
        assert source.source_type_code == 3
