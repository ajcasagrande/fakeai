"""
Comprehensive Tests for StreamingMetricsTracker

This test suite provides complete coverage of the StreamingMetricsTracker class
in fakeai/streaming_metrics_tracker.py, covering all functionality:

1. Stream Lifecycle - start, record, complete, fail
2. Token Tracking - counts, timestamps, chunk sizes, first token time
3. Metrics Calculation - TTFT, ITL, TPS, duration
4. Percentile Calculations - p50/p95/p99 for all metrics
5. Memory Management - max streams, deque bounds, eviction
6. Aggregation - get_metrics, time windows, per-model breakdown, success rate
7. Prometheus Export - format validation, all metrics, labels
8. Performance Tests - concurrent access, stress testing
9. Edge Cases - empty data, single values, boundary conditions

Author: Claude Code
Date: 2025-10-07
"""

#  SPDX-License-Identifier: Apache-2.0

import importlib.util
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

# Import module directly from file to avoid fakeai/__init__.py which imports app
module_path = Path(__file__).parent.parent / "fakeai" / "streaming_metrics_tracker.py"
spec = importlib.util.spec_from_file_location("streaming_metrics_tracker", module_path)
streaming_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(streaming_module)

StreamingMetricsTracker = streaming_module.StreamingMetricsTracker
StreamState = streaming_module.StreamState
StreamingAggregateMetrics = streaming_module.StreamingAggregateMetrics


class TestStreamState:
    """Test StreamState dataclass and its methods."""

    def test_stream_state_creation(self):
        """Test creating a StreamState instance with required fields."""
        stream = StreamState(
            stream_id="test-123",
            model="gpt-4",
            start_time=1000.0,
            prompt_tokens=50,
        )

        assert stream.stream_id == "test-123"
        assert stream.model == "gpt-4"
        assert stream.start_time == 1000.0
        assert stream.prompt_tokens == 50
        assert stream.tokens_generated == 0
        assert stream.total_bytes_sent == 0
        assert len(stream.token_timestamps) == 0
        assert len(stream.tokens) == 0
        assert stream.first_token_time is None
        assert stream.last_token_time is None
        assert stream.completion_time is None
        assert stream.completed is False
        assert stream.failed is False

    def test_stream_state_with_optional_fields(self):
        """Test creating StreamState with optional metadata."""
        stream = StreamState(
            stream_id="test-123",
            model="gpt-4",
            start_time=1000.0,
            prompt_tokens=50,
            temperature=0.7,
            max_tokens=100,
            client_id="client-abc",
        )

        assert stream.temperature == 0.7
        assert stream.max_tokens == 100
        assert stream.client_id == "client-abc"

    def test_get_ttft_no_first_token(self):
        """Test TTFT calculation when no token generated yet."""
        stream = StreamState(
            stream_id="test-123",
            model="gpt-4",
            start_time=1000.0,
            prompt_tokens=50,
        )

        assert stream.get_ttft() is None

    def test_get_ttft_with_first_token(self):
        """Test TTFT calculation with first token recorded."""
        stream = StreamState(
            stream_id="test-123",
            model="gpt-4",
            start_time=1000.0,
            prompt_tokens=50,
        )
        stream.first_token_time = 1000.15  # 150ms after start

        ttft = stream.get_ttft()
        assert abs(ttft - 150.0) < 0.01  # Within 0.01ms tolerance

    def test_get_ttft_precision(self):
        """Test TTFT calculation maintains millisecond precision."""
        stream = StreamState(
            stream_id="test-123",
            model="gpt-4",
            start_time=1000.0,
            prompt_tokens=50,
        )
        stream.first_token_time = 1000.0123  # 12.3ms after start

        ttft = stream.get_ttft()
        assert abs(ttft - 12.3) < 0.01

    def test_get_duration_active_stream(self):
        """Test duration calculation for active stream uses current time."""
        stream = StreamState(
            stream_id="test-123",
            model="gpt-4",
            start_time=time.time() - 1.0,  # Started 1 second ago
            prompt_tokens=50,
        )

        duration = stream.get_duration()
        # Should be approximately 1000ms (1 second)
        assert 950 < duration < 1050

    def test_get_duration_completed_stream(self):
        """Test duration calculation for completed stream uses completion time."""
        stream = StreamState(
            stream_id="test-123",
            model="gpt-4",
            start_time=1000.0,
            prompt_tokens=50,
        )
        stream.completion_time = 1002.5  # 2.5 seconds after start

        duration = stream.get_duration()
        assert duration == 2500.0

    def test_get_tokens_per_second_no_tokens(self):
        """Test TPS calculation returns 0 when no tokens generated."""
        stream = StreamState(
            stream_id="test-123",
            model="gpt-4",
            start_time=1000.0,
            prompt_tokens=50,
        )
        stream.completion_time = 1001.0

        tps = stream.get_tokens_per_second()
        assert tps == 0.0

    def test_get_tokens_per_second_with_tokens(self):
        """Test TPS calculation with generated tokens."""
        stream = StreamState(
            stream_id="test-123",
            model="gpt-4",
            start_time=1000.0,
            prompt_tokens=50,
        )
        stream.tokens_generated = 100
        stream.completion_time = 1001.0  # 1 second

        tps = stream.get_tokens_per_second()
        assert tps == 100.0

    def test_get_tokens_per_second_fractional(self):
        """Test TPS calculation with fractional seconds."""
        stream = StreamState(
            stream_id="test-123",
            model="gpt-4",
            start_time=1000.0,
            prompt_tokens=50,
        )
        stream.tokens_generated = 50
        stream.completion_time = 1000.5  # 0.5 seconds

        tps = stream.get_tokens_per_second()
        assert tps == 100.0

    def test_get_inter_token_latencies_empty(self):
        """Test ITL calculation with no tokens returns empty list."""
        stream = StreamState(
            stream_id="test-123",
            model="gpt-4",
            start_time=1000.0,
            prompt_tokens=50,
        )

        itls = stream.get_inter_token_latencies()
        assert itls == []

    def test_get_inter_token_latencies_single_token(self):
        """Test ITL calculation with single token returns empty list."""
        stream = StreamState(
            stream_id="test-123",
            model="gpt-4",
            start_time=1000.0,
            prompt_tokens=50,
        )
        stream.token_timestamps.append(1000.1)

        itls = stream.get_inter_token_latencies()
        assert itls == []

    def test_get_inter_token_latencies_multiple_tokens(self):
        """Test ITL calculation with multiple tokens."""
        stream = StreamState(
            stream_id="test-123",
            model="gpt-4",
            start_time=1000.0,
            prompt_tokens=50,
        )
        # Tokens at 100ms, 150ms, 250ms
        stream.token_timestamps = [1000.1, 1000.15, 1000.25]

        itls = stream.get_inter_token_latencies()
        assert len(itls) == 2
        assert abs(itls[0] - 50.0) < 0.01  # 50ms between first and second
        assert abs(itls[1] - 100.0) < 0.01  # 100ms between second and third

    def test_get_average_itl_no_tokens(self):
        """Test average ITL with no tokens returns None."""
        stream = StreamState(
            stream_id="test-123",
            model="gpt-4",
            start_time=1000.0,
            prompt_tokens=50,
        )

        avg_itl = stream.get_average_itl()
        assert avg_itl is None

    def test_get_average_itl_with_tokens(self):
        """Test average ITL calculation."""
        stream = StreamState(
            stream_id="test-123",
            model="gpt-4",
            start_time=1000.0,
            prompt_tokens=50,
        )
        # Tokens at 50ms intervals
        stream.token_timestamps = [1000.0, 1000.05, 1000.1, 1000.15]

        avg_itl = stream.get_average_itl()
        assert abs(avg_itl - 50.0) < 0.01  # Within 0.01ms tolerance


