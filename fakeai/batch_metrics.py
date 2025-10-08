#!/usr/bin/env python3
"""
FakeAI Batch Processing Metrics Module

This module provides detailed metrics tracking for batch API processing,
including lifecycle metrics, request-level statistics, throughput metrics,
and resource usage tracking.
"""
# SPDX-License-Identifier: Apache-2.0

import logging
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class BatchLifecycleMetrics:
    """Metrics for a single batch's lifecycle."""

    batch_id: str
    total_requests: int
    start_time: float = field(default_factory=time.time)

    # Lifecycle timestamps
    validation_start: float | None = None
    validation_end: float | None = None
    queue_start: float | None = None
    queue_end: float | None = None
    processing_start: float | None = None
    processing_end: float | None = None
    finalization_start: float | None = None
    finalization_end: float | None = None
    completion_time: float | None = None

    # Request processing metrics
    requests_processed: int = 0
    requests_succeeded: int = 0
    requests_failed: int = 0

    # Request-level timing (milliseconds)
    request_latencies: list[float] = field(default_factory=list)

    # Token usage per request
    request_token_counts: list[int] = field(default_factory=list)

    # Error categorization
    error_types: dict[str, int] = field(
        default_factory=lambda: defaultdict(int))

    # Resource metrics (simulated)
    peak_memory_mb: float = 0.0
    total_bytes_written: int = 0
    total_bytes_read: int = 0
    network_bandwidth_mbps: float = 0.0

    def calculate_validation_time(self) -> float:
        """Calculate validation duration in seconds."""
        if self.validation_start and self.validation_end:
            return self.validation_end - self.validation_start
        return 0.0

    def calculate_queue_time(self) -> float:
        """Calculate queue waiting time in seconds."""
        if self.queue_start and self.queue_end:
            return self.queue_end - self.queue_start
        return 0.0

    def calculate_processing_time(self) -> float:
        """Calculate total processing time in seconds."""
        if self.processing_start and self.processing_end:
            return self.processing_end - self.processing_start
        return 0.0

    def calculate_finalization_time(self) -> float:
        """Calculate finalization time in seconds."""
        if self.finalization_start and self.finalization_end:
            return self.finalization_end - self.finalization_start
        return 0.0

    def calculate_total_duration(self) -> float:
        """Calculate total batch duration in seconds."""
        if self.completion_time:
            return self.completion_time - self.start_time
        return time.time() - self.start_time

    def calculate_requests_per_second(self) -> float:
        """Calculate RPS during processing phase."""
        processing_time = self.calculate_processing_time()
        if processing_time > 0 and self.requests_processed > 0:
            return self.requests_processed / processing_time
        return 0.0

    def calculate_tokens_per_second(self) -> float:
        """Calculate TPS during processing phase."""
        processing_time = self.calculate_processing_time()
        total_tokens = sum(self.request_token_counts)
        if processing_time > 0 and total_tokens > 0:
            return total_tokens / processing_time
        return 0.0

    def calculate_success_rate(self) -> float:
        """Calculate request success rate as percentage."""
        if self.requests_processed > 0:
            return (self.requests_succeeded / self.requests_processed) * 100
        return 0.0

    def get_latency_percentiles(self) -> dict[str, float]:
        """Calculate latency percentiles in milliseconds."""
        if not self.request_latencies:
            return {
                "min": 0.0,
                "max": 0.0,
                "avg": 0.0,
                "p50": 0.0,
                "p90": 0.0,
                "p95": 0.0,
                "p99": 0.0,
            }

        latencies = np.array(self.request_latencies)
        return {
            "min": float(np.min(latencies)),
            "max": float(np.max(latencies)),
            "avg": float(np.mean(latencies)),
            "p50": float(np.percentile(latencies, 50)),
            "p90": float(np.percentile(latencies, 90)),
            "p95": float(np.percentile(latencies, 95)),
            "p99": float(np.percentile(latencies, 99)),
        }

    def get_token_statistics(self) -> dict[str, float]:
        """Calculate token usage statistics."""
        if not self.request_token_counts:
            return {
                "total": 0,
                "min": 0,
                "max": 0,
                "avg": 0.0,
                "p50": 0.0,
                "p90": 0.0,
            }

        tokens = np.array(self.request_token_counts)
        return {
            "total": int(np.sum(tokens)),
            "min": int(np.min(tokens)),
            "max": int(np.max(tokens)),
            "avg": float(np.mean(tokens)),
            "p50": float(np.percentile(tokens, 50)),
            "p90": float(np.percentile(tokens, 90)),
        }

    def calculate_batch_efficiency(self) -> float:
        """
        Calculate batch efficiency vs sequential processing.

        Estimates how much faster batch processing was compared to
        sequential processing with typical overhead.
        Returns efficiency as a ratio (e.g., 2.5 means 2.5x faster).
        """
        if not self.request_latencies:
            return 1.0

        # Estimate sequential time: sum of all latencies + overhead per request
        sequential_overhead_ms = 50  # Network + setup overhead per request
        estimated_sequential_time = sum(self.request_latencies) + (
            len(self.request_latencies) * sequential_overhead_ms
        )

        # Actual batch processing time
        actual_time_ms = self.calculate_processing_time() * 1000

        if actual_time_ms > 0:
            return estimated_sequential_time / actual_time_ms
        return 1.0


