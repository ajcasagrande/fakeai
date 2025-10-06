"""
Chunking and token management for streaming.

This module provides utilities for breaking down full responses into
streamable chunks, generating deltas, and tracking progress.
"""

#  SPDX-License-Identifier: Apache-2.0

import re
import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class TokenTiming:
    """Timing information for a single token."""

    token: str
    delay_seconds: float
    timestamp: float = field(default_factory=time.time)


class TokenChunker:
    """
    Splits text into tokens for streaming.

    Uses regex-based tokenization to separate words, punctuation, and whitespace
    while preserving the structure of the original text.
    """

    # Pattern to match words, punctuation, and whitespace
    TOKEN_PATTERN = re.compile(
        r"\b\w+\b|[.,;:!?()[\]{}<>\"'`~@#$%^&*\-+=|/\\]|\s+", re.UNICODE
    )

    def __init__(self, min_chunk_size: int = 1, max_chunk_size: int = 10):
        """
        Initialize token chunker.

        Args:
            min_chunk_size: Minimum number of tokens per chunk
            max_chunk_size: Maximum number of tokens per chunk
        """
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size

    def tokenize(self, text: str) -> list[str]:
        """
        Split text into tokens.

        Args:
            text: Text to tokenize

        Returns:
            List of token strings
        """
        if not text:
            return []

        # Find all matches
        tokens = self.TOKEN_PATTERN.findall(text)

        # Filter out pure whitespace tokens (we'll preserve them in reconstruction)
        return [t for t in tokens if t.strip()]

    def chunk_tokens(self, tokens: list[str]) -> list[list[str]]:
        """
        Group tokens into chunks.

        Args:
            tokens: List of tokens to chunk

        Returns:
            List of token chunks
        """
        if not tokens:
            return []

        chunks = []
        current_chunk = []

        for token in tokens:
            current_chunk.append(token)

            # Check if we should create a chunk
            if len(current_chunk) >= self.max_chunk_size:
                chunks.append(current_chunk)
                current_chunk = []

        # Add remaining tokens
        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    def chunk_text(self, text: str) -> list[str]:
        """
        Split text into streamable chunks.

        Args:
            text: Text to chunk

        Returns:
            List of text chunks
        """
        tokens = self.tokenize(text)
        token_chunks = self.chunk_tokens(tokens)
        return [" ".join(chunk) for chunk in token_chunks]


class DeltaGenerator:
    """
    Generates delta objects for streaming responses.

    Creates incremental updates that represent the difference between
    successive states of a streaming response.
    """

    def __init__(self):
        """Initialize delta generator."""
        self._previous_state = {}

    def generate_chat_delta(
        self,
        role: str | None = None,
        content: str | None = None,
        tool_calls: list[dict[str, Any]] | None = None,
        finish_reason: str | None = None,
    ) -> dict[str, Any]:
        """
        Generate a chat completion delta.

        Args:
            role: Message role (for first chunk)
            content: Message content delta
            tool_calls: Tool calls delta
            finish_reason: Finish reason (for last chunk)

        Returns:
            Delta dictionary
        """
        delta = {}

        if role is not None:
            delta["role"] = role

        if content is not None:
            delta["content"] = content

        if tool_calls is not None:
            delta["tool_calls"] = tool_calls

        if finish_reason is not None:
            delta["finish_reason"] = finish_reason

        return delta

    def generate_completion_delta(
        self,
        text: str | None = None,
        finish_reason: str | None = None,
    ) -> dict[str, Any]:
        """
        Generate a completion delta.

        Args:
            text: Text delta
            finish_reason: Finish reason (for last chunk)

        Returns:
            Delta dictionary
        """
        delta = {}

        if text is not None:
            delta["text"] = text

        if finish_reason is not None:
            delta["finish_reason"] = finish_reason

        return delta

    def generate_audio_delta(
        self,
        audio_chunk: bytes | None = None,
        transcript_delta: str | None = None,
    ) -> dict[str, Any]:
        """
        Generate an audio streaming delta.

        Args:
            audio_chunk: Audio data chunk
            transcript_delta: Transcript text delta

        Returns:
            Delta dictionary
        """
        delta = {}

        if audio_chunk is not None:
            delta["audio"] = audio_chunk

        if transcript_delta is not None:
            delta["transcript"] = transcript_delta

        return delta

    def reset(self):
        """Reset delta generator state."""
        self._previous_state = {}


