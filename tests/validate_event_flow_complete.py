#!/usr/bin/env python3
"""
Complete Event Flow Validation Test

This test validates that events flow correctly through the entire system:
1. Events are emitted correctly
2. All subscribers receive events
3. Trackers are updated properly
4. No errors or timeouts occur
5. Metrics are incremented correctly

Visual output shows the complete event flow diagram.
"""

import asyncio
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

# Add fakeai directory to path to import modules without triggering app initialization
fakeai_dir = Path(__file__).parent.parent / "fakeai"
sys.path.insert(0, str(fakeai_dir))

# Import trackers
from cost_tracker import CostTracker
from dynamo_metrics import DynamoMetricsCollector
from error_metrics import ErrorMetricsTracker

# Import directly from modules (not from fakeai package)
from events.bus import EventBusFactory
from events.event_types import RequestCompletedEvent, RequestStartedEvent
from metrics import MetricsTracker
from model_metrics import ModelMetricsTracker


class EventFlowValidator:
    """Validates complete event flow through all subscribers."""

    def __init__(self):
        self.event_log: list[dict[str, Any]] = []
        self.subscriber_logs: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self.tracker_states_before: dict[str, Any] = {}
        self.tracker_states_after: dict[str, Any] = {}

    def log_event(self, event_type: str, event_data: dict[str, Any]) -> None:
        """Log an event emission."""
        self.event_log.append(
            {"timestamp": time.time(), "event_type": event_type, "data": event_data}
        )

    def log_subscriber_call(
        self, subscriber_name: str, event_type: str, success: bool, error: str = None
    ) -> None:
        """Log a subscriber receiving an event."""
        self.subscriber_logs[subscriber_name].append(
            {
                "timestamp": time.time(),
                "event_type": event_type,
                "success": success,
                "error": error,
            }
        )