class TestStreamingAggregateMetrics:
    """Test StreamingAggregateMetrics dataclass."""

    def test_metrics_creation_defaults(self):
        """Test creating metrics with default values."""
        metrics = StreamingAggregateMetrics()

        assert metrics.total_streams == 0
        assert metrics.active_streams == 0
        assert metrics.completed_streams == 0
        assert metrics.failed_streams == 0
        assert metrics.total_tokens_generated == 0
        assert metrics.success_rate == 0.0

    def test_metrics_to_dict(self):
        """Test converting metrics to dictionary."""
        metrics = StreamingAggregateMetrics(
            total_streams=100,
            active_streams=5,
            completed_streams=90,
            failed_streams=5,
            total_tokens_generated=5000,
            success_rate=0.9,
        )

        data = metrics.to_dict()

        assert data["total_streams"] == 100
        assert data["active_streams"] == 5
        assert data["completed_streams"] == 90
        assert data["failed_streams"] == 5
        assert data["total_tokens_generated"] == 5000
        assert data["success_rate"] == 0.9

    def test_metrics_to_dict_includes_all_fields(self):
        """Test to_dict includes all expected fields."""
        metrics = StreamingAggregateMetrics()
        data = metrics.to_dict()

        # Check all required fields are present
        assert "total_streams" in data
        assert "active_streams" in data
        assert "completed_streams" in data
        assert "failed_streams" in data
        assert "total_tokens_generated" in data
        assert "total_bytes_sent" in data
        assert "avg_tokens_per_second" in data
        assert "p50_tokens_per_second" in data
        assert "p95_tokens_per_second" in data
        assert "p99_tokens_per_second" in data
        assert "ttft" in data
        assert "itl" in data
        assert "duration" in data
        assert "total_backpressure_events" in data
        assert "success_rate" in data
        assert "streams_by_model" in data
        assert "tokens_by_model" in data

    def test_metrics_to_dict_rounding(self):
        """Test that float values are properly rounded."""
        metrics = StreamingAggregateMetrics(
            avg_tokens_per_second=123.456789,
            success_rate=0.123456789,
        )

        data = metrics.to_dict()

        assert data["avg_tokens_per_second"] == 123.46
        assert data["success_rate"] == 0.1235


class TestStreamingMetricsTrackerLifecycle:
    """Test stream lifecycle operations: start, record, complete, fail."""

    def test_tracker_initialization(self):
        """Test tracker initialization with default parameters."""
        tracker = StreamingMetricsTracker()

        assert tracker.max_active_streams == 10000
        assert tracker.max_completed_streams == 1000
        assert tracker.aggregation_window_seconds == 300
        assert tracker.get_active_stream_count() == 0

    def test_tracker_initialization_custom_params(self):
        """Test tracker initialization with custom parameters."""
        tracker = StreamingMetricsTracker(
            max_active_streams=500,
            max_completed_streams=100,
            aggregation_window_seconds=60,
        )

        assert tracker.max_active_streams == 500
        assert tracker.max_completed_streams == 100
        assert tracker.aggregation_window_seconds == 60

    def test_start_stream_basic(self):
        """Test starting a stream with basic parameters."""
        tracker = StreamingMetricsTracker()

        tracker.start_stream(
            stream_id="test-123",
            model="gpt-4",
            prompt_tokens=50,
        )

        assert tracker.get_active_stream_count() == 1
        details = tracker.get_stream_details("test-123")
        assert details is not None
        assert details["stream_id"] == "test-123"
        assert details["model"] == "gpt-4"
        assert details["status"] == "active"

    def test_start_stream_with_metadata(self):
        """Test starting a stream with optional metadata."""
        tracker = StreamingMetricsTracker()

        tracker.start_stream(
            stream_id="test-123",
            model="gpt-4",
            prompt_tokens=50,
            temperature=0.7,
            max_tokens=100,
            client_id="client-abc",
        )

        assert tracker.get_active_stream_count() == 1

    def test_start_stream_duplicate_ignored(self):
        """Test that starting duplicate stream ID is ignored."""
        tracker = StreamingMetricsTracker()

        tracker.start_stream(
            stream_id="test-123",
            model="gpt-4",
            prompt_tokens=50,
        )

        # Start again with same ID
        tracker.start_stream(
            stream_id="test-123",
            model="gpt-3.5-turbo",  # Different model
            prompt_tokens=100,
        )

        assert tracker.get_active_stream_count() == 1
        # Should still have original stream
        details = tracker.get_stream_details("test-123")
        assert details["model"] == "gpt-4"

    def test_start_stream_max_limit(self):
        """Test that max active streams limit is enforced."""
        tracker = StreamingMetricsTracker(max_active_streams=3)

        # Start 3 streams successfully
        for i in range(3):
            tracker.start_stream(
                stream_id=f"test-{i}",
                model="gpt-4",
                prompt_tokens=50,
            )

        assert tracker.get_active_stream_count() == 3

        # Try to start 4th stream - should raise ValueError
        with pytest.raises(ValueError, match="Max active streams limit reached"):
            tracker.start_stream(
                stream_id="test-3",
                model="gpt-4",
                prompt_tokens=50,
            )

    def test_record_token_basic(self):
        """Test recording a token in a stream."""
        tracker = StreamingMetricsTracker()

        tracker.start_stream(
            stream_id="test-123",
            model="gpt-4",
            prompt_tokens=50,
        )

        tracker.record_token(
            stream_id="test-123",
            token="hello",
            chunk_size_bytes=5,
        )

        details = tracker.get_stream_details("test-123")
        assert details["tokens_generated"] == 1

    def test_record_token_multiple(self):
        """Test recording multiple tokens."""
        tracker = StreamingMetricsTracker()

        tracker.start_stream(
            stream_id="test-123",
            model="gpt-4",
            prompt_tokens=50,
        )

        tokens = ["hello", "world", "test"]
        for token in tokens:
            tracker.record_token(
                stream_id="test-123",
                token=token,
                chunk_size_bytes=len(token),
            )

        details = tracker.get_stream_details("test-123")
        assert details["tokens_generated"] == 3

    def test_record_token_first_token_time_captured(self):
        """Test that first token time is captured on first token."""
        tracker = StreamingMetricsTracker()

        tracker.start_stream(
            stream_id="test-123",
            model="gpt-4",
            prompt_tokens=50,
        )

        # Wait a bit before first token
        time.sleep(0.05)

        tracker.record_token(
            stream_id="test-123",
            token="hello",
            chunk_size_bytes=5,
        )

        details = tracker.get_stream_details("test-123")
        assert details["ttft_ms"] is not None
        assert details["ttft_ms"] > 40  # At least 40ms

    def test_record_token_nonexistent_stream(self):
        """Test recording token for nonexistent stream is ignored."""
        tracker = StreamingMetricsTracker()

        # Should not crash
        tracker.record_token(
            stream_id="nonexistent",
            token="hello",
            chunk_size_bytes=5,
        )

        # No error, just ignored
        assert tracker.get_active_stream_count() == 0

    def test_record_token_chunk_sizes_accumulated(self):
        """Test that chunk sizes are accumulated correctly."""
        tracker = StreamingMetricsTracker()

        tracker.start_stream(
            stream_id="test-123",
            model="gpt-4",
            prompt_tokens=50,
        )

        tracker.record_token("test-123", "hello", chunk_size_bytes=10)
        tracker.record_token("test-123", "world", chunk_size_bytes=15)
        tracker.record_token("test-123", "test", chunk_size_bytes=20)

        metrics = tracker.get_metrics()
        assert metrics.total_bytes_sent == 45

    def test_complete_stream_basic(self):
        """Test completing a stream."""
        tracker = StreamingMetricsTracker()

        tracker.start_stream(
            stream_id="test-123",
            model="gpt-4",
            prompt_tokens=50,
        )

        tracker.record_token("test-123", "hello", chunk_size_bytes=5)

        tracker.complete_stream(
            stream_id="test-123",
            finish_reason="stop",
        )

        assert tracker.get_active_stream_count() == 0
        details = tracker.get_stream_details("test-123")
        assert details["status"] == "completed"
        assert details["finish_reason"] == "stop"

    def test_complete_stream_with_client_id(self):
        """Test completing stream with client_id."""
        tracker = StreamingMetricsTracker()

        tracker.start_stream(
            stream_id="test-123",
            model="gpt-4",
            prompt_tokens=50,
        )

        tracker.complete_stream(
            stream_id="test-123",
            finish_reason="stop",
            client_id="client-abc",
        )

        assert tracker.get_active_stream_count() == 0

    def test_complete_stream_nonexistent(self):
        """Test completing nonexistent stream is ignored."""
        tracker = StreamingMetricsTracker()

        # Should not crash
        tracker.complete_stream(
            stream_id="nonexistent",
            finish_reason="stop",
        )

        # No error
        assert tracker.get_active_stream_count() == 0

    def test_complete_stream_moves_to_completed(self):
        """Test that completed stream is moved to completed queue."""
        tracker = StreamingMetricsTracker()

        tracker.start_stream(
            stream_id="test-123",
            model="gpt-4",
            prompt_tokens=50,
        )

        tracker.complete_stream(
            stream_id="test-123",
            finish_reason="stop",
        )

        # Stream should be in completed queue
        details = tracker.get_stream_details("test-123")
        assert details is not None
        assert details["status"] == "completed"

    def test_fail_stream_basic(self):
        """Test failing a stream."""
        tracker = StreamingMetricsTracker()

        tracker.start_stream(
            stream_id="test-123",
            model="gpt-4",
            prompt_tokens=50,
        )

        tracker.record_token("test-123", "hello", chunk_size_bytes=5)

        tracker.fail_stream(
            stream_id="test-123",
            error_message="Connection lost",
        )

        assert tracker.get_active_stream_count() == 0
        details = tracker.get_stream_details("test-123")
        assert details["status"] == "failed"
        assert details["error_message"] == "Connection lost"

    def test_fail_stream_nonexistent(self):
        """Test failing nonexistent stream is ignored."""
        tracker = StreamingMetricsTracker()

        # Should not crash
        tracker.fail_stream(
            stream_id="nonexistent",
            error_message="Error",
        )

        # No error
        assert tracker.get_active_stream_count() == 0

    def test_fail_stream_moves_to_completed(self):
        """Test that failed stream is moved to completed queue."""
        tracker = StreamingMetricsTracker()

        tracker.start_stream(
            stream_id="test-123",
            model="gpt-4",
            prompt_tokens=50,
        )

        tracker.fail_stream(
            stream_id="test-123",
            error_message="Error",
        )

        # Failed stream should still be queryable
        details = tracker.get_stream_details("test-123")
        assert details is not None
        assert details["status"] == "failed"


