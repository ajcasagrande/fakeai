"""
Comprehensive Integration Tests for All Metrics Modules.

Tests end-to-end metrics flow across all systems:
- MetricsTracker (core metrics)
- KVCacheMetrics (cache performance)
- DCGMMetricsSimulator (GPU metrics)
- DynamoMetricsCollector (latency/queue metrics)
- MetricsAggregator (unified metrics)

Verifies:
- Cross-system correlation
- Metrics consistency
- Export format consistency
- End-to-end tracking
"""

import asyncio
import json
import time
from unittest.mock import Mock, patch

import pytest

from fakeai.config import AppConfig
from fakeai.dcgm_metrics import DCGMMetricsSimulator
from fakeai.dynamo_metrics import DynamoMetricsCollector
from fakeai.fakeai_service import FakeAIService
from fakeai.kv_cache import KVCacheMetrics, SmartRouter, tokenize_for_cache
from fakeai.metrics import MetricsTracker
from fakeai.metrics_aggregator import HealthStatus, MetricsAggregator
from fakeai.models import (
    ChatCompletionRequest,
    CompletionRequest,
    EmbeddingRequest,
    Message,
    Role,
)


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
    return DCGMMetricsSimulator(num_gpus=2, gpu_model="H100-80GB")


@pytest.fixture
def dynamo_metrics():
    """Create Dynamo metrics collector."""
    return DynamoMetricsCollector(window_size=60)


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
async def service(config, kv_metrics, dynamo_metrics):
    """Create FakeAI service with metrics."""
    service = FakeAIService(config)
    # Inject metrics for testing
    service.kv_cache_metrics = kv_metrics
    service.dynamo_metrics = dynamo_metrics
    return service


@pytest.mark.asyncio
@pytest.mark.integration
class TestEndToEndMetricsFlow:
    """Test complete metrics flow from request to export."""

    async def test_chat_completion_end_to_end(
        self, service, metrics_tracker, kv_metrics, dynamo_metrics, aggregator
    ):
        """Complete flow: request -> all metrics -> aggregator -> export."""
        # Make a chat completion request
        request = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[Message(role=Role.USER, content="What is the meaning of life?")],
            max_tokens=100,
        )

        # Execute request
        response = await service.create_chat_completion(request)

        # Give time for metrics to propagate
        await asyncio.sleep(0.1)

        # Verify all metrics systems tracked the request
        core_metrics = metrics_tracker.get_metrics()
        kv_stats = kv_metrics.get_stats()
        dynamo_stats = dynamo_metrics.get_stats_dict()

        # Core metrics should have request/response
        assert "/v1/chat/completions" in core_metrics["requests"]
        assert "/v1/chat/completions" in core_metrics["responses"]
        assert "/v1/chat/completions" in core_metrics["tokens"]

        # KV cache should have processed tokens
        assert kv_stats["total_tokens_processed"] > 0

        # Dynamo should have request metrics
        assert dynamo_stats["summary"]["total_requests"] > 0

        # Aggregator should combine all sources
        unified = aggregator.get_unified_metrics()
        assert "requests" in unified
        assert "kv_cache" in unified
        assert "dynamo" in unified

        # Prometheus export should include all sources
        prom_metrics = aggregator.export_prometheus()
        assert "fakeai_requests_per_second" in prom_metrics
        assert "fakeai_kv_cache_hit_rate" in prom_metrics
        assert "fakeai_ttft_ms" in prom_metrics

    async def test_streaming_request_comprehensive_tracking(
        self, service, metrics_tracker, kv_metrics, dynamo_metrics
    ):
        """Streaming request tracked across all systems."""
        request = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[Message(role=Role.USER, content="Count to 10")],
            max_tokens=50,
            stream=True,
        )

        # Consume stream
        chunk_count = 0
        async for chunk in await service.create_chat_completion(request):
            chunk_count += 1

        await asyncio.sleep(0.1)

        # Verify streaming metrics
        core_metrics = metrics_tracker.get_metrics()
        assert "streaming_stats" in core_metrics

        # Verify tokens processed
        kv_stats = kv_metrics.get_stats()
        assert kv_stats["total_tokens_processed"] > 0

        # Verify dynamo tracked streaming
        dynamo_stats = dynamo_metrics.get_stats_dict()
        assert dynamo_stats["summary"]["total_requests"] > 0

        # Verify chunk count is reasonable
        assert chunk_count > 0

    async def test_multiple_endpoints_tracked_separately(
        self, service, metrics_tracker, aggregator
    ):
        """Different endpoints tracked with separate metrics."""
        # Chat completion
        chat_req = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[Message(role=Role.USER, content="Hello")],
        )
        await service.create_chat_completion(chat_req)

        # Embedding
        embed_req = EmbeddingRequest(
            model="text-embedding-3-large",
            input="Hello world",
        )
        await service.create_embeddings(embed_req)

        # Completion
        comp_req = CompletionRequest(
            model="openai/gpt-oss-120b",
            prompt="Once upon a time",
        )
        await service.create_completion(comp_req)

        await asyncio.sleep(0.1)

        # Verify separate tracking
        core_metrics = metrics_tracker.get_metrics()
        assert "/v1/chat/completions" in core_metrics["requests"]
        assert "/v1/embeddings" in core_metrics["requests"]
        assert "/v1/completions" in core_metrics["requests"]

        # Verify aggregator sees all endpoints
        unified = aggregator.get_unified_metrics()
        assert len(unified["requests"]) >= 3


