"""
Worker Pool Management with Comprehensive Statistics.

This module provides worker pool management for tracking:
- Per-worker active and total request counts
- Average request duration and utilization
- Worker status (active/idle/offline)
- Realistic load distribution across workers
"""

#  SPDX-License-Identifier: Apache-2.0

import logging
import random
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class WorkerStatus(Enum):
    """Worker operational status."""

    ACTIVE = "active"  # Processing requests
    IDLE = "idle"  # Available but not processing
    OFFLINE = "offline"  # Not available


@dataclass
class WorkerStatistics:
    """
    Comprehensive per-worker statistics.

    Tracks all metrics needed for dashboard monitoring:
    - Active request count (current load)
    - Total requests processed (lifetime)
    - Average request duration
    - Utilization percentage
    """

    worker_id: str
    status: WorkerStatus = WorkerStatus.IDLE

    # Request tracking
    active_requests: int = 0
    total_requests: int = 0
    completed_requests: int = 0
    failed_requests: int = 0

    # Timing metrics
    total_request_duration_ms: float = 0.0
    request_durations: deque = field(
        default_factory=lambda: deque(maxlen=1000))

    # Utilization tracking
    busy_time_ms: float = 0.0
    last_active_time: float = 0.0
    last_idle_time: float = 0.0

    # Lifecycle
    created_at: float = field(default_factory=time.time)
    last_request_time: float = 0.0

    def __post_init__(self):
        """Initialize timing fields."""
        if self.last_idle_time == 0.0:
            self.last_idle_time = time.time()

    @property
    def avg_request_duration_ms(self) -> float:
        """Calculate average request duration in milliseconds."""
        if self.completed_requests > 0:
            return self.total_request_duration_ms / self.completed_requests
        return 0.0

    @property
    def utilization(self) -> float:
        """
        Calculate worker utilization percentage (0.0 - 1.0).

        Based on ratio of time spent processing vs total uptime.
        """
        uptime_ms = (time.time() - self.created_at) * 1000
        if uptime_ms > 0:
            return min(1.0, self.busy_time_ms / uptime_ms)
        return 0.0

    @property
    def recent_avg_duration_ms(self) -> float:
        """Calculate average duration from recent requests."""
        if not self.request_durations:
            return 0.0
        return sum(self.request_durations) / len(self.request_durations)

    def start_request(self):
        """Mark request as started."""
        self.active_requests += 1
        self.total_requests += 1
        self.last_request_time = time.time()

        # Update status
        if self.status == WorkerStatus.IDLE:
            self.status = WorkerStatus.ACTIVE
            self.last_active_time = time.time()

    def complete_request(self, duration_ms: float, success: bool = True):
        """
        Mark request as completed.

        Args:
            duration_ms: Request processing duration in milliseconds
            success: Whether request succeeded
        """
        self.active_requests = max(0, self.active_requests - 1)

        if success:
            self.completed_requests += 1
            self.total_request_duration_ms += duration_ms
            self.request_durations.append(duration_ms)
            self.busy_time_ms += duration_ms
        else:
            self.failed_requests += 1

        # Update status
        if self.active_requests == 0:
            self.status = WorkerStatus.IDLE
            self.last_idle_time = time.time()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "worker_id": self.worker_id,
            "status": self.status.value,
            "active_requests": self.active_requests,
            "total_requests": self.total_requests,
            "avg_request_duration_ms": round(self.avg_request_duration_ms, 2),
            "utilization": round(self.utilization, 3),
            "completed_requests": self.completed_requests,
            "failed_requests": self.failed_requests,
        }