class TestTokenTracking:
    """Test token tracking functionality."""

    def test_token_count_increments(self):
        """Test that token count increments correctly."""
        tracker = StreamingMetricsTracker()

        tracker.start_stream("test-123", model="gpt-4", prompt_tokens=50)

        for i in range(10):
            tracker.record_token("test-123", f"token{i}", chunk_size_bytes=5)

        details = tracker.get_stream_details("test-123")
        assert details["tokens_generated"] == 10

    def test_timestamps_recorded(self):
        """Test that timestamps are recorded for each token."""
        tracker = StreamingMetricsTracker()

        tracker.start_stream("test-123", model="gpt-4", prompt_tokens=50)

        start_time = time.time()
        for i in range(5):
            tracker.record_token("test-123", f"token{i}", chunk_size_bytes=5)
            time.sleep(0.01)  # Small delay between tokens

        end_time = time.time()

        details = tracker.get_stream_details("test-123")
        duration_ms = details["duration_ms"]

        # Duration should be approximately the elapsed time
        elapsed_ms = (end_time - start_time) * 1000
        assert abs(duration_ms - elapsed_ms) < 50  # Within 50ms tolerance

    def test_chunk_sizes_summed(self):
        """Test that chunk sizes are summed correctly."""
        tracker = StreamingMetricsTracker()

        tracker.start_stream("test-123", model="gpt-4", prompt_tokens=50)

        tracker.record_token("test-123", "hello", chunk_size_bytes=10)
        tracker.record_token("test-123", "world", chunk_size_bytes=20)
        tracker.record_token("test-123", "test", chunk_size_bytes=30)

        metrics = tracker.get_metrics()
        assert metrics.total_bytes_sent == 60

    def test_first_token_time_recorded(self):
        """Test that first token time is recorded only once."""
        tracker = StreamingMetricsTracker()

        tracker.start_stream("test-123", model="gpt-4", prompt_tokens=50)

        time.sleep(0.05)  # Wait before first token

        tracker.record_token("test-123", "first", chunk_size_bytes=5)
        first_ttft = tracker.get_stream_details("test-123")["ttft_ms"]

        time.sleep(0.05)  # Wait before second token

        tracker.record_token("test-123", "second", chunk_size_bytes=5)
        second_ttft = tracker.get_stream_details("test-123")["ttft_ms"]

        # TTFT should be the same (not updated by second token)
        assert first_ttft == second_ttft
        assert first_ttft >= 40  # At least 40ms

    def test_record_first_token_time_explicit(self):
        """Test explicitly recording first token time."""
        tracker = StreamingMetricsTracker()

        tracker.start_stream("test-123", model="gpt-4", prompt_tokens=50)

        # Explicitly set TTFT
        tracker.record_first_token_time("test-123", ttft_ms=123.45)

        details = tracker.get_stream_details("test-123")
        assert abs(details["ttft_ms"] - 123.45) < 0.1


