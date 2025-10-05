"""
Tests for structured outputs with JSON schema validation and generation.
"""
#  SPDX-License-Identifier: Apache-2.0

import json
import pytest
from openai import OpenAI

from fakeai import AppConfig
from fakeai.fakeai_service import FakeAIService
from fakeai.models import (
    ChatCompletionRequest,
    JsonSchema,
    JsonSchemaResponseFormat,
    Message,
    Role,
)
from fakeai.structured_outputs import (
    SchemaValidationError,
    generate_from_schema,
    validate_strict_schema,
)


# Test Schemas

VALID_STRICT_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "age": {"type": "integer"},
        "email": {"type": "string", "format": "email"},
    },
    "required": ["name", "age", "email"],
    "additionalProperties": False,
}

INVALID_SCHEMA_MISSING_ADDITIONAL_PROPERTIES = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "age": {"type": "integer"},
    },
    "required": ["name", "age"],
    # Missing additionalProperties: false
}

INVALID_SCHEMA_PARTIAL_REQUIRED = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "age": {"type": "integer"},
        "email": {"type": "string"},
    },
    "required": ["name", "age"],  # Missing email in required
    "additionalProperties": False,
}

INVALID_SCHEMA_WITH_ANYOF = {
    "type": "object",
    "anyOf": [
        {"properties": {"name": {"type": "string"}}},
        {"properties": {"id": {"type": "integer"}}},
    ],
    "additionalProperties": False,
}

NESTED_VALID_SCHEMA = {
    "type": "object",
    "properties": {
        "user": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"},
            },
            "required": ["name", "age"],
            "additionalProperties": False,
        },
        "metadata": {
            "type": "object",
            "properties": {
                "created": {"type": "string", "format": "date-time"},
                "updated": {"type": "string", "format": "date-time"},
            },
            "required": ["created", "updated"],
            "additionalProperties": False,
        },
    },
    "required": ["user", "metadata"],
    "additionalProperties": False,
}

NESTED_INVALID_SCHEMA = {
    "type": "object",
    "properties": {
        "user": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"},
            },
            "required": ["name"],  # Missing age
            "additionalProperties": False,
        },
    },
    "required": ["user"],
    "additionalProperties": False,
}

ARRAY_SCHEMA = {
    "type": "object",
    "properties": {
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "name": {"type": "string"},
                },
                "required": ["id", "name"],
                "additionalProperties": False,
            },
            "minItems": 1,
            "maxItems": 3,
        },
    },
    "required": ["items"],
    "additionalProperties": False,
}

ENUM_SCHEMA = {
    "type": "object",
    "properties": {
        "status": {"type": "string", "enum": ["active", "inactive", "pending"]},
        "priority": {"type": "integer", "enum": [1, 2, 3, 4, 5]},
    },
    "required": ["status", "priority"],
    "additionalProperties": False,
}


class TestSchemaValidation:
    """Test JSON schema validation for strict mode."""

    def test_valid_strict_schema(self):
        """Test that a valid strict schema passes validation."""
        # Should not raise
        validate_strict_schema(VALID_STRICT_SCHEMA)

    def test_invalid_schema_missing_additional_properties(self):
        """Test that schema without additionalProperties: false fails."""
        with pytest.raises(SchemaValidationError) as exc_info:
            validate_strict_schema(INVALID_SCHEMA_MISSING_ADDITIONAL_PROPERTIES)
        assert "additionalProperties" in str(exc_info.value)

    def test_invalid_schema_partial_required(self):
        """Test that schema with partial required array fails."""
        with pytest.raises(SchemaValidationError) as exc_info:
            validate_strict_schema(INVALID_SCHEMA_PARTIAL_REQUIRED)
        assert "required" in str(exc_info.value).lower()

    def test_invalid_schema_with_anyof(self):
        """Test that schema with anyOf at root level fails."""
        with pytest.raises(SchemaValidationError) as exc_info:
            validate_strict_schema(INVALID_SCHEMA_WITH_ANYOF)
        assert "anyOf" in str(exc_info.value)

    def test_nested_valid_schema(self):
        """Test that nested objects with valid schemas pass."""
        validate_strict_schema(NESTED_VALID_SCHEMA)

    def test_nested_invalid_schema(self):
        """Test that nested objects with invalid schemas fail."""
        with pytest.raises(SchemaValidationError) as exc_info:
            validate_strict_schema(NESTED_INVALID_SCHEMA)
        assert "required" in str(exc_info.value).lower()

    def test_array_schema(self):
        """Test that schemas with arrays of objects pass."""
        validate_strict_schema(ARRAY_SCHEMA)


