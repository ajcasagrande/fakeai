"""
Tests for the Realtime WebSocket API.

This module tests the WebSocket-based Realtime API for bidirectional streaming
conversations with audio and text support, voice activity detection, and function calling.
"""

#  SPDX-License-Identifier: Apache-2.0

import asyncio
import base64
import json

import pytest
from fastapi.testclient import TestClient

from fakeai.app import app
from fakeai.models import (
    RealtimeContentType,
    RealtimeEventType,
    RealtimeItemRole,
    RealtimeItemType,
    RealtimeModality,
)


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


def test_realtime_websocket_connection(client):
    """Test basic WebSocket connection."""
    with client.websocket_connect(
        "/v1/realtime?model=openai/gpt-oss-120b-realtime-preview-2024-10-01"
    ) as websocket:
        # Should receive session.created event
        data = websocket.receive_text()
        event = json.loads(data)

        assert event["type"] == "session.created"
        assert "session" in event
        assert (
            event["session"]["model"]
            == "openai/gpt-oss-120b-realtime-preview-2024-10-01"
        )
        assert "id" in event["session"]
        assert event["session"]["object"] == "realtime.session"


def test_realtime_session_update(client):
    """Test session configuration update."""
    with client.websocket_connect(
        "/v1/realtime?model=openai/gpt-oss-120b-realtime-preview-2024-10-01"
    ) as websocket:
        # Receive session.created
        session_created = json.loads(websocket.receive_text())
        assert session_created["type"] == "session.created"

        # Send session.update
        websocket.send_json(
            {
                "type": "session.update",
                "session": {
                    "modalities": ["text", "audio"],
                    "instructions": "You are a helpful assistant.",
                    "voice": "alloy",
                    "temperature": 0.8,
                },
            }
        )

        # Receive session.updated
        data = websocket.receive_text()
        event = json.loads(data)

        assert event["type"] == "session.updated"
        assert event["session"]["instructions"] == "You are a helpful assistant."
        assert event["session"]["voice"] == "alloy"
        assert event["session"]["temperature"] == 0.8


def test_realtime_audio_buffer_append(client):
    """Test appending audio to the input buffer."""
    with client.websocket_connect(
        "/v1/realtime?model=openai/gpt-oss-120b-realtime-preview-2024-10-01"
    ) as websocket:
        # Receive session.created
        session_created = json.loads(websocket.receive_text())
        assert session_created["type"] == "session.created"

        # Send audio buffer append events (simulate audio chunks)
        fake_audio = base64.b64encode(b"fake audio data chunk 1").decode("utf-8")

        for i in range(5):
            websocket.send_json(
                {
                    "type": "input_audio_buffer.append",
                    "audio": fake_audio + str(i),
                }
            )

            # After 3 chunks, should detect speech
            if i >= 2:
                # Receive speech_started event
                data = websocket.receive_text()
                event = json.loads(data)
                if event["type"] == "input_audio_buffer.speech_started":
                    assert "audio_end_ms" in event
                    break


def test_realtime_audio_buffer_commit(client):
    """Test committing audio buffer and creating conversation item."""
    with client.websocket_connect(
        "/v1/realtime?model=openai/gpt-oss-120b-realtime-preview-2024-10-01"
    ) as websocket:
        # Receive session.created
        session_created = json.loads(websocket.receive_text())
        assert session_created["type"] == "session.created"

        # Append audio chunks
        fake_audio = base64.b64encode(b"fake audio data").decode("utf-8")
        for i in range(4):
            websocket.send_json(
                {
                    "type": "input_audio_buffer.append",
                    "audio": fake_audio,
                }
            )

        # Speech started should be received
        speech_started = json.loads(websocket.receive_text())
        assert speech_started["type"] == "input_audio_buffer.speech_started"

        # Commit the audio buffer
        websocket.send_json(
            {
                "type": "input_audio_buffer.commit",
            }
        )

        # Should receive multiple events
        events = []
        for _ in range(3):
            data = websocket.receive_text()
            events.append(json.loads(data))

        # Check event types
        event_types = [e["type"] for e in events]
        assert "input_audio_buffer.speech_stopped" in event_types
        assert "input_audio_buffer.committed" in event_types
        assert "conversation.item.created" in event_types

        # Check conversation item
        item_created = next(
            e for e in events if e["type"] == "conversation.item.created"
        )
        assert item_created["item"]["type"] == "message"
        assert item_created["item"]["role"] == "user"
        assert len(item_created["item"]["content"]) > 0
        assert item_created["item"]["content"][0]["type"] == "input_audio"


