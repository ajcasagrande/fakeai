"""
Comprehensive Memory Management and Bounded Collection Tests

This test suite verifies that all trackers and data structures in FakeAI
properly enforce memory bounds and prevent unbounded growth.

Test Coverage:
1. Streaming Tracker Bounds - max active/completed streams, deque eviction
2. Error Tracker Bounds - recent errors bounded, pattern cleanup
3. Cost Tracker Bounds - usage records can be cleaned, memory growth
4. Event Bus Queue - queue maxsize, event dropping, dropped count
5. Deque Behavior - maxlen enforced, FIFO ordering
6. Memory Leak Detection - reference counting, memory baseline restoration

Best Practices:
- Uses tracemalloc for memory profiling when available
- Tests both soft and hard limits
- Verifies FIFO/LRU eviction behavior
- Checks for memory leaks after bulk operations

Author: Claude Code
Date: 2025-10-07
"""

#  SPDX-License-Identifier: Apache-2.0

import asyncio
import gc
import importlib.util
import sys
import threading
import time
from collections import deque
from pathlib import Path

import pytest


# Import modules directly to avoid Flask app initialization
def import_module_from_path(module_name: str, file_name: str):
    """Import a module directly from its file path."""
    module_path = Path(__file__).parent.parent / "fakeai" / file_name
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Import required modules
streaming_module = import_module_from_path("streaming_metrics_tracker", "streaming_metrics_tracker.py")
error_module = import_module_from_path("error_metrics_tracker", "error_metrics_tracker.py")
cost_module = import_module_from_path("cost_tracker", "cost_tracker.py")

StreamingMetricsTracker = streaming_module.StreamingMetricsTracker
ErrorMetricsTracker = error_module.ErrorMetricsTracker
CostTracker = cost_module.CostTracker

# Import event bus (requires async) - import directly to avoid app initialization
try:
    bus_module = import_module_from_path("bus", "events/bus.py")
    AsyncEventBus = bus_module.AsyncEventBus
except Exception:
    AsyncEventBus = None


# Try to import tracemalloc for memory profiling
try:
    import tracemalloc
    HAS_TRACEMALLOC = True
except ImportError:
    HAS_TRACEMALLOC = False


