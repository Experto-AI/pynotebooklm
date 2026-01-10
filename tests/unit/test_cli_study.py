"""Unit tests for the study CLI commands."""

from unittest.mock import AsyncMock, MagicMock, patch

from typer.testing import CliRunner

from pynotebooklm.cli import app
from pynotebooklm.study import FlashcardDifficulty

runner = CliRunner()


class TestFlashcardsCommand:
    """Tests for the 'study flashcards' command."""

    @patch("pynotebooklm.cli.BrowserSession")
    @patch("pynotebooklm.cli.AuthManager")
    def test_flashcards_success(
        self, mock_auth_class: MagicMock, mock_session_class: MagicMock
    ) -> None:
        """Test successful flashcard creation."""
        # Set up mocks
        mock_auth = MagicMock()
        mock_auth.is_authenticated.return_value = True
        mock_auth_class.return_value = mock_auth

        # Mock notebook with sources
        mock_notebook = MagicMock()
        mock_source = MagicMock()
        mock_source.id = "src-123"
        mock_notebook.sources = [mock_source]

        # Mock managers
        mock_notebook_manager = MagicMock()
        mock_notebook_manager.get = AsyncMock(return_value=mock_notebook)

        mock_result = MagicMock()
        mock_result.artifact_id = "artifact-123"
        mock_result.difficulty = "medium"
        mock_result.status = "in_progress"

        mock_study_manager = MagicMock()
        mock_study_manager.create_flashcards = AsyncMock(return_value=mock_result)

        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session_class.return_value = mock_session

        with patch(
            "pynotebooklm.cli.NotebookManager", return_value=mock_notebook_manager
        ):
            with patch(
                "pynotebooklm.cli.StudyManager", return_value=mock_study_manager
            ):
                result = runner.invoke(app, ["study", "flashcards", "nb-123"])

        assert result.exit_code == 0
        assert "Flashcard generation started" in result.output
        assert "artifact-123" in result.output

    @patch("pynotebooklm.cli.AuthManager")
    def test_flashcards_not_authenticated(self, mock_auth_class: MagicMock) -> None:
        """Test flashcards command when not authenticated."""
        mock_auth = MagicMock()
        mock_auth.is_authenticated.return_value = False
        mock_auth_class.return_value = mock_auth

        result = runner.invoke(app, ["study", "flashcards", "nb-123"])

        assert result.exit_code == 1
        assert "Not authenticated" in result.output

    @patch("pynotebooklm.cli.BrowserSession")
    @patch("pynotebooklm.cli.AuthManager")
    def test_flashcards_with_difficulty(
        self, mock_auth_class: MagicMock, mock_session_class: MagicMock
    ) -> None:
        """Test flashcard creation with specific difficulty."""
        mock_auth = MagicMock()
        mock_auth.is_authenticated.return_value = True
        mock_auth_class.return_value = mock_auth

        mock_notebook = MagicMock()
        mock_source = MagicMock()
        mock_source.id = "src-123"
        mock_notebook.sources = [mock_source]

        mock_notebook_manager = MagicMock()
        mock_notebook_manager.get = AsyncMock(return_value=mock_notebook)

        mock_result = MagicMock()
        mock_result.artifact_id = "artifact-hard"
        mock_result.difficulty = "hard"
        mock_result.status = "in_progress"

        mock_study_manager = MagicMock()
        mock_study_manager.create_flashcards = AsyncMock(return_value=mock_result)

        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session_class.return_value = mock_session

        with patch(
            "pynotebooklm.cli.NotebookManager", return_value=mock_notebook_manager
        ):
            with patch(
                "pynotebooklm.cli.StudyManager", return_value=mock_study_manager
            ):
                result = runner.invoke(
                    app, ["study", "flashcards", "nb-123", "--difficulty", "hard"]
                )

        assert result.exit_code == 0
        # Verify create_flashcards was called with correct difficulty
        call_kwargs = mock_study_manager.create_flashcards.call_args.kwargs
        assert call_kwargs["difficulty"] == FlashcardDifficulty.HARD

    @patch("pynotebooklm.cli.AuthManager")
    def test_flashcards_invalid_difficulty(self, mock_auth_class: MagicMock) -> None:
        """Test flashcards command with invalid difficulty."""
        mock_auth = MagicMock()
        mock_auth.is_authenticated.return_value = True
        mock_auth_class.return_value = mock_auth

        result = runner.invoke(
            app, ["study", "flashcards", "nb-123", "--difficulty", "insane"]
        )

        assert result.exit_code == 1
        assert "Invalid difficulty" in result.output

    @patch("pynotebooklm.cli.BrowserSession")
    @patch("pynotebooklm.cli.AuthManager")
    def test_flashcards_notebook_not_found(
        self, mock_auth_class: MagicMock, mock_session_class: MagicMock
    ) -> None:
        """Test flashcards when notebook is not found."""
        mock_auth = MagicMock()
        mock_auth.is_authenticated.return_value = True
        mock_auth_class.return_value = mock_auth

        mock_notebook_manager = MagicMock()
        mock_notebook_manager.get = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session_class.return_value = mock_session

        with patch(
            "pynotebooklm.cli.NotebookManager", return_value=mock_notebook_manager
        ):
            result = runner.invoke(app, ["study", "flashcards", "nb-123"])

        assert result.exit_code == 1
        assert "Notebook not found" in result.output

    @patch("pynotebooklm.cli.BrowserSession")
    @patch("pynotebooklm.cli.AuthManager")
    def test_flashcards_no_sources(
        self, mock_auth_class: MagicMock, mock_session_class: MagicMock
    ) -> None:
        """Test flashcards when notebook has no sources."""
        mock_auth = MagicMock()
        mock_auth.is_authenticated.return_value = True
        mock_auth_class.return_value = mock_auth

        mock_notebook = MagicMock()
        mock_notebook.sources = []  # No sources

        mock_notebook_manager = MagicMock()
        mock_notebook_manager.get = AsyncMock(return_value=mock_notebook)

        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session_class.return_value = mock_session

        with patch(
            "pynotebooklm.cli.NotebookManager", return_value=mock_notebook_manager
        ):
            result = runner.invoke(app, ["study", "flashcards", "nb-123"])

        assert result.exit_code == 1
        assert "No sources found" in result.output