async def test_complete_event_flow():
    """
    Test complete event flow from emission to all subscribers.

    This test:
    1. Creates all trackers
    2. Sets up event bus with all subscribers
    3. Captures initial state
    4. Emits a single request (started -> completed)
    5. Validates all subscribers received events
    6. Checks all trackers were updated
    7. Verifies no errors or timeouts
    8. Prints visual event flow diagram
    """
    print("\n" + "=" * 80)
    print("COMPLETE EVENT FLOW VALIDATION TEST")
    print("=" * 80 + "\n")

    validator = EventFlowValidator()

    # ========================================================================
    # Step 1: Initialize all trackers
    # ========================================================================
    print("Step 1: Initializing trackers...")
    print("-" * 80)

    metrics_tracker = MetricsTracker()
    cost_tracker = CostTracker()
    model_tracker = ModelMetricsTracker()
    dynamo_collector = DynamoMetricsCollector()
    error_tracker = ErrorMetricsTracker()

    print("✓ MetricsTracker initialized")
    print("✓ CostTracker initialized")
    print("✓ ModelMetricsTracker initialized")
    print("✓ DynamoMetricsCollector initialized")
    print("✓ ErrorMetricsTracker initialized")
    print()

    # ========================================================================
    # Step 2: Create event bus and register all subscribers
    # ========================================================================
    print("Step 2: Setting up event bus with subscribers...")
    print("-" * 80)

    event_bus = EventBusFactory.create_event_bus(
        metrics_tracker=metrics_tracker,
        cost_tracker=cost_tracker,
        model_tracker=model_tracker,
        dynamo_collector=dynamo_collector,
        error_tracker=error_tracker,
    )

    # Start the event bus
    await event_bus.start()
    print("✓ Event bus started")
    print()

    # Wait a moment for bus to be ready
    await asyncio.sleep(0.1)

    # ========================================================================
    # Step 3: Capture initial state of all trackers
    # ========================================================================
    print("Step 3: Capturing initial tracker states...")
    print("-" * 80)

    initial_states = {
        "metrics_tracker": {
            "endpoint": "/v1/chat/completions",
            "requests_before": 0,
            "responses_before": 0,
        },
        "cost_tracker": {
            "api_key": "test-api-key",
            "total_cost_before": 0.0,
        },
        "model_tracker": {
            "model": "gpt-4o",
            "requests_before": 0,
        },
        "dynamo_collector": {
            "total_requests_before": dynamo_collector.total_requests,
            "successful_requests_before": dynamo_collector.successful_requests,
        },
        "error_tracker": {
            "endpoint": "/v1/chat/completions",
            "success_count_before": 0,
        },
    }

    print("✓ Initial states captured")
    print(f"  - MetricsTracker: {initial_states['metrics_tracker']}")
    print(f"  - CostTracker: {initial_states['cost_tracker']}")
    print(f"  - ModelTracker: {initial_states['model_tracker']}")
    print(f"  - DynamoMetrics: {initial_states['dynamo_collector']}")
    print(f"  - ErrorTracker: {initial_states['error_tracker']}")
    print()

    # ========================================================================
    # Step 4: Emit RequestStartedEvent
    # ========================================================================
    print("Step 4: Emitting RequestStartedEvent...")
    print("-" * 80)

    request_id = "test-request-123"
    endpoint = "/v1/chat/completions"
    model = "gpt-4o"
    api_key = "test-api-key"

    started_event = RequestStartedEvent(
        request_id=request_id,
        endpoint=endpoint,
        method="POST",
        model=model,
        user_id="test-user",
        api_key=api_key,
        streaming=False,
        input_tokens=100,
        metadata={"api_key": api_key, "user_id": "test-user"},
    )

    validator.log_event("request.started", started_event.to_dict())
    await event_bus.publish(started_event)
    print(f"✓ RequestStartedEvent published (request_id={request_id})")
    print(f"  - Endpoint: {endpoint}")
    print(f"  - Model: {model}")
    print(f"  - Input tokens: 100")
    print()

    # Wait for event to be processed
    await asyncio.sleep(0.2)

    # ========================================================================
    # Step 5: Emit RequestCompletedEvent
    # ========================================================================
    print("Step 5: Emitting RequestCompletedEvent...")
    print("-" * 80)

    completed_event = RequestCompletedEvent(
        request_id=request_id,
        endpoint=endpoint,
        model=model,
        duration_ms=1500.0,
        status_code=200,
        input_tokens=100,
        output_tokens=200,
        cached_tokens=0,
        finish_reason="stop",
        metadata={
            "api_key": api_key,
            "user_id": "test-user",
            "worker_id": "worker-1",
        },
    )

    validator.log_event("request.completed", completed_event.to_dict())
    await event_bus.publish(completed_event)
    print(f"✓ RequestCompletedEvent published (request_id={request_id})")
    print(f"  - Duration: 1500ms")
    print(f"  - Status: 200")
    print(f"  - Output tokens: 200")
    print(f"  - Total tokens: 300")
    print()

    # Wait for events to be fully processed
    await asyncio.sleep(0.5)

    # ========================================================================
    # Step 6: Verify all subscribers received events
    # ========================================================================
    print("Step 6: Verifying subscriber event reception...")
    print("-" * 80)

    bus_stats = event_bus.get_stats()
    print(f"✓ Event bus stats:")
    print(f"  - Events published: {bus_stats['events_published']}")
    print(f"  - Events processed: {bus_stats['events_processed']}")
    print(f"  - Events dropped: {bus_stats['events_dropped']}")
    print(f"  - Queue depth: {bus_stats['queue_depth']}")
    print()

    # Check each subscriber type
    subscriber_types = [
        "request.started",
        "request.completed",
    ]

    print("Subscriber success counts:")
    all_subscribers_ok = True

    for event_type in subscriber_types:
        if event_type in bus_stats["subscribers"]:
            subscribers = bus_stats["subscribers"][event_type]
            print(f"\n  Event: {event_type}")
            for sub_info in subscribers:
                handler_name = sub_info["handler_name"]
                success_count = sub_info["success_count"]
                error_count = sub_info["error_count"]
                timeout_count = sub_info["timeout_count"]

                status = "✓" if error_count == 0 and timeout_count == 0 else "✗"
                print(
                    f"    {status} {handler_name}: {success_count} success, "
                    f"{error_count} errors, {timeout_count} timeouts"
                )

                if error_count > 0 or timeout_count > 0:
                    all_subscribers_ok = False

    print()

    # ========================================================================
    # Step 7: Verify trackers were updated
    # ========================================================================
    print("Step 7: Verifying tracker updates...")
    print("-" * 80)

    # Check MetricsTracker
    print("✓ MetricsTracker:")
    metrics = metrics_tracker.get_metrics()
    requests_metrics = metrics.get("requests", {}).get(endpoint, {})
    responses_metrics = metrics.get("responses", {}).get(endpoint, {})
    print(f"  - Requests rate: {requests_metrics.get('rate', 0):.4f}/s")
    print(f"  - Responses rate: {responses_metrics.get('rate', 0):.4f}/s")
    print(
        f"  - Avg latency: {responses_metrics.get('avg', 0)*1000:.2f}ms"
    )
    print()

    # Check CostTracker
    print("✓ CostTracker:")
    cost_summary = cost_tracker.get_cost_by_key(api_key)
    print(f"  - Total requests: {cost_summary.get('request_count', 0)}")
    print(f"  - Total tokens: {cost_summary.get('total_tokens', 0)}")
    print(f"  - Total cost: ${cost_summary.get('total_cost', 0):.6f}")
    print()

    # Check ModelMetricsTracker
    print("✓ ModelMetricsTracker:")
    try:
        model_data = model_tracker.get_model_stats(model)
        print(f"  - Model: {model}")
        print(f"  - Requests: {model_data.get('request_count', 0)}")
        print(f"  - Total tokens: {model_data.get('total_tokens', 0)}")
        print(
            f"  - Avg latency: {model_data.get('avg_latency_ms', 0):.2f}ms"
        )
    except Exception as e:
        print(f"  - No data for model {model} yet: {e}")
    print()

    # Check DynamoMetricsCollector
    print("✓ DynamoMetricsCollector:")
    print(f"  - Total requests: {dynamo_collector.total_requests}")
    print(f"  - Successful requests: {dynamo_collector.successful_requests}")
    print(f"  - Failed requests: {dynamo_collector.failed_requests}")
    print()

    # Check ErrorMetricsTracker
    print("✓ ErrorMetricsTracker:")
    error_summary = error_tracker.get_all_metrics()
    summary_section = error_summary.get("summary", {})
    recovery_section = error_summary.get("recovery", {})
    print(f"  - Total errors: {summary_section.get('total_errors', 0)}")
    print(f"  - Total successes: {recovery_section.get('success_after_error', 0)}")
    print(
        f"  - Error rate: {summary_section.get('error_rate_percentage', 0):.2f}%"
    )
    # Check if record_success was called (success_timestamps should have data)
    request_timestamps_count = len(error_tracker._request_timestamps) if hasattr(error_tracker, '_request_timestamps') else 0
    print(f"  - Total requests tracked: {request_timestamps_count}")
    print()

    # ========================================================================
    # Step 8: Print visual event flow diagram
    # ========================================================================
    print("Step 8: Event Flow Diagram")
    print("=" * 80)
    print()
    print_event_flow_diagram(bus_stats)
    print()

    # ========================================================================
    # Step 9: Final validation
    # ========================================================================
    print("=" * 80)
    print("VALIDATION RESULTS")
    print("=" * 80)
    print()

    # Check if all validations passed
    model_tracker_has_data = False
    try:
        model_data = model_tracker.get_model_stats(model)
        model_tracker_has_data = model_data.get("request_count", 0) > 0
    except:
        pass

    request_timestamps_count = len(error_tracker._request_timestamps) if hasattr(error_tracker, '_request_timestamps') else 0

    validations = {
        "Events published correctly": bus_stats["events_published"] == 2,
        "Events processed correctly": bus_stats["events_processed"] == 2,
        "No events dropped": bus_stats["events_dropped"] == 0,
        "All subscribers succeeded": all_subscribers_ok,
        "MetricsTracker updated": requests_metrics.get("rate", 0) > 0,
        "CostTracker updated": cost_summary.get("request_count", 0) > 0 or cost_summary.get("total_cost", 0) > 0,
        "ModelTracker updated": model_tracker_has_data,
        "DynamoMetrics updated": dynamo_collector.total_requests > 0,
        "ErrorTracker updated": request_timestamps_count > 0,
    }

    all_passed = all(validations.values())

    for check, passed in validations.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {check}")

    print()
    print("=" * 80)
    if all_passed:
        print("✓✓✓ ALL VALIDATIONS PASSED! ✓✓✓")
    else:
        print("✗✗✗ SOME VALIDATIONS FAILED ✗✗✗")
    print("=" * 80)
    print()

    # ========================================================================
    # Cleanup
    # ========================================================================
    print("Cleaning up...")
    await event_bus.stop(timeout=2.0)
    print("✓ Event bus stopped")
    print()

    return all_passed


