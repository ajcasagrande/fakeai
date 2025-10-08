"""
NVIDIA AI-Dynamo Advanced Metrics - Production-Grade Implementation.

Extreme granularity metrics matching production NVIDIA Dynamo systems:
- Request lifecycle phase tracking with microsecond precision
- Multi-tier queue management with priority-based scheduling
- Dynamic batch optimization with padding efficiency
- Disaggregation metrics for prefill/decode separation
- Model-specific performance profiling
- Advanced analytics with long-tail analysis
"""

import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class RequestPriority(Enum):
    """Request priority levels."""

    CRITICAL = 0  # P0: Interactive, latency-sensitive
    HIGH = 1  # P1: Production workloads
    NORMAL = 2  # P2: Standard requests
    LOW = 3  # P3: Batch processing
    BACKGROUND = 4  # P4: Best-effort


class QueuePhase(Enum):
    """Queue phases in request lifecycle."""

    SCHEDULER_QUEUE = "scheduler_queue"  # Global scheduler queue
    WORKER_QUEUE = "worker_queue"  # Worker-specific queue
    PROCESSING = "processing"  # Active processing


@dataclass
class AdvancedRequestMetrics:
    """
    Comprehensive request lifecycle metrics with extreme granularity.

    Tracks every phase of request processing with microsecond precision.
    """

    request_id: str
    model: str
    endpoint: str
    priority: RequestPriority = RequestPriority.NORMAL

    # Timestamps (all in seconds since epoch)
    arrival_time: float = 0.0

    # Queue phases
    scheduler_queue_entry_time: float = 0.0
    scheduler_queue_exit_time: float = 0.0
    worker_queue_entry_time: float = 0.0
    worker_queue_exit_time: float = 0.0

    # Router decision
    router_decision_start_time: float = 0.0
    router_decision_end_time: float = 0.0

    # KV cache lookup
    kv_cache_lookup_start_time: float = 0.0
    kv_cache_lookup_end_time: float = 0.0

    # Processing phases
    prefill_start_time: float = 0.0
    prefill_end_time: float = 0.0
    first_token_time: float = 0.0
    decode_start_time: float = 0.0
    decode_end_time: float = 0.0

    # KV cache write-back
    kv_writeback_start_time: float = 0.0
    kv_writeback_end_time: float = 0.0

    # Network transfer
    network_transfer_start_time: float = 0.0
    network_transfer_end_time: float = 0.0

    completion_time: float = 0.0

    # Token counts
    input_tokens: int = 0
    output_tokens: int = 0
    cached_tokens: int = 0

    # Derived timing metrics (calculated)
    router_decision_time_us: float = 0.0
    scheduler_queue_time_ms: float = 0.0
    worker_queue_time_ms: float = 0.0
    total_queue_time_ms: float = 0.0
    kv_cache_lookup_time_us: float = 0.0
    prefill_time_ms: float = 0.0
    first_token_generation_time_ms: float = 0.0
    decode_time_ms: float = 0.0
    decode_time_per_token_ms: float = 0.0
    kv_writeback_time_us: float = 0.0
    network_transfer_time_ms: float = 0.0
    total_time_ms: float = 0.0

    # KV cache metrics
    kv_cache_hit: bool = False
    kv_cache_blocks_matched: int = 0
    kv_cache_overlap_score: float = 0.0

    # Disaggregation metrics
    is_prefill_worker: bool = True
    is_decode_worker: bool = False
    kv_transfer_bytes: int = 0
    disaggregation_overhead_us: float = 0.0

    # Batch metrics
    batch_id: str = ""
    batch_size: int = 1
    batch_position: int = 0
    padding_tokens: int = 0

    # Worker assignment
    worker_id: str = ""
    routing_cost: float = 0.0
    worker_active_requests: int = 0

    # Status
    success: bool = True
    finish_reason: str = "stop"
    timeout: bool = False
    queue_rejected: bool = False

    def calculate_derived_metrics(self):
        """Calculate all derived timing metrics with microsecond precision."""
        # Router decision time
        if self.router_decision_start_time > 0 and self.router_decision_end_time > 0:
            self.router_decision_time_us = (
                self.router_decision_end_time - self.router_decision_start_time
            ) * 1_000_000

        # Scheduler queue time
        if self.scheduler_queue_entry_time > 0 and self.scheduler_queue_exit_time > 0:
            self.scheduler_queue_time_ms = (
                self.scheduler_queue_exit_time - self.scheduler_queue_entry_time) * 1000

        # Worker queue time
        if self.worker_queue_entry_time > 0 and self.worker_queue_exit_time > 0:
            self.worker_queue_time_ms = (
                self.worker_queue_exit_time - self.worker_queue_entry_time
            ) * 1000

        # Total queue time
        self.total_queue_time_ms = (
            self.scheduler_queue_time_ms + self.worker_queue_time_ms
        )

        # KV cache lookup time
        if self.kv_cache_lookup_start_time > 0 and self.kv_cache_lookup_end_time > 0:
            self.kv_cache_lookup_time_us = (
                self.kv_cache_lookup_end_time - self.kv_cache_lookup_start_time
            ) * 1_000_000

        # Prefill time
        if self.prefill_start_time > 0 and self.prefill_end_time > 0:
            self.prefill_time_ms = (
                self.prefill_end_time - self.prefill_start_time
            ) * 1000

        # First token generation time (prefill + first decode)
        if self.prefill_start_time > 0 and self.first_token_time > 0:
            self.first_token_generation_time_ms = (
                self.first_token_time - self.prefill_start_time
            ) * 1000

        # Decode time
        if self.decode_start_time > 0 and self.decode_end_time > 0:
            self.decode_time_ms = (
                self.decode_end_time - self.decode_start_time) * 1000

        # Decode time per token
        if self.output_tokens > 1 and self.decode_time_ms > 0:
            self.decode_time_per_token_ms = self.decode_time_ms / (
                self.output_tokens - 1
            )

        # KV writeback time
        if self.kv_writeback_start_time > 0 and self.kv_writeback_end_time > 0:
            self.kv_writeback_time_us = (
                self.kv_writeback_end_time - self.kv_writeback_start_time
            ) * 1_000_000

        # Network transfer time
        if self.network_transfer_start_time > 0 and self.network_transfer_end_time > 0:
            self.network_transfer_time_ms = (
                self.network_transfer_end_time - self.network_transfer_start_time) * 1000

        # Total time
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
        return self.decode_time_per_token_ms

    @property
    def queue_efficiency(self) -> float:
        """Queue efficiency: processing time / total time."""
        if self.total_time_ms > 0:
            processing_time = self.prefill_time_ms + self.decode_time_ms
            return processing_time / self.total_time_ms
        return 0.0

    @property
    def padding_waste_percentage(self) -> float:
        """Percentage of tokens that are padding."""
        total_batch_tokens = self.batch_size * \
            (self.input_tokens + self.padding_tokens)
        if total_batch_tokens > 0:
            return (self.padding_tokens * self.batch_size /
                    total_batch_tokens) * 100
        return 0.0