class TestQuizCommand:
    """Tests for the 'study quiz' command."""

    @patch("pynotebooklm.cli.BrowserSession")
    @patch("pynotebooklm.cli.AuthManager")
    def test_quiz_success(
        self, mock_auth_class: MagicMock, mock_session_class: MagicMock
    ) -> None:
        """Test successful quiz creation."""
        mock_auth = MagicMock()
        mock_auth.is_authenticated.return_value = True
        mock_auth_class.return_value = mock_auth

        mock_notebook = MagicMock()
        mock_source = MagicMock()
        mock_source.id = "src-123"
        mock_notebook.sources = [mock_source]

        mock_notebook_manager = MagicMock()
        mock_notebook_manager.get = AsyncMock(return_value=mock_notebook)

        mock_result = MagicMock()
        mock_result.artifact_id = "quiz-123"
        mock_result.question_count = 2
        mock_result.difficulty = 2
        mock_result.status = "in_progress"

        mock_study_manager = MagicMock()
        mock_study_manager.create_quiz = AsyncMock(return_value=mock_result)

        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session_class.return_value = mock_session

        with patch(
            "pynotebooklm.cli.NotebookManager", return_value=mock_notebook_manager
        ):
            with patch(
                "pynotebooklm.cli.StudyManager", return_value=mock_study_manager
            ):
                result = runner.invoke(app, ["study", "quiz", "nb-123"])

        assert result.exit_code == 0
        assert "Quiz generation started" in result.output
        assert "quiz-123" in result.output

    @patch("pynotebooklm.cli.BrowserSession")
    @patch("pynotebooklm.cli.AuthManager")
    def test_quiz_custom_questions(
        self, mock_auth_class: MagicMock, mock_session_class: MagicMock
    ) -> None:
        """Test quiz creation with custom question count."""
        mock_auth = MagicMock()
        mock_auth.is_authenticated.return_value = True
        mock_auth_class.return_value = mock_auth

        mock_notebook = MagicMock()
        mock_source = MagicMock()
        mock_source.id = "src-123"
        mock_notebook.sources = [mock_source]

        mock_notebook_manager = MagicMock()
        mock_notebook_manager.get = AsyncMock(return_value=mock_notebook)

        mock_result = MagicMock()
        mock_result.artifact_id = "quiz-10"
        mock_result.question_count = 10
        mock_result.difficulty = 2
        mock_result.status = "in_progress"

        mock_study_manager = MagicMock()
        mock_study_manager.create_quiz = AsyncMock(return_value=mock_result)

        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session_class.return_value = mock_session

        with patch(
            "pynotebooklm.cli.NotebookManager", return_value=mock_notebook_manager
        ):
            with patch(
                "pynotebooklm.cli.StudyManager", return_value=mock_study_manager
            ):
                result = runner.invoke(
                    app, ["study", "quiz", "nb-123", "--questions", "10"]
                )

        assert result.exit_code == 0
        call_kwargs = mock_study_manager.create_quiz.call_args.kwargs
        assert call_kwargs["question_count"] == 10

    @patch("pynotebooklm.cli.AuthManager")
    def test_quiz_not_authenticated(self, mock_auth_class: MagicMock) -> None:
        """Test quiz command when not authenticated."""
        mock_auth = MagicMock()
        mock_auth.is_authenticated.return_value = False
        mock_auth_class.return_value = mock_auth

        result = runner.invoke(app, ["study", "quiz", "nb-123"])

        assert result.exit_code == 1
        assert "Not authenticated" in result.output

    @patch("pynotebooklm.cli.BrowserSession")
    @patch("pynotebooklm.cli.AuthManager")
    def test_quiz_notebook_not_found(
        self, mock_auth_class: MagicMock, mock_session_class: MagicMock
    ) -> None:
        """Test quiz when notebook is not found."""
        mock_auth = MagicMock()
        mock_auth.is_authenticated.return_value = True
        mock_auth_class.return_value = mock_auth

        mock_notebook_manager = MagicMock()
        mock_notebook_manager.get = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session_class.return_value = mock_session

        with patch(
            "pynotebooklm.cli.NotebookManager", return_value=mock_notebook_manager
        ):
            result = runner.invoke(app, ["study", "quiz", "nb-123"])

        assert result.exit_code == 1
        assert "Notebook not found" in result.output

    @patch("pynotebooklm.cli.BrowserSession")
    @patch("pynotebooklm.cli.AuthManager")
    def test_quiz_no_sources(
        self, mock_auth_class: MagicMock, mock_session_class: MagicMock
    ) -> None:
        """Test quiz when notebook has no sources."""
        mock_auth = MagicMock()
        mock_auth.is_authenticated.return_value = True
        mock_auth_class.return_value = mock_auth

        mock_notebook = MagicMock()
        mock_notebook.sources = []  # No sources

        mock_notebook_manager = MagicMock()
        mock_notebook_manager.get = AsyncMock(return_value=mock_notebook)

        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session_class.return_value = mock_session

        with patch(
            "pynotebooklm.cli.NotebookManager", return_value=mock_notebook_manager
        ):
            result = runner.invoke(app, ["study", "quiz", "nb-123"])

        assert result.exit_code == 1
        assert "No sources found" in result.output


