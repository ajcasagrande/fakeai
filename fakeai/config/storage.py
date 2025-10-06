"""
Storage configuration module.

This module provides storage backend configuration options.
"""

#  SPDX-License-Identifier: Apache-2.0

from enum import Enum

from pydantic import Field, field_validator

from .base import ModuleConfig


class StorageBackend(str, Enum):
    """Valid storage backends."""

    MEMORY = "memory"
    DISK = "disk"


class StorageConfig(ModuleConfig):
    """Storage configuration settings."""

    # File storage
    file_storage_backend: StorageBackend = Field(
        default=StorageBackend.MEMORY,
        description="File storage backend (memory or disk).",
    )
    file_storage_path: str | None = Field(
        default=None,
        description="Path for disk-based file storage (only used when backend is 'disk').",
    )
    file_cleanup_enabled: bool = Field(
        default=True,
        description="Enable automatic cleanup of expired files.",
    )
    file_retention_hours: int = Field(
        default=24,
        description="Hours to retain uploaded files before cleanup.",
    )

    # Image storage
    image_storage_backend: StorageBackend = Field(
        default=StorageBackend.MEMORY,
        description="Image storage backend (memory or disk).",
    )
    image_storage_path: str | None = Field(
        default=None,
        description="Path for disk-based image storage (only used when backend is 'disk').",
    )
    image_retention_hours: int = Field(
        default=1,
        description="Hours to retain generated images before cleanup.",
    )

    @field_validator("file_storage_backend", "image_storage_backend", mode="before")
    @classmethod
    def validate_storage_backend(cls, v: str | StorageBackend) -> StorageBackend:
        """Validate and convert storage backend."""
        if isinstance(v, StorageBackend):
            return v
        if isinstance(v, str):
            try:
                return StorageBackend(v.lower())
            except ValueError:
                valid = ", ".join([backend.value for backend in StorageBackend])
                raise ValueError(f"Storage backend must be one of: {valid}")
        raise ValueError("Storage backend must be a string or StorageBackend enum")

    @field_validator("file_retention_hours")
    @classmethod
    def validate_file_retention_hours(cls, v: int) -> int:
        """Validate file retention hours."""
        if v < 0:
            raise ValueError("File retention hours cannot be negative")
        if v > 168:  # 1 week max
            raise ValueError("File retention hours cannot exceed 168 (1 week)")
        return v

    @field_validator("image_retention_hours")
    @classmethod
    def validate_image_retention_hours(cls, v: int) -> int:
        """Validate image retention hours."""
        if v < 0:
            raise ValueError("Image retention hours cannot be negative")
        if v > 168:  # 1 week max
            raise ValueError("Image retention hours cannot exceed 168 (1 week)")
        return v
