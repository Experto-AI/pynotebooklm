"""
Source management for PyNotebookLM.

This module provides the SourceManager class for adding, listing,
and deleting sources in NotebookLM notebooks.
"""

import logging
import re
from typing import TYPE_CHECKING

from .api import NotebookLMAPI, parse_source_response
from .models import Source, SourceType

if TYPE_CHECKING:
    from .session import BrowserSession

logger = logging.getLogger(__name__)


class SourceManager:
    """
    Manages sources in NotebookLM notebooks.

    This class provides high-level methods for adding various types
    of sources (URLs, YouTube videos, Google Drive docs, text) to
    notebooks and managing them.

    Example:
        >>> async with BrowserSession(auth) as session:
        ...     sources = SourceManager(session)
        ...     source = await sources.add_url(notebook_id, "https://example.com")
    """

    def __init__(self, session: "BrowserSession") -> None:
        """
        Initialize the source manager.

        Args:
            session: Active BrowserSession instance.
        """
        self._session = session
        self._api = NotebookLMAPI(session)

    async def add_url(self, notebook_id: str, url: str) -> Source:
        """
        Add a URL as a source to a notebook.

        The URL will be fetched and its content extracted for use
        in the notebook.

        Args:
            notebook_id: The notebook ID.
            url: The URL to add (must be a valid HTTP/HTTPS URL).

        Returns:
            The created Source object.

        Raises:
            ValueError: If URL is invalid.
            SourceError: If the URL cannot be added.
            NotebookNotFoundError: If notebook doesn't exist.
            APIError: If the API call fails.

        Example:
            >>> source = await manager.add_url(
            ...     "notebook123",
            ...     "https://en.wikipedia.org/wiki/Python"
            ... )
            >>> print(f"Added: {source.title}")
        """
        if not notebook_id:
            raise ValueError("Notebook ID cannot be empty")

        if not url:
            raise ValueError("URL cannot be empty")

        # Basic URL validation
        if not self._is_valid_url(url):
            raise ValueError(f"Invalid URL format: {url}")

        # Check if it's a YouTube URL
        if self._is_youtube_url(url):
            logger.info("URL detected as YouTube, using YouTube source type")
            return await self.add_youtube(notebook_id, url)

        logger.info("Adding URL source to %s: %s", notebook_id, url)

        raw_result = await self._api.add_url_source(notebook_id, url)

        source = parse_source_response(raw_result)

        logger.info("Added URL source: %s (%s)", source.title, source.id)
        return source

    async def add_youtube(self, notebook_id: str, url: str) -> Source:
        """
        Add a YouTube video as a source to a notebook.

        The video's transcript will be extracted for use in the notebook.

        Args:
            notebook_id: The notebook ID.
            url: The YouTube URL (various formats supported).

        Returns:
            The created Source object.

        Raises:
            ValueError: If URL is invalid or not a YouTube URL.
            SourceError: If the video cannot be added.
            NotebookNotFoundError: If notebook doesn't exist.
            APIError: If the API call fails.

        Example:
            >>> source = await manager.add_youtube(
            ...     "notebook123",
            ...     "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
            ... )
        """
        if not notebook_id:
            raise ValueError("Notebook ID cannot be empty")

        if not url:
            raise ValueError("URL cannot be empty")

        if not self._is_youtube_url(url):
            raise ValueError(f"Not a valid YouTube URL: {url}")

        logger.info("Adding YouTube source to %s: %s", notebook_id, url)

        raw_result = await self._api.add_youtube_source(notebook_id, url)

        source = parse_source_response(raw_result)
        source.type = SourceType.YOUTUBE  # Ensure correct type

        logger.info("Added YouTube source: %s (%s)", source.title, source.id)
        return source

    async def add_text(
        self,
        notebook_id: str,
        content: str,
        title: str | None = None,
    ) -> Source:
        """
        Add plain text as a source to a notebook.

        Args:
            notebook_id: The notebook ID.
            content: The text content (must not be empty).
            title: Optional title for the source (defaults to "Untitled Text").

        Returns:
            The created Source object.

        Raises:
            ValueError: If content is empty.
            SourceError: If the text cannot be added.
            NotebookNotFoundError: If notebook doesn't exist.
            APIError: If the API call fails.

        Example:
            >>> source = await manager.add_text(
            ...     "notebook123",
            ...     "This is my research notes...",
            ...     title="Research Notes"
            ... )
        """
        if not notebook_id:
            raise ValueError("Notebook ID cannot be empty")

        if not content or not content.strip():
            raise ValueError("Content cannot be empty")

        title = title.strip() if title else "Untitled Text"

        logger.info("Adding text source to %s: %s", notebook_id, title)

        raw_result = await self._api.add_text_source(notebook_id, content, title)

        source = parse_source_response(raw_result)
        source.type = SourceType.TEXT  # Ensure correct type

        logger.info("Added text source: %s (%s)", source.title, source.id)
        return source

    async def add_drive(self, notebook_id: str, drive_doc_id: str) -> Source:
        """
        Add a Google Drive document as a source to a notebook.

        The user must have access to the Drive document.

        Args:
            notebook_id: The notebook ID.
            drive_doc_id: The Google Drive document ID.

        Returns:
            The created Source object.

        Raises:
            ValueError: If drive_doc_id is empty.
            SourceError: If the document cannot be added.
            NotebookNotFoundError: If notebook doesn't exist.
            APIError: If the API call fails.

        Example:
            >>> source = await manager.add_drive(
            ...     "notebook123",
            ...     "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"
            ... )
        """
        if not notebook_id:
            raise ValueError("Notebook ID cannot be empty")

        if not drive_doc_id or not drive_doc_id.strip():
            raise ValueError("Drive document ID cannot be empty")

        drive_doc_id = drive_doc_id.strip()

        logger.info("Adding Drive source to %s: %s", notebook_id, drive_doc_id)

        raw_result = await self._api.add_drive_source(notebook_id, drive_doc_id)

        source = parse_source_response(raw_result)
        source.type = SourceType.DRIVE  # Ensure correct type

        logger.info("Added Drive source: %s (%s)", source.title, source.id)
        return source

    async def list_sources(self, notebook_id: str) -> list[Source]:
        """
        List all sources in a notebook.

        Args:
            notebook_id: The notebook ID.

        Returns:
            List of Source objects.

        Raises:
            NotebookNotFoundError: If notebook doesn't exist.
            APIError: If the API call fails.

        Example:
            >>> sources = await manager.list_sources("notebook123")
            >>> for src in sources:
            ...     print(f"{src.title} ({src.type})")
        """
        if not notebook_id:
            raise ValueError("Notebook ID cannot be empty")

        logger.info("Listing sources for notebook: %s", notebook_id)

        raw_notebook = await self._api.get_notebook(notebook_id)

        sources: list[Source] = []

        # Sources are typically in the notebook response
        if isinstance(raw_notebook, list) and len(raw_notebook) > 3:
            sources_data = raw_notebook[3] if isinstance(raw_notebook[3], list) else []
            for raw in sources_data:
                try:
                    source = parse_source_response(raw)
                    sources.append(source)
                except Exception as e:
                    logger.warning("Failed to parse source: %s", e)

        logger.info("Found %d sources", len(sources))
        return sources

    async def delete(self, notebook_id: str, source_id: str) -> bool:
        """
        Delete a source from a notebook.

        Args:
            notebook_id: The notebook ID.
            source_id: The source ID to delete.

        Returns:
            True if deletion was successful.

        Raises:
            ValueError: If IDs are empty.
            SourceError: If the source cannot be deleted.
            NotebookNotFoundError: If notebook doesn't exist.
            APIError: If the API call fails.

        Example:
            >>> await manager.delete("notebook123", "source456")
        """
        if not notebook_id:
            raise ValueError("Notebook ID cannot be empty")

        if not source_id:
            raise ValueError("Source ID cannot be empty")

        logger.info("Deleting source %s from %s", source_id, notebook_id)

        result = await self._api.delete_source(notebook_id, source_id)

        logger.info("Deleted source: %s", source_id)
        return result

    async def list_drive(self) -> list[dict[str, str]]:
        """
        List available Google Drive documents.

        Returns a list of Drive documents that can be added as sources.

        Returns:
            List of dictionaries with 'id' and 'title' keys.

        Raises:
            APIError: If the API call fails.

        Example:
            >>> docs = await manager.list_drive()
            >>> for doc in docs:
            ...     print(f"{doc['title']} ({doc['id']})")
        """
        logger.info("Listing available Drive documents...")

        raw_docs = await self._api.list_drive_docs()

        docs: list[dict[str, str]] = []
        for raw in raw_docs:
            if isinstance(raw, list) and len(raw) >= 2:
                docs.append(
                    {
                        "id": str(raw[0]) if raw[0] else "",
                        "title": str(raw[1]) if raw[1] else "Untitled",
                    }
                )

        logger.info("Found %d Drive documents", len(docs))
        return docs

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _is_valid_url(self, url: str) -> bool:
        """Check if a string is a valid HTTP/HTTPS URL."""
        pattern = r"^https?://[^\s/$.?#].[^\s]*$"
        return bool(re.match(pattern, url, re.IGNORECASE))

    def _is_youtube_url(self, url: str) -> bool:
        """Check if a URL is a YouTube URL."""
        youtube_patterns = [
            r"(?:youtube\.com/watch\?v=)",
            r"(?:youtu\.be/)",
            r"(?:youtube\.com/embed/)",
            r"(?:youtube\.com/v/)",
        ]
        return any(re.search(p, url, re.IGNORECASE) for p in youtube_patterns)