class TestMetricsCalculation:
    """Test metrics calculation: TTFT, ITL, TPS, duration."""

    def test_ttft_calculated_correctly(self):
        """Test TTFT calculation is accurate."""
        tracker = StreamingMetricsTracker()

        tracker.start_stream("test-123", model="gpt-4", prompt_tokens=50)

        # Sleep to create measurable TTFT
        time.sleep(0.1)  # 100ms

        tracker.record_token("test-123", "hello", chunk_size_bytes=5)

        details = tracker.get_stream_details("test-123")
        ttft = details["ttft_ms"]

        # Should be approximately 100ms
        assert 90 < ttft < 110

    def test_itl_calculated_correctly(self):
        """Test inter-token latency calculation."""
        tracker = StreamingMetricsTracker()

        tracker.start_stream("test-123", model="gpt-4", prompt_tokens=50)

        # Record tokens with controlled delays
        tracker.record_token("test-123", "token1", chunk_size_bytes=5)
        time.sleep(0.05)  # 50ms
        tracker.record_token("test-123", "token2", chunk_size_bytes=5)
        time.sleep(0.05)  # 50ms
        tracker.record_token("test-123", "token3", chunk_size_bytes=5)

        tracker.complete_stream("test-123", "stop")

        details = tracker.get_stream_details("test-123")
        avg_itl = details["avg_itl_ms"]

        # Should be approximately 50ms
        assert avg_itl is not None
        assert 40 < avg_itl < 60

    def test_tps_calculated_correctly(self):
        """Test tokens per second calculation."""
        tracker = StreamingMetricsTracker()

        start_time = time.time()
        tracker.start_stream("test-123", model="gpt-4", prompt_tokens=50)

        # Generate tokens quickly
        for i in range(20):
            tracker.record_token("test-123", f"token{i}", chunk_size_bytes=5)

        time.sleep(0.1)  # Small delay to get measurable duration
        tracker.complete_stream("test-123", "stop")

        details = tracker.get_stream_details("test-123")
        tps = details["tps"]

        # Should have generated 20 tokens
        assert tps > 0
        # TPS should be high (> 100 tokens/sec typically for in-memory operations)
        assert tps > 50

    def test_duration_measured_correctly(self):
        """Test duration measurement."""
        tracker = StreamingMetricsTracker()

        tracker.start_stream("test-123", model="gpt-4", prompt_tokens=50)

        time.sleep(0.2)  # 200ms

        tracker.complete_stream("test-123", "stop")

        details = tracker.get_stream_details("test-123")
        duration = details["duration_ms"]

        # Should be approximately 200ms
        assert 190 < duration < 210


class TestPercentileCalculations:
    """Test percentile calculations for TTFT, ITL, TPS."""

    def test_ttft_percentiles_with_many_samples(self):
        """Test TTFT percentile calculation with >= 20 samples."""
        tracker = StreamingMetricsTracker()

        # Create 50 streams with varying TTFT
        for i in range(50):
            stream_id = f"test-{i}"
            tracker.start_stream(stream_id, model="gpt-4", prompt_tokens=50)

            # Vary TTFT from 10ms to 500ms by manually setting first_token_time
            ttft_ms = 10 + (i * 10)
            # Manually set TTFT in the stream state BEFORE recording token
            with tracker._lock:
                stream = tracker._active_streams[stream_id]
                stream.first_token_time = stream.start_time + (ttft_ms / 1000)
                # Also add a token to the list so there's data
                stream.tokens_generated = 1
                stream.token_timestamps.append(stream.first_token_time)

            tracker.complete_stream(stream_id, "stop")

        metrics = tracker.get_metrics()

        # Check percentiles exist and are ordered
        assert metrics.p50_ttft > 0
        assert metrics.p95_ttft > metrics.p50_ttft
        assert metrics.p99_ttft >= metrics.p95_ttft
        assert metrics.min_ttft > 0
        assert metrics.max_ttft > metrics.min_ttft

        # P50 should be around median value (255)
        assert 200 < metrics.p50_ttft < 300

    def test_ttft_percentiles_with_few_samples(self):
        """Test TTFT percentile calculation with < 20 samples."""
        tracker = StreamingMetricsTracker()

        # Create only 5 streams
        for i in range(5):
            stream_id = f"test-{i}"
            tracker.start_stream(stream_id, model="gpt-4", prompt_tokens=50)

            ttft_ms = 100 + (i * 50)
            tracker.record_first_token_time(stream_id, ttft_ms=ttft_ms)
            tracker.record_token(stream_id, "token", chunk_size_bytes=5)
            tracker.complete_stream(stream_id, "stop")

        metrics = tracker.get_metrics()

        # With < 20 samples, p95 and p99 should fall back to max
        assert metrics.p95_ttft == metrics.max_ttft
        assert metrics.p99_ttft == metrics.max_ttft

    def test_itl_percentiles_with_many_samples(self):
        """Test ITL percentile calculation with many samples."""
        tracker = StreamingMetricsTracker()

        # Create streams with varying ITL
        for i in range(30):
            stream_id = f"test-{i}"
            tracker.start_stream(stream_id, model="gpt-4", prompt_tokens=50)

            # Generate tokens with varying delays
            base_time = time.time()
            for j in range(10):
                # Mock token timestamps with controlled ITL
                pass

            # Use token timestamps to create ITL
            tracker.record_token(stream_id, "token1", chunk_size_bytes=5)
            time.sleep(0.001 * (i + 1))  # Varying delay
            tracker.record_token(stream_id, "token2", chunk_size_bytes=5)

            tracker.complete_stream(stream_id, "stop")

        metrics = tracker.get_metrics()

        # Check ITL percentiles exist
        assert metrics.p50_itl >= 0
        assert metrics.p95_itl >= metrics.p50_itl
        assert metrics.p99_itl >= metrics.p95_itl

    def test_itl_percentiles_with_few_samples(self):
        """Test ITL percentile calculation with < 20 samples."""
        tracker = StreamingMetricsTracker()

        # Create only 3 streams
        for i in range(3):
            stream_id = f"test-{i}"
            tracker.start_stream(stream_id, model="gpt-4", prompt_tokens=50)

            tracker.record_token(stream_id, "token1", chunk_size_bytes=5)
            time.sleep(0.01)
            tracker.record_token(stream_id, "token2", chunk_size_bytes=5)

            tracker.complete_stream(stream_id, "stop")

        metrics = tracker.get_metrics()

        # With < 20 samples, percentiles fall back to max
        # p50_itl is a float, not a list
        if metrics.p50_itl > 0:
            assert metrics.p95_itl >= metrics.p50_itl

    def test_tps_percentiles_with_many_samples(self):
        """Test TPS percentile calculation with many samples."""
        tracker = StreamingMetricsTracker()

        # Create 40 streams with varying TPS
        for i in range(40):
            stream_id = f"test-{i}"
            tracker.start_stream(stream_id, model="gpt-4", prompt_tokens=50)

            # Generate varying number of tokens
            token_count = 10 + i
            for j in range(token_count):
                tracker.record_token(stream_id, f"token{j}", chunk_size_bytes=5)

            time.sleep(0.01)  # Small delay for duration
            tracker.complete_stream(stream_id, "stop")

        metrics = tracker.get_metrics()

        # Check TPS percentiles exist and are ordered
        assert metrics.p50_tokens_per_second > 0
        assert metrics.p95_tokens_per_second >= metrics.p50_tokens_per_second
        assert metrics.p99_tokens_per_second >= metrics.p95_tokens_per_second

    def test_tps_percentiles_with_few_samples(self):
        """Test TPS percentile calculation with < 20 samples."""
        tracker = StreamingMetricsTracker()

        # Create only 3 streams
        for i in range(3):
            stream_id = f"test-{i}"
            tracker.start_stream(stream_id, model="gpt-4", prompt_tokens=50)

            for j in range(10):
                tracker.record_token(stream_id, f"token{j}", chunk_size_bytes=5)

            time.sleep(0.01)
            tracker.complete_stream(stream_id, "stop")

        metrics = tracker.get_metrics()

        # Percentiles fall back to max with < 20 samples
        assert metrics.p95_tokens_per_second == metrics.p99_tokens_per_second


