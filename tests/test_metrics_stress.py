"""
Stress Tests for Metrics Systems.

Tests metrics performance under heavy load:
- 1000+ concurrent requests
- Thread safety verification
- Memory leak detection
- Deadlock prevention
- Accuracy under load
"""

import asyncio
import gc
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import Mock

import psutil
import pytest

from fakeai.config import AppConfig
from fakeai.dcgm_metrics import DCGMMetricsSimulator
from fakeai.dynamo_metrics import DynamoMetricsCollector
from fakeai.fakeai_service import FakeAIService
from fakeai.kv_cache import KVCacheMetrics, SmartRouter
from fakeai.metrics import MetricsTracker
from fakeai.metrics_aggregator import MetricsAggregator
from fakeai.models import ChatCompletionRequest, Message, Role


@pytest.fixture
def config():
    """Create test config with minimal delays."""
    return AppConfig(
        response_delay=0.0,
        min_delay=0.0,
        max_delay=0.0,
    )


@pytest.fixture
def metrics_tracker():
    """Create fresh MetricsTracker."""
    # Get the singleton instance
    tracker = MetricsTracker()
    # Clear all metrics (MetricsTracker stores metrics in _metrics dict)
    for metric_type in tracker._metrics.values():
        metric_type.clear()
    tracker._streaming_metrics.clear()
    tracker._completed_streams.clear()
    tracker._failed_streams.clear()
    return tracker


@pytest.fixture
def kv_metrics():
    """Create KV cache metrics."""
    return KVCacheMetrics()


@pytest.fixture
def dcgm_metrics():
    """Create DCGM metrics simulator."""
    return DCGMMetricsSimulator(num_gpus=4, gpu_model="H100-80GB")


@pytest.fixture
def dynamo_metrics():
    """Create Dynamo metrics collector."""
    return DynamoMetricsCollector(window_size=300)


@pytest.fixture
def aggregator(metrics_tracker, kv_metrics, dcgm_metrics, dynamo_metrics):
    """Create metrics aggregator with all sources."""
    return MetricsAggregator(
        metrics_tracker=metrics_tracker,
        kv_metrics=kv_metrics,
        dcgm_metrics=dcgm_metrics,
        dynamo_metrics=dynamo_metrics,
    )


@pytest.fixture
async def service(config):
    """Create FakeAI service."""
    return FakeAIService(config)


def get_memory_usage():
    """Get current process memory usage in MB."""
    process = psutil.Process()
    return process.memory_info().rss / 1024 / 1024


