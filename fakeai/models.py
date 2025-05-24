"""
Pydantic models for the OpenAI API.

This module contains all the Pydantic models used to validate and structure
the request and response data for the OpenAI API.
"""
#  SPDX-License-Identifier: Apache-2.0

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field

# Common Models


class ModelPermission(BaseModel):
    """Model permissions."""

    id: str = Field(description="The ID of this model permission.")
    object: Literal["model_permission"] = Field(
        default="model_permission", description="The object type."
    )
    created: int = Field(description="Unix timestamp when this permission was created.")
    allow_create_engine: bool = Field(
        description="Whether the user can create engines with this model."
    )
    allow_sampling: bool = Field(
        description="Whether sampling is allowed on this model."
    )
    allow_logprobs: bool = Field(
        description="Whether logprobs is allowed on this model."
    )
    allow_search_indices: bool = Field(
        description="Whether search indices are allowed for this model."
    )
    allow_view: bool = Field(description="Whether the model can be viewed.")
    allow_fine_tuning: bool = Field(description="Whether the model can be fine-tuned.")
    organization: str = Field(description="The organization this permission is for.")
    group: str | None = Field(
        default=None, description="The group this permission is for."
    )
    is_blocking: bool = Field(description="Whether this permission is blocking.")


class Model(BaseModel):
    """OpenAI model information."""

    id: str = Field(description="The model identifier.")
    object: Literal["model"] = Field(default="model", description="The object type.")
    created: int = Field(description="Unix timestamp when this model was created.")
    owned_by: str = Field(description="Organization that owns the model.")
    permission: list[ModelPermission] = Field(
        description="List of permissions for this model."
    )
    root: str | None = Field(
        default=None, description="Root model from which this model was created."
    )
    parent: str | None = Field(
        default=None, description="Parent model from which this model was created."
    )


class ModelListResponse(BaseModel):
    """Response for listing available models."""

    object: Literal["list"] = Field(default="list", description="The object type.")
    data: list[Model] = Field(description="List of model objects.")


class Usage(BaseModel):
    """Token usage information."""

    prompt_tokens: int = Field(description="Number of tokens used in the prompt.")
    completion_tokens: int | None = Field(
        default=None, description="Number of tokens used in the completion."
    )
    total_tokens: int = Field(description="Total number of tokens used.")


class ErrorDetail(BaseModel):
    """Error details."""

    message: str = Field(description="Error message.")
    type: str = Field(description="Error type.")
    param: str | None = Field(
        default=None, description="Parameter that caused the error."
    )
    code: str | None = Field(default=None, description="Error code.")


class ErrorResponse(BaseModel):
    """Error response."""

    error: ErrorDetail = Field(description="Error details.")


# Chat Completion Models


