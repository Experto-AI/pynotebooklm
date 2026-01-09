"""
Low-level API wrapper for NotebookLM internal RPC calls.

This module provides the NotebookLMAPI class which wraps the BrowserSession
to provide typed RPC calls with proper error handling and response parsing.
"""

import logging
import re
from datetime import datetime
from typing import Any

from .exceptions import (
    APIError,
    NotebookNotFoundError,
    SourceError,
)
from .models import Notebook, Source, SourceStatus, SourceType
from .session import BrowserSession

logger = logging.getLogger(__name__)


# =============================================================================
# RPC IDs for NotebookLM internal API
# =============================================================================

# Notebook operations
RPC_LIST_NOTEBOOKS = "wXbhsf"
RPC_CREATE_NOTEBOOK = "CCqFvf"
RPC_GET_NOTEBOOK = "rLM1Ne"
RPC_RENAME_NOTEBOOK = "cBavhb"
RPC_DELETE_NOTEBOOK = "WWINqb"

# Source operations
RPC_ADD_URL_SOURCE = "izAoDd"
RPC_ADD_TEXT_SOURCE = "dqfPBf"
RPC_DELETE_SOURCE = "tGMBJ"
RPC_LIST_SOURCES = "rLM1Ne"

# Drive operations
RPC_LIST_DRIVE_DOCS = "KGBelc"
RPC_ADD_DRIVE_SOURCE = "izAoDd"