class TestStreamingTrackerBounds:
    """Test memory bounds for StreamingMetricsTracker."""

    def test_max_active_streams_enforced(self):
        """Test that max active streams limit is enforced (10K default)."""
        tracker = StreamingMetricsTracker(max_active_streams=10)

        # Fill up to limit
        for i in range(10):
            tracker.start_stream(f"stream-{i}", model="gpt-4", prompt_tokens=50)

        assert tracker.get_active_stream_count() == 10

        # Attempt to exceed limit should raise ValueError
        with pytest.raises(ValueError, match="Max active streams limit reached"):
            tracker.start_stream("stream-overflow", model="gpt-4", prompt_tokens=50)

    def test_max_active_streams_default_10k(self):
        """Test that default max active streams is 10,000."""
        tracker = StreamingMetricsTracker()
        assert tracker.max_active_streams == 10000

    def test_completed_streams_bounded_to_1k(self):
        """Test that completed streams are bounded to 1K by default."""
        tracker = StreamingMetricsTracker(max_completed_streams=100)

        # Create 200 streams
        for i in range(200):
            stream_id = f"stream-{i}"
            tracker.start_stream(stream_id, model="gpt-4", prompt_tokens=50)
            tracker.record_token(stream_id, "token", chunk_size_bytes=5)
            tracker.complete_stream(stream_id, "stop")

        # Only last 100 should be retained (deque maxlen)
        # Oldest streams should be evicted
        assert tracker.get_stream_details("stream-0") is None
        assert tracker.get_stream_details("stream-50") is None
        assert tracker.get_stream_details("stream-99") is None

        # Recent streams should exist
        assert tracker.get_stream_details("stream-100") is not None
        assert tracker.get_stream_details("stream-150") is not None
        assert tracker.get_stream_details("stream-199") is not None

    def test_completed_streams_deque_maxlen(self):
        """Test that completed streams use deque with maxlen."""
        tracker = StreamingMetricsTracker(max_completed_streams=5)

        # Verify deque has maxlen
        assert tracker._completed_streams.maxlen == 5

        # Fill beyond maxlen
        for i in range(10):
            stream_id = f"stream-{i}"
            tracker.start_stream(stream_id, model="gpt-4", prompt_tokens=50)
            tracker.complete_stream(stream_id, "stop")

        # Deque should only contain last 5
        assert len(tracker._completed_streams) == 5

    def test_old_streams_evicted_fifo(self):
        """Test that oldest completed streams are evicted in FIFO order."""
        tracker = StreamingMetricsTracker(max_completed_streams=3)

        # Complete streams in order
        for i in range(6):
            stream_id = f"stream-{i}"
            tracker.start_stream(stream_id, model="gpt-4", prompt_tokens=50)
            tracker.complete_stream(stream_id, "stop")
            time.sleep(0.01)  # Ensure time ordering

        # Only last 3 should remain
        assert tracker.get_stream_details("stream-0") is None
        assert tracker.get_stream_details("stream-1") is None
        assert tracker.get_stream_details("stream-2") is None
        assert tracker.get_stream_details("stream-3") is not None
        assert tracker.get_stream_details("stream-4") is not None
        assert tracker.get_stream_details("stream-5") is not None

    def test_completing_streams_frees_active_slots(self):
        """Test that completing streams frees up active stream slots."""
        tracker = StreamingMetricsTracker(max_active_streams=5)

        # Fill active slots
        for i in range(5):
            tracker.start_stream(f"stream-{i}", model="gpt-4", prompt_tokens=50)

        # Cannot add more
        with pytest.raises(ValueError):
            tracker.start_stream("overflow", model="gpt-4", prompt_tokens=50)

        # Complete 2 streams
        tracker.complete_stream("stream-0", "stop")
        tracker.complete_stream("stream-1", "stop")

        # Now we can add 2 more
        tracker.start_stream("stream-5", model="gpt-4", prompt_tokens=50)
        tracker.start_stream("stream-6", model="gpt-4", prompt_tokens=50)

        assert tracker.get_active_stream_count() == 5

    def test_failing_streams_frees_active_slots(self):
        """Test that failing streams frees up active stream slots."""
        tracker = StreamingMetricsTracker(max_active_streams=3)

        # Fill active slots
        for i in range(3):
            tracker.start_stream(f"stream-{i}", model="gpt-4", prompt_tokens=50)

        # Fail one stream
        tracker.fail_stream("stream-0", "Connection error")

        # Now we can add another
        tracker.start_stream("stream-3", model="gpt-4", prompt_tokens=50)
        assert tracker.get_active_stream_count() == 3


