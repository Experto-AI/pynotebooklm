"""Unit tests for the research CLI commands."""

from unittest.mock import AsyncMock, MagicMock, patch

from typer.testing import CliRunner

from pynotebooklm.cli import app
from pynotebooklm.research import (
    ImportedSource,
    ResearchResult,
    ResearchSession,
    ResearchStatus,
)

runner = CliRunner()


class TestResearchStartCommand:
    """Tests for the 'research start' command."""

    @patch("pynotebooklm.cli.BrowserSession")
    @patch("pynotebooklm.cli.AuthManager")
    def test_start_success(
        self, mock_auth_class: MagicMock, mock_session_class: MagicMock
    ) -> None:
        """Test successful research start."""
        mock_auth = MagicMock()
        mock_auth.is_authenticated.return_value = True
        mock_auth_class.return_value = mock_auth

        mock_result = ResearchSession(
            task_id="task-123",
            notebook_id="nb-123",
            query="AI trends",
            source="web",
            mode="fast",
            status=ResearchStatus.IN_PROGRESS,
        )

        mock_research = MagicMock()
        mock_research.start_research = AsyncMock(return_value=mock_result)

        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session_class.return_value = mock_session

        with patch("pynotebooklm.cli.ResearchDiscovery", return_value=mock_research):
            result = runner.invoke(app, ["research", "start", "nb-123", "AI trends"])

        assert result.exit_code == 0
        assert "Started research session" in result.output
        assert "task-123" in result.output

    @patch("pynotebooklm.cli.AuthManager")
    def test_start_not_authenticated(self, mock_auth_class: MagicMock) -> None:
        """Test research start when not authenticated."""
        mock_auth = MagicMock()
        mock_auth.is_authenticated.return_value = False
        mock_auth_class.return_value = mock_auth

        result = runner.invoke(app, ["research", "start", "nb-123", "AI trends"])

        assert result.exit_code == 1
        assert "Not authenticated" in result.output

    @patch("pynotebooklm.cli.BrowserSession")
    @patch("pynotebooklm.cli.AuthManager")
    def test_start_deep_mode(
        self, mock_auth_class: MagicMock, mock_session_class: MagicMock
    ) -> None:
        """Test research start with deep mode."""
        mock_auth = MagicMock()
        mock_auth.is_authenticated.return_value = True
        mock_auth_class.return_value = mock_auth

        mock_result = ResearchSession(
            task_id="task-deep",
            notebook_id="nb-123",
            query="AI trends",
            source="web",
            mode="deep",
            status=ResearchStatus.IN_PROGRESS,
        )

        mock_research = MagicMock()
        mock_research.start_research = AsyncMock(return_value=mock_result)

        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session_class.return_value = mock_session

        with patch("pynotebooklm.cli.ResearchDiscovery", return_value=mock_research):
            result = runner.invoke(
                app, ["research", "start", "nb-123", "AI trends", "--deep"]
            )

        assert result.exit_code == 0
        assert "deep" in result.output.lower()


