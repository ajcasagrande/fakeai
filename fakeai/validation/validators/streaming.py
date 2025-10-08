"""
Streaming validator.

Validates streaming-related parameters.
"""

#  SPDX-License-Identifier: Apache-2.0

from typing import Any

from fakeai.validation.base import ValidationResult


class StreamingValidator:
    """
    Validator that checks streaming parameters.

    Validates the 'stream' parameter and ensures it's used correctly
    with other parameters.
    """

    def __init__(self, name: str = "StreamingValidator"):
        """
        Initialize the streaming validator.

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
        Validate streaming parameters.

        Args:
            request: Request object with streaming parameters
            context: Optional context information

        Returns:
            ValidationResult indicating success or failure
        """
        result = ValidationResult.success()

        # Handle both dict and Pydantic models
        if hasattr(request, "model_dump"):
            params = request.model_dump()
        elif isinstance(request, dict):
            params = request
        else:
            return ValidationResult.failure(
                message="Request must be a dict or Pydantic model",
                code="invalid_request_type",
            )

        # Validate stream parameter
        if "stream" in params and params["stream"] is not None:
            stream = params["stream"]
            if not isinstance(stream, bool):
                result.add_error(
                    message="stream must be a boolean",
                    code="invalid_type",
                    param="stream",
                )

        # Validate stream_options (for SSE usage tracking)
        if "stream_options" in params and params["stream_options"] is not None:
            stream_options = params["stream_options"]

            # stream_options only makes sense with stream=True
            if not params.get("stream", False):
                result.add_warning(
                    message="stream_options is only used when stream=true",
                    code="unused_parameter",
                    param="stream_options",
                )

            # Validate structure
            if not isinstance(stream_options, dict):
                result.add_error(
                    message="stream_options must be an object",
                    code="invalid_type",
                    param="stream_options",
                )
            else:
                # Check for include_usage field
                if "include_usage" in stream_options:
                    include_usage = stream_options["include_usage"]
                    if not isinstance(include_usage, bool):
                        result.add_error(
                            message="stream_options.include_usage must be a boolean",
                            code="invalid_type",
                            param="stream_options.include_usage",
                        )

        return result
