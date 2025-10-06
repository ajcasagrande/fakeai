"""
Tests for chat completion models.

This module tests all chat-related Pydantic models including:
- ChatCompletionRequest
- ChatCompletionResponse
- ChatCompletionChoice
- Message
- ChatCompletionChunk
- ChatCompletionChunkChoice
- Delta
- Tool
- ToolCall
- ToolChoice
- ToolCallFunction
- FunctionCall
- FunctionDelta
- ToolCallDelta
- ResponseFormat
- JsonSchema
- JsonSchemaResponseFormat
- StreamOptions
- PredictionContent
- ChatLogprob
- TopLogprob
- ChatLogprobs
"""

#  SPDX-License-Identifier: Apache-2.0

import pytest
from pydantic import ValidationError

from fakeai.models import (
    ChatCompletionChoice,
    ChatCompletionChunk,
    ChatCompletionChunkChoice,
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatLogprob,
    ChatLogprobs,
    CompletionTokensDetails,
    Delta,
    FunctionCall,
    FunctionDelta,
    JsonSchema,
    JsonSchemaResponseFormat,
    Message,
    PredictionContent,
    PromptTokensDetails,
    ResponseFormat,
    Role,
    StreamOptions,
    TextContent,
    Tool,
    ToolCall,
    ToolCallDelta,
    ToolCallFunction,
    ToolChoice,
    TopLogprob,
    Usage,
)


def test_import_chat_models():
    """Test that all chat models can be imported from fakeai.models."""
    from fakeai.models import (
        ChatCompletionChoice,
        ChatCompletionChunk,
        ChatCompletionChunkChoice,
        ChatCompletionRequest,
        ChatCompletionResponse,
        ChatLogprob,
        ChatLogprobs,
        Delta,
        FunctionCall,
        FunctionDelta,
        JsonSchema,
        JsonSchemaResponseFormat,
        Message,
        PredictionContent,
        ResponseFormat,
        StreamOptions,
        Tool,
        ToolCall,
        ToolCallDelta,
        ToolCallFunction,
        ToolChoice,
        TopLogprob,
    )

    assert ChatCompletionRequest is not None
    assert ChatCompletionResponse is not None
    assert ChatCompletionChoice is not None
    assert Message is not None
    assert ChatCompletionChunk is not None
    assert ChatCompletionChunkChoice is not None
    assert Delta is not None
    assert Tool is not None
    assert ToolCall is not None
    assert ToolChoice is not None
    assert ToolCallFunction is not None
    assert FunctionCall is not None
    assert FunctionDelta is not None
    assert ToolCallDelta is not None
    assert ResponseFormat is not None
    assert JsonSchema is not None
    assert JsonSchemaResponseFormat is not None
    assert StreamOptions is not None
    assert PredictionContent is not None
    assert ChatLogprob is not None
    assert TopLogprob is not None
    assert ChatLogprobs is not None


def test_message_creation_simple():
    """Test creating a simple text message."""
    msg = Message(role=Role.USER, content="Hello, world!")
    assert msg.role == Role.USER
    assert msg.content == "Hello, world!"
    assert msg.name is None
    assert msg.tool_calls is None
    assert msg.tool_call_id is None


def test_message_creation_multimodal():
    """Test creating a message with multi-modal content."""
    content = [
        TextContent(type="text", text="What's in this image?"),
    ]
    msg = Message(role=Role.USER, content=content)
    assert msg.role == Role.USER
    assert isinstance(msg.content, list)
    assert len(msg.content) == 1
    assert msg.content[0].type == "text"


def test_message_with_tool_calls():
    """Test creating an assistant message with tool calls."""
    tool_call = ToolCall(
        id="call_abc123",
        type="function",
        function=ToolCallFunction(
            name="get_weather", arguments='{"location": "San Francisco"}'
        ),
    )
    msg = Message(role=Role.ASSISTANT, content=None, tool_calls=[tool_call])
    assert msg.role == Role.ASSISTANT
    assert msg.content is None
    assert len(msg.tool_calls) == 1
    assert msg.tool_calls[0].id == "call_abc123"
    assert msg.tool_calls[0].function.name == "get_weather"


