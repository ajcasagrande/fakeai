"""
Rate limit validator.

Validates that requests don't exceed rate limits using the rate limiter.
"""

#  SPDX-License-Identifier: Apache-2.0

from typing import Any

from fakeai.rate_limiter import RateLimiter
from fakeai.validation.base import ValidationResult


class RateLimitValidator:
    """
    Validator that checks rate limits.

    Uses the existing RateLimiter to enforce RPM and TPM limits.
    """

    def __init__(
        self,
        rate_limiter: RateLimiter | None = None,
        name: str = "RateLimitValidator",
    ):
        """
        Initialize the rate limit validator.

        Args:
            rate_limiter: RateLimiter instance to use (creates new one if None)
            name: Name for this validator
        """
        self._rate_limiter = rate_limiter or RateLimiter()
        self._name = name

    @property
    def name(self) -> str:
        """Get the name of this validator."""
        return self._name

    def validate(
        self, request: Any, context: dict[str, Any] | None = None
    ) -> ValidationResult:
        """
        Validate rate limits for a request.

        Expected context keys:
            - api_key: API key making the request (required)
            - tokens: Number of tokens in the request (optional, default 0)

        Args:
            request: The request object (not used directly, uses context)
            context: Context containing API key and token count

        Returns:
            ValidationResult indicating success or failure
        """
        context = context or {}

        # Extract required fields
        api_key = context.get("api_key")
        if not api_key:
            return ValidationResult.failure(
                message="API key is required for rate limit validation",
                code="missing_api_key",
            )

        # Extract optional fields
        tokens = context.get("tokens", 0)

        # Check rate limit
        allowed, retry_after, headers = self._rate_limiter.check_rate_limit(
            api_key=api_key,
            tokens=tokens,
        )

        if allowed:
            return ValidationResult.success(
                metadata={
                    "rate_limit_headers": headers,
                }
            )
        else:
            # Determine which limit was exceeded
            if context.get("rpm_exceeded", False):
                limit_type = "requests per minute"
            elif context.get("tpm_exceeded", False):
                limit_type = "tokens per minute"
            else:
                limit_type = "rate"

            return ValidationResult.failure(
                message=f"Rate limit exceeded. Please retry after {retry_after} seconds.",
                code="rate_limit_exceeded",
                metadata={
                    "retry_after": retry_after,
                    "rate_limit_headers": headers,
                    "limit_type": limit_type,
                },
            )
