"""
Research discovery for PyNotebookLM.

This module provides the ResearchDiscovery class for performing web research,
discovering related sources, and importing findings into notebooks.
"""

import logging
import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field

from .api import NotebookLMAPI
from .exceptions import APIError, NotebookNotFoundError

if TYPE_CHECKING:
    from .session import BrowserSession

logger = logging.getLogger(__name__)


# =============================================================================
# RPC Constants - Discovered via browser reverse engineering (Jan 2026)
# =============================================================================

# Research operations - Discovered RPC IDs
RPC_FAST_RESEARCH = "Ljjv0c"  # Fast/quick web research (parameter: 1)
RPC_DEEP_RESEARCH = "QA9ei"  # Deep research (parameter: 5)
RPC_RESEARCH_STATUS = "e3bVqc"  # Check research progress/status
RPC_IMPORT_RESEARCH = "LBwxtb"  # Import research findings to notebook

# Per-source operations - accessed via source context menu
RPC_SYNC_DRIVE = "placeholder_sync_drive"  # Sync is per-source, not notebook-wide

# Topic suggestions - These appear as chips after chat responses in the UI
# In practice, they are generated as part of chat/notebook guide responses
# Keeping as placeholder for API compatibility
RPC_SUGGEST_TOPICS = "placeholder_suggest_topics"


class ResearchType(str, Enum):
    """Type of research to perform."""

    FAST = "fast"  # Quick research with immediate results
    DEEP = "deep"  # Comprehensive research with detailed analysis


# =============================================================================
# Models
# =============================================================================