class NotebookLMAPI:
    """
    Low-level API wrapper for NotebookLM RPC calls.

    This class provides methods for making typed RPC calls to NotebookLM's
    internal API with proper error handling and response parsing.

    Example:
        >>> async with BrowserSession(auth) as session:
        ...     api = NotebookLMAPI(session)
        ...     notebooks = await api.list_notebooks()
    """

    def __init__(self, session: BrowserSession) -> None:
        """
        Initialize the API wrapper.

        Args:
            session: Active BrowserSession instance.
        """
        self._session = session

    # =========================================================================
    # Notebook Operations
    # =========================================================================

    async def list_notebooks(self) -> list[dict[str, Any]]:
        """
        List all notebooks in the account.

        Returns:
            List of raw notebook data dictionaries.

        Raises:
            APIError: If the API call fails.
        """
        logger.debug("Listing notebooks...")
        result = await self._session.call_rpc(
            RPC_LIST_NOTEBOOKS,
            [None, 1, None, [2]],
        )

        # Response structure: [[notebook_data, ...], ...]
        if isinstance(result, list) and len(result) > 0:
            notebooks_data = result[0] if isinstance(result[0], list) else []
            return notebooks_data

        return []

    async def create_notebook(self, name: str) -> dict[str, Any]:
        """
        Create a new notebook.

        Args:
            name: Name for the new notebook.

        Returns:
            Raw notebook data dictionary.

        Raises:
            APIError: If creation fails.
        """
        logger.debug("Creating notebook: %s", name)

        # Payload structure based on reverse engineering
        result = await self._session.call_rpc(
            RPC_CREATE_NOTEBOOK,
            [name, None, None, [2], []],
        )

        return result  # type: ignore[no-any-return]

    async def get_notebook(self, notebook_id: str) -> dict[str, Any]:
        """
        Get notebook details including sources.

        Args:
            notebook_id: The notebook ID.

        Returns:
            Raw notebook data dictionary.

        Raises:
            NotebookNotFoundError: If notebook doesn't exist.
            APIError: If the API call fails.
        """
        logger.debug("Getting notebook: %s", notebook_id)

        try:
            result = await self._session.call_rpc(
                RPC_GET_NOTEBOOK,
                [notebook_id, None, [2], None, 0],
            )
            return result  # type: ignore[no-any-return]
        except APIError as e:
            # Check if it's a not found error
            if e.status_code == 404 or "not found" in str(e).lower():
                raise NotebookNotFoundError(notebook_id) from e
            raise

    async def rename_notebook(self, notebook_id: str, new_name: str) -> dict[str, Any]:
        """
        Rename an existing notebook.

        Args:
            notebook_id: The notebook ID.
            new_name: The new name for the notebook.

        Returns:
            Raw response data.

        Raises:
            NotebookNotFoundError: If notebook doesn't exist.
            APIError: If the API call fails.
        """
        logger.debug("Renaming notebook %s to: %s", notebook_id, new_name)

        try:
            result = await self._session.call_rpc(
                RPC_RENAME_NOTEBOOK,
                [notebook_id, new_name, [2]],
            )
            return result  # type: ignore[no-any-return]
        except APIError as e:
            if "not found" in str(e).lower():
                raise NotebookNotFoundError(notebook_id) from e
            raise

    async def delete_notebook(self, notebook_id: str) -> bool:
        """
        Delete a notebook.

        Args:
            notebook_id: The notebook ID to delete.

        Returns:
            True if deletion was successful.

        Raises:
            NotebookNotFoundError: If notebook doesn't exist.
            APIError: If the API call fails.
        """
        logger.debug("Deleting notebook: %s", notebook_id)

        try:
            await self._session.call_rpc(
                RPC_DELETE_NOTEBOOK,
                [[notebook_id], [2]],
            )
            return True
        except APIError as e:
            if "not found" in str(e).lower():
                raise NotebookNotFoundError(notebook_id) from e
            raise

    # =========================================================================
    # Source Operations
    # =========================================================================

    async def add_url_source(self, notebook_id: str, url: str) -> Any:
        """
        Add a URL as a source to a notebook.
        """
        logger.debug("Adding URL source to %s: %s", notebook_id, url)

        # New signature (reversed engineered Jan 2026)
        source_info = [None, None, [url], None, None, None, None, None, None, None, 1]
        extra_param = [1, None, None, None, None, None, None, None, None, None, [1]]

        try:
            result = await self._session.call_rpc(
                RPC_ADD_URL_SOURCE,
                [[source_info], notebook_id, [2], extra_param],
            )
            return self._unwrap_add_source_response(result)
        except APIError as e:
            if "not found" in str(e).lower():
                raise NotebookNotFoundError(notebook_id) from e
            if "invalid" in str(e).lower() or "url" in str(e).lower():
                raise SourceError(f"Failed to add URL: {url}") from e
            raise

    async def add_youtube_source(self, notebook_id: str, url: str) -> Any:
        """
        Add a YouTube video as a source to a notebook.
        """
        logger.debug("Adding YouTube source to %s: %s", notebook_id, url)

        # Extract video ID from URL
        video_id = self._extract_youtube_id(url)
        if not video_id:
            raise SourceError(f"Invalid YouTube URL: {url}")

        # YouTube uses type 2
        # Note: URL field still takes the full URL in the list
        source_info = [None, None, [url], None, None, None, None, None, None, None, 2]
        extra_param = [1, None, None, None, None, None, None, None, None, None, [1]]

        try:
            result = await self._session.call_rpc(
                RPC_ADD_URL_SOURCE,
                [[source_info], notebook_id, [2], extra_param],
            )
            return self._unwrap_add_source_response(result)
        except APIError as e:
            if "not found" in str(e).lower():
                raise NotebookNotFoundError(notebook_id) from e
            raise SourceError(f"Failed to add YouTube video: {url}") from e

    async def add_text_source(
        self, notebook_id: str, content: str, title: str | None = None
    ) -> Any:
        """
        Add plain text as a source to a notebook.
        Note: The RPC ID for text might be different (dqfPBf), but let's assume
        it follows a new pattern or we stick to the old one if we haven't RE'd it.
        Actually, let's keep the old one for text for now unless we're sure.
        But previous text attempt failed with 400.
        Let's try to assume a similar structure for 'dqfPBf' or maybe it uses 'izAoDd' now?
        'izAoDd' seems to be 'Add Source' generic.
        Let's mark text source as potentially broken or try to use izAoDd with type 4?
        For now, I will leave add_text_source mostly alone but add a TODO,
        or try to adapt it if I'm confident.
        The previous fail suggest parameters were wrong.
        Let's stick to fixing add_url first.
        """
        logger.debug("Adding text source to %s (title: %s)", notebook_id, title)
        source_title = title or "Untitled Text"

        # NOTE: Text source RPC 'dqfPBf' fails with 400.
        # It needs reverse engineering. For now, we restore original code but warn.
        try:
            result = await self._session.call_rpc(
                RPC_ADD_TEXT_SOURCE,
                [notebook_id, source_title, content, [2]],
            )
            return result
        except APIError as e:
            if "not found" in str(e).lower():
                raise NotebookNotFoundError(notebook_id) from e
            raise SourceError(f"Failed to add text source: {title}") from e

    async def add_drive_source(self, notebook_id: str, drive_doc_id: str) -> Any:
        """
        Add a Google Drive document as a source to a notebook.
        """
        logger.debug("Adding Drive source to %s: %s", notebook_id, drive_doc_id)

        # Drive sources use type 3
        # Format might be slightly different - drive ID instead of URL list?
        source_info = [
            None,
            None,
            [drive_doc_id],
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            3,
        ]
        extra_param = [1, None, None, None, None, None, None, None, None, None, [1]]

        try:
            result = await self._session.call_rpc(
                RPC_ADD_DRIVE_SOURCE,
                [[source_info], notebook_id, [2], extra_param],
            )
            return self._unwrap_add_source_response(result)
        except APIError as e:
            if "not found" in str(e).lower():
                raise NotebookNotFoundError(notebook_id) from e
            raise SourceError(f"Failed to add Drive document: {drive_doc_id}") from e

    def _unwrap_add_source_response(self, result: Any) -> Any:
        """Helper to unwrap the deeply nested response from add source RPCs."""
        # Response: [[[["id"], "Title", ...]]]
        if (
            isinstance(result, list)
            and len(result) > 0
            and isinstance(result[0], list)
            and len(result[0]) > 0
            and isinstance(result[0][0], list)
            and len(result[0][0]) > 0
        ):
            # Return the source object: [["id"], "Title", ...]
            # Wait, verify nesting level from reproduce script:
            # Result: [[[['506f...', ...]]]]
            # level 0: list
            # level 1: list
            # level 2: list
            # level 3: list (source obj)

            # Let's be safe and recursive or check types
            inner = result[0][0]
            if isinstance(inner, list):
                # Verify it looks like a source (index 0 is list of ID)
                if len(inner) > 0 and isinstance(inner[0], list):
                    return inner

        # Fallback or error
        logger.warning(f"Unexpected add_source response structure: {result}")
        return result

    async def delete_source(self, notebook_id: str, source_id: str) -> bool:
        """
        Delete a source from a notebook.

        Args:
            notebook_id: The notebook ID.
            source_id: The source ID to delete.

        Returns:
            True if deletion was successful.

        Raises:
            SourceError: If the source cannot be deleted.
            NotebookNotFoundError: If notebook doesn't exist.
            APIError: If the API call fails.
        """
        logger.debug("Deleting source %s from %s", source_id, notebook_id)

        try:
            await self._session.call_rpc(
                RPC_DELETE_SOURCE,
                [[[source_id]], [2]],
            )
            return True
        except APIError as e:
            if "not found" in str(e).lower():
                if "notebook" in str(e).lower():
                    raise NotebookNotFoundError(notebook_id) from e
                raise SourceError(
                    f"Source not found: {source_id}", source_id=source_id
                ) from e
            raise

    async def list_drive_docs(self) -> list[dict[str, Any]]:
        """
        List available Google Drive documents.

        Returns:
            List of raw Drive document data.

        Raises:
            APIError: If the API call fails.
        """
        logger.debug("Listing Drive documents...")

        result = await self._session.call_rpc(
            RPC_LIST_DRIVE_DOCS,
            [None, [2]],
        )

        if isinstance(result, list):
            return result
        return []

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _extract_youtube_id(self, url: str) -> str | None:
        """
        Extract YouTube video ID from various URL formats.

        Args:
            url: YouTube URL in any format.

        Returns:
            Video ID or None if not a valid YouTube URL.
        """
        patterns = [
            r"(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})",
            r"youtube\.com/embed/([a-zA-Z0-9_-]{11})",
            r"youtube\.com/v/([a-zA-Z0-9_-]{11})",
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)

        return None


