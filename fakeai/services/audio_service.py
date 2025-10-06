"""
Audio service for text-to-speech generation.

This module provides the AudioService class that handles text-to-speech
audio generation with support for multiple voices, formats, and speeds.
"""

#  SPDX-License-Identifier: Apache-2.0

import asyncio
import logging
import random

from fakeai.config import AppConfig
from fakeai.metrics import MetricsTracker
from fakeai.models import SpeechRequest
from fakeai.utils import generate_simulated_audio

logger = logging.getLogger(__name__)


class AudioService:
    """
    Service for handling text-to-speech audio generation.

    This service simulates the OpenAI text-to-speech API, generating
    audio files in various formats with realistic processing times.

    Supported voices:
        - alloy: Neutral and balanced
        - echo: Clear and expressive
        - fable: Warm and engaging
        - onyx: Deep and authoritative
        - nova: Bright and energetic
        - shimmer: Soft and gentle
        - marin: Natural and conversational (extended)
        - cedar: Rich and smooth (extended)

    Supported formats:
        - mp3: MPEG-1 Layer 3 (default, widely compatible)
        - opus: Opus codec (efficient streaming)
        - aac: Advanced Audio Coding (high quality)
        - flac: Free Lossless Audio Codec (highest quality)
        - wav: Waveform Audio (uncompressed)
        - pcm: Raw PCM audio (no container)

    Speed range: 0.25x (slow) to 4.0x (fast)
    """

    def __init__(
        self,
        config: AppConfig,
        metrics_tracker: MetricsTracker,
    ):
        """
        Initialize the audio service.

        Args:
            config: Application configuration
            metrics_tracker: Metrics tracker for recording usage
        """
        self.config = config
        self.metrics_tracker = metrics_tracker

    async def create_speech(self, request: SpeechRequest) -> bytes:
        """
        Create text-to-speech audio.

        Generates simulated audio files in the requested format with realistic
        duration based on the input text length and speed parameter.

        Processing time is estimated based on:
        - Text length: Longer text takes more time to process
        - Speed parameter: Higher speeds require less processing time
        - Base latency: Simulates model initialization and encoding

        Args:
            request: SpeechRequest containing:
                - model: TTS model ID (e.g., "tts-1", "tts-1-hd")
                - input: Text to convert (max 4096 characters)
                - voice: Voice to use (alloy, echo, fable, onyx, nova, shimmer, marin, cedar)
                - response_format: Audio format (mp3, opus, aac, flac, wav, pcm)
                - speed: Playback speed multiplier (0.25 to 4.0)

        Returns:
            Bytes containing the audio file in the requested format

        Raises:
            ValueError: If parameters are invalid

        Example:
            >>> service = AudioService(config, metrics_tracker)
            >>> request = SpeechRequest(
            ...     model="tts-1",
            ...     input="Hello world!",
            ...     voice="alloy",
            ...     response_format="mp3",
            ...     speed=1.0
            ... )
            >>> audio_bytes = await service.create_speech(request)
            >>> len(audio_bytes)  # Returns size of generated audio file
            1234
        """
        # Validate voice (should be caught by Pydantic, but double-check)
        valid_voices = [
            "alloy",
            "echo",
            "fable",
            "onyx",
            "nova",
            "shimmer",
            "marin",
            "cedar",
        ]
        if request.voice not in valid_voices:
            raise ValueError(
                f"Invalid voice '{request.voice}'. "
                f"Must be one of: {', '.join(valid_voices)}"
            )

        # Validate format (should be caught by Pydantic, but double-check)
        valid_formats = ["mp3", "opus", "aac", "flac", "wav", "pcm"]
        if request.response_format not in valid_formats:
            raise ValueError(
                f"Invalid format '{request.response_format}'. "
                f"Must be one of: {', '.join(valid_formats)}"
            )

        # Estimate processing time based on text length and speed
        # Real TTS systems have latency proportional to output length
        text_length = len(request.input)

        # Base delay: ~0.5s + 0.1s per 100 characters / speed
        # This simulates:
        # - Model initialization: 0.5s
        # - Text processing: proportional to length
        # - Speed adjustment: faster speeds reduce processing time
        base_delay = 0.5 + (text_length / 100) * 0.1 / request.speed

        # Add some randomness for realism (±0.1-0.3s variance)
        # This simulates variable system load and network conditions
        delay = base_delay + random.uniform(0.1, 0.3)

        # Simulate processing time
        await asyncio.sleep(delay)

        # Generate audio using utils function
        # This creates a properly formatted audio file with realistic duration
        audio_bytes = generate_simulated_audio(
            text=request.input,
            voice=request.voice,
            response_format=request.response_format,
            speed=request.speed,
        )

        # Track character count as token usage
        # TTS APIs typically charge per character, not per token
        character_count = len(request.input)
        self.metrics_tracker.track_tokens("/v1/audio/speech", character_count)

        # Log the generation
        logger.info(
            f"Generated {request.response_format} audio: "
            f"{len(audio_bytes)} bytes, "
            f"voice={request.voice}, "
            f"speed={request.speed}x, "
            f"text_length={character_count} chars"
        )

        return audio_bytes