def print_event_flow_diagram(bus_stats: dict[str, Any]) -> None:
    """Print a visual diagram of the event flow."""

    print("┌─────────────────────────────────────────────────────────────────────┐")
    print("│                        EVENT FLOW DIAGRAM                            │")
    print("└─────────────────────────────────────────────────────────────────────┘")
    print()
    print("  ┌──────────────┐")
    print("  │ REQUEST API  │")
    print("  └──────┬───────┘")
    print("         │")
    print("         ▼")
    print("  ┌──────────────────┐")
    print("  │ RequestStarted   │──────┐")
    print("  │    Event         │      │")
    print("  └──────┬───────────┘      │")
    print("         │                  │")
    print("         │                  ▼")
    print("         │          ┌─────────────────┐")
    print("         │          │   EVENT BUS     │")
    print("         │          │  (Async Queue)  │")
    print("         │          └────────┬────────┘")
    print("         │                   │")
    print("         │                   ├──────► MetricsTracker")
    print("         │                   │        - track_request()")
    print("         │                   │")
    print("         │                   ├──────► DynamoMetrics")
    print("         │                   │        - start_request()")
    print("         │                   │")
    print("         │                   └──────► ErrorTracker")
    print("         │                            - (monitoring)")
    print("         │")
    print("         ▼")
    print("  ┌──────────────────┐")
    print("  │ Process Request  │")
    print("  │   (Simulate)     │")
    print("  └──────┬───────────┘")
    print("         │")
    print("         ▼")
    print("  ┌──────────────────┐")
    print("  │ RequestCompleted │──────┐")
    print("  │    Event         │      │")
    print("  └──────────────────┘      │")
    print("                            │")
    print("                            ▼")
    print("                    ┌─────────────────┐")
    print("                    │   EVENT BUS     │")
    print("                    │  (Async Queue)  │")
    print("                    └────────┬────────┘")
    print("                             │")
    print("                             ├──────► MetricsTracker")
    print("                             │        - track_response()")
    print("                             │        - track_tokens()")
    print("                             │")
    print("                             ├──────► CostTracker")
    print("                             │        - record_usage()")
    print("                             │")
    print("                             ├──────► ModelTracker")
    print("                             │        - track_request()")
    print("                             │")
    print("                             ├──────► DynamoMetrics")
    print("                             │        - complete_request()")
    print("                             │")
    print("                             └──────► ErrorTracker")
    print("                                      - record_success()")
    print()

    # Print subscriber statistics
    print("┌─────────────────────────────────────────────────────────────────────┐")
    print("│                      SUBSCRIBER STATISTICS                           │")
    print("└─────────────────────────────────────────────────────────────────────┘")
    print()

    total_successes = 0
    total_errors = 0
    total_timeouts = 0

    for event_type, subscribers in bus_stats["subscribers"].items():
        if subscribers:
            print(f"Event Type: {event_type}")
            for sub in subscribers:
                print(f"  • {sub['handler_name']}")
                print(f"    - Successes: {sub['success_count']}")
                print(f"    - Errors: {sub['error_count']}")
                print(f"    - Timeouts: {sub['timeout_count']}")
                print(f"    - Avg processing time: {sub['avg_processing_time_ms']:.2f}ms")
                print()

                total_successes += sub["success_count"]
                total_errors += sub["error_count"]
                total_timeouts += sub["timeout_count"]

    print("TOTALS:")
    print(f"  ✓ Total successful handler calls: {total_successes}")
    print(f"  ✗ Total errors: {total_errors}")
    print(f"  ⏱ Total timeouts: {total_timeouts}")
    print()


async def main():
    """Main test runner."""
    try:
        success = await test_complete_event_flow()
        return 0 if success else 1
    except Exception as e:
        print(f"\n✗✗✗ TEST FAILED WITH EXCEPTION ✗✗✗")
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    import sys

    exit_code = asyncio.run(main())
    sys.exit(exit_code)