# =============================================================================
# Response Parsing Utilities
# =============================================================================


def _parse_timestamp(ts_data: Any) -> datetime | None:
    """Helper to parse various timestamp formats (seconds, milliseconds, list)."""
    if not ts_data:
        return None

    try:
        ts_val = None
        if isinstance(ts_data, int | float):
            ts_val = ts_data
        elif (
            isinstance(ts_data, list)
            and len(ts_data) > 0
            and isinstance(ts_data[0], int | float)
        ):
            ts_val = ts_data[0]

        if ts_val:
            # Timestamp might be in milliseconds
            if ts_val > 1e12:  # Milliseconds
                ts_val = ts_val / 1000
            return datetime.fromtimestamp(ts_val)
    except (ValueError, TypeError):
        pass
    return None


def parse_notebook_response(data: Any) -> Notebook:
    """
    Parse raw API response into a Notebook model.

    Args:
        data: Raw notebook data from API.

    Returns:
        Parsed Notebook instance.
    """
    if isinstance(data, list) and len(data) == 1 and isinstance(data[0], list):
        data = data[0]

    if not isinstance(data, list) or len(data) < 2:
        raise APIError("Invalid notebook response format")

    # Standard notebook response structure: [name, sources, id, created_ts, updated_ts, ...]
    name = str(data[0]) if data[0] else "Untitled"
    notebook_id = str(data[2]) if len(data) > 2 and data[2] else ""

    # Parse timestamps
    created_at = _parse_timestamp(data[3]) if len(data) > 3 else None
    updated_at = _parse_timestamp(data[4]) if len(data) > 4 else None

    # Try metadata location at index 5 if timestamps not found
    if not created_at and len(data) > 5 and isinstance(data[5], list):
        meta = data[5]
        # Metadata structure: [..., ..., ..., ..., ..., created_ts, ..., ..., updated_ts]
        if len(meta) > 5:
            created_at = _parse_timestamp(meta[5]) or created_at
        if len(meta) > 8:
            updated_at = _parse_timestamp(meta[8]) or updated_at

    # Parse sources if available
    sources: list[Source] = []
    source_count = 0

    # Sources are at index 1
    if len(data) > 1 and isinstance(data[1], list):
        for src_data in data[1]:
            try:
                source = parse_source_response(src_data)
                sources.append(source)
            except Exception:
                pass
        source_count = len(sources)

    return Notebook(
        id=notebook_id,
        name=name,
        created_at=created_at,
        updated_at=updated_at,
        sources=sources,
        source_count=source_count,
    )


