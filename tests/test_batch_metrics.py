"""
Comprehensive tests for the Batch Metrics module.

Tests lifecycle tracking, request-level metrics, throughput calculations,
resource tracking, and aggregate statistics.
"""

import time

import pytest

from fakeai.batch_metrics import BatchLifecycleMetrics, BatchMetricsTracker


class TestBatchLifecycleMetrics:
    """Tests for BatchLifecycleMetrics dataclass."""

    def test_initialization(self):
        """Test basic initialization of lifecycle metrics."""
        metrics = BatchLifecycleMetrics(
            batch_id="batch_123",
            total_requests=10,
        )

        assert metrics.batch_id == "batch_123"
        assert metrics.total_requests == 10
        assert metrics.requests_processed == 0
        assert metrics.requests_succeeded == 0
        assert metrics.requests_failed == 0
        assert len(metrics.request_latencies) == 0
        assert len(metrics.request_token_counts) == 0

    def test_validation_time_calculation(self):
        """Test validation time calculation."""
        metrics = BatchLifecycleMetrics(batch_id="test", total_requests=5)

        # Before setting times
        assert metrics.calculate_validation_time() == 0.0

        # After setting times
        metrics.validation_start = 1000.0
        metrics.validation_end = 1000.5
        assert metrics.calculate_validation_time() == 0.5

    def test_queue_time_calculation(self):
        """Test queue time calculation."""
        metrics = BatchLifecycleMetrics(batch_id="test", total_requests=5)

        metrics.queue_start = 1000.0
        metrics.queue_end = 1002.0
        assert metrics.calculate_queue_time() == 2.0

    def test_processing_time_calculation(self):
        """Test processing time calculation."""
        metrics = BatchLifecycleMetrics(batch_id="test", total_requests=5)

        metrics.processing_start = 1000.0
        metrics.processing_end = 1005.0
        assert metrics.calculate_processing_time() == 5.0

    def test_finalization_time_calculation(self):
        """Test finalization time calculation."""
        metrics = BatchLifecycleMetrics(batch_id="test", total_requests=5)

        metrics.finalization_start = 1000.0
        metrics.finalization_end = 1000.3
        assert abs(metrics.calculate_finalization_time() - 0.3) < 0.001

    def test_total_duration_calculation(self):
        """Test total duration calculation."""
        metrics = BatchLifecycleMetrics(batch_id="test", total_requests=5)
        start_time = time.time()
        metrics.start_time = start_time

        # Before completion
        duration = metrics.calculate_total_duration()
        assert duration >= 0.0

        # After completion
        metrics.completion_time = start_time + 10.0
        assert metrics.calculate_total_duration() == 10.0

    def test_requests_per_second_calculation(self):
        """Test RPS calculation."""
        metrics = BatchLifecycleMetrics(batch_id="test", total_requests=100)
        metrics.processing_start = 1000.0
        metrics.processing_end = 1010.0  # 10 seconds
        metrics.requests_processed = 100

        rps = metrics.calculate_requests_per_second()
        assert rps == 10.0  # 100 requests / 10 seconds

    def test_tokens_per_second_calculation(self):
        """Test TPS calculation."""
        metrics = BatchLifecycleMetrics(batch_id="test", total_requests=10)
        metrics.processing_start = 1000.0
        metrics.processing_end = 1005.0  # 5 seconds
        metrics.request_token_counts = [
            100,
            150,
            200,
            100,
            150,
            200,
            100,
            150,
            200,
            100,
        ]

        tps = metrics.calculate_tokens_per_second()
        assert tps == 290.0  # 1450 tokens / 5 seconds

    def test_success_rate_calculation(self):
        """Test success rate calculation."""
        metrics = BatchLifecycleMetrics(batch_id="test", total_requests=10)

        # No requests processed
        assert metrics.calculate_success_rate() == 0.0

        # All succeeded
        metrics.requests_processed = 10
        metrics.requests_succeeded = 10
        assert metrics.calculate_success_rate() == 100.0

        # Half succeeded
        metrics.requests_succeeded = 5
        assert metrics.calculate_success_rate() == 50.0

    def test_latency_percentiles(self):
        """Test latency percentile calculations."""
        metrics = BatchLifecycleMetrics(batch_id="test", total_requests=10)

        # Empty latencies
        stats = metrics.get_latency_percentiles()
        assert stats["avg"] == 0.0

        # With data
        metrics.request_latencies = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        stats = metrics.get_latency_percentiles()

        assert stats["min"] == 10.0
        assert stats["max"] == 100.0
        assert stats["avg"] == 55.0
        assert stats["p50"] == 55.0
        assert stats["p90"] >= 90.0
        assert stats["p99"] >= 99.0

    def test_token_statistics(self):
        """Test token usage statistics."""
        metrics = BatchLifecycleMetrics(batch_id="test", total_requests=5)

        # Empty tokens
        stats = metrics.get_token_statistics()
        assert stats["total"] == 0

        # With data
        metrics.request_token_counts = [100, 200, 150, 300, 250]
        stats = metrics.get_token_statistics()

        assert stats["total"] == 1000
        assert stats["min"] == 100
        assert stats["max"] == 300
        assert stats["avg"] == 200.0
        assert stats["p50"] == 200.0

    def test_batch_efficiency_calculation(self):
        """Test batch efficiency vs sequential processing."""
        metrics = BatchLifecycleMetrics(batch_id="test", total_requests=10)

        # No latencies
        assert metrics.calculate_batch_efficiency() == 1.0

        # With realistic data
        # 10 requests of 100ms each = 1000ms + 500ms overhead = 1500ms sequential
        # Batch processes in 500ms (more realistic timing)
        metrics.request_latencies = [100.0] * 10
        metrics.processing_start = 1000.0
        metrics.processing_end = 1000.5  # 500ms actual processing

        efficiency = metrics.calculate_batch_efficiency()
        # Should be > 1.0 (faster than sequential)
        # 1000ms + 500ms = 1500ms sequential vs 500ms actual = 3.0x efficiency
        assert efficiency >= 1.0


