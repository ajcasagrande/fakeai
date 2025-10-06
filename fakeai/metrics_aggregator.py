"""
Unified Metrics Aggregation Module.

Aggregates metrics from all sources (MetricsTracker, KV cache, DCGM, Dynamo)
into unified views with cross-system correlation, health scoring, and
time-series aggregation.
"""

import logging
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """System health status levels."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"


class TimeResolution(Enum):
    """Time-series resolution levels."""

    ONE_SECOND = "1s"
    ONE_MINUTE = "1m"
    ONE_HOUR = "1h"


@dataclass
class MetricDataPoint:
    """Single metric data point with timestamp."""

    timestamp: float
    value: float
    metric_name: str
    labels: dict[str, str] = field(default_factory=dict)


@dataclass
class HealthScore:
    """Health score for a subsystem."""

    score: float  # 0-100
    status: HealthStatus
    issues: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)


@dataclass
class CorrelatedMetrics:
    """Correlated metrics across systems."""

    metric_a: str
    metric_b: str
    correlation: float  # -1.0 to 1.0
    significance: float  # 0.0 to 1.0
    relationship: str  # positive, negative, none


class MetricsAggregator:
    """
    Unified metrics aggregation from all FakeAI metric sources.

    Provides:
    - Single unified metrics API
    - Cross-system metric correlation
    - Health scoring and anomaly detection
    - Time-series aggregation with multiple resolutions
    - Prometheus export for all metrics
    """

    def __init__(
        self,
        metrics_tracker=None,
        kv_metrics=None,
        dcgm_metrics=None,
        dynamo_metrics=None,
    ):
        """
        Initialize metrics aggregator.

        Args:
            metrics_tracker: MetricsTracker instance
            kv_metrics: KVCacheMetrics instance
            dcgm_metrics: DCGMMetricsSimulator instance
            dynamo_metrics: DynamoMetricsCollector instance
        """
        self.metrics_tracker = metrics_tracker
        self.kv_metrics = kv_metrics
        self.dcgm_metrics = dcgm_metrics
        self.dynamo_metrics = dynamo_metrics

        # Time-series storage (with automatic downsampling)
        self._time_series_1s: dict[str, deque[MetricDataPoint]] = defaultdict(
            lambda: deque(maxlen=3600)  # 1 hour at 1s resolution
        )
        self._time_series_1m: dict[str, deque[MetricDataPoint]] = defaultdict(
            lambda: deque(maxlen=1440)  # 24 hours at 1m resolution
        )
        self._time_series_1h: dict[str, deque[MetricDataPoint]] = defaultdict(
            lambda: deque(maxlen=168)  # 7 days at 1h resolution
        )

        # Aggregation state
        self._last_1s_sample = 0.0
        self._last_1m_sample = 0.0
        self._last_1h_sample = 0.0

        # Anomaly detection thresholds
        self.anomaly_thresholds = {
            "error_rate": 5.0,  # % errors
            "latency_p99": 10000.0,  # ms
            "cache_hit_rate": 20.0,  # minimum %
            "gpu_utilization": 95.0,  # maximum %
            "gpu_temperature": 85.0,  # celsius
        }

        # Health history
        self._health_history: deque[tuple[float, HealthScore]] = deque(maxlen=1000)

        self._lock = threading.Lock()

        # Start background aggregation
        self._stop_event = threading.Event()
        self._aggregation_thread = threading.Thread(
            target=self._aggregation_loop, daemon=True
        )
        self._aggregation_thread.start()

    def get_unified_metrics(self) -> dict[str, Any]:
        """
        Get all metrics from all sources in unified format.

        Returns:
            Dictionary containing all metrics organized by source
        """
        unified = {
            "timestamp": time.time(),
            "sources": {},
        }

        # Collect from MetricsTracker
        if self.metrics_tracker:
            try:
                unified["sources"][
                    "metrics_tracker"
                ] = self.metrics_tracker.get_metrics()
            except Exception as e:
                logger.error(f"Error getting metrics_tracker metrics: {e}")
                unified["sources"]["metrics_tracker"] = {"error": str(e)}

        # Collect from KV cache
        if self.kv_metrics:
            try:
                unified["sources"]["kv_cache"] = self.kv_metrics.get_stats()
            except Exception as e:
                logger.error(f"Error getting kv_metrics: {e}")
                unified["sources"]["kv_cache"] = {"error": str(e)}

        # Collect from DCGM
        if self.dcgm_metrics:
            try:
                unified["sources"]["dcgm"] = self.dcgm_metrics.get_metrics_dict()
            except Exception as e:
                logger.error(f"Error getting dcgm_metrics: {e}")
                unified["sources"]["dcgm"] = {"error": str(e)}

        # Collect from Dynamo
        if self.dynamo_metrics:
            try:
                unified["sources"]["dynamo"] = self.dynamo_metrics.get_stats_dict()
            except Exception as e:
                logger.error(f"Error getting dynamo_metrics: {e}")
                unified["sources"]["dynamo"] = {"error": str(e)}

        return unified

    def get_correlated_metrics(self) -> dict[str, Any]:
        """
        Get correlated metrics across systems.

        Returns:
            Dictionary containing correlated metrics and insights
        """
        correlations = []

        # Get recent data for correlation
        unified = self.get_unified_metrics()
        sources = unified.get("sources", {})

        # GPU utilization vs token throughput
        if "dcgm" in sources and "metrics_tracker" in sources:
            gpu_util = self._extract_avg_gpu_utilization(sources["dcgm"])
            token_rate = self._extract_token_throughput(sources["metrics_tracker"])

            if gpu_util is not None and token_rate is not None:
                # Calculate efficiency: tokens/sec per % GPU util
                efficiency = token_rate / gpu_util if gpu_util > 0 else 0.0

                correlations.append(
                    {
                        "metric_a": "gpu_utilization",
                        "metric_b": "token_throughput",
                        "values": {
                            "gpu_utilization_pct": gpu_util,
                            "tokens_per_second": token_rate,
                            "tokens_per_gpu_percent": efficiency,
                        },
                        "relationship": "positive",
                        "insight": f"GPU efficiency: {efficiency:.2f} tokens/sec per 1% GPU util",
                    }
                )

        # Cache hit rate vs latency improvement
        if "kv_cache" in sources and "dynamo" in sources:
            cache_hit_rate = sources["kv_cache"].get("cache_hit_rate", 0)
            latency_stats = sources["dynamo"].get("latency", {}).get("ttft", {})
            avg_ttft = latency_stats.get("avg", 0)

            # Estimate latency reduction from cache
            # Assuming cache hit reduces TTFT by ~50%
            estimated_reduction = (cache_hit_rate / 100.0) * 0.5 * avg_ttft

            correlations.append(
                {
                    "metric_a": "cache_hit_rate",
                    "metric_b": "ttft_latency",
                    "values": {
                        "cache_hit_rate_pct": cache_hit_rate,
                        "avg_ttft_ms": avg_ttft,
                        "estimated_latency_reduction_ms": estimated_reduction,
                    },
                    "relationship": "negative",
                    "insight": f"Cache saves ~{estimated_reduction:.2f}ms TTFT on average",
                }
            )

        # Queue depth vs TTFT
        if "dynamo" in sources:
            queue_stats = sources["dynamo"].get("queue", {})
            latency_stats = sources["dynamo"].get("latency", {}).get("ttft", {})

            queue_depth = queue_stats.get("current_depth", 0)
            avg_ttft = latency_stats.get("avg", 0)

            # Estimate queue impact (each queued request adds ~100ms)
            estimated_queue_impact = queue_depth * 100

            correlations.append(
                {
                    "metric_a": "queue_depth",
                    "metric_b": "ttft_latency",
                    "values": {
                        "queue_depth": queue_depth,
                        "avg_ttft_ms": avg_ttft,
                        "estimated_queue_impact_ms": estimated_queue_impact,
                    },
                    "relationship": "positive",
                    "insight": f"Queue adds ~{estimated_queue_impact:.0f}ms to TTFT",
                }
            )

        # Worker load vs response time
        if "dynamo" in sources and "metrics_tracker" in sources:
            batch_stats = sources["dynamo"].get("batch", {})
            latency_stats = sources["dynamo"].get("latency", {}).get("total", {})

            batch_size = batch_stats.get("current_size", 0)
            avg_latency = latency_stats.get("avg", 0)

            # Calculate per-request latency
            per_request_latency = (
                avg_latency / batch_size if batch_size > 0 else avg_latency
            )

            correlations.append(
                {
                    "metric_a": "batch_size",
                    "metric_b": "latency",
                    "values": {
                        "batch_size": batch_size,
                        "avg_total_latency_ms": avg_latency,
                        "per_request_latency_ms": per_request_latency,
                    },
                    "relationship": "batch_efficiency",
                    "insight": f"Batching: {per_request_latency:.2f}ms per request",
                }
            )

        return {
            "timestamp": time.time(),
            "correlations": correlations,
            "derived_metrics": self._calculate_derived_metrics(unified),
        }

    def _calculate_derived_metrics(self, unified: dict[str, Any]) -> dict[str, Any]:
        """Calculate derived efficiency metrics."""
        sources = unified.get("sources", {})
        derived = {}

        # Token efficiency = output_tokens / (latency_ms / 1000)
        if "dynamo" in sources:
            throughput = sources["dynamo"].get("throughput", {})
            latency = sources["dynamo"].get("latency", {}).get("total", {})

            tokens_per_sec = throughput.get("tokens_per_second", 0)
            avg_latency_sec = latency.get("avg", 0) / 1000.0

            if avg_latency_sec > 0:
                token_efficiency = tokens_per_sec
                derived["token_efficiency"] = {
                    "value": token_efficiency,
                    "unit": "tokens/second",
                    "description": "Token generation efficiency",
                }

        # Cache effectiveness = (cache_hit_rate * latency_reduction) / 100
        if "kv_cache" in sources and "dynamo" in sources:
            cache_hit_rate = sources["kv_cache"].get("cache_hit_rate", 0)
            latency_stats = sources["dynamo"].get("latency", {}).get("ttft", {})
            avg_ttft = latency_stats.get("avg", 0)

            # Estimate cache reduces TTFT by 50%
            latency_reduction_pct = 50.0
            cache_effectiveness = (cache_hit_rate * latency_reduction_pct) / 100.0

            derived["cache_effectiveness"] = {
                "value": cache_effectiveness,
                "unit": "percentage",
                "description": "Cache contribution to performance",
            }

        # GPU efficiency = tokens_per_second / gpu_utilization
        if "dcgm" in sources and "metrics_tracker" in sources:
            gpu_util = self._extract_avg_gpu_utilization(sources["dcgm"])
            token_rate = self._extract_token_throughput(sources["metrics_tracker"])

            if gpu_util and token_rate and gpu_util > 0:
                gpu_efficiency = token_rate / gpu_util

                derived["gpu_efficiency"] = {
                    "value": gpu_efficiency,
                    "unit": "tokens/sec per % GPU",
                    "description": "GPU compute efficiency",
                }

        # Cost efficiency = tokens_per_dollar (simulated: $1/GPU-hour)
        if "dcgm" in sources and "metrics_tracker" in sources:
            token_rate = self._extract_token_throughput(sources["metrics_tracker"])
            num_gpus = len(sources.get("dcgm", {})) - 1 if "dcgm" in sources else 1

            # Assume $1/GPU-hour
            cost_per_second = (num_gpus * 1.0) / 3600.0
            tokens_per_dollar = (
                (token_rate / cost_per_second) if cost_per_second > 0 else 0
            )

            derived["cost_efficiency"] = {
                "value": tokens_per_dollar,
                "unit": "tokens per dollar",
                "description": "Cost efficiency (assuming $1/GPU-hour)",
            }

        return derived

    def get_health_score(self) -> dict[str, Any]:
        """
        Calculate overall system health score.

        Returns:
            Dictionary with health scores per subsystem and overall
        """
        health_scores = {}
        issues = []
        recommendations = []

        # Get unified metrics
        unified = self.get_unified_metrics()
        sources = unified.get("sources", {})

        # Score API health (from metrics_tracker)
        if "metrics_tracker" in sources:
            api_health = self._score_api_health(sources["metrics_tracker"])
            health_scores["api"] = api_health
            issues.extend(api_health.issues)
            recommendations.extend(api_health.recommendations)

        # Score cache health (from kv_cache)
        if "kv_cache" in sources:
            cache_health = self._score_cache_health(sources["kv_cache"])
            health_scores["cache"] = cache_health
            issues.extend(cache_health.issues)
            recommendations.extend(cache_health.recommendations)

        # Score GPU health (from dcgm)
        if "dcgm" in sources:
            gpu_health = self._score_gpu_health(sources["dcgm"])
            health_scores["gpu"] = gpu_health
            issues.extend(gpu_health.issues)
            recommendations.extend(gpu_health.recommendations)

        # Score inference health (from dynamo)
        if "dynamo" in sources:
            inference_health = self._score_inference_health(sources["dynamo"])
            health_scores["inference"] = inference_health
            issues.extend(inference_health.issues)
            recommendations.extend(inference_health.recommendations)

        # Calculate overall health
        if health_scores:
            overall_score = sum(h.score for h in health_scores.values()) / len(
                health_scores
            )
            overall_status = self._score_to_status(overall_score)
        else:
            overall_score = 100.0
            overall_status = HealthStatus.HEALTHY

        overall = HealthScore(
            score=overall_score,
            status=overall_status,
            issues=issues,
            recommendations=recommendations,
        )

        # Store in history
        with self._lock:
            self._health_history.append((time.time(), overall))

        return {
            "timestamp": time.time(),
            "overall": {
                "score": overall.score,
                "status": overall.status.value,
                "issues": overall.issues,
                "recommendations": overall.recommendations,
            },
            "subsystems": {
                name: {
                    "score": health.score,
                    "status": health.status.value,
                    "issues": health.issues,
                    "recommendations": health.recommendations,
                }
                for name, health in health_scores.items()
            },
        }

    def _score_api_health(self, metrics: dict[str, Any]) -> HealthScore:
        """Score API health based on error rates and latency."""
        issues = []
        recommendations = []
        score = 100.0

        # Check error rate
        errors = metrics.get("errors", {})
        responses = metrics.get("responses", {})

        total_errors = sum(stats.get("rate", 0) for stats in errors.values())
        total_responses = sum(stats.get("rate", 0) for stats in responses.values())

        if total_responses > 0:
            error_rate = (total_errors / total_responses) * 100
        else:
            error_rate = 0.0

        if error_rate > self.anomaly_thresholds["error_rate"]:
            score -= 30
            issues.append(f"High error rate: {error_rate:.2f}%")
            recommendations.append("Investigate error logs and failing endpoints")

        # Check latency
        for endpoint, stats in responses.items():
            p99_latency_ms = stats.get("p99", 0) * 1000
            if p99_latency_ms > self.anomaly_thresholds["latency_p99"]:
                score -= 20
                issues.append(f"High p99 latency on {endpoint}: {p99_latency_ms:.0f}ms")
                recommendations.append(f"Optimize {endpoint} endpoint performance")

        score = max(0.0, score)
        status = self._score_to_status(score)

        return HealthScore(
            score=score, status=status, issues=issues, recommendations=recommendations
        )

    def _score_cache_health(self, metrics: dict[str, Any]) -> HealthScore:
        """Score cache health based on hit rate."""
        issues = []
        recommendations = []
        score = 100.0

        cache_hit_rate = metrics.get("cache_hit_rate", 100.0)

        if cache_hit_rate < self.anomaly_thresholds["cache_hit_rate"]:
            score -= 40
            issues.append(f"Low cache hit rate: {cache_hit_rate:.2f}%")
            recommendations.append("Review cache configuration and request patterns")

        score = max(0.0, score)
        status = self._score_to_status(score)

        return HealthScore(
            score=score, status=status, issues=issues, recommendations=recommendations
        )

    def _score_gpu_health(self, metrics: dict[str, Any]) -> HealthScore:
        """Score GPU health based on utilization and temperature."""
        issues = []
        recommendations = []
        score = 100.0

        for gpu_key, gpu_metrics in metrics.items():
            if not isinstance(gpu_metrics, dict):
                continue

            # Check utilization
            gpu_util = gpu_metrics.get("gpu_utilization_pct", 0)
            if gpu_util > self.anomaly_thresholds["gpu_utilization"]:
                score -= 10
                issues.append(f"{gpu_key}: High utilization {gpu_util}%")
                recommendations.append(f"Consider scaling {gpu_key}")

            # Check temperature
            temp = gpu_metrics.get("temperature_c", 0)
            if temp > self.anomaly_thresholds["gpu_temperature"]:
                score -= 20
                issues.append(f"{gpu_key}: High temperature {temp}°C")
                recommendations.append(f"Check cooling for {gpu_key}")

            # Check ECC errors
            ecc_dbe = gpu_metrics.get("ecc_dbe_total", 0)
            if ecc_dbe > 0:
                score -= 50
                issues.append(f"{gpu_key}: {ecc_dbe} double-bit ECC errors detected")
                recommendations.append(f"CRITICAL: Replace {gpu_key} immediately")

        score = max(0.0, score)
        status = self._score_to_status(score)

        return HealthScore(
            score=score, status=status, issues=issues, recommendations=recommendations
        )

    def _score_inference_health(self, metrics: dict[str, Any]) -> HealthScore:
        """Score inference health based on queue and latency."""
        issues = []
        recommendations = []
        score = 100.0

        # Check queue depth
        queue_stats = metrics.get("queue", {})
        queue_depth = queue_stats.get("current_depth", 0)
        max_queue = queue_stats.get("max_depth", 10)

        if queue_depth > max_queue * 0.8:
            score -= 30
            issues.append(f"Queue near capacity: {queue_depth}/{max_queue}")
            recommendations.append("Scale prefill workers or increase queue capacity")

        # Check TTFT
        latency_stats = metrics.get("latency", {}).get("ttft", {})
        p99_ttft = latency_stats.get("p99", 0)

        if p99_ttft > 5000:  # 5 seconds
            score -= 25
            issues.append(f"High p99 TTFT: {p99_ttft:.0f}ms")
            recommendations.append("Optimize prefill pipeline or add workers")

        score = max(0.0, score)
        status = self._score_to_status(score)

        return HealthScore(
            score=score, status=status, issues=issues, recommendations=recommendations
        )

    def _score_to_status(self, score: float) -> HealthStatus:
        """Convert numeric score to health status."""
        if score >= 90:
            return HealthStatus.HEALTHY
        elif score >= 70:
            return HealthStatus.DEGRADED
        elif score >= 40:
            return HealthStatus.UNHEALTHY
        else:
            return HealthStatus.CRITICAL

    def get_time_series(
        self, metric: str, resolution: str, duration: int
    ) -> list[dict[str, Any]]:
        """
        Get time-series data for a metric.

        Args:
            metric: Metric name (e.g., "gpu_utilization", "token_rate")
            resolution: Time resolution ("1s", "1m", "1h")
            duration: Duration in seconds

        Returns:
            List of data points with timestamp and value
        """
        resolution_enum = TimeResolution(resolution)

        # Select appropriate storage
        if resolution_enum == TimeResolution.ONE_SECOND:
            storage = self._time_series_1s
        elif resolution_enum == TimeResolution.ONE_MINUTE:
            storage = self._time_series_1m
        else:
            storage = self._time_series_1h

        with self._lock:
            if metric not in storage:
                return []

            # Filter by duration
            cutoff_time = time.time() - duration
            points = [
                {
                    "timestamp": point.timestamp,
                    "value": point.value,
                    "labels": point.labels,
                }
                for point in storage[metric]
                if point.timestamp >= cutoff_time
            ]

        return points

    def get_prometheus_unified(self) -> str:
        """
        Export all metrics in Prometheus format.

        Returns:
            String containing Prometheus-formatted metrics from all sources
        """
        lines = []

        # Add header
        lines.append("# FakeAI Unified Metrics")
        lines.append(f"# Generated at {time.time()}")
        lines.append("")

        # MetricsTracker metrics
        if self.metrics_tracker:
            try:
                lines.append("# MetricsTracker Metrics")
                lines.append(self.metrics_tracker.get_prometheus_metrics())
                lines.append("")
            except Exception as e:
                logger.error(f"Error exporting metrics_tracker: {e}")

        # DCGM metrics
        if self.dcgm_metrics:
            try:
                lines.append("# DCGM GPU Metrics")
                lines.append(self.dcgm_metrics.get_prometheus_metrics())
                lines.append("")
            except Exception as e:
                logger.error(f"Error exporting dcgm_metrics: {e}")

        # Dynamo metrics
        if self.dynamo_metrics:
            try:
                lines.append("# Dynamo Inference Metrics")
                lines.append(self.dynamo_metrics.get_prometheus_metrics())
                lines.append("")
            except Exception as e:
                logger.error(f"Error exporting dynamo_metrics: {e}")

        # Add derived metrics
        try:
            unified = self.get_unified_metrics()
            derived = self._calculate_derived_metrics(unified)

            lines.append("# Derived Efficiency Metrics")
            for metric_name, metric_data in derived.items():
                lines.append(f"# TYPE fakeai_derived_{metric_name} gauge")
                lines.append(
                    f"# HELP fakeai_derived_{metric_name} {metric_data['description']}"
                )
                lines.append(f"fakeai_derived_{metric_name} {metric_data['value']:.6f}")
                lines.append("")
        except Exception as e:
            logger.error(f"Error exporting derived metrics: {e}")

        # Add health scores
        try:
            health = self.get_health_score()

            lines.append("# Health Scores")
            lines.append("# TYPE fakeai_health_score gauge")
            lines.append(
                f"fakeai_health_score{{subsystem=\"overall\"}} {health['overall']['score']:.2f}"
            )

            for subsystem, score_data in health["subsystems"].items():
                lines.append(
                    f"fakeai_health_score{{subsystem=\"{subsystem}\"}} {score_data['score']:.2f}"
                )

            lines.append("")
        except Exception as e:
            logger.error(f"Error exporting health scores: {e}")

        return "\n".join(lines)

    def _aggregation_loop(self):
        """Background thread for time-series aggregation."""
        while not self._stop_event.is_set():
            try:
                current_time = time.time()

                # Sample at 1-second resolution
                if current_time - self._last_1s_sample >= 1.0:
                    self._sample_metrics(TimeResolution.ONE_SECOND)
                    self._last_1s_sample = current_time

                # Sample at 1-minute resolution
                if current_time - self._last_1m_sample >= 60.0:
                    self._sample_metrics(TimeResolution.ONE_MINUTE)
                    self._last_1m_sample = current_time

                # Sample at 1-hour resolution
                if current_time - self._last_1h_sample >= 3600.0:
                    self._sample_metrics(TimeResolution.ONE_HOUR)
                    self._last_1h_sample = current_time

                time.sleep(1.0)

            except Exception as e:
                logger.error(f"Error in aggregation loop: {e}")

    def _sample_metrics(self, resolution: TimeResolution):
        """Sample current metrics and store in time-series."""
        try:
            unified = self.get_unified_metrics()
            sources = unified.get("sources", {})
            timestamp = time.time()

            # Select storage
            if resolution == TimeResolution.ONE_SECOND:
                storage = self._time_series_1s
            elif resolution == TimeResolution.ONE_MINUTE:
                storage = self._time_series_1m
            else:
                storage = self._time_series_1h

            # Sample GPU metrics
            if "dcgm" in sources:
                gpu_util = self._extract_avg_gpu_utilization(sources["dcgm"])
                if gpu_util is not None:
                    with self._lock:
                        storage["gpu_utilization"].append(
                            MetricDataPoint(timestamp, gpu_util, "gpu_utilization")
                        )

            # Sample token throughput
            if "metrics_tracker" in sources:
                token_rate = self._extract_token_throughput(sources["metrics_tracker"])
                if token_rate is not None:
                    with self._lock:
                        storage["token_throughput"].append(
                            MetricDataPoint(timestamp, token_rate, "token_throughput")
                        )

            # Sample cache hit rate
            if "kv_cache" in sources:
                cache_hit_rate = sources["kv_cache"].get("cache_hit_rate", 0)
                with self._lock:
                    storage["cache_hit_rate"].append(
                        MetricDataPoint(timestamp, cache_hit_rate, "cache_hit_rate")
                    )

            # Sample queue depth
            if "dynamo" in sources:
                queue_depth = sources["dynamo"].get("queue", {}).get("current_depth", 0)
                with self._lock:
                    storage["queue_depth"].append(
                        MetricDataPoint(timestamp, float(queue_depth), "queue_depth")
                    )

        except Exception as e:
            logger.error(f"Error sampling metrics: {e}")

    def _extract_avg_gpu_utilization(
        self, dcgm_metrics: dict[str, Any]
    ) -> float | None:
        """Extract average GPU utilization from DCGM metrics."""
        utilizations = []
        for key, gpu_data in dcgm_metrics.items():
            if isinstance(gpu_data, dict) and "gpu_utilization_pct" in gpu_data:
                utilizations.append(gpu_data["gpu_utilization_pct"])

        if utilizations:
            return sum(utilizations) / len(utilizations)
        return None

    def _extract_token_throughput(self, metrics: dict[str, Any]) -> float | None:
        """Extract total token throughput from metrics."""
        tokens = metrics.get("tokens", {})
        total_rate = sum(stats.get("rate", 0) for stats in tokens.values())
        return total_rate if total_rate > 0 else None

    def shutdown(self):
        """Stop background aggregation thread."""
        self._stop_event.set()
        if self._aggregation_thread.is_alive():
            self._aggregation_thread.join(timeout=2.0)
