"""
Response format validator.

Validates response_format parameters for structured outputs.
"""

#  SPDX-License-Identifier: Apache-2.0

from typing import Any

from fakeai.validation.base import ValidationResult


class ResponseFormatValidator:
    """
    Validator that checks response_format parameters.

    Validates structured output requests including JSON mode and JSON schema.
    """

    VALID_TYPES = {"text", "json_object", "json_schema"}

    def __init__(self, name: str = "ResponseFormatValidator"):
        """
        Initialize the response format validator.

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
        Validate response format parameters.

        Args:
            request: Request object with response_format parameter
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

        # Validate response_format parameter
        if "response_format" in params and params["response_format"] is not None:
            response_format = params["response_format"]

            # Must be a dict/object
            if not isinstance(response_format, dict):
                result.add_error(
                    message="response_format must be an object",
                    code="invalid_type",
                    param="response_format",
                )
                return result

            # Validate type field
            if "type" not in response_format:
                result.add_error(
                    message="response_format must include a 'type' field",
                    code="missing_field",
                    param="response_format.type",
                )
            else:
                fmt_type = response_format["type"]
                if not isinstance(fmt_type, str):
                    result.add_error(
                        message="response_format.type must be a string",
                        code="invalid_type",
                        param="response_format.type",
                    )
                elif fmt_type not in self.VALID_TYPES:
                    result.add_error(
                        message=f"response_format.type must be one of: {
                            ', '.join(
                                self.VALID_TYPES)}",
                        code="invalid_value",
                        param="response_format.type",
                    )

                # Validate json_schema format
                if fmt_type == "json_schema":
                    if "json_schema" not in response_format:
                        result.add_error(
                            message="response_format.json_schema is required when type is 'json_schema'",
                            code="missing_field",
                            param="response_format.json_schema",
                        )
                    else:
                        json_schema = response_format["json_schema"]
                        if not isinstance(json_schema, dict):
                            result.add_error(
                                message="response_format.json_schema must be an object",
                                code="invalid_type",
                                param="response_format.json_schema",
                            )
                        else:
                            # Validate required fields in json_schema
                            if "name" not in json_schema:
                                result.add_error(
                                    message="response_format.json_schema.name is required",
                                    code="missing_field",
                                    param="response_format.json_schema.name",
                                )
                            elif not isinstance(json_schema["name"], str):
                                result.add_error(
                                    message="response_format.json_schema.name must be a string",
                                    code="invalid_type",
                                    param="response_format.json_schema.name",
                                )

                            if "schema" not in json_schema:
                                result.add_error(
                                    message="response_format.json_schema.schema is required",
                                    code="missing_field",
                                    param="response_format.json_schema.schema",
                                )
                            elif not isinstance(json_schema["schema"], dict):
                                result.add_error(
                                    message="response_format.json_schema.schema must be an object",
                                    code="invalid_type",
                                    param="response_format.json_schema.schema",
                                )

                            # Check for strict mode
                            if "strict" in json_schema:
                                strict = json_schema["strict"]
                                if not isinstance(strict, bool):
                                    result.add_error(
                                        message="response_format.json_schema.strict must be a boolean",
                                        code="invalid_type",
                                        param="response_format.json_schema.strict",
                                    )

                # Warn about json_object usage
                if fmt_type == "json_object":
                    result.add_warning(
                        message="Using json_object requires including 'JSON' in the prompt",
                        code="json_object_usage",
                        param="response_format",
                    )

        return result
