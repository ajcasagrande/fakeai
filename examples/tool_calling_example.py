"""
Example script demonstrating tool calling with FakeAI.

This script shows how to use the tool calling decision engine
to simulate tool usage in chat completions.
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fakeai.models import Message, Role, Tool
from fakeai.tool_calling import ToolCallGenerator, ToolDecisionEngine


def main():
    """Run tool calling examples."""
    print("=" * 70)
    print("FakeAI Tool Calling Examples")
    print("=" * 70)

    # Initialize engines
    decision_engine = ToolDecisionEngine()
    call_generator = ToolCallGenerator()

    # Define sample tools
    weather_tool = Tool(
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
                        "description": "Temperature unit",
                    },
                },
                "required": ["location"],
            },
        },
    )

    search_tool = Tool(
        type="function",
        function={
            "name": "search_web",
            "description": "Search the web for information",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query"},
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results",
                    },
                },
                "required": ["query"],
            },
        },
    )

    calculator_tool = Tool(
        type="function",
        function={
            "name": "calculate",
            "description": "Perform mathematical calculations",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Mathematical expression to evaluate",
                    }
                },
                "required": ["expression"],
            },
        },
    )

    tools = [weather_tool, search_tool, calculator_tool]

    # Example 1: Auto mode with weather query
    print("\n" + "=" * 70)
    print("Example 1: Auto Mode - Weather Query")
    print("=" * 70)

    messages1 = [
        Message(
            role=Role.USER, content="What's the weather like in San Francisco today?"
        )
    ]

    should_call, selected_tools = decision_engine.should_call_tools(
        messages=messages1, tools=tools, tool_choice="auto", parallel_tool_calls=False
    )

    print(f"\nUser Message: {messages1[0].content}")
    print(f"Should Call Tools: {should_call}")
    print(f"Selected Tools: {[t.function['name'] for t in selected_tools]}")

    if should_call:
        tool_calls = call_generator.generate_tool_calls(
            selected_tools, messages1, parallel=False
        )
        for tc in tool_calls:
            print(f"\nTool Call ID: {tc.id}")
            print(f"Function Name: {tc.function.name}")
            print(f"Arguments: {tc.function.arguments}")

    # Example 2: Required mode
    print("\n" + "=" * 70)
    print("Example 2: Required Mode - Must Call Tool")
    print("=" * 70)

    messages2 = [Message(role=Role.USER, content="Hello, how are you?")]

    should_call, selected_tools = decision_engine.should_call_tools(
        messages=messages2,
        tools=tools,
        tool_choice="required",
        parallel_tool_calls=False,
    )

    print(f"\nUser Message: {messages2[0].content}")
    print(f"Tool Choice: required")
    print(f"Should Call Tools: {should_call}")
    print(f"Selected Tools: {[t.function['name'] for t in selected_tools]}")

    if should_call:
        tool_calls = call_generator.generate_tool_calls(
            selected_tools, messages2, parallel=False
        )
        for tc in tool_calls:
            print(f"\nTool Call ID: {tc.id}")
            print(f"Function Name: {tc.function.name}")
            print(f"Arguments: {tc.function.arguments}")

    # Example 3: Parallel tool calls
    print("\n" + "=" * 70)
    print("Example 3: Parallel Tool Calls")
    print("=" * 70)

    messages3 = [
        Message(
            role=Role.USER,
            content="Search for weather forecasts and calculate the average temperature",
        )
    ]

    should_call, selected_tools = decision_engine.should_call_tools(
        messages=messages3,
        tools=tools,
        tool_choice="required",
        parallel_tool_calls=True,
    )

    print(f"\nUser Message: {messages3[0].content}")
    print(f"Tool Choice: required")
    print(f"Parallel Tool Calls: True")
    print(f"Should Call Tools: {should_call}")
    print(f"Selected Tools: {[t.function['name'] for t in selected_tools]}")

    if should_call:
        tool_calls = call_generator.generate_tool_calls(
            selected_tools, messages3, parallel=True
        )
        print(f"\nGenerated {len(tool_calls)} tool calls:")
        for i, tc in enumerate(tool_calls, 1):
            print(f"\n  Tool Call {i}:")
            print(f"    ID: {tc.id}")
            print(f"    Function: {tc.function.name}")
            print(f"    Arguments: {tc.function.arguments}")

    # Example 4: Context extraction
    print("\n" + "=" * 70)
    print("Example 4: Context Extraction - Email and Numbers")
    print("=" * 70)

    email_tool = Tool(
        type="function",
        function={
            "name": "send_email",
            "description": "Send an email",
            "parameters": {
                "type": "object",
                "properties": {
                    "recipient": {"type": "string", "description": "Email address"},
                    "subject": {"type": "string", "description": "Email subject"},
                    "limit": {"type": "integer", "description": "Max message length"},
                },
                "required": ["recipient"],
            },
        },
    )

    messages4 = [
        Message(
            role=Role.USER,
            content="Send an email to john.doe@example.com about the meeting with a limit of 500 words",
        )
    ]

    tool_calls = call_generator.generate_tool_calls(
        [email_tool], messages4, parallel=False
    )

    print(f"\nUser Message: {messages4[0].content}")
    print(f"\nGenerated Tool Call:")
    print(f"  Function: {tool_calls[0].function.name}")
    print(f"  Arguments: {tool_calls[0].function.arguments}")
    print(f"\n  Extracted Values:")
    import json

    args = json.loads(tool_calls[0].function.arguments)
    print(f"    - Recipient (email): {args.get('recipient')}")
    print(f"    - Limit (number): {args.get('limit')}")

    # Example 5: None mode - no tool calls
    print("\n" + "=" * 70)
    print("Example 5: None Mode - Never Call Tools")
    print("=" * 70)

    messages5 = [Message(role=Role.USER, content="What's the weather in Tokyo?")]

    should_call, selected_tools = decision_engine.should_call_tools(
        messages=messages5, tools=tools, tool_choice="none", parallel_tool_calls=False
    )

    print(f"\nUser Message: {messages5[0].content}")
    print(f"Tool Choice: none")
    print(f"Should Call Tools: {should_call}")
    print(f"Selected Tools: {selected_tools}")
    print("\nNote: Even with weather keywords, tools are not called in 'none' mode")

    print("\n" + "=" * 70)
    print("Examples Complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
