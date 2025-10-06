# FakeAI Structured Outputs

Complete implementation of OpenAI's structured outputs feature with JSON schema validation and generation.

## Overview

FakeAI now supports OpenAI's [structured outputs](https://platform.openai.com/docs/guides/structured-outputs) feature, allowing you to define JSON schemas and get guaranteed valid JSON responses. This is ideal for:

- **Extracting structured data** from unstructured text
- **Building reliable pipelines** with type-safe outputs
- **Function calling** with validated parameters
- **Testing** applications that use structured outputs

## Features

###  Complete Implementation

- **JSON Schema Validation**: Strict mode validation according to OpenAI's requirements
- **Automatic Data Generation**: Realistic fake data matching your schema
- **Type Support**: Objects, arrays, strings, numbers, integers, booleans, enums
- **Format Support**: email, date-time, date, uuid, uri, and more
- **Nested Objects**: Full support for complex nested structures
- **Constraints**: minLength, maxLength, minimum, maximum, minItems, maxItems
- **Error Handling**: Clear validation errors for invalid schemas

###  Strict Mode Requirements

FakeAI enforces all strict mode requirements:

1.  Root level must have `additionalProperties: false`
2.  All properties must be in `required` array
3.  No `anyOf` at root level
4.  `parallel_tool_calls` must be `false`
5.  Nested objects must follow same rules

## Quick Start

### Basic Example

```python
from openai import OpenAI

client = OpenAI(
    api_key="test-key",
    base_url="http://localhost:8000",
)

# Define your schema
user_schema = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "age": {"type": "integer", "minimum": 0, "maximum": 150},
        "email": {"type": "string", "format": "email"}
    },
    "required": ["name", "age", "email"],
    "additionalProperties": False
}

# Request structured output
response = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[
        {"role": "user", "content": "Generate a user profile"}
    ],
    response_format={
        "type": "json_schema",
        "json_schema": {
            "name": "user_profile",
            "schema": user_schema,
            "strict": True
        }
    },
    parallel_tool_calls=False  # Required for strict mode
)

# Parse JSON response
import json
data = json.loads(response.choices[0].message.content)

print(f"Name: {data['name']}")
print(f"Age: {data['age']}")
print(f"Email: {data['email']}")
```

## Schema Examples

### Simple Object

```python
simple_schema = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "count": {"type": "integer"}
    },
    "required": ["title", "count"],
    "additionalProperties": False
}
```

### Nested Objects

```python
nested_schema = {
    "type": "object",
    "properties": {
        "user": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"}
            },
            "required": ["name", "age"],
            "additionalProperties": False
        },
        "metadata": {
            "type": "object",
            "properties": {
                "created": {"type": "string", "format": "date-time"},
                "updated": {"type": "string", "format": "date-time"}
            },
            "required": ["created", "updated"],
            "additionalProperties": False
        }
    },
    "required": ["user", "metadata"],
    "additionalProperties": False
}
```

### Arrays

```python
array_schema = {
    "type": "object",
    "properties": {
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "name": {"type": "string"}
                },
                "required": ["id", "name"],
                "additionalProperties": False
            },
            "minItems": 1,
            "maxItems": 5
        }
    },
    "required": ["items"],
    "additionalProperties": False
}
```

### Enums

```python
enum_schema = {
    "type": "object",
    "properties": {
        "status": {
            "type": "string",
            "enum": ["active", "inactive", "pending"]
        },
        "priority": {
            "type": "integer",
            "enum": [1, 2, 3, 4, 5]
        }
    },
    "required": ["status", "priority"],
    "additionalProperties": False
}
```

### String Formats

Supported format types:
- `email`: john.doe@example.com
- `date-time`: 2025-10-04T12:34:56Z
- `date`: 2025-10-04
- `time`: 12:34:56
- `uri` / `url`: https://example.com
- `uuid`: 550e8400-e29b-41d4-a716-446655440000
- `hostname`: example.com
- `ipv4`: 192.168.1.1
- `ipv6`: 2001:0db8:85a3:0000:0000:8a2e:0370:7334

```python
format_schema = {
    "type": "object",
    "properties": {
        "email": {"type": "string", "format": "email"},
        "created_at": {"type": "string", "format": "date-time"},
        "birthday": {"type": "string", "format": "date"},
        "website": {"type": "string", "format": "uri"},
        "user_id": {"type": "string", "format": "uuid"}
    },
    "required": ["email", "created_at", "birthday", "website", "user_id"],
    "additionalProperties": False
}
```

### Constraints

