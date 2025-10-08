"""
NVIDIA AI-Dynamo Enhanced Metrics.

Comprehensive LLM inference metrics including latency breakdown,
throughput measurements, queue statistics, batch metrics, and
disaggregated serving metrics with worker pool tracking.
"""

import random
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Any

from fakeai.queue_depth_tracker import get_queue_tracker
from fakeai.worker_pool import get_worker_pool


@dataclass
class RequestMetrics:
    """Complete metrics for a single request."""

    request_id: str
    model: str
    endpoint: str

    # Timestamps (all in seconds since epoch)
    arrival_time: float = 0.0
    queue_start_time: float = 0.0
    prefill_start_time: float = 0.0
    first_token_time: float = 0.0
    decode_start_time: float = 0.0
    completion_time: float = 0.0

    # Token counts
    input_tokens: int = 0
    output_tokens: int = 0
    cached_tokens: int = 0

    # Phase durations (calculated)
    queue_time_ms: float = 0.0
    prefill_time_ms: float = 0.0
    decode_time_ms: float = 0.0
    total_time_ms: float = 0.0

    # KV cache metrics
    kv_cache_hit: bool = False
    kv_cache_blocks_matched: int = 0
    kv_cache_overlap_score: float = 0.0

    # Worker assignment
    worker_id: str = ""
    routing_cost: float = 0.0

    # Status
    success: bool = True
    finish_reason: str = "stop"

    def calculate_derived_metrics(self):
        """Calculate derived timing metrics."""
        if self.queue_start_time > 0 and self.prefill_start_time > 0:
            self.queue_time_ms = (
                self.prefill_start_time - self.queue_start_time
            ) * 1000

        if self.prefill_start_time > 0 and self.first_token_time > 0:
            self.prefill_time_ms = (
                self.first_token_time - self.prefill_start_time
            ) * 1000

        if self.decode_start_time > 0 and self.completion_time > 0:
            self.decode_time_ms = (
                self.completion_time - self.decode_start_time) * 1000

        if self.arrival_time > 0 and self.completion_time > 0:
            self.total_time_ms = (
                self.completion_time - self.arrival_time) * 1000

    @property
    def ttft_ms(self) -> float:
        """Time to first token in milliseconds."""
        if self.arrival_time > 0 and self.first_token_time > 0:
            return (self.first_token_time - self.arrival_time) * 1000
        return 0.0

    @property
    def tpot_ms(self) -> float:
        """Time per output token in milliseconds."""
        if self.output_tokens > 1 and self.decode_time_ms > 0:
            return self.decode_time_ms / (self.output_tokens - 1)
        return 0.0

    @property
    def itl_ms(self) -> float:
        """Inter-token latency (same as TPOT)."""
        return self.tpot_ms