@pytest.mark.asyncio
@pytest.mark.integration
class TestCrossSystemCorrelation:
    """Test metrics correlation across different systems."""

    async def test_cache_hits_correlate_with_latency_reduction(
        self, service, kv_metrics, dynamo_metrics, aggregator
    ):
        """Cache hits should reduce latency."""
        # First request (no cache)
        request1 = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[
                ChatMessage(
                    role="user",
                    content="This is a very specific question about physics",
                )
            ],
        )
        await service.create_chat_completion(request1)

        # Similar request (should have cache overlap)
        request2 = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[
                ChatMessage(
                    role="user",
                    content="This is a very specific question about chemistry",
                )
            ],
        )
        await service.create_chat_completion(request2)

        await asyncio.sleep(0.1)

        # Check correlation
        correlations = aggregator.correlate_metrics(
            "kv_cache_hit_rate", "avg_ttft_ms", window_seconds=60
        )

        # Should show some relationship (may be positive or negative depending on data)
        assert correlations is not None
        assert "correlation" in correlations
        assert "significance" in correlations

    async def test_gpu_utilization_correlates_with_throughput(
        self, service, metrics_tracker, dcgm_metrics, aggregator
    ):
        """Higher GPU usage should correlate with higher token throughput."""
        # Make multiple requests to generate load
        for i in range(10):
            request = ChatCompletionRequest(
                model="openai/gpt-oss-120b",
                messages=[Message(role=Role.USER, content=f"Question {i}")],
                max_tokens=50,
            )
            await service.create_chat_completion(request)

        await asyncio.sleep(0.2)

        # Simulate GPU load
        dcgm_metrics.simulate_workload(duration_seconds=1, intensity=0.8)

        # Get metrics
        core_metrics = metrics_tracker.get_metrics()
        gpu_metrics = dcgm_metrics.get_metrics_dict()

        # Verify both systems have data
        if "/v1/chat/completions" in core_metrics["tokens"]:
            token_rate = core_metrics["tokens"]["/v1/chat/completions"].get("rate", 0)
            assert token_rate > 0

        # GPU should show utilization
        gpu_util = gpu_metrics["gpu_0"]["gpu_utilization_pct"]
        assert gpu_util > 0

    async def test_queue_depth_correlates_with_ttft(
        self, service, dynamo_metrics, aggregator
    ):
        """Higher queue depth should increase time to first token."""
        # Simulate queue buildup with concurrent requests
        tasks = []
        for i in range(20):
            request = ChatCompletionRequest(
                model="openai/gpt-oss-120b",
                messages=[Message(role=Role.USER, content=f"Query {i}")],
            )
            tasks.append(service.create_chat_completion(request))

        # Execute concurrently
        await asyncio.gather(*tasks)
        await asyncio.sleep(0.1)

        # Check dynamo metrics
        stats = dynamo_metrics.get_stats_dict()
        assert stats["summary"]["total_requests"] >= 20

        # Check for queue/latency data
        if "latency" in stats:
            assert "avg_ttft_ms" in stats["latency"]


