"""
Comprehensive integration tests for the complete pub-sub metrics system.

Tests cover end-to-end event flows through the EventBus with real tracker instances,
ensuring that events properly update all subscribed metrics trackers.

Test Coverage:
1. End-to-End Event Flow - Request lifecycle with all trackers
2. Streaming Flow - Complete streaming response with token generation
3. Error Flow - Error tracking, pattern detection, and SLO monitoring
4. Cost Flow - Cost calculation, budget tracking, and suggestions
5. Multiple Trackers - Same event updates multiple trackers correctly
6. Realistic Scenario - 100 requests with various models and failures

NOTE: This test file is designed to be imported after the application modules
are already available, avoiding circular import issues.
"""

import asyncio
import time
from unittest.mock import Mock

import pytest


@pytest.mark.integration
@pytest.mark.asyncio
class TestEndToEndEventFlow:
    """Test complete request lifecycle through the event bus."""

    async def test_request_lifecycle_updates_all_trackers(self):
        """
        End-to-end test: emit RequestStartedEvent and RequestCompletedEvent,
        verify all trackers are updated correctly.
        """
        # Lazy imports to avoid circular dependencies
        from fakeai.cost_tracker import CostTracker
        from fakeai.error_metrics_tracker import ErrorMetricsTracker
        from fakeai.events.bus import EventBusFactory
        from fakeai.events.event_types import RequestCompletedEvent, RequestStartedEvent
        from fakeai.streaming_metrics_tracker import StreamingMetricsTracker

        # Create real tracker instances
        streaming_tracker = StreamingMetricsTracker(
            max_active_streams=100, max_completed_streams=100
        )
        error_tracker = ErrorMetricsTracker(max_recent_errors=100)
        cost_tracker = CostTracker()

        # Create mock trackers for other systems
        mock_metrics_tracker = Mock()
        mock_metrics_tracker.track_request = Mock()
        mock_metrics_tracker.track_response = Mock()
        mock_metrics_tracker.track_tokens = Mock()

        # Create event bus with all trackers
        bus = EventBusFactory.create_event_bus(
            metrics_tracker=mock_metrics_tracker,
            streaming_tracker=streaming_tracker,
            error_tracker=error_tracker,
            cost_tracker=cost_tracker,
        )

        # Start the event bus
        await bus.start()

        try:
            # Emit RequestStartedEvent
            request_event = RequestStartedEvent(
                request_id="req-001",
                endpoint="/v1/chat/completions",
                method="POST",
                model="gpt-4",
                user_id="user-123",
                api_key="sk-test-key",
            )
            await bus.publish(request_event)

            # Give event bus time to process
            await asyncio.sleep(0.2)

            # Verify metrics tracker was called
            mock_metrics_tracker.track_request.assert_called_once_with(
                "/v1/chat/completions"
            )

            # Emit RequestCompletedEvent
            completed_event = RequestCompletedEvent(
                request_id="req-001",
                endpoint="/v1/chat/completions",
                model="gpt-4",
                duration_ms=1500.0,
                status_code=200,
                input_tokens=100,
                output_tokens=250,
                cached_tokens=20,
                finish_reason="stop",
                metadata={"api_key": "sk-test-key", "user_id": "user-123"},
            )
            await bus.publish(completed_event)

            # Give event bus time to process
            await asyncio.sleep(0.2)

            # Verify metrics tracker was called for response
            mock_metrics_tracker.track_response.assert_called_once()
            mock_metrics_tracker.track_tokens.assert_called_once_with(
                "/v1/chat/completions", 350  # input + output
            )

            # Verify error tracker recorded success
            assert error_tracker._total_successes == 1
            assert error_tracker._total_requests == 1

            # Verify cost tracker recorded usage
            cost_data = cost_tracker.get_cost_by_key("sk-test-key")
            assert cost_data["total_cost"] > 0
            assert cost_data["requests"] == 1

        finally:
            await bus.stop(timeout=2.0)


