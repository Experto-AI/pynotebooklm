"""
Integration tests for ResearchDiscovery.

These tests verify research discovery operations including
web research, status checking, and result importing.
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from pynotebooklm import APIError, AuthManager, BrowserSession
from pynotebooklm.research import (
    ResearchDiscovery,
    ResearchResult,
    ResearchSession,
    ResearchStatus,
    TopicSuggestion,
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
def research_discovery(mock_session):
    """Create a ResearchDiscovery with mocked session."""
    return ResearchDiscovery(mock_session)


# =============================================================================
# Mock Research Responses
# =============================================================================

MOCK_RESEARCH_STARTED = [
    "in_progress",
    [],
]

MOCK_RESEARCH_COMPLETED = [
    "completed",
    [
        [
            "res_001",
            "AI Trends 2024",
            "https://example.com/ai-trends",
            "Summary of AI trends",
            0.95,
        ],
        [
            "res_002",
            "Machine Learning Guide",
            "https://example.com/ml-guide",
            "ML overview",
            0.88,
        ],
        [
            "res_003",
            "Deep Learning Paper",
            "https://arxiv.org/abs/2401.00001",
            "Research paper",
            0.82,
        ],
    ],
]

MOCK_TOPIC_SUGGESTIONS = [
    ["Reinforcement Learning", "Advanced RL techniques and applications", "high"],
    ["Natural Language Processing", "NLP trends and transformers", "high"],
    ["Computer Vision", "Image recognition and object detection", "medium"],
]


# =============================================================================
# Start Web Research Tests
# =============================================================================


class TestStartWebResearch:
    """Tests for ResearchDiscovery.start_web_research()"""

    @pytest.mark.asyncio
    async def test_start_returns_research_session(
        self, research_discovery, mock_session
    ):
        """Should return ResearchSession object."""
        mock_session.call_rpc.side_effect = APIError(
            "RPC not available", status_code=400
        )

        session = await research_discovery.start_web_research(
            "nb_123", "AI trends 2024"
        )

        assert isinstance(session, ResearchSession)
        assert session.topic == "AI trends 2024"
        assert session.id.startswith("research_")

    @pytest.mark.asyncio
    async def test_start_generates_unique_id(self, research_discovery, mock_session):
        """Should generate unique research IDs."""
        mock_session.call_rpc.side_effect = APIError(
            "RPC not available", status_code=400
        )

        session1 = await research_discovery.start_web_research("nb_123", "Topic 1")
        session2 = await research_discovery.start_web_research("nb_123", "Topic 2")

        assert session1.id != session2.id

    @pytest.mark.asyncio
    async def test_start_rejects_empty_topic(self, research_discovery):
        """Should reject empty topic."""
        with pytest.raises(ValueError, match="topic cannot be empty"):
            await research_discovery.start_web_research("nb_123", "")

    @pytest.mark.asyncio
    async def test_start_rejects_empty_notebook_id(self, research_discovery):
        """Should reject empty notebook ID."""
        with pytest.raises(ValueError, match="Notebook ID cannot be empty"):
            await research_discovery.start_web_research("", "Test topic")

    @pytest.mark.asyncio
    async def test_start_strips_whitespace(self, research_discovery, mock_session):
        """Should strip whitespace from topic."""
        mock_session.call_rpc.side_effect = APIError(
            "RPC not available", status_code=400
        )

        session = await research_discovery.start_web_research(
            "nb_123", "  Padded Topic  "
        )

        assert session.topic == "Padded Topic"

    @pytest.mark.asyncio
    async def test_start_sets_timestamp(self, research_discovery, mock_session):
        """Should set started_at timestamp."""
        mock_session.call_rpc.side_effect = APIError(
            "RPC not available", status_code=400
        )

        session = await research_discovery.start_web_research("nb_123", "Test topic")

        assert session.started_at is not None
        assert isinstance(session.started_at, datetime)

    @pytest.mark.asyncio
    async def test_start_with_valid_response(self, research_discovery, mock_session):
        """Should parse valid research response."""
        mock_session.call_rpc.return_value = MOCK_RESEARCH_STARTED

        session = await research_discovery.start_web_research("nb_123", "AI topics")

        assert session.status == ResearchStatus.IN_PROGRESS

    @pytest.mark.asyncio
    async def test_start_parses_completed_response(
        self, research_discovery, mock_session
    ):
        """Should parse completed research with results."""
        mock_session.call_rpc.return_value = MOCK_RESEARCH_COMPLETED

        session = await research_discovery.start_web_research("nb_123", "AI topics")

        assert session.status == ResearchStatus.COMPLETED
        assert len(session.results) == 3
        assert session.results[0].title == "AI Trends 2024"


# =============================================================================
# Get Status Tests
# =============================================================================


class TestGetStatus:
    """Tests for ResearchDiscovery.get_status()"""

    @pytest.mark.asyncio
    async def test_get_status_from_cache(self, research_discovery, mock_session):
        """Should return cached session."""
        mock_session.call_rpc.side_effect = APIError(
            "RPC not available", status_code=400
        )

        # First, create a session
        created = await research_discovery.start_web_research("nb_123", "Test topic")

        # Then get its status
        status = await research_discovery.get_status(created.id)

        assert status.id == created.id
        assert status.topic == "Test topic"

    @pytest.mark.asyncio
    async def test_get_status_rejects_empty_id(self, research_discovery):
        """Should reject empty research ID."""
        with pytest.raises(ValueError, match="cannot be empty"):
            await research_discovery.get_status("")

    @pytest.mark.asyncio
    async def test_get_status_not_found(self, research_discovery, mock_session):
        """Should raise ValueError for unknown research ID."""
        mock_session.call_rpc.side_effect = APIError("Not found", status_code=404)

        with pytest.raises(ValueError, match="not found"):
            await research_discovery.get_status("nonexistent_id")

    @pytest.mark.asyncio
    async def test_get_status_updates_in_progress(
        self, research_discovery, mock_session
    ):
        """Should fetch updated status for in-progress research."""
        # Create an in-progress session
        research_discovery._research_sessions["test_id"] = ResearchSession(
            id="test_id",
            topic="Test",
            status=ResearchStatus.IN_PROGRESS,
        )

        # Mock the status check to return completed
        mock_session.call_rpc.return_value = MOCK_RESEARCH_COMPLETED

        status = await research_discovery.get_status("test_id")

        assert status.status == ResearchStatus.COMPLETED


# =============================================================================
# Import Research Results Tests
# =============================================================================


class TestImportResearchResults:
    """Tests for ResearchDiscovery.import_research_results()"""

    @pytest.mark.asyncio
    async def test_import_returns_source_ids(self, research_discovery, mock_session):
        """Should return list of created source IDs."""
        mock_session.call_rpc.return_value = ["src_new_001", "Source Title", 1]

        results = [
            ResearchResult(id="res_1", title="Test 1", url="https://example.com/1"),
            ResearchResult(id="res_2", title="Test 2", url="https://example.com/2"),
        ]

        source_ids = await research_discovery.import_research_results("nb_123", results)

        assert isinstance(source_ids, list)
        assert len(source_ids) == 2

    @pytest.mark.asyncio
    async def test_import_rejects_empty_notebook_id(self, research_discovery):
        """Should reject empty notebook ID."""
        results = [ResearchResult(id="r1", title="Test", url="https://example.com")]

        with pytest.raises(ValueError, match="Notebook ID cannot be empty"):
            await research_discovery.import_research_results("", results)

    @pytest.mark.asyncio
    async def test_import_rejects_empty_results(self, research_discovery):
        """Should reject empty results list."""
        with pytest.raises(ValueError, match="Results list cannot be empty"):
            await research_discovery.import_research_results("nb_123", [])

    @pytest.mark.asyncio
    async def test_import_skips_results_without_url(
        self, research_discovery, mock_session
    ):
        """Should skip results that don't have URLs."""
        mock_session.call_rpc.return_value = ["src_new_001", "Source Title", 1]

        results = [
            ResearchResult(id="res_1", title="Has URL", url="https://example.com/1"),
            ResearchResult(id="res_2", title="No URL", url=None),  # No URL
        ]

        source_ids = await research_discovery.import_research_results("nb_123", results)

        # Should only import the one with URL
        assert len(source_ids) == 1

    @pytest.mark.asyncio
    async def test_import_handles_api_errors_gracefully(
        self, research_discovery, mock_session
    ):
        """Should continue importing even if some fail."""
        # First call succeeds, second fails
        mock_session.call_rpc.side_effect = [
            ["src_001", "Title 1", 1],
            APIError("Failed to add source", status_code=400),
        ]

        results = [
            ResearchResult(id="r1", title="Test 1", url="https://example.com/1"),
            ResearchResult(id="r2", title="Test 2", url="https://example.com/2"),
        ]

        source_ids = await research_discovery.import_research_results("nb_123", results)

        assert len(source_ids) == 1


