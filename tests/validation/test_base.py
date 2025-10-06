"""
Tests for base validation classes and protocols.
"""

#  SPDX-License-Identifier: Apache-2.0

import pytest

from fakeai.validation.base import (
    ValidationError,
    ValidationResult,
    ValidationSeverity,
    ValidationWarning,
)


class TestValidationResult:
    """Tests for ValidationResult class."""

    def test_success_creation(self):
        """Test creating a successful validation result."""
        result = ValidationResult.success()
        assert result.valid is True
        assert len(result.errors) == 0
        assert len(result.warnings) == 0
        assert result.metadata == {}

    def test_success_with_metadata(self):
        """Test creating a successful result with metadata."""
        metadata = {"foo": "bar", "count": 42}
        result = ValidationResult.success(metadata=metadata)
        assert result.valid is True
        assert result.metadata == metadata

    def test_failure_creation(self):
        """Test creating a failed validation result."""
        result = ValidationResult.failure(
            message="Test error",
            code="test_error",
            param="test_param",
        )
        assert result.valid is False
        assert len(result.errors) == 1
        assert result.errors[0].message == "Test error"
        assert result.errors[0].code == "test_error"
        assert result.errors[0].param == "test_param"

    def test_add_error(self):
        """Test adding errors to a validation result."""
        result = ValidationResult(valid=True)
        assert result.valid is True

        result.add_error("Error 1", code="err1", param="param1")
        assert result.valid is False
        assert len(result.errors) == 1

        result.add_error("Error 2", code="err2", param="param2")
        assert len(result.errors) == 2

    def test_add_warning(self):
        """Test adding warnings to a validation result."""
        result = ValidationResult.success()

        result.add_warning("Warning 1", code="warn1", param="param1")
        assert result.valid is True  # Warnings don't affect validity
        assert len(result.warnings) == 1

        result.add_warning("Warning 2", code="warn2")
        assert len(result.warnings) == 2

    def test_merge_results(self):
        """Test merging validation results."""
        result1 = ValidationResult.success(metadata={"key1": "value1"})
        result1.add_warning("Warning 1")

        result2 = ValidationResult.failure(
            "Error 1", code="err1", metadata={"key2": "value2"}
        )
        result2.add_warning("Warning 2")

        result1.merge(result2)

        assert result1.valid is False  # Merged error makes it invalid
        assert len(result1.errors) == 1
        assert len(result1.warnings) == 2
        assert result1.metadata == {"key1": "value1", "key2": "value2"}

    def test_to_error_response_single_error(self):
        """Test converting a single error to error response."""
        result = ValidationResult.failure(
            message="Invalid value",
            code="invalid_value",
            param="temperature",
        )

        error_response = result.to_error_response()

        assert "error" in error_response
        assert error_response["error"]["message"] == "Invalid value"
        assert error_response["error"]["type"] == "invalid_request_error"
        assert error_response["error"]["code"] == "invalid_value"
        assert error_response["error"]["param"] == "temperature"

    def test_to_error_response_multiple_errors(self):
        """Test converting multiple errors to error response."""
        result = ValidationResult(valid=False)
        result.add_error("Error 1", code="err1", param="param1")
        result.add_error("Error 2", code="err2", param="param2")
        result.add_error("Error 3", code="err3")

        error_response = result.to_error_response()

        assert "error" in error_response
        assert error_response["error"]["message"] == "Error 1"
        assert "additional_errors" in error_response["error"]
        assert len(error_response["error"]["additional_errors"]) == 2

    def test_to_error_response_no_errors(self):
        """Test converting a result with no errors."""
        result = ValidationResult.success()
        error_response = result.to_error_response()
        assert error_response == {}


class TestValidationError:
    """Tests for ValidationError class."""

    def test_creation_minimal(self):
        """Test creating a validation error with minimal fields."""
        error = ValidationError(message="Test error")
        assert error.message == "Test error"
        assert error.code is None
        assert error.param is None
        assert error.severity == ValidationSeverity.ERROR

    def test_creation_full(self):
        """Test creating a validation error with all fields."""
        error = ValidationError(
            message="Test error",
            code="test_code",
            param="test_param",
            severity=ValidationSeverity.WARNING,
        )
        assert error.message == "Test error"
        assert error.code == "test_code"
        assert error.param == "test_param"
        assert error.severity == ValidationSeverity.WARNING

    def test_string_representation(self):
        """Test string representation of validation error."""
        error1 = ValidationError(message="Simple error")
        assert str(error1) == "Simple error"

        error2 = ValidationError(message="Error", param="field")
        assert str(error2) == "Error (param: field)"

        error3 = ValidationError(message="Error", code="err_code")
        assert str(error3) == "Error [err_code]"

        error4 = ValidationError(message="Error", param="field", code="err_code")
        assert str(error4) == "Error (param: field) [err_code]"


class TestValidationWarning:
    """Tests for ValidationWarning class."""

    def test_creation_minimal(self):
        """Test creating a validation warning with minimal fields."""
        warning = ValidationWarning(message="Test warning")
        assert warning.message == "Test warning"
        assert warning.code is None
        assert warning.param is None

    def test_creation_full(self):
        """Test creating a validation warning with all fields."""
        warning = ValidationWarning(
            message="Test warning",
            code="test_code",
            param="test_param",
        )
        assert warning.message == "Test warning"
        assert warning.code == "test_code"
        assert warning.param == "test_param"

    def test_string_representation(self):
        """Test string representation of validation warning."""
        warning1 = ValidationWarning(message="Simple warning")
        assert str(warning1) == "Simple warning"

        warning2 = ValidationWarning(message="Warning", param="field")
        assert str(warning2) == "Warning (param: field)"

        warning3 = ValidationWarning(message="Warning", code="warn_code")
        assert str(warning3) == "Warning [warn_code]"

        warning4 = ValidationWarning(message="Warning", param="field", code="warn_code")
        assert str(warning4) == "Warning (param: field) [warn_code]"


class TestValidationSeverity:
    """Tests for ValidationSeverity enum."""

    def test_severity_values(self):
        """Test validation severity values."""
        assert ValidationSeverity.ERROR == "error"
        assert ValidationSeverity.WARNING == "warning"
        assert ValidationSeverity.INFO == "info"

    def test_severity_comparison(self):
        """Test comparing severity values."""
        assert ValidationSeverity.ERROR == ValidationSeverity.ERROR
        assert ValidationSeverity.ERROR != ValidationSeverity.WARNING
