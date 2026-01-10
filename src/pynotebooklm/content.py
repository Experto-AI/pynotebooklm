"""
Content generation module for PyNotebookLM.

This module provides the ContentGenerator class for creating multi-modal
content from notebook sources: audio overviews, video overviews, infographics,
and slide decks.
"""

import logging
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from .exceptions import APIError, GenerationError
from .session import BrowserSession

logger = logging.getLogger(__name__)

# RPC IDs for Studio operations
RPC_CREATE_STUDIO = "R7cb6c"
RPC_POLL_STUDIO = "gArtLc"
RPC_DELETE_STUDIO = "V5N4be"

# Studio content type codes
STUDIO_TYPE_AUDIO = 1
STUDIO_TYPE_VIDEO = 3
STUDIO_TYPE_INFOGRAPHIC = 7
STUDIO_TYPE_SLIDE_DECK = 8

# Status codes
STATUS_IN_PROGRESS = 1
STATUS_COMPLETED = 3


# =============================================================================
# Enums for Content Options
# =============================================================================


class AudioFormat(str, Enum):
    """Audio overview format options."""

    DEEP_DIVE = "deep_dive"  # Code 1
    BRIEF = "brief"  # Code 2
    CRITIQUE = "critique"  # Code 3
    DEBATE = "debate"  # Code 4


class AudioLength(str, Enum):
    """Audio overview length options."""

    SHORT = "short"  # Code 1
    DEFAULT = "default"  # Code 2
    LONG = "long"  # Code 3


class VideoFormat(str, Enum):
    """Video overview format options."""

    EXPLAINER = "explainer"  # Code 1
    BRIEF = "brief"  # Code 2


class VideoStyle(str, Enum):
    """Video overview visual style options."""

    AUTO_SELECT = "auto_select"  # Code 1
    CUSTOM = "custom"  # Code 2
    CLASSIC = "classic"  # Code 3
    WHITEBOARD = "whiteboard"  # Code 4
    KAWAII = "kawaii"  # Code 5
    ANIME = "anime"  # Code 6
    WATERCOLOR = "watercolor"  # Code 7
    RETRO_PRINT = "retro_print"  # Code 8
    HERITAGE = "heritage"  # Code 9
    PAPER_CRAFT = "paper_craft"  # Code 10


class InfographicOrientation(str, Enum):
    """Infographic orientation options."""

    LANDSCAPE = "landscape"  # Code 1 - 16:9
    PORTRAIT = "portrait"  # Code 2 - 9:16
    SQUARE = "square"  # Code 3 - 1:1


class InfographicDetailLevel(str, Enum):
    """Infographic detail level options."""

    CONCISE = "concise"  # Code 1
    STANDARD = "standard"  # Code 2
    DETAILED = "detailed"  # Code 3


class SlideDeckFormat(str, Enum):
    """Slide deck format options."""

    DETAILED_DECK = "detailed_deck"  # Code 1
    PRESENTER_SLIDES = "presenter_slides"  # Code 2


class SlideDeckLength(str, Enum):
    """Slide deck length options."""

    SHORT = "short"  # Code 1
    DEFAULT = "default"  # Code 3


class StudioArtifactType(str, Enum):
    """Types of studio artifacts."""

    AUDIO = "audio"
    VIDEO = "video"
    INFOGRAPHIC = "infographic"
    SLIDE_DECK = "slide_deck"
    REPORT = "report"
    FLASHCARDS = "flashcards"
    DATA_TABLE = "data_table"
    UNKNOWN = "unknown"


class StudioArtifactStatus(str, Enum):
    """Status of studio artifacts."""

    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    UNKNOWN = "unknown"


# =============================================================================
# Pydantic Models for Content Generation
# =============================================================================


class StudioArtifact(BaseModel):
    """Represents a studio artifact (audio, video, infographic, slide deck)."""

    artifact_id: str = Field(..., description="Unique artifact identifier")
    notebook_id: str = Field(..., description="Parent notebook ID")
    title: str = Field("", description="Artifact title")
    artifact_type: StudioArtifactType = Field(..., description="Type of artifact")
    status: StudioArtifactStatus = Field(..., description="Generation status")
    created_at: str | None = Field(None, description="ISO timestamp when created")

    # Type-specific URLs
    audio_url: str | None = Field(None, description="Audio download URL")
    video_url: str | None = Field(None, description="Video download URL")
    infographic_url: str | None = Field(None, description="Infographic image URL")
    slide_deck_url: str | None = Field(None, description="Slide deck download URL")

    # Additional metadata
    duration_seconds: int | None = Field(None, description="Audio duration in seconds")
    report_content: str | None = Field(None, description="Report markdown content")
    flashcard_count: int | None = Field(None, description="Number of flashcards")

    model_config = {"frozen": False}