def test_message_with_reasoning_content():
    """Test creating a message with reasoning content (GPT-OSS models)."""
    msg = Message(
        role=Role.ASSISTANT,
        content="The answer is 42.",
        reasoning_content="First, I considered... Then I calculated...",
    )
    assert msg.content == "The answer is 42."
    assert msg.reasoning_content == "First, I considered... Then I calculated..."


def test_chat_request_creation():
    """Test creating a basic chat completion request."""
    request = ChatCompletionRequest(
        model="gpt-4", messages=[Message(role=Role.USER, content="Hello!")]
    )
    assert request.model == "gpt-4"
    assert len(request.messages) == 1
    assert request.messages[0].content == "Hello!"
    assert request.temperature == 1.0
    assert request.stream is False
    assert request.n == 1


def test_chat_request_with_tools():
    """Test creating a chat request with tool definitions."""
    tool = Tool(
        type="function",
        function={
            "name": "get_weather",
            "description": "Get the current weather",
            "parameters": {
                "type": "object",
                "properties": {"location": {"type": "string"}},
                "required": ["location"],
            },
        },
    )
    request = ChatCompletionRequest(
        model="gpt-4",
        messages=[Message(role=Role.USER, content="What's the weather?")],
        tools=[tool],
        tool_choice="auto",
    )
    assert len(request.tools) == 1
    assert request.tools[0].function["name"] == "get_weather"
    assert request.tool_choice == "auto"


def test_chat_request_with_prediction():
    """Test creating a chat request with predicted outputs (GPT-4o)."""
    prediction = PredictionContent(type="content", content="I predict this response...")
    request = ChatCompletionRequest(
        model="gpt-4o",
        messages=[Message(role=Role.USER, content="Complete this...")],
        prediction=prediction,
    )
    assert request.prediction is not None
    assert request.prediction.type == "content"
    assert request.prediction.content == "I predict this response..."


def test_chat_request_with_response_format():
    """Test creating a chat request with response format."""
    # Test with basic response format
    request1 = ChatCompletionRequest(
        model="gpt-4",
        messages=[Message(role=Role.USER, content="Tell me a joke")],
        response_format=ResponseFormat(type="json_object"),
    )
    assert request1.response_format.type == "json_object"

    # Test with JSON schema
    json_schema = JsonSchemaResponseFormat(
        type="json_schema",
        json_schema=JsonSchema(
            name="joke_response",
            schema={
                "type": "object",
                "properties": {
                    "setup": {"type": "string"},
                    "punchline": {"type": "string"},
                },
                "required": ["setup", "punchline"],
            },
        ),
    )
    request2 = ChatCompletionRequest(
        model="gpt-4",
        messages=[Message(role=Role.USER, content="Tell me a joke")],
        response_format=json_schema,
    )
    assert request2.response_format.type == "json_schema"
    assert request2.response_format.json_schema.name == "joke_response"


def test_chat_request_streaming_options():
    """Test creating a streaming chat request with options."""
    request = ChatCompletionRequest(
        model="gpt-4",
        messages=[Message(role=Role.USER, content="Hello")],
        stream=True,
        stream_options=StreamOptions(include_usage=True),
    )
    assert request.stream is True
    assert request.stream_options is not None
    assert request.stream_options.include_usage is True


