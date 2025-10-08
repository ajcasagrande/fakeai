"""
Comprehensive tests for streaming latency metrics (TTFT and ITL).

This test suite validates the accuracy and reliability of streaming latency
measurements including Time to First Token (TTFT) and Inter-Token Latency (ITL).

Coverage:
1. TTFT (Time to First Token) - Latency from request start to first token
2. ITL (Inter-Token Latency) - Latency between consecutive tokens
3. Edge cases - Single token, zero tokens, extreme latencies
4. Statistical accuracy - Percentile calculations (p50/p95/p99)
5. Real-world scenarios - Simulating different model behaviors
"""

#  SPDX-License-Identifier: Apache-2.0

import statistics
import time

import pytest

from fakeai.streaming_metrics_tracker import (
    StreamingMetricsTracker,
)


class TestTTFTCalculation:
    """Test Time to First Token (TTFT) calculation accuracy."""

    def test_ttft_basic_calculation(self):
        """Test basic TTFT calculation - (first_token_time - start_time)."""
        tracker = StreamingMetricsTracker()

        # Start stream at known time
        stream_id = "test-ttft-basic"
        tracker.start_stream(stream_id=stream_id, model="gpt-4", prompt_tokens=50)

        # Manually set precise timing
        stream = tracker._active_streams[stream_id]
        start_time = 1000.0  # 1000 seconds
        stream.start_time = start_time

        # First token arrives 150ms later
        first_token_time = start_time + 0.150  # 150ms = 0.150s
        stream.first_token_time = first_token_time

        # Calculate TTFT
        ttft = stream.get_ttft()
        assert ttft is not None, "TTFT should not be None"
        assert abs(ttft - 150.0) < 0.001, f"TTFT should be ~150.0ms, got {ttft}ms"

    def test_ttft_millisecond_accuracy(self):
        """Test TTFT is accurate to milliseconds."""
        tracker = StreamingMetricsTracker()

        stream_id = "test-ttft-precision"
        tracker.start_stream(stream_id=stream_id, model="gpt-4", prompt_tokens=50)

        stream = tracker._active_streams[stream_id]
        start_time = 1000.0
        stream.start_time = start_time

        # Test various millisecond values
        test_cases = [
            (0.001, 1.0),  # 1ms
            (0.010, 10.0),  # 10ms
            (0.100, 100.0),  # 100ms
            (0.250, 250.0),  # 250ms
            (1.500, 1500.0),  # 1.5s
        ]

        for delta_seconds, expected_ms in test_cases:
            stream.first_token_time = start_time + delta_seconds
            ttft = stream.get_ttft()
            assert abs(ttft - expected_ms) < 0.001, f"Expected {expected_ms}ms, got {ttft}ms"

    def test_ttft_captured_on_first_token_only(self):
        """Test TTFT is captured on the first token and not changed after."""
        tracker = StreamingMetricsTracker()

        stream_id = "test-ttft-first-only"
        tracker.start_stream(stream_id=stream_id, model="gpt-4", prompt_tokens=50)

        # Record first token
        start_time = time.time()
        time.sleep(0.05)  # 50ms delay
        tracker.record_token(stream_id, "first")

        # Get TTFT after first token
        stream = tracker._active_streams[stream_id]
        first_ttft = stream.get_ttft()
        first_token_time = stream.first_token_time

        # Record more tokens
        tracker.record_token(stream_id, "second")
        tracker.record_token(stream_id, "third")

        # TTFT should not change
        assert stream.first_token_time == first_token_time
        assert stream.get_ttft() == first_ttft

    def test_ttft_none_when_no_tokens(self):
        """Test TTFT is None when no tokens have been generated."""
        tracker = StreamingMetricsTracker()

        stream_id = "test-ttft-none"
        tracker.start_stream(stream_id=stream_id, model="gpt-4", prompt_tokens=50)

        stream = tracker._active_streams[stream_id]
        ttft = stream.get_ttft()
        assert ttft is None, "TTFT should be None when no tokens generated"

    def test_ttft_with_very_fast_token(self):
        """Test TTFT with very fast tokens (< 1ms)."""
        tracker = StreamingMetricsTracker()

        stream_id = "test-ttft-fast"
        tracker.start_stream(stream_id=stream_id, model="gpt-4", prompt_tokens=50)

        stream = tracker._active_streams[stream_id]
        start_time = 1000.0
        stream.start_time = start_time

        # First token arrives 0.5ms later
        stream.first_token_time = start_time + 0.0005  # 0.5ms
        ttft = stream.get_ttft()

        assert abs(ttft - 0.5) < 0.001, f"TTFT should be ~0.5ms, got {ttft}ms"

    def test_ttft_with_very_slow_token(self):
        """Test TTFT with very slow tokens (> 1s)."""
        tracker = StreamingMetricsTracker()

        stream_id = "test-ttft-slow"
        tracker.start_stream(stream_id=stream_id, model="gpt-4", prompt_tokens=50)

        stream = tracker._active_streams[stream_id]
        start_time = 1000.0
        stream.start_time = start_time

        # First token arrives 5 seconds later
        stream.first_token_time = start_time + 5.0
        ttft = stream.get_ttft()

        assert abs(ttft - 5000.0) < 0.01, f"TTFT should be ~5000.0ms, got {ttft}ms"


