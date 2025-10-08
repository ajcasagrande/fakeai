#!/usr/bin/env python3
"""
Standalone test runner for event types.
This can be run without pytest to avoid import issues.
Usage: python tests/test_event_types_standalone.py
"""

import json
import os
import sys
import time
import uuid

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Prevent fakeai package init from loading the app
import importlib
import importlib.util


# Manually load the modules we need
def load_module_directly(module_path, module_name):
    """Load a module directly from file path."""
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    return module, spec

# Load base module first
base_path = os.path.join(os.path.dirname(__file__), '../fakeai/events/base.py')
base_module, base_spec = load_module_directly(base_path, 'fakeai.events.base')
base_spec.loader.exec_module(base_module)

# Load event_types module
event_types_path = os.path.join(os.path.dirname(__file__), '../fakeai/events/event_types.py')
event_types_module, event_types_spec = load_module_directly(event_types_path, 'fakeai.events.event_types')
event_types_spec.loader.exec_module(event_types_module)

# Import what we need
BaseEvent = base_module.BaseEvent
RequestStartedEvent = event_types_module.RequestStartedEvent
RequestCompletedEvent = event_types_module.RequestCompletedEvent
RequestFailedEvent = event_types_module.RequestFailedEvent
TokensGeneratedEvent = event_types_module.TokensGeneratedEvent
TokenBatchGeneratedEvent = event_types_module.TokenBatchGeneratedEvent
StreamingTokenGeneratedEvent = event_types_module.StreamingTokenGeneratedEvent
FirstTokenGeneratedEvent = event_types_module.FirstTokenGeneratedEvent
StreamStartedEvent = event_types_module.StreamStartedEvent
StreamCompletedEvent = event_types_module.StreamCompletedEvent
ErrorOccurredEvent = event_types_module.ErrorOccurredEvent
ErrorPatternDetectedEvent = event_types_module.ErrorPatternDetectedEvent
CacheHitEvent = event_types_module.CacheHitEvent
CostCalculatedEvent = event_types_module.CostCalculatedEvent
LatencyMeasuredEvent = event_types_module.LatencyMeasuredEvent

# Test counters
tests_passed = 0
tests_failed = 0

def test(description):
    """Decorator for test functions."""
    def decorator(func):
        def wrapper():
            global tests_passed, tests_failed
            try:
                func()
                tests_passed += 1
                print(f"✓ {description}")
            except AssertionError as e:
                tests_failed += 1
                print(f"✗ {description}")
                print(f"  Error: {e}")
            except Exception as e:
                tests_failed += 1
                print(f"✗ {description}")
                print(f"  Unexpected error: {e}")
        return wrapper
    return decorator

# ============================================================================
# Base Event Tests
# ============================================================================

@test("BaseEvent auto-generates event_id")
def test_base_event_id():
    event = BaseEvent()
    assert event.event_id is not None
    assert isinstance(event.event_id, str)
    uuid.UUID(event.event_id)  # Should be valid UUID

@test("BaseEvent auto-generates timestamp")
def test_base_event_timestamp():
    before = time.time()
    event = BaseEvent()
    after = time.time()
    assert before <= event.timestamp <= after

@test("BaseEvent generates unique IDs")
def test_base_event_unique_ids():
    event1 = BaseEvent()
    event2 = BaseEvent()
    assert event1.event_id != event2.event_id

@test("BaseEvent to_dict is JSON serializable")
def test_base_event_serialization():
    event = BaseEvent(request_id="req-123")
    event_dict = event.to_dict()
    json_str = json.dumps(event_dict)
    assert len(json_str) > 0

# ============================================================================
# Request Lifecycle Events
# ============================================================================

@test("RequestStartedEvent creation with all fields")
def test_request_started_full():
    event = RequestStartedEvent(
        endpoint="/v1/chat/completions",
        method="POST",
        model="gpt-4",
        user_id="user-123",
        streaming=True,
        input_tokens=100,
    )
    assert event.event_type == "request.started"
    assert event.endpoint == "/v1/chat/completions"
    assert event.model == "gpt-4"
    assert event.streaming is True

@test("RequestStartedEvent default values")
def test_request_started_defaults():
    event = RequestStartedEvent()
    assert event.endpoint == ""
    assert event.method == "POST"
    assert event.streaming is False

@test("RequestCompletedEvent creation")
def test_request_completed():
    event = RequestCompletedEvent(
        endpoint="/v1/chat/completions",
        model="gpt-4",
        duration_ms=1234.5,
        input_tokens=50,
        output_tokens=150,
    )
    assert event.event_type == "request.completed"
    assert event.duration_ms == 1234.5
    assert event.input_tokens == 50

@test("RequestFailedEvent with error details")
def test_request_failed():
    event = RequestFailedEvent(
        endpoint="/v1/chat/completions",
        error_type="RateLimitError",
        error_message="Rate limit exceeded",
        status_code=429,
    )
    assert event.error_type == "RateLimitError"
    assert event.status_code == 429

# ============================================================================
# Token Events
# ============================================================================

@test("TokensGeneratedEvent creation")
def test_tokens_generated():
    event = TokensGeneratedEvent(
        model="gpt-4",
        prompt_tokens=100,
        completion_tokens=200,
    )
    assert event.event_type == "tokens.generated"
    assert event.prompt_tokens == 100