@pytest.mark.asyncio
@pytest.mark.stress
class TestConcurrentLoad:
    """Test metrics under heavy concurrent load."""

    async def test_1000_concurrent_requests(self, service, metrics_tracker):
        """Handle 1000 concurrent requests without errors."""
        request_count = 1000

        async def make_request(i):
            request = ChatCompletionRequest(
                model="openai/gpt-oss-120b",
                messages=[Message(role=Role.USER, content=f"Request {i}")],
                max_tokens=20,
            )
            return await service.create_chat_completion(request)

        # Create all tasks
        tasks = [make_request(i) for i in range(request_count)]

        # Execute concurrently
        start = time.time()
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        duration = time.time() - start

        # Count successes and failures
        successes = sum(1 for r in responses if not isinstance(r, Exception))
        failures = sum(1 for r in responses if isinstance(r, Exception))

        print(f"\nCompleted {request_count} requests in {duration:.2f}s")
        print(f"Successes: {successes}, Failures: {failures}")
        print(f"Rate: {request_count / duration:.2f} req/s")

        # Should have high success rate
        assert successes >= request_count * 0.95  # At least 95% success

        # Verify metrics tracked
        await asyncio.sleep(0.2)
        core_metrics = metrics_tracker.get_metrics()
        assert len(core_metrics["requests"]) > 0

    async def test_2000_concurrent_with_streaming(self, service, metrics_tracker):
        """Handle 2000 concurrent requests including streaming."""
        request_count = 2000

        async def make_request(i):
            is_streaming = i % 3 == 0  # Every 3rd request is streaming
            request = ChatCompletionRequest(
                model="openai/gpt-oss-120b",
                messages=[Message(role=Role.USER, content=f"Query {i}")],
                max_tokens=20,
                stream=is_streaming,
            )

            if is_streaming:
                # Consume stream
                try:
                    async for chunk in await service.create_chat_completion(request):
                        pass
                    return "streaming_success"
                except Exception as e:
                    return e
            else:
                return await service.create_chat_completion(request)

        # Execute all requests
        tasks = [make_request(i) for i in range(request_count)]

        start = time.time()
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        duration = time.time() - start

        successes = sum(1 for r in responses if not isinstance(r, Exception))

        print(f"\nCompleted {request_count} mixed requests in {duration:.2f}s")
        print(f"Successes: {successes}")
        print(f"Rate: {request_count / duration:.2f} req/s")

        # Should have high success rate
        assert successes >= request_count * 0.90

    async def test_sustained_load_5_minutes(self, service, metrics_tracker):
        """Sustained load test for 30 seconds (simulating 5 min behavior)."""
        duration_seconds = 30  # Shortened for CI
        target_rps = 20  # Requests per second

        request_count = 0
        start_time = time.time()

        while time.time() - start_time < duration_seconds:
            # Send batch of requests
            batch_size = 10
            tasks = []
            for i in range(batch_size):
                request = ChatCompletionRequest(
                    model="openai/gpt-oss-120b",
                    messages=[Message(role=Role.USER, content=f"Sustained query {i}")],
                    max_tokens=20,
                )
                tasks.append(service.create_chat_completion(request))

            responses = await asyncio.gather(*tasks, return_exceptions=True)
            request_count += len(responses)

            # Maintain target rate
            await asyncio.sleep(batch_size / target_rps)

        total_duration = time.time() - start_time
        actual_rps = request_count / total_duration

        print(f"\nSustained load: {request_count} requests in {total_duration:.2f}s")
        print(f"Actual rate: {actual_rps:.2f} req/s (target: {target_rps} req/s)")

        # Verify metrics still working
        core_metrics = metrics_tracker.get_metrics()
        assert len(core_metrics["requests"]) > 0

    async def test_burst_traffic_pattern(self, service, metrics_tracker):
        """Test burst traffic pattern (idle -> spike -> idle)."""
        # Initial burst
        burst1 = []
        for i in range(200):
            request = ChatCompletionRequest(
                model="openai/gpt-oss-120b",
                messages=[Message(role=Role.USER, content=f"Burst1 {i}")],
                max_tokens=10,
            )
            burst1.append(service.create_chat_completion(request))

        responses1 = await asyncio.gather(*burst1, return_exceptions=True)
        success1 = sum(1 for r in responses1 if not isinstance(r, Exception))

        # Idle period
        await asyncio.sleep(0.5)

        # Second burst
        burst2 = []
        for i in range(300):
            request = ChatCompletionRequest(
                model="openai/gpt-oss-120b",
                messages=[Message(role=Role.USER, content=f"Burst2 {i}")],
                max_tokens=10,
            )
            burst2.append(service.create_chat_completion(request))

        responses2 = await asyncio.gather(*burst2, return_exceptions=True)
        success2 = sum(1 for r in responses2 if not isinstance(r, Exception))

        print(f"\nBurst 1: {success1}/200 successful")
        print(f"Burst 2: {success2}/300 successful")

        # Both bursts should succeed
        assert success1 >= 190  # 95%+
        assert success2 >= 285  # 95%+

        # Metrics should handle both bursts
        await asyncio.sleep(0.2)
        core_metrics = metrics_tracker.get_metrics()
        assert len(core_metrics["requests"]) > 0


