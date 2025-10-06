"""
Base configuration classes for FakeAI.

This module provides common configuration patterns and utilities.
"""

#  SPDX-License-Identifier: Apache-2.0

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseConfig(BaseModel):
    """Base configuration class with common patterns."""

    model_config = SettingsConfigDict(
        env_prefix="FAKEAI_",
        case_sensitive=False,
        extra="forbid",  # Catch typos in config
    )


class ModuleConfig(BaseConfig):
    """Base class for modular configuration sections."""

    pass
