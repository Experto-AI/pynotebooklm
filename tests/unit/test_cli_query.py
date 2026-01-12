"""
Unit tests for CLI query commands.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from typer.testing import CliRunner

from pynotebooklm.cli import app

runner = CliRunner()


class TestCliQuery:
    @pytest.fixture
    def mock_chat(self):
        with patch("pynotebooklm.cli.ChatSession") as mock:
            yield mock

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

    def test_query_ask(self, mock_auth, mock_session, mock_chat):
        """Test query ask command."""
        chat_inst = MagicMock()
        chat_inst.query = AsyncMock(return_value="The answer.")
        mock_chat.return_value = chat_inst

        result = runner.invoke(app, ["query", "ask", "nb_123", "What is it?"])

        assert result.exit_code == 0
        assert "The answer." in result.output
        chat_inst.query.assert_called_with(
            "nb_123", "What is it?", source_ids=None, conversation_id=None
        )

    def test_query_configure(self, mock_auth, mock_session, mock_chat):
        """Test query configure command."""
        chat_inst = MagicMock()
        chat_inst.configure = AsyncMock()
        mock_chat.return_value = chat_inst

        result = runner.invoke(
            app, ["query", "configure", "nb_123", "--goal", "learning"]
        )

        assert result.exit_code == 0
        chat_inst.configure.assert_called_with(
            "nb_123", goal="learning", custom_prompt=None, length="default"
        )

    def test_query_summary(self, mock_auth, mock_session, mock_chat):
        """Test query summary command."""
        chat_inst = MagicMock()
        chat_inst.get_notebook_summary = AsyncMock(
            return_value={
                "summary": "The summary",
                "suggested_topics": [{"question": "Q1", "prompt": "P1"}],
            }
        )
        mock_chat.return_value = chat_inst

        result = runner.invoke(app, ["query", "summary", "nb_123"])

        assert result.exit_code == 0
        assert "The summary" in result.output
        assert "Q1" in result.output

    def test_query_briefing(self, mock_auth, mock_session, mock_chat):
        """Test query briefing command."""
        chat_inst = MagicMock()
        chat_inst.create_briefing = AsyncMock(return_value={"artifact_id": "art_123"})
        mock_chat.return_value = chat_inst

        result = runner.invoke(app, ["query", "briefing", "nb_123"])

        assert result.exit_code == 0
        assert "art_123" in result.output
        chat_inst.create_briefing.assert_called_with("nb_123")

    def test_query_unauthenticated(self, mock_auth):
        """Test query command when not authenticated."""
        mock_auth.return_value.is_authenticated.return_value = False

        result = runner.invoke(app, ["query", "ask", "nb_123", "question"])

        assert result.exit_code == 1
        assert "Not authenticated" in result.output
