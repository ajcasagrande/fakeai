"""
Tests for Unified Metrics Aggregator.

Tests unified metrics API, cross-system correlation, health scoring,
time-series aggregation, and Prometheus export.
"""

import time
from unittest.mock import MagicMock, Mock

import pytest

from fakeai.metrics_aggregator import (
    CorrelatedMetrics,
    HealthScore,
    HealthStatus,
    MetricDataPoint,
    MetricsAggregator,
    TimeResolution,
)


@pytest.fixture
def mock_metrics_tracker():
    """Create mock MetricsTracker."""
    tracker = Mock()
    tracker.get_metrics.return_value = {
        "requests": {
            "/v1/chat/completions": {
                "rate": 10.0,
                "avg": 0.0,
                "min": 0.0,
                "max": 0.0,
                "p50": 0.0,
                "p90": 0.0,
                "p99": 0.0,
            }
        },
        "responses": {
            "/v1/chat/completions": {
                "rate": 9.5,
                "avg": 0.5,
                "min": 0.1,
                "max": 2.0,
                "p50": 0.4,
                "p90": 1.0,
                "p99": 1.8,
            }
        },
        "tokens": {
            "/v1/chat/completions": {
                "rate": 500.0,
                "avg": 0.0,
                "min": 0.0,
                "max": 0.0,
                "p50": 0.0,
                "p90": 0.0,
                "p99": 0.0,
            }
        },
        "errors": {
            "/v1/chat/completions": {
                "rate": 0.5,
                "avg": 0.0,
                "min": 0.0,
                "max": 0.0,
                "p50": 0.0,
                "p90": 0.0,
                "p99": 0.0,
            }
        },
        "streaming_stats": {"active_streams": 5},
    }
    tracker.get_prometheus_metrics.return_value = (
        "# MetricsTracker metrics\nfakeai_requests_per_second 10.0\n"
    )
    return tracker


@pytest.fixture
def mock_kv_metrics():
    """Create mock KVCacheMetrics."""
    metrics = Mock()
    metrics.get_stats.return_value = {
        "cache_hit_rate": 75.0,
        "token_reuse_rate": 60.0,
        "total_cache_hits": 750,
        "total_cache_misses": 250,
        "total_tokens_processed": 50000,
        "cached_tokens_reused": 30000,
        "average_prefix_length": 128.0,
    }
    return metrics


@pytest.fixture
def mock_dcgm_metrics():
    """Create mock DCGMMetricsSimulator."""
    dcgm = Mock()
    dcgm.get_metrics_dict.return_value = {
        "gpu_0": {
            "gpu_id": 0,
            "name": "NVIDIA H100",
            "gpu_utilization_pct": 80,
            "temperature_c": 75,
            "power_usage_w": 400.0,
            "memory_used_mib": 40960,
            "memory_total_mib": 81920,
            "ecc_sbe_total": 0,
            "ecc_dbe_total": 0,
        },
        "gpu_1": {
            "gpu_id": 1,
            "name": "NVIDIA H100",
            "gpu_utilization_pct": 85,
            "temperature_c": 78,
            "power_usage_w": 420.0,
            "memory_used_mib": 45056,
            "memory_total_mib": 81920,
            "ecc_sbe_total": 0,
            "ecc_dbe_total": 0,
        },
    }
    dcgm.get_prometheus_metrics.return_value = (
        "# DCGM metrics\nDCGM_FI_DEV_GPU_UTIL 80\n"
    )
    return dcgm


