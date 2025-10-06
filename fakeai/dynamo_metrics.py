"""
NVIDIA AI-Dynamo Enhanced Metrics.

Comprehensive LLM inference metrics including latency breakdown,
throughput measurements, queue statistics, batch metrics, and
disaggregated serving metrics.
"""

import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any


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
            self.decode_time_ms = (self.completion_time - self.decode_start_time) * 1000

        if self.arrival_time > 0 and self.completion_time > 0:
            self.total_time_ms = (self.completion_time - self.arrival_time) * 1000

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

    def __init__(self, window_size: int = 300):
        """
        Initialize metrics collector.

        Args:
            window_size: Time window for metrics in seconds (default: 5 minutes)
        """
        self.window_size = window_size

        # Request tracking
        self._completed_requests: deque[RequestMetrics] = deque(maxlen=10000)
        self._active_requests: dict[str, RequestMetrics] = {}

        # Histogram buckets for latencies (in seconds)
        self.ttft_buckets = [0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0, 10.0]
        self.itl_buckets = [0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1.0]
        self.total_latency_buckets = [0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]

        # Counters
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0

        # Per-model statistics
        self.model_stats = defaultdict(
            lambda: {
                "requests": 0,
                "tokens": 0,
                "ttft_sum": 0.0,
                "itl_sum": 0.0,
            }
        )

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
            request = RequestMetrics(
                request_id=request_id,
                model=model,
                endpoint=endpoint,
                arrival_time=time.time(),
                queue_start_time=time.time(),
                input_tokens=input_tokens,
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
            request.worker_id = worker_id
            request.success = success
            request.finish_reason = finish_reason

            # Calculate derived metrics
            request.calculate_derived_metrics()

            # Store completed request
            self._completed_requests.append(request)

            # Update counters
            if success:
                self.successful_requests += 1
            else:
                self.failed_requests += 1

            # Update model stats
            self.model_stats[request.model]["requests"] += 1
            self.model_stats[request.model]["tokens"] += output_tokens
            self.model_stats[request.model]["ttft_sum"] += request.ttft_ms
            self.model_stats[request.model]["itl_sum"] += request.itl_ms

            self.decode_requests += 1

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
                r for r in self._completed_requests if r.completion_time >= cutoff_time
            ]

    def calculate_percentile(self, values: list[float], percentile: float) -> float:
        """Calculate percentile from sorted values."""
        if not values:
            return 0.0
        sorted_vals = sorted(values)
        idx = int(len(sorted_vals) * (percentile / 100.0))
        idx = min(idx, len(sorted_vals) - 1)
        return sorted_vals[idx]

    def get_latency_stats(self, window_seconds: int = 60) -> dict[str, Any]:
        """Get latency statistics for recent window."""
        recent = self.get_recent_requests(window_seconds)

        if not recent:
            return {
                "ttft": {"avg": 0.0, "p50": 0.0, "p90": 0.0, "p99": 0.0},
                "itl": {"avg": 0.0, "p50": 0.0, "p90": 0.0, "p99": 0.0},
                "total": {"avg": 0.0, "p50": 0.0, "p90": 0.0, "p99": 0.0},
                "queue": {"avg": 0.0, "p50": 0.0, "p90": 0.0, "p99": 0.0},
                "prefill": {"avg": 0.0, "p50": 0.0, "p90": 0.0, "p99": 0.0},
                "decode": {"avg": 0.0, "p50": 0.0, "p90": 0.0, "p99": 0.0},
            }

        # Extract values
        ttft_values = [r.ttft_ms for r in recent if r.ttft_ms > 0]
        itl_values = [r.itl_ms for r in recent if r.itl_ms > 0]
        total_values = [r.total_time_ms for r in recent if r.total_time_ms > 0]
        queue_values = [r.queue_time_ms for r in recent if r.queue_time_ms > 0]
        prefill_values = [r.prefill_time_ms for r in recent if r.prefill_time_ms > 0]
        decode_values = [r.decode_time_ms for r in recent if r.decode_time_ms > 0]

        # Calculate stats
        return {
            "ttft": {
                "avg": sum(ttft_values) / len(ttft_values) if ttft_values else 0.0,
                "p50": self.calculate_percentile(ttft_values, 50),
                "p90": self.calculate_percentile(ttft_values, 90),
                "p99": self.calculate_percentile(ttft_values, 99),
            },
            "itl": {
                "avg": sum(itl_values) / len(itl_values) if itl_values else 0.0,
                "p50": self.calculate_percentile(itl_values, 50),
                "p90": self.calculate_percentile(itl_values, 90),
                "p99": self.calculate_percentile(itl_values, 99),
            },
            "total": {
                "avg": sum(total_values) / len(total_values) if total_values else 0.0,
                "p50": self.calculate_percentile(total_values, 50),
                "p90": self.calculate_percentile(total_values, 90),
                "p99": self.calculate_percentile(total_values, 99),
            },
            "queue": {
                "avg": sum(queue_values) / len(queue_values) if queue_values else 0.0,
                "p50": self.calculate_percentile(queue_values, 50),
                "p90": self.calculate_percentile(queue_values, 90),
                "p99": self.calculate_percentile(queue_values, 99),
            },
            "prefill": {
                "avg": (
                    sum(prefill_values) / len(prefill_values) if prefill_values else 0.0
                ),
                "p50": self.calculate_percentile(prefill_values, 50),
                "p90": self.calculate_percentile(prefill_values, 90),
                "p99": self.calculate_percentile(prefill_values, 99),
            },
            "decode": {
                "avg": (
                    sum(decode_values) / len(decode_values) if decode_values else 0.0
                ),
                "p50": self.calculate_percentile(decode_values, 50),
                "p90": self.calculate_percentile(decode_values, 90),
                "p99": self.calculate_percentile(decode_values, 99),
            },
        }

    def get_throughput_stats(self, window_seconds: int = 60) -> dict[str, float]:
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
            "tokens_per_second": (total_input_tokens + total_output_tokens)
            / window_seconds,
            "input_tokens_per_second": total_input_tokens / window_seconds,
            "output_tokens_per_second": total_output_tokens / window_seconds,
        }

    def get_model_stats(self) -> dict[str, Any]:
        """Get per-model statistics."""
        with self._lock:
            stats = {}
            for model, data in self.model_stats.items():
                if data["requests"] > 0:
                    stats[model] = {
                        "requests": data["requests"],
                        "total_tokens": data["tokens"],
                        "avg_ttft_ms": data["ttft_sum"] / data["requests"],
                        "avg_itl_ms": (
                            data["itl_sum"] / data["requests"]
                            if data["requests"] > 0
                            else 0.0
                        ),
                    }
            return stats

    def get_queue_stats(self) -> dict[str, Any]:
        """Get queue statistics."""
        with self._lock:
            return {
                "current_depth": self.current_queue_depth,
                "max_depth": self.max_queue_depth,
                "avg_depth": (
                    sum(d for _, d in self.queue_depth_history)
                    / len(self.queue_depth_history)
                    if self.queue_depth_history
                    else 0.0
                ),
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
            r.kv_cache_overlap_score for r in recent if r.kv_cache_overlap_score > 0
        ]

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

    def get_disaggregation_stats(self) -> dict[str, Any]:
        """Get disaggregated serving statistics."""
        with self._lock:
            total = self.prefill_requests + self.decode_requests
            return {
                "prefill_requests": self.prefill_requests,
                "decode_requests": self.decode_requests,
                "prefill_ratio": self.prefill_requests / total if total > 0 else 0.0,
                "decode_ratio": self.decode_requests / total if total > 0 else 0.0,
                "kv_transfer_bytes": self.kv_transfer_bytes,
                "kv_transfer_time_ms": self.kv_transfer_time_ms,
            }

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
            f"fakeai_dynamo_requests_successful_total {self.successful_requests}"
        )
        lines.append("# TYPE fakeai_dynamo_requests_failed_total counter")
        lines.append(f"fakeai_dynamo_requests_failed_total {self.failed_requests}")
        lines.append("")

        # Latency metrics (summaries)
        for metric_name, stats in [
            ("fakeai_dynamo_ttft_seconds", latency_stats["ttft"]),
            ("fakeai_dynamo_itl_seconds", latency_stats["itl"]),
            ("fakeai_dynamo_total_latency_seconds", latency_stats["total"]),
        ]:
            lines.append(f"# TYPE {metric_name} summary")
            lines.append(f'{metric_name}{{quantile="0.5"}} {stats["p50"] / 1000:.6f}')
            lines.append(f'{metric_name}{{quantile="0.9"}} {stats["p90"] / 1000:.6f}')
            lines.append(f'{metric_name}{{quantile="0.99"}} {stats["p99"] / 1000:.6f}')
            lines.append("")

        # Throughput metrics
        lines.append("# TYPE fakeai_dynamo_requests_per_second gauge")
        lines.append(
            f'fakeai_dynamo_requests_per_second {throughput_stats["requests_per_second"]:.2f}'
        )
        lines.append("# TYPE fakeai_dynamo_tokens_per_second gauge")
        lines.append(
            f'fakeai_dynamo_tokens_per_second {throughput_stats["tokens_per_second"]:.2f}'
        )
        lines.append("")

        # Queue metrics
        lines.append("# TYPE fakeai_dynamo_queue_depth gauge")
        lines.append(f'fakeai_dynamo_queue_depth {queue_stats["current_depth"]}')
        lines.append("# TYPE fakeai_dynamo_queue_depth_max gauge")
        lines.append(f'fakeai_dynamo_queue_depth_max {queue_stats["max_depth"]}')
        lines.append("")

        # Batch metrics
        lines.append("# TYPE fakeai_dynamo_batch_size gauge")
        lines.append(f'fakeai_dynamo_batch_size {batch_stats["current_size"]}')
        lines.append("# TYPE fakeai_dynamo_batch_size_avg gauge")
        lines.append(f'fakeai_dynamo_batch_size_avg {batch_stats["avg_size"]:.2f}')
        lines.append("")

        # Cache metrics
        lines.append("# TYPE fakeai_dynamo_kv_cache_hit_rate gauge")
        lines.append(f'fakeai_dynamo_kv_cache_hit_rate {cache_stats["hit_rate"]:.2f}')
        lines.append("")

        return "\n".join(lines)

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
            "throughput": self.get_throughput_stats(60),
            "queue": self.get_queue_stats(),
            "batch": self.get_batch_stats(),
            "cache": self.get_cache_stats(60),
            "disaggregation": self.get_disaggregation_stats(),
            "per_model": self.get_model_stats(),
        }
