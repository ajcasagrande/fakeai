"""
Rate limiting implementation for FakeAI using token bucket algorithm.

This module provides a thread-safe, per-API-key rate limiting system that enforces
both requests per minute (RPM) and tokens per minute (TPM) limits using the
token bucket algorithm with continuous refill.
"""
#  SPDX-License-Identifier: Apache-2.0

import threading
import time
from dataclasses import dataclass
from typing import Literal


@dataclass
class RateLimitTier:
    """Configuration for a rate limit tier."""

    name: str
    rpm: int  # Requests per minute
    tpm: int  # Tokens per minute


# Pre-defined rate limit tiers matching OpenAI structure
RATE_LIMIT_TIERS = {
    "free": RateLimitTier(name="free", rpm=60, tpm=10_000),
    "tier-1": RateLimitTier(name="tier-1", rpm=500, tpm=30_000),
    "tier-2": RateLimitTier(name="tier-2", rpm=5_000, tpm=450_000),
    "tier-3": RateLimitTier(name="tier-3", rpm=10_000, tpm=1_000_000),
    "tier-4": RateLimitTier(name="tier-4", rpm=30_000, tpm=5_000_000),
    "tier-5": RateLimitTier(name="tier-5", rpm=100_000, tpm=15_000_000),
}


class RateLimitBucket:
    """
    Token bucket implementation for rate limiting with continuous refill.

    The token bucket algorithm allows for smooth rate limiting with burst capacity.
    Tokens are continuously refilled at a constant rate, and requests consume tokens.
    """

    def __init__(self, capacity: int, refill_rate: float):
        """
        Initialize a rate limit bucket.

        Args:
            capacity: Maximum number of tokens the bucket can hold
            refill_rate: Number of tokens added per second
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = float(capacity)  # Start with full bucket
        self.last_refill_time = time.time()
        self._lock = threading.Lock()

    def _refill(self) -> None:
        """Refill tokens based on elapsed time since last refill."""
        current_time = time.time()
        elapsed = current_time - self.last_refill_time

        # Calculate tokens to add based on elapsed time
        tokens_to_add = elapsed * self.refill_rate

        # Refill up to capacity
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_refill_time = current_time

    def try_consume(self, tokens: int = 1) -> tuple[bool, float]:
        """
        Try to consume tokens from the bucket.

        Args:
            tokens: Number of tokens to consume

        Returns:
            Tuple of (success: bool, retry_after: float)
            - success: True if tokens were consumed, False otherwise
            - retry_after: Seconds to wait before retrying (0 if success)
        """
        with self._lock:
            self._refill()

            if self.tokens >= tokens:
                self.tokens -= tokens
                return True, 0.0

            # Calculate how long until we have enough tokens
            tokens_needed = tokens - self.tokens
            retry_after = tokens_needed / self.refill_rate
            return False, retry_after

    def remaining(self) -> int:
        """Get the number of tokens currently available."""
        with self._lock:
            self._refill()
            return int(self.tokens)

    def reset_time(self) -> float:
        """Get the Unix timestamp when the bucket will be full again."""
        with self._lock:
            self._refill()
            tokens_to_full = self.capacity - self.tokens
            time_to_full = tokens_to_full / self.refill_rate
            return time.time() + time_to_full


class RateLimiter:
    """
    Singleton rate limiter that tracks per-API-key limits.

    Enforces both RPM (requests per minute) and TPM (tokens per minute) limits
    using separate token buckets for each metric.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """Ensure only one instance exists (singleton pattern)."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(RateLimiter, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        """Initialize the rate limiter (only once)."""
        if self._initialized:
            return

        # Per-API-key buckets: key -> {"rpm": bucket, "tpm": bucket}
        self._buckets: dict[str, dict[str, RateLimitBucket]] = {}
        self._config_lock = threading.Lock()

        # Default configuration (can be overridden)
        self._default_tier = "tier-1"
        self._rpm_override: int | None = None
        self._tpm_override: int | None = None

        self._initialized = True

    def configure(
        self,
        tier: str = "tier-1",
        rpm_override: int | None = None,
        tpm_override: int | None = None,
    ) -> None:
        """
        Configure rate limiter with tier or custom limits.

        Args:
            tier: Rate limit tier name (free, tier-1, tier-2, etc.)
            rpm_override: Custom RPM limit (overrides tier)
            tpm_override: Custom TPM limit (overrides tier)
        """
        with self._config_lock:
            self._default_tier = tier
            self._rpm_override = rpm_override
            self._tpm_override = tpm_override

    def _get_or_create_buckets(self, api_key: str) -> dict[str, RateLimitBucket]:
        """Get or create rate limit buckets for an API key."""
        if api_key not in self._buckets:
            # Determine limits
            if self._rpm_override is not None and self._tpm_override is not None:
                rpm_limit = self._rpm_override
                tpm_limit = self._tpm_override
            else:
                tier = RATE_LIMIT_TIERS.get(
                    self._default_tier, RATE_LIMIT_TIERS["tier-1"]
                )
                rpm_limit = self._rpm_override or tier.rpm
                tpm_limit = self._tpm_override or tier.tpm

            # Create buckets with per-second refill rates
            self._buckets[api_key] = {
                "rpm": RateLimitBucket(
                    capacity=rpm_limit,
                    refill_rate=rpm_limit / 60.0,  # Tokens per second
                ),
                "tpm": RateLimitBucket(
                    capacity=tpm_limit,
                    refill_rate=tpm_limit / 60.0,  # Tokens per second
                ),
            }

        return self._buckets[api_key]

    def check_rate_limit(
        self, api_key: str, tokens: int = 0
    ) -> tuple[bool, str | None, dict[str, str]]:
        """
        Check if a request is within rate limits and consume resources.

        Args:
            api_key: The API key making the request
            tokens: Number of tokens in the request (for TPM limit)

        Returns:
            Tuple of (allowed: bool, retry_after: str | None, headers: dict)
            - allowed: True if request is allowed, False if rate limited
            - retry_after: Seconds to wait as string (None if allowed)
            - headers: Dictionary of x-ratelimit-* headers
        """
        buckets = self._get_or_create_buckets(api_key)

        # Try to consume 1 request from RPM bucket
        rpm_allowed, rpm_retry = buckets["rpm"].try_consume(1)

        # Try to consume tokens from TPM bucket
        tpm_allowed, tpm_retry = buckets["tpm"].try_consume(tokens)

        # Build rate limit headers
        headers = self._build_headers(buckets)

        # If either limit is exceeded, deny the request
        if not rpm_allowed:
            return False, str(int(rpm_retry) + 1), headers
        if not tpm_allowed:
            # Refund the RPM token since we're denying the request
            buckets["rpm"].tokens = min(
                buckets["rpm"].capacity, buckets["rpm"].tokens + 1
            )
            return False, str(int(tpm_retry) + 1), headers

        return True, None, headers

    def _build_headers(self, buckets: dict[str, RateLimitBucket]) -> dict[str, str]:
        """
        Build x-ratelimit-* headers for the response.

        Args:
            buckets: Dictionary containing rpm and tpm buckets

        Returns:
            Dictionary of header name -> value
        """
        rpm_bucket = buckets["rpm"]
        tpm_bucket = buckets["tpm"]

        return {
            "x-ratelimit-limit-requests": str(rpm_bucket.capacity),
            "x-ratelimit-limit-tokens": str(tpm_bucket.capacity),
            "x-ratelimit-remaining-requests": str(rpm_bucket.remaining()),
            "x-ratelimit-remaining-tokens": str(tpm_bucket.remaining()),
            "x-ratelimit-reset-requests": str(int(rpm_bucket.reset_time())),
            "x-ratelimit-reset-tokens": str(int(tpm_bucket.reset_time())),
        }

    def get_headers(self, api_key: str) -> dict[str, str]:
        """
        Get rate limit headers without consuming resources.

        Args:
            api_key: The API key to get headers for

        Returns:
            Dictionary of header name -> value
        """
        buckets = self._get_or_create_buckets(api_key)
        return self._build_headers(buckets)

    def reset(self, api_key: str | None = None) -> None:
        """
        Reset rate limits for testing purposes.

        Args:
            api_key: Specific API key to reset, or None to reset all
        """
        with self._config_lock:
            if api_key is None:
                self._buckets.clear()
            elif api_key in self._buckets:
                del self._buckets[api_key]
