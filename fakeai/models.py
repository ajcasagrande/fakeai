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


class ModelPricing(BaseModel):
    """Model pricing information per 1M tokens."""

    input_per_million: float = Field(
        description="Cost per 1 million input tokens in USD."
    )
    output_per_million: float = Field(
        description="Cost per 1 million output tokens in USD."
    )
    cached_input_per_million: float | None = Field(
        default=None, description="Cost per 1 million cached input tokens in USD."
    )


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
    context_window: int = Field(
        default=8192, description="Maximum context window size in tokens."
    )
    max_output_tokens: int = Field(
        default=4096, description="Maximum number of tokens that can be generated."
    )
    supports_vision: bool = Field(
        default=False, description="Whether the model supports vision/image inputs."
    )
    supports_audio: bool = Field(
        default=False, description="Whether the model supports audio inputs."
    )
    supports_tools: bool = Field(
        default=True, description="Whether the model supports function/tool calling."
    )
    training_cutoff: str | None = Field(
        default=None, description="Training data cutoff date (YYYY-MM format)."
    )
    pricing: ModelPricing | None = Field(
        default=None, description="Pricing information for the model."
    )


class ModelListResponse(BaseModel):
    """Response for listing available models."""

    object: Literal["list"] = Field(default="list", description="The object type.")
    data: list[Model] = Field(description="List of model objects.")


class ModelCapabilitiesResponse(BaseModel):
    """Response for model capabilities endpoint."""

    id: str = Field(description="The model identifier.")
    object: Literal["model.capabilities"] = Field(
        default="model.capabilities", description="The object type."
    )
    context_window: int = Field(description="Maximum context window size in tokens.")
    max_output_tokens: int = Field(
        description="Maximum number of tokens that can be generated."
    )
    supports_vision: bool = Field(
        description="Whether the model supports vision/image inputs."
    )
    supports_audio: bool = Field(
        description="Whether the model supports audio inputs."
    )
    supports_tools: bool = Field(
        description="Whether the model supports function/tool calling."
    )
    training_cutoff: str | None = Field(
        description="Training data cutoff date (YYYY-MM format)."
    )
    pricing: ModelPricing | None = Field(
        description="Pricing information for the model."
    )


class PromptTokensDetails(BaseModel):
    """Breakdown of prompt tokens."""

    cached_tokens: int = Field(default=0, description="Number of cached tokens.")
    audio_tokens: int = Field(default=0, description="Number of audio tokens.")


class CompletionTokensDetails(BaseModel):
    """Breakdown of completion tokens."""

    reasoning_tokens: int = Field(default=0, description="Number of reasoning tokens.")
    audio_tokens: int = Field(default=0, description="Number of audio tokens.")
    accepted_prediction_tokens: int = Field(
        default=0, description="Number of accepted prediction tokens."
    )
    rejected_prediction_tokens: int = Field(
        default=0, description="Number of rejected prediction tokens."
    )


class Usage(BaseModel):
    """Token usage information."""

    prompt_tokens: int = Field(description="Number of tokens used in the prompt.")
    completion_tokens: int | None = Field(
        default=None, description="Number of tokens used in the completion."
    )
    total_tokens: int = Field(description="Total number of tokens used.")
    prompt_tokens_details: PromptTokensDetails | None = Field(
        default=None, description="Breakdown of prompt tokens."
    )
    completion_tokens_details: CompletionTokensDetails | None = Field(
        default=None, description="Breakdown of completion tokens."
    )

    # For Responses API compatibility
    input_tokens: int | None = Field(
        default=None, description="Alias for prompt_tokens in Responses API."
    )
    output_tokens: int | None = Field(
        default=None, description="Alias for completion_tokens in Responses API."
    )


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


# Multi-Modal Content Models

class TextContent(BaseModel):
    """Text content part."""

    type: Literal["text"] = Field(default="text", description="Content type.")
    text: str = Field(description="The text content.")


class ImageUrl(BaseModel):
    """Image URL configuration."""

    url: str = Field(description="URL of the image or data URI (data:image/*;base64,...).")
    detail: Literal["auto", "low", "high"] = Field(
        default="auto", description="Image detail level for processing."
    )


class ImageContent(BaseModel):
    """Image content part."""

    type: Literal["image_url"] = Field(default="image_url", description="Content type.")
    image_url: ImageUrl = Field(description="Image URL configuration.")


class InputAudio(BaseModel):
    """Input audio configuration."""

    data: str = Field(description="Base64-encoded audio data.")
    format: Literal["wav", "mp3"] = Field(description="Audio format.")


class InputAudioContent(BaseModel):
    """Input audio content part."""

    type: Literal["input_audio"] = Field(default="input_audio", description="Content type.")
    input_audio: InputAudio = Field(description="Audio data and format.")


# Union type for content parts
ContentPart = TextContent | ImageContent | InputAudioContent


# Audio Output Configuration

class AudioConfig(BaseModel):
    """Audio output configuration."""

    voice: Literal[
        "alloy", "ash", "ballad", "coral", "echo",
        "fable", "onyx", "nova", "sage", "shimmer", "verse"
    ] = Field(description="Voice to use for audio output.")
    format: Literal["mp3", "opus", "aac", "flac", "wav", "pcm16"] = Field(
        default="mp3", description="Audio format for output."
    )


class AudioOutput(BaseModel):
    """Audio output in assistant message."""

    id: str = Field(description="Unique identifier for the audio output.")
    data: str = Field(description="Base64-encoded audio data.")
    transcript: str = Field(description="Text transcript of the audio.")
    expires_at: int = Field(description="Unix timestamp when the audio expires.")


# Logprobs Models for Chat Completions

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
        default=False, description="If set, include usage statistics in the final chunk."
    )


class Message(BaseModel):
    """Chat message."""

    role: Role = Field(description="The role of the message author.")
    content: str | list[ContentPart] | None = Field(
        default=None, description="The content of the message. Can be text string or array of content parts."
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
        default=None, description="Reasoning content showing the model's internal thinking process (gpt-oss and deepseek-ai/DeepSeek-R1 models)."
    )
    audio: AudioOutput | None = Field(
        default=None, description="Audio output for assistant messages (when audio modality is requested)."
    )


