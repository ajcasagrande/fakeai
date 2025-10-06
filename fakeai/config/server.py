"""
Server configuration module.

This module provides server-related configuration options.
"""

#  SPDX-License-Identifier: Apache-2.0

from enum import Enum

from pydantic import Field, field_validator

from .base import ModuleConfig


class LogLevel(str, Enum):
    """Valid log levels."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ServerConfig(ModuleConfig):
    """Server configuration settings."""

    host: str = Field(
        default="127.0.0.1",
        description="Host to bind the server to.",
    )
    port: int = Field(
        default=8000,
        description="Port to bind the server to.",
    )
    debug: bool = Field(
        default=False,
        description="Enable debug mode.",
    )
    workers: int = Field(
        default=1,
        description="Number of worker processes (uvicorn workers).",
    )
    reload: bool = Field(
        default=False,
        description="Enable auto-reload on code changes (development only).",
    )
    log_level: LogLevel = Field(
        default=LogLevel.INFO,
        description="Logging level (debug, info, warning, error, critical).",
    )

    @field_validator("port")
    @classmethod
    def validate_port(cls, v: int) -> int:
        """Validate port number."""
        if not 1 <= v <= 65535:
            raise ValueError("Port must be between 1 and 65535")
        return v

    @field_validator("workers")
    @classmethod
    def validate_workers(cls, v: int) -> int:
        """Validate number of workers."""
        if v < 1:
            raise ValueError("Number of workers must be at least 1")
        if v > 128:
            raise ValueError("Number of workers cannot exceed 128")
        return v

    @field_validator("log_level", mode="before")
    @classmethod
    def validate_log_level(cls, v: str | LogLevel) -> LogLevel:
        """Validate and convert log level."""
        if isinstance(v, LogLevel):
            return v
        if isinstance(v, str):
            try:
                return LogLevel(v.lower())
            except ValueError:
                valid = ", ".join([level.value for level in LogLevel])
                raise ValueError(f"Log level must be one of: {valid}")
        raise ValueError("Log level must be a string or LogLevel enum")