@dataclass
class QueueMetrics:
    """Metrics for a single priority queue."""

    priority: RequestPriority
    current_depth: int = 0
    max_depth: int = 0
    total_enqueued: int = 0
    total_dequeued: int = 0
    total_timeouts: int = 0
    total_rejections: int = 0
    depth_history: deque = field(default_factory=lambda: deque(maxlen=1000))
    wait_times_ms: deque = field(default_factory=lambda: deque(maxlen=1000))


class QueueManager:
    """
    Multi-tier queue manager with priority-based scheduling.

    Manages separate queues per priority level with different timeout
    and capacity limits.
    """

    def __init__(
        self,
        max_queue_depth_per_priority: dict[RequestPriority, int] | None = None,
        timeout_per_priority: dict[RequestPriority, float] | None = None,
    ):
        """
        Initialize queue manager.

        Args:
            max_queue_depth_per_priority: Max queue depth for each priority
            timeout_per_priority: Timeout in seconds for each priority
        """
        # Default limits
        self.max_queue_depth = max_queue_depth_per_priority or {
            RequestPriority.CRITICAL: 100,
            RequestPriority.HIGH: 500,
            RequestPriority.NORMAL: 1000,
            RequestPriority.LOW: 2000,
            RequestPriority.BACKGROUND: 5000,
        }

        self.timeout_limits = timeout_per_priority or {
            RequestPriority.CRITICAL: 1.0,  # 1s
            RequestPriority.HIGH: 5.0,  # 5s
            RequestPriority.NORMAL: 30.0,  # 30s
            RequestPriority.LOW: 120.0,  # 2m
            RequestPriority.BACKGROUND: 600.0,  # 10m
        }

        # Per-priority queues
        self.queues: dict[RequestPriority, QueueMetrics] = {
            priority: QueueMetrics(priority=priority) for priority in RequestPriority
        }

        self._lock = threading.RLock()  # Reentrant lock to allow nested locking

    def enqueue(self, priority: RequestPriority) -> tuple[bool, str]:
        """
        Enqueue a request with given priority.

        Returns:
            (success, reason) - whether enqueue succeeded and reason if failed
        """
        with self._lock:
            queue = self.queues[priority]

            # Check capacity
            max_depth = self.max_queue_depth[priority]
            if queue.current_depth >= max_depth:
                queue.total_rejections += 1
                return (
                    False, f"Queue full (depth={
                        queue.current_depth}, max={max_depth})", )

            # Enqueue
            queue.current_depth += 1
            queue.max_depth = max(queue.max_depth, queue.current_depth)
            queue.total_enqueued += 1
            queue.depth_history.append((time.time(), queue.current_depth))

            return True, "success"

    def dequeue(self, priority: RequestPriority, wait_time_ms: float) -> bool:
        """
        Dequeue a request with given priority.

        Returns:
            success - whether dequeue succeeded
        """
        with self._lock:
            queue = self.queues[priority]

            if queue.current_depth > 0:
                queue.current_depth -= 1
                queue.total_dequeued += 1
                queue.wait_times_ms.append(wait_time_ms)
                return True

            return False

    def timeout_request(self, priority: RequestPriority):
        """Record a timeout for given priority."""
        with self._lock:
            self.queues[priority].total_timeouts += 1

    def get_queue_stats(self, priority: RequestPriority) -> dict[str, Any]:
        """Get statistics for a specific priority queue."""
        with self._lock:
            queue = self.queues[priority]

            return {
                "priority": priority.name,
                "current_depth": queue.current_depth,
                "max_depth": queue.max_depth,
                "total_enqueued": queue.total_enqueued,
                "total_dequeued": queue.total_dequeued,
                "total_timeouts": queue.total_timeouts,
                "total_rejections": queue.total_rejections,
                "timeout_rate": (
                    queue.total_timeouts / queue.total_dequeued * 100
                    if queue.total_dequeued > 0
                    else 0.0
                ),
                "rejection_rate": (
                    queue.total_rejections / queue.total_enqueued * 100
                    if queue.total_enqueued > 0
                    else 0.0
                ),
                "avg_wait_time_ms": (
                    sum(queue.wait_times_ms) / len(queue.wait_times_ms)
                    if queue.wait_times_ms
                    else 0.0
                ),
                "max_wait_time_ms": (
                    max(queue.wait_times_ms) if queue.wait_times_ms else 0.0
                ),
            }

    def get_all_queue_stats(self) -> dict[str, Any]:
        """Get statistics for all priority queues."""
        return {
            priority.name: self.get_queue_stats(priority)
            for priority in RequestPriority
        }


