"""
PyNotebookLM - Production-grade Python library for NotebookLM automation.

This library provides programmatic access to Google NotebookLM functionality
including notebook management, source handling, and content generation.
"""

from .api import NotebookLMAPI
from .auth import AuthManager, save_auth_tokens
from .chat import ChatSession
from .client import NotebookLMClient
from .content import (
    AudioFormat,
    AudioLength,
    ContentGenerator,
    CreateContentResult,
    InfographicDetailLevel,
    InfographicOrientation,
    SlideDeckFormat,
    SlideDeckLength,
    StudioArtifact,
    StudioArtifactStatus,
    StudioArtifactType,
    VideoFormat,
    VideoStyle,
)
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
from .retry import RetryStrategy, with_retry
from .session import BrowserSession, PersistentBrowserSession
from .sources import SourceManager
from .study import (
    DataTableCreateResult,
    FlashcardCreateResult,
    FlashcardDifficulty,
    QuizCreateResult,
    StudyManager,
)

__version__ = "0.20.0"

__all__ = [
    # Version
    "__version__",
    # Core classes
    "AuthManager",
    "BrowserSession",
    "PersistentBrowserSession",
    "ChatSession",
    "NotebookLMAPI",
    "NotebookLMClient",
    "NotebookManager",
    "save_auth_tokens",
    "ResearchDiscovery",
    "SourceManager",
    "MindMapGenerator",
    "ContentGenerator",
    "StudyManager",
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
    # Content generation types
    "StudioArtifact",
    "StudioArtifactType",
    "StudioArtifactStatus",
    "CreateContentResult",
    "AudioFormat",
    "AudioLength",
    "VideoFormat",
    "VideoStyle",
    "InfographicOrientation",
    "InfographicDetailLevel",
    "SlideDeckFormat",
    "SlideDeckLength",
    # Study tool types
    "FlashcardDifficulty",
    "FlashcardCreateResult",
    "QuizCreateResult",
    "DataTableCreateResult",
    # Export functions
    "export_to_opml",
    "export_to_freemind",
    "export_to_json",
    # Retry strategies
    "RetryStrategy",
    "with_retry",
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
