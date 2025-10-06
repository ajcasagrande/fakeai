"""
Audio streaming generator.

Generates streaming chunks for audio synthesis and transcription.
"""

#  SPDX-License-Identifier: Apache-2.0

import asyncio
from typing import Any, AsyncIterator

from fakeai.streaming.base import StreamChunk, StreamContext


class AudioStreamingGenerator:
    """
    Generator for audio streaming.

    Converts audio data into streamable chunks with optional transcription.
    """

    def __init__(self, latency_manager=None, chunk_size_bytes: int = 4096):
        """
        Initialize audio streaming generator.

        Args:
            latency_manager: LatencyProfileManager for timing simulation
            chunk_size_bytes: Size of audio chunks in bytes
        """
        self.latency_manager = latency_manager
        self.chunk_size_bytes = chunk_size_bytes

    async def generate(
        self,
        context: StreamContext,
        full_response: Any,
    ) -> AsyncIterator[StreamChunk]:
        """
        Generate streaming audio chunks.

        Args:
            context: Stream context with configuration
            full_response: Complete audio response object

        Yields:
            StreamChunk objects representing audio data
        """
        # Extract audio data
        audio_data = getattr(full_response, "audio", b"")
        transcript = getattr(full_response, "transcript", None)

        if not audio_data:
            return

        # Calculate chunk count
        total_chunks = (len(audio_data) + self.chunk_size_bytes - 1) // self.chunk_size_bytes

        # Stream audio chunks
        sequence = 0
        for i in range(0, len(audio_data), self.chunk_size_bytes):
            chunk_data = audio_data[i : i + self.chunk_size_bytes]

            # Create chunk
            chunk = StreamChunk(
                chunk_id=f"{context.stream_id}-{sequence}",
                sequence_number=sequence,
                data={
                    "audio": chunk_data,
                    "transcript": transcript if i == 0 else None,
                },
                chunk_type="audio",
                is_first=(sequence == 0),
                is_last=(sequence == total_chunks - 1),
                metadata={
                    "model": context.model,
                    "endpoint": context.endpoint,
                    "chunk_size": len(chunk_data),
                },
            )

            yield chunk
            sequence += 1

            # Delay between chunks
            if context.chunk_delay_seconds > 0:
                await asyncio.sleep(context.chunk_delay_seconds)
