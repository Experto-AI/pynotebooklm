"""
Unit tests for the SourceManager class.

These tests verify source management functionality including
adding, listing, and deleting sources, as well as the freshness check feature.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pynotebooklm.models import Notebook, Source, SourceType
from pynotebooklm.sources import SourceManager

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_session():
    """Create a mock BrowserSession."""
    return MagicMock()


@pytest.fixture
def source_manager(mock_session):
    """Create a SourceManager with a mock session."""
    return SourceManager(mock_session)


# =============================================================================
# list_sources Tests
# =============================================================================


class TestListSources:
    """Tests for SourceManager.list_sources method."""

    @pytest.mark.asyncio
    async def test_list_sources_success(self, source_manager):
        """list_sources returns sources from the notebook."""
        mock_notebook = Notebook(
            id="nb_123",
            name="Test Notebook",
            sources=[
                Source(id="src_1", title="Source 1", type=SourceType.URL),
                Source(id="src_2", title="Source 2", type=SourceType.DRIVE),
            ],
        )

        with patch.object(source_manager, "_api") as mock_api:
            mock_api.get_notebook = AsyncMock(return_value={"some": "data"})

            with patch(
                "pynotebooklm.sources.parse_notebook_response",
                return_value=mock_notebook,
            ):
                sources = await source_manager.list_sources("nb_123")

        assert len(sources) == 2
        assert sources[0].id == "src_1"
        assert sources[1].id == "src_2"

    @pytest.mark.asyncio
    async def test_list_sources_empty(self, source_manager):
        """list_sources returns empty list when no sources."""
        mock_notebook = Notebook(id="nb_123", name="Test Notebook", sources=[])

        with patch.object(source_manager, "_api") as mock_api:
            mock_api.get_notebook = AsyncMock(return_value={"some": "data"})

            with patch(
                "pynotebooklm.sources.parse_notebook_response",
                return_value=mock_notebook,
            ):
                sources = await source_manager.list_sources("nb_123")

        assert len(sources) == 0

    @pytest.mark.asyncio
    async def test_list_sources_empty_notebook_id_raises(self, source_manager):
        """list_sources raises ValueError for empty notebook_id."""
        with pytest.raises(ValueError, match="Notebook ID cannot be empty"):
            await source_manager.list_sources("")

    @pytest.mark.asyncio
    async def test_list_sources_parse_error_returns_empty(self, source_manager):
        """list_sources returns empty list when parse fails."""
        with patch.object(source_manager, "_api") as mock_api:
            mock_api.get_notebook = AsyncMock(return_value={"some": "data"})

            with patch(
                "pynotebooklm.sources.parse_notebook_response",
                side_effect=Exception("Parse error"),
            ):
                sources = await source_manager.list_sources("nb_123")

        assert sources == []


class TestListSourcesWithFreshness:
    """Tests for list_sources with check_freshness feature."""

    @pytest.mark.asyncio
    async def test_list_sources_with_freshness_check_drive_sources(
        self, source_manager
    ):
        """list_sources checks freshness for Drive sources when enabled."""
        mock_notebook = Notebook(
            id="nb_123",
            name="Test Notebook",
            sources=[
                Source(id="src_1", title="Web Source", type=SourceType.URL),
                Source(id="src_2", title="Drive Source", type=SourceType.DRIVE),
            ],
        )

        with patch.object(source_manager, "_api") as mock_api:
            mock_api.get_notebook = AsyncMock(return_value={"some": "data"})
            mock_api.check_source_freshness = AsyncMock(return_value=True)

            with patch(
                "pynotebooklm.sources.parse_notebook_response",
                return_value=mock_notebook,
            ):
                sources = await source_manager.list_sources(
                    "nb_123", check_freshness=True
                )

        assert len(sources) == 2
        # URL source should not have is_fresh set
        assert sources[0].is_fresh is None
        # Drive source should have is_fresh set to True
        assert sources[1].is_fresh is True
        # check_source_freshness should only be called for Drive sources
        mock_api.check_source_freshness.assert_called_once_with("src_2")

    @pytest.mark.asyncio
    async def test_list_sources_freshness_check_stale_source(self, source_manager):
        """list_sources correctly identifies stale Drive sources."""
        mock_notebook = Notebook(
            id="nb_123",
            name="Test Notebook",
            sources=[
                Source(id="src_1", title="Drive Source", type=SourceType.DRIVE),
            ],
        )

        with patch.object(source_manager, "_api") as mock_api:
            mock_api.get_notebook = AsyncMock(return_value={"some": "data"})
            mock_api.check_source_freshness = AsyncMock(return_value=False)

            with patch(
                "pynotebooklm.sources.parse_notebook_response",
                return_value=mock_notebook,
            ):
                sources = await source_manager.list_sources(
                    "nb_123", check_freshness=True
                )

        assert len(sources) == 1
        assert sources[0].is_fresh is False

    @pytest.mark.asyncio
    async def test_list_sources_freshness_check_failure_sets_none(self, source_manager):
        """list_sources sets is_fresh to None when check fails."""
        mock_notebook = Notebook(
            id="nb_123",
            name="Test Notebook",
            sources=[
                Source(id="src_1", title="Drive Source", type=SourceType.DRIVE),
            ],
        )

        with patch.object(source_manager, "_api") as mock_api:
            mock_api.get_notebook = AsyncMock(return_value={"some": "data"})
            mock_api.check_source_freshness = AsyncMock(
                side_effect=Exception("API Error")
            )

            with patch(
                "pynotebooklm.sources.parse_notebook_response",
                return_value=mock_notebook,
            ):
                sources = await source_manager.list_sources(
                    "nb_123", check_freshness=True
                )

        assert len(sources) == 1
        assert sources[0].is_fresh is None

    @pytest.mark.asyncio
    async def test_list_sources_without_freshness_check_skips_api_call(
        self, source_manager
    ):
        """list_sources skips freshness check when check_freshness=False."""
        mock_notebook = Notebook(
            id="nb_123",
            name="Test Notebook",
            sources=[
                Source(id="src_1", title="Drive Source", type=SourceType.DRIVE),
            ],
        )

        with patch.object(source_manager, "_api") as mock_api:
            mock_api.get_notebook = AsyncMock(return_value={"some": "data"})
            mock_api.check_source_freshness = AsyncMock(return_value=True)

            with patch(
                "pynotebooklm.sources.parse_notebook_response",
                return_value=mock_notebook,
            ):
                sources = await source_manager.list_sources(
                    "nb_123", check_freshness=False
                )

        assert len(sources) == 1
        # check_source_freshness should not be called
        mock_api.check_source_freshness.assert_not_called()

    @pytest.mark.asyncio
    async def test_list_sources_freshness_multiple_drive_sources(self, source_manager):
        """list_sources checks freshness for all Drive sources."""
        mock_notebook = Notebook(
            id="nb_123",
            name="Test Notebook",
            sources=[
                Source(id="src_1", title="Drive Source 1", type=SourceType.DRIVE),
                Source(id="src_2", title="Drive Source 2", type=SourceType.DRIVE),
                Source(id="src_3", title="Drive Source 3", type=SourceType.DRIVE),
            ],
        )

        with patch.object(source_manager, "_api") as mock_api:
            mock_api.get_notebook = AsyncMock(return_value={"some": "data"})
            # Return True, False, True for the three sources
            mock_api.check_source_freshness = AsyncMock(side_effect=[True, False, True])

            with patch(
                "pynotebooklm.sources.parse_notebook_response",
                return_value=mock_notebook,
            ):
                sources = await source_manager.list_sources(
                    "nb_123", check_freshness=True
                )

        assert len(sources) == 3
        assert sources[0].is_fresh is True
        assert sources[1].is_fresh is False
        assert sources[2].is_fresh is True
        assert mock_api.check_source_freshness.call_count == 3


# =============================================================================
# add_url Tests
# =============================================================================


class TestAddUrl:
    """Tests for SourceManager.add_url method."""

    @pytest.mark.asyncio
    async def test_add_url_success(self, source_manager):
        """add_url creates a source from a URL."""
        mock_source_data = {"id": "src_123", "title": "Example Page"}

        with patch.object(source_manager, "_api") as mock_api:
            mock_api.add_url_source = AsyncMock(return_value=mock_source_data)

            with patch(
                "pynotebooklm.sources.parse_source_response",
                return_value=Source(
                    id="src_123", title="Example Page", type=SourceType.URL
                ),
            ):
                source = await source_manager.add_url("nb_123", "https://example.com")

        assert source.id == "src_123"
        assert source.title == "Example Page"

    @pytest.mark.asyncio
    async def test_add_url_empty_notebook_id_raises(self, source_manager):
        """add_url raises ValueError for empty notebook_id."""
        with pytest.raises(ValueError, match="Notebook ID cannot be empty"):
            await source_manager.add_url("", "https://example.com")

    @pytest.mark.asyncio
    async def test_add_url_empty_url_raises(self, source_manager):
        """add_url raises ValueError for empty URL."""
        with pytest.raises(ValueError, match="URL cannot be empty"):
            await source_manager.add_url("nb_123", "")

    @pytest.mark.asyncio
    async def test_add_url_invalid_url_raises(self, source_manager):
        """add_url raises ValueError for invalid URL."""
        with pytest.raises(ValueError, match="Invalid URL format"):
            await source_manager.add_url("nb_123", "not-a-valid-url")

    @pytest.mark.asyncio
    async def test_add_url_detects_youtube_url(self, source_manager):
        """add_url detects YouTube URLs and calls add_youtube."""
        with patch.object(
            source_manager, "add_youtube", new_callable=AsyncMock
        ) as mock_add_youtube:
            mock_add_youtube.return_value = Source(
                id="src_yt", title="Video", type=SourceType.YOUTUBE
            )

            source = await source_manager.add_url(
                "nb_123", "https://www.youtube.com/watch?v=abc123"
            )

        assert source.type == SourceType.YOUTUBE
        mock_add_youtube.assert_called_once()


# =============================================================================
# add_youtube Tests
# =============================================================================


class TestAddYoutube:
    """Tests for SourceManager.add_youtube method."""

    @pytest.mark.asyncio
    async def test_add_youtube_success(self, source_manager):
        """add_youtube creates a source from a YouTube URL."""
        mock_source_data = {"id": "src_yt", "title": "Video Title"}

        with patch.object(source_manager, "_api") as mock_api:
            mock_api.add_youtube_source = AsyncMock(return_value=mock_source_data)

            with patch(
                "pynotebooklm.sources.parse_source_response",
                return_value=Source(
                    id="src_yt", title="Video Title", type=SourceType.URL
                ),
            ):
                source = await source_manager.add_youtube(
                    "nb_123", "https://www.youtube.com/watch?v=abc123"
                )

        assert source.id == "src_yt"
        assert source.type == SourceType.YOUTUBE

    @pytest.mark.asyncio
    async def test_add_youtube_empty_notebook_id_raises(self, source_manager):
        """add_youtube raises ValueError for empty notebook_id."""
        with pytest.raises(ValueError, match="Notebook ID cannot be empty"):
            await source_manager.add_youtube("", "https://www.youtube.com/watch?v=abc")

    @pytest.mark.asyncio
    async def test_add_youtube_empty_url_raises(self, source_manager):
        """add_youtube raises ValueError for empty URL."""
        with pytest.raises(ValueError, match="URL cannot be empty"):
            await source_manager.add_youtube("nb_123", "")

    @pytest.mark.asyncio
    async def test_add_youtube_invalid_url_raises(self, source_manager):
        """add_youtube raises ValueError for non-YouTube URL."""
        with pytest.raises(ValueError, match="Not a valid YouTube URL"):
            await source_manager.add_youtube("nb_123", "https://example.com")


# =============================================================================
# add_text Tests
# =============================================================================


class TestAddText:
    """Tests for SourceManager.add_text method."""

    @pytest.mark.asyncio
    async def test_add_text_success(self, source_manager):
        """add_text creates a source from text content."""
        mock_source_data = {"id": "src_txt", "title": "My Notes"}

        with patch.object(source_manager, "_api") as mock_api:
            mock_api.add_text_source = AsyncMock(return_value=mock_source_data)

            with patch(
                "pynotebooklm.sources.parse_source_response",
                return_value=Source(
                    id="src_txt", title="My Notes", type=SourceType.URL
                ),
            ):
                source = await source_manager.add_text(
                    "nb_123", "Some content", title="My Notes"
                )

        assert source.id == "src_txt"
        assert source.type == SourceType.TEXT

    @pytest.mark.asyncio
    async def test_add_text_empty_notebook_id_raises(self, source_manager):
        """add_text raises ValueError for empty notebook_id."""
        with pytest.raises(ValueError, match="Notebook ID cannot be empty"):
            await source_manager.add_text("", "content")

    @pytest.mark.asyncio
    async def test_add_text_empty_content_raises(self, source_manager):
        """add_text raises ValueError for empty content."""
        with pytest.raises(ValueError, match="Content cannot be empty"):
            await source_manager.add_text("nb_123", "")

    @pytest.mark.asyncio
    async def test_add_text_whitespace_content_raises(self, source_manager):
        """add_text raises ValueError for whitespace-only content."""
        with pytest.raises(ValueError, match="Content cannot be empty"):
            await source_manager.add_text("nb_123", "   ")


# =============================================================================
# add_drive Tests
# =============================================================================


class TestAddDrive:
    """Tests for SourceManager.add_drive method."""

    @pytest.mark.asyncio
    async def test_add_drive_success(self, source_manager):
        """add_drive creates a source from a Drive document."""
        mock_source_data = {"id": "src_drive", "title": "Google Doc"}

        with patch.object(source_manager, "_api") as mock_api:
            mock_api.add_drive_source = AsyncMock(return_value=mock_source_data)

            with patch(
                "pynotebooklm.sources.parse_source_response",
                return_value=Source(
                    id="src_drive", title="Google Doc", type=SourceType.URL
                ),
            ):
                source = await source_manager.add_drive("nb_123", "1ABC123XYZ")

        assert source.id == "src_drive"
        assert source.type == SourceType.DRIVE

    @pytest.mark.asyncio
    async def test_add_drive_empty_notebook_id_raises(self, source_manager):
        """add_drive raises ValueError for empty notebook_id."""
        with pytest.raises(ValueError, match="Notebook ID cannot be empty"):
            await source_manager.add_drive("", "doc_id")

    @pytest.mark.asyncio
    async def test_add_drive_empty_doc_id_raises(self, source_manager):
        """add_drive raises ValueError for empty drive_doc_id."""
        with pytest.raises(ValueError, match="Drive document ID cannot be empty"):
            await source_manager.add_drive("nb_123", "")


# =============================================================================
# batch_add_urls Tests
# =============================================================================


class TestBatchAddUrls:
    """Tests for SourceManager.batch_add_urls method."""

    @pytest.mark.asyncio
    async def test_batch_add_urls_success(self, source_manager):
        """batch_add_urls adds multiple URLs."""
        with patch.object(
            source_manager, "add_url", new_callable=AsyncMock
        ) as mock_add_url:
            mock_add_url.side_effect = [
                Source(id="src_1", title="Page 1", type=SourceType.URL),
                Source(id="src_2", title="Page 2", type=SourceType.URL),
            ]

            sources = await source_manager.batch_add_urls(
                "nb_123", ["https://example1.com", "https://example2.com"]
            )

        assert len(sources) == 2
        assert mock_add_url.call_count == 2

    @pytest.mark.asyncio
    async def test_batch_add_urls_empty_notebook_id_raises(self, source_manager):
        """batch_add_urls raises ValueError for empty notebook_id."""
        with pytest.raises(ValueError, match="Notebook ID cannot be empty"):
            await source_manager.batch_add_urls("", ["https://example.com"])

    @pytest.mark.asyncio
    async def test_batch_add_urls_empty_list_raises(self, source_manager):
        """batch_add_urls raises ValueError for empty URLs list."""
        with pytest.raises(ValueError, match="URLs list cannot be empty"):
            await source_manager.batch_add_urls("nb_123", [])


# =============================================================================
# delete Tests
# =============================================================================


class TestDelete:
    """Tests for SourceManager.delete method."""

    @pytest.mark.asyncio
    async def test_delete_success(self, source_manager):
        """delete removes a source successfully."""
        with patch.object(source_manager, "_api") as mock_api:
            mock_api.delete_source = AsyncMock(return_value=True)

            result = await source_manager.delete("nb_123", "src_456")

        assert result is True
        mock_api.delete_source.assert_called_once_with("nb_123", "src_456")

    @pytest.mark.asyncio
    async def test_delete_empty_notebook_id_raises(self, source_manager):
        """delete raises ValueError for empty notebook_id."""
        with pytest.raises(ValueError, match="Notebook ID cannot be empty"):
            await source_manager.delete("", "src_456")

    @pytest.mark.asyncio
    async def test_delete_empty_source_id_raises(self, source_manager):
        """delete raises ValueError for empty source_id."""
        with pytest.raises(ValueError, match="Source ID cannot be empty"):
            await source_manager.delete("nb_123", "")


# =============================================================================
# list_drive Tests
# =============================================================================


class TestListDrive:
    """Tests for SourceManager.list_drive method."""

    @pytest.mark.asyncio
    async def test_list_drive_success(self, source_manager):
        """list_drive returns Drive documents."""
        with patch.object(source_manager, "_api") as mock_api:
            mock_api.list_drive_docs = AsyncMock(
                return_value=[
                    ["doc_1", "Document 1"],
                    ["doc_2", "Document 2"],
                ]
            )

            docs = await source_manager.list_drive()

        assert len(docs) == 2
        assert docs[0]["id"] == "doc_1"
        assert docs[0]["title"] == "Document 1"

    @pytest.mark.asyncio
    async def test_list_drive_empty(self, source_manager):
        """list_drive returns empty list when no documents."""
        with patch.object(source_manager, "_api") as mock_api:
            mock_api.list_drive_docs = AsyncMock(return_value=[])

            docs = await source_manager.list_drive()

        assert len(docs) == 0

    @pytest.mark.asyncio
    async def test_list_drive_handles_malformed_data(self, source_manager):
        """list_drive handles malformed response data."""
        with patch.object(source_manager, "_api") as mock_api:
            mock_api.list_drive_docs = AsyncMock(
                return_value=[
                    ["doc_1", "Document 1"],  # Valid
                    ["single_item"],  # Invalid - single item
                    "not_a_list",  # Invalid - not a list
                    ["doc_2", "Document 2"],  # Valid
                ]
            )

            docs = await source_manager.list_drive()

        # Only valid entries should be returned
        assert len(docs) == 2
        assert docs[0]["id"] == "doc_1"
        assert docs[1]["id"] == "doc_2"


# =============================================================================
# Helper Method Tests
# =============================================================================


class TestHelperMethods:
    """Tests for private helper methods."""

    def test_is_valid_url_http(self, source_manager):
        """_is_valid_url returns True for HTTP URLs."""
        assert source_manager._is_valid_url("http://example.com") is True

    def test_is_valid_url_https(self, source_manager):
        """_is_valid_url returns True for HTTPS URLs."""
        assert source_manager._is_valid_url("https://example.com") is True

    def test_is_valid_url_with_path(self, source_manager):
        """_is_valid_url returns True for URLs with paths."""
        assert source_manager._is_valid_url("https://example.com/path/to/page") is True

    def test_is_valid_url_invalid(self, source_manager):
        """_is_valid_url returns False for invalid URLs."""
        assert source_manager._is_valid_url("not-a-url") is False
        assert source_manager._is_valid_url("ftp://example.com") is False
        assert source_manager._is_valid_url("") is False

    def test_is_youtube_url_standard(self, source_manager):
        """_is_youtube_url returns True for standard YouTube URL."""
        assert (
            source_manager._is_youtube_url("https://www.youtube.com/watch?v=abc123")
            is True
        )

    def test_is_youtube_url_short(self, source_manager):
        """_is_youtube_url returns True for short YouTube URL."""
        assert source_manager._is_youtube_url("https://youtu.be/abc123") is True

    def test_is_youtube_url_embed(self, source_manager):
        """_is_youtube_url returns True for embed YouTube URL."""
        assert (
            source_manager._is_youtube_url("https://www.youtube.com/embed/abc123")
            is True
        )

    def test_is_youtube_url_not_youtube(self, source_manager):
        """_is_youtube_url returns False for non-YouTube URL."""
        assert source_manager._is_youtube_url("https://example.com") is False
        assert source_manager._is_youtube_url("https://vimeo.com/123") is False