def test_realtime_audio_buffer_clear(client):
    """Test clearing the audio buffer."""
    with client.websocket_connect(
        "/v1/realtime?model=openai/gpt-oss-120b-realtime-preview-2024-10-01"
    ) as websocket:
        # Receive session.created
        session_created = json.loads(websocket.receive_text())
        assert session_created["type"] == "session.created"

        # Append audio
        fake_audio = base64.b64encode(b"fake audio data").decode("utf-8")
        websocket.send_json(
            {
                "type": "input_audio_buffer.append",
                "audio": fake_audio,
            }
        )

        # Clear the buffer
        websocket.send_json(
            {
                "type": "input_audio_buffer.clear",
            }
        )

        # Should receive cleared event
        data = websocket.receive_text()
        event = json.loads(data)
        assert event["type"] == "input_audio_buffer.cleared"


def test_realtime_conversation_item_create(client):
    """Test creating a conversation item."""
    with client.websocket_connect(
        "/v1/realtime?model=openai/gpt-oss-120b-realtime-preview-2024-10-01"
    ) as websocket:
        # Receive session.created
        session_created = json.loads(websocket.receive_text())
        assert session_created["type"] == "session.created"

        # Create a text message item
        websocket.send_json(
            {
                "type": "conversation.item.create",
                "item": {
                    "type": "message",
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": "Hello, how are you?",
                        }
                    ],
                },
            }
        )

        # Should receive item.created event
        data = websocket.receive_text()
        event = json.loads(data)

        assert event["type"] == "conversation.item.created"
        assert event["item"]["type"] == "message"
        assert event["item"]["role"] == "user"
        assert len(event["item"]["content"]) == 1
        assert event["item"]["content"][0]["type"] == "input_text"
        assert event["item"]["content"][0]["text"] == "Hello, how are you?"


def test_realtime_response_create_text(client):
    """Test creating a response with text modality."""
    with client.websocket_connect(
        "/v1/realtime?model=openai/gpt-oss-120b-realtime-preview-2024-10-01"
    ) as websocket:
        # Receive session.created
        session_created = json.loads(websocket.receive_text())
        assert session_created["type"] == "session.created"

        # Update session to text-only
        websocket.send_json(
            {
                "type": "session.update",
                "session": {
                    "modalities": ["text"],
                },
            }
        )

        # Receive session.updated
        session_updated = json.loads(websocket.receive_text())
        assert session_updated["type"] == "session.updated"

        # Create a conversation item
        websocket.send_json(
            {
                "type": "conversation.item.create",
                "item": {
                    "type": "message",
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": "Tell me a joke.",
                        }
                    ],
                },
            }
        )

        # Receive item.created
        item_created = json.loads(websocket.receive_text())
        assert item_created["type"] == "conversation.item.created"

        # Request response
        websocket.send_json(
            {
                "type": "response.create",
                "response": {
                    "modalities": ["text"],
                },
            }
        )

        # Collect response events
        events = []
        while True:
            data = websocket.receive_text()
            event = json.loads(data)
            events.append(event)

            if event["type"] == "response.done":
                break

        # Verify event sequence
        event_types = [e["type"] for e in events]
        assert "response.created" in event_types
        assert "response.output_item.added" in event_types
        assert "response.content_part.added" in event_types
        assert "response.text.delta" in event_types
        assert "response.text.done" in event_types
        assert "response.content_part.done" in event_types
        assert "response.output_item.done" in event_types
        assert "response.done" in event_types

        # Check response content
        response_done = next(e for e in events if e["type"] == "response.done")
        assert response_done["response"]["status"] == "completed"
        assert len(response_done["response"]["output"]) > 0
        assert response_done["response"]["output"][0]["type"] == "message"
        assert response_done["response"]["output"][0]["role"] == "assistant"