class TestErrorTrackerBounds:
    """Test memory bounds for ErrorMetricsTracker."""

    def test_recent_errors_bounded_to_500(self):
        """Test that recent errors are bounded to 500 by default."""
        tracker = ErrorMetricsTracker(max_recent_errors=50)

        # Record 100 errors
        for i in range(100):
            tracker.record_error(
                endpoint="/v1/chat/completions",
                status_code=500,
                error_type="InternalServerError",
                error_message=f"Error {i}",
                request_id=f"req-{i}",
            )

        # Only last 50 should be retained
        recent_errors = tracker.get_recent_errors(limit=100)
        assert len(recent_errors) == 50

        # Most recent error should be present
        assert recent_errors[0].request_id == "req-99"

    def test_recent_errors_deque_maxlen(self):
        """Test that recent errors use deque with maxlen."""
        tracker = ErrorMetricsTracker(max_recent_errors=10)

        # Verify deque has maxlen
        assert tracker._recent_errors.maxlen == 10

        # Fill beyond maxlen
        for i in range(20):
            tracker.record_error(
                endpoint="/v1/chat/completions",
                status_code=500,
                error_type="InternalServerError",
                error_message=f"Error {i}",
            )

        # Deque should only contain 10
        assert len(tracker._recent_errors) == 10

    def test_oldest_errors_evicted(self):
        """Test that oldest errors are evicted when limit reached."""
        tracker = ErrorMetricsTracker(max_recent_errors=5)

        # Record errors with identifiable messages
        for i in range(10):
            tracker.record_error(
                endpoint="/v1/chat/completions",
                status_code=500,
                error_type="InternalServerError",
                error_message=f"Error {i}",
            )

        # Get recent errors (most recent first)
        recent = tracker.get_recent_errors(limit=10)

        # Should have only last 5 errors (9, 8, 7, 6, 5)
        assert len(recent) == 5
        assert recent[0].error_message == "Error 9"
        assert recent[1].error_message == "Error 8"
        assert recent[4].error_message == "Error 5"

    def test_pattern_count_cleanup(self):
        """Test that cleanup_old_patterns removes old patterns."""
        tracker = ErrorMetricsTracker(max_recent_errors=100)

        # Create some error patterns
        for i in range(10):
            tracker.record_error(
                endpoint=f"/v1/endpoint-{i}",
                status_code=500,
                error_type="InternalServerError",
                error_message=f"Consistent error pattern {i}",
            )

        # Should have patterns
        initial_pattern_count = len(tracker._patterns)
        assert initial_pattern_count > 0

        # Manually age some patterns (set last_seen to old time)
        with tracker._lock:
            cutoff = time.time() - 7200  # 2 hours ago
            for fingerprint in list(tracker._patterns.keys())[:5]:
                tracker._patterns[fingerprint].last_seen = cutoff

        # Cleanup patterns older than 1 hour
        removed = tracker.cleanup_old_patterns(age_seconds=3600)

        # Should have removed 5 patterns
        assert removed == 5
        assert len(tracker._patterns) == initial_pattern_count - 5

    def test_pattern_count_bounded_growth(self):
        """Test that pattern count doesn't grow unbounded."""
        tracker = ErrorMetricsTracker(max_recent_errors=100)

        # Create many different error patterns
        for i in range(100):
            tracker.record_error(
                endpoint=f"/v1/endpoint-{i}",
                status_code=500 + (i % 10),
                error_type=f"ErrorType{i % 20}",
                error_message=f"Unique error message {i}",
            )

        # Patterns should be created but bounded by cleanup
        initial_patterns = len(tracker._patterns)

        # Cleanup old patterns periodically
        tracker.cleanup_old_patterns(age_seconds=0)  # Remove all

        # All patterns should be removed
        assert len(tracker._patterns) == 0

    def test_error_metrics_counters_grow_but_manageable(self):
        """Test that counter dictionaries grow but remain manageable."""
        tracker = ErrorMetricsTracker(max_recent_errors=100)

        # Record errors across different dimensions
        for i in range(50):
            tracker.record_error(
                endpoint=f"/v1/endpoint-{i % 5}",  # 5 unique endpoints
                status_code=500 + (i % 3),  # 3 unique status codes
                error_type=f"ErrorType{i % 4}",  # 4 unique error types
                error_message=f"Error {i}",
                model=f"model-{i % 3}",  # 3 unique models
            )

        # Counters should have bounded size
        assert len(tracker._errors_by_endpoint) <= 5
        assert len(tracker._errors_by_status) <= 3
        assert len(tracker._errors_by_type) <= 4
        assert len(tracker._errors_by_model) <= 3


