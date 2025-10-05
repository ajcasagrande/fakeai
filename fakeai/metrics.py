#!/usr/bin/env python3
"""
FakeAI Server Metrics Tracking

This module provides functionality to track various metrics for the FakeAI server,
including requests per second, responses per second, response times, and more.
"""
#  SPDX-License-Identifier: Apache-2.0

import logging
import random
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics tracked."""
    REQUESTS = "requests"
    RESPONSES = "responses"
    TOKENS = "tokens"
    ERRORS = "errors"
    LATENCY = "latency"
    STREAMING = "streaming"


@dataclass
class StreamingMetrics:
    """Metrics for a single stream."""
    stream_id: str
    start_time: float
    first_token_time: float | None = None
    last_token_time: float | None = None
    token_count: int = 0
    completed: bool = False
    failed: bool = False
    error_message: str | None = None
    total_duration: float | None = None

    def calculate_ttft(self) -> float | None:
        """Calculate time to first token (TTFT)."""
        if self.first_token_time:
            return self.first_token_time - self.start_time
        return None

    def calculate_tokens_per_second(self) -> float | None:
        """Calculate tokens per second."""
        if self.completed and self.total_duration and self.token_count > 0:
            return self.token_count / self.total_duration
        return None


@dataclass
class MetricsWindow:
    """Numpy-based sliding window for metrics tracking with smooth rate calculations."""
    window_size: float = 60.0  # Default 60 seconds window
    max_samples: int = 100000  # Maximum samples to keep in memory

    def __post_init__(self):
        """Initialize numpy arrays for data storage."""
        self.timestamps = np.array([], dtype=np.float64)
        self.values = np.array([], dtype=np.float64)
        self.latencies = np.array([], dtype=np.float64)
        self.latency_timestamps = np.array([], dtype=np.float64)

        # Use threading.Lock (not asyncio.Lock) because:
        # 1. Metrics accessed from both sync (background thread) and async (FastAPI handlers) code
        # 2. Numpy operations are extremely fast (microseconds), so blocking is negligible
        # 3. threading.Lock works in both sync and async contexts
        self._lock = threading.Lock()

    def add(self, value: int = 1) -> None:
        """Add a data point with current timestamp."""
        with self._lock:
            current_time = time.time()

            # Append new data
            self.timestamps = np.append(self.timestamps, current_time)
            self.values = np.append(self.values, float(value))

            # Cleanup old data beyond window
            self._cleanup()

    def add_latency(self, latency: float) -> None:
        """Add a latency measurement with current timestamp."""
        with self._lock:
            current_time = time.time()

            # Append new latency
            self.latency_timestamps = np.append(self.latency_timestamps, current_time)
            self.latencies = np.append(self.latencies, latency)

            # Cleanup old data beyond window
            self._cleanup()

    def _cleanup(self) -> None:
        """Remove data older than the window size using vectorized operations."""
        current_time = time.time()
        cutoff_time = current_time - self.window_size

        # Filter timestamps for events
        if len(self.timestamps) > 0:
            valid_mask = self.timestamps >= cutoff_time
            self.timestamps = self.timestamps[valid_mask]
            self.values = self.values[valid_mask]

            # If we exceed max samples, keep only the most recent
            if len(self.timestamps) > self.max_samples:
                self.timestamps = self.timestamps[-self.max_samples:]
                self.values = self.values[-self.max_samples:]

        # Filter timestamps for latencies
        if len(self.latency_timestamps) > 0:
            valid_mask = self.latency_timestamps >= cutoff_time
            self.latency_timestamps = self.latency_timestamps[valid_mask]
            self.latencies = self.latencies[valid_mask]

            # If we exceed max samples, keep only the most recent
            if len(self.latency_timestamps) > self.max_samples:
                self.latency_timestamps = self.latency_timestamps[-self.max_samples:]
                self.latencies = self.latencies[-self.max_samples:]

    def get_rate(self) -> float:
        """
        Get the current rate per second within the window using numpy.

        This calculates rate as: total_events / actual_time_span
        which provides smooth up/down behavior over time.
        """
        with self._lock:
            if len(self.timestamps) == 0:
                return 0.0

            current_time = time.time()
            cutoff_time = current_time - self.window_size

            # Filter to window
            valid_mask = self.timestamps >= cutoff_time
            valid_timestamps = self.timestamps[valid_mask]
            valid_values = self.values[valid_mask]

            if len(valid_timestamps) == 0:
                return 0.0

            # Calculate actual time span covered by the data
            time_span = current_time - valid_timestamps[0]

            # Avoid division by zero
            if time_span <= 0.0:
                time_span = 0.001  # 1ms minimum

            # Sum all values and divide by time span for rate per second
            total_count = np.sum(valid_values)
            rate = total_count / time_span

            return float(rate)

    def get_latency_stats(self) -> Dict[str, float]:
        """Get latency statistics within the window using numpy percentiles."""
        with self._lock:
            if len(self.latency_timestamps) == 0:
                return {
                    "avg": 0.0,
                    "min": 0.0,
                    "max": 0.0,
                    "p50": 0.0,
                    "p90": 0.0,
                    "p99": 0.0,
                }

            current_time = time.time()
            cutoff_time = current_time - self.window_size

            # Filter to window
            valid_mask = self.latency_timestamps >= cutoff_time
            valid_latencies = self.latencies[valid_mask]

            if len(valid_latencies) == 0:
                return {
                    "avg": 0.0,
                    "min": 0.0,
                    "max": 0.0,
                    "p50": 0.0,
                    "p90": 0.0,
                    "p99": 0.0,
                }

            # Use numpy for efficient percentile calculations
            return {
                "avg": float(np.mean(valid_latencies)),
                "min": float(np.min(valid_latencies)),
                "max": float(np.max(valid_latencies)),
                "p50": float(np.percentile(valid_latencies, 50)),
                "p90": float(np.percentile(valid_latencies, 90)),
                "p99": float(np.percentile(valid_latencies, 99)),
            }

    def get_stats(self) -> Dict[str, float]:
        """Get all stats for this window."""
        return {
            "rate": self.get_rate(),
            **{k: v for k, v in self.get_latency_stats().items()},
        }


class MetricsTracker:
    """Singleton class to track FakeAI server metrics."""
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(MetricsTracker, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._metrics = {
            MetricType.REQUESTS: defaultdict(lambda: MetricsWindow()),
            MetricType.RESPONSES: defaultdict(lambda: MetricsWindow()),
            MetricType.TOKENS: defaultdict(lambda: MetricsWindow()),
            MetricType.ERRORS: defaultdict(lambda: MetricsWindow()),
            MetricType.LATENCY: defaultdict(lambda: MetricsWindow()),
            MetricType.STREAMING: defaultdict(lambda: MetricsWindow()),
        }

        # Endpoints to skip tracking (non-OpenAI endpoints)
        self._skip_endpoints = {
            "/metrics",
            "/dcgm-metrics",
            "/dcgm-metrics/json",
            "/dynamo-metrics",
            "/dynamo-metrics/json",
            "/kv-cache-metrics",
            "/dashboard",
            "/dashboard/dynamo",
        }

        # Queue for response times (used for per-request timing)
        self._response_times = defaultdict(lambda: deque(maxlen=1000))

        # Streaming metrics storage
        self._streaming_metrics: Dict[str, StreamingMetrics] = {}
        self._streaming_lock = threading.Lock()

        # Aggregate streaming stats
        self._completed_streams: deque[StreamingMetrics] = deque(maxlen=1000)
        self._failed_streams: deque[StreamingMetrics] = deque(maxlen=1000)

        # Print metrics periodically in a separate thread
        self._stop_thread = False
        self._print_interval = 5  # Print metrics every 5 seconds
        self._thread = threading.Thread(target=self._print_metrics_periodically)
        self._thread.daemon = True
        self._thread.start()

        self._initialized = True
        logger.info("Metrics tracker initialized")

    def _should_track_endpoint(self, endpoint: str) -> bool:
        """
        Check if an endpoint should be tracked.

        Skip tracking for:
        - Non-OpenAI endpoints (metrics, dashboards)
        - Static file endpoints
        """
        # Skip exact matches
        if endpoint in self._skip_endpoints:
            return False

        # Skip anything starting with /static/
        if endpoint.startswith("/static/"):
            return False

        # Track everything else (OpenAI API endpoints, /health, etc.)
        return True

    def track_request(self, endpoint: str) -> None:
        """Track a new request to a specific endpoint."""
        if not self._should_track_endpoint(endpoint):
            return
        self._metrics[MetricType.REQUESTS][endpoint].add()

    def track_response(self, endpoint: str, latency: Optional[float] = None) -> None:
        """Track a new response from a specific endpoint."""
        if not self._should_track_endpoint(endpoint):
            return
        self._metrics[MetricType.RESPONSES][endpoint].add()
        if latency is not None:
            self._metrics[MetricType.RESPONSES][endpoint].add_latency(latency)

    def track_tokens(self, endpoint: str, count: int) -> None:
        """Track tokens generated for a specific endpoint."""
        if not self._should_track_endpoint(endpoint):
            return
        self._metrics[MetricType.TOKENS][endpoint].add(count)

    def track_error(self, endpoint: str) -> None:
        """Track an error for a specific endpoint."""
        if not self._should_track_endpoint(endpoint):
            return
        self._metrics[MetricType.ERRORS][endpoint].add()
    
    def start_request_timer(self, endpoint: str) -> int:
        """Start timing a request and return a request ID."""
        request_id = hash(f"{endpoint}_{time.time()}_{random.random()}")
        self._response_times[endpoint].append((request_id, time.time()))
        return request_id
    
    def end_request_timer(self, endpoint: str, request_id: int) -> float:
        """End timing a request and return the latency."""
        for i, (rid, start_time) in enumerate(self._response_times[endpoint]):
            if rid == request_id:
                latency = time.time() - start_time
                self.track_response(endpoint, latency)
                return latency

        # If request ID not found, just record response without latency
        self.track_response(endpoint)
        return 0.0

    def start_stream(self, stream_id: str, endpoint: str) -> None:
        """Start tracking a new stream."""
        with self._streaming_lock:
            self._streaming_metrics[stream_id] = StreamingMetrics(
                stream_id=stream_id,
                start_time=time.time(),
            )
            self._metrics[MetricType.STREAMING][endpoint].add()

    def track_stream_first_token(self, stream_id: str) -> None:
        """Track the first token in a stream (TTFT)."""
        with self._streaming_lock:
            if stream_id in self._streaming_metrics:
                self._streaming_metrics[stream_id].first_token_time = time.time()

    def track_stream_token(self, stream_id: str) -> None:
        """Track a token in a stream."""
        with self._streaming_lock:
            if stream_id in self._streaming_metrics:
                metrics = self._streaming_metrics[stream_id]
                metrics.token_count += 1
                metrics.last_token_time = time.time()

    def complete_stream(self, stream_id: str, endpoint: str) -> None:
        """Mark a stream as completed successfully."""
        with self._streaming_lock:
            if stream_id in self._streaming_metrics:
                metrics = self._streaming_metrics[stream_id]
                metrics.completed = True
                metrics.total_duration = time.time() - metrics.start_time

                # Move to completed streams
                self._completed_streams.append(metrics)

                # Track in metrics window
                if metrics.total_duration:
                    self._metrics[MetricType.RESPONSES][endpoint].add_latency(metrics.total_duration)

                # Remove from active
                del self._streaming_metrics[stream_id]

    def fail_stream(self, stream_id: str, endpoint: str, error_message: str) -> None:
        """Mark a stream as failed."""
        with self._streaming_lock:
            if stream_id in self._streaming_metrics:
                metrics = self._streaming_metrics[stream_id]
                metrics.failed = True
                metrics.error_message = error_message
                metrics.total_duration = time.time() - metrics.start_time

                # Move to failed streams
                self._failed_streams.append(metrics)

                # Track error
                self._metrics[MetricType.ERRORS][endpoint].add()

                # Remove from active
                del self._streaming_metrics[stream_id]

    def get_active_streams(self) -> int:
        """Get count of currently active streams."""
        with self._streaming_lock:
            return len(self._streaming_metrics)

    def get_streaming_stats(self) -> Dict[str, Any]:
        """Get aggregate streaming statistics."""
        with self._streaming_lock:
            active_count = len(self._streaming_metrics)

            # Calculate TTFT stats from completed streams
            ttfts = [s.calculate_ttft() for s in self._completed_streams if s.calculate_ttft() is not None]
            tokens_per_sec = [s.calculate_tokens_per_second() for s in self._completed_streams if s.calculate_tokens_per_second() is not None]

            ttft_stats = {}
            if ttfts:
                ttfts.sort()
                n = len(ttfts)
                ttft_stats = {
                    "avg": sum(ttfts) / n,
                    "min": ttfts[0],
                    "max": ttfts[-1],
                    "p50": ttfts[n // 2],
                    "p90": ttfts[int(n * 0.9)],
                    "p99": ttfts[int(n * 0.99)],
                }

            tps_stats = {}
            if tokens_per_sec:
                tokens_per_sec.sort()
                n = len(tokens_per_sec)
                tps_stats = {
                    "avg": sum(tokens_per_sec) / n,
                    "min": tokens_per_sec[0],
                    "max": tokens_per_sec[-1],
                    "p50": tokens_per_sec[n // 2],
                    "p90": tokens_per_sec[int(n * 0.9)],
                    "p99": tokens_per_sec[int(n * 0.99)],
                }

            return {
                "active_streams": active_count,
                "completed_streams": len(self._completed_streams),
                "failed_streams": len(self._failed_streams),
                "ttft": ttft_stats,
                "tokens_per_second": tps_stats,
            }
    
    def get_metrics(self) -> Dict[str, Dict[str, Dict[str, float]] | Dict[str, Any]]:
        """Get all current metrics."""
        result = {}
        for metric_type in MetricType:
            type_name = metric_type.value
            result[type_name] = {}

            for endpoint, window in self._metrics[metric_type].items():
                result[type_name][endpoint] = window.get_stats()

        # Add streaming statistics
        result["streaming_stats"] = self.get_streaming_stats()

        return result

    def get_prometheus_metrics(self) -> str:
        """
        Export metrics in Prometheus format.

        Returns:
            String containing Prometheus-formatted metrics
        """
        lines = []

        # Request rate metrics
        lines.append("# HELP fakeai_requests_per_second Request rate per endpoint")
        lines.append("# TYPE fakeai_requests_per_second gauge")
        for endpoint, window in self._metrics[MetricType.REQUESTS].items():
            stats = window.get_stats()
            lines.append(f'fakeai_requests_per_second{{endpoint="{endpoint}"}} {stats["rate"]:.6f}')

        # Response metrics
        lines.append("# HELP fakeai_responses_per_second Response rate per endpoint")
        lines.append("# TYPE fakeai_responses_per_second gauge")
        for endpoint, window in self._metrics[MetricType.RESPONSES].items():
            stats = window.get_stats()
            lines.append(f'fakeai_responses_per_second{{endpoint="{endpoint}"}} {stats["rate"]:.6f}')

        # Latency metrics
        lines.append("# HELP fakeai_latency_seconds Response latency in seconds")
        lines.append("# TYPE fakeai_latency_seconds summary")
        for endpoint, window in self._metrics[MetricType.RESPONSES].items():
            stats = window.get_latency_stats()
            if stats["avg"] > 0:
                lines.append(f'fakeai_latency_seconds{{endpoint="{endpoint}",quantile="0.5"}} {stats["p50"]:.6f}')
                lines.append(f'fakeai_latency_seconds{{endpoint="{endpoint}",quantile="0.9"}} {stats["p90"]:.6f}')
                lines.append(f'fakeai_latency_seconds{{endpoint="{endpoint}",quantile="0.99"}} {stats["p99"]:.6f}')
                lines.append(f'fakeai_latency_seconds_sum{{endpoint="{endpoint}"}} {stats["avg"] * stats["rate"]:.6f}')

        # Token metrics
        lines.append("# HELP fakeai_tokens_per_second Token generation rate per endpoint")
        lines.append("# TYPE fakeai_tokens_per_second gauge")
        for endpoint, window in self._metrics[MetricType.TOKENS].items():
            stats = window.get_stats()
            lines.append(f'fakeai_tokens_per_second{{endpoint="{endpoint}"}} {stats["rate"]:.6f}')

        # Error metrics
        lines.append("# HELP fakeai_errors_per_second Error rate per endpoint")
        lines.append("# TYPE fakeai_errors_per_second gauge")
        for endpoint, window in self._metrics[MetricType.ERRORS].items():
            stats = window.get_stats()
            if stats["rate"] > 0:
                lines.append(f'fakeai_errors_per_second{{endpoint="{endpoint}"}} {stats["rate"]:.6f}')

        # Streaming metrics
        streaming_stats = self.get_streaming_stats()
        lines.append("# HELP fakeai_active_streams Number of currently active streams")
        lines.append("# TYPE fakeai_active_streams gauge")
        lines.append(f'fakeai_active_streams {streaming_stats.get("active_streams", 0)}')

        lines.append("# HELP fakeai_completed_streams Total completed streams")
        lines.append("# TYPE fakeai_completed_streams gauge")
        lines.append(f'fakeai_completed_streams {streaming_stats.get("completed_streams", 0)}')

        lines.append("# HELP fakeai_failed_streams Total failed streams")
        lines.append("# TYPE fakeai_failed_streams gauge")
        lines.append(f'fakeai_failed_streams {streaming_stats.get("failed_streams", 0)}')

        # TTFT metrics
        ttft = streaming_stats.get("ttft", {})
        if ttft:
            lines.append("# HELP fakeai_ttft_seconds Time to first token in seconds")
            lines.append("# TYPE fakeai_ttft_seconds summary")
            lines.append(f'fakeai_ttft_seconds{{quantile="0.5"}} {ttft["p50"]:.6f}')
            lines.append(f'fakeai_ttft_seconds{{quantile="0.9"}} {ttft["p90"]:.6f}')
            lines.append(f'fakeai_ttft_seconds{{quantile="0.99"}} {ttft["p99"]:.6f}')

        # Tokens per second streaming metrics
        tps = streaming_stats.get("tokens_per_second", {})
        if tps:
            lines.append("# HELP fakeai_stream_tokens_per_second Streaming tokens per second")
            lines.append("# TYPE fakeai_stream_tokens_per_second summary")
            lines.append(f'fakeai_stream_tokens_per_second{{quantile="0.5"}} {tps["p50"]:.6f}')
            lines.append(f'fakeai_stream_tokens_per_second{{quantile="0.9"}} {tps["p90"]:.6f}')
            lines.append(f'fakeai_stream_tokens_per_second{{quantile="0.99"}} {tps["p99"]:.6f}')

        return "\n".join(lines) + "\n"

    def get_csv_metrics(self) -> str:
        """
        Export metrics in CSV format.

        Returns:
            String containing CSV-formatted metrics
        """
        import csv
        import io

        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow([
            "metric_type", "endpoint", "rate", "avg_latency", "min_latency",
            "max_latency", "p50_latency", "p90_latency", "p99_latency"
        ])

        # Write request metrics
        for endpoint, window in self._metrics[MetricType.REQUESTS].items():
            stats = window.get_stats()
            writer.writerow([
                "requests", endpoint, stats["rate"],
                stats["avg"], stats["min"], stats["max"],
                stats["p50"], stats["p90"], stats["p99"]
            ])

        # Write response metrics
        for endpoint, window in self._metrics[MetricType.RESPONSES].items():
            stats = window.get_stats()
            writer.writerow([
                "responses", endpoint, stats["rate"],
                stats["avg"], stats["min"], stats["max"],
                stats["p50"], stats["p90"], stats["p99"]
            ])

        # Write token metrics
        for endpoint, window in self._metrics[MetricType.TOKENS].items():
            stats = window.get_stats()
            writer.writerow([
                "tokens", endpoint, stats["rate"],
                stats["avg"], stats["min"], stats["max"],
                stats["p50"], stats["p90"], stats["p99"]
            ])

        # Write error metrics
        for endpoint, window in self._metrics[MetricType.ERRORS].items():
            stats = window.get_stats()
            if stats["rate"] > 0:
                writer.writerow([
                    "errors", endpoint, stats["rate"],
                    stats["avg"], stats["min"], stats["max"],
                    stats["p50"], stats["p90"], stats["p99"]
                ])

        return output.getvalue()

    def get_detailed_health(self) -> Dict[str, Any]:
        """
        Get detailed health information including metrics summary.

        Returns:
            Dictionary containing health status and metrics
        """
        metrics = self.get_metrics()

        # Calculate overall health
        total_requests = sum(
            stats["rate"]
            for stats in metrics.get("requests", {}).values()
        )
        total_errors = sum(
            stats["rate"]
            for stats in metrics.get("errors", {}).values()
        )

        error_rate = (total_errors / total_requests * 100) if total_requests > 0 else 0

        # Determine health status
        if error_rate > 10:
            status = "unhealthy"
        elif error_rate > 5:
            status = "degraded"
        else:
            status = "healthy"

        # Calculate average latency
        response_metrics = metrics.get("responses", {})
        if response_metrics:
            avg_latencies = [stats["avg"] for stats in response_metrics.values() if stats["avg"] > 0]
            avg_latency = sum(avg_latencies) / len(avg_latencies) if avg_latencies else 0
        else:
            avg_latency = 0

        return {
            "status": status,
            "timestamp": time.time(),
            "uptime_seconds": time.time() - (self._metrics[MetricType.REQUESTS]["/health"].data.get(min(self._metrics[MetricType.REQUESTS]["/health"].data.keys()), 0) if self._metrics[MetricType.REQUESTS].get("/health") and self._metrics[MetricType.REQUESTS]["/health"].data else time.time()),
            "metrics_summary": {
                "total_requests_per_second": total_requests,
                "total_errors_per_second": total_errors,
                "error_rate_percentage": round(error_rate, 2),
                "average_latency_seconds": round(avg_latency, 3),
                "active_streams": metrics.get("streaming_stats", {}).get("active_streams", 0),
            },
            "endpoints": {
                endpoint: {
                    "requests_per_second": stats["rate"],
                    "latency_p50_ms": round(stats["p50"] * 1000, 2),
                    "latency_p99_ms": round(stats["p99"] * 1000, 2),
                }
                for endpoint, stats in metrics.get("responses", {}).items()
                if stats["rate"] > 0
            }
        }
    
    def _print_metrics_periodically(self) -> None:
        """Print metrics periodically in a background thread."""
        while not self._stop_thread:
            time.sleep(self._print_interval)
            self._print_current_metrics()
    
    def _print_current_metrics(self) -> None:
        """Print the current metrics to the log."""
        metrics = self.get_metrics()
        
        # Only log if we have data
        if not metrics.get("requests") and not metrics.get("responses"):
            return
        
        log_lines = ["SERVER METRICS:"]
        
        # Format requests per second
        if "requests" in metrics:
            for endpoint, stats in metrics["requests"].items():
                if stats["rate"] > 0:
                    log_lines.append(f"  Requests/sec [{endpoint}]: {stats['rate']:.2f}")
        
        # Format responses per second
        if "responses" in metrics:
            for endpoint, stats in metrics["responses"].items():
                if stats["rate"] > 0:
                    log_line = f"  Responses/sec [{endpoint}]: {stats['rate']:.2f}"
                    
                    # Add latency stats if available
                    if "avg" in stats:
                        log_line += f" (avg: {stats['avg'] * 1000:.2f}ms, p99: {stats['p99'] * 1000:.2f}ms)"
                    
                    log_lines.append(log_line)
        
        # Format tokens per second
        if "tokens" in metrics:
            for endpoint, stats in metrics["tokens"].items():
                if stats["rate"] > 0:
                    log_lines.append(f"  Tokens/sec [{endpoint}]: {stats['rate']:.2f}")
        
        # Format errors per second
        if "errors" in metrics:
            for endpoint, stats in metrics["errors"].items():
                if stats["rate"] > 0:
                    log_lines.append(f"  Errors/sec [{endpoint}]: {stats['rate']:.2f}")

        # Format streaming statistics
        streaming_stats = metrics.get("streaming_stats", {})
        if streaming_stats.get("active_streams", 0) > 0 or streaming_stats.get("completed_streams", 0) > 0:
            log_lines.append(f"  Active streams: {streaming_stats.get('active_streams', 0)}")
            log_lines.append(f"  Completed streams: {streaming_stats.get('completed_streams', 0)}")
            log_lines.append(f"  Failed streams: {streaming_stats.get('failed_streams', 0)}")

            ttft = streaming_stats.get("ttft", {})
            if ttft:
                log_lines.append(f"  TTFT (ms): avg={ttft['avg']*1000:.2f}, p50={ttft['p50']*1000:.2f}, p99={ttft['p99']*1000:.2f}")

            tps = streaming_stats.get("tokens_per_second", {})
            if tps:
                log_lines.append(f"  Tokens/sec: avg={tps['avg']:.2f}, p50={tps['p50']:.2f}, p99={tps['p99']:.2f}")

        if len(log_lines) > 1:  # Only log if we have metrics beyond the header
            logger.info("\n".join(log_lines))
    
    def shutdown(self) -> None:
        """Stop the background thread."""
        self._stop_thread = True
        if self._thread.is_alive():
            self._thread.join(timeout=1.0)
