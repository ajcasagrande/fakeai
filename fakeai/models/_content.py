"""
Multi-modal content Pydantic models for the OpenAI API.

This module contains models for different types of content parts that can
be included in messages: text, images, audio, video, and RAG documents.
"""

#  SPDX-License-Identifier: Apache-2.0

from typing import Any, Literal

from pydantic import BaseModel, Field


class TextContent(BaseModel):
    """Text content part."""

    type: Literal["text"] = Field(default="text", description="Content type.")
    text: str = Field(description="The text content.")


class ImageUrl(BaseModel):
    """Image URL configuration."""

    url: str = Field(
        description="URL of the image or data URI (data:image/*;base64,...)."
    )
    detail: Literal["auto", "low", "high"] = Field(
        default="auto", description="Image detail level for processing."
    )


class ImageContent(BaseModel):
    """Image content part."""

    type: Literal["image_url"] = Field(
        default="image_url",
        description="Content type.")
    image_url: ImageUrl = Field(description="Image URL configuration.")


class InputAudio(BaseModel):
    """Input audio configuration."""

    data: str = Field(description="Base64-encoded audio data.")
    format: Literal["wav", "mp3"] = Field(description="Audio format.")


class InputAudioContent(BaseModel):
    """Input audio content part."""

    type: Literal["input_audio"] = Field(
        default="input_audio", description="Content type."
    )
    input_audio: InputAudio = Field(description="Audio data and format.")


class VideoUrl(BaseModel):
    """Video URL configuration (NVIDIA Cosmos extension)."""

    url: str = Field(
        description="URL of the video or data URI (data:video/*;base64,...)."
    )
    detail: Literal["auto", "low", "high"] = Field(
        default="auto", description="Video detail level for processing."
    )


class VideoContent(BaseModel):
    """Video content part (NVIDIA Cosmos extension)."""

    type: Literal["video_url"] = Field(
        default="video_url",
        description="Content type.")
    video_url: VideoUrl = Field(description="Video URL configuration.")


class AudioConfig(BaseModel):
    """Audio output configuration."""

    voice: Literal[
        "alloy",
        "ash",
        "ballad",
        "coral",
        "echo",
        "fable",
        "onyx",
        "nova",
        "sage",
        "shimmer",
        "verse",
    ] = Field(description="Voice to use for audio output.")
    format: Literal["mp3", "opus", "aac", "flac", "wav", "pcm16"] = Field(
        default="mp3", description="Audio format for output."
    )


class RagDocument(BaseModel):
    """Retrieved document for RAG context."""

    id: str = Field(description="Document ID.")
    content: str = Field(description="Document content/text.")
    score: float = Field(
        description="Relevance score (0.0-1.0).",
        ge=0.0,
        le=1.0)
    metadata: dict[str, Any] | None = Field(
        default=None, description="Optional document metadata."
    )
    source: str | None = Field(default=None,
                               description="Document source/origin.")


# Union type for content parts
ContentPart = TextContent | ImageContent | InputAudioContent | VideoContent