def test_chat_request_validation_temperature():
    """Test that temperature validation works."""
    # Valid temperature
    request = ChatCompletionRequest(
        model="gpt-4", messages=[Message(role=Role.USER, content="Hi")], temperature=0.5
    )
    assert request.temperature == 0.5

    # Invalid temperature (too high)
    with pytest.raises(ValidationError):
        ChatCompletionRequest(
            model="gpt-4",
            messages=[Message(role=Role.USER, content="Hi")],
            temperature=3.0,
        )

    # Invalid temperature (negative)
    with pytest.raises(ValidationError):
        ChatCompletionRequest(
            model="gpt-4",
            messages=[Message(role=Role.USER, content="Hi")],
            temperature=-1.0,
        )


def test_chat_response_creation():
    """Test creating a chat completion response."""
    response = ChatCompletionResponse(
        id="chatcmpl-abc123",
        object="chat.completion",
        created=1234567890,
        model="gpt-4",
        choices=[
            ChatCompletionChoice(
                index=0,
                message=Message(
                    role=Role.ASSISTANT, content="Hello! How can I help you?"
                ),
                finish_reason="stop",
            )
        ],
        usage=Usage(prompt_tokens=10, completion_tokens=8, total_tokens=18),
    )
    assert response.id == "chatcmpl-abc123"
    assert response.object == "chat.completion"
    assert len(response.choices) == 1
    assert response.choices[0].message.content == "Hello! How can I help you?"
    assert response.usage.total_tokens == 18


def test_chat_response_with_reasoning_tokens():
    """Test chat response with reasoning tokens (GPT-OSS models)."""
    response = ChatCompletionResponse(
        id="chatcmpl-abc123",
        object="chat.completion",
        created=1234567890,
        model="gpt-oss-120b",
        choices=[
            ChatCompletionChoice(
                index=0,
                message=Message(
                    role=Role.ASSISTANT,
                    content="The answer is 42.",
                    reasoning_content="Let me think through this...",
                ),
                finish_reason="stop",
            )
        ],
        usage=Usage(
            prompt_tokens=20,
            completion_tokens=30,
            total_tokens=50,
            completion_tokens_details=CompletionTokensDetails(
                reasoning_tokens=15, audio_tokens=0
            ),
        ),
    )
    assert response.choices[0].message.reasoning_content is not None
    assert response.usage.completion_tokens_details.reasoning_tokens == 15


def test_chat_response_with_logprobs():
    """Test chat response with log probabilities."""
    top_logprobs = [
        TopLogprob(token="Hello", logprob=-0.1),
        TopLogprob(token="Hi", logprob=-0.5),
    ]
    logprob = ChatLogprob(
        token="Hello",
        logprob=-0.1,
        bytes=[72, 101, 108, 108, 111],
        top_logprobs=top_logprobs,
    )
    logprobs = ChatLogprobs(content=[logprob])

    response = ChatCompletionResponse(
        id="chatcmpl-abc123",
        object="chat.completion",
        created=1234567890,
        model="gpt-4",
        choices=[
            ChatCompletionChoice(
                index=0,
                message=Message(role=Role.ASSISTANT, content="Hello"),
                finish_reason="stop",
                logprobs=logprobs,
            )
        ],
        usage=Usage(prompt_tokens=5, completion_tokens=1, total_tokens=6),
    )
    assert response.choices[0].logprobs is not None
    assert len(response.choices[0].logprobs.content) == 1
    assert response.choices[0].logprobs.content[0].token == "Hello"


def test_streaming_chunks():
    """Test creating streaming chat completion chunks."""
    # First chunk with role
    chunk1 = ChatCompletionChunk(
        id="chatcmpl-abc123",
        object="chat.completion.chunk",
        created=1234567890,
        model="gpt-4",
        choices=[
            ChatCompletionChunkChoice(
                index=0, delta=Delta(role=Role.ASSISTANT), finish_reason=None
            )
        ],
    )
    assert chunk1.choices[0].delta.role == Role.ASSISTANT
    assert chunk1.choices[0].delta.content is None

    # Content chunks
    chunk2 = ChatCompletionChunk(
        id="chatcmpl-abc123",
        object="chat.completion.chunk",
        created=1234567890,
        model="gpt-4",
        choices=[
            ChatCompletionChunkChoice(
                index=0, delta=Delta(content="Hello"), finish_reason=None
            )
        ],
    )
    assert chunk2.choices[0].delta.content == "Hello"

    # Final chunk with finish reason
    chunk3 = ChatCompletionChunk(
        id="chatcmpl-abc123",
        object="chat.completion.chunk",
        created=1234567890,
        model="gpt-4",
        choices=[
            ChatCompletionChunkChoice(index=0, delta=Delta(), finish_reason="stop")
        ],
    )
    assert chunk3.choices[0].finish_reason == "stop"