class CreateContentResult(BaseModel):
    """Result from creating studio content."""

    artifact_id: str = Field(..., description="Created artifact ID")
    notebook_id: str = Field(..., description="Notebook ID")
    content_type: str = Field(..., description="Content type (audio, video, etc.)")
    status: str = Field(..., description="Initial status (usually in_progress)")

    # Type-specific options
    format: str | None = Field(None, description="Format option selected")
    length: str | None = Field(None, description="Length option selected")
    style: str | None = Field(None, description="Style option selected")
    orientation: str | None = Field(None, description="Orientation selected")
    detail_level: str | None = Field(None, description="Detail level selected")
    language: str = Field("en", description="Language code")

    model_config = {"frozen": False}


# =============================================================================
# Mapping Functions
# =============================================================================


def _audio_format_to_code(fmt: AudioFormat) -> int:
    """Convert AudioFormat enum to RPC code."""
    mapping = {
        AudioFormat.DEEP_DIVE: 1,
        AudioFormat.BRIEF: 2,
        AudioFormat.CRITIQUE: 3,
        AudioFormat.DEBATE: 4,
    }
    return mapping.get(fmt, 1)


def _audio_length_to_code(length: AudioLength) -> int:
    """Convert AudioLength enum to RPC code."""
    mapping = {
        AudioLength.SHORT: 1,
        AudioLength.DEFAULT: 2,
        AudioLength.LONG: 3,
    }
    return mapping.get(length, 2)


def _video_format_to_code(fmt: VideoFormat) -> int:
    """Convert VideoFormat enum to RPC code."""
    mapping = {
        VideoFormat.EXPLAINER: 1,
        VideoFormat.BRIEF: 2,
    }
    return mapping.get(fmt, 1)


def _video_style_to_code(style: VideoStyle) -> int:
    """Convert VideoStyle enum to RPC code."""
    mapping = {
        VideoStyle.AUTO_SELECT: 1,
        VideoStyle.CUSTOM: 2,
        VideoStyle.CLASSIC: 3,
        VideoStyle.WHITEBOARD: 4,
        VideoStyle.KAWAII: 5,
        VideoStyle.ANIME: 6,
        VideoStyle.WATERCOLOR: 7,
        VideoStyle.RETRO_PRINT: 8,
        VideoStyle.HERITAGE: 9,
        VideoStyle.PAPER_CRAFT: 10,
    }
    return mapping.get(style, 1)


def _infographic_orientation_to_code(orientation: InfographicOrientation) -> int:
    """Convert InfographicOrientation enum to RPC code."""
    mapping = {
        InfographicOrientation.LANDSCAPE: 1,
        InfographicOrientation.PORTRAIT: 2,
        InfographicOrientation.SQUARE: 3,
    }
    return mapping.get(orientation, 1)


def _infographic_detail_to_code(detail: InfographicDetailLevel) -> int:
    """Convert InfographicDetailLevel enum to RPC code."""
    mapping = {
        InfographicDetailLevel.CONCISE: 1,
        InfographicDetailLevel.STANDARD: 2,
        InfographicDetailLevel.DETAILED: 3,
    }
    return mapping.get(detail, 2)


def _slide_format_to_code(fmt: SlideDeckFormat) -> int:
    """Convert SlideDeckFormat enum to RPC code."""
    mapping = {
        SlideDeckFormat.DETAILED_DECK: 1,
        SlideDeckFormat.PRESENTER_SLIDES: 2,
    }
    return mapping.get(fmt, 1)


def _slide_length_to_code(length: SlideDeckLength) -> int:
    """Convert SlideDeckLength enum to RPC code."""
    mapping = {
        SlideDeckLength.SHORT: 1,
        SlideDeckLength.DEFAULT: 3,
    }
    return mapping.get(length, 3)