@pytest.fixture
def mock_dynamo_metrics():
    """Create mock DynamoMetricsCollector."""
    dynamo = Mock()
    dynamo.get_stats_dict.return_value = {
        "summary": {
            "total_requests": 1000,
            "successful_requests": 950,
            "failed_requests": 50,
            "active_requests": 10,
        },
        "latency": {
            "ttft": {"avg": 500.0, "p50": 450.0, "p90": 800.0, "p99": 1200.0},
            "itl": {"avg": 50.0, "p50": 45.0, "p90": 80.0, "p99": 120.0},
            "total": {"avg": 2000.0, "p50": 1800.0, "p90": 3000.0, "p99": 5000.0},
        },
        "throughput": {
            "requests_per_second": 10.0,
            "tokens_per_second": 500.0,
            "input_tokens_per_second": 200.0,
            "output_tokens_per_second": 300.0,
        },
        "queue": {
            "current_depth": 5,
            "max_depth": 20,
            "avg_depth": 8.0,
        },
        "batch": {
            "current_size": 8,
            "avg_size": 7.5,
            "max_size": 16,
        },
        "cache": {
            "hit_rate": 75.0,
            "avg_overlap_score": 0.8,
            "avg_blocks_matched": 10.0,
            "total_cached_tokens": 30000,
        },
    }
    dynamo.get_prometheus_metrics.return_value = (
        "# Dynamo metrics\nfakeai_dynamo_requests_total 1000\n"
    )
    return dynamo


@pytest.fixture
def aggregator(
    mock_metrics_tracker, mock_kv_metrics, mock_dcgm_metrics, mock_dynamo_metrics
):
    """Create MetricsAggregator with mocked sources."""
    agg = MetricsAggregator(
        metrics_tracker=mock_metrics_tracker,
        kv_metrics=mock_kv_metrics,
        dcgm_metrics=mock_dcgm_metrics,
        dynamo_metrics=mock_dynamo_metrics,
    )
    yield agg
    agg.shutdown()


class TestUnifiedMetricsAPI:
    """Tests for unified metrics API."""

    def test_get_unified_metrics_structure(self, aggregator):
        """Test unified metrics returns correct structure."""
        result = aggregator.get_unified_metrics()

        assert "timestamp" in result
        assert "sources" in result
        assert isinstance(result["sources"], dict)

    def test_get_unified_metrics_all_sources(self, aggregator):
        """Test all sources are included."""
        result = aggregator.get_unified_metrics()
        sources = result["sources"]

        assert "metrics_tracker" in sources
        assert "kv_cache" in sources
        assert "dcgm" in sources
        assert "dynamo" in sources

    def test_get_unified_metrics_with_missing_sources(self):
        """Test aggregator handles missing sources gracefully."""
        agg = MetricsAggregator(
            metrics_tracker=None,
            kv_metrics=None,
            dcgm_metrics=None,
            dynamo_metrics=None,
        )

        result = agg.get_unified_metrics()

        assert "timestamp" in result
        assert "sources" in result
        assert len(result["sources"]) == 0

        agg.shutdown()

    def test_get_unified_metrics_with_error(self, mock_metrics_tracker):
        """Test aggregator handles source errors gracefully."""
        mock_metrics_tracker.get_metrics.side_effect = Exception("Test error")

        agg = MetricsAggregator(metrics_tracker=mock_metrics_tracker)
        result = agg.get_unified_metrics()

        assert "metrics_tracker" in result["sources"]
        assert "error" in result["sources"]["metrics_tracker"]

        agg.shutdown()

    def test_unified_metrics_content(self, aggregator):
        """Test unified metrics contain expected data."""
        result = aggregator.get_unified_metrics()
        sources = result["sources"]

        # Check MetricsTracker data
        assert "requests" in sources["metrics_tracker"]
        assert "responses" in sources["metrics_tracker"]
        assert "tokens" in sources["metrics_tracker"]

        # Check KV cache data
        assert "cache_hit_rate" in sources["kv_cache"]
        assert sources["kv_cache"]["cache_hit_rate"] == 75.0

        # Check DCGM data
        assert "gpu_0" in sources["dcgm"]
        assert sources["dcgm"]["gpu_0"]["gpu_utilization_pct"] == 80

        # Check Dynamo data
        assert "latency" in sources["dynamo"]
        assert "throughput" in sources["dynamo"]


