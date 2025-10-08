#!/usr/bin/env python3
"""
End-to-End Workflow Tests for FakeAI Metrics System

This test suite simulates real production usage patterns and validates
the complete request lifecycle including:
- Complete request lifecycle (Started → Completed → metrics updated)
- Streaming lifecycle with TTFT/ITL/TPS calculations
- Error scenarios with pattern detection
- Mixed workloads with various models
- Budget exceeded scenarios
- SLO violation detection

These tests verify that all metrics trackers work together correctly
to provide accurate, production-ready telemetry.
"""
#  SPDX-License-Identifier: Apache-2.0

import importlib.util
import sys
import time
import uuid
from pathlib import Path

import pytest

# Get the fakeai directory
FAKEAI_DIR = Path(__file__).parent.parent / "fakeai"


def load_module_from_file(module_name, file_path):
    """Load a module directly from a file without triggering __init__.py."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


# Load modules directly to avoid app initialization
cost_tracker_module = load_module_from_file(
    "cost_tracker", str(FAKEAI_DIR / "cost_tracker.py")
)
error_tracker_module = load_module_from_file(
    "error_metrics_tracker", str(FAKEAI_DIR / "error_metrics_tracker.py")
)
metrics_module = load_module_from_file("metrics", str(FAKEAI_DIR / "metrics.py"))
model_metrics_module = load_module_from_file(
    "model_metrics", str(FAKEAI_DIR / "model_metrics.py")
)
streaming_tracker_module = load_module_from_file(
    "streaming_metrics_tracker", str(FAKEAI_DIR / "streaming_metrics_tracker.py")
)

# Extract the classes we need
BudgetLimitType = cost_tracker_module.BudgetLimitType
BudgetPeriod = cost_tracker_module.BudgetPeriod
CostTracker = cost_tracker_module.CostTracker
ErrorMetricsTracker = error_tracker_module.ErrorMetricsTracker
MetricsTracker = metrics_module.MetricsTracker
ModelMetricsTracker = model_metrics_module.ModelMetricsTracker
StreamingMetricsTracker = streaming_tracker_module.StreamingMetricsTracker


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def metrics_tracker():
    """Create fresh MetricsTracker instance."""
    from collections import defaultdict

    tracker = MetricsTracker()
    # Clear existing data while preserving defaultdict behavior
    MetricType = metrics_module.MetricType
    MetricsWindow = metrics_module.MetricsWindow
    tracker._metrics = {
        metric_type: defaultdict(lambda: MetricsWindow())
        for metric_type in MetricType
    }
    return tracker


@pytest.fixture
def cost_tracker():
    """Create fresh CostTracker instance."""
    tracker = CostTracker()
    tracker.clear_history()
    return tracker


@pytest.fixture
def model_tracker():
    """Create fresh ModelMetricsTracker instance."""
    tracker = ModelMetricsTracker()
    tracker.reset_stats()
    return tracker


@pytest.fixture
def error_tracker():
    """Create fresh ErrorMetricsTracker instance."""
    return ErrorMetricsTracker(
        max_recent_errors=500,
        error_budget_slo=0.999,
        window_seconds=300,
        pattern_threshold=3,
    )


@pytest.fixture
def streaming_tracker():
    """Create fresh StreamingMetricsTracker instance."""
    return StreamingMetricsTracker(
        max_active_streams=10000,
        max_completed_streams=1000,
        aggregation_window_seconds=300,
    )


# ============================================================================
# Test 1: Complete Request Lifecycle
# ============================================================================


class TestCompleteRequestLifecycle:
    """Test complete request lifecycle from start to finish."""

    def test_single_request_complete_lifecycle(
        self,
        metrics_tracker,
        cost_tracker,
        model_tracker,
        error_tracker,
    ):
        """
        Test: Single request from start to completion.

        Workflow:
        1. RequestStartedEvent → track request
        2. Process request (simulate work)
        3. RequestCompletedEvent → track response, tokens, cost
        4. Verify all trackers updated correctly
        """
        # Configuration
        endpoint = "/v1/chat/completions"
        model = "gpt-4o"
        api_key = "sk-test-123"
        prompt_tokens = 100
        completion_tokens = 50

        # Step 1: Start request
        request_start = time.time()
        metrics_tracker.track_request(endpoint)

        # Step 2: Simulate processing (10ms)
        time.sleep(0.01)

        # Step 3: Complete request
        latency_ms = (time.time() - request_start) * 1000

        # Track in all systems
        metrics_tracker.track_response(endpoint, latency_ms / 1000)  # seconds
        metrics_tracker.track_tokens(endpoint, prompt_tokens + completion_tokens)

        cost = cost_tracker.record_usage(
            api_key=api_key,
            model=model,
            endpoint=endpoint,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )

        model_tracker.track_request(
            model=model,
            endpoint=endpoint,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            latency_ms=latency_ms,
            user=api_key,
            error=False,
        )

        error_tracker.record_success(endpoint, model)

        # Step 4: Verify all trackers

        # Verify MetricsTracker
        metrics = metrics_tracker.get_metrics()
        assert metrics["requests"][endpoint]["rate"] > 0
        assert metrics["responses"][endpoint]["rate"] > 0
        assert metrics["tokens"][endpoint]["rate"] > 0

        # Verify CostTracker
        assert cost > 0
        cost_info = cost_tracker.get_cost_by_key(api_key)
        assert cost_info["total_cost"] == cost
        assert cost_info["tokens"]["total_tokens"] == prompt_tokens + completion_tokens

        # Verify ModelMetricsTracker
        model_stats = model_tracker.get_model_stats(model)
        assert model_stats["request_count"] == 1
        assert model_stats["tokens"]["total"] == prompt_tokens + completion_tokens
        assert model_stats["latency"]["avg_ms"] >= 10  # At least 10ms

        # Verify ErrorMetricsTracker
        error_metrics = error_tracker.get_metrics()
        assert error_metrics["total_requests"] == 1
        assert error_metrics["total_successes"] == 1
        assert error_metrics["total_errors"] == 0
        assert error_metrics["success_rate"] == 1.0

    def test_multiple_requests_complete_lifecycle(
        self,
        metrics_tracker,
        cost_tracker,
        model_tracker,
        error_tracker,
    ):
        """
        Test: Multiple requests through complete lifecycle.

        Simulates 10 sequential requests with varying token counts.
        """
        endpoint = "/v1/chat/completions"
        model = "gpt-4o-mini"
        api_key = "sk-test-multi"

        total_cost = 0
        total_tokens = 0

        for i in range(10):
            # Varying token counts
            prompt_tokens = 50 + (i * 10)
            completion_tokens = 25 + (i * 5)

            # Start request
            request_start = time.time()
            metrics_tracker.track_request(endpoint)

            # Simulate processing
            time.sleep(0.005)  # 5ms

            # Complete request
            latency_ms = (time.time() - request_start) * 1000

            metrics_tracker.track_response(endpoint, latency_ms / 1000)
            metrics_tracker.track_tokens(endpoint, prompt_tokens + completion_tokens)

            cost = cost_tracker.record_usage(
                api_key=api_key,
                model=model,
                endpoint=endpoint,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
            )
            total_cost += cost
            total_tokens += prompt_tokens + completion_tokens

            model_tracker.track_request(
                model=model,
                endpoint=endpoint,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                latency_ms=latency_ms,
                user=api_key,
                error=False,
            )

            error_tracker.record_success(endpoint, model)

        # Verify aggregates
        model_stats = model_tracker.get_model_stats(model)
        assert model_stats["request_count"] == 10
        assert model_stats["tokens"]["total"] == total_tokens

        cost_info = cost_tracker.get_cost_by_key(api_key)
        assert abs(cost_info["total_cost"] - total_cost) < 0.000001

        error_metrics = error_tracker.get_metrics()
        assert error_metrics["total_requests"] == 10
        assert error_metrics["total_successes"] == 10
        assert error_metrics["success_rate"] == 1.0


# ============================================================================
# Test 2: Complete Streaming Lifecycle
# ============================================================================


class TestCompleteStreamingLifecycle:
    """Test streaming request lifecycle with TTFT, ITL, and TPS."""

    def test_single_stream_complete_lifecycle(
        self,
        streaming_tracker,
        metrics_tracker,
        cost_tracker,
    ):
        """
        Test: Single streaming request from start to finish.

        Workflow:
        1. StreamStartedEvent → start tracking
        2. Generate tokens one by one
        3. FirstTokenGeneratedEvent → record TTFT
        4. Continue generating tokens → record ITL
        5. StreamCompletedEvent → calculate TPS
        6. Verify all metrics calculated correctly
        """
        stream_id = f"stream-{uuid.uuid4()}"
        model = "gpt-4o"
        endpoint = "/v1/chat/completions"
        prompt_tokens = 150

        # Step 1: Start stream
        streaming_tracker.start_stream(
            stream_id=stream_id,
            model=model,
            prompt_tokens=prompt_tokens,
            temperature=0.7,
            max_tokens=100,
        )

        metrics_tracker.start_stream(stream_id, endpoint)

        # Step 2: Generate first token (measure TTFT)
        time.sleep(0.05)  # 50ms TTFT
        streaming_tracker.record_token(stream_id, "Hello", chunk_size_bytes=25)
        metrics_tracker.track_stream_first_token(stream_id)

        # Step 3: Generate more tokens with varying ITL
        for i in range(1, 20):
            time.sleep(0.01)  # 10ms ITL
            token = f"token{i}"
            streaming_tracker.record_token(stream_id, token, chunk_size_bytes=20)
            metrics_tracker.track_stream_token(stream_id)

        # Step 4: Complete stream
        streaming_tracker.complete_stream(stream_id, "stop")
        metrics_tracker.complete_stream(stream_id, endpoint)

        # Step 5: Verify metrics

        # Verify StreamingMetricsTracker
        stream_metrics = streaming_tracker.get_metrics()
        assert stream_metrics.completed_streams == 1
        assert stream_metrics.active_streams == 0
        assert stream_metrics.total_tokens_generated == 20

        # TTFT should be around 50ms
        assert 40 <= stream_metrics.avg_ttft <= 70, f"TTFT: {stream_metrics.avg_ttft}ms"
        assert 40 <= stream_metrics.p50_ttft <= 70

        # ITL should be around 10ms
        assert 5 <= stream_metrics.avg_itl <= 20, f"ITL: {stream_metrics.avg_itl}ms"

        # TPS should be reasonable (20 tokens in ~250ms = ~80 tokens/sec)
        assert stream_metrics.avg_tokens_per_second > 50

        # Verify MetricsTracker
        streaming_stats = metrics_tracker.get_streaming_stats()
        assert streaming_stats["completed_streams"] == 1
        assert streaming_stats["active_streams"] == 0

    def test_multiple_streams_parallel(
        self,
        streaming_tracker,
        metrics_tracker,
    ):
        """
        Test: Multiple concurrent streaming requests.

        Simulates 5 parallel streams with different characteristics.
        """
        streams = []

        # Start 5 streams
        for i in range(5):
            stream_id = f"stream-parallel-{i}"
            model = "gpt-4o" if i % 2 == 0 else "gpt-4o-mini"

            streaming_tracker.start_stream(
                stream_id=stream_id,
                model=model,
                prompt_tokens=100 + (i * 20),
            )

            streams.append((stream_id, model, 15 + (i * 5)))  # Different token counts

        assert streaming_tracker.get_active_stream_count() == 5

        # Generate tokens for all streams
        for stream_id, model, token_count in streams:
            # First token
            time.sleep(0.03)  # 30ms TTFT
            streaming_tracker.record_token(stream_id, "First", chunk_size_bytes=20)

            # Subsequent tokens
            for j in range(1, token_count):
                time.sleep(0.005)  # 5ms ITL
                streaming_tracker.record_token(stream_id, f"tok{j}", chunk_size_bytes=15)

        # Complete all streams
        for stream_id, model, _ in streams:
            streaming_tracker.complete_stream(stream_id, "stop")

        # Verify
        stream_metrics = streaming_tracker.get_metrics()
        assert stream_metrics.completed_streams == 5
        assert stream_metrics.active_streams == 0

        # Check per-model breakdown
        assert len(stream_metrics.streams_by_model) == 2
        assert "gpt-4o" in stream_metrics.streams_by_model
        assert "gpt-4o-mini" in stream_metrics.streams_by_model


# ============================================================================
# Test 3: Error Scenario
# ============================================================================


class TestErrorScenario:
    """Test error handling and pattern detection."""

    def test_single_error_tracked(
        self,
        error_tracker,
        metrics_tracker,
        model_tracker,
    ):
        """
        Test: Single error request.

        Workflow:
        1. RequestStartedEvent
        2. RequestFailedEvent with error details
        3. Verify error tracked in all systems
        4. Verify SLO updated
        """
        endpoint = "/v1/chat/completions"
        model = "gpt-4o"
        error_type = "InternalServerError"
        error_message = "Database connection timeout after 30s"

        # Track error
        error_tracker.record_error(
            endpoint=endpoint,
            status_code=500,
            error_type=error_type,
            error_message=error_message,
            model=model,
            api_key="sk-test-error",
            request_id="req-error-123",
        )

        metrics_tracker.track_error(endpoint)

        model_tracker.track_request(
            model=model,
            endpoint=endpoint,
            prompt_tokens=100,
            completion_tokens=0,
            latency_ms=30000,
            error=True,
        )

        # Verify error tracked
        error_metrics = error_tracker.get_metrics()
        assert error_metrics["total_errors"] == 1
        assert error_metrics["total_requests"] == 1
        assert error_metrics["error_rate"] == 1.0

        # Verify recent errors
        recent = error_tracker.get_recent_errors(limit=10)
        assert len(recent) == 1
        assert recent[0].error_type == error_type
        assert recent[0].endpoint == endpoint
        assert recent[0].fingerprint is not None

        # Verify SLO
        slo_status = error_tracker.get_slo_status()
        assert slo_status.slo_violated is True  # 0% success < 99.9%
        assert slo_status.current_error_rate == 1.0

    def test_error_pattern_detection(self, error_tracker):
        """
        Test: Error pattern detection across multiple similar errors.

        Generates 5 similar errors and verifies pattern is detected.
        """
        endpoint = "/v1/chat/completions"
        error_type = "RateLimitError"

        # Generate 5 similar errors with varying dynamic content
        for i in range(5):
            error_tracker.record_error(
                endpoint=endpoint,
                status_code=429,
                error_type=error_type,
                error_message=f"Rate limit exceeded for user-{i} at timestamp {time.time()}",
                model="gpt-4o",
                api_key=f"sk-user-{i}",
                request_id=f"req-{uuid.uuid4()}",
            )

        # Also record successes to avoid 100% error rate
        for _ in range(10):
            error_tracker.record_success(endpoint, "gpt-4o")

        # Verify pattern detected
        patterns = error_tracker.get_error_patterns(min_count=3)
        assert len(patterns) >= 1

        # Find our pattern
        rate_limit_pattern = None
        for pattern in patterns:
            if pattern.error_type == error_type:
                rate_limit_pattern = pattern
                break

        assert rate_limit_pattern is not None
        assert rate_limit_pattern.count == 5
        assert rate_limit_pattern.endpoint == endpoint
        assert "Rate limit exceeded" in pattern.normalized_message

    def test_mixed_errors_and_successes(
        self,
        error_tracker,
        model_tracker,
    ):
        """
        Test: Mix of errors and successes to verify SLO calculation.

        95 successes + 5 errors = 95% success rate (violates 99.9% SLO).
        """
        endpoint = "/v1/chat/completions"
        model = "gpt-4o"

        # Record 95 successes
        for i in range(95):
            error_tracker.record_success(endpoint, model)
            model_tracker.track_request(
                model=model,
                endpoint=endpoint,
                prompt_tokens=100,
                completion_tokens=50,
                latency_ms=100,
                error=False,
            )

        # Record 5 errors
        for i in range(5):
            error_tracker.record_error(
                endpoint=endpoint,
                status_code=500,
                error_type="InternalServerError",
                error_message=f"Internal error {i}",
                model=model,
            )
            model_tracker.track_request(
                model=model,
                endpoint=endpoint,
                prompt_tokens=100,
                completion_tokens=0,
                latency_ms=50,
                error=True,
            )

        # Verify counts
        error_metrics = error_tracker.get_metrics()
        assert error_metrics["total_requests"] == 100
        assert error_metrics["total_successes"] == 95
        assert error_metrics["total_errors"] == 5
        assert abs(error_metrics["success_rate"] - 0.95) < 0.01

        # Verify SLO violated (95% < 99.9%)
        slo_status = error_tracker.get_slo_status()
        assert slo_status.slo_violated is True
        assert slo_status.current_success_rate < slo_status.target_success_rate

        # Verify burn rate is high
        assert slo_status.burn_rate >= 49  # Way over budget (5% / 0.1% = 50x)

        # Verify model metrics
        model_stats = model_tracker.get_model_stats(model)
        assert model_stats["request_count"] == 100
        assert model_stats["errors"]["count"] == 5
        assert abs(model_stats["errors"]["rate_percent"] - 5.0) < 0.1


# ============================================================================
# Test 4: Mixed Workload
# ============================================================================


class TestMixedWorkload:
    """Test realistic mixed workload with various request types."""

    def test_mixed_workload_simulation(
        self,
        metrics_tracker,
        cost_tracker,
        model_tracker,
        error_tracker,
        streaming_tracker,
    ):
        """
        Test: Comprehensive mixed workload simulation.

        Workload:
        - 50 successful standard requests (various models)
        - 10 streaming requests
        - 5 failed requests

        Verifies all metrics are tracked correctly across all systems.
        """
        api_key = "sk-test-mixed"
        endpoint = "/v1/chat/completions"

        models = ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"]
        total_cost = 0

        # === Part 1: 50 successful standard requests ===
        for i in range(50):
            model = models[i % 3]
            prompt_tokens = 100 + (i * 5)
            completion_tokens = 50 + (i * 2)

            start = time.time()
            metrics_tracker.track_request(endpoint)

            time.sleep(0.002)  # 2ms processing

            latency_ms = (time.time() - start) * 1000
            metrics_tracker.track_response(endpoint, latency_ms / 1000)
            metrics_tracker.track_tokens(endpoint, prompt_tokens + completion_tokens)

            cost = cost_tracker.record_usage(
                api_key=api_key,
                model=model,
                endpoint=endpoint,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
            )
            total_cost += cost

            model_tracker.track_request(
                model=model,
                endpoint=endpoint,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                latency_ms=latency_ms,
                user=api_key,
                error=False,
            )

            error_tracker.record_success(endpoint, model)

        # === Part 2: 10 streaming requests ===
        for i in range(10):
            stream_id = f"stream-mixed-{i}"
            model = models[i % 3]

            streaming_tracker.start_stream(
                stream_id=stream_id,
                model=model,
                prompt_tokens=150,
            )

            # Generate 15 tokens per stream
            time.sleep(0.03)  # TTFT
            streaming_tracker.record_token(stream_id, "First", chunk_size_bytes=20)

            for j in range(1, 15):
                time.sleep(0.008)  # ITL
                streaming_tracker.record_token(stream_id, f"tok{j}", chunk_size_bytes=18)

            streaming_tracker.complete_stream(stream_id, "stop")

            # Track cost for streaming
            cost = cost_tracker.record_usage(
                api_key=api_key,
                model=model,
                endpoint=endpoint,
                prompt_tokens=150,
                completion_tokens=15,
            )
            total_cost += cost

            error_tracker.record_success(endpoint, model)

        # === Part 3: 5 failed requests ===
        for i in range(5):
            model = models[i % 3]

            error_tracker.record_error(
                endpoint=endpoint,
                status_code=500,
                error_type="InternalServerError",
                error_message=f"Service unavailable: error {i}",
                model=model,
                api_key=api_key,
            )

            metrics_tracker.track_error(endpoint)

            model_tracker.track_request(
                model=model,
                endpoint=endpoint,
                prompt_tokens=100,
                completion_tokens=0,
                latency_ms=100,
                error=True,
            )

        # === Verification ===

        # Total requests: 50 standard + 10 streaming + 5 errors = 65
        error_metrics = error_tracker.get_metrics()
        assert error_metrics["total_requests"] == 65
        assert error_metrics["total_successes"] == 60
        assert error_metrics["total_errors"] == 5

        # Success rate: 60/65 = 92.3%
        expected_success_rate = 60.0 / 65.0
        assert abs(error_metrics["success_rate"] - expected_success_rate) < 0.01

        # Cost tracking
        # Note: CostTracker only tracks requests with usage (not error-only requests)
        cost_info = cost_tracker.get_cost_by_key(api_key)
        assert abs(cost_info["total_cost"] - total_cost) < 0.000001
        assert cost_info["requests"] == 60  # 50 standard + 10 streaming (errors not tracked)

        # Model tracking - verify all models tracked
        for model in models:
            model_stats = model_tracker.get_model_stats(model)
            assert model_stats["request_count"] > 0
            assert model_stats["tokens"]["total"] > 0

        # Streaming tracking
        stream_metrics = streaming_tracker.get_metrics()
        assert stream_metrics.completed_streams == 10
        assert stream_metrics.total_tokens_generated == 150  # 15 tokens * 10 streams


# ============================================================================
# Test 5: Budget Exceeded Scenario
# ============================================================================


class TestBudgetExceededScenario:
    """Test budget exceeded detection and alerting."""

    def test_budget_exceeded_soft_limit(self, cost_tracker):
        """
        Test: Budget exceeded with soft limit (warning only).

        Scenario:
        - Set $10 budget with soft limit
        - Generate $11 worth of requests
        - Verify alert triggered
        - Verify requests still processed
        """
        api_key = "sk-budget-test"
        model = "gpt-4o"  # $5 per 1M input, $15 per 1M output
        endpoint = "/v1/chat/completions"

        # Set $10 budget with soft limit
        cost_tracker.set_budget(
            api_key=api_key,
            limit=10.0,
            period=BudgetPeriod.NEVER,
            limit_type=BudgetLimitType.SOFT,
            alert_threshold=0.8,  # Alert at 80%
        )

        # Generate requests to exceed budget
        # Each request: (1M * $5 + 500k * $15) / 1M = $12.50
        # This will exceed $10 budget in first request

        cost1 = cost_tracker.record_usage(
            api_key=api_key,
            model=model,
            endpoint=endpoint,
            prompt_tokens=1_000_000,  # 1M tokens
            completion_tokens=500_000,  # 500k tokens
        )

        # Verify cost
        assert abs(cost1 - 12.50) < 0.01

        # Check budget status
        used, remaining, over_limit = cost_tracker.check_budget(api_key)
        assert used >= 10.0
        assert over_limit is True
        assert remaining <= 0

        # Verify budget info
        cost_info = cost_tracker.get_cost_by_key(api_key)
        assert cost_info["budget"]["used"] >= 10.0
        assert cost_info["budget"]["percentage"] >= 100.0

        # With soft limit, can still make more requests
        cost2 = cost_tracker.record_usage(
            api_key=api_key,
            model=model,
            endpoint=endpoint,
            prompt_tokens=100_000,
            completion_tokens=50_000,
        )

        assert cost2 > 0
        used, remaining, over_limit = cost_tracker.check_budget(api_key)
        assert over_limit is True

    def test_budget_alert_threshold(self, cost_tracker):
        """
        Test: Budget alert triggered at threshold.

        Scenario:
        - Set $10 budget with 80% alert threshold
        - Generate $8.50 worth of requests (over threshold)
        - Verify alert would be triggered
        """
        api_key = "sk-alert-test"
        model = "gpt-4o-mini"  # Cheaper model
        endpoint = "/v1/chat/completions"

        # Set budget
        cost_tracker.set_budget(
            api_key=api_key,
            limit=10.0,
            period=BudgetPeriod.NEVER,
            limit_type=BudgetLimitType.SOFT,
            alert_threshold=0.8,  # Alert at $8
        )

        # Generate requests to reach alert threshold
        # gpt-4o-mini: $0.15/1M input, $0.60/1M output
        # To get ~$8.50:
        # 10M input + 5M output = ($1.50 + $3.00) = $4.50
        # Do this twice: $9.00 total

        for _ in range(2):
            cost_tracker.record_usage(
                api_key=api_key,
                model=model,
                endpoint=endpoint,
                prompt_tokens=10_000_000,
                completion_tokens=5_000_000,
            )

        # Check budget
        used, remaining, over_limit = cost_tracker.check_budget(api_key)
        assert used >= 8.0  # Over 80% of $10
        assert used < 10.0  # But not over limit
        assert over_limit is False
        assert remaining > 0


# ============================================================================
# Test 6: SLO Violation Scenario
# ============================================================================


class TestSLOViolationScenario:
    """Test SLO violation detection and burn rate calculation."""

    def test_slo_violation_detection(self, error_tracker):
        """
        Test: SLO violation with 99.9% target.

        Scenario:
        - Target: 99.9% success rate
        - Reality: 100 requests, 2 errors = 98% success rate
        - Expected: SLO violated, high burn rate
        """
        endpoint = "/v1/chat/completions"
        model = "gpt-4o"

        # 98 successes
        for i in range(98):
            error_tracker.record_success(endpoint, model)

        # 2 errors
        for i in range(2):
            error_tracker.record_error(
                endpoint=endpoint,
                status_code=500,
                error_type="ServiceUnavailable",
                error_message=f"Service temporarily unavailable: error {i}",
                model=model,
            )

        # Verify SLO violated
        slo_status = error_tracker.get_slo_status()

        assert slo_status.total_requests == 100
        assert slo_status.successful_requests == 98
        assert slo_status.failed_requests == 2

        # Success rate: 98/100 = 0.98
        assert abs(slo_status.current_success_rate - 0.98) < 0.01
        assert abs(slo_status.current_error_rate - 0.02) < 0.01

        # SLO should be violated (98% < 99.9%)
        assert slo_status.slo_violated is True

        # Calculate expected error budget
        # Target error rate: 1 - 0.999 = 0.001
        # Allowed errors: 100 * 0.001 = 0.1 errors
        # Actual errors: 2
        # Budget consumed: 2 (way over!)
        assert slo_status.error_budget_consumed == 2

        # Burn rate should be high
        # Actual error rate / Target error rate = 0.02 / 0.001 = 20x
        assert slo_status.burn_rate >= 15.0  # At least 15x burn rate

    def test_slo_within_target(self, error_tracker):
        """
        Test: SLO within target range.

        Scenario:
        - Target: 99.9% success rate
        - Reality: 10000 requests, 5 errors = 99.95% success rate
        - Expected: SLO met, low burn rate
        """
        endpoint = "/v1/chat/completions"
        model = "gpt-4o"

        # 9995 successes
        for i in range(9995):
            error_tracker.record_success(endpoint, model)

        # 5 errors
        for i in range(5):
            error_tracker.record_error(
                endpoint=endpoint,
                status_code=503,
                error_type="ServiceUnavailable",
                error_message="Brief outage",
                model=model,
            )

        # Verify SLO met
        slo_status = error_tracker.get_slo_status()

        assert slo_status.total_requests == 10000
        assert slo_status.successful_requests == 9995
        assert slo_status.failed_requests == 5

        # Success rate: 9995/10000 = 0.9995 = 99.95%
        assert slo_status.current_success_rate >= 0.999

        # SLO should NOT be violated (99.95% >= 99.9%)
        assert slo_status.slo_violated is False

        # Error budget should have room
        # Allowed errors: 10000 * 0.001 = 10 errors
        # Actual errors: 5
        assert slo_status.error_budget_remaining >= 5

        # Burn rate should be low (under 1.0 is good)
        assert slo_status.burn_rate < 1.0

    def test_slo_edge_case_exactly_at_target(self, error_tracker):
        """
        Test: SLO exactly at target threshold.

        Scenario:
        - Target: 99.9% success rate
        - Reality: 1000 requests, 1 error = 99.9% success rate
        - Expected: SLO NOT violated (at threshold)
        """
        endpoint = "/v1/chat/completions"
        model = "gpt-4o"

        # 999 successes
        for i in range(999):
            error_tracker.record_success(endpoint, model)

        # 1 error
        error_tracker.record_error(
            endpoint=endpoint,
            status_code=500,
            error_type="InternalError",
            error_message="Single error",
            model=model,
        )

        # Verify SLO at edge
        slo_status = error_tracker.get_slo_status()

        assert slo_status.total_requests == 1000
        assert slo_status.successful_requests == 999
        assert slo_status.failed_requests == 1

        # Success rate: 999/1000 = 0.999 = 99.9%
        assert abs(slo_status.current_success_rate - 0.999) < 0.001

        # At threshold, should NOT be violated
        assert slo_status.slo_violated is False

        # Burn rate should be exactly 1.0
        assert abs(slo_status.burn_rate - 1.0) < 0.1


# ============================================================================
# Integration Tests
# ============================================================================


class TestEndToEndIntegration:
    """Full end-to-end integration tests combining all components."""

    def test_production_realistic_workload(
        self,
        metrics_tracker,
        cost_tracker,
        model_tracker,
        error_tracker,
        streaming_tracker,
    ):
        """
        Test: Realistic production workload over time.

        Simulates a production system with:
        - Multiple API keys
        - Various models
        - Mix of streaming and non-streaming
        - Some errors
        - Budget tracking
        - SLO monitoring
        """
        # Configuration
        api_keys = ["sk-user-1", "sk-user-2", "sk-user-3"]
        models = ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"]
        endpoint = "/v1/chat/completions"

        # Set budgets for each user
        for api_key in api_keys:
            cost_tracker.set_budget(
                api_key=api_key,
                limit=100.0,
                period=BudgetPeriod.NEVER,
                limit_type=BudgetLimitType.SOFT,
                alert_threshold=0.9,
            )

        # Simulate workload
        total_requests = 0
        streaming_count = 0
        error_count = 0

        for i in range(100):
            api_key = api_keys[i % 3]
            model = models[i % 3]

            # 70% standard requests
            if i % 10 < 7:
                # Standard request
                start = time.time()
                metrics_tracker.track_request(endpoint)

                # Simulate success 98% of the time
                if i % 50 != 0:  # 2% error rate
                    prompt_tokens = 100 + (i * 3)
                    completion_tokens = 50 + (i * 2)

                    time.sleep(0.001)  # 1ms
                    latency_ms = (time.time() - start) * 1000

                    metrics_tracker.track_response(endpoint, latency_ms / 1000)
                    metrics_tracker.track_tokens(endpoint, prompt_tokens + completion_tokens)

                    cost_tracker.record_usage(
                        api_key=api_key,
                        model=model,
                        endpoint=endpoint,
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens,
                    )

                    model_tracker.track_request(
                        model=model,
                        endpoint=endpoint,
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens,
                        latency_ms=latency_ms,
                        user=api_key,
                        error=False,
                    )

                    error_tracker.record_success(endpoint, model)
                else:
                    # Error
                    error_tracker.record_error(
                        endpoint=endpoint,
                        status_code=500,
                        error_type="InternalServerError",
                        error_message="Internal error",
                        model=model,
                        api_key=api_key,
                    )
                    metrics_tracker.track_error(endpoint)
                    error_count += 1

                total_requests += 1

            # 30% streaming requests
            else:
                stream_id = f"stream-prod-{i}"
                streaming_tracker.start_stream(
                    stream_id=stream_id,
                    model=model,
                    prompt_tokens=150,
                )

                # Generate tokens
                time.sleep(0.02)  # TTFT
                streaming_tracker.record_token(stream_id, "First", chunk_size_bytes=20)

                for j in range(1, 10):
                    time.sleep(0.005)  # ITL
                    streaming_tracker.record_token(stream_id, f"t{j}", chunk_size_bytes=15)

                streaming_tracker.complete_stream(stream_id, "stop")

                cost_tracker.record_usage(
                    api_key=api_key,
                    model=model,
                    endpoint=endpoint,
                    prompt_tokens=150,
                    completion_tokens=10,
                )

                error_tracker.record_success(endpoint, model)
                streaming_count += 1
                total_requests += 1

        # === Comprehensive Verification ===

        # Error tracking
        error_metrics = error_tracker.get_metrics()
        assert error_metrics["total_requests"] == 100
        assert error_metrics["total_errors"] == error_count

        # SLO should be good (98% > 99.9% target might fail, but close)
        slo_status = error_tracker.get_slo_status()
        # With 2 errors out of 100, we have 98% success, which violates 99.9%
        # But that's expected in this test

        # Cost tracking - verify all users have costs
        for api_key in api_keys:
            cost_info = cost_tracker.get_cost_by_key(api_key)
            assert cost_info["total_cost"] > 0
            assert cost_info["requests"] > 0

        # Model tracking - verify all models used
        for model in models:
            model_stats = model_tracker.get_model_stats(model)
            assert model_stats["request_count"] > 0

        # Streaming tracking
        stream_metrics = streaming_tracker.get_metrics()
        assert stream_metrics.completed_streams == streaming_count
        assert stream_metrics.total_tokens_generated == streaming_count * 10

        # Verify metrics make sense
        assert stream_metrics.avg_ttft > 0
        assert stream_metrics.avg_itl > 0
        assert stream_metrics.avg_tokens_per_second > 0


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "-s"])