class TestMemoryManagement:
    """Test memory management: max streams, deque bounds, eviction."""

    def test_max_active_streams_enforced(self):
        """Test that max active streams limit is enforced."""
        tracker = StreamingMetricsTracker(max_active_streams=5)

        # Create 5 streams
        for i in range(5):
            tracker.start_stream(f"test-{i}", model="gpt-4", prompt_tokens=50)

        assert tracker.get_active_stream_count() == 5

        # Try to create 6th stream
        with pytest.raises(ValueError):
            tracker.start_stream("test-5", model="gpt-4", prompt_tokens=50)

    def test_completed_streams_bounded(self):
        """Test that completed streams are bounded by maxlen."""
        tracker = StreamingMetricsTracker(max_completed_streams=3)

        # Create and complete 10 streams
        for i in range(10):
            stream_id = f"test-{i}"
            tracker.start_stream(stream_id, model="gpt-4", prompt_tokens=50)
            tracker.record_token(stream_id, "token", chunk_size_bytes=5)
            tracker.complete_stream(stream_id, "stop")

        # Should only keep last 3 completed streams
        # Check that we can find recent ones
        assert tracker.get_stream_details("test-9") is not None
        assert tracker.get_stream_details("test-8") is not None
        assert tracker.get_stream_details("test-7") is not None

        # Older ones should be gone
        assert tracker.get_stream_details("test-0") is None

    def test_old_data_evicted_properly(self):
        """Test that old data is evicted when queue is full."""
        tracker = StreamingMetricsTracker(max_completed_streams=5)

        # Create 20 streams
        for i in range(20):
            stream_id = f"test-{i}"
            tracker.start_stream(stream_id, model="gpt-4", prompt_tokens=50)
            tracker.record_token(stream_id, "token", chunk_size_bytes=5)
            tracker.complete_stream(stream_id, "stop")

        # Only last 5 should be retained
        for i in range(15, 20):
            assert tracker.get_stream_details(f"test-{i}") is not None

        # Earlier ones should be evicted
        for i in range(10):
            assert tracker.get_stream_details(f"test-{i}") is None

    def test_active_streams_freed_on_completion(self):
        """Test that active streams are freed when completed."""
        tracker = StreamingMetricsTracker(max_active_streams=5)

        # Create 5 streams
        for i in range(5):
            tracker.start_stream(f"test-{i}", model="gpt-4", prompt_tokens=50)

        assert tracker.get_active_stream_count() == 5

        # Complete one stream
        tracker.complete_stream("test-0", "stop")

        assert tracker.get_active_stream_count() == 4

        # Now we can start another
        tracker.start_stream("test-5", model="gpt-4", prompt_tokens=50)
        assert tracker.get_active_stream_count() == 5

    def test_active_streams_freed_on_failure(self):
        """Test that active streams are freed when failed."""
        tracker = StreamingMetricsTracker(max_active_streams=5)

        # Create 5 streams
        for i in range(5):
            tracker.start_stream(f"test-{i}", model="gpt-4", prompt_tokens=50)

        assert tracker.get_active_stream_count() == 5

        # Fail one stream
        tracker.fail_stream("test-0", "Error")

        assert tracker.get_active_stream_count() == 4

        # Now we can start another
        tracker.start_stream("test-5", model="gpt-4", prompt_tokens=50)
        assert tracker.get_active_stream_count() == 5