class TestResearchPollCommand:
    """Tests for the 'research poll' command."""

    @patch("pynotebooklm.cli.BrowserSession")
    @patch("pynotebooklm.cli.AuthManager")
    def test_poll_completed(
        self, mock_auth_class: MagicMock, mock_session_class: MagicMock
    ) -> None:
        """Test polling completed research."""
        mock_auth = MagicMock()
        mock_auth.is_authenticated.return_value = True
        mock_auth_class.return_value = mock_auth

        mock_result = ResearchSession(
            task_id="task-123",
            notebook_id="nb-123",
            query="AI trends",
            source="web",
            mode="fast",
            status=ResearchStatus.COMPLETED,
            source_count=3,
            results=[
                ResearchResult(
                    index=0,
                    url="https://example.com/1",
                    title="Article 1",
                    description="Description 1",
                    result_type=1,
                    result_type_name="web",
                ),
                ResearchResult(
                    index=1,
                    url="https://example.com/2",
                    title="Article 2",
                    description="Description 2",
                    result_type=1,
                    result_type_name="web",
                ),
            ],
        )

        mock_research = MagicMock()
        mock_research.poll_research = AsyncMock(return_value=mock_result)

        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session_class.return_value = mock_session

        with patch("pynotebooklm.cli.ResearchDiscovery", return_value=mock_research):
            result = runner.invoke(app, ["research", "poll", "nb-123"])

        assert result.exit_code == 0
        assert "completed" in result.output.lower()
        assert "Article 1" in result.output

    @patch("pynotebooklm.cli.BrowserSession")
    @patch("pynotebooklm.cli.AuthManager")
    def test_poll_no_research(
        self, mock_auth_class: MagicMock, mock_session_class: MagicMock
    ) -> None:
        """Test polling when no research is found."""
        mock_auth = MagicMock()
        mock_auth.is_authenticated.return_value = True
        mock_auth_class.return_value = mock_auth

        mock_result = ResearchSession(
            task_id="",
            notebook_id="nb-123",
            query="",
            status=ResearchStatus.NO_RESEARCH,
        )

        mock_research = MagicMock()
        mock_research.poll_research = AsyncMock(return_value=mock_result)

        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session_class.return_value = mock_session

        with patch("pynotebooklm.cli.ResearchDiscovery", return_value=mock_research):
            result = runner.invoke(app, ["research", "poll", "nb-123"])

        assert result.exit_code == 0
        assert "No active research" in result.output

    @patch("pynotebooklm.cli.AuthManager")
    def test_poll_not_authenticated(self, mock_auth_class: MagicMock) -> None:
        """Test poll when not authenticated."""
        mock_auth = MagicMock()
        mock_auth.is_authenticated.return_value = False
        mock_auth_class.return_value = mock_auth

        result = runner.invoke(app, ["research", "poll", "nb-123"])

        assert result.exit_code == 1
        assert "Not authenticated" in result.output

    @patch("pynotebooklm.cli.BrowserSession")
    @patch("pynotebooklm.cli.AuthManager")
    def test_poll_with_auto_import(
        self, mock_auth_class: MagicMock, mock_session_class: MagicMock
    ) -> None:
        """Test polling with auto-import flag."""
        mock_auth = MagicMock()
        mock_auth.is_authenticated.return_value = True
        mock_auth_class.return_value = mock_auth

        mock_results = [
            ResearchResult(
                index=0,
                url="https://example.com/1",
                title="Article 1",
                description="Description 1",
                result_type=1,
                result_type_name="web",
            ),
        ]

        mock_poll_result = ResearchSession(
            task_id="task-123",
            notebook_id="nb-123",
            query="AI trends",
            source="web",
            mode="fast",
            status=ResearchStatus.COMPLETED,
            source_count=1,
            results=mock_results,
        )

        mock_imported = [
            ImportedSource(id="source-001", title="Article 1"),
        ]

        mock_research = MagicMock()
        mock_research.poll_research = AsyncMock(return_value=mock_poll_result)
        mock_research.import_research_sources = AsyncMock(return_value=mock_imported)

        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session_class.return_value = mock_session

        with patch("pynotebooklm.cli.ResearchDiscovery", return_value=mock_research):
            result = runner.invoke(app, ["research", "poll", "nb-123", "--auto-import"])

        assert result.exit_code == 0
        assert "Imported 1 sources" in result.output
        mock_research.import_research_sources.assert_called_once()

    @patch("pynotebooklm.cli.BrowserSession")
    @patch("pynotebooklm.cli.AuthManager")
    def test_poll_auto_import_skipped_when_in_progress(
        self, mock_auth_class: MagicMock, mock_session_class: MagicMock
    ) -> None:
        """Test auto-import is skipped when research is not completed."""
        mock_auth = MagicMock()
        mock_auth.is_authenticated.return_value = True
        mock_auth_class.return_value = mock_auth

        mock_result = ResearchSession(
            task_id="task-123",
            notebook_id="nb-123",
            query="AI trends",
            source="web",
            mode="fast",
            status=ResearchStatus.IN_PROGRESS,
            source_count=0,
            results=[],
        )

        mock_research = MagicMock()
        mock_research.poll_research = AsyncMock(return_value=mock_result)

        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session_class.return_value = mock_session

        with patch("pynotebooklm.cli.ResearchDiscovery", return_value=mock_research):
            result = runner.invoke(app, ["research", "poll", "nb-123", "--auto-import"])

        assert result.exit_code == 0
        assert "skipped" in result.output.lower()
        mock_research.import_research_sources.assert_not_called()


