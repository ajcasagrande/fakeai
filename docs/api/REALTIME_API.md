# FakeAI Realtime WebSocket API

The FakeAI Realtime API provides a WebSocket-based interface for bidirectional streaming conversations with support for both text and audio modalities, voice activity detection (VAD), and function calling.

## Overview

The Realtime API simulates the OpenAI Realtime API, enabling you to:

- **Bidirectional Communication**: Send and receive events over WebSocket
- **Multi-modal Support**: Handle both text and audio inputs/outputs
- **Voice Activity Detection**: Simulated VAD for detecting speech in audio streams
- **Streaming Responses**: Receive incremental text and audio deltas
- **Function Calling**: Support for tools and function calls (coming soon)
- **Session Management**: Configure and update session parameters in real-time

## Endpoint

```
ws://localhost:8000/v1/realtime?model=<model_id>
```

**Query Parameters:**
- `model` (string): The model to use (default: `openai/gpt-oss-120b-realtime-preview-2024-10-01`)

## Connection Flow

1. **Connect** to the WebSocket endpoint
2. **Receive** `session.created` event with initial session configuration
3. **Send** client events (audio, text, configuration updates)
4. **Receive** server events (responses, transcripts, errors)
5. **Disconnect** when done

## Event Types

### Client Events (Sent to Server)

| Event Type | Description |
|------------|-------------|
| `session.update` | Update session configuration |
| `input_audio_buffer.append` | Append audio data to input buffer |
| `input_audio_buffer.commit` | Commit audio buffer and create conversation item |
| `input_audio_buffer.clear` | Clear the audio buffer |
| `conversation.item.create` | Create a conversation item (message, function call, etc.) |
| `conversation.item.delete` | Delete a conversation item |
| `conversation.item.truncate` | Truncate an item's audio |
| `response.create` | Request a response from the model |
| `response.cancel` | Cancel an in-progress response |

### Server Events (Received from Server)

| Event Type | Description |
|------------|-------------|
| `session.created` | Session has been created |
| `session.updated` | Session configuration has been updated |
| `input_audio_buffer.speech_started` | Speech detected in audio input |
| `input_audio_buffer.speech_stopped` | Speech ended in audio input |
| `input_audio_buffer.committed` | Audio buffer has been committed |
| `input_audio_buffer.cleared` | Audio buffer has been cleared |
| `conversation.item.created` | Conversation item has been created |
| `conversation.item.deleted` | Conversation item has been deleted |
| `response.created` | Response generation has started |
| `response.output_item.added` | New output item added to response |
| `response.content_part.added` | New content part added |
| `response.text.delta` | Incremental text content |
| `response.text.done` | Text content complete |
| `response.audio.delta` | Incremental audio content (base64 PCM16) |
| `response.audio.done` | Audio content complete |
| `response.audio_transcript.delta` | Incremental audio transcript |
| `response.audio_transcript.done` | Audio transcript complete |
| `response.done` | Response generation complete |
| `rate_limits.updated` | Rate limit information updated |
| `error` | An error occurred |

## Session Configuration

The session can be configured with the following parameters:

```json
{
  "modalities": ["text", "audio"],
  "instructions": "You are a helpful assistant.",
  "voice": "alloy",
  "input_audio_format": "pcm16",
  "output_audio_format": "pcm16",
  "input_audio_transcription": {
    "model": "whisper-1"
  },
  "turn_detection": {
    "type": "server_vad",
    "threshold": 0.5,
    "prefix_padding_ms": 300,
    "silence_duration_ms": 500,
    "create_response": true
  },
  "tools": [],
  "tool_choice": "auto",
  "temperature": 0.8,
  "max_response_output_tokens": "inf"
}
```

### Configuration Options

- **modalities**: `["text", "audio"]` - Enabled modalities
- **instructions**: System instructions for the model
- **voice**: Voice for audio output (`alloy`, `ash`, `ballad`, `coral`, `echo`, `sage`, `shimmer`, `verse`)
- **input_audio_format**: Format of input audio (`pcm16`, `g711_ulaw`, `g711_alaw`)
- **output_audio_format**: Format of output audio (`pcm16`, `g711_ulaw`, `g711_alaw`)
- **turn_detection**: Voice activity detection configuration
- **temperature**: Sampling temperature (0.6 - 1.2)
- **max_response_output_tokens**: Maximum tokens in response