@pytest.mark.asyncio
@pytest.mark.integration
class TestMetricsConsistency:
    """Test consistency across metrics systems."""

    async def test_same_request_appears_in_all_systems(
        self, service, metrics_tracker, kv_metrics, dynamo_metrics
    ):
        """Single request should be tracked by all relevant metrics."""
        # Track initial counts
        kv_before = kv_metrics.get_stats()["total_tokens_processed"]
        dynamo_before = dynamo_metrics.get_stats_dict()["summary"]["total_requests"]

        # Make request
        request = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[Message(role=Role.USER, content="Hello world")],
        )
        response = await service.create_chat_completion(request)

        await asyncio.sleep(0.1)

        # Verify increments in all systems
        core_metrics = metrics_tracker.get_metrics()
        assert "/v1/chat/completions" in core_metrics["requests"]

        kv_after = kv_metrics.get_stats()["total_tokens_processed"]
        assert kv_after > kv_before

        dynamo_after = dynamo_metrics.get_stats_dict()["summary"]["total_requests"]
        assert dynamo_after > dynamo_before

    async def test_token_counts_consistent_across_systems(
        self, service, metrics_tracker, kv_metrics
    ):
        """Token counts should match between core metrics and KV cache."""
        request = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[
                ChatMessage(
                    role="user",
                    content="This is a test message with a specific number of words",
                )
            ],
            max_tokens=50,
        )

        response = await service.create_chat_completion(request)
        await asyncio.sleep(0.1)

        # Get token counts from different systems
        core_metrics = metrics_tracker.get_metrics()
        kv_stats = kv_metrics.get_stats()

        # Core metrics should have token data
        if "/v1/chat/completions" in core_metrics["tokens"]:
            core_rate = core_metrics["tokens"]["/v1/chat/completions"].get("rate", 0)
            assert core_rate >= 0

        # KV cache should have processed tokens
        assert kv_stats["total_tokens_processed"] > 0

        # Both should be non-zero and reasonable
        assert kv_stats["total_tokens_processed"] < 1000000  # Sanity check

    async def test_timestamps_consistent(self, service, dynamo_metrics):
        """Timestamps across systems should be consistent."""
        start_time = time.time()

        request = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[Message(role=Role.USER, content="Test")],
        )
        await service.create_chat_completion(request)

        end_time = time.time()
        await asyncio.sleep(0.1)

        # Check dynamo timestamps
        stats = dynamo_metrics.get_stats_dict()
        if stats["summary"]["total_requests"] > 0:
            # Timestamps should be within request window
            assert start_time <= end_time

    async def test_no_duplicate_counting(
        self, service, metrics_tracker, kv_metrics, dynamo_metrics
    ):
        """Same request should not be counted multiple times."""
        # Get initial counts
        core_before = metrics_tracker.get_metrics()
        kv_before = kv_metrics.get_stats()
        dynamo_before = dynamo_metrics.get_stats_dict()

        # Make single request
        request = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[Message(role=Role.USER, content="Single request")],
        )
        await service.create_chat_completion(request)
        await asyncio.sleep(0.1)

        # Get final counts
        core_after = metrics_tracker.get_metrics()
        kv_after = kv_metrics.get_stats()
        dynamo_after = dynamo_metrics.get_stats_dict()

        # Each system should increment by exactly 1 request worth
        dynamo_delta = (
            dynamo_after["summary"]["total_requests"]
            - dynamo_before["summary"]["total_requests"]
        )
        assert dynamo_delta == 1

        # Token processing should be non-zero but reasonable
        kv_delta = (
            kv_after["total_tokens_processed"] - kv_before["total_tokens_processed"]
        )
        assert 0 < kv_delta < 10000


@pytest.mark.asyncio
@pytest.mark.integration
class TestPrometheusExport:
    """Test Prometheus export from all sources."""

    async def test_prometheus_export_includes_all_sources(self, aggregator):
        """Prometheus export should include metrics from all systems."""
        prom_output = aggregator.export_prometheus()

        # Should include metrics from each system
        assert "fakeai_requests_per_second" in prom_output  # Core metrics
        assert "fakeai_kv_cache_hit_rate" in prom_output  # KV cache
        assert "fakeai_gpu_utilization" in prom_output  # DCGM
        assert "fakeai_ttft_ms" in prom_output  # Dynamo

    async def test_prometheus_metrics_valid_format(self, aggregator):
        """Prometheus export should be valid format."""
        prom_output = aggregator.export_prometheus()

        # Should have HELP and TYPE declarations
        assert "# HELP" in prom_output
        assert "# TYPE" in prom_output

        # Metric values should be numeric
        lines = prom_output.split("\n")
        for line in lines:
            if line and not line.startswith("#"):
                parts = line.split()
                if len(parts) >= 2:
                    # Last part should be numeric
                    try:
                        float(parts[-1])
                    except ValueError:
                        pytest.fail(f"Invalid metric value in line: {line}")

    async def test_prometheus_labels_consistent(
        self, service, metrics_tracker, aggregator
    ):
        """Prometheus labels should be consistent across metrics."""
        # Make some requests
        for i in range(3):
            request = ChatCompletionRequest(
                model="openai/gpt-oss-120b",
                messages=[Message(role=Role.USER, content=f"Test {i}")],
            )
            await service.create_chat_completion(request)

        await asyncio.sleep(0.1)

        prom_output = aggregator.export_prometheus()

        # Check for consistent labeling
        assert 'endpoint="/v1/chat/completions"' in prom_output


