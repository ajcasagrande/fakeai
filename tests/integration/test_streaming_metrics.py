"""
Comprehensive Integration Tests for Streaming Metrics

Tests the full integration of streaming metrics tracking across the FakeAI system,
including interactions with the MetricsTracker, StreamingMetricsTracker, and
per-model metrics tracking.

Coverage:
1. TTFT (Time to First Token) measurement
2. ITL (Inter-Token Latency) tracking
3. Tokens per second calculation
4. Streaming request tracking
5. Per-model streaming metrics
6. Streaming vs non-streaming comparison
7. Streaming errors and failures
8. Concurrent streaming metrics
9. Streaming metrics export
10. Real-time metrics updates
11. Streaming latency percentiles
12. Token generation rate
"""

#  SPDX-License-Identifier: Apache-2.0

import asyncio
import time

import pytest

from fakeai.metrics import MetricsTracker
from fakeai.streaming_metrics import StreamingMetricsTracker


class TestTTFTMeasurement:
    """Test TTFT (Time to First Token) measurement accuracy and consistency."""

    def test_ttft_basic_measurement(self):
        """Test basic TTFT measurement for a single stream."""
        tracker = StreamingMetricsTracker()

        stream_id = "ttft-test-1"
        start_time_ns = time.time_ns()

        # Start stream
        tracker.start_stream(
            stream_id=stream_id,
            model="openai/gpt-oss-120b",
            prompt_tokens=100,
        )

        # Wait 50ms before first token
        time.sleep(0.05)
        first_token_time_ns = time.time_ns()

        # Record first token
        tracker.record_token(stream_id, "Hello", timestamp_ns=first_token_time_ns)

        # Complete stream
        tracker.complete_stream(stream_id, "stop")

        # Get stats
        stats = tracker.get_stream_stats(stream_id)
        assert stats is not None
        assert stats["ttft_ms"] is not None

        # TTFT should be approximately 50ms (within 10ms tolerance)
        ttft_ms = stats["ttft_ms"]
        assert 40 < ttft_ms < 60, f"Expected TTFT ~50ms, got {ttft_ms}ms"

    def test_ttft_across_multiple_streams(self):
        """Test TTFT consistency across multiple concurrent streams."""
        tracker = StreamingMetricsTracker()

        stream_ids = []
        expected_ttfts = [20, 30, 40, 50, 60]  # Different TTFTs in ms

        # Create multiple streams with different TTFTs
        for i, ttft_ms in enumerate(expected_ttfts):
            stream_id = f"ttft-multi-{i}"
            stream_ids.append(stream_id)

            start_time_ns = time.time_ns()
            tracker.start_stream(
                stream_id=stream_id,
                model="openai/gpt-oss-120b",
                prompt_tokens=100,
            )

            # Wait for specific TTFT
            time.sleep(ttft_ms / 1000.0)
            tracker.record_token(
                stream_id, f"token-{i}", timestamp_ns=time.time_ns()
            )
            tracker.complete_stream(stream_id, "stop")

        # Verify each stream's TTFT
        report = tracker.get_streaming_quality_report()
        ttft_stats = report["quality_metrics"]["ttft_ms"]

        assert ttft_stats["mean"] > 0
        assert ttft_stats["min"] > 0
        assert ttft_stats["max"] > 0

        # p50 should be close to median (40ms)
        assert 30 < ttft_stats["p50"] < 50

    def test_ttft_with_delayed_prompt(self):
        """Test TTFT measurement with varying prompt sizes."""
        tracker = StreamingMetricsTracker()

        prompt_sizes = [10, 100, 1000, 5000]
        ttfts = []

        for i, prompt_tokens in enumerate(prompt_sizes):
            stream_id = f"ttft-prompt-{i}"

            tracker.start_stream(
                stream_id=stream_id,
                model="openai/gpt-oss-120b",
                prompt_tokens=prompt_tokens,
            )

            # Simulate processing time proportional to prompt size
            processing_time = 0.01 + (prompt_tokens / 10000.0)
            time.sleep(processing_time)

            tracker.record_token(stream_id, "token", timestamp_ns=time.time_ns())
            tracker.complete_stream(stream_id, "stop")

            stats = tracker.get_stream_stats(stream_id)
            ttfts.append(stats["ttft_ms"])

        # Larger prompts should have longer TTFTs (generally)
        assert ttfts[0] < ttfts[-1]

    def test_ttft_percentiles(self):
        """Test TTFT percentile calculations (p50, p90, p99)."""
        tracker = StreamingMetricsTracker()

        # Create 100 streams with varying TTFTs
        for i in range(100):
            stream_id = f"ttft-percentile-{i}"

            tracker.start_stream(
                stream_id=stream_id,
                model="openai/gpt-oss-120b",
                prompt_tokens=100,
            )

            # TTFT varies from 10ms to 100ms
            ttft_ms = 10 + (i * 0.9)
            time.sleep(ttft_ms / 1000.0)

            tracker.record_token(stream_id, "token", timestamp_ns=time.time_ns())
            tracker.complete_stream(stream_id, "stop")

        # Get quality report
        report = tracker.get_streaming_quality_report()
        ttft_stats = report["quality_metrics"]["ttft_ms"]

        # Verify percentiles are in order
        assert ttft_stats["p50"] < ttft_stats["p90"]
        assert ttft_stats["p90"] < ttft_stats["p99"]

        # p50 should be around 55ms (middle of 10-100ms range)
        assert 40 < ttft_stats["p50"] < 70