@test("TokenBatchGeneratedEvent with __post_init__")
def test_token_batch_post_init():
    event1 = TokenBatchGeneratedEvent(batch_size=0)
    assert event1.tokens == []

    event2 = TokenBatchGeneratedEvent(batch_size=0, tokens=None)
    assert event2.tokens == []

@test("StreamingTokenGeneratedEvent with sequence")
def test_streaming_token_sequence():
    events = [
        StreamingTokenGeneratedEvent(
            stream_id="stream-123",
            token=f"token_{i}",
            sequence_number=i
        )
        for i in range(5)
    ]
    for i, event in enumerate(events):
        assert event.sequence_number == i

@test("FirstTokenGeneratedEvent")
def test_first_token():
    event = FirstTokenGeneratedEvent(stream_id="stream-456", ttft_ms=123.45)
    assert event.event_type == "stream.first_token"
    assert event.ttft_ms == 123.45

# ============================================================================
# Stream Events
# ============================================================================

@test("StreamStartedEvent with optional fields")
def test_stream_started():
    event = StreamStartedEvent(
        stream_id="stream-001",
        model="gpt-4",
        temperature=0.7,
    )
    assert event.stream_id == "stream-001"
    assert event.temperature == 0.7

@test("StreamCompletedEvent default finish_reason")
def test_stream_completed():
    event = StreamCompletedEvent(stream_id="stream-002")
    assert event.finish_reason == "stop"

# ============================================================================
# Latency Events
# ============================================================================

@test("LatencyMeasuredEvent for TTFT")
def test_latency_ttft():
    event = LatencyMeasuredEvent(
        endpoint="/v1/chat/completions",
        latency_type="ttft",
        value_ms=123.45,
    )
    assert event.latency_type == "ttft"
    assert event.value_ms == 123.45

@test("LatencyMeasuredEvent for TPOT")
def test_latency_tpot():
    event = LatencyMeasuredEvent(
        latency_type="tpot",
        value_ms=15.2,
    )
    assert event.latency_type == "tpot"

# ============================================================================
# Cache Events
# ============================================================================

@test("CacheHitEvent creation")
def test_cache_hit():
    event = CacheHitEvent(
        cache_type="kv",
        cached_tokens=50,
        speedup_ms=100.0,
    )
    assert event.event_type == "cache.hit"
    assert event.cached_tokens == 50

# ============================================================================
# Error Events
# ============================================================================

@test("ErrorOccurredEvent with fingerprinting")
def test_error_occurred():
    event = ErrorOccurredEvent(
        endpoint="/v1/chat/completions",
        error_type="TimeoutError",
        error_message="Request timed out",
    )
    assert event.error_type == "TimeoutError"
    assert event.error_message == "Request timed out"

@test("ErrorPatternDetectedEvent with __post_init__")
def test_error_pattern():
    event1 = ErrorPatternDetectedEvent(
        error_signature="sig",
        error_type="err",
    )
    assert event1.affected_endpoints == []

    event2 = ErrorPatternDetectedEvent(
        error_signature="sig",
        error_type="err",
        affected_endpoints=None,
    )
    assert event2.affected_endpoints == []

# ============================================================================
# Cost Events
# ============================================================================

@test("CostCalculatedEvent with float values")
def test_cost_calculated():
    event = CostCalculatedEvent(
        model="gpt-4",
        input_cost=0.005,
        output_cost=0.010,
        total_cost=0.015,
    )
    assert event.model == "gpt-4"
    assert event.total_cost == 0.015

# ============================================================================
# Serialization Tests
# ============================================================================

@test("All events have base fields")
def test_all_have_base_fields():
    events = [
        RequestStartedEvent(),
        TokensGeneratedEvent(),
        StreamStartedEvent(stream_id="test"),
        ErrorOccurredEvent(error_type="test"),
    ]
    for event in events:
        event_dict = event.to_dict()
        assert "event_id" in event_dict
        assert "event_type" in event_dict
        assert "timestamp" in event_dict

@test("Event serialization includes all fields")
def test_serialization_complete():
    event = RequestStartedEvent(
        endpoint="/test",
        model="gpt-4",
        streaming=True,
    )
    event_dict = event.to_dict()
    assert event_dict["endpoint"] == "/test"
    assert event_dict["model"] == "gpt-4"
    assert event_dict["streaming"] is True

@test("Multiple event types are JSON serializable")
def test_multiple_json_serializable():
    events = [
        RequestStartedEvent(endpoint="/test"),
        RequestCompletedEvent(model="test"),
        TokensGeneratedEvent(model="test"),
        CacheHitEvent(cache_type="kv"),
    ]
    for event in events:
        event_dict = event.to_dict()
        json_str = json.dumps(event_dict)
        assert len(json_str) > 0

# ============================================================================
# Run all tests
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("Running Event Types Tests")
    print("=" * 70)
    print()

    # Get all test functions
    test_functions = [
        obj for name, obj in globals().items()
        if callable(obj) and name.startswith('test_')
    ]

    # Run all tests
    for test_func in test_functions:
        test_func()

    print()
    print("=" * 70)
    print(f"Results: {tests_passed} passed, {tests_failed} failed")
    print("=" * 70)

    sys.exit(0 if tests_failed == 0 else 1)
