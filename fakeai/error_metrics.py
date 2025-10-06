"""
Error analytics and tracking module.

This module provides comprehensive error tracking, classification, and analysis
for the FakeAI server, including error patterns, rates, distributions, recovery
metrics, and SLO tracking.
"""

#  SPDX-License-Identifier: Apache-2.0

import logging
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class ErrorEvent:
    """Record of a single error occurrence."""

    timestamp: float
    endpoint: str
    status_code: int
    error_type: str
    error_message: str
    model: str | None = None
    api_key: str | None = None
    request_id: str | None = None


@dataclass
class ErrorPattern:
    """Identified error pattern with frequency and context."""

    error_signature: str  # Unique identifier for this error pattern
    error_type: str
    status_code: int
    first_occurrence: float
    last_occurrence: float
    count: int
    affected_endpoints: set[str] = field(default_factory=set)
    affected_models: set[str] = field(default_factory=set)
    sample_messages: deque = field(default_factory=lambda: deque(maxlen=5))


@dataclass
class RecoveryMetrics:
    """Metrics for error recovery and retry behavior."""

    total_errors: int = 0
    total_recoveries: int = 0
    recovery_attempts: deque = field(default_factory=lambda: deque(maxlen=100))
    time_to_recovery: deque = field(default_factory=lambda: deque(maxlen=100))
    success_after_error: int = 0
    retry_patterns: dict[str, int] = field(default_factory=lambda: defaultdict(int))