class TestITLCalculation:
    """Test Inter-Token Latency (ITL) calculation accuracy."""

    def test_itl_basic_calculation(self):
        """Test basic ITL calculation between consecutive tokens."""
        tracker = StreamingMetricsTracker()

        stream_id = "test-itl-basic"
        tracker.start_stream(stream_id=stream_id, model="gpt-4", prompt_tokens=50)

        stream = tracker._active_streams[stream_id]
        base_time = 1000.0

        # Add tokens with known intervals
        stream.token_timestamps = [
            base_time,  # Token 0
            base_time + 0.050,  # Token 1 (50ms later)
            base_time + 0.150,  # Token 2 (100ms later)
            base_time + 0.200,  # Token 3 (50ms later)
        ]

        itls = stream.get_inter_token_latencies()
        expected_itls = [50.0, 100.0, 50.0]

        assert len(itls) == 3, f"Expected 3 ITLs, got {len(itls)}"
        for i, (actual, expected) in enumerate(zip(itls, expected_itls)):
            assert abs(actual - expected) < 0.001, f"ITL[{i}] should be ~{expected}ms, got {actual}ms"

    def test_itl_array_generation(self):
        """Test ITL generates array of latencies correctly."""
        tracker = StreamingMetricsTracker()

        stream_id = "test-itl-array"
        tracker.start_stream(stream_id=stream_id, model="gpt-4", prompt_tokens=50)

        stream = tracker._active_streams[stream_id]
        base_time = 1000.0

        # Add 10 tokens
        stream.token_timestamps = [base_time + (i * 0.010) for i in range(10)]

        itls = stream.get_inter_token_latencies()

        # Should have 9 inter-token latencies (10 tokens - 1)
        assert len(itls) == 9, f"Expected 9 ITLs for 10 tokens, got {len(itls)}"

        # All ITLs should be 10ms
        for i, itl in enumerate(itls):
            assert abs(itl - 10.0) < 0.001, f"ITL[{i}] should be ~10.0ms, got {itl}ms"

    def test_itl_average_calculation(self):
        """Test average ITL calculation is correct."""
        tracker = StreamingMetricsTracker()

        stream_id = "test-itl-avg"
        tracker.start_stream(stream_id=stream_id, model="gpt-4", prompt_tokens=50)

        stream = tracker._active_streams[stream_id]
        base_time = 1000.0

        # Add tokens with varying ITLs
        stream.token_timestamps = [
            base_time,  # Token 0
            base_time + 0.010,  # Token 1 (10ms)
            base_time + 0.030,  # Token 2 (20ms)
            base_time + 0.060,  # Token 3 (30ms)
            base_time + 0.100,  # Token 4 (40ms)
            base_time + 0.150,  # Token 5 (50ms)
        ]

        avg_itl = stream.get_average_itl()
        # ITLs: 10, 20, 30, 40, 50 -> Average = 30
        expected_avg = 30.0

        assert avg_itl is not None, "Average ITL should not be None"
        assert abs(avg_itl - expected_avg) < 0.001, f"Average ITL should be ~{expected_avg}ms, got {avg_itl}ms"

    def test_itl_with_single_token(self):
        """Test ITL with only 1 token (no ITL possible)."""
        tracker = StreamingMetricsTracker()

        stream_id = "test-itl-single"
        tracker.start_stream(stream_id=stream_id, model="gpt-4", prompt_tokens=50)

        stream = tracker._active_streams[stream_id]
        stream.token_timestamps = [1000.0]

        itls = stream.get_inter_token_latencies()
        assert len(itls) == 0, "Single token should have no ITLs"

        avg_itl = stream.get_average_itl()
        assert avg_itl is None, "Average ITL should be None for single token"

    def test_itl_with_no_tokens(self):
        """Test ITL with 0 tokens."""
        tracker = StreamingMetricsTracker()

        stream_id = "test-itl-none"
        tracker.start_stream(stream_id=stream_id, model="gpt-4", prompt_tokens=50)

        stream = tracker._active_streams[stream_id]
        itls = stream.get_inter_token_latencies()

        assert len(itls) == 0, "No tokens should have no ITLs"

        avg_itl = stream.get_average_itl()
        assert avg_itl is None, "Average ITL should be None with no tokens"

    def test_itl_very_fast_tokens(self):
        """Test ITL with very fast tokens (< 1ms)."""
        tracker = StreamingMetricsTracker()

        stream_id = "test-itl-fast"
        tracker.start_stream(stream_id=stream_id, model="gpt-4", prompt_tokens=50)

        stream = tracker._active_streams[stream_id]
        base_time = 1000.0

        # Tokens 0.1ms apart
        stream.token_timestamps = [base_time + (i * 0.0001) for i in range(5)]

        itls = stream.get_inter_token_latencies()

        # All ITLs should be 0.1ms
        for i, itl in enumerate(itls):
            assert abs(itl - 0.1) < 0.001, f"ITL[{i}] should be ~0.1ms, got {itl}ms"

    def test_itl_very_slow_tokens(self):
        """Test ITL with very slow tokens (> 1s)."""
        tracker = StreamingMetricsTracker()

        stream_id = "test-itl-slow"
        tracker.start_stream(stream_id=stream_id, model="gpt-4", prompt_tokens=50)

        stream = tracker._active_streams[stream_id]
        base_time = 1000.0

        # Tokens 2 seconds apart
        stream.token_timestamps = [base_time + (i * 2.0) for i in range(3)]

        itls = stream.get_inter_token_latencies()
        expected_itls = [2000.0, 2000.0]

        assert len(itls) == 2
        for i, (actual, expected) in enumerate(zip(itls, expected_itls)):
            assert abs(actual - expected) < 0.01, f"ITL[{i}] should be ~{expected}ms, got {actual}ms"