# =============================================================================
# Sync Drive Sources Tests
# =============================================================================


class TestSyncDriveSources:
    """Tests for ResearchDiscovery.sync_drive_sources()"""

    @pytest.mark.asyncio
    async def test_sync_returns_count(self, research_discovery, mock_session):
        """Should return number of synced sources."""
        mock_session.call_rpc.return_value = [5]

        count = await research_discovery.sync_drive_sources("nb_123")

        assert count == 5

    @pytest.mark.asyncio
    async def test_sync_rejects_empty_notebook_id(self, research_discovery):
        """Should reject empty notebook ID."""
        with pytest.raises(ValueError, match="cannot be empty"):
            await research_discovery.sync_drive_sources("")

    @pytest.mark.asyncio
    async def test_sync_handles_unavailable_rpc(self, research_discovery, mock_session):
        """Should return 0 when RPC not available."""
        mock_session.call_rpc.side_effect = APIError(
            "RPC not available", status_code=400
        )

        count = await research_discovery.sync_drive_sources("nb_123")

        assert count == 0

    @pytest.mark.asyncio
    async def test_sync_handles_empty_response(self, research_discovery, mock_session):
        """Should handle empty response."""
        mock_session.call_rpc.return_value = []

        count = await research_discovery.sync_drive_sources("nb_123")

        assert count == 0