## Examples

### Example 1: Text-Only Conversation

```python
import asyncio
import json
import websockets

async def text_conversation():
    uri = "ws://localhost:8000/v1/realtime?model=openai/gpt-oss-120b-realtime-preview-2024-10-01"

    async with websockets.connect(uri) as websocket:
        # Receive session.created
        session_created = json.loads(await websocket.recv())
        print(f"Session ID: {session_created['session']['id']}")

        # Configure text-only mode
        await websocket.send(json.dumps({
            "type": "session.update",
            "session": {"modalities": ["text"]}
        }))

        await websocket.recv()  # session.updated

        # Send a message
        await websocket.send(json.dumps({
            "type": "conversation.item.create",
            "item": {
                "type": "message",
                "role": "user",
                "content": [{"type": "input_text", "text": "Hello!"}]
            }
        }))

        await websocket.recv()  # conversation.item.created

        # Request response
        await websocket.send(json.dumps({"type": "response.create"}))

        # Receive streaming response
        while True:
            event = json.loads(await websocket.recv())

            if event["type"] == "response.text.delta":
                print(event["delta"], end="", flush=True)
            elif event["type"] == "response.done":
                break

asyncio.run(text_conversation())
```

### Example 2: Audio Input with VAD

```python
import asyncio
import base64
import json
import websockets

async def audio_conversation():
    uri = "ws://localhost:8000/v1/realtime?model=openai/gpt-oss-120b-realtime-preview-2024-10-01"

    async with websockets.connect(uri) as websocket:
        # Receive session.created
        await websocket.recv()

        # Enable VAD
        await websocket.send(json.dumps({
            "type": "session.update",
            "session": {
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": 0.5,
                    "silence_duration_ms": 500
                }
            }
        }))

        await websocket.recv()  # session.updated

        # Send audio chunks
        audio_chunk = base64.b64encode(b"fake audio data").decode()
        for i in range(5):
            await websocket.send(json.dumps({
                "type": "input_audio_buffer.append",
                "audio": audio_chunk
            }))

            # Check for speech detection
            try:
                event = json.loads(await asyncio.wait_for(
                    websocket.recv(), timeout=0.1
                ))
                if event["type"] == "input_audio_buffer.speech_started":
                    print("Speech detected!")
            except asyncio.TimeoutError:
                pass

        # Commit audio
        await websocket.send(json.dumps({
            "type": "input_audio_buffer.commit"
        }))

        # Receive events
        for _ in range(3):
            event = json.loads(await websocket.recv())
            print(f"Event: {event['type']}")

asyncio.run(audio_conversation())
```

### Example 3: Multi-modal Response

```python
import asyncio
import json
import websockets

async def multimodal_response():
    uri = "ws://localhost:8000/v1/realtime?model=openai/gpt-oss-120b-realtime-preview-2024-10-01"

    async with websockets.connect(uri) as websocket:
        await websocket.recv()  # session.created

        # Create message
        await websocket.send(json.dumps({
            "type": "conversation.item.create",
            "item": {
                "type": "message",
                "role": "user",
                "content": [{"type": "input_text", "text": "Say hello!"}]
            }
        }))

        await websocket.recv()  # conversation.item.created

        # Request multi-modal response
        await websocket.send(json.dumps({
            "type": "response.create",
            "response": {"modalities": ["text", "audio"]}
        }))

        # Receive streaming response
        text = ""
        audio_chunks = 0

        while True:
            event = json.loads(await websocket.recv())

            if event["type"] == "response.text.delta":
                text += event["delta"]
            elif event["type"] == "response.audio.delta":
                audio_chunks += 1
            elif event["type"] == "response.done":
                print(f"Text: {text}")
                print(f"Audio chunks: {audio_chunks}")
                break

asyncio.run(multimodal_response())
```

## Voice Activity Detection (VAD)