class TestPercentileAccuracy:
    """Test statistical percentile calculations for TTFT and ITL."""

    def test_ttft_median_calculation(self):
        """Test p50 (median) TTFT calculation."""
        tracker = StreamingMetricsTracker()

        # Create 5 completed streams with known TTFTs
        ttft_values = [100.0, 150.0, 200.0, 250.0, 300.0]

        for i, ttft_ms in enumerate(ttft_values):
            stream_id = f"stream-{i}"
            tracker.start_stream(stream_id=stream_id, model="gpt-4", prompt_tokens=50)

            stream = tracker._active_streams[stream_id]
            stream.start_time = 1000.0
            stream.first_token_time = 1000.0 + (ttft_ms / 1000.0)
            stream.token_timestamps.append(stream.first_token_time)
            stream.tokens_generated = 1

            tracker.complete_stream(stream_id, "stop")

        metrics = tracker.get_metrics()

        # Median should be 200.0ms (middle value)
        assert abs(metrics.p50_ttft - 200.0) < 0.01, f"p50 TTFT should be ~200.0ms, got {metrics.p50_ttft}ms"
        assert abs(metrics.avg_ttft - 200.0) < 0.01, f"Average TTFT should be ~200.0ms, got {metrics.avg_ttft}ms"

    def test_ttft_p95_with_small_sample(self):
        """Test p95 TTFT with < 20 samples (should use max)."""
        tracker = StreamingMetricsTracker()

        # Create 10 streams (< 20)
        ttft_values = list(range(10, 110, 10))  # 10, 20, 30, ..., 100

        for i, ttft_ms in enumerate(ttft_values):
            stream_id = f"stream-{i}"
            tracker.start_stream(stream_id=stream_id, model="gpt-4", prompt_tokens=50)

            stream = tracker._active_streams[stream_id]
            stream.start_time = 1000.0
            stream.first_token_time = 1000.0 + (ttft_ms / 1000.0)
            stream.token_timestamps.append(stream.first_token_time)
            stream.tokens_generated = 1

            tracker.complete_stream(stream_id, "stop")

        metrics = tracker.get_metrics()

        # With < 20 samples, p95 should be max value (100.0)
        assert abs(metrics.p95_ttft - 100.0) < 0.01, f"p95 TTFT should be ~100.0ms (max), got {metrics.p95_ttft}ms"
        assert abs(metrics.max_ttft - 100.0) < 0.01, f"Max TTFT should be ~100.0ms, got {metrics.max_ttft}ms"

    def test_ttft_p95_with_large_sample(self):
        """Test p95 TTFT with >= 20 samples."""
        tracker = StreamingMetricsTracker()

        # Create 100 streams with values 1-100ms
        ttft_values = list(range(1, 101))

        for ttft_ms in ttft_values:
            stream_id = f"stream-{ttft_ms}"
            tracker.start_stream(stream_id=stream_id, model="gpt-4", prompt_tokens=50)

            stream = tracker._active_streams[stream_id]
            stream.start_time = 1000.0
            stream.first_token_time = 1000.0 + (ttft_ms / 1000.0)
            stream.token_timestamps.append(stream.first_token_time)
            stream.tokens_generated = 1

            tracker.complete_stream(stream_id, "stop")

        metrics = tracker.get_metrics()

        # p95 should be around 95th value
        # Using quantiles(n=20)[18] which is the 95th percentile
        expected_p95 = statistics.quantiles(ttft_values, n=20)[18]
        assert abs(metrics.p95_ttft - expected_p95) < 0.01, f"p95 TTFT should be ~{expected_p95}ms, got {metrics.p95_ttft}ms"

    def test_ttft_p99_with_large_dataset(self):
        """Test p99 TTFT with large dataset."""
        tracker = StreamingMetricsTracker()

        # Create 200 streams
        ttft_values = list(range(1, 201))

        for ttft_ms in ttft_values:
            stream_id = f"stream-{ttft_ms}"
            tracker.start_stream(stream_id=stream_id, model="gpt-4", prompt_tokens=50)

            stream = tracker._active_streams[stream_id]
            stream.start_time = 1000.0
            stream.first_token_time = 1000.0 + (ttft_ms / 1000.0)
            stream.token_timestamps.append(stream.first_token_time)
            stream.tokens_generated = 1

            tracker.complete_stream(stream_id, "stop")

        metrics = tracker.get_metrics()

        # p99 using quantiles(n=100)[98]
        expected_p99 = statistics.quantiles(ttft_values, n=100)[98]
        assert abs(metrics.p99_ttft - expected_p99) < 0.01, f"p99 TTFT should be ~{expected_p99}ms, got {metrics.p99_ttft}ms"

    def test_itl_percentiles_with_varying_data(self):
        """Test ITL percentile calculations with varying data."""
        tracker = StreamingMetricsTracker()

        # Create 30 streams with varying ITLs
        for stream_num in range(30):
            stream_id = f"stream-{stream_num}"
            tracker.start_stream(stream_id=stream_id, model="gpt-4", prompt_tokens=50)

            stream = tracker._active_streams[stream_id]
            base_time = 1000.0

            # Each stream has 10 tokens with ITLs ranging from 5-50ms
            itl_base = 5 + stream_num  # 5, 6, 7, ..., 34ms
            stream.token_timestamps = [
                base_time + (i * itl_base / 1000.0) for i in range(10)
            ]
            stream.tokens_generated = 10

            tracker.complete_stream(stream_id, "stop")

        metrics = tracker.get_metrics()

        # Verify we got ITL percentiles
        assert metrics.p50_itl > 0, "p50 ITL should be > 0"
        assert metrics.p95_itl > 0, "p95 ITL should be > 0"
        assert metrics.p99_itl > 0, "p99 ITL should be > 0"
        assert metrics.p95_itl >= metrics.p50_itl, "p95 should be >= p50"
        assert metrics.p99_itl >= metrics.p95_itl, "p99 should be >= p95"


