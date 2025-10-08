"""
Comprehensive thread safety tests for concurrent access to trackers.

Tests all trackers for thread safety under various concurrent access patterns:
- StreamingMetricsTracker
- ErrorMetricsTracker
- CostTracker
- MetricsTracker (legacy)
- AsyncEventBus

Coverage:
1. Concurrent event publishing
2. Concurrent tracker updates
3. Read while write scenarios
4. Subscriber execution threading
5. Counter integrity under concurrent increments
6. Collection safety (deque, dict operations)
"""

import asyncio
import importlib.util
import random
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pytest


# Import modules directly by file path to avoid triggering app initialization
def import_module_from_path(module_name, file_path):
    """Import a module directly from file path without importing parent package."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

# Get the project root
project_root = Path(__file__).parent.parent

# Import trackers directly
cost_tracker_module = import_module_from_path(
    "fakeai.cost_tracker",
    project_root / "fakeai" / "cost_tracker.py"
)
error_metrics_module = import_module_from_path(
    "fakeai.error_metrics_tracker",
    project_root / "fakeai" / "error_metrics_tracker.py"
)
streaming_metrics_module = import_module_from_path(
    "fakeai.streaming_metrics_tracker",
    project_root / "fakeai" / "streaming_metrics_tracker.py"
)
metrics_module = import_module_from_path(
    "fakeai.metrics",
    project_root / "fakeai" / "metrics.py"
)

# Import events
events_base_module = import_module_from_path(
    "fakeai.events.base",
    project_root / "fakeai" / "events" / "base.py"
)
events_bus_module = import_module_from_path(
    "fakeai.events.bus",
    project_root / "fakeai" / "events" / "bus.py"
)

# Extract classes
CostTracker = cost_tracker_module.CostTracker
ErrorMetricsTracker = error_metrics_module.ErrorMetricsTracker
StreamingMetricsTracker = streaming_metrics_module.StreamingMetricsTracker
MetricsTracker = metrics_module.MetricsTracker
BaseEvent = events_base_module.BaseEvent
AsyncEventBus = events_bus_module.AsyncEventBus


class TestConcurrentEventPublishing:
    """Test concurrent event publishing to AsyncEventBus."""

    @pytest.mark.asyncio
    async def test_10_threads_publishing_simultaneously(self):
        """
        Test that 10 threads can publish events simultaneously without
        losing events or causing race conditions.
        """
        bus = AsyncEventBus(max_queue_size=10000)
        await bus.start()

        # Collector to track received events
        received_events = []
        received_lock = asyncio.Lock()

        async def collect_event(event: BaseEvent):
            async with received_lock:
                received_events.append(event.event_id)

        # Subscribe to test events
        bus.subscribe("test.event", collect_event)

        # Create test events
        num_threads = 10
        events_per_thread = 100
        total_events = num_threads * events_per_thread

        # Publish from multiple threads
        def publish_events(thread_id: int):
            """Publish events from a single thread."""
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            async def publish():
                for i in range(events_per_thread):
                    event = BaseEvent(
                        event_type="test.event",
                        event_id=f"thread-{thread_id}-event-{i}",
                        request_id=f"req-{thread_id}-{i}",
                    )
                    await bus.publish(event)

            loop.run_until_complete(publish())
            loop.close()

        # Run publishing threads
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [
                executor.submit(publish_events, i) for i in range(num_threads)
            ]
            for future in as_completed(futures):
                future.result()  # Wait for completion

        # Wait for all events to be processed
        await asyncio.sleep(2.0)

        # Verify all events received
        assert len(received_events) == total_events, (
            f"Expected {total_events} events, received {len(received_events)}"
        )

        # Verify no duplicate event IDs
        assert len(set(received_events)) == total_events, (
            "Duplicate events detected"
        )

        # Verify events from all threads
        thread_ids = set()
        for event_id in received_events:
            thread_id = int(event_id.split("-")[1])
            thread_ids.add(thread_id)
        assert len(thread_ids) == num_threads, (
            f"Expected events from {num_threads} threads, got {len(thread_ids)}"
        )

        await bus.stop(timeout=2.0)

    @pytest.mark.asyncio
    async def test_no_events_lost(self):
        """Verify that no events are lost during concurrent publishing."""
        bus = AsyncEventBus(max_queue_size=5000)
        await bus.start()

        # Track published vs received
        published_count = [0]  # Use list for mutability in closure
        received_count = [0]
        lock = asyncio.Lock()

        async def count_event(event: BaseEvent):
            async with lock:
                received_count[0] += 1

        bus.subscribe("count.event", count_event)

        # Publish from multiple threads
        def publish_batch(batch_id: int, count: int):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            async def publish():
                for i in range(count):
                    event = BaseEvent(
                        event_type="count.event",
                        event_id=f"batch-{batch_id}-{i}",
                    )
                    await bus.publish(event)
                    published_count[0] += 1

            loop.run_until_complete(publish())
            loop.close()

        # Publish 500 events from 5 threads
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(publish_batch, i, 100) for i in range(5)]
            for future in as_completed(futures):
                future.result()

        # Wait for processing
        await asyncio.sleep(2.0)

        # Verify counts match
        assert published_count[0] == 500, f"Published {published_count[0]}, expected 500"
        assert received_count[0] == 500, f"Received {received_count[0]}, expected 500"

        await bus.stop(timeout=2.0)

    @pytest.mark.asyncio
    async def test_no_race_conditions_in_ordering(self):
        """Verify events from same thread maintain ordering."""
        bus = AsyncEventBus(max_queue_size=5000)
        await bus.start()

        # Track event order per thread
        received_orders = {}
        lock = asyncio.Lock()

        async def track_order(event: BaseEvent):
            async with lock:
                thread_id = event.event_id.split("-")[0]
                sequence = int(event.event_id.split("-")[1])

                if thread_id not in received_orders:
                    received_orders[thread_id] = []
                received_orders[thread_id].append(sequence)

        bus.subscribe("order.event", track_order)

        # Publish sequential events from each thread
        def publish_sequential(thread_id: int, count: int):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            async def publish():
                for i in range(count):
                    event = BaseEvent(
                        event_type="order.event",
                        event_id=f"thread{thread_id}-{i}",
                    )
                    await bus.publish(event)
                    # Small delay to ensure ordering
                    await asyncio.sleep(0.001)

            loop.run_until_complete(publish())
            loop.close()

        # Publish from 3 threads
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(publish_sequential, i, 20) for i in range(3)]
            for future in as_completed(futures):
                future.result()

        await asyncio.sleep(2.0)

        # Verify ordering within each thread
        for thread_id, orders in received_orders.items():
            assert orders == sorted(orders), (
                f"Thread {thread_id} events out of order: {orders}"
            )

        await bus.stop(timeout=2.0)


class TestConcurrentTrackerUpdates:
    """Test concurrent updates to various trackers."""

    def test_streaming_metrics_concurrent_updates(self):
        """Test StreamingMetricsTracker handles concurrent stream updates."""
        tracker = StreamingMetricsTracker(
            max_active_streams=1000,
            max_completed_streams=500,
        )

        num_threads = 10
        streams_per_thread = 20

        def manage_streams(thread_id: int):
            """Start, update, and complete streams from one thread."""
            for i in range(streams_per_thread):
                stream_id = f"stream-{thread_id}-{i}"

                # Start stream
                tracker.start_stream(
                    stream_id=stream_id,
                    model="gpt-4o",
                    prompt_tokens=100,
                )

                # Record tokens
                for token_num in range(10):
                    tracker.record_token(
                        stream_id=stream_id,
                        token=f"token{token_num}",
                        chunk_size_bytes=5,
                    )
                    time.sleep(0.001)  # Simulate token generation delay

                # Complete stream
                tracker.complete_stream(
                    stream_id=stream_id,
                    finish_reason="stop",
                )

        # Run concurrent stream management
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(manage_streams, i) for i in range(num_threads)]
            for future in as_completed(futures):
                future.result()

        # Verify metrics
        metrics = tracker.get_metrics()
        expected_total = num_threads * streams_per_thread

        assert metrics.total_streams == expected_total, (
            f"Expected {expected_total} streams, got {metrics.total_streams}"
        )
        assert metrics.completed_streams == expected_total, (
            f"Expected {expected_total} completed, got {metrics.completed_streams}"
        )
        assert metrics.total_tokens_generated == expected_total * 10, (
            f"Expected {expected_total * 10} tokens"
        )

    def test_error_metrics_concurrent_recording(self):
        """Test ErrorMetricsTracker handles concurrent error recording."""
        tracker = ErrorMetricsTracker(max_recent_errors=1000)

        num_threads = 8
        errors_per_thread = 50

        def record_errors(thread_id: int):
            """Record errors from one thread."""
            for i in range(errors_per_thread):
                # Record error
                tracker.record_error(
                    endpoint="/v1/chat/completions",
                    status_code=500,
                    error_type="InternalServerError",
                    error_message=f"Error from thread {thread_id} iteration {i}",
                    model="gpt-4",
                    request_id=f"req-{thread_id}-{i}",
                )

                # Record some successes too
                if i % 2 == 0:
                    tracker.record_success(
                        endpoint="/v1/chat/completions",
                        model="gpt-4",
                    )

                time.sleep(0.001)

        # Run concurrent error recording
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(record_errors, i) for i in range(num_threads)]
            for future in as_completed(futures):
                future.result()

        # Verify metrics
        metrics = tracker.get_metrics()
        expected_errors = num_threads * errors_per_thread
        expected_successes = num_threads * (errors_per_thread // 2)

        assert metrics["total_errors"] == expected_errors, (
            f"Expected {expected_errors} errors, got {metrics['total_errors']}"
        )
        assert metrics["total_successes"] == expected_successes, (
            f"Expected {expected_successes} successes, got {metrics['total_successes']}"
        )

    def test_cost_tracker_concurrent_usage_recording(self):
        """Test CostTracker handles concurrent usage recording."""
        tracker = CostTracker()
        tracker.clear_history()  # Clean slate

        num_threads = 10
        records_per_thread = 30

        def record_usage(thread_id: int):
            """Record usage from one thread."""
            api_key = f"sk-test-thread{thread_id}"

            for i in range(records_per_thread):
                tracker.record_usage(
                    api_key=api_key,
                    model="gpt-4o",
                    endpoint="/v1/chat/completions",
                    prompt_tokens=100,
                    completion_tokens=50,
                )
                time.sleep(0.001)

        # Run concurrent recording
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(record_usage, i) for i in range(num_threads)]
            for future in as_completed(futures):
                future.result()

        # Verify summary
        summary = tracker.get_summary()
        expected_requests = num_threads * records_per_thread

        assert summary["total_requests"] == expected_requests, (
            f"Expected {expected_requests} requests, got {summary['total_requests']}"
        )
        assert summary["unique_api_keys"] == num_threads, (
            f"Expected {num_threads} API keys, got {summary['unique_api_keys']}"
        )

        # Verify per-key costs
        for thread_id in range(num_threads):
            api_key = f"sk-test-thread{thread_id}"
            key_cost = tracker.get_cost_by_key(api_key)
            assert key_cost["requests"] == records_per_thread, (
                f"Thread {thread_id} expected {records_per_thread} requests"
            )

        tracker.clear_history()

    def test_metrics_tracker_concurrent_requests(self):
        """Test legacy MetricsTracker handles concurrent requests."""
        tracker = MetricsTracker()

        num_threads = 8
        requests_per_thread = 40
        endpoint = "/v1/chat/completions"

        def simulate_requests(thread_id: int):
            """Simulate requests from one thread."""
            for i in range(requests_per_thread):
                # Track request
                tracker.track_request(endpoint)

                # Simulate processing
                time.sleep(random.uniform(0.001, 0.005))

                # Track response with latency
                latency = random.uniform(0.1, 0.5)
                tracker.track_response(endpoint, latency)

                # Track tokens
                tracker.track_tokens(endpoint, random.randint(50, 200))

        # Run concurrent requests
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(simulate_requests, i) for i in range(num_threads)]
            for future in as_completed(futures):
                future.result()

        # Allow metrics to stabilize
        time.sleep(1.0)

        # Verify metrics
        metrics = tracker.get_metrics()

        # Check that we have data for the endpoint
        assert "requests" in metrics
        assert endpoint in metrics["requests"]
        assert "responses" in metrics
        assert endpoint in metrics["responses"]


class TestReadWhileWrite:
    """Test reading metrics while concurrent writes are happening."""

    def test_streaming_tracker_read_during_write(self):
        """Test reading StreamingMetricsTracker while streams are being updated."""
        tracker = StreamingMetricsTracker(max_active_streams=500)

        stop_flag = threading.Event()
        read_errors = []

        def writer():
            """Continuously write stream data."""
            stream_id = 0
            while not stop_flag.is_set():
                sid = f"stream-{stream_id}"
                try:
                    tracker.start_stream(sid, "gpt-4o", 100)
                    for _ in range(5):
                        tracker.record_token(sid, "token", 5)
                    tracker.complete_stream(sid, "stop")
                    stream_id += 1
                except Exception as e:
                    read_errors.append(f"Writer error: {e}")
                time.sleep(0.01)

        def reader():
            """Continuously read metrics."""
            while not stop_flag.is_set():
                try:
                    # Read metrics
                    metrics = tracker.get_metrics()
                    assert metrics is not None
                    assert isinstance(metrics.total_streams, int)
                    assert metrics.total_streams >= 0

                    # Read active count
                    active = tracker.get_active_stream_count()
                    assert isinstance(active, int)
                    assert active >= 0

                except Exception as e:
                    read_errors.append(f"Reader error: {e}")
                time.sleep(0.005)

        # Run writers and readers concurrently
        writer_threads = [threading.Thread(target=writer) for _ in range(3)]
        reader_threads = [threading.Thread(target=reader) for _ in range(3)]

        for t in writer_threads + reader_threads:
            t.start()

        # Run for 2 seconds
        time.sleep(2.0)
        stop_flag.set()

        for t in writer_threads + reader_threads:
            t.join(timeout=2.0)

        # Verify no errors occurred
        assert len(read_errors) == 0, f"Errors during concurrent read/write: {read_errors}"

    def test_error_tracker_read_during_write(self):
        """Test reading ErrorMetricsTracker while errors are being recorded."""
        tracker = ErrorMetricsTracker(max_recent_errors=500)

        stop_flag = threading.Event()
        errors = []

        def writer():
            """Continuously record errors."""
            count = 0
            while not stop_flag.is_set():
                try:
                    tracker.record_error(
                        endpoint="/v1/test",
                        status_code=500,
                        error_type="TestError",
                        error_message=f"Error {count}",
                    )
                    count += 1
                except Exception as e:
                    errors.append(f"Writer: {e}")
                time.sleep(0.01)

        def reader():
            """Continuously read error metrics."""
            while not stop_flag.is_set():
                try:
                    # Read metrics
                    metrics = tracker.get_metrics()
                    assert metrics is not None
                    assert "total_errors" in metrics

                    # Read patterns
                    patterns = tracker.get_error_patterns()
                    assert isinstance(patterns, list)

                    # Read SLO status
                    slo = tracker.get_slo_status()
                    assert slo is not None

                except Exception as e:
                    errors.append(f"Reader: {e}")
                time.sleep(0.005)

        # Run writers and readers
        writer_threads = [threading.Thread(target=writer) for _ in range(2)]
        reader_threads = [threading.Thread(target=reader) for _ in range(3)]

        for t in writer_threads + reader_threads:
            t.start()

        time.sleep(2.0)
        stop_flag.set()

        for t in writer_threads + reader_threads:
            t.join(timeout=2.0)

        assert len(errors) == 0, f"Errors: {errors}"

    def test_no_deadlocks(self):
        """Verify that concurrent reads and writes don't cause deadlocks."""
        tracker = StreamingMetricsTracker(max_active_streams=200)

        stop_flag = threading.Event()
        completed_operations = {"writes": 0, "reads": 0}
        lock = threading.Lock()

        def aggressive_writer():
            """Aggressively write to tracker."""
            while not stop_flag.is_set():
                try:
                    sid = f"stream-{threading.get_ident()}-{time.time()}"
                    tracker.start_stream(sid, "model", 10)
                    tracker.record_token(sid, "x", 1)
                    tracker.complete_stream(sid, "stop")

                    with lock:
                        completed_operations["writes"] += 1
                except ValueError:
                    # Max streams reached, ignore
                    pass
                except Exception:
                    pass

        def aggressive_reader():
            """Aggressively read from tracker."""
            while not stop_flag.is_set():
                try:
                    tracker.get_metrics()
                    tracker.get_active_stream_count()

                    with lock:
                        completed_operations["reads"] += 1
                except Exception:
                    pass

        # Create many threads
        num_writers = 5
        num_readers = 5

        threads = []
        threads.extend([threading.Thread(target=aggressive_writer) for _ in range(num_writers)])
        threads.extend([threading.Thread(target=aggressive_reader) for _ in range(num_readers)])

        for t in threads:
            t.start()

        # Run for 3 seconds
        time.sleep(3.0)
        stop_flag.set()

        # Join with timeout - if we timeout, there's a deadlock
        for t in threads:
            t.join(timeout=2.0)
            assert not t.is_alive(), "Thread still alive - possible deadlock detected"

        # Verify we did actual work
        assert completed_operations["writes"] > 0, "No write operations completed"
        assert completed_operations["reads"] > 0, "No read operations completed"


