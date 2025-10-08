"""
Base classes and protocols for the validation framework.

This module defines the core abstractions used throughout the validation system,
including validators, validation results, and error/warning types.
"""

#  SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol, runtime_checkable


class ValidationSeverity(str, Enum):
    """Severity level for validation issues."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationResult:
    """
    Result of a validation operation.

    A validation result can be either successful or contain errors/warnings.
    Multiple errors and warnings can be accumulated during validation.
    """

    valid: bool
    errors: list["ValidationError"] = field(default_factory=list)
    warnings: list["ValidationWarning"] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_error(
        self,
        message: str,
        code: str | None = None,
        param: str | None = None,
        severity: ValidationSeverity = ValidationSeverity.ERROR,
    ) -> None:
        """
        Add an error to this validation result.

        Args:
            message: Human-readable error message
            code: Machine-readable error code
            param: Parameter that caused the error
            severity: Severity level of the error
        """
        self.errors.append(
            ValidationError(
                message=message, code=code, param=param, severity=severity
            )
        )
        self.valid = False

    def add_warning(
        self,
        message: str,
        code: str | None = None,
        param: str | None = None,
    ) -> None:
        """
        Add a warning to this validation result.

        Args:
            message: Human-readable warning message
            code: Machine-readable warning code
            param: Parameter that caused the warning
        """
        self.warnings.append(
            ValidationWarning(message=message, code=code, param=param)
        )

    def merge(self, other: "ValidationResult") -> None:
        """
        Merge another validation result into this one.

        Args:
            other: Another validation result to merge
        """
        self.valid = self.valid and other.valid
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
        self.metadata.update(other.metadata)

    @classmethod
    def success(cls, metadata: dict[str, Any] |
                None = None) -> "ValidationResult":
        """
        Create a successful validation result.

        Args:
            metadata: Optional metadata to attach

        Returns:
            A successful validation result
        """
        return cls(valid=True, metadata=metadata or {})

    @classmethod
    def failure(
        cls,
        message: str,
        code: str | None = None,
        param: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> "ValidationResult":
        """
        Create a failed validation result with a single error.

        Args:
            message: Error message
            code: Error code
            param: Parameter that caused the error
            metadata: Optional metadata to attach

        Returns:
            A failed validation result
        """
        result = cls(valid=False, metadata=metadata or {})
        result.add_error(message=message, code=code, param=param)
        return result

    def to_error_response(self) -> dict[str, Any]:
        """
        Convert validation errors to OpenAI-compatible error response.

        Returns:
            Dictionary with error information
        """
        if not self.errors:
            return {}

        # Use the first error for the main response
        first_error = self.errors[0]

        error_dict = {
            "error": {
                "message": first_error.message,
                "type": "invalid_request_error",
            }
        }

        if first_error.code:
            error_dict["error"]["code"] = first_error.code

        if first_error.param:
            error_dict["error"]["param"] = first_error.param

        # Include additional errors if present
        if len(self.errors) > 1:
            error_dict["error"]["additional_errors"] = [
                {
                    "message": e.message,
                    "code": e.code,
                    "param": e.param,
                }
                for e in self.errors[1:]
            ]

        return error_dict


@dataclass
class ValidationError:
    """
    Represents a validation error.

    Validation errors indicate that a request is invalid and should be rejected.
    """

    message: str
    code: str | None = None
    param: str | None = None
    severity: ValidationSeverity = ValidationSeverity.ERROR

    def __str__(self) -> str:
        """Return a human-readable string representation."""
        parts = [self.message]
        if self.param:
            parts.append(f"(param: {self.param})")
        if self.code:
            parts.append(f"[{self.code}]")
        return " ".join(parts)


@dataclass
class ValidationWarning:
    """
    Represents a validation warning.

    Validation warnings indicate potential issues that don't prevent request
    processing but should be brought to the user's attention.
    """

    message: str
    code: str | None = None
    param: str | None = None

    def __str__(self) -> str:
        """Return a human-readable string representation."""
        parts = [self.message]
        if self.param:
            parts.append(f"(param: {self.param})")
        if self.code:
            parts.append(f"[{self.code}]")
        return " ".join(parts)


@runtime_checkable
class Validator(Protocol):
    """
    Protocol for synchronous validators.

    Validators are responsible for checking specific aspects of a request
    and returning validation results.
    """

    def validate(self,
                 request: Any,
                 context: dict[str,
                               Any] | None = None) -> ValidationResult:
        """
        Validate a request.

        Args:
            request: The request object to validate
            context: Optional context information (e.g., API key, model info)

        Returns:
            ValidationResult indicating success or failure
        """
        ...

    @property
    def name(self) -> str:
        """
        Get the name of this validator.

        Returns:
            Human-readable validator name
        """
        ...


@runtime_checkable
class AsyncValidator(Protocol):
    """
    Protocol for asynchronous validators.

    Async validators are used for validation operations that require I/O or
    other async operations (e.g., database lookups, external API calls).
    """

    async def validate(self,
                       request: Any,
                       context: dict[str,
                                     Any] | None = None) -> ValidationResult:
        """
        Validate a request asynchronously.

        Args:
            request: The request object to validate
            context: Optional context information (e.g., API key, model info)

        Returns:
            ValidationResult indicating success or failure
        """
        ...

    @property
    def name(self) -> str:
        """
        Get the name of this validator.

        Returns:
            Human-readable validator name
        """
        ...