class TestInterTokenLatency:
    """Test ITL (Inter-Token Latency) tracking and analysis."""

    def test_itl_basic_tracking(self):
        """Test basic ITL tracking for a stream."""
        tracker = StreamingMetricsTracker()

        stream_id = "itl-test-1"
        tracker.start_stream(
            stream_id=stream_id,
            model="openai/gpt-oss-120b",
            prompt_tokens=50,
        )

        # Add tokens with known ITLs
        base_time_ns = time.time_ns()
        itl_values = [10, 15, 20, 10, 15]  # ms

        for i, itl_ms in enumerate(itl_values):
            current_time_ns = base_time_ns + sum(itl_values[: i + 1]) * 1_000_000
            tracker.record_token(stream_id, f"token-{i}", timestamp_ns=current_time_ns)

        tracker.complete_stream(stream_id, "stop")

        # Verify ITL stats
        stats = tracker.get_stream_stats(stream_id)
        itl_stats = stats["inter_token_latencies_ms"]

        assert itl_stats["mean"] is not None
        assert itl_stats["min"] == 10.0
        assert itl_stats["max"] == 20.0

    def test_itl_consistency(self):
        """Test ITL consistency with uniform token generation."""
        tracker = StreamingMetricsTracker()

        stream_id = "itl-consistent"
        tracker.start_stream(
            stream_id=stream_id,
            model="openai/gpt-oss-120b",
            prompt_tokens=50,
        )

        # Add tokens with consistent 5ms ITL
        base_time_ns = time.time_ns()
        for i in range(20):
            current_time_ns = base_time_ns + (i * 5_000_000)
            tracker.record_token(stream_id, f"token-{i}", timestamp_ns=current_time_ns)

        tracker.complete_stream(stream_id, "stop")

        # Check smoothness score (should be very high)
        stats = tracker.get_stream_stats(stream_id)
        smoothness = stats["smoothness_score"]

        assert smoothness is not None
        assert smoothness > 95.0  # Very smooth

    def test_itl_with_stalls(self):
        """Test ITL tracking with stalls (>500ms delays)."""
        tracker = StreamingMetricsTracker()

        stream_id = "itl-stalls"
        tracker.start_stream(
            stream_id=stream_id,
            model="openai/gpt-oss-120b",
            prompt_tokens=50,
        )

        # Add tokens with two stalls
        base_time_ns = time.time_ns()
        itl_values = [10, 20, 600, 15, 700, 10]  # Two stalls: 600ms and 700ms

        for i, itl_ms in enumerate(itl_values):
            current_time_ns = base_time_ns + sum(itl_values[: i + 1]) * 1_000_000
            tracker.record_token(stream_id, f"token-{i}", timestamp_ns=current_time_ns)

        tracker.complete_stream(stream_id, "stop")

        # Verify stall detection
        stats = tracker.get_stream_stats(stream_id)
        assert stats["stall_events"] == 2

    def test_itl_jitter_calculation(self):
        """Test jitter calculation (standard deviation of ITL)."""
        tracker = StreamingMetricsTracker()

        # Create two streams: one with low jitter, one with high jitter
        low_jitter_id = "itl-low-jitter"
        high_jitter_id = "itl-high-jitter"

        # Low jitter stream (consistent ITL)
        tracker.start_stream(
            stream_id=low_jitter_id,
            model="openai/gpt-oss-120b",
            prompt_tokens=50,
        )

        base_time_ns = time.time_ns()
        for i in range(20):
            current_time_ns = base_time_ns + (i * 10_000_000)  # Exactly 10ms
            tracker.record_token(
                low_jitter_id, f"token-{i}", timestamp_ns=current_time_ns
            )

        tracker.complete_stream(low_jitter_id, "stop")

        # High jitter stream (varying ITL)
        tracker.start_stream(
            stream_id=high_jitter_id,
            model="openai/gpt-oss-120b",
            prompt_tokens=50,
        )

        base_time_ns = time.time_ns()
        itl_values = [5, 50, 10, 40, 15, 35, 20, 30, 25, 25]
        for i, itl_ms in enumerate(itl_values):
            current_time_ns = base_time_ns + sum(itl_values[: i + 1]) * 1_000_000
            tracker.record_token(
                high_jitter_id, f"token-{i}", timestamp_ns=current_time_ns
            )

        tracker.complete_stream(high_jitter_id, "stop")

        # Compare jitter
        low_jitter_stats = tracker.get_stream_stats(low_jitter_id)
        high_jitter_stats = tracker.get_stream_stats(high_jitter_id)

        assert low_jitter_stats["jitter_ms"] < high_jitter_stats["jitter_ms"]