class TestRealWorldScenarios:
    """Test real-world model latency scenarios."""

    def test_gpt4_slow_ttft_consistent_itl(self):
        """Simulate GPT-4: slow TTFT (~500ms), consistent ITL (~30ms)."""
        tracker = StreamingMetricsTracker()

        # Create 10 GPT-4 streams
        for i in range(10):
            stream_id = f"gpt4-{i}"
            tracker.start_stream(stream_id=stream_id, model="gpt-4", prompt_tokens=100)

            stream = tracker._active_streams[stream_id]
            start_time = 1000.0
            stream.start_time = start_time

            # TTFT: 450-550ms (500ms ± 50ms)
            ttft_ms = 500.0 + ((i - 5) * 10)  # 450, 460, ..., 550
            stream.first_token_time = start_time + (ttft_ms / 1000.0)

            # Generate 20 tokens with consistent 30ms ITL
            current_time = stream.first_token_time
            stream.token_timestamps = [current_time]
            for _ in range(19):
                current_time += 0.030  # 30ms
                stream.token_timestamps.append(current_time)

            stream.tokens_generated = 20
            tracker.complete_stream(stream_id, "stop")

        metrics = tracker.get_metrics()

        # Verify GPT-4 characteristics
        assert 450 <= metrics.p50_ttft <= 550, f"GPT-4 p50 TTFT should be ~500ms, got {metrics.p50_ttft}ms"
        assert 25 <= metrics.avg_itl <= 35, f"GPT-4 avg ITL should be ~30ms, got {metrics.avg_itl}ms"

    def test_gpt4o_fast_ttft_variable_itl(self):
        """Simulate GPT-4o: fast TTFT (~100ms), variable ITL (15-45ms)."""
        tracker = StreamingMetricsTracker()

        # Create 10 GPT-4o streams
        for i in range(10):
            stream_id = f"gpt4o-{i}"
            tracker.start_stream(stream_id=stream_id, model="gpt-4o", prompt_tokens=100)

            stream = tracker._active_streams[stream_id]
            start_time = 1000.0
            stream.start_time = start_time

            # TTFT: 80-120ms (100ms ± 20ms)
            ttft_ms = 100.0 + ((i - 5) * 4)  # 80, 84, ..., 120
            stream.first_token_time = start_time + (ttft_ms / 1000.0)

            # Generate 20 tokens with variable ITL (15-45ms)
            current_time = stream.first_token_time
            stream.token_timestamps = [current_time]
            for j in range(19):
                # ITL varies: 15, 20, 25, 30, 35, 40, 45, repeating
                itl_ms = 15 + ((j % 7) * 5)
                current_time += itl_ms / 1000.0
                stream.token_timestamps.append(current_time)

            stream.tokens_generated = 20
            tracker.complete_stream(stream_id, "stop")

        metrics = tracker.get_metrics()

        # Verify GPT-4o characteristics
        assert 80 <= metrics.p50_ttft <= 120, f"GPT-4o p50 TTFT should be ~100ms, got {metrics.p50_ttft}ms"
        assert 20 <= metrics.avg_itl <= 40, f"GPT-4o avg ITL should be ~30ms, got {metrics.avg_itl}ms"

    def test_network_delay_simulation(self):
        """Simulate network delays affecting latencies."""
        tracker = StreamingMetricsTracker()

        # Create 5 streams with network delays
        for i in range(5):
            stream_id = f"network-{i}"
            tracker.start_stream(stream_id=stream_id, model="gpt-4", prompt_tokens=50)

            stream = tracker._active_streams[stream_id]
            start_time = 1000.0
            stream.start_time = start_time

            # TTFT includes network delay (200ms base + 100ms network)
            ttft_ms = 300.0
            stream.first_token_time = start_time + (ttft_ms / 1000.0)

            # ITL has occasional spikes due to network issues
            current_time = stream.first_token_time
            stream.token_timestamps = [current_time]
            for j in range(20):
                # Normal ITL: 20ms, but every 5th token has 200ms spike
                if j % 5 == 0:
                    itl_ms = 200.0  # Network spike
                else:
                    itl_ms = 20.0  # Normal
                current_time += itl_ms / 1000.0
                stream.token_timestamps.append(current_time)

            stream.tokens_generated = 21
            tracker.complete_stream(stream_id, "stop")

        metrics = tracker.get_metrics()

        # Should capture network characteristics
        assert abs(metrics.p50_ttft - 300.0) < 0.01, "TTFT should include network delay"
        assert metrics.p95_itl > 100, "p95 ITL should capture network spikes"


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_stream_with_zero_tokens(self):
        """Test stream that completes with zero tokens generated."""
        tracker = StreamingMetricsTracker()

        stream_id = "zero-tokens"
        tracker.start_stream(stream_id=stream_id, model="gpt-4", prompt_tokens=50)
        tracker.complete_stream(stream_id, "stop")

        metrics = tracker.get_metrics()

        # Should not crash, metrics should handle empty data
        assert metrics.total_streams == 1
        assert metrics.completed_streams == 1

    def test_simultaneous_streams(self):
        """Test tracking multiple simultaneous streams."""
        tracker = StreamingMetricsTracker()

        # Start 5 streams
        stream_ids = [f"concurrent-{i}" for i in range(5)]
        for stream_id in stream_ids:
            tracker.start_stream(stream_id=stream_id, model="gpt-4", prompt_tokens=50)

        # All should be active
        assert tracker.get_active_stream_count() == 5

        # Complete them at different times
        for i, stream_id in enumerate(stream_ids):
            stream = tracker._active_streams[stream_id]
            stream.start_time = 1000.0
            stream.first_token_time = 1000.0 + 0.1
            stream.token_timestamps = [stream.first_token_time]
            stream.tokens_generated = 1
            tracker.complete_stream(stream_id, "stop")

        # All should be completed
        assert tracker.get_active_stream_count() == 0
        metrics = tracker.get_metrics()
        assert metrics.completed_streams == 5

    def test_extremely_long_stream(self):
        """Test stream with many tokens (1000+)."""
        tracker = StreamingMetricsTracker()

        stream_id = "long-stream"
        tracker.start_stream(stream_id=stream_id, model="gpt-4", prompt_tokens=50)

        stream = tracker._active_streams[stream_id]
        start_time = 1000.0
        stream.start_time = start_time
        stream.first_token_time = start_time + 0.1  # 100ms TTFT

        # Generate 1000 tokens with 5ms ITL
        current_time = stream.first_token_time
        stream.token_timestamps = [current_time]
        for _ in range(999):
            current_time += 0.005  # 5ms
            stream.token_timestamps.append(current_time)

        stream.tokens_generated = 1000
        tracker.complete_stream(stream_id, "stop")

        # Should have 999 ITL measurements
        itls = stream.get_inter_token_latencies()
        assert len(itls) == 999, f"Expected 999 ITLs, got {len(itls)}"

        metrics = tracker.get_metrics()
        assert abs(metrics.avg_itl - 5.0) < 0.001, f"Average ITL should be ~5.0ms, got {metrics.avg_itl}ms"

    def test_instant_tokens(self):
        """Test tokens arriving at exactly the same time (0ms ITL)."""
        tracker = StreamingMetricsTracker()

        stream_id = "instant"
        tracker.start_stream(stream_id=stream_id, model="gpt-4", prompt_tokens=50)

        stream = tracker._active_streams[stream_id]
        start_time = 1000.0
        stream.start_time = start_time

        # All tokens at exactly the same time
        token_time = start_time + 0.1
        stream.first_token_time = token_time
        stream.token_timestamps = [token_time] * 5

        itls = stream.get_inter_token_latencies()

        # All ITLs should be 0.0ms
        assert all(abs(itl) < 0.001 for itl in itls), "All ITLs should be ~0.0ms for instant tokens"

    def test_backwards_time(self):
        """Test handling of timestamps that go backwards (clock issues)."""
        tracker = StreamingMetricsTracker()

        stream_id = "backwards"
        tracker.start_stream(stream_id=stream_id, model="gpt-4", prompt_tokens=50)

        stream = tracker._active_streams[stream_id]
        start_time = 1000.0
        stream.start_time = start_time

        # Timestamps that go backwards (clock adjustment)
        stream.token_timestamps = [
            1000.1,  # Token 0
            1000.15,  # Token 1 (50ms later)
            1000.12,  # Token 2 (goes back 30ms!)
            1000.17,  # Token 3 (50ms later)
        ]

        itls = stream.get_inter_token_latencies()

        # ITL[1] will be negative (-30ms)
        assert abs(itls[0] - 50.0) < 0.001, "First ITL should be ~50.0ms"
        assert abs(itls[1] - (-30.0)) < 0.001, "Second ITL should be ~-30.0ms (backwards time)"
        assert abs(itls[2] - 50.0) < 0.001, "Third ITL should be ~50.0ms"