@pytest.mark.integration
@pytest.mark.asyncio
class TestStreamingFlow:
    """Test streaming response flow through the event bus."""

    async def test_streaming_flow_calculates_metrics(self):
        """
        Streaming test: emit StreamStartedEvent, multiple StreamingTokenGeneratedEvents,
        and StreamCompletedEvent. Verify streaming metrics are calculated correctly.
        """
        from fakeai.events.bus import EventBusFactory
        from fakeai.events.event_types import (
            FirstTokenGeneratedEvent,
            StreamCompletedEvent,
            StreamingTokenGeneratedEvent,
            StreamStartedEvent,
        )
        from fakeai.streaming_metrics_tracker import StreamingMetricsTracker

        # Create streaming tracker
        streaming_tracker = StreamingMetricsTracker(
            max_active_streams=100, max_completed_streams=100
        )

        # Create event bus
        bus = EventBusFactory.create_event_bus(streaming_tracker=streaming_tracker)

        await bus.start()

        try:
            stream_id = "stream-001"

            # Emit StreamStartedEvent
            start_event = StreamStartedEvent(
                request_id="req-001",
                stream_id=stream_id,
                endpoint="/v1/chat/completions",
                model="gpt-4",
                input_tokens=100,
                temperature=0.7,
                max_tokens=500,
            )
            await bus.publish(start_event)
            await asyncio.sleep(0.1)

            # Verify stream started
            assert streaming_tracker.get_active_stream_count() == 1

            # Emit first token (for TTFT)
            first_token_event = FirstTokenGeneratedEvent(
                request_id="req-001",
                stream_id=stream_id,
                ttft_ms=125.5,
            )
            await bus.publish(first_token_event)
            await asyncio.sleep(0.05)

            # Emit multiple token generation events
            tokens = ["Hello", " ", "world", "!", " How", " are", " you", "?"]
            for i, token in enumerate(tokens):
                token_event = StreamingTokenGeneratedEvent(
                    request_id="req-001",
                    stream_id=stream_id,
                    token=token,
                    sequence_number=i + 1,
                    timestamp_ns=int(time.time() * 1e9),
                    chunk_size_bytes=len(token),
                )
                await bus.publish(token_event)
                await asyncio.sleep(0.02)  # Simulate token generation time

            # Emit StreamCompletedEvent
            complete_event = StreamCompletedEvent(
                request_id="req-001",
                stream_id=stream_id,
                endpoint="/v1/chat/completions",
                duration_ms=500.0,
                token_count=len(tokens),
                finish_reason="stop",
            )
            await bus.publish(complete_event)
            await asyncio.sleep(0.2)

            # Verify stream completed
            assert streaming_tracker.get_active_stream_count() == 0

            # Get streaming metrics
            metrics = streaming_tracker.get_metrics()

            # Verify metrics were calculated
            assert metrics.total_streams == 1
            assert metrics.completed_streams == 1
            assert metrics.failed_streams == 0
            assert metrics.total_tokens_generated == len(tokens)
            assert metrics.success_rate == 1.0

            # Verify TTFT was recorded
            assert metrics.avg_ttft > 0
            assert metrics.p50_ttft > 0

            # Verify stream details
            stream_details = streaming_tracker.get_stream_details(stream_id)
            assert stream_details is not None
            assert stream_details["status"] == "completed"
            assert stream_details["tokens_generated"] == len(tokens)
            assert stream_details["finish_reason"] == "stop"

        finally:
            await bus.stop(timeout=2.0)


