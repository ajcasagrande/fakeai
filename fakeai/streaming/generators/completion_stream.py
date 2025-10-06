"""
Text completion streaming generator.

Generates streaming chunks for OpenAI-compatible legacy completion responses.
"""

#  SPDX-License-Identifier: Apache-2.0

import asyncio
import time
import uuid
from typing import Any, AsyncIterator

from fakeai.streaming.base import StreamChunk, StreamContext
from fakeai.streaming.chunking import DeltaGenerator, TokenChunker


class CompletionStreamingGenerator:
    """
    Generator for text completion streaming.

    Converts a complete completion response into a series of text chunks,
    simulating realistic token-by-token streaming with proper timing.
    """

    def __init__(
        self,
        latency_manager=None,
        default_chunk_size: int = 3,
        min_chunk_size: int = 1,
        max_chunk_size: int = 10,
    ):
        """
        Initialize completion streaming generator.

        Args:
            latency_manager: LatencyProfileManager for timing simulation
            default_chunk_size: Default tokens per chunk
            min_chunk_size: Minimum tokens per chunk
            max_chunk_size: Maximum tokens per chunk
        """
        self.latency_manager = latency_manager
        self.chunker = TokenChunker(
            min_chunk_size=min_chunk_size,
            max_chunk_size=max_chunk_size,
        )
        self.delta_generator = DeltaGenerator()

    async def generate(
        self,
        context: StreamContext,
        full_response: Any,
    ) -> AsyncIterator[StreamChunk]:
        """
        Generate streaming chunks from a complete completion response.

        Args:
            context: Stream context with configuration
            full_response: Complete CompletionResponse object

        Yields:
            StreamChunk objects representing text deltas
        """
        # Extract response data
        if not full_response or not hasattr(full_response, "choices"):
            return

        if not full_response.choices:
            return

        choice = full_response.choices[0]

        # Extract completion text
        text = choice.text or ""
        finish_reason = choice.finish_reason

        # Tokenize text
        tokens = self.chunker.tokenize(text)

        if not tokens:
            # Empty response, send just finish
            chunk = self._create_chunk(
                context=context,
                sequence=0,
                text="",
                finish_reason=finish_reason,
                is_first=True,
                is_last=True,
                response=full_response,
            )
            yield chunk
            return

        # Calculate timing if latency simulation is enabled
        ttft_delay = 0.0
        itl_delay = context.chunk_delay_seconds

        if context.enable_latency_simulation and self.latency_manager:
            # Get realistic TTFT
            ttft_delay = self.latency_manager.get_ttft(
                model=context.model,
                prompt_tokens=context.prompt_tokens,
                temperature=context.temperature,
            )

            # Get realistic ITL
            itl_delay = self.latency_manager.get_itl(
                model=context.model,
                temperature=context.temperature,
            )

        # Wait for TTFT before first token
        if ttft_delay > 0:
            await asyncio.sleep(ttft_delay)

        # Stream text tokens
        sequence = 0
        for i, token in enumerate(tokens):
            is_first = i == 0
            is_last = i == len(tokens) - 1

            # Create chunk with text
            chunk = self._create_chunk(
                context=context,
                sequence=sequence,
                text=token,
                finish_reason=finish_reason if is_last else None,
                is_first=is_first,
                is_last=is_last,
                response=full_response,
                token_count=1,
            )

            yield chunk
            sequence += 1

            # Wait for inter-token delay (except after last token)
            if not is_last and itl_delay > 0:
                await asyncio.sleep(itl_delay)

    def _create_chunk(
        self,
        context: StreamContext,
        sequence: int,
        text: str,
        finish_reason: str | None,
        is_first: bool,
        is_last: bool,
        response: Any,
        token_count: int = 0,
    ) -> StreamChunk:
        """
        Create a stream chunk with proper OpenAI completion format.

        Args:
            context: Stream context
            sequence: Sequence number
            text: Text content
            finish_reason: Finish reason (for last chunk)
            is_first: Whether this is the first chunk
            is_last: Whether this is the last chunk
            response: Original response object
            token_count: Number of tokens in this chunk

        Returns:
            StreamChunk object
        """
        # Build chunk data in OpenAI format
        chunk_data = {
            "id": response.id if hasattr(response, "id") else f"cmpl-{uuid.uuid4().hex[:12]}",
            "object": "text_completion",
            "created": int(response.created if hasattr(response, "created") else time.time()),
            "model": context.model,
            "choices": [
                {
                    "text": text,
                    "index": 0,
                    "finish_reason": finish_reason,
                    "logprobs": None,
                }
            ],
        }

        # Add usage info to last chunk (if available)
        if is_last and hasattr(response, "usage") and response.usage:
            chunk_data["usage"] = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }

        return StreamChunk(
            chunk_id=f"{context.stream_id}-{sequence}",
            sequence_number=sequence,
            data=chunk_data,
            chunk_type="text_completion",
            token_count=token_count,
            is_first=is_first,
            is_last=is_last,
            metadata={
                "model": context.model,
                "endpoint": context.endpoint,
            },
        )
