"""
Chat completion Pydantic models for the OpenAI API.

This module contains all models related to chat completions including
requests, responses, streaming, tool calling, and logprobs.
"""

#  SPDX-License-Identifier: Apache-2.0

from typing import Any, Literal

from pydantic import BaseModel, Field

from ._base import AudioOutput, Role, Usage
from ._content import AudioConfig, ContentPart


class ChatLogprob(BaseModel):
    """Log probability information for a single token."""

    token: str = Field(description="The token.")
    logprob: float = Field(description="The log probability of this token.")
    bytes: list[int] | None = Field(
        default=None, description="Byte representation of the token."
    )
    top_logprobs: list["TopLogprob"] = Field(
        description="Most likely tokens at this position."
    )


class TopLogprob(BaseModel):
    """Top alternative token with log probability."""

    token: str = Field(description="The token.")
    logprob: float = Field(description="The log probability of this token.")
    bytes: list[int] | None = Field(
        default=None, description="Byte representation of the token."
    )


class ChatLogprobs(BaseModel):
    """Log probability information for chat completion."""

    content: list[ChatLogprob] | None = Field(
        default=None, description="Log probability information for each token."
    )


class FunctionCall(BaseModel):
    """Function call information."""

    name: str = Field(description="The name of the function to call.")
    arguments: str = Field(
        description="The arguments to call the function with, encoded as a JSON string."
    )


class ToolCallFunction(BaseModel):
    """Function information for tool calls."""

    name: str = Field(description="The name of the function.")
    arguments: str = Field(
        description="The arguments for the function, encoded as a JSON string."
    )


class ToolCall(BaseModel):
    """Tool call information."""

    id: str = Field(description="The ID of the tool call.")
    type: Literal["function"] = Field(
        default="function", description="The type of tool call."
    )
    function: ToolCallFunction = Field(
        description="The function that the model called."
    )


class ToolChoice(BaseModel):
    """Tool choice."""

    type: Literal["function"] = Field(
        default="function", description="The type of tool."
    )
    function: dict[str, str] = Field(description="The function to use.")


class Tool(BaseModel):
    """Tool definition."""

    type: Literal["function"] = Field(
        default="function", description="The type of tool."
    )
    function: dict[str, Any] = Field(description="The function definition.")


class ResponseFormat(BaseModel):
    """Response format specification."""

    type: Literal["text", "json_object"] = Field(
        default="text", description="The format type."
    )


class JsonSchema(BaseModel):
    """JSON Schema definition for structured outputs."""

    name: str = Field(description="Name of the response format.")
    description: str | None = Field(
        default=None, description="Description of the response format."
    )
    schema: dict[str, Any] = Field(description="JSON Schema object.")
    strict: bool | None = Field(
        default=None, description="Whether to enforce strict schema compliance."
    )


class JsonSchemaResponseFormat(BaseModel):
    """Response format with JSON schema for structured outputs."""

    type: Literal["json_schema"] = Field(
        default="json_schema", description="The format type."
    )
    json_schema: JsonSchema = Field(description="JSON Schema definition.")


class StreamOptions(BaseModel):
    """Options for streaming responses."""

    include_usage: bool = Field(
        default=False,
        description="If set, include usage statistics in the final chunk.",
    )


class Message(BaseModel):
    """Chat message."""

    role: Role = Field(description="The role of the message author.")
    content: str | list[ContentPart] | None = Field(
        default=None,
        description="The content of the message. Can be text string or array of content parts.",
    )
    name: str | None = Field(
        default=None, description="The name of the author of this message."
    )
    tool_calls: list[ToolCall] | None = Field(
        default=None, description="The tool calls made by the assistant."
    )
    tool_call_id: str | None = Field(
        default=None, description="Tool call ID for tool responses."
    )
    function_call: FunctionCall | None = Field(
        default=None, description="Function call information (deprecated)."
    )
    refusal: str | None = Field(
        default=None, description="Refusal message if model refuses to fulfill request."
    )
    reasoning_content: str | None = Field(
        default=None,
        description="Reasoning content showing the model's internal thinking process (gpt-oss and deepseek-ai/DeepSeek-R1 models).",
    )
    audio: AudioOutput | None = Field(
        default=None,
        description="Audio output for assistant messages (when audio modality is requested).",
    )


class PredictionContent(BaseModel):
    """Prediction content for speculative decoding (GPT-4o Predicted Outputs)."""

    type: Literal["content"] = Field(
        default="content",
        description="Type of prediction (currently only 'content' supported)",
    )
    content: str = Field(
        description="Predicted output content to accelerate generation via speculative decoding"
    )