@dataclass
class BatchMetrics:
    """Metrics for a single batch."""

    batch_id: str
    batch_size: int
    total_input_tokens: int
    total_output_tokens: int
    total_padding_tokens: int
    max_input_tokens: int
    min_input_tokens: int
    start_time: float
    end_time: float

    @property
    def padding_waste_percentage(self) -> float:
        """Calculate padding waste percentage."""
        total_tokens = (
            self.total_input_tokens + self.total_padding_tokens
        ) * self.batch_size
        if total_tokens > 0:
            return (self.total_padding_tokens *
                    self.batch_size / total_tokens) * 100
        return 0.0

    @property
    def efficiency_score(self) -> float:
        """
        Batch efficiency score (0-100).

        Higher is better. Considers batch size and padding waste.
        """
        # Penalize padding waste
        padding_penalty = self.padding_waste_percentage / 100

        # Reward larger batches (up to a point)
        size_bonus = min(self.batch_size / 32.0, 1.0)

        return (1.0 - padding_penalty) * size_bonus * 100

    @property
    def processing_time_ms(self) -> float:
        """Total batch processing time in milliseconds."""
        if self.end_time > 0:
            return (self.end_time - self.start_time) * 1000
        return 0.0


class BatchOptimizer:
    """
    Dynamic batch optimization tracker.

    Tracks batch composition, padding efficiency, and optimal batch sizes
    for different request patterns.
    """

    def __init__(self, target_batch_size: int = 32,
                 max_padding_waste: float = 20.0):
        """
        Initialize batch optimizer.

        Args:
            target_batch_size: Target batch size
            max_padding_waste: Maximum acceptable padding waste percentage
        """
        self.target_batch_size = target_batch_size
        self.max_padding_waste = max_padding_waste

        # Batch tracking
        self.active_batches: dict[str, BatchMetrics] = {}
        self.completed_batches: deque[BatchMetrics] = deque(maxlen=1000)

        # Dynamic batch size tracking
        self.batch_sizes: deque[int] = deque(maxlen=1000)
        self.padding_waste_history: deque[float] = deque(maxlen=1000)
        self.efficiency_scores: deque[float] = deque(maxlen=1000)

        self._lock = threading.RLock()  # Reentrant lock to allow nested locking

    def start_batch(
        self,
        batch_id: str,
        batch_size: int,
        input_tokens_per_request: list[int],
    ) -> BatchMetrics:
        """
        Start tracking a new batch.

        Args:
            batch_id: Unique batch identifier
            batch_size: Number of requests in batch
            input_tokens_per_request: Input token count for each request

        Returns:
            BatchMetrics object
        """
        with self._lock:
            max_tokens = max(input_tokens_per_request)
            total_input = sum(input_tokens_per_request)
            total_padding = sum(
                max_tokens - tokens for tokens in input_tokens_per_request
            )

            batch = BatchMetrics(
                batch_id=batch_id,
                batch_size=batch_size,
                total_input_tokens=total_input,
                total_output_tokens=0,
                total_padding_tokens=total_padding,
                max_input_tokens=max_tokens,
                min_input_tokens=min(input_tokens_per_request),
                start_time=time.time(),
                end_time=0.0,
            )

            self.active_batches[batch_id] = batch
            self.batch_sizes.append(batch_size)

            return batch

    def complete_batch(self, batch_id: str, output_tokens: int):
        """
        Mark batch as completed.

        Args:
            batch_id: Unique batch identifier
            output_tokens: Total output tokens generated
        """
        with self._lock:
            if batch_id not in self.active_batches:
                return

            batch = self.active_batches.pop(batch_id)
            batch.end_time = time.time()
            batch.total_output_tokens = output_tokens

            self.completed_batches.append(batch)
            self.padding_waste_history.append(batch.padding_waste_percentage)
            self.efficiency_scores.append(batch.efficiency_score)

    def get_optimal_batch_size(self) -> int:
        """
        Calculate optimal batch size based on recent history.

        Returns:
            Recommended batch size
        """
        with self._lock:
            if not self.completed_batches:
                return self.target_batch_size

            # Find batches with efficiency > threshold
            efficient_batches = [
                b for b in self.completed_batches if b.efficiency_score >= 70.0
            ]

            if not efficient_batches:
                return self.target_batch_size

            # Average size of efficient batches
            avg_size = sum(b.batch_size for b in efficient_batches) / len(
                efficient_batches
            )
            return int(avg_size)

    def get_batch_stats(self) -> dict[str, Any]:
        """Get batch optimization statistics."""
        with self._lock:
            recent_batches = list(self.completed_batches)[-100:]

            if not recent_batches:
                return {
                    "current_active_batches": len(self.active_batches),
                    "avg_batch_size": 0.0,
                    "avg_padding_waste": 0.0,
                    "avg_efficiency_score": 0.0,
                    "optimal_batch_size": self.target_batch_size,
                }

            # Calculate optimal batch size inline to avoid nested lock
            efficient_batches = [
                b for b in self.completed_batches if b.efficiency_score >= 70.0
            ]
            optimal_size = self.target_batch_size
            if efficient_batches:
                avg_size = sum(b.batch_size for b in efficient_batches) / len(
                    efficient_batches
                )
                optimal_size = int(avg_size)

            return {
                "current_active_batches": len(self.active_batches),
                "avg_batch_size": (
                    sum(b.batch_size for b in recent_batches) / len(recent_batches)
                ),
                "min_batch_size": min(b.batch_size for b in recent_batches),
                "max_batch_size": max(b.batch_size for b in recent_batches),
                "avg_padding_waste": (
                    sum(b.padding_waste_percentage for b in recent_batches) /
                    len(recent_batches)
                ),
                "max_padding_waste": max(
                    b.padding_waste_percentage for b in recent_batches
                ),
                "avg_efficiency_score": (
                    sum(b.efficiency_score for b in recent_batches) /
                    len(recent_batches)
                ),
                "optimal_batch_size": optimal_size,
                "total_batches_processed": len(self.completed_batches),
            }


