"""
Tools and function calling validator.

Validates tool/function calling parameters.
"""

#  SPDX-License-Identifier: Apache-2.0

from typing import Any

from fakeai.validation.base import ValidationResult


class ToolsValidator:
    """
    Validator that checks tool/function calling parameters.

    Validates 'tools', 'tool_choice', 'functions', and 'function_call' parameters.
    Note: 'functions' and 'function_call' are deprecated in favor of 'tools' and 'tool_choice'.
    """

    VALID_TOOL_TYPES = {"function"}
    MAX_TOOLS = 128

    def __init__(self, name: str = "ToolsValidator"):
        """
        Initialize the tools validator.

        Args:
            name: Name for this validator
        """
        self._name = name

    @property
    def name(self) -> str:
        """Get the name of this validator."""
        return self._name

    def _validate_function_definition(
        self, func: dict[str, Any], index: int | None = None
    ) -> list[tuple[str, str, str | None]]:
        """
        Validate a function definition.

        Args:
            func: Function definition object
            index: Index in array (for error messages)

        Returns:
            List of (message, code, param) tuples for errors
        """
        errors = []
        prefix = f"tools[{index}].function" if index is not None else "function"

        # Function must be a dict
        if not isinstance(func, dict):
            errors.append(
                (f"{prefix} must be an object", "invalid_type", prefix))
            return errors

        # Validate name
        if "name" not in func:
            errors.append(
                (f"{prefix}.name is required",
                 "missing_field",
                 f"{prefix}.name"))
        elif not isinstance(func["name"], str):
            errors.append(
                (f"{prefix}.name must be a string",
                 "invalid_type",
                 f"{prefix}.name"))
        elif not func["name"]:
            errors.append(
                (f"{prefix}.name cannot be empty",
                 "invalid_value",
                 f"{prefix}.name"))
        elif len(func["name"]) > 64:
            errors.append(
                (f"{prefix}.name cannot be longer than 64 characters",
                 "invalid_value",
                 f"{prefix}.name"))

        # Validate description (optional but recommended)
        if "description" in func and func["description"] is not None:
            if not isinstance(func["description"], str):
                errors.append(
                    (f"{prefix}.description must be a string",
                     "invalid_type",
                     f"{prefix}.description"))

        # Validate parameters (optional JSON schema)
        if "parameters" in func and func["parameters"] is not None:
            params = func["parameters"]
            if not isinstance(params, dict):
                errors.append(
                    (f"{prefix}.parameters must be an object",
                     "invalid_type",
                     f"{prefix}.parameters"))
            else:
                # Basic JSON schema validation
                if "type" in params and params["type"] != "object":
                    errors.append(
                        (
                            f"{prefix}.parameters.type must be 'object'",
                            "invalid_value",
                            f"{prefix}.parameters.type",
                        )
                    )

        return errors

    def validate(
        self, request: Any, context: dict[str, Any] | None = None
    ) -> ValidationResult:
        """
        Validate tool/function calling parameters.

        Args:
            request: Request object with tool parameters
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

        # Validate tools parameter (modern API)
        if "tools" in params and params["tools"] is not None:
            tools = params["tools"]

            # Must be an array
            if not isinstance(tools, list):
                result.add_error(
                    message="tools must be an array",
                    code="invalid_type",
                    param="tools",
                )
            elif not tools:
                result.add_error(
                    message="tools array cannot be empty",
                    code="invalid_value",
                    param="tools",
                )
            elif len(tools) > self.MAX_TOOLS:
                result.add_error(
                    message=f"tools array cannot have more than {
                        self.MAX_TOOLS} tools",
                    code="invalid_value",
                    param="tools",
                )
            else:
                # Validate each tool
                for i, tool in enumerate(tools):
                    if not isinstance(tool, dict):
                        result.add_error(
                            message=f"tools[{i}] must be an object",
                            code="invalid_type",
                            param=f"tools[{i}]",
                        )
                        continue

                    # Validate type
                    if "type" not in tool:
                        result.add_error(
                            message=f"tools[{i}].type is required",
                            code="missing_field",
                            param=f"tools[{i}].type",
                        )
                    elif tool["type"] not in self.VALID_TOOL_TYPES:
                        result.add_error(
                            message=f"tools[{i}].type must be one of: {
                                ', '.join(
                                    self.VALID_TOOL_TYPES)}",
                            code="invalid_value",
                            param=f"tools[{i}].type",
                        )

                    # Validate function definition
                    if tool.get("type") == "function":
                        if "function" not in tool:
                            result.add_error(
                                message=f"tools[{i}].function is required when type is 'function'",
                                code="missing_field",
                                param=f"tools[{i}].function",
                            )
                        else:
                            errors = self._validate_function_definition(
                                tool["function"], i)
                            for msg, code, param in errors:
                                result.add_error(
                                    message=msg, code=code, param=param)

        # Validate tool_choice parameter
        if "tool_choice" in params and params["tool_choice"] is not None:
            tool_choice = params["tool_choice"]

            # tool_choice only makes sense with tools
            if "tools" not in params or not params["tools"]:
                result.add_warning(
                    message="tool_choice is only used when tools are provided",
                    code="unused_parameter",
                    param="tool_choice",
                )

            # Can be string or object
            if isinstance(tool_choice, str):
                # Valid values: "none", "auto", "required"
                if tool_choice not in {"none", "auto", "required"}:
                    result.add_error(
                        message="tool_choice must be 'none', 'auto', 'required', or an object",
                        code="invalid_value",
                        param="tool_choice",
                    )
            elif isinstance(tool_choice, dict):
                # Must have type and function
                if "type" not in tool_choice:
                    result.add_error(
                        message="tool_choice.type is required",
                        code="missing_field",
                        param="tool_choice.type",
                    )
                elif tool_choice["type"] != "function":
                    result.add_error(
                        message="tool_choice.type must be 'function'",
                        code="invalid_value",
                        param="tool_choice.type",
                    )

                if "function" not in tool_choice:
                    result.add_error(
                        message="tool_choice.function is required",
                        code="missing_field",
                        param="tool_choice.function",
                    )
                elif not isinstance(tool_choice["function"], dict):
                    result.add_error(
                        message="tool_choice.function must be an object",
                        code="invalid_type",
                        param="tool_choice.function",
                    )
                elif "name" not in tool_choice["function"]:
                    result.add_error(
                        message="tool_choice.function.name is required",
                        code="missing_field",
                        param="tool_choice.function.name",
                    )
            else:
                result.add_error(
                    message="tool_choice must be a string or object",
                    code="invalid_type",
                    param="tool_choice",
                )

        # Validate deprecated functions parameter
        if "functions" in params and params["functions"] is not None:
            result.add_warning(
                message="'functions' is deprecated. Use 'tools' instead",
                code="deprecated_parameter",
                param="functions",
            )

            functions = params["functions"]
            if not isinstance(functions, list):
                result.add_error(
                    message="functions must be an array",
                    code="invalid_type",
                    param="functions",
                )
            elif functions:
                # Validate each function
                for i, func in enumerate(functions):
                    errors = self._validate_function_definition(func, None)
                    for msg, code, param in errors:
                        # Adjust param to use functions instead of tools
                        param = param.replace(
                            "tools[", "functions[").replace(
                            ".function", "")
                        result.add_error(message=msg, code=code, param=param)

        # Validate deprecated function_call parameter
        if "function_call" in params and params["function_call"] is not None:
            result.add_warning(
                message="'function_call' is deprecated. Use 'tool_choice' instead",
                code="deprecated_parameter",
                param="function_call",
            )

            function_call = params["function_call"]

            # function_call only makes sense with functions
            if "functions" not in params or not params["functions"]:
                result.add_warning(
                    message="function_call is only used when functions are provided",
                    code="unused_parameter",
                    param="function_call",
                )

            # Can be string or object
            if isinstance(function_call, str):
                if function_call not in {"none", "auto"}:
                    result.add_error(
                        message="function_call must be 'none', 'auto', or an object with 'name'",
                        code="invalid_value",
                        param="function_call",
                    )
            elif isinstance(function_call, dict):
                if "name" not in function_call:
                    result.add_error(
                        message="function_call.name is required",
                        code="missing_field",
                        param="function_call.name",
                    )
            else:
                result.add_error(
                    message="function_call must be a string or object",
                    code="invalid_type",
                    param="function_call",
                )

        # Warn if both old and new APIs are used together
        if ("tools" in params and params["tools"]) and (
            "functions" in params and params["functions"]
        ):
            result.add_warning(
                message="Using both 'tools' and 'functions' is not recommended. Use 'tools' only",
                code="mixed_tool_apis",
            )

        return result