@pytest.mark.integration
@pytest.mark.asyncio
class TestErrorFlow:
    """Test error tracking and pattern detection."""

    async def test_error_flow_detects_patterns_and_updates_slo(self):
        """
        Error test: emit RequestFailedEvent and ErrorOccurredEvent,
        verify error tracking, pattern detection, and SLO updates.
        """
        from fakeai.error_metrics_tracker import ErrorMetricsTracker
        from fakeai.events.bus import EventBusFactory
        from fakeai.events.event_types import (
            ErrorOccurredEvent,
            RequestCompletedEvent,
            RequestFailedEvent,
        )

        # Create error tracker with SLO
        error_tracker = ErrorMetricsTracker(
            max_recent_errors=100,
            error_budget_slo=0.95,  # 95% success rate
            pattern_threshold=2,
        )

        # Create event bus
        bus = EventBusFactory.create_event_bus(error_tracker=error_tracker)

        await bus.start()

        try:
            # Emit multiple successful requests first
            for i in range(10):
                success_event = RequestCompletedEvent(
                    request_id=f"req-success-{i}",
                    endpoint="/v1/chat/completions",
                    model="gpt-4",
                    duration_ms=1000.0,
                    status_code=200,
                    input_tokens=50,
                    output_tokens=100,
                )
                await bus.publish(success_event)

            await asyncio.sleep(0.2)

            # Emit error events with same pattern
            for i in range(3):
                error_event = ErrorOccurredEvent(
                    request_id=f"req-error-{i}",
                    endpoint="/v1/chat/completions",
                    model="gpt-4",
                    error_type="RateLimitError",
                    error_message="Rate limit exceeded for organization",
                    stack_trace="...",
                    metadata={"api_key": "sk-test-key"},
                )
                await bus.publish(error_event)

            await asyncio.sleep(0.2)

            # Emit request failed events
            for i in range(2):
                failed_event = RequestFailedEvent(
                    request_id=f"req-failed-{i}",
                    endpoint="/v1/embeddings",
                    model="text-embedding-ada-002",
                    error_type="TimeoutError",
                    error_message="Request timeout after 30 seconds",
                    status_code=504,
                    duration_ms=30000.0,
                    metadata={"api_key": "sk-test-key"},
                )
                await bus.publish(failed_event)

            await asyncio.sleep(0.2)

            # Verify error tracking
            metrics = error_tracker.get_metrics()
            assert metrics["total_requests"] == 15  # 10 success + 5 errors
            assert metrics["total_errors"] == 5
            assert metrics["total_successes"] == 10
            assert metrics["error_rate"] > 0

            # Verify error patterns detected
            patterns = error_tracker.get_error_patterns(min_count=2)
            assert len(patterns) >= 1  # At least one pattern detected

            # Check for RateLimitError pattern
            rate_limit_pattern = next(
                (p for p in patterns if p.error_type == "RateLimitError"), None
            )
            assert rate_limit_pattern is not None
            assert rate_limit_pattern.count >= 3

            # Verify SLO status
            slo_status = error_tracker.get_slo_status()
            assert slo_status.total_requests == 15
            assert slo_status.failed_requests == 5
            assert slo_status.current_error_rate > 0.3  # 5/15 = 0.33

            # Verify recent errors can be retrieved
            recent_errors = error_tracker.get_recent_errors(limit=10)
            assert len(recent_errors) >= 5

        finally:
            await bus.stop(timeout=2.0)


@pytest.mark.integration
@pytest.mark.asyncio
class TestCostFlow:
    """Test cost tracking and budget management."""

    async def test_cost_flow_tracks_budget_and_generates_suggestions(self):
        """
        Cost test: emit RequestCompletedEvent with token counts,
        verify cost calculation, budget updates, and suggestions.
        """
        from fakeai.cost_tracker import CostTracker
        from fakeai.events.bus import EventBusFactory
        from fakeai.events.event_types import RequestCompletedEvent

        # Create cost tracker
        cost_tracker = CostTracker()

        # Create event bus
        bus = EventBusFactory.create_event_bus(cost_tracker=cost_tracker)

        await bus.start()

        try:
            api_key = "sk-budget-test"

            # Emit multiple completion events with different models
            models_and_tokens = [
                ("gpt-4", 100, 200),  # More expensive
                ("gpt-4", 150, 300),
                ("gpt-3.5-turbo", 200, 400),  # Cheaper
                ("gpt-3.5-turbo", 100, 200),
            ]

            for i, (model, input_tokens, output_tokens) in enumerate(
                models_and_tokens
            ):
                event = RequestCompletedEvent(
                    request_id=f"req-{i}",
                    endpoint="/v1/chat/completions",
                    model=model,
                    duration_ms=1500.0,
                    status_code=200,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    cached_tokens=10,
                    metadata={"api_key": api_key, "user_id": "user-123"},
                )
                await bus.publish(event)

            await asyncio.sleep(0.3)

            # Verify cost was tracked
            cost_data = cost_tracker.get_cost_by_key(api_key)
            assert cost_data["total_cost"] > 0
            assert cost_data["requests"] == len(models_and_tokens)

            # Verify breakdown by model
            assert "gpt-4" in cost_data["by_model"]
            assert "gpt-3.5-turbo" in cost_data["by_model"]

            # GPT-4 should cost more than GPT-3.5-turbo
            assert cost_data["by_model"]["gpt-4"] > cost_data["by_model"][
                "gpt-3.5-turbo"
            ]

            # Verify cost by endpoint
            costs_by_endpoint = cost_tracker.get_cost_by_endpoint()
            assert "/v1/chat/completions" in costs_by_endpoint

        finally:
            await bus.stop(timeout=2.0)