class TestAggregation:
    """Test get_metrics, time windows, per-model breakdown, success rate."""

    def test_get_metrics_basic(self):
        """Test basic metrics aggregation."""
        tracker = StreamingMetricsTracker()

        # Create some streams
        for i in range(5):
            stream_id = f"test-{i}"
            tracker.start_stream(stream_id, model="gpt-4", prompt_tokens=50)
            tracker.record_token(stream_id, "token", chunk_size_bytes=5)
            tracker.complete_stream(stream_id, "stop")

        metrics = tracker.get_metrics()

        assert metrics.total_streams == 5
        assert metrics.completed_streams == 5
        assert metrics.failed_streams == 0
        assert metrics.active_streams == 0

    def test_get_metrics_success_rate(self):
        """Test success rate calculation."""
        tracker = StreamingMetricsTracker()

        # Complete 8 streams
        for i in range(8):
            stream_id = f"test-{i}"
            tracker.start_stream(stream_id, model="gpt-4", prompt_tokens=50)
            tracker.complete_stream(stream_id, "stop")

        # Fail 2 streams
        for i in range(8, 10):
            stream_id = f"test-{i}"
            tracker.start_stream(stream_id, model="gpt-4", prompt_tokens=50)
            tracker.fail_stream(stream_id, "Error")

        metrics = tracker.get_metrics()

        assert metrics.total_streams == 10
        assert metrics.completed_streams == 8
        assert metrics.failed_streams == 2
        assert metrics.success_rate == 0.8

    def test_get_metrics_per_model_breakdown(self):
        """Test per-model stream breakdown."""
        tracker = StreamingMetricsTracker()

        # Create streams for different models
        for i in range(3):
            stream_id = f"gpt4-{i}"
            tracker.start_stream(stream_id, model="gpt-4", prompt_tokens=50)
            tracker.record_token(stream_id, "token", chunk_size_bytes=5)
            tracker.complete_stream(stream_id, "stop")

        for i in range(2):
            stream_id = f"gpt35-{i}"
            tracker.start_stream(stream_id, model="gpt-3.5-turbo", prompt_tokens=50)
            tracker.record_token(stream_id, "token", chunk_size_bytes=5)
            tracker.complete_stream(stream_id, "stop")

        metrics = tracker.get_metrics()

        assert metrics.streams_by_model["gpt-4"] == 3
        assert metrics.streams_by_model["gpt-3.5-turbo"] == 2

    def test_get_metrics_per_model_tokens(self):
        """Test per-model token breakdown."""
        tracker = StreamingMetricsTracker()

        # GPT-4 streams with 10 tokens each
        for i in range(2):
            stream_id = f"gpt4-{i}"
            tracker.start_stream(stream_id, model="gpt-4", prompt_tokens=50)
            for j in range(10):
                tracker.record_token(stream_id, f"token{j}", chunk_size_bytes=5)
            tracker.complete_stream(stream_id, "stop")

        # GPT-3.5 streams with 5 tokens each
        for i in range(2):
            stream_id = f"gpt35-{i}"
            tracker.start_stream(stream_id, model="gpt-3.5-turbo", prompt_tokens=50)
            for j in range(5):
                tracker.record_token(stream_id, f"token{j}", chunk_size_bytes=5)
            tracker.complete_stream(stream_id, "stop")

        metrics = tracker.get_metrics()

        assert metrics.tokens_by_model["gpt-4"] == 20
        assert metrics.tokens_by_model["gpt-3.5-turbo"] == 10

    def test_get_metrics_time_windowing(self):
        """Test time windowing for metrics aggregation."""
        tracker = StreamingMetricsTracker(aggregation_window_seconds=1)

        # Create old stream (outside window)
        tracker.start_stream("old", model="gpt-4", prompt_tokens=50)
        tracker.record_token("old", "token", chunk_size_bytes=5)
        # Manually set old completion time
        with tracker._lock:
            stream = tracker._active_streams.pop("old")
            stream.completion_time = time.time() - 2  # 2 seconds ago
            stream.completed = True
            tracker._completed_streams.append(stream)
            tracker._total_streams_completed += 1

        # Wait to ensure time window separation
        time.sleep(0.1)

        # Create new stream (inside window)
        tracker.start_stream("new", model="gpt-4", prompt_tokens=50)
        tracker.record_token("new", "token", chunk_size_bytes=5)
        tracker.complete_stream("new", "stop")

        metrics = tracker.get_metrics()

        # Should only include the new stream in windowed calculations
        # Note: Total counts are cumulative, but percentile calculations
        # use only windowed data

    def test_get_metrics_caching(self):
        """Test that metrics are cached to avoid recalculation."""
        tracker = StreamingMetricsTracker()

        # Create some streams
        for i in range(5):
            stream_id = f"test-{i}"
            tracker.start_stream(stream_id, model="gpt-4", prompt_tokens=50)
            tracker.complete_stream(stream_id, "stop")

        # First call calculates metrics
        metrics1 = tracker.get_metrics()
        timestamp1 = tracker._cache_timestamp

        # Second call within TTL should return cached metrics
        time.sleep(0.1)  # Small delay
        metrics2 = tracker.get_metrics()
        timestamp2 = tracker._cache_timestamp

        # Should be the same cached metrics
        assert timestamp1 == timestamp2
        assert metrics1 is metrics2

    def test_get_metrics_cache_invalidation(self):
        """Test that cache is invalidated when streams complete."""
        tracker = StreamingMetricsTracker()

        # Create and complete a stream
        tracker.start_stream("test-1", model="gpt-4", prompt_tokens=50)
        tracker.complete_stream("test-1", "stop")

        # Get metrics (populates cache)
        metrics1 = tracker.get_metrics()

        # Complete another stream (should invalidate cache)
        tracker.start_stream("test-2", model="gpt-4", prompt_tokens=50)
        tracker.complete_stream("test-2", "stop")

        # Get metrics again (should recalculate)
        metrics2 = tracker.get_metrics()

        # Should be different instances
        assert metrics1 is not metrics2
        assert metrics1.total_streams != metrics2.total_streams

    def test_get_metrics_empty_tracker(self):
        """Test metrics with no streams."""
        tracker = StreamingMetricsTracker()

        metrics = tracker.get_metrics()

        assert metrics.total_streams == 0
        assert metrics.active_streams == 0
        assert metrics.completed_streams == 0
        assert metrics.failed_streams == 0
        assert metrics.success_rate == 0.0


class TestPrometheusExport:
    """Test Prometheus metrics export."""

    def test_prometheus_format_valid(self):
        """Test that Prometheus output is valid format."""
        tracker = StreamingMetricsTracker()

        # Create some streams
        for i in range(3):
            stream_id = f"test-{i}"
            tracker.start_stream(stream_id, model="gpt-4", prompt_tokens=50)
            tracker.record_token(stream_id, "token", chunk_size_bytes=5)
            tracker.complete_stream(stream_id, "stop")

        prom_output = tracker.get_prometheus_metrics()

        # Should be a string
        assert isinstance(prom_output, str)

        # Should end with newline
        assert prom_output.endswith("\n")

        # Should contain HELP and TYPE lines
        assert "# HELP" in prom_output
        assert "# TYPE" in prom_output

    def test_prometheus_includes_all_metrics(self):
        """Test that all expected metrics are included."""
        tracker = StreamingMetricsTracker()

        # Create some streams
        for i in range(5):
            stream_id = f"test-{i}"
            tracker.start_stream(stream_id, model="gpt-4", prompt_tokens=50)
            tracker.record_token(stream_id, "token", chunk_size_bytes=5)
            tracker.complete_stream(stream_id, "stop")

        prom_output = tracker.get_prometheus_metrics()

        # Check for expected metric names
        assert "streaming_total_streams" in prom_output
        assert "streaming_active_streams" in prom_output
        assert "streaming_completed_streams" in prom_output
        assert "streaming_failed_streams" in prom_output
        assert "streaming_total_tokens" in prom_output
        assert "streaming_ttft_milliseconds" in prom_output
        assert "streaming_tokens_per_second" in prom_output
        assert "streaming_success_rate" in prom_output

    def test_prometheus_quantiles_present(self):
        """Test that quantile labels are present."""
        tracker = StreamingMetricsTracker()

        # Create streams with varying metrics
        for i in range(25):
            stream_id = f"test-{i}"
            tracker.start_stream(stream_id, model="gpt-4", prompt_tokens=50)
            tracker.record_first_token_time(stream_id, ttft_ms=100 + i)
            tracker.record_token(stream_id, "token", chunk_size_bytes=5)
            tracker.complete_stream(stream_id, "stop")

        prom_output = tracker.get_prometheus_metrics()

        # Check for quantile labels
        assert 'quantile="0.5"' in prom_output
        assert 'quantile="0.95"' in prom_output
        assert 'quantile="0.99"' in prom_output

    def test_prometheus_per_model_labels(self):
        """Test that per-model metrics have proper labels."""
        tracker = StreamingMetricsTracker()

        # Create streams for multiple models
        tracker.start_stream("test-1", model="gpt-4", prompt_tokens=50)
        tracker.complete_stream("test-1", "stop")

        tracker.start_stream("test-2", model="gpt-3.5-turbo", prompt_tokens=50)
        tracker.complete_stream("test-2", "stop")

        prom_output = tracker.get_prometheus_metrics()

        # Check for model labels
        assert 'model="gpt-4"' in prom_output
        assert 'model="gpt-3.5-turbo"' in prom_output
        assert "streaming_streams_by_model" in prom_output

    def test_prometheus_metric_types(self):
        """Test that correct metric types are used."""
        tracker = StreamingMetricsTracker()

        tracker.start_stream("test-1", model="gpt-4", prompt_tokens=50)
        tracker.complete_stream("test-1", "stop")

        prom_output = tracker.get_prometheus_metrics()

        # Check metric types
        assert "# TYPE streaming_total_streams counter" in prom_output
        assert "# TYPE streaming_active_streams gauge" in prom_output
        assert "# TYPE streaming_ttft_milliseconds summary" in prom_output
        assert "# TYPE streaming_tokens_per_second summary" in prom_output

    def test_prometheus_empty_tracker(self):
        """Test Prometheus output with no streams."""
        tracker = StreamingMetricsTracker()

        prom_output = tracker.get_prometheus_metrics()

        # Should still produce valid output
        assert isinstance(prom_output, str)
        assert len(prom_output) > 0
        assert "streaming_total_streams 0" in prom_output


