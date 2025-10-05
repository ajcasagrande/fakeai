#!/usr/bin/env python3
"""
Example of using the FakeAI Realtime WebSocket API.

This example demonstrates:
1. Connecting to the Realtime WebSocket endpoint
2. Configuring the session
3. Sending text messages
4. Appending audio to the buffer
5. Creating responses with streaming
"""
#  SPDX-License-Identifier: Apache-2.0

import asyncio
import base64
import json

import websockets


async def realtime_example():
    """Example of using the Realtime WebSocket API."""
    uri = "ws://localhost:8000/v1/realtime?model=openai/gpt-oss-120b-realtime-preview-2024-10-01"

    async with websockets.connect(uri) as websocket:
        print("Connected to Realtime WebSocket API")

        # Receive session.created event
        session_created = json.loads(await websocket.recv())
        print(f"\nReceived: {session_created['type']}")
        print(f"Session ID: {session_created['session']['id']}")

        # Update session configuration
        print("\n--- Updating session configuration ---")
        await websocket.send(json.dumps({
            "type": "session.update",
            "session": {
                "modalities": ["text", "audio"],
                "instructions": "You are a helpful AI assistant. Be concise and friendly.",
                "voice": "alloy",
                "temperature": 0.8,
            }
        }))

        session_updated = json.loads(await websocket.recv())
        print(f"Received: {session_updated['type']}")

        # Example 1: Create a text conversation item
        print("\n--- Creating text conversation item ---")
        await websocket.send(json.dumps({
            "type": "conversation.item.create",
            "item": {
                "type": "message",
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": "Tell me a short joke about programming.",
                    }
                ],
            },
        }))

        item_created = json.loads(await websocket.recv())
        print(f"Received: {item_created['type']}")

        # Create a text-only response
        print("\n--- Creating text response ---")
        await websocket.send(json.dumps({
            "type": "response.create",
            "response": {
                "modalities": ["text"],
            },
        }))

        # Receive streaming response
        full_text = ""
        while True:
            message = await websocket.recv()
            event = json.loads(message)

            if event["type"] == "response.text.delta":
                full_text += event["delta"]
                print(event["delta"], end="", flush=True)

            elif event["type"] == "response.done":
                print(f"\n\nResponse completed!")
                print(f"Usage: {event['response']['usage']}")
                break

        # Example 2: Simulate audio input
        print("\n--- Simulating audio input ---")

        # Generate fake audio data (in real usage, this would be actual PCM16 audio)
        fake_audio = base64.b64encode(b"fake audio data chunk").decode("utf-8")

        # Append audio chunks
        for i in range(5):
            await websocket.send(json.dumps({
                "type": "input_audio_buffer.append",
                "audio": fake_audio + str(i),
            }))

            # Check for speech detection
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=0.1)
                event = json.loads(message)
                if event["type"] == "input_audio_buffer.speech_started":
                    print(f"Speech detected at {event['audio_end_ms']}ms")
            except asyncio.TimeoutError:
                pass

        # Commit the audio buffer
        print("\n--- Committing audio buffer ---")
        await websocket.send(json.dumps({
            "type": "input_audio_buffer.commit",
        }))

        # Receive events
        events_received = 0
        while events_received < 3:
            message = await websocket.recv()
            event = json.loads(message)
            print(f"Received: {event['type']}")
            events_received += 1

            if event["type"] == "conversation.item.created":
                print(f"Conversation item: {event['item']['type']}")
                if event['item']['content']:
                    print(f"Content type: {event['item']['content'][0]['type']}")
                    if event['item']['content'][0].get('transcript'):
                        print(f"Transcript: {event['item']['content'][0]['transcript']}")

        # Example 3: Create an audio response
        print("\n--- Creating audio response ---")
        await websocket.send(json.dumps({
            "type": "response.create",
            "response": {
                "modalities": ["audio"],
            },
        }))

        # Receive streaming audio response
        audio_chunks = []
        transcript = ""
        while True:
            message = await websocket.recv()
            event = json.loads(message)

            if event["type"] == "response.audio.delta":
                audio_chunks.append(event["delta"])
                print(".", end="", flush=True)

            elif event["type"] == "response.audio_transcript.delta":
                transcript += event["delta"]
                print(f"\nTranscript delta: {event['delta']}")

            elif event["type"] == "response.audio_transcript.done":
                print(f"\nFinal transcript: {event['transcript']}")

            elif event["type"] == "response.done":
                print(f"\nAudio response completed!")
                print(f"Audio chunks received: {len(audio_chunks)}")
                break

        print("\n--- Example completed successfully! ---")


if __name__ == "__main__":
    print("FakeAI Realtime WebSocket API Example")
    print("=" * 50)
    print("\nMake sure the FakeAI server is running on http://localhost:8000")
    print("Start the server with: fakeai-server\n")

    try:
        asyncio.run(realtime_example())
    except KeyboardInterrupt:
        print("\n\nExample interrupted by user")
    except Exception as e:
        print(f"\n\nError: {e}")
        print("Make sure the FakeAI server is running!")