def _code_to_audio_format(code: int) -> str:
    """Convert RPC code to audio format name."""
    mapping = {1: "deep_dive", 2: "brief", 3: "critique", 4: "debate"}
    return mapping.get(code, "unknown")


def _code_to_audio_length(code: int) -> str:
    """Convert RPC code to audio length name."""
    mapping = {1: "short", 2: "default", 3: "long"}
    return mapping.get(code, "unknown")


def _code_to_video_format(code: int) -> str:
    """Convert RPC code to video format name."""
    mapping = {1: "explainer", 2: "brief"}
    return mapping.get(code, "unknown")


def _code_to_video_style(code: int) -> str:
    """Convert RPC code to video style name."""
    mapping = {
        1: "auto_select",
        2: "custom",
        3: "classic",
        4: "whiteboard",
        5: "kawaii",
        6: "anime",
        7: "watercolor",
        8: "retro_print",
        9: "heritage",
        10: "paper_craft",
    }
    return mapping.get(code, "unknown")


def _type_code_to_artifact_type(code: int) -> StudioArtifactType:
    """Convert RPC type code to StudioArtifactType enum."""
    mapping = {
        1: StudioArtifactType.AUDIO,
        2: StudioArtifactType.REPORT,
        3: StudioArtifactType.VIDEO,
        4: StudioArtifactType.FLASHCARDS,
        7: StudioArtifactType.INFOGRAPHIC,
        8: StudioArtifactType.SLIDE_DECK,
        9: StudioArtifactType.DATA_TABLE,
    }
    return mapping.get(code, StudioArtifactType.UNKNOWN)


def _status_code_to_status(code: int) -> StudioArtifactStatus:
    """Convert RPC status code to StudioArtifactStatus enum."""
    if code == STATUS_IN_PROGRESS:
        return StudioArtifactStatus.IN_PROGRESS
    elif code == STATUS_COMPLETED:
        return StudioArtifactStatus.COMPLETED
    return StudioArtifactStatus.UNKNOWN


# =============================================================================
# ContentGenerator Class
# =============================================================================


