"""
Study tools module for PyNotebookLM.

This module provides the StudyManager class for creating study aids
from notebook sources: flashcards, quizzes, and data tables.
"""

import logging
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from .exceptions import GenerationError
from .session import BrowserSession

logger = logging.getLogger(__name__)

# RPC IDs for Studio operations (shared with content.py)
RPC_CREATE_STUDIO = "R7cb6c"

# Studio content type codes for study tools
STUDIO_TYPE_FLASHCARDS = 4  # Also used for Quiz (differentiated by format code)
STUDIO_TYPE_DATA_TABLE = 9

# Status codes
STATUS_IN_PROGRESS = 1
STATUS_COMPLETED = 3

# Flashcard difficulty codes
FLASHCARD_DIFFICULTY_EASY = 1
FLASHCARD_DIFFICULTY_MEDIUM = 2
FLASHCARD_DIFFICULTY_HARD = 3
FLASHCARD_COUNT_DEFAULT = 2


# =============================================================================
# Enums for Study Tool Options
# =============================================================================


class FlashcardDifficulty(str, Enum):
    """Flashcard difficulty options."""

    EASY = "easy"  # Code 1
    MEDIUM = "medium"  # Code 2
    HARD = "hard"  # Code 3


# =============================================================================
# Pydantic Models for Study Tools
# =============================================================================


class FlashcardCreateResult(BaseModel):
    """Result from creating flashcards."""

    artifact_id: str = Field(..., description="Created artifact ID")
    notebook_id: str = Field(..., description="Notebook ID")
    status: str = Field(..., description="Initial status (usually in_progress)")
    difficulty: str = Field(..., description="Difficulty level")

    model_config = {"frozen": False}


class QuizCreateResult(BaseModel):
    """Result from creating a quiz."""

    artifact_id: str = Field(..., description="Created artifact ID")
    notebook_id: str = Field(..., description="Notebook ID")
    status: str = Field(..., description="Initial status (usually in_progress)")
    question_count: int = Field(..., description="Number of questions")
    difficulty: int = Field(..., description="Difficulty level")

    model_config = {"frozen": False}


class DataTableCreateResult(BaseModel):
    """Result from creating a data table."""

    artifact_id: str = Field(..., description="Created artifact ID")
    notebook_id: str = Field(..., description="Notebook ID")
    status: str = Field(..., description="Initial status (usually in_progress)")
    description: str = Field(..., description="Data table description")
    language: str = Field("en", description="Language code")

    model_config = {"frozen": False}


# =============================================================================
# Mapping Functions
# =============================================================================


def _difficulty_to_code(difficulty: FlashcardDifficulty) -> int:
    """Convert FlashcardDifficulty enum to RPC code."""
    mapping = {
        FlashcardDifficulty.EASY: FLASHCARD_DIFFICULTY_EASY,
        FlashcardDifficulty.MEDIUM: FLASHCARD_DIFFICULTY_MEDIUM,
        FlashcardDifficulty.HARD: FLASHCARD_DIFFICULTY_HARD,
    }
    return mapping.get(difficulty, FLASHCARD_DIFFICULTY_MEDIUM)


def _code_to_difficulty(code: int) -> str:
    """Convert RPC code to difficulty name."""
    mapping = {1: "easy", 2: "medium", 3: "hard"}
    return mapping.get(code, "medium")


# =============================================================================
# StudyManager Class
# =============================================================================


