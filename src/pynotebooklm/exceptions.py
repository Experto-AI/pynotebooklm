"""
Custom exceptions for PyNotebookLM.

This module defines a hierarchy of exceptions for handling various error
conditions that can occur when interacting with NotebookLM.
"""


class PyNotebookLMError(Exception):
    """Base exception for all PyNotebookLM errors."""

    def __init__(self, message: str = "An error occurred in PyNotebookLM") -> None:
        self.message = message
        super().__init__(self.message)


class AuthenticationError(PyNotebookLMError):
    """
    Raised when authentication fails or cookies are expired/invalid.

    This typically occurs when:
    - No authentication cookies exist
    - Cookies have expired (usually after 2-4 weeks)
    - Cookies are malformed or invalid
    """

    def __init__(
        self, message: str = "Authentication failed. Please login again."
    ) -> None:
        super().__init__(message)


class NotebookNotFoundError(PyNotebookLMError):
    """
    Raised when a requested notebook does not exist.

    Attributes:
        notebook_id: The ID of the notebook that was not found.
    """

    def __init__(self, notebook_id: str) -> None:
        self.notebook_id = notebook_id
        super().__init__(f"Notebook not found: {notebook_id}")


class SourceError(PyNotebookLMError):
    """
    Raised when source operations fail.

    This can occur when:
    - Adding a source fails (invalid URL, unsupported format)
    - Source processing fails
    - Source deletion fails
    """

    def __init__(
        self, message: str = "Source operation failed", source_id: str | None = None
    ) -> None:
        self.source_id = source_id
        super().__init__(message)


class GenerationError(PyNotebookLMError):
    """
    Raised when content generation fails.

    This can occur when:
    - Not enough sources in notebook
    - Generation process encounters an error
    - Invalid generation parameters
    """

    def __init__(
        self, message: str = "Content generation failed", artifact_id: str | None = None
    ) -> None:
        self.artifact_id = artifact_id
        super().__init__(message)


class GenerationTimeoutError(GenerationError):
    """
    Raised when content generation exceeds the maximum allowed time.

    Attributes:
        timeout: The timeout value in seconds that was exceeded.
    """

    def __init__(self, timeout: int, artifact_id: str | None = None) -> None:
        self.timeout = timeout
        super().__init__(
            message=f"Generation timed out after {timeout} seconds",
            artifact_id=artifact_id,
        )


class RateLimitError(PyNotebookLMError):
    """
    Raised when the API rate limit is exceeded.

    Attributes:
        retry_after: Suggested time to wait before retrying (in seconds).
    """

    def __init__(
        self, message: str = "Rate limit exceeded", retry_after: int | None = None
    ) -> None:
        self.retry_after = retry_after
        if retry_after:
            message = f"{message}. Retry after {retry_after} seconds."
        super().__init__(message)


class APIError(PyNotebookLMError):
    """
    Raised when the NotebookLM internal API returns an error.

    Attributes:
        status_code: HTTP status code (if applicable).
        response_body: Raw response body from the API.
    """

    def __init__(
        self,
        message: str = "API error occurred",
        status_code: int | None = None,
        response_body: str | None = None,
    ) -> None:
        self.status_code = status_code
        self.response_body = response_body
        if status_code:
            message = f"{message} (status: {status_code})"
        super().__init__(message)


class BrowserError(PyNotebookLMError):
    """
    Raised when browser automation fails.

    This can occur when:
    - Playwright fails to launch browser
    - Page navigation fails
    - JavaScript execution fails
    """

    def __init__(self, message: str = "Browser automation failed") -> None:
        super().__init__(message)


class SessionError(PyNotebookLMError):
    """
    Raised when there's an issue with the browser session.

    This can occur when:
    - Session is not initialized
    - Session has been closed
    - Cookie injection fails
    """

    def __init__(self, message: str = "Session error") -> None:
        super().__init__(message)