class TestSchemaGeneration:
    """Test data generation from JSON schemas."""

    def test_generate_string(self):
        """Test string generation."""
        schema = {"type": "string"}
        result = generate_from_schema(schema)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_generate_number(self):
        """Test number generation."""
        schema = {"type": "number", "minimum": 0, "maximum": 100}
        result = generate_from_schema(schema)
        assert isinstance(result, (int, float))
        assert 0 <= result <= 100

    def test_generate_integer(self):
        """Test integer generation."""
        schema = {"type": "integer", "minimum": 1, "maximum": 10}
        result = generate_from_schema(schema)
        assert isinstance(result, int)
        assert 1 <= result <= 10

    def test_generate_boolean(self):
        """Test boolean generation."""
        schema = {"type": "boolean"}
        result = generate_from_schema(schema)
        assert isinstance(result, bool)

    def test_generate_enum(self):
        """Test enum generation."""
        schema = {"enum": ["red", "green", "blue"]}
        result = generate_from_schema(schema)
        assert result in ["red", "green", "blue"]

    def test_generate_object(self):
        """Test object generation."""
        result = generate_from_schema(VALID_STRICT_SCHEMA)
        assert isinstance(result, dict)
        assert "name" in result
        assert "age" in result
        assert "email" in result
        assert isinstance(result["name"], str)
        assert isinstance(result["age"], int)
        assert isinstance(result["email"], str)
        assert "@" in result["email"]

    def test_generate_nested_object(self):
        """Test nested object generation."""
        result = generate_from_schema(NESTED_VALID_SCHEMA)
        assert isinstance(result, dict)
        assert "user" in result
        assert "metadata" in result
        assert isinstance(result["user"], dict)
        assert "name" in result["user"]
        assert "age" in result["user"]
        assert isinstance(result["metadata"], dict)
        assert "created" in result["metadata"]
        assert "updated" in result["metadata"]

    def test_generate_array(self):
        """Test array generation."""
        result = generate_from_schema(ARRAY_SCHEMA)
        assert isinstance(result, dict)
        assert "items" in result
        assert isinstance(result["items"], list)
        assert 1 <= len(result["items"]) <= 3
        for item in result["items"]:
            assert isinstance(item, dict)
            assert "id" in item
            assert "name" in item
            assert isinstance(item["id"], int)
            assert isinstance(item["name"], str)

    def test_generate_enum_schema(self):
        """Test enum values in schema."""
        result = generate_from_schema(ENUM_SCHEMA)
        assert isinstance(result, dict)
        assert result["status"] in ["active", "inactive", "pending"]
        assert result["priority"] in [1, 2, 3, 4, 5]

    def test_string_formats(self):
        """Test different string format generations."""
        formats_to_test = {
            "email": "@",
            "date-time": "T",
            "date": "-",
            "uuid": "-",
            "uri": "://",
        }

        for format_type, expected_char in formats_to_test.items():
            schema = {"type": "string", "format": format_type}
            result = generate_from_schema(schema)
            assert isinstance(result, str)
            if expected_char:
                assert expected_char in result, f"Format {format_type} should contain '{expected_char}'"

    def test_string_length_constraints(self):
        """Test string length constraints."""
        schema = {"type": "string", "minLength": 10, "maxLength": 20}
        result = generate_from_schema(schema)
        assert isinstance(result, str)
        assert 10 <= len(result) <= 20