class TestCorrelatedMetrics:
    """Tests for cross-system metric correlation."""

    def test_get_correlated_metrics_structure(self, aggregator):
        """Test correlated metrics return structure."""
        result = aggregator.get_correlated_metrics()

        assert "timestamp" in result
        assert "correlations" in result
        assert "derived_metrics" in result
        assert isinstance(result["correlations"], list)

    def test_gpu_utilization_vs_token_throughput(self, aggregator):
        """Test GPU utilization vs token throughput correlation."""
        result = aggregator.get_correlated_metrics()

        # Find the correlation
        correlation = next(
            (c for c in result["correlations"] if c["metric_a"] == "gpu_utilization"),
            None,
        )

        assert correlation is not None
        assert correlation["metric_b"] == "token_throughput"
        assert "values" in correlation
        assert "gpu_utilization_pct" in correlation["values"]
        assert "tokens_per_second" in correlation["values"]
        assert "tokens_per_gpu_percent" in correlation["values"]
        assert correlation["relationship"] == "positive"

    def test_cache_hit_rate_vs_latency(self, aggregator):
        """Test cache hit rate vs latency correlation."""
        result = aggregator.get_correlated_metrics()

        correlation = next(
            (c for c in result["correlations"] if c["metric_a"] == "cache_hit_rate"),
            None,
        )

        assert correlation is not None
        assert correlation["metric_b"] == "ttft_latency"
        assert "cache_hit_rate_pct" in correlation["values"]
        assert "avg_ttft_ms" in correlation["values"]
        assert "estimated_latency_reduction_ms" in correlation["values"]
        assert correlation["relationship"] == "negative"

    def test_queue_depth_vs_ttft(self, aggregator):
        """Test queue depth vs TTFT correlation."""
        result = aggregator.get_correlated_metrics()

        correlation = next(
            (c for c in result["correlations"] if c["metric_a"] == "queue_depth"), None
        )

        assert correlation is not None
        assert correlation["metric_b"] == "ttft_latency"
        assert "queue_depth" in correlation["values"]
        assert "estimated_queue_impact_ms" in correlation["values"]

    def test_worker_load_vs_response_time(self, aggregator):
        """Test worker load vs response time correlation."""
        result = aggregator.get_correlated_metrics()

        correlation = next(
            (c for c in result["correlations"] if c["metric_a"] == "batch_size"), None
        )

        assert correlation is not None
        assert "batch_size" in correlation["values"]
        assert "per_request_latency_ms" in correlation["values"]


class TestDerivedMetrics:
    """Tests for derived efficiency metrics."""

    def test_token_efficiency(self, aggregator):
        """Test token efficiency calculation."""
        result = aggregator.get_correlated_metrics()
        derived = result["derived_metrics"]

        assert "token_efficiency" in derived
        assert "value" in derived["token_efficiency"]
        assert "unit" in derived["token_efficiency"]
        assert derived["token_efficiency"]["unit"] == "tokens/second"

    def test_cache_effectiveness(self, aggregator):
        """Test cache effectiveness calculation."""
        result = aggregator.get_correlated_metrics()
        derived = result["derived_metrics"]

        assert "cache_effectiveness" in derived
        assert "value" in derived["cache_effectiveness"]
        assert derived["cache_effectiveness"]["unit"] == "percentage"

    def test_gpu_efficiency(self, aggregator):
        """Test GPU efficiency calculation."""
        result = aggregator.get_correlated_metrics()
        derived = result["derived_metrics"]

        assert "gpu_efficiency" in derived
        assert "value" in derived["gpu_efficiency"]
        assert derived["gpu_efficiency"]["unit"] == "tokens/sec per % GPU"
        assert derived["gpu_efficiency"]["value"] > 0

    def test_cost_efficiency(self, aggregator):
        """Test cost efficiency calculation."""
        result = aggregator.get_correlated_metrics()
        derived = result["derived_metrics"]

        assert "cost_efficiency" in derived
        assert "value" in derived["cost_efficiency"]
        assert derived["cost_efficiency"]["unit"] == "tokens per dollar"