class TestResearchImportCommand:
    """Tests for the 'research import' command."""

    @patch("pynotebooklm.cli.BrowserSession")
    @patch("pynotebooklm.cli.AuthManager")
    def test_import_success(
        self, mock_auth_class: MagicMock, mock_session_class: MagicMock
    ) -> None:
        """Test successful research import."""
        mock_auth = MagicMock()
        mock_auth.is_authenticated.return_value = True
        mock_auth_class.return_value = mock_auth

        mock_results = [
            ResearchResult(
                index=0,
                url="https://example.com/1",
                title="Article 1",
                description="Description 1",
                result_type=1,
                result_type_name="web",
            ),
            ResearchResult(
                index=1,
                url="https://example.com/2",
                title="Article 2",
                description="Description 2",
                result_type=1,
                result_type_name="web",
            ),
        ]

        mock_poll_result = ResearchSession(
            task_id="task-123",
            notebook_id="nb-123",
            query="AI trends",
            source="web",
            mode="fast",
            status=ResearchStatus.COMPLETED,
            source_count=2,
            results=mock_results,
        )

        mock_imported = [
            ImportedSource(id="source-001", title="Article 1"),
            ImportedSource(id="source-002", title="Article 2"),
        ]

        mock_research = MagicMock()
        mock_research.poll_research = AsyncMock(return_value=mock_poll_result)
        mock_research.import_research_sources = AsyncMock(return_value=mock_imported)

        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session_class.return_value = mock_session

        with patch("pynotebooklm.cli.ResearchDiscovery", return_value=mock_research):
            result = runner.invoke(app, ["research", "import", "nb-123"])

        assert result.exit_code == 0
        assert "Successfully imported 2 sources" in result.output
        mock_research.import_research_sources.assert_called_once()

    @patch("pynotebooklm.cli.BrowserSession")
    @patch("pynotebooklm.cli.AuthManager")
    def test_import_with_indices(
        self, mock_auth_class: MagicMock, mock_session_class: MagicMock
    ) -> None:
        """Test importing specific sources by indices."""
        mock_auth = MagicMock()
        mock_auth.is_authenticated.return_value = True
        mock_auth_class.return_value = mock_auth

        mock_results = [
            ResearchResult(
                index=0,
                url="https://example.com/1",
                title="Article 1",
                description="Description 1",
                result_type=1,
                result_type_name="web",
            ),
            ResearchResult(
                index=1,
                url="https://example.com/2",
                title="Article 2",
                description="Description 2",
                result_type=1,
                result_type_name="web",
            ),
            ResearchResult(
                index=2,
                url="https://example.com/3",
                title="Article 3",
                description="Description 3",
                result_type=1,
                result_type_name="web",
            ),
        ]

        mock_poll_result = ResearchSession(
            task_id="task-123",
            notebook_id="nb-123",
            query="AI trends",
            source="web",
            mode="fast",
            status=ResearchStatus.COMPLETED,
            source_count=3,
            results=mock_results,
        )

        mock_imported = [
            ImportedSource(id="source-001", title="Article 1"),
            ImportedSource(id="source-003", title="Article 3"),
        ]

        mock_research = MagicMock()
        mock_research.poll_research = AsyncMock(return_value=mock_poll_result)
        mock_research.import_research_sources = AsyncMock(return_value=mock_imported)

        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session_class.return_value = mock_session

        with patch("pynotebooklm.cli.ResearchDiscovery", return_value=mock_research):
            result = runner.invoke(
                app, ["research", "import", "nb-123", "--indices", "0,2"]
            )

        assert result.exit_code == 0
        # Verify only indices 0 and 2 were passed
        call_args = mock_research.import_research_sources.call_args
        sources_passed = call_args.kwargs["sources"]
        assert len(sources_passed) == 2
        assert sources_passed[0].title == "Article 1"
        assert sources_passed[1].title == "Article 3"

    @patch("pynotebooklm.cli.BrowserSession")
    @patch("pynotebooklm.cli.AuthManager")
    def test_import_invalid_indices(
        self, mock_auth_class: MagicMock, mock_session_class: MagicMock
    ) -> None:
        """Test import with invalid indices."""
        mock_auth = MagicMock()
        mock_auth.is_authenticated.return_value = True
        mock_auth_class.return_value = mock_auth

        mock_results = [
            ResearchResult(
                index=0,
                url="https://example.com/1",
                title="Article 1",
                description="Description 1",
                result_type=1,
                result_type_name="web",
            ),
        ]

        mock_poll_result = ResearchSession(
            task_id="task-123",
            notebook_id="nb-123",
            query="AI trends",
            source="web",
            mode="fast",
            status=ResearchStatus.COMPLETED,
            source_count=1,
            results=mock_results,
        )

        mock_research = MagicMock()
        mock_research.poll_research = AsyncMock(return_value=mock_poll_result)

        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session_class.return_value = mock_session

        with patch("pynotebooklm.cli.ResearchDiscovery", return_value=mock_research):
            result = runner.invoke(
                app, ["research", "import", "nb-123", "--indices", "0,5"]
            )

        assert result.exit_code == 1
        assert "Invalid indices" in result.output

    @patch("pynotebooklm.cli.BrowserSession")
    @patch("pynotebooklm.cli.AuthManager")
    def test_import_invalid_indices_format(
        self, mock_auth_class: MagicMock, mock_session_class: MagicMock
    ) -> None:
        """Test import with invalid indices format."""
        mock_auth = MagicMock()
        mock_auth.is_authenticated.return_value = True
        mock_auth_class.return_value = mock_auth

        mock_results = [
            ResearchResult(
                index=0,
                url="https://example.com/1",
                title="Article 1",
                description="Description 1",
                result_type=1,
                result_type_name="web",
            ),
        ]

        mock_poll_result = ResearchSession(
            task_id="task-123",
            notebook_id="nb-123",
            query="AI trends",
            source="web",
            mode="fast",
            status=ResearchStatus.COMPLETED,
            source_count=1,
            results=mock_results,
        )

        mock_research = MagicMock()
        mock_research.poll_research = AsyncMock(return_value=mock_poll_result)

        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session_class.return_value = mock_session

        with patch("pynotebooklm.cli.ResearchDiscovery", return_value=mock_research):
            result = runner.invoke(
                app, ["research", "import", "nb-123", "--indices", "abc"]
            )

        assert result.exit_code == 1
        assert "Invalid indices format" in result.output

    @patch("pynotebooklm.cli.BrowserSession")
    @patch("pynotebooklm.cli.AuthManager")
    def test_import_no_research(
        self, mock_auth_class: MagicMock, mock_session_class: MagicMock
    ) -> None:
        """Test import when no research is found."""
        mock_auth = MagicMock()
        mock_auth.is_authenticated.return_value = True
        mock_auth_class.return_value = mock_auth

        mock_poll_result = ResearchSession(
            task_id="",
            notebook_id="nb-123",
            query="",
            status=ResearchStatus.NO_RESEARCH,
        )

        mock_research = MagicMock()
        mock_research.poll_research = AsyncMock(return_value=mock_poll_result)

        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session_class.return_value = mock_session

        with patch("pynotebooklm.cli.ResearchDiscovery", return_value=mock_research):
            result = runner.invoke(app, ["research", "import", "nb-123"])

        assert result.exit_code == 1
        assert "No research found" in result.output

    @patch("pynotebooklm.cli.BrowserSession")
    @patch("pynotebooklm.cli.AuthManager")
    def test_import_research_in_progress(
        self, mock_auth_class: MagicMock, mock_session_class: MagicMock
    ) -> None:
        """Test import when research is still in progress."""
        mock_auth = MagicMock()
        mock_auth.is_authenticated.return_value = True
        mock_auth_class.return_value = mock_auth

        mock_poll_result = ResearchSession(
            task_id="task-123",
            notebook_id="nb-123",
            query="AI trends",
            status=ResearchStatus.IN_PROGRESS,
        )

        mock_research = MagicMock()
        mock_research.poll_research = AsyncMock(return_value=mock_poll_result)

        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session_class.return_value = mock_session

        with patch("pynotebooklm.cli.ResearchDiscovery", return_value=mock_research):
            result = runner.invoke(app, ["research", "import", "nb-123"])

        assert result.exit_code == 1
        assert "in progress" in result.output.lower()

    @patch("pynotebooklm.cli.AuthManager")
    def test_import_not_authenticated(self, mock_auth_class: MagicMock) -> None:
        """Test import when not authenticated."""
        mock_auth = MagicMock()
        mock_auth.is_authenticated.return_value = False
        mock_auth_class.return_value = mock_auth

        result = runner.invoke(app, ["research", "import", "nb-123"])

        assert result.exit_code == 1
        assert "Not authenticated" in result.output

    @patch("pynotebooklm.cli.SourceManager")
    @patch("pynotebooklm.cli.BrowserSession")
    @patch("pynotebooklm.cli.AuthManager")
    def test_import_deep_research_with_report(
        self,
        mock_auth_class: MagicMock,
        mock_session_class: MagicMock,
        mock_source_manager_class: MagicMock,
    ) -> None:
        """Test importing deep research with report as text source."""
        mock_auth = MagicMock()
        mock_auth.is_authenticated.return_value = True
        mock_auth_class.return_value = mock_auth

        mock_results = [
            ResearchResult(
                index=0,
                url="https://example.com/1",
                title="Article 1",
                description="Description 1",
                result_type=1,
                result_type_name="web",
            ),
        ]

        mock_poll_result = ResearchSession(
            task_id="task-123",
            notebook_id="nb-123",
            query="AI trends",
            source="web",
            mode="deep",
            status=ResearchStatus.COMPLETED,
            source_count=1,
            results=mock_results,
            report="# Deep Research Report\n\nThis is the AI-generated report...",
        )

        mock_imported = [
            ImportedSource(id="source-001", title="Article 1"),
        ]

        mock_research = MagicMock()
        mock_research.poll_research = AsyncMock(return_value=mock_poll_result)
        mock_research.import_research_sources = AsyncMock(return_value=mock_imported)

        mock_source_manager = MagicMock()
        mock_source_manager.add_text = AsyncMock(return_value=MagicMock(id="text-001"))
        mock_source_manager_class.return_value = mock_source_manager

        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session_class.return_value = mock_session

        with patch("pynotebooklm.cli.ResearchDiscovery", return_value=mock_research):
            result = runner.invoke(app, ["research", "import", "nb-123"])

        assert result.exit_code == 0
        # Check that deep research handling was triggered (may warn or succeed)
        assert "deep research" in result.output.lower()


class TestResearchCommandHelp:
    """Tests for research command help output."""

    def test_research_help(self) -> None:
        """Test research command shows help."""
        result = runner.invoke(app, ["research", "--help"])

        assert result.exit_code == 0
        assert "start" in result.output
        assert "poll" in result.output
        assert "import" in result.output

    def test_start_help(self) -> None:
        """Test start command shows help."""
        result = runner.invoke(app, ["research", "start", "--help"])

        assert result.exit_code == 0
        assert "topic" in result.output.lower() or "query" in result.output.lower()
        assert "deep" in result.output.lower()

    def test_poll_help(self) -> None:
        """Test poll command shows help."""
        result = runner.invoke(app, ["research", "poll", "--help"])

        assert result.exit_code == 0
        assert "auto-import" in result.output.lower()

    def test_import_help(self) -> None:
        """Test import command shows help."""
        result = runner.invoke(app, ["research", "import", "--help"])

        assert result.exit_code == 0
        assert "indices" in result.output.lower()
        assert "report" in result.output.lower()
