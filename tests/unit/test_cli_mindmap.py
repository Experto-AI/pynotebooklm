"""
Unit tests for the CLI mindmap commands.
"""

from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from typer.testing import CliRunner

from pynotebooklm.cli import app
from pynotebooklm.mindmaps import MindMap

runner = CliRunner()


@pytest.fixture
def mock_mindmap() -> MindMap:
    """Create a mock mind map."""
    return MindMap(
        id="mm_123",
        notebook_id="nb_123",
        title="Test Mind Map",
        created_at=datetime.now(),
        mind_map_json='{"name": "Root", "children": []}',
        source_ids=["src_1", "src_2"],
    )


class TestMindMapCreateCommand:
    """Tests for the 'mindmap create' CLI command."""

    def test_create_mindmap_not_authenticated(self) -> None:
        """Create mindmap exits when not authenticated."""
        with patch("pynotebooklm.cli.AuthManager") as mock_auth_cls:
            mock_auth = MagicMock()
            mock_auth.is_authenticated.return_value = False
            mock_auth_cls.return_value = mock_auth

            result = runner.invoke(app, ["mindmap", "create", "nb_123"])

            assert result.exit_code == 1
            assert "Not authenticated" in result.output

    def test_create_mindmap_success(self, mock_mindmap: MindMap) -> None:
        """Create mindmap command succeeds."""
        with (
            patch("pynotebooklm.cli.AuthManager") as mock_auth_cls,
            patch("pynotebooklm.cli.BrowserSession") as mock_session_cls,
            patch("pynotebooklm.cli.MindMapGenerator") as mock_gen_cls,
        ):
            mock_auth = MagicMock()
            mock_auth.is_authenticated.return_value = True
            mock_auth_cls.return_value = mock_auth

            mock_session = MagicMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            mock_session_cls.return_value = mock_session

            mock_gen = MagicMock()
            mock_gen.create = AsyncMock(return_value=mock_mindmap)
            mock_gen_cls.return_value = mock_gen

            result = runner.invoke(app, ["mindmap", "create", "nb_123"])

            assert result.exit_code == 0
            assert "Created mind map successfully" in result.output
            assert "mm_123" in result.output
            assert "Test Mind Map" in result.output

    def test_create_mindmap_failure(self) -> None:
        """Create mindmap handles failure."""
        with (
            patch("pynotebooklm.cli.AuthManager") as mock_auth_cls,
            patch("pynotebooklm.cli.BrowserSession") as mock_session_cls,
            patch("pynotebooklm.cli.MindMapGenerator") as mock_gen_cls,
        ):
            mock_auth = MagicMock()
            mock_auth.is_authenticated.return_value = True
            mock_auth_cls.return_value = mock_auth

            mock_session = MagicMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            mock_session_cls.return_value = mock_session

            mock_gen = MagicMock()
            mock_gen.create = AsyncMock(side_effect=Exception("API Error"))
            mock_gen_cls.return_value = mock_gen

            result = runner.invoke(app, ["mindmap", "create", "nb_123"])

            assert result.exit_code == 1
            assert "Failed to create mind map" in result.output
            assert "API Error" in result.output


class TestMindMapListCommand:
    """Tests for the 'mindmap list' CLI command."""

    def test_list_mindmaps_not_authenticated(self) -> None:
        """List mindmaps exits when not authenticated."""
        with patch("pynotebooklm.cli.AuthManager") as mock_auth_cls:
            mock_auth = MagicMock()
            mock_auth.is_authenticated.return_value = False
            mock_auth_cls.return_value = mock_auth

            result = runner.invoke(app, ["mindmap", "list", "nb_123"])

            assert result.exit_code == 1
            assert "Not authenticated" in result.output

    def test_list_mindmaps_success(self, mock_mindmap: MindMap) -> None:
        """List mindmaps command succeeds."""
        with (
            patch("pynotebooklm.cli.AuthManager") as mock_auth_cls,
            patch("pynotebooklm.cli.BrowserSession") as mock_session_cls,
            patch("pynotebooklm.cli.MindMapGenerator") as mock_gen_cls,
        ):
            mock_auth = MagicMock()
            mock_auth.is_authenticated.return_value = True
            mock_auth_cls.return_value = mock_auth

            mock_session = MagicMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            mock_session_cls.return_value = mock_session

            mock_gen = MagicMock()
            mock_gen.list = AsyncMock(return_value=[mock_mindmap])
            mock_gen_cls.return_value = mock_gen

            result = runner.invoke(app, ["mindmap", "list", "nb_123"])

            assert result.exit_code == 0
            assert "mm_123" in result.output
            assert "Test Mind Map" in result.output

    def test_list_mindmaps_empty(self) -> None:
        """List mindmaps handles empty list."""
        with (
            patch("pynotebooklm.cli.AuthManager") as mock_auth_cls,
            patch("pynotebooklm.cli.BrowserSession") as mock_session_cls,
            patch("pynotebooklm.cli.MindMapGenerator") as mock_gen_cls,
        ):
            mock_auth = MagicMock()
            mock_auth.is_authenticated.return_value = True
            mock_auth_cls.return_value = mock_auth

            mock_session = MagicMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            mock_session_cls.return_value = mock_session

            mock_gen = MagicMock()
            mock_gen.list = AsyncMock(return_value=[])
            mock_gen_cls.return_value = mock_gen

            result = runner.invoke(app, ["mindmap", "list", "nb_123"])

            assert result.exit_code == 0
            assert "No mind maps found" in result.output


