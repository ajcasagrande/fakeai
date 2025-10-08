"""
Stop sequences validator.

Validates stop sequence parameters.
"""

#  SPDX-License-Identifier: Apache-2.0

from typing import Any

from fakeai.validation.base import ValidationResult


class StopSequencesValidator:
    """
    Validator that checks stop sequence parameters.

    Validates the 'stop' parameter which can be a string or array of strings.
    """

    MAX_STOP_SEQUENCES = 4
    MAX_STOP_LENGTH = 100

    def __init__(self, name: str = "StopSequencesValidator"):
        """
        Initialize the stop sequences validator.

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
        Validate stop sequence parameters.

        Args:
            request: Request object with stop parameter
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

        # Validate stop parameter
        if "stop" in params and params["stop"] is not None:
            stop = params["stop"]

            # Can be string or list of strings
            if isinstance(stop, str):
                # Validate single stop sequence
                if not stop:
                    result.add_error(
                        message="stop sequence cannot be empty",
                        code="invalid_value",
                        param="stop",
                    )
                elif len(stop) > self.MAX_STOP_LENGTH:
                    result.add_error(
                        message=f"stop sequence cannot be longer than {
                            self.MAX_STOP_LENGTH} characters",
                        code="invalid_value",
                        param="stop",
                    )
            elif isinstance(stop, list):
                # Validate list of stop sequences
                if not stop:
                    result.add_error(
                        message="stop array cannot be empty",
                        code="invalid_value",
                        param="stop",
                    )
                elif len(stop) > self.MAX_STOP_SEQUENCES:
                    result.add_error(
                        message=f"stop array cannot have more than {
                            self.MAX_STOP_SEQUENCES} sequences",
                        code="invalid_value",
                        param="stop",
                    )
                else:
                    # Validate each stop sequence
                    for i, seq in enumerate(stop):
                        if not isinstance(seq, str):
                            result.add_error(
                                message=f"stop[{i}] must be a string",
                                code="invalid_type",
                                param=f"stop[{i}]",
                            )
                        elif not seq:
                            result.add_error(
                                message=f"stop[{i}] cannot be empty",
                                code="invalid_value",
                                param=f"stop[{i}]",
                            )
                        elif len(seq) > self.MAX_STOP_LENGTH:
                            result.add_error(
                                message=f"stop[{i}] cannot be longer than {
                                    self.MAX_STOP_LENGTH} characters",
                                code="invalid_value",
                                param=f"stop[{i}]",
                            )

                    # Check for duplicates
                    if len(stop) != len(set(stop)):
                        result.add_warning(
                            message="stop array contains duplicate sequences",
                            code="duplicate_stop_sequences",
                            param="stop",
                        )
            else:
                result.add_error(
                    message="stop must be a string or array of strings",
                    code="invalid_type",
                    param="stop",
                )

        return result
