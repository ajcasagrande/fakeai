#!/usr/bin/env python3
"""
Example demonstrating FakeAI structured outputs with JSON schema validation.

This example shows how to use OpenAI's structured outputs feature with FakeAI,
including strict schema validation and automatic data generation.
"""
#  SPDX-License-Identifier: Apache-2.0

import json
from openai import OpenAI


# Define a strict JSON schema
USER_PROFILE_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {
            "type": "string",
            "description": "The user's full name"
        },
        "age": {
            "type": "integer",
            "description": "The user's age in years",
            "minimum": 0,
            "maximum": 150
        },
        "email": {
            "type": "string",
            "format": "email",
            "description": "The user's email address"
        },
        "occupation": {
            "type": "string",
            "description": "The user's job title or occupation"
        },
        "interests": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of user's interests",
            "minItems": 1,
            "maxItems": 5
        }
    },
    "required": ["name", "age", "email", "occupation", "interests"],
    "additionalProperties": False
}

# Nested schema example
ORGANIZATION_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {
            "type": "string",
            "description": "Organization name"
        },
        "employees": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "name": {"type": "string"},
                    "role": {
                        "type": "string",
                        "enum": ["engineer", "manager", "designer", "analyst"]
                    }
                },
                "required": ["id", "name", "role"],
                "additionalProperties": False
            },
            "minItems": 1,
            "maxItems": 3
        },
        "founded": {
            "type": "string",
            "format": "date",
            "description": "Date organization was founded"
        }
    },
    "required": ["name", "employees", "founded"],
    "additionalProperties": False
}


def example_user_profile():
    """Example: Generate a user profile with structured output."""
    print("=" * 80)
    print("Example 1: User Profile with Structured Output")
    print("=" * 80)

    client = OpenAI(
        api_key="test-key",
        base_url="http://localhost:8000",
    )

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {"role": "user", "content": "Generate a user profile for a software engineer"}
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "user_profile",
                "description": "A user profile with personal information",
                "schema": USER_PROFILE_SCHEMA,
                "strict": True
            }
        },
        parallel_tool_calls=False,  # Required for strict mode
    )

    content = response.choices[0].message.content
    print(f"\nRaw response:\n{content}\n")

    # Parse and pretty-print
    data = json.loads(content)
    print("Parsed data:")
    print(json.dumps(data, indent=2))

    # Validate structure
    print("\nValidation:")
    print(f"  ✓ Name: {data['name']}")
    print(f"  ✓ Age: {data['age']}")
    print(f"  ✓ Email: {data['email']}")
    print(f"  ✓ Occupation: {data['occupation']}")
    print(f"  ✓ Interests: {', '.join(data['interests'])}")

    return data


def example_organization():
    """Example: Generate organization data with nested objects."""
    print("\n" + "=" * 80)
    print("Example 2: Organization with Nested Employee Data")
    print("=" * 80)

    client = OpenAI(
        api_key="test-key",
        base_url="http://localhost:8000",
    )

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {"role": "user", "content": "Generate an organization with employees"}
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "organization",
                "description": "Organization structure with employees",
                "schema": ORGANIZATION_SCHEMA,
                "strict": True
            }
        },
        parallel_tool_calls=False,
    )

    content = response.choices[0].message.content
    data = json.loads(content)

    print("\nOrganization Data:")
    print(json.dumps(data, indent=2))

    print("\nEmployee Details:")
    for i, employee in enumerate(data['employees'], 1):
        print(f"  {i}. {employee['name']} (ID: {employee['id']}) - {employee['role']}")

    return data


def example_enum_constraints():
    """Example: Schema with enum constraints."""
    print("\n" + "=" * 80)
    print("Example 3: Task with Status and Priority Enums")
    print("=" * 80)

    task_schema = {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "status": {
                "type": "string",
                "enum": ["todo", "in_progress", "review", "done"],
                "description": "Current task status"
            },
            "priority": {
                "type": "integer",
                "enum": [1, 2, 3, 4, 5],
                "description": "Priority level (1=lowest, 5=highest)"
            },
            "assignee": {"type": "string"}
        },
        "required": ["title", "status", "priority", "assignee"],
        "additionalProperties": False
    }

    client = OpenAI(
        api_key="test-key",
        base_url="http://localhost:8000",
    )

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": "Create a task"}],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "task",
                "schema": task_schema,
                "strict": True
            }
        },
        parallel_tool_calls=False,
    )

    data = json.loads(response.choices[0].message.content)

    print("\nTask Data:")
    print(json.dumps(data, indent=2))

    print("\nValidation:")
    assert data['status'] in ["todo", "in_progress", "review", "done"]
    assert data['priority'] in [1, 2, 3, 4, 5]
    print("  ✓ Status is valid enum value")
    print("  ✓ Priority is valid enum value")

    return data


def example_error_handling():
    """Example: Demonstrating error handling for invalid schemas."""
    print("\n" + "=" * 80)
    print("Example 4: Error Handling for Invalid Schemas")
    print("=" * 80)

    # Invalid schema (missing additionalProperties: false)
    invalid_schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"}
        },
        "required": ["name", "age"]
        # Missing: "additionalProperties": False
    }

    client = OpenAI(
        api_key="test-key",
        base_url="http://localhost:8000",
    )

    print("\nAttempting to use invalid schema (missing additionalProperties)...")

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
            parallel_tool_calls=False,
        )
        print("ERROR: Should have raised validation error!")
    except Exception as e:
        print(f"✓ Caught expected validation error: {e}")

    # Invalid: parallel_tool_calls=True with strict mode
    print("\nAttempting strict mode with parallel_tool_calls=True...")

    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[{"role": "user", "content": "Test"}],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "test",
                    "schema": USER_PROFILE_SCHEMA,
                    "strict": True
                }
            },
            parallel_tool_calls=True,  # Invalid with strict=True
        )
        print("ERROR: Should have raised error!")
    except Exception as e:
        print(f"✓ Caught expected error: {e}")


def main():
    """Run all examples."""
    print("\n" + "=" * 80)
    print("FakeAI Structured Outputs Examples")
    print("=" * 80)
    print("\nThese examples demonstrate OpenAI's structured outputs feature")
    print("with JSON schema validation and automatic data generation.")
    print("\nMake sure the FakeAI server is running:")
    print("  python run_server.py")
    print()

    try:
        example_user_profile()
        example_organization()
        example_enum_constraints()
        example_error_handling()

        print("\n" + "=" * 80)
        print("All examples completed successfully!")
        print("=" * 80)

    except Exception as e:
        print(f"\nError: {e}")
        print("\nMake sure the FakeAI server is running at http://localhost:8000")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
