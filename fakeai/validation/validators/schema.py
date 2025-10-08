"""
Schema validator using Pydantic.

Validates that requests conform to expected Pydantic models.
"""

#  SPDX-License-Identifier: Apache-2.0

from typing import Any, Type

from pydantic import BaseModel
from pydantic import ValidationError as PydanticValidationError

from fakeai.validation.base import ValidationResult


class SchemaValidator:
    """
    Validator that checks request data against a Pydantic schema.

    This validator ensures that incoming requests conform to the expected
    structure and data types defined by Pydantic models.
    """

    def __init__(self, schema: Type[BaseModel], name: str | None = None):
        """
        Initialize the schema validator.

        Args:
            schema: Pydantic model class to validate against
            name: Optional custom name for this validator
        """
        self._schema = schema
        self._name = name or f"SchemaValidator({schema.__name__})"

    @property
    def name(self) -> str:
        """Get the name of this validator."""
        return self._name

    def validate(
        self, request: Any, context: dict[str, Any] | None = None
    ) -> ValidationResult:
        """
        Validate request data against the Pydantic schema.

        Args:
            request: Request data to validate (dict or Pydantic model)
            context: Optional context information (unused)

        Returns:
            ValidationResult indicating success or failure
        """
        # If request is already a validated Pydantic model of the correct type,
        # it's valid
        if isinstance(request, self._schema):
            return ValidationResult.success(
                metadata={
                    "schema": self._schema.__name__,
                    "validated_model": request})

        # Convert to dict if it's a Pydantic model of a different type
        if isinstance(request, BaseModel):
            request_data = request.model_dump()
        else:
            request_data = request

        try:
            # Validate using Pydantic
            validated_model = self._schema.model_validate(request_data)

            return ValidationResult.success(
                metadata={
                    "schema": self._schema.__name__,
                    "validated_model": validated_model,
                }
            )

        except PydanticValidationError as e:
            result = ValidationResult(valid=False)

            # Convert Pydantic errors to our validation errors
            for error in e.errors():
                # Build field path
                field_path = ".".join(str(loc) for loc in error["loc"])

                # Get error message
                message = error["msg"]

                # Add error to result
                result.add_error(
                    message=f"{field_path}: {message}",
                    code="invalid_value",
                    param=field_path,
                )

            result.metadata["schema"] = self._schema.__name__
            result.metadata["pydantic_errors"] = e.errors()

            return result

        except Exception as e:
            return ValidationResult.failure(
                message=f"Schema validation failed: {e}",
                code="schema_validation_error",
                metadata={"schema": self._schema.__name__},
            )
