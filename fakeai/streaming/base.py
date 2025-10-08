"""
Base types and protocols for the unified streaming framework.

This module defines the core abstractions, data structures, and protocols
used throughout the streaming system.
"""

#  SPDX-License-Identifier: Apache-2.0

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, AsyncIterator, Protocol, runtime_checkable


class StreamType(Enum):
    """Type of stream being generated."""

    CHAT = "chat"
    COMPLETION = "completion"
    AUDIO = "audio"
    REALTIME = "realtime"
    IMAGE = "image"
    EMBEDDING = "embedding"


class StreamStatus(Enum):
    """Current status of a stream."""

    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class ErrorSeverity(Enum):
    """Severity level of streaming errors."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class StreamContext:
    """
    Context information for a stream.

    Contains all metadata and configuration needed to manage a stream's lifecycle.
    """

    stream_id: str
    stream_type: StreamType
    model: str
    endpoint: str
    start_time: float = field(default_factory=time.time)
    timeout_seconds: float | None = None
    chunk_delay_seconds: float = 0.05
    max_chunks: int | None = None
    enable_metrics: bool = True
    enable_latency_simulation: bool = True
    kv_cache_enabled: bool = True
    prompt_tokens: int = 0
    temperature: float = 1.0
    max_tokens: int | None = None
    client_id: str | None = None
    request_metadata: dict[str, Any] = field(default_factory=dict)

    def elapsed_time(self) -> float:
        """Get elapsed time since stream start."""
        return time.time() - self.start_time

    def is_timeout(self) -> bool:
        """Check if stream has exceeded timeout."""
        if self.timeout_seconds is None:
            return False
        return self.elapsed_time() > self.timeout_seconds


@dataclass
class StreamChunk:
    """
    A single chunk of streaming data.

    Represents one unit of data in a stream, with metadata for tracking
    and formatting.
    """

    chunk_id: str
    sequence_number: int
    data: Any
    chunk_type: str = "data"
    timestamp: float = field(default_factory=time.time)
    token_count: int = 0
    is_first: bool = False
    is_last: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert chunk to dictionary representation."""
        return {
            "chunk_id": self.chunk_id,
            "sequence_number": self.sequence_number,
            "data": self.data,
            "chunk_type": self.chunk_type,
            "timestamp": self.timestamp,
            "token_count": self.token_count,
            "is_first": self.is_first,
            "is_last": self.is_last,
            "metadata": self.metadata,
        }


@dataclass
class StreamError:
    """
    Error information for stream failures.

    Captures detailed error context for debugging and recovery.
    """

    error_code: str
    message: str
    severity: ErrorSeverity
    timestamp: float = field(default_factory=time.time)
    recoverable: bool = False
    retry_after_seconds: float | None = None
    context: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert error to dictionary representation."""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "severity": self.severity.value,
            "timestamp": self.timestamp,
            "recoverable": self.recoverable,
            "retry_after_seconds": self.retry_after_seconds,
            "context": self.context,
        }


@dataclass
class StreamMetrics:
    """
    Metrics collected during stream lifecycle.

    Tracks timing, throughput, and quality metrics for a stream.
    """

    stream_id: str
    start_time: float
    first_chunk_time: float | None = None
    last_chunk_time: float | None = None
    completion_time: float | None = None
    total_chunks: int = 0
    total_tokens: int = 0
    total_bytes: int = 0
    error_count: int = 0
    retry_count: int = 0
    backpressure_events: int = 0

    def time_to_first_chunk_ms(self) -> float | None:
        """Calculate time to first chunk in milliseconds."""
        if self.first_chunk_time is None:
            return None
        return (self.first_chunk_time - self.start_time) * 1000

    def total_duration_ms(self) -> float | None:
        """Calculate total duration in milliseconds."""
        if self.completion_time is None:
            return None
        return (self.completion_time - self.start_time) * 1000

    def tokens_per_second(self) -> float | None:
        """Calculate tokens per second throughput."""
        if self.completion_time is None or self.first_chunk_time is None:
            return None
        duration = self.completion_time - self.first_chunk_time
        if duration <= 0:
            return None
        return self.total_tokens / duration

    def to_dict(self) -> dict[str, Any]:
        """Convert metrics to dictionary representation."""
        return {
            "stream_id": self.stream_id,
            "start_time": self.start_time,
            "first_chunk_time": self.first_chunk_time,
            "last_chunk_time": self.last_chunk_time,
            "completion_time": self.completion_time,
            "total_chunks": self.total_chunks,
            "total_tokens": self.total_tokens,
            "total_bytes": self.total_bytes,
            "error_count": self.error_count,
            "retry_count": self.retry_count,
            "backpressure_events": self.backpressure_events,
            "time_to_first_chunk_ms": self.time_to_first_chunk_ms(),
            "total_duration_ms": self.total_duration_ms(),
            "tokens_per_second": self.tokens_per_second(),
        }


@runtime_checkable
class StreamingGenerator(Protocol):
    """
    Protocol for streaming generators.

    Defines the interface that all streaming generators must implement.
    """

    async def generate(
        self,
        context: StreamContext,
        full_response: Any,
    ) -> AsyncIterator[StreamChunk]:
        """
        Generate streaming chunks from a complete response.

        Args:
            context: Stream context with configuration
            full_response: Complete response object to stream

        Yields:
            StreamChunk objects representing incremental data
        """
        ...


@runtime_checkable
class ChunkFormatter(Protocol):
    """
    Protocol for chunk formatters.

    Defines the interface for formatting chunks into specific output formats
    (SSE, JSON Lines, etc.).
    """

    def format(self, chunk: StreamChunk) -> str:
        """
        Format a chunk for transmission.

        Args:
            chunk: Chunk to format

        Returns:
            Formatted string ready for transmission
        """
        ...

    def format_error(self, error: StreamError) -> str:
        """
        Format an error for transmission.

        Args:
            error: Error to format

        Returns:
            Formatted error string
        """
        ...

    def format_done(self) -> str:
        """
        Format the stream completion signal.

        Returns:
            Formatted completion signal
        """
        ...


class StreamCancelledException(Exception):
    """Exception raised when a stream is cancelled by the client."""

    def __init__(self, stream_id: str, message: str = "Stream cancelled"):
        self.stream_id = stream_id
        self.message = message
        super().__init__(f"{message}: {stream_id}")


class StreamTimeoutException(Exception):
    """Exception raised when a stream exceeds its timeout."""

    def __init__(
            self,
            stream_id: str,
            timeout_seconds: float,
            message: str = "Stream timeout"):
        self.stream_id = stream_id
        self.timeout_seconds = timeout_seconds
        self.message = message
        super().__init__(
            f"{message}: {stream_id} (timeout: {timeout_seconds}s)"
        )


class StreamGenerationException(Exception):
    """Exception raised when stream generation fails."""

    def __init__(
        self,
        stream_id: str,
        error: StreamError,
        message: str = "Stream generation failed",
    ):
        self.stream_id = stream_id
        self.error = error
        self.message = message
        super().__init__(f"{message}: {stream_id} - {error.message}")
