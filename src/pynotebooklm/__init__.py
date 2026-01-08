"""
PyNotebookLM - Production-grade Python library for NotebookLM automation.

This library provides programmatic access to Google NotebookLM functionality
including notebook management, source handling, and content generation.
"""

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
from .session import BrowserSession

__version__ = "0.1.0"

__all__ = [
    # Version
    "__version__",
    # Core classes
    "AuthManager",
    "BrowserSession",
    # Models
    "Notebook",
    "Source",
    "SourceType",
    "SourceStatus",
    "Artifact",
    "ArtifactType",
    "ArtifactStatus",
    "ChatMessage",
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
