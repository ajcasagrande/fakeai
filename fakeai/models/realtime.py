"""
Realtime WebSocket API models for the OpenAI API.

This module contains models for the Realtime API which provides bidirectional
streaming communication with support for audio, text, and function calling.
"""
#  SPDX-License-Identifier: Apache-2.0

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field

from ._base import Usage


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


class RealtimeInputAudioTranscription(BaseModel):
    """Configuration for input audio transcription."""

    model: str = Field(
        default="whisper-1", description="The model to use for transcription."
    )


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
    role: RealtimeItemRole | None = Field(
        default=None, description="The role (for messages)."
    )
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
    param: str | None = Field(
        default=None, description="Parameter that caused the error."
    )
    event_id: str | None = Field(
        default=None, description="Event ID that caused the error."
    )


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
    previous_item_id: str | None = Field(
        default=None, description="Previous item identifier."
    )
    content_index: int | None = Field(default=None, description="Content part index.")
    audio_end_ms: int | None = Field(
        default=None, description="End time of audio in ms."
    )

    # Response fields
    response: RealtimeResponse | None = Field(
        default=None, description="Response object."
    )
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
