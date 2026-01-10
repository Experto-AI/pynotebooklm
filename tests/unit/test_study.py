"""Unit tests for the study module."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from pynotebooklm.exceptions import GenerationError
from pynotebooklm.study import (
    STATUS_COMPLETED,
    STATUS_IN_PROGRESS,
    DataTableCreateResult,
    FlashcardCreateResult,
    FlashcardDifficulty,
    QuizCreateResult,
    StudyManager,
)


class TestFlashcardDifficulty:
    """Tests for FlashcardDifficulty enum."""

    def test_easy_value(self) -> None:
        """Test easy difficulty value."""
        assert FlashcardDifficulty.EASY.value == "easy"

    def test_medium_value(self) -> None:
        """Test medium difficulty value."""
        assert FlashcardDifficulty.MEDIUM.value == "medium"

    def test_hard_value(self) -> None:
        """Test hard difficulty value."""
        assert FlashcardDifficulty.HARD.value == "hard"


class TestFlashcardCreateResult:
    """Tests for FlashcardCreateResult model."""

    def test_create_result_fields(self) -> None:
        """Test creating a result with required fields."""
        result = FlashcardCreateResult(
            artifact_id="abc-123",
            notebook_id="nb-456",
            status="in_progress",
            difficulty="medium",
        )
        assert result.artifact_id == "abc-123"
        assert result.notebook_id == "nb-456"
        assert result.status == "in_progress"
        assert result.difficulty == "medium"


class TestQuizCreateResult:
    """Tests for QuizCreateResult model."""

    def test_create_result_fields(self) -> None:
        """Test creating a result with required fields."""
        result = QuizCreateResult(
            artifact_id="quiz-123",
            notebook_id="nb-456",
            status="in_progress",
            question_count=5,
            difficulty=2,
        )
        assert result.artifact_id == "quiz-123"
        assert result.notebook_id == "nb-456"
        assert result.status == "in_progress"
        assert result.question_count == 5
        assert result.difficulty == 2


class TestDataTableCreateResult:
    """Tests for DataTableCreateResult model."""

    def test_create_result_fields(self) -> None:
        """Test creating a result with required fields."""
        result = DataTableCreateResult(
            artifact_id="table-123",
            notebook_id="nb-456",
            status="completed",
            description="Extract key dates",
            language="en",
        )
        assert result.artifact_id == "table-123"
        assert result.notebook_id == "nb-456"
        assert result.status == "completed"
        assert result.description == "Extract key dates"
        assert result.language == "en"


class TestStudyManagerCreateFlashcards:
    """Tests for StudyManager.create_flashcards method."""

    @pytest.fixture
    def mock_session(self) -> MagicMock:
        """Create a mock session."""
        session = MagicMock()
        session.call_rpc = AsyncMock()
        return session

    @pytest.mark.asyncio
    async def test_create_flashcards_success(self, mock_session: MagicMock) -> None:
        """Test successful flashcard creation."""
        mock_session.call_rpc.return_value = [
            ["artifact-123", "Flashcards", 4, None, STATUS_IN_PROGRESS]
        ]

        manager = StudyManager(mock_session)
        result = await manager.create_flashcards(
            notebook_id="nb-123",
            source_ids=["src-1", "src-2"],
            difficulty=FlashcardDifficulty.MEDIUM,
        )

        assert result.artifact_id == "artifact-123"
        assert result.notebook_id == "nb-123"
        assert result.status == "in_progress"
        assert result.difficulty == "medium"

        # Verify RPC was called correctly
        mock_session.call_rpc.assert_called_once()
        call_args = mock_session.call_rpc.call_args
        assert call_args[0][0] == "R7cb6c"  # RPC_CREATE_STUDIO

    @pytest.mark.asyncio
    async def test_create_flashcards_easy_difficulty(
        self, mock_session: MagicMock
    ) -> None:
        """Test flashcard creation with easy difficulty."""
        mock_session.call_rpc.return_value = [
            ["artifact-easy", "Flashcards", 4, None, STATUS_IN_PROGRESS]
        ]

        manager = StudyManager(mock_session)
        result = await manager.create_flashcards(
            notebook_id="nb-123",
            source_ids=["src-1"],
            difficulty=FlashcardDifficulty.EASY,
        )

        assert result.difficulty == "easy"

    @pytest.mark.asyncio
    async def test_create_flashcards_hard_difficulty(
        self, mock_session: MagicMock
    ) -> None:
        """Test flashcard creation with hard difficulty."""
        mock_session.call_rpc.return_value = [
            ["artifact-hard", "Flashcards", 4, None, STATUS_IN_PROGRESS]
        ]

        manager = StudyManager(mock_session)
        result = await manager.create_flashcards(
            notebook_id="nb-123",
            source_ids=["src-1"],
            difficulty=FlashcardDifficulty.HARD,
        )

        assert result.difficulty == "hard"

    @pytest.mark.asyncio
    async def test_create_flashcards_completed_status(
        self, mock_session: MagicMock
    ) -> None:
        """Test flashcard creation with completed status."""
        mock_session.call_rpc.return_value = [
            ["artifact-123", "Flashcards", 4, None, STATUS_COMPLETED]
        ]

        manager = StudyManager(mock_session)
        result = await manager.create_flashcards(
            notebook_id="nb-123",
            source_ids=["src-1"],
        )

        assert result.status == "completed"

    @pytest.mark.asyncio
    async def test_create_flashcards_no_sources(self, mock_session: MagicMock) -> None:
        """Test flashcard creation with no sources raises error."""
        manager = StudyManager(mock_session)

        with pytest.raises(GenerationError, match="At least one source ID is required"):
            await manager.create_flashcards(
                notebook_id="nb-123",
                source_ids=[],
            )

    @pytest.mark.asyncio
    async def test_create_flashcards_rpc_error(self, mock_session: MagicMock) -> None:
        """Test flashcard creation when RPC fails."""
        mock_session.call_rpc.side_effect = Exception("RPC failed")

        manager = StudyManager(mock_session)

        with pytest.raises(GenerationError, match="Failed to create flashcards"):
            await manager.create_flashcards(
                notebook_id="nb-123",
                source_ids=["src-1"],
            )


class TestStudyManagerCreateQuiz:
    """Tests for StudyManager.create_quiz method."""

    @pytest.fixture
    def mock_session(self) -> MagicMock:
        """Create a mock session."""
        session = MagicMock()
        session.call_rpc = AsyncMock()
        return session

    @pytest.mark.asyncio
    async def test_create_quiz_success(self, mock_session: MagicMock) -> None:
        """Test successful quiz creation."""
        mock_session.call_rpc.return_value = [
            ["quiz-123", "Quiz", 4, None, STATUS_IN_PROGRESS]
        ]

        manager = StudyManager(mock_session)
        result = await manager.create_quiz(
            notebook_id="nb-123",
            source_ids=["src-1", "src-2"],
            question_count=5,
            difficulty=2,
        )

        assert result.artifact_id == "quiz-123"
        assert result.notebook_id == "nb-123"
        assert result.status == "in_progress"
        assert result.question_count == 5
        assert result.difficulty == 2

    @pytest.mark.asyncio
    async def test_create_quiz_default_params(self, mock_session: MagicMock) -> None:
        """Test quiz creation with default parameters."""
        mock_session.call_rpc.return_value = [
            ["quiz-default", "Quiz", 4, None, STATUS_IN_PROGRESS]
        ]

        manager = StudyManager(mock_session)
        result = await manager.create_quiz(
            notebook_id="nb-123",
            source_ids=["src-1"],
        )

        assert result.question_count == 2
        assert result.difficulty == 2

    @pytest.mark.asyncio
    async def test_create_quiz_custom_questions(self, mock_session: MagicMock) -> None:
        """Test quiz creation with custom question count."""
        mock_session.call_rpc.return_value = [
            ["quiz-123", "Quiz", 4, None, STATUS_IN_PROGRESS]
        ]

        manager = StudyManager(mock_session)
        result = await manager.create_quiz(
            notebook_id="nb-123",
            source_ids=["src-1"],
            question_count=10,
        )

        assert result.question_count == 10

    @pytest.mark.asyncio
    async def test_create_quiz_no_sources(self, mock_session: MagicMock) -> None:
        """Test quiz creation with no sources raises error."""
        manager = StudyManager(mock_session)

        with pytest.raises(GenerationError, match="At least one source ID is required"):
            await manager.create_quiz(
                notebook_id="nb-123",
                source_ids=[],
            )

    @pytest.mark.asyncio
    async def test_create_quiz_rpc_error(self, mock_session: MagicMock) -> None:
        """Test quiz creation when RPC fails."""
        mock_session.call_rpc.side_effect = Exception("RPC failed")

        manager = StudyManager(mock_session)

        with pytest.raises(GenerationError, match="Failed to create quiz"):
            await manager.create_quiz(
                notebook_id="nb-123",
                source_ids=["src-1"],
            )


class TestStudyManagerCreateDataTable:
    """Tests for StudyManager.create_data_table method."""

    @pytest.fixture
    def mock_session(self) -> MagicMock:
        """Create a mock session."""
        session = MagicMock()
        session.call_rpc = AsyncMock()
        return session

    @pytest.mark.asyncio
    async def test_create_data_table_success(self, mock_session: MagicMock) -> None:
        """Test successful data table creation."""
        mock_session.call_rpc.return_value = [
            ["table-123", "Data Table", 9, None, STATUS_IN_PROGRESS]
        ]

        manager = StudyManager(mock_session)
        result = await manager.create_data_table(
            notebook_id="nb-123",
            source_ids=["src-1", "src-2"],
            description="Extract key dates and events",
            language="en",
        )

        assert result.artifact_id == "table-123"
        assert result.notebook_id == "nb-123"
        assert result.status == "in_progress"
        assert result.description == "Extract key dates and events"
        assert result.language == "en"

    @pytest.mark.asyncio
    async def test_create_data_table_spanish(self, mock_session: MagicMock) -> None:
        """Test data table creation in Spanish."""
        mock_session.call_rpc.return_value = [
            ["table-es", "Data Table", 9, None, STATUS_IN_PROGRESS]
        ]

        manager = StudyManager(mock_session)
        result = await manager.create_data_table(
            notebook_id="nb-123",
            source_ids=["src-1"],
            description="Lista de eventos",
            language="es",
        )

        assert result.language == "es"

    @pytest.mark.asyncio
    async def test_create_data_table_no_sources(self, mock_session: MagicMock) -> None:
        """Test data table creation with no sources raises error."""
        manager = StudyManager(mock_session)

        with pytest.raises(GenerationError, match="At least one source ID is required"):
            await manager.create_data_table(
                notebook_id="nb-123",
                source_ids=[],
                description="Extract data",
            )

    @pytest.mark.asyncio
    async def test_create_data_table_no_description(
        self, mock_session: MagicMock
    ) -> None:
        """Test data table creation with no description raises error."""
        manager = StudyManager(mock_session)

        with pytest.raises(
            GenerationError, match="Description is required for data table creation"
        ):
            await manager.create_data_table(
                notebook_id="nb-123",
                source_ids=["src-1"],
                description="",
            )

    @pytest.mark.asyncio
    async def test_create_data_table_rpc_error(self, mock_session: MagicMock) -> None:
        """Test data table creation when RPC fails."""
        mock_session.call_rpc.side_effect = Exception("RPC failed")

        manager = StudyManager(mock_session)

        with pytest.raises(GenerationError, match="Failed to create data table"):
            await manager.create_data_table(
                notebook_id="nb-123",
                source_ids=["src-1"],
                description="Extract data",
            )


class TestStudyManagerResultParsing:
    """Tests for result parsing edge cases."""

    @pytest.fixture
    def mock_session(self) -> MagicMock:
        """Create a mock session."""
        session = MagicMock()
        session.call_rpc = AsyncMock()
        return session

    @pytest.mark.asyncio
    async def test_parse_invalid_response_empty(self, mock_session: MagicMock) -> None:
        """Test parsing empty response."""
        mock_session.call_rpc.return_value = []

        manager = StudyManager(mock_session)

        with pytest.raises(GenerationError, match="Invalid response"):
            await manager.create_flashcards(
                notebook_id="nb-123",
                source_ids=["src-1"],
            )

    @pytest.mark.asyncio
    async def test_parse_invalid_response_none(self, mock_session: MagicMock) -> None:
        """Test parsing None response."""
        mock_session.call_rpc.return_value = None

        manager = StudyManager(mock_session)

        with pytest.raises(GenerationError, match="Invalid response"):
            await manager.create_flashcards(
                notebook_id="nb-123",
                source_ids=["src-1"],
            )

    @pytest.mark.asyncio
    async def test_parse_unknown_status(self, mock_session: MagicMock) -> None:
        """Test parsing unknown status code."""
        mock_session.call_rpc.return_value = [
            ["artifact-123", "Flashcards", 4, None, 99]  # Unknown status
        ]

        manager = StudyManager(mock_session)
        result = await manager.create_flashcards(
            notebook_id="nb-123",
            source_ids=["src-1"],
        )

        assert result.status == "unknown"

    @pytest.mark.asyncio
    async def test_parse_short_artifact_data(self, mock_session: MagicMock) -> None:
        """Test parsing artifact data with missing status."""
        mock_session.call_rpc.return_value = [
            ["artifact-123", "Flashcards"]  # Missing status
        ]

        manager = StudyManager(mock_session)
        result = await manager.create_flashcards(
            notebook_id="nb-123",
            source_ids=["src-1"],
        )

        # Should handle gracefully with unknown status
        assert result.artifact_id == "artifact-123"
        assert result.status == "unknown"


class TestStudyManagerHelperFunctions:
    """Tests for private helper functions in study module."""

    def test_code_to_difficulty(self) -> None:
        """Test _code_to_difficulty mapping."""
        from pynotebooklm.study import _code_to_difficulty

        assert _code_to_difficulty(1) == "easy"
        assert _code_to_difficulty(2) == "medium"
        assert _code_to_difficulty(3) == "hard"
        assert _code_to_difficulty(99) == "medium"  # default


class TestStudyManagerResultParsingExt:
    """Extended tests for result parsing edge cases in StudyManager."""

    @pytest.fixture
    def mock_session(self) -> MagicMock:
        """Create a mock session."""
        session = MagicMock()
        session.call_rpc = AsyncMock()
        return session

    @pytest.mark.asyncio
    async def test_parse_quiz_invalid_response_empty(
        self, mock_session: MagicMock
    ) -> None:
        """Test parsing empty quiz response."""
        mock_session.call_rpc.return_value = []
        manager = StudyManager(mock_session)
        with pytest.raises(
            GenerationError, match="Invalid response when creating quiz"
        ):
            await manager.create_quiz("nb", ["src"])

    @pytest.mark.asyncio
    async def test_parse_quiz_invalid_artifact_data(
        self, mock_session: MagicMock
    ) -> None:
        """Test parsing invalid artifact data in quiz response."""
        mock_session.call_rpc.return_value = [[]]
        manager = StudyManager(mock_session)
        with pytest.raises(
            GenerationError, match="Invalid artifact data when creating quiz"
        ):
            await manager.create_quiz("nb", ["src"])

    @pytest.mark.asyncio
    async def test_parse_data_table_invalid_response_empty(
        self, mock_session: MagicMock
    ) -> None:
        """Test parsing empty data table response."""
        mock_session.call_rpc.return_value = []
        manager = StudyManager(mock_session)
        with pytest.raises(
            GenerationError, match="Invalid response when creating data table"
        ):
            await manager.create_data_table("nb", ["src"], "desc")

    @pytest.mark.asyncio
    async def test_parse_data_table_invalid_artifact_data(
        self, mock_session: MagicMock
    ) -> None:
        """Test parsing invalid artifact data in data table response."""
        mock_session.call_rpc.return_value = [[]]
        manager = StudyManager(mock_session)
        with pytest.raises(
            GenerationError, match="Invalid artifact data when creating data table"
        ):
            await manager.create_data_table("nb", ["src"], "desc")

    @pytest.mark.asyncio
    async def test_parse_flashcard_invalid_artifact_data(
        self, mock_session: MagicMock
    ) -> None:
        """Test parsing invalid artifact data in flashcard response."""
        mock_session.call_rpc.return_value = [[]]
        manager = StudyManager(mock_session)
        with pytest.raises(
            GenerationError, match="Invalid artifact data when creating flashcards"
        ):
            await manager.create_flashcards("nb", ["src"])

    @pytest.mark.asyncio
    async def test_parse_quiz_completed_status(self, mock_session: MagicMock) -> None:
        """Test quiz parsing with completed status."""
        mock_session.call_rpc.return_value = [["q", None, None, None, STATUS_COMPLETED]]
        manager = StudyManager(mock_session)
        result = await manager.create_quiz("nb", ["src"])
        assert result.status == "completed"

    @pytest.mark.asyncio
    async def test_parse_quiz_unknown_status(self, mock_session: MagicMock) -> None:
        """Test quiz parsing with unknown status."""
        mock_session.call_rpc.return_value = [["q", None, None, None, 99]]
        manager = StudyManager(mock_session)
        result = await manager.create_quiz("nb", ["src"])
        assert result.status == "unknown"

    @pytest.mark.asyncio
    async def test_parse_data_table_completed_status(
        self, mock_session: MagicMock
    ) -> None:
        """Test data table parsing with completed status."""
        mock_session.call_rpc.return_value = [["t", None, None, None, STATUS_COMPLETED]]
        manager = StudyManager(mock_session)
        result = await manager.create_data_table("nb", ["src"], "d")
        assert result.status == "completed"

    @pytest.mark.asyncio
    async def test_parse_data_table_unknown_status(
        self, mock_session: MagicMock
    ) -> None:
        """Test data table parsing with unknown status."""
        mock_session.call_rpc.return_value = [["t", None, None, None, 99]]
        manager = StudyManager(mock_session)
        result = await manager.create_data_table("nb", ["src"], "d")
        assert result.status == "unknown"