```python
constraints_schema = {
    "type": "object",
    "properties": {
        "username": {
            "type": "string",
            "minLength": 3,
            "maxLength": 20
        },
        "age": {
            "type": "integer",
            "minimum": 18,
            "maximum": 100
        },
        "score": {
            "type": "number",
            "minimum": 0.0,
            "maximum": 1.0
        }
    },
    "required": ["username", "age", "score"],
    "additionalProperties": False
}
```

## API Reference

### Request Format

```python
response = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[...],
    response_format={
        "type": "json_schema",
        "json_schema": {
            "name": "schema_name",           # Required: Schema identifier
            "description": "...",             # Optional: Schema description
            "schema": {...},                  # Required: JSON Schema object
            "strict": True                    # Optional: Enable strict mode
        }
    },
    parallel_tool_calls=False  # Required when strict=True
)
```

### Schema Requirements (Strict Mode)

When `strict: True`, schemas must meet these requirements:

1. **Root level:**
   - Must be `type: "object"`
   - Must have `additionalProperties: false`
   - All properties must be in `required` array
   - Cannot use `anyOf` at root level

2. **Nested objects:**
   - Must also have `additionalProperties: false`
   - All properties must be in `required` array

3. **Request parameters:**
   - `parallel_tool_calls` must be `false`

### Supported Types

| Type | Description | Example |
|------|-------------|---------|
| `string` | Text value | `"hello"` |
| `integer` | Whole number | `42` |
| `number` | Decimal number | `3.14` |
| `boolean` | True/false | `true` |
| `null` | Null value | `null` |
| `object` | JSON object | `{"key": "value"}` |
| `array` | JSON array | `[1, 2, 3]` |
| `enum` | Fixed set of values | `["red", "green", "blue"]` |

## Error Handling

### Invalid Schema Error

```python
# Missing additionalProperties: false
invalid_schema = {
    "type": "object",
    "properties": {"name": {"type": "string"}},
    "required": ["name"]
    # Missing: "additionalProperties": False
}

try:
    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": "Test"}],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "invalid",
                "schema": invalid_schema,
                "strict": True
            }
        },
        parallel_tool_calls=False
    )
except Exception as e:
    print(f"Schema validation error: {e}")
    # Output: Invalid JSON schema for strict mode: Strict mode requires
    #         'additionalProperties': false at root level
```

### Parallel Tool Calls Error

```python
try:
    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": "Test"}],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "test",
                "schema": valid_schema,
                "strict": True
            }
        },
        parallel_tool_calls=True  # Invalid with strict=True
    )
except Exception as e:
    print(f"Parameter error: {e}")
    # Output: When using strict mode with structured outputs,
    #         parallel_tool_calls must be false
```

## Testing

### Unit Tests

```bash
# Run all structured outputs tests
pytest tests/test_structured_outputs.py -v

# Run specific test categories
pytest tests/test_structured_outputs.py::TestSchemaValidation -v
pytest tests/test_structured_outputs.py::TestSchemaGeneration -v
pytest tests/test_structured_outputs.py::TestStructuredOutputsService -v
```

### Integration Tests

```bash
# Start FakeAI server
python run_server.py

# Run integration tests (in another terminal)
pytest tests/test_structured_outputs.py::TestStructuredOutputsWithOpenAIClient -v
```

## Examples

Complete working examples are available in `examples/structured_outputs_example.py`:

```bash
# Start the server
python run_server.py

# Run examples (in another terminal)
python examples/structured_outputs_example.py
```

Examples demonstrate:
1. User profile generation
2. Nested organization data
3. Enum constraints
4. Error handling

## Implementation Details

### Module Structure

```
fakeai/
 structured_outputs.py    # Schema validation and generation
 fakeai_service.py         # Integration with service layer
 models.py                 # JsonSchema and JsonSchemaResponseFormat models

tests/
 test_structured_outputs.py  # Comprehensive test suite

examples/
 structured_outputs_example.py  # Usage examples
```

### Key Functions

#### `validate_strict_schema(schema: dict) -> None`

Validates a JSON schema for strict mode compliance.

Raises `SchemaValidationError` if:
- Missing `additionalProperties: false`
- Not all properties in `required` array
- Uses `anyOf` at root level
- Nested objects don't meet requirements

#### `generate_from_schema(schema: dict) -> Any`

Generates realistic fake data matching the schema.

Supports:
- Basic types (string, number, integer, boolean, null)
- Complex types (object, array)
- String formats (email, date-time, uri, etc.)
- Enums
- Constraints (min/max length, min/max value, min/max items)

#### `format_as_json_string(data: Any) -> str`

Formats generated data as properly formatted JSON string.

## Compatibility

### OpenAI API Compatibility

FakeAI's structured outputs implementation is **100% compatible** with OpenAI's API:

