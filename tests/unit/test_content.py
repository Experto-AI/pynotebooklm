"""Unit tests for the content generation module."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from pynotebooklm.content import (
    AudioFormat,
    AudioLength,
    ContentGenerator,
    CreateContentResult,
    InfographicDetailLevel,
    InfographicOrientation,
    SlideDeckFormat,
    SlideDeckLength,
    StudioArtifact,
    StudioArtifactStatus,
    StudioArtifactType,
    VideoFormat,
    VideoStyle,
    _audio_format_to_code,
    _audio_length_to_code,
    _code_to_audio_format,
    _code_to_audio_length,
    _code_to_video_format,
    _code_to_video_style,
    _infographic_detail_to_code,
    _infographic_orientation_to_code,
    _slide_format_to_code,
    _slide_length_to_code,
    _status_code_to_status,
    _type_code_to_artifact_type,
    _video_format_to_code,
    _video_style_to_code,
)
from pynotebooklm.exceptions import APIError, GenerationError

# =============================================================================
# Enum Mapping Tests
# =============================================================================


class TestAudioFormatMapping:
    """Tests for audio format enum mappings."""

    def test_audio_format_to_code_deep_dive(self) -> None:
        assert _audio_format_to_code(AudioFormat.DEEP_DIVE) == 1

    def test_audio_format_to_code_brief(self) -> None:
        assert _audio_format_to_code(AudioFormat.BRIEF) == 2

    def test_audio_format_to_code_critique(self) -> None:
        assert _audio_format_to_code(AudioFormat.CRITIQUE) == 3

    def test_audio_format_to_code_debate(self) -> None:
        assert _audio_format_to_code(AudioFormat.DEBATE) == 4

    def test_code_to_audio_format(self) -> None:
        assert _code_to_audio_format(1) == "deep_dive"
        assert _code_to_audio_format(2) == "brief"
        assert _code_to_audio_format(3) == "critique"
        assert _code_to_audio_format(4) == "debate"
        assert _code_to_audio_format(99) == "unknown"


class TestAudioLengthMapping:
    """Tests for audio length enum mappings."""

    def test_audio_length_to_code_short(self) -> None:
        assert _audio_length_to_code(AudioLength.SHORT) == 1

    def test_audio_length_to_code_default(self) -> None:
        assert _audio_length_to_code(AudioLength.DEFAULT) == 2

    def test_audio_length_to_code_long(self) -> None:
        assert _audio_length_to_code(AudioLength.LONG) == 3

    def test_code_to_audio_length(self) -> None:
        assert _code_to_audio_length(1) == "short"
        assert _code_to_audio_length(2) == "default"
        assert _code_to_audio_length(3) == "long"
        assert _code_to_audio_length(99) == "unknown"


class TestVideoFormatMapping:
    """Tests for video format enum mappings."""

    def test_video_format_to_code_explainer(self) -> None:
        assert _video_format_to_code(VideoFormat.EXPLAINER) == 1

    def test_video_format_to_code_brief(self) -> None:
        assert _video_format_to_code(VideoFormat.BRIEF) == 2

    def test_code_to_video_format(self) -> None:
        assert _code_to_video_format(1) == "explainer"
        assert _code_to_video_format(2) == "brief"
        assert _code_to_video_format(99) == "unknown"


class TestVideoStyleMapping:
    """Tests for video style enum mappings."""

    def test_video_style_to_code_all_styles(self) -> None:
        assert _video_style_to_code(VideoStyle.AUTO_SELECT) == 1
        assert _video_style_to_code(VideoStyle.CUSTOM) == 2
        assert _video_style_to_code(VideoStyle.CLASSIC) == 3
        assert _video_style_to_code(VideoStyle.WHITEBOARD) == 4
        assert _video_style_to_code(VideoStyle.KAWAII) == 5
        assert _video_style_to_code(VideoStyle.ANIME) == 6
        assert _video_style_to_code(VideoStyle.WATERCOLOR) == 7
        assert _video_style_to_code(VideoStyle.RETRO_PRINT) == 8
        assert _video_style_to_code(VideoStyle.HERITAGE) == 9
        assert _video_style_to_code(VideoStyle.PAPER_CRAFT) == 10

    def test_code_to_video_style(self) -> None:
        assert _code_to_video_style(1) == "auto_select"
        assert _code_to_video_style(3) == "classic"
        assert _code_to_video_style(10) == "paper_craft"
        assert _code_to_video_style(99) == "unknown"


class TestInfographicMapping:
    """Tests for infographic enum mappings."""

    def test_orientation_to_code(self) -> None:
        assert _infographic_orientation_to_code(InfographicOrientation.LANDSCAPE) == 1
        assert _infographic_orientation_to_code(InfographicOrientation.PORTRAIT) == 2
        assert _infographic_orientation_to_code(InfographicOrientation.SQUARE) == 3

    def test_detail_to_code(self) -> None:
        assert _infographic_detail_to_code(InfographicDetailLevel.CONCISE) == 1
        assert _infographic_detail_to_code(InfographicDetailLevel.STANDARD) == 2
        assert _infographic_detail_to_code(InfographicDetailLevel.DETAILED) == 3


class TestSlideDeckMapping:
    """Tests for slide deck enum mappings."""

    def test_format_to_code(self) -> None:
        assert _slide_format_to_code(SlideDeckFormat.DETAILED_DECK) == 1
        assert _slide_format_to_code(SlideDeckFormat.PRESENTER_SLIDES) == 2

    def test_length_to_code(self) -> None:
        assert _slide_length_to_code(SlideDeckLength.SHORT) == 1
        assert _slide_length_to_code(SlideDeckLength.DEFAULT) == 3


class TestTypeCodeMapping:
    """Tests for studio artifact type code mappings."""

    def test_type_code_to_artifact_type(self) -> None:
        assert _type_code_to_artifact_type(1) == StudioArtifactType.AUDIO
        assert _type_code_to_artifact_type(2) == StudioArtifactType.REPORT
        assert _type_code_to_artifact_type(3) == StudioArtifactType.VIDEO
        assert _type_code_to_artifact_type(4) == StudioArtifactType.FLASHCARDS
        assert _type_code_to_artifact_type(7) == StudioArtifactType.INFOGRAPHIC
        assert _type_code_to_artifact_type(8) == StudioArtifactType.SLIDE_DECK
        assert _type_code_to_artifact_type(9) == StudioArtifactType.DATA_TABLE
        assert _type_code_to_artifact_type(99) == StudioArtifactType.UNKNOWN


class TestStatusCodeMapping:
    """Tests for status code mappings."""

    def test_status_code_to_status(self) -> None:
        assert _status_code_to_status(1) == StudioArtifactStatus.IN_PROGRESS
        assert _status_code_to_status(3) == StudioArtifactStatus.COMPLETED
        assert _status_code_to_status(99) == StudioArtifactStatus.UNKNOWN


# =============================================================================
# Model Tests
# =============================================================================


class TestStudioArtifactModel:
    """Tests for StudioArtifact Pydantic model."""

    def test_create_studio_artifact_minimal(self) -> None:
        artifact = StudioArtifact(
            artifact_id="test-123",
            notebook_id="nb-456",
            artifact_type=StudioArtifactType.AUDIO,
            status=StudioArtifactStatus.IN_PROGRESS,
        )
        assert artifact.artifact_id == "test-123"
        assert artifact.notebook_id == "nb-456"
        assert artifact.artifact_type == StudioArtifactType.AUDIO
        assert artifact.status == StudioArtifactStatus.IN_PROGRESS

    def test_create_studio_artifact_with_urls(self) -> None:
        artifact = StudioArtifact(
            artifact_id="test-123",
            notebook_id="nb-456",
            artifact_type=StudioArtifactType.AUDIO,
            status=StudioArtifactStatus.COMPLETED,
            audio_url="https://example.com/audio.mp3",
            duration_seconds=300,
        )
        assert artifact.audio_url == "https://example.com/audio.mp3"
        assert artifact.duration_seconds == 300


class TestCreateContentResultModel:
    """Tests for CreateContentResult Pydantic model."""

    def test_create_content_result(self) -> None:
        result = CreateContentResult(
            artifact_id="art-123",
            notebook_id="nb-456",
            content_type="audio",
            status="in_progress",
            format="deep_dive",
            length="default",
            language="en",
        )
        assert result.artifact_id == "art-123"
        assert result.content_type == "audio"
        assert result.format == "deep_dive"


# =============================================================================
# ContentGenerator Tests
# =============================================================================


class TestContentGeneratorInit:
    """Tests for ContentGenerator initialization."""

    def test_init_with_session(self) -> None:
        session = MagicMock()
        generator = ContentGenerator(session)
        assert generator._session == session


class TestCreateAudio:
    """Tests for ContentGenerator.create_audio()."""

    @pytest.mark.asyncio
    async def test_create_audio_success(self) -> None:
        session = MagicMock()
        session.call_rpc = AsyncMock(
            return_value=[["artifact-id-123", "title", 1, None, 1]]
        )

        generator = ContentGenerator(session)
        result = await generator.create_audio(
            notebook_id="nb-123",
            source_ids=["src-1", "src-2"],
            format=AudioFormat.DEEP_DIVE,
            length=AudioLength.DEFAULT,
            language="en",
        )

        assert result.artifact_id == "artifact-id-123"
        assert result.content_type == "audio"
        assert result.status == "in_progress"
        session.call_rpc.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_audio_empty_sources_raises(self) -> None:
        session = MagicMock()
        generator = ContentGenerator(session)

        with pytest.raises(GenerationError, match="At least one source ID is required"):
            await generator.create_audio(
                notebook_id="nb-123", source_ids=[], format=AudioFormat.DEEP_DIVE
            )

    @pytest.mark.asyncio
    async def test_create_audio_rpc_failure_raises(self) -> None:
        session = MagicMock()
        session.call_rpc = AsyncMock(side_effect=Exception("RPC failed"))

        generator = ContentGenerator(session)

        with pytest.raises(GenerationError, match="Failed to create audio"):
            await generator.create_audio(
                notebook_id="nb-123",
                source_ids=["src-1"],
                format=AudioFormat.DEEP_DIVE,
            )


class TestCreateVideo:
    """Tests for ContentGenerator.create_video()."""

    @pytest.mark.asyncio
    async def test_create_video_success(self) -> None:
        session = MagicMock()
        session.call_rpc = AsyncMock(
            return_value=[["video-id-123", "title", 3, None, 1]]
        )

        generator = ContentGenerator(session)
        result = await generator.create_video(
            notebook_id="nb-123",
            source_ids=["src-1"],
            format=VideoFormat.EXPLAINER,
            style=VideoStyle.CLASSIC,
        )

        assert result.artifact_id == "video-id-123"
        assert result.content_type == "video"
        session.call_rpc.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_video_empty_sources_raises(self) -> None:
        session = MagicMock()
        generator = ContentGenerator(session)

        with pytest.raises(GenerationError, match="At least one source ID is required"):
            await generator.create_video(
                notebook_id="nb-123", source_ids=[], format=VideoFormat.EXPLAINER
            )


class TestCreateInfographic:
    """Tests for ContentGenerator.create_infographic()."""

    @pytest.mark.asyncio
    async def test_create_infographic_success(self) -> None:
        session = MagicMock()
        session.call_rpc = AsyncMock(
            return_value=[["infographic-id-123", "title", 7, None, 1]]
        )

        generator = ContentGenerator(session)
        result = await generator.create_infographic(
            notebook_id="nb-123",
            source_ids=["src-1"],
            orientation=InfographicOrientation.LANDSCAPE,
            detail_level=InfographicDetailLevel.STANDARD,
        )

        assert result.artifact_id == "infographic-id-123"
        assert result.content_type == "infographic"
        session.call_rpc.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_infographic_empty_sources_raises(self) -> None:
        session = MagicMock()
        generator = ContentGenerator(session)

        with pytest.raises(GenerationError, match="At least one source ID is required"):
            await generator.create_infographic(notebook_id="nb-123", source_ids=[])


class TestCreateSlides:
    """Tests for ContentGenerator.create_slides()."""

    @pytest.mark.asyncio
    async def test_create_slides_success(self) -> None:
        session = MagicMock()
        session.call_rpc = AsyncMock(
            return_value=[["slides-id-123", "title", 8, None, 1]]
        )

        generator = ContentGenerator(session)
        result = await generator.create_slides(
            notebook_id="nb-123",
            source_ids=["src-1"],
            format=SlideDeckFormat.DETAILED_DECK,
            length=SlideDeckLength.DEFAULT,
        )

        assert result.artifact_id == "slides-id-123"
        assert result.content_type == "slide_deck"
        session.call_rpc.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_slides_empty_sources_raises(self) -> None:
        session = MagicMock()
        generator = ContentGenerator(session)

        with pytest.raises(GenerationError, match="At least one source ID is required"):
            await generator.create_slides(notebook_id="nb-123", source_ids=[])


class TestPollStatus:
    """Tests for ContentGenerator.poll_status()."""

    @pytest.mark.asyncio
    async def test_poll_status_returns_artifacts(self) -> None:
        session = MagicMock()
        session.call_rpc = AsyncMock(
            return_value=[
                [
                    [
                        "art-1",
                        "Audio Overview",
                        1,
                        None,
                        3,
                        None,
                        [None, None, None, "https://audio.url"],
                    ],
                    ["art-2", "Video", 3, None, 1],
                ]
            ]
        )

        generator = ContentGenerator(session)
        artifacts = await generator.poll_status("nb-123")

        assert len(artifacts) == 2
        assert artifacts[0].artifact_id == "art-1"
        assert artifacts[0].artifact_type == StudioArtifactType.AUDIO
        assert artifacts[0].status == StudioArtifactStatus.COMPLETED
        assert artifacts[1].artifact_id == "art-2"
        assert artifacts[1].status == StudioArtifactStatus.IN_PROGRESS

    @pytest.mark.asyncio
    async def test_poll_status_empty_response(self) -> None:
        session = MagicMock()
        session.call_rpc = AsyncMock(return_value=[])

        generator = ContentGenerator(session)
        artifacts = await generator.poll_status("nb-123")

        assert artifacts == []

    @pytest.mark.asyncio
    async def test_poll_status_rpc_failure_raises(self) -> None:
        session = MagicMock()
        session.call_rpc = AsyncMock(side_effect=Exception("RPC failed"))

        generator = ContentGenerator(session)

        with pytest.raises(APIError, match="Failed to poll studio status"):
            await generator.poll_status("nb-123")


class TestDeleteArtifact:
    """Tests for ContentGenerator.delete()."""

    @pytest.mark.asyncio
    async def test_delete_success(self) -> None:
        session = MagicMock()
        session.call_rpc = AsyncMock(return_value=[])

        generator = ContentGenerator(session)
        result = await generator.delete("art-123")

        assert result is True
        session.call_rpc.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_failure_raises(self) -> None:
        session = MagicMock()
        session.call_rpc = AsyncMock(side_effect=Exception("RPC failed"))

        generator = ContentGenerator(session)

        with pytest.raises(APIError, match="Failed to delete artifact"):
            await generator.delete("art-123")


# =============================================================================
# Parse Result Tests
# =============================================================================


class TestParseCreateResult:
    """Tests for _parse_create_result helper."""

    @pytest.mark.asyncio
    async def test_parse_create_result_invalid_response_raises(self) -> None:
        session = MagicMock()
        session.call_rpc = AsyncMock(return_value=None)

        generator = ContentGenerator(session)

        with pytest.raises(GenerationError, match="Invalid response"):
            await generator.create_audio(
                notebook_id="nb-123",
                source_ids=["src-1"],
                format=AudioFormat.DEEP_DIVE,
            )

    @pytest.mark.asyncio
    async def test_parse_create_result_empty_artifact_raises(self) -> None:
        session = MagicMock()
        session.call_rpc = AsyncMock(return_value=[[]])

        generator = ContentGenerator(session)

        with pytest.raises(GenerationError, match="Invalid artifact data"):
            await generator.create_audio(
                notebook_id="nb-123",
                source_ids=["src-1"],
                format=AudioFormat.DEEP_DIVE,
            )


class TestParsePollResult:
    """Tests for _parse_poll_result helper."""

    @pytest.mark.asyncio
    async def test_parse_poll_result_with_audio_url(self) -> None:
        session = MagicMock()
        # Simulate audio artifact with URL at position 6
        session.call_rpc = AsyncMock(
            return_value=[
                [
                    [
                        "audio-id",
                        "My Podcast",
                        1,  # type = audio
                        None,
                        3,  # status = completed
                        None,
                        [
                            None,
                            None,
                            None,
                            "https://audio.url",
                            None,
                            None,
                            None,
                            None,
                            None,
                            [300, 0],
                        ],
                    ]
                ]
            ]
        )

        generator = ContentGenerator(session)
        artifacts = await generator.poll_status("nb-123")

        assert len(artifacts) == 1
        assert artifacts[0].audio_url == "https://audio.url"
        assert artifacts[0].duration_seconds == 300

    @pytest.mark.asyncio
    async def test_parse_poll_result_skips_invalid_entries(self) -> None:
        session = MagicMock()
        session.call_rpc = AsyncMock(
            return_value=[
                [
                    ["valid-id", "title", 1, None, 3],  # Valid
                    [1, 2],  # Too short - should be skipped
                    "not a list",  # Not a list - should be skipped
                ]
            ]
        )

        generator = ContentGenerator(session)
        artifacts = await generator.poll_status("nb-123")

        assert len(artifacts) == 1
        assert artifacts[0].artifact_id == "valid-id"

    @pytest.mark.asyncio
    async def test_parse_poll_result_with_video_url(self) -> None:
        session = MagicMock()
        # Simulate video artifact with URL at position 8
        session.call_rpc = AsyncMock(
            return_value=[
                [
                    [
                        "video-id",
                        "My Video",
                        3,  # type = video
                        None,
                        3,  # status = completed
                        None,
                        None,
                        None,
                        [None, None, None, "https://video.url"],
                    ]
                ]
            ]
        )

        generator = ContentGenerator(session)
        artifacts = await generator.poll_status("nb-123")

        assert len(artifacts) == 1
        assert artifacts[0].artifact_type == StudioArtifactType.VIDEO
        assert artifacts[0].video_url == "https://video.url"

    @pytest.mark.asyncio
    async def test_parse_poll_result_with_infographic_url(self) -> None:
        session = MagicMock()
        # Simulate infographic artifact with URL at position 14
        # Structure for extraction:
        # infographic_options[2] = image_data = [[first_image[0], image_details]]
        # image_details[0] = url
        session.call_rpc = AsyncMock(
            return_value=[
                [
                    [
                        "infographic-id",
                        "My Infographic",
                        7,  # type = infographic
                        None,
                        3,  # status = completed
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        # infographic_options: [None, None, image_data]
                        # image_data: [[first_image_item0, image_details]]
                        # image_details: [url]
                        [None, None, [["placeholder", ["https://infographic.url"]]]],
                    ]
                ]
            ]
        )

        generator = ContentGenerator(session)
        artifacts = await generator.poll_status("nb-123")

        assert len(artifacts) == 1
        assert artifacts[0].artifact_type == StudioArtifactType.INFOGRAPHIC
        assert artifacts[0].infographic_url == "https://infographic.url"

    @pytest.mark.asyncio
    async def test_parse_poll_result_with_slide_deck_url(self) -> None:
        session = MagicMock()
        # Simulate slide deck artifact with URL at position 16
        session.call_rpc = AsyncMock(
            return_value=[
                [
                    [
                        "slides-id",
                        "My Slides",
                        8,  # type = slide_deck
                        None,
                        3,  # status = completed
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
                        ["https://slides.url"],
                    ]
                ]
            ]
        )

        generator = ContentGenerator(session)
        artifacts = await generator.poll_status("nb-123")

        assert len(artifacts) == 1
        assert artifacts[0].artifact_type == StudioArtifactType.SLIDE_DECK
        assert artifacts[0].slide_deck_url == "https://slides.url"

    @pytest.mark.asyncio
    async def test_parse_poll_result_with_slide_deck_url_at_position_3(self) -> None:
        session = MagicMock()
        # Slide deck URL can also be at options[3]
        session.call_rpc = AsyncMock(
            return_value=[
                [
                    [
                        "slides-id",
                        "My Slides",
                        8,  # type = slide_deck
                        None,
                        3,  # status = completed
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
                        [None, None, None, "https://slides-alt.url"],
                    ]
                ]
            ]
        )

        generator = ContentGenerator(session)
        artifacts = await generator.poll_status("nb-123")

        assert len(artifacts) == 1
        assert artifacts[0].slide_deck_url == "https://slides-alt.url"

    @pytest.mark.asyncio
    async def test_parse_poll_result_with_timestamp(self) -> None:
        session = MagicMock()
        # Simulate artifact with timestamp at position 10
        session.call_rpc = AsyncMock(
            return_value=[
                [
                    [
                        "art-id",
                        "My Artifact",
                        1,  # type = audio
                        None,
                        3,  # status = completed
                        None,
                        None,
                        None,
                        None,
                        None,
                        [1704067200, 0],  # Timestamp: 2024-01-01T00:00:00Z
                    ]
                ]
            ]
        )

        generator = ContentGenerator(session)
        artifacts = await generator.poll_status("nb-123")

        assert len(artifacts) == 1
        assert artifacts[0].created_at is not None
        assert "2024-01-01" in artifacts[0].created_at

    @pytest.mark.asyncio
    async def test_parse_create_result_completed_status(self) -> None:
        session = MagicMock()
        session.call_rpc = AsyncMock(
            return_value=[
                ["art-id", "title", 1, None, 3]
            ]  # status_code = 3 (completed)
        )

        generator = ContentGenerator(session)
        result = await generator.create_audio(
            notebook_id="nb-123",
            source_ids=["src-1"],
            format=AudioFormat.DEEP_DIVE,
        )

        assert result.status == "completed"

    @pytest.mark.asyncio
    async def test_parse_create_result_unknown_status(self) -> None:
        session = MagicMock()
        session.call_rpc = AsyncMock(
            return_value=[
                ["art-id", "title", 1, None, 99]
            ]  # status_code = 99 (unknown)
        )

        generator = ContentGenerator(session)
        result = await generator.create_audio(
            notebook_id="nb-123",
            source_ids=["src-1"],
            format=AudioFormat.DEEP_DIVE,
        )

        assert result.status == "unknown"


class TestCreateContentRpcFailures:
    """Tests for RPC failure handling in create_* methods."""

    @pytest.mark.asyncio
    async def test_create_video_rpc_failure_raises(self) -> None:
        session = MagicMock()
        session.call_rpc = AsyncMock(side_effect=Exception("RPC failed"))

        generator = ContentGenerator(session)

        with pytest.raises(GenerationError, match="Failed to create video"):
            await generator.create_video(
                notebook_id="nb-123",
                source_ids=["src-1"],
                format=VideoFormat.EXPLAINER,
            )

    @pytest.mark.asyncio
    async def test_create_infographic_rpc_failure_raises(self) -> None:
        session = MagicMock()
        session.call_rpc = AsyncMock(side_effect=Exception("RPC failed"))

        generator = ContentGenerator(session)

        with pytest.raises(GenerationError, match="Failed to create infographic"):
            await generator.create_infographic(
                notebook_id="nb-123",
                source_ids=["src-1"],
            )

    @pytest.mark.asyncio
    async def test_create_slides_rpc_failure_raises(self) -> None:
        session = MagicMock()
        session.call_rpc = AsyncMock(side_effect=Exception("RPC failed"))

        generator = ContentGenerator(session)

        with pytest.raises(GenerationError, match="Failed to create slide deck"):
            await generator.create_slides(
                notebook_id="nb-123",
                source_ids=["src-1"],
            )