@pytest.mark.asyncio
@pytest.mark.stress
class TestThreadSafety:
    """Test thread safety of metrics systems."""

    async def test_no_deadlocks_concurrent_reads_writes(
        self, service, metrics_tracker, kv_metrics, dynamo_metrics
    ):
        """No deadlocks with concurrent reads and writes."""
        stop_event = threading.Event()
        errors = []

        def reader_thread():
            """Continuously read metrics."""
            try:
                while not stop_event.is_set():
                    metrics_tracker.get_metrics()
                    kv_metrics.get_stats()
                    dynamo_metrics.get_stats_dict()
                    time.sleep(0.001)
            except Exception as e:
                errors.append(("reader", e))

        def writer_thread():
            """Continuously write metrics."""
            try:
                while not stop_event.is_set():
                    metrics_tracker.track_request("/v1/test")
                    metrics_tracker.track_response("/v1/test", 0.1, 100)
                    kv_metrics.record_cache_lookup("/v1/test", 100, 50)
                    time.sleep(0.001)
            except Exception as e:
                errors.append(("writer", e))

        # Start reader/writer threads
        threads = []
        for i in range(5):
            threads.append(threading.Thread(target=reader_thread))
            threads.append(threading.Thread(target=writer_thread))

        for t in threads:
            t.start()

        # Run for 5 seconds
        await asyncio.sleep(5)

        # Stop threads
        stop_event.set()
        for t in threads:
            t.join(timeout=2)

        # Check for errors
        if errors:
            for source, error in errors:
                print(f"Error in {source}: {error}")
            pytest.fail(f"Thread safety issues detected: {len(errors)} errors")

    async def test_concurrent_prometheus_export(self, aggregator):
        """Concurrent Prometheus exports don't deadlock."""

        def export_metrics():
            for _ in range(50):
                aggregator.export_prometheus()
                time.sleep(0.01)

        threads = [threading.Thread(target=export_metrics) for _ in range(10)]

        start = time.time()
        for t in threads:
            t.start()

        for t in threads:
            t.join(timeout=10)

        duration = time.time() - start

        # Should complete in reasonable time (no deadlocks)
        assert duration < 15

    async def test_metrics_aggregation_thread_safe(
        self, service, aggregator, metrics_tracker
    ):
        """Metrics aggregation is thread-safe during concurrent requests."""

        async def make_requests():
            for i in range(50):
                request = ChatCompletionRequest(
                    model="openai/gpt-oss-120b",
                    messages=[Message(role=Role.USER, content=f"Test {i}")],
                    max_tokens=10,
                )
                await service.create_chat_completion(request)

        def read_aggregated_metrics():
            for _ in range(100):
                aggregator.get_unified_metrics()
                time.sleep(0.01)

        # Start metric reader thread
        reader = threading.Thread(target=read_aggregated_metrics)
        reader.start()

        # Make requests concurrently
        await make_requests()

        # Wait for reader
        reader.join(timeout=5)

        # No deadlock = success
        assert not reader.is_alive()


@pytest.mark.asyncio
@pytest.mark.stress
class TestMemoryLeaks:
    """Test for memory leaks in metrics collection."""

    async def test_no_memory_leak_continuous_requests(self, service, metrics_tracker):
        """Memory usage should stabilize, not continuously grow."""
        gc.collect()
        initial_memory = get_memory_usage()

        # Warmup
        for i in range(100):
            request = ChatCompletionRequest(
                model="openai/gpt-oss-120b",
                messages=[Message(role=Role.USER, content=f"Warmup {i}")],
                max_tokens=10,
            )
            await service.create_chat_completion(request)

        gc.collect()
        baseline_memory = get_memory_usage()

        # Run sustained load
        for i in range(500):
            request = ChatCompletionRequest(
                model="openai/gpt-oss-120b",
                messages=[Message(role=Role.USER, content=f"Test {i}")],
                max_tokens=10,
            )
            await service.create_chat_completion(request)

        gc.collect()
        final_memory = get_memory_usage()

        memory_growth = final_memory - baseline_memory
        print(
            f"\nMemory: initial={initial_memory:.1f}MB, "
            f"baseline={baseline_memory:.1f}MB, final={final_memory:.1f}MB"
        )
        print(f"Growth after 500 requests: {memory_growth:.1f}MB")

        # Memory growth should be reasonable (< 50MB for 500 requests)
        assert memory_growth < 50, f"Possible memory leak: {memory_growth:.1f}MB growth"

    async def test_metrics_window_memory_bounded(
        self, service, metrics_tracker, kv_metrics
    ):
        """Metrics windows should not grow unbounded."""
        # Generate lots of data points
        for i in range(5000):
            metrics_tracker.track_request("/v1/test")
            metrics_tracker.track_response("/v1/test", 0.1, 100)
            kv_metrics.record_cache_lookup("/v1/test", 100, 50)

        gc.collect()
        memory_after_5k = get_memory_usage()

        # Generate another 5k data points
        for i in range(5000):
            metrics_tracker.track_request("/v1/test")
            metrics_tracker.track_response("/v1/test", 0.1, 100)
            kv_metrics.record_cache_lookup("/v1/test", 100, 50)

        gc.collect()
        memory_after_10k = get_memory_usage()

        growth = memory_after_10k - memory_after_5k
        print(f"\nMemory growth from 5k to 10k data points: {growth:.1f}MB")

        # Second 5k should not add much memory (due to sliding windows)
        assert growth < 20, "Metrics windows not properly bounded"

    async def test_streaming_metrics_cleanup(self, service, metrics_tracker):
        """Streaming metrics should be cleaned up after completion."""
        gc.collect()
        baseline_memory = get_memory_usage()

        # Create and complete many streams
        for i in range(200):
            request = ChatCompletionRequest(
                model="openai/gpt-oss-120b",
                messages=[Message(role=Role.USER, content=f"Stream {i}")],
                max_tokens=20,
                stream=True,
            )

            # Consume stream
            async for chunk in await service.create_chat_completion(request):
                pass

        gc.collect()
        final_memory = get_memory_usage()

        growth = final_memory - baseline_memory
        print(f"\nMemory growth after 200 streams: {growth:.1f}MB")

        # Memory growth should be minimal
        assert growth < 30


