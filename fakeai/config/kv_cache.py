"""
KV cache configuration module.

This module provides KV cache and smart routing configuration options.
"""

#  SPDX-License-Identifier: Apache-2.0

from pydantic import Field, field_validator

from .base import ModuleConfig


class KVCacheConfig(ModuleConfig):
    """KV cache configuration settings."""

    enabled: bool = Field(
        default=True,
        description="Enable KV cache simulation.",
    )
    block_size: int = Field(
        default=16,
        description="Block size for KV cache (default: 16 tokens).",
    )
    num_workers: int = Field(
        default=4,
        description="Number of parallel workers for cache processing.",
    )
    overlap_weight: float = Field(
        default=1.0,
        description="Weight for overlap scoring in KV cache (0.0-2.0).",
    )
    load_balance_weight: float = Field(
        default=0.5,
        description="Weight for load balancing in smart routing (0.0-2.0).",
    )

    @field_validator("block_size")
    @classmethod
    def validate_block_size(cls, v: int) -> int:
        """Validate KV cache block size."""
        if v < 1:
            raise ValueError("KV cache block size must be at least 1")
        if v > 128:
            raise ValueError("KV cache block size cannot exceed 128")
        return v

    @field_validator("num_workers")
    @classmethod
    def validate_num_workers(cls, v: int) -> int:
        """Validate KV cache number of workers."""
        if v < 1:
            raise ValueError("KV cache number of workers must be at least 1")
        if v > 64:
            raise ValueError("KV cache number of workers cannot exceed 64")
        return v

    @field_validator("overlap_weight")
    @classmethod
    def validate_overlap_weight(cls, v: float) -> float:
        """Validate KV overlap weight."""
        if not 0.0 <= v <= 2.0:
            raise ValueError("KV overlap weight must be between 0.0 and 2.0")
        return v

    @field_validator("load_balance_weight")
    @classmethod
    def validate_load_balance_weight(cls, v: float) -> float:
        """Validate load balance weight."""
        if not 0.0 <= v <= 2.0:
            raise ValueError("Load balance weight must be between 0.0 and 2.0")
        return v