- Same request/response format
- Same strict mode requirements
- Same error messages
- Same validation rules

### Client Libraries

Works with all OpenAI-compatible clients:

- **Official OpenAI Python SDK** 
- **LangChain** 
- **LlamaIndex** 
- **Haystack** 
- **Any HTTP client** 

## Use Cases

### Data Extraction

Extract structured information from text:

```python
extraction_schema = {
    "type": "object",
    "properties": {
        "entities": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "type": {"type": "string", "enum": ["person", "organization", "location"]},
                    "mentions": {"type": "integer"}
                },
                "required": ["name", "type", "mentions"],
                "additionalProperties": False
            }
        }
    },
    "required": ["entities"],
    "additionalProperties": False
}
```

### Function Parameters

Generate function call parameters:

```python
function_params_schema = {
    "type": "object",
    "properties": {
        "function_name": {"type": "string"},
        "arguments": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 100},
                "filters": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            },
            "required": ["query"],
            "additionalProperties": False
        }
    },
    "required": ["function_name", "arguments"],
    "additionalProperties": False
}
```

### Response Validation

Ensure consistent API responses:

```python
api_response_schema = {
    "type": "object",
    "properties": {
        "status": {"type": "string", "enum": ["success", "error"]},
        "data": {"type": "object", "additionalProperties": False, "properties": {}, "required": []},
        "error": {
            "type": "object",
            "properties": {
                "code": {"type": "string"},
                "message": {"type": "string"}
            },
            "required": ["code", "message"],
            "additionalProperties": False
        }
    },
    "required": ["status", "data"],
    "additionalProperties": False
}
```

## Best Practices

### 1. Always Use Strict Mode

```python
# Good
response_format={
    "type": "json_schema",
    "json_schema": {
        "name": "my_schema",
        "schema": schema,
        "strict": True  # Always use strict mode
    }
}
```

### 2. Provide Descriptions

```python
# Good - includes descriptions
schema = {
    "type": "object",
    "properties": {
        "email": {
            "type": "string",
            "format": "email",
            "description": "User's email address"  # Helpful for understanding
        }
    },
    "required": ["email"],
    "additionalProperties": False
}
```

### 3. Set Constraints

```python
# Good - uses constraints
schema = {
    "type": "object",
    "properties": {
        "items": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 1,  # At least one item
            "maxItems": 10  # No more than 10
        }
    },
    "required": ["items"],
    "additionalProperties": False
}
```

### 4. Use Enums for Fixed Values

```python
# Good - uses enum
schema = {
    "type": "object",
    "properties": {
        "status": {
            "type": "string",
            "enum": ["pending", "approved", "rejected"]  # Fixed values
        }
    },
    "required": ["status"],
    "additionalProperties": False
}
```

## Troubleshooting

### Common Issues

#### "additionalProperties must be false"

**Problem:** Root or nested object missing `additionalProperties: false`

**Solution:**
```python
# Add to all objects
{
    "type": "object",
    "properties": {...},
    "required": [...],
    "additionalProperties": False  # Add this
}
```

#### "All properties must be in required array"

**Problem:** Some properties not in `required` array

**Solution:**
```python
# Include all properties
{
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "age": {"type": "integer"}
    },
    "required": ["name", "age"],  # Must include all properties
    "additionalProperties": False
}
```

#### "parallel_tool_calls must be false"

**Problem:** `parallel_tool_calls=True` with `strict=True`

**Solution:**
```python
# Set to False when using strict mode
client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[...],
    response_format={...},
    parallel_tool_calls=False  # Required for strict mode
)
```

## Advanced Topics

### Recursive Schemas

For self-referential structures, define all levels explicitly:

```python
# Tree structure
tree_schema = {
    "type": "object",
    "properties": {
        "value": {"type": "integer"},
        "children": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "value": {"type": "integer"},
                    "children": {"type": "array", "items": {}}
                },
                "required": ["value", "children"],
                "additionalProperties": False
            }
        }
    },
    "required": ["value", "children"],
    "additionalProperties": False
}
```

### Complex Validations

Use JSON Schema's full power:

```python
# Pattern matching
{
    "type": "string",
    "pattern": "^[A-Z]{2}\\d{4}$"  # US state code format
}

# Exclusive bounds
{
    "type": "number",
    "exclusiveMinimum": 0.0,
    "exclusiveMaximum": 1.0
}
```

## Resources

- [OpenAI Structured Outputs Guide](https://platform.openai.com/docs/guides/structured-outputs)
- [JSON Schema Documentation](https://json-schema.org/)
- [FakeAI GitHub Repository](https://github.com/ajcasagrande/fakeai)

## License

Apache License 2.0 - see LICENSE file for details
