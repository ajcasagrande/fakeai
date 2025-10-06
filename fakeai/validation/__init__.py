"""
Validation pipeline framework for FakeAI.

This module provides a comprehensive, composable validation system for validating
API requests through a pipeline of validators.
"""

#  SPDX-License-Identifier: Apache-2.0

from fakeai.validation.base import (
    AsyncValidator,
    ValidationError,
    ValidationResult,
    ValidationSeverity,
    ValidationWarning,
    Validator,
)
from fakeai.validation.factory import (
    create_audio_validators,
    create_batch_validators,
    create_chat_validators,
    create_completion_validators,
    create_embedding_validators,
    create_image_validators,
    create_moderation_validators,
    create_validators_for_endpoint,
)
from fakeai.validation.pipeline import ValidationPipeline

__all__ = [
    # Base classes
    "Validator",
    "AsyncValidator",
    "ValidationResult",
    "ValidationError",
    "ValidationWarning",
    "ValidationSeverity",
    # Pipeline
    "ValidationPipeline",
    # Factory functions
    "create_validators_for_endpoint",
    "create_chat_validators",
    "create_completion_validators",
    "create_embedding_validators",
    "create_image_validators",
    "create_audio_validators",
    "create_moderation_validators",
    "create_batch_validators",
]
