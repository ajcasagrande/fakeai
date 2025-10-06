#!/usr/bin/env python3
"""
FakeAI Latency Histogram Tracking

This module provides accurate latency distribution tracking using histogram buckets
for precise percentile calculation without storing individual samples.
"""
#  SPDX-License-Identifier: Apache-2.0

import logging
import math
import threading
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


# Logarithmic bucket boundaries in milliseconds
# These cover the range from 1ms to 10s with good granularity
HISTOGRAM_BUCKETS = [
    1.0,  # 1ms
    2.0,  # 2ms
    5.0,  # 5ms
    10.0,  # 10ms
    20.0,  # 20ms
    50.0,  # 50ms
    100.0,  # 100ms
    200.0,  # 200ms
    500.0,  # 500ms
    1000.0,  # 1s
    2000.0,  # 2s
    5000.0,  # 5s
    10000.0,  # 10s
    float("inf"),  # Catch-all for anything above 10s
]


@dataclass
class LatencyHistogram:
    """
    Thread-safe histogram for tracking latency distributions.

    Uses logarithmic buckets for efficient memory usage and accurate
    percentile calculation via linear interpolation.
    """

    buckets: List[float] = field(default_factory=lambda: list(HISTOGRAM_BUCKETS))
    _lock: threading.Lock = field(default_factory=threading.Lock)
    _counts: List[int] = field(default_factory=lambda: [0] * len(HISTOGRAM_BUCKETS))
    _total_count: int = 0
    _sum: float = 0.0
    _sum_squares: float = 0.0
    _min: float = float("inf")
    _max: float = 0.0

    def record(self, latency_ms: float) -> None:
        """
        Record a latency sample.

        Args:
            latency_ms: Latency in milliseconds
        """
        with self._lock:
            # Find the appropriate bucket using binary search
            bucket_idx = self._find_bucket(latency_ms)
            self._counts[bucket_idx] += 1

            # Update statistics
            self._total_count += 1
            self._sum += latency_ms
            self._sum_squares += latency_ms * latency_ms
            self._min = min(self._min, latency_ms)
            self._max = max(self._max, latency_ms)

    def _find_bucket(self, latency_ms: float) -> int:
        """
        Find the bucket index for a given latency using binary search.

        Args:
            latency_ms: Latency in milliseconds

        Returns:
            Bucket index
        """
        left, right = 0, len(self.buckets) - 1

        while left < right:
            mid = (left + right) // 2
            if latency_ms <= self.buckets[mid]:
                right = mid
            else:
                left = mid + 1

        return left

    def get_percentile(self, percentile: float) -> float:
        """
        Get latency at a specific percentile using linear interpolation.

        Args:
            percentile: Percentile (0.0-100.0)

        Returns:
            Latency in milliseconds at the given percentile
        """
        with self._lock:
            if self._total_count == 0:
                return 0.0

            # Calculate target rank
            target_rank = (percentile / 100.0) * self._total_count

            # Find the bucket containing the target rank
            cumulative_count = 0
            for i, count in enumerate(self._counts):
                cumulative_count += count

                if cumulative_count >= target_rank:
                    # Linear interpolation within the bucket
                    if count == 0:
                        # Empty bucket, use bucket boundary
                        return self.buckets[i]

                    # Calculate position within bucket
                    bucket_start = self.buckets[i - 1] if i > 0 else 0.0
                    bucket_end = self.buckets[i]

                    # Calculate how far into the bucket we are
                    prev_cumulative = cumulative_count - count
                    position_in_bucket = (target_rank - prev_cumulative) / count

                    # Linear interpolation
                    return bucket_start + position_in_bucket * (
                        bucket_end - bucket_start
                    )

            # Should not reach here, but return max if we do
            return self._max

    def get_percentiles(self, percentiles: List[float]) -> Dict[float, float]:
        """
        Get multiple percentiles efficiently.

        Args:
            percentiles: List of percentiles (0.0-100.0)

        Returns:
            Dictionary mapping percentile to latency in milliseconds
        """
        return {p: self.get_percentile(p) for p in percentiles}

    def get_mean(self) -> float:
        """Get mean latency in milliseconds."""
        with self._lock:
            if self._total_count == 0:
                return 0.0
            return self._sum / self._total_count

    def get_median(self) -> float:
        """Get median latency (p50) in milliseconds."""
        return self.get_percentile(50.0)

    def get_mode(self) -> float | None:
        """
        Get mode (most frequent bucket midpoint) in milliseconds.

        Returns:
            Mode latency or None if no data
        """
        with self._lock:
            if self._total_count == 0:
                return None

            # Find bucket with highest count
            max_count = 0
            max_bucket_idx = 0

            for i, count in enumerate(self._counts):
                if count > max_count:
                    max_count = count
                    max_bucket_idx = i

            # Return midpoint of the modal bucket
            bucket_start = (
                self.buckets[max_bucket_idx - 1] if max_bucket_idx > 0 else 0.0
            )
            bucket_end = self.buckets[max_bucket_idx]

            return (bucket_start + bucket_end) / 2.0

    def get_std_dev(self) -> float:
        """Get standard deviation in milliseconds."""
        with self._lock:
            if self._total_count == 0:
                return 0.0

            mean = self._sum / self._total_count
            variance = (self._sum_squares / self._total_count) - (mean * mean)

            # Handle floating point precision issues
            if variance < 0:
                variance = 0

            return math.sqrt(variance)

    def get_coefficient_of_variation(self) -> float:
        """
        Get coefficient of variation (CV = std_dev / mean).

        Returns:
            CV value (0.0-1.0+), or 0.0 if mean is zero
        """
        mean = self.get_mean()
        if mean == 0:
            return 0.0

        return self.get_std_dev() / mean

    def get_skewness(self) -> float:
        """
        Get skewness using Pearson's second skewness coefficient.

        Returns:
            Skewness value (negative = left-skewed, positive = right-skewed)
        """
        mean = self.get_mean()
        median = self.get_median()
        std_dev = self.get_std_dev()

        if std_dev == 0:
            return 0.0

        # Pearson's second skewness coefficient: 3 * (mean - median) / std_dev
        return 3.0 * (mean - median) / std_dev

    def get_stats(self) -> Dict[str, float]:
        """
        Get comprehensive statistics.

        Returns:
            Dictionary containing all statistical metrics
        """
        with self._lock:
            if self._total_count == 0:
                return {
                    "count": 0,
                    "mean": 0.0,
                    "median": 0.0,
                    "mode": 0.0,
                    "std_dev": 0.0,
                    "cv": 0.0,
                    "skewness": 0.0,
                    "min": 0.0,
                    "max": 0.0,
                    "p50": 0.0,
                    "p75": 0.0,
                    "p90": 0.0,
                    "p95": 0.0,
                    "p99": 0.0,
                    "p99.9": 0.0,
                    "p99.99": 0.0,
                }

        # Calculate percentiles
        percentiles = self.get_percentiles([50.0, 75.0, 90.0, 95.0, 99.0, 99.9, 99.99])

        mode = self.get_mode()

        return {
            "count": self._total_count,
            "mean": self.get_mean(),
            "median": self.get_median(),
            "mode": mode if mode is not None else 0.0,
            "std_dev": self.get_std_dev(),
            "cv": self.get_coefficient_of_variation(),
            "skewness": self.get_skewness(),
            "min": self._min if self._min != float("inf") else 0.0,
            "max": self._max,
            "p50": percentiles[50.0],
            "p75": percentiles[75.0],
            "p90": percentiles[90.0],
            "p95": percentiles[95.0],
            "p99": percentiles[99.0],
            "p99.9": percentiles[99.9],
            "p99.99": percentiles[99.99],
        }

    def detect_anomalies(self) -> List[Dict[str, Any]]:
        """
        Detect latency anomalies.

        Returns:
            List of anomaly descriptions
        """
        anomalies = []

        with self._lock:
            if self._total_count == 0:
                return anomalies

        mean = self.get_mean()
        std_dev = self.get_std_dev()

        # Detect outliers (> 3σ from mean)
        # For histogram data, we check if any buckets beyond mean+3σ have samples
        if std_dev > 0:
            outlier_threshold = mean + 3 * std_dev

            # Count samples in buckets that exceed 3σ threshold
            outlier_count = 0
            for i, count in enumerate(self._counts):
                if count == 0:
                    continue

                # Check bucket midpoint against threshold
                bucket_start = self.buckets[i - 1] if i > 0 else 0.0
                bucket_end = self.buckets[i]

                # If bucket midpoint is beyond threshold, count as outliers
                bucket_midpoint = (bucket_start + bucket_end) / 2.0
                if bucket_midpoint > outlier_threshold:
                    outlier_count += count

            if outlier_count > 0:
                outlier_percentage = (outlier_count / self._total_count) * 100
                anomalies.append(
                    {
                        "type": "outliers",
                        "description": f"{outlier_count} samples ({outlier_percentage:.2f}%) exceed 3σ threshold",
                        "threshold_ms": outlier_threshold,
                        "count": outlier_count,
                        "percentage": outlier_percentage,
                    }
                )

        # Detect bimodal distribution
        # Look for two peaks with a valley between them
        peaks = []
        with self._lock:
            for i in range(1, len(self._counts) - 1):
                # A peak is where count is greater than both neighbors
                if (
                    self._counts[i] > self._counts[i - 1]
                    and self._counts[i] > self._counts[i + 1]
                ):
                    # Only consider significant peaks (> 5% of total)
                    if self._counts[i] > self._total_count * 0.05:
                        bucket_midpoint = (
                            (self.buckets[i - 1] + self.buckets[i]) / 2.0
                            if i > 0
                            else self.buckets[i] / 2.0
                        )
                        peaks.append((i, bucket_midpoint, self._counts[i]))

        if len(peaks) >= 2:
            # Check if there's a valley between the first two peaks
            peak1_idx, peak1_value, peak1_count = peaks[0]
            peak2_idx, peak2_value, peak2_count = peaks[1]

            # Find minimum count between peaks
            min_count = min(self._counts[peak1_idx + 1 : peak2_idx])

            # Bimodal if valley is significantly lower than both peaks
            if min_count < peak1_count * 0.5 and min_count < peak2_count * 0.5:
                anomalies.append(
                    {
                        "type": "bimodal",
                        "description": f"Bimodal distribution detected with peaks at {peak1_value:.2f}ms and {peak2_value:.2f}ms",
                        "peak1_ms": peak1_value,
                        "peak2_ms": peak2_value,
                        "peak1_count": peak1_count,
                        "peak2_count": peak2_count,
                    }
                )

        # Detect latency spikes (p99 >> p50)
        p50 = self.get_percentile(50.0)
        p99 = self.get_percentile(99.0)

        if p50 > 0 and p99 / p50 > 10:
            anomalies.append(
                {
                    "type": "latency_spike",
                    "description": f"Latency spike detected: p99 ({p99:.2f}ms) is {p99/p50:.1f}x higher than p50 ({p50:.2f}ms)",
                    "p50_ms": p50,
                    "p99_ms": p99,
                    "ratio": p99 / p50,
                }
            )

        return anomalies

    def get_histogram_data(self) -> Dict[str, Any]:
        """
        Get raw histogram data for plotting.

        Returns:
            Dictionary containing bucket boundaries and counts
        """
        with self._lock:
            return {
                "buckets": list(self.buckets),
                "counts": list(self._counts),
                "total_count": self._total_count,
                "bucket_edges": [
                    (self.buckets[i - 1] if i > 0 else 0.0, self.buckets[i])
                    for i in range(len(self.buckets))
                ],
            }

    def reset(self) -> None:
        """Reset all histogram data."""
        with self._lock:
            self._counts = [0] * len(self.buckets)
            self._total_count = 0
            self._sum = 0.0
            self._sum_squares = 0.0
            self._min = float("inf")
            self._max = 0.0


