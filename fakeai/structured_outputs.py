"""
JSON Schema validation and generation for FakeAI structured outputs.

This module provides validation and generation capabilities for OpenAI's
structured outputs feature, supporting strict schema compliance.
"""

#  SPDX-License-Identifier: Apache-2.0

import random
import re
from typing import Any

from faker import Faker

fake = Faker()


class SchemaValidationError(Exception):
    """Raised when a JSON schema fails validation for strict mode."""

    pass


def validate_strict_schema(schema: dict[str, Any]) -> None:
    """
    Validate that a JSON schema meets OpenAI's strict mode requirements.

    Strict mode requirements:
    - Must have "additionalProperties": false at the root level
    - All object properties must be in "required" array
    - Cannot use "anyOf" at the root level
    - Nested objects must also follow these rules

    Args:
        schema: The JSON schema to validate

    Raises:
        SchemaValidationError: If the schema doesn't meet strict mode requirements
    """
    # Check root level requirements
    if schema.get("type") == "object":
        # Must have additionalProperties: false
        if schema.get("additionalProperties") is not False:
            raise SchemaValidationError(
                "Strict mode requires 'additionalProperties': false at root level"
            )

        # All properties must be in required array
        properties = schema.get("properties", {})
        required = set(schema.get("required", []))
        property_names = set(properties.keys())

        if property_names != required:
            missing = property_names - required
            extra = required - property_names
            msg_parts = []
            if missing:
                msg_parts.append(
                    f"properties not in required: {', '.join(sorted(missing))}"
                )
            if extra:
                msg_parts.append(
                    f"required contains non-existent properties: {', '.join(sorted(extra))}"
                )
            raise SchemaValidationError(
                f"Strict mode requires all properties to be in required array. {'; '.join(msg_parts)}"
            )

        # Validate nested objects
        for prop_name, prop_schema in properties.items():
            _validate_nested_schema(prop_schema, f"properties.{prop_name}")

    # Check for disallowed root-level constructs
    if "anyOf" in schema:
        raise SchemaValidationError(
            "Strict mode does not support 'anyOf' at root level"
        )


def _validate_nested_schema(schema: dict[str, Any], path: str) -> None:
    """
    Recursively validate nested schemas for strict mode compliance.

    Args:
        schema: The schema to validate
        path: The path to this schema (for error messages)

    Raises:
        SchemaValidationError: If nested schema doesn't meet requirements
    """
    if not isinstance(schema, dict):
        return

    schema_type = schema.get("type")

    if schema_type == "object":
        # Nested objects must also have additionalProperties: false
        if schema.get("additionalProperties") is not False:
            raise SchemaValidationError(
                f"Strict mode requires 'additionalProperties': false at {path}"
            )

        # All properties must be in required array
        properties = schema.get("properties", {})
        required = set(schema.get("required", []))
        property_names = set(properties.keys())

        if property_names != required:
            missing = property_names - required
            extra = required - property_names
            msg_parts = []
            if missing:
                msg_parts.append(
                    f"properties not in required: {', '.join(sorted(missing))}"
                )
            if extra:
                msg_parts.append(
                    f"required contains non-existent properties: {', '.join(sorted(extra))}"
                )
            raise SchemaValidationError(
                f"Strict mode requires all properties to be in required array at {path}. {'; '.join(msg_parts)}"
            )

        # Recursively validate nested properties
        for prop_name, prop_schema in properties.items():
            _validate_nested_schema(prop_schema, f"{path}.{prop_name}")

    elif schema_type == "array":
        # Validate array items schema
        items = schema.get("items")
        if items:
            _validate_nested_schema(items, f"{path}[]")


def generate_from_schema(schema: dict[str, Any]) -> Any:
    """
    Generate fake data that matches the given JSON schema.

    Supports:
    - Basic types: string, number, integer, boolean, null
    - Complex types: object, array
    - String formats: date-time, date, time, email, uri, uuid
    - Enums (for any type)
    - Constraints: minLength, maxLength, minimum, maximum, minItems, maxItems

    Args:
        schema: The JSON schema to generate data for

    Returns:
        Generated data matching the schema
    """
    schema_type = schema.get("type")

    # Handle enums first (they override type)
    if "enum" in schema:
        return random.choice(schema["enum"])

    # Handle different types
    if schema_type == "string":
        return _generate_string(schema)
    elif schema_type == "number":
        return _generate_number(schema, is_float=True)
    elif schema_type == "integer":
        return _generate_number(schema, is_float=False)
    elif schema_type == "boolean":
        return random.choice([True, False])
    elif schema_type == "null":
        return None
    elif schema_type == "object":
        return _generate_object(schema)
    elif schema_type == "array":
        return _generate_array(schema)
    else:
        # Default to string if type not specified
        return fake.sentence()


