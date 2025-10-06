"""
Tests for tool calling decision engine and argument generation.
"""

#  SPDX-License-Identifier: Apache-2.0

import pytest

from fakeai.models import Message, Role, Tool, ToolChoice
from fakeai.tool_calling import (
    ToolCallGenerator,
    ToolDecisionEngine,
    extract_text_content,
)


# Test extract_text_content helper function
def test_extract_text_content_string():
    """Test extracting text from string content."""
    content = "Hello, world!"
    result = extract_text_content(content)
    assert result == "Hello, world!"


def test_extract_text_content_list():
    """Test extracting text from list of content parts."""
    content = [
        {"type": "text", "text": "Hello"},
        {"type": "image_url", "image_url": {"url": "https://example.com/image.png"}},
        {"type": "text", "text": "world"},
    ]
    result = extract_text_content(content)
    assert result == "Hello world"


def test_extract_text_content_none():
    """Test extracting text from None content."""
    result = extract_text_content(None)
    assert result == ""


# ToolDecisionEngine Tests


@pytest.fixture
def tool_engine():
    """Create a ToolDecisionEngine instance."""
    return ToolDecisionEngine()


@pytest.fixture
def sample_tools():
    """Create sample tool definitions."""
    return [
        Tool(
            type="function",
            function={
                "name": "get_weather",
                "description": "Get the current weather in a location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "City and state, e.g. San Francisco, CA",
                        },
                        "unit": {
                            "type": "string",
                            "enum": ["celsius", "fahrenheit"],
                        },
                    },
                    "required": ["location"],
                },
            },
        ),
        Tool(
            type="function",
            function={
                "name": "search_web",
                "description": "Search the web for information",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query",
                        }
                    },
                    "required": ["query"],
                },
            },
        ),
        Tool(
            type="function",
            function={
                "name": "calculate",
                "description": "Perform mathematical calculations",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expression": {
                            "type": "string",
                            "description": "The mathematical expression to evaluate",
                        }
                    },
                    "required": ["expression"],
                },
            },
        ),
    ]


def test_tool_decision_no_tools(tool_engine):
    """Test that no tools are called when none are provided."""
    messages = [Message(role=Role.USER, content="Hello, world!")]
    should_call, tools = tool_engine.should_call_tools(messages, None, "auto", True)
    assert should_call is False
    assert tools == []


def test_tool_decision_none_mode(tool_engine, sample_tools):
    """Test that tools are never called when tool_choice is 'none'."""
    messages = [Message(role=Role.USER, content="What's the weather in San Francisco?")]
    should_call, tools = tool_engine.should_call_tools(
        messages, sample_tools, "none", True
    )
    assert should_call is False
    assert tools == []


def test_tool_decision_required_mode(tool_engine, sample_tools):
    """Test that tools are always called when tool_choice is 'required'."""
    messages = [Message(role=Role.USER, content="Hello")]
    should_call, tools = tool_engine.should_call_tools(
        messages, sample_tools, "required", True
    )
    assert should_call is True
    assert len(tools) >= 1


def test_tool_decision_specific_tool(tool_engine, sample_tools):
    """Test forcing a specific tool to be called."""
    messages = [Message(role=Role.USER, content="Calculate something")]
    tool_choice = ToolChoice(
        type="function",
        function={"name": "calculate"},
    )
    should_call, tools = tool_engine.should_call_tools(
        messages, sample_tools, tool_choice, True
    )
    assert should_call is True
    assert len(tools) == 1
    assert tools[0].function["name"] == "calculate"


def test_tool_decision_auto_relevant(tool_engine, sample_tools):
    """Test auto mode with relevant keywords."""
    messages = [Message(role=Role.USER, content="What's the weather in New York?")]
    should_call, tools = tool_engine.should_call_tools(
        messages, sample_tools, "auto", True
    )
    # Should have high chance of calling weather tool
    if should_call:
        assert any(t.function["name"] == "get_weather" for t in tools)


