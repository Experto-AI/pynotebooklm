"""
Pydantic models for PyNotebookLM.

This module contains all the data models used throughout the library
for representing notebooks, sources, artifacts, and API requests/responses.
"""

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field

# =============================================================================
# Enums
# =============================================================================


class SourceType(str, Enum):
    """Types of sources that can be added to a notebook."""

    URL = "url"
    YOUTUBE = "youtube"
    DRIVE = "drive"
    TEXT = "text"


class SourceStatus(str, Enum):
    """Processing status of a source."""

    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


class ArtifactType(str, Enum):
    """Types of content artifacts that can be generated."""

    AUDIO = "audio"
    VIDEO = "video"
    INFOGRAPHIC = "infographic"
    SLIDES = "slides"
    MINDMAP = "mindmap"
    FLASHCARDS = "flashcards"
    BRIEFING = "briefing"
    QUIZ = "quiz"
    DATA_TABLE = "data_table"


class ArtifactStatus(str, Enum):
    """Generation status of an artifact."""

    PENDING = "pending"
    GENERATING = "generating"
    READY = "ready"
    FAILED = "failed"


class PodcastStyle(str, Enum):
    """Available podcast generation styles."""

    DEEP_DIVE = "deep_dive"
    BRIEFING = "briefing"
    LEARNING_GUIDE = "learning_guide"


class ChatRole(str, Enum):
    """Roles in a chat conversation."""

    USER = "user"
    ASSISTANT = "assistant"


# =============================================================================
# Core Models
# =============================================================================


class Source(BaseModel):
    """
    Represents a source document in a notebook.

    Attributes:
        id: Unique identifier for the source.
        type: Type of source (url, youtube, drive, text).
        title: Display title of the source.
        url: Original URL for URL/YouTube sources.
        status: Processing status.
        created_at: When the source was added.
        is_fresh: For Drive sources, whether content is up-to-date.
        source_type_code: Internal numeric type code for debugging.
    """

    id: str = Field(..., description="Unique source identifier")
    type: SourceType = Field(..., description="Source type")
    title: str = Field(..., description="Source title")
    url: str | None = Field(None, description="Source URL (for url/youtube types)")
    status: SourceStatus = Field(
        SourceStatus.PROCESSING, description="Processing status"
    )
    created_at: datetime | None = Field(None, description="Creation timestamp")
    is_fresh: bool | None = Field(
        None, description="For Drive sources, whether content is up-to-date"
    )
    source_type_code: int | None = Field(
        None, description="Internal numeric type code for debugging"
    )

    model_config = {"frozen": False}


class Notebook(BaseModel):
    """
    Represents a NotebookLM notebook.

    Attributes:
        id: Unique identifier for the notebook.
        name: Display name of the notebook.
        created_at: When the notebook was created.
        updated_at: When the notebook was last modified.
        sources: List of sources in the notebook.
        source_count: Number of sources.
    """

    id: str = Field(..., description="Unique notebook identifier")
    name: str = Field(..., description="Notebook name")
    created_at: datetime | None = Field(None, description="Creation timestamp")
    updated_at: datetime | None = Field(None, description="Last update timestamp")
    sources: list[Source] = Field(default_factory=list, description="Notebook sources")
    source_count: int = Field(0, description="Number of sources")

    model_config = {"frozen": False}


class Artifact(BaseModel):
    """
    Represents a generated content artifact (podcast, video, etc.).

    Attributes:
        id: Unique identifier for the artifact.
        type: Type of artifact.
        status: Generation status.
        url: Download URL when ready.
        progress: Generation progress (0.0 to 1.0).
        error_message: Error message if generation failed.
        created_at: When generation was started.
    """

    id: str = Field(..., description="Unique artifact identifier")
    type: ArtifactType = Field(..., description="Artifact type")
    status: ArtifactStatus = Field(
        ArtifactStatus.PENDING, description="Generation status"
    )
    url: str | None = Field(None, description="Download URL when ready")
    progress: float = Field(0.0, ge=0.0, le=1.0, description="Progress (0.0-1.0)")
    error_message: str | None = Field(None, description="Error message if failed")
    created_at: datetime | None = Field(None, description="Creation timestamp")

    model_config = {"frozen": False}