class ErrorMetricsTracker:
    """
    Singleton class to track comprehensive error analytics.

    Provides error classification, rate tracking, pattern detection, recovery
    metrics, and SLO compliance monitoring.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """Ensure only one instance exists (singleton pattern)."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ErrorMetricsTracker, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        """Initialize the error metrics tracker (only once)."""
        if self._initialized:
            return

        # Error storage (last 10,000 events)
        self._error_history: deque[ErrorEvent] = deque(maxlen=10000)
        self._error_lock = threading.Lock()

        # Error classification counters
        self._status_code_counts: dict[int, int] = defaultdict(int)
        self._error_type_counts: dict[str, int] = defaultdict(int)
        self._endpoint_errors: dict[str, int] = defaultdict(int)
        self._model_errors: dict[str, int] = defaultdict(int)
        self._api_key_errors: dict[str, int] = defaultdict(int)

        # Error patterns (detected recurring errors)
        self._error_patterns: dict[str, ErrorPattern] = {}
        self._pattern_lock = threading.Lock()

        # Time-series data for rate tracking (numpy arrays)
        self._error_timestamps = np.array([], dtype=np.float64)
        self._success_timestamps = np.array([], dtype=np.float64)
        self._request_timestamps = np.array([], dtype=np.float64)

        # Per-endpoint time-series
        self._endpoint_errors_ts: dict[str, np.ndarray] = defaultdict(
            lambda: np.array([], dtype=np.float64)
        )
        self._endpoint_requests_ts: dict[str, np.ndarray] = defaultdict(
            lambda: np.array([], dtype=np.float64)
        )

        # Error burst detection
        self._burst_threshold = 10  # errors per second
        self._burst_events: deque = deque(maxlen=100)

        # Recovery tracking
        self._recovery_metrics = RecoveryMetrics()
        self._pending_recovery: dict[str, float] = {}  # api_key -> error_timestamp

        # SLO configuration
        self._slo_config = {
            "availability_target": 0.999,  # 99.9% availability (1 nine)
            "error_rate_target": 0.01,  # 1% error rate max
            "error_budget_window": 30 * 24 * 3600,  # 30 days
            "p99_latency_target_ms": 1000,  # Not tracked here, but included for consistency
        }

        # SLO tracking
        self._slo_violations: deque = deque(maxlen=1000)
        self._error_budget_consumed = 0.0
        self._error_budget_total = 0.0

        # Correlation tracking (which errors happen together)
        self._error_correlations: dict[tuple[str, str], int] = defaultdict(int)
        self._correlation_window_seconds = 60.0

        # Window for sliding calculations
        self._window_size = 60.0  # 60 seconds

        # Error message clustering (for pattern detection)
        self._message_signatures: dict[str, list[str]] = defaultdict(list)

        self._initialized = True
        logger.info("Error metrics tracker initialized")

    def record_error(
        self,
        endpoint: str,
        status_code: int,
        error_type: str,
        error_message: str,
        model: str | None = None,
        api_key: str | None = None,
        request_id: str | None = None,
    ) -> None:
        """
        Record an error occurrence.

        Args:
            endpoint: The API endpoint where the error occurred
            status_code: HTTP status code (400, 401, 429, 500, etc.)
            error_type: Error classification (validation, auth, rate_limit, internal, timeout)
            error_message: Detailed error message
            model: Model identifier (if applicable)
            api_key: API key associated with the request (if applicable)
            request_id: Unique request identifier (if available)
        """
        current_time = time.time()

        # Create error event
        event = ErrorEvent(
            timestamp=current_time,
            endpoint=endpoint,
            status_code=status_code,
            error_type=error_type,
            error_message=error_message,
            model=model,
            api_key=api_key,
            request_id=request_id,
        )

        with self._error_lock:
            # Add to history
            self._error_history.append(event)

            # Update classification counters
            self._status_code_counts[status_code] += 1
            self._error_type_counts[error_type] += 1
            self._endpoint_errors[endpoint] += 1
            if model:
                self._model_errors[model] += 1
            if api_key:
                self._api_key_errors[api_key] += 1

            # Update time-series data
            self._error_timestamps = np.append(self._error_timestamps, current_time)
            self._endpoint_errors_ts[endpoint] = np.append(
                self._endpoint_errors_ts[endpoint], current_time
            )

            # Cleanup old data
            self._cleanup_timeseries()

        # Detect patterns
        self._detect_error_pattern(event)

        # Check for burst
        self._check_error_burst(current_time)

        # Check for correlations
        self._detect_correlations(event)

        # Update recovery tracking
        if api_key:
            with self._error_lock:
                self._pending_recovery[api_key] = current_time
                self._recovery_metrics.total_errors += 1

        # Check SLO compliance
        self._check_slo_violation()

    def record_success(
        self,
        endpoint: str,
        api_key: str | None = None,
    ) -> None:
        """
        Record a successful request (for error rate calculation).

        Args:
            endpoint: The API endpoint
            api_key: API key associated with the request (if applicable)
        """
        current_time = time.time()

        with self._error_lock:
            self._success_timestamps = np.append(self._success_timestamps, current_time)
            self._request_timestamps = np.append(self._request_timestamps, current_time)
            self._endpoint_requests_ts[endpoint] = np.append(
                self._endpoint_requests_ts[endpoint], current_time
            )

            # Cleanup old data
            self._cleanup_timeseries()

        # Check for recovery
        if api_key and api_key in self._pending_recovery:
            with self._error_lock:
                error_time = self._pending_recovery[api_key]
                recovery_time = current_time - error_time
                self._recovery_metrics.total_recoveries += 1
                self._recovery_metrics.success_after_error += 1
                self._recovery_metrics.time_to_recovery.append(recovery_time)
                self._recovery_metrics.recovery_attempts.append(
                    {"timestamp": current_time, "recovery_time": recovery_time}
                )
                del self._pending_recovery[api_key]

    def record_request(
        self,
        endpoint: str,
    ) -> None:
        """
        Record a request (for error rate calculation).

        Args:
            endpoint: The API endpoint
        """
        current_time = time.time()

        with self._error_lock:
            self._request_timestamps = np.append(self._request_timestamps, current_time)
            self._endpoint_requests_ts[endpoint] = np.append(
                self._endpoint_requests_ts[endpoint], current_time
            )

            # Cleanup old data
            self._cleanup_timeseries()

    def get_error_rate(
        self, endpoint: str | None = None, window_seconds: float | None = None
    ) -> float:
        """
        Get error rate percentage.

        Args:
            endpoint: Specific endpoint to get error rate for (None = overall)
            window_seconds: Time window in seconds (None = use default window)

        Returns:
            Error rate as a percentage (0.0-100.0)
        """
        window = window_seconds or self._window_size
        current_time = time.time()
        cutoff_time = current_time - window

        with self._error_lock:
            if endpoint:
                # Endpoint-specific error rate
                error_ts = self._endpoint_errors_ts.get(endpoint, np.array([]))
                request_ts = self._endpoint_requests_ts.get(endpoint, np.array([]))

                recent_errors = (
                    np.sum(error_ts >= cutoff_time) if len(error_ts) > 0 else 0
                )
                recent_requests = (
                    np.sum(request_ts >= cutoff_time) if len(request_ts) > 0 else 0
                )
            else:
                # Overall error rate
                recent_errors = (
                    np.sum(self._error_timestamps >= cutoff_time)
                    if len(self._error_timestamps) > 0
                    else 0
                )
                recent_requests = (
                    np.sum(self._request_timestamps >= cutoff_time)
                    if len(self._request_timestamps) > 0
                    else 0
                )

            if recent_requests == 0:
                return 0.0

            return (recent_errors / recent_requests) * 100.0

    def get_error_rate_over_time(
        self, endpoint: str | None = None, bucket_seconds: float = 60.0
    ) -> dict[str, Any]:
        """
        Get error rate over time with sliding window.

        Args:
            endpoint: Specific endpoint (None = overall)
            bucket_seconds: Size of time buckets in seconds

        Returns:
            Dictionary with time buckets and error rates
        """
        current_time = time.time()
        cutoff_time = current_time - self._window_size

        with self._error_lock:
            if endpoint:
                error_ts = self._endpoint_errors_ts.get(endpoint, np.array([]))
                request_ts = self._endpoint_requests_ts.get(endpoint, np.array([]))
            else:
                error_ts = self._error_timestamps
                request_ts = self._request_timestamps

            # Filter to window
            recent_errors = error_ts[error_ts >= cutoff_time]
            recent_requests = request_ts[request_ts >= cutoff_time]

            # Create buckets
            num_buckets = int(self._window_size / bucket_seconds)
            buckets = []

            for i in range(num_buckets):
                bucket_start = cutoff_time + (i * bucket_seconds)
                bucket_end = bucket_start + bucket_seconds

                errors_in_bucket = np.sum(
                    (recent_errors >= bucket_start) & (recent_errors < bucket_end)
                )
                requests_in_bucket = np.sum(
                    (recent_requests >= bucket_start) & (recent_requests < bucket_end)
                )

                error_rate = (
                    (errors_in_bucket / requests_in_bucket) * 100.0
                    if requests_in_bucket > 0
                    else 0.0
                )

                buckets.append(
                    {
                        "timestamp": bucket_start,
                        "errors": int(errors_in_bucket),
                        "requests": int(requests_in_bucket),
                        "error_rate": error_rate,
                    }
                )

            return {
                "endpoint": endpoint or "overall",
                "bucket_seconds": bucket_seconds,
                "window_seconds": self._window_size,
                "buckets": buckets,
            }

    def get_top_errors(
        self, limit: int = 10, by: str = "frequency"
    ) -> list[dict[str, Any]]:
        """
        Get most frequent or recent errors.

        Args:
            limit: Maximum number of errors to return
            by: Sort method ('frequency', 'recent', or 'impact')

        Returns:
            List of error dictionaries with details
        """
        with self._pattern_lock:
            patterns = list(self._error_patterns.values())

            if by == "frequency":
                patterns.sort(key=lambda p: p.count, reverse=True)
            elif by == "recent":
                patterns.sort(key=lambda p: p.last_occurrence, reverse=True)
            elif by == "impact":
                # Impact = frequency × endpoints affected × recency factor
                current_time = time.time()
                patterns.sort(
                    key=lambda p: p.count
                    * len(p.affected_endpoints)
                    * (1.0 / (1.0 + (current_time - p.last_occurrence) / 3600)),
                    reverse=True,
                )

            top_patterns = patterns[:limit]

            return [
                {
                    "error_signature": p.error_signature,
                    "error_type": p.error_type,
                    "status_code": p.status_code,
                    "count": p.count,
                    "affected_endpoints": sorted(list(p.affected_endpoints)),
                    "affected_models": sorted(list(p.affected_models)),
                    "first_occurrence": p.first_occurrence,
                    "last_occurrence": p.last_occurrence,
                    "sample_messages": list(p.sample_messages),
                    "duration_seconds": p.last_occurrence - p.first_occurrence,
                }
                for p in top_patterns
            ]

    def get_error_distribution(self) -> dict[str, Any]:
        """
        Get error distribution by various dimensions.

        Returns:
            Dictionary with error counts by status code, type, endpoint, and model
        """
        with self._error_lock:
            return {
                "by_status_code": dict(self._status_code_counts),
                "by_error_type": dict(self._error_type_counts),
                "by_endpoint": dict(
                    sorted(
                        self._endpoint_errors.items(), key=lambda x: x[1], reverse=True
                    )[:20]
                ),
                "by_model": dict(
                    sorted(
                        self._model_errors.items(), key=lambda x: x[1], reverse=True
                    )[:20]
                ),
                "total_errors": len(self._error_history),
            }

    def get_error_correlations(self, limit: int = 10) -> list[dict[str, Any]]:
        """
        Get errors that frequently occur together.

        Args:
            limit: Maximum number of correlations to return

        Returns:
            List of correlated error pairs
        """
        with self._error_lock:
            correlations = sorted(
                self._error_correlations.items(), key=lambda x: x[1], reverse=True
            )[:limit]

            return [
                {
                    "error_pair": list(pair),
                    "occurrence_count": count,
                    "correlation_strength": min(
                        count / self._error_type_counts.get(pair[0], 1),
                        count / self._error_type_counts.get(pair[1], 1),
                    ),
                }
                for pair, count in correlations
            ]

    def get_recovery_metrics(self) -> dict[str, Any]:
        """
        Get error recovery and retry metrics.

        Returns:
            Dictionary with recovery statistics
        """
        with self._error_lock:
            time_to_recovery_list = list(self._recovery_metrics.time_to_recovery)

            if time_to_recovery_list:
                recovery_stats = {
                    "avg_seconds": float(np.mean(time_to_recovery_list)),
                    "min_seconds": float(np.min(time_to_recovery_list)),
                    "max_seconds": float(np.max(time_to_recovery_list)),
                    "p50_seconds": float(np.percentile(time_to_recovery_list, 50)),
                    "p90_seconds": float(np.percentile(time_to_recovery_list, 90)),
                    "p99_seconds": float(np.percentile(time_to_recovery_list, 99)),
                }
            else:
                recovery_stats = {
                    "avg_seconds": 0.0,
                    "min_seconds": 0.0,
                    "max_seconds": 0.0,
                    "p50_seconds": 0.0,
                    "p90_seconds": 0.0,
                    "p99_seconds": 0.0,
                }

            recovery_rate = (
                (
                    self._recovery_metrics.total_recoveries
                    / self._recovery_metrics.total_errors
                )
                * 100.0
                if self._recovery_metrics.total_errors > 0
                else 0.0
            )

            return {
                "total_errors": self._recovery_metrics.total_errors,
                "total_recoveries": self._recovery_metrics.total_recoveries,
                "recovery_rate_percentage": recovery_rate,
                "success_after_error": self._recovery_metrics.success_after_error,
                "pending_recoveries": len(self._pending_recovery),
                "time_to_recovery": recovery_stats,
                "retry_patterns": dict(self._recovery_metrics.retry_patterns),
            }

    def get_slo_status(self) -> dict[str, Any]:
        """
        Get SLO compliance status.

        Returns:
            Dictionary with SLO targets, current status, and budget consumption
        """
        current_error_rate = self.get_error_rate() / 100.0  # Convert to 0-1 range
        availability = 1.0 - current_error_rate

        # Calculate error budget
        error_budget_target = 1.0 - self._slo_config["availability_target"]
        if error_budget_target > 0:
            budget_consumed_pct = (current_error_rate / error_budget_target) * 100.0
        else:
            budget_consumed_pct = 0.0

        # Check compliance
        availability_compliant = availability >= self._slo_config["availability_target"]
        error_rate_compliant = (
            current_error_rate <= self._slo_config["error_rate_target"]
        )

        # Count recent violations
        current_time = time.time()
        recent_violations = sum(
            1
            for v in self._slo_violations
            if current_time - v.get("timestamp", 0) < 3600
        )

        return {
            "targets": {
                "availability": self._slo_config["availability_target"],
                "error_rate_max": self._slo_config["error_rate_target"],
                "error_budget_window_days": self._slo_config["error_budget_window"]
                / 86400,
            },
            "current_status": {
                "availability": availability,
                "error_rate": current_error_rate,
                "availability_compliant": availability_compliant,
                "error_rate_compliant": error_rate_compliant,
                "overall_compliant": availability_compliant and error_rate_compliant,
            },
            "error_budget": {
                "target": error_budget_target,
                "consumed_percentage": min(budget_consumed_pct, 100.0),
                "remaining_percentage": max(100.0 - budget_consumed_pct, 0.0),
            },
            "violations": {
                "total": len(self._slo_violations),
                "last_hour": recent_violations,
            },
        }

    def get_burst_events(self) -> list[dict[str, Any]]:
        """
        Get detected error burst events.

        Returns:
            List of error burst events with details
        """
        with self._error_lock:
            return list(self._burst_events)

    def get_all_metrics(self) -> dict[str, Any]:
        """
        Get comprehensive error metrics summary.

        Returns:
            Dictionary containing all error metrics categories
        """
        return {
            "summary": {
                "total_errors": len(self._error_history),
                "error_rate_percentage": self.get_error_rate(),
                "unique_error_patterns": len(self._error_patterns),
                "burst_events": len(self._burst_events),
            },
            "distribution": self.get_error_distribution(),
            "top_errors": self.get_top_errors(limit=10, by="impact"),
            "error_rate_over_time": self.get_error_rate_over_time(),
            "correlations": self.get_error_correlations(limit=10),
            "recovery": self.get_recovery_metrics(),
            "slo": self.get_slo_status(),
            "bursts": self.get_burst_events(),
        }

    def get_prometheus_metrics(self) -> str:
        """
        Export error metrics in Prometheus format.

        Returns:
            String containing Prometheus-formatted metrics
        """
        lines = []

        # Error rate by status code
        lines.append(
            "# HELP fakeai_errors_by_status_code Total errors by HTTP status code"
        )
        lines.append("# TYPE fakeai_errors_by_status_code counter")
        for status_code, count in self._status_code_counts.items():
            lines.append(
                f'fakeai_errors_by_status_code{{status_code="{status_code}"}} {count}'
            )

        # Error rate by type
        lines.append("# HELP fakeai_errors_by_type Total errors by error type")
        lines.append("# TYPE fakeai_errors_by_type counter")
        for error_type, count in self._error_type_counts.items():
            lines.append(f'fakeai_errors_by_type{{error_type="{error_type}"}} {count}')

        # Error rate by endpoint
        lines.append("# HELP fakeai_errors_by_endpoint Total errors by endpoint")
        lines.append("# TYPE fakeai_errors_by_endpoint counter")
        for endpoint, count in list(self._endpoint_errors.items())[:20]:
            lines.append(f'fakeai_errors_by_endpoint{{endpoint="{endpoint}"}} {count}')

        # Overall error rate
        lines.append(
            "# HELP fakeai_error_rate_percentage Current error rate percentage"
        )
        lines.append("# TYPE fakeai_error_rate_percentage gauge")
        lines.append(f"fakeai_error_rate_percentage {self.get_error_rate():.6f}")

        # SLO metrics
        slo_status = self.get_slo_status()
        lines.append("# HELP fakeai_availability Current availability")
        lines.append("# TYPE fakeai_availability gauge")
        lines.append(
            f"fakeai_availability {slo_status['current_status']['availability']:.6f}"
        )

        lines.append(
            "# HELP fakeai_error_budget_consumed_percentage Error budget consumed"
        )
        lines.append("# TYPE fakeai_error_budget_consumed_percentage gauge")
        lines.append(
            f"fakeai_error_budget_consumed_percentage {slo_status['error_budget']['consumed_percentage']:.6f}"
        )

        lines.append(
            "# HELP fakeai_slo_compliant SLO compliance status (1=compliant, 0=non-compliant)"
        )
        lines.append("# TYPE fakeai_slo_compliant gauge")
        lines.append(
            f"fakeai_slo_compliant {1 if slo_status['current_status']['overall_compliant'] else 0}"
        )

        # Recovery metrics
        recovery = self.get_recovery_metrics()
        lines.append("# HELP fakeai_error_recovery_rate_percentage Error recovery rate")
        lines.append("# TYPE fakeai_error_recovery_rate_percentage gauge")
        lines.append(
            f"fakeai_error_recovery_rate_percentage {recovery['recovery_rate_percentage']:.6f}"
        )

        lines.append(
            "# HELP fakeai_time_to_recovery_seconds Time to recover from errors"
        )
        lines.append("# TYPE fakeai_time_to_recovery_seconds summary")
        if recovery["time_to_recovery"]["avg_seconds"] > 0:
            lines.append(
                f'fakeai_time_to_recovery_seconds{{quantile="0.5"}} {recovery["time_to_recovery"]["p50_seconds"]:.6f}'
            )
            lines.append(
                f'fakeai_time_to_recovery_seconds{{quantile="0.9"}} {recovery["time_to_recovery"]["p90_seconds"]:.6f}'
            )
            lines.append(
                f'fakeai_time_to_recovery_seconds{{quantile="0.99"}} {recovery["time_to_recovery"]["p99_seconds"]:.6f}'
            )

        # Error burst events
        lines.append(
            "# HELP fakeai_error_burst_events Total error burst events detected"
        )
        lines.append("# TYPE fakeai_error_burst_events counter")
        lines.append(f"fakeai_error_burst_events {len(self._burst_events)}")

        return "\n".join(lines) + "\n"

    def _detect_error_pattern(self, event: ErrorEvent) -> None:
        """
        Detect and track recurring error patterns.

        Args:
            event: The error event to analyze
        """
        # Create error signature (simplified message)
        signature = self._create_error_signature(event.error_message, event.error_type)

        with self._pattern_lock:
            if signature in self._error_patterns:
                # Update existing pattern
                pattern = self._error_patterns[signature]
                pattern.count += 1
                pattern.last_occurrence = event.timestamp
                pattern.affected_endpoints.add(event.endpoint)
                if event.model:
                    pattern.affected_models.add(event.model)
                pattern.sample_messages.append(event.error_message)
            else:
                # Create new pattern
                pattern = ErrorPattern(
                    error_signature=signature,
                    error_type=event.error_type,
                    status_code=event.status_code,
                    first_occurrence=event.timestamp,
                    last_occurrence=event.timestamp,
                    count=1,
                )
                pattern.affected_endpoints.add(event.endpoint)
                if event.model:
                    pattern.affected_models.add(event.model)
                pattern.sample_messages.append(event.error_message)
                self._error_patterns[signature] = pattern

    def _create_error_signature(self, error_message: str, error_type: str) -> str:
        """
        Create a normalized signature for error message clustering.

        Args:
            error_message: The error message
            error_type: The error type

        Returns:
            Normalized error signature
        """
        # Simple signature: error_type + first 50 chars (normalized)
        normalized = error_message.lower().strip()[:50]
        # Remove numbers and special chars for better clustering
        import re

        normalized = re.sub(r"[0-9]+", "N", normalized)
        normalized = re.sub(r"[^a-z\s]", "", normalized)
        normalized = " ".join(normalized.split())  # Normalize whitespace

        return f"{error_type}:{normalized}"

    def _check_error_burst(self, current_time: float) -> None:
        """
        Check for error burst (high error rate in short time).

        Args:
            current_time: Current timestamp
        """
        # Count errors in last second
        with self._error_lock:
            recent_errors = np.sum(self._error_timestamps >= (current_time - 1.0))

            if recent_errors >= self._burst_threshold:
                # Burst detected
                burst_event = {
                    "timestamp": current_time,
                    "error_count": int(recent_errors),
                    "threshold": self._burst_threshold,
                    "duration_seconds": 1.0,
                }
                self._burst_events.append(burst_event)
                logger.warning(
                    f"Error burst detected: {recent_errors} errors in 1 second (threshold: {self._burst_threshold})"
                )

    def _detect_correlations(self, event: ErrorEvent) -> None:
        """
        Detect errors that occur together within a time window.

        Args:
            event: The error event to analyze
        """
        current_time = event.timestamp
        window_start = current_time - self._correlation_window_seconds

        with self._error_lock:
            # Find recent errors within correlation window
            recent_errors = [
                e
                for e in self._error_history
                if e.timestamp >= window_start and e.timestamp < current_time
            ]

            # Track correlations
            for other_error in recent_errors:
                if other_error.error_type != event.error_type:
                    # Create correlation key (sorted to avoid duplicates)
                    key = tuple(sorted([event.error_type, other_error.error_type]))
                    self._error_correlations[key] += 1

    def _check_slo_violation(self) -> None:
        """Check if current error rate violates SLO."""
        current_error_rate = self.get_error_rate() / 100.0
        availability = 1.0 - current_error_rate

        if availability < self._slo_config["availability_target"]:
            violation = {
                "timestamp": time.time(),
                "availability": availability,
                "target": self._slo_config["availability_target"],
                "error_rate": current_error_rate,
            }
            self._slo_violations.append(violation)
            logger.warning(
                f"SLO violation: Availability {availability:.4f} below target {self._slo_config['availability_target']:.4f}"
            )

    def _cleanup_timeseries(self) -> None:
        """Remove data older than the window size using vectorized operations."""
        current_time = time.time()
        cutoff_time = current_time - self._window_size

        # Cleanup main error timestamps
        if len(self._error_timestamps) > 0:
            valid_mask = self._error_timestamps >= cutoff_time
            self._error_timestamps = self._error_timestamps[valid_mask]

        # Cleanup success timestamps
        if len(self._success_timestamps) > 0:
            valid_mask = self._success_timestamps >= cutoff_time
            self._success_timestamps = self._success_timestamps[valid_mask]

        # Cleanup request timestamps
        if len(self._request_timestamps) > 0:
            valid_mask = self._request_timestamps >= cutoff_time
            self._request_timestamps = self._request_timestamps[valid_mask]

        # Cleanup per-endpoint timestamps
        for endpoint in list(self._endpoint_errors_ts.keys()):
            ts = self._endpoint_errors_ts[endpoint]
            if len(ts) > 0:
                valid_mask = ts >= cutoff_time
                self._endpoint_errors_ts[endpoint] = ts[valid_mask]

        for endpoint in list(self._endpoint_requests_ts.keys()):
            ts = self._endpoint_requests_ts[endpoint]
            if len(ts) > 0:
                valid_mask = ts >= cutoff_time
                self._endpoint_requests_ts[endpoint] = ts[valid_mask]

    def reset(self) -> None:
        """Reset all error metrics (for testing purposes)."""
        with self._error_lock:
            self._error_history.clear()
            self._status_code_counts.clear()
            self._error_type_counts.clear()
            self._endpoint_errors.clear()
            self._model_errors.clear()
            self._api_key_errors.clear()
            self._error_timestamps = np.array([], dtype=np.float64)
            self._success_timestamps = np.array([], dtype=np.float64)
            self._request_timestamps = np.array([], dtype=np.float64)
            self._endpoint_errors_ts.clear()
            self._endpoint_requests_ts.clear()
            self._burst_events.clear()
            self._pending_recovery.clear()
            self._slo_violations.clear()
            self._error_correlations.clear()

        with self._pattern_lock:
            self._error_patterns.clear()

        self._recovery_metrics = RecoveryMetrics()
        logger.info("Error metrics reset")