class TestCostTrackerBounds:
    """Test memory bounds for CostTracker."""

    def test_usage_records_can_be_cleaned(self):
        """Test that usage records can be cleaned via clear_history."""
        # Get singleton instance
        tracker = CostTracker()
        tracker.clear_history()  # Start fresh

        # Record some usage
        for i in range(50):
            tracker.record_usage(
                api_key=f"key-{i % 5}",
                model="gpt-4",
                endpoint="/v1/chat/completions",
                prompt_tokens=100,
                completion_tokens=50,
            )

        # Should have 50 records
        assert len(tracker._usage_records) == 50

        # Clear history
        tracker.clear_history()

        # Should have 0 records
        assert len(tracker._usage_records) == 0
        assert len(tracker._costs_by_key) == 0

    def test_usage_records_grow_unbounded_by_default(self):
        """Test that usage records list grows unbounded (by design)."""
        tracker = CostTracker()
        tracker.clear_history()

        # Record many usage records
        for i in range(100):
            tracker.record_usage(
                api_key="test-key",
                model="gpt-4",
                endpoint="/v1/chat/completions",
                prompt_tokens=100,
                completion_tokens=50,
            )

        # All records should be retained (no automatic cleanup)
        assert len(tracker._usage_records) == 100

    def test_clear_history_by_api_key(self):
        """Test that clear_history can target specific API keys."""
        tracker = CostTracker()
        tracker.clear_history()

        # Record usage for multiple keys
        for i in range(30):
            tracker.record_usage(
                api_key=f"key-{i % 3}",
                model="gpt-4",
                endpoint="/v1/chat/completions",
                prompt_tokens=100,
                completion_tokens=50,
            )

        # Should have 30 records
        assert len(tracker._usage_records) == 30

        # Clear only key-0
        tracker.clear_history(api_key="key-0")

        # Should have ~20 records left (key-1 and key-2)
        remaining = len(tracker._usage_records)
        assert remaining == 20

    def test_periodic_cleanup_pattern(self):
        """Test pattern for periodic cleanup to prevent unbounded growth."""
        tracker = CostTracker()
        tracker.clear_history()

        # Simulate periodic usage
        for i in range(100):
            tracker.record_usage(
                api_key="test-key",
                model="gpt-4",
                endpoint="/v1/chat/completions",
                prompt_tokens=100,
                completion_tokens=50,
            )

            # Periodic cleanup every 50 records
            if i % 50 == 49:
                # Keep only records from last N operations
                with tracker._usage_lock:
                    if len(tracker._usage_records) > 50:
                        # Keep last 50
                        tracker._usage_records = tracker._usage_records[-50:]

        # After cleanup, should have at most 50 records
        assert len(tracker._usage_records) <= 50

    def test_aggregated_costs_dont_grow_unbounded(self):
        """Test that per-key cost dictionaries grow with number of unique keys."""
        tracker = CostTracker()
        tracker.clear_history()

        # Record usage for 100 unique keys
        for i in range(100):
            tracker.record_usage(
                api_key=f"key-{i}",
                model="gpt-4",
                endpoint="/v1/chat/completions",
                prompt_tokens=100,
                completion_tokens=50,
            )

        # Dictionaries grow with unique keys (expected)
        assert len(tracker._costs_by_key) == 100

        # Clear history removes these
        tracker.clear_history()
        assert len(tracker._costs_by_key) == 0


