"""
PyNotebookLM - Production-grade Python library for NotebookLM automation.

This library provides programmatic access to Google NotebookLM functionality
including notebook management, source handling, and content generation.
"""

from .api import NotebookLMAPI
from .auth import AuthManager
from .exceptions import (
    APIError,
    AuthenticationError,
    BrowserError,
    GenerationError,
    GenerationTimeoutError,
    NotebookNotFoundError,
    PyNotebookLMError,
    RateLimitError,
    SessionError,
    SourceError,
)
from .mindmaps import (
    MindMap,
    MindMapGenerateResult,
    MindMapGenerator,
    MindMapNode,
    export_to_freemind,
    export_to_json,
    export_to_opml,
)
from .models import (
    Artifact,
    ArtifactStatus,
    ArtifactType,
    ChatMessage,
    Notebook,
    Source,
    SourceStatus,
    SourceType,
)
from .notebooks import NotebookManager
from .research import (
    ImportedSource,
    ResearchDiscovery,
    ResearchResult,
    ResearchSession,
    ResearchSource,
    ResearchStatus,
    ResearchType,
)
from .session import BrowserSession
from .sources import SourceManager

__version__ = "0.14.0"

__all__ = [
    # Version
    "__version__",
    # Core classes
    "AuthManager",
    "BrowserSession",
    "NotebookLMAPI",
    "NotebookManager",
    "ResearchDiscovery",
    "SourceManager",
    "MindMapGenerator",
    # Models
    "Notebook",
    "Source",
    "SourceType",
    "SourceStatus",
    "Artifact",
    "ArtifactType",
    "ArtifactStatus",
    "ChatMessage",
    "ResearchSession",
    "ResearchResult",
    "ResearchStatus",
    "ResearchType",
    "ImportedSource",
    "ResearchSource",
    "MindMap",
    "MindMapNode",
    "MindMapGenerateResult",
    # Export functions
    "export_to_opml",
    "export_to_freemind",
    "export_to_json",
    # Exceptions
    "PyNotebookLMError",
    "AuthenticationError",
    "BrowserError",
    "NotebookNotFoundError",
    "SessionError",
    "SourceError",
    "GenerationError",
    "GenerationTimeoutError",
    "RateLimitError",
    "APIError",
]