@pytest.mark.asyncio
@pytest.mark.stress
class TestMetricAccuracy:
    """Test metric accuracy under load."""

    async def test_request_count_accuracy_under_load(
        self, service, metrics_tracker, dynamo_metrics
    ):
        """Request counts should be accurate even under load."""
        request_count = 500

        # Get initial counts
        initial_dynamo = dynamo_metrics.get_stats_dict()["summary"]["total_requests"]

        # Make exact number of requests
        tasks = []
        for i in range(request_count):
            request = ChatCompletionRequest(
                model="openai/gpt-oss-120b",
                messages=[Message(role=Role.USER, content=f"Accuracy test {i}")],
                max_tokens=10,
            )
            tasks.append(service.create_chat_completion(request))

        responses = await asyncio.gather(*tasks, return_exceptions=True)
        successes = sum(1 for r in responses if not isinstance(r, Exception))

        await asyncio.sleep(0.2)

        # Check final counts
        final_dynamo = dynamo_metrics.get_stats_dict()["summary"]["total_requests"]

        dynamo_delta = final_dynamo - initial_dynamo

        print(f"\nSent: {request_count}, Successes: {successes}")
        print(f"Dynamo delta: {dynamo_delta}")

        # Counts should match successes (within small margin)
        assert abs(dynamo_delta - successes) <= 5

    async def test_token_count_accuracy(self, service, kv_metrics):
        """Token counts should be accurate."""
        # Get initial count
        initial_tokens = kv_metrics.get_stats()["total_tokens_processed"]

        # Make requests with known content
        request_count = 100
        tasks = []
        for i in range(request_count):
            request = ChatCompletionRequest(
                model="openai/gpt-oss-120b",
                messages=[
                    ChatMessage(
                        role="user",
                        content="This is a test message with exactly ten words here now",
                    )
                ],
                max_tokens=10,
            )
            tasks.append(service.create_chat_completion(request))

        await asyncio.gather(*tasks)
        await asyncio.sleep(0.2)

        # Check token count
        final_tokens = kv_metrics.get_stats()["total_tokens_processed"]
        tokens_processed = final_tokens - initial_tokens

        print(f"\nTokens processed for {request_count} requests: {tokens_processed}")

        # Should have processed tokens for all requests
        assert tokens_processed > request_count * 5  # At least 5 tokens per request

    async def test_cache_hit_rate_accuracy(self, service, kv_metrics):
        """Cache hit rate calculation should be accurate."""
        # Make initial request (cache miss)
        request1 = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[
                ChatMessage(
                    role="user",
                    content="What is the capital of France? Please explain.",
                )
            ],
        )
        await service.create_chat_completion(request1)

        # Make similar request (should have some cache hit)
        request2 = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[
                ChatMessage(
                    role="user",
                    content="What is the capital of Germany? Please explain.",
                )
            ],
        )
        await service.create_chat_completion(request2)

        await asyncio.sleep(0.1)

        # Check cache metrics
        stats = kv_metrics.get_stats()
        hit_rate = stats["cache_hit_rate"]

        print(f"\nCache hits: {stats['total_cache_hits']}")
        print(f"Cache misses: {stats['total_cache_misses']}")
        print(f"Hit rate: {hit_rate}%")

        # Hit rate should be in valid range
        assert 0 <= hit_rate <= 100