@dataclass
class DisaggregationMetrics:
    """Metrics for prefill/decode disaggregation."""

    prefill_requests: int = 0
    decode_requests: int = 0
    kv_transfer_bytes: int = 0
    kv_transfer_time_ms: float = 0.0
    disaggregation_overhead_us: float = 0.0
    cross_worker_transfers: int = 0


class DisaggregationTracker:
    """
    Tracks prefill/decode disaggregation metrics.

    Monitors KV cache transfers between prefill and decode workers,
    disaggregation overhead, and communication patterns.
    """

    def __init__(self):
        """Initialize disaggregation tracker."""
        # Global metrics
        self.metrics = DisaggregationMetrics()

        # Per-worker metrics
        self.prefill_worker_metrics: dict[str, DisaggregationMetrics] = defaultdict(
            DisaggregationMetrics)
        self.decode_worker_metrics: dict[str, DisaggregationMetrics] = defaultdict(
            DisaggregationMetrics)

        # Transfer tracking
        self.transfer_history: deque[tuple[float, int]] = deque(
            maxlen=1000
        )  # (time, bytes)

        self._lock = threading.RLock()  # Reentrant lock to allow nested locking

    def record_prefill_request(self, worker_id: str, kv_cache_size_bytes: int):
        """
        Record a prefill request.

        Args:
            worker_id: Prefill worker ID
            kv_cache_size_bytes: Size of KV cache generated
        """
        with self._lock:
            self.metrics.prefill_requests += 1
            self.prefill_worker_metrics[worker_id].prefill_requests += 1

            # Track KV cache size for potential transfer
            self.prefill_worker_metrics[
                worker_id
            ].kv_transfer_bytes += kv_cache_size_bytes

    def record_decode_request(self, worker_id: str):
        """
        Record a decode request.

        Args:
            worker_id: Decode worker ID
        """
        with self._lock:
            self.metrics.decode_requests += 1
            self.decode_worker_metrics[worker_id].decode_requests += 1

    def record_kv_transfer(
        self,
        prefill_worker_id: str,
        decode_worker_id: str,
        transfer_bytes: int,
        transfer_time_ms: float,
        overhead_us: float,
    ):
        """
        Record KV cache transfer from prefill to decode worker.

        Args:
            prefill_worker_id: Source prefill worker
            decode_worker_id: Destination decode worker
            transfer_bytes: Number of bytes transferred
            transfer_time_ms: Transfer time in milliseconds
            overhead_us: Disaggregation overhead in microseconds
        """
        with self._lock:
            # Global metrics
            self.metrics.kv_transfer_bytes += transfer_bytes
            self.metrics.kv_transfer_time_ms += transfer_time_ms
            self.metrics.disaggregation_overhead_us += overhead_us
            self.metrics.cross_worker_transfers += 1

            # Per-worker metrics
            self.prefill_worker_metrics[
                prefill_worker_id
            ].kv_transfer_bytes += transfer_bytes
            self.prefill_worker_metrics[
                prefill_worker_id
            ].kv_transfer_time_ms += transfer_time_ms
            self.decode_worker_metrics[
                decode_worker_id
            ].kv_transfer_bytes += transfer_bytes
            self.decode_worker_metrics[
                decode_worker_id
            ].kv_transfer_time_ms += transfer_time_ms

            # Transfer history
            self.transfer_history.append((time.time(), transfer_bytes))

    def get_disaggregation_ratio(self) -> float:
        """
        Calculate prefill/decode disaggregation ratio.

        Returns:
            Ratio of prefill to decode requests
        """
        with self._lock:
            total = self.metrics.prefill_requests + self.metrics.decode_requests
            if total > 0:
                return self.metrics.prefill_requests / total
            return 0.0

    def get_avg_transfer_bandwidth_mbps(
            self, window_seconds: int = 60) -> float:
        """
        Calculate average transfer bandwidth in Mbps.

        Args:
            window_seconds: Time window for calculation

        Returns:
            Average bandwidth in Mbps
        """
        with self._lock:
            cutoff_time = time.time() - window_seconds
            recent_transfers = [
                (t, bytes_) for t, bytes_ in self.transfer_history if t >= cutoff_time]

            if not recent_transfers:
                return 0.0

            total_bytes = sum(bytes_ for _, bytes_ in recent_transfers)
            total_bits = total_bytes * 8
            mbps = (total_bits / window_seconds) / 1_000_000

            return mbps

    def get_stats(self, window_seconds: int = 60) -> dict[str, Any]:
        """Get disaggregation statistics."""
        with self._lock:
            total_requests = (
                self.metrics.prefill_requests + self.metrics.decode_requests
            )

            return {
                "prefill_requests": self.metrics.prefill_requests,
                "decode_requests": self.metrics.decode_requests,
                "total_requests": total_requests,
                "prefill_ratio": (
                    self.metrics.prefill_requests / total_requests * 100
                    if total_requests > 0
                    else 0.0
                ),
                "decode_ratio": (
                    self.metrics.decode_requests / total_requests * 100
                    if total_requests > 0
                    else 0.0
                ),
                "kv_transfer_bytes": self.metrics.kv_transfer_bytes,
                "kv_transfer_mb": self.metrics.kv_transfer_bytes / (1024 * 1024),
                "kv_transfer_time_ms": self.metrics.kv_transfer_time_ms,
                "disaggregation_overhead_us": self.metrics.disaggregation_overhead_us,
                "disaggregation_overhead_ms": self.metrics.disaggregation_overhead_us /
                1000,
                "cross_worker_transfers": self.metrics.cross_worker_transfers,
                "avg_transfer_bandwidth_mbps": self.get_avg_transfer_bandwidth_mbps(
                    window_seconds
                ),
                "avg_overhead_per_transfer_us": (
                    self.metrics.disaggregation_overhead_us /
                    self.metrics.cross_worker_transfers
                    if self.metrics.cross_worker_transfers > 0
                    else 0.0
                ),
            }


