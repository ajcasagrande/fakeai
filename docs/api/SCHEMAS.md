# Schema Reference

This document provides a comprehensive reference for all Pydantic models and schemas used in FakeAI.

## Table of Contents

- [Common Models](#common-models)
- [Chat Completion Models](#chat-completion-models)
- [Text Completion Models](#text-completion-models)
- [Embedding Models](#embedding-models)
- [Image Generation Models](#image-generation-models)
- [File Models](#file-models)
- [Responses API Models](#responses-api-models)
- [Rankings API Models](#rankings-api-models)
- [Multi-Modal Content Models](#multi-modal-content-models)
- [Tool Calling Models](#tool-calling-models)
- [Structured Outputs Models](#structured-outputs-models)

---

## Common Models

### Usage

Token usage statistics with detailed breakdowns.

**Fields:**
- `prompt_tokens` (int): Number of tokens in the prompt
- `completion_tokens` (int, optional): Number of tokens in the completion
- `total_tokens` (int): Total tokens used (prompt + completion)
- `prompt_tokens_details` (PromptTokensDetails, optional): Breakdown of prompt tokens
- `completion_tokens_details` (CompletionTokensDetails, optional): Breakdown of completion tokens
- `input_tokens` (int, optional): Alias for prompt_tokens (Responses API)
- `output_tokens` (int, optional): Alias for completion_tokens (Responses API)

**Example:**
```python
from fakeai.models import Usage, PromptTokensDetails, CompletionTokensDetails

usage = Usage(
    prompt_tokens=100,
    completion_tokens=50,
    total_tokens=150,
    prompt_tokens_details=PromptTokensDetails(
        cached_tokens=10,
        audio_tokens=5
    ),
    completion_tokens_details=CompletionTokensDetails(
        reasoning_tokens=20,
        audio_tokens=0,
        accepted_prediction_tokens=5,
        rejected_prediction_tokens=2
    )
)
```

### PromptTokensDetails

Breakdown of prompt token usage.

**Fields:**
- `cached_tokens` (int, default=0): Number of cached tokens reused
- `audio_tokens` (int, default=0): Number of audio tokens in prompt

### CompletionTokensDetails

Breakdown of completion token usage.

**Fields:**
- `reasoning_tokens` (int, default=0): Tokens used for reasoning (e.g., deepseek-ai/DeepSeek-R1 models)
- `audio_tokens` (int, default=0): Tokens in audio output
- `accepted_prediction_tokens` (int, default=0): Tokens from accepted predictions
- `rejected_prediction_tokens` (int, default=0): Tokens from rejected predictions

### ErrorDetail

Error information.

**Fields:**
- `message` (str): Human-readable error message
- `type` (str): Error type identifier
- `param` (str, optional): Parameter that caused the error
- `code` (str, optional): Machine-readable error code

**Example:**
```python
from fakeai.models import ErrorDetail, ErrorResponse

error = ErrorResponse(
    error=ErrorDetail(
        message="Invalid model specified",
        type="invalid_request_error",
        param="model",
        code="invalid_model"
    )
)
```

### Model

Information about an available model.

**Fields:**
- `id` (str): Model identifier (e.g., "openai/gpt-oss-120b", "meta-llama/Llama-3.1-8B-Instruct")
- `object` (Literal["model"]): Object type
- `created` (int): Unix timestamp of model creation
- `owned_by` (str): Organization that owns the model
- `permission` (list[ModelPermission]): List of permissions
- `root` (str, optional): Root model identifier
- `parent` (str, optional): Parent model identifier

### ModelPermission

Permissions for a model.

**Fields:**
- `id` (str): Permission identifier
- `object` (Literal["model_permission"]): Object type
- `created` (int): Unix timestamp
- `allow_create_engine` (bool): Whether engine creation is allowed
- `allow_sampling` (bool): Whether sampling is allowed
- `allow_logprobs` (bool): Whether logprobs are allowed
- `allow_search_indices` (bool): Whether search indices are allowed
- `allow_view` (bool): Whether viewing is allowed
- `allow_fine_tuning` (bool): Whether fine-tuning is allowed
- `organization` (str): Organization this permission applies to
- `group` (str, optional): Group this permission applies to
- `is_blocking` (bool): Whether this is a blocking permission

---

## Chat Completion Models

### Message

A message in a conversation.

**Fields:**
- `role` (Role): Message role (system, user, assistant, tool, function)
- `content` (str | list[ContentPart], optional): Message content (text or multi-modal array)
- `name` (str, optional): Name of the message author
- `tool_calls` (list[ToolCall], optional): Tool calls made by assistant
- `tool_call_id` (str, optional): ID for tool response messages
- `function_call` (FunctionCall, optional): Function call (deprecated)
- `refusal` (str, optional): Refusal message if model refuses request

**Example (Text Content):**
```python
from fakeai.models import Message, Role

message = Message(
    role=Role.USER,
    content="Hello, how are you?"
)
```

**Example (Multi-Modal Content):**
```python
from fakeai.models import Message, Role, TextContent, ImageContent, ImageUrl

message = Message(
    role=Role.USER,
    content=[
        TextContent(text="What's in this image?"),
        ImageContent(
            image_url=ImageUrl(
                url="https://example.com/image.jpg",
                detail="high"
            )
        )
    ]
)
```

### ChatCompletionRequest

Request for creating a chat completion.

**Fields:**
- `model` (str): Model identifier
- `messages` (list[Message]): Conversation messages
- `temperature` (float, optional): Sampling temperature (0-2, default=1.0)
- `top_p` (float, optional): Nucleus sampling parameter (0-1, default=1.0)
- `n` (int, optional): Number of completions to generate (default=1)
- `stream` (bool, optional): Whether to stream responses (default=False)
- `stream_options` (StreamOptions, optional): Streaming configuration
- `stop` (str | list[str], optional): Stop sequences
- `max_tokens` (int, optional): Maximum tokens to generate
- `max_completion_tokens` (int, optional): Max completion tokens (for deepseek-ai/DeepSeek-R1 models)
- `presence_penalty` (float, optional): Presence penalty (-2.0 to 2.0, default=0)
- `frequency_penalty` (float, optional): Frequency penalty (-2.0 to 2.0, default=0)
- `logit_bias` (dict[str, float], optional): Token logit biases
- `logprobs` (bool, optional): Return log probabilities (default=False)
- `top_logprobs` (int, optional): Number of top logprobs to return (0-20)
- `user` (str, optional): End-user identifier
- `response_format` (ResponseFormat | JsonSchemaResponseFormat, optional): Response format
- `seed` (int, optional): Seed for deterministic sampling
- `service_tier` (Literal["auto", "default"], optional): Service tier
- `tools` (list[Tool], optional): Available tools
- `tool_choice` (Literal["auto", "none", "required"] | ToolChoice, optional): Tool selection
- `parallel_tool_calls` (bool, optional): Enable parallel tool calls (default=True)
- `functions` (list[dict], optional): Functions (deprecated)
- `function_call` (Literal["auto", "none"] | dict, optional): Function call control (deprecated)
- `modalities` (list[Literal["text", "audio"]], optional): Output modalities
- `audio` (AudioConfig, optional): Audio output configuration
- `store` (bool, optional): Store output for distillation (default=False)
- `metadata` (dict[str, str], optional): Developer-defined metadata

**Validation Rules:**
- `temperature`: 0 ≤ temperature ≤ 2
- `top_p`: 0 ≤ top_p ≤ 1
- `n`: n ≥ 1
- `max_tokens`: max_tokens ≥ 0
- `presence_penalty`: -2.0 ≤ presence_penalty ≤ 2.0
- `frequency_penalty`: -2.0 ≤ frequency_penalty ≤ 2.0
- `top_logprobs`: 0 ≤ top_logprobs ≤ 20

**Example:**
```python
from fakeai.models import ChatCompletionRequest, Message, Role, StreamOptions

request = ChatCompletionRequest(
    model="openai/gpt-oss-120b",
    messages=[
        Message(role=Role.SYSTEM, content="You are helpful"),
        Message(role=Role.USER, content="Hello")
    ],
    temperature=0.7,
    max_tokens=150,
    logprobs=True,
    top_logprobs=5,
    stream_options=StreamOptions(include_usage=True),
    parallel_tool_calls=False,
    store=True,
    metadata={"user_id": "123"}
)
```

### ChatCompletionResponse

Response from a chat completion.

**Fields:**
- `id` (str): Unique completion identifier
- `object` (Literal["chat.completion"]): Object type
- `created` (int): Unix timestamp
- `model` (str): Model used
- `choices` (list[ChatCompletionChoice]): Completion choices
- `usage` (Usage): Token usage statistics
- `system_fingerprint` (str, optional): System fingerprint

### ChatCompletionChoice

A single choice in the completion response.

**Fields:**
- `index` (int): Choice index
- `message` (Message): Generated message
- `finish_reason` (str, optional): Reason generation stopped (stop, length, tool_calls, etc.)
- `logprobs` (ChatLogprobs, optional): Log probability information

### ChatCompletionChunk

A chunk in a streaming chat completion.

**Fields:**
- `id` (str): Unique completion identifier
- `object` (Literal["chat.completion.chunk"]): Object type
- `created` (int): Unix timestamp
- `model` (str): Model used
- `choices` (list[ChatCompletionChunkChoice]): Chunk choices
- `system_fingerprint` (str, optional): System fingerprint

### Delta

Partial message content in streaming responses.

**Fields:**
- `role` (Role, optional): Message role (in first chunk)
- `content` (str, optional): Partial content
- `tool_calls` (list[ToolCallDelta], optional): Partial tool call info
- `function_call` (FunctionCall, optional): Function call (deprecated)
- `refusal` (str, optional): Refusal message
- `token_timing` (list[float], optional): Token timing information

---

## Text Completion Models

### CompletionRequest

Request for text completion.

**Fields:**
- `model` (str): Model identifier
- `prompt` (str | list[str] | list[int] | list[list[int]]): Prompt text or tokens
- `suffix` (str, optional): Text after completion
- `max_tokens` (int, optional): Maximum tokens (default=16)
- `temperature` (float, optional): Sampling temperature (0-2, default=1.0)
- `top_p` (float, optional): Nucleus sampling (0-1, default=1.0)
- `n` (int, optional): Number of completions (default=1)
- `stream` (bool, optional): Stream responses (default=False)
- `logprobs` (int, optional): Number of logprobs (0-5)
- `echo` (bool, optional): Echo prompt in completion (default=False)
- `stop` (str | list[str], optional): Stop sequences
- `presence_penalty` (float, optional): Presence penalty (-2.0 to 2.0)
- `frequency_penalty` (float, optional): Frequency penalty (-2.0 to 2.0)
- `best_of` (int, optional): Generate best_of and return best (default=1)
- `logit_bias` (dict[str, float], optional): Token logit biases
- `user` (str, optional): End-user identifier

**Example:**
```python
from fakeai.models import CompletionRequest

request = CompletionRequest(
    model="meta-llama/Llama-3.1-8B-Instruct",
    prompt="Once upon a time",
    max_tokens=50,
    temperature=0.8,
    stop=["\n", "."]
)
```

### CompletionResponse

Response from a text completion.

**Fields:**
- `id` (str): Unique completion identifier
- `object` (Literal["text_completion"]): Object type
- `created` (int): Unix timestamp
- `model` (str): Model used
- `choices` (list[CompletionChoice]): Completion choices
- `usage` (Usage): Token usage

### CompletionChoice

A choice in the completion response.

**Fields:**
- `text` (str): Generated text
- `index` (int): Choice index
- `logprobs` (LogProbs, optional): Log probability information
- `finish_reason` (str, optional): Why generation stopped
- `token_timing` (list[float], optional): Token timing info

---

## Embedding Models

### EmbeddingRequest

Request for creating embeddings.

**Fields:**
- `model` (str): Model identifier
- `input` (str | list[str] | list[int] | list[list[int]]): Input text or tokens
- `user` (str, optional): End-user identifier
- `encoding_format` (Literal["float", "base64"], optional): Encoding format (default="float")
- `dimensions` (int, optional): Output dimensions

**Example:**
```python
from fakeai.models import EmbeddingRequest

request = EmbeddingRequest(
    model="sentence-transformers/all-mpnet-base-v2",
    input="The quick brown fox",
    encoding_format="float",
    dimensions=1536
)
```

### EmbeddingResponse

Response containing embeddings.

**Fields:**
- `object` (Literal["list"]): Object type
- `data` (list[Embedding]): List of embedding objects
- `model` (str): Model used
- `usage` (Usage): Token usage

### Embedding

A single embedding result.

**Fields:**
- `object` (Literal["embedding"]): Object type
- `embedding` (list[float]): Embedding vector
- `index` (int): Index in the input array

---

## Image Generation Models

### ImageGenerationRequest

Request for image generation.

**Fields:**
- `prompt` (str): Text description of desired image (max 1000 chars)
- `model` (str, optional): Model to use (default="stabilityai/stable-diffusion-2-1")
- `n` (int, optional): Number of images (1-10, default=1)
- `quality` (ImageQuality, optional): Image quality (standard, hd; default="standard")
- `response_format` (ImageResponseFormat, optional): Format (url, b64_json; default="url")
- `size` (ImageSize, optional): Image size (default="1024x1024")
- `style` (ImageStyle, optional): Image style (vivid, natural; default="vivid")
- `user` (str, optional): End-user identifier

**Available Sizes:**
- `256x256`
- `512x512`
- `1024x1024`
- `1792x1024`
- `1024x1792`

**Example:**
```python
from fakeai.models import ImageGenerationRequest, ImageQuality, ImageStyle

request = ImageGenerationRequest(
    prompt="A futuristic city with flying cars",
    model="stabilityai/stable-diffusion-xl-base-1.0",
    n=1,
    quality=ImageQuality.HD,
    size="1024x1024",
    style=ImageStyle.VIVID
)
```

### ImageGenerationResponse

Response containing generated images.

**Fields:**
- `created` (int): Unix timestamp
- `data` (list[GeneratedImage]): List of generated images

### GeneratedImage

A single generated image.

**Fields:**
- `url` (str, optional): Image URL
- `b64_json` (str, optional): Base64-encoded image
- `revised_prompt` (str, optional): Revised prompt used

---

## File Models

### FileObject

Information about an uploaded file.

**Fields:**
- `id` (str): File identifier
- `object` (Literal["file"]): Object type
- `bytes` (int): File size in bytes
- `created_at` (int): Unix timestamp
- `filename` (str): Filename
- `purpose` (str): File purpose (e.g., "fine-tune")
- `status` (str, optional): File status
- `status_details` (str, optional): Status details

### FileListResponse

Response containing list of files.

**Fields:**
- `object` (Literal["list"]): Object type
- `data` (list[FileObject]): List of file objects

---

## Responses API Models

### ResponsesRequest

Request for the Responses API (March 2025 format).

**Fields:**
- `model` (str): Model identifier
- `input` (str | list[Message]): Text or message array
- `instructions` (str, optional): System-level instructions
- `tools` (list[Tool], optional): Available tools
- `previous_response_id` (str, optional): Previous response ID for continuation
- `max_output_tokens` (int, optional): Maximum output tokens
- `temperature` (float, optional): Sampling temperature (0-2)
- `top_p` (float, optional): Nucleus sampling (0-1)
- `stream` (bool, optional): Stream via SSE (default=False)
- `store` (bool, optional): Store for retrieval (default=False)
- `metadata` (dict[str, str], optional): Developer metadata (max 16 pairs)
- `parallel_tool_calls` (bool, optional): Parallel tool execution (default=True)
- `tool_choice` (Literal["auto", "none", "required"] | ToolChoice, optional): Tool selection
- `response_format` (ResponseFormat | JsonSchemaResponseFormat, optional): Output format
- `background` (bool, optional): Run as background task (default=False)

**Example:**
```python
from fakeai.models import ResponsesRequest, Message, Role

request = ResponsesRequest(
    model="openai/gpt-oss-120b",
    input="Tell me about quantum computing",
    instructions="Be concise and technical",
    max_output_tokens=500,
    store=True,
    metadata={"session_id": "abc123"}
)

# Or with message array:
request = ResponsesRequest(
    model="openai/gpt-oss-120b",
    input=[
        Message(role=Role.USER, content="Hello"),
        Message(role=Role.ASSISTANT, content="Hi there!"),
        Message(role=Role.USER, content="How are you?")
    ],
    temperature=0.7
)
```

### ResponsesResponse

Response from the Responses API.

**Fields:**
- `id` (str): Unique response identifier
- `object` (Literal["response"]): Object type
- `created_at` (int): Unix timestamp
- `model` (str): Model used
- `status` (Literal["queued", "in_progress", "completed", "failed", "cancelled", "incomplete"]): Status
- `error` (ErrorDetail, optional): Error if failed
- `incomplete_details` (dict, optional): Incompletion details
- `instructions` (str, optional): Instructions used
- `max_output_tokens` (int, optional): Max tokens specified
- `metadata` (dict[str, str], optional): Metadata
- `previous_response_id` (str, optional): Previous response ID
- `temperature` (float, optional): Temperature used
- `top_p` (float, optional): Top-p used
- `parallel_tool_calls` (bool, optional): Parallel tool calls setting
- `tool_choice` (str | dict, optional): Tool choice used
- `tools` (list[Tool], optional): Tools used
- `output` (list[dict]): Polymorphic output items
- `usage` (Usage, optional): Token usage

---

## Rankings API Models

### RankingRequest

Request for document ranking/reranking.

**Fields:**
- `model` (str): Reranking model identifier
- `query` (RankingQuery): Query to rank against
- `passages` (list[RankingPassage]): Passages to rank (max 512)
- `truncate` (Literal["NONE", "END"], optional): Truncation strategy (default="NONE")

**Example:**
```python
from fakeai.models import RankingRequest, RankingQuery, RankingPassage

request = RankingRequest(
    model="nvidia/nv-rerankqa-mistral-4b-v3",
    query=RankingQuery(text="What is machine learning?"),
    passages=[
        RankingPassage(text="ML is a subset of AI..."),
        RankingPassage(text="Python is popular for ML..."),
        RankingPassage(text="Neural networks are used in ML...")
    ],
    truncate="END"
)
```

### RankingQuery

Query for ranking.

**Fields:**
- `text` (str): Query text

### RankingPassage

A passage to rank.

**Fields:**
- `text` (str): Passage text content

### RankingResponse

Response containing rankings.

**Fields:**
- `rankings` (list[RankingObject]): Ranked results (sorted by logit descending)

### RankingObject

A single ranking result.

**Fields:**
- `index` (int): Zero-based index in original passages array
- `logit` (float): Relevance score (higher is more relevant)

---

## Multi-Modal Content Models

### ContentPart

Union type for content parts: `TextContent | ImageContent | InputAudioContent`

### TextContent

Text content part.

**Fields:**
- `type` (Literal["text"]): Content type
- `text` (str): Text content

**Example:**
```python
from fakeai.models import TextContent

content = TextContent(type="text", text="Hello world")
```

### ImageContent

Image content part.

**Fields:**
- `type` (Literal["image_url"]): Content type
- `image_url` (ImageUrl): Image URL configuration

**Example:**
```python
from fakeai.models import ImageContent, ImageUrl

content = ImageContent(
    type="image_url",
    image_url=ImageUrl(
        url="https://example.com/image.jpg",
        detail="high"
    )
)

# Or with base64:
content = ImageContent(
    type="image_url",
    image_url=ImageUrl(
        url="data:image/png;base64,iVBORw0KGgo...",
        detail="auto"
    )
)
```

### ImageUrl

Image URL configuration.

**Fields:**
- `url` (str): URL or data URI (data:image/*;base64,...)
- `detail` (Literal["auto", "low", "high"]): Processing detail level (default="auto")

### InputAudioContent

Audio input content part.

**Fields:**
- `type` (Literal["input_audio"]): Content type
- `input_audio` (InputAudio): Audio data and format

**Example:**
```python
from fakeai.models import InputAudioContent, InputAudio

content = InputAudioContent(
    type="input_audio",
    input_audio=InputAudio(
        data="base64_encoded_audio_data",
        format="wav"
    )
)
```

### InputAudio

Audio input configuration.

**Fields:**
- `data` (str): Base64-encoded audio data
- `format` (Literal["wav", "mp3"]): Audio format

### AudioConfig

Audio output configuration.

**Fields:**
- `voice` (Literal["alloy", "ash", "ballad", "coral", "echo", "fable", "onyx", "nova", "sage", "shimmer", "verse"]): Voice selection
- `format` (Literal["mp3", "opus", "aac", "flac", "wav", "pcm16"]): Audio format (default="mp3")

---

## Tool Calling Models

### Tool

Tool definition for function calling.

**Fields:**
- `type` (Literal["function"]): Tool type
- `function` (dict[str, Any]): Function definition with name, description, and parameters

**Example:**
```python
from fakeai.models import Tool

tool = Tool(
    type="function",
    function={
        "name": "get_weather",
        "description": "Get current weather for a location",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "City name"},
                "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]}
            },
            "required": ["location"]
        }
    }
)
```

### ToolCall

A tool call made by the assistant.

**Fields:**
- `id` (str): Tool call identifier
- `type` (Literal["function"]): Tool type
- `function` (ToolCallFunction): Function information

### ToolCallFunction

Function information in a tool call.

**Fields:**
- `name` (str): Function name
- `arguments` (str): JSON-encoded function arguments

### ToolChoice

Explicit tool choice specification.

**Fields:**
- `type` (Literal["function"]): Tool type
- `function` (dict[str, str]): Function to use

### ToolCallDelta

Partial tool call in streaming responses.

**Fields:**
- `index` (int): Tool call array index
- `id` (str, optional): Tool call ID
- `type` (Literal["function"], optional): Tool type
- `function` (FunctionDelta, optional): Partial function info

### FunctionDelta

Partial function information in streaming.

**Fields:**
- `name` (str, optional): Function name
- `arguments` (str, optional): Partial arguments string

---

## Structured Outputs Models

### ResponseFormat

Basic response format specification.

**Fields:**
- `type` (Literal["text", "json_object"]): Format type (default="text")

**Example:**
```python
from fakeai.models import ResponseFormat

format = ResponseFormat(type="json_object")
```

### JsonSchemaResponseFormat

Response format with JSON schema validation.

**Fields:**
- `type` (Literal["json_schema"]): Format type
- `json_schema` (JsonSchema): JSON schema definition

**Example:**
```python
from fakeai.models import JsonSchemaResponseFormat, JsonSchema

format = JsonSchemaResponseFormat(
    type="json_schema",
    json_schema=JsonSchema(
        name="person_data",
        description="Extract person information",
        strict=True,
        schema={
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "number"},
                "email": {"type": "string", "format": "email"}
            },
            "required": ["name", "age"],
            "additionalProperties": False
        }
    )
)
```

### JsonSchema

JSON schema definition for structured outputs.

**Fields:**
- `name` (str): Schema name
- `description` (str, optional): Schema description
- `schema` (dict[str, Any]): JSON schema object
- `strict` (bool, optional): Enforce strict schema compliance

---

## Log Probability Models

### ChatLogprobs

Log probability information for chat completion.

**Fields:**
- `content` (list[ChatLogprob], optional): Per-token log probabilities

### ChatLogprob

Log probability for a single token.

**Fields:**
- `token` (str): The token
- `logprob` (float): Log probability of this token
- `bytes` (list[int], optional): UTF-8 byte representation
- `top_logprobs` (list[TopLogprob]): Most likely alternative tokens

### TopLogprob

Alternative token with log probability.

**Fields:**
- `token` (str): The token
- `logprob` (float): Log probability
- `bytes` (list[int], optional): UTF-8 byte representation

### LogProbs

Log probability information for text completions.

**Fields:**
- `tokens` (list[str]): Tokens
- `token_logprobs` (list[float]): Log probabilities
- `top_logprobs` (list[dict[str, float]], optional): Top alternative tokens
- `text_offset` (list[int]): Character offsets in text

---

## Streaming Models

### StreamOptions

Options for streaming responses.

**Fields:**
- `include_usage` (bool): Include usage statistics in final chunk (default=False)

**Example:**
```python
from fakeai.models import ChatCompletionRequest, StreamOptions

request = ChatCompletionRequest(
    model="openai/gpt-oss-120b",
    messages=[...],
    stream=True,
    stream_options=StreamOptions(include_usage=True)
)
```

---

## Relationships Between Models

### Chat Completion Flow

```
ChatCompletionRequest
    > messages: list[Message]
           > content: str | list[ContentPart]
                  > TextContent
                  > ImageContent (with ImageUrl)
                  > InputAudioContent (with InputAudio)
           > tool_calls: list[ToolCall]
    > tools: list[Tool]
    > response_format: ResponseFormat | JsonSchemaResponseFormat
    > stream_options: StreamOptions

ChatCompletionResponse
    > choices: list[ChatCompletionChoice]
           > message: Message
           > logprobs: ChatLogprobs
    > usage: Usage
            > prompt_tokens_details: PromptTokensDetails
            > completion_tokens_details: CompletionTokensDetails
```

### Streaming Chat Completion Flow

```
ChatCompletionChunk (repeated)
    > choices: list[ChatCompletionChunkChoice]
            > delta: Delta
                    > content: str (partial)
                    > tool_calls: list[ToolCallDelta]
```

### Responses API Flow

```
ResponsesRequest
    > input: str | list[Message]
    > tools: list[Tool]

ResponsesResponse
    > output: list[dict] (polymorphic)
           > ResponseMessageOutput
           > ResponseFunctionCallOutput
    > usage: Usage
```