class TestHealthScoring:
    """Tests for system health scoring."""

    def test_get_health_score_structure(self, aggregator):
        """Test health score return structure."""
        result = aggregator.get_health_score()

        assert "timestamp" in result
        assert "overall" in result
        assert "subsystems" in result

        assert "score" in result["overall"]
        assert "status" in result["overall"]
        assert "issues" in result["overall"]
        assert "recommendations" in result["overall"]

    def test_overall_health_score_range(self, aggregator):
        """Test overall health score is in valid range."""
        result = aggregator.get_health_score()

        score = result["overall"]["score"]
        assert 0.0 <= score <= 100.0

    def test_subsystem_health_scores(self, aggregator):
        """Test all subsystems have health scores."""
        result = aggregator.get_health_score()
        subsystems = result["subsystems"]

        assert "api" in subsystems
        assert "cache" in subsystems
        assert "gpu" in subsystems
        assert "inference" in subsystems

        for name, health in subsystems.items():
            assert "score" in health
            assert "status" in health
            assert 0.0 <= health["score"] <= 100.0

    def test_api_health_with_high_errors(self, mock_metrics_tracker):
        """Test API health score degrades with high error rate."""
        mock_metrics_tracker.get_metrics.return_value = {
            "requests": {
                "/v1/chat/completions": {
                    "rate": 10.0,
                    "avg": 0,
                    "min": 0,
                    "max": 0,
                    "p50": 0,
                    "p90": 0,
                    "p99": 0,
                }
            },
            "responses": {
                "/v1/chat/completions": {
                    "rate": 10.0,
                    "avg": 0.5,
                    "min": 0,
                    "max": 1,
                    "p50": 0.5,
                    "p90": 0.8,
                    "p99": 1.0,
                }
            },
            "tokens": {},
            "errors": {
                "/v1/chat/completions": {
                    "rate": 2.0,
                    "avg": 0,
                    "min": 0,
                    "max": 0,
                    "p50": 0,
                    "p90": 0,
                    "p99": 0,
                }
            },  # 20% error rate
            "streaming_stats": {},
        }

        agg = MetricsAggregator(metrics_tracker=mock_metrics_tracker)
        result = agg.get_health_score()

        api_health = result["subsystems"]["api"]
        assert api_health["score"] < 100.0
        assert len(api_health["issues"]) > 0

        agg.shutdown()

    def test_cache_health_with_low_hit_rate(self, mock_kv_metrics):
        """Test cache health score degrades with low hit rate."""
        mock_kv_metrics.get_stats.return_value = {
            "cache_hit_rate": 15.0,  # Below threshold
            "token_reuse_rate": 10.0,
        }

        agg = MetricsAggregator(kv_metrics=mock_kv_metrics)
        result = agg.get_health_score()

        cache_health = result["subsystems"]["cache"]
        assert cache_health["score"] < 100.0
        assert any(
            "cache hit rate" in issue.lower() for issue in cache_health["issues"]
        )

        agg.shutdown()

    def test_gpu_health_with_high_temperature(self, mock_dcgm_metrics):
        """Test GPU health score degrades with high temperature."""
        mock_dcgm_metrics.get_metrics_dict.return_value = {
            "gpu_0": {
                "gpu_utilization_pct": 80,
                "temperature_c": 90,  # Above threshold
                "ecc_dbe_total": 0,
            }
        }

        agg = MetricsAggregator(dcgm_metrics=mock_dcgm_metrics)
        result = agg.get_health_score()

        gpu_health = result["subsystems"]["gpu"]
        assert gpu_health["score"] < 100.0
        assert any("temperature" in issue.lower() for issue in gpu_health["issues"])

        agg.shutdown()

    def test_gpu_health_with_ecc_errors(self, mock_dcgm_metrics):
        """Test GPU health critical with ECC errors."""
        mock_dcgm_metrics.get_metrics_dict.return_value = {
            "gpu_0": {
                "gpu_utilization_pct": 80,
                "temperature_c": 75,
                "ecc_dbe_total": 5,  # Critical errors
            }
        }

        agg = MetricsAggregator(dcgm_metrics=mock_dcgm_metrics)
        result = agg.get_health_score()

        gpu_health = result["subsystems"]["gpu"]
        assert gpu_health["score"] < 60.0  # Should be significantly degraded
        assert any("ECC" in issue for issue in gpu_health["issues"])

        agg.shutdown()

    def test_inference_health_with_full_queue(self, mock_dynamo_metrics):
        """Test inference health degrades with full queue."""
        mock_dynamo_metrics.get_stats_dict.return_value = {
            "queue": {
                "current_depth": 18,
                "max_depth": 20,  # 90% full
            },
            "latency": {"ttft": {"avg": 500, "p99": 1000}},
        }

        agg = MetricsAggregator(dynamo_metrics=mock_dynamo_metrics)
        result = agg.get_health_score()

        inference_health = result["subsystems"]["inference"]
        assert inference_health["score"] < 100.0
        assert any("queue" in issue.lower() for issue in inference_health["issues"])

        agg.shutdown()

    def test_health_status_mapping(self, aggregator):
        """Test health score to status mapping."""
        # Test status enumeration
        assert aggregator._score_to_status(95.0) == HealthStatus.HEALTHY
        assert aggregator._score_to_status(75.0) == HealthStatus.DEGRADED
        assert aggregator._score_to_status(50.0) == HealthStatus.UNHEALTHY
        assert aggregator._score_to_status(30.0) == HealthStatus.CRITICAL


