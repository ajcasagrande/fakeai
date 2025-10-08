"""
Tests for Enhanced Streaming Metrics Module

Comprehensive tests for streaming_metrics.py covering all functionality:
- Per-stream tracking
- Quality metrics
- Token-level metrics
- Client behavior
- Advanced analytics
"""

#  SPDX-License-Identifier: Apache-2.0



from fakeai.streaming_metrics import (
    ClientBehavior,
    StreamingMetricsTracker,
    StreamLifecycle,
    TokenTiming,
)


class TestTokenTiming:
    """Test TokenTiming dataclass."""

    def test_token_timing_creation(self):
        """Test creating a TokenTiming instance."""
        timing = TokenTiming(
            token="hello",
            timestamp_ns=1000000000,
            chunk_size_bytes=5,
            sequence_number=0,
        )

        assert timing.token == "hello"
        assert timing.timestamp_ns == 1000000000
        assert timing.chunk_size_bytes == 5
        assert timing.sequence_number == 0


class TestStreamLifecycle:
    """Test StreamLifecycle dataclass and methods."""

    def test_stream_lifecycle_creation(self):
        """Test creating a StreamLifecycle instance."""
        stream = StreamLifecycle(
            stream_id="test-123",
            model="gpt-4",
            prompt_tokens=50,
            start_time_ns=1000000000,
        )

        assert stream.stream_id == "test-123"
        assert stream.model == "gpt-4"
        assert stream.prompt_tokens == 50
        assert stream.start_time_ns == 1000000000
        assert len(stream.tokens) == 0
        assert stream.first_token_time_ns is None

    def test_get_ttft_ms(self):
        """Test time to first token calculation."""
        stream = StreamLifecycle(
            stream_id="test-123",
            model="gpt-4",
            prompt_tokens=50,
            start_time_ns=1000000000,
        )

        # No first token yet
        assert stream.get_ttft_ms() is None

        # Set first token time (100ms after start)
        stream.first_token_time_ns = 1100000000
        ttft = stream.get_ttft_ms()
        assert ttft == 100.0

    def test_get_total_duration_ms(self):
        """Test total duration calculation."""
        stream = StreamLifecycle(
            stream_id="test-123",
            model="gpt-4",
            prompt_tokens=50,
            start_time_ns=1000000000,
        )

        # Not completed yet
        assert stream.get_total_duration_ms() is None

        # Set completion time (500ms after start)
        stream.completion_time_ns = 1500000000
        duration = stream.get_total_duration_ms()
        assert duration == 500.0

    def test_get_tokens_per_second(self):
        """Test tokens per second calculation."""
        stream = StreamLifecycle(
            stream_id="test-123",
            model="gpt-4",
            prompt_tokens=50,
            start_time_ns=1000000000,
        )

        # Add tokens over 1 second
        stream.first_token_time_ns = 1100000000  # 100ms after start
        for i in range(20):
            stream.tokens.append(
                TokenTiming(
                    token=f"token{i}",
                    timestamp_ns=1100000000 + (i * 50000000),  # 50ms apart
                    chunk_size_bytes=10,
                    sequence_number=i,
                )
            )
        stream.last_token_time_ns = stream.tokens[-1].timestamp_ns

        tps = stream.get_tokens_per_second()
        assert tps is not None
        # 20 tokens over ~950ms = ~21 tokens/sec
        assert 19 < tps < 23

    def test_get_inter_token_latencies_ms(self):
        """Test inter-token latency calculation."""
        stream = StreamLifecycle(
            stream_id="test-123",
            model="gpt-4",
            prompt_tokens=50,
            start_time_ns=1000000000,
        )

        # Add tokens with known ITLs
        stream.tokens.append(
            TokenTiming(
                token="token0",
                timestamp_ns=1000000000,
                chunk_size_bytes=10,
                sequence_number=0,
            )
        )
        stream.tokens.append(
            TokenTiming(
                token="token1",
                timestamp_ns=1050000000,  # 50ms later
                chunk_size_bytes=10,
                sequence_number=1,
            )
        )
        stream.tokens.append(
            TokenTiming(
                token="token2",
                timestamp_ns=1150000000,  # 100ms later
                chunk_size_bytes=10,
                sequence_number=2,
            )
        )

        itls = stream.get_inter_token_latencies_ms()
        assert len(itls) == 2
        assert itls[0] == 50.0
        assert itls[1] == 100.0

    def test_calculate_jitter_ms(self):
        """Test jitter calculation."""
        stream = StreamLifecycle(
            stream_id="test-123",
            model="gpt-4",
            prompt_tokens=50,
            start_time_ns=1000000000,
        )

        # Add tokens with consistent ITL (low jitter)
        for i in range(10):
            stream.tokens.append(
                TokenTiming(
                    token=f"token{i}",
                    timestamp_ns=1000000000 + (i * 50000000),  # Exactly 50ms apart
                    chunk_size_bytes=10,
                    sequence_number=i,
                )
            )

        jitter = stream.calculate_jitter_ms()
        assert jitter is not None
        assert jitter < 1.0  # Very low jitter

    def test_calculate_smoothness_score(self):
        """Test smoothness score calculation."""
        stream = StreamLifecycle(
            stream_id="test-123",
            model="gpt-4",
            prompt_tokens=50,
            start_time_ns=1000000000,
        )

        # Add tokens with consistent ITL (high smoothness)
        for i in range(10):
            stream.tokens.append(
                TokenTiming(
                    token=f"token{i}",
                    timestamp_ns=1000000000 + (i * 50000000),  # Exactly 50ms apart
                    chunk_size_bytes=10,
                    sequence_number=i,
                )
            )

        smoothness = stream.calculate_smoothness_score()
        assert smoothness is not None
        assert smoothness > 95.0  # Very smooth

    def test_count_stalls(self):
        """Test stall counting."""
        stream = StreamLifecycle(
            stream_id="test-123",
            model="gpt-4",
            prompt_tokens=50,
            start_time_ns=1000000000,
        )

        # Add tokens with one stall
        stream.tokens.append(
            TokenTiming(
                token="token0",
                timestamp_ns=1000000000,
                chunk_size_bytes=10,
                sequence_number=0,
            )
        )
        stream.tokens.append(
            TokenTiming(
                token="token1",
                timestamp_ns=1050000000,  # 50ms (no stall)
                chunk_size_bytes=10,
                sequence_number=1,
            )
        )
        stream.tokens.append(
            TokenTiming(
                token="token2",
                timestamp_ns=1650000000,  # 600ms (stall!)
                chunk_size_bytes=10,
                sequence_number=2,
            )
        )

        stalls = stream.count_stalls()
        assert stalls == 1

    def test_calculate_throughput_variance(self):
        """Test throughput variance calculation."""
        stream = StreamLifecycle(
            stream_id="test-123",
            model="gpt-4",
            prompt_tokens=50,
            start_time_ns=1000000000,
        )

        # Add tokens with varying throughput
        # First 5 tokens: 50ms apart (20 tokens/sec)
        # Next 5 tokens: 100ms apart (10 tokens/sec)
        for i in range(5):
            stream.tokens.append(
                TokenTiming(
                    token=f"token{i}",
                    timestamp_ns=1000000000 + (i * 50000000),
                    chunk_size_bytes=10,
                    sequence_number=i,
                )
            )

        for i in range(5, 10):
            stream.tokens.append(
                TokenTiming(
                    token=f"token{i}",
                    timestamp_ns=1000000000 + (5 * 50000000) + ((i - 5) * 100000000),
                    chunk_size_bytes=10,
                    sequence_number=i,
                )
            )

        variance = stream.calculate_throughput_variance()
        assert variance is not None
        assert variance > 0  # Should have variance

    def test_get_token_size_distribution(self):
        """Test token size distribution calculation."""
        stream = StreamLifecycle(
            stream_id="test-123",
            model="gpt-4",
            prompt_tokens=50,
            start_time_ns=1000000000,
        )

        # Add tokens with varying sizes
        stream.tokens.append(
            TokenTiming(
                token="hi",  # 2 chars
                timestamp_ns=1000000000,
                chunk_size_bytes=2,
                sequence_number=0,
            )
        )
        stream.tokens.append(
            TokenTiming(
                token="hello",  # 5 chars
                timestamp_ns=1100000000,
                chunk_size_bytes=5,
                sequence_number=1,
            )
        )
        stream.tokens.append(
            TokenTiming(
                token="world",  # 5 chars
                timestamp_ns=1200000000,
                chunk_size_bytes=5,
                sequence_number=2,
            )
        )

        dist = stream.get_token_size_distribution()
        assert dist["min"] == 2
        assert dist["max"] == 5
        assert dist["mean"] == 4.0

    def test_get_punctuation_ratio(self):
        """Test punctuation ratio calculation."""
        stream = StreamLifecycle(
            stream_id="test-123",
            model="gpt-4",
            prompt_tokens=50,
            start_time_ns=1000000000,
        )

        # Add 7 word tokens and 3 punctuation tokens
        for word in ["hello", "world", "this", "is", "a", "test", "sentence"]:
            stream.tokens.append(
                TokenTiming(
                    token=word,
                    timestamp_ns=1000000000,
                    chunk_size_bytes=len(word),
                    sequence_number=len(stream.tokens),
                )
            )

        for punct in [".", ",", "!"]:
            stream.tokens.append(
                TokenTiming(
                    token=punct,
                    timestamp_ns=1000000000,
                    chunk_size_bytes=1,
                    sequence_number=len(stream.tokens),
                )
            )

        ratio = stream.get_punctuation_ratio()
        assert 0.25 < ratio < 0.35  # 3/10 = 0.3

    def test_calculate_network_overhead_percent(self):
        """Test network overhead calculation."""
        stream = StreamLifecycle(
            stream_id="test-123",
            model="gpt-4",
            prompt_tokens=50,
            start_time_ns=1000000000,
        )

        # Add tokens with known sizes
        stream.tokens.append(
            TokenTiming(
                token="hello",  # 5 bytes
                timestamp_ns=1000000000,
                chunk_size_bytes=5,
                sequence_number=0,
            )
        )
        stream.tokens.append(
            TokenTiming(
                token="world",  # 5 bytes
                timestamp_ns=1100000000,
                chunk_size_bytes=5,
                sequence_number=1,
            )
        )

        # Total content: 10 bytes, sent: 20 bytes (100% overhead)
        stream.total_bytes_sent = 20

        overhead = stream.calculate_network_overhead_percent()
        assert overhead == 50.0  # 10 bytes overhead / 20 total = 50%