class BatchMetricsTracker:
    """
    Tracks detailed metrics for batch processing operations.

    This class provides comprehensive metrics tracking for the batch API,
    including lifecycle timing, request-level statistics, throughput metrics,
    and resource usage. It maintains both active and completed batch metrics
    and provides aggregate statistics across all batches.

    Thread-safe for concurrent batch processing.
    """

    def __init__(self):
        """Initialize the batch metrics tracker."""
        self._active_batches: dict[str, BatchLifecycleMetrics] = {}
        self._completed_batches: deque[BatchLifecycleMetrics] = deque(
            maxlen=1000)
        self._lock = threading.Lock()

        # Aggregate statistics
        self._total_batches_started = 0
        self._total_batches_completed = 0
        self._total_batches_failed = 0
        self._total_requests_processed = 0
        self._total_tokens_processed = 0

        logger.info("Batch metrics tracker initialized")

    def start_batch(self, batch_id: str, total_requests: int) -> None:
        """
        Start tracking a new batch.

        Args:
            batch_id: Unique identifier for the batch
            total_requests: Total number of requests in the batch
        """
        with self._lock:
            metrics = BatchLifecycleMetrics(
                batch_id=batch_id,
                total_requests=total_requests,
            )
            metrics.validation_start = time.time()
            self._active_batches[batch_id] = metrics
            self._total_batches_started += 1

        logger.debug(
            f"Started tracking batch {batch_id} with {total_requests} requests"
        )

    def record_validation_complete(self, batch_id: str) -> None:
        """
        Record that batch validation is complete.

        Args:
            batch_id: Batch identifier
        """
        with self._lock:
            if batch_id in self._active_batches:
                metrics = self._active_batches[batch_id]
                metrics.validation_end = time.time()
                metrics.queue_start = time.time()

    def record_processing_start(self, batch_id: str) -> None:
        """
        Record that batch processing has started.

        Args:
            batch_id: Batch identifier
        """
        with self._lock:
            if batch_id in self._active_batches:
                metrics = self._active_batches[batch_id]
                metrics.queue_end = time.time()
                metrics.processing_start = time.time()

    def record_request_processed(
        self,
        batch_id: str,
        request_num: int,
        latency_ms: float,
        tokens: int,
        success: bool,
        error_type: str | None = None,
    ) -> None:
        """
        Record a processed request within a batch.

        Args:
            batch_id: Batch identifier
            request_num: Request number/index in batch
            latency_ms: Request processing latency in milliseconds
            tokens: Number of tokens processed
            success: Whether request succeeded
            error_type: Error type if request failed
        """
        with self._lock:
            if batch_id not in self._active_batches:
                return

            metrics = self._active_batches[batch_id]
            metrics.requests_processed += 1
            metrics.request_latencies.append(latency_ms)
            metrics.request_token_counts.append(tokens)

            if success:
                metrics.requests_succeeded += 1
            else:
                metrics.requests_failed += 1
                if error_type:
                    metrics.error_types[error_type] += 1

            self._total_requests_processed += 1
            self._total_tokens_processed += tokens

    def record_processing_complete(self, batch_id: str) -> None:
        """
        Record that batch processing phase is complete.

        Args:
            batch_id: Batch identifier
        """
        with self._lock:
            if batch_id in self._active_batches:
                metrics = self._active_batches[batch_id]
                metrics.processing_end = time.time()
                metrics.finalization_start = time.time()

    def record_finalization_complete(self, batch_id: str) -> None:
        """
        Record that batch finalization is complete.

        Args:
            batch_id: Batch identifier
        """
        with self._lock:
            if batch_id in self._active_batches:
                metrics = self._active_batches[batch_id]
                metrics.finalization_end = time.time()

    def complete_batch(
        self,
        batch_id: str,
        bytes_written: int = 0,
        bytes_read: int = 0,
    ) -> None:
        """
        Mark batch as completed and calculate final statistics.

        Args:
            batch_id: Batch identifier
            bytes_written: Total bytes written (output files)
            bytes_read: Total bytes read (input files)
        """
        with self._lock:
            if batch_id not in self._active_batches:
                logger.warning(
                    f"Attempted to complete unknown batch: {batch_id}")
                return

            metrics = self._active_batches[batch_id]
            metrics.completion_time = time.time()
            metrics.total_bytes_written = bytes_written
            metrics.total_bytes_read = bytes_read

            # Simulate resource metrics
            metrics.peak_memory_mb = self._simulate_memory_usage(
                metrics.total_requests)
            metrics.network_bandwidth_mbps = self._simulate_bandwidth(
                bytes_written + bytes_read, metrics.calculate_total_duration()
            )

            # Move to completed batches
            self._completed_batches.append(metrics)
            del self._active_batches[batch_id]
            self._total_batches_completed += 1

        logger.info(
            f"Batch {batch_id} completed: {
                metrics.requests_succeeded} succeeded, " f"{
                metrics.requests_failed} failed, " f"{
                metrics.calculate_total_duration():.2f}s total")

    def fail_batch(self, batch_id: str, error_message: str) -> None:
        """
        Mark batch as failed.

        Args:
            batch_id: Batch identifier
            error_message: Error message describing failure
        """
        with self._lock:
            if batch_id in self._active_batches:
                metrics = self._active_batches[batch_id]
                metrics.completion_time = time.time()
                metrics.error_types["batch_failure"] += 1

                # Move to completed (even though failed)
                self._completed_batches.append(metrics)
                del self._active_batches[batch_id]
                self._total_batches_failed += 1

        logger.error(f"Batch {batch_id} failed: {error_message}")

    def get_batch_stats(self, batch_id: str) -> dict[str, Any] | None:
        """
        Get statistics for a specific batch.

        Args:
            batch_id: Batch identifier

        Returns:
            Dictionary containing batch statistics, or None if not found
        """
        with self._lock:
            # Check active batches
            if batch_id in self._active_batches:
                metrics = self._active_batches[batch_id]
                return self._format_batch_stats(metrics, active=True)

            # Check completed batches
            for metrics in self._completed_batches:
                if metrics.batch_id == batch_id:
                    return self._format_batch_stats(metrics, active=False)

        return None

    def get_all_batches_stats(self) -> dict[str, Any]:
        """
        Get aggregate statistics for all batches.

        Returns:
            Dictionary containing aggregate statistics across all batches
        """
        with self._lock:
            # Aggregate metrics from completed batches
            all_latencies = []
            all_tokens = []
            all_durations = []
            all_rps = []
            all_tps = []
            all_efficiencies = []
            total_errors_by_type = defaultdict(int)

            for metrics in self._completed_batches:
                all_latencies.extend(metrics.request_latencies)
                all_tokens.extend(metrics.request_token_counts)
                all_durations.append(metrics.calculate_total_duration())
                all_rps.append(metrics.calculate_requests_per_second())
                all_tps.append(metrics.calculate_tokens_per_second())
                all_efficiencies.append(metrics.calculate_batch_efficiency())

                for error_type, count in metrics.error_types.items():
                    total_errors_by_type[error_type] += count

            # Calculate aggregate statistics
            latency_stats = self._calculate_array_stats(
                all_latencies, "Latency (ms)")
            token_stats = self._calculate_array_stats(
                all_tokens, "Tokens per request")
            duration_stats = self._calculate_array_stats(
                all_durations, "Batch duration (s)"
            )
            rps_stats = self._calculate_array_stats(all_rps, "Requests/sec")
            tps_stats = self._calculate_array_stats(all_tps, "Tokens/sec")
            efficiency_stats = self._calculate_array_stats(
                all_efficiencies, "Batch efficiency"
            )

            return {
                "summary": {
                    "total_batches_started": self._total_batches_started,
                    "total_batches_completed": self._total_batches_completed,
                    "total_batches_failed": self._total_batches_failed,
                    "active_batches": len(self._active_batches),
                    "total_requests_processed": self._total_requests_processed,
                    "total_tokens_processed": self._total_tokens_processed,
                },
                "latency": latency_stats,
                "tokens": token_stats,
                "duration": duration_stats,
                "throughput": {
                    "requests_per_second": rps_stats,
                    "tokens_per_second": tps_stats,
                },
                "efficiency": efficiency_stats,
                "errors": {
                    "by_type": dict(total_errors_by_type),
                    "total": sum(total_errors_by_type.values()),
                },
                "active_batches_detail": [
                    {
                        "batch_id": metrics.batch_id,
                        "total_requests": metrics.total_requests,
                        "requests_processed": metrics.requests_processed,
                        "elapsed_time": time.time() - metrics.start_time,
                    }
                    for metrics in self._active_batches.values()
                ],
            }

    def _format_batch_stats(
        self, metrics: BatchLifecycleMetrics, active: bool
    ) -> dict[str, Any]:
        """
        Format batch metrics into a statistics dictionary.

        Args:
            metrics: Batch metrics to format
            active: Whether batch is still active

        Returns:
            Formatted statistics dictionary
        """
        return {
            "batch_id": metrics.batch_id,
            "status": "active" if active else "completed",
            "lifecycle": {
                "validation_time_ms": metrics.calculate_validation_time() * 1000,
                "queue_time_ms": metrics.calculate_queue_time() * 1000,
                "processing_time_ms": metrics.calculate_processing_time() * 1000,
                "finalization_time_ms": metrics.calculate_finalization_time() * 1000,
                "total_duration_ms": metrics.calculate_total_duration() * 1000,
            },
            "requests": {
                "total": metrics.total_requests,
                "processed": metrics.requests_processed,
                "succeeded": metrics.requests_succeeded,
                "failed": metrics.requests_failed,
                "success_rate_pct": metrics.calculate_success_rate(),
            },
            "latency": metrics.get_latency_percentiles(),
            "tokens": metrics.get_token_statistics(),
            "throughput": {
                "requests_per_second": metrics.calculate_requests_per_second(),
                "tokens_per_second": metrics.calculate_tokens_per_second(),
            },
            "efficiency": {
                "batch_vs_sequential": metrics.calculate_batch_efficiency(),
            },
            "resources": {
                "peak_memory_mb": metrics.peak_memory_mb,
                "bytes_read": metrics.total_bytes_read,
                "bytes_written": metrics.total_bytes_written,
                "network_bandwidth_mbps": metrics.network_bandwidth_mbps,
            },
            "errors": {
                "by_type": dict(
                    metrics.error_types),
                "total": sum(
                    metrics.error_types.values()),
            },
        }

    def _calculate_array_stats(
        self, values: list[float], label: str
    ) -> dict[str, float]:
        """
        Calculate statistics for an array of values.

        Args:
            values: List of numeric values
            label: Label for the statistics

        Returns:
            Dictionary of statistics
        """
        if not values:
            return {
                "count": 0,
                "min": 0.0,
                "max": 0.0,
                "avg": 0.0,
                "p50": 0.0,
                "p90": 0.0,
                "p95": 0.0,
                "p99": 0.0,
            }

        arr = np.array(values)
        return {
            "count": len(values),
            "min": float(np.min(arr)),
            "max": float(np.max(arr)),
            "avg": float(np.mean(arr)),
            "p50": float(np.percentile(arr, 50)),
            "p90": float(np.percentile(arr, 90)),
            "p95": float(np.percentile(arr, 95)),
            "p99": float(np.percentile(arr, 99)),
        }

    def _simulate_memory_usage(self, num_requests: int) -> float:
        """
        Simulate peak memory usage based on batch size.

        Args:
            num_requests: Number of requests in batch

        Returns:
            Simulated peak memory in MB
        """
        # Baseline memory + per-request overhead
        baseline_mb = 50.0
        per_request_mb = 2.5
        return baseline_mb + (num_requests * per_request_mb)

    def _simulate_bandwidth(
            self,
            total_bytes: int,
            duration_seconds: float) -> float:
        """
        Simulate network bandwidth usage.

        Args:
            total_bytes: Total bytes transferred
            duration_seconds: Time period in seconds

        Returns:
            Simulated bandwidth in Mbps
        """
        if duration_seconds <= 0:
            return 0.0

        # Convert bytes to megabits
        megabits = (total_bytes * 8) / 1_000_000
        return megabits / duration_seconds

    def reset(self) -> None:
        """Reset all metrics (useful for testing)."""
        with self._lock:
            self._active_batches.clear()
            self._completed_batches.clear()
            self._total_batches_started = 0
            self._total_batches_completed = 0
            self._total_batches_failed = 0
            self._total_requests_processed = 0
            self._total_tokens_processed = 0

        logger.info("Batch metrics tracker reset")
