"""
Unit tests for retry logic and exponential backoff.
"""

import asyncio
from unittest.mock import patch

import pytest

from pynotebooklm.exceptions import (
    APIError,
    AuthenticationError,
    NotebookNotFoundError,
    RateLimitError,
)
from pynotebooklm.retry import RetryStrategy, with_retry


class TestRetryStrategy:
    """Test cases for RetryStrategy class."""

    def test_default_initialization(self):
        """Test default initialization from environment or defaults."""
        strategy = RetryStrategy()
        assert strategy.max_attempts == 3
        assert strategy.base_delay == 1.0
        assert strategy.max_delay == 60.0
        assert strategy.exponential_base == 2.0
        assert strategy.jitter is True

    def test_custom_initialization(self):
        """Test initialization with custom values."""
        strategy = RetryStrategy(
            max_attempts=5,
            base_delay=2.0,
            max_delay=120.0,
            exponential_base=3.0,
            jitter=False,
        )
        assert strategy.max_attempts == 5
        assert strategy.base_delay == 2.0
        assert strategy.max_delay == 120.0
        assert strategy.exponential_base == 3.0
        assert strategy.jitter is False

    def test_calculate_delay_exponential(self):
        """Test exponential backoff calculation."""
        strategy = RetryStrategy(base_delay=1.0, exponential_base=2.0, jitter=False)

        # Test exponential growth
        assert strategy.calculate_delay(0) == 1.0  # 1 * 2^0
        assert strategy.calculate_delay(1) == 2.0  # 1 * 2^1
        assert strategy.calculate_delay(2) == 4.0  # 1 * 2^2
        assert strategy.calculate_delay(3) == 8.0  # 1 * 2^3

    def test_calculate_delay_max_cap(self):
        """Test that delay is capped at max_delay."""
        strategy = RetryStrategy(
            base_delay=1.0, max_delay=5.0, exponential_base=2.0, jitter=False
        )

        # Should be capped at 5.0
        assert strategy.calculate_delay(10) == 5.0

    def test_calculate_delay_with_jitter(self):
        """Test that jitter adds randomness."""
        strategy = RetryStrategy(base_delay=10.0, jitter=True)

        delays = [strategy.calculate_delay(0) for _ in range(100)]

        # All delays should be between 5.0 and 10.0 (with jitter)
        assert all(5.0 <= d <= 10.0 for d in delays)

        # Should have some variance (not all the same)
        assert len(set(delays)) > 1

    def test_should_retry_rate_limit(self):
        """Test that rate limit errors are retried."""
        strategy = RetryStrategy(max_attempts=3)

        error = RateLimitError("Rate limited")
        assert strategy.should_retry(error, 0) is True
        assert strategy.should_retry(error, 1) is True
        assert strategy.should_retry(error, 2) is True
        assert strategy.should_retry(error, 3) is False  # Exceeded max

    def test_should_retry_transient_api_errors(self):
        """Test that transient API errors (5xx) are retried."""
        strategy = RetryStrategy(max_attempts=3)

        # Test 5xx errors
        for status in [500, 502, 503, 504]:
            error = APIError("Server error", status_code=status)
            assert strategy.should_retry(error, 0) is True

    def test_should_not_retry_client_errors(self):
        """Test that client errors (4xx) are not retried."""
        strategy = RetryStrategy(max_attempts=3)

        # Test 4xx errors
        for status in [400, 401, 403, 404]:
            error = APIError("Client error", status_code=status)
            assert strategy.should_retry(error, 0) is False

    def test_should_not_retry_auth_errors(self):
        """Test that authentication errors are not retried."""
        strategy = RetryStrategy(max_attempts=3)

        error = AuthenticationError("Not authenticated")
        assert strategy.should_retry(error, 0) is False

    def test_should_not_retry_not_found_errors(self):
        """Test that not found errors are not retried."""
        strategy = RetryStrategy(max_attempts=3)

        error = NotebookNotFoundError("notebook-123")
        assert strategy.should_retry(error, 0) is False

    def test_should_not_retry_after_max_attempts(self):
        """Test that retry stops after max attempts."""
        strategy = RetryStrategy(max_attempts=3)

        error = RateLimitError("Rate limited")
        assert strategy.should_retry(error, 3) is False
        assert strategy.should_retry(error, 10) is False


