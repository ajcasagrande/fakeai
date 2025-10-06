# Tool Calling Guide

This guide explains how to use tool calling (function calling) in FakeAI.

## Table of Contents

- [Overview](#overview)
- [Tool Definition](#tool-definition)
- [Request Format](#request-format)
- [Response Format](#response-format)
- [Tool Choice Control](#tool-choice-control)
- [Parallel vs Sequential Execution](#parallel-vs-sequential-execution)
- [Streaming Tool Calls](#streaming-tool-calls)
- [Complete Examples](#complete-examples)
- [Best Practices](#best-practices)

---

## Overview

Tool calling (also known as function calling) allows the model to intelligently decide when to call external tools or functions to help complete a task. This is useful for:

- Retrieving real-time data (weather, stock prices, etc.)
- Performing calculations
- Querying databases
- Calling external APIs
- Executing code
- Any programmatic operation

The flow is:
1. You provide tool definitions in your request
2. The model decides if and which tools to call
3. You receive tool call requests in the response
4. You execute the tools with the provided arguments
5. You send the results back to continue the conversation

---

## Tool Definition

Tools are defined using JSON Schema to specify their parameters.

### Schema

```python
{
  "type": "function",
  "function": {
    "name": "function_name",
    "description": "What this function does",
    "parameters": {
      "type": "object",
      "properties": {
        "param1": {
          "type": "string",
          "description": "Description of param1"
        },
        "param2": {
          "type": "number",
          "description": "Description of param2"
        }
      },
      "required": ["param1"]
    }
  }
}
```

### Example: Weather Tool

```python
weather_tool = {
    "type": "function",
    "function": {
        "name": "get_current_weather",
        "description": "Get the current weather in a given location",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "The city and state, e.g. San Francisco, CA"
                },
                "unit": {
                    "type": "string",
                    "enum": ["celsius", "fahrenheit"],
                    "description": "The temperature unit"
                }
            },
            "required": ["location"]
        }
    }
}
```

### Example: Database Query Tool

```python
database_tool = {
    "type": "function",
    "function": {
        "name": "query_database",
        "description": "Execute a SQL query on the database",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "SQL query to execute"
                },
                "database": {
                    "type": "string",
                    "description": "Database name",
                    "enum": ["users", "products", "orders"]
                }
            },
            "required": ["query", "database"]
        }
    }
}
```

### Example: Calculator Tool

```python
calculator_tool = {
    "type": "function",
    "function": {
        "name": "calculate",
        "description": "Perform mathematical calculations",
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Mathematical expression to evaluate"
                }
            },
            "required": ["expression"]
        }
    }
}
```

---

## Request Format

Include tools in your chat completion request:

```python
from openai import OpenAI

client = OpenAI(
    api_key="sk-fakeai-1234567890abcdef",
    base_url="http://localhost:8000/v1"
)

response = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[
        {"role": "user", "content": "What's the weather in Boston?"}
    ],
    tools=[weather_tool],
    tool_choice="auto"  # Let model decide
)
```

---

## Response Format

When the model decides to call a tool, the response includes tool calls:

### Non-Streaming Response

```json
{
  "id": "chatcmpl-abc123",
  "object": "chat.completion",
  "created": 1234567890,
  "model": "openai/gpt-oss-120b",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": null,
        "tool_calls": [
          {
            "id": "call_abc123",
            "type": "function",
            "function": {
              "name": "get_current_weather",
              "arguments": "{\"location\": \"Boston, MA\", \"unit\": \"fahrenheit\"}"
            }
          }
        ]
      },
      "finish_reason": "tool_calls"
    }
  ],
  "usage": {...}
}
```

### Accessing Tool Calls

```python
response = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[{"role": "user", "content": "What's the weather in Boston?"}],
    tools=[weather_tool]
)

# Check if model called a tool
if response.choices[0].message.tool_calls:
    for tool_call in response.choices[0].message.tool_calls:
        function_name = tool_call.function.name
        function_args = tool_call.function.arguments
        tool_call_id = tool_call.id

        print(f"Function: {function_name}")
        print(f"Arguments: {function_args}")
        print(f"Call ID: {tool_call_id}")
```

### Executing Tools and Sending Results

After executing the tool, send the results back:

```python
import json

# Parse arguments
args = json.loads(tool_call.function.arguments)

# Execute the function
result = get_current_weather(
    location=args["location"],
    unit=args.get("unit", "fahrenheit")
)

# Send result back
messages = [
    {"role": "user", "content": "What's the weather in Boston?"},
    response.choices[0].message,  # Assistant's tool call request
    {
        "role": "tool",
        "tool_call_id": tool_call.id,
        "content": json.dumps(result)
    }
]

# Get final response
final_response = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=messages,
    tools=[weather_tool]
)

print(final_response.choices[0].message.content)
```

---

## Tool Choice Control

Control which tools the model can call using the `tool_choice` parameter.

### Options

1. **`"auto"`** (default): Model decides whether and which tools to call
2. **`"none"`**: Model will not call any tools
3. **`"required"`**: Model must call at least one tool
4. **Specific tool**: Force a specific tool to be called

### Example: Auto (Default)

```python
response = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[{"role": "user", "content": "What's the weather?"}],
    tools=[weather_tool],
    tool_choice="auto"  # Model decides
)
```

### Example: None

```python
response = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[{"role": "user", "content": "Tell me about weather APIs"}],
    tools=[weather_tool],
    tool_choice="none"  # Don't call tools
)
```

### Example: Required

```python
response = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[{"role": "user", "content": "Get weather data"}],
    tools=[weather_tool],
    tool_choice="required"  # Must call at least one tool
)
```

### Example: Specific Tool

```python
response = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[{"role": "user", "content": "Weather info needed"}],
    tools=[weather_tool, search_tool],
    tool_choice={
        "type": "function",
        "function": {"name": "get_current_weather"}
    }  # Force specific tool
)
```

---

## Parallel vs Sequential Execution

Control whether multiple tools can be called simultaneously.

### Parallel Tool Calls (Default)

Enable multiple tools to be called at once:

```python
response = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[{
        "role": "user",
        "content": "What's the weather in Boston, NYC, and LA?"
    }],
    tools=[weather_tool],
    parallel_tool_calls=True  # Default
)

# Response may include multiple tool calls:
# [
#   {"function": {"name": "get_current_weather", "arguments": '{"location": "Boston, MA"}'}},
#   {"function": {"name": "get_current_weather", "arguments": '{"location": "New York, NY"}'}},
#   {"function": {"name": "get_current_weather", "arguments": '{"location": "Los Angeles, CA"}'}}
# ]
```

### Sequential Tool Calls

Disable parallel execution for dependent operations:

```python
response = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[{
        "role": "user",
        "content": "First get my user ID, then get my order history"
    }],
    tools=[get_user_tool, get_orders_tool],
    parallel_tool_calls=False  # One at a time
)
```

### Executing Parallel Tool Calls

```python
import json
import concurrent.futures

# Get all tool calls
tool_calls = response.choices[0].message.tool_calls

# Execute in parallel
def execute_tool(tool_call):
    args = json.loads(tool_call.function.arguments)

    if tool_call.function.name == "get_current_weather":
        result = get_current_weather(**args)
    # ... handle other tools

    return {
        "role": "tool",
        "tool_call_id": tool_call.id,
        "content": json.dumps(result)
    }

# Execute concurrently
with concurrent.futures.ThreadPoolExecutor() as executor:
    tool_messages = list(executor.map(execute_tool, tool_calls))

# Send all results back
messages = [
    {"role": "user", "content": "What's the weather in Boston, NYC, and LA?"},
    response.choices[0].message,
    *tool_messages
]

final_response = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=messages,
    tools=[weather_tool]
)
```

---

## Streaming Tool Calls

Tool calls can be streamed incrementally, allowing you to see them as they're generated.

### Streaming Response Format

```python
stream = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[{"role": "user", "content": "What's the weather in Boston?"}],
    tools=[weather_tool],
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.tool_calls:
        for tool_call_delta in chunk.choices[0].delta.tool_calls:
            print(f"Tool call delta: {tool_call_delta}")
```

### Processing Streaming Tool Calls

```python
import json

# Accumulate tool call information
tool_calls = {}

for chunk in stream:
    delta = chunk.choices[0].delta

    if delta.tool_calls:
        for tool_call_delta in delta.tool_calls:
            idx = tool_call_delta.index

            # Initialize if new tool call
            if idx not in tool_calls:
                tool_calls[idx] = {
                    "id": "",
                    "type": "function",
                    "function": {
                        "name": "",
                        "arguments": ""
                    }
                }

            # Accumulate data
            if tool_call_delta.id:
                tool_calls[idx]["id"] = tool_call_delta.id

            if tool_call_delta.function:
                if tool_call_delta.function.name:
                    tool_calls[idx]["function"]["name"] = tool_call_delta.function.name
                if tool_call_delta.function.arguments:
                    tool_calls[idx]["function"]["arguments"] += tool_call_delta.function.arguments

# Now execute the complete tool calls
for tool_call in tool_calls.values():
    args = json.loads(tool_call["function"]["arguments"])
    # Execute function...
```

---

## Complete Examples

### Example 1: Simple Weather Function

```python
from openai import OpenAI
import json

client = OpenAI(
    api_key="sk-fakeai-1234567890abcdef",
    base_url="http://localhost:8000/v1"
)

# Define the tool
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_current_weather",
            "description": "Get the current weather in a given location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City and state, e.g. San Francisco, CA"
                    },
                    "unit": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"]
                    }
                },
                "required": ["location"]
            }
        }
    }
]

# Mock weather function
def get_current_weather(location, unit="fahrenheit"):
    return {
        "location": location,
        "temperature": 72,
        "unit": unit,
        "forecast": "sunny"
    }

# Initial request
messages = [
    {"role": "user", "content": "What's the weather like in Boston?"}
]

response = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=messages,
    tools=tools
)

# Process tool calls
response_message = response.choices[0].message
messages.append(response_message)

if response_message.tool_calls:
    for tool_call in response_message.tool_calls:
        # Execute function
        args = json.loads(tool_call.function.arguments)
        result = get_current_weather(**args)

        # Add result to messages
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": json.dumps(result)
        })

    # Get final response
    final_response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=messages,
        tools=tools
    )

    print(final_response.choices[0].message.content)
```

### Example 2: Multiple Tools

```python
# Define multiple tools
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get weather for a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string"}
                },
                "required": ["location"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_flight_status",
            "description": "Get flight status by flight number",
            "parameters": {
                "type": "object",
                "properties": {
                    "flight_number": {"type": "string"}
                },
                "required": ["flight_number"]
            }
        }
    }
]

# Functions
def get_weather(location):
    return {"location": location, "temp": 72, "condition": "sunny"}

def get_flight_status(flight_number):
    return {"flight": flight_number, "status": "on time", "gate": "B12"}

# Request
response = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[{
        "role": "user",
        "content": "What's the weather in Boston and status of flight AA100?"
    }],
    tools=tools,
    parallel_tool_calls=True
)

# Handle multiple tool calls
messages = [{"role": "user", "content": "..."}]
messages.append(response.choices[0].message)

for tool_call in response.choices[0].message.tool_calls:
    args = json.loads(tool_call.function.arguments)

    # Route to correct function
    if tool_call.function.name == "get_weather":
        result = get_weather(**args)
    elif tool_call.function.name == "get_flight_status":
        result = get_flight_status(**args)

    messages.append({
        "role": "tool",
        "tool_call_id": tool_call.id,
        "content": json.dumps(result)
    })

# Get final response
final_response = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=messages,
    tools=tools
)

print(final_response.choices[0].message.content)
```

### Example 3: Conversation with Multiple Rounds

```python
def chat_with_tools(initial_message, tools, tool_functions):
    """Handle a multi-turn conversation with tools."""
    messages = [{"role": "user", "content": initial_message}]

    while True:
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=messages,
            tools=tools
        )

        response_message = response.choices[0].message
        messages.append(response_message)

        # Check for tool calls
        if response_message.tool_calls:
            # Execute all tool calls
            for tool_call in response_message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)

                # Call the actual function
                function_result = tool_functions[function_name](**function_args)

                # Add result to messages
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(function_result)
                })

            # Continue the loop to get next response
            continue
        else:
            # No more tool calls, return final response
            return response_message.content

# Usage
tools = [...]  # Your tool definitions
tool_functions = {
    "get_weather": get_weather,
    "get_flight_status": get_flight_status
}

result = chat_with_tools(
    "What's the weather in Boston and is flight AA100 on time?",
    tools,
    tool_functions
)
print(result)
```

### Example 4: Streaming with Tools

```python
def stream_with_tools(message, tools, tool_functions):
    """Stream responses with tool calling support."""
    messages = [{"role": "user", "content": message}]

    while True:
        tool_calls_accumulated = {}
        current_response = {"role": "assistant", "content": "", "tool_calls": []}

        stream = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=messages,
            tools=tools,
            stream=True
        )

        for chunk in stream:
            delta = chunk.choices[0].delta

            # Accumulate content
            if delta.content:
                current_response["content"] += delta.content
                print(delta.content, end="", flush=True)

            # Accumulate tool calls
            if delta.tool_calls:
                for tool_delta in delta.tool_calls:
                    idx = tool_delta.index

                    if idx not in tool_calls_accumulated:
                        tool_calls_accumulated[idx] = {
                            "id": "",
                            "type": "function",
                            "function": {"name": "", "arguments": ""}
                        }

                    if tool_delta.id:
                        tool_calls_accumulated[idx]["id"] = tool_delta.id
                    if tool_delta.function:
                        if tool_delta.function.name:
                            tool_calls_accumulated[idx]["function"]["name"] = tool_delta.function.name
                        if tool_delta.function.arguments:
                            tool_calls_accumulated[idx]["function"]["arguments"] += tool_delta.function.arguments

        # Add accumulated response to messages
        if tool_calls_accumulated:
            current_response["tool_calls"] = list(tool_calls_accumulated.values())

        messages.append(current_response)

        # Execute tool calls if any
        if tool_calls_accumulated:
            print("\n[Executing tools...]")

            for tool_call in tool_calls_accumulated.values():
                function_name = tool_call["function"]["name"]
                function_args = json.loads(tool_call["function"]["arguments"])
                result = tool_functions[function_name](**function_args)

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": json.dumps(result)
                })

            print("[Tools executed, continuing...]")
            continue
        else:
            # No tool calls, we're done
            print()
            return current_response["content"]

# Usage
result = stream_with_tools(
    "What's the weather in Boston?",
    tools,
    {"get_weather": get_weather}
)
```

---

## Best Practices

1. **Clear Descriptions**: Provide clear, detailed descriptions for both tools and parameters. The model uses these to decide when to call tools.

2. **Type Safety**: Use JSON Schema validation to ensure correct parameter types.

3. **Error Handling**: Always handle potential errors in tool execution:
   ```python
   try:
       result = execute_tool(args)
   except Exception as e:
       result = {"error": str(e)}
   ```

4. **Required Fields**: Mark essential parameters as `required` in the schema.

5. **Enums**: Use enums for parameters with limited valid values:
   ```python
   "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]}
   ```

6. **Parallel Execution**: Use `parallel_tool_calls=True` when tools are independent, `False` when they depend on each other.

7. **Tool Choice**: Use `tool_choice="required"` when you know a tool must be called, `"none"` when discussing tools conceptually.

8. **Response Validation**: Always parse and validate tool call arguments before execution:
   ```python
   try:
       args = json.loads(tool_call.function.arguments)
   except json.JSONDecodeError:
       # Handle invalid JSON
       pass
   ```

9. **Conversation Context**: Keep all messages in context so the model understands the full conversation flow.

10. **Streaming Accumulation**: When streaming, carefully accumulate partial tool calls before executing them.

---

## Troubleshooting

### Model Not Calling Tools

**Problem**: Model responds with text instead of calling tools.

**Solutions**:
- Make tool descriptions more specific
- Use `tool_choice="required"` to force tool usage
- Rephrase user message to be more action-oriented
- Ensure tools are relevant to the query

### Invalid Tool Arguments

**Problem**: Tool receives malformed JSON arguments.

**Solutions**:
- Validate JSON before parsing
- Add more constraints in JSON Schema
- Improve parameter descriptions
- Use default values for optional parameters

### Parallel Tool Calls Not Working

**Problem**: Tools called sequentially when parallel execution expected.

**Solutions**:
- Ensure `parallel_tool_calls=True`
- Check that tools are independent
- Verify model supports parallel execution

---

## API Reference

For complete API documentation, see:
- [ENDPOINTS.md](ENDPOINTS.md) - Full endpoint reference
- [SCHEMAS.md](SCHEMAS.md) - Complete schema documentation
