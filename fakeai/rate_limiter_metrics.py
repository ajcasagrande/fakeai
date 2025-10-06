"""
Rate limiter metrics tracking module.

This module provides detailed tracking and analytics for rate limiting behavior,
including per-key metrics, quota tracking, throttling analytics, and tier statistics.
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
class KeyMetrics:
    """Metrics for a single API key."""

    api_key: str
    tier: str
    creation_time: float = field(default_factory=time.time)

    # Request tracking
    total_requests_attempted: int = 0
    total_requests_allowed: int = 0
    total_requests_throttled: int = 0

    # Token tracking
    total_tokens_consumed: int = 0
    total_tokens_requested: int = 0

    # Throttling tracking
    total_throttle_time_ms: float = 0.0
    throttle_events: deque = field(default_factory=lambda: deque(maxlen=100))

    # Usage patterns
    burst_requests: int = 0  # Requests in last second
    last_request_time: float = 0.0
    peak_rpm: float = 0.0
    peak_tpm: float = 0.0

    # Retry tracking
    retry_count: int = 0
    retry_after_values: deque = field(default_factory=lambda: deque(maxlen=50))

    # Quota snapshots (timestamp, rpm_remaining, tpm_remaining)
    quota_snapshots: deque = field(
        default_factory=lambda: deque(maxlen=60)
    )  # 1 per second for 1 minute


@dataclass
class ThrottleEvent:
    """Record of a single throttle event."""

    timestamp: float
    api_key: str
    retry_after_ms: float
    requested_tokens: int
    rpm_exceeded: bool
    tpm_exceeded: bool


class RateLimiterMetrics:
    """
    Singleton class to track detailed rate limiting behavior and patterns.

    Provides comprehensive analytics including per-key metrics, quota tracking,
    throttling analytics, tier statistics, and abuse pattern detection.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """Ensure only one instance exists (singleton pattern)."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(RateLimiterMetrics, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        """Initialize the rate limiter metrics tracker (only once)."""
        if self._initialized:
            return

        # Per-key metrics storage
        self._key_metrics: dict[str, KeyMetrics] = {}
        self._key_metrics_lock = threading.Lock()

        # Tier-level aggregation
        self._tier_assignments: dict[str, str] = {}  # api_key -> tier

        # Throttle events for analytics (last 1000 events)
        self._throttle_history: deque[ThrottleEvent] = deque(maxlen=1000)
        self._throttle_lock = threading.Lock()

        # Time-series data for burst detection
        self._request_timestamps: dict[str, deque] = defaultdict(
            lambda: deque(maxlen=100)
        )  # api_key -> recent timestamps

        # Quota utilization tracking (per-tier averages)
        self._tier_utilization: dict[str, dict[str, float]] = defaultdict(
            lambda: {"rpm_avg": 0.0, "tpm_avg": 0.0, "count": 0}
        )

        # Abuse pattern detection thresholds
        self._abuse_thresholds = {
            "high_throttle_rate": 0.5,  # >50% throttled requests
            "excessive_retries": 10,  # >10 retries in 60 seconds
            "burst_threshold": 20,  # >20 requests in 1 second
            "quota_exhaustion_rate": 0.95,  # >95% quota consumed
        }

        # Statistics windows (numpy-based for efficiency)
        self._window_size = 60.0  # 60 second window
        self._throttle_durations = np.array([], dtype=np.float64)
        self._throttle_timestamps = np.array([], dtype=np.float64)

        self._initialized = True
        logger.info("Rate limiter metrics initialized")

    def assign_tier(self, api_key: str, tier: str) -> None:
        """
        Assign a tier to an API key.

        Args:
            api_key: The API key
            tier: The tier name (free, tier-1, tier-2, etc.)
        """
        with self._key_metrics_lock:
            self._tier_assignments[api_key] = tier
            if api_key not in self._key_metrics:
                self._key_metrics[api_key] = KeyMetrics(api_key=api_key, tier=tier)
            else:
                self._key_metrics[api_key].tier = tier

    def record_request_attempt(
        self, api_key: str, allowed: bool, tokens: int, rpm_limit: int, tpm_limit: int
    ) -> None:
        """
        Record a rate limit check.

        Args:
            api_key: The API key making the request
            allowed: Whether the request was allowed
            tokens: Number of tokens requested
            rpm_limit: Current RPM limit for the key
            tpm_limit: Current TPM limit for the key
        """
        current_time = time.time()

        with self._key_metrics_lock:
            # Ensure key metrics exist
            if api_key not in self._key_metrics:
                tier = self._tier_assignments.get(api_key, "unknown")
                self._key_metrics[api_key] = KeyMetrics(api_key=api_key, tier=tier)

            metrics = self._key_metrics[api_key]

            # Update request counts
            metrics.total_requests_attempted += 1
            if allowed:
                metrics.total_requests_allowed += 1
                metrics.total_tokens_consumed += tokens
            else:
                metrics.total_requests_throttled += 1

            metrics.total_tokens_requested += tokens

            # Track burst behavior
            self._request_timestamps[api_key].append(current_time)
            recent_requests = sum(
                1
                for ts in self._request_timestamps[api_key]
                if current_time - ts <= 1.0
            )
            metrics.burst_requests = recent_requests

            # Update peak rates (estimate from recent window)
            if len(self._request_timestamps[api_key]) >= 2:
                timestamps = list(self._request_timestamps[api_key])
                time_span = current_time - timestamps[0]
                if time_span > 0:
                    rpm = len(timestamps) / time_span * 60
                    metrics.peak_rpm = max(metrics.peak_rpm, rpm)

            metrics.last_request_time = current_time

            # Take quota snapshot
            # This would need to be filled from the actual rate limiter
            # For now, we'll estimate based on allowed/throttled ratio
            if allowed and len(metrics.quota_snapshots) < 60:
                metrics.quota_snapshots.append(
                    (current_time, rpm_limit, tpm_limit - tokens)
                )

    def record_throttle(
        self,
        api_key: str,
        retry_after_ms: float,
        requested_tokens: int = 0,
        rpm_exceeded: bool = False,
        tpm_exceeded: bool = False,
    ) -> None:
        """
        Record a throttled request.

        Args:
            api_key: The API key that was throttled
            retry_after_ms: Milliseconds until retry
            requested_tokens: Number of tokens requested
            rpm_exceeded: Whether RPM limit was exceeded
            tpm_exceeded: Whether TPM limit was exceeded
        """
        current_time = time.time()

        with self._key_metrics_lock:
            if api_key in self._key_metrics:
                metrics = self._key_metrics[api_key]
                metrics.total_throttle_time_ms += retry_after_ms
                metrics.retry_after_values.append(retry_after_ms)

                # Record throttle event
                event = {
                    "timestamp": current_time,
                    "retry_after_ms": retry_after_ms,
                    "requested_tokens": requested_tokens,
                    "rpm_exceeded": rpm_exceeded,
                    "tpm_exceeded": tpm_exceeded,
                }
                metrics.throttle_events.append(event)

        # Record in global throttle history
        with self._throttle_lock:
            throttle_event = ThrottleEvent(
                timestamp=current_time,
                api_key=api_key,
                retry_after_ms=retry_after_ms,
                requested_tokens=requested_tokens,
                rpm_exceeded=rpm_exceeded,
                tpm_exceeded=tpm_exceeded,
            )
            self._throttle_history.append(throttle_event)

            # Update numpy arrays for efficient analytics
            self._throttle_durations = np.append(
                self._throttle_durations, retry_after_ms
            )
            self._throttle_timestamps = np.append(
                self._throttle_timestamps, current_time
            )

            # Cleanup old data
            self._cleanup_throttle_data()

    def record_retry(self, api_key: str) -> None:
        """
        Record a retry attempt.

        Args:
            api_key: The API key making the retry
        """
        with self._key_metrics_lock:
            if api_key in self._key_metrics:
                self._key_metrics[api_key].retry_count += 1

    def update_quota_snapshot(
        self, api_key: str, rpm_remaining: int, tpm_remaining: int
    ) -> None:
        """
        Update quota snapshot for an API key.

        Args:
            api_key: The API key
            rpm_remaining: Remaining requests per minute
            tpm_remaining: Remaining tokens per minute
        """
        current_time = time.time()

        with self._key_metrics_lock:
            if api_key in self._key_metrics:
                metrics = self._key_metrics[api_key]
                metrics.quota_snapshots.append(
                    (current_time, rpm_remaining, tpm_remaining)
                )

    def get_key_stats(self, api_key: str) -> dict[str, Any]:
        """
        Get statistics for a specific API key.

        Args:
            api_key: The API key to get stats for

        Returns:
            Dictionary containing detailed statistics
        """
        with self._key_metrics_lock:
            if api_key not in self._key_metrics:
                return {}

            metrics = self._key_metrics[api_key]

            # Calculate throttle rate
            throttle_rate = (
                metrics.total_requests_throttled / metrics.total_requests_attempted
                if metrics.total_requests_attempted > 0
                else 0.0
            )

            # Calculate average retry-after time
            avg_retry_after = (
                np.mean(list(metrics.retry_after_values))
                if metrics.retry_after_values
                else 0.0
            )

            # Calculate quota utilization from snapshots
            rpm_utilization = 0.0
            tpm_utilization = 0.0
            if metrics.quota_snapshots:
                # Get most recent snapshot
                _, rpm_remaining, tpm_remaining = metrics.quota_snapshots[-1]
                # Estimate utilization (this is approximate)
                if len(metrics.quota_snapshots) > 1:
                    _, rpm_start, tpm_start = metrics.quota_snapshots[0]
                    rpm_utilization = (
                        1.0 - (rpm_remaining / rpm_start) if rpm_start > 0 else 0.0
                    )
                    tpm_utilization = (
                        1.0 - (tpm_remaining / tpm_start) if tpm_start > 0 else 0.0
                    )

            # Calculate time in service
            time_in_service = time.time() - metrics.creation_time

            # Token efficiency (consumed vs requested)
            token_efficiency = (
                metrics.total_tokens_consumed / metrics.total_tokens_requested
                if metrics.total_tokens_requested > 0
                else 0.0
            )

            return {
                "api_key": api_key,
                "tier": metrics.tier,
                "time_in_service_seconds": time_in_service,
                "requests": {
                    "total_attempted": metrics.total_requests_attempted,
                    "total_allowed": metrics.total_requests_allowed,
                    "total_throttled": metrics.total_requests_throttled,
                    "throttle_rate": throttle_rate,
                    "success_rate": 1.0 - throttle_rate,
                },
                "tokens": {
                    "total_requested": metrics.total_tokens_requested,
                    "total_consumed": metrics.total_tokens_consumed,
                    "efficiency": token_efficiency,
                },
                "throttling": {
                    "total_throttle_time_ms": metrics.total_throttle_time_ms,
                    "avg_retry_after_ms": avg_retry_after,
                    "throttle_event_count": len(metrics.throttle_events),
                    "recent_retry_count": metrics.retry_count,
                },
                "usage_patterns": {
                    "current_burst_requests": metrics.burst_requests,
                    "peak_rpm": metrics.peak_rpm,
                    "peak_tpm": metrics.peak_tpm,
                    "last_request_time": metrics.last_request_time,
                },
                "quota_utilization": {
                    "rpm_utilization": rpm_utilization,
                    "tpm_utilization": tpm_utilization,
                },
            }

    def get_tier_stats(self) -> dict[str, dict[str, Any]]:
        """
        Get statistics aggregated by tier.

        Returns:
            Dictionary mapping tier names to aggregated statistics
        """
        with self._key_metrics_lock:
            tier_data: dict[str, dict[str, Any]] = defaultdict(
                lambda: {
                    "key_count": 0,
                    "total_requests_attempted": 0,
                    "total_requests_allowed": 0,
                    "total_requests_throttled": 0,
                    "total_tokens_consumed": 0,
                    "total_throttle_time_ms": 0.0,
                    "keys_with_high_throttle": 0,
                    "keys_with_exhaustion": 0,
                    "avg_throttle_rate": 0.0,
                    "peak_burst_requests": 0,
                }
            )

            for api_key, metrics in self._key_metrics.items():
                tier = metrics.tier
                data = tier_data[tier]

                data["key_count"] += 1
                data["total_requests_attempted"] += metrics.total_requests_attempted
                data["total_requests_allowed"] += metrics.total_requests_allowed
                data["total_requests_throttled"] += metrics.total_requests_throttled
                data["total_tokens_consumed"] += metrics.total_tokens_consumed
                data["total_throttle_time_ms"] += metrics.total_throttle_time_ms
                data["peak_burst_requests"] = max(
                    data["peak_burst_requests"], metrics.burst_requests
                )

                # Check for high throttle rate
                throttle_rate = (
                    metrics.total_requests_throttled / metrics.total_requests_attempted
                    if metrics.total_requests_attempted > 0
                    else 0.0
                )
                if throttle_rate > self._abuse_thresholds["high_throttle_rate"]:
                    data["keys_with_high_throttle"] += 1

                # Check for quota exhaustion
                if metrics.quota_snapshots:
                    _, rpm_remaining, tpm_remaining = metrics.quota_snapshots[-1]
                    if rpm_remaining == 0 or tpm_remaining < 100:
                        data["keys_with_exhaustion"] += 1

            # Calculate averages
            for tier, data in tier_data.items():
                if data["total_requests_attempted"] > 0:
                    data["avg_throttle_rate"] = (
                        data["total_requests_throttled"]
                        / data["total_requests_attempted"]
                    )
                else:
                    data["avg_throttle_rate"] = 0.0

                # Add upgrade opportunity detection
                data["upgrade_opportunities"] = (
                    data["keys_with_high_throttle"] + data["keys_with_exhaustion"]
                )

            return dict(tier_data)

    def get_throttle_analytics(self) -> dict[str, Any]:
        """
        Get detailed throttling analytics.

        Returns:
            Dictionary containing throttle duration histogram, retry-after distribution,
            and other throttling statistics
        """
        with self._throttle_lock:
            # Cleanup old data first
            self._cleanup_throttle_data()

            if len(self._throttle_durations) == 0:
                return {
                    "total_throttle_events": 0,
                    "duration_histogram": {},
                    "retry_after_distribution": {},
                    "rpm_vs_tpm_exceeded": {
                        "rpm_only": 0,
                        "tpm_only": 0,
                        "both": 0,
                    },
                }

            # Calculate duration histogram (buckets in milliseconds)
            histogram_buckets = [100, 500, 1000, 5000, 10000, 30000, 60000]
            histogram = {
                f"<{bucket}ms": np.sum(self._throttle_durations < bucket)
                for bucket in histogram_buckets
            }
            histogram[f">{histogram_buckets[-1]}ms"] = np.sum(
                self._throttle_durations >= histogram_buckets[-1]
            )

            # Retry-after percentiles
            retry_after_distribution = {
                "min": float(np.min(self._throttle_durations)),
                "max": float(np.max(self._throttle_durations)),
                "avg": float(np.mean(self._throttle_durations)),
                "median": float(np.median(self._throttle_durations)),
                "p90": float(np.percentile(self._throttle_durations, 90)),
                "p95": float(np.percentile(self._throttle_durations, 95)),
                "p99": float(np.percentile(self._throttle_durations, 99)),
            }

            # Analyze RPM vs TPM exceeded
            rpm_only = 0
            tpm_only = 0
            both = 0
            for event in self._throttle_history:
                if event.rpm_exceeded and event.tpm_exceeded:
                    both += 1
                elif event.rpm_exceeded:
                    rpm_only += 1
                elif event.tpm_exceeded:
                    tpm_only += 1

            return {
                "total_throttle_events": len(self._throttle_history),
                "duration_histogram": histogram,
                "retry_after_distribution": retry_after_distribution,
                "rpm_vs_tpm_exceeded": {
                    "rpm_only": rpm_only,
                    "tpm_only": tpm_only,
                    "both": both,
                },
            }

    def detect_abuse_patterns(self) -> list[dict[str, Any]]:
        """
        Detect potential abuse patterns across API keys.

        Returns:
            List of dictionaries describing detected abuse patterns
        """
        patterns = []
        current_time = time.time()

        with self._key_metrics_lock:
            for api_key, metrics in self._key_metrics.items():
                issues = []

                # Check high throttle rate
                throttle_rate = (
                    metrics.total_requests_throttled / metrics.total_requests_attempted
                    if metrics.total_requests_attempted > 0
                    else 0.0
                )
                if throttle_rate > self._abuse_thresholds["high_throttle_rate"]:
                    issues.append(
                        f"High throttle rate: {throttle_rate:.1%} (threshold: {self._abuse_thresholds['high_throttle_rate']:.1%})"
                    )

                # Check excessive retries (in last 60 seconds)
                recent_retries = sum(
                    1
                    for event in metrics.throttle_events
                    if current_time - event["timestamp"] <= 60
                )
                if recent_retries > self._abuse_thresholds["excessive_retries"]:
                    issues.append(
                        f"Excessive retries: {recent_retries} in last 60s (threshold: {self._abuse_thresholds['excessive_retries']})"
                    )

                # Check burst behavior
                if metrics.burst_requests > self._abuse_thresholds["burst_threshold"]:
                    issues.append(
                        f"Burst behavior: {metrics.burst_requests} requests/sec (threshold: {self._abuse_thresholds['burst_threshold']})"
                    )

                # Check quota exhaustion pattern
                if metrics.quota_snapshots:
                    exhaustion_count = sum(
                        1
                        for _, rpm_remaining, tpm_remaining in metrics.quota_snapshots
                        if rpm_remaining == 0 or tpm_remaining < 100
                    )
                    exhaustion_rate = exhaustion_count / len(metrics.quota_snapshots)
                    if (
                        exhaustion_rate
                        > self._abuse_thresholds["quota_exhaustion_rate"]
                    ):
                        issues.append(
                            f"Frequent quota exhaustion: {exhaustion_rate:.1%} of samples (threshold: {self._abuse_thresholds['quota_exhaustion_rate']:.1%})"
                        )

                if issues:
                    patterns.append(
                        {
                            "api_key": api_key,
                            "tier": metrics.tier,
                            "issues": issues,
                            "total_requests": metrics.total_requests_attempted,
                            "throttle_rate": throttle_rate,
                            "severity": (
                                "high" if len(issues) >= 3 else "medium"
                            ),  # 3+ issues = high severity
                        }
                    )

        return patterns

    def get_all_metrics(self) -> dict[str, Any]:
        """
        Get comprehensive metrics summary.

        Returns:
            Dictionary containing all metrics categories
        """
        return {
            "summary": {
                "total_keys": len(self._key_metrics),
                "total_throttle_events": len(self._throttle_history),
                "tiers": list(
                    set(m.tier for m in self._key_metrics.values() if m.tier)
                ),
            },
            "tier_stats": self.get_tier_stats(),
            "throttle_analytics": self.get_throttle_analytics(),
            "abuse_patterns": self.detect_abuse_patterns(),
        }

    def _cleanup_throttle_data(self) -> None:
        """Remove throttle data older than the window size."""
        current_time = time.time()
        cutoff_time = current_time - self._window_size

        if len(self._throttle_timestamps) > 0:
            valid_mask = self._throttle_timestamps >= cutoff_time
            self._throttle_durations = self._throttle_durations[valid_mask]
            self._throttle_timestamps = self._throttle_timestamps[valid_mask]

    def reset(self, api_key: str | None = None) -> None:
        """
        Reset metrics for testing purposes.

        Args:
            api_key: Specific API key to reset, or None to reset all
        """
        with self._key_metrics_lock:
            if api_key is None:
                self._key_metrics.clear()
                self._tier_assignments.clear()
                self._request_timestamps.clear()
            elif api_key in self._key_metrics:
                del self._key_metrics[api_key]
                if api_key in self._tier_assignments:
                    del self._tier_assignments[api_key]
                if api_key in self._request_timestamps:
                    del self._request_timestamps[api_key]

        if api_key is None:
            with self._throttle_lock:
                self._throttle_history.clear()
                self._throttle_durations = np.array([], dtype=np.float64)
                self._throttle_timestamps = np.array([], dtype=np.float64)