class TestWithRetryDecorator:
    """Test cases for with_retry decorator."""

    @pytest.mark.asyncio
    async def test_successful_call_no_retry(self):
        """Test that successful calls don't trigger retries."""
        call_count = 0

        @with_retry()
        async def successful_function():
            nonlocal call_count
            call_count += 1
            return "success"

        result = await successful_function()

        assert result == "success"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_retry_on_transient_error(self):
        """Test that transient errors trigger retries."""
        call_count = 0

        @with_retry(RetryStrategy(max_attempts=3, base_delay=0.01))
        async def failing_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise APIError("Transient error", status_code=503)
            return "success"

        result = await failing_function()

        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_no_retry_on_permanent_error(self):
        """Test that permanent errors are not retried."""
        call_count = 0

        @with_retry(RetryStrategy(max_attempts=3))
        async def failing_function():
            nonlocal call_count
            call_count += 1
            raise AuthenticationError("Not authenticated")

        with pytest.raises(AuthenticationError):
            await failing_function()

        assert call_count == 1  # No retries

    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self):
        """Test that retries stop after max attempts."""
        call_count = 0

        @with_retry(RetryStrategy(max_attempts=3, base_delay=0.01))
        async def always_failing():
            nonlocal call_count
            call_count += 1
            raise RateLimitError("Always fails")

        with pytest.raises(RateLimitError):
            await always_failing()

        assert call_count == 3

    @pytest.mark.asyncio
    async def test_retry_delay_increases(self):
        """Test that retry delays follow exponential backoff."""
        call_times = []

        @with_retry(RetryStrategy(max_attempts=3, base_delay=0.1, jitter=False))
        async def failing_function():
            call_times.append(asyncio.get_event_loop().time())
            raise APIError("Error", status_code=500)

        with pytest.raises(APIError):
            await failing_function()

        # Calculate delays between attempts
        if len(call_times) >= 2:
            delay1 = call_times[1] - call_times[0]
            # Should be approximately 0.1s (base_delay)
            assert 0.08 <= delay1 <= 0.15

        if len(call_times) >= 3:
            delay2 = call_times[2] - call_times[1]
            # Should be approximately 0.2s (base_delay * 2)
            assert 0.18 <= delay2 <= 0.25

    @pytest.mark.asyncio
    async def test_custom_retry_strategy(self):
        """Test with custom retry strategy."""
        call_count = 0

        custom_strategy = RetryStrategy(max_attempts=5, base_delay=0.01)

        @with_retry(custom_strategy)
        async def failing_function():
            nonlocal call_count
            call_count += 1
            if call_count < 4:
                raise RateLimitError("Rate limited")
            return "success"

        result = await failing_function()

        assert result == "success"
        assert call_count == 4

    @pytest.mark.asyncio
    async def test_retry_with_rate_limit_error(self):
        """Test retry behavior with rate limit errors."""
        call_count = 0

        @with_retry(RetryStrategy(max_attempts=3, base_delay=0.01))
        async def rate_limited_function():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise RateLimitError("Rate limited", retry_after=1)
            return "success"

        result = await rate_limited_function()

        assert result == "success"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_retry_preserves_exception_type(self):
        """Test that the original exception type is preserved."""

        @with_retry(RetryStrategy(max_attempts=2, base_delay=0.01))
        async def failing_function():
            raise NotebookNotFoundError("test-notebook")

        with pytest.raises(NotebookNotFoundError) as exc_info:
            await failing_function()

        assert exc_info.value.notebook_id == "test-notebook"

    @pytest.mark.asyncio
    async def test_retry_with_function_arguments(self):
        """Test that retry decorator works with function arguments."""

        @with_retry(RetryStrategy(max_attempts=2, base_delay=0.01))
        async def function_with_args(x: int, y: int) -> int:
            return x + y

        result = await function_with_args(2, 3)
        assert result == 5

    @pytest.mark.asyncio
    async def test_retry_with_kwargs(self):
        """Test that retry decorator works with keyword arguments."""

        @with_retry(RetryStrategy(max_attempts=2, base_delay=0.01))
        async def function_with_kwargs(*, name: str, value: int) -> str:
            return f"{name}={value}"

        result = await function_with_kwargs(name="test", value=42)
        assert result == "test=42"


class TestEnvironmentVariables:
    """Test that retry strategy reads from environment variables."""

    @patch.dict("os.environ", {"PYNOTEBOOKLM_MAX_RETRIES": "5"})
    def test_max_retries_from_env(self):
        """Test reading max retries from environment."""
        strategy = RetryStrategy()
        assert strategy.max_attempts == 5

    @patch.dict("os.environ", {"PYNOTEBOOKLM_BASE_DELAY": "2.5"})
    def test_base_delay_from_env(self):
        """Test reading base delay from environment."""
        strategy = RetryStrategy()
        assert strategy.base_delay == 2.5

    @patch.dict("os.environ", {"PYNOTEBOOKLM_MAX_DELAY": "120.0"})
    def test_max_delay_from_env(self):
        """Test reading max delay from environment."""
        strategy = RetryStrategy()
        assert strategy.max_delay == 120.0

    @patch.dict(
        "os.environ",
        {
            "PYNOTEBOOKLM_MAX_RETRIES": "10",
            "PYNOTEBOOKLM_BASE_DELAY": "3.0",
            "PYNOTEBOOKLM_MAX_DELAY": "180.0",
        },
    )
    def test_all_env_vars(self):
        """Test reading all environment variables."""
        strategy = RetryStrategy()
        assert strategy.max_attempts == 10
        assert strategy.base_delay == 3.0
        assert strategy.max_delay == 180.0