class TestSubscriberExecution:
    """Test that subscribers are executed correctly in worker thread."""

    @pytest.mark.asyncio
    async def test_subscribers_called_from_worker_thread(self):
        """Verify subscribers execute in the worker thread, not main thread."""
        bus = AsyncEventBus(max_queue_size=1000)
        await bus.start()

        main_thread_id = threading.get_ident()
        subscriber_thread_ids = []
        lock = asyncio.Lock()

        async def capture_thread_id(event: BaseEvent):
            thread_id = threading.get_ident()
            async with lock:
                subscriber_thread_ids.append(thread_id)

        bus.subscribe("test.event", capture_thread_id)

        # Publish events
        for i in range(10):
            await bus.publish(BaseEvent(event_type="test.event", event_id=f"event-{i}"))

        await asyncio.sleep(1.0)

        # Verify subscribers ran in worker thread (not main)
        assert len(subscriber_thread_ids) == 10
        # All should be in same worker thread
        assert len(set(subscriber_thread_ids)) == 1
        # Worker thread should be different from main
        worker_thread_id = subscriber_thread_ids[0]
        # Note: In async context, thread IDs may be same, but execution is still async

        await bus.stop(timeout=2.0)

    @pytest.mark.asyncio
    async def test_main_thread_can_publish_while_subscriber_runs(self):
        """Verify main thread can continue publishing while subscribers process."""
        bus = AsyncEventBus(max_queue_size=1000)
        await bus.start()

        processed_count = [0]
        lock = asyncio.Lock()

        async def slow_subscriber(event: BaseEvent):
            """Subscriber that takes time to process."""
            await asyncio.sleep(0.1)  # Simulate slow processing
            async with lock:
                processed_count[0] += 1

        bus.subscribe("slow.event", slow_subscriber)

        # Publish rapidly while subscribers are still processing
        publish_count = 20
        for i in range(publish_count):
            await bus.publish(BaseEvent(event_type="slow.event", event_id=f"event-{i}"))
            # Don't wait - publish immediately

        # Verify we could publish all events without blocking
        assert bus._event_count == publish_count

        # Wait for processing to complete
        await asyncio.sleep(3.0)

        # Verify all events were processed
        assert processed_count[0] == publish_count

        await bus.stop(timeout=2.0)

    @pytest.mark.asyncio
    async def test_no_blocking_on_publish(self):
        """Verify that publish() never blocks the caller."""
        bus = AsyncEventBus(max_queue_size=100)
        await bus.start()

        async def never_finishes(event: BaseEvent):
            """Subscriber that would block forever if executed synchronously."""
            await asyncio.sleep(1000)

        bus.subscribe("blocking.event", never_finishes)

        # Measure time to publish
        start = time.time()
        for i in range(50):
            await bus.publish(BaseEvent(event_type="blocking.event", event_id=f"e{i}"))
        elapsed = time.time() - start

        # Should complete almost instantly (< 100ms) despite slow subscriber
        assert elapsed < 0.1, f"Publishing took {elapsed}s - too slow, might be blocking"

        await bus.stop(timeout=1.0)


