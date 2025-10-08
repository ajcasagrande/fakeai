"""
Feature flags configuration module.

This module provides toggleable feature flags.
"""

#  SPDX-License-Identifier: Apache-2.0

from pydantic import Field, field_validator

from .base import ModuleConfig


class FeatureFlags(ModuleConfig):
    """Feature flags for enabling/disabling functionality."""

    # Caching features
    enable_prompt_caching: bool = Field(
        default=True,
        description="Enable prompt caching simulation.",
    )
    cache_ttl_seconds: int = Field(
        default=600,
        description="Cache TTL in seconds (default: 10 minutes).",
    )
    min_tokens_for_cache: int = Field(
        default=1024,
        description="Minimum tokens required to cache a prompt.",
    )

    # Content safety features
    enable_moderation: bool = Field(
        default=False,
        description="Enable content moderation API.",
    )
    moderation_threshold: float = Field(
        default=0.5,
        description="Threshold for content moderation (0.0-1.0).",
    )
    enable_refusals: bool = Field(
        default=False,
        description="Enable refusal responses for harmful content.",
    )
    enable_safety_features: bool = Field(
        default=False,
        description="Enable safety refusal mechanism for harmful content.",
    )
    enable_jailbreak_detection: bool = Field(
        default=False,
        description="Enable jailbreak/prompt injection detection.",
    )
    prepend_safety_message: bool = Field(
        default=False,
        description="Prepend safety guidelines as system message when no system message exists.",
    )

    # Audio features
    enable_audio: bool = Field(
        default=True,
        description="Enable audio input/output in chat completions.",
    )
    default_voice: str = Field(
        default="alloy",
        description="Default voice for audio output (alloy, echo, fable, onyx, nova, shimmer, etc.).",
    )
    default_audio_format: str = Field(
        default="mp3",
        description="Default audio format (mp3, opus, aac, flac, wav, pcm16).",
    )

    # Performance features
    enable_context_validation: bool = Field(
        default=True,
        description="Enable context window validation and warnings.",
    )
    strict_token_counting: bool = Field(
        default=False,
        description="Use strict token counting (slower but more accurate).",
    )

    # Streaming features
    stream_timeout_seconds: float = Field(
        default=300.0,
        description="Total timeout for streaming responses in seconds (default: 5 minutes).",
    )
    stream_token_timeout_seconds: float = Field(
        default=30.0,
        description="Timeout between individual tokens in streaming (default: 30 seconds).",
    )
    stream_keepalive_enabled: bool = Field(
        default=True,
        description="Enable keep-alive heartbeat for long streams.",
    )
    stream_keepalive_interval_seconds: float = Field(
        default=15.0,
        description="Interval between keep-alive heartbeats in seconds.",
    )

    @field_validator("cache_ttl_seconds")
    @classmethod
    def validate_cache_ttl(cls, v: int) -> int:
        """Validate cache TTL."""
        if v < 0:
            raise ValueError("Cache TTL cannot be negative")
        return v

    @field_validator("min_tokens_for_cache")
    @classmethod
    def validate_min_tokens_for_cache(cls, v: int) -> int:
        """Validate minimum tokens for cache."""
        if v < 0:
            raise ValueError("Minimum tokens for cache cannot be negative")
        return v

    @field_validator("moderation_threshold")
    @classmethod
    def validate_moderation_threshold(cls, v: float) -> float:
        """Validate moderation threshold."""
        if not 0.0 <= v <= 1.0:
            raise ValueError(
                "Moderation threshold must be between 0.0 and 1.0")
        return v

    @field_validator("default_voice")
    @classmethod
    def validate_default_voice(cls, v: str) -> str:
        """Validate default voice."""
        valid_voices = {
            "alloy",
            "ash",
            "ballad",
            "coral",
            "echo",
            "fable",
            "onyx",
            "nova",
            "shimmer",
            "sage",
            "verse",
        }
        if v not in valid_voices:
            raise ValueError(
                f"Default voice must be one of: {
                    ', '.join(
                        sorted(valid_voices))}")
        return v

    @field_validator("default_audio_format")
    @classmethod
    def validate_default_audio_format(cls, v: str) -> str:
        """Validate default audio format."""
        valid_formats = {"mp3", "opus", "aac", "flac", "wav", "pcm16"}
        if v not in valid_formats:
            raise ValueError(
                f"Default audio format must be one of: {
                    ', '.join(
                        sorted(valid_formats))}")
        return v

    @field_validator("stream_timeout_seconds")
    @classmethod
    def validate_stream_timeout(cls, v: float) -> float:
        """Validate stream timeout."""
        if v <= 0:
            raise ValueError("Stream timeout must be positive")
        return v

    @field_validator("stream_token_timeout_seconds")
    @classmethod
    def validate_stream_token_timeout(cls, v: float) -> float:
        """Validate stream token timeout."""
        if v <= 0:
            raise ValueError("Stream token timeout must be positive")
        return v

    @field_validator("stream_keepalive_interval_seconds")
    @classmethod
    def validate_keepalive_interval(cls, v: float) -> float:
        """Validate keep-alive interval."""
        if v <= 0:
            raise ValueError("Keep-alive interval must be positive")
        return v
