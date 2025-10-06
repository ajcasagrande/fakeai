"""
Enhanced Streaming Metrics Module

This module provides detailed streaming-specific metrics tracking beyond the basic
MetricsTracker. It tracks per-stream lifecycle, token timings, quality metrics,
client behavior, and advanced analytics.
"""

#  SPDX-License-Identifier: Apache-2.0

import logging
import statistics
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class TokenTiming:
    """Timing information for a single token."""

    token: str
    timestamp_ns: int  # Nanosecond timestamp
    chunk_size_bytes: int
    sequence_number: int  # Token position in stream


@dataclass
class StreamLifecycle:
    """Complete lifecycle tracking for a single stream."""

    stream_id: str
    model: str
    prompt_tokens: int
    start_time_ns: int

    # Token tracking
    tokens: List[TokenTiming] = field(default_factory=list)

    # Timing milestones
    first_token_time_ns: Optional[int] = None
    last_token_time_ns: Optional[int] = None
    completion_time_ns: Optional[int] = None

    # Stream state
    finish_reason: Optional[str] = None
    cancelled: bool = False
    cancellation_point: Optional[int] = None  # Token number at cancellation
    error_message: Optional[str] = None

    # Network tracking
    chunks_sent: int = 0
    total_bytes_sent: int = 0
    chunk_sizes: List[int] = field(default_factory=list)

    # Client behavior
    backpressure_events: int = 0
    stall_events: int = 0  # Inter-token latency > 500ms

    # Request metadata
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None

    def get_ttft_ms(self) -> Optional[float]:
        """Get time to first token in milliseconds."""
        if self.first_token_time_ns is None:
            return None
        return (self.first_token_time_ns - self.start_time_ns) / 1_000_000

    def get_total_duration_ms(self) -> Optional[float]:
        """Get total stream duration in milliseconds."""
        if self.completion_time_ns is None:
            return None
        return (self.completion_time_ns - self.start_time_ns) / 1_000_000

    def get_token_count(self) -> int:
        """Get total number of tokens in stream."""
        return len(self.tokens)

    def get_tokens_per_second(self) -> Optional[float]:
        """Get tokens per second (excluding TTFT)."""
        if (
            len(self.tokens) < 2
            or self.last_token_time_ns is None
            or self.first_token_time_ns is None
        ):
            return None
        duration_s = (
            self.last_token_time_ns - self.first_token_time_ns
        ) / 1_000_000_000
        if duration_s <= 0:
            return None
        return (len(self.tokens) - 1) / duration_s

    def get_inter_token_latencies_ms(self) -> List[float]:
        """Get inter-token latencies in milliseconds."""
        if len(self.tokens) < 2:
            return []
        itls = []
        for i in range(1, len(self.tokens)):
            itl_ns = self.tokens[i].timestamp_ns - self.tokens[i - 1].timestamp_ns
            itls.append(itl_ns / 1_000_000)
        return itls

    def calculate_jitter_ms(self) -> Optional[float]:
        """Calculate jitter (standard deviation of ITL) in milliseconds."""
        itls = self.get_inter_token_latencies_ms()
        if len(itls) < 2:
            return None
        return statistics.stdev(itls)

    def calculate_smoothness_score(self) -> Optional[float]:
        """
        Calculate smoothness score (0-100, higher is better).

        Based on coefficient of variation of ITL. Lower CV = higher smoothness.
        """
        itls = self.get_inter_token_latencies_ms()
        if len(itls) < 2:
            return None

        mean_itl = statistics.mean(itls)
        if mean_itl == 0:
            return 100.0

        stdev_itl = statistics.stdev(itls)
        cv = stdev_itl / mean_itl  # Coefficient of variation

        # Convert CV to 0-100 score (lower CV = higher score)
        # CV of 0 = 100, CV of 1 = 0, interpolate linearly
        smoothness = max(0.0, min(100.0, 100.0 * (1.0 - cv)))
        return smoothness

    def count_stalls(self) -> int:
        """Count number of stalls (ITL > 500ms)."""
        itls = self.get_inter_token_latencies_ms()
        return sum(1 for itl in itls if itl > 500.0)

    def calculate_throughput_variance(self) -> Optional[float]:
        """Calculate variance in throughput (tokens/sec) over time windows."""
        if len(self.tokens) < 10:
            return None

        # Calculate tokens/sec in 5-token windows
        window_size = 5
        throughputs = []

        for i in range(0, len(self.tokens) - window_size):
            window_start_ns = self.tokens[i].timestamp_ns
            window_end_ns = self.tokens[i + window_size - 1].timestamp_ns
            duration_s = (window_end_ns - window_start_ns) / 1_000_000_000

            if duration_s > 0:
                tps = window_size / duration_s
                throughputs.append(tps)

        if len(throughputs) < 2:
            return None

        return statistics.variance(throughputs)

    def get_token_size_distribution(self) -> Dict[str, float]:
        """Get statistics on token sizes (characters per token)."""
        if not self.tokens:
            return {}

        sizes = [len(t.token) for t in self.tokens]
        return {
            "mean": statistics.mean(sizes),
            "median": statistics.median(sizes),
            "min": min(sizes),
            "max": max(sizes),
            "stdev": statistics.stdev(sizes) if len(sizes) > 1 else 0.0,
        }

    def get_punctuation_ratio(self) -> float:
        """Get ratio of punctuation tokens to word tokens."""
        if not self.tokens:
            return 0.0

        punctuation = 0
        words = 0

        for token in self.tokens:
            text = token.token.strip()
            if not text:
                continue

            # Check if primarily punctuation
            punct_chars = sum(
                1 for c in text if c in ".,;:!?()[]{}<>\"'`~@#$%^&*-+=|/\\"
            )
            if punct_chars > len(text) / 2:
                punctuation += 1
            else:
                words += 1

        total = punctuation + words
        if total == 0:
            return 0.0

        return punctuation / total

    def calculate_network_overhead_percent(self) -> Optional[float]:
        """
        Calculate network overhead percentage.

        Overhead = (total_bytes_sent - actual_token_bytes) / total_bytes_sent * 100
        """
        if self.total_bytes_sent == 0:
            return None

        # Calculate actual content bytes
        actual_bytes = sum(len(t.token.encode("utf-8")) for t in self.tokens)
        overhead_bytes = self.total_bytes_sent - actual_bytes

        if overhead_bytes < 0:
            # This shouldn't happen, but handle gracefully
            return 0.0

        return (overhead_bytes / self.total_bytes_sent) * 100.0