def test_streaming_with_usage():
    """Test streaming chunk with usage information."""
    chunk = ChatCompletionChunk(
        id="chatcmpl-abc123",
        object="chat.completion.chunk",
        created=1234567890,
        model="gpt-4",
        choices=[
            ChatCompletionChunkChoice(index=0, delta=Delta(), finish_reason="stop")
        ],
        usage=Usage(prompt_tokens=10, completion_tokens=20, total_tokens=30),
    )
    assert chunk.usage is not None
    assert chunk.usage.total_tokens == 30


def test_streaming_tool_calls():
    """Test streaming chunks with tool call deltas."""
    # First chunk with tool call ID
    chunk1 = ChatCompletionChunk(
        id="chatcmpl-abc123",
        object="chat.completion.chunk",
        created=1234567890,
        model="gpt-4",
        choices=[
            ChatCompletionChunkChoice(
                index=0,
                delta=Delta(
                    tool_calls=[
                        ToolCallDelta(
                            index=0,
                            id="call_abc123",
                            type="function",
                            function=FunctionDelta(name="get_weather"),
                        )
                    ]
                ),
                finish_reason=None,
            )
        ],
    )
    assert chunk1.choices[0].delta.tool_calls[0].id == "call_abc123"
    assert chunk1.choices[0].delta.tool_calls[0].function.name == "get_weather"

    # Subsequent chunks with partial arguments
    chunk2 = ChatCompletionChunk(
        id="chatcmpl-abc123",
        object="chat.completion.chunk",
        created=1234567890,
        model="gpt-4",
        choices=[
            ChatCompletionChunkChoice(
                index=0,
                delta=Delta(
                    tool_calls=[
                        ToolCallDelta(
                            index=0, function=FunctionDelta(arguments='{"location":')
                        )
                    ]
                ),
                finish_reason=None,
            )
        ],
    )
    assert chunk2.choices[0].delta.tool_calls[0].function.arguments == '{"location":'


def test_tool_definitions():
    """Test creating tool definitions."""
    tool = Tool(
        type="function",
        function={
            "name": "calculate_sum",
            "description": "Calculate the sum of two numbers",
            "parameters": {
                "type": "object",
                "properties": {
                    "a": {"type": "number", "description": "First number"},
                    "b": {"type": "number", "description": "Second number"},
                },
                "required": ["a", "b"],
            },
        },
    )
    assert tool.type == "function"
    assert tool.function["name"] == "calculate_sum"
    assert "a" in tool.function["parameters"]["properties"]


def test_tool_choice():
    """Test tool choice configuration."""
    # Auto tool choice
    request1 = ChatCompletionRequest(
        model="gpt-4",
        messages=[Message(role=Role.USER, content="Hi")],
        tool_choice="auto",
    )
    assert request1.tool_choice == "auto"

    # Specific tool choice
    tool_choice = ToolChoice(type="function", function={"name": "get_weather"})
    request2 = ChatCompletionRequest(
        model="gpt-4",
        messages=[Message(role=Role.USER, content="Hi")],
        tool_choice=tool_choice,
    )
    assert request2.tool_choice.function["name"] == "get_weather"


