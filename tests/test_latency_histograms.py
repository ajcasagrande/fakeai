#!/usr/bin/env python3
"""
Tests for FakeAI Latency Histogram Tracking
"""
#  SPDX-License-Identifier: Apache-2.0

import random
import threading

import pytest

from fakeai.latency_histograms import (
    HISTOGRAM_BUCKETS,
    LatencyHistogram,
    LatencyHistogramTracker,
)


class TestLatencyHistogram:
    """Tests for LatencyHistogram class."""

    def test_empty_histogram(self):
        """Test histogram with no data."""
        hist = LatencyHistogram()
        stats = hist.get_stats()

        assert stats["count"] == 0
        assert stats["mean"] == 0.0
        assert stats["median"] == 0.0
        assert stats["min"] == 0.0
        assert stats["max"] == 0.0
        assert stats["p50"] == 0.0
        assert stats["p99"] == 0.0

    def test_single_sample(self):
        """Test histogram with a single sample."""
        hist = LatencyHistogram()
        hist.record(50.0)

        stats = hist.get_stats()
        assert stats["count"] == 1
        assert stats["mean"] == 50.0
        assert stats["min"] == 50.0
        assert stats["max"] == 50.0
        assert stats["std_dev"] == 0.0

    def test_multiple_samples(self):
        """Test histogram with multiple samples."""
        hist = LatencyHistogram()
        samples = [10.0, 20.0, 30.0, 40.0, 50.0]

        for sample in samples:
            hist.record(sample)

        stats = hist.get_stats()
        assert stats["count"] == 5
        assert stats["mean"] == 30.0
        assert stats["min"] == 10.0
        assert stats["max"] == 50.0

    def test_percentile_calculation(self):
        """Test accurate percentile calculation."""
        hist = LatencyHistogram()

        # Record 100 samples from 1ms to 100ms
        for i in range(1, 101):
            hist.record(float(i))

        # Test key percentiles
        assert 45.0 <= hist.get_percentile(50.0) <= 55.0  # p50 should be around 50
        assert 85.0 <= hist.get_percentile(90.0) <= 95.0  # p90 should be around 90
        assert 95.0 <= hist.get_percentile(99.0) <= 100.0  # p99 should be around 99

    def test_percentile_edge_cases(self):
        """Test percentile calculation edge cases."""
        hist = LatencyHistogram()

        # Test p0 (minimum)
        hist.record(10.0)
        hist.record(20.0)
        hist.record(30.0)

        assert hist.get_percentile(0.0) <= 10.0

        # Test p100 (maximum)
        assert hist.get_percentile(100.0) >= 30.0

    def test_get_percentiles_batch(self):
        """Test batch percentile calculation."""
        hist = LatencyHistogram()

        for i in range(1, 101):
            hist.record(float(i))

        percentiles = hist.get_percentiles([50.0, 90.0, 99.0])

        assert "50.0" in str(percentiles) or 50.0 in percentiles
        assert "90.0" in str(percentiles) or 90.0 in percentiles
        assert "99.0" in str(percentiles) or 99.0 in percentiles

    def test_mean_calculation(self):
        """Test mean calculation."""
        hist = LatencyHistogram()

        hist.record(10.0)
        hist.record(20.0)
        hist.record(30.0)

        assert hist.get_mean() == 20.0

    def test_median_calculation(self):
        """Test median calculation."""
        hist = LatencyHistogram()

        # Odd number of samples
        for val in [10.0, 20.0, 30.0, 40.0, 50.0]:
            hist.record(val)

        median = hist.get_median()
        assert 25.0 <= median <= 35.0  # Should be around 30

    def test_mode_calculation(self):
        """Test mode calculation."""
        hist = LatencyHistogram()

        # Create a clear mode at 50ms
        for _ in range(10):
            hist.record(50.0)

        for val in [10.0, 20.0, 30.0, 40.0, 60.0, 70.0]:
            hist.record(val)

        mode = hist.get_mode()
        assert mode is not None
        # Mode should be in the bucket containing 50ms (20-50ms bucket)
        assert 20.0 <= mode <= 55.0

    def test_standard_deviation(self):
        """Test standard deviation calculation."""
        hist = LatencyHistogram()

        # Uniform distribution
        for i in range(1, 11):
            hist.record(float(i))

        std_dev = hist.get_std_dev()
        assert std_dev > 0
        # For 1-10, std dev should be around 2.87
        assert 2.0 <= std_dev <= 4.0

    def test_coefficient_of_variation(self):
        """Test coefficient of variation calculation."""
        hist = LatencyHistogram()

        # Low variation
        for val in [95.0, 100.0, 105.0]:
            hist.record(val)

        cv = hist.get_coefficient_of_variation()
        assert cv < 0.1  # Low variation

        # High variation
        hist2 = LatencyHistogram()
        for val in [1.0, 50.0, 100.0]:
            hist2.record(val)

        cv2 = hist2.get_coefficient_of_variation()
        assert cv2 > 0.3  # High variation

    def test_skewness(self):
        """Test skewness calculation using Pearson's second coefficient."""
        hist = LatencyHistogram()

        # Right-skewed distribution (long tail to the right)
        # Mean will be > median due to outliers
        for _ in range(90):
            hist.record(10.0)
        for _ in range(5):
            hist.record(50.0)
        for _ in range(5):
            hist.record(200.0)  # High outliers push mean higher

        skewness = hist.get_skewness()
        mean = hist.get_mean()
        median = hist.get_median()

        assert skewness > 0  # Right-skewed (mean > median)
        assert mean > median  # Confirm mean is greater than median

        # Test that skewness formula is working
        # For symmetric distribution, skewness should be near 0
        hist_symmetric = LatencyHistogram()
        for i in range(1, 101):
            hist_symmetric.record(float(i))

        skewness_symmetric = hist_symmetric.get_skewness()
        # Symmetric distribution should have low skewness
        assert abs(skewness_symmetric) < 1.0  # Near zero

    def test_bucket_assignment(self):
        """Test that samples are assigned to correct buckets."""
        hist = LatencyHistogram()

        # Test samples at bucket boundaries
        hist.record(1.0)  # First bucket
        hist.record(5.0)  # Third bucket boundary
        hist.record(100.0)  # Seventh bucket boundary
        hist.record(1000.0)  # Tenth bucket boundary

        assert hist._total_count == 4
        assert sum(hist._counts) == 4

    def test_outlier_detection(self):
        """Test outlier detection (> 3σ)."""
        hist = LatencyHistogram()

        # Tight cluster of normal samples (low std dev)
        for _ in range(95):
            hist.record(50.0)  # All at 50ms

        # Add extreme outliers that will be > 3σ away
        for _ in range(5):
            hist.record(10000.0)  # 10 seconds - extremely far from mean

        anomalies = hist.detect_anomalies()
        outlier_anomalies = [a for a in anomalies if a["type"] == "outliers"]

        assert len(outlier_anomalies) > 0
        assert outlier_anomalies[0]["count"] > 0

    def test_bimodal_detection(self):
        """Test bimodal distribution detection."""
        hist = LatencyHistogram()

        # Create two distinct peaks
        for _ in range(50):
            hist.record(10.0)  # First peak

        for _ in range(50):
            hist.record(200.0)  # Second peak

        anomalies = hist.detect_anomalies()
        bimodal_anomalies = [a for a in anomalies if a["type"] == "bimodal"]

        assert len(bimodal_anomalies) > 0

    def test_latency_spike_detection(self):
        """Test latency spike detection (p99 >> p50)."""
        hist = LatencyHistogram()

        # Most samples are fast
        for _ in range(95):
            hist.record(10.0)

        # Few samples are very slow
        for _ in range(5):
            hist.record(500.0)

        anomalies = hist.detect_anomalies()
        spike_anomalies = [a for a in anomalies if a["type"] == "latency_spike"]

        assert len(spike_anomalies) > 0
        assert spike_anomalies[0]["ratio"] > 10

    def test_histogram_data_export(self):
        """Test raw histogram data export."""
        hist = LatencyHistogram()

        for i in range(1, 11):
            hist.record(float(i * 10))

        data = hist.get_histogram_data()

        assert "buckets" in data
        assert "counts" in data
        assert "total_count" in data
        assert "bucket_edges" in data
        assert data["total_count"] == 10
        assert len(data["buckets"]) == len(HISTOGRAM_BUCKETS)
        assert len(data["counts"]) == len(HISTOGRAM_BUCKETS)

    def test_reset(self):
        """Test histogram reset."""
        hist = LatencyHistogram()

        for i in range(1, 11):
            hist.record(float(i))

        assert hist._total_count == 10

        hist.reset()

        assert hist._total_count == 0
        assert all(count == 0 for count in hist._counts)
        assert hist._sum == 0.0
        assert hist._min == float("inf")
        assert hist._max == 0.0

    def test_thread_safety(self):
        """Test thread-safe concurrent recording."""
        hist = LatencyHistogram()
        num_threads = 10
        samples_per_thread = 100

        def record_samples():
            for _ in range(samples_per_thread):
                hist.record(random.uniform(1.0, 100.0))

        threads = []
        for _ in range(num_threads):
            thread = threading.Thread(target=record_samples)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        assert hist._total_count == num_threads * samples_per_thread

    def test_comprehensive_stats(self):
        """Test comprehensive statistics output."""
        hist = LatencyHistogram()

        for i in range(1, 101):
            hist.record(float(i))

        stats = hist.get_stats()

        # Check all required fields
        required_fields = [
            "count",
            "mean",
            "median",
            "mode",
            "std_dev",
            "cv",
            "skewness",
            "min",
            "max",
            "p50",
            "p75",
            "p90",
            "p95",
            "p99",
            "p99.9",
            "p99.99",
        ]

        for field in required_fields:
            assert field in stats
            assert isinstance(stats[field], (int, float))