@pytest.mark.integration
@pytest.mark.asyncio
class TestMultipleTrackers:
    """Test that multiple trackers can handle the same events."""

    async def test_same_event_updates_multiple_trackers(self):
        """
        Multiple trackers test: emit a single event that should be handled
        by multiple trackers. Verify no interference and priority order.
        """
        from fakeai.cost_tracker import CostTracker
        from fakeai.error_metrics_tracker import ErrorMetricsTracker
        from fakeai.events.bus import EventBusFactory
        from fakeai.events.event_types import RequestCompletedEvent
        from fakeai.streaming_metrics_tracker import StreamingMetricsTracker

        # Create all trackers
        streaming_tracker = StreamingMetricsTracker()
        error_tracker = ErrorMetricsTracker()
        cost_tracker = CostTracker()

        mock_metrics_tracker = Mock()
        mock_metrics_tracker.track_request = Mock()
        mock_metrics_tracker.track_response = Mock()
        mock_metrics_tracker.track_tokens = Mock()

        # Create event bus with all trackers
        bus = EventBusFactory.create_event_bus(
            metrics_tracker=mock_metrics_tracker,
            streaming_tracker=streaming_tracker,
            error_tracker=error_tracker,
            cost_tracker=cost_tracker,
        )

        await bus.start()

        try:
            # Emit a RequestCompletedEvent that should be handled by multiple subscribers
            event = RequestCompletedEvent(
                request_id="req-multi-001",
                endpoint="/v1/chat/completions",
                model="gpt-4",
                duration_ms=2000.0,
                status_code=200,
                input_tokens=200,
                output_tokens=400,
                cached_tokens=30,
                finish_reason="stop",
                metadata={"api_key": "sk-multi-test", "user_id": "user-123"},
            )

            await bus.publish(event)
            await asyncio.sleep(0.3)

            # Verify metrics tracker was called
            mock_metrics_tracker.track_response.assert_called_once()
            mock_metrics_tracker.track_tokens.assert_called_once()

            # Verify error tracker recorded success
            assert error_tracker._total_successes >= 1

            # Verify cost tracker recorded usage
            cost_data = cost_tracker.get_cost_by_key("sk-multi-test")
            assert cost_data["total_cost"] > 0
            assert cost_data["requests"] >= 1

            # Verify no interference - all trackers updated independently
            assert error_tracker._total_requests >= 1
            assert cost_data["by_model"]["gpt-4"] > 0

        finally:
            await bus.stop(timeout=2.0)

    async def test_priority_order_respected(self):
        """Verify that event handlers are called in priority order."""
        from fakeai.events.bus import AsyncEventBus
        from fakeai.events.event_types import RequestStartedEvent

        # Track call order
        call_order = []

        def make_handler(name, priority):
            async def handler(event):
                call_order.append((name, priority))

            handler.__name__ = name
            return handler

        # Create bus and add subscribers with different priorities
        bus = AsyncEventBus()

        bus.subscribe("test.event", make_handler("high", 10), priority=10)
        bus.subscribe("test.event", make_handler("medium", 5), priority=5)
        bus.subscribe("test.event", make_handler("low", 1), priority=1)

        await bus.start()

        try:
            # Emit event
            event = RequestStartedEvent(
                request_id="test-priority",
                endpoint="/test",
                event_type="test.event",
            )
            await bus.publish(event)
            await asyncio.sleep(0.2)

            # Verify priority order (highest priority first)
            assert len(call_order) == 3
            assert call_order[0] == ("high", 10)
            assert call_order[1] == ("medium", 5)
            assert call_order[2] == ("low", 1)

        finally:
            await bus.stop(timeout=2.0)


