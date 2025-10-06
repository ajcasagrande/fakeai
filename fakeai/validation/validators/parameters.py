"""
Parameter validator.

Validates request parameters for correctness and valid ranges.
"""

#  SPDX-License-Identifier: Apache-2.0

from typing import Any

from fakeai.validation.base import ValidationResult, ValidationSeverity


class ParameterValidator:
    """
    Validator that checks parameter values and ranges.

    Validates common API parameters like temperature, top_p, frequency_penalty,
    presence_penalty, max_tokens, etc.
    """

    def __init__(self, name: str = "ParameterValidator"):
        """
        Initialize the parameter validator.

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
        Validate request parameters.

        Args:
            request: Request object with parameters to validate
            context: Optional context information (unused)

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

        # Validate temperature
        if "temperature" in params and params["temperature"] is not None:
            temp = params["temperature"]
            if not isinstance(temp, (int, float)):
                result.add_error(
                    message="temperature must be a number",
                    code="invalid_type",
                    param="temperature",
                )
            elif temp < 0 or temp > 2:
                result.add_error(
                    message="temperature must be between 0 and 2",
                    code="invalid_value",
                    param="temperature",
                )
            elif temp > 1.5:
                result.add_warning(
                    message="temperature > 1.5 may produce incoherent outputs",
                    code="high_temperature",
                    param="temperature",
                )

        # Validate top_p
        if "top_p" in params and params["top_p"] is not None:
            top_p = params["top_p"]
            if not isinstance(top_p, (int, float)):
                result.add_error(
                    message="top_p must be a number",
                    code="invalid_type",
                    param="top_p",
                )
            elif top_p < 0 or top_p > 1:
                result.add_error(
                    message="top_p must be between 0 and 1",
                    code="invalid_value",
                    param="top_p",
                )

        # Validate frequency_penalty
        if "frequency_penalty" in params and params["frequency_penalty"] is not None:
            freq = params["frequency_penalty"]
            if not isinstance(freq, (int, float)):
                result.add_error(
                    message="frequency_penalty must be a number",
                    code="invalid_type",
                    param="frequency_penalty",
                )
            elif freq < -2 or freq > 2:
                result.add_error(
                    message="frequency_penalty must be between -2 and 2",
                    code="invalid_value",
                    param="frequency_penalty",
                )

        # Validate presence_penalty
        if "presence_penalty" in params and params["presence_penalty"] is not None:
            pres = params["presence_penalty"]
            if not isinstance(pres, (int, float)):
                result.add_error(
                    message="presence_penalty must be a number",
                    code="invalid_type",
                    param="presence_penalty",
                )
            elif pres < -2 or pres > 2:
                result.add_error(
                    message="presence_penalty must be between -2 and 2",
                    code="invalid_value",
                    param="presence_penalty",
                )

        # Validate max_tokens
        if "max_tokens" in params and params["max_tokens"] is not None:
            max_tok = params["max_tokens"]
            if not isinstance(max_tok, int):
                result.add_error(
                    message="max_tokens must be an integer",
                    code="invalid_type",
                    param="max_tokens",
                )
            elif max_tok < 1:
                result.add_error(
                    message="max_tokens must be at least 1",
                    code="invalid_value",
                    param="max_tokens",
                )
            elif max_tok > 128000:
                result.add_warning(
                    message="max_tokens > 128000 may exceed most model limits",
                    code="high_max_tokens",
                    param="max_tokens",
                )

        # Validate n (number of completions)
        if "n" in params and params["n"] is not None:
            n = params["n"]
            if not isinstance(n, int):
                result.add_error(
                    message="n must be an integer",
                    code="invalid_type",
                    param="n",
                )
            elif n < 1:
                result.add_error(
                    message="n must be at least 1",
                    code="invalid_value",
                    param="n",
                )
            elif n > 10:
                result.add_warning(
                    message="n > 10 may be expensive and slow",
                    code="high_n",
                    param="n",
                )

        # Validate best_of (for completions API)
        if "best_of" in params and params["best_of"] is not None:
            best_of = params["best_of"]
            n = params.get("n", 1)
            if not isinstance(best_of, int):
                result.add_error(
                    message="best_of must be an integer",
                    code="invalid_type",
                    param="best_of",
                )
            elif best_of < n:
                result.add_error(
                    message=f"best_of ({best_of}) must be >= n ({n})",
                    code="invalid_value",
                    param="best_of",
                )

        # Validate logprobs
        if "logprobs" in params and params["logprobs"] is not None:
            logprobs = params["logprobs"]
            # In chat completions, logprobs is a boolean
            if isinstance(logprobs, bool):
                pass  # Valid
            # In completions API, logprobs is an integer 0-5
            elif isinstance(logprobs, int):
                if logprobs < 0 or logprobs > 5:
                    result.add_error(
                        message="logprobs must be between 0 and 5",
                        code="invalid_value",
                        param="logprobs",
                    )
            else:
                result.add_error(
                    message="logprobs must be a boolean or integer (0-5)",
                    code="invalid_type",
                    param="logprobs",
                )

        # Validate top_logprobs (chat completions)
        if "top_logprobs" in params and params["top_logprobs"] is not None:
            top_logprobs = params["top_logprobs"]
            if not isinstance(top_logprobs, int):
                result.add_error(
                    message="top_logprobs must be an integer",
                    code="invalid_type",
                    param="top_logprobs",
                )
            elif top_logprobs < 0 or top_logprobs > 20:
                result.add_error(
                    message="top_logprobs must be between 0 and 20",
                    code="invalid_value",
                    param="top_logprobs",
                )

        # Validate seed
        if "seed" in params and params["seed"] is not None:
            seed = params["seed"]
            if not isinstance(seed, int):
                result.add_error(
                    message="seed must be an integer",
                    code="invalid_type",
                    param="seed",
                )

        # Validate timeout
        if "timeout" in params and params["timeout"] is not None:
            timeout = params["timeout"]
            if not isinstance(timeout, (int, float)):
                result.add_error(
                    message="timeout must be a number",
                    code="invalid_type",
                    param="timeout",
                )
            elif timeout < 0:
                result.add_error(
                    message="timeout must be non-negative",
                    code="invalid_value",
                    param="timeout",
                )

        # Validate both temperature and top_p are not set together
        if (
            "temperature" in params
            and params["temperature"] is not None
            and params["temperature"] != 1.0
            and "top_p" in params
            and params["top_p"] is not None
            and params["top_p"] != 1.0
        ):
            result.add_warning(
                message="Setting both temperature and top_p is not recommended",
                code="both_sampling_params",
            )

        return result