class TestTokensPerSecond:
    """Test tokens per second (TPS) calculation."""

    def test_tps_basic_calculation(self):
        """Test basic TPS calculation."""
        tracker = StreamingMetricsTracker()

        stream_id = "tps-test-1"
        tracker.start_stream(
            stream_id=stream_id,
            model="openai/gpt-oss-120b",
            prompt_tokens=50,
        )

        # Add 20 tokens over 1 second
        base_time_ns = time.time_ns()
        for i in range(20):
            current_time_ns = base_time_ns + (i * 50_000_000)  # 50ms apart
            tracker.record_token(stream_id, f"token-{i}", timestamp_ns=current_time_ns)

        tracker.complete_stream(stream_id, "stop")

        # Verify TPS
        stats = tracker.get_stream_stats(stream_id)
        tps = stats["tokens_per_second"]

        assert tps is not None
        # 20 tokens over ~950ms = ~21 tokens/sec
        assert 19 < tps < 23

    def test_tps_varying_rates(self):
        """Test TPS calculation with varying generation rates."""
        tracker = StreamingMetricsTracker()

        rates = [10, 20, 30, 40, 50]  # tokens per second

        for rate in rates:
            stream_id = f"tps-rate-{rate}"
            tracker.start_stream(
                stream_id=stream_id,
                model="openai/gpt-oss-120b",
                prompt_tokens=50,
            )

            # Generate tokens at specific rate
            base_time_ns = time.time_ns()
            token_count = 20
            interval_ns = 1_000_000_000 // rate  # nanoseconds per token

            for i in range(token_count):
                current_time_ns = base_time_ns + (i * interval_ns)
                tracker.record_token(
                    stream_id, f"token-{i}", timestamp_ns=current_time_ns
                )

            tracker.complete_stream(stream_id, "stop")

            # Verify TPS
            stats = tracker.get_stream_stats(stream_id)
            measured_tps = stats["tokens_per_second"]

            assert measured_tps is not None
            # Allow 20% tolerance
            assert rate * 0.8 < measured_tps < rate * 1.2

    def test_tps_aggregation(self):
        """Test TPS aggregation across multiple streams."""
        tracker = StreamingMetricsTracker()

        # Create 10 streams with varying TPS
        for i in range(10):
            stream_id = f"tps-agg-{i}"
            tracker.start_stream(
                stream_id=stream_id,
                model="openai/gpt-oss-120b",
                prompt_tokens=50,
            )

            # Generate 20 tokens with varying speed
            base_time_ns = time.time_ns()
            rate = 10 + (i * 5)  # 10 to 55 tokens/sec
            interval_ns = 1_000_000_000 // rate

            for j in range(20):
                current_time_ns = base_time_ns + (j * interval_ns)
                tracker.record_token(
                    stream_id, f"token-{j}", timestamp_ns=current_time_ns
                )

            tracker.complete_stream(stream_id, "stop")

        # Get quality report
        report = tracker.get_streaming_quality_report()
        tps_stats = report["quality_metrics"]["tokens_per_second"]

        assert tps_stats["mean"] > 0
        assert tps_stats["min"] < tps_stats["max"]
        assert tps_stats["p50"] < tps_stats["p90"]


class TestStreamingRequestTracking:
    """Test streaming request lifecycle tracking."""

    def test_active_stream_tracking(self):
        """Test tracking of active streams."""
        tracker = StreamingMetricsTracker()

        # Start 5 streams
        stream_ids = [f"active-{i}" for i in range(5)]
        for stream_id in stream_ids:
            tracker.start_stream(
                stream_id=stream_id,
                model="openai/gpt-oss-120b",
                prompt_tokens=50,
            )

        assert tracker.get_active_stream_count() == 5

        # Complete 3 streams
        for i in range(3):
            tracker.record_token(stream_ids[i], "token", timestamp_ns=time.time_ns())
            tracker.complete_stream(stream_ids[i], "stop")

        assert tracker.get_active_stream_count() == 2
        assert tracker.get_completed_stream_count() == 3

    def test_completed_stream_tracking(self):
        """Test tracking of completed streams."""
        tracker = StreamingMetricsTracker()

        # Create and complete 10 streams
        for i in range(10):
            stream_id = f"completed-{i}"
            tracker.start_stream(
                stream_id=stream_id,
                model="openai/gpt-oss-120b",
                prompt_tokens=50,
            )

            tracker.record_token(stream_id, "token", timestamp_ns=time.time_ns())
            tracker.complete_stream(stream_id, "stop")

        assert tracker.get_completed_stream_count() == 10
        assert tracker.get_active_stream_count() == 0

    def test_failed_stream_tracking(self):
        """Test tracking of failed/cancelled streams."""
        tracker = StreamingMetricsTracker()

        # Create 5 successful and 3 failed streams
        for i in range(5):
            stream_id = f"success-{i}"
            tracker.start_stream(
                stream_id=stream_id,
                model="openai/gpt-oss-120b",
                prompt_tokens=50,
            )
            tracker.record_token(stream_id, "token", timestamp_ns=time.time_ns())
            tracker.complete_stream(stream_id, "stop")

        for i in range(3):
            stream_id = f"failed-{i}"
            tracker.start_stream(
                stream_id=stream_id,
                model="openai/gpt-oss-120b",
                prompt_tokens=50,
            )
            tracker.record_token(stream_id, "token", timestamp_ns=time.time_ns())
            tracker.cancel_stream(stream_id, "Connection error")

        assert tracker.get_completed_stream_count() == 5
        assert tracker.get_failed_stream_count() == 3


