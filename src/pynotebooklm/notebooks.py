"""
Notebook management for PyNotebookLM.

This module provides the NotebookManager class for creating, listing,
retrieving, renaming, and deleting NotebookLM notebooks.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Sequence
from typing import TYPE_CHECKING

from .api import NotebookLMAPI, parse_notebook_response
from .exceptions import NotebookNotFoundError
from .models import Notebook

if TYPE_CHECKING:
    from .session import BrowserSession

logger = logging.getLogger(__name__)


class NotebookManager:
    """
    Manages NotebookLM notebooks.

    This class provides high-level methods for notebook CRUD operations
    with properly typed inputs and outputs.

    Example:
        >>> async with BrowserSession(auth) as session:
        ...     notebooks = NotebookManager(session)
        ...     all_notebooks = await notebooks.list()
        ...     new_notebook = await notebooks.create("My Research")
    """

    def __init__(self, session: BrowserSession) -> None:
        """
        Initialize the notebook manager.

        Args:
            session: Active BrowserSession instance.
        """
        self._session = session
        self._api = NotebookLMAPI(session)

    async def list(self) -> list[Notebook]:
        """
        List all notebooks in the account.

        Returns:
            List of Notebook objects.

        Raises:
            APIError: If the API call fails.

        Example:
            >>> notebooks = await manager.list()
            >>> for nb in notebooks:
            ...     print(f"{nb.name} ({nb.id})")
        """
        logger.info("Listing all notebooks...")

        raw_notebooks = await self._api.list_notebooks()

        notebooks: list[Notebook] = []
        for raw in raw_notebooks:
            try:
                notebook = parse_notebook_response(raw)
                notebooks.append(notebook)
            except Exception as e:
                logger.warning("Failed to parse notebook: %s", e)
                continue

        logger.info("Found %d notebooks", len(notebooks))
        return notebooks

    async def create(self, name: str) -> Notebook:
        """
        Create a new notebook.

        Args:
            name: Name for the new notebook (1-200 characters).

        Returns:
            The created Notebook object.

        Raises:
            ValueError: If name is invalid.
            APIError: If creation fails.

        Example:
            >>> notebook = await manager.create("My Research Project")
            >>> print(f"Created: {notebook.id}")
        """
        # Validate name
        if not name or not name.strip():
            raise ValueError("Notebook name cannot be empty")

        name = name.strip()
        if len(name) > 200:
            raise ValueError("Notebook name cannot exceed 200 characters")

        logger.info("Creating notebook: %s", name)

        raw_result = await self._api.create_notebook(name)

        # Parse the response
        notebook = parse_notebook_response(raw_result)

        logger.info("Created notebook: %s (%s)", notebook.name, notebook.id)
        return notebook

    async def get(self, notebook_id: str) -> Notebook:
        """
        Get a notebook by ID with its sources.

        Args:
            notebook_id: The notebook ID.

        Returns:
            The Notebook object with sources populated.

        Raises:
            NotebookNotFoundError: If notebook doesn't exist.
            APIError: If the API call fails.

        Example:
            >>> notebook = await manager.get("abc123")
            >>> print(f"Sources: {len(notebook.sources)}")
        """
        if not notebook_id:
            raise ValueError("Notebook ID cannot be empty")

        logger.info("Getting notebook: %s", notebook_id)

        raw_result = await self._api.get_notebook(notebook_id)

        notebook = parse_notebook_response(raw_result)

        logger.info(
            "Retrieved notebook: %s with %d sources",
            notebook.name,
            notebook.source_count,
        )
        return notebook

    async def rename(self, notebook_id: str, new_name: str) -> Notebook:
        """
        Rename an existing notebook.

        Args:
            notebook_id: The notebook ID.
            new_name: The new name for the notebook.

        Returns:
            The updated Notebook object.

        Raises:
            ValueError: If new_name is invalid.
            NotebookNotFoundError: If notebook doesn't exist.
            APIError: If the API call fails.

        Example:
            >>> notebook = await manager.rename("abc123", "New Name")
            >>> print(f"Renamed to: {notebook.name}")
        """
        if not notebook_id:
            raise ValueError("Notebook ID cannot be empty")

        if not new_name or not new_name.strip():
            raise ValueError("New name cannot be empty")

        new_name = new_name.strip()
        if len(new_name) > 200:
            raise ValueError("Notebook name cannot exceed 200 characters")

        logger.info("Renaming notebook %s to: %s", notebook_id, new_name)

        await self._api.rename_notebook(notebook_id, new_name)

        # Fetch the updated notebook
        notebook = await self.get(notebook_id)

        logger.info("Renamed notebook to: %s", notebook.name)
        return notebook

    async def delete(self, notebook_id: str, confirm: bool = False) -> bool:
        """
        Delete a notebook.

        Args:
            notebook_id: The notebook ID to delete.
            confirm: Must be True to actually delete. Safety mechanism.

        Returns:
            True if deletion was successful.

        Raises:
            ValueError: If confirm is not True.
            NotebookNotFoundError: If notebook doesn't exist.
            APIError: If the API call fails.

        Example:
            >>> # This will raise ValueError - safety mechanism
            >>> await manager.delete("abc123")

            >>> # This will actually delete
            >>> await manager.delete("abc123", confirm=True)
        """
        if not notebook_id:
            raise ValueError("Notebook ID cannot be empty")

        if not confirm:
            raise ValueError(
                "Deletion not confirmed. Pass confirm=True to delete the notebook. "
                "This action cannot be undone."
            )

        logger.warning("Deleting notebook: %s", notebook_id)

        result = await self._api.delete_notebook(notebook_id)

        logger.info("Deleted notebook: %s", notebook_id)
        return result

    async def batch_delete(
        self, notebook_ids: Sequence[str], confirm: bool = False
    ) -> dict[str, bool]:
        """
        Delete multiple notebooks concurrently.

        Args:
            notebook_ids: Sequence of notebook IDs to delete.
            confirm: Must be True to proceed.

        Returns:
            Mapping of notebook ID to deletion success.
        """
        if not confirm:
            raise ValueError("confirm must be True to delete notebooks in batch")
        if not notebook_ids:
            raise ValueError("Notebook IDs cannot be empty")

        async def _delete_single(nid: str) -> tuple[str, bool]:
            try:
                result = await self.delete(nid, confirm=True)
                return nid, bool(result)
            except Exception:
                return nid, False

        results = await asyncio.gather(*(_delete_single(nid) for nid in notebook_ids))
        return dict(results)

    async def exists(self, notebook_id: str) -> bool:
        """
        Check if a notebook exists.

        Args:
            notebook_id: The notebook ID to check.

        Returns:
            True if the notebook exists, False otherwise.

        Example:
            >>> if await manager.exists("abc123"):
            ...     print("Notebook exists!")
        """
        try:
            await self.get(notebook_id)
            return True
        except NotebookNotFoundError:
            return False
