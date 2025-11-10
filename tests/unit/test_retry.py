"""Unit tests for retry utilities."""

import time
import pytest
from unittest.mock import Mock, patch
from spotify_to_ytmusic.utils.retry import (
    retry_with_backoff,
    is_rate_limit_error,
    is_network_error,
    categorize_api_error,
)
from spotify_to_ytmusic.exceptions import (
    RateLimitError,
    NetworkError,
    APIError,
    MaxRetriesExceededError,
)


class TestRetryWithBackoff:
    """Tests for the retry_with_backoff decorator."""

    def test_successful_call_no_retry(self):
        """Function should succeed on first call without retry."""
        mock_func = Mock(return_value="success")
        decorated = retry_with_backoff()(mock_func)

        result = decorated()

        assert result == "success"
        assert mock_func.call_count == 1

    def test_retries_on_exception(self):
        """Function should retry on exception."""
        mock_func = Mock(side_effect=[Exception("error"), "success"])
        mock_func.__name__ = "test_func"
        decorated = retry_with_backoff(max_attempts=2, initial_delay=0.01)(mock_func)

        result = decorated()

        assert result == "success"
        assert mock_func.call_count == 2

    def test_max_retries_exceeded(self):
        """Function should raise MaxRetriesExceededError after max attempts."""
        mock_func = Mock(side_effect=Exception("error"))
        mock_func.__name__ = "test_func"
        decorated = retry_with_backoff(max_attempts=3, initial_delay=0.01)(mock_func)

        with pytest.raises(MaxRetriesExceededError) as exc_info:
            decorated()

        assert mock_func.call_count == 3
        assert "test_func" in str(exc_info.value)
        assert "3" in str(exc_info.value)

    def test_rate_limit_error_uses_retry_after(self):
        """RateLimitError should use retry_after value for backoff."""
        mock_func = Mock(side_effect=[RateLimitError("Service", 0.01), "success"])
        mock_func.__name__ = "test_func"
        decorated = retry_with_backoff(
            max_attempts=2,
            initial_delay=1.0,
            rate_limit_exceptions=(RateLimitError,),
        )(mock_func)

        start_time = time.time()
        result = decorated()
        elapsed = time.time() - start_time

        assert result == "success"
        assert mock_func.call_count == 2
        # Should wait for retry_after (0.01s) not initial_delay (1.0s)
        assert elapsed < 0.5

    def test_exponential_backoff(self):
        """Backoff delay should increase exponentially."""
        mock_func = Mock(
            side_effect=[Exception("error"), Exception("error"), "success"]
        )
        mock_func.__name__ = "test_func"
        decorated = retry_with_backoff(
            max_attempts=3,
            initial_delay=0.01,
            exponential_base=2.0,
        )(mock_func)

        start_time = time.time()
        result = decorated()
        elapsed = time.time() - start_time

        assert result == "success"
        assert mock_func.call_count == 3
        # Total wait: 0.01 + 0.02 ≈ 0.03s
        assert elapsed >= 0.03

    def test_max_delay_cap(self):
        """Backoff delay should be capped at max_delay."""
        mock_func = Mock(side_effect=[Exception("error"), "success"])
        mock_func.__name__ = "test_func"
        decorated = retry_with_backoff(
            max_attempts=2,
            initial_delay=10.0,
            max_delay=0.01,
        )(mock_func)

        start_time = time.time()
        result = decorated()
        elapsed = time.time() - start_time

        assert result == "success"
        # Should wait max_delay (0.01s) not initial_delay (10.0s)
        assert elapsed < 0.5

    def test_specific_exceptions_only(self):
        """Decorator should only catch specified exceptions."""
        mock_func = Mock(side_effect=ValueError("wrong exception"))
        mock_func.__name__ = "test_func"
        decorated = retry_with_backoff(
            max_attempts=3,
            initial_delay=0.01,
            exceptions=(NetworkError,),
        )(mock_func)

        with pytest.raises(ValueError):
            decorated()

        assert mock_func.call_count == 1

    def test_preserves_function_metadata(self):
        """Decorator should preserve function metadata."""

        def test_function():
            """Test docstring."""
            return "result"

        decorated = retry_with_backoff()(test_function)

        assert decorated.__name__ == "test_function"
        assert decorated.__doc__ == "Test docstring."

    def test_rate_limit_error_max_retries(self):
        """RateLimitError should raise MaxRetriesExceededError after max attempts."""
        mock_func = Mock(side_effect=RateLimitError("Service", 0.01))
        mock_func.__name__ = "test_func"
        decorated = retry_with_backoff(
            max_attempts=2,
            initial_delay=0.01,
            rate_limit_exceptions=(RateLimitError,),
        )(mock_func)

        with pytest.raises(MaxRetriesExceededError):
            decorated()

        assert mock_func.call_count == 2