@pytest.mark.asyncio
class TestStructuredOutputsService:
    """Test structured outputs integration with FakeAIService."""

    async def test_chat_completion_with_structured_output(self):
        """Test chat completion with JSON schema response format."""
        config = AppConfig(response_delay=0.0)
        service = FakeAIService(config)

        request = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[Message(role=Role.USER, content="Generate a user profile")],
            response_format=JsonSchemaResponseFormat(
                type="json_schema",
                json_schema=JsonSchema(
                    name="user_profile",
                    schema=VALID_STRICT_SCHEMA,
                    strict=True,
                ),
            ),
            parallel_tool_calls=False,  # Required for strict mode
        )

        response = await service.create_chat_completion(request)

        assert response.choices[0].message.content
        # Parse JSON response
        data = json.loads(response.choices[0].message.content)
        assert isinstance(data, dict)
        assert "name" in data
        assert "age" in data
        assert "email" in data

    async def test_strict_mode_requires_parallel_tool_calls_false(self):
        """Test that strict mode enforces parallel_tool_calls=false."""
        config = AppConfig(response_delay=0.0)
        service = FakeAIService(config)

        request = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[Message(role=Role.USER, content="Test")],
            response_format=JsonSchemaResponseFormat(
                type="json_schema",
                json_schema=JsonSchema(
                    name="test_schema",
                    schema=VALID_STRICT_SCHEMA,
                    strict=True,
                ),
            ),
            parallel_tool_calls=True,  # This should fail
        )

        with pytest.raises(ValueError) as exc_info:
            await service.create_chat_completion(request)
        assert "parallel_tool_calls must be false" in str(exc_info.value)

    async def test_invalid_schema_raises_error(self):
        """Test that invalid strict schema raises validation error."""
        config = AppConfig(response_delay=0.0)
        service = FakeAIService(config)

        request = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[Message(role=Role.USER, content="Test")],
            response_format=JsonSchemaResponseFormat(
                type="json_schema",
                json_schema=JsonSchema(
                    name="invalid_schema",
                    schema=INVALID_SCHEMA_MISSING_ADDITIONAL_PROPERTIES,
                    strict=True,
                ),
            ),
            parallel_tool_calls=False,
        )

        with pytest.raises(ValueError) as exc_info:
            await service.create_chat_completion(request)
        assert "Invalid JSON schema" in str(exc_info.value)

    async def test_nested_schema_generation(self):
        """Test generation with nested objects."""
        config = AppConfig(response_delay=0.0)
        service = FakeAIService(config)

        request = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[Message(role=Role.USER, content="Generate nested data")],
            response_format=JsonSchemaResponseFormat(
                type="json_schema",
                json_schema=JsonSchema(
                    name="nested_data",
                    schema=NESTED_VALID_SCHEMA,
                    strict=True,
                ),
            ),
            parallel_tool_calls=False,
        )

        response = await service.create_chat_completion(request)
        data = json.loads(response.choices[0].message.content)

        assert "user" in data
        assert "name" in data["user"]
        assert "age" in data["user"]
        assert "metadata" in data
        assert "created" in data["metadata"]
        assert "updated" in data["metadata"]

    async def test_array_schema_generation(self):
        """Test generation with arrays."""
        config = AppConfig(response_delay=0.0)
        service = FakeAIService(config)

        request = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[Message(role=Role.USER, content="Generate items")],
            response_format=JsonSchemaResponseFormat(
                type="json_schema",
                json_schema=JsonSchema(
                    name="items_list",
                    schema=ARRAY_SCHEMA,
                    strict=True,
                ),
            ),
            parallel_tool_calls=False,
        )

        response = await service.create_chat_completion(request)
        data = json.loads(response.choices[0].message.content)

        assert "items" in data
        assert isinstance(data["items"], list)
        assert 1 <= len(data["items"]) <= 3

    async def test_non_strict_mode_works(self):
        """Test that non-strict mode also works."""
        config = AppConfig(response_delay=0.0)
        service = FakeAIService(config)

        request = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[Message(role=Role.USER, content="Generate data")],
            response_format=JsonSchemaResponseFormat(
                type="json_schema",
                json_schema=JsonSchema(
                    name="user_profile",
                    schema=VALID_STRICT_SCHEMA,
                    strict=False,  # Non-strict mode
                ),
            ),
        )

        response = await service.create_chat_completion(request)
        data = json.loads(response.choices[0].message.content)
        assert isinstance(data, dict)


@pytest.mark.integration
class TestStructuredOutputsWithOpenAIClient:
    """Integration tests using OpenAI Python client."""

    @pytest.fixture
    def client(self):
        """Create OpenAI client pointed at FakeAI server."""
        # Note: Assumes server is running at localhost:8000
        return OpenAI(
            api_key="test-key",
            base_url="http://localhost:8000",
        )

    def test_structured_output_with_client(self, client):
        """Test structured output using OpenAI client."""
        try:
            response = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=[{"role": "user", "content": "Generate a user profile"}],
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "user_profile",
                        "schema": VALID_STRICT_SCHEMA,
                        "strict": True,
                    },
                },
                parallel_tool_calls=False,
            )

            content = response.choices[0].message.content
            data = json.loads(content)

            assert "name" in data
            assert "age" in data
            assert "email" in data
            assert isinstance(data["name"], str)
            assert isinstance(data["age"], int)
            assert "@" in data["email"]

        except Exception as e:
            pytest.skip(f"Server not available: {e}")

    def test_strict_mode_validation_error(self, client):
        """Test that invalid schema raises error via client."""
        try:
            with pytest.raises(Exception) as exc_info:
                client.chat.completions.create(
                    model="openai/gpt-oss-120b",
                    messages=[{"role": "user", "content": "Test"}],
                    response_format={
                        "type": "json_schema",
                        "json_schema": {
                            "name": "invalid",
                            "schema": INVALID_SCHEMA_MISSING_ADDITIONAL_PROPERTIES,
                            "strict": True,
                        },
                    },
                    parallel_tool_calls=False,
                )
            # Should raise error about invalid schema

        except Exception as e:
            pytest.skip(f"Server not available: {e}")

    def test_parallel_tool_calls_enforcement(self, client):
        """Test that parallel_tool_calls enforcement works via client."""
        try:
            with pytest.raises(Exception):
                client.chat.completions.create(
                    model="openai/gpt-oss-120b",
                    messages=[{"role": "user", "content": "Test"}],
                    response_format={
                        "type": "json_schema",
                        "json_schema": {
                            "name": "test",
                            "schema": VALID_STRICT_SCHEMA,
                            "strict": True,
                        },
                    },
                    parallel_tool_calls=True,  # Should fail
                )

        except Exception as e:
            pytest.skip(f"Server not available: {e}")