@pytest.mark.asyncio
@pytest.mark.stress
class TestSystemStability:
    """Test system stability under stress."""

    async def test_graceful_degradation_high_load(self, service, metrics_tracker):
        """System should degrade gracefully, not crash."""
        # Extreme load
        request_count = 2000

        async def make_request(i):
            try:
                request = ChatCompletionRequest(
                    model="openai/gpt-oss-120b",
                    messages=[Message(role=Role.USER, content=f"Load {i}")],
                    max_tokens=10,
                )
                return await service.create_chat_completion(request)
            except Exception as e:
                return e

        tasks = [make_request(i) for i in range(request_count)]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # System should handle requests (even if some fail gracefully)
        total_exceptions = sum(1 for r in responses if isinstance(r, Exception))
        success_rate = (request_count - total_exceptions) / request_count * 100

        print(f"\nLoad test: {request_count} requests")
        print(f"Success rate: {success_rate:.1f}%")
        print(f"Exceptions: {total_exceptions}")

        # Should handle at least 50% successfully
        assert success_rate >= 50

    async def test_recovery_after_burst(self, service, metrics_tracker):
        """System should recover after burst."""
        # Initial burst
        burst = []
        for i in range(500):
            request = ChatCompletionRequest(
                model="openai/gpt-oss-120b",
                messages=[Message(role=Role.USER, content=f"Burst {i}")],
                max_tokens=5,
            )
            burst.append(service.create_chat_completion(request))

        await asyncio.gather(*burst, return_exceptions=True)

        # Wait for recovery
        await asyncio.sleep(1)

        # Normal requests should work
        normal_request = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[Message(role=Role.USER, content="Post-burst test")],
        )
        response = await service.create_chat_completion(normal_request)

        # Should succeed
        assert response is not None
        assert response.choices[0].message.content

    async def test_metrics_export_under_load(
        self, service, aggregator, metrics_tracker
    ):
        """Metrics export should work even under load."""

        async def continuous_requests():
            for i in range(200):
                request = ChatCompletionRequest(
                    model="openai/gpt-oss-120b",
                    messages=[Message(role=Role.USER, content=f"Load {i}")],
                    max_tokens=10,
                )
                await service.create_chat_completion(request)
                await asyncio.sleep(0.01)

        # Start load
        load_task = asyncio.create_task(continuous_requests())

        # Try to export metrics during load
        exports_succeeded = 0
        for i in range(20):
            try:
                prom_metrics = aggregator.export_prometheus()
                if len(prom_metrics) > 0:
                    exports_succeeded += 1
            except Exception as e:
                print(f"Export failed: {e}")
            await asyncio.sleep(0.1)

        # Wait for load to finish
        await load_task

        print(f"\nMetric exports during load: {exports_succeeded}/20")

        # Should succeed most of the time
        assert exports_succeeded >= 15


@pytest.mark.asyncio
@pytest.mark.stress
class TestEdgeCases:
    """Test edge cases under stress."""

    async def test_empty_requests_high_volume(self, service, metrics_tracker):
        """Handle high volume of minimal requests."""
        tasks = []
        for i in range(1000):
            request = ChatCompletionRequest(
                model="openai/gpt-oss-120b",
                messages=[Message(role=Role.USER, content="Hi")],
                max_tokens=1,
            )
            tasks.append(service.create_chat_completion(request))

        responses = await asyncio.gather(*tasks, return_exceptions=True)
        successes = sum(1 for r in responses if not isinstance(r, Exception))

        print(f"\nMinimal requests: {successes}/1000 successful")
        assert successes >= 950

    async def test_large_requests_concurrent(self, service, metrics_tracker):
        """Handle concurrent large requests."""
        large_content = " ".join([f"word{i}" for i in range(500)])

        tasks = []
        for i in range(50):
            request = ChatCompletionRequest(
                model="openai/gpt-oss-120b",
                messages=[Message(role=Role.USER, content=large_content)],
                max_tokens=100,
            )
            tasks.append(service.create_chat_completion(request))

        responses = await asyncio.gather(*tasks, return_exceptions=True)
        successes = sum(1 for r in responses if not isinstance(r, Exception))

        print(f"\nLarge requests: {successes}/50 successful")
        assert successes >= 45

    async def test_mixed_workload(self, service, metrics_tracker):
        """Handle mixed workload (chat, embeddings, completions)."""
        tasks = []

        # Mix of different request types
        for i in range(300):
            if i % 3 == 0:
                # Chat
                request = ChatCompletionRequest(
                    model="openai/gpt-oss-120b",
                    messages=[Message(role=Role.USER, content=f"Chat {i}")],
                )
                tasks.append(service.create_chat_completion(request))
            elif i % 3 == 1:
                # Embeddings
                from fakeai.models import EmbeddingRequest

                request = EmbeddingRequest(
                    model="text-embedding-3-large", input=f"Embed {i}"
                )
                tasks.append(service.create_embeddings(request))
            else:
                # Completions
                from fakeai.models import CompletionRequest

                request = CompletionRequest(
                    model="openai/gpt-oss-120b", prompt=f"Complete {i}"
                )
                tasks.append(service.create_completion(request))

        responses = await asyncio.gather(*tasks, return_exceptions=True)
        successes = sum(1 for r in responses if not isinstance(r, Exception))

        print(f"\nMixed workload: {successes}/300 successful")
        assert successes >= 270
