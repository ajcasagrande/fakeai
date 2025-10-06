"""
Multi-modal content validator.

Validates multi-modal content (images, audio, video) in requests.
"""

#  SPDX-License-Identifier: Apache-2.0

from typing import Any

from fakeai.validation.base import ValidationResult


class MultiModalValidator:
    """
    Validator that checks multi-modal content.

    Validates that models support the requested modalities (vision, audio, video)
    and that multi-modal content is properly formatted.
    """

    # Models that support vision
    VISION_MODELS = {
        "gpt-4-vision-preview",
        "gpt-4-turbo",
        "gpt-4o",
        "gpt-4o-mini",
        "claude-3-opus",
        "claude-3-sonnet",
        "claude-3-haiku",
        "gemini-pro-vision",
    }

    # Models that support audio
    AUDIO_MODELS = {
        "whisper-1",
        "gpt-4-audio-preview",
    }

    # Models that support video (NVIDIA Cosmos extension)
    VIDEO_MODELS = {
        "nvidia/cosmos-vision-1",
        "gpt-4-video-preview",
    }

    def __init__(self, name: str = "MultiModalValidator"):
        """
        Initialize the multi-modal validator.

        Args:
            name: Name for this validator
        """
        self._name = name

    @property
    def name(self) -> str:
        """Get the name of this validator."""
        return self._name

    def _check_model_supports_modality(
        self, model: str, modality: str
    ) -> tuple[bool, str]:
        """
        Check if a model supports a specific modality.

        Args:
            model: Model ID
            modality: Modality type (vision, audio, video)

        Returns:
            Tuple of (supported, error_message)
        """
        # Extract base model name for checking
        base_model = model.split("/")[-1] if "/" in model else model

        # Check for fine-tuned models (format: ft:base:org::id)
        if model.startswith("ft:"):
            parts = model.split(":")
            if len(parts) >= 2:
                base_model = parts[1].split("/")[-1]

        if modality == "vision":
            supported = any(vm in base_model for vm in self.VISION_MODELS)
            if not supported:
                return False, f"Model '{model}' does not support vision/image inputs"

        elif modality == "audio":
            supported = any(am in base_model for am in self.AUDIO_MODELS)
            if not supported:
                return False, f"Model '{model}' does not support audio inputs"

        elif modality == "video":
            supported = any(vm in base_model for vm in self.VIDEO_MODELS)
            if not supported:
                return False, f"Model '{model}' does not support video inputs"

        else:
            return False, f"Unknown modality: {modality}"

        return True, ""

    def _extract_content_types(self, messages: list) -> set[str]:
        """
        Extract content types from messages.

        Args:
            messages: List of message objects

        Returns:
            Set of content types found (text, image_url, audio, video_url, etc.)
        """
        content_types = set()

        for msg in messages:
            # Get content
            content = None
            if isinstance(msg, dict):
                content = msg.get("content")
            elif hasattr(msg, "content"):
                content = msg.content

            if not content:
                continue

            # String content is text
            if isinstance(content, str):
                content_types.add("text")
                continue

            # List content can have multiple types
            if isinstance(content, list):
                for part in content:
                    part_type = None
                    if isinstance(part, dict):
                        part_type = part.get("type")
                    elif hasattr(part, "type"):
                        part_type = part.type

                    if part_type:
                        content_types.add(part_type)

        return content_types

    def validate(
        self, request: Any, context: dict[str, Any] | None = None
    ) -> ValidationResult:
        """
        Validate multi-modal content.

        Expected context keys:
            - model: Model ID (required)
            - messages: List of messages (optional)

        Args:
            request: The request object
            context: Context containing model and messages

        Returns:
            ValidationResult indicating success or failure
        """
        result = ValidationResult.success()
        context = context or {}

        # Get model
        model = context.get("model")
        if not model and hasattr(request, "model"):
            model = request.model

        if not model:
            return ValidationResult.failure(
                message="Model is required for multi-modal validation",
                code="missing_model",
            )

        # Get messages
        messages = context.get("messages")
        if not messages and hasattr(request, "messages"):
            messages = request.messages

        if not messages:
            # No messages to validate - this is fine
            return result

        # Extract content types from messages
        content_types = self._extract_content_types(messages)

        # Check if model supports each modality
        if "image_url" in content_types:
            supported, error_msg = self._check_model_supports_modality(model, "vision")
            if not supported:
                result.add_error(
                    message=error_msg,
                    code="unsupported_modality",
                    param="messages",
                )

        if "input_audio" in content_types or "audio_url" in content_types:
            supported, error_msg = self._check_model_supports_modality(model, "audio")
            if not supported:
                result.add_error(
                    message=error_msg,
                    code="unsupported_modality",
                    param="messages",
                )

        if "video_url" in content_types:
            supported, error_msg = self._check_model_supports_modality(model, "video")
            if not supported:
                result.add_error(
                    message=error_msg,
                    code="unsupported_modality",
                    param="messages",
                )

        # Add metadata about content types found
        result.metadata["content_types"] = list(content_types)
        result.metadata["is_multimodal"] = len(content_types) > 1

        return result
