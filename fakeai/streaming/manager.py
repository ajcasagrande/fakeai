"""
Stream Manager - Core orchestration for unified streaming.

This module provides the StreamManager class, which orchestrates the creation
and lifecycle management of streams, integrating metrics, latency simulation,
KV cache, error handling, and timeout enforcement.
"""

#  SPDX-License-Identifier: Apache-2.0

import asyncio
import logging
import time
import uuid
from typing import Any, AsyncIterator

from fakeai.streaming.base import (
    ErrorSeverity,
    StreamCancelledException,
    StreamChunk,
    StreamContext,
    StreamError,
    StreamGenerationException,
    StreamMetrics,
    StreamStatus,
    StreamTimeoutException,
    StreamType,
    StreamingGenerator,
)

logger = logging.getLogger(__name__)


class StreamManager:
    """
    Manages stream lifecycle and orchestrates streaming components.

    The StreamManager is responsible for:
    - Creating and initializing streams
    - Enforcing timeouts
    - Tracking metrics
    - Handling errors and cancellations
    - Coordinating with KV cache and latency simulation
    """

    def __init__(
        self,
        metrics_tracker=None,
        streaming_metrics_tracker=None,
        latency_manager=None,
        kv_cache_router=None,
        kv_cache_metrics=None,
        default_timeout_seconds: float = 300.0,
        enable_metrics: bool = True,
        enable_latency_simulation: bool = True,
    ):
        """
        Initialize stream manager.

        Args:
            metrics_tracker: MetricsTracker instance for basic metrics
            streaming_metrics_tracker: StreamingMetricsTracker for detailed metrics
            latency_manager: LatencyProfileManager for timing simulation
            kv_cache_router: SmartRouter for KV cache routing
            kv_cache_metrics: KVCacheMetrics for cache performance tracking
            default_timeout_seconds: Default stream timeout
            enable_metrics: Whether to track metrics
            enable_latency_simulation: Whether to simulate realistic latency
        """
        self.metrics_tracker = metrics_tracker
        self.streaming_metrics_tracker = streaming_metrics_tracker
        self.latency_manager = latency_manager
        self.kv_cache_router = kv_cache_router
        self.kv_cache_metrics = kv_cache_metrics
        self.default_timeout_seconds = default_timeout_seconds
        self.enable_metrics = enable_metrics
        self.enable_latency_simulation = enable_latency_simulation

        # Active streams tracking
        self._active_streams: dict[str, StreamStatus] = {}
        self._stream_metrics: dict[str, StreamMetrics] = {}
        self._lock = asyncio.Lock()

        logger.info("StreamManager initialized")

    async def create_stream(
        self,
        stream_type: StreamType,
        stream_id: str | None = None,
        model: str = "gpt-4o",
        full_response: Any = None,
        endpoint: str = "/v1/chat/completions",
        timeout_seconds: float | None = None,
        chunk_delay_seconds: float = 0.05,
        max_chunks: int | None = None,
        prompt_tokens: int = 0,
        temperature: float = 1.0,
        max_tokens: int | None = None,
        client_id: str | None = None,
        request_metadata: dict[str, Any] | None = None,
        generator: StreamingGenerator | None = None,
    ) -> AsyncIterator[StreamChunk]:
        """
        Create and manage a streaming response.

        This is the main entry point for creating streams. It handles:
        - Stream initialization
        - Metrics tracking
        - Timeout enforcement
        - Error handling
        - Cleanup

        Args:
            stream_type: Type of stream to create
            stream_id: Optional stream identifier (generated if not provided)
            model: Model being used
            full_response: Complete response object to stream
            endpoint: API endpoint path
            timeout_seconds: Stream timeout (uses default if not provided)
            chunk_delay_seconds: Base delay between chunks
            max_chunks: Maximum number of chunks to generate
            prompt_tokens: Number of input tokens (for metrics)
            temperature: Sampling temperature
            max_tokens: Maximum output tokens
            client_id: Client identifier (for behavior tracking)
            request_metadata: Additional request metadata
            generator: Custom streaming generator (uses default if not provided)

        Yields:
            StreamChunk objects representing incremental data

        Raises:
            StreamTimeoutException: If stream exceeds timeout
            StreamCancelledException: If stream is cancelled
            StreamGenerationException: If generation fails
        """
        # Generate stream ID if not provided
        if stream_id is None:
            stream_id = f"stream-{uuid.uuid4().hex[:12]}"

        # Use default timeout if not specified
        if timeout_seconds is None:
            timeout_seconds = self.default_timeout_seconds

        # Create stream context
        context = StreamContext(
            stream_id=stream_id,
            stream_type=stream_type,
            model=model,
            endpoint=endpoint,
            start_time=time.time(),
            timeout_seconds=timeout_seconds,
            chunk_delay_seconds=chunk_delay_seconds,
            max_chunks=max_chunks,
            enable_metrics=self.enable_metrics and self.metrics_tracker is not None,
            enable_latency_simulation=self.enable_latency_simulation
            and self.latency_manager is not None,
            kv_cache_enabled=self.kv_cache_router is not None,
            prompt_tokens=prompt_tokens,
            temperature=temperature,
            max_tokens=max_tokens,
            client_id=client_id,
            request_metadata=request_metadata or {},
        )

        # Initialize metrics
        stream_metrics = StreamMetrics(
            stream_id=stream_id,
            start_time=context.start_time,
        )

        try:
            # Mark stream as active
            async with self._lock:
                self._active_streams[stream_id] = StreamStatus.INITIALIZING
                self._stream_metrics[stream_id] = stream_metrics

            # Start metrics tracking
            if context.enable_metrics:
                self._start_metrics_tracking(context)

            # Get generator if not provided
            if generator is None:
                generator = self._get_default_generator(stream_type)

            # Mark as running
            async with self._lock:
                self._active_streams[stream_id] = StreamStatus.RUNNING

            # Generate stream chunks
            async for chunk in self._generate_with_timeout(
                generator, context, full_response, stream_metrics
            ):
                # Check for timeout
                if context.is_timeout():
                    raise StreamTimeoutException(
                        stream_id=stream_id,
                        timeout_seconds=timeout_seconds,
                    )

                # Track chunk metrics
                self._track_chunk(stream_metrics, chunk)

                # Yield chunk to caller
                yield chunk

                # Check max chunks limit
                if max_chunks and stream_metrics.total_chunks >= max_chunks:
                    logger.info(
                        f"Stream {stream_id} reached max chunks limit: {max_chunks}"
                    )
                    break

            # Complete stream successfully
            await self._complete_stream(context, stream_metrics)

        except StreamTimeoutException as e:
            logger.warning(f"Stream {stream_id} timeout: {timeout_seconds}s")
            await self._fail_stream(
                context,
                stream_metrics,
                StreamError(
                    error_code="stream_timeout",
                    message=f"Stream exceeded timeout of {timeout_seconds}s",
                    severity=ErrorSeverity.ERROR,
                    recoverable=True,
                    retry_after_seconds=1.0,
                ),
            )
            raise

        except StreamCancelledException as e:
            logger.info(f"Stream {stream_id} cancelled")
            await self._cancel_stream(context, stream_metrics)
            raise

        except Exception as e:
            logger.error(f"Stream {stream_id} generation failed: {e}", exc_info=True)
            await self._fail_stream(
                context,
                stream_metrics,
                StreamError(
                    error_code="stream_generation_failed",
                    message=str(e),
                    severity=ErrorSeverity.CRITICAL,
                    recoverable=False,
                ),
            )
            raise StreamGenerationException(
                stream_id=stream_id,
                error=StreamError(
                    error_code="stream_generation_failed",
                    message=str(e),
                    severity=ErrorSeverity.CRITICAL,
                ),
            )

        finally:
            # Cleanup
            await self._cleanup_stream(stream_id)

    async def _generate_with_timeout(
        self,
        generator: StreamingGenerator,
        context: StreamContext,
        full_response: Any,
        stream_metrics: StreamMetrics,
    ) -> AsyncIterator[StreamChunk]:
        """
        Generate chunks with timeout enforcement.

        Args:
            generator: Streaming generator to use
            context: Stream context
            full_response: Full response object
            stream_metrics: Metrics tracker

        Yields:
            StreamChunk objects
        """
        timeout = context.timeout_seconds

        try:
            async for chunk in generator.generate(context, full_response):
                # Check timeout before yielding
                if context.is_timeout():
                    raise StreamTimeoutException(
                        stream_id=context.stream_id,
                        timeout_seconds=timeout,
                    )

                yield chunk

        except asyncio.TimeoutError:
            raise StreamTimeoutException(
                stream_id=context.stream_id,
                timeout_seconds=timeout,
            )

    def _get_default_generator(self, stream_type: StreamType) -> StreamingGenerator:
        """
        Get default generator for stream type.

        Args:
            stream_type: Type of stream

        Returns:
            Appropriate generator instance

        Raises:
            ValueError: If stream type is not supported
        """
        # Import generators here to avoid circular imports
        from fakeai.streaming.generators.chat_stream import ChatStreamingGenerator
        from fakeai.streaming.generators.completion_stream import (
            CompletionStreamingGenerator,
        )

        if stream_type == StreamType.CHAT:
            return ChatStreamingGenerator(
                latency_manager=self.latency_manager,
            )
        elif stream_type == StreamType.COMPLETION:
            return CompletionStreamingGenerator(
                latency_manager=self.latency_manager,
            )
        else:
            raise ValueError(f"Unsupported stream type: {stream_type}")

    def _start_metrics_tracking(self, context: StreamContext):
        """
        Start tracking metrics for stream.

        Args:
            context: Stream context
        """
        # Track request in basic metrics
        if self.metrics_tracker:
            self.metrics_tracker.track_request(context.endpoint)
            self.metrics_tracker.start_stream(context.stream_id, context.endpoint)

        # Track in detailed streaming metrics
        if self.streaming_metrics_tracker:
            self.streaming_metrics_tracker.start_stream(
                stream_id=context.stream_id,
                model=context.model,
                prompt_tokens=context.prompt_tokens,
                temperature=context.temperature,
                max_tokens=context.max_tokens,
                client_id=context.client_id,
            )

        # Track with latency manager
        if self.latency_manager:
            self.latency_manager.start_request()

    def _track_chunk(self, stream_metrics: StreamMetrics, chunk: StreamChunk):
        """
        Track metrics for a generated chunk.

        Args:
            stream_metrics: Stream metrics tracker
            chunk: Generated chunk
        """
        # Update stream metrics
        stream_metrics.total_chunks += 1
        stream_metrics.total_tokens += chunk.token_count
        stream_metrics.last_chunk_time = chunk.timestamp

        if stream_metrics.first_chunk_time is None:
            stream_metrics.first_chunk_time = chunk.timestamp

        # Track in basic metrics
        if self.metrics_tracker:
            self.metrics_tracker.track_stream_token(stream_metrics.stream_id)
            if stream_metrics.first_chunk_time == chunk.timestamp:
                self.metrics_tracker.track_stream_first_token(stream_metrics.stream_id)

        # Track in detailed streaming metrics
        if self.streaming_metrics_tracker:
            # Extract token text from chunk
            token_text = self._extract_token_text(chunk)
            if token_text:
                self.streaming_metrics_tracker.record_token(
                    stream_id=stream_metrics.stream_id,
                    token=token_text,
                )

    def _extract_token_text(self, chunk: StreamChunk) -> str:
        """
        Extract token text from chunk data.

        Args:
            chunk: Stream chunk

        Returns:
            Token text or empty string
        """
        if isinstance(chunk.data, dict):
            # Try to extract from common formats
            if "choices" in chunk.data:
                choices = chunk.data["choices"]
                if choices and len(choices) > 0:
                    choice = choices[0]
                    if "delta" in choice:
                        delta = choice["delta"]
                        return delta.get("content", "")
                    elif "text" in choice:
                        return choice["text"]
            elif "content" in chunk.data:
                return chunk.data["content"]
            elif "text" in chunk.data:
                return chunk.data["text"]
        elif isinstance(chunk.data, str):
            return chunk.data

        return ""

    async def _complete_stream(
        self, context: StreamContext, stream_metrics: StreamMetrics
    ):
        """
        Complete a stream successfully.

        Args:
            context: Stream context
            stream_metrics: Stream metrics
        """
        stream_metrics.completion_time = time.time()

        async with self._lock:
            self._active_streams[context.stream_id] = StreamStatus.COMPLETED

        # Complete metrics tracking
        if self.metrics_tracker:
            self.metrics_tracker.complete_stream(
                context.stream_id, context.endpoint
            )
            latency = stream_metrics.total_duration_ms() / 1000 if stream_metrics.total_duration_ms() else 0
            self.metrics_tracker.track_response(context.endpoint, latency)
            self.metrics_tracker.track_tokens(
                context.endpoint, stream_metrics.total_tokens
            )

        if self.streaming_metrics_tracker:
            self.streaming_metrics_tracker.complete_stream(
                stream_id=context.stream_id,
                finish_reason="stop",
                client_id=context.client_id,
            )

        if self.latency_manager:
            self.latency_manager.end_request()

        logger.info(
            f"Stream {context.stream_id} completed: "
            f"{stream_metrics.total_chunks} chunks, "
            f"{stream_metrics.total_tokens} tokens, "
            f"{stream_metrics.total_duration_ms():.1f}ms"
        )

    async def _fail_stream(
        self,
        context: StreamContext,
        stream_metrics: StreamMetrics,
        error: StreamError,
    ):
        """
        Mark stream as failed.

        Args:
            context: Stream context
            stream_metrics: Stream metrics
            error: Error information
        """
        stream_metrics.completion_time = time.time()
        stream_metrics.error_count += 1

        async with self._lock:
            self._active_streams[context.stream_id] = StreamStatus.FAILED

        # Track error in metrics
        if self.metrics_tracker:
            self.metrics_tracker.fail_stream(
                context.stream_id, context.endpoint, error.message
            )
            self.metrics_tracker.track_error(context.endpoint)

        if self.streaming_metrics_tracker:
            self.streaming_metrics_tracker.cancel_stream(
                stream_id=context.stream_id,
                error_message=error.message,
                client_id=context.client_id,
            )

        if self.latency_manager:
            self.latency_manager.end_request()

        logger.error(
            f"Stream {context.stream_id} failed: "
            f"{error.error_code} - {error.message}"
        )

    async def _cancel_stream(
        self, context: StreamContext, stream_metrics: StreamMetrics
    ):
        """
        Mark stream as cancelled.

        Args:
            context: Stream context
            stream_metrics: Stream metrics
        """
        stream_metrics.completion_time = time.time()

        async with self._lock:
            self._active_streams[context.stream_id] = StreamStatus.CANCELLED

        # Track cancellation in metrics
        if self.streaming_metrics_tracker:
            self.streaming_metrics_tracker.cancel_stream(
                stream_id=context.stream_id,
                error_message="Client cancelled",
                client_id=context.client_id,
            )

        if self.latency_manager:
            self.latency_manager.end_request()

        logger.info(f"Stream {context.stream_id} cancelled")

    async def _cleanup_stream(self, stream_id: str):
        """
        Clean up stream resources.

        Args:
            stream_id: Stream identifier
        """
        async with self._lock:
            self._active_streams.pop(stream_id, None)
            self._stream_metrics.pop(stream_id, None)

    async def get_stream_status(self, stream_id: str) -> StreamStatus | None:
        """
        Get current status of a stream.

        Args:
            stream_id: Stream identifier

        Returns:
            Stream status or None if not found
        """
        async with self._lock:
            return self._active_streams.get(stream_id)

    async def get_stream_metrics(self, stream_id: str) -> dict[str, Any] | None:
        """
        Get metrics for a stream.

        Args:
            stream_id: Stream identifier

        Returns:
            Metrics dictionary or None if not found
        """
        async with self._lock:
            metrics = self._stream_metrics.get(stream_id)
            if metrics:
                return metrics.to_dict()
            return None

    async def get_active_stream_count(self) -> int:
        """
        Get count of currently active streams.

        Returns:
            Number of active streams
        """
        async with self._lock:
            return len(self._active_streams)

    async def cancel_stream(self, stream_id: str) -> bool:
        """
        Cancel a running stream.

        Args:
            stream_id: Stream identifier

        Returns:
            True if stream was cancelled, False if not found or already completed
        """
        async with self._lock:
            status = self._active_streams.get(stream_id)
            if status in (StreamStatus.RUNNING, StreamStatus.INITIALIZING):
                self._active_streams[stream_id] = StreamStatus.CANCELLED
                return True
            return False
