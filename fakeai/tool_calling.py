"""
Tool Calling Decision Engine for FakeAI

This module provides intelligent tool calling decisions and argument generation
for simulating realistic tool usage patterns in chat completions.
"""

#  SPDX-License-Identifier: Apache-2.0

import json
import random
import re
import uuid
from typing import Any

from faker import Faker

from fakeai.models import (
    Message,
    Role,
    Tool,
    ToolCall,
    ToolCallFunction,
    ToolChoice,
)

fake = Faker()


def extract_text_content(content: str | list | None) -> str:
    """
    Extract text from message content (string or content parts array).

    Args:
        content: Message content (string, list of content parts, or None)

    Returns:
        Extracted text content as string
    """
    if isinstance(content, str):
        return content
    elif isinstance(content, list):
        texts = []
        for part in content:
            if isinstance(part, dict) and part.get("type") == "text":
                texts.append(part.get("text", ""))
            elif hasattr(part, "type") and part.type == "text":
                texts.append(part.text)
        return " ".join(texts)
    return ""


class ToolDecisionEngine:
    """
    Decides whether and which tools to call based on tool_choice and message context.

    This engine analyzes the conversation and available tools to make intelligent
    decisions about tool usage, supporting all tool_choice modes:
    - "auto": Decide based on context and keyword matching
    - "none": Never call tools
    - "required": Must call at least one tool
    - Specific tool: Force calling a specific tool
    """

    # Keywords that suggest tool usage for common tool types
    TOOL_KEYWORDS = {
        "weather": [
            "weather",
            "temperature",
            "forecast",
            "rain",
            "sunny",
            "climate",
            "cold",
            "hot",
        ],
        "search": ["search", "find", "look up", "query", "google", "information about"],
        "calculator": [
            "calculate",
            "compute",
            "math",
            "sum",
            "multiply",
            "divide",
            "add",
            "subtract",
        ],
        "database": [
            "query",
            "database",
            "select",
            "insert",
            "update",
            "delete",
            "table",
            "record",
        ],
        "email": ["email", "send", "message", "mail", "recipient", "compose"],
        "calendar": [
            "calendar",
            "schedule",
            "appointment",
            "meeting",
            "book",
            "reserve",
        ],
        "file": ["file", "read", "write", "save", "load", "document", "upload"],
        "api": ["api", "request", "endpoint", "http", "get", "post", "fetch"],
    }

    def __init__(self):
        """Initialize the tool decision engine."""
        self.fake = Faker()

    def should_call_tools(
        self,
        messages: list[Message],
        tools: list[Tool] | None,
        tool_choice: str | ToolChoice | None,
        parallel_tool_calls: bool = True,
    ) -> tuple[bool, list[Tool]]:
        """
        Decide whether to call tools and which ones.

        Args:
            messages: Conversation messages
            tools: Available tools
            tool_choice: Tool choice setting ("auto", "none", "required", or ToolChoice)
            parallel_tool_calls: Whether parallel calls are allowed

        Returns:
            Tuple of (should_call, tools_to_call)
        """
        # No tools available
        if not tools:
            return False, []

        # Handle tool_choice = "none"
        if tool_choice == "none":
            return False, []

        # Handle tool_choice = "required"
        if tool_choice == "required":
            # Must call at least one tool - select most relevant
            selected_tools = self._select_relevant_tools(
                messages, tools, parallel_tool_calls
            )
            if not selected_tools:
                # Fallback to first tool if no relevance match
                selected_tools = [tools[0]]
            return True, selected_tools

        # Handle specific tool choice
        if isinstance(tool_choice, ToolChoice):
            # Force specific tool
            tool_name = tool_choice.function.get("name")
            for tool in tools:
                if tool.function.get("name") == tool_name:
                    return True, [tool]
            # Tool not found, but we were asked to use it - use first tool
            return True, [tools[0]]

        # Handle tool_choice = "auto" or None (default is auto)
        # Decide based on context and keywords
        selected_tools = self._select_relevant_tools(
            messages, tools, parallel_tool_calls
        )

        if selected_tools:
            # Randomly decide to call tools (70% chance if keywords match)
            return random.random() < 0.7, selected_tools

        # No relevant tools found, small chance of calling anyway (10%)
        if random.random() < 0.1:
            return True, [random.choice(tools)]

        return False, []

    def _select_relevant_tools(
        self,
        messages: list[Message],
        tools: list[Tool],
        parallel_tool_calls: bool,
    ) -> list[Tool]:
        """
        Select relevant tools based on message content.

        Args:
            messages: Conversation messages
            tools: Available tools
            parallel_tool_calls: Whether to allow multiple tools

        Returns:
            List of relevant tools to call
        """
        # Get last user message
        last_message = None
        for msg in reversed(messages):
            if msg.role == Role.USER:
                last_message = msg
                break

        if not last_message:
            return []

        message_text = extract_text_content(last_message.content).lower()

        # Score each tool by relevance
        tool_scores = []
        for tool in tools:
            score = self._calculate_tool_relevance(message_text, tool)
            tool_scores.append((tool, score))

        # Sort by score descending
        tool_scores.sort(key=lambda x: x[1], reverse=True)

        # Select tools with positive scores
        relevant_tools = [tool for tool, score in tool_scores if score > 0]

        if not relevant_tools:
            return []

        # If parallel calls not allowed or only one relevant tool, return just the best
        if not parallel_tool_calls or len(relevant_tools) == 1:
            return [relevant_tools[0]]

        # For parallel calls, return up to 3 highly relevant tools
        # (only if they have score > 3)
        high_relevance_tools = [tool for tool, score in tool_scores if score > 3]

        if len(high_relevance_tools) > 1:
            # Return 2-3 tools for parallel calling
            num_tools = random.randint(2, min(3, len(high_relevance_tools)))
            return high_relevance_tools[:num_tools]

        return [relevant_tools[0]]

    def _calculate_tool_relevance(self, message_text: str, tool: Tool) -> float:
        """
        Calculate relevance score for a tool given the message text.

        Args:
            message_text: Lowercased message text
            tool: Tool to score

        Returns:
            Relevance score (higher is more relevant)
        """
        score = 0.0

        tool_name = tool.function.get("name", "").lower()
        tool_description = tool.function.get("description", "").lower()

        # Check if tool name appears in message
        if tool_name in message_text:
            score += 5.0

        # Check if tool name words appear
        tool_name_words = re.findall(r"\w+", tool_name)
        for word in tool_name_words:
            if len(word) > 3 and word in message_text:
                score += 2.0

        # Check description keywords
        description_words = re.findall(r"\w+", tool_description)
        for word in description_words:
            if len(word) > 4 and word in message_text:
                score += 1.0

        # Check against known keywords for common tool types
        for tool_type, keywords in self.TOOL_KEYWORDS.items():
            if tool_type in tool_name or tool_type in tool_description:
                for keyword in keywords:
                    if keyword in message_text:
                        score += 1.5

        return score