class TestTimeSeriesAggregation:
    """Tests for time-series data aggregation."""

    def test_time_series_storage_initialization(self, aggregator):
        """Test time-series storage is initialized."""
        assert hasattr(aggregator, "_time_series_1s")
        assert hasattr(aggregator, "_time_series_1m")
        assert hasattr(aggregator, "_time_series_1h")

    def test_sample_metrics(self, aggregator):
        """Test metric sampling."""
        aggregator._sample_metrics(TimeResolution.ONE_SECOND)

        # Check that some metrics were sampled
        assert len(aggregator._time_series_1s) > 0

    def test_get_time_series(self, aggregator):
        """Test retrieving time-series data."""
        # Sample some data
        aggregator._sample_metrics(TimeResolution.ONE_SECOND)
        time.sleep(0.1)
        aggregator._sample_metrics(TimeResolution.ONE_SECOND)

        # Retrieve data
        result = aggregator.get_time_series("gpu_utilization", "1s", 60)

        assert isinstance(result, list)

    def test_time_series_filtering_by_duration(self, aggregator):
        """Test time-series filtering by duration."""
        # Add multiple data points
        for _ in range(5):
            aggregator._sample_metrics(TimeResolution.ONE_SECOND)
            time.sleep(0.1)

        # Get last 1 second
        recent = aggregator.get_time_series("token_throughput", "1s", 1)

        # All points should be recent
        if recent:
            for point in recent:
                assert time.time() - point["timestamp"] <= 1.5

    def test_time_series_resolution_storage(self, aggregator):
        """Test different resolutions use different storage."""
        aggregator._sample_metrics(TimeResolution.ONE_SECOND)
        aggregator._sample_metrics(TimeResolution.ONE_MINUTE)
        aggregator._sample_metrics(TimeResolution.ONE_HOUR)

        # All resolutions should have data
        result_1s = aggregator.get_time_series("token_throughput", "1s", 3600)
        result_1m = aggregator.get_time_series("token_throughput", "1m", 86400)
        result_1h = aggregator.get_time_series("token_throughput", "1h", 604800)

        # Check data exists in at least one resolution
        assert len(result_1s) > 0 or len(result_1m) > 0 or len(result_1h) > 0