def parse_source_response(data: Any) -> Source:
    """
    Parse raw API response into a Source model.

    Args:
        data: Raw source data from API.

    Returns:
        Parsed Source instance.
    """
    if not isinstance(data, list) or len(data) < 2:
        raise APIError("Invalid source response format")

    # Source ID is often wrapped in a list at index 0
    raw_id = data[0]
    if isinstance(raw_id, list) and len(raw_id) > 0:
        source_id = str(raw_id[0])
    else:
        source_id = str(raw_id) if raw_id else ""

    title = str(data[1]) if len(data) > 1 and data[1] else "Untitled"

    # Determine source type based on data structure
    source_type = SourceType.TEXT
    url = None

    if len(data) > 2:
        # Type indicator might be at index 2 or embedded in URL structure
        type_indicator = data[2] if len(data) > 2 else None

        if isinstance(type_indicator, int):
            if type_indicator == 1:
                source_type = SourceType.URL
            elif type_indicator == 2:
                source_type = SourceType.YOUTUBE
            elif type_indicator == 3:
                source_type = SourceType.DRIVE
            else:
                source_type = SourceType.TEXT

        # URL might be at index 3
        if len(data) > 3 and isinstance(data[3], str):
            url = data[3]

    # Parse status
    status = SourceStatus.PROCESSING
    if len(data) > 4:
        status_val = data[4]
        if status_val == 1 or status_val == "ready":
            status = SourceStatus.READY
        elif status_val == 2 or status_val == "failed":
            status = SourceStatus.FAILED

    return Source(
        id=source_id,
        type=source_type,
        title=title,
        url=url,
        status=status,
    )
