"""
Rate limiting configuration module.

This module provides rate limiting configuration options.
"""

#  SPDX-License-Identifier: Apache-2.0

from enum import Enum

from pydantic import Field, field_validator

from .base import ModuleConfig


class RateLimitTier(str, Enum):
    """Rate limit tiers matching OpenAI's pricing tiers."""

    FREE = "free"
    TIER_1 = "tier-1"
    TIER_2 = "tier-2"
    TIER_3 = "tier-3"
    TIER_4 = "tier-4"
    TIER_5 = "tier-5"


# Tier limits (requests per minute, tokens per minute)
TIER_LIMITS = {
    RateLimitTier.FREE: (3, 200_000),
    RateLimitTier.TIER_1: (500, 2_000_000),
    RateLimitTier.TIER_2: (5000, 10_000_000),
    RateLimitTier.TIER_3: (10000, 30_000_000),
    RateLimitTier.TIER_4: (30000, 150_000_000),
    RateLimitTier.TIER_5: (30000, 300_000_000),
}


class RateLimitConfig(ModuleConfig):
    """Rate limiting configuration settings."""

    enabled: bool = Field(
        default=False,
        description="Enable rate limiting.",
    )
    tier: RateLimitTier = Field(
        default=RateLimitTier.TIER_1,
        description="Rate limit tier (free, tier-1, tier-2, tier-3, tier-4, tier-5).",
    )
    rpm_override: int | None = Field(
        default=None,
        description="Custom requests per minute limit (overrides tier).",
    )
    tpm_override: int | None = Field(
        default=None,
        description="Custom tokens per minute limit (overrides tier).",
    )

    @field_validator("tier", mode="before")
    @classmethod
    def validate_tier(cls, v: str | RateLimitTier) -> RateLimitTier:
        """Validate and convert tier."""
        if isinstance(v, RateLimitTier):
            return v
        if isinstance(v, str):
            # Handle both "tier-1" and "tier_1" formats
            v = v.lower().replace("_", "-")
            try:
                return RateLimitTier(v)
            except ValueError:
                valid = ", ".join([tier.value for tier in RateLimitTier])
                raise ValueError(f"Rate limit tier must be one of: {valid}")
        raise ValueError("Rate limit tier must be a string or RateLimitTier enum")

    @field_validator("rpm_override")
    @classmethod
    def validate_rpm_override(cls, v: int | None) -> int | None:
        """Validate RPM override."""
        if v is not None and v < 1:
            raise ValueError("RPM override must be at least 1")
        return v

    @field_validator("tpm_override")
    @classmethod
    def validate_tpm_override(cls, v: int | None) -> int | None:
        """Validate TPM override."""
        if v is not None and v < 1:
            raise ValueError("TPM override must be at least 1")
        return v

    def get_rpm_limit(self) -> int:
        """Get effective requests per minute limit."""
        if self.rpm_override is not None:
            return self.rpm_override
        return TIER_LIMITS[self.tier][0]

    def get_tpm_limit(self) -> int:
        """Get effective tokens per minute limit."""
        if self.tpm_override is not None:
            return self.tpm_override
        return TIER_LIMITS[self.tier][1]
