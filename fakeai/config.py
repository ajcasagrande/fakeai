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
        default_factory=lambda: [
            "sk-fakeai-1234567890abcdef",
            "sk-test-abcdefghijklmnop",
        ],
        description="List of valid API keys.",
    )
    require_api_key: bool = Field(
        default=True, description="Whether to require API key authentication."
    )
    rate_limit_enabled: bool = Field(default=True, description="Enable rate limiting.")
    requests_per_minute: int = Field(
        default=60, description="Maximum number of requests per minute per API key."
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