class WorkerPool:
    """
    Worker pool with comprehensive statistics tracking.

    Manages a pool of workers and tracks their utilization, status,
    and performance metrics for dashboard monitoring.
    """

    def __init__(self, num_workers: int = 4):
        """
        Initialize worker pool.

        Args:
            num_workers: Number of workers to simulate (default: 4)
        """
        self.num_workers = num_workers
        self.workers: dict[str, WorkerStatistics] = {}
        self._lock = threading.RLock()

        # Initialize workers
        for i in range(num_workers):
            worker_id = f"worker-{i}"
            self.workers[worker_id] = WorkerStatistics(worker_id=worker_id)

        # Background simulation thread - DISABLED (causes issues with real
        # requests)
        self._simulation_enabled = False
        self._simulation_thread = None
        # self._simulation_thread = threading.Thread(
        #     target=self._simulate_load_distribution, daemon=True
        # )
        # self._simulation_thread.start()

        logger.info(f"WorkerPool initialized with {num_workers} workers")

    def assign_request(self, request_id: str) -> str:
        """
        Assign request to a worker.

        Uses simple round-robin with load balancing:
        - Prefer idle workers
        - Then least loaded active workers

        Args:
            request_id: Unique request identifier

        Returns:
            worker_id: ID of assigned worker
        """
        with self._lock:
            # Find idle workers
            idle_workers = [
                w for w in self.workers.values() if w.status == WorkerStatus.IDLE]

            if idle_workers:
                # Pick random idle worker for better distribution
                worker = random.choice(idle_workers)
            else:
                # All busy - pick least loaded
                worker = min(
                    self.workers.values(),
                    key=lambda w: w.active_requests)

            worker.start_request()
            return worker.worker_id

    def complete_request(
        self, worker_id: str, duration_ms: float, success: bool = True
    ):
        """
        Mark request as completed on worker.

        Args:
            worker_id: Worker that processed the request
            duration_ms: Processing duration in milliseconds
            success: Whether request succeeded
        """
        with self._lock:
            if worker_id in self.workers:
                self.workers[worker_id].complete_request(duration_ms, success)

    def get_worker_stats(self) -> dict[str, Any]:
        """
        Get comprehensive worker statistics.

        Returns dictionary matching dashboard format:
        {
            "total_workers": 4,
            "active_workers": 2,
            "idle_workers": 2,
            "offline_workers": 0,
            "workers": [...]
        }
        """
        with self._lock:
            workers_list = []
            active_count = 0
            idle_count = 0
            offline_count = 0

            for worker in self.workers.values():
                if worker.status == WorkerStatus.ACTIVE:
                    active_count += 1
                elif worker.status == WorkerStatus.IDLE:
                    idle_count += 1
                elif worker.status == WorkerStatus.OFFLINE:
                    offline_count += 1

                workers_list.append(worker.to_dict())

            # Sort by worker_id for consistent ordering
            workers_list.sort(key=lambda w: w["worker_id"])

            return {
                "total_workers": self.num_workers,
                "active_workers": active_count,
                "idle_workers": idle_count,
                "offline_workers": offline_count,
                "workers": workers_list,
            }

    def get_worker(self, worker_id: str) -> WorkerStatistics | None:
        """Get specific worker statistics."""
        with self._lock:
            return self.workers.get(worker_id)

    def get_total_active_requests(self) -> int:
        """Get total active requests across all workers."""
        with self._lock:
            return sum(w.active_requests for w in self.workers.values())

    def get_total_requests_processed(self) -> int:
        """Get total requests processed by all workers."""
        with self._lock:
            return sum(w.completed_requests for w in self.workers.values())

    def get_avg_utilization(self) -> float:
        """Get average utilization across all workers."""
        with self._lock:
            if not self.workers:
                return 0.0
            return sum(w.utilization for w in self.workers.values()) / len(
                self.workers
            )

    def _simulate_load_distribution(self):
        """
        Background thread to simulate realistic load distribution.

        This creates varied utilization patterns across workers to show
        realistic dashboard behavior even without actual load.
        """
        while self._simulation_enabled:
            try:
                time.sleep(5)  # Update every 5 seconds

                with self._lock:
                    # Simulate some workers being busier than others
                    for i, worker in enumerate(self.workers.values()):
                        # Skip if worker already has real requests
                        if worker.active_requests > 0:
                            continue

                        # Create varied load patterns
                        # Worker 0: High load (70-90% utilization)
                        # Worker 1: Medium load (40-60% utilization)
                        # Worker 2: Low load (10-30% utilization)
                        # Worker 3: Very low load (0-15% utilization)

                        if i == 0:
                            target_util = random.uniform(0.70, 0.90)
                        elif i == 1:
                            target_util = random.uniform(0.40, 0.60)
                        elif i == 2:
                            target_util = random.uniform(0.10, 0.30)
                        else:
                            target_util = random.uniform(0.0, 0.15)

                        # Adjust simulated metrics to achieve target
                        # utilization
                        current_util = worker.utilization
                        if current_util < target_util:
                            # Simulate completed requests to increase
                            # utilization
                            sim_duration = random.uniform(20, 100)
                            worker.completed_requests += 1
                            worker.total_request_duration_ms += sim_duration
                            worker.busy_time_ms += sim_duration
                            worker.request_durations.append(sim_duration)

            except Exception as e:
                logger.error(f"Error in load simulation: {e}")

    def shutdown(self):
        """Shutdown worker pool."""
        self._simulation_enabled = False
        if self._simulation_thread and self._simulation_thread.is_alive():
            self._simulation_thread.join(timeout=1.0)
        logger.info("WorkerPool shutdown complete")


# Global worker pool instance
_worker_pool: WorkerPool | None = None
_pool_lock = threading.Lock()


def get_worker_pool(num_workers: int = 4) -> WorkerPool:
    """
    Get or create global worker pool instance.

    Args:
        num_workers: Number of workers (only used on first call)

    Returns:
        Global WorkerPool instance
    """
    global _worker_pool
    with _pool_lock:
        if _worker_pool is None:
            _worker_pool = WorkerPool(num_workers=num_workers)
        return _worker_pool


def reset_worker_pool():
    """Reset global worker pool (for testing)."""
    global _worker_pool
    with _pool_lock:
        if _worker_pool is not None:
            _worker_pool.shutdown()
            _worker_pool = None
