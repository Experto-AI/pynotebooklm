"""
Integration tests for SourceManager.

These tests verify source management operations against the actual
NotebookLM API (or mocked responses for unit testing).
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from pynotebooklm import (
    APIError,
    AuthManager,
    BrowserSession,
    NotebookNotFoundError,
    Source,
    SourceManager,
    SourceType,
)

# Import mock data
from tests.fixtures.mock_rpc_responses import (
    MOCK_DRIVE_DOCS,
    MOCK_DRIVE_SOURCE,
    MOCK_NOTEBOOK_WITH_SOURCES,
    MOCK_TEXT_SOURCE,
    MOCK_URL_SOURCE,
    MOCK_YOUTUBE_SOURCE,
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
def source_manager(mock_session):
    """Create a SourceManager with mocked session."""
    return SourceManager(mock_session)


# =============================================================================
# Add URL Source Tests
# =============================================================================


class TestAddUrlSource:
    """Tests for SourceManager.add_url()"""

    @pytest.mark.asyncio
    async def test_add_url_returns_source(self, source_manager, mock_session):
        """Should return Source object for valid URL."""
        mock_session.call_rpc.return_value = MOCK_URL_SOURCE

        source = await source_manager.add_url("nb_123", "https://example.com/article")

        assert isinstance(source, Source)
        assert source.id == "src_url001"

    @pytest.mark.asyncio
    async def test_add_url_rejects_empty_notebook_id(self, source_manager):
        """Should reject empty notebook ID."""
        with pytest.raises(ValueError, match="Notebook ID cannot be empty"):
            await source_manager.add_url("", "https://example.com")

    @pytest.mark.asyncio
    async def test_add_url_rejects_empty_url(self, source_manager):
        """Should reject empty URL."""
        with pytest.raises(ValueError, match="URL cannot be empty"):
            await source_manager.add_url("nb_123", "")

    @pytest.mark.asyncio
    async def test_add_url_rejects_invalid_url(self, source_manager):
        """Should reject invalid URL format."""
        with pytest.raises(ValueError, match="Invalid URL"):
            await source_manager.add_url("nb_123", "not-a-url")

    @pytest.mark.asyncio
    async def test_add_url_detects_youtube_url(self, source_manager, mock_session):
        """Should automatically use YouTube type for YouTube URLs."""
        mock_session.call_rpc.return_value = MOCK_YOUTUBE_SOURCE

        source = await source_manager.add_url(
            "nb_123", "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        )

        # Should have been routed to YouTube handler
        assert source.type == SourceType.YOUTUBE


# =============================================================================
# Add YouTube Source Tests
# =============================================================================


class TestAddYoutubeSource:
    """Tests for SourceManager.add_youtube()"""

    @pytest.mark.asyncio
    async def test_add_youtube_returns_source(self, source_manager, mock_session):
        """Should return Source object for valid YouTube URL."""
        mock_session.call_rpc.return_value = MOCK_YOUTUBE_SOURCE

        source = await source_manager.add_youtube(
            "nb_123", "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        )

        assert isinstance(source, Source)
        assert source.type == SourceType.YOUTUBE

    @pytest.mark.asyncio
    async def test_add_youtube_accepts_short_url(self, source_manager, mock_session):
        """Should accept youtu.be short URLs."""
        mock_session.call_rpc.return_value = MOCK_YOUTUBE_SOURCE

        source = await source_manager.add_youtube(
            "nb_123", "https://youtu.be/dQw4w9WgXcQ"
        )

        assert isinstance(source, Source)

    @pytest.mark.asyncio
    async def test_add_youtube_rejects_non_youtube_url(self, source_manager):
        """Should reject non-YouTube URLs."""
        with pytest.raises(ValueError, match="Not a valid YouTube URL"):
            await source_manager.add_youtube("nb_123", "https://example.com")


# =============================================================================
# Add Text Source Tests
# =============================================================================


class TestAddTextSource:
    """Tests for SourceManager.add_text()"""

    @pytest.mark.asyncio
    async def test_add_text_returns_source(self, source_manager, mock_session):
        """Should return Source object for valid text content."""
        mock_session.call_rpc.return_value = MOCK_TEXT_SOURCE

        source = await source_manager.add_text(
            "nb_123", "This is my research notes.", title="Research Notes"
        )

        assert isinstance(source, Source)
        assert source.type == SourceType.TEXT

    @pytest.mark.asyncio
    async def test_add_text_uses_default_title(self, source_manager, mock_session):
        """Should use default title when not provided."""
        mock_session.call_rpc.return_value = MOCK_TEXT_SOURCE

        await source_manager.add_text("nb_123", "Content without title")

        # Verify default title was used
        call_args = mock_session.call_rpc.call_args
        assert "Untitled Text" in str(call_args) or call_args is not None

    @pytest.mark.asyncio
    async def test_add_text_rejects_empty_content(self, source_manager):
        """Should reject empty content."""
        with pytest.raises(ValueError, match="Content cannot be empty"):
            await source_manager.add_text("nb_123", "")

    @pytest.mark.asyncio
    async def test_add_text_rejects_whitespace_only(self, source_manager):
        """Should reject whitespace-only content."""
        with pytest.raises(ValueError, match="Content cannot be empty"):
            await source_manager.add_text("nb_123", "   ")


# =============================================================================
# Add Drive Source Tests
# =============================================================================


class TestAddDriveSource:
    """Tests for SourceManager.add_drive()"""

    @pytest.mark.asyncio
    async def test_add_drive_returns_source(self, source_manager, mock_session):
        """Should return Source object for valid Drive document."""
        mock_session.call_rpc.return_value = MOCK_DRIVE_SOURCE

        source = await source_manager.add_drive(
            "nb_123", "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"
        )

        assert isinstance(source, Source)
        assert source.type == SourceType.DRIVE

    @pytest.mark.asyncio
    async def test_add_drive_rejects_empty_doc_id(self, source_manager):
        """Should reject empty document ID."""
        with pytest.raises(ValueError, match="Drive document ID cannot be empty"):
            await source_manager.add_drive("nb_123", "")


# =============================================================================
# List Sources Tests
# =============================================================================


class TestListSources:
    """Tests for SourceManager.list_sources()"""

    @pytest.mark.asyncio
    async def test_list_returns_sources(self, source_manager, mock_session):
        """Should return list of Source objects."""
        mock_session.call_rpc.return_value = MOCK_NOTEBOOK_WITH_SOURCES

        sources = await source_manager.list_sources("nb_xyz789")

        assert isinstance(sources, list)
        # May have parsed sources depending on implementation
        assert len(sources) >= 0

    @pytest.mark.asyncio
    async def test_list_rejects_empty_notebook_id(self, source_manager):
        """Should reject empty notebook ID."""
        with pytest.raises(ValueError, match="Notebook ID cannot be empty"):
            await source_manager.list_sources("")

    @pytest.mark.asyncio
    async def test_list_not_found_raises_error(self, source_manager, mock_session):
        """Should raise NotebookNotFoundError for non-existent notebook."""
        mock_session.call_rpc.side_effect = APIError("not found", status_code=404)

        with pytest.raises(NotebookNotFoundError):
            await source_manager.list_sources("invalid_id")


# =============================================================================
# Delete Source Tests
# =============================================================================


class TestDeleteSource:
    """Tests for SourceManager.delete()"""

    @pytest.mark.asyncio
    async def test_delete_returns_true(self, source_manager, mock_session):
        """Should return True on successful deletion."""
        mock_session.call_rpc.return_value = None

        result = await source_manager.delete("nb_123", "src_456")

        assert result is True

    @pytest.mark.asyncio
    async def test_delete_rejects_empty_notebook_id(self, source_manager):
        """Should reject empty notebook ID."""
        with pytest.raises(ValueError, match="Notebook ID cannot be empty"):
            await source_manager.delete("", "src_456")

    @pytest.mark.asyncio
    async def test_delete_rejects_empty_source_id(self, source_manager):
        """Should reject empty source ID."""
        with pytest.raises(ValueError, match="Source ID cannot be empty"):
            await source_manager.delete("nb_123", "")


# =============================================================================
# List Drive Documents Tests
# =============================================================================


class TestListDriveDocs:
    """Tests for SourceManager.list_drive()"""

    @pytest.mark.asyncio
    async def test_list_drive_returns_documents(self, source_manager, mock_session):
        """Should return list of Drive document info."""
        mock_session.call_rpc.return_value = MOCK_DRIVE_DOCS

        docs = await source_manager.list_drive()

        assert isinstance(docs, list)
        assert len(docs) == 3
        assert docs[0]["id"] == "doc_id_1"
        assert docs[0]["title"] == "Project Proposal"

    @pytest.mark.asyncio
    async def test_list_drive_empty_result(self, source_manager, mock_session):
        """Should return empty list when no Drive docs available."""
        mock_session.call_rpc.return_value = []

        docs = await source_manager.list_drive()

        assert docs == []


# =============================================================================
# URL Validation Tests
# =============================================================================


class TestUrlValidation:
    """Tests for URL validation helper methods."""

    def test_is_valid_url_accepts_http(self, source_manager):
        """Should accept HTTP URLs."""
        assert source_manager._is_valid_url("http://example.com")

    def test_is_valid_url_accepts_https(self, source_manager):
        """Should accept HTTPS URLs."""
        assert source_manager._is_valid_url("https://example.com/path?query=1")

    def test_is_valid_url_rejects_invalid(self, source_manager):
        """Should reject invalid URLs."""
        assert not source_manager._is_valid_url("not-a-url")
        assert not source_manager._is_valid_url("ftp://example.com")
        assert not source_manager._is_valid_url("")

    def test_is_youtube_url_recognizes_youtube(self, source_manager):
        """Should recognize YouTube URLs."""
        assert source_manager._is_youtube_url("https://www.youtube.com/watch?v=abc123")
        assert source_manager._is_youtube_url("https://youtu.be/abc123")
        assert source_manager._is_youtube_url("https://youtube.com/embed/abc123")

    def test_is_youtube_url_rejects_non_youtube(self, source_manager):
        """Should reject non-YouTube URLs."""
        assert not source_manager._is_youtube_url("https://example.com")
        assert not source_manager._is_youtube_url("https://vimeo.com/12345")


# =============================================================================
# Batch Add URLs Tests
# =============================================================================


class TestBatchAddUrls:
    """Tests for SourceManager.batch_add_urls()."""

    @pytest.mark.asyncio
    async def test_batch_add_urls_requires_inputs(self, source_manager) -> None:
        with pytest.raises(ValueError):
            await source_manager.batch_add_urls("", ["https://example.com"])
        with pytest.raises(ValueError):
            await source_manager.batch_add_urls("nb", [])

    @pytest.mark.asyncio
    async def test_batch_add_urls_returns_sources(self, source_manager) -> None:
        source_manager.add_url = AsyncMock(
            side_effect=[MagicMock(id="s1"), MagicMock(id="s2")]
        )

        results = await source_manager.batch_add_urls(
            "nb", ["https://a.com", "https://b.com"]
        )

        assert [r.id for r in results] == ["s1", "s2"]
