"""
Research discovery for PyNotebookLM.

This module provides the ResearchDiscovery class for performing web research,
discovering related sources, and importing findings into notebooks.

Based on reverse engineering of jacob-bd/notebooklm-mcp (Jan 2026).
"""

import asyncio
import logging
import re
from enum import Enum
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field

from .exceptions import APIError, NotebookNotFoundError

if TYPE_CHECKING:
    from .session import BrowserSession

logger = logging.getLogger(__name__)


# =============================================================================
# RPC Constants - Discovered via browser reverse engineering (Jan 2026)
# Based on jacob-bd/notebooklm-mcp reference implementation
# =============================================================================

# Research operations - Correct RPC IDs and payload structures
RPC_START_FAST_RESEARCH = "Ljjv0c"  # Fast/quick research
RPC_START_DEEP_RESEARCH = "QA9ei"  # Deep research (web only)
RPC_POLL_RESEARCH = "e3bVqc"  # Poll for research results
RPC_IMPORT_RESEARCH = "LBwxtb"  # Import research sources to notebook

# Research source types
RESEARCH_SOURCE_WEB = 1
RESEARCH_SOURCE_DRIVE = 2

# Research modes
RESEARCH_MODE_FAST = 1
RESEARCH_MODE_DEEP = 5

# Result types (returned by poll)
RESULT_TYPE_WEB = 1
RESULT_TYPE_GOOGLE_DOC = 2
RESULT_TYPE_GOOGLE_SLIDES = 3
RESULT_TYPE_DEEP_REPORT = 5
RESULT_TYPE_GOOGLE_SHEETS = 8


class ResearchType(str, Enum):
    """Type of research to perform."""

    FAST = "fast"  # Quick research with immediate results
    DEEP = "deep"  # Comprehensive research with detailed analysis


class ResearchSource(str, Enum):
    """Source type for research."""

    WEB = "web"  # Web search
    DRIVE = "drive"  # Google Drive search


# =============================================================================
# Models
# =============================================================================


class ResearchStatus(str, Enum):
    """Status of a research operation."""

    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    NO_RESEARCH = "no_research"


class ResearchResult(BaseModel):
    """Represents a single research result/finding."""

    index: int = Field(..., description="Result index")
    url: str = Field("", description="Source URL")
    title: str = Field("", description="Result title")
    description: str = Field("", description="Result description/snippet")
    result_type: int = Field(1, description="Result type code")
    result_type_name: str = Field("web", description="Human-readable result type")


class ResearchSession(BaseModel):
    """Represents an ongoing or completed research session."""

    task_id: str = Field(..., description="Research task ID from API")
    report_id: str | None = Field(None, description="Report ID (for deep research)")
    notebook_id: str = Field(..., description="Associated notebook ID")
    query: str = Field(..., description="Research topic/query")
    source: str = Field("web", description="Source type (web/drive)")
    mode: str = Field("fast", description="Research mode (fast/deep)")
    status: ResearchStatus = Field(
        ResearchStatus.IN_PROGRESS, description="Current status"
    )
    results: list[ResearchResult] = Field(
        default_factory=list, description="Discovered results"
    )
    summary: str = Field("", description="Research summary (fast research)")
    report: str = Field("", description="Deep research report (markdown)")
    source_count: int = Field(0, description="Number of sources found")


class ImportedSource(BaseModel):
    """Represents an imported research source."""

    id: str = Field(..., description="Source ID in notebook")
    title: str = Field("Untitled", description="Source title")


# =============================================================================
# Research Discovery Class
# =============================================================================


