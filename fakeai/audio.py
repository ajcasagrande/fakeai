"""
Audio utilities for FakeAI chat completions.

This module provides utilities for handling audio input/output in chat completions,
including token estimation, content extraction, and audio generation.
"""

#  SPDX-License-Identifier: Apache-2.0

import base64
import time
import uuid
from typing import Any

from fakeai.utils.audio_generation import generate_simulated_audio


def estimate_audio_tokens(duration_seconds: float) -> int:
    """
    Estimate audio tokens based on duration.

    Uses OpenAI's heuristic of ~1 token per 0.6 seconds of audio.
    This is based on Whisper's tokenization where approximately
    1.67 tokens per second.

    Args:
        duration_seconds: Duration of audio in seconds

    Returns:
        Estimated number of audio tokens
    """
    # ~1.67 tokens per second (or 1 token per 0.6 seconds)
    tokens_per_second = 1.67
    tokens = int(duration_seconds * tokens_per_second)
    return max(1, tokens)  # At least 1 token


def estimate_audio_duration(tokens: int) -> float:
    """
    Estimate audio duration based on tokens.

    Inverse of estimate_audio_tokens - converts tokens back to duration.

    Args:
        tokens: Number of audio tokens

    Returns:
        Estimated duration in seconds
    """
    # ~1 token per 0.6 seconds
    seconds_per_token = 0.6
    duration = tokens * seconds_per_token
    return max(0.1, duration)


def extract_audio_from_content(messages: list[Any]) -> list[tuple[bytes, str]]:
    """
    Extract audio data from message content.

    Searches through messages for InputAudioContent parts and extracts
    the base64-encoded audio data and format.

    Args:
        messages: List of Message objects

    Returns:
        List of (audio_bytes, format) tuples
    """
    audio_inputs = []

    for msg in messages:
        if not msg.content:
            continue

        # Handle list of content parts (multi-modal)
        if isinstance(msg.content, list):
            for part in msg.content:
                # Handle dict (from JSON)
                if isinstance(part, dict) and part.get(
                        "type") == "input_audio":
                    input_audio = part.get("input_audio", {})
                    audio_data = input_audio.get("data", "")
                    audio_format = input_audio.get("format", "wav")

                    if audio_data:
                        try:
                            audio_bytes = base64.b64decode(audio_data)
                            audio_inputs.append((audio_bytes, audio_format))
                        except Exception:
                            # Invalid base64, skip
                            pass

                # Handle Pydantic model (after validation)
                elif hasattr(part, "type") and part.type == "input_audio":
                    if hasattr(part, "input_audio"):
                        input_audio = part.input_audio
                        audio_data = input_audio.data
                        audio_format = input_audio.format

                        if audio_data:
                            try:
                                audio_bytes = base64.b64decode(audio_data)
                                audio_inputs.append(
                                    (audio_bytes, audio_format))
                            except Exception:
                                # Invalid base64, skip
                                pass

    return audio_inputs


def transcribe_audio_input(audio_bytes: bytes, audio_format: str) -> str:
    """
    Simulate transcription of audio input.

    In a real implementation, this would call a speech-to-text model.
    For simulation, we return a placeholder transcription.

    Args:
        audio_bytes: Raw audio data
        audio_format: Audio format (wav, mp3)

    Returns:
        Transcribed text
    """
    # Estimate duration from audio size
    # WAV: 24000 Hz * 2 bytes/sample = 48000 bytes/second
    # MP3: ~16000 bytes/second (128 kbps)
    if audio_format == "wav":
        # WAV has 44 byte header + data
        data_size = len(audio_bytes) - 44
        sample_rate = 24000
        bytes_per_sample = 2
        duration = max(0.1, data_size / (sample_rate * bytes_per_sample))
    elif audio_format == "mp3":
        # MP3 at 128kbps
        duration = max(0.1, len(audio_bytes) / 16000)
    else:
        # Default estimate
        duration = max(0.1, len(audio_bytes) / 20000)

    # Generate simulated transcription
    # Create a realistic placeholder that indicates audio was processed
    tokens = estimate_audio_tokens(duration)

    # Simulate transcription based on duration
    if duration < 2.0:
        transcription = "Hello"
    elif duration < 5.0:
        transcription = "Hello, how can I help you today?"
    elif duration < 10.0:
        transcription = "Hello, how can I help you today? I'd like to know more about your services."
    else:
        transcription = (
            "Hello, how can I help you today? I'd like to know more about your services "
            "and how they can benefit my business. Can you provide some details?")

    return transcription


def generate_audio_output(
    text: str, voice: str = "alloy", audio_format: str = "mp3"
) -> dict[str, Any]:
    """
    Generate simulated audio output for chat completion response.

    Creates an AudioOutput object with base64-encoded audio data,
    transcript, and expiration timestamp.

    Args:
        text: Text to convert to speech
        voice: Voice to use for audio output
        audio_format: Audio format (mp3, wav, opus, etc.)

    Returns:
        Dictionary containing audio output data
    """
    # Generate audio bytes
    audio_bytes = generate_simulated_audio(
        text=text,
        voice=voice,
        response_format=audio_format,
        speed=1.0,
    )

    # Encode to base64
    audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")

    # Calculate expiration (24 hours from now)
    expires_at = int(time.time()) + (24 * 3600)

    # Create audio output
    audio_output = {
        "id": f"audio-{uuid.uuid4().hex}",
        "data": audio_b64,
        "transcript": text,
        "expires_at": expires_at,
    }

    return audio_output


def calculate_audio_input_tokens(messages: list[Any]) -> int:
    """
    Calculate total audio tokens from input messages.

    Extracts all audio inputs from messages and calculates
    the total token count based on audio duration.

    Args:
        messages: List of Message objects

    Returns:
        Total audio input tokens
    """
    audio_inputs = extract_audio_from_content(messages)
    total_tokens = 0

    for audio_bytes, audio_format in audio_inputs:
        # Estimate duration from audio size
        if audio_format == "wav":
            data_size = len(audio_bytes) - 44  # Remove WAV header
            sample_rate = 24000
            bytes_per_sample = 2
            duration = max(0.1, data_size / (sample_rate * bytes_per_sample))
        elif audio_format == "mp3":
            duration = max(0.1, len(audio_bytes) / 16000)
        else:
            duration = max(0.1, len(audio_bytes) / 20000)

        tokens = estimate_audio_tokens(duration)
        total_tokens += tokens

    return total_tokens


def extract_text_from_audio(messages: list[Any]) -> str:
    """
    Extract and transcribe text from audio inputs in messages.

    Combines transcriptions of all audio inputs into a single text string.

    Args:
        messages: List of Message objects

    Returns:
        Combined transcribed text
    """
    audio_inputs = extract_audio_from_content(messages)
    transcriptions = []

    for audio_bytes, audio_format in audio_inputs:
        transcription = transcribe_audio_input(audio_bytes, audio_format)
        transcriptions.append(transcription)

    return " ".join(transcriptions)
