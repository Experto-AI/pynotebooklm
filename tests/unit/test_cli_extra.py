"""
Additional unit tests for CLI commands to improve coverage.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from typer.testing import CliRunner

from pynotebooklm.cli import app

runner = CliRunner()


class TestCliExtra:
    @pytest.fixture
    def mock_auth(self):
        with patch("pynotebooklm.cli.AuthManager") as mock:
            inst = MagicMock()
            inst.is_authenticated.return_value = True
            mock.return_value = inst
            yield mock

    @pytest.fixture
    def mock_session(self):
        with patch("pynotebooklm.cli.BrowserSession") as mock:
            inst = MagicMock()
            inst.__aenter__ = AsyncMock(return_value=inst)
            inst.__aexit__ = AsyncMock(return_value=None)
            mock.return_value = inst
            yield mock

    def test_auth_check(self, mock_auth):
        """Test auth check command."""
        mock_auth.return_value.is_authenticated.return_value = True
        result = runner.invoke(app, ["auth", "check"])
        assert "Authenticated: True" in result.output
        assert result.exit_code == 0

        mock_auth.return_value.is_authenticated.return_value = False
        result = runner.invoke(app, ["auth", "check"])
        assert "Authenticated: False" in result.output
        assert result.exit_code == 1

    def test_auth_logout(self, mock_auth):
        """Test auth logout command."""
        mock_auth.return_value.logout = MagicMock()
        result = runner.invoke(app, ["auth", "logout"])
        assert "Logged out" in result.output
        assert result.exit_code == 0
        mock_auth.return_value.logout.assert_called_once()

    def test_notebooks_list_detailed(self, mock_auth, mock_session):
        """Test notebooks list --detailed."""
        with patch("pynotebooklm.cli.NotebookManager") as mock_nb:
            inst = MagicMock()
            # Use a simple object to avoid Rich rendering issues with MagicMock
            nb = MagicMock()
            nb.id = "nb1"
            nb.name = "NB1"
            nb.source_count = 5
            nb.created_at = None

            inst.list = AsyncMock(return_value=[nb])
            mock_nb.return_value = inst

            result = runner.invoke(app, ["notebooks", "list", "--detailed"])
            assert result.exit_code == 0
            assert "NB1" in result.output
            assert "5" in result.output

    def test_notebooks_delete_force(self, mock_auth, mock_session):
        """Test notebooks delete with --force."""
        with patch("pynotebooklm.cli.NotebookManager") as mock_nb:
            inst = MagicMock()
            inst.delete = AsyncMock(return_value=True)
            mock_nb.return_value = inst

            result = runner.invoke(app, ["notebooks", "delete", "nb1", "--force"])
            assert result.exit_code == 0
            assert "Deleted notebook: nb1" in result.output
            inst.delete.assert_called_once_with("nb1", confirm=True)

    def test_sources_list_empty(self, mock_auth, mock_session):
        """Test sources list when empty."""
        with patch("pynotebooklm.cli.SourceManager") as mock_src:
            inst = MagicMock()
            inst.list_sources = AsyncMock(return_value=[])
            mock_src.return_value = inst

            result = runner.invoke(app, ["sources", "list", "nb1"])
            assert result.exit_code == 0
            assert "No sources found" in result.output

    def test_mindmap_create_value_error(self, mock_auth, mock_session):
        """Test mindmap create with ValueError."""
        with patch("pynotebooklm.cli.MindMapGenerator") as mock_gen:
            inst = MagicMock()
            inst.create = AsyncMock(side_effect=ValueError("Invalid notebook"))
            mock_gen.return_value = inst

            result = runner.invoke(app, ["mindmap", "create", "nb_123"])

            assert result.exit_code == 1
            assert "Error: Invalid notebook" in result.output

    def test_mindmap_export_invalid_format(self, mock_auth, mock_session):
        """Test mindmap export with invalid format."""
        with patch("pynotebooklm.cli.MindMapGenerator") as mock_gen:
            inst = MagicMock()
            # Use a mock that returns real strings for ID and title
            mm = MagicMock()
            mm.id = "mm_123"
            mm.title = "Map Title"
            mm.mind_map_json = {"root": {}}
            inst.get = AsyncMock(return_value=mm)
            mock_gen.return_value = inst

            result = runner.invoke(
                app, ["mindmap", "export", "nb_123", "mm_123", "--format", "invalid"]
            )

            assert result.exit_code == 1
            assert "Invalid format" in result.output

    def test_generate_audio_invalid_options(self, mock_auth, mock_session):
        """Test generate audio with invalid format/length."""
        result = runner.invoke(app, ["generate", "audio", "nb_123", "--format", "bad"])
        assert result.exit_code == 1
        assert "Invalid format" in result.output

    def test_studio_delete_no_confirm(self, mock_auth, mock_session):
        """Test studio delete when user says no to confirmation."""
        result = runner.invoke(app, ["studio", "delete", "art_123"], input="n\n")
        assert "Aborted" in result.output
        assert result.exit_code == 0

    def test_sources_add_text(self, mock_auth, mock_session):
        """Test sources add-text command."""
        from pynotebooklm.models import Source, SourceType

        with patch("pynotebooklm.cli.SourceManager") as mock_src:
            inst = MagicMock()
            inst.add_text = AsyncMock(
                return_value=Source(
                    id="src_txt_123", title="My Text", type=SourceType.TEXT
                )
            )
            mock_src.return_value = inst

            result = runner.invoke(
                app,
                [
                    "sources",
                    "add-text",
                    "nb_123",
                    "This is some content",
                    "--title",
                    "My Text",
                ],
            )

            assert result.exit_code == 0
            assert "Added text source" in result.output
            inst.add_text.assert_called_once_with(
                "nb_123", "This is some content", "My Text"
            )

    def test_sources_add_drive(self, mock_auth, mock_session):
        """Test sources add-drive command."""
        from pynotebooklm.models import Source, SourceType

        with patch("pynotebooklm.cli.SourceManager") as mock_src:
            inst = MagicMock()
            inst.add_drive = AsyncMock(
                return_value=Source(
                    id="src_drive_123", title="Google Doc", type=SourceType.DRIVE
                )
            )
            mock_src.return_value = inst

            result = runner.invoke(
                app, ["sources", "add-drive", "nb_123", "1ABC123XYZ"]
            )

            assert result.exit_code == 0
            assert "Added Drive source" in result.output
            inst.add_drive.assert_called_once_with("nb_123", "1ABC123XYZ")

    def test_sources_describe_success(self, mock_auth, mock_session):
        """Test sources describe command success."""
        mock_api_instance = MagicMock()
        mock_api_instance.get_source_guide = AsyncMock(
            return_value=[
                [
                    ["This is the source summary."],
                    None,
                    [["keyword1", "keyword2"]],
                ]
            ]
        )

        with patch("pynotebooklm.api.NotebookLMAPI", return_value=mock_api_instance):
            result = runner.invoke(app, ["sources", "describe", "src_123"])

        assert result.exit_code == 0
        assert "Summary for Source src_123" in result.output
        assert "This is the source summary." in result.output

    def test_sources_describe_no_result(self, mock_auth, mock_session):
        """Test sources describe when no result."""
        mock_api_instance = MagicMock()
        mock_api_instance.get_source_guide = AsyncMock(return_value=None)

        with patch("pynotebooklm.api.NotebookLMAPI", return_value=mock_api_instance):
            result = runner.invoke(app, ["sources", "describe", "src_123"])

        assert result.exit_code == 1
        assert "Failed to get source description" in result.output

    def test_sources_describe_not_authenticated(self):
        """Test sources describe when not authenticated."""
        with patch("pynotebooklm.cli.AuthManager") as mock_auth_cls:
            mock_auth_cls.return_value.is_authenticated.return_value = False
            result = runner.invoke(app, ["sources", "describe", "src_123"])
            assert result.exit_code == 1
            assert "Not authenticated" in result.output

    def test_sources_get_text_success(self, mock_auth, mock_session):
        """Test sources get-text command success."""
        mock_api_instance = MagicMock()
        mock_api_instance.get_source_text = AsyncMock(
            return_value={
                "content": "This is the full text content.",
                "title": "Test Source",
                "source_type": "url",
                "char_count": 30,
            }
        )

        with patch("pynotebooklm.api.NotebookLMAPI", return_value=mock_api_instance):
            result = runner.invoke(app, ["sources", "get-text", "src_123"])

        assert result.exit_code == 0
        assert "Content for Source: Test Source" in result.output
        assert "This is the full text content." in result.output
        assert "30 chars" in result.output

    def test_sources_get_text_empty(self, mock_auth, mock_session):
        """Test sources get-text when content is empty."""
        mock_api_instance = MagicMock()
        mock_api_instance.get_source_text = AsyncMock(return_value=None)

        with patch("pynotebooklm.api.NotebookLMAPI", return_value=mock_api_instance):
            result = runner.invoke(app, ["sources", "get-text", "src_123"])

        assert result.exit_code == 1
        assert "Failed to extract source text" in result.output

    def test_sources_get_text_not_authenticated(self):
        """Test sources get-text when not authenticated."""
        with patch("pynotebooklm.cli.AuthManager") as mock_auth_cls:
            mock_auth_cls.return_value.is_authenticated.return_value = False
            result = runner.invoke(app, ["sources", "get-text", "src_123"])
            assert result.exit_code == 1
            assert "Not authenticated" in result.output

    def test_sources_sync_success(self, mock_auth, mock_session):
        """Test sources sync command success."""
        mock_api_instance = MagicMock()
        mock_api_instance.sync_source = AsyncMock(return_value=True)

        with patch("pynotebooklm.api.NotebookLMAPI", return_value=mock_api_instance):
            result = runner.invoke(app, ["sources", "sync", "src_123"])

        assert result.exit_code == 0
        assert "Successfully triggered sync" in result.output

    def test_sources_sync_failure(self, mock_auth, mock_session):
        """Test sources sync command failure."""
        mock_api_instance = MagicMock()
        mock_api_instance.sync_source = AsyncMock(return_value=False)

        with patch("pynotebooklm.api.NotebookLMAPI", return_value=mock_api_instance):
            result = runner.invoke(app, ["sources", "sync", "src_123"])

        assert result.exit_code == 1
        assert "Failed to sync source" in result.output

    def test_sources_sync_not_authenticated(self):
        """Test sources sync when not authenticated."""
        with patch("pynotebooklm.cli.AuthManager") as mock_auth_cls:
            mock_auth_cls.return_value.is_authenticated.return_value = False
            result = runner.invoke(app, ["sources", "sync", "src_123"])
            assert result.exit_code == 1
            assert "Not authenticated" in result.output

    def test_sources_delete_abort(self, mock_auth, mock_session):
        """Test sources delete when user aborts."""
        with patch("pynotebooklm.cli.SourceManager") as mock_src:
            inst = MagicMock()
            mock_src.return_value = inst

            result = runner.invoke(
                app, ["sources", "delete", "nb_123", "src_456"], input="n\n"
            )

            assert "Aborted" in result.output
            assert result.exit_code == 0

    def test_notebooks_delete_abort(self, mock_auth, mock_session):
        """Test notebooks delete when user aborts."""
        with patch("pynotebooklm.cli.NotebookManager") as mock_nb:
            inst = MagicMock()
            mock_nb.return_value = inst

            result = runner.invoke(app, ["notebooks", "delete", "nb_123"], input="n\n")

            assert "Aborted" in result.output
            assert result.exit_code == 0