# =============================================================================
# Suggest Topics Tests
# =============================================================================


class TestSuggestTopics:
    """Tests for ResearchDiscovery.suggest_topics()"""

    @pytest.mark.asyncio
    async def test_suggest_returns_topic_list(self, research_discovery, mock_session):
        """Should return list of TopicSuggestion objects."""
        mock_session.call_rpc.return_value = MOCK_TOPIC_SUGGESTIONS

        topics = await research_discovery.suggest_topics("nb_123")

        assert isinstance(topics, list)
        assert len(topics) == 3
        assert all(isinstance(t, TopicSuggestion) for t in topics)

    @pytest.mark.asyncio
    async def test_suggest_parses_topic_details(self, research_discovery, mock_session):
        """Should parse topic details correctly."""
        mock_session.call_rpc.return_value = MOCK_TOPIC_SUGGESTIONS

        topics = await research_discovery.suggest_topics("nb_123")

        assert topics[0].topic == "Reinforcement Learning"
        assert topics[0].description == "Advanced RL techniques and applications"
        assert topics[0].relevance == "high"

    @pytest.mark.asyncio
    async def test_suggest_rejects_empty_notebook_id(self, research_discovery):
        """Should reject empty notebook ID."""
        with pytest.raises(ValueError, match="cannot be empty"):
            await research_discovery.suggest_topics("")

    @pytest.mark.asyncio
    async def test_suggest_handles_unavailable_rpc(
        self, research_discovery, mock_session
    ):
        """Should return empty list when RPC not available."""
        mock_session.call_rpc.side_effect = APIError(
            "RPC not available", status_code=400
        )

        topics = await research_discovery.suggest_topics("nb_123")

        assert topics == []

    @pytest.mark.asyncio
    async def test_suggest_handles_empty_response(
        self, research_discovery, mock_session
    ):
        """Should handle empty response."""
        mock_session.call_rpc.return_value = []

        topics = await research_discovery.suggest_topics("nb_123")

        assert topics == []


# =============================================================================
# ResearchResult Model Tests
# =============================================================================


class TestResearchResultModel:
    """Tests for ResearchResult model."""

    def test_creates_with_required_fields(self):
        """Should create with required fields."""
        result = ResearchResult(id="r1", title="Test Title")

        assert result.id == "r1"
        assert result.title == "Test Title"
        assert result.url is None
        assert result.source_type == "web"

    def test_creates_with_all_fields(self):
        """Should create with all fields."""
        result = ResearchResult(
            id="r1",
            title="Full Result",
            url="https://example.com",
            snippet="This is a snippet",
            source_type="academic",
            relevance_score=0.95,
        )

        assert result.url == "https://example.com"
        assert result.snippet == "This is a snippet"
        assert result.source_type == "academic"
        assert result.relevance_score == 0.95


# =============================================================================
# ResearchSession Model Tests
# =============================================================================


class TestResearchSessionModel:
    """Tests for ResearchSession model."""

    def test_creates_with_defaults(self):
        """Should create with default values."""
        session = ResearchSession(id="s1", topic="Test Topic")

        assert session.id == "s1"
        assert session.topic == "Test Topic"
        assert session.status == ResearchStatus.PENDING
        assert session.results == []

    def test_status_enum_values(self):
        """Should have correct status enum values."""
        assert ResearchStatus.PENDING.value == "pending"
        assert ResearchStatus.IN_PROGRESS.value == "in_progress"
        assert ResearchStatus.COMPLETED.value == "completed"
        assert ResearchStatus.FAILED.value == "failed"


# =============================================================================
# TopicSuggestion Model Tests
# =============================================================================


class TestTopicSuggestionModel:
    """Tests for TopicSuggestion model."""

    def test_creates_with_required_fields(self):
        """Should create with required fields."""
        topic = TopicSuggestion(topic="AI Trends")

        assert topic.topic == "AI Trends"
        assert topic.description is None
        assert topic.relevance == "medium"

    def test_creates_with_all_fields(self):
        """Should create with all fields."""
        topic = TopicSuggestion(
            topic="Machine Learning",
            description="ML techniques and applications",
            relevance="high",
        )

        assert topic.description == "ML techniques and applications"
        assert topic.relevance == "high"