@dataclass
class ClientBehavior:
    """Track client behavior patterns."""

    client_id: str  # Could be API key, IP, or other identifier
    streams: List[str] = field(default_factory=list)
    total_tokens_read: int = 0
    total_duration_ms: float = 0.0
    slow_stream_count: int = 0  # Streams with < 10 tokens/sec
    timeout_count: int = 0
    cancellation_count: int = 0
    reconnection_count: int = 0

    def get_average_read_rate_tps(self) -> float:
        """Get average token read rate in tokens per second."""
        if self.total_duration_ms == 0:
            return 0.0
        return self.total_tokens_read / (self.total_duration_ms / 1000.0)

    def is_slow_client(self) -> bool:
        """Determine if this is a slow client (< 10 tokens/sec on average)."""
        return self.get_average_read_rate_tps() < 10.0


class StreamingMetricsTracker:
    """
    Advanced streaming metrics tracker.

    Tracks detailed per-stream metrics including token timings, quality metrics,
    client behavior, and advanced analytics.
    """

    def __init__(
        self, max_active_streams: int = 10000, max_completed_streams: int = 1000
    ):
        """
        Initialize the streaming metrics tracker.

        Args:
            max_active_streams: Maximum number of active streams to track
            max_completed_streams: Maximum number of completed streams to keep in history
        """
        self.max_active_streams = max_active_streams
        self.max_completed_streams = max_completed_streams

        # Active streams (currently streaming)
        self._active_streams: Dict[str, StreamLifecycle] = {}

        # Completed streams (for historical analysis)
        self._completed_streams: deque[StreamLifecycle] = deque(
            maxlen=max_completed_streams
        )

        # Failed/cancelled streams
        self._failed_streams: deque[StreamLifecycle] = deque(
            maxlen=max_completed_streams
        )

        # Client behavior tracking
        self._clients: Dict[str, ClientBehavior] = {}

        # Thread safety
        self._lock = threading.Lock()

        # Correlation tracking (for analytics)
        self._correlation_data = {
            "prompt_length_vs_ttft": [],  # (prompt_tokens, ttft_ms)
            "temperature_vs_variance": [],  # (temperature, token_variance)
            "max_tokens_vs_duration": [],  # (max_tokens, duration_ms)
        }

        logger.info("StreamingMetricsTracker initialized")

    def start_stream(
        self,
        stream_id: str,
        model: str,
        prompt_tokens: int,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        client_id: Optional[str] = None,
    ) -> None:
        """
        Begin tracking a new stream.

        Args:
            stream_id: Unique identifier for the stream
            model: Model being used
            prompt_tokens: Number of tokens in the prompt
            temperature: Temperature parameter (optional)
            max_tokens: Max tokens parameter (optional)
            client_id: Client identifier (optional)
        """
        with self._lock:
            # Check if we're at capacity
            if len(self._active_streams) >= self.max_active_streams:
                logger.warning(
                    f"Max active streams ({self.max_active_streams}) reached. "
                    f"Dropping oldest active stream."
                )
                # Drop oldest active stream
                oldest_id = next(iter(self._active_streams))
                del self._active_streams[oldest_id]

            # Create new stream lifecycle
            stream = StreamLifecycle(
                stream_id=stream_id,
                model=model,
                prompt_tokens=prompt_tokens,
                start_time_ns=time.time_ns(),
                temperature=temperature,
                max_tokens=max_tokens,
            )

            self._active_streams[stream_id] = stream

            # Track client
            if client_id:
                if client_id not in self._clients:
                    self._clients[client_id] = ClientBehavior(client_id=client_id)
                self._clients[client_id].streams.append(stream_id)

    def record_token(
        self,
        stream_id: str,
        token: str,
        timestamp_ns: Optional[int] = None,
        chunk_size_bytes: Optional[int] = None,
    ) -> None:
        """
        Record a streamed token.

        Args:
            stream_id: Stream identifier
            token: The token text
            timestamp_ns: Token timestamp in nanoseconds (defaults to current time)
            chunk_size_bytes: Size of network chunk in bytes (optional)
        """
        with self._lock:
            if stream_id not in self._active_streams:
                logger.warning(f"Stream {stream_id} not found in active streams")
                return

            stream = self._active_streams[stream_id]

            # Use current time if not provided
            if timestamp_ns is None:
                timestamp_ns = time.time_ns()

            # Record first token time
            if stream.first_token_time_ns is None:
                stream.first_token_time_ns = timestamp_ns

            # Update last token time
            stream.last_token_time_ns = timestamp_ns

            # Create token timing
            timing = TokenTiming(
                token=token,
                timestamp_ns=timestamp_ns,
                chunk_size_bytes=chunk_size_bytes or len(token.encode("utf-8")),
                sequence_number=len(stream.tokens),
            )

            stream.tokens.append(timing)

            # Check for stalls (ITL > 500ms)
            if len(stream.tokens) > 1:
                itl_ns = timestamp_ns - stream.tokens[-2].timestamp_ns
                itl_ms = itl_ns / 1_000_000
                if itl_ms > 500.0:
                    stream.stall_events += 1

    def record_chunk_sent(self, stream_id: str, chunk_size_bytes: int) -> None:
        """
        Record a network chunk sent.

        Args:
            stream_id: Stream identifier
            chunk_size_bytes: Size of the chunk in bytes
        """
        with self._lock:
            if stream_id not in self._active_streams:
                return

            stream = self._active_streams[stream_id]
            stream.chunks_sent += 1
            stream.total_bytes_sent += chunk_size_bytes
            stream.chunk_sizes.append(chunk_size_bytes)

    def record_backpressure(self, stream_id: str) -> None:
        """
        Record a backpressure event (client not reading fast enough).

        Args:
            stream_id: Stream identifier
        """
        with self._lock:
            if stream_id not in self._active_streams:
                return

            stream = self._active_streams[stream_id]
            stream.backpressure_events += 1

    def complete_stream(
        self,
        stream_id: str,
        finish_reason: str,
        client_id: Optional[str] = None,
    ) -> None:
        """
        Mark a stream as completed.

        Args:
            stream_id: Stream identifier
            finish_reason: Reason for completion (stop, length, etc.)
            client_id: Client identifier (optional)
        """
        with self._lock:
            if stream_id not in self._active_streams:
                logger.warning(f"Stream {stream_id} not found in active streams")
                return

            stream = self._active_streams[stream_id]
            stream.completion_time_ns = time.time_ns()
            stream.finish_reason = finish_reason

            # Record correlation data
            ttft = stream.get_ttft_ms()
            if ttft is not None:
                self._correlation_data["prompt_length_vs_ttft"].append(
                    (stream.prompt_tokens, ttft)
                )

            if stream.temperature is not None:
                variance = stream.calculate_throughput_variance()
                if variance is not None:
                    self._correlation_data["temperature_vs_variance"].append(
                        (stream.temperature, variance)
                    )

            if stream.max_tokens is not None:
                duration = stream.get_total_duration_ms()
                if duration is not None:
                    self._correlation_data["max_tokens_vs_duration"].append(
                        (stream.max_tokens, duration)
                    )

            # Update client behavior
            if client_id:
                if client_id not in self._clients:
                    self._clients[client_id] = ClientBehavior(client_id=client_id)
                client = self._clients[client_id]
                client.total_tokens_read += stream.get_token_count()
                duration_ms = stream.get_total_duration_ms()
                if duration_ms is not None:
                    client.total_duration_ms += duration_ms

                tps = stream.get_tokens_per_second()
                if tps is not None and tps < 10.0:
                    client.slow_stream_count += 1

            # Move to completed streams
            self._completed_streams.append(stream)
            del self._active_streams[stream_id]

    def cancel_stream(
        self,
        stream_id: str,
        error_message: Optional[str] = None,
        client_id: Optional[str] = None,
    ) -> None:
        """
        Mark a stream as cancelled or failed.

        Args:
            stream_id: Stream identifier
            error_message: Optional error message
            client_id: Client identifier (optional)
        """
        with self._lock:
            if stream_id not in self._active_streams:
                return

            stream = self._active_streams[stream_id]
            stream.completion_time_ns = time.time_ns()
            stream.cancelled = True
            stream.cancellation_point = len(stream.tokens)
            stream.error_message = error_message

            # Update client behavior
            if client_id:
                if client_id not in self._clients:
                    self._clients[client_id] = ClientBehavior(client_id=client_id)
                client = self._clients[client_id]
                client.cancellation_count += 1

            # Move to failed streams
            self._failed_streams.append(stream)
            del self._active_streams[stream_id]

    def record_timeout(self, client_id: str) -> None:
        """Record a timeout event for a client."""
        with self._lock:
            if client_id not in self._clients:
                self._clients[client_id] = ClientBehavior(client_id=client_id)
            self._clients[client_id].timeout_count += 1

    def record_reconnection(self, client_id: str) -> None:
        """Record a reconnection event for a client."""
        with self._lock:
            if client_id not in self._clients:
                self._clients[client_id] = ClientBehavior(client_id=client_id)
            self._clients[client_id].reconnection_count += 1

    def get_stream_stats(self, stream_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed statistics for a specific stream.

        Args:
            stream_id: Stream identifier

        Returns:
            Dictionary of stream statistics or None if not found
        """
        with self._lock:
            # Check active streams
            if stream_id in self._active_streams:
                stream = self._active_streams[stream_id]
                return self._stream_to_dict(stream, status="active")

            # Check completed streams
            for stream in self._completed_streams:
                if stream.stream_id == stream_id:
                    return self._stream_to_dict(stream, status="completed")

            # Check failed streams
            for stream in self._failed_streams:
                if stream.stream_id == stream_id:
                    return self._stream_to_dict(stream, status="failed")

            return None

    def _stream_to_dict(self, stream: StreamLifecycle, status: str) -> Dict[str, Any]:
        """Convert a StreamLifecycle to a dictionary."""
        itls = stream.get_inter_token_latencies_ms()

        return {
            "stream_id": stream.stream_id,
            "status": status,
            "model": stream.model,
            "prompt_tokens": stream.prompt_tokens,
            "token_count": stream.get_token_count(),
            "ttft_ms": stream.get_ttft_ms(),
            "duration_ms": stream.get_total_duration_ms(),
            "tokens_per_second": stream.get_tokens_per_second(),
            "finish_reason": stream.finish_reason,
            "cancelled": stream.cancelled,
            "cancellation_point": stream.cancellation_point,
            "error_message": stream.error_message,
            "chunks_sent": stream.chunks_sent,
            "total_bytes_sent": stream.total_bytes_sent,
            "backpressure_events": stream.backpressure_events,
            "stall_events": stream.stall_events,
            "jitter_ms": stream.calculate_jitter_ms(),
            "smoothness_score": stream.calculate_smoothness_score(),
            "throughput_variance": stream.calculate_throughput_variance(),
            "network_overhead_percent": stream.calculate_network_overhead_percent(),
            "token_size_distribution": stream.get_token_size_distribution(),
            "punctuation_ratio": stream.get_punctuation_ratio(),
            "inter_token_latencies_ms": {
                "mean": statistics.mean(itls) if itls else None,
                "median": statistics.median(itls) if itls else None,
                "min": min(itls) if itls else None,
                "max": max(itls) if itls else None,
                "p90": np.percentile(itls, 90) if itls else None,
                "p99": np.percentile(itls, 99) if itls else None,
            },
            "temperature": stream.temperature,
            "max_tokens": stream.max_tokens,
        }

    def get_streaming_quality_report(self) -> Dict[str, Any]:
        """
        Get comprehensive streaming quality report across all streams.

        Returns:
            Dictionary containing quality metrics and analytics
        """
        with self._lock:
            # Collect all completed streams
            all_streams = list(self._completed_streams) + list(self._failed_streams)

            if not all_streams:
                return {
                    "total_streams": 0,
                    "active_streams": len(self._active_streams),
                    "message": "No completed streams yet",
                }

            # Calculate aggregate metrics
            ttfts = [
                s.get_ttft_ms() for s in all_streams if s.get_ttft_ms() is not None
            ]
            tpss = [
                s.get_tokens_per_second()
                for s in all_streams
                if s.get_tokens_per_second() is not None
            ]
            jitters = [
                s.calculate_jitter_ms()
                for s in all_streams
                if s.calculate_jitter_ms() is not None
            ]
            smoothness = [
                s.calculate_smoothness_score()
                for s in all_streams
                if s.calculate_smoothness_score() is not None
            ]
            stalls = [s.count_stalls() for s in all_streams]

            # Quality metrics
            quality_metrics = {
                "ttft_ms": self._calculate_percentiles(ttfts) if ttfts else {},
                "tokens_per_second": self._calculate_percentiles(tpss) if tpss else {},
                "jitter_ms": self._calculate_percentiles(jitters) if jitters else {},
                "smoothness_score": (
                    self._calculate_percentiles(smoothness) if smoothness else {}
                ),
                "stall_count": {
                    "mean": statistics.mean(stalls) if stalls else 0,
                    "median": statistics.median(stalls) if stalls else 0,
                    "max": max(stalls) if stalls else 0,
                    "streams_with_stalls": sum(1 for s in stalls if s > 0),
                },
            }

            # Token-level metrics
            all_tokens = []
            for stream in all_streams:
                all_tokens.extend(stream.tokens)

            token_sizes = [len(t.token) for t in all_tokens]

            token_metrics = {
                "total_tokens": len(all_tokens),
                "token_size_distribution": (
                    self._calculate_percentiles(token_sizes) if token_sizes else {}
                ),
                "punctuation_ratio": {
                    "mean": (
                        statistics.mean(
                            [s.get_punctuation_ratio() for s in all_streams]
                        )
                        if all_streams
                        else 0
                    ),
                },
            }

            # Network metrics
            network_overheads = [
                s.calculate_network_overhead_percent()
                for s in all_streams
                if s.calculate_network_overhead_percent() is not None
            ]

            network_metrics = {
                "total_bytes_sent": sum(s.total_bytes_sent for s in all_streams),
                "total_chunks_sent": sum(s.chunks_sent for s in all_streams),
                "network_overhead_percent": (
                    self._calculate_percentiles(network_overheads)
                    if network_overheads
                    else {}
                ),
            }

            # Client behavior summary
            slow_clients = [c for c in self._clients.values() if c.is_slow_client()]

            client_metrics = {
                "total_clients": len(self._clients),
                "slow_clients": len(slow_clients),
                "total_timeouts": sum(c.timeout_count for c in self._clients.values()),
                "total_cancellations": sum(
                    c.cancellation_count for c in self._clients.values()
                ),
                "total_reconnections": sum(
                    c.reconnection_count for c in self._clients.values()
                ),
            }

            # Correlation analytics
            correlations = self._calculate_correlations()

            return {
                "summary": {
                    "total_streams": len(all_streams),
                    "completed_streams": len(self._completed_streams),
                    "failed_streams": len(self._failed_streams),
                    "active_streams": len(self._active_streams),
                    "success_rate": (
                        len(self._completed_streams) / len(all_streams) * 100
                        if all_streams
                        else 0
                    ),
                },
                "quality_metrics": quality_metrics,
                "token_metrics": token_metrics,
                "network_metrics": network_metrics,
                "client_metrics": client_metrics,
                "correlations": correlations,
            }

    def _calculate_percentiles(self, values: List[float]) -> Dict[str, float]:
        """Calculate percentiles for a list of values."""
        if not values:
            return {}

        values_array = np.array(values)
        return {
            "mean": float(np.mean(values_array)),
            "median": float(np.median(values_array)),
            "min": float(np.min(values_array)),
            "max": float(np.max(values_array)),
            "p50": float(np.percentile(values_array, 50)),
            "p90": float(np.percentile(values_array, 90)),
            "p95": float(np.percentile(values_array, 95)),
            "p99": float(np.percentile(values_array, 99)),
            "stdev": float(np.std(values_array)),
        }

    def _calculate_correlations(self) -> Dict[str, Any]:
        """Calculate correlation coefficients for tracked relationships."""
        correlations = {}

        # Prompt length vs TTFT
        if len(self._correlation_data["prompt_length_vs_ttft"]) > 1:
            data = np.array(self._correlation_data["prompt_length_vs_ttft"])
            if data.shape[0] > 1:
                corr = np.corrcoef(data[:, 0], data[:, 1])[0, 1]
                correlations["prompt_length_vs_ttft"] = {
                    "correlation": float(corr),
                    "sample_size": len(data),
                    "description": "Correlation between prompt length and time to first token",
                }

        # Temperature vs variance
        if len(self._correlation_data["temperature_vs_variance"]) > 1:
            data = np.array(self._correlation_data["temperature_vs_variance"])
            if data.shape[0] > 1:
                corr = np.corrcoef(data[:, 0], data[:, 1])[0, 1]
                correlations["temperature_vs_variance"] = {
                    "correlation": float(corr),
                    "sample_size": len(data),
                    "description": "Correlation between temperature and throughput variance",
                }

        # Max tokens vs duration
        if len(self._correlation_data["max_tokens_vs_duration"]) > 1:
            data = np.array(self._correlation_data["max_tokens_vs_duration"])
            if data.shape[0] > 1:
                corr = np.corrcoef(data[:, 0], data[:, 1])[0, 1]
                correlations["max_tokens_vs_duration"] = {
                    "correlation": float(corr),
                    "sample_size": len(data),
                    "description": "Correlation between max_tokens parameter and stream duration",
                }

        return correlations

    def get_client_stats(self, client_id: str) -> Optional[Dict[str, Any]]:
        """
        Get statistics for a specific client.

        Args:
            client_id: Client identifier

        Returns:
            Dictionary of client statistics or None if not found
        """
        with self._lock:
            if client_id not in self._clients:
                return None

            client = self._clients[client_id]

            return {
                "client_id": client_id,
                "total_streams": len(client.streams),
                "total_tokens_read": client.total_tokens_read,
                "average_read_rate_tps": client.get_average_read_rate_tps(),
                "slow_stream_count": client.slow_stream_count,
                "timeout_count": client.timeout_count,
                "cancellation_count": client.cancellation_count,
                "reconnection_count": client.reconnection_count,
                "is_slow_client": client.is_slow_client(),
            }

    def get_all_clients(self) -> List[Dict[str, Any]]:
        """Get statistics for all tracked clients."""
        with self._lock:
            # Build stats inline to avoid nested lock acquisition
            results = []
            for client_id, client in self._clients.items():
                results.append(
                    {
                        "client_id": client_id,
                        "total_streams": len(client.streams),
                        "total_tokens_read": client.total_tokens_read,
                        "average_read_rate_tps": client.get_average_read_rate_tps(),
                        "slow_stream_count": client.slow_stream_count,
                        "timeout_count": client.timeout_count,
                        "cancellation_count": client.cancellation_count,
                        "reconnection_count": client.reconnection_count,
                        "is_slow_client": client.is_slow_client(),
                    }
                )
            return results

    def get_active_stream_count(self) -> int:
        """Get count of currently active streams."""
        with self._lock:
            return len(self._active_streams)

    def get_completed_stream_count(self) -> int:
        """Get count of completed streams in history."""
        with self._lock:
            return len(self._completed_streams)

    def get_failed_stream_count(self) -> int:
        """Get count of failed streams in history."""
        with self._lock:
            return len(self._failed_streams)

    def clear_history(self) -> None:
        """Clear completed and failed stream history."""
        with self._lock:
            self._completed_streams.clear()
            self._failed_streams.clear()
            self._correlation_data = {
                "prompt_length_vs_ttft": [],
                "temperature_vs_variance": [],
                "max_tokens_vs_duration": [],
            }
            logger.info("Cleared streaming metrics history")

    def reset(self) -> None:
        """Reset all metrics (including active streams)."""
        with self._lock:
            self._active_streams.clear()
            self._completed_streams.clear()
            self._failed_streams.clear()
            self._clients.clear()
            self._correlation_data = {
                "prompt_length_vs_ttft": [],
                "temperature_vs_variance": [],
                "max_tokens_vs_duration": [],
            }
            logger.info("Reset all streaming metrics")