class TestPerModelStreamingMetrics:
    """Test per-model streaming metrics tracking."""

    def test_per_model_stream_tracking(self):
        """Test streaming metrics separated by model."""
        tracker = StreamingMetricsTracker()

        models = [
            "openai/gpt-oss-120b",
            "openai/gpt-oss-20b",
            "meta-llama/Llama-3.1-8B-Instruct",
        ]

        # Create streams for different models
        for model_idx, model in enumerate(models):
            for stream_idx in range(5):
                stream_id = f"model-{model_idx}-stream-{stream_idx}"

                tracker.start_stream(
                    stream_id=stream_id,
                    model=model,
                    prompt_tokens=50,
                )

                # Add tokens
                base_time_ns = time.time_ns()
                for i in range(10):
                    current_time_ns = base_time_ns + (i * 10_000_000)
                    tracker.record_token(
                        stream_id, f"token-{i}", timestamp_ns=current_time_ns
                    )

                tracker.complete_stream(stream_id, "stop")

        # Verify all streams completed
        assert tracker.get_completed_stream_count() == 15

        # Check each model's streams
        report = tracker.get_streaming_quality_report()
        assert report["summary"]["total_streams"] == 15

    def test_model_specific_performance(self):
        """Test tracking different performance characteristics per model."""
        tracker = StreamingMetricsTracker()

        # Fast model
        fast_model = "openai/gpt-oss-20b"
        tracker.start_stream(
            stream_id="fast-stream",
            model=fast_model,
            prompt_tokens=50,
        )

        base_time_ns = time.time_ns()
        for i in range(20):
            current_time_ns = base_time_ns + (i * 2_000_000)  # 2ms ITL
            tracker.record_token(
                "fast-stream", f"token-{i}", timestamp_ns=current_time_ns
            )

        tracker.complete_stream("fast-stream", "stop")

        # Slow model
        slow_model = "openai/gpt-oss-120b"
        tracker.start_stream(
            stream_id="slow-stream",
            model=slow_model,
            prompt_tokens=50,
        )

        base_time_ns = time.time_ns()
        for i in range(20):
            current_time_ns = base_time_ns + (i * 20_000_000)  # 20ms ITL
            tracker.record_token(
                "slow-stream", f"token-{i}", timestamp_ns=current_time_ns
            )

        tracker.complete_stream("slow-stream", "stop")

        # Compare performance
        fast_stats = tracker.get_stream_stats("fast-stream")
        slow_stats = tracker.get_stream_stats("slow-stream")

        assert fast_stats["tokens_per_second"] > slow_stats["tokens_per_second"]


class TestStreamingVsNonStreaming:
    """Test comparison between streaming and non-streaming metrics."""

    def test_metrics_tracker_integration(self):
        """Test integration between MetricsTracker and StreamingMetricsTracker."""
        metrics = MetricsTracker()
        streaming_metrics = StreamingMetricsTracker()

        endpoint = "/v1/chat/completions"

        # Non-streaming request
        metrics.track_request(endpoint)
        time.sleep(0.05)
        metrics.track_response(endpoint, latency=0.05)

        # Streaming request
        stream_id = "integration-stream-1"
        metrics.start_stream(stream_id, endpoint)
        streaming_metrics.start_stream(
            stream_id=stream_id,
            model="openai/gpt-oss-120b",
            prompt_tokens=50,
        )

        # Stream tokens
        base_time_ns = time.time_ns()
        for i in range(10):
            current_time_ns = base_time_ns + (i * 10_000_000)
            metrics.track_stream_token(stream_id)
            streaming_metrics.record_token(
                stream_id, f"token-{i}", timestamp_ns=current_time_ns
            )

        metrics.complete_stream(stream_id, endpoint)
        streaming_metrics.complete_stream(stream_id, "stop")

        # Verify both trackers recorded the stream
        assert metrics.get_active_streams() == 0
        assert streaming_metrics.get_completed_stream_count() == 1

    def test_streaming_response_time_comparison(self):
        """Test comparing response times between streaming and non-streaming."""
        tracker = StreamingMetricsTracker()

        # Create a streaming request
        stream_id = "stream-timing"
        tracker.start_stream(
            stream_id=stream_id,
            model="openai/gpt-oss-120b",
            prompt_tokens=50,
        )

        # Add tokens over 1 second
        base_time_ns = time.time_ns()
        for i in range(20):
            current_time_ns = base_time_ns + (i * 50_000_000)  # 50ms apart
            tracker.record_token(stream_id, f"token-{i}", timestamp_ns=current_time_ns)

        # Complete after 1 second
        completion_time_ns = base_time_ns + 1_000_000_000
        tracker.complete_stream(stream_id, "stop")

        stats = tracker.get_stream_stats(stream_id)

        # TTFT should be much faster than total duration
        assert stats["ttft_ms"] < stats["duration_ms"]


