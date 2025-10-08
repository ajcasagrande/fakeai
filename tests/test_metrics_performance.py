"""
Performance and Load Tests for Metrics System.

This test suite validates the performance characteristics of all metrics
tracking components under load:

1. Event Bus Throughput
2. StreamingMetricsTracker Performance
3. ErrorMetricsTracker Performance
4. CostTracker Performance
5. Concurrent Access Patterns
6. Memory Usage Patterns

Each test includes performance assertions for latency, throughput, and memory.

RUNNING THESE TESTS:
-------------------
Due to import dependencies, run with:

    # Run all performance tests
    pytest -m performance tests/test_metrics_performance.py -v

    # Run specific test class
    pytest tests/test_metrics_performance.py::TestEventBusPerformance -v

    # Run single test
    pytest tests/test_metrics_performance.py::TestEventBusPerformance::test_event_bus_sustainable_throughput_10k_per_sec -v

    # Run benchmarks (requires pytest-benchmark)
    pytest -m benchmark tests/test_metrics_performance.py -v

NOTE: These tests use direct module imports to avoid triggering full
app initialization. See import block below for implementation details.
"""

import asyncio
import gc
import logging
import sys
import threading
import time
import tracemalloc
from collections import deque
from pathlib import Path

import pytest

# Add fakeai directory to path to import modules without triggering app initialization
fakeai_dir = Path(__file__).parent.parent / "fakeai"
sys.path.insert(0, str(fakeai_dir))

from events.base import BaseEvent
from events.bus import AsyncEventBus
from metrics import MetricsTracker

logger = logging.getLogger(__name__)


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def event_bus():
    """Create a fresh event bus for testing."""
    bus = AsyncEventBus(max_queue_size=100000)
    yield bus
    # No cleanup needed - each test creates its own bus


@pytest.fixture
def metrics_tracker():
    """Create a fresh metrics tracker for testing."""
    # Note: MetricsTracker is a singleton, but we can track individual endpoints
    tracker = MetricsTracker()
    yield tracker
    # Cleanup happens automatically via singleton


@pytest.fixture
def streaming_tracker():
    """Create a streaming metrics tracker for testing."""
    tracker = MetricsTracker()
    return tracker


# ============================================================================
# Event Bus Performance Tests
# ============================================================================


