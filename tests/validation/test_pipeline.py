"""
Tests for validation pipeline orchestration.
"""

#  SPDX-License-Identifier: Apache-2.0

import pytest

from fakeai.validation.base import ValidationResult
from fakeai.validation.pipeline import ParallelValidationPipeline, ValidationPipeline


# Mock validators for testing
class AlwaysPassValidator:
    """Mock validator that always passes."""

    def __init__(self, name: str = "AlwaysPass"):
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    def validate(self, request, context=None):
        return ValidationResult.success(metadata={"validator": self.name})


class AlwaysFailValidator:
    """Mock validator that always fails."""

    def __init__(self, name: str = "AlwaysFail"):
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    def validate(self, request, context=None):
        return ValidationResult.failure(
            message=f"{self.name} failed",
            code="test_failure",
            metadata={"validator": self.name},
        )


class AddWarningValidator:
    """Mock validator that adds a warning but passes."""

    def __init__(self, name: str = "AddWarning"):
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    def validate(self, request, context=None):
        result = ValidationResult.success()
        result.add_warning(f"{self.name} warning", code="test_warning")
        return result


class AsyncPassValidator:
    """Mock async validator that always passes."""

    def __init__(self, name: str = "AsyncPass"):
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    async def validate(self, request, context=None):
        return ValidationResult.success(metadata={"validator": self.name})


class AsyncFailValidator:
    """Mock async validator that always fails."""

    def __init__(self, name: str = "AsyncFail"):
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    async def validate(self, request, context=None):
        return ValidationResult.failure(
            message=f"{self.name} failed",
            code="test_failure",
        )


class TestValidationPipeline:
    """Tests for ValidationPipeline class."""

    def test_empty_pipeline(self):
        """Test empty pipeline always succeeds."""
        pipeline = ValidationPipeline()
        result = pipeline.validate(request={})

        assert result.valid is True
        assert len(result.errors) == 0
        assert len(result.warnings) == 0

    def test_single_passing_validator(self):
        """Test pipeline with single passing validator."""
        pipeline = ValidationPipeline()
        pipeline.add_validator(AlwaysPassValidator())

        result = pipeline.validate(request={})

        assert result.valid is True
        assert len(result.errors) == 0

    def test_single_failing_validator(self):
        """Test pipeline with single failing validator."""
        pipeline = ValidationPipeline()
        pipeline.add_validator(AlwaysFailValidator())

        result = pipeline.validate(request={})

        assert result.valid is False
        assert len(result.errors) == 1
        assert "failed_validator" in result.metadata

    def test_multiple_passing_validators(self):
        """Test pipeline with multiple passing validators."""
        pipeline = ValidationPipeline()
        pipeline.add_validators(
            [
                AlwaysPassValidator("Pass1"),
                AlwaysPassValidator("Pass2"),
                AlwaysPassValidator("Pass3"),
            ]
        )

        result = pipeline.validate(request={})

        assert result.valid is True
        assert len(result.errors) == 0

    def test_fail_fast_mode(self):
        """Test fail-fast mode stops at first error."""
        pipeline = ValidationPipeline(fail_fast=True)
        pipeline.add_validators(
            [
                AlwaysPassValidator("Pass1"),
                AlwaysFailValidator("Fail1"),
                AlwaysFailValidator("Fail2"),  # Should not be reached
            ]
        )

        result = pipeline.validate(request={})

        assert result.valid is False
        assert len(result.errors) == 1  # Only first error
        assert result.metadata["failed_validator"] == "Fail1"

    def test_collect_all_mode(self):
        """Test collect-all mode collects all errors."""
        pipeline = ValidationPipeline(fail_fast=False)
        pipeline.add_validators(
            [
                AlwaysFailValidator("Fail1"),
                AlwaysFailValidator("Fail2"),
                AlwaysFailValidator("Fail3"),
            ]
        )

        result = pipeline.validate(request={})

        assert result.valid is False
        assert len(result.errors) == 3  # All errors collected

    def test_warnings_dont_stop_execution(self):
        """Test that warnings don't stop pipeline execution."""
        pipeline = ValidationPipeline(fail_fast=True)
        pipeline.add_validators(
            [
                AddWarningValidator("Warn1"),
                AddWarningValidator("Warn2"),
                AlwaysPassValidator("Pass1"),
            ]
        )

        result = pipeline.validate(request={})

        assert result.valid is True
        assert len(result.warnings) == 2
        assert len(result.errors) == 0

    def test_context_passing(self):
        """Test that context is passed to validators."""

        class ContextCheckValidator:
            @property
            def name(self):
                return "ContextCheck"

            def validate(self, request, context=None):
                if context and context.get("check_key") == "check_value":
                    return ValidationResult.success()
                return ValidationResult.failure("Context check failed")

        pipeline = ValidationPipeline()
        pipeline.add_validator(ContextCheckValidator())

        result = pipeline.validate(request={}, context={"check_key": "check_value"})
        assert result.valid is True

    def test_pipeline_length(self):
        """Test pipeline length reporting."""
        pipeline = ValidationPipeline()
        assert len(pipeline) == 0

        pipeline.add_validator(AlwaysPassValidator())
        assert len(pipeline) == 1

        pipeline.add_validators([AlwaysPassValidator(), AlwaysPassValidator()])
        assert len(pipeline) == 3

    def test_pipeline_repr(self):
        """Test pipeline string representation."""
        pipeline = ValidationPipeline(name="TestPipeline", fail_fast=True)
        pipeline.add_validators(
            [AlwaysPassValidator("V1"), AlwaysPassValidator("V2")]
        )

        repr_str = repr(pipeline)
        assert "TestPipeline" in repr_str
        assert "fail_fast=True" in repr_str
        assert "V1" in repr_str
        assert "V2" in repr_str

    @pytest.mark.asyncio
    async def test_async_validation(self):
        """Test async validation with async validators."""
        pipeline = ValidationPipeline()
        pipeline.add_validators(
            [
                AsyncPassValidator("AsyncPass1"),
                AsyncPassValidator("AsyncPass2"),
            ]
        )

        result = await pipeline.validate_async(request={})

        assert result.valid is True
        assert len(result.errors) == 0

    @pytest.mark.asyncio
    async def test_async_fail_fast(self):
        """Test async validation with fail-fast mode."""
        pipeline = ValidationPipeline(fail_fast=True)
        pipeline.add_validators(
            [
                AsyncPassValidator("AsyncPass"),
                AsyncFailValidator("AsyncFail1"),
                AsyncFailValidator("AsyncFail2"),  # Should not be reached
            ]
        )

        result = await pipeline.validate_async(request={})

        assert result.valid is False
        assert len(result.errors) == 1  # Only first error

    @pytest.mark.asyncio
    async def test_mixed_sync_async_validators(self):
        """Test pipeline with mixed sync and async validators."""
        pipeline = ValidationPipeline()
        pipeline.add_validators(
            [
                AlwaysPassValidator("SyncPass"),
                AsyncPassValidator("AsyncPass"),
                AlwaysPassValidator("SyncPass2"),
            ]
        )

        result = await pipeline.validate_async(request={})

        assert result.valid is True

    def test_sync_validation_with_async_validators_raises(self):
        """Test that sync validation raises error with async validators."""
        pipeline = ValidationPipeline()
        pipeline.add_validator(AsyncPassValidator())

        with pytest.raises(RuntimeError, match="contains async validators"):
            pipeline.validate(request={})


