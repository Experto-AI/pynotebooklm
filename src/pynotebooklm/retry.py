"""
Retry logic with exponential backoff for PyNotebookLM.

This module provides retry decorators and strategies for handling transient
errors in API calls with configurable exponential backoff.
"""

import asyncio
import logging
import os
import random
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

from .exceptions import (
    APIError,
    AuthenticationError,
    NotebookNotFoundError,
    RateLimitError,
)

logger = logging.getLogger(__name__)

# Type variable for generic async functions
F = TypeVar("F", bound=Callable[..., Any])


class RetryStrategy:
    """
    Configuration for retry behavior with exponential backoff.

    Attributes:
        max_attempts: Maximum number of retry attempts (including initial attempt).
        base_delay: Initial delay between retries in seconds.
        max_delay: Maximum delay between retries in seconds.
        exponential_base: Base for exponential backoff calculation.
        jitter: Whether to add random jitter to delays.
    """

    def __init__(
        self,
        max_attempts: int | None = None,
        base_delay: float | None = None,
        max_delay: float | None = None,
        exponential_base: float = 2.0,
        jitter: bool = True,
    ) -> None:
        """
        Initialize retry strategy.

        Args:
            max_attempts: Maximum retry attempts. Defaults to PYNOTEBOOKLM_MAX_RETRIES env var or 3.
            base_delay: Initial delay in seconds. Defaults to PYNOTEBOOKLM_BASE_DELAY or 1.0.
            max_delay: Maximum delay in seconds. Defaults to PYNOTEBOOKLM_MAX_DELAY or 60.0.
            exponential_base: Base for exponential calculation.
            jitter: Whether to add random jitter to reduce thundering herd.
        """
        self.max_attempts = (
            max_attempts
            if max_attempts is not None
            else int(os.getenv("PYNOTEBOOKLM_MAX_RETRIES", "3"))
        )
        self.base_delay = (
            base_delay
            if base_delay is not None
            else float(os.getenv("PYNOTEBOOKLM_BASE_DELAY", "1.0"))
        )
        self.max_delay = (
            max_delay
            if max_delay is not None
            else float(os.getenv("PYNOTEBOOKLM_MAX_DELAY", "60.0"))
        )
        self.exponential_base = exponential_base
        self.jitter = jitter

    def calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay for a given attempt number.

        Uses exponential backoff: delay = base_delay * (exponential_base ** attempt)
        Capped at max_delay, with optional jitter.

        Args:
            attempt: Current attempt number (0-indexed).

        Returns:
            Delay in seconds before next retry.
        """
        # Calculate exponential delay
        delay = self.base_delay * (self.exponential_base**attempt)

        # Cap at max_delay
        delay = min(delay, self.max_delay)

        # Add jitter if enabled (random value between 0 and delay)
        if self.jitter:
            delay = delay * (0.5 + random.random() / 2)

        return delay

    def should_retry(self, exception: Exception, attempt: int) -> bool:
        """
        Determine if an exception should trigger a retry.

        Args:
            exception: The exception that was raised.
            attempt: Current attempt number (0-indexed).

        Returns:
            True if should retry, False otherwise.
        """
        # Don't retry if we've exceeded max attempts
        if attempt >= self.max_attempts:
            return False

        # Always retry rate limit errors
        if isinstance(exception, RateLimitError):
            return True

        # Retry on transient API errors (5xx status codes)
        if isinstance(exception, APIError):
            if exception.status_code and 500 <= exception.status_code < 600:
                return True

        # Don't retry on authentication or not found errors
        if isinstance(exception, AuthenticationError | NotebookNotFoundError):
            return False

        return False


def with_retry(strategy: RetryStrategy | None = None) -> Callable[[F], F]:
    """
    Decorator to add retry logic with exponential backoff to async functions.

    Args:
        strategy: Retry strategy to use. If None, uses default strategy.

    Returns:
        Decorated function with retry logic.

    Example:
        >>> @with_retry()
        ... async def call_api():
        ...     # Your API call here
        ...     pass
        >>>
        >>> # With custom strategy
        >>> @with_retry(RetryStrategy(max_attempts=5, base_delay=2.0))
        ... async def call_api_with_custom_retry():
        ...     pass
    """

    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            retry_strategy = strategy or RetryStrategy()
            last_exception: Exception | None = None

            for attempt in range(retry_strategy.max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e

                    # Check if we should retry
                    if not retry_strategy.should_retry(e, attempt):
                        logger.debug(
                            "Not retrying %s after attempt %d: %s",
                            func.__name__,
                            attempt + 1,
                            e,
                        )
                        raise

                    # Calculate delay and log
                    delay = retry_strategy.calculate_delay(attempt)
                    logger.info(
                        "Retrying %s after attempt %d/%d (delay: %.2fs): %s",
                        func.__name__,
                        attempt + 1,
                        retry_strategy.max_attempts,
                        delay,
                        str(e)[:100],
                    )

                    # Wait before retry
                    await asyncio.sleep(delay)

            # If we get here, all retries failed
            if last_exception:
                logger.error(
                    "All retry attempts failed for %s: %s",
                    func.__name__,
                    last_exception,
                )
                raise last_exception

            # This should never happen, but satisfy type checker
            raise RuntimeError("Retry logic failed unexpectedly")

        return wrapper  # type: ignore[return-value]

    return decorator