def test_tool_decision_auto_search(tool_engine, sample_tools):
    """Test auto mode with search-related query."""
    messages = [Message(role=Role.USER, content="Search for information about Python")]
    should_call, tools = tool_engine.should_call_tools(
        messages, sample_tools, "auto", True
    )
    # Should have chance of calling search tool
    if should_call:
        assert any(t.function["name"] == "search_web" for t in tools)


def test_tool_relevance_scoring(tool_engine):
    """Test tool relevance calculation."""
    message_text = "what is the weather like in london today"

    weather_tool = Tool(
        type="function",
        function={
            "name": "get_weather",
            "description": "Get current weather",
            "parameters": {},
        },
    )

    score = tool_engine._calculate_tool_relevance(message_text, weather_tool)
    assert score > 0  # Should have positive relevance


def test_parallel_tool_calls(tool_engine, sample_tools):
    """Test that parallel tool calls are limited."""
    messages = [
        Message(
            role=Role.USER,
            content="Search the web for weather information and calculate the temperature",
        )
    ]
    should_call, tools = tool_engine.should_call_tools(
        messages, sample_tools, "required", parallel_tool_calls=True
    )
    assert should_call is True
    # Should select multiple relevant tools
    assert len(tools) <= 3  # Max 3 tools for parallel


def test_sequential_tool_calls(tool_engine, sample_tools):
    """Test that sequential mode only selects one tool."""
    messages = [
        Message(
            role=Role.USER,
            content="Search the web for weather information",
        )
    ]
    should_call, tools = tool_engine.should_call_tools(
        messages, sample_tools, "required", parallel_tool_calls=False
    )
    assert should_call is True
    assert len(tools) == 1  # Only one tool for sequential


# ToolCallGenerator Tests


@pytest.fixture
def tool_generator():
    """Create a ToolCallGenerator instance."""
    return ToolCallGenerator()


def test_generate_tool_calls(tool_generator, sample_tools):
    """Test generating tool calls."""
    messages = [Message(role=Role.USER, content="What's the weather in Paris?")]
    tool_calls = tool_generator.generate_tool_calls(
        [sample_tools[0]], messages, parallel=True
    )

    assert len(tool_calls) == 1
    assert tool_calls[0].id.startswith("call_")
    assert tool_calls[0].type == "function"
    assert tool_calls[0].function.name == "get_weather"
    # Arguments should be valid JSON
    import json

    args = json.loads(tool_calls[0].function.arguments)
    assert "location" in args


def test_generate_arguments_location(tool_generator):
    """Test generating arguments with location extraction."""
    messages = [Message(role=Role.USER, content="What's the weather in Tokyo?")]
    function_def = {
        "name": "get_weather",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "City name"},
                "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
            },
            "required": ["location"],
        },
    }

    args = tool_generator.generate_arguments(function_def, messages)

    assert "location" in args
    # Should extract Tokyo or generate a realistic city
    assert isinstance(args["location"], str)
    if "unit" in args:
        assert args["unit"] in ["celsius", "fahrenheit"]


def test_generate_arguments_query(tool_generator):
    """Test generating arguments with query extraction."""
    messages = [
        Message(role=Role.USER, content='Search for "Python programming tutorial"')
    ]
    function_def = {
        "name": "search",
        "parameters": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "Search query"}},
            "required": ["query"],
        },
    }

    args = tool_generator.generate_arguments(function_def, messages)

    assert "query" in args
    assert isinstance(args["query"], str)


def test_generate_string_values(tool_generator):
    """Test generating various string value types."""
    messages = [Message(role=Role.USER, content="Test message")]

    # Location
    location = tool_generator._generate_string_value("location", "city name")
    assert isinstance(location, str)

    # Email
    email = tool_generator._generate_string_value("email", "email address")
    assert "@" in email

    # Name
    name = tool_generator._generate_string_value("user_name", "person name")
    assert isinstance(name, str)

    # URL
    url = tool_generator._generate_string_value("website_url", "website address")
    assert url.startswith("http")


def test_generate_number_values(tool_generator):
    """Test generating number values."""
    # Temperature
    temp = tool_generator._generate_number_value(
        "temperature", "temp in celsius", "number"
    )
    assert isinstance(temp, (int, float))
    assert -50 <= temp <= 50

    # Limit/count
    limit = tool_generator._generate_number_value("limit", "max results", "integer")
    assert isinstance(limit, int)
    assert 1 <= limit <= 100

    # Age
    age = tool_generator._generate_number_value("age", "person age", "integer")
    assert isinstance(age, int)
    assert 18 <= age <= 80