def test_function_call_deprecated():
    """Test deprecated function call format."""
    func_call = FunctionCall(name="old_function", arguments='{"arg": "value"}')
    msg = Message(role=Role.ASSISTANT, content=None, function_call=func_call)
    assert msg.function_call is not None
    assert msg.function_call.name == "old_function"


def test_delta_with_token_timing():
    """Test delta with token timing information."""
    delta = Delta(content="word", token_timing=[0.05, 0.08, 0.06, 0.07])
    assert delta.content == "word"
    assert delta.token_timing is not None
    assert len(delta.token_timing) == 4


def test_chat_request_max_tokens_variants():
    """Test both max_tokens and max_completion_tokens fields."""
    # Standard max_tokens
    request1 = ChatCompletionRequest(
        model="gpt-4", messages=[Message(role=Role.USER, content="Hi")], max_tokens=100
    )
    assert request1.max_tokens == 100

    # DeepSeek-R1 style max_completion_tokens
    request2 = ChatCompletionRequest(
        model="deepseek-ai/DeepSeek-R1",
        messages=[Message(role=Role.USER, content="Hi")],
        max_completion_tokens=200,
    )
    assert request2.max_completion_tokens == 200


def test_chat_request_modalities():
    """Test chat request with audio modality."""
    from fakeai.models import AudioConfig

    request = ChatCompletionRequest(
        model="gpt-4o-audio",
        messages=[Message(role=Role.USER, content="Say hello")],
        modalities=["text", "audio"],
        audio=AudioConfig(voice="alloy", format="mp3"),
    )
    assert request.modalities == ["text", "audio"]
    assert request.audio is not None
    assert request.audio.voice == "alloy"


def test_chat_request_metadata_and_store():
    """Test chat request with metadata and store flags."""
    request = ChatCompletionRequest(
        model="gpt-4",
        messages=[Message(role=Role.USER, content="Hello")],
        store=True,
        metadata={"user_id": "123", "session_id": "abc"},
    )
    assert request.store is True
    assert request.metadata["user_id"] == "123"


def test_chat_response_with_refusal():
    """Test chat response with refusal message."""
    response = ChatCompletionResponse(
        id="chatcmpl-abc123",
        object="chat.completion",
        created=1234567890,
        model="gpt-4",
        choices=[
            ChatCompletionChoice(
                index=0,
                message=Message(
                    role=Role.ASSISTANT,
                    content=None,
                    refusal="I cannot help with that request.",
                ),
                finish_reason="stop",
            )
        ],
        usage=Usage(prompt_tokens=10, completion_tokens=0, total_tokens=10),
    )
    assert response.choices[0].message.refusal is not None
    assert "cannot help" in response.choices[0].message.refusal


def test_parallel_tool_calls():
    """Test parallel tool calls configuration."""
    request = ChatCompletionRequest(
        model="gpt-4",
        messages=[Message(role=Role.USER, content="Multi-task")],
        parallel_tool_calls=True,
    )
    assert request.parallel_tool_calls is True

    request2 = ChatCompletionRequest(
        model="gpt-4",
        messages=[Message(role=Role.USER, content="Sequential")],
        parallel_tool_calls=False,
    )
    assert request2.parallel_tool_calls is False


def test_logprobs_configuration():
    """Test logprobs request configuration."""
    request = ChatCompletionRequest(
        model="gpt-4",
        messages=[Message(role=Role.USER, content="Test")],
        logprobs=True,
        top_logprobs=5,
    )
    assert request.logprobs is True
    assert request.top_logprobs == 5

    # Test validation of top_logprobs range
    with pytest.raises(ValidationError):
        ChatCompletionRequest(
            model="gpt-4",
            messages=[Message(role=Role.USER, content="Test")],
            logprobs=True,
            top_logprobs=25,  # Max is 20
        )


def test_seed_for_deterministic_sampling():
    """Test seed parameter for deterministic sampling."""
    request = ChatCompletionRequest(
        model="gpt-4", messages=[Message(role=Role.USER, content="Random")], seed=42
    )
    assert request.seed == 42


