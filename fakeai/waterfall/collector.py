"""
Request Timing Data Collector for Waterfall Charts.

Captures detailed timing information for each request:
- Request start time
- Time to first token (TTFT)
- Token generation times
- Request completion time
- Model and endpoint information
"""

#  SPDX-License-Identifier: Apache-2.0

import threading
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any


@dataclass
class TokenTiming:
    """Timing information for a single token."""

    token_index: int
    timestamp_ms: float  # Relative to request start
    token_text: str | None = None
    latency_ms: float | None = None  # Time since previous token


@dataclass
class RequestTiming:
    """Complete timing information for a single request."""

    request_id: str
    endpoint: str
    model: str
    start_time: float  # Absolute timestamp
    ttft_ms: float | None = None  # Time to first token
    end_time: float | None = None  # Absolute timestamp
    total_duration_ms: float | None = None
    is_streaming: bool = False
    input_tokens: int = 0
    output_tokens: int = 0
    tokens: list[TokenTiming] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_complete(self) -> bool:
        """Check if request is complete."""
        return self.end_time is not None

    @property
    def duration_ms(self) -> float:
        """Get request duration in milliseconds."""
        if self.total_duration_ms is not None:
            return self.total_duration_ms
        if self.end_time is not None:
            return (self.end_time - self.start_time) * 1000
        return (time.time() - self.start_time) * 1000


class RequestTimingCollector:
    """
    Collects and stores request timing data for waterfall visualization.

    Thread-safe singleton that captures:
    - Request start/end times
    - TTFT (Time To First Token) for streaming requests
    - Individual token generation times
    - Request metadata (model, endpoint, tokens)

    Features:
    - Automatic memory management (configurable max requests)
    - Thread-safe operations
    - Integration with FakeAI event bus
    - Zero-overhead when not in use
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, max_requests: int = 1000):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, max_requests: int = 1000):
        """Initialize the timing collector."""
        if self._initialized:
            return

        with self._lock:
            if self._initialized:
                return

            self.max_requests = max_requests
            self._requests: deque[RequestTiming] = deque(maxlen=max_requests)
            self._active_requests: dict[str, RequestTiming] = {}
            self._data_lock = threading.RLock()
            self._initialized = True

    def start_request(
        self,
        request_id: str,
        endpoint: str,
        model: str,
        is_streaming: bool = False,
        input_tokens: int = 0,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Record request start."""
        with self._data_lock:
            timing = RequestTiming(
                request_id=request_id,
                endpoint=endpoint,
                model=model,
                start_time=time.time(),
                is_streaming=is_streaming,
                input_tokens=input_tokens,
                metadata=metadata or {},
            )
            self._active_requests[request_id] = timing

    def record_first_token(
        self, request_id: str, token_text: str | None = None
    ) -> None:
        """Record time to first token."""
        with self._data_lock:
            if request_id not in self._active_requests:
                return

            request = self._active_requests[request_id]
            current_time = time.time()
            ttft_ms = (current_time - request.start_time) * 1000
            request.ttft_ms = ttft_ms

            # Record first token
            request.tokens.append(
                TokenTiming(
                    token_index=0,
                    timestamp_ms=ttft_ms,
                    token_text=token_text,
                    latency_ms=ttft_ms,
                )
            )

    def record_token(
        self, request_id: str, token_index: int, token_text: str | None = None
    ) -> None:
        """Record token generation time."""
        with self._data_lock:
            if request_id not in self._active_requests:
                return

            request = self._active_requests[request_id]
            current_time = time.time()
            timestamp_ms = (current_time - request.start_time) * 1000

            # Calculate latency since previous token
            latency_ms = None
            if request.tokens:
                prev_timestamp = request.tokens[-1].timestamp_ms
                latency_ms = timestamp_ms - prev_timestamp

            request.tokens.append(
                TokenTiming(
                    token_index=token_index,
                    timestamp_ms=timestamp_ms,
                    token_text=token_text,
                    latency_ms=latency_ms,
                )
            )

    def complete_request(
        self, request_id: str, output_tokens: int = 0, success: bool = True
    ) -> None:
        """Record request completion."""
        with self._data_lock:
            if request_id not in self._active_requests:
                return

            request = self._active_requests[request_id]
            request.end_time = time.time()
            request.total_duration_ms = (request.end_time - request.start_time) * 1000
            request.output_tokens = output_tokens
            request.metadata["success"] = success

            # Move to completed requests
            self._requests.append(request)
            del self._active_requests[request_id]

    def get_recent_requests(
        self, limit: int = 100, endpoint: str | None = None, model: str | None = None
    ) -> list[RequestTiming]:
        """Get recent completed requests with optional filtering."""
        with self._data_lock:
            requests = list(self._requests)

            # Apply filters
            if endpoint:
                requests = [r for r in requests if r.endpoint == endpoint]
            if model:
                requests = [r for r in requests if r.model == model]

            # Return most recent first
            requests.reverse()
            return requests[:limit]

    def get_active_requests(self) -> list[RequestTiming]:
        """Get currently active (incomplete) requests."""
        with self._data_lock:
            return list(self._active_requests.values())

    def get_request(self, request_id: str) -> RequestTiming | None:
        """Get specific request by ID (active or completed)."""
        with self._data_lock:
            if request_id in self._active_requests:
                return self._active_requests[request_id]

            for request in reversed(self._requests):
                if request.request_id == request_id:
                    return request

            return None

    def get_stats(self) -> dict[str, Any]:
        """Get collector statistics."""
        with self._data_lock:
            return {
                "total_completed": len(self._requests),
                "active_requests": len(self._active_requests),
                "max_capacity": self.max_requests,
                "utilization_percent": (len(self._requests) / self.max_requests) * 100,
            }

    def clear(self) -> None:
        """Clear all collected data."""
        with self._data_lock:
            self._requests.clear()
            self._active_requests.clear()


# Singleton instance
_collector: RequestTimingCollector | None = None
_collector_lock = threading.Lock()


def get_timing_collector(max_requests: int = 1000) -> RequestTimingCollector:
    """Get the singleton timing collector instance."""
    global _collector
    if _collector is None:
        with _collector_lock:
            if _collector is None:
                _collector = RequestTimingCollector(max_requests=max_requests)
    return _collector