class TestDataTableCommand:
    """Tests for the 'study table' command."""

    @patch("pynotebooklm.cli.BrowserSession")
    @patch("pynotebooklm.cli.AuthManager")
    def test_data_table_success(
        self, mock_auth_class: MagicMock, mock_session_class: MagicMock
    ) -> None:
        """Test successful data table creation."""
        mock_auth = MagicMock()
        mock_auth.is_authenticated.return_value = True
        mock_auth_class.return_value = mock_auth

        mock_notebook = MagicMock()
        mock_source = MagicMock()
        mock_source.id = "src-123"
        mock_notebook.sources = [mock_source]

        mock_notebook_manager = MagicMock()
        mock_notebook_manager.get = AsyncMock(return_value=mock_notebook)

        mock_result = MagicMock()
        mock_result.artifact_id = "table-123"
        mock_result.description = "Extract dates"
        mock_result.language = "en"
        mock_result.status = "in_progress"

        mock_study_manager = MagicMock()
        mock_study_manager.create_data_table = AsyncMock(return_value=mock_result)

        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session_class.return_value = mock_session

        with patch(
            "pynotebooklm.cli.NotebookManager", return_value=mock_notebook_manager
        ):
            with patch(
                "pynotebooklm.cli.StudyManager", return_value=mock_study_manager
            ):
                result = runner.invoke(
                    app,
                    ["study", "table", "nb-123", "--description", "Extract dates"],
                )

        assert result.exit_code == 0
        assert "Data table generation started" in result.output
        assert "table-123" in result.output

    def test_data_table_missing_description(self) -> None:
        """Test data table command without required description."""
        result = runner.invoke(app, ["study", "table", "nb-123"])

        # Should fail because --description is required
        assert result.exit_code != 0
        assert "Missing option" in result.output or "required" in result.output.lower()

    @patch("pynotebooklm.cli.BrowserSession")
    @patch("pynotebooklm.cli.AuthManager")
    def test_data_table_with_language(
        self, mock_auth_class: MagicMock, mock_session_class: MagicMock
    ) -> None:
        """Test data table creation with specific language."""
        mock_auth = MagicMock()
        mock_auth.is_authenticated.return_value = True
        mock_auth_class.return_value = mock_auth

        mock_notebook = MagicMock()
        mock_source = MagicMock()
        mock_source.id = "src-123"
        mock_notebook.sources = [mock_source]

        mock_notebook_manager = MagicMock()
        mock_notebook_manager.get = AsyncMock(return_value=mock_notebook)

        mock_result = MagicMock()
        mock_result.artifact_id = "table-es"
        mock_result.description = "Extraer fechas"
        mock_result.language = "es"
        mock_result.status = "in_progress"

        mock_study_manager = MagicMock()
        mock_study_manager.create_data_table = AsyncMock(return_value=mock_result)

        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session_class.return_value = mock_session

        with patch(
            "pynotebooklm.cli.NotebookManager", return_value=mock_notebook_manager
        ):
            with patch(
                "pynotebooklm.cli.StudyManager", return_value=mock_study_manager
            ):
                result = runner.invoke(
                    app,
                    [
                        "study",
                        "table",
                        "nb-123",
                        "--description",
                        "Extraer fechas",
                        "--language",
                        "es",
                    ],
                )

        assert result.exit_code == 0
        call_kwargs = mock_study_manager.create_data_table.call_args.kwargs
        assert call_kwargs["language"] == "es"

    @patch("pynotebooklm.cli.AuthManager")
    def test_data_table_not_authenticated(self, mock_auth_class: MagicMock) -> None:
        """Test data table command when not authenticated."""
        mock_auth = MagicMock()
        mock_auth.is_authenticated.return_value = False
        mock_auth_class.return_value = mock_auth

        result = runner.invoke(app, ["study", "table", "nb-123", "--description", "."])

        assert result.exit_code == 1
        assert "Not authenticated" in result.output

    @patch("pynotebooklm.cli.BrowserSession")
    @patch("pynotebooklm.cli.AuthManager")
    def test_data_table_notebook_not_found(
        self, mock_auth_class: MagicMock, mock_session_class: MagicMock
    ) -> None:
        """Test data table when notebook is not found."""
        mock_auth = MagicMock()
        mock_auth.is_authenticated.return_value = True
        mock_auth_class.return_value = mock_auth

        mock_notebook_manager = MagicMock()
        mock_notebook_manager.get = AsyncMock(return_value=None)

        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session_class.return_value = mock_session

        with patch(
            "pynotebooklm.cli.NotebookManager", return_value=mock_notebook_manager
        ):
            result = runner.invoke(
                app, ["study", "table", "nb-123", "--description", "."]
            )

        assert result.exit_code == 1
        assert "Notebook not found" in result.output

    @patch("pynotebooklm.cli.BrowserSession")
    @patch("pynotebooklm.cli.AuthManager")
    def test_data_table_no_sources(
        self, mock_auth_class: MagicMock, mock_session_class: MagicMock
    ) -> None:
        """Test data table when notebook has no sources."""
        mock_auth = MagicMock()
        mock_auth.is_authenticated.return_value = True
        mock_auth_class.return_value = mock_auth

        mock_notebook = MagicMock()
        mock_notebook.sources = []  # No sources

        mock_notebook_manager = MagicMock()
        mock_notebook_manager.get = AsyncMock(return_value=mock_notebook)

        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session_class.return_value = mock_session

        with patch(
            "pynotebooklm.cli.NotebookManager", return_value=mock_notebook_manager
        ):
            result = runner.invoke(
                app, ["study", "table", "nb-123", "--description", "."]
            )

        assert result.exit_code == 1
        assert "No sources found" in result.output


class TestStudyCommandHelp:
    """Tests for study command help output."""

    def test_study_help(self) -> None:
        """Test study command shows help."""
        result = runner.invoke(app, ["study", "--help"])

        assert result.exit_code == 0
        assert "flashcards" in result.output
        assert "quiz" in result.output
        assert "table" in result.output

    def test_flashcards_help(self) -> None:
        """Test flashcards command shows help."""
        result = runner.invoke(app, ["study", "flashcards", "--help"])

        assert result.exit_code == 0
        assert "difficulty" in result.output
        assert "easy" in result.output or "medium" in result.output

    def test_quiz_help(self) -> None:
        """Test quiz command shows help."""
        result = runner.invoke(app, ["study", "quiz", "--help"])

        assert result.exit_code == 0
        assert "questions" in result.output
        assert "difficulty" in result.output

    def test_table_help(self) -> None:
        """Test table command shows help."""
        result = runner.invoke(app, ["study", "table", "--help"])

        assert result.exit_code == 0
        assert "description" in result.output
        assert "language" in result.output