class TestMetricsAggregation:
    """Test aggregation of metrics across multiple streams."""

    def test_min_max_ttft(self):
        """Test min and max TTFT tracking."""
        tracker = StreamingMetricsTracker()

        ttft_values = [50.0, 100.0, 25.0, 200.0, 75.0]

        for i, ttft_ms in enumerate(ttft_values):
            stream_id = f"stream-{i}"
            tracker.start_stream(stream_id=stream_id, model="gpt-4", prompt_tokens=50)

            stream = tracker._active_streams[stream_id]
            stream.start_time = 1000.0
            stream.first_token_time = 1000.0 + (ttft_ms / 1000.0)
            stream.token_timestamps.append(stream.first_token_time)
            stream.tokens_generated = 1

            tracker.complete_stream(stream_id, "stop")

        metrics = tracker.get_metrics()

        assert abs(metrics.min_ttft - 25.0) < 0.01, f"Min TTFT should be ~25.0ms, got {metrics.min_ttft}ms"
        assert abs(metrics.max_ttft - 200.0) < 0.01, f"Max TTFT should be ~200.0ms, got {metrics.max_ttft}ms"

    def test_mixed_models_statistics(self):
        """Test statistics across different models."""
        tracker = StreamingMetricsTracker()

        models = ["gpt-4", "gpt-4", "gpt-3.5-turbo", "gpt-3.5-turbo", "claude-3"]

        for i, model in enumerate(models):
            stream_id = f"stream-{i}"
            tracker.start_stream(stream_id=stream_id, model=model, prompt_tokens=50)

            stream = tracker._active_streams[stream_id]
            stream.start_time = 1000.0
            stream.first_token_time = 1000.0 + 0.1
            stream.token_timestamps = [stream.first_token_time]
            stream.tokens_generated = 1

            tracker.complete_stream(stream_id, "stop")

        metrics = tracker.get_metrics()

        # Check per-model tracking
        assert len(metrics.streams_by_model) == 3, "Should track 3 different models"
        assert metrics.streams_by_model.get("gpt-4", 0) == 2
        assert metrics.streams_by_model.get("gpt-3.5-turbo", 0) == 2
        assert metrics.streams_by_model.get("claude-3", 0) == 1

    def test_success_rate_calculation(self):
        """Test success rate with completed and failed streams."""
        tracker = StreamingMetricsTracker()

        # Complete 7 streams successfully
        for i in range(7):
            stream_id = f"success-{i}"
            tracker.start_stream(stream_id=stream_id, model="gpt-4", prompt_tokens=50)
            stream = tracker._active_streams[stream_id]
            stream.start_time = 1000.0
            stream.first_token_time = 1000.0 + 0.1
            stream.token_timestamps.append(stream.first_token_time)
            stream.tokens_generated = 1
            tracker.complete_stream(stream_id, "stop")

        # Fail 3 streams
        for i in range(3):
            stream_id = f"fail-{i}"
            tracker.start_stream(stream_id=stream_id, model="gpt-4", prompt_tokens=50)
            tracker.fail_stream(stream_id, "Error")

        metrics = tracker.get_metrics()

        # Success rate should be 70% (7/10)
        expected_rate = 0.7
        assert abs(metrics.success_rate - expected_rate) < 0.001, f"Success rate should be ~{expected_rate}, got {metrics.success_rate}"