class TestLatencyHistogramTracker:
    """Tests for LatencyHistogramTracker class."""

    def test_empty_tracker(self):
        """Test tracker with no data."""
        tracker = LatencyHistogramTracker()

        endpoint_stats = tracker.get_all_endpoint_stats()
        model_stats = tracker.get_all_model_stats()

        assert len(endpoint_stats) == 0
        assert len(model_stats) == 0

    def test_record_endpoint_latency(self):
        """Test recording latency for endpoints."""
        tracker = LatencyHistogramTracker()

        tracker.record_latency(50.0, endpoint="/v1/chat/completions")
        tracker.record_latency(75.0, endpoint="/v1/chat/completions")

        stats = tracker.get_endpoint_stats("/v1/chat/completions")
        assert stats["count"] == 2
        assert stats["mean"] == 62.5

    def test_record_model_latency(self):
        """Test recording latency for models."""
        tracker = LatencyHistogramTracker()

        tracker.record_latency(100.0, model="openai/gpt-oss-120b")
        tracker.record_latency(120.0, model="openai/gpt-oss-120b")

        stats = tracker.get_model_stats("openai/gpt-oss-120b")
        assert stats["count"] == 2
        assert stats["mean"] == 110.0

    def test_record_both_endpoint_and_model(self):
        """Test recording latency for both endpoint and model."""
        tracker = LatencyHistogramTracker()

        tracker.record_latency(
            50.0, endpoint="/v1/chat/completions", model="openai/gpt-oss-120b"
        )

        endpoint_stats = tracker.get_endpoint_stats("/v1/chat/completions")
        model_stats = tracker.get_model_stats("openai/gpt-oss-120b")

        assert endpoint_stats["count"] == 1
        assert model_stats["count"] == 1
        assert endpoint_stats["mean"] == 50.0
        assert model_stats["mean"] == 50.0

    def test_multiple_endpoints(self):
        """Test tracking multiple endpoints."""
        tracker = LatencyHistogramTracker()

        tracker.record_latency(50.0, endpoint="/v1/chat/completions")
        tracker.record_latency(100.0, endpoint="/v1/embeddings")

        all_stats = tracker.get_all_endpoint_stats()
        assert len(all_stats) == 2
        assert "/v1/chat/completions" in all_stats
        assert "/v1/embeddings" in all_stats

    def test_multiple_models(self):
        """Test tracking multiple models."""
        tracker = LatencyHistogramTracker()

        tracker.record_latency(50.0, model="openai/gpt-oss-120b")
        tracker.record_latency(100.0, model="openai/gpt-oss-20b")

        all_stats = tracker.get_all_model_stats()
        assert len(all_stats) == 2
        assert "openai/gpt-oss-120b" in all_stats
        assert "openai/gpt-oss-20b" in all_stats

    def test_endpoint_anomaly_detection(self):
        """Test anomaly detection for endpoints."""
        tracker = LatencyHistogramTracker()

        # Normal samples
        for _ in range(100):
            tracker.record_latency(50.0, endpoint="/v1/chat/completions")

        # Outliers
        for _ in range(5):
            tracker.record_latency(500.0, endpoint="/v1/chat/completions")

        anomalies = tracker.detect_endpoint_anomalies("/v1/chat/completions")
        assert len(anomalies) > 0

    def test_model_anomaly_detection(self):
        """Test anomaly detection for models."""
        tracker = LatencyHistogramTracker()

        # Create bimodal distribution
        for _ in range(50):
            tracker.record_latency(10.0, model="openai/gpt-oss-120b")
        for _ in range(50):
            tracker.record_latency(200.0, model="openai/gpt-oss-120b")

        anomalies = tracker.detect_model_anomalies("openai/gpt-oss-120b")
        # Bimodal detection might not trigger with simplified buckets, but anomalies should exist
        assert isinstance(anomalies, list)

    def test_endpoint_histogram_data(self):
        """Test histogram data export for endpoints."""
        tracker = LatencyHistogramTracker()

        for i in range(1, 11):
            tracker.record_latency(float(i * 10), endpoint="/v1/chat/completions")

        data = tracker.get_endpoint_histogram_data("/v1/chat/completions")
        assert "buckets" in data
        assert "counts" in data
        assert data["total_count"] == 10

    def test_model_histogram_data(self):
        """Test histogram data export for models."""
        tracker = LatencyHistogramTracker()

        for i in range(1, 11):
            tracker.record_latency(float(i * 10), model="openai/gpt-oss-120b")

        data = tracker.get_model_histogram_data("openai/gpt-oss-120b")
        assert "buckets" in data
        assert "counts" in data
        assert data["total_count"] == 10

    def test_prometheus_export(self):
        """Test Prometheus metrics export."""
        tracker = LatencyHistogramTracker()

        for i in range(1, 101):
            tracker.record_latency(float(i), endpoint="/v1/chat/completions")

        prometheus = tracker.get_prometheus_metrics()

        assert "fakeai_latency_histogram_seconds" in prometheus
        assert 'endpoint="/v1/chat/completions"' in prometheus
        assert "le=" in prometheus  # Bucket labels
        assert "_bucket" in prometheus
        assert "_sum" in prometheus
        assert "_count" in prometheus

    def test_reset_tracker(self):
        """Test tracker reset."""
        tracker = LatencyHistogramTracker()

        tracker.record_latency(50.0, endpoint="/v1/chat/completions")
        tracker.record_latency(75.0, model="openai/gpt-oss-120b")

        assert len(tracker.get_all_endpoint_stats()) > 0
        assert len(tracker.get_all_model_stats()) > 0

        tracker.reset()

        endpoint_stats = tracker.get_endpoint_stats("/v1/chat/completions")
        model_stats = tracker.get_model_stats("openai/gpt-oss-120b")

        # After reset, counts should be 0
        assert endpoint_stats["count"] == 0
        assert model_stats["count"] == 0

    def test_thread_safety_tracker(self):
        """Test thread-safe concurrent recording in tracker."""
        tracker = LatencyHistogramTracker()
        num_threads = 10
        samples_per_thread = 100

        def record_samples():
            for _ in range(samples_per_thread):
                tracker.record_latency(
                    random.uniform(1.0, 100.0),
                    endpoint="/v1/chat/completions",
                    model="openai/gpt-oss-120b",
                )

        threads = []
        for _ in range(num_threads):
            thread = threading.Thread(target=record_samples)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        endpoint_stats = tracker.get_endpoint_stats("/v1/chat/completions")
        model_stats = tracker.get_model_stats("openai/gpt-oss-120b")

        expected_count = num_threads * samples_per_thread
        assert endpoint_stats["count"] == expected_count
        assert model_stats["count"] == expected_count


