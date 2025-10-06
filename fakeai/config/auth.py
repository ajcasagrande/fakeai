"""
Authentication configuration module.

This module provides authentication-related configuration options.
"""

#  SPDX-License-Identifier: Apache-2.0

from pydantic import Field, field_validator

from .base import ModuleConfig


class AuthConfig(ModuleConfig):
    """Authentication configuration settings."""

    require_api_key: bool = Field(
        default=False,
        description="Whether to require API key authentication.",
    )
    api_keys: list[str] = Field(
        default_factory=list,
        description="List of valid API keys.",
    )
    hash_api_keys: bool = Field(
        default=False,
        description="Hash API keys for secure storage.",
    )

    @field_validator("api_keys")
    @classmethod
    def validate_api_keys(cls, v: list[str]) -> list[str]:
        """Validate API key format."""
        for key in v:
            if not key or not isinstance(key, str):
                raise ValueError("API keys must be non-empty strings")
            if len(key) < 8:
                raise ValueError("API keys must be at least 8 characters long")
            # Check for common weak patterns
            if key.lower() in ["test", "testing", "password", "12345678"]:
                import logging

                logger = logging.getLogger(__name__)
                logger.warning(
                    f"API key '{key}' appears to be a weak test key. "
                    "Use strong keys in production."
                )
        return v
