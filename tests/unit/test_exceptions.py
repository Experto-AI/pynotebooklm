"""
Unit tests for custom exceptions.

These tests verify exception messages and attributes.
"""

from pynotebooklm.exceptions import (
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


class TestPyNotebookLMError:
    """Tests for the base exception."""

    def test_default_message(self) -> None:
        """Base exception has default message."""
        error = PyNotebookLMError()
        assert "An error occurred" in str(error)

    def test_custom_message(self) -> None:
        """Base exception accepts custom message."""
        error = PyNotebookLMError("Custom error message")
        assert error.message == "Custom error message"
        assert str(error) == "Custom error message"


class TestAuthenticationError:
    """Tests for AuthenticationError."""

    def test_default_message(self) -> None:
        """AuthenticationError has default message."""
        error = AuthenticationError()
        assert "login" in str(error).lower()

    def test_inherits_from_base(self) -> None:
        """AuthenticationError inherits from PyNotebookLMError."""
        error = AuthenticationError()
        assert isinstance(error, PyNotebookLMError)


class TestNotebookNotFoundError:
    """Tests for NotebookNotFoundError."""

    def test_includes_notebook_id(self) -> None:
        """NotebookNotFoundError includes notebook ID in message."""
        error = NotebookNotFoundError("nb_12345")
        assert "nb_12345" in str(error)
        assert error.notebook_id == "nb_12345"


class TestSourceError:
    """Tests for SourceError."""

    def test_default_message(self) -> None:
        """SourceError has default message."""
        error = SourceError()
        assert "Source operation failed" in str(error)

    def test_with_source_id(self) -> None:
        """SourceError can include source ID."""
        error = SourceError("Upload failed", source_id="src_456")
        assert error.source_id == "src_456"
        assert "Upload failed" in str(error)


class TestGenerationError:
    """Tests for GenerationError."""

    def test_default_message(self) -> None:
        """GenerationError has default message."""
        error = GenerationError()
        assert "generation failed" in str(error).lower()

    def test_with_artifact_id(self) -> None:
        """GenerationError can include artifact ID."""
        error = GenerationError("Generation cancelled", artifact_id="art_789")
        assert error.artifact_id == "art_789"


class TestGenerationTimeoutError:
    """Tests for GenerationTimeoutError."""

    def test_includes_timeout(self) -> None:
        """GenerationTimeoutError includes timeout in message."""
        error = GenerationTimeoutError(timeout=300)
        assert "300" in str(error)
        assert error.timeout == 300

    def test_with_artifact_id(self) -> None:
        """GenerationTimeoutError can include artifact ID."""
        error = GenerationTimeoutError(timeout=300, artifact_id="art_abc")
        assert error.artifact_id == "art_abc"

    def test_inherits_from_generation_error(self) -> None:
        """GenerationTimeoutError inherits from GenerationError."""
        error = GenerationTimeoutError(timeout=300)
        assert isinstance(error, GenerationError)


class TestRateLimitError:
    """Tests for RateLimitError."""

    def test_default_message(self) -> None:
        """RateLimitError has default message."""
        error = RateLimitError()
        assert "rate limit" in str(error).lower()

    def test_with_retry_after(self) -> None:
        """RateLimitError includes retry_after in message."""
        error = RateLimitError(retry_after=60)
        assert error.retry_after == 60
        assert "60" in str(error)


class TestAPIError:
    """Tests for APIError."""

    def test_default_message(self) -> None:
        """APIError has default message."""
        error = APIError()
        assert "api error" in str(error).lower()

    def test_with_status_code(self) -> None:
        """APIError includes status code in message."""
        error = APIError("Request failed", status_code=500)
        assert error.status_code == 500
        assert "500" in str(error)

    def test_with_response_body(self) -> None:
        """APIError stores response body."""
        error = APIError("Request failed", response_body='{"error": "detail"}')
        assert error.response_body == '{"error": "detail"}'


class TestBrowserError:
    """Tests for BrowserError."""

    def test_default_message(self) -> None:
        """BrowserError has default message."""
        error = BrowserError()
        assert "browser" in str(error).lower()

    def test_custom_message(self) -> None:
        """BrowserError accepts custom message."""
        error = BrowserError("Failed to launch Chrome")
        assert "Failed to launch Chrome" in str(error)


class TestSessionError:
    """Tests for SessionError."""

    def test_default_message(self) -> None:
        """SessionError has default message."""
        error = SessionError()
        assert "session" in str(error).lower()


class TestExceptionHierarchy:
    """Tests for exception inheritance."""

    def test_all_inherit_from_base(self) -> None:
        """All custom exceptions inherit from PyNotebookLMError."""
        exceptions = [
            AuthenticationError(),
            NotebookNotFoundError("nb_123"),
            SourceError(),
            GenerationError(),
            GenerationTimeoutError(timeout=300),
            RateLimitError(),
            APIError(),
            BrowserError(),
            SessionError(),
        ]

        for error in exceptions:
            assert isinstance(error, PyNotebookLMError)
            assert isinstance(error, Exception)