class TestMemoryBounds:
    """Test memory management and bounds."""

    def test_max_completed_streams_limit(self):
        """Test that completed streams are bounded."""
        tracker = StreamingMetricsTracker(max_completed_streams=10)

        # Create 50 streams
        for i in range(50):
            stream_id = f"stream-{i}"
            tracker.start_stream(stream_id=stream_id, model="gpt-4", prompt_tokens=50)
            stream = tracker._active_streams[stream_id]
            stream.start_time = 1000.0
            stream.first_token_time = 1000.0 + 0.1
            stream.token_timestamps.append(stream.first_token_time)
            stream.tokens_generated = 1
            tracker.complete_stream(stream_id, "stop")

        # Should only keep last 10
        assert len(tracker._completed_streams) <= 10, f"Should keep max 10 completed streams"

    def test_cache_invalidation(self):
        """Test that metrics cache is invalidated on updates."""
        tracker = StreamingMetricsTracker()

        # Get initial metrics (cache)
        metrics1 = tracker.get_metrics()
        cache_time1 = tracker._cache_timestamp

        # Add a stream
        stream_id = "new-stream"
        tracker.start_stream(stream_id=stream_id, model="gpt-4", prompt_tokens=50)
        stream = tracker._active_streams[stream_id]
        stream.start_time = 1000.0
        stream.first_token_time = 1000.0 + 0.1
        stream.token_timestamps.append(stream.first_token_time)
        stream.tokens_generated = 1
        tracker.complete_stream(stream_id, "stop")

        # Cache should be invalidated
        assert tracker._cached_metrics is None, "Cache should be invalidated after completion"

        # Get new metrics
        metrics2 = tracker.get_metrics()

        # Should reflect the new stream
        assert metrics2.total_streams > metrics1.total_streams