class TestParallelValidationPipeline:
    """Tests for ParallelValidationPipeline class."""

    @pytest.mark.asyncio
    async def test_empty_parallel_pipeline(self):
        """Test empty parallel pipeline."""
        pipeline = ParallelValidationPipeline()
        result = await pipeline.validate_async(request={})

        assert result.valid is True
        assert len(result.errors) == 0

    @pytest.mark.asyncio
    async def test_parallel_all_pass(self):
        """Test parallel execution with all passing validators."""
        pipeline = ParallelValidationPipeline()
        pipeline.add_validator(AsyncPassValidator("Async1"))
        pipeline.add_validator(AsyncPassValidator("Async2"))
        pipeline.add_validator(AsyncPassValidator("Async3"))

        result = await pipeline.validate_async(request={})

        assert result.valid is True
        assert len(result.errors) == 0

    @pytest.mark.asyncio
    async def test_parallel_all_fail(self):
        """Test parallel execution with all failing validators."""
        pipeline = ParallelValidationPipeline()
        pipeline.add_validator(AsyncFailValidator("Fail1"))
        pipeline.add_validator(AsyncFailValidator("Fail2"))
        pipeline.add_validator(AsyncFailValidator("Fail3"))

        result = await pipeline.validate_async(request={})

        assert result.valid is False
        assert len(result.errors) == 3  # All errors collected

    @pytest.mark.asyncio
    async def test_parallel_mixed_results(self):
        """Test parallel execution with mixed results."""
        pipeline = ParallelValidationPipeline()
        pipeline.add_validator(AsyncPassValidator("Pass"))
        pipeline.add_validator(AsyncFailValidator("Fail"))
        pipeline.add_validator(AsyncPassValidator("Pass2"))

        result = await pipeline.validate_async(request={})

        assert result.valid is False
        assert len(result.errors) == 1

    def test_parallel_pipeline_rejects_sync_validators(self):
        """Test that parallel pipeline rejects sync validators."""
        pipeline = ParallelValidationPipeline()

        with pytest.raises(ValueError, match="not async"):
            pipeline.add_validator(AlwaysPassValidator())

    def test_parallel_pipeline_length(self):
        """Test parallel pipeline length reporting."""
        pipeline = ParallelValidationPipeline()
        assert len(pipeline) == 0

        pipeline.add_validator(AsyncPassValidator())
        assert len(pipeline) == 1

    def test_parallel_pipeline_repr(self):
        """Test parallel pipeline string representation."""
        pipeline = ParallelValidationPipeline(name="TestParallel")
        pipeline.add_validator(AsyncPassValidator("V1"))

        repr_str = repr(pipeline)
        assert "TestParallel" in repr_str
        assert "V1" in repr_str
