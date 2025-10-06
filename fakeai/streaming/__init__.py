"""
Unified Streaming Framework for FakeAI

This module provides a comprehensive streaming infrastructure with support for
multiple streaming types (chat, completion, audio, realtime), configurable chunking,
SSE formatting, metrics tracking, and error handling.

Key Components:
- StreamManager: Orchestrates stream creation and lifecycle
- TokenChunker: Handles token-based chunking with configurable algorithms
- DeltaGenerator: Generates delta objects for streaming responses
- SSEFormatter: Formats chunks as Server-Sent Events
- StreamingMetricsTracker: Tracks detailed streaming metrics
- LatencyProfileManager: Provides realistic model-specific latency profiles

Usage:
    from fakeai.streaming import StreamManager, StreamType, SSEFormatter

    manager = StreamManager(metrics_tracker=metrics, latency_manager=latency)

    async for chunk in manager.create_stream(
        stream_type=StreamType.CHAT,
        stream_id="stream-123",
        model="gpt-4o",
        full_response=chat_response,
        endpoint="/v1/chat/completions"
    ):
        yield SSEFormatter.format(chunk)
"""

#  SPDX-License-Identifier: Apache-2.0

from fakeai.streaming.base import (
    ChunkFormatter,
    ErrorSeverity,
    StreamCancelledException,
    StreamChunk,
    StreamContext,
    StreamError,
    StreamingGenerator,
    StreamMetrics,
    StreamStatus,
    StreamTimeoutException,
    StreamType,
)
from fakeai.streaming.chunking import DeltaGenerator, ProgressTracker, TokenChunker
from fakeai.streaming.manager import StreamManager
from fakeai.streaming.sse import JSONLinesFormatter, PlainTextFormatter, SSEFormatter

__all__ = [
    # Base types
    "StreamType",
    "StreamStatus",
    "ErrorSeverity",
    "StreamContext",
    "StreamChunk",
    "StreamError",
    "StreamMetrics",
    "StreamingGenerator",
    "ChunkFormatter",
    "StreamCancelledException",
    "StreamTimeoutException",
    # Manager
    "StreamManager",
    # Chunking
    "TokenChunker",
    "DeltaGenerator",
    "ProgressTracker",
    # Formatters
    "SSEFormatter",
    "JSONLinesFormatter",
    "PlainTextFormatter",
]

__version__ = "0.1.0"
