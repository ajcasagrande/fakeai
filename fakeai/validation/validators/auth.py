"""
Authentication validator.

Validates API keys and authentication headers.
"""

#  SPDX-License-Identifier: Apache-2.0

from typing import Any

from fakeai.validation.base import ValidationResult


class AuthValidator:
    """
    Validator that checks API authentication.

    Validates that requests include valid API keys when required.
    """

    def __init__(
        self,
        valid_api_keys: list[str] | None = None,
        require_api_key: bool = True,
        name: str = "AuthValidator",
    ):
        """
        Initialize the auth validator.

        Args:
            valid_api_keys: List of valid API keys (None means all keys valid)
            require_api_key: Whether to require an API key
            name: Name for this validator
        """
        self._valid_api_keys = set(valid_api_keys) if valid_api_keys else None
        self._require_api_key = require_api_key
        self._name = name

    @property
    def name(self) -> str:
        """Get the name of this validator."""
        return self._name

    def validate(
        self, request: Any, context: dict[str, Any] | None = None
    ) -> ValidationResult:
        """
        Validate authentication for a request.

        Expected context keys:
            - api_key: API key from request header (optional)

        Args:
            request: The request object (unused)
            context: Context containing API key

        Returns:
            ValidationResult indicating success or failure
        """
        context = context or {}

        # Extract API key from context
        api_key = context.get("api_key")

        # Check if API key is required
        if self._require_api_key and not api_key:
            return ValidationResult.failure(
                message="Authentication required. Please provide an API key.",
                code="missing_api_key",
                metadata={"require_api_key": True},
            )

        # If we have a specific list of valid keys, check against it
        if api_key and self._valid_api_keys is not None:
            if api_key not in self._valid_api_keys:
                return ValidationResult.failure(
                    message="Invalid API key provided.",
                    code="invalid_api_key",
                    metadata={"api_key_provided": True},
                )

        # Authentication successful
        return ValidationResult.success(
            metadata={
                "authenticated": api_key is not None,
                "api_key_provided": api_key is not None,
            }
        )
