"""Retry utilities with exponential backoff for API calls."""

import time
import logging
from functools import wraps
from typing import Callable, Type, Tuple
from ..exceptions import (
    MaxRetriesExceededError,
    RateLimitError,
    NetworkError,
    APIError,
)

logger = logging.getLogger(__name__)


def retry_with_backoff(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    rate_limit_exceptions: Tuple[Type[Exception], ...] = (RateLimitError,),
):
    """Decorator to retry a function with exponential backoff.

    Args:
        max_attempts: Maximum number of retry attempts
        initial_delay: Initial delay in seconds before first retry
        max_delay: Maximum delay in seconds between retries
        exponential_base: Base for exponential backoff calculation
        exceptions: Tuple of exceptions to catch and retry
        rate_limit_exceptions: Tuple of rate limit exceptions (will use custom backoff)

    Returns:
        Decorated function with retry logic
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 0
            delay = initial_delay

            while attempt < max_attempts:
                try:
                    return func(*args, **kwargs)
                except rate_limit_exceptions as e:
                    attempt += 1
                    if attempt >= max_attempts:
                        logger.error(
                            f"Max retries exceeded for {func.__name__} due to rate limit"
                        )
                        raise MaxRetriesExceededError(
                            func.__name__, max_attempts
                        ) from e

                    # Use retry_after from exception if available
                    if hasattr(e, "retry_after") and e.retry_after:
                        wait_time = float(e.retry_after)
                    else:
                        wait_time = min(delay, max_delay)

                    logger.warning(
                        f"Rate limit hit for {func.__name__}. "
                        f"Attempt {attempt}/{max_attempts}. "
                        f"Waiting {wait_time:.1f}s before retry..."
                    )
                    time.sleep(wait_time)
                    delay *= exponential_base

                except exceptions as e:
                    attempt += 1
                    if attempt >= max_attempts:
                        logger.error(
                            f"Max retries exceeded for {func.__name__}: {str(e)}"
                        )
                        raise MaxRetriesExceededError(
                            func.__name__, max_attempts
                        ) from e

                    wait_time = min(delay, max_delay)
                    logger.warning(
                        f"Error in {func.__name__}: {str(e)}. "
                        f"Attempt {attempt}/{max_attempts}. "
                        f"Retrying in {wait_time:.1f}s..."
                    )
                    time.sleep(wait_time)
                    delay *= exponential_base

            # Should not reach here, but for type checker satisfaction
            return func(*args, **kwargs)

        return wrapper

    return decorator


def is_rate_limit_error(error: Exception) -> bool:
    """Check if an error is a rate limit error.

    Args:
        error: Exception to check

    Returns:
        True if the error is a rate limit error, False otherwise
    """
    # Check for common rate limit indicators
    error_str = str(error).lower()
    rate_limit_indicators = [
        "rate limit",
        "too many requests",
        "429",
        "quota exceeded",
        "throttle",
    ]
    return any(indicator in error_str for indicator in rate_limit_indicators)


def is_network_error(error: Exception) -> bool:
    """Check if an error is a network-related error.

    Args:
        error: Exception to check

    Returns:
        True if the error is a network error, False otherwise
    """
    error_str = str(error).lower()
    network_indicators = [
        "connection",
        "timeout",
        "network",
        "dns",
        "unreachable",
        "socket",
    ]
    return any(indicator in error_str for indicator in network_indicators)


def categorize_api_error(error: Exception, service: str) -> Exception:
    """Categorize a generic API error into a specific exception type.

    Args:
        error: The original exception
        service: Name of the service (e.g., "Spotify", "YouTube Music")

    Returns:
        A categorized exception (RateLimitError, NetworkError, or APIError)
    """
    if is_rate_limit_error(error):
        # Try to extract retry_after if available
        retry_after = None
        if hasattr(error, "retry_after"):
            retry_after = error.retry_after
        return RateLimitError(service, retry_after)

    if is_network_error(error):
        return NetworkError(f"{service}: {str(error)}")

    # Default to generic API error
    status_code = getattr(error, "status_code", None) or getattr(
        error, "http_status", None
    )
    return APIError(service, str(error), status_code)