class ChatMessage(BaseModel):
    """
    Represents a message in a notebook chat conversation.

    Attributes:
        role: Message role (user or assistant).
        content: Message content.
        citations: Source citations in the response.
        created_at: Message timestamp.
    """

    role: ChatRole = Field(..., description="Message role")
    content: str = Field(..., description="Message content")
    citations: list[str] = Field(default_factory=list, description="Source citations")
    created_at: datetime | None = Field(None, description="Message timestamp")

    model_config = {"frozen": False}


# =============================================================================
# Request/Response Models
# =============================================================================


class CreateNotebookRequest(BaseModel):
    """Request model for creating a notebook."""

    name: str = Field(..., min_length=1, max_length=200, description="Notebook name")


class CreateNotebookResponse(BaseModel):
    """Response model for notebook creation."""

    notebook: Notebook = Field(..., description="Created notebook")


class AddSourceRequest(BaseModel):
    """Request model for adding a source to a notebook."""

    notebook_id: str = Field(..., description="Target notebook ID")
    source_type: SourceType = Field(..., description="Source type")
    url: str | None = Field(None, description="URL for url/youtube sources")
    content: str | None = Field(None, description="Content for text sources")
    title: str | None = Field(None, description="Optional title for text sources")
    drive_doc_id: str | None = Field(None, description="Google Drive document ID")


class AddSourceResponse(BaseModel):
    """Response model for source addition."""

    source: Source = Field(..., description="Added source")


class GeneratePodcastRequest(BaseModel):
    """Request model for podcast generation."""

    notebook_id: str = Field(..., description="Notebook ID")
    style: PodcastStyle = Field(PodcastStyle.DEEP_DIVE, description="Podcast style")
    timeout: int = Field(300, ge=60, le=600, description="Timeout in seconds")


class GeneratePodcastResponse(BaseModel):
    """Response model for podcast generation."""

    artifact: Artifact = Field(..., description="Generated artifact")


class QueryNotebookRequest(BaseModel):
    """Request model for querying a notebook."""

    notebook_id: str = Field(..., description="Notebook ID")
    question: str = Field(..., min_length=1, description="Question to ask")
    conversation_id: str | None = Field(
        None, description="Conversation ID for multi-turn chat"
    )


class QueryNotebookResponse(BaseModel):
    """Response model for notebook query."""

    message: ChatMessage = Field(..., description="AI response")
    conversation_id: str = Field(..., description="Conversation ID")


# =============================================================================
# Authentication Models
# =============================================================================


class Cookie(BaseModel):
    """Represents a browser cookie."""

    name: str = Field(..., description="Cookie name")
    value: str = Field(..., description="Cookie value")
    domain: str = Field(..., description="Cookie domain")
    path: str = Field("/", description="Cookie path")
    expires: float | None = Field(None, description="Expiration timestamp")
    http_only: bool = Field(False, description="HTTP only flag")
    secure: bool = Field(False, description="Secure flag")
    same_site: Literal["Strict", "Lax", "None"] = Field(
        "Lax", description="SameSite attribute"
    )


class AuthState(BaseModel):
    """
    Persistent authentication state.

    Stored in ~/.pynotebooklm/auth.json
    """

    cookies: list[Cookie] = Field(default_factory=list, description="Browser cookies")
    csrf_token: str | None = Field(None, description="CSRF token (SNlM0e)")
    authenticated_at: datetime | None = Field(
        None, description="When authentication occurred"
    )
    expires_at: datetime | None = Field(None, description="Estimated expiration time")

    def is_valid(self) -> bool:
        """Check if the authentication state appears valid."""
        if not self.cookies:
            return False

        # Check for essential cookies
        cookie_names = {c.name for c in self.cookies}
        required_cookies = {"SID", "HSID", "SSID"}
        if not required_cookies.issubset(cookie_names):
            return False

        # Check expiration
        if self.expires_at and datetime.now() > self.expires_at:
            return False

        return True