class TestIsRateLimitError:
    """Tests for is_rate_limit_error function."""

    @pytest.mark.parametrize("error_message,expected", [
        ("rate limit exceeded", True),
        ("too many requests", True),
        ("HTTP 429 error", True),
        ("quota exceeded", True),
        ("request throttled", True),
        ("Rate Limit Exceeded", True),  # case insensitive
        ("server error", False),
        ("connection timeout", False),
    ])
    def test_detects_rate_limit_errors(self, error_message, expected):
        """Should correctly identify rate limit errors."""
        error = Exception(error_message)
        assert is_rate_limit_error(error) is expected


class TestIsNetworkError:
    """Tests for is_network_error function."""

    @pytest.mark.parametrize("error_message,expected", [
        ("connection refused", True),
        ("request timeout", True),
        ("network error", True),
        ("DNS resolution failed", True),
        ("host unreachable", True),
        ("socket error", True),
        ("Connection Timeout", True),  # case insensitive
        ("validation error", False),
        ("rate limit", False),
    ])
    def test_detects_network_errors(self, error_message, expected):
        """Should correctly identify network errors."""
        error = Exception(error_message)
        assert is_network_error(error) is expected


class TestCategorizeAPIError:
    """Tests for categorize_api_error function."""

    def test_categorizes_rate_limit_error(self):
        """Should categorize rate limit errors."""
        error = Exception("rate limit exceeded")
        result = categorize_api_error(error, "Spotify")

        assert isinstance(result, RateLimitError)
        assert result.service == "Spotify"

    def test_categorizes_network_error(self):
        """Should categorize network errors."""
        error = Exception("connection timeout")
        result = categorize_api_error(error, "YouTube Music")

        assert isinstance(result, NetworkError)
        assert "YouTube Music" in str(result)

    def test_categorizes_generic_api_error(self):
        """Should categorize generic errors as APIError."""
        error = Exception("server error")
        result = categorize_api_error(error, "Spotify")

        assert isinstance(result, APIError)
        assert result.service == "Spotify"

    def test_extracts_retry_after_from_rate_limit(self):
        """Should extract retry_after from rate limit error."""

        class RateLimitException(Exception):
            retry_after = 60

        error = RateLimitException("rate limit exceeded")
        result = categorize_api_error(error, "Spotify")

        assert isinstance(result, RateLimitError)
        assert result.retry_after == 60

    def test_extracts_status_code_from_error(self):
        """Should extract status_code from error."""

        class HTTPError(Exception):
            status_code = 500

        error = HTTPError("server error")
        result = categorize_api_error(error, "Spotify")

        assert isinstance(result, APIError)
        assert result.status_code == 500

    def test_extracts_http_status_from_error(self):
        """Should extract http_status as fallback for status_code."""

        class HTTPError(Exception):
            http_status = 503

        error = HTTPError("service unavailable")
        result = categorize_api_error(error, "Spotify")

        assert isinstance(result, APIError)
        assert result.status_code == 503

    def test_handles_missing_status_code(self):
        """Should handle errors without status codes."""
        error = Exception("generic error")
        result = categorize_api_error(error, "Spotify")

        assert isinstance(result, APIError)
        assert result.status_code is None