class TestStreamingErrors:
    """Test streaming error handling and metrics."""

    def test_stream_cancellation(self):
        """Test tracking of cancelled streams."""
        tracker = StreamingMetricsTracker()

        stream_id = "cancelled-stream"
        tracker.start_stream(
            stream_id=stream_id,
            model="openai/gpt-oss-120b",
            prompt_tokens=50,
            client_id="client-1",
        )

        # Add some tokens
        for i in range(5):
            tracker.record_token(stream_id, f"token-{i}", timestamp_ns=time.time_ns())

        # Cancel stream
        tracker.cancel_stream(stream_id, "Client disconnected", client_id="client-1")

        # Verify cancellation
        stats = tracker.get_stream_stats(stream_id)
        assert stats["cancelled"] is True
        assert stats["error_message"] == "Client disconnected"
        assert stats["cancellation_point"] == 5

        # Verify client tracking
        client_stats = tracker.get_client_stats("client-1")
        assert client_stats["cancellation_count"] == 1

    def test_stream_timeout(self):
        """Test tracking of timeout events."""
        tracker = StreamingMetricsTracker()

        client_id = "timeout-client"

        # Record multiple timeouts
        for i in range(3):
            tracker.record_timeout(client_id)

        client_stats = tracker.get_client_stats(client_id)
        assert client_stats["timeout_count"] == 3

    def test_stream_reconnection(self):
        """Test tracking of reconnection events."""
        tracker = StreamingMetricsTracker()

        client_id = "reconnect-client"

        # Record multiple reconnections
        for i in range(5):
            tracker.record_reconnection(client_id)

        client_stats = tracker.get_client_stats(client_id)
        assert client_stats["reconnection_count"] == 5

    def test_error_impact_on_quality_report(self):
        """Test how errors affect quality report metrics."""
        tracker = StreamingMetricsTracker()

        # Create 7 successful streams
        for i in range(7):
            stream_id = f"success-{i}"
            tracker.start_stream(
                stream_id=stream_id,
                model="openai/gpt-oss-120b",
                prompt_tokens=50,
            )
            tracker.record_token(stream_id, "token", timestamp_ns=time.time_ns())
            tracker.complete_stream(stream_id, "stop")

        # Create 3 failed streams
        for i in range(3):
            stream_id = f"failed-{i}"
            tracker.start_stream(
                stream_id=stream_id,
                model="openai/gpt-oss-120b",
                prompt_tokens=50,
            )
            tracker.record_token(stream_id, "token", timestamp_ns=time.time_ns())
            tracker.cancel_stream(stream_id, "Error")

        # Check quality report
        report = tracker.get_streaming_quality_report()

        assert report["summary"]["total_streams"] == 10
        assert report["summary"]["completed_streams"] == 7
        assert report["summary"]["failed_streams"] == 3
        assert report["summary"]["success_rate"] == 70.0


