"""Unit tests for the content generation CLI commands."""

from unittest.mock import AsyncMock, MagicMock, patch

from typer.testing import CliRunner

from pynotebooklm.cli import app
from pynotebooklm.content import (
    CreateContentResult,
    StudioArtifact,
    StudioArtifactStatus,
    StudioArtifactType,
)

runner = CliRunner()


# =============================================================================
# Generate Audio Tests
# =============================================================================


class TestGenerateAudioCommand:
    """Tests for the 'generate audio' CLI command."""

    @patch("pynotebooklm.cli.AuthManager")
    @patch("pynotebooklm.cli.BrowserSession")
    @patch("pynotebooklm.cli.SourceManager")
    @patch("pynotebooklm.cli.ContentGenerator")
    def test_generate_audio_success(
        self,
        mock_generator_cls: MagicMock,
        mock_source_mgr_cls: MagicMock,
        mock_session_cls: MagicMock,
        mock_auth_cls: MagicMock,
    ) -> None:
        # Setup mocks
        mock_auth = MagicMock()
        mock_auth.is_authenticated.return_value = True
        mock_auth_cls.return_value = mock_auth

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session_cls.return_value = mock_session

        mock_source_mgr = MagicMock()
        mock_source = MagicMock()
        mock_source.id = "src-1"
        mock_source_mgr.list_sources = AsyncMock(return_value=[mock_source])
        mock_source_mgr_cls.return_value = mock_source_mgr

        mock_generator = MagicMock()
        mock_generator.create_audio = AsyncMock(
            return_value=CreateContentResult(
                artifact_id="audio-123",
                notebook_id="nb-123",
                content_type="audio",
                status="in_progress",
                format="deep_dive",
                length="default",
            )
        )
        mock_generator_cls.return_value = mock_generator

        result = runner.invoke(app, ["generate", "audio", "nb-123"])

        assert result.exit_code == 0
        assert "Audio generation started" in result.output
        assert "audio-123" in result.output

    @patch("pynotebooklm.cli.AuthManager")
    def test_generate_audio_not_authenticated(self, mock_auth_cls: MagicMock) -> None:
        mock_auth = MagicMock()
        mock_auth.is_authenticated.return_value = False
        mock_auth_cls.return_value = mock_auth

        result = runner.invoke(app, ["generate", "audio", "nb-123"])

        assert result.exit_code == 1
        assert "Not authenticated" in result.output

    @patch("pynotebooklm.cli.AuthManager")
    @patch("pynotebooklm.cli.BrowserSession")
    @patch("pynotebooklm.cli.SourceManager")
    def test_generate_audio_no_sources(
        self,
        mock_source_mgr_cls: MagicMock,
        mock_session_cls: MagicMock,
        mock_auth_cls: MagicMock,
    ) -> None:
        mock_auth = MagicMock()
        mock_auth.is_authenticated.return_value = True
        mock_auth_cls.return_value = mock_auth

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session_cls.return_value = mock_session

        mock_source_mgr = MagicMock()
        mock_source_mgr.list_sources = AsyncMock(return_value=[])
        mock_source_mgr_cls.return_value = mock_source_mgr

        result = runner.invoke(app, ["generate", "audio", "nb-123"])

        assert result.exit_code == 1
        assert "No sources found" in result.output

    def test_generate_audio_invalid_format(self) -> None:
        # This test verifies the command exits with an error for invalid format
        with patch("pynotebooklm.cli.AuthManager") as mock_auth_cls:
            mock_auth = MagicMock()
            mock_auth.is_authenticated.return_value = True
            mock_auth_cls.return_value = mock_auth

            with patch("pynotebooklm.cli.BrowserSession") as mock_session_cls:
                mock_session = AsyncMock()
                mock_session.__aenter__ = AsyncMock(return_value=mock_session)
                mock_session.__aexit__ = AsyncMock(return_value=None)
                mock_session_cls.return_value = mock_session

                with patch("pynotebooklm.cli.SourceManager") as mock_source_mgr_cls:
                    mock_source = MagicMock()
                    mock_source.id = "src-1"
                    mock_source_mgr = MagicMock()
                    mock_source_mgr.list_sources = AsyncMock(return_value=[mock_source])
                    mock_source_mgr_cls.return_value = mock_source_mgr

                    result = runner.invoke(
                        app,
                        ["generate", "audio", "nb-123", "--format", "invalid_format"],
                    )

                    assert result.exit_code == 1
                    assert "Invalid format" in result.output