class TestClientBehavior:
    """Test ClientBehavior dataclass."""

    def test_client_behavior_creation(self):
        """Test creating a ClientBehavior instance."""
        client = ClientBehavior(client_id="client-123")

        assert client.client_id == "client-123"
        assert len(client.streams) == 0
        assert client.total_tokens_read == 0

    def test_get_average_read_rate_tps(self):
        """Test average read rate calculation."""
        client = ClientBehavior(client_id="client-123")

        # No data yet
        assert client.get_average_read_rate_tps() == 0.0

        # Add some data: 100 tokens in 10 seconds
        client.total_tokens_read = 100
        client.total_duration_ms = 10000.0

        rate = client.get_average_read_rate_tps()
        assert rate == 10.0

    def test_is_slow_client(self):
        """Test slow client detection."""
        client = ClientBehavior(client_id="client-123")

        # Fast client: 20 tokens/sec
        client.total_tokens_read = 200
        client.total_duration_ms = 10000.0
        assert not client.is_slow_client()

        # Slow client: 5 tokens/sec
        client.total_tokens_read = 50
        client.total_duration_ms = 10000.0
        assert client.is_slow_client()


class TestStreamingMetricsTracker:
    """Test StreamingMetricsTracker main class."""

    def test_tracker_initialization(self):
        """Test tracker initialization."""
        tracker = StreamingMetricsTracker()

        assert tracker.get_active_stream_count() == 0
        assert tracker.get_completed_stream_count() == 0
        assert tracker.get_failed_stream_count() == 0

    def test_start_stream(self):
        """Test starting a new stream."""
        tracker = StreamingMetricsTracker()

        tracker.start_stream(
            stream_id="test-123",
            model="gpt-4",
            prompt_tokens=50,
            temperature=0.7,
            max_tokens=100,
            client_id="client-1",
        )

        assert tracker.get_active_stream_count() == 1
        stats = tracker.get_stream_stats("test-123")
        assert stats is not None
        assert stats["stream_id"] == "test-123"
        assert stats["model"] == "gpt-4"
        assert stats["prompt_tokens"] == 50
        assert stats["status"] == "active"

    def test_record_token(self):
        """Test recording tokens."""
        tracker = StreamingMetricsTracker()

        tracker.start_stream(
            stream_id="test-123",
            model="gpt-4",
            prompt_tokens=50,
        )

        # Record tokens
        tracker.record_token("test-123", "hello", timestamp_ns=1000000000)
        tracker.record_token("test-123", "world", timestamp_ns=1050000000)

        stats = tracker.get_stream_stats("test-123")
        assert stats["token_count"] == 2
        assert stats["ttft_ms"] is not None

    def test_record_chunk_sent(self):
        """Test recording network chunks."""
        tracker = StreamingMetricsTracker()

        tracker.start_stream(
            stream_id="test-123",
            model="gpt-4",
            prompt_tokens=50,
        )

        tracker.record_chunk_sent("test-123", 100)
        tracker.record_chunk_sent("test-123", 150)

        stats = tracker.get_stream_stats("test-123")
        assert stats["chunks_sent"] == 2
        assert stats["total_bytes_sent"] == 250

    def test_record_backpressure(self):
        """Test recording backpressure events."""
        tracker = StreamingMetricsTracker()

        tracker.start_stream(
            stream_id="test-123",
            model="gpt-4",
            prompt_tokens=50,
        )

        tracker.record_backpressure("test-123")
        tracker.record_backpressure("test-123")

        stats = tracker.get_stream_stats("test-123")
        assert stats["backpressure_events"] == 2

    def test_complete_stream(self):
        """Test completing a stream."""
        tracker = StreamingMetricsTracker()

        tracker.start_stream(
            stream_id="test-123",
            model="gpt-4",
            prompt_tokens=50,
            client_id="client-1",
        )

        tracker.record_token("test-123", "hello", timestamp_ns=1000000000)
        tracker.record_token("test-123", "world", timestamp_ns=1050000000)

        tracker.complete_stream("test-123", "stop", client_id="client-1")

        # Should be in completed streams
        assert tracker.get_active_stream_count() == 0
        assert tracker.get_completed_stream_count() == 1

        stats = tracker.get_stream_stats("test-123")
        assert stats["status"] == "completed"
        assert stats["finish_reason"] == "stop"

    def test_cancel_stream(self):
        """Test cancelling a stream."""
        tracker = StreamingMetricsTracker()

        tracker.start_stream(
            stream_id="test-123",
            model="gpt-4",
            prompt_tokens=50,
            client_id="client-1",
        )

        tracker.record_token("test-123", "hello", timestamp_ns=1000000000)

        tracker.cancel_stream("test-123", "Client disconnected", client_id="client-1")

        # Should be in failed streams
        assert tracker.get_active_stream_count() == 0
        assert tracker.get_failed_stream_count() == 1

        stats = tracker.get_stream_stats("test-123")
        assert stats["status"] == "failed"
        assert stats["cancelled"] is True
        assert stats["error_message"] == "Client disconnected"

    def test_client_tracking(self):
        """Test client behavior tracking."""
        tracker = StreamingMetricsTracker()

        # Create and complete a stream
        tracker.start_stream(
            stream_id="test-123",
            model="gpt-4",
            prompt_tokens=50,
            client_id="client-1",
        )

        for i in range(20):
            tracker.record_token(
                "test-123", f"token{i}", timestamp_ns=1000000000 + (i * 50000000)
            )

        tracker.complete_stream("test-123", "stop", client_id="client-1")

        # Check client stats
        client_stats = tracker.get_client_stats("client-1")
        assert client_stats is not None
        assert client_stats["total_streams"] == 1
        assert client_stats["total_tokens_read"] == 20

    def test_record_timeout(self):
        """Test recording timeouts."""
        tracker = StreamingMetricsTracker()

        tracker.record_timeout("client-1")
        tracker.record_timeout("client-1")

        client_stats = tracker.get_client_stats("client-1")
        assert client_stats["timeout_count"] == 2

    def test_record_reconnection(self):
        """Test recording reconnections."""
        tracker = StreamingMetricsTracker()

        tracker.record_reconnection("client-1")
        tracker.record_reconnection("client-1")

        client_stats = tracker.get_client_stats("client-1")
        assert client_stats["reconnection_count"] == 2

    def test_get_streaming_quality_report(self):
        """Test generating quality report."""
        tracker = StreamingMetricsTracker()

        # Create multiple completed streams
        for stream_num in range(5):
            stream_id = f"test-{stream_num}"

            tracker.start_stream(
                stream_id=stream_id,
                model="gpt-4",
                prompt_tokens=50,
                temperature=0.7,
                max_tokens=100,
            )

            # Add tokens
            for i in range(20):
                tracker.record_token(
                    stream_id, f"token{i}", timestamp_ns=1000000000 + (i * 50000000)
                )

            tracker.complete_stream(stream_id, "stop")

        # Get quality report
        report = tracker.get_streaming_quality_report()

        assert report["summary"]["total_streams"] == 5
        assert report["summary"]["completed_streams"] == 5
        assert report["summary"]["success_rate"] == 100.0

        # Check quality metrics exist
        assert "quality_metrics" in report
        assert "ttft_ms" in report["quality_metrics"]
        assert "tokens_per_second" in report["quality_metrics"]
        assert "jitter_ms" in report["quality_metrics"]
        assert "smoothness_score" in report["quality_metrics"]

        # Check token metrics
        assert "token_metrics" in report
        assert report["token_metrics"]["total_tokens"] == 100  # 20 tokens × 5 streams

        # Check network metrics
        assert "network_metrics" in report

        # Check client metrics
        assert "client_metrics" in report

    def test_correlations(self):
        """Test correlation calculations."""
        tracker = StreamingMetricsTracker()

        # Create streams with varying parameters
        for i in range(10):
            stream_id = f"test-{i}"

            tracker.start_stream(
                stream_id=stream_id,
                model="gpt-4",
                prompt_tokens=50 + (i * 10),  # Varying prompt length
                temperature=0.5 + (i * 0.05),  # Varying temperature
                max_tokens=50 + (i * 20),  # Varying max_tokens
            )

            # Add tokens
            for j in range(20):
                tracker.record_token(
                    stream_id,
                    f"token{j}",
                    timestamp_ns=1000000000 + (j * 50000000) + (i * 1000000),
                )

            tracker.complete_stream(stream_id, "stop")

        # Get quality report with correlations
        report = tracker.get_streaming_quality_report()

        assert "correlations" in report
        # Should have some correlation data
        # (exact values depend on the simulated data)

    def test_max_active_streams_limit(self):
        """Test that max active streams limit is enforced."""
        tracker = StreamingMetricsTracker(max_active_streams=5)

        # Create 10 streams (should only keep last 5)
        for i in range(10):
            tracker.start_stream(
                stream_id=f"test-{i}",
                model="gpt-4",
                prompt_tokens=50,
            )

        # Should only have 5 active streams
        assert tracker.get_active_stream_count() == 5

    def test_max_completed_streams_limit(self):
        """Test that max completed streams limit is enforced."""
        tracker = StreamingMetricsTracker(max_completed_streams=3)

        # Create and complete 10 streams
        for i in range(10):
            stream_id = f"test-{i}"
            tracker.start_stream(
                stream_id=stream_id,
                model="gpt-4",
                prompt_tokens=50,
            )
            tracker.record_token(stream_id, "token", timestamp_ns=1000000000)
            tracker.complete_stream(stream_id, "stop")

        # Should only keep last 3
        assert tracker.get_completed_stream_count() == 3

    def test_clear_history(self):
        """Test clearing history."""
        tracker = StreamingMetricsTracker()

        # Create and complete some streams
        for i in range(3):
            stream_id = f"test-{i}"
            tracker.start_stream(stream_id=stream_id, model="gpt-4", prompt_tokens=50)
            tracker.record_token(stream_id, "token", timestamp_ns=1000000000)
            tracker.complete_stream(stream_id, "stop")

        assert tracker.get_completed_stream_count() == 3

        # Clear history
        tracker.clear_history()

        assert tracker.get_completed_stream_count() == 0

    def test_reset(self):
        """Test full reset."""
        tracker = StreamingMetricsTracker()

        # Create active and completed streams
        tracker.start_stream("active-1", model="gpt-4", prompt_tokens=50)
        tracker.start_stream("active-2", model="gpt-4", prompt_tokens=50)

        tracker.start_stream("completed-1", model="gpt-4", prompt_tokens=50)
        tracker.record_token("completed-1", "token", timestamp_ns=1000000000)
        tracker.complete_stream("completed-1", "stop")

        assert tracker.get_active_stream_count() == 2
        assert tracker.get_completed_stream_count() == 1

        # Reset everything
        tracker.reset()

        assert tracker.get_active_stream_count() == 0
        assert tracker.get_completed_stream_count() == 0

    def test_get_all_clients(self):
        """Test getting all client statistics."""
        tracker = StreamingMetricsTracker()

        # Create streams for different clients
        for client_num in range(3):
            client_id = f"client-{client_num}"

            for stream_num in range(2):
                stream_id = f"test-{client_num}-{stream_num}"

                tracker.start_stream(
                    stream_id=stream_id,
                    model="gpt-4",
                    prompt_tokens=50,
                    client_id=client_id,
                )

                tracker.record_token(stream_id, "token", timestamp_ns=1000000000)
                tracker.complete_stream(stream_id, "stop", client_id=client_id)

        # Get all clients
        all_clients = tracker.get_all_clients()

        assert len(all_clients) == 3
        for client in all_clients:
            assert client["total_streams"] == 2

    def test_stall_detection(self):
        """Test automatic stall detection."""
        tracker = StreamingMetricsTracker()

        tracker.start_stream(
            stream_id="test-123",
            model="gpt-4",
            prompt_tokens=50,
        )

        # Add tokens with one stall
        tracker.record_token("test-123", "token0", timestamp_ns=1000000000)
        tracker.record_token(
            "test-123", "token1", timestamp_ns=1050000000
        )  # 50ms (no stall)
        tracker.record_token(
            "test-123", "token2", timestamp_ns=1700000000
        )  # 650ms (stall!)

        tracker.complete_stream("test-123", "stop")

        stats = tracker.get_stream_stats("test-123")
        assert stats["stall_events"] == 1

    def test_nonexistent_stream(self):
        """Test operations on nonexistent streams."""
        tracker = StreamingMetricsTracker()

        # Try to get stats for nonexistent stream
        stats = tracker.get_stream_stats("nonexistent")
        assert stats is None

        # Try to record token for nonexistent stream (should not crash)
        tracker.record_token("nonexistent", "token", timestamp_ns=1000000000)

        # Try to complete nonexistent stream (should not crash)
        tracker.complete_stream("nonexistent", "stop")

    def test_nonexistent_client(self):
        """Test operations on nonexistent clients."""
        tracker = StreamingMetricsTracker()

        # Try to get stats for nonexistent client
        stats = tracker.get_client_stats("nonexistent")
        assert stats is None

    def test_empty_quality_report(self):
        """Test quality report with no streams."""
        tracker = StreamingMetricsTracker()

        report = tracker.get_streaming_quality_report()

        assert report["total_streams"] == 0
        assert report["active_streams"] == 0
        assert "message" in report