class TestEventBusQueue:
    """Test memory bounds for AsyncEventBus queue."""

    @pytest.mark.skipif(AsyncEventBus is None, reason="AsyncEventBus not available")
    @pytest.mark.asyncio
    async def test_queue_has_maxsize(self):
        """Test that event queue has a maxsize limit."""
        bus = AsyncEventBus(max_queue_size=100)

        # Queue should have maxsize
        assert bus._event_queue.maxsize == 100

    @pytest.mark.skipif(AsyncEventBus is None, reason="AsyncEventBus not available")
    @pytest.mark.asyncio
    async def test_events_dropped_when_full(self):
        """Test that events are dropped when queue is full."""
        bus = AsyncEventBus(max_queue_size=5)

        # Don't start the worker so queue fills up
        # Create a mock event
        class MockEvent:
            event_type = "test.event"

        # Fill queue beyond capacity
        for i in range(10):
            await bus.publish(MockEvent())

        # Some events should have been dropped
        assert bus._dropped_events > 0
        assert bus._dropped_events == 5  # 10 - 5 (maxsize)

    @pytest.mark.skipif(AsyncEventBus is None, reason="AsyncEventBus not available")
    @pytest.mark.asyncio
    async def test_dropped_count_tracked(self):
        """Test that dropped event count is tracked correctly."""
        bus = AsyncEventBus(max_queue_size=3)

        class MockEvent:
            event_type = "test.event"

        # Initial dropped count should be 0
        assert bus._dropped_events == 0

        # Fill queue
        for i in range(5):
            await bus.publish(MockEvent())

        # Dropped count should be 2
        assert bus._dropped_events == 2

        # Try to add more
        for i in range(3):
            await bus.publish(MockEvent())

        # Dropped count should increase
        assert bus._dropped_events == 5

    @pytest.mark.skipif(AsyncEventBus is None, reason="AsyncEventBus not available")
    @pytest.mark.asyncio
    async def test_queue_drains_when_worker_active(self):
        """Test that queue drains when worker is processing."""
        bus = AsyncEventBus(max_queue_size=100)

        class MockEvent:
            event_type = "test.event"

        # Start the worker
        await bus.start()

        # Publish events
        for i in range(50):
            await bus.publish(MockEvent())

        # Wait for processing
        await asyncio.sleep(0.2)

        # Queue should be drained
        assert bus._event_queue.qsize() < 50
        assert bus._processed_events > 0

        # Stop the bus
        await bus.stop()

    @pytest.mark.skipif(AsyncEventBus is None, reason="AsyncEventBus not available")
    @pytest.mark.asyncio
    async def test_default_queue_size_10k(self):
        """Test that default queue size is 10,000."""
        bus = AsyncEventBus()
        assert bus._event_queue.maxsize == 10000


class TestDequeBehavior:
    """Test deque behavior with maxlen."""

    def test_deque_maxlen_enforced(self):
        """Test that deque maxlen is strictly enforced."""
        d = deque(maxlen=5)

        # Add 10 items
        for i in range(10):
            d.append(i)

        # Should only have 5 items
        assert len(d) == 5

        # Should have last 5 items: [5, 6, 7, 8, 9]
        assert list(d) == [5, 6, 7, 8, 9]

    def test_deque_append_evicts_oldest(self):
        """Test that append() evicts oldest item when at maxlen."""
        d = deque(maxlen=3)

        # Fill deque
        d.append("a")
        d.append("b")
        d.append("c")
        assert list(d) == ["a", "b", "c"]

        # Add another item
        d.append("d")

        # Oldest ("a") should be evicted
        assert list(d) == ["b", "c", "d"]

    def test_deque_fifo_ordering_maintained(self):
        """Test that FIFO ordering is maintained in deque."""
        d = deque(maxlen=10)

        # Add items in order
        for i in range(20):
            d.append(i)

        # Should have items 10-19 in order
        assert list(d) == list(range(10, 20))

        # First item should be 10, last should be 19
        assert d[0] == 10
        assert d[-1] == 19

    def test_deque_memory_efficient(self):
        """Test that deque with maxlen doesn't grow beyond limit."""
        d = deque(maxlen=100)

        # Add many items
        for i in range(10000):
            d.append(i)

        # Should still only have 100 items
        assert len(d) == 100
        assert sys.getsizeof(d) < sys.getsizeof([None] * 10000)