def _generate_string(schema: dict[str, Any]) -> str:
    """Generate a string value based on schema constraints."""
    # Check for format hints
    format_type = schema.get("format")

    if format_type == "date-time":
        return fake.iso8601()
    elif format_type == "date":
        return fake.date()
    elif format_type == "time":
        return fake.time()
    elif format_type == "email":
        return fake.email()
    elif format_type == "uri" or format_type == "url":
        return fake.url()
    elif format_type == "uuid":
        return fake.uuid4()
    elif format_type == "hostname":
        return fake.domain_name()
    elif format_type == "ipv4":
        return fake.ipv4()
    elif format_type == "ipv6":
        return fake.ipv6()

    # Check for pattern (if provided, try to match it)
    pattern = schema.get("pattern")
    if pattern:
        # Simple patterns we can handle
        if pattern == r"^\d{3}-\d{2}-\d{4}$":
            return f"{random.randint(100,999)}-{random.randint(10,99)}-{random.randint(1000,9999)}"
        elif pattern == r"^[A-Z]{2}\d{4}$":
            return f"{fake.random_uppercase_letter()}{fake.random_uppercase_letter()}{random.randint(1000,9999)}"
        # For other patterns, ignore and generate based on other constraints

    # Use description as a hint
    description = schema.get("description", "").lower()
    if "name" in description:
        value = fake.name()
    elif "email" in description:
        value = fake.email()
    elif "address" in description:
        value = fake.address().replace("\n", ", ")
    elif "phone" in description:
        value = fake.phone_number()
    elif "company" in description:
        value = fake.company()
    elif "city" in description:
        value = fake.city()
    elif "country" in description:
        value = fake.country()
    elif "url" in description or "link" in description:
        value = fake.url()
    else:
        # Default to a sentence
        value = fake.sentence()

    # Apply length constraints
    min_length = schema.get("minLength", 0)
    max_length = schema.get("maxLength")

    if max_length and len(value) > max_length:
        value = value[:max_length]

    # Ensure minimum length
    while len(value) < min_length:
        value += " " + fake.word()

    # Trim to max length if needed
    if max_length and len(value) > max_length:
        value = value[:max_length].rstrip()

    return value


def _generate_number(schema: dict[str, Any], is_float: bool = True) -> int | float:
    """Generate a number value based on schema constraints."""
    minimum = schema.get("minimum", 0)
    maximum = schema.get("maximum", 1000)

    # Handle exclusive bounds
    if schema.get("exclusiveMinimum") is not None:
        minimum = schema["exclusiveMinimum"] + (0.01 if is_float else 1)
    if schema.get("exclusiveMaximum") is not None:
        maximum = schema["exclusiveMaximum"] - (0.01 if is_float else 1)

    if is_float:
        value = random.uniform(minimum, maximum)
        # Round to reasonable precision
        return round(value, 2)
    else:
        return random.randint(int(minimum), int(maximum))


def _generate_object(schema: dict[str, Any]) -> dict[str, Any]:
    """Generate an object value based on schema constraints."""
    properties = schema.get("properties", {})
    result = {}

    for prop_name, prop_schema in properties.items():
        result[prop_name] = generate_from_schema(prop_schema)

    return result


def _generate_array(schema: dict[str, Any]) -> list[Any]:
    """Generate an array value based on schema constraints."""
    items_schema = schema.get("items", {})

    # Determine array length
    min_items = schema.get("minItems", 1)
    max_items = schema.get("maxItems", 5)
    length = random.randint(min_items, max_items)

    # Generate array items
    return [generate_from_schema(items_schema) for _ in range(length)]


def format_as_json_string(data: Any) -> str:
    """
    Format generated data as a JSON string.

    This uses Python's standard library to ensure valid JSON output.

    Args:
        data: The data to format

    Returns:
        JSON string representation
    """
    import json

    return json.dumps(data, indent=2)
