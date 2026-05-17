"""Rate limiting and concurrency control for AI API calls."""

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Optional, Callable
from functools import wraps
import threading

logger = logging.getLogger(__name__)


@dataclass
class RateLimit:
    """Rate limit configuration."""
    requests_per_minute: int = 60
    tokens_per_minute: int = 100000
    min_interval_seconds: float = 0.5  # Minimum time between requests


# Default rate limits for different providers
PROVIDER_RATE_LIMITS = {
    'openai': RateLimit(
        requests_per_minute=500,
        tokens_per_minute=200000,
        min_interval_seconds=0.1,
    ),
    'claude': RateLimit(
        requests_per_minute=60,
        tokens_per_minute=100000,
        min_interval_seconds=0.5,
    ),
    'kimi': RateLimit(
        requests_per_minute=30,
        tokens_per_minute=50000,
        min_interval_seconds=1.0,
    ),
}


class RateLimiter:
    """
    Token bucket rate limiter for API calls.

    Supports:
    - Requests per minute limit
    - Tokens per minute limit
    - Minimum interval between requests
    - Concurrent request limiting
    """

    def __init__(
        self,
        rate_limit: Optional[RateLimit] = None,
        max_concurrent: int = 5,
    ):
        self.rate_limit = rate_limit or RateLimit()
        self.max_concurrent = max_concurrent

        # Token bucket state
        self._request_tokens = self.rate_limit.requests_per_minute
        self._token_tokens = self.rate_limit.tokens_per_minute
        self._last_refill = time.time()
        self._last_request = 0.0

        # Concurrency control
        self._semaphore = threading.Semaphore(max_concurrent)
        self._lock = threading.Lock()

        # Statistics
        self._total_requests = 0
        self._total_wait_time = 0.0

    def _refill_tokens(self):
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self._last_refill
        self._last_refill = now

        # Refill based on per-minute rate
        refill_factor = elapsed / 60.0

        self._request_tokens = min(
            self.rate_limit.requests_per_minute,
            self._request_tokens + self.rate_limit.requests_per_minute * refill_factor
        )
        self._token_tokens = min(
            self.rate_limit.tokens_per_minute,
            self._token_tokens + self.rate_limit.tokens_per_minute * refill_factor
        )

    def acquire(self, estimated_tokens: int = 1000) -> float:
        """
        Acquire permission to make an API call.

        Args:
            estimated_tokens: Estimated tokens for the request

        Returns:
            Wait time in seconds (0 if no wait needed)
        """
        with self._lock:
            self._refill_tokens()

            wait_time = 0.0

            # Check minimum interval
            time_since_last = time.time() - self._last_request
            if time_since_last < self.rate_limit.min_interval_seconds:
                wait_time = max(wait_time, self.rate_limit.min_interval_seconds - time_since_last)

            # Check request rate
            if self._request_tokens < 1:
                wait_time = max(wait_time, 60.0 / self.rate_limit.requests_per_minute)

            # Check token rate
            if self._token_tokens < estimated_tokens:
                wait_time = max(wait_time, 60.0 * estimated_tokens / self.rate_limit.tokens_per_minute)

            if wait_time > 0:
                self._total_wait_time += wait_time
                logger.debug(f"Rate limit: waiting {wait_time:.2f}s")

            return wait_time

    def release(self, actual_tokens: int = 1000):
        """
        Release tokens after API call completion.

        Args:
            actual_tokens: Actual tokens used in the request
        """
        with self._lock:
            self._request_tokens = max(0, self._request_tokens - 1)
            self._token_tokens = max(0, self._token_tokens - actual_tokens)
            self._last_request = time.time()
            self._total_requests += 1

    def __enter__(self):
        """Context manager entry - acquire semaphore and wait if needed."""
        self._semaphore.acquire()
        wait_time = self.acquire()
        if wait_time > 0:
            time.sleep(wait_time)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - release semaphore."""
        self._semaphore.release()
        return False

    def get_stats(self) -> dict:
        """Get rate limiter statistics."""
        return {
            'total_requests': self._total_requests,
            'total_wait_time': round(self._total_wait_time, 2),
            'current_request_tokens': round(self._request_tokens, 1),
            'current_token_tokens': round(self._token_tokens, 1),
        }


class MultiProviderRateLimiter:
    """Rate limiter that manages multiple providers."""

    def __init__(self, max_concurrent_per_provider: int = 3):
        self._limiters: dict[str, RateLimiter] = {}
        self._max_concurrent = max_concurrent_per_provider

    def get_limiter(self, provider: str) -> RateLimiter:
        """Get or create rate limiter for a provider."""
        if provider not in self._limiters:
            rate_limit = PROVIDER_RATE_LIMITS.get(provider, RateLimit())
            self._limiters[provider] = RateLimiter(
                rate_limit=rate_limit,
                max_concurrent=self._max_concurrent,
            )
        return self._limiters[provider]

    def acquire(self, provider: str, estimated_tokens: int = 1000) -> float:
        """Acquire permission for a specific provider."""
        return self.get_limiter(provider).acquire(estimated_tokens)

    def release(self, provider: str, actual_tokens: int = 1000):
        """Release tokens for a specific provider."""
        self.get_limiter(provider).release(actual_tokens)

    def get_all_stats(self) -> dict:
        """Get statistics for all providers."""
        return {
            provider: limiter.get_stats()
            for provider, limiter in self._limiters.items()
        }


# Global rate limiter instance
_global_rate_limiter: Optional[MultiProviderRateLimiter] = None


def get_rate_limiter() -> MultiProviderRateLimiter:
    """Get the global rate limiter instance."""
    global _global_rate_limiter
    if _global_rate_limiter is None:
        _global_rate_limiter = MultiProviderRateLimiter()
    return _global_rate_limiter


def with_rate_limit(provider: str, estimated_tokens: int = 1000):
    """
    Decorator to apply rate limiting to a function.

    Usage:
        @with_rate_limit('openai', estimated_tokens=2000)
        def call_openai_api(prompt):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            limiter = get_rate_limiter()

            # Acquire and wait
            wait_time = limiter.acquire(provider, estimated_tokens)
            if wait_time > 0:
                time.sleep(wait_time)

            try:
                result = func(*args, **kwargs)
                return result
            finally:
                limiter.release(provider, estimated_tokens)

        return wrapper
    return decorator