class DynamoMetricsCollector:
    """
    Collects comprehensive LLM inference metrics in AI-Dynamo style.

    Tracks request lifecycle, latency breakdown, throughput, queue metrics,
    and disaggregation statistics.
    """

    def __init__(self, window_size: int = 300, num_workers: int = 4):
        """
        Initialize metrics collector.

        Args:
            window_size: Time window for metrics in seconds (default: 5 minutes)
            num_workers: Number of workers to track (default: 4)
        """
        self.window_size = window_size
        self.num_workers = num_workers

        # Initialize worker pool and queue tracker
        self.worker_pool = get_worker_pool(num_workers=num_workers)
        self.queue_tracker = get_queue_tracker()

        # Request tracking
        self._completed_requests: deque[RequestMetrics] = deque(maxlen=10000)
        self._active_requests: dict[str, RequestMetrics] = {}

        # Latency breakdown tracking (last 100 requests for dashboard
        # visualization)
        self._latency_breakdowns: deque[dict[str, Any]] = deque(maxlen=100)

        # Lifecycle tracking (last 100 requests for timeline visualization)
        self._request_lifecycles: deque[RequestMetrics] = deque(maxlen=100)

        # Histogram buckets for latencies (in seconds)
        self.ttft_buckets = [0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0, 10.0]
        self.itl_buckets = [0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1.0]
        self.total_latency_buckets = [
            0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]

        # Counters
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0

        # Per-model statistics (enhanced for dashboard)
        self.model_stats = defaultdict(
            lambda: {
                "requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                # For RPS calculation
                "request_timestamps": deque(maxlen=1000),
                # For TPS calculation (timestamp, token_count)
                "token_timestamps": deque(maxlen=1000),
                "input_tokens": 0,
                "output_tokens": 0,
                "ttft_sum": 0.0,
                "itl_sum": 0.0,
                "cache_hits": 0,
                "cache_attempts": 0,
            }
        )

        # Token statistics (cumulative counters)
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cached_tokens = 0

        # Queue tracking
        self.current_queue_depth = 0
        self.max_queue_depth = 0
        self.queue_depth_history: deque[tuple[float, int]] = deque(maxlen=1000)

        # Batch tracking
        self.current_batch_size = 0
        self.avg_batch_size = 0.0
        self.batch_size_history: deque[int] = deque(maxlen=1000)

        # Disaggregation metrics
        self.prefill_requests = 0
        self.decode_requests = 0
        self.kv_transfer_bytes = 0
        self.kv_transfer_time_ms = 0.0

        self._lock = threading.Lock()

    def start_request(
        self, request_id: str, model: str, endpoint: str, input_tokens: int
    ) -> RequestMetrics:
        """
        Start tracking a new request.

        Returns:
            RequestMetrics object for this request
        """
        with self._lock:
            # Assign request to a worker (or use fallback if disabled)
            if self.worker_pool:
                worker_id = self.worker_pool.assign_request(request_id)
            else:
                worker_id = f"worker-{random.randint(0, self.num_workers - 1)}"

            request = RequestMetrics(
                request_id=request_id,
                model=model,
                endpoint=endpoint,
                arrival_time=time.time(),
                queue_start_time=time.time(),
                input_tokens=input_tokens,
                worker_id=worker_id,
            )

            self._active_requests[request_id] = request
            self.total_requests += 1

            return request

    def record_prefill_start(self, request_id: str):
        """Record when prefill phase begins."""
        if request_id in self._active_requests:
            self._active_requests[request_id].prefill_start_time = time.time()
            self.prefill_requests += 1

    def record_first_token(self, request_id: str):
        """Record when first token is generated."""
        if request_id in self._active_requests:
            self._active_requests[request_id].first_token_time = time.time()
            self._active_requests[request_id].decode_start_time = time.time()

    def record_decode_start(self, request_id: str):
        """Record when decode phase starts (typically same as first token)."""
        if request_id in self._active_requests:
            # Only set if not already set (avoid overwriting first_token
            # timing)
            if self._active_requests[request_id].decode_start_time == 0.0:
                self._active_requests[request_id].decode_start_time = time.time(
                )

    def complete_request(
        self,
        request_id: str,
        output_tokens: int,
        cached_tokens: int = 0,
        kv_cache_hit: bool = False,
        worker_id: str = "",
        success: bool = True,
        finish_reason: str = "stop",
    ):
        """Mark request as completed and calculate final metrics."""
        with self._lock:
            if request_id not in self._active_requests:
                return

            request = self._active_requests.pop(request_id)
            request.completion_time = time.time()
            request.output_tokens = output_tokens
            request.cached_tokens = cached_tokens
            request.kv_cache_hit = kv_cache_hit

            # Use worker ID from request (assigned at start) if not provided
            if not worker_id and request.worker_id:
                worker_id = request.worker_id
            elif not worker_id:
                # Fallback: assign to random worker
                worker_id = f"worker-{random.randint(0, self.num_workers - 1)}"

            request.worker_id = worker_id

            # Calculate realistic routing cost (0.1-2ms)
            request.routing_cost = random.uniform(0.1, 2.0)

            request.success = success
            request.finish_reason = finish_reason

            # Calculate derived metrics
            request.calculate_derived_metrics()

            # Update worker pool statistics (if enabled)
            if self.worker_pool:
                duration_ms = request.total_time_ms if request.total_time_ms > 0 else 50.0
                self.worker_pool.complete_request(
                    worker_id, duration_ms, success)

            # Store completed request
            self._completed_requests.append(request)

            # Store in lifecycle tracking (last 100 for timeline visualization)
            self._request_lifecycles.append(request)

            # Add to latency breakdown tracking (last 100 requests)
            self._add_latency_breakdown(request)

            # Update counters
            if success:
                self.successful_requests += 1
            else:
                self.failed_requests += 1

            # Update model stats (enhanced tracking for dashboard)
            completion_ts = time.time()
            model_data = self.model_stats[request.model]

            model_data["requests"] += 1
            model_data["request_timestamps"].append(completion_ts)

            # Track success/failure
            if success:
                model_data["successful_requests"] += 1
            else:
                model_data["failed_requests"] += 1

            # Track tokens separately
            model_data["input_tokens"] += request.input_tokens
            model_data["output_tokens"] += output_tokens
            model_data["token_timestamps"].append(
                (completion_ts, request.input_tokens + output_tokens)
            )

            # Track latency sums
            model_data["ttft_sum"] += request.ttft_ms
            model_data["itl_sum"] += request.itl_ms

            # Track cache performance
            model_data["cache_attempts"] += 1
            if kv_cache_hit:
                model_data["cache_hits"] += 1

            # Update token statistics (cumulative counters)
            self.total_input_tokens += request.input_tokens
            self.total_output_tokens += output_tokens
            self.total_cached_tokens += cached_tokens

            self.decode_requests += 1

    def _add_latency_breakdown(self, request: RequestMetrics):
        """
        Add latency breakdown entry for dashboard visualization.

        Creates a breakdown entry with realistic phase timings:
        - Queue time: 1-10ms
        - Prefill time: 5-20ms
        - Decode time: ~10ms per output token
        """
        # Use actual calculated values if available, otherwise generate
        # realistic ones
        queue_time = request.queue_time_ms
        prefill_time = request.prefill_time_ms
        decode_time = request.decode_time_ms

        # If times weren't properly set, generate realistic values
        if queue_time == 0.0:
            queue_time = random.uniform(1.0, 10.0)
        if prefill_time == 0.0:
            prefill_time = random.uniform(5.0, 20.0)
        if decode_time == 0.0 and request.output_tokens > 0:
            # Realistic decode time: ~10ms per token with some variance
            decode_time = request.output_tokens * random.uniform(8.0, 12.0)

        total_time = queue_time + prefill_time + decode_time

        breakdown = {
            "timestamp": int(request.completion_time),
            "queue_time_ms": round(queue_time, 2),
            "prefill_time_ms": round(prefill_time, 2),
            "decode_time_ms": round(decode_time, 2),
            "total_time_ms": round(total_time, 2),
            "request_id": request.request_id,
        }

        self._latency_breakdowns.append(breakdown)

    def record_queue_depth(self, depth: int):
        """Record current queue depth."""
        with self._lock:
            self.current_queue_depth = depth
            self.max_queue_depth = max(self.max_queue_depth, depth)
            self.queue_depth_history.append((time.time(), depth))

    def record_batch_size(self, size: int):
        """Record current batch size."""
        with self._lock:
            self.current_batch_size = size
            self.batch_size_history.append(size)

            # Update running average
            if len(self.batch_size_history) > 0:
                self.avg_batch_size = sum(self.batch_size_history) / len(
                    self.batch_size_history
                )

    def get_recent_requests(self, seconds: int = 60) -> list[RequestMetrics]:
        """Get requests completed in last N seconds."""
        cutoff_time = time.time() - seconds
        with self._lock:
            return [
                r for r in self._completed_requests if r.completion_time >= cutoff_time]

    def calculate_percentile(
            self,
            values: list[float],
            percentile: float) -> float:
        """Calculate percentile from sorted values."""
        if not values:
            return 0.0
        sorted_vals = sorted(values)
        idx = int(len(sorted_vals) * (percentile / 100.0))
        idx = min(idx, len(sorted_vals) - 1)
        return sorted_vals[idx]

    def get_latency_stats(self, window_seconds: int = 60) -> dict[str, Any]:
        """Get latency statistics for recent window with min/max and p95."""
        recent = self.get_recent_requests(window_seconds)

        if not recent:
            return {
                "ttft": {"avg": 0.0, "min": 0.0, "max": 0.0, "p50": 0.0, "p90": 0.0, "p95": 0.0, "p99": 0.0},
                "itl": {"avg": 0.0, "min": 0.0, "max": 0.0, "p50": 0.0, "p90": 0.0, "p95": 0.0, "p99": 0.0},
                "total": {"avg": 0.0, "min": 0.0, "max": 0.0, "p50": 0.0, "p90": 0.0, "p95": 0.0, "p99": 0.0},
                "queue": {"avg": 0.0, "min": 0.0, "max": 0.0, "p50": 0.0, "p90": 0.0, "p95": 0.0, "p99": 0.0},
                "prefill": {"avg": 0.0, "min": 0.0, "max": 0.0, "p50": 0.0, "p90": 0.0, "p95": 0.0, "p99": 0.0},
                "decode": {"avg": 0.0, "min": 0.0, "max": 0.0, "p50": 0.0, "p90": 0.0, "p95": 0.0, "p99": 0.0},
            }

        # Extract values
        ttft_values = [r.ttft_ms for r in recent if r.ttft_ms > 0]
        itl_values = [r.itl_ms for r in recent if r.itl_ms > 0]
        total_values = [r.total_time_ms for r in recent if r.total_time_ms > 0]
        queue_values = [r.queue_time_ms for r in recent if r.queue_time_ms > 0]
        prefill_values = [
            r.prefill_time_ms for r in recent if r.prefill_time_ms > 0]
        decode_values = [
            r.decode_time_ms for r in recent if r.decode_time_ms > 0]

        # Calculate stats with min, max, and p95
        return {
            "ttft": {
                "avg": sum(ttft_values) / len(ttft_values) if ttft_values else 0.0,
                "min": min(ttft_values) if ttft_values else 0.0,
                "max": max(ttft_values) if ttft_values else 0.0,
                "p50": self.calculate_percentile(ttft_values, 50),
                "p90": self.calculate_percentile(ttft_values, 90),
                "p95": self.calculate_percentile(ttft_values, 95),
                "p99": self.calculate_percentile(ttft_values, 99),
            },
            "itl": {
                "avg": sum(itl_values) / len(itl_values) if itl_values else 0.0,
                "min": min(itl_values) if itl_values else 0.0,
                "max": max(itl_values) if itl_values else 0.0,
                "p50": self.calculate_percentile(itl_values, 50),
                "p90": self.calculate_percentile(itl_values, 90),
                "p95": self.calculate_percentile(itl_values, 95),
                "p99": self.calculate_percentile(itl_values, 99),
            },
            "total": {
                "avg": sum(total_values) / len(total_values) if total_values else 0.0,
                "min": min(total_values) if total_values else 0.0,
                "max": max(total_values) if total_values else 0.0,
                "p50": self.calculate_percentile(total_values, 50),
                "p90": self.calculate_percentile(total_values, 90),
                "p95": self.calculate_percentile(total_values, 95),
                "p99": self.calculate_percentile(total_values, 99),
            },
            "queue": {
                "avg": sum(queue_values) / len(queue_values) if queue_values else 0.0,
                "min": min(queue_values) if queue_values else 0.0,
                "max": max(queue_values) if queue_values else 0.0,
                "p50": self.calculate_percentile(queue_values, 50),
                "p90": self.calculate_percentile(queue_values, 90),
                "p95": self.calculate_percentile(queue_values, 95),
                "p99": self.calculate_percentile(queue_values, 99),
            },
            "prefill": {
                "avg": (
                    sum(prefill_values) / len(prefill_values) if prefill_values else 0.0
                ),
                "min": min(prefill_values) if prefill_values else 0.0,
                "max": max(prefill_values) if prefill_values else 0.0,
                "p50": self.calculate_percentile(prefill_values, 50),
                "p90": self.calculate_percentile(prefill_values, 90),
                "p95": self.calculate_percentile(prefill_values, 95),
                "p99": self.calculate_percentile(prefill_values, 99),
            },
            "decode": {
                "avg": (
                    sum(decode_values) / len(decode_values) if decode_values else 0.0
                ),
                "min": min(decode_values) if decode_values else 0.0,
                "max": max(decode_values) if decode_values else 0.0,
                "p50": self.calculate_percentile(decode_values, 50),
                "p90": self.calculate_percentile(decode_values, 90),
                "p95": self.calculate_percentile(decode_values, 95),
                "p99": self.calculate_percentile(decode_values, 99),
            },
        }

    def get_throughput_stats(
            self, window_seconds: int = 60) -> dict[str, float]:
        """Get throughput statistics."""
        recent = self.get_recent_requests(window_seconds)

        if not recent:
            return {
                "requests_per_second": 0.0,
                "tokens_per_second": 0.0,
                "input_tokens_per_second": 0.0,
                "output_tokens_per_second": 0.0,
            }

        total_input_tokens = sum(r.input_tokens for r in recent)
        total_output_tokens = sum(r.output_tokens for r in recent)

        return {
            "requests_per_second": len(recent) / window_seconds,
            "tokens_per_second": (total_input_tokens + total_output_tokens) /
            window_seconds,
            "input_tokens_per_second": total_input_tokens / window_seconds,
            "output_tokens_per_second": total_output_tokens / window_seconds,
        }

    def get_model_stats(self, window_seconds: int = 60) -> dict[str, Any]:
        """
        Get enhanced per-model statistics matching dashboard expectations.

        Args:
            window_seconds: Time window for RPS/TPS calculations (default: 60)

        Returns:
            Dictionary with per-model stats including:
            - requests, rps, tps
            - avg_ttft_ms, avg_itl_ms
            - input_tokens, output_tokens
            - cache_hit_rate
            - success_rate
        """
        with self._lock:
            current_time = time.time()
            cutoff_time = current_time - window_seconds

            stats = {}
            for model, data in self.model_stats.items():
                if data["requests"] > 0:
                    # Calculate RPS (requests per second over last N seconds)
                    recent_requests = [
                        ts
                        for ts in data["request_timestamps"]
                        if ts >= cutoff_time
                    ]
                    rps = len(recent_requests) / \
                        window_seconds if recent_requests else 0.0

                    # Calculate TPS (tokens per second over last N seconds)
                    recent_tokens = [
                        token_count
                        for ts, token_count in data["token_timestamps"]
                        if ts >= cutoff_time
                    ]
                    total_recent_tokens = sum(recent_tokens)
                    tps = total_recent_tokens / window_seconds if recent_tokens else 0.0

                    # Calculate success rate
                    success_rate = (
                        data["successful_requests"] / data["requests"]
                        if data["requests"] > 0
                        else 0.0
                    )

                    # Calculate cache hit rate
                    cache_hit_rate = (
                        data["cache_hits"] / data["cache_attempts"]
                        if data["cache_attempts"] > 0
                        else 0.0
                    )

                    stats[model] = {
                        "requests": data["requests"],
                        "rps": round(rps, 2),
                        "tps": round(tps, 1),
                        "avg_ttft_ms": round(data["ttft_sum"] / data["requests"], 2),
                        "avg_itl_ms": round(
                            data["itl_sum"] / data["requests"], 2
                        ),
                        "input_tokens": data["input_tokens"],
                        "output_tokens": data["output_tokens"],
                        "cache_hit_rate": round(cache_hit_rate, 3),
                        "success_rate": round(success_rate, 3),
                    }

            return stats

    def get_queue_stats(self) -> dict[str, Any]:
        """
        Get comprehensive queue statistics.

        Combines internal tracking with QueueDepthTracker for complete statistics.
        Returns queue depth, wait times (avg, P50, P95, P99), and per-model stats.
        """
        # If queue tracker is disabled, return simple stats
        if self.queue_tracker is None:
            with self._lock:
                return {
                    "current_depth": self.current_queue_depth,
                    "max_depth": self.max_queue_depth,
                    "avg_depth": 0.0,
                }

        # Get detailed stats from queue tracker
        tracker_stats = self.queue_tracker.get_queue_stats()
        model_stats = self.queue_tracker.get_model_stats()

        with self._lock:
            # Merge with internal tracking
            return {
                # Current state
                "current_depth": tracker_stats["current_depth"],
                "max_depth": tracker_stats["max_depth"],
                "avg_depth": (
                    sum(d for _, d in self.queue_depth_history) /
                    len(self.queue_depth_history)
                    if self.queue_depth_history
                    else 0.0
                ),
                # Queue activity
                "total_enqueued": tracker_stats["total_enqueued"],
                "total_dequeued": tracker_stats["total_dequeued"],
                "active_requests": tracker_stats["active_requests"],
                # Wait times
                "wait_times": tracker_stats["wait_times"],
                # Per-model stats
                "per_model": model_stats,
                # Utilization
                "utilization_pct": tracker_stats.get("utilization_pct", 0.0),
            }

    def get_batch_stats(self) -> dict[str, Any]:
        """Get batch statistics."""
        with self._lock:
            return {
                "current_size": self.current_batch_size,
                "avg_size": self.avg_batch_size,
                "max_size": (
                    max(self.batch_size_history) if self.batch_size_history else 0
                ),
            }

    def get_cache_stats(self, window_seconds: int = 60) -> dict[str, Any]:
        """Get KV cache statistics."""
        recent = self.get_recent_requests(window_seconds)

        if not recent:
            return {
                "hit_rate": 0.0,
                "avg_overlap_score": 0.0,
                "avg_blocks_matched": 0.0,
                "total_cached_tokens": 0,
            }

        hits = sum(1 for r in recent if r.kv_cache_hit)
        total_cached = sum(r.cached_tokens for r in recent)
        overlap_scores = [
            r.kv_cache_overlap_score for r in recent if r.kv_cache_overlap_score > 0]

        return {
            "hit_rate": (hits / len(recent)) * 100 if recent else 0.0,
            "avg_overlap_score": (
                sum(overlap_scores) / len(overlap_scores) if overlap_scores else 0.0
            ),
            "avg_blocks_matched": (
                sum(r.kv_cache_blocks_matched for r in recent) / len(recent)
                if recent
                else 0.0
            ),
            "total_cached_tokens": total_cached,
        }

    def get_token_stats(self, window_seconds: int = 60) -> dict[str, Any]:
        """
        Get comprehensive token statistics.

        Returns:
            Dictionary with total tokens, rates, averages, and percentiles
        """
        recent = self.get_recent_requests(window_seconds)

        if not recent:
            return {
                "total_input_tokens": self.total_input_tokens,
                "total_output_tokens": self.total_output_tokens,
                "total_cached_tokens": self.total_cached_tokens,
                "input_tokens_per_sec": 0.0,
                "output_tokens_per_sec": 0.0,
                "avg_input_tokens": 0.0,
                "avg_output_tokens": 0.0,
                "p95_input_tokens": 0.0,
                "p95_output_tokens": 0.0,
                "p99_input_tokens": 0.0,
                "p99_output_tokens": 0.0,
            }

        # Extract token values
        input_tokens = [r.input_tokens for r in recent]
        output_tokens = [r.output_tokens for r in recent]

        # Calculate total tokens in window
        total_input_in_window = sum(input_tokens)
        total_output_in_window = sum(output_tokens)

        # Calculate rates (tokens per second over the window)
        input_tokens_per_sec = total_input_in_window / window_seconds
        output_tokens_per_sec = total_output_in_window / window_seconds

        # Calculate averages
        avg_input = total_input_in_window / len(recent) if recent else 0.0
        avg_output = total_output_in_window / len(recent) if recent else 0.0

        # Calculate percentiles
        p95_input = self.calculate_percentile(input_tokens, 95)
        p95_output = self.calculate_percentile(output_tokens, 95)
        p99_input = self.calculate_percentile(input_tokens, 99)
        p99_output = self.calculate_percentile(output_tokens, 99)

        return {
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_cached_tokens": self.total_cached_tokens,
            "input_tokens_per_sec": round(input_tokens_per_sec, 2),
            "output_tokens_per_sec": round(output_tokens_per_sec, 2),
            "avg_input_tokens": round(avg_input, 1),
            "avg_output_tokens": round(avg_output, 1),
            "p95_input_tokens": int(p95_input),
            "p95_output_tokens": int(p95_output),
            "p99_input_tokens": int(p99_input),
            "p99_output_tokens": int(p99_output),
        }

    def get_disaggregation_stats(self) -> dict[str, Any]:
        """Get disaggregated serving statistics."""
        with self._lock:
            total = self.prefill_requests + self.decode_requests
            return {
                "prefill_requests": self.prefill_requests,
                "decode_requests": self.decode_requests,
                "prefill_ratio": self.prefill_requests /
                total if total > 0 else 0.0,
                "decode_ratio": self.decode_requests /
                total if total > 0 else 0.0,
                "kv_transfer_bytes": self.kv_transfer_bytes,
                "kv_transfer_time_ms": self.kv_transfer_time_ms,
            }

    def get_request_lifecycles(self) -> list[dict[str, Any]]:
        """
        Get the last 100 complete request lifecycles for timeline visualization.

        Returns a list of request lifecycle dictionaries with all timestamps
        and metadata needed for visual timeline rendering.
        """
        with self._lock:
            lifecycles = []
            for request in self._request_lifecycles:
                lifecycle = {
                    "request_id": request.request_id,
                    "model": request.model,
                    "status": "completed" if request.success else "failed",
                    "arrival_time": request.arrival_time,
                    "queue_start_time": request.queue_start_time,
                    "prefill_start_time": request.prefill_start_time,
                    "first_token_time": request.first_token_time,
                    "completion_time": request.completion_time,
                    "input_tokens": request.input_tokens,
                    "output_tokens": request.output_tokens,
                    "cached_tokens": request.cached_tokens,
                    "worker_id": request.worker_id,
                    "routing_cost_ms": round(request.routing_cost, 3),
                }
                lifecycles.append(lifecycle)
            return lifecycles

    def get_prometheus_metrics(self) -> str:
        """Export metrics in Prometheus format."""
        lines = []

        # Get recent stats
        latency_stats = self.get_latency_stats(60)
        throughput_stats = self.get_throughput_stats(60)
        queue_stats = self.get_queue_stats()
        batch_stats = self.get_batch_stats()
        cache_stats = self.get_cache_stats(60)

        # Request counters
        lines.append("# TYPE fakeai_dynamo_requests_total counter")
        lines.append(f"fakeai_dynamo_requests_total {self.total_requests}")
        lines.append("# TYPE fakeai_dynamo_requests_successful_total counter")
        lines.append(
            f"fakeai_dynamo_requests_successful_total {
                self.successful_requests}")
        lines.append("# TYPE fakeai_dynamo_requests_failed_total counter")
        lines.append(
            f"fakeai_dynamo_requests_failed_total {
                self.failed_requests}")
        lines.append("")

        # Latency metrics (summaries)
        for metric_name, stats in [
            ("fakeai_dynamo_ttft_seconds", latency_stats["ttft"]),
            ("fakeai_dynamo_itl_seconds", latency_stats["itl"]),
            ("fakeai_dynamo_total_latency_seconds", latency_stats["total"]),
        ]:
            lines.append(f"# TYPE {metric_name} summary")
            lines.append(
                f'{metric_name}{{quantile="0.5"}} {stats["p50"] / 1000:.6f}')
            lines.append(
                f'{metric_name}{{quantile="0.9"}} {stats["p90"] / 1000:.6f}')
            lines.append(
                f'{metric_name}{{quantile="0.99"}} {stats["p99"] / 1000:.6f}')
            lines.append("")

        # Throughput metrics
        lines.append("# TYPE fakeai_dynamo_requests_per_second gauge")
        lines.append(
            f'fakeai_dynamo_requests_per_second {
                throughput_stats["requests_per_second"]:.2f}')
        lines.append("# TYPE fakeai_dynamo_tokens_per_second gauge")
        lines.append(
            f'fakeai_dynamo_tokens_per_second {
                throughput_stats["tokens_per_second"]:.2f}')
        lines.append("")

        # Queue metrics
        lines.append("# TYPE fakeai_dynamo_queue_depth gauge")
        lines.append(
            f'fakeai_dynamo_queue_depth {
                queue_stats["current_depth"]}')
        lines.append("# TYPE fakeai_dynamo_queue_depth_max gauge")
        lines.append(
            f'fakeai_dynamo_queue_depth_max {
                queue_stats["max_depth"]}')
        lines.append("")

        # Batch metrics
        lines.append("# TYPE fakeai_dynamo_batch_size gauge")
        lines.append(f'fakeai_dynamo_batch_size {batch_stats["current_size"]}')
        lines.append("# TYPE fakeai_dynamo_batch_size_avg gauge")
        lines.append(
            f'fakeai_dynamo_batch_size_avg {
                batch_stats["avg_size"]:.2f}')
        lines.append("")

        # Cache metrics
        lines.append("# TYPE fakeai_dynamo_kv_cache_hit_rate gauge")
        lines.append(
            f'fakeai_dynamo_kv_cache_hit_rate {
                cache_stats["hit_rate"]:.2f}')
        lines.append("")

        return "\n".join(lines)

    def get_latency_breakdowns(self) -> list[dict[str, Any]]:
        """
        Get latency breakdown data for last 100 requests.

        Returns list of breakdown entries with queue, prefill, and decode times.
        """
        with self._lock:
            return list(self._latency_breakdowns)

    def get_worker_stats(self) -> dict[str, Any]:
        """
        Get comprehensive worker statistics.

        Returns dictionary matching dashboard format with:
        - total_workers, active_workers, idle_workers, offline_workers
        - Per-worker stats (active_requests, total_requests, avg_duration, utilization)
        """
        if self.worker_pool is None:
            return {
                "total_workers": 0,
                "active_workers": 0,
                "idle_workers": 0,
                "offline_workers": 0,
                "workers": []
            }

        return self.worker_pool.get_worker_stats()

    def get_historical_trends(
            self, window_seconds: int = 3600) -> list[dict[str, Any]]:
        """
        Get historical trend data for time-series visualization (1-minute buckets).

        Returns a list of trend snapshots over the collection window, with each
        snapshot containing aggregate metrics for requests, latency, throughput,
        and error rates in 1-minute intervals.

        Args:
            window_seconds: Time window for trends (default: 3600 seconds / 60 minutes)

        Returns:
            List of trend dictionaries with 1-minute aggregations matching dashboard format:
            {
                "timestamp": unix_timestamp,
                "request_count": number of requests,
                "avg_ttft_ms": average time to first token,
                "avg_itl_ms": average inter-token latency,
                "throughput_rps": requests per second,
                "throughput_tps": tokens per second,
                "error_rate": failure rate (0.0 to 1.0)
            }
        """
        with self._lock:
            # Get completed requests within window
            cutoff_time = time.time() - window_seconds
            recent_requests = [
                r for r in self._completed_requests if r.completion_time >= cutoff_time]

            if not recent_requests:
                return []

            # Group requests into time buckets (1-minute intervals as per
            # dashboard spec)
            bucket_size = 60  # seconds (1 minute)
            num_buckets = max(1, window_seconds // bucket_size)

            # Find earliest and latest timestamps
            earliest = min(r.completion_time for r in recent_requests)
            latest = max(r.completion_time for r in recent_requests)

            # Create time buckets
            buckets: dict[int, list[RequestMetrics]] = {}
            for request in recent_requests:
                # Calculate which bucket this request belongs to
                bucket_idx = int(
                    (request.completion_time - earliest) / bucket_size)
                if bucket_idx not in buckets:
                    buckets[bucket_idx] = []
                buckets[bucket_idx].append(request)

            # Generate trend data for each bucket
            trends = []
            for bucket_idx in sorted(buckets.keys()):
                bucket_requests = buckets[bucket_idx]
                bucket_timestamp = int(earliest + (bucket_idx * bucket_size))

                # Calculate aggregate metrics for this bucket
                total_reqs = len(bucket_requests)
                successful_reqs = sum(1 for r in bucket_requests if r.success)
                failed_reqs = total_reqs - successful_reqs

                # Latency metrics
                total_latencies = [
                    r.total_time_ms for r in bucket_requests if r.total_time_ms > 0]
                ttft_values = [
                    r.ttft_ms for r in bucket_requests if r.ttft_ms > 0]
                tpot_values = [
                    r.tpot_ms for r in bucket_requests if r.tpot_ms > 0]

                avg_total_latency = sum(
                    total_latencies) / len(total_latencies) if total_latencies else 0.0
                avg_ttft = sum(ttft_values) / \
                    len(ttft_values) if ttft_values else 0.0
                avg_tpot = sum(tpot_values) / \
                    len(tpot_values) if tpot_values else 0.0
                p95_total_latency = self.calculate_percentile(
                    total_latencies, 95) if total_latencies else 0.0

                # Throughput metrics
                input_tokens = sum(r.input_tokens for r in bucket_requests)
                output_tokens = sum(r.output_tokens for r in bucket_requests)
                total_tokens = input_tokens + output_tokens

                # Calculate rates (per second within this bucket)
                requests_per_sec = total_reqs / bucket_size
                tokens_per_sec = total_tokens / bucket_size

                # Queue metrics (use queue history if available)
                queue_depths_in_bucket = [
                    depth for ts, depth in self.queue_depth_history
                    if bucket_timestamp <= ts < bucket_timestamp + bucket_size
                ]
                avg_queue_depth = sum(
                    queue_depths_in_bucket) / len(queue_depths_in_bucket) if queue_depths_in_bucket else 0.0

                # Queue wait times from requests
                queue_waits = [
                    r.queue_time_ms for r in bucket_requests if r.queue_time_ms > 0]
                avg_queue_wait = sum(queue_waits) / \
                    len(queue_waits) if queue_waits else 0.0

                # Cache metrics
                cache_hits = sum(1 for r in bucket_requests if r.kv_cache_hit)
                cache_hit_rate = (
                    cache_hits /
                    total_reqs *
                    100) if total_reqs > 0 else 0.0

                # Calculate error rate
                error_rate = failed_reqs / total_reqs if total_reqs > 0 else 0.0

                # Build trend entry matching dashboard interface specification
                trend = {
                    "timestamp": bucket_timestamp,
                    "request_count": total_reqs,
                    "avg_ttft_ms": round(avg_ttft, 2),
                    "avg_itl_ms": round(avg_tpot, 2),  # ITL is same as TPOT
                    "throughput_rps": round(requests_per_sec, 2),
                    "throughput_tps": round(tokens_per_sec, 1),
                    "error_rate": round(error_rate, 4),
                }

                trends.append(trend)

            return trends

    def get_stats_dict(self) -> dict[str, Any]:
        """Get all statistics as dictionary."""
        return {
            "summary": {
                "total_requests": self.total_requests,
                "successful_requests": self.successful_requests,
                "failed_requests": self.failed_requests,
                "active_requests": len(self._active_requests),
            },
            "latency": self.get_latency_stats(60),
            "latency_breakdown": self.get_latency_breakdowns(),
            "throughput": self.get_throughput_stats(60),
            "token_stats": self.get_token_stats(60),
            "queue": self.get_queue_stats(),
            "batch": self.get_batch_stats(),
            "cache": self.get_cache_stats(60),
            "disaggregation": self.get_disaggregation_stats(),
            "per_model": self.get_model_stats(),
            "worker_stats": self.get_worker_stats(),
            "request_lifecycles": self.get_request_lifecycles(),
            "historical_trends": self.get_historical_trends(),
        }
