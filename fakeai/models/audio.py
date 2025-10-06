"""
Audio models for FakeAI.

This module contains Pydantic models for audio-related API endpoints:
- Text-to-Speech (TTS) models
- Audio transcription (Whisper) models
- Audio usage/billing models
"""

#  SPDX-License-Identifier: Apache-2.0

from typing import Literal

from pydantic import BaseModel, Field

# Text-to-Speech (Audio Speech API)


class SpeechRequest(BaseModel):
    """Request for text-to-speech audio generation."""

    model: str = Field(
        description="ID of the model to use for TTS (e.g., tts-1, tts-1-hd)."
    )
    input: str = Field(
        max_length=4096,
        description="The text to generate audio for. Maximum length is 4096 characters.",
    )
    voice: Literal[
        "alloy", "echo", "fable", "onyx", "nova", "shimmer", "marin", "cedar"
    ] = Field(description="The voice to use for audio generation.")
    response_format: Literal["mp3", "opus", "aac", "flac", "wav", "pcm"] = Field(
        default="mp3",
        description="The audio format to return. Supported formats: mp3, opus, aac, flac, wav, pcm.",
    )
    speed: float = Field(
        default=1.0,
        ge=0.25,
        le=4.0,
        description="The speed of the generated audio. Range: 0.25 to 4.0.",
    )


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
    no_speech_prob: float = Field(
        description="Probability that this segment contains no speech."
    )


class TranscriptionRequest(BaseModel):
    """Request for audio transcription (Whisper API)."""

    model: str = Field(description="Whisper model ID (e.g., whisper-1).")
    language: str | None = Field(
        default=None,
        description="Language of the audio in ISO-639-1 format (e.g., 'en', 'es').",
    )
    prompt: str | None = Field(
        default=None,
        description="Optional text to guide the model's style or continue from previous audio.",
    )
    response_format: Literal["json", "text", "srt", "verbose_json", "vtt"] | None = (
        Field(default="json", description="Format of the transcript output.")
    )
    temperature: float | None = Field(
        default=0.0, ge=0.0, le=1.0, description="Sampling temperature between 0 and 1."
    )
    timestamp_granularities: list[Literal["word", "segment"]] | None = Field(
        default=None,
        description="Timestamp granularities to include (word and/or segment level).",
    )


class TranscriptionResponse(BaseModel):
    """Response from transcription endpoint (JSON format)."""

    text: str = Field(description="The transcribed text.")


class VerboseTranscriptionResponse(BaseModel):
    """Response from transcription endpoint (verbose_json format)."""

    task: Literal["transcribe"] = Field(
        default="transcribe", description="The task performed (always 'transcribe')."
    )
    language: str = Field(description="Detected or specified language code.")
    duration: float = Field(description="Duration of the audio in seconds.")
    text: str = Field(description="The complete transcribed text.")
    words: list[TranscriptionWord] | None = Field(
        default=None, description="Word-level timestamps (if requested)."
    )
    segments: list[TranscriptionSegment] | None = Field(
        default=None, description="Segment-level transcription with timing."
    )


# Audio Translation (Whisper API - translates to English)


class AudioTranslationRequest(BaseModel):
    """Request for audio translation (Whisper API - translates to English)."""

    model: str = Field(description="Whisper model ID (e.g., whisper-1).")
    prompt: str | None = Field(
        default=None,
        description="Optional text to guide the model's style or continue from previous audio.",
    )
    response_format: Literal["json", "text", "srt", "verbose_json", "vtt"] | None = (
        Field(default="json", description="Format of the transcript output.")
    )
    temperature: float | None = Field(
        default=0.0, ge=0.0, le=1.0, description="Sampling temperature between 0 and 1."
    )


# Audio Usage/Billing Models


class UsageAggregationBucket(BaseModel):
    """Usage aggregated by time bucket."""

    object: Literal["bucket"] = Field(default="bucket", description="The object type.")
    start_time: int = Field(description="Unix timestamp for start of bucket.")
    end_time: int = Field(description="Unix timestamp for end of bucket.")
    results: list[dict] = Field(description="Usage results for this time bucket.")


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