class TestTokensPerSecond:
    """Test tokens per second calculation."""

    def test_tps_basic_calculation(self):
        """Test basic TPS calculation."""
        tracker = StreamingMetricsTracker()

        stream_id = "tps-test"
        tracker.start_stream(stream_id=stream_id, model="gpt-4", prompt_tokens=50)

        stream = tracker._active_streams[stream_id]
        start_time = 1000.0
        stream.start_time = start_time

        # Generate 20 tokens over 1 second
        stream.first_token_time = start_time + 0.1
        stream.token_timestamps = [stream.first_token_time]
        for i in range(19):
            stream.token_timestamps.append(stream.first_token_time + 1.0)

        stream.tokens_generated = 20
        stream.completion_time = stream.token_timestamps[-1]

        tps = stream.get_tokens_per_second()

        # Duration: (start + 1.1) - start = 1.1s
        # TPS: 20 / 1.1 = ~18.18
        assert 18 <= tps <= 19, f"TPS should be ~18, got {tps}"

    def test_tps_percentiles(self):
        """Test TPS percentile calculations."""
        tracker = StreamingMetricsTracker()

        # Create streams with varying TPS
        for i in range(20):
            stream_id = f"stream-{i}"
            tracker.start_stream(stream_id=stream_id, model="gpt-4", prompt_tokens=50)

            stream = tracker._active_streams[stream_id]
            start_time = 1000.0
            stream.start_time = start_time

            # Tokens per second: 10, 11, 12, ..., 29
            tps_target = 10 + i
            duration = 1.0  # 1 second

            stream.first_token_time = start_time + 0.1
            stream.token_timestamps = [stream.first_token_time]
            stream.tokens_generated = tps_target

            # Spread tokens evenly over 1 second
            for j in range(1, tps_target):
                stream.token_timestamps.append(start_time + 0.1 + (j * duration / tps_target))

            stream.completion_time = stream.token_timestamps[-1]
            tracker.complete_stream(stream_id, "stop")

        metrics = tracker.get_metrics()

        # Should have TPS metrics
        assert metrics.p50_tokens_per_second > 0, "p50 TPS should be > 0"
        assert metrics.p95_tokens_per_second > metrics.p50_tokens_per_second, "p95 TPS should be > p50"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
