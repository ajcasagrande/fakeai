"""
Security configuration module.

This module provides security-related configuration options.
"""

#  SPDX-License-Identifier: Apache-2.0

from pydantic import Field, field_validator

from .base import ModuleConfig


class SecurityConfig(ModuleConfig):
    """Security configuration settings."""

    # Master security flag
    enable_security: bool = Field(
        default=False,
        description="Master flag to enable all security features (overrides individual flags).",
    )

    # Input validation
    enable_input_validation: bool = Field(
        default=False,
        description="Enable input validation and sanitization.",
    )
    enable_injection_detection: bool = Field(
        default=False,
        description="Enable injection attack detection.",
    )

    # Request limits
    max_request_size: int = Field(
        default=100 * 1024 * 1024,
        description="Maximum request size in bytes (default: 100 MB).",
    )

    # Abuse detection
    enable_abuse_detection: bool = Field(
        default=False,
        description="Enable IP-based abuse detection and banning.",
    )
    abuse_cleanup_interval: int = Field(
        default=3600,
        description="Interval for cleaning up old abuse records (seconds).",
    )

    # CORS settings
    cors_allowed_origins: list[str] = Field(
        default_factory=lambda: ["*"],
        description="CORS allowed origins (use ['*'] for all or specific domains).",
    )
    cors_allow_credentials: bool = Field(
        default=True,
        description="Allow credentials in CORS requests.",
    )

    @field_validator("max_request_size")
    @classmethod
    def validate_max_request_size(cls, v: int) -> int:
        """Validate maximum request size."""
        if v < 1024:  # At least 1 KB
            raise ValueError(
                "Maximum request size must be at least 1024 bytes")
        if v > 100 * 1024 * 1024:  # At most 100 MB
            raise ValueError("Maximum request size cannot exceed 100 MB")
        return v

    @field_validator("abuse_cleanup_interval")
    @classmethod
    def validate_abuse_cleanup_interval(cls, v: int) -> int:
        """Validate abuse cleanup interval."""
        if v < 60:  # At least 1 minute
            raise ValueError(
                "Abuse cleanup interval must be at least 60 seconds")
        return v

    @field_validator("cors_allowed_origins")
    @classmethod
    def validate_cors_origins(cls, v: list[str]) -> list[str]:
        """Validate CORS allowed origins."""
        if not v:
            raise ValueError("CORS allowed origins cannot be empty")
        return v

    def is_input_validation_enabled(self) -> bool:
        """Check if input validation is enabled (respects master security flag)."""
        return self.enable_security or self.enable_input_validation

    def is_injection_detection_enabled(self) -> bool:
        """Check if injection detection is enabled (respects master security flag)."""
        return self.enable_security or self.enable_injection_detection

    def is_abuse_detection_enabled(self) -> bool:
        """Check if abuse detection is enabled (respects master security flag)."""
        return self.enable_security or self.enable_abuse_detection
