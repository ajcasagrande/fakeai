"""
Chat completion streaming generator.

Generates streaming chunks for OpenAI-compatible chat completion responses.
"""

#  SPDX-License-Identifier: Apache-2.0

import asyncio
import time
import uuid
from typing import Any, AsyncIterator

from fakeai.streaming.base import StreamChunk, StreamContext
from fakeai.streaming.chunking import DeltaGenerator, TokenChunker


class ChatStreamingGenerator:
    """
    Generator for chat completion streaming.

    Converts a complete chat response into a series of delta chunks,
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
        Initialize chat streaming generator.

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
        Generate streaming chunks from a complete chat response.

        Args:
            context: Stream context with configuration
            full_response: Complete ChatCompletionResponse object

        Yields:
            StreamChunk objects representing chat deltas
        """
        # Extract response data
        if not full_response or not hasattr(full_response, "choices"):
            return

        if not full_response.choices:
            return

        choice = full_response.choices[0]
        message = choice.message

        # Extract message content
        content = message.content or ""
        role = message.role
        finish_reason = choice.finish_reason

        # Tokenize content
        tokens = self.chunker.tokenize(content)

        if not tokens:
            # Empty response, send just role and finish
            chunk = self._create_chunk(
                context=context,
                sequence=0,
                delta=self.delta_generator.generate_chat_delta(
                    role=role,
                    finish_reason=finish_reason,
                ),
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

        # First chunk: role only (after TTFT delay)
        if ttft_delay > 0:
            await asyncio.sleep(ttft_delay)

        first_chunk = self._create_chunk(
            context=context,
            sequence=0,
            delta=self.delta_generator.generate_chat_delta(role=role),
            is_first=True,
            is_last=False,
            response=full_response,
        )
        yield first_chunk

        # Stream content tokens
        sequence = 1
        for i, token in enumerate(tokens):
            # Wait for inter-token delay
            if itl_delay > 0:
                await asyncio.sleep(itl_delay)

            # Create chunk with content delta
            delta = self.delta_generator.generate_chat_delta(content=token)

            chunk = self._create_chunk(
                context=context,
                sequence=sequence,
                delta=delta,
                is_first=False,
                is_last=False,
                response=full_response,
                token_count=1,
            )

            yield chunk
            sequence += 1

        # Final chunk: finish_reason
        final_chunk = self._create_chunk(
            context=context,
            sequence=sequence,
            delta=self.delta_generator.generate_chat_delta(
                finish_reason=finish_reason
            ),
            is_first=False,
            is_last=True,
            response=full_response,
        )
        yield final_chunk

    def _create_chunk(
        self,
        context: StreamContext,
        sequence: int,
        delta: dict[str, Any],
        is_first: bool,
        is_last: bool,
        response: Any,
        token_count: int = 0,
    ) -> StreamChunk:
        """
        Create a stream chunk with proper OpenAI format.

        Args:
            context: Stream context
            sequence: Sequence number
            delta: Delta object
            is_first: Whether this is the first chunk
            is_last: Whether this is the last chunk
            response: Original response object
            token_count: Number of tokens in this chunk

        Returns:
            StreamChunk object
        """
        # Build chunk data in OpenAI format
        chunk_data = {
            "id": response.id if hasattr(response, "id") else f"chatcmpl-{uuid.uuid4().hex[:12]}",
            "object": "chat.completion.chunk",
            "created": int(response.created if hasattr(response, "created") else time.time()),
            "model": context.model,
            "choices": [
                {
                    "index": 0,
                    "delta": delta,
                    "finish_reason": delta.get("finish_reason"),
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
            chunk_type="chat.completion.chunk",
            token_count=token_count,
            is_first=is_first,
            is_last=is_last,
            metadata={
                "model": context.model,
                "endpoint": context.endpoint,
            },
        )