class ResearchDiscovery:
    """
    Performs web research and source discovery for NotebookLM.

    This class provides methods for starting research sessions,
    polling their status, and importing results into notebooks.

    Research is asynchronous - start_research returns a task_id,
    then call poll_research to check status and get results.

    Example:
        >>> async with BrowserSession(auth) as session:
        ...     research = ResearchDiscovery(session)
        ...     result = await research.start_research("notebook123", "AI trends")
        ...     print(f"Task ID: {result.task_id}")
        ...     # Poll for results
        ...     status = await research.poll_research("notebook123")
        ...     if status.status == "completed":
        ...         print(f"Found {len(status.results)} sources")
    """

    def __init__(self, session: "BrowserSession") -> None:
        """
        Initialize the research discovery.

        Args:
            session: Active BrowserSession instance.
        """
        self._session = session

    async def start_research(
        self,
        notebook_id: str,
        query: str,
        source: ResearchSource | str = ResearchSource.WEB,
        mode: ResearchType | str = ResearchType.FAST,
    ) -> ResearchSession:
        """
        Start a research session to discover sources.

        Research is asynchronous. This method returns immediately with a task_id.
        Use poll_research() to check status and get results.

        Args:
            notebook_id: The notebook ID to perform research in.
            query: The research topic or query string.
            source: Source type - "web" or "drive" (default: "web")
            mode: Research mode - "fast" or "deep" (default: "fast")

        Returns:
            ResearchSession with task_id for polling.

        Raises:
            ValueError: If invalid source/mode combination.
            APIError: If the research cannot be started.
            NotebookNotFoundError: If notebook doesn't exist.

        Example:
            >>> result = await research.start_research(
            ...     "notebook123",
            ...     "Machine learning trends",
            ...     source="web",
            ...     mode="deep"
            ... )
            >>> print(f"Started research: {result.task_id}")
        """
        if not notebook_id or not notebook_id.strip():
            raise ValueError("Notebook ID cannot be empty")
        if not query or not query.strip():
            raise ValueError("Research query cannot be empty")

        notebook_id = notebook_id.strip()
        query = query.strip()

        # Normalize source and mode
        source_str = (
            source.value if isinstance(source, ResearchSource) else source.lower()
        )
        mode_str = mode.value if isinstance(mode, ResearchType) else mode.lower()

        if source_str not in ("web", "drive"):
            raise ValueError(f"Invalid source '{source_str}'. Use 'web' or 'drive'.")

        if mode_str not in ("fast", "deep"):
            raise ValueError(f"Invalid mode '{mode_str}'. Use 'fast' or 'deep'.")

        if mode_str == "deep" and source_str == "drive":
            raise ValueError(
                "Deep Research only supports Web sources. Use mode='fast' for Drive."
            )

        # Map to internal constants
        source_type = (
            RESEARCH_SOURCE_WEB if source_str == "web" else RESEARCH_SOURCE_DRIVE
        )

        logger.info(
            "Starting %s research for query '%s' in notebook %s (source: %s)",
            mode_str,
            query,
            notebook_id,
            source_str,
        )

        try:
            if mode_str == "fast":
                # Fast Research: Ljjv0c
                # Payload: [[query, source_type], None, 1, notebook_id]
                rpc_id = RPC_START_FAST_RESEARCH
                params = [[query, source_type], None, RESEARCH_MODE_FAST, notebook_id]
            else:
                # Deep Research: QA9ei
                # Payload: [None, [1], [query, source_type], 5, notebook_id]
                rpc_id = RPC_START_DEEP_RESEARCH
                params = [
                    None,
                    [1],
                    [query, source_type],
                    RESEARCH_MODE_DEEP,
                    notebook_id,
                ]

            result = await self._session.call_rpc(rpc_id, params)

            # Parse the response - should contain task_id and optionally report_id
            task_id = None
            report_id = None

            if result and isinstance(result, list) and len(result) > 0:
                task_id = result[0]
                report_id = result[1] if len(result) > 1 else None

            if not task_id:
                raise APIError("Research started but no task_id returned")

            logger.info("Research started with task_id: %s", task_id)

            return ResearchSession(
                task_id=str(task_id),
                report_id=str(report_id) if report_id else None,
                notebook_id=notebook_id,
                query=query,
                source=source_str,
                mode=mode_str,
                status=ResearchStatus.IN_PROGRESS,
            )

        except APIError as e:
            if e.status_code == 404:
                raise NotebookNotFoundError(notebook_id) from e
            raise

    async def poll_research(self, notebook_id: str) -> ResearchSession:
        """
        Poll for research results.

        Call this repeatedly until status is "completed".

        Args:
            notebook_id: The notebook UUID.

        Returns:
            ResearchSession with current status and results.
            When no research is found, status will be ResearchStatus.NO_RESEARCH.

        Example:
            >>> status = await research.poll_research("notebook123")
            >>> if status and status.status == "completed":
            ...     for result in status.results:
            ...         print(f"{result.title}: {result.url}")
        """
        if not notebook_id or not notebook_id.strip():
            raise ValueError("Notebook ID cannot be empty")

        notebook_id = notebook_id.strip()
        logger.debug("Polling research for notebook: %s", notebook_id)

        try:
            # Poll params: [null, null, "notebook_id"]
            params = [None, None, notebook_id]
            result = await self._session.call_rpc(RPC_POLL_RESEARCH, params)

            if not result or not isinstance(result, list) or len(result) == 0:
                return ResearchSession(
                    task_id="",
                    notebook_id=notebook_id,
                    query="",
                    status=ResearchStatus.NO_RESEARCH,
                )

            # Parse the research result
            return self._parse_poll_response(result, notebook_id)

        except APIError as e:
            if e.status_code == 404:
                raise NotebookNotFoundError(notebook_id) from e
            raise

    async def poll_with_backoff(
        self,
        notebook_id: str,
        max_attempts: int = 10,
        base_interval: float = 5.0,
        max_interval: float = 60.0,
    ) -> ResearchSession:
        """
        Poll research status with exponential backoff.

        Args:
            notebook_id: The notebook UUID.
            max_attempts: Maximum number of polling attempts.
            base_interval: Initial polling interval in seconds.
            max_interval: Maximum polling interval in seconds.

        Returns:
            ResearchSession when completed or after max_attempts.
        """
        interval = base_interval
        last_result = ResearchSession(
            task_id="",
            notebook_id=notebook_id,
            query="",
            status=ResearchStatus.NO_RESEARCH,
        )

        for _ in range(max_attempts):
            last_result = await self.poll_research(notebook_id)
            if last_result.status != ResearchStatus.IN_PROGRESS:
                return last_result
            await asyncio.sleep(interval)
            interval = min(max_interval, interval * 2)

        return last_result

    async def import_research_sources(
        self,
        notebook_id: str,
        task_id: str,
        sources: list[ResearchResult],
    ) -> list[ImportedSource]:
        """
        Import research sources into the notebook.

        Args:
            notebook_id: The target notebook ID.
            task_id: The research task ID.
            sources: List of research results to import.

        Returns:
            List of imported sources with their IDs.

        Raises:
            ValueError: If inputs are empty.
            NotebookNotFoundError: If notebook doesn't exist.
            APIError: If import fails.

        Example:
            >>> poll_result = await research.poll_research("notebook123")
            >>> if poll_result.status == "completed":
            ...     imported = await research.import_research_sources(
            ...         "notebook123",
            ...         poll_result.task_id,
            ...         poll_result.results[:5]  # Import top 5
            ...     )
            ...     print(f"Imported {len(imported)} sources")
        """
        if not notebook_id:
            raise ValueError("Notebook ID cannot be empty")
        if not task_id:
            raise ValueError("Task ID cannot be empty")
        if not sources:
            raise ValueError("Sources list cannot be empty")

        logger.info(
            "Importing %d research sources to notebook %s (task: %s)",
            len(sources),
            notebook_id,
            task_id,
        )

        # Build source array for import
        # Web source: [null, null, ["url", "title"], null, null, null, null, null, null, null, 2]
        # Drive source: [[doc_id, mime_type, 1, title], null x9, 2]
        source_array: list[list[Any]] = []

        for src in sources:
            # Skip deep_report sources (type 5) - not importable
            if src.result_type == RESULT_TYPE_DEEP_REPORT or not src.url:
                continue

            if src.result_type == RESULT_TYPE_WEB:
                # Web source
                source_data: list[Any] = [
                    None,
                    None,
                    [src.url, src.title],
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    2,
                ]
            else:
                # Drive source - extract document ID from URL
                doc_id = None
                if "id=" in src.url:
                    doc_id = src.url.split("id=")[-1].split("&")[0]
                if not doc_id:
                    match = re.search(r"/d/([a-zA-Z0-9_-]+)", src.url)
                    if match:
                        doc_id = match.group(1)

                if doc_id:
                    mime_types = {
                        RESULT_TYPE_GOOGLE_DOC: "application/vnd.google-apps.document",
                        RESULT_TYPE_GOOGLE_SLIDES: "application/vnd.google-apps.presentation",
                        RESULT_TYPE_GOOGLE_SHEETS: "application/vnd.google-apps.spreadsheet",
                    }
                    mime_type = mime_types.get(
                        src.result_type, "application/vnd.google-apps.document"
                    )
                    source_data = [
                        [doc_id, mime_type, 1, src.title],
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        2,
                    ]
                else:
                    # Fallback to web-style
                    source_data = [
                        None,
                        None,
                        [src.url, src.title],
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        2,
                    ]

            source_array.append(source_data)

        if not source_array:
            logger.warning("No importable sources found")
            return []

        try:
            # Import RPC: [null, [1], task_id, notebook_id, source_array]
            params = [None, [1], task_id, notebook_id, source_array]
            result = await self._session.call_rpc(RPC_IMPORT_RESEARCH, params)

            # Parse imported sources
            imported = self._parse_import_response(result)
            logger.info("Successfully imported %d sources", len(imported))
            return imported

        except APIError as e:
            if e.status_code == 404:
                raise NotebookNotFoundError(notebook_id) from e
            raise

    # =========================================================================
    # Backward Compatibility - Legacy API
    # =========================================================================

    async def start_web_research(
        self,
        notebook_id: str,
        topic: str,
        research_type: ResearchType = ResearchType.FAST,
    ) -> ResearchSession:
        """
        Start a web research session on a topic.

        Backward-compatible wrapper for start_research().

        Args:
            notebook_id: The notebook ID to associate research with.
            topic: The research topic or query string.
            research_type: Type of research (FAST or DEEP).

        Returns:
            ResearchSession with task_id for polling.
        """
        return await self.start_research(
            notebook_id=notebook_id,
            query=topic,
            source=ResearchSource.WEB,
            mode=research_type,
        )

    # =========================================================================
    # Response Parsing Helpers
    # =========================================================================

    def _parse_poll_response(
        self,
        result: list[Any],
        notebook_id: str,
    ) -> ResearchSession:
        """Parse the poll_research response into ResearchSession."""
        # Unwrap outer array if needed
        # Structure: [[task_id, task_info, ...], [timestamp], ...]
        if (
            isinstance(result[0], list)
            and len(result[0]) > 0
            and isinstance(result[0][0], list)
        ):
            result = result[0]

        # Find the research task (skip timestamp arrays)
        for task_data in result:
            if not isinstance(task_data, list) or len(task_data) < 2:
                continue

            task_id = task_data[0]
            task_info = task_data[1] if len(task_data) > 1 else None

            # Skip if task_id isn't a UUID string
            if not isinstance(task_id, str):
                continue

            if not task_info or not isinstance(task_info, list):
                continue

            # Parse task info
            # Structure: [?, query_info, mode, sources_and_summary, status_code, ...]
            query_info = task_info[1] if len(task_info) > 1 else None
            research_mode = task_info[2] if len(task_info) > 2 else None
            sources_and_summary = task_info[3] if len(task_info) > 3 else []
            status_code = task_info[4] if len(task_info) > 4 else None

            query_text = query_info[0] if query_info and len(query_info) > 0 else ""
            source_type = query_info[1] if query_info and len(query_info) > 1 else 1

            # Parse sources and summary
            sources_data = []
            summary = ""
            report = ""

            if isinstance(sources_and_summary, list) and len(sources_and_summary) >= 1:
                sources_data = (
                    sources_and_summary[0]
                    if isinstance(sources_and_summary[0], list)
                    else []
                )
                if len(sources_and_summary) >= 2 and isinstance(
                    sources_and_summary[1], str
                ):
                    summary = sources_and_summary[1]

            # Parse sources
            results: list[ResearchResult] = []
            for idx, src in enumerate(sources_data):
                if not isinstance(src, list) or len(src) < 2:
                    continue

                # Check if deep research format (src[0] is None)
                if src[0] is None and len(src) > 1 and isinstance(src[1], str):
                    # Deep research format
                    title = src[1] if isinstance(src[1], str) else ""
                    result_type = (
                        src[3] if len(src) > 3 and isinstance(src[3], int) else 5
                    )
                    # Report at src[6][0]
                    if len(src) > 6 and isinstance(src[6], list) and len(src[6]) > 0:
                        report = src[6][0] if isinstance(src[6][0], str) else ""

                    results.append(
                        ResearchResult(
                            index=idx,
                            url="",
                            title=title,
                            description="",
                            result_type=result_type,
                            result_type_name=self._get_result_type_name(result_type),
                        )
                    )
                elif isinstance(src[0], str) or len(src) >= 3:
                    # Fast research format: [url, title, desc, type, ...]
                    url = src[0] if isinstance(src[0], str) else ""
                    title = src[1] if len(src) > 1 and isinstance(src[1], str) else ""
                    desc = src[2] if len(src) > 2 and isinstance(src[2], str) else ""
                    result_type = (
                        src[3] if len(src) > 3 and isinstance(src[3], int) else 1
                    )

                    results.append(
                        ResearchResult(
                            index=idx,
                            url=url,
                            title=title,
                            description=desc,
                            result_type=result_type,
                            result_type_name=self._get_result_type_name(result_type),
                        )
                    )

            # Determine status (1 = in_progress, 2 = completed)
            status = (
                ResearchStatus.COMPLETED
                if status_code == 2
                else ResearchStatus.IN_PROGRESS
            )

            return ResearchSession(
                task_id=task_id,
                notebook_id=notebook_id,
                query=query_text,
                source="web" if source_type == 1 else "drive",
                mode="deep" if research_mode == 5 else "fast",
                status=status,
                results=results,
                summary=summary,
                report=report,
                source_count=len(results),
            )

        # No research found
        return ResearchSession(
            task_id="",
            notebook_id=notebook_id,
            query="",
            status=ResearchStatus.NO_RESEARCH,
        )

    def _parse_import_response(self, result: Any) -> list[ImportedSource]:
        """Parse import_research_sources response."""
        imported: list[ImportedSource] = []

        if not result or not isinstance(result, list):
            return imported

        # Response may be wrapped: [[source1, source2, ...]]
        if (
            len(result) > 0
            and isinstance(result[0], list)
            and len(result[0]) > 0
            and isinstance(result[0][0], list)
        ):
            result = result[0]

        for src_data in result:
            if isinstance(src_data, list) and len(src_data) >= 2:
                src_id = (
                    src_data[0][0]
                    if src_data[0] and isinstance(src_data[0], list)
                    else None
                )
                src_title = src_data[1] if len(src_data) > 1 else "Untitled"
                if src_id:
                    imported.append(
                        ImportedSource(id=str(src_id), title=str(src_title))
                    )

        return imported

    @staticmethod
    def _get_result_type_name(result_type: int) -> str:
        """Convert result type code to human-readable name."""
        type_names = {
            RESULT_TYPE_WEB: "web",
            RESULT_TYPE_GOOGLE_DOC: "google_doc",
            RESULT_TYPE_GOOGLE_SLIDES: "google_slides",
            RESULT_TYPE_DEEP_REPORT: "deep_report",
            RESULT_TYPE_GOOGLE_SHEETS: "google_sheets",
        }
        return type_names.get(result_type, "unknown")