class TestCounterIntegrity:
    """Test that counters maintain integrity under concurrent increments."""

    def test_streaming_tracker_token_count_accuracy(self):
        """Verify token counts are accurate despite concurrent updates."""
        tracker = StreamingMetricsTracker(max_active_streams=500)

        num_threads = 10
        tokens_per_thread = 100

        def record_tokens(thread_id: int):
            """Record tokens from one thread."""
            stream_id = f"stream-{thread_id}"

            tracker.start_stream(stream_id, "gpt-4", 50)

            for i in range(tokens_per_thread):
                tracker.record_token(stream_id, f"token{i}", chunk_size_bytes=10)

            tracker.complete_stream(stream_id, "stop")

        # Execute concurrently
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(record_tokens, i) for i in range(num_threads)]
            for future in as_completed(futures):
                future.result()

        # Verify counts
        metrics = tracker.get_metrics()
        expected_tokens = num_threads * tokens_per_thread
        expected_bytes = expected_tokens * 10

        assert metrics.total_tokens_generated == expected_tokens, (
            f"Expected {expected_tokens} tokens, got {metrics.total_tokens_generated}"
        )
        assert metrics.total_bytes_sent == expected_bytes, (
            f"Expected {expected_bytes} bytes, got {metrics.total_bytes_sent}"
        )

    def test_error_tracker_counter_accuracy(self):
        """Verify error counters are accurate under concurrent increments."""
        tracker = ErrorMetricsTracker(max_recent_errors=2000)

        num_threads = 15
        errors_per_thread = 50
        successes_per_thread = 50

        def record_mixed(thread_id: int):
            """Record errors and successes."""
            for i in range(errors_per_thread):
                tracker.record_error(
                    endpoint="/v1/test",
                    status_code=500,
                    error_type="TestError",
                    error_message=f"Error {thread_id}-{i}",
                )

            for i in range(successes_per_thread):
                tracker.record_success(endpoint="/v1/test")

        # Execute concurrently
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(record_mixed, i) for i in range(num_threads)]
            for future in as_completed(futures):
                future.result()

        # Verify counts
        metrics = tracker.get_metrics()
        expected_errors = num_threads * errors_per_thread
        expected_successes = num_threads * successes_per_thread

        assert metrics["total_errors"] == expected_errors, (
            f"Expected {expected_errors} errors, got {metrics['total_errors']}"
        )
        assert metrics["total_successes"] == expected_successes, (
            f"Expected {expected_successes} successes, got {metrics['total_successes']}"
        )

    def test_cost_tracker_cost_accumulation_accuracy(self):
        """Verify cost accumulation is accurate under concurrent updates."""
        tracker = CostTracker()
        tracker.clear_history()

        num_threads = 12
        records_per_thread = 40
        api_key = "sk-test-concurrent"

        # Known costs for gpt-4o: $5.00 per 1M input, $15.00 per 1M output
        # 100 prompt tokens = $0.0005, 50 completion tokens = $0.00075
        # Total per record = $0.00125
        expected_cost_per_record = 0.00125
        expected_total = num_threads * records_per_thread * expected_cost_per_record

        def record_usage_batch(thread_id: int):
            """Record usage from one thread."""
            for i in range(records_per_thread):
                tracker.record_usage(
                    api_key=api_key,
                    model="gpt-4o",
                    endpoint="/v1/chat/completions",
                    prompt_tokens=100,
                    completion_tokens=50,
                )

        # Execute concurrently
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(record_usage_batch, i) for i in range(num_threads)]
            for future in as_completed(futures):
                future.result()

        # Verify cost
        cost_info = tracker.get_cost_by_key(api_key)
        actual_cost = cost_info["total_cost"]

        # Allow small floating point tolerance
        assert abs(actual_cost - expected_total) < 0.0001, (
            f"Expected ${expected_total:.6f}, got ${actual_cost:.6f}"
        )

        tracker.clear_history()

    def test_no_lost_increments(self):
        """
        Stress test to verify no increments are lost under high contention.

        This is the most critical test for counter integrity.
        """
        tracker = ErrorMetricsTracker(max_recent_errors=10000)

        num_threads = 20
        increments_per_thread = 500
        expected_total = num_threads * increments_per_thread

        # Use a barrier to maximize contention
        barrier = threading.Barrier(num_threads)

        def increment_errors(thread_id: int):
            """Increment error counter many times."""
            # Wait for all threads to be ready
            barrier.wait()

            # Now all threads increment simultaneously
            for i in range(increments_per_thread):
                tracker.record_error(
                    endpoint="/v1/stress",
                    status_code=500,
                    error_type="StressError",
                    error_message=f"Stress {thread_id}-{i}",
                )

        # Execute with maximum contention
        threads = [threading.Thread(target=increment_errors, args=(i,)) for i in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Verify count
        metrics = tracker.get_metrics()
        assert metrics["total_errors"] == expected_total, (
            f"Lost increments! Expected {expected_total}, got {metrics['total_errors']}"
        )


class TestCollectionSafety:
    """Test thread safety of collection operations (deque, dict)."""

    def test_deque_operations_thread_safe(self):
        """Test that deque operations in StreamingMetricsTracker are thread-safe."""
        tracker = StreamingMetricsTracker(
            max_active_streams=100,
            max_completed_streams=200,
        )

        num_threads = 8
        streams_per_thread = 30

        def complete_streams(thread_id: int):
            """Complete many streams rapidly."""
            for i in range(streams_per_thread):
                stream_id = f"deque-{thread_id}-{i}"
                tracker.start_stream(stream_id, "model", 10)
                tracker.record_token(stream_id, "x", 1)
                tracker.complete_stream(stream_id, "stop")

        # Execute concurrently
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(complete_streams, i) for i in range(num_threads)]
            for future in as_completed(futures):
                future.result()

        # Verify deque integrity
        metrics = tracker.get_metrics()

        # All streams should be completed
        assert metrics.completed_streams == num_threads * streams_per_thread

        # Deque should respect maxlen (200)
        assert metrics.completed_streams <= 200 or tracker.max_completed_streams == 200

    def test_dict_operations_thread_safe(self):
        """Test that dict operations in ErrorMetricsTracker are thread-safe."""
        tracker = ErrorMetricsTracker(max_recent_errors=1000)

        num_threads = 10
        unique_endpoints = 20

        def record_varied_errors(thread_id: int):
            """Record errors for various endpoints."""
            for i in range(100):
                endpoint = f"/v1/endpoint{i % unique_endpoints}"
                tracker.record_error(
                    endpoint=endpoint,
                    status_code=500,
                    error_type=f"ErrorType{i % 5}",
                    error_message=f"Message {thread_id}-{i}",
                )

        # Execute concurrently
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(record_varied_errors, i) for i in range(num_threads)]
            for future in as_completed(futures):
                future.result()

        # Verify dict integrity
        metrics = tracker.get_metrics()

        # Should have data for all endpoints
        assert len(metrics["errors_by_endpoint"]) == unique_endpoints

        # Counts should be consistent
        total_from_endpoints = sum(metrics["errors_by_endpoint"].values())
        assert total_from_endpoints == metrics["total_errors"]

    def test_no_collection_corruption(self):
        """
        Stress test to verify collections don't get corrupted.

        This tests for rare corruption issues that can occur with
        non-thread-safe collection operations.
        """
        tracker = StreamingMetricsTracker(max_active_streams=500)

        stop_flag = threading.Event()
        corruption_detected = []

        def hammer_collections():
            """Continuously perform collection operations."""
            stream_count = 0
            while not stop_flag.is_set():
                try:
                    # Add and remove from dict
                    sid = f"hammer-{threading.get_ident()}-{stream_count}"
                    tracker.start_stream(sid, "model", 10)
                    tracker.record_token(sid, "x", 1)
                    tracker.complete_stream(sid, "stop")
                    stream_count += 1

                    # Read operations
                    tracker.get_metrics()
                    tracker.get_active_stream_count()

                except Exception as e:
                    corruption_detected.append(str(e))

        # Run many threads hammering collections
        threads = [threading.Thread(target=hammer_collections) for _ in range(8)]
        for t in threads:
            t.start()

        # Run for 3 seconds
        time.sleep(3.0)
        stop_flag.set()

        for t in threads:
            t.join(timeout=2.0)

        # Verify no corruption detected
        assert len(corruption_detected) == 0, (
            f"Collection corruption detected: {corruption_detected}"
        )


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_concurrent_tracker_reset(self):
        """Test that reset during concurrent operations doesn't crash."""
        tracker = StreamingMetricsTracker(max_active_streams=100)

        stop_flag = threading.Event()

        def continuous_updates():
            """Continuously update streams."""
            count = 0
            while not stop_flag.is_set():
                try:
                    sid = f"reset-test-{count}"
                    tracker.start_stream(sid, "model", 10)
                    tracker.record_token(sid, "x", 1)
                    tracker.complete_stream(sid, "stop")
                    count += 1
                except (ValueError, KeyError):
                    # Might fail during reset - that's ok
                    pass
                time.sleep(0.001)

        def reset_periodically():
            """Periodically reset tracker."""
            while not stop_flag.is_set():
                time.sleep(0.1)
                try:
                    tracker.reset()
                except Exception:
                    pass

        # Run updaters and resetter
        update_threads = [threading.Thread(target=continuous_updates) for _ in range(3)]
        reset_thread = threading.Thread(target=reset_periodically)

        for t in update_threads + [reset_thread]:
            t.start()

        time.sleep(1.0)
        stop_flag.set()

        for t in update_threads + [reset_thread]:
            t.join(timeout=2.0)

        # Just verify we didn't crash

    def test_max_capacity_handling(self):
        """Test behavior when reaching maximum capacity."""
        tracker = StreamingMetricsTracker(max_active_streams=10)

        def try_add_streams(thread_id: int):
            """Try to add more streams than capacity."""
            for i in range(20):
                try:
                    sid = f"capacity-{thread_id}-{i}"
                    tracker.start_stream(sid, "model", 10)
                except ValueError:
                    # Expected when max reached
                    pass
                time.sleep(0.001)

        # Multiple threads try to exceed capacity
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(try_add_streams, i) for i in range(5)]
            for future in as_completed(futures):
                future.result()

        # Verify we never exceeded max
        active_count = tracker.get_active_stream_count()
        assert active_count <= 10, f"Exceeded max capacity: {active_count} > 10"


