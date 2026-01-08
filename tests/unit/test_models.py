"""
Unit tests for Pydantic models.

These tests verify model validation, serialization, and enums.
"""

from datetime import datetime

import pytest
from pydantic import ValidationError

from pynotebooklm.models import (
    AddSourceRequest,
    Artifact,
    ArtifactStatus,
    ArtifactType,
    AuthState,
    ChatMessage,
    ChatRole,
    Cookie,
    CreateNotebookRequest,
    GeneratePodcastRequest,
    Notebook,
    PodcastStyle,
    QueryNotebookRequest,
    Source,
    SourceStatus,
    SourceType,
)

# =============================================================================
# Enum Tests
# =============================================================================


class TestEnums:
    """Tests for enum types."""

    def test_source_type_values(self) -> None:
        """SourceType has expected values."""
        assert SourceType.URL.value == "url"
        assert SourceType.YOUTUBE.value == "youtube"
        assert SourceType.DRIVE.value == "drive"
        assert SourceType.TEXT.value == "text"

    def test_source_status_values(self) -> None:
        """SourceStatus has expected values."""
        assert SourceStatus.PROCESSING.value == "processing"
        assert SourceStatus.READY.value == "ready"
        assert SourceStatus.FAILED.value == "failed"

    def test_artifact_type_values(self) -> None:
        """ArtifactType has expected values."""
        assert ArtifactType.AUDIO.value == "audio"
        assert ArtifactType.VIDEO.value == "video"
        assert ArtifactType.INFOGRAPHIC.value == "infographic"
        assert ArtifactType.SLIDES.value == "slides"
        assert ArtifactType.MINDMAP.value == "mindmap"

    def test_artifact_status_values(self) -> None:
        """ArtifactStatus has expected values."""
        assert ArtifactStatus.PENDING.value == "pending"
        assert ArtifactStatus.GENERATING.value == "generating"
        assert ArtifactStatus.READY.value == "ready"
        assert ArtifactStatus.FAILED.value == "failed"

    def test_podcast_style_values(self) -> None:
        """PodcastStyle has expected values."""
        assert PodcastStyle.DEEP_DIVE.value == "deep_dive"
        assert PodcastStyle.BRIEFING.value == "briefing"
        assert PodcastStyle.LEARNING_GUIDE.value == "learning_guide"


# =============================================================================
# Source Model Tests
# =============================================================================


class TestSourceModel:
    """Tests for the Source model."""

    def test_source_creation_minimal(self) -> None:
        """Source can be created with minimal fields."""
        source = Source(
            id="src_123",
            type=SourceType.URL,
            title="Test Source",
        )
        assert source.id == "src_123"
        assert source.type == SourceType.URL
        assert source.title == "Test Source"
        assert source.url is None
        assert source.status == SourceStatus.PROCESSING  # default

    def test_source_creation_full(self) -> None:
        """Source can be created with all fields."""
        now = datetime.now()
        source = Source(
            id="src_456",
            type=SourceType.YOUTUBE,
            title="YouTube Video",
            url="https://youtube.com/watch?v=test",
            status=SourceStatus.READY,
            created_at=now,
        )
        assert source.url == "https://youtube.com/watch?v=test"
        assert source.status == SourceStatus.READY
        assert source.created_at == now

    def test_source_serialization(self) -> None:
        """Source model serializes to dict correctly."""
        source = Source(
            id="src_789",
            type=SourceType.TEXT,
            title="Text Note",
        )
        data = source.model_dump()
        assert data["id"] == "src_789"
        assert data["type"] == "text"

    def test_source_from_string_enum(self) -> None:
        """Source can be created with string enum values."""
        source = Source(
            id="src_abc",
            type="drive",  # type: ignore
            title="Drive Doc",
            status="ready",  # type: ignore
        )
        assert source.type == SourceType.DRIVE
        assert source.status == SourceStatus.READY


# =============================================================================
# Notebook Model Tests
# =============================================================================


class TestNotebookModel:
    """Tests for the Notebook model."""

    def test_notebook_creation_minimal(self) -> None:
        """Notebook can be created with minimal fields."""
        notebook = Notebook(id="nb_123", name="Test Notebook")
        assert notebook.id == "nb_123"
        assert notebook.name == "Test Notebook"
        assert notebook.sources == []
        assert notebook.source_count == 0

    def test_notebook_with_sources(self) -> None:
        """Notebook can contain sources."""
        sources = [
            Source(id="src_1", type=SourceType.URL, title="Source 1"),
            Source(id="src_2", type=SourceType.YOUTUBE, title="Source 2"),
        ]
        notebook = Notebook(
            id="nb_456",
            name="Research Notebook",
            sources=sources,
            source_count=2,
        )
        assert len(notebook.sources) == 2
        assert notebook.source_count == 2


# =============================================================================
# Artifact Model Tests
# =============================================================================