class TestPrometheusExport:
    """Tests for Prometheus format export."""

    def test_get_prometheus_unified(self, aggregator):
        """Test unified Prometheus export."""
        result = aggregator.get_prometheus_unified()

        assert isinstance(result, str)
        assert len(result) > 0

    def test_prometheus_includes_all_sources(self, aggregator):
        """Test Prometheus export includes all metric sources."""
        result = aggregator.get_prometheus_unified()

        assert "MetricsTracker" in result
        assert "DCGM" in result
        assert "Dynamo" in result

    def test_prometheus_includes_derived_metrics(self, aggregator):
        """Test Prometheus export includes derived metrics."""
        result = aggregator.get_prometheus_unified()

        assert "fakeai_derived_" in result

    def test_prometheus_includes_health_scores(self, aggregator):
        """Test Prometheus export includes health scores."""
        result = aggregator.get_prometheus_unified()

        assert "fakeai_health_score" in result

    def test_prometheus_format_validity(self, aggregator):
        """Test Prometheus export format is valid."""
        result = aggregator.get_prometheus_unified()

        lines = result.split("\n")

        # Check for proper format
        has_type = any("# TYPE" in line for line in lines)
        has_help = any("# HELP" in line for line in lines)
        has_metrics = any(line and not line.startswith("#") for line in lines)

        assert has_type
        assert has_help
        assert has_metrics


class TestAggregatorLifecycle:
    """Tests for aggregator lifecycle management."""

    def test_aggregator_initialization(self):
        """Test aggregator initializes correctly."""
        agg = MetricsAggregator()

        assert agg is not None
        assert hasattr(agg, "_aggregation_thread")
        assert agg._aggregation_thread.is_alive()

        agg.shutdown()

    def test_aggregator_shutdown(self):
        """Test aggregator shuts down cleanly."""
        agg = MetricsAggregator()

        assert agg._aggregation_thread.is_alive()

        agg.shutdown()

        # Give thread time to stop
        time.sleep(0.5)

        assert not agg._aggregation_thread.is_alive()

    def test_background_aggregation_runs(self):
        """Test background aggregation thread runs."""
        agg = MetricsAggregator()

        initial_1s_sample = agg._last_1s_sample

        # Wait for at least one sample
        time.sleep(1.5)

        # Check that sampling occurred
        assert agg._last_1s_sample > initial_1s_sample

        agg.shutdown()


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_metrics_sources(self):
        """Test aggregator with no metric sources."""
        agg = MetricsAggregator()

        result = agg.get_unified_metrics()
        assert result["sources"] == {}

        health = agg.get_health_score()
        assert health["overall"]["score"] == 100.0
        assert health["overall"]["status"] == "healthy"

        agg.shutdown()

    def test_partial_metrics_sources(self, mock_metrics_tracker):
        """Test aggregator with only some sources."""
        agg = MetricsAggregator(metrics_tracker=mock_metrics_tracker)

        result = agg.get_unified_metrics()
        assert "metrics_tracker" in result["sources"]
        assert "kv_cache" not in result["sources"]

        agg.shutdown()

    def test_metric_extraction_with_missing_data(self, aggregator):
        """Test metric extraction handles missing data."""
        # Should not raise exceptions
        gpu_util = aggregator._extract_avg_gpu_utilization({})
        assert gpu_util is None

        token_rate = aggregator._extract_token_throughput({"tokens": {}})
        assert token_rate is None

    def test_health_scoring_with_no_data(self):
        """Test health scoring with empty metrics."""
        agg = MetricsAggregator()

        health = agg.get_health_score()

        # Should still return valid structure
        assert "overall" in health
        assert "subsystems" in health
        assert health["overall"]["score"] == 100.0

        agg.shutdown()
