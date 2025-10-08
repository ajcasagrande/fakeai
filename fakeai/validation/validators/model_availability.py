"""
Model availability validator.

Validates that requested models exist and are available.
"""

#  SPDX-License-Identifier: Apache-2.0

import re
from typing import Any

from fakeai.validation.base import ValidationResult


class ModelAvailabilityValidator:
    """
    Validator that checks model availability.

    Validates that requested models exist and are available for use.
    In FakeAI, models are auto-created, so this mainly validates format.
    """

    def __init__(
        self,
        available_models: set[str] | None = None,
        allow_auto_create: bool = True,
        name: str = "ModelAvailabilityValidator",
    ):
        """
        Initialize the model availability validator.

        Args:
            available_models: Set of available model IDs (None means all allowed)
            allow_auto_create: If True, allow any model ID (FakeAI auto-creates)
            name: Name for this validator
        """
        self._available_models = available_models
        self._allow_auto_create = allow_auto_create
        self._name = name

    @property
    def name(self) -> str:
        """Get the name of this validator."""
        return self._name

    def _is_valid_model_format(self, model: str) -> tuple[bool, str]:
        """
        Check if model ID has valid format.

        Args:
            model: Model ID to check

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not model:
            return False, "Model ID cannot be empty"

        if not isinstance(model, str):
            return False, "Model ID must be a string"

        # Check for extremely long model IDs (possible abuse)
        if len(model) > 500:
            return False, f"Model ID is too long ({len(model)} characters)"

        # Check for fine-tuned models (format: ft:base:org::id or
        # ft:base:org:id)
        if model.startswith("ft:"):
            parts = model.split(":")
            # Fine-tuned models should have at least ft:base format (2 parts minimum)
            # Full format is ft:base:org::id (5 parts with empty slot before id)
            # or ft:base:org:id (4 parts)
            if len(parts) < 2:
                return False, "Invalid fine-tuned model format. Expected: ft:base_model or ft:base:org:id"

            # Validate that base model is not empty
            if len(parts) >= 2 and not parts[1]:
                return False, "Fine-tuned model must specify a base model"

            # If organization is specified, validate it's a reasonable format
            if len(parts) >= 3 and parts[2]:
                # Check org name contains valid characters
                if not re.match(r"^[a-zA-Z0-9\-_]+$", parts[2]):
                    return False, "Fine-tuned model organization contains invalid characters"

        # Check for invalid characters (very permissive)
        # Allow alphanumeric, hyphens, underscores, slashes, colons, dots
        if not re.match(r"^[a-zA-Z0-9\-_/:.]+$", model):
            return False, "Model ID contains invalid characters"

        return True, ""

    def validate(
        self, request: Any, context: dict[str, Any] | None = None
    ) -> ValidationResult:
        """
        Validate model availability.

        Expected context keys:
            - model: Model ID (optional, can also come from request)

        Args:
            request: The request object
            context: Context containing model information

        Returns:
            ValidationResult indicating success or failure
        """
        context = context or {}

        # Get model ID from context or request
        model = context.get("model")
        if not model and hasattr(request, "model"):
            model = request.model

        if not model:
            return ValidationResult.failure(
                message="Model is required",
                code="missing_model",
                param="model",
            )

        # Validate model format
        is_valid, error_msg = self._is_valid_model_format(model)
        if not is_valid:
            return ValidationResult.failure(
                message=error_msg,
                code="invalid_model_format",
                param="model",
            )

        # If we have a specific list of available models, check it
        if not self._allow_auto_create and self._available_models is not None:
            # For fine-tuned models, check the base model
            model_to_check = model
            if model.startswith("ft:"):
                parts = model.split(":")
                if len(parts) >= 2:
                    model_to_check = parts[1]

            # Check both the full model ID and just the base name
            base_model = model_to_check.split(
                "/")[-1] if "/" in model_to_check else model_to_check

            if (
                model not in self._available_models and
                model_to_check not in self._available_models and
                base_model not in self._available_models
            ):
                return ValidationResult.failure(
                    message=f"Model '{model}' is not available",
                    code="model_not_found",
                    param="model",
                )

        # Model is valid
        return ValidationResult.success(
            metadata={
                "model": model,
                "is_fine_tuned": model.startswith("ft:"),
            }
        )