The Realtime API simulates voice activity detection (VAD) to automatically detect when speech starts and stops in audio input.

### Configuration

```json
{
  "turn_detection": {
    "type": "server_vad",
    "threshold": 0.5,
    "prefix_padding_ms": 300,
    "silence_duration_ms": 500,
    "create_response": true
  }
}
```

### VAD Events

1. **Speech Started**: Triggered after detecting speech in the audio buffer
   - Event: `input_audio_buffer.speech_started`
   - Contains: `audio_end_ms` (timestamp)

2. **Speech Stopped**: Triggered after detecting silence
   - Event: `input_audio_buffer.speech_stopped`
   - Contains: `audio_end_ms` (timestamp)

### Simulation Details

FakeAI simulates VAD behavior:
- Speech is detected after receiving 3+ audio chunks
- Speech automatically stops when buffer is committed
- No actual audio analysis is performed (this is a simulation)

## Audio Formats

### Supported Formats

- **PCM16**: 16-bit PCM audio (default)
- **G.711 μ-law**: 8-bit G.711 μ-law encoding
- **G.711 A-law**: 8-bit G.711 A-law encoding

### Audio Data Format

Audio data is sent and received as **base64-encoded strings**.

**Example:**
```python
import base64

# Encode audio bytes
audio_bytes = b"PCM16 audio data..."
audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")

# Send to server
await websocket.send(json.dumps({
    "type": "input_audio_buffer.append",
    "audio": audio_base64
}))
```

## Error Handling

Errors are returned as events with type `error`:

```json
{
  "type": "error",
  "event_id": "event_abc123",
  "error": {
    "type": "invalid_request_error",
    "code": "unknown_event",
    "message": "Unknown event type: xyz",
    "param": null,
    "event_id": null
  }
}
```

### Common Error Types

- `invalid_request_error`: Invalid request format or parameters
- `invalid_json`: Malformed JSON
- `unknown_event`: Unknown event type
- `server_error`: Internal server error

## Rate Limiting

Rate limit information is provided in `rate_limits.updated` events:

```json
{
  "type": "rate_limits.updated",
  "event_id": "event_xyz789",
  "rate_limits": [
    {
      "name": "requests",
      "limit": 1000,
      "remaining": 950,
      "reset_seconds": 60.0
    },
    {
      "name": "tokens",
      "limit": 100000,
      "remaining": 95000,
      "reset_seconds": 60.0
    }
  ]
}
```

## Testing

Run the test suite:

```bash
pytest tests/test_realtime.py -v
```

## Running the Example

1. Start the FakeAI server:
```bash
fakeai-server
```

2. Run the example in another terminal:
```bash
python examples/realtime_example.py
```

Or install websockets and run inline:
```bash
pip install websockets
python examples/realtime_example.py
```

## Differences from OpenAI Realtime API

FakeAI simulates the OpenAI Realtime API with these differences:

1. **No Actual Inference**: Responses are generated using the Faker library
2. **Simulated Audio**: Audio is generated as random bytes, not actual TTS
3. **Simulated VAD**: Voice activity detection uses simple heuristics, not actual audio analysis
4. **Simulated Transcription**: Audio transcription generates random text
5. **No Function Calling**: Tool/function calling support is basic (coming soon)

## Additional Resources

- Full example: `examples/realtime_example.py`
- Test suite: `tests/test_realtime.py`
- Models documentation: See `fakeai/models.py` for all event schemas
- OpenAI Realtime API docs: https://platform.openai.com/docs/guides/realtime

## Troubleshooting

### Connection Issues

**Problem**: Cannot connect to WebSocket
**Solution**: Ensure the FakeAI server is running on port 8000

### Event Errors

**Problem**: Receiving error events
**Solution**: Check event format matches the schema, ensure all required fields are present

### Audio Issues

**Problem**: Audio not being processed
**Solution**: Ensure audio is base64-encoded and format is specified in session config

## Support

For issues or questions:
- GitHub Issues: https://github.com/ajcasagrande/fakeai/issues
- Check existing tests for examples
- Review the [CLAUDE.md](../development/CLAUDE.md) documentation