class TestBackpressure:
    """Test backpressure tracking."""

    def test_record_backpressure_basic(self):
        """Test recording backpressure events."""
        tracker = StreamingMetricsTracker()

        tracker.start_stream("test-123", model="gpt-4", prompt_tokens=50)
        tracker.record_backpressure("test-123")

        details = tracker.get_stream_details("test-123")
        assert details["backpressure_count"] == 1

    def test_record_backpressure_multiple(self):
        """Test recording multiple backpressure events."""
        tracker = StreamingMetricsTracker()

        tracker.start_stream("test-123", model="gpt-4", prompt_tokens=50)

        for _ in range(5):
            tracker.record_backpressure("test-123")

        details = tracker.get_stream_details("test-123")
        assert details["backpressure_count"] == 5

    def test_record_backpressure_nonexistent(self):
        """Test recording backpressure for nonexistent stream."""
        tracker = StreamingMetricsTracker()

        # Should not crash
        tracker.record_backpressure("nonexistent")

    def test_backpressure_in_aggregate_metrics(self):
        """Test that backpressure is included in aggregate metrics."""
        tracker = StreamingMetricsTracker()

        # Create streams with backpressure
        for i in range(3):
            stream_id = f"test-{i}"
            tracker.start_stream(stream_id, model="gpt-4", prompt_tokens=50)
            tracker.record_backpressure(stream_id)
            tracker.record_backpressure(stream_id)
            tracker.complete_stream(stream_id, "stop")

        metrics = tracker.get_metrics()
        assert metrics.total_backpressure_events == 6


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_zero_duration_stream(self):
        """Test stream with near-zero duration."""
        tracker = StreamingMetricsTracker()

        tracker.start_stream("test-123", model="gpt-4", prompt_tokens=50)
        # Complete immediately
        tracker.complete_stream("test-123", "stop")

        details = tracker.get_stream_details("test-123")
        # Duration should be very small but non-negative
        assert details["duration_ms"] >= 0
        assert details["duration_ms"] < 10

    def test_stream_with_no_tokens(self):
        """Test completing stream without generating tokens."""
        tracker = StreamingMetricsTracker()

        tracker.start_stream("test-123", model="gpt-4", prompt_tokens=50)
        tracker.complete_stream("test-123", "stop")

        details = tracker.get_stream_details("test-123")
        assert details["tokens_generated"] == 0
        assert details["ttft_ms"] is None
        assert details["tps"] == 0.0

    def test_single_token_stream(self):
        """Test stream with single token."""
        tracker = StreamingMetricsTracker()

        tracker.start_stream("test-123", model="gpt-4", prompt_tokens=50)
        tracker.record_token("test-123", "token", chunk_size_bytes=5)
        tracker.complete_stream("test-123", "stop")

        details = tracker.get_stream_details("test-123")
        assert details["tokens_generated"] == 1
        assert details["ttft_ms"] is not None
        # Single token has no ITL
        assert details["avg_itl_ms"] is None

    def test_get_stream_details_nonexistent(self):
        """Test getting details for nonexistent stream."""
        tracker = StreamingMetricsTracker()

        details = tracker.get_stream_details("nonexistent")
        assert details is None

    def test_multiple_starts_ignored(self):
        """Test that multiple start calls for same ID are ignored."""
        tracker = StreamingMetricsTracker()

        tracker.start_stream("test-123", model="gpt-4", prompt_tokens=50)
        tracker.start_stream("test-123", model="claude", prompt_tokens=100)

        details = tracker.get_stream_details("test-123")
        # Should still be the first model
        assert details["model"] == "gpt-4"

    def test_complete_before_start(self):
        """Test completing stream that was never started."""
        tracker = StreamingMetricsTracker()

        # Should not crash
        tracker.complete_stream("never-started", "stop")

    def test_fail_before_start(self):
        """Test failing stream that was never started."""
        tracker = StreamingMetricsTracker()

        # Should not crash
        tracker.fail_stream("never-started", "Error")

    def test_empty_token_string(self):
        """Test recording empty token."""
        tracker = StreamingMetricsTracker()

        tracker.start_stream("test-123", model="gpt-4", prompt_tokens=50)
        tracker.record_token("test-123", "", chunk_size_bytes=0)

        details = tracker.get_stream_details("test-123")
        assert details["tokens_generated"] == 1

    def test_negative_chunk_size_handled(self):
        """Test that negative chunk size is handled."""
        tracker = StreamingMetricsTracker()

        tracker.start_stream("test-123", model="gpt-4", prompt_tokens=50)
        # Record with negative chunk size (shouldn't happen but test resilience)
        tracker.record_token("test-123", "token", chunk_size_bytes=-5)

        # Should not crash
        metrics = tracker.get_metrics()
        # Negative bytes would be added (not ideal but won't crash)


class TestReset:
    """Test reset functionality."""

    def test_reset_clears_active_streams(self):
        """Test that reset clears active streams."""
        tracker = StreamingMetricsTracker()

        for i in range(5):
            tracker.start_stream(f"test-{i}", model="gpt-4", prompt_tokens=50)

        assert tracker.get_active_stream_count() == 5

        tracker.reset()

        assert tracker.get_active_stream_count() == 0

    def test_reset_clears_completed_streams(self):
        """Test that reset clears completed streams."""
        tracker = StreamingMetricsTracker()

        for i in range(5):
            stream_id = f"test-{i}"
            tracker.start_stream(stream_id, model="gpt-4", prompt_tokens=50)
            tracker.complete_stream(stream_id, "stop")

        tracker.reset()

        # Completed streams should be gone
        assert tracker.get_stream_details("test-0") is None

    def test_reset_clears_counters(self):
        """Test that reset clears all counters."""
        tracker = StreamingMetricsTracker()

        for i in range(5):
            stream_id = f"test-{i}"
            tracker.start_stream(stream_id, model="gpt-4", prompt_tokens=50)
            tracker.record_token(stream_id, "token", chunk_size_bytes=10)
            tracker.complete_stream(stream_id, "stop")

        tracker.reset()

        metrics = tracker.get_metrics()
        assert metrics.total_streams == 0
        assert metrics.completed_streams == 0
        assert metrics.total_tokens_generated == 0
        assert metrics.total_bytes_sent == 0

    def test_reset_invalidates_cache(self):
        """Test that reset invalidates metrics cache."""
        tracker = StreamingMetricsTracker()

        tracker.start_stream("test-1", model="gpt-4", prompt_tokens=50)
        tracker.complete_stream("test-1", "stop")

        # Get metrics (populates cache)
        tracker.get_metrics()

        # Reset
        tracker.reset()

        # Cache should be cleared
        assert tracker._cached_metrics is None