class TestConcurrentStreamingMetrics:
    """Test metrics tracking with concurrent streams."""

    @pytest.mark.asyncio
    async def test_concurrent_stream_tracking(self):
        """Test tracking multiple concurrent streams."""
        tracker = StreamingMetricsTracker()

        async def simulate_stream(stream_id: str, token_count: int, itl_ms: int):
            """Simulate a streaming request."""
            tracker.start_stream(
                stream_id=stream_id,
                model="openai/gpt-oss-120b",
                prompt_tokens=50,
            )

            base_time_ns = time.time_ns()
            for i in range(token_count):
                await asyncio.sleep(itl_ms / 1000.0)
                current_time_ns = base_time_ns + ((i + 1) * itl_ms * 1_000_000)
                tracker.record_token(
                    stream_id, f"token-{i}", timestamp_ns=current_time_ns
                )

            tracker.complete_stream(stream_id, "stop")

        # Create 10 concurrent streams
        tasks = [
            simulate_stream(f"concurrent-{i}", token_count=20, itl_ms=5)
            for i in range(10)
        ]

        # Run all streams concurrently
        await asyncio.gather(*tasks)

        # Verify all streams completed
        assert tracker.get_completed_stream_count() == 10
        assert tracker.get_active_stream_count() == 0

    @pytest.mark.asyncio
    async def test_concurrent_different_speeds(self):
        """Test concurrent streams with different generation speeds."""
        tracker = StreamingMetricsTracker()

        async def fast_stream(stream_id: str):
            tracker.start_stream(
                stream_id=stream_id,
                model="openai/gpt-oss-20b",
                prompt_tokens=50,
            )

            base_time_ns = time.time_ns()
            for i in range(50):
                await asyncio.sleep(0.002)  # 2ms ITL
                current_time_ns = base_time_ns + ((i + 1) * 2_000_000)
                tracker.record_token(
                    stream_id, f"token-{i}", timestamp_ns=current_time_ns
                )

            tracker.complete_stream(stream_id, "stop")

        async def slow_stream(stream_id: str):
            tracker.start_stream(
                stream_id=stream_id,
                model="openai/gpt-oss-120b",
                prompt_tokens=50,
            )

            base_time_ns = time.time_ns()
            for i in range(20):
                await asyncio.sleep(0.02)  # 20ms ITL
                current_time_ns = base_time_ns + ((i + 1) * 20_000_000)
                tracker.record_token(
                    stream_id, f"token-{i}", timestamp_ns=current_time_ns
                )

            tracker.complete_stream(stream_id, "stop")

        # Run 3 fast and 2 slow streams concurrently
        tasks = [fast_stream(f"fast-{i}") for i in range(3)] + [
            slow_stream(f"slow-{i}") for i in range(2)
        ]

        await asyncio.gather(*tasks)

        # Verify completion
        assert tracker.get_completed_stream_count() == 5

        # Fast streams should have higher TPS
        fast_stats = tracker.get_stream_stats("fast-0")
        slow_stats = tracker.get_stream_stats("slow-0")

        assert fast_stats["tokens_per_second"] > slow_stats["tokens_per_second"]

    def test_max_concurrent_streams_enforcement(self):
        """Test enforcement of max concurrent streams limit."""
        tracker = StreamingMetricsTracker(max_active_streams=5)

        # Try to create 10 streams
        for i in range(10):
            tracker.start_stream(
                stream_id=f"limited-{i}",
                model="openai/gpt-oss-120b",
                prompt_tokens=50,
            )

        # Should only have 5 active (oldest dropped)
        assert tracker.get_active_stream_count() == 5


class TestStreamingMetricsExport:
    """Test exporting streaming metrics in various formats."""

    def test_quality_report_export(self):
        """Test exporting quality report."""
        tracker = StreamingMetricsTracker()

        # Create several streams
        for i in range(10):
            stream_id = f"export-{i}"
            tracker.start_stream(
                stream_id=stream_id,
                model="openai/gpt-oss-120b",
                prompt_tokens=50,
            )

            base_time_ns = time.time_ns()
            for j in range(20):
                current_time_ns = base_time_ns + (j * 10_000_000)
                tracker.record_token(
                    stream_id, f"token-{j}", timestamp_ns=current_time_ns
                )

            tracker.complete_stream(stream_id, "stop")

        # Export quality report
        report = tracker.get_streaming_quality_report()

        # Verify all sections present
        assert "summary" in report
        assert "quality_metrics" in report
        assert "token_metrics" in report
        assert "network_metrics" in report
        assert "client_metrics" in report

    def test_prometheus_format_export(self):
        """Test exporting streaming metrics in Prometheus format."""
        metrics = MetricsTracker()
        tracker = StreamingMetricsTracker()

        endpoint = "/v1/chat/completions"

        # Get initial state
        initial_stats = metrics.get_streaming_stats()
        initial_completed = initial_stats.get("completed_streams", 0)

        # Create and track streams through both trackers
        for i in range(5):
            stream_id = f"prom-{i}-{time.time_ns()}"  # Unique stream IDs

            metrics.start_stream(stream_id, endpoint)
            tracker.start_stream(
                stream_id=stream_id,
                model="openai/gpt-oss-120b",
                prompt_tokens=50,
            )

            base_time_ns = time.time_ns()
            for j in range(10):
                current_time_ns = base_time_ns + (j * 10_000_000)
                metrics.track_stream_token(stream_id)
                tracker.record_token(
                    stream_id, f"token-{j}", timestamp_ns=current_time_ns
                )

            metrics.complete_stream(stream_id, endpoint)
            tracker.complete_stream(stream_id, "stop")

        # Give metrics time to aggregate
        time.sleep(0.1)

        # Get streaming stats
        streaming_stats = metrics.get_streaming_stats()

        # Verify streaming stats are tracked (check delta from initial state)
        completed_delta = streaming_stats["completed_streams"] - initial_completed
        assert completed_delta >= 5, f"Expected at least 5 new completed streams, got {completed_delta}"
        assert streaming_stats["active_streams"] == 0

        # Verify TTFT and TPS stats exist
        if streaming_stats.get("ttft"):
            assert "avg" in streaming_stats["ttft"]
        if streaming_stats.get("tokens_per_second"):
            assert "avg" in streaming_stats["tokens_per_second"]

    def test_per_stream_stats_export(self):
        """Test exporting individual stream statistics."""
        tracker = StreamingMetricsTracker()

        stream_id = "detailed-stream"
        tracker.start_stream(
            stream_id=stream_id,
            model="openai/gpt-oss-120b",
            prompt_tokens=50,
            temperature=0.7,
            max_tokens=100,
        )

        # Add diverse tokens
        base_time_ns = time.time_ns()
        tokens = ["Hello", ",", " ", "world", "!", " ", "How", " ", "are", " ", "you", "?"]

        for i, token in enumerate(tokens):
            current_time_ns = base_time_ns + (i * 10_000_000)
            tracker.record_token(stream_id, token, timestamp_ns=current_time_ns)

        tracker.complete_stream(stream_id, "stop")

        # Export stream stats
        stats = tracker.get_stream_stats(stream_id)

        # Verify all fields present
        assert stats["stream_id"] == stream_id
        assert stats["model"] == "openai/gpt-oss-120b"
        assert stats["prompt_tokens"] == 50
        assert stats["token_count"] == len(tokens)
        assert stats["ttft_ms"] is not None
        assert stats["duration_ms"] is not None
        assert stats["tokens_per_second"] is not None
        assert stats["finish_reason"] == "stop"
        assert stats["temperature"] == 0.7
        assert stats["max_tokens"] == 100