class TestBatchMetricsTracker:
    """Tests for BatchMetricsTracker class."""

    @pytest.fixture
    def tracker(self):
        """Create a fresh metrics tracker for each test."""
        tracker = BatchMetricsTracker()
        tracker.reset()  # Ensure clean state
        return tracker

    def test_initialization(self, tracker):
        """Test tracker initialization."""
        assert tracker._total_batches_started == 0
        assert tracker._total_batches_completed == 0
        assert tracker._total_batches_failed == 0
        assert len(tracker._active_batches) == 0

    def test_start_batch(self, tracker):
        """Test starting batch tracking."""
        tracker.start_batch("batch_1", total_requests=10)

        assert tracker._total_batches_started == 1
        assert "batch_1" in tracker._active_batches
        assert tracker._active_batches["batch_1"].total_requests == 10

    def test_record_validation_complete(self, tracker):
        """Test recording validation completion."""
        tracker.start_batch("batch_1", total_requests=5)
        time.sleep(0.01)
        tracker.record_validation_complete("batch_1")

        metrics = tracker._active_batches["batch_1"]
        assert metrics.validation_end is not None
        assert metrics.queue_start is not None

    def test_record_processing_start(self, tracker):
        """Test recording processing start."""
        tracker.start_batch("batch_1", total_requests=5)
        tracker.record_validation_complete("batch_1")
        time.sleep(0.01)
        tracker.record_processing_start("batch_1")

        metrics = tracker._active_batches["batch_1"]
        assert metrics.queue_end is not None
        assert metrics.processing_start is not None

    def test_record_request_processed_success(self, tracker):
        """Test recording a successful request."""
        tracker.start_batch("batch_1", total_requests=5)

        tracker.record_request_processed(
            batch_id="batch_1",
            request_num=1,
            latency_ms=150.0,
            tokens=100,
            success=True,
        )

        metrics = tracker._active_batches["batch_1"]
        assert metrics.requests_processed == 1
        assert metrics.requests_succeeded == 1
        assert metrics.requests_failed == 0
        assert 150.0 in metrics.request_latencies
        assert 100 in metrics.request_token_counts
        assert tracker._total_requests_processed == 1
        assert tracker._total_tokens_processed == 100

    def test_record_request_processed_failure(self, tracker):
        """Test recording a failed request."""
        tracker.start_batch("batch_1", total_requests=5)

        tracker.record_request_processed(
            batch_id="batch_1",
            request_num=1,
            latency_ms=50.0,
            tokens=0,
            success=False,
            error_type="validation_error",
        )

        metrics = tracker._active_batches["batch_1"]
        assert metrics.requests_processed == 1
        assert metrics.requests_succeeded == 0
        assert metrics.requests_failed == 1
        assert metrics.error_types["validation_error"] == 1

    def test_record_processing_complete(self, tracker):
        """Test recording processing completion."""
        tracker.start_batch("batch_1", total_requests=5)
        tracker.record_processing_start("batch_1")
        time.sleep(0.01)
        tracker.record_processing_complete("batch_1")

        metrics = tracker._active_batches["batch_1"]
        assert metrics.processing_end is not None
        assert metrics.finalization_start is not None

    def test_record_finalization_complete(self, tracker):
        """Test recording finalization completion."""
        tracker.start_batch("batch_1", total_requests=5)
        tracker.record_processing_complete("batch_1")
        time.sleep(0.01)
        tracker.record_finalization_complete("batch_1")

        metrics = tracker._active_batches["batch_1"]
        assert metrics.finalization_end is not None

    def test_complete_batch(self, tracker):
        """Test completing a batch."""
        tracker.start_batch("batch_1", total_requests=5)

        # Process some requests
        for i in range(5):
            tracker.record_request_processed(
                batch_id="batch_1",
                request_num=i,
                latency_ms=100.0,
                tokens=50,
                success=True,
            )

        tracker.complete_batch(
            batch_id="batch_1",
            bytes_written=1024,
            bytes_read=512,
        )

        # Check batch moved to completed
        assert "batch_1" not in tracker._active_batches
        assert tracker._total_batches_completed == 1
        assert len(tracker._completed_batches) == 1

        # Check resource metrics were recorded
        completed = tracker._completed_batches[0]
        assert completed.total_bytes_written == 1024
        assert completed.total_bytes_read == 512
        assert completed.peak_memory_mb > 0
        assert completed.completion_time is not None

    def test_fail_batch(self, tracker):
        """Test marking a batch as failed."""
        tracker.start_batch("batch_1", total_requests=5)
        tracker.fail_batch("batch_1", "Processing error")

        assert "batch_1" not in tracker._active_batches
        assert tracker._total_batches_failed == 1
        assert len(tracker._completed_batches) == 1

        completed = tracker._completed_batches[0]
        assert "batch_failure" in completed.error_types

    def test_get_batch_stats_active(self, tracker):
        """Test getting stats for an active batch."""
        tracker.start_batch("batch_1", total_requests=10)
        tracker.record_request_processed(
            batch_id="batch_1",
            request_num=1,
            latency_ms=100.0,
            tokens=50,
            success=True,
        )

        stats = tracker.get_batch_stats("batch_1")

        assert stats is not None
        assert stats["batch_id"] == "batch_1"
        assert stats["status"] == "active"
        assert stats["requests"]["total"] == 10
        assert stats["requests"]["processed"] == 1

    def test_get_batch_stats_completed(self, tracker):
        """Test getting stats for a completed batch."""
        tracker.start_batch("batch_1", total_requests=5)
        for i in range(5):
            tracker.record_request_processed(
                batch_id="batch_1",
                request_num=i,
                latency_ms=100.0,
                tokens=50,
                success=True,
            )
        tracker.complete_batch("batch_1")

        stats = tracker.get_batch_stats("batch_1")

        assert stats is not None
        assert stats["status"] == "completed"
        assert stats["requests"]["processed"] == 5
        assert stats["tokens"]["total"] == 250

    def test_get_batch_stats_nonexistent(self, tracker):
        """Test getting stats for non-existent batch."""
        stats = tracker.get_batch_stats("batch_nonexistent")
        assert stats is None

    def test_get_all_batches_stats_empty(self, tracker):
        """Test getting aggregate stats with no batches."""
        stats = tracker.get_all_batches_stats()

        assert stats["summary"]["total_batches_started"] == 0
        assert stats["summary"]["total_batches_completed"] == 0
        assert stats["summary"]["active_batches"] == 0

    def test_get_all_batches_stats_with_data(self, tracker):
        """Test getting aggregate stats with completed batches."""
        # Create and complete multiple batches
        for batch_num in range(3):
            batch_id = f"batch_{batch_num}"
            tracker.start_batch(batch_id, total_requests=10)

            for req_num in range(10):
                tracker.record_request_processed(
                    batch_id=batch_id,
                    request_num=req_num,
                    latency_ms=100.0 + req_num * 10,
                    tokens=50 + req_num * 5,
                    success=True,
                )

            tracker.complete_batch(batch_id)

        stats = tracker.get_all_batches_stats()

        assert stats["summary"]["total_batches_started"] == 3
        assert stats["summary"]["total_batches_completed"] == 3
        assert stats["summary"]["total_requests_processed"] == 30
        # Each batch: 50+55+60+65+70+75+80+85+90+95 = 725 tokens
        # 3 batches * 725 = 2175 tokens
        assert stats["summary"]["total_tokens_processed"] == 2175

        # Check aggregate latency stats
        assert stats["latency"]["count"] == 30
        assert stats["latency"]["avg"] > 0

        # Check throughput stats
        assert stats["throughput"]["requests_per_second"]["count"] == 3
        assert stats["throughput"]["tokens_per_second"]["count"] == 3

    def test_multiple_batches_concurrently(self, tracker):
        """Test tracking multiple active batches."""
        tracker.start_batch("batch_1", total_requests=5)
        tracker.start_batch("batch_2", total_requests=10)
        tracker.start_batch("batch_3", total_requests=15)

        assert len(tracker._active_batches) == 3
        assert tracker._total_batches_started == 3

        # Complete one
        tracker.complete_batch("batch_1")
        assert len(tracker._active_batches) == 2
        assert tracker._total_batches_completed == 1

    def test_error_categorization(self, tracker):
        """Test that errors are properly categorized."""
        tracker.start_batch("batch_1", total_requests=10)

        # Record different error types
        tracker.record_request_processed(
            "batch_1", 1, 50.0, 0, False, "validation_error"
        )
        tracker.record_request_processed(
            "batch_1", 2, 50.0, 0, False, "validation_error"
        )
        tracker.record_request_processed("batch_1", 3, 50.0, 0, False, "timeout_error")

        tracker.complete_batch("batch_1")

        stats = tracker.get_batch_stats("batch_1")
        assert stats["errors"]["by_type"]["validation_error"] == 2
        assert stats["errors"]["by_type"]["timeout_error"] == 1
        assert stats["errors"]["total"] == 3

    def test_resource_metrics_simulation(self, tracker):
        """Test that resource metrics are simulated."""
        tracker.start_batch("batch_1", total_requests=20)

        for i in range(20):
            tracker.record_request_processed("batch_1", i, 100.0, 100, True)

        tracker.complete_batch("batch_1", bytes_written=2048, bytes_read=1024)

        stats = tracker.get_batch_stats("batch_1")

        # Check resource metrics exist and are reasonable
        assert stats["resources"]["peak_memory_mb"] > 0
        assert stats["resources"]["bytes_written"] == 2048
        assert stats["resources"]["bytes_read"] == 1024
        assert stats["resources"]["network_bandwidth_mbps"] >= 0

    def test_efficiency_calculation(self, tracker):
        """Test batch efficiency calculation."""
        tracker.start_batch("batch_1", total_requests=10)
        tracker.record_processing_start("batch_1")

        # Simulate fast batch processing
        for i in range(10):
            tracker.record_request_processed("batch_1", i, 100.0, 50, True)

        time.sleep(0.2)  # Actual processing takes 200ms
        tracker.record_processing_complete("batch_1")
        tracker.complete_batch("batch_1")

        stats = tracker.get_batch_stats("batch_1")

        # Efficiency should be > 1 (batch faster than sequential)
        assert stats["efficiency"]["batch_vs_sequential"] >= 1.0

    def test_reset(self, tracker):
        """Test resetting metrics."""
        # Add some data
        tracker.start_batch("batch_1", total_requests=5)
        tracker.complete_batch("batch_1")

        # Reset
        tracker.reset()

        # Verify everything is cleared
        assert tracker._total_batches_started == 0
        assert tracker._total_batches_completed == 0
        assert len(tracker._active_batches) == 0
        assert len(tracker._completed_batches) == 0

    def test_full_lifecycle_tracking(self, tracker):
        """Test tracking a complete batch lifecycle."""
        batch_id = "batch_full_lifecycle"
        tracker.start_batch(batch_id, total_requests=5)

        # Validation phase
        time.sleep(0.01)
        tracker.record_validation_complete(batch_id)

        # Queue phase
        time.sleep(0.01)
        tracker.record_processing_start(batch_id)

        # Processing phase
        for i in range(5):
            tracker.record_request_processed(
                batch_id, i, 100.0 + i * 10, 50 + i * 5, True
            )
            time.sleep(0.01)

        tracker.record_processing_complete(batch_id)

        # Finalization phase
        time.sleep(0.01)
        tracker.record_finalization_complete(batch_id)

        # Complete
        tracker.complete_batch(batch_id, bytes_written=1024, bytes_read=512)

        # Verify all lifecycle phases were tracked
        stats = tracker.get_batch_stats(batch_id)

        assert stats["lifecycle"]["validation_time_ms"] > 0
        assert stats["lifecycle"]["queue_time_ms"] > 0
        assert stats["lifecycle"]["processing_time_ms"] > 0
        assert stats["lifecycle"]["finalization_time_ms"] > 0
        assert stats["lifecycle"]["total_duration_ms"] > 0

        # Verify total duration is sum of all phases (approximately)
        total = (
            stats["lifecycle"]["validation_time_ms"]
            + stats["lifecycle"]["queue_time_ms"]
            + stats["lifecycle"]["processing_time_ms"]
            + stats["lifecycle"]["finalization_time_ms"]
        )
        # Allow some tolerance for timing precision
        assert abs(stats["lifecycle"]["total_duration_ms"] - total) < 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