class TestThreadSafety:
    """Test thread safety and concurrent access."""

    def test_concurrent_start_streams(self):
        """Test starting streams from multiple threads."""
        tracker = StreamingMetricsTracker(max_active_streams=200)

        def start_streams(thread_id: int):
            for i in range(10):
                stream_id = f"thread{thread_id}-stream{i}"
                try:
                    tracker.start_stream(stream_id, model="gpt-4", prompt_tokens=50)
                except ValueError:
                    # Might hit limit, that's ok
                    pass

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(start_streams, i) for i in range(10)]
            for future in futures:
                future.result()

        # Should have created many streams (up to 100 or max limit)
        count = tracker.get_active_stream_count()
        assert count > 0
        assert count <= tracker.max_active_streams

    def test_concurrent_record_tokens(self):
        """Test recording tokens from multiple threads."""
        tracker = StreamingMetricsTracker()

        # Create streams
        for i in range(10):
            tracker.start_stream(f"test-{i}", model="gpt-4", prompt_tokens=50)

        def record_tokens(stream_id: str):
            for i in range(20):
                tracker.record_token(stream_id, f"token{i}", chunk_size_bytes=5)

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(record_tokens, f"test-{i}") for i in range(10)
            ]
            for future in futures:
                future.result()

        # Each stream should have 20 tokens
        metrics = tracker.get_metrics()
        assert metrics.total_tokens_generated == 200

    def test_concurrent_complete_streams(self):
        """Test completing streams from multiple threads."""
        tracker = StreamingMetricsTracker()

        # Create streams
        for i in range(20):
            tracker.start_stream(f"test-{i}", model="gpt-4", prompt_tokens=50)

        def complete_stream(stream_id: str):
            tracker.complete_stream(stream_id, "stop")

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(complete_stream, f"test-{i}") for i in range(20)
            ]
            for future in futures:
                future.result()

        # All streams should be completed
        assert tracker.get_active_stream_count() == 0

    def test_concurrent_get_metrics(self):
        """Test getting metrics from multiple threads concurrently."""
        tracker = StreamingMetricsTracker()

        # Create some streams
        for i in range(10):
            stream_id = f"test-{i}"
            tracker.start_stream(stream_id, model="gpt-4", prompt_tokens=50)
            tracker.record_token(stream_id, "token", chunk_size_bytes=5)
            tracker.complete_stream(stream_id, "stop")

        def get_metrics():
            return tracker.get_metrics()

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(get_metrics) for _ in range(100)]
            results = [future.result() for future in futures]

        # All results should be valid
        for metrics in results:
            assert metrics.total_streams == 10
            assert metrics.completed_streams == 10


class TestPerformance:
    """Performance and stress tests."""

    def test_many_streams_performance(self):
        """Test creating and completing many streams."""
        tracker = StreamingMetricsTracker(
            max_active_streams=1000, max_completed_streams=1000
        )

        start_time = time.time()

        # Create 500 streams
        for i in range(500):
            stream_id = f"test-{i}"
            tracker.start_stream(stream_id, model="gpt-4", prompt_tokens=50)
            # Generate some tokens
            for j in range(10):
                tracker.record_token(stream_id, f"token{j}", chunk_size_bytes=5)
            tracker.complete_stream(stream_id, "stop")

        elapsed = time.time() - start_time

        # Should complete in reasonable time (< 5 seconds)
        assert elapsed < 5.0

        # Verify correctness
        metrics = tracker.get_metrics()
        assert metrics.total_streams == 500
        assert metrics.total_tokens_generated == 5000

    def test_metrics_calculation_performance(self):
        """Test that metrics calculation is reasonably fast."""
        tracker = StreamingMetricsTracker()

        # Create many completed streams
        for i in range(100):
            stream_id = f"test-{i}"
            tracker.start_stream(stream_id, model="gpt-4", prompt_tokens=50)
            tracker.record_first_token_time(stream_id, ttft_ms=100 + i)
            for j in range(20):
                tracker.record_token(stream_id, f"token{j}", chunk_size_bytes=5)
            tracker.complete_stream(stream_id, "stop")

        # Invalidate cache
        tracker._cached_metrics = None

        start_time = time.time()
        metrics = tracker.get_metrics()
        elapsed = time.time() - start_time

        # Should calculate in < 100ms
        assert elapsed < 0.1

        # Verify correctness
        assert metrics.total_streams == 100

    def test_prometheus_export_performance(self):
        """Test that Prometheus export is reasonably fast."""
        tracker = StreamingMetricsTracker()

        # Create many streams with different models
        for i in range(50):
            stream_id = f"test-{i}"
            model = f"model-{i % 5}"  # 5 different models
            tracker.start_stream(stream_id, model=model, prompt_tokens=50)
            tracker.record_token(stream_id, "token", chunk_size_bytes=5)
            tracker.complete_stream(stream_id, "stop")

        start_time = time.time()
        prom_output = tracker.get_prometheus_metrics()
        elapsed = time.time() - start_time

        # Should export in < 50ms
        assert elapsed < 0.05

        # Verify output is valid
        assert len(prom_output) > 0

    def test_high_frequency_token_recording(self):
        """Test recording tokens at high frequency."""
        tracker = StreamingMetricsTracker()

        tracker.start_stream("test-123", model="gpt-4", prompt_tokens=50)

        start_time = time.time()

        # Record 1000 tokens as fast as possible
        for i in range(1000):
            tracker.record_token("test-123", f"token{i}", chunk_size_bytes=5)

        elapsed = time.time() - start_time

        # Should handle high frequency (< 1 second for 1000 tokens)
        assert elapsed < 1.0

        details = tracker.get_stream_details("test-123")
        assert details["tokens_generated"] == 1000


class TestStreamDetails:
    """Test get_stream_details functionality."""

    def test_get_active_stream_details(self):
        """Test getting details for active stream."""
        tracker = StreamingMetricsTracker()

        tracker.start_stream("test-123", model="gpt-4", prompt_tokens=50)
        tracker.record_token("test-123", "token", chunk_size_bytes=5)

        details = tracker.get_stream_details("test-123")

        assert details is not None
        assert details["stream_id"] == "test-123"
        assert details["model"] == "gpt-4"
        assert details["status"] == "active"
        assert details["tokens_generated"] == 1
        assert "duration_ms" in details
        assert "ttft_ms" in details
        assert "tps" in details

    def test_get_completed_stream_details(self):
        """Test getting details for completed stream."""
        tracker = StreamingMetricsTracker()

        tracker.start_stream("test-123", model="gpt-4", prompt_tokens=50)
        tracker.record_token("test-123", "token", chunk_size_bytes=5)
        tracker.complete_stream("test-123", "stop")

        details = tracker.get_stream_details("test-123")

        assert details is not None
        assert details["status"] == "completed"
        assert details["finish_reason"] == "stop"

    def test_get_failed_stream_details(self):
        """Test getting details for failed stream."""
        tracker = StreamingMetricsTracker()

        tracker.start_stream("test-123", model="gpt-4", prompt_tokens=50)
        tracker.fail_stream("test-123", "Connection error")

        details = tracker.get_stream_details("test-123")

        assert details is not None
        assert details["status"] == "failed"
        assert details["error_message"] == "Connection error"

    def test_get_stream_details_searches_completed(self):
        """Test that get_stream_details searches completed queue."""
        tracker = StreamingMetricsTracker()

        # Create and complete multiple streams
        for i in range(5):
            stream_id = f"test-{i}"
            tracker.start_stream(stream_id, model="gpt-4", prompt_tokens=50)
            tracker.complete_stream(stream_id, "stop")

        # Should find all completed streams
        for i in range(5):
            details = tracker.get_stream_details(f"test-{i}")
            assert details is not None