class ToolCallGenerator:
    """
    Generates realistic tool call arguments based on tool definitions and context.

    This generator analyzes tool schemas and conversation context to produce
    plausible arguments for tool calls.
    """

    def __init__(self):
        """Initialize the tool call generator."""
        self.fake = Faker()

    def generate_tool_calls(
        self,
        tools_to_call: list[Tool],
        messages: list[Message],
        parallel: bool = True,
    ) -> list[ToolCall]:
        """
        Generate tool calls with realistic arguments.

        Args:
            tools_to_call: Tools to generate calls for
            messages: Conversation context
            parallel: Whether these are parallel calls

        Returns:
            List of ToolCall objects with generated arguments
        """
        tool_calls = []

        for tool in tools_to_call:
            tool_call = self._generate_single_tool_call(tool, messages)
            tool_calls.append(tool_call)

        return tool_calls

    def _generate_single_tool_call(
        self,
        tool: Tool,
        messages: list[Message],
    ) -> ToolCall:
        """
        Generate a single tool call.

        Args:
            tool: Tool to call
            messages: Conversation context

        Returns:
            ToolCall with generated arguments
        """
        tool_id = f"call_{uuid.uuid4().hex[:24]}"
        function_def = tool.function
        function_name = function_def.get("name", "unknown_function")

        # Generate arguments based on the function schema
        arguments = self.generate_arguments(function_def, messages)

        return ToolCall(
            id=tool_id,
            type="function",
            function=ToolCallFunction(
                name=function_name,
                arguments=json.dumps(arguments),
            ),
        )

    def generate_arguments(
        self,
        function_def: dict[str, Any],
        messages: list[Message],
    ) -> dict[str, Any]:
        """
        Generate realistic arguments for a function call.

        Args:
            function_def: Function definition with parameters schema
            messages: Conversation context

        Returns:
            Dictionary of generated arguments
        """
        parameters = function_def.get("parameters", {})
        properties = parameters.get("properties", {})
        required = parameters.get("required", [])

        # Get last user message for context
        last_user_message = None
        for msg in reversed(messages):
            if msg.role == Role.USER:
                last_user_message = msg
                break

        message_text = ""
        if last_user_message:
            message_text = extract_text_content(last_user_message.content)

        arguments = {}

        # Generate each parameter
        for param_name, param_schema in properties.items():
            # Always generate required parameters
            # Generate optional parameters 60% of the time
            if param_name in required or random.random() < 0.6:
                value = self._generate_parameter_value(
                    param_name,
                    param_schema,
                    message_text,
                )
                arguments[param_name] = value

        return arguments

    def _generate_parameter_value(
        self,
        param_name: str,
        param_schema: dict[str, Any],
        context: str,
    ) -> Any:
        """
        Generate a value for a specific parameter.

        Args:
            param_name: Parameter name
            param_schema: JSON schema for the parameter
            context: Message context

        Returns:
            Generated parameter value
        """
        param_type = param_schema.get("type", "string")
        param_description = param_schema.get("description", "").lower()
        enum_values = param_schema.get("enum")

        # Handle enum values
        if enum_values:
            return random.choice(enum_values)

        # Try to extract value from context first
        extracted = self._extract_value_from_context(
            param_name,
            param_type,
            param_description,
            context,
        )
        if extracted is not None:
            return extracted

        # Generate based on type
        if param_type == "string":
            return self._generate_string_value(param_name, param_description)
        elif param_type == "number" or param_type == "integer":
            return self._generate_number_value(
                param_name, param_description, param_type
            )
        elif param_type == "boolean":
            return random.choice([True, False])
        elif param_type == "array":
            items_schema = param_schema.get("items", {})
            # Generate 1-3 items
            return [
                self._generate_parameter_value(param_name, items_schema, context)
                for _ in range(random.randint(1, 3))
            ]
        elif param_type == "object":
            # Recursively generate object properties
            obj_properties = param_schema.get("properties", {})
            return {
                key: self._generate_parameter_value(key, schema, context)
                for key, schema in obj_properties.items()
            }

        # Default to string
        return self._generate_string_value(param_name, param_description)

    def _extract_value_from_context(
        self,
        param_name: str,
        param_type: str,
        param_description: str,
        context: str,
    ) -> Any | None:
        """
        Try to extract parameter value from conversation context.

        Args:
            param_name: Parameter name
            param_type: Parameter type
            param_description: Parameter description
            context: Message text

        Returns:
            Extracted value or None if not found
        """
        context_lower = context.lower()

        # Location extraction
        if "location" in param_name.lower() or "city" in param_name.lower():
            # Look for city names in context
            cities = ["San Francisco", "New York", "London", "Paris", "Tokyo", "Berlin"]
            for city in cities:
                if city.lower() in context_lower:
                    return city

            # Look for "in <location>" pattern
            match = re.search(r"\bin\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)", context)
            if match:
                return match.group(1)

        # Query/question extraction
        if "query" in param_name.lower() or "question" in param_name.lower():
            # Extract question marks or quoted text
            match = re.search(r'"([^"]+)"', context)
            if match:
                return match.group(1)

            # Return first sentence if it's a question
            sentences = re.split(r"[.!?]", context)
            if sentences and "?" in context:
                for sentence in sentences:
                    if "?" in sentence:
                        return sentence.strip().rstrip("?").strip()

        # Number extraction
        if param_type in ["number", "integer"]:
            # Look for numbers in context
            numbers = re.findall(r"\b\d+(?:\.\d+)?\b", context)
            if numbers:
                value = float(numbers[0]) if param_type == "number" else int(numbers[0])
                return value

        # Email extraction
        if "email" in param_name.lower() or "recipient" in param_name.lower():
            match = re.search(
                r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", context
            )
            if match:
                return match.group(0)

        # Date extraction
        if "date" in param_name.lower() or "time" in param_name.lower():
            # Look for date patterns
            date_patterns = [
                r"\b\d{4}-\d{2}-\d{2}\b",  # YYYY-MM-DD
                r"\b\d{1,2}/\d{1,2}/\d{4}\b",  # MM/DD/YYYY
                r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+\d{4}\b",
            ]
            for pattern in date_patterns:
                match = re.search(pattern, context, re.IGNORECASE)
                if match:
                    return match.group(0)

        return None

    def _generate_string_value(self, param_name: str, param_description: str) -> str:
        """Generate a string value based on parameter name and description."""
        param_name_lower = param_name.lower()
        param_description_lower = param_description.lower()

        # Location/city
        if "location" in param_name_lower or "city" in param_name_lower:
            return self.fake.city()

        # State
        if "state" in param_name_lower:
            return self.fake.state_abbr()

        # Country
        if "country" in param_name_lower:
            return self.fake.country()

        # Email
        if "email" in param_name_lower:
            return self.fake.email()

        # Name
        if "name" in param_name_lower:
            return self.fake.name()

        # Query/question
        if "query" in param_name_lower or "question" in param_name_lower:
            return self.fake.sentence()

        # URL
        if "url" in param_name_lower:
            return self.fake.url()

        # Date
        if "date" in param_name_lower:
            return self.fake.date()

        # Time
        if "time" in param_name_lower:
            return self.fake.time()

        # Description/text
        if "description" in param_name_lower or "text" in param_name_lower:
            return self.fake.sentence()

        # Message/content
        if "message" in param_name_lower or "content" in param_name_lower:
            return self.fake.text(max_nb_chars=100)

        # Default to a word
        return self.fake.word()

    def _generate_number_value(
        self,
        param_name: str,
        param_description: str,
        param_type: str,
    ) -> int | float:
        """Generate a number value based on parameter context."""
        param_name_lower = param_name.lower()

        # Temperature (typically -50 to 50 Celsius)
        if "temperature" in param_name_lower:
            value = random.randint(-50, 50)
            return value if param_type == "integer" else float(value)

        # Limit/count (typically 1-100)
        if "limit" in param_name_lower or "count" in param_name_lower:
            return random.randint(1, 100)

        # Page (typically 1-10)
        if "page" in param_name_lower:
            return random.randint(1, 10)

        # Age (typically 18-80)
        if "age" in param_name_lower:
            return random.randint(18, 80)

        # Price/amount (typically 0-1000)
        if "price" in param_name_lower or "amount" in param_name_lower:
            value = random.uniform(0, 1000)
            return int(value) if param_type == "integer" else round(value, 2)

        # Default to small integer or float
        if param_type == "integer":
            return random.randint(1, 100)
        else:
            return round(random.uniform(0, 100), 2)