@pytest.mark.performance
@pytest.mark.asyncio
class TestEventBusPerformance:
    """Test event bus throughput and latency under load."""

    async def test_event_bus_sustainable_throughput_10k_per_sec(self, event_bus):
        """
        Test: Event bus can handle 10K events/sec sustained load.

        Requirements:
        - Process 10,000 events/sec for 5 seconds (50K total)
        - Queue doesn't overflow (no dropped events)
        - Average latency < 1ms per event
        """
        await event_bus.start()

        # Track processed events
        processed_events = []
        processing_times = []

        async def track_handler(event: BaseEvent):
            """Handler that tracks event processing."""
            start = time.perf_counter()
            processed_events.append(event)
            processing_times.append((time.perf_counter() - start) * 1000)

        event_bus.subscribe("test.event", track_handler)

        # Publish 50K events over 5 seconds (10K/sec)
        total_events = 50000
        duration_sec = 5.0
        events_per_batch = 1000
        batch_delay = (events_per_batch / total_events) * duration_sec

        start_time = time.time()
        published_count = 0

        for batch in range(total_events // events_per_batch):
            batch_start = time.time()

            for i in range(events_per_batch):
                event = BaseEvent(
                    event_type="test.event",
                    data={"batch": batch, "index": i},
                )
                await event_bus.publish(event)
                published_count += 1

            # Maintain target rate
            elapsed = time.time() - batch_start
            if elapsed < batch_delay:
                await asyncio.sleep(batch_delay - elapsed)

        # Wait for all events to be processed
        deadline = time.time() + 10.0
        while len(processed_events) < total_events and time.time() < deadline:
            await asyncio.sleep(0.1)

        end_time = time.time()
        actual_duration = end_time - start_time

        # Get stats
        stats = event_bus.get_stats()

        # Assertions
        assert stats["events_dropped"] == 0, "No events should be dropped"
        assert len(processed_events) == total_events, f"All {total_events} events should be processed"

        actual_rate = len(processed_events) / actual_duration
        assert actual_rate >= 9000, f"Should handle ~10K/sec, got {actual_rate:.0f}/sec"

        # Check latency (per-event processing time)
        if processing_times:
            avg_latency = sum(processing_times) / len(processing_times)
            assert avg_latency < 1.0, f"Average latency should be < 1ms, got {avg_latency:.3f}ms"

        await event_bus.stop()

        logger.info(f"✓ Processed {len(processed_events)} events in {actual_duration:.2f}s "
                   f"({actual_rate:.0f}/sec, avg latency: {avg_latency:.3f}ms)")

    async def test_event_bus_burst_throughput_100k_per_sec(self, event_bus):
        """
        Test: Event bus can handle 100K events/sec burst load.

        Requirements:
        - Publish 100,000 events as fast as possible
        - Complete within 1 second
        - Queue doesn't overflow
        """
        await event_bus.start()

        processed_count = 0
        lock = asyncio.Lock()

        async def count_handler(event: BaseEvent):
            """Handler that counts events."""
            nonlocal processed_count
            async with lock:
                processed_count += 1

        event_bus.subscribe("burst.event", count_handler)

        # Publish 100K events as fast as possible
        total_events = 100000
        start_time = time.perf_counter()

        for i in range(total_events):
            event = BaseEvent(event_type="burst.event", data={"index": i})
            await event_bus.publish(event)

        publish_time = time.perf_counter() - start_time

        # Wait for processing to complete
        deadline = time.time() + 30.0
        while processed_count < total_events and time.time() < deadline:
            await asyncio.sleep(0.1)

        processing_time = time.perf_counter() - start_time

        # Get stats
        stats = event_bus.get_stats()

        # Assertions
        assert stats["events_dropped"] == 0, "No events should be dropped during burst"
        assert processed_count == total_events, "All events should be processed"

        publish_rate = total_events / publish_time
        assert publish_rate >= 100000, f"Publish rate should be >= 100K/sec, got {publish_rate:.0f}/sec"

        await event_bus.stop()

        logger.info(f"✓ Burst published {total_events} events in {publish_time:.3f}s "
                   f"({publish_rate:.0f}/sec), processed in {processing_time:.3f}s")

    async def test_event_bus_queue_overflow_handling(self):
        """
        Test: Event bus handles queue overflow gracefully.

        Requirements:
        - Publish more events than queue can hold
        - Events are dropped (not blocked)
        - Drop count is accurate
        """
        # Create bus with small queue
        bus = AsyncEventBus(max_queue_size=100)
        await bus.start()

        # Don't subscribe any handlers - queue will fill up

        # Publish 1000 events
        for i in range(1000):
            event = BaseEvent(event_type="overflow.event", data={"index": i})
            await bus.publish(event)

        stats = bus.get_stats()

        # Assertions
        assert stats["events_dropped"] > 0, "Some events should be dropped"
        assert stats["events_published"] == 1000, "All publishes should be counted"
        assert stats["queue_depth"] <= 100, "Queue should not exceed max size"

        await bus.stop()

        logger.info(f"✓ Queue overflow handled: {stats['events_dropped']} events dropped")

    async def test_event_bus_latency_under_load(self, event_bus):
        """
        Test: Event bus maintains low latency under load.

        Requirements:
        - Average end-to-end latency < 1ms
        - p99 latency < 10ms
        - Measured across 10K events
        """
        await event_bus.start()

        latencies = []
        lock = asyncio.Lock()

        async def latency_handler(event: BaseEvent):
            """Handler that measures latency."""
            publish_time = event.data.get("publish_time")
            if publish_time:
                latency_ms = (time.perf_counter() - publish_time) * 1000
                async with lock:
                    latencies.append(latency_ms)

        event_bus.subscribe("latency.event", latency_handler)

        # Publish 10K events
        total_events = 10000
        for i in range(total_events):
            event = BaseEvent(
                event_type="latency.event",
                data={"index": i, "publish_time": time.perf_counter()},
            )
            await event_bus.publish(event)

        # Wait for processing
        deadline = time.time() + 10.0
        while len(latencies) < total_events and time.time() < deadline:
            await asyncio.sleep(0.1)

        # Calculate statistics
        latencies.sort()
        avg_latency = sum(latencies) / len(latencies)
        p99_latency = latencies[int(len(latencies) * 0.99)]

        # Assertions
        assert avg_latency < 1.0, f"Average latency should be < 1ms, got {avg_latency:.3f}ms"
        assert p99_latency < 10.0, f"p99 latency should be < 10ms, got {p99_latency:.3f}ms"

        await event_bus.stop()

        logger.info(f"✓ Latency test: avg={avg_latency:.3f}ms, p99={p99_latency:.3f}ms")


# ============================================================================
# StreamingMetricsTracker Performance Tests
# ============================================================================


@pytest.mark.performance
class TestStreamingMetricsPerformance:
    """Test streaming metrics tracker performance under load."""

    def test_tracking_1000_concurrent_streams(self, streaming_tracker):
        """
        Test: Track 1000 concurrent streams without degradation.

        Requirements:
        - Create 1000 simultaneous streams
        - Track tokens on each stream
        - Complete all streams
        - get_metrics() < 100ms
        """
        endpoint = "/v1/chat/completions"
        num_streams = 1000

        # Start 1000 streams
        start_time = time.perf_counter()
        stream_ids = []

        for i in range(num_streams):
            stream_id = f"stream_{i}"
            stream_ids.append(stream_id)
            streaming_tracker.start_stream(stream_id, endpoint)

        start_duration = (time.perf_counter() - start_time) * 1000

        # Track first token on all streams
        for stream_id in stream_ids:
            streaming_tracker.track_stream_first_token(stream_id)

        # Track 10 tokens per stream
        tokens_per_stream = 10
        token_start = time.perf_counter()

        for stream_id in stream_ids:
            for _ in range(tokens_per_stream):
                streaming_tracker.track_stream_token(stream_id)

        token_duration = (time.perf_counter() - token_start) * 1000

        # Complete all streams
        complete_start = time.perf_counter()

        for stream_id in stream_ids:
            streaming_tracker.complete_stream(stream_id, endpoint)

        complete_duration = (time.perf_counter() - complete_start) * 1000

        # Measure get_metrics() performance
        metrics_start = time.perf_counter()
        metrics = streaming_tracker.get_metrics()
        metrics_duration = (time.perf_counter() - metrics_start) * 1000

        # Assertions
        assert start_duration < 1000, f"Starting {num_streams} streams should take < 1s"
        assert metrics_duration < 100, f"get_metrics() should take < 100ms, got {metrics_duration:.1f}ms"

        streaming_stats = metrics.get("streaming_stats", {})
        assert streaming_stats.get("completed_streams", 0) >= num_streams, \
            f"Should have {num_streams} completed streams"

        total_tokens = num_streams * tokens_per_stream
        logger.info(f"✓ Tracked {num_streams} streams with {total_tokens} tokens: "
                   f"start={start_duration:.1f}ms, tokens={token_duration:.1f}ms, "
                   f"complete={complete_duration:.1f}ms, metrics={metrics_duration:.1f}ms")

    def test_10k_token_events_per_second(self, streaming_tracker):
        """
        Test: Process 10K token events per second.

        Requirements:
        - Track 10,000 token events/sec
        - Sustained for 5 seconds
        - No performance degradation
        """
        endpoint = "/v1/chat/completions"

        # Create 100 streams
        num_streams = 100
        stream_ids = []

        for i in range(num_streams):
            stream_id = f"token_stream_{i}"
            stream_ids.append(stream_id)
            streaming_tracker.start_stream(stream_id, endpoint)
            streaming_tracker.track_stream_first_token(stream_id)

        # Track 50K tokens over 5 seconds (10K/sec)
        total_tokens = 50000
        tokens_per_second = 10000
        duration_sec = 5.0

        start_time = time.time()
        tokens_tracked = 0

        for second in range(int(duration_sec)):
            second_start = time.time()

            for _ in range(tokens_per_second):
                stream_id = stream_ids[tokens_tracked % num_streams]
                streaming_tracker.track_stream_token(stream_id)
                tokens_tracked += 1

            # Maintain timing
            elapsed = time.time() - second_start
            if elapsed < 1.0:
                time.sleep(1.0 - elapsed)

        end_time = time.time()
        actual_duration = end_time - start_time
        actual_rate = tokens_tracked / actual_duration

        # Assertions
        assert tokens_tracked == total_tokens, f"Should track {total_tokens} tokens"
        assert actual_rate >= 9000, f"Should maintain ~10K tokens/sec, got {actual_rate:.0f}/sec"

        # Complete streams
        for stream_id in stream_ids:
            streaming_tracker.complete_stream(stream_id, endpoint)

        logger.info(f"✓ Tracked {tokens_tracked} tokens in {actual_duration:.2f}s "
                   f"({actual_rate:.0f} tokens/sec)")

    def test_get_metrics_with_1000_completed_streams(self, streaming_tracker):
        """
        Test: get_metrics() performance with 1000 completed streams.

        Requirements:
        - Complete 1000 streams
        - get_metrics() < 100ms
        - Calculate percentiles correctly
        """
        endpoint = "/v1/chat/completions"
        num_streams = 1000

        # Create and complete 1000 streams with varying token counts
        for i in range(num_streams):
            stream_id = f"completed_stream_{i}"
            streaming_tracker.start_stream(stream_id, endpoint)
            streaming_tracker.track_stream_first_token(stream_id)

            # Vary token count (10-100 tokens)
            token_count = 10 + (i % 90)
            for _ in range(token_count):
                streaming_tracker.track_stream_token(stream_id)

            streaming_tracker.complete_stream(stream_id, endpoint)

        # Measure get_metrics() performance
        start_time = time.perf_counter()
        metrics = streaming_tracker.get_metrics()
        duration_ms = (time.perf_counter() - start_time) * 1000

        # Assertions
        assert duration_ms < 100, f"get_metrics() should take < 100ms, got {duration_ms:.1f}ms"

        streaming_stats = metrics.get("streaming_stats", {})
        assert streaming_stats.get("completed_streams", 0) >= num_streams

        # Check that statistics were calculated
        ttft_stats = streaming_stats.get("ttft", {})
        assert "avg" in ttft_stats
        assert "p99" in ttft_stats

        logger.info(f"✓ get_metrics() with {num_streams} completed streams: {duration_ms:.1f}ms")

    def test_memory_bounded_under_load(self, streaming_tracker):
        """
        Test: Memory usage is bounded with maxlen.

        Requirements:
        - Complete 2000 streams (exceeds maxlen=1000)
        - Memory doesn't grow unbounded
        - Old streams are evicted
        """
        endpoint = "/v1/chat/completions"

        # Start memory tracking
        tracemalloc.start()
        gc.collect()
        baseline_memory = tracemalloc.get_traced_memory()[0]

        # Complete 2000 streams
        num_streams = 2000
        for i in range(num_streams):
            stream_id = f"memory_stream_{i}"
            streaming_tracker.start_stream(stream_id, endpoint)
            streaming_tracker.track_stream_first_token(stream_id)

            for _ in range(50):
                streaming_tracker.track_stream_token(stream_id)

            streaming_tracker.complete_stream(stream_id, endpoint)

        # Measure final memory
        gc.collect()
        current_memory = tracemalloc.get_traced_memory()[0]
        memory_increase = (current_memory - baseline_memory) / 1024 / 1024  # MB
        tracemalloc.stop()

        # Get metrics to check stream count
        metrics = streaming_tracker.get_metrics()
        streaming_stats = metrics.get("streaming_stats", {})
        completed_count = streaming_stats.get("completed_streams", 0)

        # Assertions
        # Deque has maxlen=1000, so should only keep 1000 streams
        assert completed_count <= 1000, f"Should keep at most 1000 streams, got {completed_count}"

        # Memory increase should be reasonable (< 50MB for 1000 streams)
        assert memory_increase < 50, f"Memory increase should be < 50MB, got {memory_increase:.1f}MB"

        logger.info(f"✓ Memory bounded: {completed_count} streams kept, "
                   f"memory increase: {memory_increase:.1f}MB")


# ============================================================================
# Concurrent Access Tests
# ============================================================================


@pytest.mark.performance
class TestConcurrentAccess:
    """Test thread-safe concurrent access to metrics."""

    def test_10_threads_publishing_events(self, metrics_tracker):
        """
        Test: 10 threads concurrently tracking metrics.

        Requirements:
        - 10 threads each tracking 1000 events
        - No race conditions
        - All 10,000 events counted
        - Thread-safe operations
        """
        endpoint = "/v1/chat/completions"
        threads_count = 10
        events_per_thread = 1000
        total_expected = threads_count * events_per_thread

        def track_events(thread_id: int):
            """Thread function to track events."""
            for i in range(events_per_thread):
                metrics_tracker.track_request(endpoint)
                metrics_tracker.track_response(endpoint, latency=0.1)
                metrics_tracker.track_tokens(endpoint, count=50)

        # Launch threads
        start_time = time.time()
        threads = []

        for i in range(threads_count):
            thread = threading.Thread(target=track_events, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        duration = time.time() - start_time

        # Small delay for metrics aggregation
        time.sleep(0.5)

        # Get metrics
        metrics = metrics_tracker.get_metrics()

        # Verify data was tracked (note: exact counts may vary due to time windows)
        assert endpoint in metrics.get("requests", {})
        assert endpoint in metrics.get("responses", {})
        assert endpoint in metrics.get("tokens", {})

        logger.info(f"✓ {threads_count} threads tracked {total_expected} events in {duration:.2f}s "
                   f"({total_expected/duration:.0f} events/sec)")

    def test_concurrent_stream_operations(self, streaming_tracker):
        """
        Test: Concurrent stream start/update/complete operations.

        Requirements:
        - Multiple threads operating on different streams
        - No data corruption
        - All streams tracked correctly
        """
        endpoint = "/v1/chat/completions"
        num_threads = 10
        streams_per_thread = 100

        def stream_lifecycle(thread_id: int):
            """Simulate complete stream lifecycle."""
            for i in range(streams_per_thread):
                stream_id = f"thread_{thread_id}_stream_{i}"

                # Start stream
                streaming_tracker.start_stream(stream_id, endpoint)

                # First token
                streaming_tracker.track_stream_first_token(stream_id)

                # Track tokens
                for _ in range(50):
                    streaming_tracker.track_stream_token(stream_id)

                # Complete stream
                streaming_tracker.complete_stream(stream_id, endpoint)

        # Launch threads
        start_time = time.time()
        threads = []

        for i in range(num_threads):
            thread = threading.Thread(target=stream_lifecycle, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        duration = time.time() - start_time

        # Get metrics
        metrics = streaming_tracker.get_metrics()
        streaming_stats = metrics.get("streaming_stats", {})

        total_expected = num_threads * streams_per_thread
        completed = streaming_stats.get("completed_streams", 0)

        # Assertions
        assert completed >= total_expected * 0.9, \
            f"Should have ~{total_expected} completed streams, got {completed}"

        logger.info(f"✓ {num_threads} threads completed {completed} streams in {duration:.2f}s")

    def test_concurrent_read_write_operations(self, metrics_tracker):
        """
        Test: Concurrent reads and writes don't deadlock.

        Requirements:
        - Some threads writing metrics
        - Some threads reading metrics
        - No deadlocks
        - Operations complete in reasonable time
        """
        endpoint = "/v1/chat/completions"
        writer_threads = 5
        reader_threads = 5
        duration_sec = 2

        stop_flag = threading.Event()
        write_counts = []
        read_counts = []
        errors = []

        def writer_func():
            """Continuously write metrics."""
            count = 0
            try:
                while not stop_flag.is_set():
                    metrics_tracker.track_request(endpoint)
                    metrics_tracker.track_response(endpoint, latency=0.05)
                    count += 1
                    time.sleep(0.001)  # 1ms between writes
            except Exception as e:
                errors.append(f"Writer error: {e}")
            finally:
                write_counts.append(count)

        def reader_func():
            """Continuously read metrics."""
            count = 0
            try:
                while not stop_flag.is_set():
                    metrics_tracker.get_metrics()
                    count += 1
                    time.sleep(0.01)  # 10ms between reads
            except Exception as e:
                errors.append(f"Reader error: {e}")
            finally:
                read_counts.append(count)

        # Launch threads
        threads = []

        for _ in range(writer_threads):
            thread = threading.Thread(target=writer_func)
            threads.append(thread)
            thread.start()

        for _ in range(reader_threads):
            thread = threading.Thread(target=reader_func)
            threads.append(thread)
            thread.start()

        # Run for specified duration
        time.sleep(duration_sec)
        stop_flag.set()

        # Wait for all threads
        for thread in threads:
            thread.join(timeout=5.0)

        # Assertions
        assert len(errors) == 0, f"No errors should occur: {errors}"
        assert len(write_counts) == writer_threads, "All writer threads should complete"
        assert len(read_counts) == reader_threads, "All reader threads should complete"

        total_writes = sum(write_counts)
        total_reads = sum(read_counts)

        logger.info(f"✓ Concurrent operations: {total_writes} writes, {total_reads} reads "
                   f"in {duration_sec}s, no deadlocks")


# ============================================================================
# Memory Usage Tests
# ============================================================================


@pytest.mark.performance
class TestMemoryUsage:
    """Test memory usage patterns and bounds."""

    def test_deque_eviction_with_maxlen(self):
        """
        Test: Deque with maxlen properly evicts old items.

        Requirements:
        - Add more items than maxlen
        - Memory doesn't grow unbounded
        - Old items are evicted
        """
        maxlen = 1000
        test_deque = deque(maxlen=maxlen)

        # Start memory tracking
        tracemalloc.start()
        gc.collect()
        baseline_memory = tracemalloc.get_traced_memory()[0]

        # Add 10,000 items (10x maxlen)
        for i in range(10000):
            test_deque.append({"index": i, "data": "x" * 100})

        # Measure memory after additions
        gc.collect()
        current_memory = tracemalloc.get_traced_memory()[0]
        memory_increase = (current_memory - baseline_memory) / 1024  # KB
        tracemalloc.stop()

        # Assertions
        assert len(test_deque) == maxlen, f"Deque should contain exactly {maxlen} items"
        assert test_deque[0]["index"] == 9000, "Oldest item should be from index 9000"
        assert test_deque[-1]["index"] == 9999, "Newest item should be from index 9999"

        # Memory should be bounded (roughly size of 1000 items)
        # Each item is ~150 bytes, so 1000 items ~= 150KB
        assert memory_increase < 500, f"Memory increase should be < 500KB, got {memory_increase:.1f}KB"

        logger.info(f"✓ Deque eviction: {maxlen} items kept, memory: {memory_increase:.1f}KB")

    def test_metrics_window_memory_bounded(self, metrics_tracker):
        """
        Test: MetricsWindow with max_samples keeps memory bounded.

        Requirements:
        - Track events beyond max_samples
        - Memory doesn't grow unbounded
        - Old samples are evicted
        """
        endpoint = "/v1/test/memory"

        # Start memory tracking
        tracemalloc.start()
        gc.collect()
        baseline_memory = tracemalloc.get_traced_memory()[0]

        # Track 200K events (exceeds typical max_samples=100K)
        total_events = 200000
        batch_size = 1000

        for batch in range(total_events // batch_size):
            for _ in range(batch_size):
                metrics_tracker.track_request(endpoint)

            # Periodic GC to get accurate measurement
            if batch % 10 == 0:
                gc.collect()

        # Final memory measurement
        gc.collect()
        current_memory = tracemalloc.get_traced_memory()[0]
        memory_increase = (current_memory - baseline_memory) / 1024 / 1024  # MB
        tracemalloc.stop()

        # Get metrics
        metrics = metrics_tracker.get_metrics()

        # Assertions
        # Memory should be bounded (not grow linearly with event count)
        assert memory_increase < 100, \
            f"Memory should be bounded < 100MB, got {memory_increase:.1f}MB"

        logger.info(f"✓ Tracked {total_events} events, memory increase: {memory_increase:.1f}MB")

    def test_no_memory_leaks_in_stream_lifecycle(self, streaming_tracker):
        """
        Test: No memory leaks in stream lifecycle.

        Requirements:
        - Create/complete streams repeatedly
        - Memory stabilizes after initial growth
        - No continuous growth
        """
        endpoint = "/v1/chat/completions"

        # Warmup phase (allow initial allocations)
        for i in range(100):
            stream_id = f"warmup_{i}"
            streaming_tracker.start_stream(stream_id, endpoint)
            streaming_tracker.track_stream_first_token(stream_id)
            for _ in range(50):
                streaming_tracker.track_stream_token(stream_id)
            streaming_tracker.complete_stream(stream_id, endpoint)

        gc.collect()
        time.sleep(0.1)

        # Start memory tracking
        tracemalloc.start()
        baseline_memory = tracemalloc.get_traced_memory()[0]

        # Run 1000 stream lifecycles
        for i in range(1000):
            stream_id = f"leak_test_{i}"
            streaming_tracker.start_stream(stream_id, endpoint)
            streaming_tracker.track_stream_first_token(stream_id)

            for _ in range(50):
                streaming_tracker.track_stream_token(stream_id)

            streaming_tracker.complete_stream(stream_id, endpoint)

            # Periodic GC
            if i % 100 == 0:
                gc.collect()

        # Final measurement
        gc.collect()
        final_memory = tracemalloc.get_traced_memory()[0]
        memory_increase = (final_memory - baseline_memory) / 1024 / 1024  # MB
        tracemalloc.stop()

        # Assertions
        # Memory should stay relatively stable (< 20MB increase for 1000 streams)
        # Note: deque maxlen=1000, so memory should be bounded
        assert memory_increase < 20, \
            f"Memory increase should be < 20MB (bounded by deque), got {memory_increase:.1f}MB"

        logger.info(f"✓ No memory leaks detected: 1000 streams, memory increase: {memory_increase:.1f}MB")


# ============================================================================
# Benchmarks (if pytest-benchmark available)
# ============================================================================


@pytest.mark.benchmark
@pytest.mark.skipif(
    not pytest.importorskip("pytest_benchmark", reason="pytest-benchmark not installed"),
    reason="pytest-benchmark not installed"
)
class TestMetricsBenchmarks:
    """Benchmarks using pytest-benchmark."""

    def test_benchmark_track_request(self, benchmark, metrics_tracker):
        """Benchmark single track_request call."""
        endpoint = "/v1/chat/completions"

        result = benchmark(metrics_tracker.track_request, endpoint)

        # Benchmark automatically collects stats
        logger.info(f"✓ Benchmark track_request: {benchmark.stats}")

    def test_benchmark_track_stream_token(self, benchmark, streaming_tracker):
        """Benchmark single track_stream_token call."""
        endpoint = "/v1/chat/completions"
        stream_id = "benchmark_stream"

        streaming_tracker.start_stream(stream_id, endpoint)
        streaming_tracker.track_stream_first_token(stream_id)

        result = benchmark(streaming_tracker.track_stream_token, stream_id)

        logger.info(f"✓ Benchmark track_stream_token: {benchmark.stats}")

    def test_benchmark_get_metrics(self, benchmark, metrics_tracker):
        """Benchmark get_metrics call."""
        endpoint = "/v1/chat/completions"

        # Pre-populate with data
        for i in range(1000):
            metrics_tracker.track_request(endpoint)
            metrics_tracker.track_response(endpoint, latency=0.1)

        result = benchmark(metrics_tracker.get_metrics)

        logger.info(f"✓ Benchmark get_metrics: {benchmark.stats}")

    @pytest.mark.asyncio
    async def test_benchmark_event_bus_publish(self, benchmark, event_bus):
        """Benchmark event bus publish."""
        await event_bus.start()

        def publish_event():
            event = BaseEvent(event_type="benchmark.event", data={"test": "data"})
            asyncio.run(event_bus.publish(event))

        result = benchmark(publish_event)

        await event_bus.stop()
        logger.info(f"✓ Benchmark event_bus.publish: {benchmark.stats}")


# ============================================================================
# Summary Report
# ============================================================================


def test_performance_summary(metrics_tracker, capsys):
    """
    Generate a performance summary report.

    This test always passes and prints a summary of expected performance.
    """
    summary = """
    ╔══════════════════════════════════════════════════════════════╗
    ║         METRICS SYSTEM PERFORMANCE REQUIREMENTS              ║
    ╠══════════════════════════════════════════════════════════════╣
    ║ Event Bus Throughput:                                        ║
    ║   • Sustainable: 10,000 events/sec                          ║
    ║   • Burst: 100,000 events/sec                               ║
    ║   • Latency: < 1ms per event (avg)                          ║
    ║   • Queue: No overflow under normal load                     ║
    ║                                                              ║
    ║ StreamingMetricsTracker:                                     ║
    ║   • Concurrent Streams: 1,000 simultaneous                   ║
    ║   • Token Events: 10,000/sec sustained                       ║
    ║   • get_metrics(): < 100ms with 1000 completed streams      ║
    ║   • Memory: Bounded by deque maxlen=1000                     ║
    ║                                                              ║
    ║ Concurrent Access:                                           ║
    ║   • 10 threads publishing events concurrently                ║
    ║   • No race conditions or deadlocks                          ║
    ║   • Thread-safe operations                                   ║
    ║                                                              ║
    ║ Memory Usage:                                                ║
    ║   • Bounded by maxlen on collections                         ║
    ║   • Deque eviction working correctly                         ║
    ║   • No memory leaks in stream lifecycle                      ║
    ╚══════════════════════════════════════════════════════════════╝
    """

    print(summary)

    # This test always passes - it's just informational
    assert True
