"""
Context length validator.

Validates that requests don't exceed model context window limits.
Uses the existing context_validator module.
"""

#  SPDX-License-Identifier: Apache-2.0

from typing import Any

from fakeai.context_validator import validate_context_length
from fakeai.validation.base import ValidationResult


class ContextLengthValidator:
    """
    Validator that checks context length limits.

    Ensures that prompt tokens + max_tokens doesn't exceed the model's
    context window, including multi-modal content (images, audio, video).
    """

    def __init__(self, name: str = "ContextLengthValidator"):
        """
        Initialize the context length validator.

        Args:
            name: Name for this validator
        """
        self._name = name

    @property
    def name(self) -> str:
        """Get the name of this validator."""
        return self._name

    def validate(
        self, request: Any, context: dict[str, Any] | None = None
    ) -> ValidationResult:
        """
        Validate context length for a request.

        Expected context keys:
            - model: Model ID (required)
            - prompt_tokens: Number of text tokens in prompt (required)
            - max_tokens: Maximum tokens to generate (optional)
            - image_tokens: Number of tokens from images (optional, default 0)
            - audio_tokens: Number of tokens from audio (optional, default 0)
            - video_tokens: Number of tokens from video (optional, default 0)

        Args:
            request: The request object (not used directly, uses context)
            context: Context containing token counts and model info

        Returns:
            ValidationResult indicating success or failure
        """
        context = context or {}

        # Extract required fields
        model = context.get("model")
        prompt_tokens = context.get("prompt_tokens")

        # Validate required fields
        if not model:
            return ValidationResult.failure(
                message="Model is required for context length validation",
                code="missing_model",
            )

        if prompt_tokens is None:
            return ValidationResult.failure(
                message="prompt_tokens is required for context length validation",
                code="missing_prompt_tokens",
            )

        # Extract optional fields
        max_tokens = context.get("max_tokens")
        image_tokens = context.get("image_tokens", 0)
        audio_tokens = context.get("audio_tokens", 0)
        video_tokens = context.get("video_tokens", 0)

        # Validate context length
        is_valid, error_message = validate_context_length(
            model=model,
            prompt_tokens=prompt_tokens,
            max_tokens=max_tokens,
            image_tokens=image_tokens,
            audio_tokens=audio_tokens,
            video_tokens=video_tokens,
        )

        if is_valid:
            total_tokens = (
                prompt_tokens + image_tokens + audio_tokens + video_tokens
            )
            return ValidationResult.success(
                metadata={
                    "model": model,
                    "total_input_tokens": total_tokens,
                    "max_tokens": max_tokens,
                }
            )
        else:
            return ValidationResult.failure(
                message=error_message,
                code="context_length_exceeded",
                param="messages",
                metadata={
                    "model": model,
                    "prompt_tokens": prompt_tokens,
                    "max_tokens": max_tokens,
                },
            )