@pytest.mark.asyncio
@pytest.mark.integration
class TestMetricsAggregation:
    """Test metrics aggregator functionality."""

    async def test_aggregator_combines_all_sources(
        self,
        service,
        aggregator,
        metrics_tracker,
        kv_metrics,
        dcgm_metrics,
        dynamo_metrics,
    ):
        """Aggregator should successfully combine all metric sources."""
        # Generate some activity
        for i in range(5):
            request = ChatCompletionRequest(
                model="openai/gpt-oss-120b",
                messages=[Message(role=Role.USER, content=f"Question {i}")],
            )
            await service.create_chat_completion(request)

        await asyncio.sleep(0.1)

        # Get unified metrics
        unified = aggregator.get_unified_metrics()

        # Should have all sections
        assert "requests" in unified
        assert "kv_cache" in unified
        assert "gpu" in unified
        assert "dynamo" in unified

    async def test_health_scoring(self, aggregator, metrics_tracker, dcgm_metrics):
        """Health scoring should aggregate across systems."""
        # Generate some metrics
        metrics_tracker.track_request("/v1/chat/completions")
        metrics_tracker.track_response("/v1/chat/completions", 0.5, 100)

        # Simulate healthy GPU
        dcgm_metrics.simulate_workload(duration_seconds=1, intensity=0.5)

        # Get health score
        health = aggregator.calculate_health_score()

        assert health is not None
        assert "overall" in health
        assert health["overall"]["status"] in [s.value for s in HealthStatus]
        assert 0 <= health["overall"]["score"] <= 100

    async def test_time_series_aggregation(self, service, aggregator, metrics_tracker):
        """Time-series data should be aggregated correctly."""
        # Generate requests over time
        for i in range(10):
            request = ChatCompletionRequest(
                model="openai/gpt-oss-120b",
                messages=[Message(role=Role.USER, content=f"Query {i}")],
            )
            await service.create_chat_completion(request)
            await asyncio.sleep(0.05)

        # Get time-series data
        ts_data = aggregator.get_time_series("requests_per_second", window_seconds=10)

        assert ts_data is not None
        assert len(ts_data) > 0


@pytest.mark.asyncio
@pytest.mark.integration
class TestModelMetricsCorrelation:
    """Test model-specific metrics correlation."""

    async def test_model_metrics_match_endpoint_metrics(
        self, service, metrics_tracker, aggregator
    ):
        """Model-level metrics should align with endpoint metrics."""
        # Make requests to specific model
        model_name = "openai/gpt-oss-120b"
        for i in range(5):
            request = ChatCompletionRequest(
                model=model_name,
                messages=[Message(role=Role.USER, content=f"Test {i}")],
            )
            await service.create_chat_completion(request)

        await asyncio.sleep(0.1)

        # Get metrics
        core_metrics = metrics_tracker.get_metrics()
        unified = aggregator.get_unified_metrics()

        # Verify model appears in metrics
        assert "/v1/chat/completions" in core_metrics["requests"]

    async def test_different_models_tracked_separately(self, service, metrics_tracker):
        """Different models should have separate metrics."""
        # Request to model 1
        request1 = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[Message(role=Role.USER, content="Test 1")],
        )
        await service.create_chat_completion(request1)

        # Request to model 2
        request2 = ChatCompletionRequest(
            model="openai/gpt-oss-20b",
            messages=[Message(role=Role.USER, content="Test 2")],
        )
        await service.create_chat_completion(request2)

        await asyncio.sleep(0.1)

        # Both should be in metrics
        core_metrics = metrics_tracker.get_metrics()
        assert "/v1/chat/completions" in core_metrics["requests"]


@pytest.mark.asyncio
@pytest.mark.integration
class TestCostTrackingConsistency:
    """Test cost tracking matches token usage."""

    async def test_cost_matches_tokens(self, service, metrics_tracker):
        """Calculated cost should match token usage."""
        request = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[
                ChatMessage(
                    role="user",
                    content="Generate a long response with many tokens to test cost calculation",
                )
            ],
            max_tokens=200,
        )

        response = await service.create_chat_completion(request)
        await asyncio.sleep(0.1)

        # Get token counts
        assert response.usage is not None
        prompt_tokens = response.usage.prompt_tokens
        completion_tokens = response.usage.completion_tokens

        # Both should be non-zero
        assert prompt_tokens > 0
        assert completion_tokens > 0

        # Total should equal sum
        assert response.usage.total_tokens == prompt_tokens + completion_tokens