class LatencyHistogramTracker:
    """
    Thread-safe tracker for multiple latency histograms.

    Maintains separate histograms per endpoint and per model for
    detailed latency analysis.
    """

    def __init__(self):
        """Initialize the histogram tracker."""
        self._endpoint_histograms: Dict[str, LatencyHistogram] = defaultdict(
            LatencyHistogram
        )
        self._model_histograms: Dict[str, LatencyHistogram] = defaultdict(
            LatencyHistogram
        )
        self._lock = threading.Lock()

    def record_latency(
        self, latency_ms: float, endpoint: str | None = None, model: str | None = None
    ) -> None:
        """
        Record a latency sample.

        Args:
            latency_ms: Latency in milliseconds
            endpoint: Optional endpoint identifier
            model: Optional model identifier
        """
        with self._lock:
            if endpoint:
                self._endpoint_histograms[endpoint].record(latency_ms)

            if model:
                self._model_histograms[model].record(latency_ms)

    def get_endpoint_stats(self, endpoint: str) -> Dict[str, float]:
        """
        Get statistics for a specific endpoint.

        Args:
            endpoint: Endpoint identifier

        Returns:
            Statistics dictionary
        """
        with self._lock:
            if endpoint not in self._endpoint_histograms:
                return {}
            return self._endpoint_histograms[endpoint].get_stats()

    def get_model_stats(self, model: str) -> Dict[str, float]:
        """
        Get statistics for a specific model.

        Args:
            model: Model identifier

        Returns:
            Statistics dictionary
        """
        with self._lock:
            if model not in self._model_histograms:
                return {}
            return self._model_histograms[model].get_stats()

    def get_all_endpoint_stats(self) -> Dict[str, Dict[str, float]]:
        """
        Get statistics for all endpoints.

        Returns:
            Dictionary mapping endpoint to statistics
        """
        with self._lock:
            return {
                endpoint: histogram.get_stats()
                for endpoint, histogram in self._endpoint_histograms.items()
            }

    def get_all_model_stats(self) -> Dict[str, Dict[str, float]]:
        """
        Get statistics for all models.

        Returns:
            Dictionary mapping model to statistics
        """
        with self._lock:
            return {
                model: histogram.get_stats()
                for model, histogram in self._model_histograms.items()
            }

    def detect_endpoint_anomalies(self, endpoint: str) -> List[Dict[str, Any]]:
        """
        Detect anomalies for a specific endpoint.

        Args:
            endpoint: Endpoint identifier

        Returns:
            List of anomaly descriptions
        """
        with self._lock:
            if endpoint not in self._endpoint_histograms:
                return []
            return self._endpoint_histograms[endpoint].detect_anomalies()

    def detect_model_anomalies(self, model: str) -> List[Dict[str, Any]]:
        """
        Detect anomalies for a specific model.

        Args:
            model: Model identifier

        Returns:
            List of anomaly descriptions
        """
        with self._lock:
            if model not in self._model_histograms:
                return []
            return self._model_histograms[model].detect_anomalies()

    def get_endpoint_histogram_data(self, endpoint: str) -> Dict[str, Any]:
        """
        Get histogram data for a specific endpoint.

        Args:
            endpoint: Endpoint identifier

        Returns:
            Histogram data dictionary
        """
        with self._lock:
            if endpoint not in self._endpoint_histograms:
                return {}
            return self._endpoint_histograms[endpoint].get_histogram_data()

    def get_model_histogram_data(self, model: str) -> Dict[str, Any]:
        """
        Get histogram data for a specific model.

        Args:
            model: Model identifier

        Returns:
            Histogram data dictionary
        """
        with self._lock:
            if model not in self._model_histograms:
                return {}
            return self._model_histograms[model].get_histogram_data()

    def get_prometheus_metrics(self) -> str:
        """
        Export histogram metrics in Prometheus format.

        Returns:
            Prometheus-formatted metrics
        """
        lines = []

        # Endpoint histogram metrics
        with self._lock:
            if self._endpoint_histograms:
                lines.append(
                    "# HELP fakeai_latency_histogram_seconds Latency distribution by endpoint"
                )
                lines.append("# TYPE fakeai_latency_histogram_seconds histogram")

                for endpoint, histogram in self._endpoint_histograms.items():
                    data = histogram.get_histogram_data()
                    cumulative = 0

                    for i, (count, bucket) in enumerate(
                        zip(data["counts"], data["buckets"])
                    ):
                        cumulative += count
                        bucket_seconds = bucket / 1000.0  # Convert ms to seconds

                        # Skip infinity bucket in Prometheus format
                        if bucket != float("inf"):
                            lines.append(
                                f'fakeai_latency_histogram_seconds_bucket{{endpoint="{endpoint}",le="{bucket_seconds:.6f}"}} {cumulative}'
                            )

                    # Add +Inf bucket
                    lines.append(
                        f'fakeai_latency_histogram_seconds_bucket{{endpoint="{endpoint}",le="+Inf"}} {data["total_count"]}'
                    )

                    # Add sum and count
                    stats = histogram.get_stats()
                    lines.append(
                        f'fakeai_latency_histogram_seconds_sum{{endpoint="{endpoint}"}} {stats["mean"] * stats["count"] / 1000.0:.6f}'
                    )
                    lines.append(
                        f'fakeai_latency_histogram_seconds_count{{endpoint="{endpoint}"}} {stats["count"]}'
                    )

        return "\n".join(lines) + "\n"

    def reset(self) -> None:
        """Reset all histogram data."""
        with self._lock:
            for histogram in self._endpoint_histograms.values():
                histogram.reset()
            for histogram in self._model_histograms.values():
                histogram.reset()