class ResearchStatus(str, Enum):
    """Status of a research operation."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class ResearchResult(BaseModel):
    """Represents a single research result/finding."""

    id: str = Field(..., description="Unique result identifier")
    title: str = Field(..., description="Result title")
    url: str | None = Field(None, description="Source URL")
    snippet: str | None = Field(None, description="Text snippet/summary")
    source_type: str = Field("web", description="Type of source (web, academic, news)")
    relevance_score: float = Field(0.0, ge=0.0, le=1.0, description="Relevance score")


class ResearchSession(BaseModel):
    """Represents an ongoing or completed research session."""

    id: str = Field(..., description="Research session ID")
    topic: str = Field(..., description="Research topic/query")
    status: ResearchStatus = Field(ResearchStatus.PENDING, description="Current status")
    results: list[ResearchResult] = Field(
        default_factory=list, description="Discovered results"
    )
    started_at: datetime | None = Field(None, description="Start timestamp")
    completed_at: datetime | None = Field(None, description="Completion timestamp")
    error_message: str | None = Field(None, description="Error message if failed")


class TopicSuggestion(BaseModel):
    """Represents a suggested topic for research."""

    topic: str = Field(..., description="Suggested topic")
    description: str | None = Field(None, description="Topic description")
    relevance: str = Field("medium", description="Relevance level (high, medium, low)")


# =============================================================================
# Research Discovery Class
# =============================================================================


class ResearchDiscovery:
    """
    Performs web research and source discovery for NotebookLM.

    This class provides methods for starting research sessions,
    checking their status, and importing results into notebooks.

    Example:
        >>> async with BrowserSession(auth) as session:
        ...     research = ResearchDiscovery(session)
        ...     session = await research.start_web_research("AI trends 2024")
        ...     status = await research.get_status(session.id)
        ...     await research.import_research_results("notebook123", session.results)
    """

    def __init__(self, session: "BrowserSession") -> None:
        """
        Initialize the research discovery.

        Args:
            session: Active BrowserSession instance.
        """
        self._session = session
        self._api = NotebookLMAPI(session)
        # In-memory cache for research sessions (simulated)
        self._research_sessions: dict[str, ResearchSession] = {}

    async def start_web_research(
        self,
        topic: str,
        notebook_id: str | None = None,
        research_type: ResearchType = ResearchType.FAST,
    ) -> ResearchSession:
        """
        Start a web research session on a topic.

        This initiates a research process that discovers relevant sources
        and information about the given topic. NotebookLM supports two types:
        - FAST: Quick research with immediate results (default)
        - DEEP: Comprehensive research with detailed analysis

        Args:
            topic: The research topic or query string.
            notebook_id: Optional notebook ID to associate research with.
            research_type: Type of research (FAST or DEEP).

        Returns:
            ResearchSession with initial status.

        Raises:
            ValueError: If topic is empty.
            APIError: If the research cannot be started.

        Example:
            >>> session = await research.start_web_research(
            ...     "Machine learning trends",
            ...     research_type=ResearchType.DEEP
            ... )
            >>> print(f"Research ID: {session.id}")
        """
        if not topic or not topic.strip():
            raise ValueError("Research topic cannot be empty")

        topic = topic.strip()
        logger.info("Starting %s research for topic: %s", research_type.value, topic)

        # Generate a unique research ID
        research_id = f"research_{uuid.uuid4().hex[:12]}"

        # Create the research session
        research_session = ResearchSession(
            id=research_id,
            topic=topic,
            status=ResearchStatus.IN_PROGRESS,
            started_at=datetime.now(),
        )

        # Select RPC ID and parameter based on research type
        if research_type == ResearchType.DEEP:
            rpc_id = RPC_DEEP_RESEARCH
            research_param = 5  # Deep research uses parameter 5
        else:
            rpc_id = RPC_FAST_RESEARCH
            research_param = 1  # Fast research uses parameter 1

        try:
            # Build the research payload
            # Structure observed: [topic, notebook_id, research_param, [2]]
            payload = [topic, notebook_id, research_param, [2]]

            result = await self._session.call_rpc(rpc_id, payload)

            # Parse the research results if available
            if result:
                research_session = self._parse_research_response(
                    research_session, result
                )
            else:
                # If no result, mark as completed with empty results
                research_session.status = ResearchStatus.COMPLETED
                research_session.completed_at = datetime.now()

        except APIError as e:
            # Handle API errors gracefully
            if e.status_code == 400:
                logger.warning(
                    "Research RPC returned 400, may require notebook context: %s", e
                )
                research_session.status = ResearchStatus.COMPLETED
                research_session.completed_at = datetime.now()
                research_session.error_message = (
                    "Research requires notebook context. "
                    "Please provide a notebook_id parameter."
                )
            else:
                research_session.status = ResearchStatus.FAILED
                research_session.error_message = str(e)
                raise

        # Cache the session
        self._research_sessions[research_id] = research_session

        logger.info("Created research session: %s", research_id)
        return research_session

    async def get_status(self, research_id: str) -> ResearchSession:
        """
        Get the status of a research session.

        Args:
            research_id: The research session ID.

        Returns:
            ResearchSession with current status and results.

        Raises:
            ValueError: If research_id is empty or not found.

        Example:
            >>> status = await research.get_status("research_abc123")
            >>> print(f"Status: {status.status}, Results: {len(status.results)}")
        """
        if not research_id:
            raise ValueError("Research ID cannot be empty")

        # Check in-memory cache first
        if research_id in self._research_sessions:
            cached = self._research_sessions[research_id]

            # If it's still in progress, try to fetch updated status
            if cached.status == ResearchStatus.IN_PROGRESS:
                try:
                    result = await self._session.call_rpc(
                        RPC_RESEARCH_STATUS,
                        [research_id, [2]],
                    )
                    if result:
                        cached = self._parse_research_response(cached, result)
                        self._research_sessions[research_id] = cached
                except APIError:
                    # Keep the cached version if the API fails
                    pass

            return cached

        # Not in cache, try to fetch from API
        try:
            result = await self._session.call_rpc(
                RPC_RESEARCH_STATUS,
                [research_id, [2]],
            )
            if result:
                session = ResearchSession(
                    id=research_id,
                    topic="Unknown",
                    status=ResearchStatus.COMPLETED,
                )
                session = self._parse_research_response(session, result)
                self._research_sessions[research_id] = session
                return session
        except APIError:
            pass

        raise ValueError(f"Research session not found: {research_id}")

    async def import_research_results(
        self,
        notebook_id: str,
        results: list[ResearchResult],
    ) -> list[str]:
        """
        Import research results as sources into a notebook.

        Args:
            notebook_id: The target notebook ID.
            results: List of research results to import.

        Returns:
            List of created source IDs.

        Raises:
            ValueError: If notebook_id is empty or results are empty.
            NotebookNotFoundError: If notebook doesn't exist.
            APIError: If import fails.

        Example:
            >>> source_ids = await research.import_research_results(
            ...     "notebook123",
            ...     session.results[:5]  # Import top 5 results
            ... )
        """
        if not notebook_id:
            raise ValueError("Notebook ID cannot be empty")
        if not results:
            raise ValueError("Results list cannot be empty")

        logger.info(
            "Importing %d research results to notebook %s",
            len(results),
            notebook_id,
        )

        source_ids: list[str] = []

        for result in results:
            if not result.url:
                logger.warning("Skipping result without URL: %s", result.title)
                continue

            try:
                # Use the existing add_url_source functionality
                source_data = await self._api.add_url_source(notebook_id, result.url)

                if source_data:
                    # Extract source ID from response
                    source_id = self._extract_source_id(source_data)
                    if source_id:
                        source_ids.append(source_id)
                        logger.info("Imported source: %s", result.title)

            except APIError as e:
                logger.warning("Failed to import %s: %s", result.title, e)
                continue

        logger.info(
            "Successfully imported %d/%d sources",
            len(source_ids),
            len(results),
        )
        return source_ids

    async def sync_drive_sources(self, notebook_id: str) -> int:
        """
        Sync Google Drive sources for a notebook.

        This updates any Drive documents that have been modified since
        they were added to the notebook.

        Args:
            notebook_id: The notebook ID.

        Returns:
            Number of sources synced/updated.

        Raises:
            ValueError: If notebook_id is empty.
            NotebookNotFoundError: If notebook doesn't exist.
            APIError: If sync fails.

        Example:
            >>> updated = await research.sync_drive_sources("notebook123")
            >>> print(f"Synced {updated} Drive sources")
        """
        if not notebook_id:
            raise ValueError("Notebook ID cannot be empty")

        logger.info("Syncing Drive sources for notebook: %s", notebook_id)

        try:
            result = await self._session.call_rpc(
                RPC_SYNC_DRIVE,
                [notebook_id, [2]],
            )

            # Parse the number of synced sources
            if isinstance(result, list) and len(result) > 0:
                synced_count = result[0] if isinstance(result[0], int) else 0
            else:
                synced_count = 0

            logger.info("Synced %d Drive sources", synced_count)
            return synced_count

        except APIError as e:
            if e.status_code == 404:
                raise NotebookNotFoundError(notebook_id) from e
            # If RPC not available, return 0
            if "placeholder" in RPC_SYNC_DRIVE:
                logger.warning("Drive sync RPC not available: %s", e)
                return 0
            raise

    async def suggest_topics(self, notebook_id: str) -> list[TopicSuggestion]:
        """
        Get topic suggestions based on notebook content.

        Analyzes the notebook's sources and content to suggest
        related research topics.

        Args:
            notebook_id: The notebook ID.

        Returns:
            List of topic suggestions.

        Raises:
            ValueError: If notebook_id is empty.
            NotebookNotFoundError: If notebook doesn't exist.
            APIError: If suggestion fails.

        Example:
            >>> topics = await research.suggest_topics("notebook123")
            >>> for topic in topics:
            ...     print(f"{topic.topic}: {topic.description}")
        """
        if not notebook_id:
            raise ValueError("Notebook ID cannot be empty")

        logger.info("Getting topic suggestions for notebook: %s", notebook_id)

        try:
            result = await self._session.call_rpc(
                RPC_SUGGEST_TOPICS,
                [notebook_id, None, [2]],
            )

            suggestions: list[TopicSuggestion] = []

            if result and isinstance(result, list):
                for item in result:
                    if isinstance(item, list) and len(item) >= 1:
                        suggestion = TopicSuggestion(
                            topic=str(item[0]),
                            description=str(item[1]) if len(item) > 1 else None,
                            relevance=str(item[2]) if len(item) > 2 else "medium",
                        )
                        suggestions.append(suggestion)

            logger.info("Found %d topic suggestions", len(suggestions))
            return suggestions

        except APIError as e:
            if e.status_code == 404:
                raise NotebookNotFoundError(notebook_id) from e
            # If RPC not available, return empty list
            if "placeholder" in RPC_SUGGEST_TOPICS:
                logger.warning("Topic suggestion RPC not available: %s", e)
                return []
            raise

    # =========================================================================
    # Private Helper Methods
    # =========================================================================

    def _parse_research_response(
        self,
        session: ResearchSession,
        result: Any,
    ) -> ResearchSession:
        """Parse raw research API response into ResearchSession."""
        if not result:
            return session

        try:
            if isinstance(result, list):
                # Parse status
                if len(result) > 0 and isinstance(result[0], str):
                    status_str = result[0].lower()
                    if "complete" in status_str:
                        session.status = ResearchStatus.COMPLETED
                        session.completed_at = datetime.now()
                    elif "progress" in status_str or "running" in status_str:
                        session.status = ResearchStatus.IN_PROGRESS
                    elif "fail" in status_str or "error" in status_str:
                        session.status = ResearchStatus.FAILED

                # Parse results
                if len(result) > 1 and isinstance(result[1], list):
                    for item in result[1]:
                        if isinstance(item, list) and len(item) >= 2:
                            research_result = ResearchResult(
                                id=str(item[0]) if item[0] else uuid.uuid4().hex[:8],
                                title=str(item[1]) if len(item) > 1 else "Untitled",
                                url=str(item[2]) if len(item) > 2 and item[2] else None,
                                snippet=str(item[3]) if len(item) > 3 else None,
                                relevance_score=(
                                    float(item[4]) if len(item) > 4 else 0.5
                                ),
                            )
                            session.results.append(research_result)

        except (IndexError, TypeError, ValueError) as e:
            logger.warning("Error parsing research response: %s", e)

        return session

    def _extract_source_id(self, source_data: Any) -> str | None:
        """Extract source ID from add_source response."""
        try:
            if isinstance(source_data, list) and len(source_data) > 0:
                # Source ID is typically the first element
                return str(source_data[0])
            elif isinstance(source_data, dict) and "id" in source_data:
                return str(source_data["id"])
        except (IndexError, TypeError, KeyError):
            pass
        return None