# =============================================================================
# Generate Video Tests
# =============================================================================


class TestGenerateVideoCommand:
    """Tests for the 'generate video' CLI command."""

    @patch("pynotebooklm.cli.AuthManager")
    @patch("pynotebooklm.cli.BrowserSession")
    @patch("pynotebooklm.cli.SourceManager")
    @patch("pynotebooklm.cli.ContentGenerator")
    def test_generate_video_success(
        self,
        mock_generator_cls: MagicMock,
        mock_source_mgr_cls: MagicMock,
        mock_session_cls: MagicMock,
        mock_auth_cls: MagicMock,
    ) -> None:
        mock_auth = MagicMock()
        mock_auth.is_authenticated.return_value = True
        mock_auth_cls.return_value = mock_auth

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session_cls.return_value = mock_session

        mock_source_mgr = MagicMock()
        mock_source = MagicMock()
        mock_source.id = "src-1"
        mock_source_mgr.list_sources = AsyncMock(return_value=[mock_source])
        mock_source_mgr_cls.return_value = mock_source_mgr

        mock_generator = MagicMock()
        mock_generator.create_video = AsyncMock(
            return_value=CreateContentResult(
                artifact_id="video-123",
                notebook_id="nb-123",
                content_type="video",
                status="in_progress",
                format="explainer",
                style="classic",
            )
        )
        mock_generator_cls.return_value = mock_generator

        result = runner.invoke(app, ["generate", "video", "nb-123"])

        assert result.exit_code == 0
        assert "Video generation started" in result.output


# =============================================================================
# Generate Infographic Tests
# =============================================================================


class TestGenerateInfographicCommand:
    """Tests for the 'generate infographic' CLI command."""

    @patch("pynotebooklm.cli.AuthManager")
    @patch("pynotebooklm.cli.BrowserSession")
    @patch("pynotebooklm.cli.SourceManager")
    @patch("pynotebooklm.cli.ContentGenerator")
    def test_generate_infographic_success(
        self,
        mock_generator_cls: MagicMock,
        mock_source_mgr_cls: MagicMock,
        mock_session_cls: MagicMock,
        mock_auth_cls: MagicMock,
    ) -> None:
        mock_auth = MagicMock()
        mock_auth.is_authenticated.return_value = True
        mock_auth_cls.return_value = mock_auth

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session_cls.return_value = mock_session

        mock_source_mgr = MagicMock()
        mock_source = MagicMock()
        mock_source.id = "src-1"
        mock_source_mgr.list_sources = AsyncMock(return_value=[mock_source])
        mock_source_mgr_cls.return_value = mock_source_mgr

        mock_generator = MagicMock()
        mock_generator.create_infographic = AsyncMock(
            return_value=CreateContentResult(
                artifact_id="infographic-123",
                notebook_id="nb-123",
                content_type="infographic",
                status="in_progress",
                orientation="landscape",
                detail_level="standard",
            )
        )
        mock_generator_cls.return_value = mock_generator

        result = runner.invoke(app, ["generate", "infographic", "nb-123"])

        assert result.exit_code == 0
        assert "Infographic generation started" in result.output


# =============================================================================
# Generate Slides Tests
# =============================================================================


class TestGenerateSlidesCommand:
    """Tests for the 'generate slides' CLI command."""

    @patch("pynotebooklm.cli.AuthManager")
    @patch("pynotebooklm.cli.BrowserSession")
    @patch("pynotebooklm.cli.SourceManager")
    @patch("pynotebooklm.cli.ContentGenerator")
    def test_generate_slides_success(
        self,
        mock_generator_cls: MagicMock,
        mock_source_mgr_cls: MagicMock,
        mock_session_cls: MagicMock,
        mock_auth_cls: MagicMock,
    ) -> None:
        mock_auth = MagicMock()
        mock_auth.is_authenticated.return_value = True
        mock_auth_cls.return_value = mock_auth

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session_cls.return_value = mock_session

        mock_source_mgr = MagicMock()
        mock_source = MagicMock()
        mock_source.id = "src-1"
        mock_source_mgr.list_sources = AsyncMock(return_value=[mock_source])
        mock_source_mgr_cls.return_value = mock_source_mgr

        mock_generator = MagicMock()
        mock_generator.create_slides = AsyncMock(
            return_value=CreateContentResult(
                artifact_id="slides-123",
                notebook_id="nb-123",
                content_type="slide_deck",
                status="in_progress",
                format="detailed_deck",
                length="default",
            )
        )
        mock_generator_cls.return_value = mock_generator

        result = runner.invoke(app, ["generate", "slides", "nb-123"])

        assert result.exit_code == 0
        assert "Slide deck generation started" in result.output