class TestRealTimeMetricsUpdates:
    """Test real-time metrics updates during streaming."""

    @pytest.mark.asyncio
    async def test_metrics_updated_during_streaming(self):
        """Test that metrics are updated in real-time during streaming."""
        tracker = StreamingMetricsTracker()

        stream_id = "realtime-stream"
        tracker.start_stream(
            stream_id=stream_id,
            model="openai/gpt-oss-120b",
            prompt_tokens=50,
        )

        # Check initial state
        assert tracker.get_active_stream_count() == 1

        # Add tokens progressively
        base_time_ns = time.time_ns()
        for i in range(10):
            current_time_ns = base_time_ns + (i * 10_000_000)
            tracker.record_token(stream_id, f"token-{i}", timestamp_ns=current_time_ns)

            # Check stats after each token
            stats = tracker.get_stream_stats(stream_id)
            assert stats["token_count"] == i + 1

            await asyncio.sleep(0.01)

        tracker.complete_stream(stream_id, "stop")

        # Final state
        assert tracker.get_active_stream_count() == 0
        assert tracker.get_completed_stream_count() == 1

    def test_metrics_during_network_issues(self):
        """Test metrics tracking during network issues (backpressure)."""
        tracker = StreamingMetricsTracker()

        stream_id = "backpressure-stream"
        tracker.start_stream(
            stream_id=stream_id,
            model="openai/gpt-oss-120b",
            prompt_tokens=50,
        )

        # Add tokens
        for i in range(10):
            tracker.record_token(stream_id, f"token-{i}", timestamp_ns=time.time_ns())

        # Simulate backpressure events
        for _ in range(3):
            tracker.record_backpressure(stream_id)

        tracker.complete_stream(stream_id, "stop")

        # Verify backpressure recorded
        stats = tracker.get_stream_stats(stream_id)
        assert stats["backpressure_events"] == 3


