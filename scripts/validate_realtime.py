#!/usr/bin/env python3
"""Quick validation script for Realtime WebSocket API."""

import json
from fakeai.models import (
    RealtimeSession,
    RealtimeEvent,
    RealtimeEventType,
    RealtimeSessionConfig,
)
from fakeai.fakeai_service import RealtimeSessionHandler
from fakeai.config import AppConfig
from fakeai.fakeai_service import FakeAIService

def test_models():
    """Test that all models can be instantiated."""
    print("Testing Realtime models...")

    # Test session config
    config = RealtimeSessionConfig()
    print(f"  ✓ RealtimeSessionConfig: modalities={config.modalities}")

    # Test session
    session = RealtimeSession(
        id="test_session",
        model="openai/gpt-oss-120b-realtime",
    )
    print(f"  ✓ RealtimeSession: id={session.id}")

    # Test event
    event = RealtimeEvent(
        type=RealtimeEventType.SESSION_CREATED,
        event_id="test_event",
        session=session,
    )
    print(f"  ✓ RealtimeEvent: type={event.type}")

    # Test serialization
    event_json = event.model_dump_json()
    event_dict = json.loads(event_json)
    print(f"  ✓ Event serialization: {len(event_json)} bytes")

    print("✓ All model tests passed!\n")


def test_session_handler():
    """Test the RealtimeSessionHandler."""
    print("Testing RealtimeSessionHandler...")

    config = AppConfig(response_delay=0.0)
    service = FakeAIService(config)
    handler = RealtimeSessionHandler("openai/gpt-oss-120b", config, service)

    print(f"  ✓ Handler created: session_id={handler.session_id}")

    # Test session creation
    event = handler._create_event(
        RealtimeEventType.SESSION_CREATED,
        session=handler.session,
    )
    print(f"  ✓ Session created event: {event.type}")

    # Test session update
    update_event = handler.update_session({
        "instructions": "Test instructions",
        "temperature": 0.9,
    })
    print(f"  ✓ Session update: {update_event.type}")
    print(f"    Instructions: {handler.session.instructions}")
    print(f"    Temperature: {handler.session.temperature}")

    # Test audio buffer
    events = handler.append_audio_buffer("test_audio_chunk_1")
    print(f"  ✓ Audio append (chunk 1): {len(events)} events")

    events = handler.append_audio_buffer("test_audio_chunk_2")
    print(f"  ✓ Audio append (chunk 2): {len(events)} events")

    events = handler.append_audio_buffer("test_audio_chunk_3")
    print(f"  ✓ Audio append (chunk 3): {len(events)} events")

    # Check if speech was detected
    if handler.speech_detected:
        print(f"  ✓ Speech detected after {len(handler.audio_buffer)} chunks")

    # Test audio clear
    clear_event = handler.clear_audio_buffer()
    print(f"  ✓ Audio clear: {clear_event.type}")

    # Test conversation item creation
    item_event = handler.create_conversation_item({
        "type": "message",
        "role": "user",
        "content": [{"type": "input_text", "text": "Hello!"}],
    })
    print(f"  ✓ Conversation item created: {item_event.type}")
    print(f"    Total items: {len(handler.conversation_items)}")

    print("✓ All handler tests passed!\n")


async def test_streaming_response():
    """Test streaming response generation."""
    import asyncio

    print("Testing streaming response...")

    config = AppConfig(response_delay=0.0)
    service = FakeAIService(config)
    handler = RealtimeSessionHandler("openai/gpt-oss-120b", config, service)

    # Add a conversation item
    handler.create_conversation_item({
        "type": "message",
        "role": "user",
        "content": [{"type": "input_text", "text": "Hello!"}],
    })

    # Generate response
    events = []
    async for event in handler.create_response({"modalities": ["text"]}):
        events.append(event)
        if len(events) >= 10:  # Limit events for testing
            break

    print(f"  ✓ Generated {len(events)} events")
    event_types = [e.type for e in events]
    print(f"  ✓ Event types: {', '.join(str(et).split('.')[-1] for et in event_types[:5])}...")

    print("✓ Streaming response test passed!\n")


def main():
    """Run all validation tests."""
    import asyncio

    print("=" * 60)
    print("FakeAI Realtime WebSocket API Validation")
    print("=" * 60)
    print()

    try:
        test_models()
        test_session_handler()
        asyncio.run(test_streaming_response())

        print("=" * 60)
        print("✓ ALL VALIDATION TESTS PASSED!")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ Validation failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