class TestArtifactModel:
    """Tests for the Artifact model."""

    def test_artifact_creation(self) -> None:
        """Artifact can be created with required fields."""
        artifact = Artifact(
            id="art_123",
            type=ArtifactType.AUDIO,
        )
        assert artifact.id == "art_123"
        assert artifact.type == ArtifactType.AUDIO
        assert artifact.status == ArtifactStatus.PENDING
        assert artifact.progress == 0.0
        assert artifact.url is None

    def test_artifact_progress_validation(self) -> None:
        """Artifact progress must be between 0 and 1."""
        artifact = Artifact(
            id="art_456",
            type=ArtifactType.VIDEO,
            progress=0.5,
        )
        assert artifact.progress == 0.5

        # Test invalid progress values
        with pytest.raises(ValidationError):
            Artifact(id="art_bad", type=ArtifactType.VIDEO, progress=1.5)

        with pytest.raises(ValidationError):
            Artifact(id="art_bad", type=ArtifactType.VIDEO, progress=-0.1)


# =============================================================================
# ChatMessage Model Tests
# =============================================================================


class TestChatMessageModel:
    """Tests for the ChatMessage model."""

    def test_chat_message_user(self) -> None:
        """User chat message can be created."""
        msg = ChatMessage(
            role=ChatRole.USER,
            content="What is this about?",
        )
        assert msg.role == ChatRole.USER
        assert msg.content == "What is this about?"
        assert msg.citations == []

    def test_chat_message_assistant_with_citations(self) -> None:
        """Assistant message can have citations."""
        msg = ChatMessage(
            role=ChatRole.ASSISTANT,
            content="According to the sources...",
            citations=["Source 1, p. 5", "Source 2, p. 10"],
        )
        assert msg.role == ChatRole.ASSISTANT
        assert len(msg.citations) == 2


# =============================================================================
# Request Model Tests
# =============================================================================


class TestRequestModels:
    """Tests for request models."""

    def test_create_notebook_request_validation(self) -> None:
        """CreateNotebookRequest validates name length."""
        # Valid name
        req = CreateNotebookRequest(name="My Notebook")
        assert req.name == "My Notebook"

        # Empty name should fail
        with pytest.raises(ValidationError):
            CreateNotebookRequest(name="")

    def test_add_source_request(self) -> None:
        """AddSourceRequest can be created for different source types."""
        # URL source
        req = AddSourceRequest(
            notebook_id="nb_123",
            source_type=SourceType.URL,
            url="https://example.com",
        )
        assert req.notebook_id == "nb_123"
        assert req.source_type == SourceType.URL
        assert req.url == "https://example.com"

        # Text source
        text_req = AddSourceRequest(
            notebook_id="nb_123",
            source_type=SourceType.TEXT,
            content="My notes here",
            title="Notes",
        )
        assert text_req.content == "My notes here"

    def test_generate_podcast_request_defaults(self) -> None:
        """GeneratePodcastRequest has sensible defaults."""
        req = GeneratePodcastRequest(notebook_id="nb_123")
        assert req.style == PodcastStyle.DEEP_DIVE
        assert req.timeout == 300

    def test_generate_podcast_request_timeout_validation(self) -> None:
        """GeneratePodcastRequest validates timeout range."""
        # Valid timeout
        req = GeneratePodcastRequest(notebook_id="nb_123", timeout=120)
        assert req.timeout == 120

        # Too short
        with pytest.raises(ValidationError):
            GeneratePodcastRequest(notebook_id="nb_123", timeout=30)

        # Too long
        with pytest.raises(ValidationError):
            GeneratePodcastRequest(notebook_id="nb_123", timeout=1000)

    def test_query_notebook_request_validation(self) -> None:
        """QueryNotebookRequest validates question."""
        req = QueryNotebookRequest(
            notebook_id="nb_123",
            question="What are the main topics?",
        )
        assert req.question == "What are the main topics?"
        assert req.conversation_id is None

        # Empty question should fail
        with pytest.raises(ValidationError):
            QueryNotebookRequest(notebook_id="nb_123", question="")


# =============================================================================
# Cookie and AuthState Tests
# =============================================================================


class TestCookieModel:
    """Tests for the Cookie model."""

    def test_cookie_defaults(self) -> None:
        """Cookie has sensible defaults."""
        cookie = Cookie(
            name="SID",
            value="test_value",
            domain=".google.com",
        )
        assert cookie.path == "/"
        assert cookie.http_only is False
        assert cookie.secure is False
        assert cookie.same_site == "Lax"

    def test_cookie_full_fields(self) -> None:
        """Cookie can be created with all fields."""
        cookie = Cookie(
            name="__Secure-1PSID",
            value="test_value",
            domain=".google.com",
            path="/",
            expires=1704067200.0,
            http_only=True,
            secure=True,
            same_site="Strict",
        )
        assert cookie.expires == 1704067200.0
        assert cookie.http_only is True
        assert cookie.secure is True
        assert cookie.same_site == "Strict"


class TestAuthStateModel:
    """Tests for the AuthState model."""

    def test_auth_state_is_valid_empty(self) -> None:
        """Empty auth state is invalid."""
        state = AuthState()
        assert state.is_valid() is False

    def test_auth_state_is_valid_missing_cookies(self) -> None:
        """Auth state without required cookies is invalid."""
        state = AuthState(
            cookies=[
                Cookie(name="SID", value="v", domain=".google.com"),
                # Missing HSID and SSID
            ]
        )
        assert state.is_valid() is False