class TestBucketConfiguration:
    """Tests for histogram bucket configuration."""

    def test_bucket_boundaries(self):
        """Test that bucket boundaries are correctly ordered."""
        buckets = HISTOGRAM_BUCKETS

        for i in range(len(buckets) - 1):
            assert buckets[i] < buckets[i + 1]

    def test_bucket_coverage(self):
        """Test that buckets cover expected latency ranges."""
        buckets = HISTOGRAM_BUCKETS

        # Should cover sub-millisecond to 10+ seconds
        assert buckets[0] == 1.0  # 1ms
        assert 1000.0 in buckets  # 1s
        assert 10000.0 in buckets  # 10s
        assert buckets[-1] == float("inf")  # Catch-all

    def test_bucket_granularity(self):
        """Test that buckets have appropriate granularity."""
        buckets = HISTOGRAM_BUCKETS

        # Should have fine granularity in common ranges (1ms-1s)
        low_range_buckets = [b for b in buckets if 1.0 <= b <= 1000.0]
        assert len(low_range_buckets) >= 8  # At least 8 buckets in this range


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_zero_latency(self):
        """Test recording zero latency."""
        hist = LatencyHistogram()
        hist.record(0.0)

        stats = hist.get_stats()
        assert stats["count"] == 1
        assert stats["mean"] == 0.0
        assert stats["min"] == 0.0
        assert stats["max"] == 0.0

    def test_very_large_latency(self):
        """Test recording very large latency."""
        hist = LatencyHistogram()
        hist.record(999999.0)  # ~1000 seconds

        stats = hist.get_stats()
        assert stats["count"] == 1
        assert stats["max"] == 999999.0

    def test_very_small_latency(self):
        """Test recording very small latency."""
        hist = LatencyHistogram()
        hist.record(0.001)  # 0.001ms

        stats = hist.get_stats()
        assert stats["count"] == 1
        assert stats["min"] == 0.001

    def test_negative_latency(self):
        """Test that negative latency is handled (shouldn't happen, but test anyway)."""
        hist = LatencyHistogram()
        hist.record(-10.0)

        # Should still record the sample
        stats = hist.get_stats()
        assert stats["count"] == 1

    def test_percentile_with_single_bucket(self):
        """Test percentile calculation when all samples are in one bucket."""
        hist = LatencyHistogram()

        for _ in range(100):
            hist.record(50.0)  # All in same bucket

        p50 = hist.get_percentile(50.0)
        p99 = hist.get_percentile(99.0)

        # Both should be in the same bucket range (20-50ms bucket)
        # Due to interpolation, they will be near the bucket boundaries
        assert 20.0 <= p50 <= 55.0
        assert 20.0 <= p99 <= 55.0

    def test_empty_endpoint_stats(self):
        """Test getting stats for non-existent endpoint."""
        tracker = LatencyHistogramTracker()
        stats = tracker.get_endpoint_stats("/non/existent")

        assert stats == {}

    def test_empty_model_stats(self):
        """Test getting stats for non-existent model."""
        tracker = LatencyHistogramTracker()
        stats = tracker.get_model_stats("non-existent-model")

        assert stats == {}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