class TestMindMapExportCommand:
    """Tests for the 'mindmap export' CLI command."""

    def test_export_mindmap_not_authenticated(self) -> None:
        """Export mindmap exits when not authenticated."""
        with patch("pynotebooklm.cli.AuthManager") as mock_auth_cls:
            mock_auth = MagicMock()
            mock_auth.is_authenticated.return_value = False
            mock_auth_cls.return_value = mock_auth

            result = runner.invoke(app, ["mindmap", "export", "nb_123", "mm_123"])

            assert result.exit_code == 1
            assert "Not authenticated" in result.output

    def test_export_mindmap_success_json(
        self, mock_mindmap: MindMap, tmp_path: Path
    ) -> None:
        """Export mindmap to JSON succeeds."""
        output_file = tmp_path / "output.json"

        with (
            patch("pynotebooklm.cli.AuthManager") as mock_auth_cls,
            patch("pynotebooklm.cli.BrowserSession") as mock_session_cls,
            patch("pynotebooklm.cli.MindMapGenerator") as mock_gen_cls,
            patch("pynotebooklm.cli.export_to_json") as mock_export,
        ):
            mock_auth = MagicMock()
            mock_auth.is_authenticated.return_value = True
            mock_auth_cls.return_value = mock_auth

            mock_session = MagicMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            mock_session_cls.return_value = mock_session

            mock_gen = MagicMock()
            mock_gen.get = AsyncMock(return_value=mock_mindmap)
            mock_gen_cls.return_value = mock_gen

            mock_export.return_value = '{"foo": "bar"}'

            result = runner.invoke(
                app,
                [
                    "mindmap",
                    "export",
                    "nb_123",
                    "mm_123",
                    "--format",
                    "json",
                    "--output",
                    str(output_file),
                ],
            )

            assert result.exit_code == 0
            assert "Exported to" in result.output
            assert output_file.read_text() == '{"foo": "bar"}'
            mock_export.assert_called_once()

    def test_export_mindmap_success_opml(
        self, mock_mindmap: MindMap, tmp_path: Path
    ) -> None:
        """Export mindmap to OPML succeeds."""
        output_file = tmp_path / "output.opml"

        with (
            patch("pynotebooklm.cli.AuthManager") as mock_auth_cls,
            patch("pynotebooklm.cli.BrowserSession") as mock_session_cls,
            patch("pynotebooklm.cli.MindMapGenerator") as mock_gen_cls,
            patch("pynotebooklm.cli.export_to_opml") as mock_export,
        ):
            mock_auth = MagicMock()
            mock_auth.is_authenticated.return_value = True
            mock_auth_cls.return_value = mock_auth

            mock_session = MagicMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            mock_session_cls.return_value = mock_session

            mock_gen = MagicMock()
            mock_gen.get = AsyncMock(return_value=mock_mindmap)
            mock_gen_cls.return_value = mock_gen

            mock_export.return_value = "<opml>...</opml>"

            result = runner.invoke(
                app,
                [
                    "mindmap",
                    "export",
                    "nb_123",
                    "mm_123",
                    "--format",
                    "opml",
                    "--output",
                    str(output_file),
                ],
            )

            assert result.exit_code == 0
            assert "Exported to" in result.output
            assert output_file.read_text() == "<opml>...</opml>"

    def test_export_mindmap_not_found(self) -> None:
        """Export mindmap handles missing mindmap."""
        with (
            patch("pynotebooklm.cli.AuthManager") as mock_auth_cls,
            patch("pynotebooklm.cli.BrowserSession") as mock_session_cls,
            patch("pynotebooklm.cli.MindMapGenerator") as mock_gen_cls,
        ):
            mock_auth = MagicMock()
            mock_auth.is_authenticated.return_value = True
            mock_auth_cls.return_value = mock_auth

            mock_session = MagicMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            mock_session_cls.return_value = mock_session

            mock_gen = MagicMock()
            mock_gen.get = AsyncMock(return_value=None)
            mock_gen_cls.return_value = mock_gen

            result = runner.invoke(app, ["mindmap", "export", "nb_123", "mm_999"])

            assert result.exit_code == 1
            assert "Mind map not found" in result.output

    def test_export_mindmap_invalid_format(self, mock_mindmap: MindMap) -> None:
        """Export mindmap validates format."""
        with (
            patch("pynotebooklm.cli.AuthManager") as mock_auth_cls,
            patch("pynotebooklm.cli.BrowserSession") as mock_session_cls,
            patch("pynotebooklm.cli.MindMapGenerator") as mock_gen_cls,
        ):
            mock_auth = MagicMock()
            mock_auth.is_authenticated.return_value = True
            mock_auth_cls.return_value = mock_auth

            mock_session = MagicMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            mock_session_cls.return_value = mock_session

            mock_gen = MagicMock()
            mock_gen.get = AsyncMock(return_value=mock_mindmap)
            mock_gen_cls.return_value = mock_gen

            result = runner.invoke(
                app, ["mindmap", "export", "nb_123", "mm_123", "--format", "invalid"]
            )

            assert result.exit_code == 1
            assert "Invalid format" in result.output
