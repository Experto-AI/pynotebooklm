"""
Unified client for PyNotebookLM.

This module provides the NotebookLMClient class which aggregates all
specialized managers into a single interface.
"""

import logging
from typing import Any

from .auth import AuthManager
from .chat import ChatSession
from .content import ContentGenerator
from .mindmaps import MindMapGenerator
from .notebooks import NotebookManager
from .research import ResearchDiscovery
from .session import BrowserSession
from .sources import SourceManager
from .study import StudyManager

logger = logging.getLogger(__name__)


class NotebookLMClient:
    """
    Unified client for Google NotebookLM.

    This client provides a high-level async context manager interface
    to all NotebookLM functionality.

    Example:
        >>> async with NotebookLMClient() as client:
        ...     notebooks = await client.notebooks.list()
        ...     print(notebooks)
    """

    def __init__(
        self,
        auth: AuthManager | None = None,
        session_class: type[BrowserSession] | None = None,
    ) -> None:
        """
        Initialize the unified client.

        Args:
            auth: Optional AuthManager instance. If not provided,
                  a default one will be created.
            session_class: BrowserSession class to use (e.g. PersistentBrowserSession).
        """
        self._auth = auth or AuthManager()
        self._session_class = session_class or BrowserSession
        self._session: BrowserSession | None = None

        # Managers - initialized in __aenter__
        self.notebooks: NotebookManager = None  # type: ignore
        self.sources: SourceManager = None  # type: ignore
        self.research: ResearchDiscovery = None  # type: ignore
        self.mindmaps: MindMapGenerator = None  # type: ignore
        self.content: ContentGenerator = None  # type: ignore
        self.study: StudyManager = None  # type: ignore
        self.chat: ChatSession = None  # type: ignore

    async def __aenter__(self) -> "NotebookLMClient":
        """
        Start the browser session and initialize all managers.
        """
        self._session = self._session_class(self._auth)
        await self._session.__aenter__()

        # Initialize managers with the active session
        self.notebooks = NotebookManager(self._session)
        self.sources = SourceManager(self._session)
        self.research = ResearchDiscovery(self._session)
        self.mindmaps = MindMapGenerator(self._session)
        self.content = ContentGenerator(self._session)
        self.study = StudyManager(self._session)
        self.chat = ChatSession(self._session)

        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """
        Close the browser session.
        """
        if self._session:
            await self._session.__aexit__(exc_type, exc_val, exc_tb)
            self._session = None

    @property
    def is_authenticated(self) -> bool:
        """Check if the client is authenticated."""
        return self._auth.is_authenticated()

    async def login(self) -> None:
        """Perform interactive login."""
        await self._auth.login()