class PredictionContent(BaseModel):
    """Prediction content for speculative decoding (GPT-4o Predicted Outputs)."""

    type: Literal["content"] = Field(
        default="content",
        description="Type of prediction (currently only 'content' supported)"
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
        default=None, ge=0, description="Maximum tokens for completion (for deepseek-ai/DeepSeek-R1 series models)."
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
        description="Predicted output content for speculative decoding (GPT-4o and GPT-4o-mini only). Provides 3-5× speedup."
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
    content: str | None = Field(
        default=None, description="The content of the message."
    )
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
        default=None, description="Partial reasoning content showing model's internal thinking (gpt-oss and deepseek-ai/DeepSeek-R1 models)."
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
        description="Usage statistics (only in final chunk if stream_options.include_usage=true)."
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
    token_timing: list[float] | None = Field(
        default=None, description="Timing information for token generation."
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

class ImageResponseFormat(str, Enum):
    """Available response formats for images."""

    URL = "url"
    B64_JSON = "b64_json"

class ImageGenerationRequest(BaseModel):
    """Request for image generation."""

    prompt: str = Field(
        max_length=1000, description="A text description of the desired image(s)."
    )
    model: str | None = Field(
        default="stabilityai/stable-diffusion-2-1", description="The model to use for image generation."
    )
    n: int | None = Field(
        default=1, ge=1, le=10, description="The number of images to generate."
    )
    quality: ImageQuality | None = Field(
        default=ImageQuality.STANDARD, description="The quality of the image."
    )
    response_format: ImageResponseFormat | None = Field(
        default=ImageResponseFormat.URL,
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


# Text-to-Speech (Audio Speech API)
class SpeechRequest(BaseModel):
    """Request for text-to-speech audio generation."""

    model: str = Field(description="ID of the model to use for TTS (e.g., tts-1, tts-1-hd).")
    input: str = Field(
        max_length=4096,
        description="The text to generate audio for. Maximum length is 4096 characters."
    )
    voice: Literal["alloy", "echo", "fable", "onyx", "nova", "shimmer", "marin", "cedar"] = Field(
        description="The voice to use for audio generation."
    )
    response_format: Literal["mp3", "opus", "aac", "flac", "wav", "pcm"] = Field(
        default="mp3",
        description="The audio format to return. Supported formats: mp3, opus, aac, flac, wav, pcm."
    )
    speed: float = Field(
        default=1.0,
        ge=0.25,
        le=4.0,
        description="The speed of the generated audio. Range: 0.25 to 4.0."
    )


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


# OpenAI Responses API Models (March 2025)


class ResponsesInput(BaseModel):
    """Input for Responses API - can be string or message array."""

    pass  # Union type handled in request


class ResponsesRequest(BaseModel):
    """Request for OpenAI Responses API."""

    model: str = Field(description="ID of the model to use.")
    input: str | list[Message] = Field(
        description="Text or array of messages."
    )
    instructions: str | None = Field(
        default=None, description="System-level instructions."
    )
    tools: list[Tool] | None = Field(
        default=None, description="Tools the model may use."
    )
    previous_response_id: str | None = Field(
        default=None, description="ID of prior response to continue conversation."
    )
    max_output_tokens: int | None = Field(
        default=None, ge=0, description="Maximum tokens in output."
    )
    temperature: float | None = Field(
        default=None, ge=0, le=2, description="Sampling temperature."
    )
    top_p: float | None = Field(
        default=None, ge=0, le=1, description="Nucleus sampling parameter."
    )
    stream: bool | None = Field(
        default=False, description="Whether to stream via server-sent events."
    )
    store: bool | None = Field(
        default=False, description="Whether to store response for retrieval."
    )
    metadata: dict[str, str] | None = Field(
        default=None, description="Developer-defined tags (max 16 key-value pairs)."
    )
    parallel_tool_calls: bool | None = Field(
        default=True, description="Whether to allow parallel tool execution."
    )
    tool_choice: Literal["auto", "none", "required"] | ToolChoice | None = Field(
        default=None, description="Tool selection strategy."
    )
    response_format: ResponseFormat | JsonSchemaResponseFormat | None = Field(
        default=None, description="Output format specification."
    )
    background: bool | None = Field(
        default=False, description="Whether to run as background task."
    )


class ResponseOutputItem(BaseModel):
    """Base class for response output items."""

    type: str = Field(description="Type of output item.")
    id: str = Field(description="Unique identifier.")
    status: Literal["queued", "in_progress", "completed", "failed"] = Field(
        description="Status of this output item."
    )


class ResponseMessageOutput(ResponseOutputItem):
    """Message output item in Responses API."""

    type: Literal["message"] = Field(default="message", description="Item type.")
    role: Role = Field(description="Message role.")
    content: list[ContentPart] = Field(description="Message content parts.")


class ResponseFunctionCallOutput(ResponseOutputItem):
    """Function call output item in Responses API."""

    type: Literal["function_call"] = Field(default="function_call", description="Item type.")
    call_id: str = Field(description="Tool call ID.")
    name: str = Field(description="Function name.")
    arguments: str = Field(description="Function arguments JSON string.")


class ResponsesResponse(BaseModel):
    """Response from OpenAI Responses API."""

    id: str = Field(description="Unique identifier for response.")
    object: Literal["response"] = Field(default="response", description="Object type.")
    created_at: int = Field(description="Unix timestamp of creation.")
    model: str = Field(description="Model used.")
    status: Literal[
        "queued", "in_progress", "completed", "failed", "cancelled", "incomplete"
    ] = Field(description="Response status.")
    error: ErrorDetail | None = Field(default=None, description="Error details if failed.")
    incomplete_details: dict[str, Any] | None = Field(
        default=None, description="Details about incompletion."
    )
    instructions: str | None = Field(default=None, description="Instructions used.")
    max_output_tokens: int | None = Field(default=None, description="Max tokens specified.")
    metadata: dict[str, str] | None = Field(default=None, description="Metadata.")
    previous_response_id: str | None = Field(
        default=None, description="Previous response ID."
    )
    temperature: float | None = Field(default=None, description="Temperature used.")
    top_p: float | None = Field(default=None, description="Top-p value used.")
    parallel_tool_calls: bool | None = Field(
        default=None, description="Parallel tool calls setting."
    )
    tool_choice: str | dict[str, Any] | None = Field(
        default=None, description="Tool choice used."
    )
    tools: list[Tool] | None = Field(default=None, description="Tools used.")
    output: list[dict[str, Any]] = Field(
        description="Polymorphic output items array."
    )
    usage: Usage | None = Field(default=None, description="Token usage.")


# NVIDIA NIM Rankings API Models


class RankingQuery(BaseModel):
    """Query object for rankings."""

    text: str = Field(description="The search query text.")


class RankingPassage(BaseModel):
    """Passage object for rankings."""

    text: str = Field(description="The passage text content.")


class RankingRequest(BaseModel):
    """Request for NVIDIA NIM rankings."""

    model: str = Field(description="Reranking model identifier.")
    query: RankingQuery = Field(description="Query to rank against.")
    passages: list[RankingPassage] = Field(
        description="Array of passages to rank (max 512)."
    )
    truncate: Literal["NONE", "END"] | None = Field(
        default="NONE", description="Truncation strategy for long sequences."
    )


class RankingObject(BaseModel):
    """Ranking result object."""

    index: int = Field(description="Zero-based index of passage in original request.")
    logit: float = Field(description="Raw unnormalized relevance score (higher is better).")


class RankingResponse(BaseModel):
    """Response from NVIDIA NIM rankings."""

    rankings: list[RankingObject] = Field(
        description="Array of rankings sorted by logit descending."
    )


# Moderation API Models

class ModerationCategories(BaseModel):
    """Boolean flags for moderation categories."""

    sexual: bool = Field(default=False, description="Sexual content.")
    hate: bool = Field(default=False, description="Hate speech.")
    harassment: bool = Field(default=False, description="Harassment.")
    self_harm: bool = Field(default=False, description="Self-harm content.", alias="self-harm")
    sexual_minors: bool = Field(default=False, description="Sexual content involving minors.", alias="sexual/minors")
    hate_threatening: bool = Field(default=False, description="Hateful threatening content.", alias="hate/threatening")
    harassment_threatening: bool = Field(default=False, description="Harassing threatening content.", alias="harassment/threatening")
    self_harm_intent: bool = Field(default=False, description="Self-harm intent.", alias="self-harm/intent")
    self_harm_instructions: bool = Field(default=False, description="Self-harm instructions.", alias="self-harm/instructions")
    violence: bool = Field(default=False, description="Violent content.")
    violence_graphic: bool = Field(default=False, description="Graphic violence.", alias="violence/graphic")
    illicit: bool = Field(default=False, description="Illicit activities.")
    illicit_violent: bool = Field(default=False, description="Violent illicit activities.", alias="illicit/violent")

    class Config:
        populate_by_name = True


class ModerationCategoryScores(BaseModel):
    """Confidence scores for moderation categories (0.0-1.0)."""

    sexual: float = Field(default=0.0, ge=0.0, le=1.0, description="Sexual content score.")
    hate: float = Field(default=0.0, ge=0.0, le=1.0, description="Hate speech score.")
    harassment: float = Field(default=0.0, ge=0.0, le=1.0, description="Harassment score.")
    self_harm: float = Field(default=0.0, ge=0.0, le=1.0, description="Self-harm score.", alias="self-harm")
    sexual_minors: float = Field(default=0.0, ge=0.0, le=1.0, description="Sexual minors score.", alias="sexual/minors")
    hate_threatening: float = Field(default=0.0, ge=0.0, le=1.0, description="Hate threatening score.", alias="hate/threatening")
    harassment_threatening: float = Field(default=0.0, ge=0.0, le=1.0, description="Harassment threatening score.", alias="harassment/threatening")
    self_harm_intent: float = Field(default=0.0, ge=0.0, le=1.0, description="Self-harm intent score.", alias="self-harm/intent")
    self_harm_instructions: float = Field(default=0.0, ge=0.0, le=1.0, description="Self-harm instructions score.", alias="self-harm/instructions")
    violence: float = Field(default=0.0, ge=0.0, le=1.0, description="Violence score.")
    violence_graphic: float = Field(default=0.0, ge=0.0, le=1.0, description="Graphic violence score.", alias="violence/graphic")
    illicit: float = Field(default=0.0, ge=0.0, le=1.0, description="Illicit score.")
    illicit_violent: float = Field(default=0.0, ge=0.0, le=1.0, description="Violent illicit score.", alias="illicit/violent")

    class Config:
        populate_by_name = True


class ModerationResult(BaseModel):
    """Single moderation result."""

    flagged: bool = Field(description="True if any category violated.")
    categories: ModerationCategories = Field(description="Category flags.")
    category_scores: ModerationCategoryScores = Field(description="Category scores.")
    category_applied_input_types: dict[str, list[str]] = Field(
        default_factory=dict,
        description="Which input types (text/image) triggered each category."
    )


class ModerationRequest(BaseModel):
    """Request for content moderation."""

    input: str | list[str] | list[dict[str, Any]] = Field(
        description="Text, array of texts, or multimodal content to moderate."
    )
    model: str | None = Field(
        default="omni-moderation-latest",
        description="Moderation model ID."
    )


class ModerationResponse(BaseModel):
    """Response from moderation endpoint."""

    id: str = Field(description="Unique moderation ID.")
    model: str = Field(description="Model used.")
    results: list[ModerationResult] = Field(description="Moderation results.")


# Whisper API Models (Audio Transcription)


class TranscriptionWord(BaseModel):
    """Word-level timing information in transcription."""

    word: str = Field(description="The transcribed word.")
    start: float = Field(description="Start time in seconds.")
    end: float = Field(description="End time in seconds.")


class TranscriptionSegment(BaseModel):
    """Segment-level transcription with timing and metadata."""

    id: int = Field(description="Segment ID.")
    seek: int = Field(description="Seek offset in samples.")
    start: float = Field(description="Start time in seconds.")
    end: float = Field(description="End time in seconds.")
    text: str = Field(description="Transcribed text for this segment.")
    tokens: list[int] = Field(description="Token IDs for this segment.")
    temperature: float = Field(description="Temperature used for this segment.")
    avg_logprob: float = Field(description="Average log probability of tokens.")
    compression_ratio: float = Field(description="Compression ratio of tokens to text.")
    no_speech_prob: float = Field(description="Probability that this segment contains no speech.")


class TranscriptionRequest(BaseModel):
    """Request for audio transcription (Whisper API)."""

    model: str = Field(description="Whisper model ID (e.g., whisper-1).")
    language: str | None = Field(
        default=None,
        description="Language of the audio in ISO-639-1 format (e.g., 'en', 'es')."
    )
    prompt: str | None = Field(
        default=None,
        description="Optional text to guide the model's style or continue from previous audio."
    )
    response_format: Literal["json", "text", "srt", "verbose_json", "vtt"] | None = Field(
        default="json",
        description="Format of the transcript output."
    )
    temperature: float | None = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Sampling temperature between 0 and 1."
    )
    timestamp_granularities: list[Literal["word", "segment"]] | None = Field(
        default=None,
        description="Timestamp granularities to include (word and/or segment level)."
    )


class TranscriptionResponse(BaseModel):
    """Response from transcription endpoint (JSON format)."""

    text: str = Field(description="The transcribed text.")


class VerboseTranscriptionResponse(BaseModel):
    """Response from transcription endpoint (verbose_json format)."""

    task: Literal["transcribe"] = Field(
        default="transcribe",
        description="The task performed (always 'transcribe')."
    )
    language: str = Field(description="Detected or specified language code.")
    duration: float = Field(description="Duration of the audio in seconds.")
    text: str = Field(description="The complete transcribed text.")
    words: list[TranscriptionWord] | None = Field(
        default=None,
        description="Word-level timestamps (if requested)."
    )
    segments: list[TranscriptionSegment] | None = Field(
        default=None,
        description="Segment-level transcription with timing."
    )


# Batch API Models


class BatchRequestCounts(BaseModel):
    """Counts of batch requests by status."""

    total: int = Field(description="Total number of requests in the batch.")
    completed: int = Field(default=0, description="Number of requests completed.")
    failed: int = Field(default=0, description="Number of requests that failed.")


class Batch(BaseModel):
    """Batch object representing a batch processing job."""

    id: str = Field(description="The batch identifier.")
    object: Literal["batch"] = Field(default="batch", description="The object type.")
    endpoint: str = Field(description="The API endpoint used (e.g., /v1/chat/completions).")
    errors: dict[str, Any] | None = Field(
        default=None, description="Error information if the batch failed."
    )
    input_file_id: str = Field(description="The ID of the input file for the batch.")
    completion_window: str = Field(
        description="The time window for completion (e.g., '24h')."
    )
    status: Literal[
        "validating",
        "failed",
        "in_progress",
        "finalizing",
        "completed",
        "expired",
        "cancelling",
        "cancelled",
    ] = Field(description="The current status of the batch.")
    output_file_id: str | None = Field(
        default=None, description="The ID of the output file (once completed)."
    )
    error_file_id: str | None = Field(
        default=None, description="The ID of the error file (if errors occurred)."
    )
    created_at: int = Field(description="Unix timestamp when the batch was created.")
    in_progress_at: int | None = Field(
        default=None, description="Unix timestamp when batch processing started."
    )
    expires_at: int | None = Field(
        default=None, description="Unix timestamp when the batch will expire."
    )
    finalizing_at: int | None = Field(
        default=None, description="Unix timestamp when batch finalization started."
    )
    completed_at: int | None = Field(
        default=None, description="Unix timestamp when the batch completed."
    )
    failed_at: int | None = Field(
        default=None, description="Unix timestamp when the batch failed."
    )
    expired_at: int | None = Field(
        default=None, description="Unix timestamp when the batch expired."
    )
    cancelling_at: int | None = Field(
        default=None, description="Unix timestamp when cancellation started."
    )
    cancelled_at: int | None = Field(
        default=None, description="Unix timestamp when the batch was cancelled."
    )
    request_counts: BatchRequestCounts = Field(
        description="Counts of requests by status."
    )
    metadata: dict[str, str] | None = Field(
        default=None, description="Developer-provided metadata."
    )


class CreateBatchRequest(BaseModel):
    """Request to create a new batch."""

    input_file_id: str = Field(description="The ID of the input file (JSONL format).")
    endpoint: str = Field(
        description="The API endpoint to call (e.g., /v1/chat/completions)."
    )
    completion_window: str = Field(
        description="Time window for completion (e.g., '24h')."
    )
    metadata: dict[str, str] | None = Field(
        default=None, description="Optional developer metadata."
    )


class BatchListResponse(BaseModel):
    """Response for listing batches."""

    object: Literal["list"] = Field(default="list", description="The object type.")
    data: list[Batch] = Field(description="List of batch objects.")
    first_id: str | None = Field(default=None, description="ID of the first batch.")
    last_id: str | None = Field(default=None, description="ID of the last batch.")
    has_more: bool = Field(default=False, description="Whether there are more batches.")


class BatchRequest(BaseModel):
    """Single request in a batch JSONL file."""

    custom_id: str = Field(description="Developer-provided ID for this request.")
    method: Literal["POST"] = Field(description="HTTP method (always POST).")
    url: str = Field(description="The API endpoint URL (e.g., /v1/chat/completions).")
    body: dict[str, Any] = Field(description="The request body.")


class BatchOutputResponse(BaseModel):
    """Single response in a batch output JSONL file."""

    id: str = Field(description="Unique ID for this response.")
    custom_id: str = Field(description="The custom_id from the request.")
    response: dict[str, Any] | None = Field(
        default=None, description="The API response (if successful)."
    )
    error: dict[str, Any] | None = Field(
        default=None, description="Error information (if failed)."
    )


# Vector Stores API Models


class ChunkingStrategyType(str, Enum):
    """Available chunking strategies for vector stores."""

    AUTO = "auto"
    STATIC = "static"


class StaticChunkingStrategy(BaseModel):
    """Static chunking strategy configuration."""

    type: Literal["static"] = Field(
        default="static", description="The chunking strategy type."
    )
    max_chunk_size_tokens: int = Field(
        description="Maximum number of tokens in each chunk.",
        ge=100,
        le=4096,
    )
    chunk_overlap_tokens: int = Field(
        description="Number of tokens that overlap between chunks.",
        ge=0,
    )


class AutoChunkingStrategy(BaseModel):
    """Auto chunking strategy (default)."""

    type: Literal["auto"] = Field(
        default="auto", description="The chunking strategy type."
    )


ChunkingStrategy = StaticChunkingStrategy | AutoChunkingStrategy


class FileCounts(BaseModel):
    """Counts of files in various states in a vector store."""

    in_progress: int = Field(
        default=0, description="Number of files currently being processed."
    )
    completed: int = Field(default=0, description="Number of files successfully processed.")
    failed: int = Field(default=0, description="Number of files that failed processing.")
    cancelled: int = Field(default=0, description="Number of files that were cancelled.")
    total: int = Field(default=0, description="Total number of files.")


class ExpiresAfter(BaseModel):
    """Expiration policy for a vector store."""

    anchor: Literal["last_active_at"] = Field(
        description="Anchor timestamp for expiration (e.g., 'last_active_at')."
    )
    days: int = Field(
        description="Number of days after anchor before expiration.", ge=1, le=365
    )


class RankingOptions(BaseModel):
    """Ranking options for search results."""

    ranker: Literal["auto", "default_2024_08_21"] = Field(
        default="auto",
        description="The ranker to use for search results.",
    )
    score_threshold: float = Field(
        description="Minimum similarity score for results.",
        ge=0.0,
        le=1.0,
    )


class VectorStore(BaseModel):
    """Vector store object for semantic search."""

    id: str = Field(description="The vector store identifier.")
    object: Literal["vector_store"] = Field(
        default="vector_store", description="The object type."
    )
    created_at: int = Field(
        description="Unix timestamp when the vector store was created."
    )
    name: str = Field(description="The name of the vector store.")
    usage_bytes: int = Field(
        default=0, description="Total size of files in the vector store in bytes."
    )
    file_counts: FileCounts = Field(
        default_factory=FileCounts, description="File counts by status."
    )
    status: Literal["expired", "in_progress", "completed"] = Field(
        description="The status of the vector store."
    )
    expires_after: ExpiresAfter | None = Field(
        default=None, description="Expiration policy for the vector store."
    )
    expires_at: int | None = Field(
        default=None, description="Unix timestamp when the vector store will expire."
    )
    last_active_at: int | None = Field(
        default=None, description="Unix timestamp of last activity."
    )
    metadata: dict[str, str] | None = Field(
        default=None, description="Developer-provided metadata."
    )


class CreateVectorStoreRequest(BaseModel):
    """Request to create a new vector store."""

    file_ids: list[str] | None = Field(
        default=None, description="List of file IDs to add to the vector store."
    )
    name: str = Field(description="The name of the vector store.")
    expires_after: ExpiresAfter | None = Field(
        default=None, description="Expiration policy for the vector store."
    )
    chunking_strategy: ChunkingStrategy | None = Field(
        default=None, description="Chunking strategy for the vector store."
    )
    metadata: dict[str, str] | None = Field(
        default=None, description="Developer-provided metadata."
    )


class ModifyVectorStoreRequest(BaseModel):
    """Request to modify an existing vector store."""

    name: str | None = Field(default=None, description="Updated name.")
    expires_after: ExpiresAfter | None = Field(
        default=None, description="Updated expiration policy."
    )
    metadata: dict[str, str] | None = Field(
        default=None, description="Updated metadata."
    )


class VectorStoreListResponse(BaseModel):
    """Response for listing vector stores."""

    object: Literal["list"] = Field(default="list", description="The object type.")
    data: list[VectorStore] = Field(description="List of vector store objects.")
    first_id: str | None = Field(default=None, description="ID of the first vector store.")
    last_id: str | None = Field(default=None, description="ID of the last vector store.")
    has_more: bool = Field(
        default=False, description="Whether there are more vector stores."
    )


class VectorStoreFile(BaseModel):
    """File attached to a vector store."""

    id: str = Field(description="The vector store file identifier.")
    object: Literal["vector_store.file"] = Field(
        default="vector_store.file", description="The object type."
    )
    usage_bytes: int = Field(
        default=0, description="Size of the file in bytes after processing."
    )
    created_at: int = Field(
        description="Unix timestamp when the file was added to the vector store."
    )
    vector_store_id: str = Field(
        description="The ID of the vector store this file belongs to."
    )
    status: Literal["in_progress", "completed", "cancelled", "failed"] = Field(
        description="The status of the file in the vector store."
    )
    last_error: dict[str, Any] | None = Field(
        default=None, description="Error information if processing failed."
    )
    chunking_strategy: ChunkingStrategy | None = Field(
        default=None, description="The chunking strategy used for this file."
    )


class CreateVectorStoreFileRequest(BaseModel):
    """Request to add a file to a vector store."""

    file_id: str = Field(description="The ID of the file to add.")
    chunking_strategy: ChunkingStrategy | None = Field(
        default=None, description="Chunking strategy for this file."
    )


class VectorStoreFileListResponse(BaseModel):
    """Response for listing vector store files."""

    object: Literal["list"] = Field(default="list", description="The object type.")
    data: list[VectorStoreFile] = Field(description="List of vector store file objects.")
    first_id: str | None = Field(default=None, description="ID of the first file.")
    last_id: str | None = Field(default=None, description="ID of the last file.")
    has_more: bool = Field(default=False, description="Whether there are more files.")


class VectorStoreFileBatch(BaseModel):
    """Batch of files being added to a vector store."""

    id: str = Field(description="The file batch identifier.")
    object: Literal["vector_store.files_batch"] = Field(
        default="vector_store.files_batch", description="The object type."
    )
    created_at: int = Field(
        description="Unix timestamp when the batch was created."
    )
    vector_store_id: str = Field(
        description="The ID of the vector store."
    )
    status: Literal["in_progress", "completed", "cancelled", "failed"] = Field(
        description="The status of the file batch."
    )
    file_counts: FileCounts = Field(
        description="File counts by status in the batch."
    )


class CreateVectorStoreFileBatchRequest(BaseModel):
    """Request to create a batch of files in a vector store."""

    file_ids: list[str] = Field(
        description="List of file IDs to add to the vector store."
    )
    chunking_strategy: ChunkingStrategy | None = Field(
        default=None, description="Chunking strategy for the files."
    )


# Organization and Project Management API Models


class OrganizationRole(str, Enum):
    """Role in an organization."""

    OWNER = "owner"
    READER = "reader"


class ProjectRole(str, Enum):
    """Role in a project."""

    OWNER = "owner"
    MEMBER = "member"


class ServiceAccountRole(str, Enum):
    """Role for service accounts."""

    OWNER = "owner"
    MEMBER = "member"


class OrganizationUser(BaseModel):
    """User within an organization."""

    object: Literal["organization.user"] = Field(
        default="organization.user", description="The object type."
    )
    id: str = Field(description="The user identifier.")
    name: str = Field(description="The name of the user.")
    email: str = Field(description="The email address of the user.")
    role: OrganizationRole = Field(description="The role of the user in the organization.")
    added_at: int = Field(description="Unix timestamp when the user was added.")


class OrganizationUserListResponse(BaseModel):
    """Response for listing organization users."""

    object: Literal["list"] = Field(default="list", description="The object type.")
    data: list[OrganizationUser] = Field(description="List of organization user objects.")
    first_id: str | None = Field(default=None, description="ID of the first user.")
    last_id: str | None = Field(default=None, description="ID of the last user.")
    has_more: bool = Field(default=False, description="Whether there are more users.")


class CreateOrganizationUserRequest(BaseModel):
    """Request to add a user to an organization."""

    email: str = Field(description="Email address of the user to add.")
    role: OrganizationRole = Field(description="Role to assign to the user.")


class ModifyOrganizationUserRequest(BaseModel):
    """Request to modify an organization user."""

    role: OrganizationRole = Field(description="New role for the user.")


class OrganizationInvite(BaseModel):
    """Invitation to join an organization."""

    object: Literal["organization.invite"] = Field(
        default="organization.invite", description="The object type."
    )
    id: str = Field(description="The invite identifier.")
    email: str = Field(description="The email address of the invited user.")
    role: OrganizationRole = Field(description="The role the user will have.")
    status: Literal["pending", "accepted", "expired"] = Field(
        description="Status of the invitation."
    )
    invited_at: int = Field(description="Unix timestamp when the invite was created.")
    expires_at: int = Field(description="Unix timestamp when the invite expires.")
    accepted_at: int | None = Field(
        default=None, description="Unix timestamp when the invite was accepted."
    )


class OrganizationInviteListResponse(BaseModel):
    """Response for listing organization invites."""

    object: Literal["list"] = Field(default="list", description="The object type.")
    data: list[OrganizationInvite] = Field(description="List of organization invite objects.")
    first_id: str | None = Field(default=None, description="ID of the first invite.")
    last_id: str | None = Field(default=None, description="ID of the last invite.")
    has_more: bool = Field(default=False, description="Whether there are more invites.")


class CreateOrganizationInviteRequest(BaseModel):
    """Request to create an organization invite."""

    email: str = Field(description="Email address to invite.")
    role: OrganizationRole = Field(description="Role to assign to the invited user.")


class DeleteOrganizationInviteResponse(BaseModel):
    """Response for deleting an organization invite."""

    object: Literal["organization.invite.deleted"] = Field(
        default="organization.invite.deleted", description="The object type."
    )
    id: str = Field(description="The ID of the deleted invite.")
    deleted: bool = Field(default=True, description="Whether the invite was deleted.")


class OrganizationProject(BaseModel):
    """Project within an organization."""

    object: Literal["organization.project"] = Field(
        default="organization.project", description="The object type."
    )
    id: str = Field(description="The project identifier.")
    name: str = Field(description="The name of the project.")
    created_at: int = Field(description="Unix timestamp when the project was created.")
    archived_at: int | None = Field(
        default=None, description="Unix timestamp when the project was archived."
    )
    status: Literal["active", "archived"] = Field(
        default="active", description="The status of the project."
    )


class OrganizationProjectListResponse(BaseModel):
    """Response for listing organization projects."""

    object: Literal["list"] = Field(default="list", description="The object type.")
    data: list[OrganizationProject] = Field(description="List of organization project objects.")
    first_id: str | None = Field(default=None, description="ID of the first project.")
    last_id: str | None = Field(default=None, description="ID of the last project.")
    has_more: bool = Field(default=False, description="Whether there are more projects.")


class CreateOrganizationProjectRequest(BaseModel):
    """Request to create a new project."""

    name: str = Field(description="The name of the project.")


class ModifyOrganizationProjectRequest(BaseModel):
    """Request to modify a project."""

    name: str = Field(description="The new name of the project.")


class ArchiveOrganizationProjectResponse(BaseModel):
    """Response for archiving a project."""

    object: Literal["organization.project.archived"] = Field(
        default="organization.project.archived", description="The object type."
    )
    id: str = Field(description="The ID of the archived project.")
    archived: bool = Field(default=True, description="Whether the project was archived.")


class ProjectUser(BaseModel):
    """User within a project."""

    object: Literal["organization.project.user"] = Field(
        default="organization.project.user", description="The object type."
    )
    id: str = Field(description="The user identifier.")
    name: str = Field(description="The name of the user.")
    email: str = Field(description="The email address of the user.")
    role: ProjectRole = Field(description="The role of the user in the project.")
    added_at: int = Field(description="Unix timestamp when the user was added to the project.")


class ProjectUserListResponse(BaseModel):
    """Response for listing project users."""

    object: Literal["list"] = Field(default="list", description="The object type.")
    data: list[ProjectUser] = Field(description="List of project user objects.")
    first_id: str | None = Field(default=None, description="ID of the first user.")
    last_id: str | None = Field(default=None, description="ID of the last user.")
    has_more: bool = Field(default=False, description="Whether there are more users.")


class CreateProjectUserRequest(BaseModel):
    """Request to add a user to a project."""

    user_id: str = Field(description="The ID of the user to add to the project.")
    role: ProjectRole = Field(description="Role to assign to the user in the project.")


class ModifyProjectUserRequest(BaseModel):
    """Request to modify a project user."""

    role: ProjectRole = Field(description="New role for the user in the project.")


class DeleteProjectUserResponse(BaseModel):
    """Response for removing a user from a project."""

    object: Literal["organization.project.user.deleted"] = Field(
        default="organization.project.user.deleted", description="The object type."
    )
    id: str = Field(description="The ID of the removed user.")
    deleted: bool = Field(default=True, description="Whether the user was removed.")


class ServiceAccount(BaseModel):
    """Service account for API access."""

    object: Literal["organization.project.service_account"] = Field(
        default="organization.project.service_account", description="The object type."
    )
    id: str = Field(description="The service account identifier.")
    name: str = Field(description="The name of the service account.")
    role: ServiceAccountRole = Field(description="The role of the service account.")
    created_at: int = Field(description="Unix timestamp when the service account was created.")


class ServiceAccountListResponse(BaseModel):
    """Response for listing service accounts."""

    object: Literal["list"] = Field(default="list", description="The object type.")
    data: list[ServiceAccount] = Field(description="List of service account objects.")
    first_id: str | None = Field(default=None, description="ID of the first service account.")
    last_id: str | None = Field(default=None, description="ID of the last service account.")
    has_more: bool = Field(default=False, description="Whether there are more service accounts.")


class CreateServiceAccountRequest(BaseModel):
    """Request to create a service account."""

    name: str = Field(description="The name of the service account.")
    role: ServiceAccountRole = Field(
        default=ServiceAccountRole.MEMBER, description="Role for the service account."
    )


class DeleteServiceAccountResponse(BaseModel):
    """Response for deleting a service account."""

    object: Literal["organization.project.service_account.deleted"] = Field(
        default="organization.project.service_account.deleted", description="The object type."
    )
    id: str = Field(description="The ID of the deleted service account.")
    deleted: bool = Field(default=True, description="Whether the service account was deleted.")


# Usage and Billing API Models


class UsageTimeBucket(BaseModel):
    """Time bucket for usage aggregation."""

    object: Literal["bucket"] = Field(default="bucket", description="The object type.")
    start_time: int = Field(description="Unix timestamp for start of bucket.")
    end_time: int = Field(description="Unix timestamp for end of bucket.")


class UsageResultItem(BaseModel):
    """Individual usage result item."""

    object: Literal["organization.usage.result"] = Field(
        default="organization.usage.result", description="The object type."
    )
    input_tokens: int = Field(default=0, description="Number of input tokens.")
    output_tokens: int = Field(default=0, description="Number of output tokens.")
    input_cached_tokens: int = Field(default=0, description="Number of cached input tokens.")
    num_model_requests: int = Field(default=0, description="Number of requests.")


class UsageAggregationBucket(BaseModel):
    """Usage aggregated by time bucket."""

    object: Literal["bucket"] = Field(default="bucket", description="The object type.")
    start_time: int = Field(description="Unix timestamp for start of bucket.")
    end_time: int = Field(description="Unix timestamp for end of bucket.")
    results: list[UsageResultItem] = Field(description="Usage results for this time bucket.")


class CompletionsUsageResponse(BaseModel):
    """Response for completions usage data."""

    object: Literal["page"] = Field(default="page", description="The object type.")
    data: list[UsageAggregationBucket] = Field(description="List of usage buckets.")
    has_more: bool = Field(default=False, description="Whether there are more results.")
    next_page: str | None = Field(default=None, description="URL for next page.")


class EmbeddingsUsageResponse(BaseModel):
    """Response for embeddings usage data."""

    object: Literal["page"] = Field(default="page", description="The object type.")
    data: list[UsageAggregationBucket] = Field(description="List of usage buckets.")
    has_more: bool = Field(default=False, description="Whether there are more results.")
    next_page: str | None = Field(default=None, description="URL for next page.")


class ImagesUsageResponse(BaseModel):
    """Response for images usage data."""

    object: Literal["page"] = Field(default="page", description="The object type.")
    data: list[UsageAggregationBucket] = Field(description="List of usage buckets.")
    has_more: bool = Field(default=False, description="Whether there are more results.")
    next_page: str | None = Field(default=None, description="URL for next page.")


class AudioSpeechesUsageResponse(BaseModel):
    """Response for audio speeches usage data."""

    object: Literal["page"] = Field(default="page", description="The object type.")
    data: list[UsageAggregationBucket] = Field(description="List of usage buckets.")
    has_more: bool = Field(default=False, description="Whether there are more results.")
    next_page: str | None = Field(default=None, description="URL for next page.")


class AudioTranscriptionsUsageResponse(BaseModel):
    """Response for audio transcriptions usage data."""

    object: Literal["page"] = Field(default="page", description="The object type.")
    data: list[UsageAggregationBucket] = Field(description="List of usage buckets.")
    has_more: bool = Field(default=False, description="Whether there are more results.")
    next_page: str | None = Field(default=None, description="URL for next page.")


class CostAmount(BaseModel):
    """Cost amount in USD."""

    value: float = Field(description="Cost value in USD.")
    currency: Literal["usd"] = Field(default="usd", description="Currency code.")


class CostResult(BaseModel):
    """Cost result with details."""

    object: Literal["organization.costs.result"] = Field(
        default="organization.costs.result", description="The object type."
    )
    amount: CostAmount = Field(description="Total cost amount.")
    line_item: str = Field(description="Line item category (e.g., 'completions', 'embeddings').")
    project_id: str | None = Field(default=None, description="Project ID if applicable.")


class CostBucket(BaseModel):
    """Cost aggregated by time bucket."""

    object: Literal["bucket"] = Field(default="bucket", description="The object type.")
    start_time: int = Field(description="Unix timestamp for start of bucket.")
    end_time: int = Field(description="Unix timestamp for end of bucket.")
    results: list[CostResult] = Field(description="Cost results for this time bucket.")


class CostsResponse(BaseModel):
    """Response for costs data."""

    object: Literal["page"] = Field(default="page", description="The object type.")
    data: list[CostBucket] = Field(description="List of cost buckets.")
    has_more: bool = Field(default=False, description="Whether there are more results.")
    next_page: str | None = Field(default=None, description="URL for next page.")


# Realtime WebSocket API Models


class RealtimeVoice(str, Enum):
    """Voice options for Realtime API."""

    ALLOY = "alloy"
    ASH = "ash"
    BALLAD = "ballad"
    CORAL = "coral"
    ECHO = "echo"
    SAGE = "sage"
    SHIMMER = "shimmer"
    VERSE = "verse"


class RealtimeAudioFormat(str, Enum):
    """Audio format options for Realtime API."""

    PCM16 = "pcm16"
    G711_ULAW = "g711_ulaw"
    G711_ALAW = "g711_alaw"


class RealtimeModality(str, Enum):
    """Modality options for Realtime API."""

    TEXT = "text"
    AUDIO = "audio"


class RealtimeTurnDetectionType(str, Enum):
    """Turn detection type for Realtime API."""

    SERVER_VAD = "server_vad"


class RealtimeToolType(str, Enum):
    """Tool type for Realtime API."""

    FUNCTION = "function"


class RealtimeToolChoice(str, Enum):
    """Tool choice options."""

    AUTO = "auto"
    NONE = "none"
    REQUIRED = "required"


class RealtimeInputAudioTranscription(BaseModel):
    """Configuration for input audio transcription."""

    model: str = Field(default="whisper-1", description="The model to use for transcription.")


class RealtimeTurnDetection(BaseModel):
    """Configuration for turn detection."""

    type: RealtimeTurnDetectionType = Field(
        default=RealtimeTurnDetectionType.SERVER_VAD,
        description="Type of turn detection.",
    )
    threshold: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Activation threshold for VAD (0.0 to 1.0).",
    )
    prefix_padding_ms: int = Field(
        default=300,
        description="Amount of audio to include before speech starts (ms).",
    )
    silence_duration_ms: int = Field(
        default=500,
        description="Duration of silence to detect end of speech (ms).",
    )
    create_response: bool = Field(
        default=True,
        description="Whether to automatically create a response when speech is detected.",
    )


class RealtimeTool(BaseModel):
    """Tool definition for Realtime API."""

    type: RealtimeToolType = Field(
        default=RealtimeToolType.FUNCTION,
        description="The type of the tool.",
    )
    name: str = Field(description="The name of the function.")
    description: str = Field(description="Description of what the function does.")
    parameters: dict[str, Any] = Field(
        default_factory=dict,
        description="JSON Schema for the function parameters.",
    )


class RealtimeSessionConfig(BaseModel):
    """Configuration for a Realtime session."""

    modalities: list[RealtimeModality] = Field(
        default=[RealtimeModality.TEXT, RealtimeModality.AUDIO],
        description="The modalities for the session.",
    )
    instructions: str = Field(
        default="",
        description="System instructions for the model.",
    )
    voice: RealtimeVoice = Field(
        default=RealtimeVoice.ALLOY,
        description="The voice to use for audio output.",
    )
    input_audio_format: RealtimeAudioFormat = Field(
        default=RealtimeAudioFormat.PCM16,
        description="Format of input audio.",
    )
    output_audio_format: RealtimeAudioFormat = Field(
        default=RealtimeAudioFormat.PCM16,
        description="Format of output audio.",
    )
    input_audio_transcription: RealtimeInputAudioTranscription | None = Field(
        default=None,
        description="Configuration for input audio transcription.",
    )
    turn_detection: RealtimeTurnDetection | None = Field(
        default=None,
        description="Configuration for turn detection.",
    )
    tools: list[RealtimeTool] = Field(
        default_factory=list,
        description="Tools available to the model.",
    )
    tool_choice: str = Field(
        default="auto",
        description="How the model should use tools ('auto', 'none', 'required').",
    )
    temperature: float = Field(
        default=0.8,
        ge=0.6,
        le=1.2,
        description="Sampling temperature.",
    )
    max_response_output_tokens: int | str = Field(
        default="inf",
        description="Maximum tokens in the response.",
    )


class RealtimeSession(BaseModel):
    """Realtime session information."""

    id: str = Field(description="Unique session identifier.")
    object: Literal["realtime.session"] = Field(
        default="realtime.session",
        description="The object type.",
    )
    model: str = Field(description="The model being used.")
    expires_at: int | None = Field(
        default=None,
        description="Unix timestamp when session expires.",
    )
    modalities: list[RealtimeModality] = Field(
        default=[RealtimeModality.TEXT, RealtimeModality.AUDIO],
        description="The modalities for the session.",
    )
    instructions: str = Field(
        default="",
        description="System instructions for the model.",
    )
    voice: RealtimeVoice = Field(
        default=RealtimeVoice.ALLOY,
        description="The voice to use for audio output.",
    )
    input_audio_format: RealtimeAudioFormat = Field(
        default=RealtimeAudioFormat.PCM16,
        description="Format of input audio.",
    )
    output_audio_format: RealtimeAudioFormat = Field(
        default=RealtimeAudioFormat.PCM16,
        description="Format of output audio.",
    )
    input_audio_transcription: RealtimeInputAudioTranscription | None = Field(
        default=None,
        description="Configuration for input audio transcription.",
    )
    turn_detection: RealtimeTurnDetection | None = Field(
        default=None,
        description="Configuration for turn detection.",
    )
    tools: list[RealtimeTool] = Field(
        default_factory=list,
        description="Tools available to the model.",
    )
    tool_choice: str = Field(
        default="auto",
        description="How the model should use tools.",
    )
    temperature: float = Field(
        default=0.8,
        description="Sampling temperature.",
    )
    max_response_output_tokens: int | str = Field(
        default="inf",
        description="Maximum tokens in the response.",
    )


class RealtimeEventType(str, Enum):
    """Event types for Realtime API."""

    # Session events
    SESSION_CREATED = "session.created"
    SESSION_UPDATED = "session.updated"

    # Input audio events
    INPUT_AUDIO_BUFFER_APPEND = "input_audio_buffer.append"
    INPUT_AUDIO_BUFFER_COMMIT = "input_audio_buffer.commit"
    INPUT_AUDIO_BUFFER_CLEAR = "input_audio_buffer.clear"
    INPUT_AUDIO_BUFFER_COMMITTED = "input_audio_buffer.committed"
    INPUT_AUDIO_BUFFER_CLEARED = "input_audio_buffer.cleared"
    INPUT_AUDIO_BUFFER_SPEECH_STARTED = "input_audio_buffer.speech_started"
    INPUT_AUDIO_BUFFER_SPEECH_STOPPED = "input_audio_buffer.speech_stopped"

    # Conversation events
    CONVERSATION_ITEM_CREATE = "conversation.item.create"
    CONVERSATION_ITEM_CREATED = "conversation.item.created"
    CONVERSATION_ITEM_DELETE = "conversation.item.delete"
    CONVERSATION_ITEM_DELETED = "conversation.item.deleted"
    CONVERSATION_ITEM_TRUNCATE = "conversation.item.truncate"
    CONVERSATION_ITEM_TRUNCATED = "conversation.item.truncated"

    # Response events
    RESPONSE_CREATE = "response.create"
    RESPONSE_CREATED = "response.created"
    RESPONSE_DONE = "response.done"
    RESPONSE_CANCEL = "response.cancel"
    RESPONSE_CANCELLED = "response.cancelled"

    # Response content events
    RESPONSE_OUTPUT_ITEM_ADDED = "response.output_item.added"
    RESPONSE_OUTPUT_ITEM_DONE = "response.output_item.done"
    RESPONSE_CONTENT_PART_ADDED = "response.content_part.added"
    RESPONSE_CONTENT_PART_DONE = "response.content_part.done"

    # Response audio events
    RESPONSE_AUDIO_DELTA = "response.audio.delta"
    RESPONSE_AUDIO_DONE = "response.audio.done"
    RESPONSE_AUDIO_TRANSCRIPT_DELTA = "response.audio_transcript.delta"
    RESPONSE_AUDIO_TRANSCRIPT_DONE = "response.audio_transcript.done"

    # Response text events
    RESPONSE_TEXT_DELTA = "response.text.delta"
    RESPONSE_TEXT_DONE = "response.text.done"

    # Response function call events
    RESPONSE_FUNCTION_CALL_ARGUMENTS_DELTA = "response.function_call_arguments.delta"
    RESPONSE_FUNCTION_CALL_ARGUMENTS_DONE = "response.function_call_arguments.done"

    # Rate limit events
    RATE_LIMITS_UPDATED = "rate_limits.updated"

    # Error event
    ERROR = "error"


class RealtimeItemType(str, Enum):
    """Item types for conversation."""

    MESSAGE = "message"
    FUNCTION_CALL = "function_call"
    FUNCTION_CALL_OUTPUT = "function_call_output"


class RealtimeItemRole(str, Enum):
    """Role for conversation items."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class RealtimeContentType(str, Enum):
    """Content types for messages."""

    INPUT_TEXT = "input_text"
    INPUT_AUDIO = "input_audio"
    TEXT = "text"
    AUDIO = "audio"


class RealtimeItemStatus(str, Enum):
    """Status of conversation items."""

    COMPLETED = "completed"
    IN_PROGRESS = "in_progress"
    INCOMPLETE = "incomplete"


class RealtimeContent(BaseModel):
    """Content part of a conversation item."""

    type: RealtimeContentType = Field(description="The type of content.")
    text: str | None = Field(default=None, description="Text content.")
    audio: str | None = Field(default=None, description="Base64-encoded audio data.")
    transcript: str | None = Field(default=None, description="Transcript of audio.")


class RealtimeItem(BaseModel):
    """A conversation item in a Realtime session."""

    id: str = Field(description="Unique item identifier.")
    object: Literal["realtime.item"] = Field(
        default="realtime.item",
        description="The object type.",
    )
    type: RealtimeItemType = Field(description="The type of item.")
    status: RealtimeItemStatus = Field(
        default=RealtimeItemStatus.COMPLETED,
        description="The status of the item.",
    )
    role: RealtimeItemRole | None = Field(default=None, description="The role (for messages).")
    content: list[RealtimeContent] = Field(
        default_factory=list,
        description="Content parts of the item.",
    )
    call_id: str | None = Field(
        default=None,
        description="Call ID (for function calls).",
    )
    name: str | None = Field(
        default=None,
        description="Function name (for function calls).",
    )
    arguments: str | None = Field(
        default=None,
        description="Function arguments JSON (for function calls).",
    )
    output: str | None = Field(
        default=None,
        description="Function output (for function call outputs).",
    )


class RealtimeResponse(BaseModel):
    """Response object in Realtime API."""

    id: str = Field(description="Unique response identifier.")
    object: Literal["realtime.response"] = Field(
        default="realtime.response",
        description="The object type.",
    )
    status: RealtimeItemStatus = Field(description="The status of the response.")
    status_details: dict[str, Any] | None = Field(
        default=None,
        description="Additional status details.",
    )
    output: list[RealtimeItem] = Field(
        default_factory=list,
        description="Output items from the response.",
    )
    usage: Usage | None = Field(default=None, description="Token usage information.")


class RealtimeRateLimits(BaseModel):
    """Rate limit information."""

    name: str = Field(description="Name of the rate limit.")
    limit: int = Field(description="Maximum allowed.")
    remaining: int = Field(description="Remaining quota.")
    reset_seconds: float = Field(description="Seconds until reset.")


class RealtimeError(BaseModel):
    """Error information for Realtime API."""

    type: str = Field(description="Error type.")
    code: str | None = Field(default=None, description="Error code.")
    message: str = Field(description="Error message.")
    param: str | None = Field(default=None, description="Parameter that caused the error.")
    event_id: str | None = Field(default=None, description="Event ID that caused the error.")


class RealtimeEvent(BaseModel):
    """Base event model for Realtime WebSocket API."""

    type: RealtimeEventType = Field(description="The type of event.")
    event_id: str = Field(description="Unique event identifier.")

    # Session fields
    session: RealtimeSession | None = Field(default=None, description="Session object.")

    # Audio fields
    audio: str | None = Field(default=None, description="Base64-encoded audio data.")

    # Item fields
    item: RealtimeItem | None = Field(default=None, description="Conversation item.")
    item_id: str | None = Field(default=None, description="Item identifier.")
    previous_item_id: str | None = Field(default=None, description="Previous item identifier.")
    content_index: int | None = Field(default=None, description="Content part index.")
    audio_end_ms: int | None = Field(default=None, description="End time of audio in ms.")

    # Response fields
    response: RealtimeResponse | None = Field(default=None, description="Response object.")
    response_id: str | None = Field(default=None, description="Response identifier.")
    output_index: int | None = Field(default=None, description="Output item index.")

    # Delta fields (for streaming)
    delta: str | None = Field(default=None, description="Delta content.")
    transcript: str | None = Field(default=None, description="Audio transcript.")
    arguments: str | None = Field(default=None, description="Function call arguments.")

    # Rate limits
    rate_limits: list[RealtimeRateLimits] | None = Field(
        default=None,
        description="Rate limit information.",
    )

    # Error fields
    error: RealtimeError | None = Field(default=None, description="Error details.")


# Fine-Tuning API Models


class Hyperparameters(BaseModel):
    """Hyperparameters for fine-tuning."""

    n_epochs: int | Literal["auto"] = Field(
        default="auto",
        description="Number of training epochs. 'auto' decides based on dataset size."
    )
    batch_size: int | Literal["auto"] = Field(
        default="auto",
        description="Batch size for training. 'auto' decides based on dataset size."
    )
    learning_rate_multiplier: float | Literal["auto"] = Field(
        default="auto",
        description="Multiplier for the learning rate. 'auto' uses recommended value."
    )


class FineTuningJobRequest(BaseModel):
    """Request to create a fine-tuning job."""

    training_file: str = Field(
        description="ID of uploaded file containing training data."
    )
    validation_file: str | None = Field(
        default=None,
        description="ID of uploaded file containing validation data."
    )
    model: str = Field(
        description="Base model to fine-tune (e.g., 'meta-llama/Llama-3.1-8B-Instruct', 'openai/gpt-oss-20b')."
    )
    hyperparameters: Hyperparameters | None = Field(
        default=None,
        description="Hyperparameters for fine-tuning."
    )
    suffix: str | None = Field(
        default=None,
        max_length=40,
        description="Suffix for the fine-tuned model name (max 40 characters)."
    )
    integrations: list[dict[str, Any]] | None = Field(
        default=None,
        description="Integrations to enable (e.g., Weights & Biases)."
    )
    seed: int | None = Field(
        default=None,
        description="Random seed for reproducibility."
    )


class FineTuningJobError(BaseModel):
    """Error information for failed fine-tuning jobs."""

    code: str = Field(description="Error code.")
    message: str = Field(description="Human-readable error message.")
    param: str | None = Field(
        default=None,
        description="Parameter that caused the error, if applicable."
    )


class FineTuningJob(BaseModel):
    """Fine-tuning job object."""

    id: str = Field(description="Unique identifier for the fine-tuning job.")
    object: Literal["fine_tuning.job"] = Field(
        default="fine_tuning.job",
        description="Object type."
    )
    created_at: int = Field(description="Unix timestamp when the job was created.")
    finished_at: int | None = Field(
        default=None,
        description="Unix timestamp when the job finished."
    )
    model: str = Field(description="Base model being fine-tuned.")
    fine_tuned_model: str | None = Field(
        default=None,
        description="Name of the fine-tuned model (null until completed)."
    )
    organization_id: str = Field(description="Organization that owns the job.")
    status: Literal[
        "validating_files",
        "queued",
        "running",
        "succeeded",
        "failed",
        "cancelled"
    ] = Field(description="Current status of the fine-tuning job.")
    hyperparameters: Hyperparameters = Field(
        description="Hyperparameters used for training."
    )
    training_file: str = Field(description="ID of the training file.")
    validation_file: str | None = Field(
        default=None,
        description="ID of the validation file."
    )
    result_files: list[str] = Field(
        default_factory=list,
        description="List of result file IDs (e.g., metrics, model files)."
    )
    trained_tokens: int | None = Field(
        default=None,
        description="Total number of tokens processed during training."
    )
    error: FineTuningJobError | None = Field(
        default=None,
        description="Error details if the job failed."
    )
    integrations: list[dict[str, Any]] | None = Field(
        default=None,
        description="Enabled integrations."
    )
    seed: int | None = Field(
        default=None,
        description="Random seed used for training."
    )
    estimated_finish: int | None = Field(
        default=None,
        description="Estimated Unix timestamp when the job will finish."
    )


class FineTuningJobList(BaseModel):
    """List of fine-tuning jobs."""

    object: Literal["list"] = Field(default="list", description="Object type.")
    data: list[FineTuningJob] = Field(description="List of fine-tuning jobs.")
    has_more: bool = Field(
        default=False,
        description="Whether there are more results available."
    )


class FineTuningEvent(BaseModel):
    """Event during fine-tuning job execution."""

    id: str = Field(description="Unique identifier for the event.")
    object: Literal["fine_tuning.job.event"] = Field(
        default="fine_tuning.job.event",
        description="Object type."
    )
    created_at: int = Field(description="Unix timestamp when the event occurred.")
    level: Literal["info", "warning", "error"] = Field(
        description="Severity level of the event."
    )
    message: str = Field(description="Event message.")
    data: dict[str, Any] | None = Field(
        default=None,
        description="Additional event data (e.g., metrics)."
    )
    type: Literal["message", "metrics"] = Field(
        default="message",
        description="Type of event."
    )


class FineTuningEventList(BaseModel):
    """List of fine-tuning events."""

    object: Literal["list"] = Field(default="list", description="Object type.")
    data: list[FineTuningEvent] = Field(description="List of events.")
    has_more: bool = Field(
        default=False,
        description="Whether there are more results available."
    )


class FineTuningCheckpoint(BaseModel):
    """Checkpoint saved during fine-tuning."""

    id: str = Field(description="Unique identifier for the checkpoint.")
    object: Literal["fine_tuning.job.checkpoint"] = Field(
        default="fine_tuning.job.checkpoint",
        description="Object type."
    )
    created_at: int = Field(description="Unix timestamp when checkpoint was created.")
    fine_tuning_job_id: str = Field(description="ID of the fine-tuning job.")
    fine_tuned_model_checkpoint: str = Field(
        description="Name of the checkpointed model."
    )
    step_number: int = Field(description="Training step number for this checkpoint.")
    metrics: dict[str, float] = Field(
        description="Training metrics at this checkpoint."
    )


class FineTuningCheckpointList(BaseModel):
    """List of fine-tuning checkpoints."""

    object: Literal["list"] = Field(default="list", description="Object type.")
    data: list[FineTuningCheckpoint] = Field(description="List of checkpoints.")
    has_more: bool = Field(
        default=False,
        description="Whether there are more results available."
    )
    first_id: str | None = Field(default=None, description="First checkpoint ID.")
    last_id: str | None = Field(default=None, description="Last checkpoint ID.")


# Assistants API Models


class AssistantToolResources(BaseModel):
    """Tool resources for an assistant (code interpreter, file search)."""

    code_interpreter: dict[str, Any] | None = Field(
        default=None, description="Code interpreter resources."
    )
    file_search: dict[str, Any] | None = Field(
        default=None, description="File search resources."
    )


class Assistant(BaseModel):
    """OpenAI Assistant object."""

    id: str = Field(description="The assistant ID.")
    object: Literal["assistant"] = Field(
        default="assistant", description="Object type."
    )
    created_at: int = Field(description="Unix timestamp of creation.")
    name: str | None = Field(
        default=None, max_length=256, description="The name of the assistant."
    )
    description: str | None = Field(
        default=None, max_length=512, description="The description of the assistant."
    )
    model: str = Field(description="Model used by the assistant.")
    instructions: str | None = Field(
        default=None, max_length=256000, description="System instructions for the assistant."
    )
    tools: list[dict[str, Any]] = Field(
        default_factory=list, max_length=128, description="Tools enabled for the assistant."
    )
    tool_resources: AssistantToolResources | None = Field(
        default=None, description="Resources for tools."
    )
    metadata: dict[str, str] = Field(
        default_factory=dict, description="User-defined metadata (max 16 key-value pairs)."
    )
    temperature: float | None = Field(
        default=1.0, ge=0.0, le=2.0, description="Sampling temperature."
    )
    top_p: float | None = Field(
        default=1.0, ge=0.0, le=1.0, description="Nucleus sampling parameter."
    )
    response_format: str | dict[str, Any] | None = Field(
        default="auto", description="Response format (auto, text, json_object, json_schema)."
    )


class CreateAssistantRequest(BaseModel):
    """Request to create an assistant."""

    model: str = Field(description="Model ID to use.")
    name: str | None = Field(
        default=None, max_length=256, description="Name of the assistant."
    )
    description: str | None = Field(
        default=None, max_length=512, description="Description of the assistant."
    )
    instructions: str | None = Field(
        default=None, max_length=256000, description="System instructions."
    )
    tools: list[dict[str, Any]] = Field(
        default_factory=list, max_length=128, description="Tools to enable."
    )
    tool_resources: AssistantToolResources | None = Field(
        default=None, description="Tool resources."
    )
    metadata: dict[str, str] = Field(
        default_factory=dict, description="Metadata (max 16 pairs)."
    )
    temperature: float | None = Field(
        default=1.0, ge=0.0, le=2.0, description="Sampling temperature."
    )
    top_p: float | None = Field(
        default=1.0, ge=0.0, le=1.0, description="Nucleus sampling."
    )
    response_format: str | dict[str, Any] | None = Field(
        default="auto", description="Response format."
    )


class ModifyAssistantRequest(BaseModel):
    """Request to modify an assistant."""

    model: str | None = Field(default=None, description="Model ID.")
    name: str | None = Field(default=None, max_length=256, description="Name.")
    description: str | None = Field(default=None, max_length=512, description="Description.")
    instructions: str | None = Field(default=None, max_length=256000, description="Instructions.")
    tools: list[dict[str, Any]] | None = Field(default=None, max_length=128, description="Tools.")
    tool_resources: AssistantToolResources | None = Field(default=None, description="Tool resources.")
    metadata: dict[str, str] | None = Field(default=None, description="Metadata.")
    temperature: float | None = Field(default=None, ge=0.0, le=2.0, description="Temperature.")
    top_p: float | None = Field(default=None, ge=0.0, le=1.0, description="Top-p.")
    response_format: str | dict[str, Any] | None = Field(default=None, description="Response format.")


class AssistantList(BaseModel):
    """List of assistants."""

    object: Literal["list"] = Field(default="list", description="Object type.")
    data: list[Assistant] = Field(description="List of assistant objects.")
    first_id: str | None = Field(default=None, description="First assistant ID.")
    last_id: str | None = Field(default=None, description="Last assistant ID.")
    has_more: bool = Field(default=False, description="Whether there are more results.")


class Thread(BaseModel):
    """OpenAI Thread object."""

    id: str = Field(description="The thread ID.")
    object: Literal["thread"] = Field(default="thread", description="Object type.")
    created_at: int = Field(description="Unix timestamp of creation.")
    metadata: dict[str, str] = Field(
        default_factory=dict, description="User-defined metadata."
    )
    tool_resources: AssistantToolResources | None = Field(
        default=None, description="Tool resources for the thread."
    )


class CreateThreadRequest(BaseModel):
    """Request to create a thread."""

    messages: list[dict[str, Any]] = Field(
        default_factory=list, description="Initial messages for the thread."
    )
    metadata: dict[str, str] = Field(
        default_factory=dict, description="Metadata (max 16 pairs)."
    )
    tool_resources: AssistantToolResources | None = Field(
        default=None, description="Tool resources."
    )


class ModifyThreadRequest(BaseModel):
    """Request to modify a thread."""

    metadata: dict[str, str] | None = Field(default=None, description="Metadata.")
    tool_resources: AssistantToolResources | None = Field(default=None, description="Tool resources.")


class ThreadMessage(BaseModel):
    """Message in a thread (Assistants API)."""

    id: str = Field(description="Message ID.")
    object: Literal["thread.message"] = Field(
        default="thread.message", description="Object type."
    )
    created_at: int = Field(description="Unix timestamp of creation.")
    thread_id: str = Field(description="Thread ID this message belongs to.")
    role: Literal["user", "assistant"] = Field(description="Message role.")
    content: list[dict[str, Any]] = Field(description="Message content array.")
    assistant_id: str | None = Field(
        default=None, description="Assistant ID if role is assistant."
    )
    run_id: str | None = Field(
        default=None, description="Run ID if created by a run."
    )
    attachments: list[dict[str, Any]] | None = Field(
        default=None, description="File attachments."
    )
    metadata: dict[str, str] = Field(
        default_factory=dict, description="User-defined metadata."
    )


class CreateMessageRequest(BaseModel):
    """Request to create a message in a thread."""

    role: Literal["user", "assistant"] = Field(description="Message role.")
    content: str | list[dict[str, Any]] = Field(description="Message content.")
    attachments: list[dict[str, Any]] | None = Field(
        default=None, description="File attachments."
    )
    metadata: dict[str, str] = Field(
        default_factory=dict, description="Metadata (max 16 pairs)."
    )


class MessageList(BaseModel):
    """List of thread messages."""

    object: Literal["list"] = Field(default="list", description="Object type.")
    data: list[ThreadMessage] = Field(description="List of message objects.")
    first_id: str | None = Field(default=None, description="First message ID.")
    last_id: str | None = Field(default=None, description="Last message ID.")
    has_more: bool = Field(default=False, description="Whether there are more results.")


class RunStatus(str, Enum):
    """Run status values."""

    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    REQUIRES_ACTION = "requires_action"
    CANCELLING = "cancelling"
    CANCELLED = "cancelled"
    FAILED = "failed"
    COMPLETED = "completed"
    INCOMPLETE = "incomplete"
    EXPIRED = "expired"


class Run(BaseModel):
    """OpenAI Run object."""

    id: str = Field(description="Run ID.")
    object: Literal["thread.run"] = Field(default="thread.run", description="Object type.")
    created_at: int = Field(description="Unix timestamp of creation.")
    thread_id: str = Field(description="Thread ID.")
    assistant_id: str = Field(description="Assistant ID.")
    status: RunStatus = Field(description="Run status.")
    required_action: dict[str, Any] | None = Field(
        default=None, description="Required action details if status is requires_action."
    )
    last_error: dict[str, Any] | None = Field(
        default=None, description="Last error details if status is failed."
    )
    expires_at: int | None = Field(
        default=None, description="Unix timestamp when run expires."
    )
    started_at: int | None = Field(
        default=None, description="Unix timestamp when run started."
    )
    cancelled_at: int | None = Field(
        default=None, description="Unix timestamp when run was cancelled."
    )
    failed_at: int | None = Field(
        default=None, description="Unix timestamp when run failed."
    )
    completed_at: int | None = Field(
        default=None, description="Unix timestamp when run completed."
    )
    incomplete_details: dict[str, Any] | None = Field(
        default=None, description="Details about incompletion."
    )
    model: str = Field(description="Model used.")
    instructions: str | None = Field(default=None, description="Instructions used.")
    tools: list[dict[str, Any]] = Field(
        default_factory=list, description="Tools used in run."
    )
    metadata: dict[str, str] = Field(
        default_factory=dict, description="User-defined metadata."
    )
    usage: Usage | None = Field(default=None, description="Token usage.")
    temperature: float | None = Field(default=None, description="Temperature used.")
    top_p: float | None = Field(default=None, description="Top-p used.")
    max_prompt_tokens: int | None = Field(
        default=None, description="Max prompt tokens."
    )
    max_completion_tokens: int | None = Field(
        default=None, description="Max completion tokens."
    )
    truncation_strategy: dict[str, Any] | None = Field(
        default=None, description="Truncation strategy."
    )
    tool_choice: str | dict[str, Any] | None = Field(
        default=None, description="Tool choice used."
    )
    parallel_tool_calls: bool = Field(
        default=True, description="Whether parallel tool calls are enabled."
    )
    response_format: str | dict[str, Any] | None = Field(
        default="auto", description="Response format."
    )


class CreateRunRequest(BaseModel):
    """Request to create a run."""

    assistant_id: str = Field(description="Assistant ID to use.")
    model: str | None = Field(default=None, description="Override model.")
    instructions: str | None = Field(default=None, description="Override instructions.")
    additional_instructions: str | None = Field(
        default=None, description="Additional instructions to append."
    )
    additional_messages: list[dict[str, Any]] | None = Field(
        default=None, description="Additional messages to add before run."
    )
    tools: list[dict[str, Any]] | None = Field(default=None, description="Override tools.")
    metadata: dict[str, str] = Field(
        default_factory=dict, description="Metadata (max 16 pairs)."
    )
    temperature: float | None = Field(default=None, ge=0.0, le=2.0, description="Temperature.")
    top_p: float | None = Field(default=None, ge=0.0, le=1.0, description="Top-p.")
    max_prompt_tokens: int | None = Field(default=None, description="Max prompt tokens.")
    max_completion_tokens: int | None = Field(default=None, description="Max completion tokens.")
    truncation_strategy: dict[str, Any] | None = Field(default=None, description="Truncation strategy.")
    tool_choice: str | dict[str, Any] | None = Field(default=None, description="Tool choice.")
    parallel_tool_calls: bool = Field(default=True, description="Enable parallel tool calls.")
    response_format: str | dict[str, Any] | None = Field(default="auto", description="Response format.")
    stream: bool = Field(default=False, description="Stream run updates.")


class ModifyRunRequest(BaseModel):
    """Request to modify a run (only metadata supported)."""

    metadata: dict[str, str] | None = Field(default=None, description="Metadata.")


class RunList(BaseModel):
    """List of runs."""

    object: Literal["list"] = Field(default="list", description="Object type.")
    data: list[Run] = Field(description="List of run objects.")
    first_id: str | None = Field(default=None, description="First run ID.")
    last_id: str | None = Field(default=None, description="Last run ID.")
    has_more: bool = Field(default=False, description="Whether there are more results.")


class RunStep(BaseModel):
    """Run step object."""

    id: str = Field(description="Run step ID.")
    object: Literal["thread.run.step"] = Field(
        default="thread.run.step", description="Object type."
    )
    created_at: int = Field(description="Unix timestamp of creation.")
    run_id: str = Field(description="Run ID.")
    assistant_id: str = Field(description="Assistant ID.")
    thread_id: str = Field(description="Thread ID.")
    type: Literal["message_creation", "tool_calls"] = Field(
        description="Step type."
    )
    status: Literal["in_progress", "cancelled", "failed", "completed", "expired"] = Field(
        description="Step status."
    )
    cancelled_at: int | None = Field(default=None, description="Cancellation timestamp.")
    completed_at: int | None = Field(default=None, description="Completion timestamp.")
    expired_at: int | None = Field(default=None, description="Expiration timestamp.")
    failed_at: int | None = Field(default=None, description="Failure timestamp.")
    last_error: dict[str, Any] | None = Field(default=None, description="Error details.")
    step_details: dict[str, Any] = Field(description="Step-specific details.")
    usage: Usage | None = Field(default=None, description="Token usage for this step.")
    metadata: dict[str, str] = Field(
        default_factory=dict, description="User-defined metadata."
    )


class RunStepList(BaseModel):
    """List of run steps."""

    object: Literal["list"] = Field(default="list", description="Object type.")
    data: list[RunStep] = Field(description="List of run step objects.")
    first_id: str | None = Field(default=None, description="First step ID.")
    last_id: str | None = Field(default=None, description="Last step ID.")
    has_more: bool = Field(default=False, description="Whether there are more results.")