class ContentGenerator:
    """
    Generator for multi-modal content from notebook sources.

    This class provides methods to create audio overviews (podcasts),
    video overviews, infographics, and slide decks from notebook sources.

    Example:
        ```python
        async with BrowserSession(auth) as session:
            generator = ContentGenerator(session)

            # Create an audio overview
            result = await generator.create_audio(
                notebook_id="abc-123",
                source_ids=["src-1", "src-2"],
                format=AudioFormat.DEEP_DIVE,
                length=AudioLength.DEFAULT,
            )

            # Poll for status
            artifacts = await generator.poll_status(notebook_id)
            for artifact in artifacts:
                print(f"{artifact.title}: {artifact.status}")
        ```
    """

    def __init__(self, session: BrowserSession):
        """
        Initialize the ContentGenerator.

        Args:
            session: Active BrowserSession instance.
        """
        self._session = session

    async def create_audio(
        self,
        notebook_id: str,
        source_ids: list[str],
        format: AudioFormat = AudioFormat.DEEP_DIVE,
        length: AudioLength = AudioLength.DEFAULT,
        language: str = "en",
        focus_prompt: str = "",
    ) -> CreateContentResult:
        """
        Create an audio overview (podcast) from notebook sources.

        Args:
            notebook_id: Notebook UUID.
            source_ids: List of source IDs to include.
            format: Audio format (deep_dive, brief, critique, debate).
            length: Audio length (short, default, long).
            language: BCP-47 language code (e.g., "en", "es").
            focus_prompt: Optional focus instructions for the AI.

        Returns:
            CreateContentResult with artifact_id and initial status.

        Raises:
            GenerationError: If audio creation fails.
            APIError: If the API call fails.
        """
        if not source_ids:
            raise GenerationError("At least one source ID is required")

        format_code = _audio_format_to_code(format)
        length_code = _audio_length_to_code(length)

        # Build source IDs in nested format: [[[id1]], [[id2]], ...]
        sources_nested = [[[sid]] for sid in source_ids]
        # Build source IDs in simple format: [[id1], [id2], ...]
        sources_simple = [[sid] for sid in source_ids]

        # Audio options structure
        audio_options = [
            None,
            [
                focus_prompt,
                length_code,
                None,
                sources_simple,
                language,
                None,
                format_code,
            ],
        ]

        params = [
            [2],
            notebook_id,
            [
                None,
                None,
                STUDIO_TYPE_AUDIO,
                sources_nested,
                None,
                None,
                audio_options,
            ],
        ]

        try:
            result = await self._session.call_rpc(RPC_CREATE_STUDIO, params)
        except Exception as e:
            raise GenerationError(f"Failed to create audio overview: {e}") from e

        return self._parse_create_result(
            result,
            notebook_id,
            "audio",
            format=format.value,
            length=length.value,
            language=language,
        )

    async def create_video(
        self,
        notebook_id: str,
        source_ids: list[str],
        format: VideoFormat = VideoFormat.EXPLAINER,
        style: VideoStyle = VideoStyle.AUTO_SELECT,
        language: str = "en",
        focus_prompt: str = "",
    ) -> CreateContentResult:
        """
        Create a video overview from notebook sources.

        Args:
            notebook_id: Notebook UUID.
            source_ids: List of source IDs to include.
            format: Video format (explainer, brief).
            style: Visual style (auto_select, classic, whiteboard, etc.).
            language: BCP-47 language code.
            focus_prompt: Optional focus instructions for the AI.

        Returns:
            CreateContentResult with artifact_id and initial status.

        Raises:
            GenerationError: If video creation fails.
            APIError: If the API call fails.
        """
        if not source_ids:
            raise GenerationError("At least one source ID is required")

        format_code = _video_format_to_code(format)
        style_code = _video_style_to_code(style)

        # Build source IDs
        sources_nested = [[[sid]] for sid in source_ids]
        sources_simple = [[sid] for sid in source_ids]

        # Video options structure
        video_options = [
            None,
            None,
            [
                sources_simple,
                language,
                focus_prompt,
                None,
                format_code,
                style_code,
            ],
        ]

        params = [
            [2],
            notebook_id,
            [
                None,
                None,
                STUDIO_TYPE_VIDEO,
                sources_nested,
                None,
                None,
                None,
                None,
                video_options,
            ],
        ]

        try:
            result = await self._session.call_rpc(RPC_CREATE_STUDIO, params)
        except Exception as e:
            raise GenerationError(f"Failed to create video overview: {e}") from e

        return self._parse_create_result(
            result,
            notebook_id,
            "video",
            format=format.value,
            style=style.value,
            language=language,
        )

    async def create_infographic(
        self,
        notebook_id: str,
        source_ids: list[str],
        orientation: InfographicOrientation = InfographicOrientation.LANDSCAPE,
        detail_level: InfographicDetailLevel = InfographicDetailLevel.STANDARD,
        language: str = "en",
        focus_prompt: str = "",
    ) -> CreateContentResult:
        """
        Create an infographic from notebook sources.

        Args:
            notebook_id: Notebook UUID.
            source_ids: List of source IDs to include.
            orientation: Infographic orientation (landscape, portrait, square).
            detail_level: Detail level (concise, standard, detailed).
            language: BCP-47 language code.
            focus_prompt: Optional focus instructions for the AI.

        Returns:
            CreateContentResult with artifact_id and initial status.

        Raises:
            GenerationError: If infographic creation fails.
            APIError: If the API call fails.
        """
        if not source_ids:
            raise GenerationError("At least one source ID is required")

        orientation_code = _infographic_orientation_to_code(orientation)
        detail_code = _infographic_detail_to_code(detail_level)

        # Build source IDs
        sources_nested = [[[sid]] for sid in source_ids]

        # Infographic options at position 14
        infographic_options = [
            [focus_prompt or None, language, None, orientation_code, detail_code]
        ]

        # Build content array with 10 nulls before options
        content = [
            None,
            None,
            STUDIO_TYPE_INFOGRAPHIC,
            sources_nested,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,  # positions 4-13
            infographic_options,  # position 14
        ]

        params = [[2], notebook_id, content]

        try:
            result = await self._session.call_rpc(RPC_CREATE_STUDIO, params)
        except Exception as e:
            raise GenerationError(f"Failed to create infographic: {e}") from e

        return self._parse_create_result(
            result,
            notebook_id,
            "infographic",
            orientation=orientation.value,
            detail_level=detail_level.value,
            language=language,
        )

    async def create_slides(
        self,
        notebook_id: str,
        source_ids: list[str],
        format: SlideDeckFormat = SlideDeckFormat.DETAILED_DECK,
        length: SlideDeckLength = SlideDeckLength.DEFAULT,
        language: str = "en",
        focus_prompt: str = "",
    ) -> CreateContentResult:
        """
        Create a slide deck from notebook sources.

        Args:
            notebook_id: Notebook UUID.
            source_ids: List of source IDs to include.
            format: Slide deck format (detailed_deck, presenter_slides).
            length: Slide deck length (short, default).
            language: BCP-47 language code.
            focus_prompt: Optional focus instructions for the AI.

        Returns:
            CreateContentResult with artifact_id and initial status.

        Raises:
            GenerationError: If slide deck creation fails.
            APIError: If the API call fails.
        """
        if not source_ids:
            raise GenerationError("At least one source ID is required")

        format_code = _slide_format_to_code(format)
        length_code = _slide_length_to_code(length)

        # Build source IDs
        sources_nested = [[[sid]] for sid in source_ids]

        # Slide deck options at position 16
        slide_deck_options = [
            [focus_prompt or None, language, format_code, length_code]
        ]

        # Build content array with 12 nulls before options
        content = [
            None,
            None,
            STUDIO_TYPE_SLIDE_DECK,
            sources_nested,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,  # positions 4-15
            slide_deck_options,  # position 16
        ]

        params = [[2], notebook_id, content]

        try:
            result = await self._session.call_rpc(RPC_CREATE_STUDIO, params)
        except Exception as e:
            raise GenerationError(f"Failed to create slide deck: {e}") from e

        return self._parse_create_result(
            result,
            notebook_id,
            "slide_deck",
            format=format.value,
            length=length.value,
            language=language,
        )

    async def poll_status(self, notebook_id: str) -> list[StudioArtifact]:
        """
        Poll for studio content status.

        Returns all artifacts in the notebook with their current status
        and download URLs if completed.

        Args:
            notebook_id: Notebook UUID.

        Returns:
            List of StudioArtifact objects with current status.

        Raises:
            APIError: If the API call fails.
        """
        params = [[2], notebook_id, 'NOT artifact.status = "ARTIFACT_STATUS_SUGGESTED"']

        try:
            result = await self._session.call_rpc(RPC_POLL_STUDIO, params)
        except Exception as e:
            raise APIError(f"Failed to poll studio status: {e}") from e

        return self._parse_poll_result(result, notebook_id)

    async def delete(self, artifact_id: str) -> bool:
        """
        Delete a studio artifact.

        WARNING: This action is IRREVERSIBLE.

        Args:
            artifact_id: Artifact UUID to delete.

        Returns:
            True if deletion was successful.

        Raises:
            APIError: If the deletion fails.
        """
        params = [[2], artifact_id]

        try:
            result = await self._session.call_rpc(RPC_DELETE_STUDIO, params)
            return result is not None
        except Exception as e:
            raise APIError(f"Failed to delete artifact: {e}") from e

    def _parse_create_result(
        self,
        result: Any,
        notebook_id: str,
        content_type: str,
        **kwargs: Any,
    ) -> CreateContentResult:
        """Parse the result from a create content RPC call."""
        if not result or not isinstance(result, list) or len(result) == 0:
            raise GenerationError(f"Invalid response when creating {content_type}")

        artifact_data = result[0]
        if not isinstance(artifact_data, list) or len(artifact_data) == 0:
            raise GenerationError(f"Invalid artifact data when creating {content_type}")

        artifact_id = artifact_data[0]
        status_code = artifact_data[4] if len(artifact_data) > 4 else None

        if status_code == STATUS_IN_PROGRESS:
            status = "in_progress"
        elif status_code == STATUS_COMPLETED:
            status = "completed"
        else:
            status = "unknown"

        return CreateContentResult(
            artifact_id=artifact_id,
            notebook_id=notebook_id,
            content_type=content_type,
            status=status,
            **kwargs,
        )

    def _parse_poll_result(self, result: Any, notebook_id: str) -> list[StudioArtifact]:
        """Parse the result from a poll status RPC call."""
        artifacts: list[StudioArtifact] = []

        if not result or not isinstance(result, list) or len(result) == 0:
            return artifacts

        # Response is an array of artifacts, possibly wrapped
        artifact_list = result[0] if isinstance(result[0], list) else result

        for artifact_data in artifact_list:
            if not isinstance(artifact_data, list) or len(artifact_data) < 5:
                continue

            artifact_id = artifact_data[0]
            title = artifact_data[1] if len(artifact_data) > 1 else ""
            type_code: int = artifact_data[2] if len(artifact_data) > 2 else 0
            status_code: int = artifact_data[4] if len(artifact_data) > 4 else 0

            artifact_type = _type_code_to_artifact_type(type_code)
            status = _status_code_to_status(status_code)

            # Extract type-specific URLs
            audio_url = None
            video_url = None
            infographic_url = None
            slide_deck_url = None
            duration_seconds = None
            report_content = None
            flashcard_count = None
            created_at = None

            # Audio artifacts have URLs at position 6
            if type_code == STUDIO_TYPE_AUDIO and len(artifact_data) > 6:
                audio_options = artifact_data[6]
                if isinstance(audio_options, list) and len(audio_options) > 3:
                    audio_url = (
                        audio_options[3] if isinstance(audio_options[3], str) else None
                    )
                    if len(audio_options) > 9 and isinstance(audio_options[9], list):
                        duration_seconds = (
                            audio_options[9][0] if audio_options[9] else None
                        )

            # Video artifacts have URLs at position 8
            if type_code == STUDIO_TYPE_VIDEO and len(artifact_data) > 8:
                video_options = artifact_data[8]
                if isinstance(video_options, list) and len(video_options) > 3:
                    video_url = (
                        video_options[3] if isinstance(video_options[3], str) else None
                    )

            # Infographic artifacts have image URL at position 14
            if type_code == STUDIO_TYPE_INFOGRAPHIC and len(artifact_data) > 14:
                infographic_options = artifact_data[14]
                if (
                    isinstance(infographic_options, list)
                    and len(infographic_options) > 2
                ):
                    image_data = infographic_options[2]
                    if isinstance(image_data, list) and len(image_data) > 0:
                        first_image = image_data[0]
                        if isinstance(first_image, list) and len(first_image) > 1:
                            image_details = first_image[1]
                            if (
                                isinstance(image_details, list)
                                and len(image_details) > 0
                            ):
                                url = image_details[0]
                                if isinstance(url, str) and url.startswith("http"):
                                    infographic_url = url

            # Slide deck artifacts have download URL at position 16
            if type_code == STUDIO_TYPE_SLIDE_DECK and len(artifact_data) > 16:
                slide_deck_options = artifact_data[16]
                if isinstance(slide_deck_options, list) and len(slide_deck_options) > 0:
                    if isinstance(slide_deck_options[0], str) and slide_deck_options[
                        0
                    ].startswith("http"):
                        slide_deck_url = slide_deck_options[0]
                    elif len(slide_deck_options) > 3 and isinstance(
                        slide_deck_options[3], str
                    ):
                        slide_deck_url = slide_deck_options[3]

            # Extract created_at timestamp from common positions
            for ts_pos in [10, 15, 17]:
                if len(artifact_data) > ts_pos:
                    ts_candidate = artifact_data[ts_pos]
                    if isinstance(ts_candidate, list) and len(ts_candidate) >= 2:
                        if (
                            isinstance(ts_candidate[0], int | float)
                            and ts_candidate[0] > 1700000000
                        ):
                            from datetime import datetime, timezone

                            dt = datetime.fromtimestamp(
                                ts_candidate[0], tz=timezone.utc
                            )
                            created_at = dt.strftime("%Y-%m-%dT%H:%M:%SZ")
                            break

            artifacts.append(
                StudioArtifact(
                    artifact_id=artifact_id,
                    notebook_id=notebook_id,
                    title=title,
                    artifact_type=artifact_type,
                    status=status,
                    created_at=created_at,
                    audio_url=audio_url,
                    video_url=video_url,
                    infographic_url=infographic_url,
                    slide_deck_url=slide_deck_url,
                    duration_seconds=duration_seconds,
                    report_content=report_content,
                    flashcard_count=flashcard_count,
                )
            )

        return artifacts