class AdvancedDynamoMetrics:
    """
    Production-grade NVIDIA AI-Dynamo metrics collector.

    Combines all advanced metrics tracking:
    - Extreme request lifecycle granularity
    - Multi-tier queue management
    - Dynamic batch optimization
    - Disaggregation tracking
    - Model-specific profiling
    - Advanced analytics with long-tail analysis
    """

    def __init__(
        self,
        window_size: int = 300,
        enable_queue_management: bool = True,
        enable_batch_optimization: bool = True,
        enable_disaggregation: bool = True,
    ):
        """
        Initialize advanced metrics collector.

        Args:
            window_size: Time window for metrics in seconds
            enable_queue_management: Enable queue management tracking
            enable_batch_optimization: Enable batch optimization tracking
            enable_disaggregation: Enable disaggregation tracking
        """
        self.window_size = window_size

        # Request tracking
        self._completed_requests: deque[AdvancedRequestMetrics] = deque(
            maxlen=10000)
        self._active_requests: dict[str, AdvancedRequestMetrics] = {}

        # Component trackers
        self.queue_manager = QueueManager() if enable_queue_management else None
        self.batch_optimizer = BatchOptimizer() if enable_batch_optimization else None
        self.disaggregation_tracker = (
            DisaggregationTracker() if enable_disaggregation else None
        )

        # Per-model statistics
        self.model_stats: dict[str, dict[str, Any]] = defaultdict(
            lambda: {
                "requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "ttft_values": deque(maxlen=1000),
                "tpot_values": deque(maxlen=1000),
                "total_latency_values": deque(maxlen=1000),
                "queue_time_values": deque(maxlen=1000),
            }
        )

        # Counters
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0

        self._lock = threading.RLock()  # Reentrant lock to allow nested locking

    def start_request(
        self,
        request_id: str,
        model: str,
        endpoint: str,
        input_tokens: int,
        priority: RequestPriority = RequestPriority.NORMAL,
    ) -> tuple[Optional[AdvancedRequestMetrics], str]:
        """
        Start tracking a new request.

        Returns:
            (metrics, reason) - metrics object if enqueued, reason if rejected
        """
        with self._lock:
            # Enqueue in queue manager
            if self.queue_manager:
                success, reason = self.queue_manager.enqueue(priority)
                if not success:
                    return None, reason

            # Create request metrics
            request = AdvancedRequestMetrics(
                request_id=request_id,
                model=model,
                endpoint=endpoint,
                priority=priority,
                arrival_time=time.time(),
                scheduler_queue_entry_time=time.time(),
                input_tokens=input_tokens,
            )

            self._active_requests[request_id] = request
            self.total_requests += 1

            return request, "success"

    def record_router_decision(
        self, request_id: str, start_time: float, end_time: float
    ):
        """Record router decision timing."""
        if request_id in self._active_requests:
            request = self._active_requests[request_id]
            request.router_decision_start_time = start_time
            request.router_decision_end_time = end_time

    def record_scheduler_queue_exit(self, request_id: str):
        """Record when request exits scheduler queue."""
        if request_id in self._active_requests:
            request = self._active_requests[request_id]
            request.scheduler_queue_exit_time = time.time()
            request.worker_queue_entry_time = time.time()

    def record_worker_queue_exit(self, request_id: str):
        """Record when request exits worker queue."""
        if request_id in self._active_requests:
            request = self._active_requests[request_id]
            request.worker_queue_exit_time = time.time()

            # Dequeue from queue manager
            if self.queue_manager:
                wait_time = (request.worker_queue_exit_time -
                             request.scheduler_queue_entry_time) * 1000
                self.queue_manager.dequeue(request.priority, wait_time)

    def record_kv_cache_lookup(
        self, request_id: str, start_time: float, end_time: float
    ):
        """Record KV cache lookup timing."""
        if request_id in self._active_requests:
            request = self._active_requests[request_id]
            request.kv_cache_lookup_start_time = start_time
            request.kv_cache_lookup_end_time = end_time

    def record_prefill_phase(
            self,
            request_id: str,
            start_time: float,
            end_time: float):
        """Record prefill phase timing."""
        if request_id in self._active_requests:
            request = self._active_requests[request_id]
            request.prefill_start_time = start_time
            request.prefill_end_time = end_time

            # Track in disaggregation
            if self.disaggregation_tracker and request.is_prefill_worker:
                # Estimate KV cache size (16 bytes per token per layer)
                kv_size = request.input_tokens * 16 * 80  # Assume 80 layers
                self.disaggregation_tracker.record_prefill_request(
                    request.worker_id, kv_size
                )

    def record_first_token(self, request_id: str):
        """Record first token generation."""
        if request_id in self._active_requests:
            request = self._active_requests[request_id]
            request.first_token_time = time.time()
            request.decode_start_time = time.time()

    def record_decode_phase(
            self,
            request_id: str,
            start_time: float,
            end_time: float):
        """Record decode phase timing."""
        if request_id in self._active_requests:
            request = self._active_requests[request_id]
            request.decode_start_time = start_time
            request.decode_end_time = end_time

            # Track in disaggregation
            if self.disaggregation_tracker and request.is_decode_worker:
                self.disaggregation_tracker.record_decode_request(
                    request.worker_id)

    def record_kv_writeback(
            self,
            request_id: str,
            start_time: float,
            end_time: float):
        """Record KV cache writeback timing."""
        if request_id in self._active_requests:
            request = self._active_requests[request_id]
            request.kv_writeback_start_time = start_time
            request.kv_writeback_end_time = end_time

    def record_network_transfer(
        self, request_id: str, start_time: float, end_time: float
    ):
        """Record network transfer timing."""
        if request_id in self._active_requests:
            request = self._active_requests[request_id]
            request.network_transfer_start_time = start_time
            request.network_transfer_end_time = end_time

    def complete_request(
        self,
        request_id: str,
        output_tokens: int,
        cached_tokens: int = 0,
        kv_cache_hit: bool = False,
        worker_id: str = "",
        success: bool = True,
        finish_reason: str = "stop",
        batch_id: str = "",
        batch_size: int = 1,
    ):
        """Complete request and calculate final metrics."""
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
            request.batch_id = batch_id
            request.batch_size = batch_size

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
            model = request.model
            self.model_stats[model]["requests"] += 1
            if success:
                self.model_stats[model]["successful_requests"] += 1
            else:
                self.model_stats[model]["failed_requests"] += 1
            self.model_stats[model]["total_input_tokens"] += request.input_tokens
            self.model_stats[model]["total_output_tokens"] += output_tokens
            if request.ttft_ms > 0:
                self.model_stats[model]["ttft_values"].append(request.ttft_ms)
            if request.tpot_ms > 0:
                self.model_stats[model]["tpot_values"].append(request.tpot_ms)
            if request.total_time_ms > 0:
                self.model_stats[model]["total_latency_values"].append(
                    request.total_time_ms
                )
            if request.total_queue_time_ms > 0:
                self.model_stats[model]["queue_time_values"].append(
                    request.total_queue_time_ms
                )

    def get_recent_requests(
            self,
            seconds: int = 60) -> list[AdvancedRequestMetrics]:
        """Get requests completed in last N seconds."""
        cutoff_time = time.time() - seconds
        with self._lock:
            return [
                r for r in self._completed_requests if r.completion_time >= cutoff_time]

    def calculate_percentile(
            self,
            values: list[float],
            percentile: float) -> float:
        """Calculate percentile from values."""
        if not values:
            return 0.0
        sorted_vals = sorted(values)
        idx = int(len(sorted_vals) * (percentile / 100.0))
        idx = min(idx, len(sorted_vals) - 1)
        return sorted_vals[idx]

    def get_latency_stats(self, window_seconds: int = 60) -> dict[str, Any]:
        """Get comprehensive latency statistics."""
        recent = self.get_recent_requests(window_seconds)

        if not recent:
            return self._empty_latency_stats()

        # Extract values for each phase
        ttft_values = [r.ttft_ms for r in recent if r.ttft_ms > 0]
        tpot_values = [r.tpot_ms for r in recent if r.tpot_ms > 0]
        total_values = [r.total_time_ms for r in recent if r.total_time_ms > 0]
        router_values = [
            r.router_decision_time_us for r in recent if r.router_decision_time_us > 0]
        scheduler_queue_values = [
            r.scheduler_queue_time_ms for r in recent if r.scheduler_queue_time_ms > 0]
        worker_queue_values = [
            r.worker_queue_time_ms for r in recent if r.worker_queue_time_ms > 0]
        total_queue_values = [
            r.total_queue_time_ms for r in recent if r.total_queue_time_ms > 0
        ]
        kv_lookup_values = [
            r.kv_cache_lookup_time_us for r in recent if r.kv_cache_lookup_time_us > 0]
        prefill_values = [
            r.prefill_time_ms for r in recent if r.prefill_time_ms > 0]
        first_token_gen_values = [
            r.first_token_generation_time_ms
            for r in recent
            if r.first_token_generation_time_ms > 0
        ]
        decode_values = [
            r.decode_time_ms for r in recent if r.decode_time_ms > 0]
        kv_writeback_values = [
            r.kv_writeback_time_us for r in recent if r.kv_writeback_time_us > 0]
        network_values = [
            r.network_transfer_time_ms for r in recent if r.network_transfer_time_ms > 0]

        return {
            "ttft": self._calc_stats(ttft_values, "ms"),
            "tpot": self._calc_stats(tpot_values, "ms"),
            "total": self._calc_stats(total_values, "ms"),
            "router_decision": self._calc_stats(router_values, "us"),
            "scheduler_queue": self._calc_stats(scheduler_queue_values, "ms"),
            "worker_queue": self._calc_stats(worker_queue_values, "ms"),
            "total_queue": self._calc_stats(total_queue_values, "ms"),
            "kv_cache_lookup": self._calc_stats(kv_lookup_values, "us"),
            "prefill": self._calc_stats(prefill_values, "ms"),
            "first_token_generation": self._calc_stats(first_token_gen_values, "ms"),
            "decode": self._calc_stats(decode_values, "ms"),
            "kv_writeback": self._calc_stats(kv_writeback_values, "us"),
            "network_transfer": self._calc_stats(network_values, "ms"),
        }

    def _calc_stats(self, values: list[float], unit: str) -> dict[str, Any]:
        """Calculate statistics for a metric."""
        if not values:
            return {
                "avg": 0.0,
                "p50": 0.0,
                "p75": 0.0,
                "p90": 0.0,
                "p95": 0.0,
                "p99": 0.0,
                "p99.9": 0.0,
                "unit": unit,
            }

        return {
            "avg": sum(values) / len(values),
            "p50": self.calculate_percentile(values, 50),
            "p75": self.calculate_percentile(values, 75),
            "p90": self.calculate_percentile(values, 90),
            "p95": self.calculate_percentile(values, 95),
            "p99": self.calculate_percentile(values, 99),
            "p99.9": self.calculate_percentile(values, 99.9),
            "unit": unit,
        }

    def _empty_latency_stats(self) -> dict[str, Any]:
        """Return empty latency stats structure."""
        empty_stat = {
            "avg": 0.0,
            "p50": 0.0,
            "p75": 0.0,
            "p90": 0.0,
            "p95": 0.0,
            "p99": 0.0,
            "p99.9": 0.0,
            "unit": "",
        }
        return {
            "ttft": {**empty_stat, "unit": "ms"},
            "tpot": {**empty_stat, "unit": "ms"},
            "total": {**empty_stat, "unit": "ms"},
            "router_decision": {**empty_stat, "unit": "us"},
            "scheduler_queue": {**empty_stat, "unit": "ms"},
            "worker_queue": {**empty_stat, "unit": "ms"},
            "total_queue": {**empty_stat, "unit": "ms"},
            "kv_cache_lookup": {**empty_stat, "unit": "us"},
            "prefill": {**empty_stat, "unit": "ms"},
            "first_token_generation": {**empty_stat, "unit": "ms"},
            "decode": {**empty_stat, "unit": "ms"},
            "kv_writeback": {**empty_stat, "unit": "us"},
            "network_transfer": {**empty_stat, "unit": "ms"},
        }

    def get_long_tail_analysis(
            self, window_seconds: int = 60) -> dict[str, Any]:
        """
        Analyze long-tail requests (>p99).

        Identifies outliers and their characteristics.
        """
        recent = self.get_recent_requests(window_seconds)

        if not recent:
            return {"long_tail_requests": 0, "analysis": {}}

        # Calculate p99 threshold
        total_latencies = [
            r.total_time_ms for r in recent if r.total_time_ms > 0]
        if not total_latencies:
            return {"long_tail_requests": 0, "analysis": {}}

        p99_threshold = self.calculate_percentile(total_latencies, 99)

        # Find long-tail requests
        long_tail = [r for r in recent if r.total_time_ms > p99_threshold]

        if not long_tail:
            return {
                "long_tail_requests": 0,
                "p99_threshold_ms": p99_threshold,
                "analysis": {},
            }

        # Analyze characteristics
        avg_input_tokens = sum(
            r.input_tokens for r in long_tail) / len(long_tail)
        avg_output_tokens = sum(
            r.output_tokens for r in long_tail) / len(long_tail)
        avg_queue_time = sum(
            r.total_queue_time_ms for r in long_tail) / len(long_tail)
        avg_batch_size = sum(r.batch_size for r in long_tail) / len(long_tail)

        # Models with long tail
        model_counts = defaultdict(int)
        for r in long_tail:
            model_counts[r.model] += 1

        return {
            "long_tail_requests": len(long_tail),
            "percentage": len(long_tail) /
            len(recent) *
            100,
            "p99_threshold_ms": p99_threshold,
            "analysis": {
                "avg_input_tokens": avg_input_tokens,
                "avg_output_tokens": avg_output_tokens,
                "avg_queue_time_ms": avg_queue_time,
                "avg_batch_size": avg_batch_size,
                "models": dict(model_counts),
                "avg_total_latency_ms": sum(
                    r.total_time_ms for r in long_tail) /
                len(long_tail),
            },
        }

    def get_model_stats(self, window_seconds: int = 60) -> dict[str, Any]:
        """Get per-model statistics."""
        with self._lock:
            stats = {}

            for model, data in self.model_stats.items():
                if data["requests"] == 0:
                    continue

                # Get recent values
                recent_ttft = list(data["ttft_values"])[-100:]
                recent_tpot = list(data["tpot_values"])[-100:]
                recent_total = list(data["total_latency_values"])[-100:]
                recent_queue = list(data["queue_time_values"])[-100:]

                stats[model] = {
                    "requests": data["requests"],
                    "successful_requests": data["successful_requests"],
                    "failed_requests": data["failed_requests"],
                    "success_rate": (
                        data["successful_requests"] /
                        data["requests"] *
                        100 if data["requests"] > 0 else 0.0),
                    "total_input_tokens": data["total_input_tokens"],
                    "total_output_tokens": data["total_output_tokens"],
                    "avg_input_tokens": (
                        data["total_input_tokens"] /
                        data["requests"] if data["requests"] > 0 else 0.0),
                    "avg_output_tokens": (
                        data["total_output_tokens"] /
                        data["requests"] if data["requests"] > 0 else 0.0),
                    "ttft": (
                        self._calc_stats(
                            recent_ttft,
                            "ms") if recent_ttft else None),
                    "tpot": (
                        self._calc_stats(
                            recent_tpot,
                            "ms") if recent_tpot else None),
                    "total_latency": (
                        self._calc_stats(
                            recent_total,
                            "ms") if recent_total else None),
                    "queue_time": (
                        self._calc_stats(
                            recent_queue,
                            "ms") if recent_queue else None),
                }

            return stats

    def get_request_size_distribution(
            self, window_seconds: int = 60) -> dict[str, Any]:
        """Get distribution of request sizes (input/output tokens)."""
        recent = self.get_recent_requests(window_seconds)

        if not recent:
            return {"input_tokens": {}, "output_tokens": {}}

        # Buckets for token distribution
        input_buckets = [0, 100, 500, 1000, 2000, 4000, 8000, 16000, 32000]
        output_buckets = [0, 50, 100, 200, 500, 1000, 2000, 4000]

        # Count requests in each bucket
        input_dist = defaultdict(int)
        output_dist = defaultdict(int)

        for request in recent:
            # Input tokens
            for i in range(len(input_buckets) - 1):
                if input_buckets[i] <= request.input_tokens < input_buckets[i + 1]:
                    bucket_name = f"{input_buckets[i]}-{input_buckets[i + 1]}"
                    input_dist[bucket_name] += 1
                    break
            else:
                if request.input_tokens >= input_buckets[-1]:
                    input_dist[f"{input_buckets[-1]}+"] += 1

            # Output tokens
            for i in range(len(output_buckets) - 1):
                if output_buckets[i] <= request.output_tokens < output_buckets[i + 1]:
                    bucket_name = f"{output_buckets[i]}-{output_buckets[i + 1]}"
                    output_dist[bucket_name] += 1
                    break
            else:
                if request.output_tokens >= output_buckets[-1]:
                    output_dist[f"{output_buckets[-1]}+"] += 1

        return {
            "input_tokens": dict(input_dist),
            "output_tokens": dict(output_dist),
            "avg_input_tokens": sum(
                r.input_tokens for r in recent) /
            len(recent),
            "avg_output_tokens": sum(
                r.output_tokens for r in recent) /
            len(recent),
        }

    def get_stats_dict(self, window_seconds: int = 60) -> dict[str, Any]:
        """Get all statistics as dictionary."""
        stats = {
            "summary": {
                "total_requests": self.total_requests,
                "successful_requests": self.successful_requests,
                "failed_requests": self.failed_requests,
                "active_requests": len(self._active_requests),
                "success_rate": (
                    self.successful_requests / self.total_requests * 100
                    if self.total_requests > 0
                    else 0.0
                ),
            },
            "latency": self.get_latency_stats(window_seconds),
            "long_tail": self.get_long_tail_analysis(window_seconds),
            "per_model": self.get_model_stats(window_seconds),
            "request_distribution": self.get_request_size_distribution(window_seconds),
        }

        # Add component stats if enabled
        if self.queue_manager:
            stats["queues"] = self.queue_manager.get_all_queue_stats()

        if self.batch_optimizer:
            stats["batch"] = self.batch_optimizer.get_batch_stats()

        if self.disaggregation_tracker:
            stats["disaggregation"] = self.disaggregation_tracker.get_stats(
                window_seconds
            )

        return stats