# =============================================================================
# Studio Status Tests
# =============================================================================


class TestStudioStatusCommand:
    """Tests for the 'studio status' CLI command."""

    @patch("pynotebooklm.cli.AuthManager")
    @patch("pynotebooklm.cli.BrowserSession")
    @patch("pynotebooklm.cli.ContentGenerator")
    def test_studio_status_success(
        self,
        mock_generator_cls: MagicMock,
        mock_session_cls: MagicMock,
        mock_auth_cls: MagicMock,
    ) -> None:
        mock_auth = MagicMock()
        mock_auth.is_authenticated.return_value = True
        mock_auth_cls.return_value = mock_auth

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session_cls.return_value = mock_session

        mock_generator = MagicMock()
        mock_generator.poll_status = AsyncMock(
            return_value=[
                StudioArtifact(
                    artifact_id="art-1",
                    notebook_id="nb-123",
                    title="My Audio",
                    artifact_type=StudioArtifactType.AUDIO,
                    status=StudioArtifactStatus.COMPLETED,
                    audio_url="https://audio.url",
                ),
            ]
        )
        mock_generator_cls.return_value = mock_generator

        result = runner.invoke(app, ["studio", "status", "nb-123"])

        assert result.exit_code == 0
        assert "art-1" in result.output
        assert "audio" in result.output

    @patch("pynotebooklm.cli.AuthManager")
    @patch("pynotebooklm.cli.BrowserSession")
    @patch("pynotebooklm.cli.ContentGenerator")
    def test_studio_status_empty(
        self,
        mock_generator_cls: MagicMock,
        mock_session_cls: MagicMock,
        mock_auth_cls: MagicMock,
    ) -> None:
        mock_auth = MagicMock()
        mock_auth.is_authenticated.return_value = True
        mock_auth_cls.return_value = mock_auth

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session_cls.return_value = mock_session

        mock_generator = MagicMock()
        mock_generator.poll_status = AsyncMock(return_value=[])
        mock_generator_cls.return_value = mock_generator

        result = runner.invoke(app, ["studio", "status", "nb-123"])

        assert result.exit_code == 0
        assert "No studio artifacts found" in result.output


# =============================================================================
# Studio Delete Tests
# =============================================================================


class TestStudioDeleteCommand:
    """Tests for the 'studio delete' CLI command."""

    @patch("pynotebooklm.cli.AuthManager")
    @patch("pynotebooklm.cli.BrowserSession")
    @patch("pynotebooklm.cli.ContentGenerator")
    def test_studio_delete_success_with_force(
        self,
        mock_generator_cls: MagicMock,
        mock_session_cls: MagicMock,
        mock_auth_cls: MagicMock,
    ) -> None:
        mock_auth = MagicMock()
        mock_auth.is_authenticated.return_value = True
        mock_auth_cls.return_value = mock_auth

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session_cls.return_value = mock_session

        mock_generator = MagicMock()
        mock_generator.delete = AsyncMock(return_value=True)
        mock_generator_cls.return_value = mock_generator

        result = runner.invoke(app, ["studio", "delete", "art-123", "--force"])

        assert result.exit_code == 0
        assert "Deleted artifact" in result.output

    @patch("pynotebooklm.cli.AuthManager")
    @patch("pynotebooklm.cli.BrowserSession")
    @patch("pynotebooklm.cli.ContentGenerator")
    def test_studio_delete_aborted_without_force(
        self,
        mock_generator_cls: MagicMock,
        mock_session_cls: MagicMock,
        mock_auth_cls: MagicMock,
    ) -> None:
        mock_auth = MagicMock()
        mock_auth.is_authenticated.return_value = True
        mock_auth_cls.return_value = mock_auth

        # When not using --force, user is prompted for confirmation
        # Simulate user saying "n" (no)
        result = runner.invoke(app, ["studio", "delete", "art-123"], input="n\n")

        assert result.exit_code == 0
        assert "Aborted" in result.output