class StudyManager:
    """
    Manager for study tools from notebook sources.

    This class provides methods to create flashcards, quizzes,
    and data tables from notebook sources.

    Example:
        ```python
        async with BrowserSession(auth) as session:
            study = StudyManager(session)

            # Create flashcards
            result = await study.create_flashcards(
                notebook_id="abc-123",
                source_ids=["src-1", "src-2"],
                difficulty=FlashcardDifficulty.MEDIUM,
            )

            # Create a quiz
            quiz = await study.create_quiz(
                notebook_id="abc-123",
                source_ids=["src-1", "src-2"],
                question_count=5,
            )

            # Create a data table
            table = await study.create_data_table(
                notebook_id="abc-123",
                source_ids=["src-1", "src-2"],
                description="Extract key dates and events",
            )
        ```
    """

    def __init__(self, session: BrowserSession):
        """
        Initialize the StudyManager.

        Args:
            session: Active BrowserSession instance.
        """
        self._session = session

    async def create_flashcards(
        self,
        notebook_id: str,
        source_ids: list[str],
        difficulty: FlashcardDifficulty = FlashcardDifficulty.MEDIUM,
    ) -> FlashcardCreateResult:
        """
        Create flashcards from notebook sources.

        Args:
            notebook_id: Notebook UUID.
            source_ids: List of source IDs to include.
            difficulty: Flashcard difficulty (easy, medium, hard).

        Returns:
            FlashcardCreateResult with artifact_id and initial status.

        Raises:
            GenerationError: If flashcard creation fails.
        """
        if not source_ids:
            raise GenerationError("At least one source ID is required")

        difficulty_code = _difficulty_to_code(difficulty)

        # Build source IDs in nested format: [[[id1]], [[id2]], ...]
        sources_nested = [[[sid]] for sid in source_ids]

        # Flashcard options at position 9
        # Format: [null, [1, null*5, [difficulty, card_count]]]
        flashcard_options = [
            None,
            [
                1,  # Format code 1 = Flashcards (vs 2 = Quiz)
                None,
                None,
                None,
                None,
                None,
                [difficulty_code, FLASHCARD_COUNT_DEFAULT],
            ],
        ]

        # Build content array: [null, null, type, sources, null*5, options]
        content = [
            None,
            None,
            STUDIO_TYPE_FLASHCARDS,
            sources_nested,
            None,
            None,
            None,
            None,
            None,  # positions 4-8
            flashcard_options,  # position 9
        ]

        params = [[2], notebook_id, content]

        try:
            result = await self._session.call_rpc(RPC_CREATE_STUDIO, params)
        except Exception as e:
            raise GenerationError(f"Failed to create flashcards: {e}") from e

        return self._parse_flashcard_result(result, notebook_id, difficulty)

    async def create_quiz(
        self,
        notebook_id: str,
        source_ids: list[str],
        question_count: int = 2,
        difficulty: int = 2,
    ) -> QuizCreateResult:
        """
        Create a quiz from notebook sources.

        Args:
            notebook_id: Notebook UUID.
            source_ids: List of source IDs to include.
            question_count: Number of quiz questions.
            difficulty: Difficulty level (integer, default 2).

        Returns:
            QuizCreateResult with artifact_id and initial status.

        Raises:
            GenerationError: If quiz creation fails.
        """
        if not source_ids:
            raise GenerationError("At least one source ID is required")

        # Build source IDs in nested format: [[[id1]], [[id2]], ...]
        sources_nested = [[[sid]] for sid in source_ids]

        # Quiz options at position 9
        # Format: [null, [2, null*6, [question_count, difficulty]]]
        # Format code 2 distinguishes Quiz from Flashcards (which uses 1)
        quiz_options = [
            None,
            [
                2,  # Format code 2 = Quiz (vs 1 = Flashcards)
                None,
                None,
                None,
                None,
                None,
                None,
                [question_count, difficulty],
            ],
        ]

        # Build content array: [null, null, type, sources, null*5, options]
        content = [
            None,
            None,
            STUDIO_TYPE_FLASHCARDS,  # Type 4 (shared with flashcards)
            sources_nested,
            None,
            None,
            None,
            None,
            None,  # positions 4-8
            quiz_options,  # position 9
        ]

        params = [[2], notebook_id, content]

        try:
            result = await self._session.call_rpc(RPC_CREATE_STUDIO, params)
        except Exception as e:
            raise GenerationError(f"Failed to create quiz: {e}") from e

        return self._parse_quiz_result(result, notebook_id, question_count, difficulty)

    async def create_data_table(
        self,
        notebook_id: str,
        source_ids: list[str],
        description: str,
        language: str = "en",
    ) -> DataTableCreateResult:
        """
        Create a data table from notebook sources.

        Args:
            notebook_id: Notebook UUID.
            source_ids: List of source IDs to include.
            description: Description of the data to extract.
            language: BCP-47 language code (e.g., "en", "es").

        Returns:
            DataTableCreateResult with artifact_id and initial status.

        Raises:
            GenerationError: If data table creation fails.
        """
        if not source_ids:
            raise GenerationError("At least one source ID is required")

        if not description:
            raise GenerationError("Description is required for data table creation")

        # Build source IDs in nested format: [[[id1]], [[id2]], ...]
        sources_nested = [[[sid]] for sid in source_ids]

        # Data table options at position 18
        # Format: [null, [description, language]]
        datatable_options = [None, [description, language]]

        # Build content array: [null, null, type, sources, null*14, options]
        content = [
            None,
            None,
            STUDIO_TYPE_DATA_TABLE,
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
            None,
            None,
            None,  # positions 4-17
            datatable_options,  # position 18
        ]

        params = [[2], notebook_id, content]

        try:
            result = await self._session.call_rpc(RPC_CREATE_STUDIO, params)
        except Exception as e:
            raise GenerationError(f"Failed to create data table: {e}") from e

        return self._parse_data_table_result(result, notebook_id, description, language)

    def _parse_flashcard_result(
        self,
        result: Any,
        notebook_id: str,
        difficulty: FlashcardDifficulty,
    ) -> FlashcardCreateResult:
        """Parse the result from a create flashcards RPC call."""
        if not result or not isinstance(result, list) or len(result) == 0:
            raise GenerationError("Invalid response when creating flashcards")

        artifact_data = result[0]
        if not isinstance(artifact_data, list) or len(artifact_data) == 0:
            raise GenerationError("Invalid artifact data when creating flashcards")

        artifact_id = artifact_data[0]
        status_code = artifact_data[4] if len(artifact_data) > 4 else None

        if status_code == STATUS_IN_PROGRESS:
            status = "in_progress"
        elif status_code == STATUS_COMPLETED:
            status = "completed"
        else:
            status = "unknown"

        return FlashcardCreateResult(
            artifact_id=artifact_id,
            notebook_id=notebook_id,
            status=status,
            difficulty=difficulty.value,
        )

    def _parse_quiz_result(
        self,
        result: Any,
        notebook_id: str,
        question_count: int,
        difficulty: int,
    ) -> QuizCreateResult:
        """Parse the result from a create quiz RPC call."""
        if not result or not isinstance(result, list) or len(result) == 0:
            raise GenerationError("Invalid response when creating quiz")

        artifact_data = result[0]
        if not isinstance(artifact_data, list) or len(artifact_data) == 0:
            raise GenerationError("Invalid artifact data when creating quiz")

        artifact_id = artifact_data[0]
        status_code = artifact_data[4] if len(artifact_data) > 4 else None

        if status_code == STATUS_IN_PROGRESS:
            status = "in_progress"
        elif status_code == STATUS_COMPLETED:
            status = "completed"
        else:
            status = "unknown"

        return QuizCreateResult(
            artifact_id=artifact_id,
            notebook_id=notebook_id,
            status=status,
            question_count=question_count,
            difficulty=difficulty,
        )

    def _parse_data_table_result(
        self,
        result: Any,
        notebook_id: str,
        description: str,
        language: str,
    ) -> DataTableCreateResult:
        """Parse the result from a create data table RPC call."""
        if not result or not isinstance(result, list) or len(result) == 0:
            raise GenerationError("Invalid response when creating data table")

        artifact_data = result[0]
        if not isinstance(artifact_data, list) or len(artifact_data) == 0:
            raise GenerationError("Invalid artifact data when creating data table")

        artifact_id = artifact_data[0]
        status_code = artifact_data[4] if len(artifact_data) > 4 else None

        if status_code == STATUS_IN_PROGRESS:
            status = "in_progress"
        elif status_code == STATUS_COMPLETED:
            status = "completed"
        else:
            status = "unknown"

        return DataTableCreateResult(
            artifact_id=artifact_id,
            notebook_id=notebook_id,
            status=status,
            description=description,
            language=language,
        )
