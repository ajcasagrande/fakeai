"""
Validation pipeline orchestration.

This module provides the ValidationPipeline class for composing multiple validators
and executing them with different strategies (fail-fast, collect-all, etc.).
"""

#  SPDX-License-Identifier: Apache-2.0

import asyncio
import inspect
from typing import Any

from fakeai.validation.base import AsyncValidator, ValidationResult, Validator


class ValidationPipeline:
    """
    Composable validation pipeline.

    The pipeline executes a series of validators in order, with configurable
    behavior for how to handle failures (short-circuit or collect all errors).
    """

    def __init__(
        self,
        validators: list[Validator | AsyncValidator] | None = None,
        fail_fast: bool = True,
        name: str = "ValidationPipeline",
    ):
        """
        Initialize a validation pipeline.

        Args:
            validators: List of validators to execute
            fail_fast: If True, stop on first error (default). If False, collect all errors.
            name: Name for this pipeline (used in logging/debugging)
        """
        self._validators = validators or []
        self._fail_fast = fail_fast
        self._name = name

    @property
    def name(self) -> str:
        """Get the name of this pipeline."""
        return self._name

    def add_validator(self, validator: Validator |
                      AsyncValidator) -> "ValidationPipeline":
        """
        Add a validator to the pipeline.

        Args:
            validator: Validator to add

        Returns:
            Self for method chaining
        """
        self._validators.append(validator)
        return self

    def add_validators(
        self, validators: list[Validator | AsyncValidator]
    ) -> "ValidationPipeline":
        """
        Add multiple validators to the pipeline.

        Args:
            validators: List of validators to add

        Returns:
            Self for method chaining
        """
        self._validators.extend(validators)
        return self

    async def validate_async(
        self, request: Any, context: dict[str, Any] | None = None
    ) -> ValidationResult:
        """
        Execute the validation pipeline asynchronously.

        This method handles both sync and async validators, running them in order.
        If fail_fast is True, stops at the first error. Otherwise, collects all errors.

        Args:
            request: The request object to validate
            context: Optional context information

        Returns:
            Aggregated validation result
        """
        result = ValidationResult.success()
        context = context or {}

        for validator in self._validators:
            # Check if validator is async
            if inspect.iscoroutinefunction(validator.validate):
                validator_result = await validator.validate(request, context)
            else:
                validator_result = validator.validate(request, context)

            # Merge results
            result.merge(validator_result)

            # Stop on first error if fail_fast is enabled
            if self._fail_fast and not validator_result.valid:
                # Add validator name to metadata for debugging
                result.metadata["failed_validator"] = validator.name
                break

        return result

    def validate(
        self, request: Any, context: dict[str, Any] | None = None
    ) -> ValidationResult:
        """
        Execute the validation pipeline synchronously.

        This is a synchronous wrapper around validate_async. It will work with
        sync validators but will raise an error if async validators are present.

        Args:
            request: The request object to validate
            context: Optional context information

        Returns:
            Aggregated validation result

        Raises:
            RuntimeError: If the pipeline contains async validators
        """
        # Check if any validators are async
        has_async = any(
            inspect.iscoroutinefunction(v.validate) for v in self._validators
        )

        if has_async:
            raise RuntimeError(
                f"Pipeline '{self._name}' contains async validators. "
                "Use validate_async() instead of validate()."
            )

        result = ValidationResult.success()
        context = context or {}

        for validator in self._validators:
            validator_result = validator.validate(request, context)
            result.merge(validator_result)

            # Stop on first error if fail_fast is enabled
            if self._fail_fast and not validator_result.valid:
                result.metadata["failed_validator"] = validator.name
                break

        return result

    def __len__(self) -> int:
        """Return the number of validators in the pipeline."""
        return len(self._validators)

    def __repr__(self) -> str:
        """Return a string representation of the pipeline."""
        validator_names = [v.name for v in self._validators]
        return (
            f"ValidationPipeline(name='{self._name}', "
            f"fail_fast={self._fail_fast}, "
            f"validators={validator_names})"
        )


class ParallelValidationPipeline:
    """
    Parallel validation pipeline.

    Executes independent validators in parallel for better performance.
    All validators must be async for parallel execution.
    """

    def __init__(
        self,
        validators: list[AsyncValidator] | None = None,
        name: str = "ParallelValidationPipeline",
    ):
        """
        Initialize a parallel validation pipeline.

        Args:
            validators: List of async validators to execute in parallel
            name: Name for this pipeline (used in logging/debugging)
        """
        self._validators = validators or []
        self._name = name

        # Verify all validators are async
        for validator in self._validators:
            if not inspect.iscoroutinefunction(validator.validate):
                raise ValueError(
                    f"Validator '{validator.name}' is not async. "
                    "ParallelValidationPipeline requires all validators to be async."
                )

    @property
    def name(self) -> str:
        """Get the name of this pipeline."""
        return self._name

    def add_validator(
            self,
            validator: AsyncValidator) -> "ParallelValidationPipeline":
        """
        Add a validator to the pipeline.

        Args:
            validator: Async validator to add

        Returns:
            Self for method chaining
        """
        if not inspect.iscoroutinefunction(validator.validate):
            raise ValueError(
                f"Validator '{validator.name}' is not async. "
                "ParallelValidationPipeline requires async validators."
            )
        self._validators.append(validator)
        return self

    async def validate_async(
        self, request: Any, context: dict[str, Any] | None = None
    ) -> ValidationResult:
        """
        Execute all validators in parallel.

        Args:
            request: The request object to validate
            context: Optional context information

        Returns:
            Aggregated validation result from all validators
        """
        result = ValidationResult.success()
        context = context or {}

        if not self._validators:
            return result

        # Execute all validators in parallel
        tasks = [validator.validate(request, context)
                 for validator in self._validators]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Merge all results
        for i, validator_result in enumerate(results):
            if isinstance(validator_result, Exception):
                # Handle exceptions from validators
                result.add_error(
                    message=f"Validator '{
                        self._validators[i].name}' raised an exception: {validator_result}",
                    code="validator_exception",
                )
            else:
                result.merge(validator_result)

        return result

    def __len__(self) -> int:
        """Return the number of validators in the pipeline."""
        return len(self._validators)

    def __repr__(self) -> str:
        """Return a string representation of the pipeline."""
        validator_names = [v.name for v in self._validators]
        return f"ParallelValidationPipeline(name='{
            self._name}', validators={validator_names})"