@dataclass
class ProgressTracker:
    """
    Tracks progress of stream generation.

    Monitors chunks generated, tokens produced, and provides progress statistics.
    """

    total_tokens: int = 0
    tokens_generated: int = 0
    chunks_generated: int = 0
    start_time: float = field(default_factory=time.time)
    first_chunk_time: float | None = None

    def record_chunk(self, token_count: int):
        """
        Record a generated chunk.

        Args:
            token_count: Number of tokens in the chunk
        """
        self.chunks_generated += 1
        self.tokens_generated += token_count

        if self.first_chunk_time is None:
            self.first_chunk_time = time.time()

    def progress_percentage(self) -> float:
        """
        Calculate progress percentage.

        Returns:
            Progress as percentage (0-100)
        """
        if self.total_tokens == 0:
            return 0.0
        return min(100.0, (self.tokens_generated / self.total_tokens) * 100)

    def time_to_first_chunk_ms(self) -> float | None:
        """
        Get time to first chunk in milliseconds.

        Returns:
            Time to first chunk or None if no chunks yet
        """
        if self.first_chunk_time is None:
            return None
        return (self.first_chunk_time - self.start_time) * 1000

    def tokens_per_second(self) -> float:
        """
        Calculate current tokens per second rate.

        Returns:
            Tokens per second
        """
        if self.first_chunk_time is None:
            return 0.0

        elapsed = time.time() - self.first_chunk_time
        if elapsed <= 0:
            return 0.0

        return self.tokens_generated / elapsed

    def estimated_time_remaining_seconds(self) -> float | None:
        """
        Estimate time remaining to complete.

        Returns:
            Estimated seconds remaining or None if cannot estimate
        """
        if self.tokens_generated == 0 or self.first_chunk_time is None:
            return None

        tps = self.tokens_per_second()
        if tps <= 0:
            return None

        remaining_tokens = self.total_tokens - self.tokens_generated
        return remaining_tokens / tps

    def to_dict(self) -> dict[str, Any]:
        """
        Convert to dictionary representation.

        Returns:
            Progress metrics as dictionary
        """
        return {
            "total_tokens": self.total_tokens,
            "tokens_generated": self.tokens_generated,
            "chunks_generated": self.chunks_generated,
            "progress_percentage": self.progress_percentage(),
            "time_to_first_chunk_ms": self.time_to_first_chunk_ms(),
            "tokens_per_second": self.tokens_per_second(),
            "estimated_time_remaining_seconds": self.estimated_time_remaining_seconds(),
        }


class AdaptiveChunker:
    """
    Adaptive token chunker that adjusts chunk size based on throughput.

    Dynamically optimizes chunk size to maintain smooth streaming while
    maximizing efficiency.
    """

    def __init__(
        self,
        initial_chunk_size: int = 3,
        min_chunk_size: int = 1,
        max_chunk_size: int = 15,
        target_chunk_delay_ms: float = 50.0,
    ):
        """
        Initialize adaptive chunker.

        Args:
            initial_chunk_size: Starting chunk size
            min_chunk_size: Minimum allowed chunk size
            max_chunk_size: Maximum allowed chunk size
            target_chunk_delay_ms: Target delay between chunks in milliseconds
        """
        self.current_chunk_size = initial_chunk_size
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
        self.target_chunk_delay_ms = target_chunk_delay_ms
        self._recent_delays = []
        self._max_delay_history = 10

    def adjust_chunk_size(self, actual_delay_ms: float):
        """
        Adjust chunk size based on actual observed delay.

        Args:
            actual_delay_ms: Actual delay between chunks in milliseconds
        """
        self._recent_delays.append(actual_delay_ms)
        if len(self._recent_delays) > self._max_delay_history:
            self._recent_delays.pop(0)

        # Calculate average recent delay
        avg_delay = sum(self._recent_delays) / len(self._recent_delays)

        # Adjust chunk size to reach target delay
        if avg_delay < self.target_chunk_delay_ms * 0.8:
            # Too fast, increase chunk size
            self.current_chunk_size = min(
                self.current_chunk_size + 1, self.max_chunk_size
            )
        elif avg_delay > self.target_chunk_delay_ms * 1.2:
            # Too slow, decrease chunk size
            self.current_chunk_size = max(
                self.current_chunk_size - 1, self.min_chunk_size
            )

    def get_chunk_size(self) -> int:
        """
        Get current recommended chunk size.

        Returns:
            Current chunk size
        """
        return self.current_chunk_size

    def reset(self):
        """Reset adaptive chunker state."""
        self._recent_delays = []