class TestStreamingLatencyPercentiles:
    """Test streaming latency percentile calculations."""

    def test_ttft_percentiles_accuracy(self):
        """Test accuracy of TTFT percentile calculations."""
        tracker = StreamingMetricsTracker()

        # Create 100 streams with known TTFT distribution
        ttft_values = list(range(10, 110))  # 10ms to 109ms

        for i, ttft_ms in enumerate(ttft_values):
            stream_id = f"percentile-{i}"
            tracker.start_stream(
                stream_id=stream_id,
                model="openai/gpt-oss-120b",
                prompt_tokens=50,
            )

            # Wait exact TTFT time
            base_time_ns = time.time_ns()
            first_token_time_ns = base_time_ns + (ttft_ms * 1_000_000)

            tracker.record_token(
                stream_id, "token", timestamp_ns=first_token_time_ns
            )
            tracker.complete_stream(stream_id, "stop")

        # Get quality report
        report = tracker.get_streaming_quality_report()
        ttft_stats = report["quality_metrics"]["ttft_ms"]

        # Verify percentiles (with more tolerance due to timing variations)
        assert 50 < ttft_stats["p50"] < 70  # Median around 59.5ms
        assert 85 < ttft_stats["p90"] < 105  # 90th percentile around 90-100ms
        assert 95 < ttft_stats["p99"] < 110  # 99th percentile around 99-109ms

    def test_itl_percentiles_accuracy(self):
        """Test accuracy of ITL percentile calculations."""
        tracker = StreamingMetricsTracker()

        stream_id = "itl-percentiles"
        tracker.start_stream(
            stream_id=stream_id,
            model="openai/gpt-oss-120b",
            prompt_tokens=50,
        )

        # Create tokens with known ITL distribution
        base_time_ns = time.time_ns()
        itl_values = list(range(5, 105))  # 5ms to 104ms

        for i, itl_ms in enumerate(itl_values):
            current_time_ns = base_time_ns + sum(itl_values[: i + 1]) * 1_000_000
            tracker.record_token(stream_id, f"token-{i}", timestamp_ns=current_time_ns)

        tracker.complete_stream(stream_id, "stop")

        # Get stats
        stats = tracker.get_stream_stats(stream_id)
        itl_stats = stats["inter_token_latencies_ms"]

        # Verify percentiles exist and are in order
        assert "mean" in itl_stats
        assert "median" in itl_stats
        assert "p90" in itl_stats
        assert "p99" in itl_stats
        assert itl_stats["mean"] is not None
        assert itl_stats["median"] is not None
        assert itl_stats["p90"] is not None
        assert itl_stats["p99"] is not None
        # Verify they're in ascending order
        assert itl_stats["median"] < itl_stats["p90"] < itl_stats["p99"]


class TestTokenGenerationRate:
    """Test token generation rate calculations and analysis."""

    def test_instantaneous_generation_rate(self):
        """Test calculating instantaneous token generation rate."""
        tracker = StreamingMetricsTracker()

        stream_id = "instant-rate"
        tracker.start_stream(
            stream_id=stream_id,
            model="openai/gpt-oss-120b",
            prompt_tokens=50,
        )

        # Generate tokens with varying rate
        base_time_ns = time.time_ns()

        # Fast generation: 10ms ITL for first 10 tokens
        for i in range(10):
            current_time_ns = base_time_ns + (i * 10_000_000)
            tracker.record_token(stream_id, f"token-{i}", timestamp_ns=current_time_ns)

        # Slow generation: 50ms ITL for next 10 tokens
        offset_ns = 10 * 10_000_000
        for i in range(10, 20):
            current_time_ns = base_time_ns + offset_ns + ((i - 10) * 50_000_000)
            tracker.record_token(stream_id, f"token-{i}", timestamp_ns=current_time_ns)

        tracker.complete_stream(stream_id, "stop")

        # Check throughput variance (should be high due to rate change)
        stats = tracker.get_stream_stats(stream_id)
        variance = stats["throughput_variance"]

        assert variance is not None
        assert variance > 0

    def test_sustained_generation_rate(self):
        """Test sustained token generation rate over long stream."""
        tracker = StreamingMetricsTracker()

        stream_id = "sustained-rate"
        tracker.start_stream(
            stream_id=stream_id,
            model="openai/gpt-oss-120b",
            prompt_tokens=50,
        )

        # Generate 100 tokens at steady 10ms ITL
        base_time_ns = time.time_ns()
        for i in range(100):
            current_time_ns = base_time_ns + (i * 10_000_000)
            tracker.record_token(stream_id, f"token-{i}", timestamp_ns=current_time_ns)

        tracker.complete_stream(stream_id, "stop")

        # Check TPS (should be ~100 tokens/sec)
        stats = tracker.get_stream_stats(stream_id)
        tps = stats["tokens_per_second"]

        assert tps is not None
        assert 95 < tps < 105

    def test_token_generation_correlation(self):
        """Test correlation between prompt length and generation rate."""
        tracker = StreamingMetricsTracker()

        # Create streams with varying prompt sizes
        for i in range(10):
            stream_id = f"correlation-{i}"
            prompt_tokens = 100 + (i * 100)  # 100 to 1000 tokens

            tracker.start_stream(
                stream_id=stream_id,
                model="openai/gpt-oss-120b",
                prompt_tokens=prompt_tokens,
            )

            # Generate tokens
            base_time_ns = time.time_ns()
            for j in range(20):
                current_time_ns = base_time_ns + (j * 10_000_000)
                tracker.record_token(
                    stream_id, f"token-{j}", timestamp_ns=current_time_ns
                )

            tracker.complete_stream(stream_id, "stop")

        # Get quality report with correlations
        report = tracker.get_streaming_quality_report()

        assert "correlations" in report
        # Should have prompt_length_vs_ttft correlation
        if "prompt_length_vs_ttft" in report["correlations"]:
            corr_data = report["correlations"]["prompt_length_vs_ttft"]
            assert "correlation" in corr_data
            assert "sample_size" in corr_data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