class Role(str, Enum):
    """Message role."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"
    FUNCTION = "function"


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


class Message(BaseModel):
    """Chat message."""

    role: Role = Field(description="The role of the message author.")
    content: str | None = Field(
        default=None, description="The content of the message."
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
    tool_choice: Literal["auto", "none"] | ToolChoice | None = Field(
        default=None, description="Controls which tool is called by the model."
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
    stop: str | list[str] | None = Field(
        default=None,
        description="Sequences where the API will stop generating further tokens.",
    )
    max_tokens: int | None = Field(
        default=None, ge=0, description="Maximum number of tokens to generate."
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
    user: str | None = Field(
        default=None, description="A unique identifier for the end-user."
    )
    response_format: ResponseFormat | None = Field(
        default=None, description="The format of the response."
    )


class ChatCompletionChoice(BaseModel):
    """A choice in chat completion results."""

    index: int = Field(description="The index of this choice.")
    message: Message = Field(description="The message generated by the model.")
    finish_reason: str | None = Field(
        default=None, description="The reason why generation stopped."
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


class Delta(BaseModel):
    """Partial message content in streaming responses."""

    role: Role | None = Field(
        default=None, description="The role of the message author."
    )
    content: str | None = Field(
        default=None, description="The content of the message."
    )
    function_call: FunctionCall | None = Field(
        default=None, description="Function call information (deprecated)."
    )
    tool_calls: list[ToolCall] | None = Field(
        default=None, description="Tool calls made by the assistant."
    )


class ChatCompletionChunkChoice(BaseModel):
    """A streaming choice in chat completion results."""

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


# Completion Models


class CompletionRequest(BaseModel):
    """Request for text completion."""

    model: str = Field(description="ID of the model to use.")
    prompt: str | list[str] | list[int] | list[list[int]] = Field(
        description="The prompt to generate completions for."
    )
    suffix: str | None = Field(
        default=None, description="The suffix that comes after a completion."
    )
    max_tokens: int | None = Field(
        default=16, ge=0, description="Maximum number of tokens to generate."
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
    logprobs: int | None = Field(
        default=None,
        ge=0,
        le=5,
        description="Include log probabilities on most likely tokens.",
    )
    echo: bool | None = Field(
        default=False, description="Echo the prompt in the completion."
    )
    stop: str | list[str] | None = Field(
        default=None,
        description="Sequences where the API will stop generating further tokens.",
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
    best_of: int | None = Field(
        default=1,
        ge=1,
        description="Generate best_of completions server-side and return the best.",
    )
    logit_bias: dict[str, float] | None = Field(
        default=None,
        description="Modify the likelihood of specified tokens appearing in the completion.",
    )
    user: str | None = Field(
        default=None, description="A unique identifier for the end-user."
    )


class LogProbs(BaseModel):
    """Log probability information."""

    tokens: list[str] = Field(description="The tokens.")
    token_logprobs: list[float] = Field(
        description="The log probabilities of the tokens."
    )
    top_logprobs: list[dict[str, float]] | None = Field(
        default=None, description="The log probabilities of the most likely tokens."
    )
    text_offset: list[int] = Field(description="The text offsets of the tokens.")


class CompletionChoice(BaseModel):
    """A choice in completion results."""

    text: str = Field(description="The completed text.")
    index: int = Field(description="The index of this choice.")
    logprobs: LogProbs | None = Field(
        default=None, description="Log probability information."
    )
    finish_reason: str | None = Field(
        default=None, description="The reason why generation stopped."
    )


class CompletionResponse(BaseModel):
    """Response for text completion."""

    id: str = Field(description="A unique identifier for this completion.")
    object: Literal["text_completion"] = Field(
        default="text_completion", description="The object type."
    )
    created: int = Field(
        description="The Unix timestamp of when this completion was created."
    )
    model: str = Field(description="The model used for completion.")
    choices: list[CompletionChoice] = Field(
        description="The list of completion choices."
    )
    usage: Usage = Field(description="Usage statistics.")


class CompletionChunk(BaseModel):
    """Streaming response for text completion."""

    id: str = Field(description="A unique identifier for this completion.")
    object: Literal["text_completion"] = Field(
        default="text_completion", description="The object type."
    )
    created: int = Field(
        description="The Unix timestamp of when this completion was created."
    )
    model: str = Field(description="The model used for completion.")
    choices: list[CompletionChoice] = Field(
        description="The list of completion choices."
    )


# Embedding Models


class EmbeddingRequest(BaseModel):
    """Request for embeddings."""

    model: str = Field(description="ID of the model to use.")
    input: str | list[str] | list[int] | list[list[int]] = Field(
        description="The input text to get embeddings for."
    )
    user: str | None = Field(
        default=None, description="A unique identifier for the end-user."
    )
    encoding_format: Literal["float", "base64"] | None = Field(
        default="float", description="The format of the embeddings."
    )
    dimensions: int | None = Field(
        default=None, description="The number of dimensions to use for the embeddings."
    )


class Embedding(BaseModel):
    """An embedding result."""

    object: Literal["embedding"] = Field(
        default="embedding", description="The object type."
    )
    embedding: list[float] = Field(description="The embedding vector.")
    index: int = Field(description="The index of the embedding.")


class EmbeddingResponse(BaseModel):
    """Response for embeddings."""

    object: Literal["list"] = Field(default="list", description="The object type.")
    data: list[Embedding] = Field(description="The list of embedding objects.")
    model: str = Field(description="The model used for embeddings.")
    usage: Usage = Field(description="Usage statistics.")


# File Models


class FileObject(BaseModel):
    """File object information."""

    id: str = Field(description="The ID of the file.")
    object: Literal["file"] = Field(default="file", description="The object type.")
    bytes: int = Field(description="The size of the file in bytes.")
    created_at: int = Field(
        description="The Unix timestamp when this file was created."
    )
    filename: str = Field(description="The filename.")
    purpose: str = Field(description="The purpose of the file.")
    status: str | None = Field(default=None, description="The status of the file.")
    status_details: str | None = Field(
        default=None, description="Additional details about the file status."
    )


class FileListResponse(BaseModel):
    """Response for listing files."""

    object: Literal["list"] = Field(default="list", description="The object type.")
    data: list[FileObject] = Field(description="The list of file objects.")


# Image Generation Models


class ImageSize(str, Enum):
    """Available image sizes."""

    SIZE_256 = "256x256"
    SIZE_512 = "512x512"
    SIZE_1024 = "1024x1024"
    SIZE_1792_1024 = "1792x1024"
    SIZE_1024_1792 = "1024x1792"


class ImageQuality(str, Enum):
    """Available image qualities."""

    STANDARD = "standard"
    HD = "hd"


class ImageStyle(str, Enum):
    """Available image styles."""

    VIVID = "vivid"
    NATURAL = "natural"


class ResponseFormat(str, Enum):
    """Available response formats for images."""

    URL = "url"
    B64_JSON = "b64_json"


class GeneratedImage(BaseModel):
    """A generated image."""

    url: str | None = Field(
        default=None, description="The URL of the generated image."
    )
    b64_json: str | None = Field(
        default=None, description="The base64-encoded JSON of the generated image."
    )
    revised_prompt: str | None = Field(
        default=None, description="The revised prompt used to generate the image."
    )


class ImageGenerationRequest(BaseModel):
    """Request for image generation."""

    prompt: str = Field(
        max_length=1000, description="A text description of the desired image(s)."
    )
    model: str | None = Field(
        default="dall-e-2", description="The model to use for image generation."
    )
    n: int | None = Field(
        default=1, ge=1, le=10, description="The number of images to generate."
    )
    quality: ImageQuality | None = Field(
        default=ImageQuality.STANDARD, description="The quality of the image."
    )
    response_format: ResponseFormat | None = Field(
        default=ResponseFormat.URL,
        description="The format in which the images are returned.",
    )
    size: ImageSize | None = Field(
        default=ImageSize.SIZE_1024, description="The size of the generated images."
    )
    style: ImageStyle | None = Field(
        default=ImageStyle.VIVID, description="The style of the generated images."
    )
    user: str | None = Field(
        default=None, description="A unique identifier for the end-user."
    )


class ImageGenerationResponse(BaseModel):
    """Response for image generation."""

    created: int = Field(
        description="The Unix timestamp of when the images were created."
    )
    data: list[GeneratedImage] = Field(description="The list of generated images.")


# Text generation (Azure API compatibility)
class TextGenerationRequest(BaseModel):
    """Request for text generation (Azure API)."""

    input: str = Field(description="The input text to generate from.")
    model: str = Field(description="ID of the model to use.")
    max_output_tokens: int | None = Field(
        default=100, description="The maximum number of tokens to generate."
    )
    temperature: float | None = Field(
        default=1.0, ge=0, le=2, description="The temperature to use for sampling."
    )
    top_p: float | None = Field(
        default=0.95, ge=0, le=1, description="Top-p sampling parameter."
    )
    stop: list[str] | None = Field(
        default=None, description="A list of tokens at which to stop generation."
    )
    user: str | None = Field(
        default=None, description="A unique identifier for the end-user."
    )


class TextGenerationResponse(BaseModel):
    """Response for text generation (Azure API)."""

    id: str = Field(description="A unique identifier for this text generation.")
    created: int = Field(
        description="The Unix timestamp of when this text generation was created."
    )
    output: str = Field(description="The generated text.")
    usage: Usage = Field(description="Usage statistics.")
    model: str = Field(description="The model used for text generation.")