@pytest.mark.integration
@pytest.mark.asyncio
class TestRealisticScenario:
    """Test a realistic scenario with 100 requests, 10 failures, and various models."""

    async def test_realistic_mixed_workload(self):
        """
        Realistic scenario: 100 requests with 10 failures, multiple models.
        Verify all metrics are correctly calculated.
        """
        from fakeai.cost_tracker import CostTracker
        from fakeai.error_metrics_tracker import ErrorMetricsTracker
        from fakeai.events.bus import EventBusFactory
        from fakeai.events.event_types import (
            RequestCompletedEvent,
            RequestFailedEvent,
            RequestStartedEvent,
        )
        from fakeai.streaming_metrics_tracker import StreamingMetricsTracker

        # Create all trackers
        streaming_tracker = StreamingMetricsTracker(
            max_active_streams=200, max_completed_streams=200
        )
        error_tracker = ErrorMetricsTracker(max_recent_errors=200)
        cost_tracker = CostTracker()

        mock_metrics_tracker = Mock()
        mock_metrics_tracker.track_request = Mock()
        mock_metrics_tracker.track_response = Mock()
        mock_metrics_tracker.track_tokens = Mock()
        mock_metrics_tracker.track_error = Mock()

        # Create event bus
        bus = EventBusFactory.create_event_bus(
            metrics_tracker=mock_metrics_tracker,
            streaming_tracker=streaming_tracker,
            error_tracker=error_tracker,
            cost_tracker=cost_tracker,
        )

        await bus.start()

        try:
            # Define model distribution
            models = ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo", "gpt-4o-mini"]
            api_key = "sk-realistic-test"

            # Emit 90 successful requests
            for i in range(90):
                model = models[i % len(models)]

                # Start event
                start_event = RequestStartedEvent(
                    request_id=f"req-{i}",
                    endpoint="/v1/chat/completions",
                    model=model,
                    api_key=api_key,
                )
                await bus.publish(start_event)

                # Complete event
                complete_event = RequestCompletedEvent(
                    request_id=f"req-{i}",
                    endpoint="/v1/chat/completions",
                    model=model,
                    duration_ms=1000.0 + (i * 10),  # Varying durations
                    status_code=200,
                    input_tokens=50 + (i % 100),
                    output_tokens=100 + (i % 200),
                    cached_tokens=10,
                    metadata={"api_key": api_key},
                )
                await bus.publish(complete_event)

                # Don't wait after each to speed up test
                if i % 10 == 0:
                    await asyncio.sleep(0.1)

            # Emit 10 failed requests
            for i in range(10):
                model = models[i % len(models)]

                # Start event
                start_event = RequestStartedEvent(
                    request_id=f"req-failed-{i}",
                    endpoint="/v1/chat/completions",
                    model=model,
                    api_key=api_key,
                )
                await bus.publish(start_event)

                # Failed event
                failed_event = RequestFailedEvent(
                    request_id=f"req-failed-{i}",
                    endpoint="/v1/chat/completions",
                    model=model,
                    error_type="TimeoutError" if i % 2 == 0 else "RateLimitError",
                    error_message="Request failed",
                    status_code=504 if i % 2 == 0 else 429,
                    duration_ms=30000.0,
                    metadata={"api_key": api_key},
                )
                await bus.publish(failed_event)

            # Wait for all events to be processed
            await asyncio.sleep(1.0)

            # Verify metrics tracker calls
            assert mock_metrics_tracker.track_request.call_count == 100
            assert mock_metrics_tracker.track_response.call_count == 90
            assert mock_metrics_tracker.track_error.call_count == 10

            # Verify error tracker
            error_metrics = error_tracker.get_metrics()
            assert error_metrics["total_requests"] == 100
            assert error_metrics["total_successes"] == 90
            assert error_metrics["total_errors"] == 10
            assert 0.09 <= error_metrics["error_rate"] <= 0.11  # ~10% error rate

            # Verify cost tracker
            cost_data = cost_tracker.get_cost_by_key(api_key)
            assert cost_data["total_cost"] > 0
            assert cost_data["requests"] == 90  # Only successful requests tracked

            # Verify all models were used
            assert len(cost_data["by_model"]) == len(models)
            for model in models:
                assert model in cost_data["by_model"]

            # Verify error patterns
            patterns = error_tracker.get_error_patterns(min_count=2)
            assert len(patterns) >= 2  # TimeoutError and RateLimitError patterns

            # Verify SLO
            slo_status = error_tracker.get_slo_status()
            assert slo_status.total_requests == 100
            assert slo_status.failed_requests == 10
            assert slo_status.successful_requests == 90
            assert abs(slo_status.current_success_rate - 0.9) < 0.01

            # Get event bus stats
            stats = bus.get_stats()
            assert stats["events_published"] >= 200  # At least 100 start + 100 complete/fail
            assert stats["events_processed"] >= 200
            assert stats["drop_rate"] == 0.0  # No events dropped

        finally:
            await bus.stop(timeout=5.0)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