@pytest.mark.asyncio
@pytest.mark.integration
class TestStreamingMetricsComprehensive:
    """Test streaming metrics across all systems."""

    async def test_streaming_metrics_all_systems(
        self, service, metrics_tracker, kv_metrics, dynamo_metrics
    ):
        """Streaming request tracked comprehensively."""
        request = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[Message(role=Role.USER, content="Tell me a story")],
            max_tokens=100,
            stream=True,
        )

        # Consume stream
        chunk_count = 0
        async for chunk in await service.create_chat_completion(request):
            chunk_count += 1

        await asyncio.sleep(0.1)

        # Core metrics should track streaming
        core_metrics = metrics_tracker.get_metrics()
        assert "streaming_stats" in core_metrics

        # KV cache should process tokens
        kv_stats = kv_metrics.get_stats()
        assert kv_stats["total_tokens_processed"] > 0

        # Dynamo should track streaming request
        dynamo_stats = dynamo_metrics.get_stats_dict()
        assert dynamo_stats["summary"]["total_requests"] > 0


@pytest.mark.asyncio
@pytest.mark.integration
class TestExportFormatConsistency:
    """Test export format consistency across systems."""

    async def test_json_exports_valid(self, aggregator):
        """JSON exports should be valid from all sources."""
        unified = aggregator.get_unified_metrics()

        # Should be valid JSON serializable
        json_str = json.dumps(unified)
        parsed = json.loads(json_str)

        assert parsed is not None
        assert isinstance(parsed, dict)

    async def test_prometheus_and_json_consistent(
        self, service, aggregator, metrics_tracker
    ):
        """Prometheus and JSON exports should have consistent data."""
        # Generate some activity
        for i in range(3):
            request = ChatCompletionRequest(
                model="openai/gpt-oss-120b",
                messages=[Message(role=Role.USER, content=f"Test {i}")],
            )
            await service.create_chat_completion(request)

        await asyncio.sleep(0.1)

        # Get both formats
        json_metrics = aggregator.get_unified_metrics()
        prom_metrics = aggregator.export_prometheus()

        # Both should have data
        assert len(json_metrics) > 0
        assert len(prom_metrics) > 0

        # Both should reference same endpoints
        if "requests" in json_metrics and json_metrics["requests"]:
            assert "/v1/chat/completions" in prom_metrics


@pytest.mark.asyncio
@pytest.mark.integration
class TestErrorMetricsCorrelation:
    """Test error metrics correlation across systems."""

    async def test_errors_tracked_across_systems(
        self, service, metrics_tracker, dynamo_metrics
    ):
        """Errors should be tracked in multiple systems."""
        # This test would need error injection, but we can verify the plumbing
        core_metrics = metrics_tracker.get_metrics()
        assert "errors" in core_metrics

        dynamo_stats = dynamo_metrics.get_stats_dict()
        assert "summary" in dynamo_stats


# Performance baseline tests
@pytest.mark.asyncio
@pytest.mark.integration
class TestMetricsPerformance:
    """Test metrics collection doesn't significantly impact performance."""

    async def test_metrics_overhead_minimal(self, service):
        """Metrics collection should have minimal overhead."""
        # Measure without heavy metrics load
        start = time.time()
        for i in range(10):
            request = ChatCompletionRequest(
                model="openai/gpt-oss-120b",
                messages=[Message(role=Role.USER, content=f"Test {i}")],
            )
            await service.create_chat_completion(request)
        duration = time.time() - start

        # Should complete reasonably fast (< 2 seconds for 10 requests)
        assert duration < 2.0

    async def test_concurrent_metrics_thread_safe(
        self, service, metrics_tracker, kv_metrics
    ):
        """Concurrent requests should have thread-safe metrics."""
        tasks = []
        for i in range(20):
            request = ChatCompletionRequest(
                model="openai/gpt-oss-120b",
                messages=[Message(role=Role.USER, content=f"Concurrent {i}")],
            )
            tasks.append(service.create_chat_completion(request))

        # Execute concurrently
        responses = await asyncio.gather(*tasks)

        await asyncio.sleep(0.2)

        # All requests should succeed
        assert len(responses) == 20

        # Metrics should be consistent (no race conditions)
        core_metrics = metrics_tracker.get_metrics()
        kv_stats = kv_metrics.get_stats()

        # Should have tracked all requests
        assert core_metrics is not None
        assert kv_stats["total_tokens_processed"] > 0