def test_realtime_response_create_audio(client):
    """Test creating a response with audio modality."""
    with client.websocket_connect(
        "/v1/realtime?model=openai/gpt-oss-120b-realtime-preview-2024-10-01"
    ) as websocket:
        # Receive session.created
        session_created = json.loads(websocket.receive_text())
        assert session_created["type"] == "session.created"

        # Update session to audio-only
        websocket.send_json(
            {
                "type": "session.update",
                "session": {
                    "modalities": ["audio"],
                },
            }
        )

        # Receive session.updated
        session_updated = json.loads(websocket.receive_text())
        assert session_updated["type"] == "session.updated"

        # Create a conversation item
        websocket.send_json(
            {
                "type": "conversation.item.create",
                "item": {
                    "type": "message",
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": "Say hello.",
                        }
                    ],
                },
            }
        )

        # Receive item.created
        item_created = json.loads(websocket.receive_text())
        assert item_created["type"] == "conversation.item.created"

        # Request response
        websocket.send_json(
            {
                "type": "response.create",
                "response": {
                    "modalities": ["audio"],
                },
            }
        )

        # Collect response events
        events = []
        audio_deltas = []
        while True:
            data = websocket.receive_text()
            event = json.loads(data)
            events.append(event)

            if event["type"] == "response.audio.delta":
                audio_deltas.append(event["delta"])

            if event["type"] == "response.done":
                break

        # Verify event sequence
        event_types = [e["type"] for e in events]
        assert "response.created" in event_types
        assert "response.output_item.added" in event_types
        assert "response.content_part.added" in event_types
        assert "response.audio.delta" in event_types
        assert "response.audio.done" in event_types
        assert "response.audio_transcript.done" in event_types
        assert "response.content_part.done" in event_types
        assert "response.output_item.done" in event_types
        assert "response.done" in event_types

        # Check audio data
        assert len(audio_deltas) > 0

        # Check response content
        response_done = next(e for e in events if e["type"] == "response.done")
        assert response_done["response"]["status"] == "completed"
        assert len(response_done["response"]["output"]) > 0
        assert response_done["response"]["output"][0]["content"][0]["type"] == "audio"


def test_realtime_response_cancel(client):
    """Test cancelling a response in progress."""
    with client.websocket_connect(
        "/v1/realtime?model=openai/gpt-oss-120b-realtime-preview-2024-10-01"
    ) as websocket:
        # Receive session.created
        session_created = json.loads(websocket.receive_text())
        assert session_created["type"] == "session.created"

        # Create a conversation item
        websocket.send_json(
            {
                "type": "conversation.item.create",
                "item": {
                    "type": "message",
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": "Tell me a long story.",
                        }
                    ],
                },
            }
        )

        # Receive item.created
        item_created = json.loads(websocket.receive_text())
        assert item_created["type"] == "conversation.item.created"

        # Request response
        websocket.send_json(
            {
                "type": "response.create",
            }
        )

        # Wait for response to start
        response_created = json.loads(websocket.receive_text())
        assert response_created["type"] == "response.created"

        # Cancel the response
        websocket.send_json(
            {
                "type": "response.cancel",
            }
        )

        # Should receive cancelled event
        data = websocket.receive_text()
        event = json.loads(data)
        assert event["type"] == "response.cancelled"


def test_realtime_error_unknown_event(client):
    """Test error handling for unknown event types."""
    with client.websocket_connect(
        "/v1/realtime?model=openai/gpt-oss-120b-realtime-preview-2024-10-01"
    ) as websocket:
        # Receive session.created
        session_created = json.loads(websocket.receive_text())
        assert session_created["type"] == "session.created"

        # Send unknown event type
        websocket.send_json(
            {
                "type": "unknown.event.type",
            }
        )

        # Should receive error event
        data = websocket.receive_text()
        event = json.loads(data)

        assert event["type"] == "error"
        assert event["error"]["type"] == "invalid_request_error"
        assert event["error"]["code"] == "unknown_event"


def test_realtime_error_invalid_json(client):
    """Test error handling for invalid JSON."""
    with client.websocket_connect(
        "/v1/realtime?model=openai/gpt-oss-120b-realtime-preview-2024-10-01"
    ) as websocket:
        # Receive session.created
        session_created = json.loads(websocket.receive_text())
        assert session_created["type"] == "session.created"

        # Send invalid JSON
        websocket.send_text("{invalid json")

        # Should receive error event
        data = websocket.receive_text()
        event = json.loads(data)

        assert event["type"] == "error"
        assert event["error"]["type"] == "invalid_request_error"
        assert event["error"]["code"] == "invalid_json"


