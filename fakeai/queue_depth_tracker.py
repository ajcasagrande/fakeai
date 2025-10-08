"""
Queue Depth Tracking for FakeAI Backend.

Implements realistic queue depth simulation and tracking for LLM inference
requests. Tracks queue entry/exit times, calculates wait times, and provides
comprehensive queue statistics including P95/P99 latencies.
"""

import threading
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any


@dataclass
class QueueEntry:
    """Represents a request in the queue."""

    request_id: str
    enqueue_time: float
    model: str
    priority: int = 0  # For future priority queue support
    metadata: dict[str, Any] = field(default_factory=dict)


class QueueDepthTracker:
    """
    Tracks queue depth and wait times for LLM inference requests.

    This class simulates realistic queue behavior:
    - Increments depth when requests arrive
    - Decrements depth when requests complete
    - Tracks wait times for each request
    - Calculates queue statistics (current, max, avg, P95, P99)
    - Integrates with DynamoMetricsCollector

    Thread-safe implementation for concurrent request handling.
    """

    def __init__(self, max_history: int = 10000):
        """
        Initialize the queue depth tracker.

        Args:
            max_history: Maximum number of wait time entries to track
        """
        # Active queue (requests currently in queue)
        self._active_queue: dict[str, QueueEntry] = {}

        # Completed wait times (for statistics)
        self._wait_times: deque[float] = deque(maxlen=max_history)

        # Queue depth history (time, depth) for graphing
        self._depth_history: deque[tuple[float, int]] = deque(maxlen=1000)

        # Statistics
        self.current_depth = 0
        self.max_depth = 0
        self.total_enqueued = 0
        self.total_dequeued = 0

        # Per-model statistics
        self._model_stats: dict[str, dict[str, Any]] = {}

        # Thread safety
        self._lock = threading.Lock()

    def enqueue(
            self,
            request_id: str,
            model: str,
            priority: int = 0,
            **metadata) -> float:
        """
        Add a request to the queue.

        Args:
            request_id: Unique request identifier
            model: Model name for the request
            priority: Priority level (higher = more urgent)
            **metadata: Additional metadata to store

        Returns:
            Enqueue timestamp
        """
        enqueue_time = time.time()

        with self._lock:
            # Create queue entry
            entry = QueueEntry(
                request_id=request_id,
                enqueue_time=enqueue_time,
                model=model,
                priority=priority,
                metadata=metadata,
            )

            # Add to active queue
            self._active_queue[request_id] = entry

            # Update depth
            self.current_depth = len(self._active_queue)
            self.max_depth = max(self.max_depth, self.current_depth)
            self.total_enqueued += 1

            # Record depth history
            self._depth_history.append((enqueue_time, self.current_depth))

            # Update model stats
            if model not in self._model_stats:
                self._model_stats[model] = {
                    "enqueued": 0,
                    "dequeued": 0,
                    "current_depth": 0,
                    "max_depth": 0,
                    "total_wait_time": 0.0,
                }

            self._model_stats[model]["enqueued"] += 1
            self._model_stats[model]["current_depth"] += 1
            self._model_stats[model]["max_depth"] = max(
                self._model_stats[model]["max_depth"],
                self._model_stats[model]["current_depth"],
            )

        return enqueue_time

    def dequeue(self, request_id: str) -> float:
        """
        Remove a request from the queue and calculate wait time.

        Args:
            request_id: Unique request identifier

        Returns:
            Wait time in milliseconds (0 if request not found)
        """
        dequeue_time = time.time()
        wait_time_ms = 0.0

        with self._lock:
            if request_id not in self._active_queue:
                # Request not in queue (might have been pre-processed)
                return 0.0

            # Get entry
            entry = self._active_queue.pop(request_id)

            # Calculate wait time
            wait_time_seconds = dequeue_time - entry.enqueue_time
            wait_time_ms = wait_time_seconds * 1000

            # Store wait time for statistics
            self._wait_times.append(wait_time_ms)

            # Update depth
            self.current_depth = len(self._active_queue)
            self.total_dequeued += 1

            # Record depth history
            self._depth_history.append((dequeue_time, self.current_depth))

            # Update model stats
            model = entry.model
            if model in self._model_stats:
                self._model_stats[model]["dequeued"] += 1
                self._model_stats[model]["current_depth"] -= 1
                self._model_stats[model]["total_wait_time"] += wait_time_ms

        return wait_time_ms

    def get_current_depth(self) -> int:
        """Get current queue depth."""
        with self._lock:
            return self.current_depth

    def get_max_depth(self) -> int:
        """Get maximum queue depth observed."""
        with self._lock:
            return self.max_depth

    def get_avg_wait_time_ms(self) -> float:
        """Get average wait time in milliseconds."""
        with self._lock:
            if not self._wait_times:
                return 0.0
            return sum(self._wait_times) / len(self._wait_times)

    def get_percentile(self, percentile: float) -> float:
        """
        Calculate percentile from wait times.

        Args:
            percentile: Percentile to calculate (0-100)

        Returns:
            Wait time at the given percentile (ms)
        """
        with self._lock:
            if not self._wait_times:
                return 0.0

            sorted_times = sorted(self._wait_times)
            idx = int(len(sorted_times) * (percentile / 100.0))
            idx = min(idx, len(sorted_times) - 1)
            return sorted_times[idx]

    def get_p50_wait_time_ms(self) -> float:
        """Get P50 (median) wait time in milliseconds."""
        return self.get_percentile(50)

    def get_p95_wait_time_ms(self) -> float:
        """Get P95 wait time in milliseconds."""
        return self.get_percentile(95)

    def get_p99_wait_time_ms(self) -> float:
        """Get P99 wait time in milliseconds."""
        return self.get_percentile(99)

    def get_queue_stats(self) -> dict[str, Any]:
        """
        Get comprehensive queue statistics.

        Returns:
            Dictionary with queue statistics
        """
        with self._lock:
            return {
                "current_depth": self.current_depth,
                "max_depth": self.max_depth,
                "total_enqueued": self.total_enqueued,
                "total_dequeued": self.total_dequeued,
                "active_requests": len(self._active_queue),
                "wait_times": {
                    "avg_ms": self.get_avg_wait_time_ms(),
                    "p50_ms": self.get_p50_wait_time_ms(),
                    "p95_ms": self.get_p95_wait_time_ms(),
                    "p99_ms": self.get_p99_wait_time_ms(),
                    "samples": len(self._wait_times),
                },
                "utilization_pct": 0.0,  # Can be set based on capacity
            }

    def get_model_stats(self) -> dict[str, Any]:
        """
        Get per-model queue statistics.

        Returns:
            Dictionary with per-model statistics
        """
        with self._lock:
            stats = {}
            for model, data in self._model_stats.items():
                avg_wait = (
                    data["total_wait_time"] /
                    data["dequeued"] if data["dequeued"] > 0 else 0.0)
                stats[model] = {
                    "enqueued": data["enqueued"],
                    "dequeued": data["dequeued"],
                    "current_depth": data["current_depth"],
                    "max_depth": data["max_depth"],
                    "avg_wait_time_ms": avg_wait,
                }
            return stats

    def get_depth_history(self, last_n: int = 100) -> list[tuple[float, int]]:
        """
        Get recent queue depth history.

        Args:
            last_n: Number of recent entries to return

        Returns:
            List of (timestamp, depth) tuples
        """
        with self._lock:
            history = list(self._depth_history)
            return history[-last_n:] if len(history) > last_n else history

    def reset_stats(self):
        """Reset statistics (for testing or periodic reset)."""
        with self._lock:
            self.max_depth = self.current_depth
            self.total_enqueued = 0
            self.total_dequeued = 0
            self._wait_times.clear()
            for model in self._model_stats:
                self._model_stats[model]["max_depth"] = self._model_stats[model]["current_depth"]
                self._model_stats[model]["total_wait_time"] = 0.0


# Global singleton instance
_queue_tracker: QueueDepthTracker | None = None
_tracker_lock = threading.Lock()


def get_queue_tracker() -> QueueDepthTracker:
    """
    Get the global queue tracker instance.

    Returns:
        QueueDepthTracker singleton
    """
    global _queue_tracker
    if _queue_tracker is None:
        with _tracker_lock:
            if _queue_tracker is None:
                _queue_tracker = QueueDepthTracker()
    return _queue_tracker


def reset_queue_tracker():
    """Reset the global queue tracker (for testing)."""
    global _queue_tracker
    with _tracker_lock:
        _queue_tracker = None