def test_service_tier():
    """Test service tier parameter."""
    request = ChatCompletionRequest(
        model="gpt-4",
        messages=[Message(role=Role.USER, content="Priority")],
        service_tier="default",
    )
    assert request.service_tier == "default"


def test_logit_bias():
    """Test logit bias parameter."""
    request = ChatCompletionRequest(
        model="gpt-4",
        messages=[Message(role=Role.USER, content="Biased")],
        logit_bias={"50256": -100, "1234": 10},
    )
    assert request.logit_bias is not None
    assert request.logit_bias["50256"] == -100


def test_stop_sequences():
    """Test stop sequences parameter."""
    # Single stop string
    request1 = ChatCompletionRequest(
        model="gpt-4", messages=[Message(role=Role.USER, content="Count")], stop="STOP"
    )
    assert request1.stop == "STOP"

    # Multiple stop strings
    request2 = ChatCompletionRequest(
        model="gpt-4",
        messages=[Message(role=Role.USER, content="Count")],
        stop=["END", "DONE", "STOP"],
    )
    assert isinstance(request2.stop, list)
    assert len(request2.stop) == 3


def test_presence_and_frequency_penalties():
    """Test presence and frequency penalty parameters."""
    request = ChatCompletionRequest(
        model="gpt-4",
        messages=[Message(role=Role.USER, content="Creative")],
        presence_penalty=0.5,
        frequency_penalty=0.3,
    )
    assert request.presence_penalty == 0.5
    assert request.frequency_penalty == 0.3

    # Test validation
    with pytest.raises(ValidationError):
        ChatCompletionRequest(
            model="gpt-4",
            messages=[Message(role=Role.USER, content="Test")],
            presence_penalty=3.0,  # Max is 2.0
        )


def test_n_parameter_multiple_choices():
    """Test generating multiple completion choices."""
    request = ChatCompletionRequest(
        model="gpt-4",
        messages=[Message(role=Role.USER, content="Generate variations")],
        n=3,
    )
    assert request.n == 3

    # Test validation (n must be >= 1)
    with pytest.raises(ValidationError):
        ChatCompletionRequest(
            model="gpt-4", messages=[Message(role=Role.USER, content="Test")], n=0
        )


def test_message_with_name():
    """Test message with name field."""
    msg = Message(role=Role.USER, content="Hello", name="john_doe")
    assert msg.name == "john_doe"


def test_tool_message():
    """Test tool response message."""
    msg = Message(
        role=Role.TOOL, content='{"result": "success"}', tool_call_id="call_abc123"
    )
    assert msg.role == Role.TOOL
    assert msg.tool_call_id == "call_abc123"
    assert "success" in msg.content


def test_system_fingerprint():
    """Test system fingerprint in responses."""
    response = ChatCompletionResponse(
        id="chatcmpl-abc123",
        object="chat.completion",
        created=1234567890,
        model="gpt-4",
        choices=[
            ChatCompletionChoice(
                index=0,
                message=Message(role=Role.ASSISTANT, content="Hi"),
                finish_reason="stop",
            )
        ],
        usage=Usage(prompt_tokens=5, completion_tokens=1, total_tokens=6),
        system_fingerprint="fp_abc123def",
    )
    assert response.system_fingerprint == "fp_abc123def"


def test_streaming_with_reasoning_content():
    """Test streaming chunks with reasoning content."""
    chunk = ChatCompletionChunk(
        id="chatcmpl-abc123",
        object="chat.completion.chunk",
        created=1234567890,
        model="gpt-oss-120b",
        choices=[
            ChatCompletionChunkChoice(
                index=0,
                delta=Delta(reasoning_content="Thinking step by step..."),
                finish_reason=None,
            )
        ],
    )
    assert chunk.choices[0].delta.reasoning_content is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