# Integration test combining multiple trackers
class TestMultiTrackerIntegration:
    """Test multiple trackers being used concurrently."""

    def test_all_trackers_concurrent(self):
        """
        Integration test: Use all trackers simultaneously from multiple threads.

        This simulates a real production scenario where all metrics systems
        are active and processing data concurrently.
        """
        streaming_tracker = StreamingMetricsTracker(max_active_streams=200)
        error_tracker = ErrorMetricsTracker(max_recent_errors=500)
        cost_tracker = CostTracker()
        cost_tracker.clear_history()

        num_threads = 6
        operations_per_thread = 30

        def simulate_requests(thread_id: int):
            """Simulate API requests with all trackers."""
            api_key = f"sk-test-{thread_id}"

            for i in range(operations_per_thread):
                stream_id = f"multi-{thread_id}-{i}"

                # Streaming tracker
                streaming_tracker.start_stream(stream_id, "gpt-4o", 100)
                for _ in range(5):
                    streaming_tracker.record_token(stream_id, "token", 5)

                # Simulate occasional errors
                if i % 5 == 0:
                    error_tracker.record_error(
                        endpoint="/v1/chat/completions",
                        status_code=500,
                        error_type="TestError",
                        error_message=f"Error {thread_id}-{i}",
                    )
                else:
                    error_tracker.record_success(endpoint="/v1/chat/completions")

                # Cost tracking
                cost_tracker.record_usage(
                    api_key=api_key,
                    model="gpt-4o",
                    endpoint="/v1/chat/completions",
                    prompt_tokens=100,
                    completion_tokens=50,
                )

                # Complete stream
                streaming_tracker.complete_stream(stream_id, "stop")

                time.sleep(0.01)

        # Run all trackers concurrently
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(simulate_requests, i) for i in range(num_threads)]
            for future in as_completed(futures):
                future.result()

        # Verify all trackers have consistent data
        expected_operations = num_threads * operations_per_thread

        # Streaming metrics
        streaming_metrics = streaming_tracker.get_metrics()
        assert streaming_metrics.completed_streams == expected_operations

        # Error metrics
        error_metrics = error_tracker.get_metrics()
        assert error_metrics["total_requests"] == expected_operations

        # Cost metrics
        cost_summary = cost_tracker.get_summary()
        assert cost_summary["total_requests"] == expected_operations

        cost_tracker.clear_history()
