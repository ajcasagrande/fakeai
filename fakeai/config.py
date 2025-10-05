"""
Configuration for the OpenAI simulated server.

This module provides configuration settings and options for the OpenAI simulated server.
"""
#  SPDX-License-Identifier: Apache-2.0

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class AppConfig(BaseSettings):
    """Application configuration settings."""

    # Server settings
    host: str = Field(default="127.0.0.1", description="Host to bind the server to.")
    port: int = Field(default=8000, description="Port to bind the server to.")
    debug: bool = Field(default=False, description="Enable debug mode.")

    # Simulated settings
    response_delay: float = Field(
        default=0.5, description="Base delay for responses in seconds."
    )
    random_delay: bool = Field(
        default=True, description="Add random variation to response delays."
    )
    max_variance: float = Field(
        default=0.3, description="Maximum variance for random delays (as a factor)."
    )

    # API settings
    api_keys: list[str] = Field(
        default_factory=list,
        description="List of valid API keys.",
    )
    require_api_key: bool = Field(
        default=False, description="Whether to require API key authentication."
    )
    rate_limit_enabled: bool = Field(default=False, description="Enable rate limiting.")
    rate_limit_tier: str = Field(
        default="tier-1",
        description="Rate limit tier (free, tier-1, tier-2, tier-3, tier-4, tier-5)."
    )
    rate_limit_rpm: int | None = Field(
        default=None,
        description="Custom requests per minute limit (overrides tier)."
    )
    rate_limit_tpm: int | None = Field(
        default=None,
        description="Custom tokens per minute limit (overrides tier)."
    )

    # Security settings (disabled by default for easy testing)
    enable_security: bool = Field(
        default=False, description="Master flag to enable all security features (overrides individual flags)."
    )
    hash_api_keys: bool = Field(
        default=False, description="Hash API keys for secure storage."
    )
    enable_input_validation: bool = Field(
        default=False, description="Enable input validation and sanitization."
    )
    enable_injection_detection: bool = Field(
        default=False, description="Enable injection attack detection."
    )
    enable_abuse_detection: bool = Field(
        default=False, description="Enable IP-based abuse detection and banning."
    )
    max_request_size: int = Field(
        default=100 * 1024 * 1024, description="Maximum request size in bytes (default: 100 MB)."
    )
    cors_allowed_origins: list[str] = Field(
        default_factory=lambda: ["*"],
        description="CORS allowed origins (use ['*'] for all or specific domains)."
    )
    cors_allow_credentials: bool = Field(
        default=True, description="Allow credentials in CORS requests."
    )
    abuse_cleanup_interval: int = Field(
        default=3600, description="Interval for cleaning up old abuse records (seconds)."
    )

    # Prompt caching settings
    enable_prompt_caching: bool = Field(
        default=True, description="Enable prompt caching simulation."
    )
    cache_ttl_seconds: int = Field(
        default=600, description="Cache TTL in seconds (default: 10 minutes)."
    )
    min_tokens_for_cache: int = Field(
        default=1024, description="Minimum tokens required to cache a prompt."
    )

    # KV Cache settings
    kv_cache_enabled: bool = Field(
        default=True, description="Enable KV cache simulation."
    )
    kv_cache_block_size: int = Field(
        default=16, description="Block size for KV cache (default: 16 tokens)."
    )
    kv_cache_num_workers: int = Field(
        default=4, description="Number of parallel workers for cache processing."
    )
    kv_overlap_weight: float = Field(
        default=1.0, description="Weight for overlap scoring in KV cache (0.0-2.0)."
    )

    # Safety settings (disabled by default for easy testing)
    enable_moderation: bool = Field(
        default=False, description="Enable content moderation API."
    )
    moderation_threshold: float = Field(
        default=0.5, description="Threshold for content moderation (0.0-1.0)."
    )
    enable_refusals: bool = Field(
        default=False, description="Enable refusal responses for harmful content."
    )
    enable_safety_features: bool = Field(
        default=False, description="Enable safety refusal mechanism for harmful content."
    )
    enable_jailbreak_detection: bool = Field(
        default=False, description="Enable jailbreak/prompt injection detection."
    )
    prepend_safety_message: bool = Field(
        default=False, description="Prepend safety guidelines as system message when no system message exists."
    )

    # Audio settings
    enable_audio: bool = Field(
        default=True, description="Enable audio input/output in chat completions."
    )
    default_voice: str = Field(
        default="alloy", description="Default voice for audio output (alloy, echo, fable, onyx, nova, shimmer, etc.)."
    )
    default_audio_format: str = Field(
        default="mp3", description="Default audio format (mp3, opus, aac, flac, wav, pcm16)."
    )

    # Performance settings
    enable_context_validation: bool = Field(
        default=True, description="Enable context window validation and warnings."
    )
    strict_token_counting: bool = Field(
        default=False, description="Use strict token counting (slower but more accurate)."
    )

    # Streaming settings
    stream_timeout_seconds: float = Field(
        default=300.0, description="Total timeout for streaming responses in seconds (default: 5 minutes)."
    )
    stream_token_timeout_seconds: float = Field(
        default=30.0, description="Timeout between individual tokens in streaming (default: 30 seconds)."
    )
    stream_keepalive_enabled: bool = Field(
        default=True, description="Enable keep-alive heartbeat for long streams."
    )
    stream_keepalive_interval_seconds: float = Field(
        default=15.0, description="Interval between keep-alive heartbeats in seconds."
    )

    # Latency simulation settings (TTFT and ITL)
    ttft_ms: float = Field(
        default=20.0,
        ge=0.0,
        description="Time to first token in milliseconds (default: 20ms)."
    )
    ttft_variance_percent: float = Field(
        default=10.0,
        ge=0.0,
        le=100.0,
        description="Variance/jitter for TTFT as percentage (default: 10%)."
    )
    itl_ms: float = Field(
        default=5.0,
        ge=0.0,
        description="Inter-token latency in milliseconds (default: 5ms)."
    )
    itl_variance_percent: float = Field(
        default=10.0,
        ge=0.0,
        le=100.0,
        description="Variance/jitter for ITL as percentage (default: 10%)."
    )

    class Config:
        """Pydantic config."""

        env_prefix = "FAKEAI_"
        case_sensitive = False

    @field_validator("port")
    def validate_port(cls, v: int) -> int:
        """Validate port number."""
        if not 1 <= v <= 65535:
            raise ValueError("Port must be between 1 and 65535")
        return v

    @field_validator("response_delay")
    def validate_response_delay(cls, v: float) -> float:
        """Validate response delay."""
        if v < 0:
            raise ValueError("Response delay cannot be negative")
        return v

    @field_validator("max_variance")
    def validate_max_variance(cls, v: float) -> float:
        """Validate max variance."""
        if v < 0:
            raise ValueError("Max variance cannot be negative")
        return v

    @field_validator("cache_ttl_seconds")
    def validate_cache_ttl(cls, v: int) -> int:
        """Validate cache TTL."""
        if v < 0:
            raise ValueError("Cache TTL cannot be negative")
        return v

    @field_validator("min_tokens_for_cache")
    def validate_min_tokens_for_cache(cls, v: int) -> int:
        """Validate minimum tokens for cache."""
        if v < 0:
            raise ValueError("Minimum tokens for cache cannot be negative")
        return v

    @field_validator("stream_timeout_seconds")
    def validate_stream_timeout(cls, v: float) -> float:
        """Validate stream timeout."""
        if v <= 0:
            raise ValueError("Stream timeout must be positive")
        return v

    @field_validator("stream_token_timeout_seconds")
    def validate_stream_token_timeout(cls, v: float) -> float:
        """Validate stream token timeout."""
        if v <= 0:
            raise ValueError("Stream token timeout must be positive")
        return v

    @field_validator("stream_keepalive_interval_seconds")
    def validate_keepalive_interval(cls, v: float) -> float:
        """Validate keep-alive interval."""
        if v <= 0:
            raise ValueError("Keep-alive interval must be positive")
        return v

    @field_validator("kv_cache_block_size")
    def validate_kv_cache_block_size(cls, v: int) -> int:
        """Validate KV cache block size."""
        if v < 1:
            raise ValueError("KV cache block size must be at least 1")
        if v > 128:
            raise ValueError("KV cache block size cannot exceed 128")
        return v

    @field_validator("kv_cache_num_workers")
    def validate_kv_cache_num_workers(cls, v: int) -> int:
        """Validate KV cache number of workers."""
        if v < 1:
            raise ValueError("KV cache number of workers must be at least 1")
        if v > 64:
            raise ValueError("KV cache number of workers cannot exceed 64")
        return v

    @field_validator("kv_overlap_weight")
    def validate_kv_overlap_weight(cls, v: float) -> float:
        """Validate KV overlap weight."""
        if not 0.0 <= v <= 2.0:
            raise ValueError("KV overlap weight must be between 0.0 and 2.0")
        return v

    @field_validator("moderation_threshold")
    def validate_moderation_threshold(cls, v: float) -> float:
        """Validate moderation threshold."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("Moderation threshold must be between 0.0 and 1.0")
        return v

    @field_validator("default_voice")
    def validate_default_voice(cls, v: str) -> str:
        """Validate default voice."""
        valid_voices = {
            "alloy", "ash", "ballad", "coral", "echo", "fable",
            "onyx", "nova", "shimmer", "sage", "verse"
        }
        if v not in valid_voices:
            raise ValueError(f"Default voice must be one of: {', '.join(sorted(valid_voices))}")
        return v

    @field_validator("default_audio_format")
    def validate_default_audio_format(cls, v: str) -> str:
        """Validate default audio format."""
        valid_formats = {"mp3", "opus", "aac", "flac", "wav", "pcm16"}
        if v not in valid_formats:
            raise ValueError(f"Default audio format must be one of: {', '.join(sorted(valid_formats))}")
        return v

    @field_validator("max_request_size")
    def validate_max_request_size(cls, v: int) -> int:
        """Validate maximum request size."""
        if v < 1024:  # At least 1 KB
            raise ValueError("Maximum request size must be at least 1024 bytes")
        if v > 100 * 1024 * 1024:  # At most 100 MB
            raise ValueError("Maximum request size cannot exceed 100 MB")
        return v

    @field_validator("abuse_cleanup_interval")
    def validate_abuse_cleanup_interval(cls, v: int) -> int:
        """Validate abuse cleanup interval."""
        if v < 60:  # At least 1 minute
            raise ValueError("Abuse cleanup interval must be at least 60 seconds")
        return v

    @field_validator("cors_allowed_origins")
    def validate_cors_origins(cls, v: list[str]) -> list[str]:
        """Validate CORS allowed origins."""
        if not v:
            raise ValueError("CORS allowed origins cannot be empty")
        return v

    # Properties to check security flags with master override
    def is_input_validation_enabled(self) -> bool:
        """Check if input validation is enabled (respects master security flag)."""
        return self.enable_security or self.enable_input_validation

    def is_injection_detection_enabled(self) -> bool:
        """Check if injection detection is enabled (respects master security flag)."""
        return self.enable_security or self.enable_injection_detection

    def is_abuse_detection_enabled(self) -> bool:
        """Check if abuse detection is enabled (respects master security flag)."""
        return self.enable_security or self.enable_abuse_detection

    def is_moderation_enabled(self) -> bool:
        """Check if content moderation is enabled (respects master security flag)."""
        return self.enable_security or self.enable_moderation

    def is_refusals_enabled(self) -> bool:
        """Check if refusals are enabled (respects master security flag)."""
        return self.enable_security or self.enable_refusals

    def is_safety_features_enabled(self) -> bool:
        """Check if safety features are enabled (respects master security flag)."""
        return self.enable_security or self.enable_safety_features

    def is_jailbreak_detection_enabled(self) -> bool:
        """Check if jailbreak detection is enabled (respects master security flag)."""
        return self.enable_security or self.enable_jailbreak_detection

    def is_api_key_hashing_enabled(self) -> bool:
        """Check if API key hashing is enabled (respects master security flag)."""
        return self.enable_security or self.hash_api_keys