def test_realtime_vad_simulation(client):
    """Test voice activity detection simulation."""
    with client.websocket_connect(
        "/v1/realtime?model=openai/gpt-oss-120b-realtime-preview-2024-10-01"
    ) as websocket:
        # Receive session.created
        session_created = json.loads(websocket.receive_text())
        assert session_created["type"] == "session.created"

        # Enable VAD in session
        websocket.send_json(
            {
                "type": "session.update",
                "session": {
                    "turn_detection": {
                        "type": "server_vad",
                        "threshold": 0.5,
                        "prefix_padding_ms": 300,
                        "silence_duration_ms": 500,
                    },
                },
            }
        )

        # Receive session.updated
        session_updated = json.loads(websocket.receive_text())
        assert session_updated["type"] == "session.updated"

        # Send audio chunks to trigger VAD
        fake_audio = base64.b64encode(b"fake audio with speech").decode("utf-8")
        for i in range(5):
            websocket.send_json(
                {
                    "type": "input_audio_buffer.append",
                    "audio": fake_audio + str(i),
                }
            )

            # After a few chunks, VAD should detect speech
            if i >= 2:
                data = websocket.receive_text()
                event = json.loads(data)
                if event["type"] == "input_audio_buffer.speech_started":
                    assert "audio_end_ms" in event
                    assert event["audio_end_ms"] > 0
                    break


def test_realtime_multimodal_response(client):
    """Test response with both text and audio modalities."""
    with client.websocket_connect(
        "/v1/realtime?model=openai/gpt-oss-120b-realtime-preview-2024-10-01"
    ) as websocket:
        # Receive session.created
        session_created = json.loads(websocket.receive_text())
        assert session_created["type"] == "session.created"

        # Update session to both modalities
        websocket.send_json(
            {
                "type": "session.update",
                "session": {
                    "modalities": ["text", "audio"],
                },
            }
        )

        # Receive session.updated
        session_updated = json.loads(websocket.receive_text())
        assert session_updated["type"] == "session.updated"

        # Create a conversation item
        websocket.send_json(
            {
                "type": "conversation.item.create",
                "item": {
                    "type": "message",
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": "Hello!",
                        }
                    ],
                },
            }
        )

        # Receive item.created
        item_created = json.loads(websocket.receive_text())
        assert item_created["type"] == "conversation.item.created"

        # Request response
        websocket.send_json(
            {
                "type": "response.create",
            }
        )

        # Collect response events
        events = []
        while True:
            data = websocket.receive_text()
            event = json.loads(data)
            events.append(event)

            if event["type"] == "response.done":
                break

        # Verify both text and audio events are present
        event_types = [e["type"] for e in events]
        assert "response.text.delta" in event_types
        assert "response.text.done" in event_types
        assert "response.audio.delta" in event_types
        assert "response.audio.done" in event_types

        # Check response has both content types
        response_done = next(e for e in events if e["type"] == "response.done")
        content_types = [
            c["type"] for c in response_done["response"]["output"][0]["content"]
        ]
        assert "text" in content_types
        assert "audio" in content_types


def test_realtime_rate_limits(client):
    """Test rate limit information in events."""
    with client.websocket_connect(
        "/v1/realtime?model=openai/gpt-oss-120b-realtime-preview-2024-10-01"
    ) as websocket:
        # Receive session.created
        session_created = json.loads(websocket.receive_text())
        assert session_created["type"] == "session.created"

        # Create a conversation item
        websocket.send_json(
            {
                "type": "conversation.item.create",
                "item": {
                    "type": "message",
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": "Hello!",
                        }
                    ],
                },
            }
        )

        # Receive item.created
        item_created = json.loads(websocket.receive_text())
        assert item_created["type"] == "conversation.item.created"

        # Request response
        websocket.send_json(
            {
                "type": "response.create",
            }
        )

        # Collect events until rate_limits.updated
        events = []
        while True:
            data = websocket.receive_text()
            event = json.loads(data)
            events.append(event)

            if event["type"] == "rate_limits.updated":
                # Check rate limit structure
                assert "rate_limits" in event
                assert len(event["rate_limits"]) > 0
                assert "name" in event["rate_limits"][0]
                assert "limit" in event["rate_limits"][0]
                assert "remaining" in event["rate_limits"][0]
                assert "reset_seconds" in event["rate_limits"][0]
                break

            if event["type"] == "response.done":
                # rate_limits should come after response.done
                pass