def test_extract_location_from_context(tool_generator):
    """Test extracting location from message context."""
    context = "What's the weather in San Francisco today?"

    value = tool_generator._extract_value_from_context(
        "location", "string", "city name", context
    )

    # Should extract San Francisco
    assert value == "San Francisco"


def test_extract_number_from_context(tool_generator):
    """Test extracting numbers from context."""
    context = "Give me 42 results"

    value = tool_generator._extract_value_from_context(
        "limit", "integer", "max results", context
    )

    assert value == 42


def test_extract_email_from_context(tool_generator):
    """Test extracting email from context."""
    context = "Send an email to user@example.com"

    value = tool_generator._extract_value_from_context(
        "email", "string", "email address", context
    )

    assert value == "user@example.com"


def test_generate_array_parameter(tool_generator):
    """Test generating array parameters."""
    messages = [Message(role=Role.USER, content="Test")]
    param_schema = {
        "type": "array",
        "items": {"type": "string"},
    }

    value = tool_generator._generate_parameter_value("tags", param_schema, "")

    assert isinstance(value, list)
    assert len(value) >= 1
    assert all(isinstance(item, str) for item in value)


def test_generate_object_parameter(tool_generator):
    """Test generating object parameters."""
    messages = [Message(role=Role.USER, content="Test")]
    param_schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"},
        },
    }

    value = tool_generator._generate_parameter_value("user", param_schema, "")

    assert isinstance(value, dict)
    assert "name" in value
    assert "age" in value


def test_generate_enum_parameter(tool_generator):
    """Test generating enum parameters."""
    messages = [Message(role=Role.USER, content="Test")]
    param_schema = {
        "type": "string",
        "enum": ["option1", "option2", "option3"],
    }

    value = tool_generator._generate_parameter_value("choice", param_schema, "")

    assert value in ["option1", "option2", "option3"]


def test_parallel_tool_call_generation(tool_generator, sample_tools):
    """Test generating multiple tool calls for parallel execution."""
    messages = [
        Message(
            role=Role.USER,
            content="Search for weather and calculate the average temperature",
        )
    ]

    # Select weather and calculate tools
    tools_to_call = [sample_tools[0], sample_tools[2]]

    tool_calls = tool_generator.generate_tool_calls(
        tools_to_call, messages, parallel=True
    )

    assert len(tool_calls) == 2
    assert all(tc.id.startswith("call_") for tc in tool_calls)
    assert all(tc.type == "function" for tc in tool_calls)

    # Each should have unique ID
    ids = [tc.id for tc in tool_calls]
    assert len(set(ids)) == len(ids)


def test_generate_realistic_weather_call(tool_generator):
    """Test generating realistic weather tool call."""
    messages = [
        Message(role=Role.USER, content="What's the temperature in London right now?")
    ]

    function_def = {
        "name": "get_weather",
        "description": "Get current weather information",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "City name",
                },
                "unit": {
                    "type": "string",
                    "enum": ["celsius", "fahrenheit"],
                    "description": "Temperature unit",
                },
            },
            "required": ["location"],
        },
    }

    args = tool_generator.generate_arguments(function_def, messages)

    # Should extract London
    assert args["location"] == "London"
    # Unit should be enum value
    if "unit" in args:
        assert args["unit"] in ["celsius", "fahrenheit"]


def test_generate_realistic_search_call(tool_generator):
    """Test generating realistic search tool call."""
    messages = [
        Message(role=Role.USER, content='Search for "machine learning algorithms"')
    ]

    function_def = {
        "name": "search_web",
        "description": "Search the web",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results",
                },
            },
            "required": ["query"],
        },
    }

    args = tool_generator.generate_arguments(function_def, messages)

    # Should extract the query
    assert "query" in args
    assert (
        "machine learning" in args["query"].lower()
        or "algorithms" in args["query"].lower()
    )