class ChatCompletionRequest(BaseModel):
    """Request for chat completion."""

    model: str = Field(description="ID of the model to use.")
    messages: list[Message] = Field(
        description="A list of messages comprising the conversation so far."
    )
    functions: list[dict[str, Any]] | None = Field(
        default=None, description="Functions the model may call (deprecated)."
    )
    function_call: Literal["auto", "none"] | dict[str, str] | None = Field(
        default=None, description="Function call behavior control (deprecated)."
    )
    tools: list[Tool] | None = Field(
        default=None, description="A list of tools the model may call."
    )
    tool_choice: Literal["auto", "none", "required"] | ToolChoice | None = Field(
        default=None, description="Controls which tool is called by the model."
    )
    parallel_tool_calls: bool | None = Field(
        default=True, description="Whether to enable parallel function calling."
    )
    temperature: float | None = Field(
        default=1.0, ge=0, le=2, description="Sampling temperature."
    )
    top_p: float | None = Field(
        default=1.0, ge=0, le=1, description="Nucleus sampling parameter."
    )
    n: int | None = Field(
        default=1, ge=1, description="Number of completion choices to generate."
    )
    stream: bool | None = Field(
        default=False, description="Whether to stream responses."
    )
    stream_options: StreamOptions | None = Field(
        default=None, description="Options for streaming (only when stream=true)."
    )
    stop: str | list[str] | None = Field(
        default=None,
        description="Sequences where the API will stop generating further tokens.",
    )
    max_tokens: int | None = Field(
        default=None, ge=0, description="Maximum number of tokens to generate."
    )
    max_completion_tokens: int | None = Field(
        default=None,
        ge=0,
        description="Maximum tokens for completion (for deepseek-ai/DeepSeek-R1 series models).",
    )
    presence_penalty: float | None = Field(
        default=0,
        ge=-2.0,
        le=2.0,
        description="Penalty for new tokens based on presence in text so far.",
    )
    frequency_penalty: float | None = Field(
        default=0,
        ge=-2.0,
        le=2.0,
        description="Penalty for new tokens based on frequency in text so far.",
    )
    logit_bias: dict[str, float] | None = Field(
        default=None,
        description="Modify the likelihood of specified tokens appearing in the completion.",
    )
    logprobs: bool | None = Field(
        default=False, description="Whether to return log probabilities."
    )
    top_logprobs: int | None = Field(
        default=None, ge=0, le=20, description="Number of most likely tokens to return."
    )
    user: str | None = Field(
        default=None, description="A unique identifier for the end-user."
    )
    response_format: ResponseFormat | JsonSchemaResponseFormat | None = Field(
        default=None, description="The format of the response."
    )
    seed: int | None = Field(
        default=None, description="Seed for deterministic sampling."
    )
    service_tier: Literal["auto", "default"] | None = Field(
        default=None, description="Service tier for request processing."
    )
    modalities: list[Literal["text", "audio"]] | None = Field(
        default=None, description="Output modalities for the response."
    )
    audio: AudioConfig | None = Field(
        default=None, description="Audio output configuration."
    )
    store: bool | None = Field(
        default=False, description="Whether to store output for model distillation."
    )
    metadata: dict[str, str] | None = Field(
        default=None, description="Developer-defined tags and values."
    )
    prediction: PredictionContent | None = Field(
        default=None,
        description="Predicted output content for speculative decoding (GPT-4o and GPT-4o-mini only). Provides 3-5× speedup.",
    )


class ChatCompletionChoice(BaseModel):
    """A choice in chat completion results."""

    index: int = Field(description="The index of this choice.")
    message: Message = Field(description="The message generated by the model.")
    finish_reason: str | None = Field(
        default=None, description="The reason why generation stopped."
    )
    logprobs: ChatLogprobs | None = Field(
        default=None, description="Log probability information."
    )


class ChatCompletionResponse(BaseModel):
    """Response for chat completion."""

    id: str = Field(description="A unique identifier for this completion.")
    object: Literal["chat.completion"] = Field(
        default="chat.completion", description="The object type."
    )
    created: int = Field(
        description="The Unix timestamp of when this completion was created."
    )
    model: str = Field(description="The model used for completion.")
    choices: list[ChatCompletionChoice] = Field(
        description="The list of completion choices."
    )
    usage: Usage = Field(description="Usage statistics.")
    system_fingerprint: str | None = Field(
        default=None, description="System fingerprint."
    )


class FunctionDelta(BaseModel):
    """Partial function information in streaming."""

    name: str | None = Field(default=None, description="The function name.")
    arguments: str | None = Field(default=None, description="Partial arguments string.")


class ToolCallDelta(BaseModel):
    """Partial tool call information in streaming."""

    index: int = Field(description="Index of the tool call in the array.")
    id: str | None = Field(default=None, description="Tool call ID.")
    type: Literal["function"] | None = Field(default=None, description="Tool type.")
    function: FunctionDelta | None = Field(default=None, description="Function delta.")


class Delta(BaseModel):
    """Partial message content in streaming responses."""

    role: Role | None = Field(
        default=None, description="The role of the message author."
    )
    content: str | None = Field(default=None, description="The content of the message.")
    tool_calls: list[ToolCallDelta] | None = Field(
        default=None, description="Partial tool call information."
    )
    function_call: FunctionCall | None = Field(
        default=None, description="Function call information (deprecated)."
    )
    refusal: str | None = Field(
        default=None, description="Refusal message if model refuses request."
    )
    reasoning_content: str | None = Field(
        default=None,
        description="Partial reasoning content showing model's internal thinking (gpt-oss and deepseek-ai/DeepSeek-R1 models).",
    )
    # Add support for token timing information
    token_timing: list[float] | None = Field(
        default=None, description="Timing information for token generation."
    )


class ChatCompletionChunkChoice(BaseModel):
    """Choice in a streaming chat completion."""

    index: int = Field(description="The index of this choice.")
    delta: Delta = Field(description="The partial message content.")
    finish_reason: str | None = Field(
        default=None, description="The reason why generation stopped."
    )


class ChatCompletionChunk(BaseModel):
    """Streaming response for chat completion."""

    id: str = Field(description="A unique identifier for this completion.")
    object: Literal["chat.completion.chunk"] = Field(
        default="chat.completion.chunk", description="The object type."
    )
    created: int = Field(
        description="The Unix timestamp of when this completion was created."
    )
    model: str = Field(description="The model used for completion.")
    choices: list[ChatCompletionChunkChoice] = Field(
        description="The list of completion choices."
    )
    system_fingerprint: str | None = Field(
        default=None, description="System fingerprint."
    )
    usage: Usage | None = Field(
        default=None,
        description="Usage statistics (only in final chunk if stream_options.include_usage=true).",
    )