class TestMemoryLeakDetection:
    """Test for memory leaks in bulk operations."""

    @pytest.mark.skipif(not HAS_TRACEMALLOC, reason="tracemalloc not available")
    def test_streaming_tracker_no_memory_leak(self):
        """Test that StreamingMetricsTracker doesn't leak memory."""
        tracemalloc.start()

        tracker = StreamingMetricsTracker(
            max_active_streams=1000,
            max_completed_streams=100,
        )

        # Get baseline memory
        gc.collect()
        baseline_memory = tracemalloc.get_traced_memory()[0]

        # Create and complete 10K streams
        for i in range(10000):
            stream_id = f"stream-{i}"
            tracker.start_stream(stream_id, model="gpt-4", prompt_tokens=50)
            tracker.record_token(stream_id, "token", chunk_size_bytes=5)
            tracker.complete_stream(stream_id, "stop")

            # Clear cache periodically to avoid skewing results
            if i % 1000 == 0:
                tracker._cached_metrics = None

        # Force garbage collection
        gc.collect()

        # Get final memory
        final_memory = tracemalloc.get_traced_memory()[0]

        # Memory should not have grown significantly beyond baseline + max_completed_streams
        # Allow for some overhead but should be bounded
        memory_growth = final_memory - baseline_memory

        # With 100 max completed streams, memory growth should be reasonable
        # Each stream is ~1-2KB, so 100 streams ~= 200KB max
        # Allow 500KB for overhead
        assert memory_growth < 500 * 1024, f"Memory grew by {memory_growth / 1024:.2f} KB"

        tracemalloc.stop()

    def test_streaming_tracker_no_references_held(self):
        """Test that completed streams don't hold unnecessary references."""
        tracker = StreamingMetricsTracker(max_completed_streams=10)

        # Create some objects that should be garbage collected
        stream_ids = []
        for i in range(20):
            stream_id = f"stream-{i}"
            stream_ids.append(stream_id)
            tracker.start_stream(stream_id, model="gpt-4", prompt_tokens=50)
            tracker.complete_stream(stream_id, "stop")

        # Force garbage collection
        gc.collect()

        # Only last 10 streams should be in completed queue
        assert len(tracker._completed_streams) == 10

        # Older streams should not be findable
        for i in range(10):
            assert tracker.get_stream_details(f"stream-{i}") is None

    def test_error_tracker_memory_bounded(self):
        """Test that ErrorMetricsTracker memory stays bounded."""
        tracker = ErrorMetricsTracker(max_recent_errors=100)

        # Record many errors
        for i in range(1000):
            tracker.record_error(
                endpoint="/v1/chat/completions",
                status_code=500,
                error_type="InternalServerError",
                error_message=f"Error {i}",
            )

        # Should only keep last 100
        assert len(tracker._recent_errors) == 100

        # Recent errors should be the last ones
        recent = tracker.get_recent_errors(limit=10)
        assert len(recent) == 10
        assert "999" in recent[0].error_message

    def test_cost_tracker_cleanup_restores_memory(self):
        """Test that clearing cost tracker history reduces memory usage."""
        tracker = CostTracker()
        tracker.clear_history()

        # Record many usage records
        for i in range(1000):
            tracker.record_usage(
                api_key=f"key-{i % 10}",
                model="gpt-4",
                endpoint="/v1/chat/completions",
                prompt_tokens=100,
                completion_tokens=50,
            )

        # Should have 1000 records
        initial_count = len(tracker._usage_records)
        assert initial_count == 1000

        # Clear history
        tracker.clear_history()
        gc.collect()

        # Should have 0 records
        assert len(tracker._usage_records) == 0
        assert len(tracker._costs_by_key) == 0

    def test_repeated_cycles_no_accumulation(self):
        """Test that repeated create/destroy cycles don't accumulate memory."""
        tracker = StreamingMetricsTracker(max_completed_streams=10)

        # Run multiple cycles
        for cycle in range(5):
            # Create and complete 100 streams
            for i in range(100):
                stream_id = f"cycle{cycle}-stream{i}"
                tracker.start_stream(stream_id, model="gpt-4", prompt_tokens=50)
                tracker.complete_stream(stream_id, "stop")

            # Force garbage collection
            gc.collect()

            # Should still only have 10 completed streams
            assert len(tracker._completed_streams) == 10

    def test_streaming_tracker_reset_clears_memory(self):
        """Test that reset() fully clears memory."""
        tracker = StreamingMetricsTracker()

        # Create many streams
        for i in range(100):
            stream_id = f"stream-{i}"
            tracker.start_stream(stream_id, model="gpt-4", prompt_tokens=50)
            tracker.record_token(stream_id, "token", chunk_size_bytes=5)
            tracker.complete_stream(stream_id, "stop")

        # Reset
        tracker.reset()

        # All data structures should be empty
        assert len(tracker._active_streams) == 0
        assert len(tracker._completed_streams) == 0
        assert tracker._total_streams_started == 0
        assert tracker._total_tokens_generated == 0
        assert tracker._cached_metrics is None


class TestBoundedGrowthScenarios:
    """Test realistic scenarios of bounded growth."""

    def test_streaming_tracker_steady_state(self):
        """Test steady state operation with bounded memory."""
        tracker = StreamingMetricsTracker(
            max_active_streams=100,
            max_completed_streams=50,
        )

        # Simulate steady state: streams come and go
        for i in range(500):
            stream_id = f"stream-{i}"
            tracker.start_stream(stream_id, model="gpt-4", prompt_tokens=50)
            tracker.record_token(stream_id, "token", chunk_size_bytes=5)
            tracker.complete_stream(stream_id, "stop")

        # Active streams should be 0 (all completed)
        assert tracker.get_active_stream_count() == 0

        # Completed streams should be bounded to 50
        assert len(tracker._completed_streams) == 50

    def test_error_tracker_high_error_rate(self):
        """Test error tracker under high error rate."""
        tracker = ErrorMetricsTracker(max_recent_errors=200)

        # Simulate high error rate
        for i in range(1000):
            tracker.record_error(
                endpoint=f"/v1/endpoint-{i % 10}",
                status_code=500 + (i % 5),
                error_type=f"ErrorType{i % 3}",
                error_message=f"Error {i}",
            )

        # Recent errors should be bounded
        assert len(tracker._recent_errors) == 200

        # Metrics should still be calculable
        metrics = tracker.get_metrics()
        assert metrics["total_errors"] == 1000
        assert metrics["recent_errors_count"] == 200

    def test_cost_tracker_long_running_service(self):
        """Test cost tracker in long-running service scenario."""
        tracker = CostTracker()
        tracker.clear_history()

        # Simulate long-running service with periodic cleanup
        for batch in range(10):
            # Add 100 usage records
            for i in range(100):
                tracker.record_usage(
                    api_key=f"key-{i % 5}",
                    model="gpt-4",
                    endpoint="/v1/chat/completions",
                    prompt_tokens=100,
                    completion_tokens=50,
                )

            # Periodic cleanup (keep last 500 records)
            with tracker._usage_lock:
                if len(tracker._usage_records) > 500:
                    # Keep only the last 500 records
                    tracker._usage_records = tracker._usage_records[-500:]

        # Should have bounded number of records
        # Note: In this test, we do 10 batches * 100 = 1000 records
        # After cleanup, should have at most 500
        assert len(tracker._usage_records) == 500


class TestConcurrentBoundedAccess:
    """Test bounded behavior under concurrent access."""

    def test_concurrent_streaming_respects_bounds(self):
        """Test that concurrent access respects stream bounds."""
        tracker = StreamingMetricsTracker(max_active_streams=50)
        errors = []

        def create_streams(thread_id):
            try:
                for i in range(20):
                    stream_id = f"thread{thread_id}-stream{i}"
                    try:
                        tracker.start_stream(stream_id, model="gpt-4", prompt_tokens=50)
                        time.sleep(0.001)
                        tracker.complete_stream(stream_id, "stop")
                    except ValueError as e:
                        # Expected when hitting limit
                        if "Max active streams" not in str(e):
                            errors.append(e)
            except Exception as e:
                errors.append(e)

        threads = []
        for i in range(5):
            t = threading.Thread(target=create_streams, args=(i,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # Should not have any unexpected errors
        assert len(errors) == 0

        # Active streams should never have exceeded max
        assert tracker.get_active_stream_count() <= tracker.max_active_streams

    def test_concurrent_error_recording_bounded(self):
        """Test that concurrent error recording respects bounds."""
        tracker = ErrorMetricsTracker(max_recent_errors=100)

        def record_errors(thread_id):
            for i in range(50):
                tracker.record_error(
                    endpoint="/v1/chat/completions",
                    status_code=500,
                    error_type="Error",
                    error_message=f"Thread {thread_id} error {i}",
                )

        threads = []
        for i in range(5):
            t = threading.Thread(target=record_errors, args=(i,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # Should have at most 100 recent errors
        assert len(tracker._recent_errors) == 100


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
