# OpenAI Realtime API Research

**Version:** 1.0
**Date:** 2025-10-04
**Purpose:** Comprehensive technical documentation for implementing WebSocket/WebRTC simulation of OpenAI's Realtime API

---

## Table of Contents

1. [Overview](#overview)
2. [Connection Protocols](#connection-protocols)
3. [Event Architecture](#event-architecture)
4. [Client Events](#client-events)
5. [Server Events](#server-events)
6. [Audio Formats](#audio-formats)
7. [Session Configuration](#session-configuration)
8. [Voice Activity Detection (VAD)](#voice-activity-detection-vad)
9. [Turn Detection](#turn-detection)
10. [Modalities](#modalities)
11. [Tool/Function Calling](#toolfunction-calling)
12. [Implementation Strategy](#implementation-strategy)

---

## Overview

### What is the Realtime API?

The OpenAI Realtime API enables **low-latency, multimodal speech-to-speech conversational experiences** using GPT-4o models. It creates persistent connections (WebSocket or WebRTC) for bidirectional real-time communication.

**Key Features:**
- Real-time speech-to-speech conversations
- Text and audio input/output (multimodal)
- Streaming responses with delta events
- Voice activity detection (VAD)
- Turn detection (semantic and server-based)
- Function/tool calling support
- Input audio transcription
- Low latency (optimized for voice)

**Models:**
- `openai/gpt-oss-120b-realtime-preview-2024-10-01` (beta)
- `openai/gpt-oss-120b-realtime-preview-2024-12-17` (updated)
- `gpt-realtime` (GA version)

---

## Connection Protocols

### WebSocket Connection

**Endpoint:**
```
wss://api.openai.com/v1/realtime?model={model_id}
```

**Example URL:**
```
wss://api.openai.com/v1/realtime?model=openai/gpt-oss-120b-realtime-preview-2024-10-01
```

**Required Headers:**
```http
Authorization: Bearer {OPENAI_API_KEY}
OpenAI-Beta: realtime=v1
```

**Connection Example (Node.js):**
```javascript
const WebSocket = require("ws");
const url = "wss://api.openai.com/v1/realtime?model=openai/gpt-oss-120b-realtime-preview-2024-10-01";

const ws = new WebSocket(url, {
  headers: {
    "Authorization": "Bearer " + process.env.OPENAI_API_KEY,
    "OpenAI-Beta": "realtime=v1",
  },
});

ws.on('open', () => {
  console.log('Connected to Realtime API');
});

ws.on('message', (data) => {
  const event = JSON.parse(data);
  console.log('Received event:', event.type);
});
```

**Connection Example (Python):**
```python
import asyncio
import websockets
import json

async def connect_realtime():
    url = "wss://api.openai.com/v1/realtime?model=openai/gpt-oss-120b-realtime-preview-2024-10-01"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "OpenAI-Beta": "realtime=v1"
    }

    async with websockets.connect(url, extra_headers=headers) as websocket:
        # Receive session.created event
        response = await websocket.recv()
        event = json.loads(response)
        print(f"Connected: {event['type']}")

        # Send and receive events
        await websocket.send(json.dumps({
            "type": "session.update",
            "session": {"modalities": ["text", "audio"]}
        }))
```

**Browser Limitation:**
The native JavaScript WebSocket API doesn't allow passing authentication headers, which can cause issues in browser environments. Solutions include:
1. Using WebSocket subprotocols
2. Passing API key as query parameter (if supported)
3. Using a backend proxy

### WebRTC Connection

**Endpoint:**
```
https://api.openai.com/v1/realtime
```

**Advantages:**
- Lower latency than WebSocket
- Better for real-time audio streaming
- Native browser support
- Optimized for voice/video communication

**Ephemeral Tokens:**
- Short-lived tokens for secure WebRTC connections
- Valid for 1 minute
- Minted by server using standard API key
- Client requests ephemeral token from backend
- Backend returns token to client for WebRTC connection

**Authentication Flow:**
1. Client requests ephemeral token from your backend
2. Backend calls OpenAI API to mint ephemeral token
3. Backend returns ephemeral token to client
4. Client uses ephemeral token to establish WebRTC connection
5. Connection expires after 1 minute if not established

**WebRTC vs WebSocket:**
| Feature | WebRTC | WebSocket |
|---------|--------|-----------|
| Latency | Lower (optimized for real-time) | Higher |
| Browser Support | Native, excellent | Native, excellent |
| Setup Complexity | More complex (SDP, ICE) | Simpler |
| Use Case | Voice/video streaming | General bidirectional data |
| Authentication | Ephemeral tokens | API key in headers |

---

## Event Architecture

### Event Protocol

The Realtime API uses a **bidirectional event-based protocol** over WebSocket/WebRTC connections. All events are JSON objects sent as text frames.

**Event Structure (Base):**
```json
{
  "type": "event.name",
  "event_id": "event_123",
  // ... event-specific fields
}
```

**Event Flow:**
1. **Connection established** → Server sends `session.created`
2. **Client configures** → Send `session.update`
3. **Server confirms** → Server sends `session.updated`
4. **Client sends audio** → Send `input_audio_buffer.append`
5. **Client commits audio** → Send `input_audio_buffer.commit`
6. **Server detects speech** → Server sends `input_audio_buffer.speech_started`
7. **Server detects end** → Server sends `input_audio_buffer.speech_stopped`
8. **Server generates response** → Server sends multiple events:
   - `response.created`
   - `response.output_item.added`
   - `response.content_part.added`
   - `response.audio.delta` (multiple, streaming)
   - `response.audio_transcript.delta` (multiple, streaming)
   - `response.audio.done`
   - `response.audio_transcript.done`
   - `response.output_item.done`
   - `response.done`

**Error Handling:**
- When errors occur, server sends `error` event
- Connection remains open after errors
- Client must handle errors explicitly
- No exceptions raised by SDK

---

## Client Events

Client events are sent **from the client to the server** to control the conversation.

### Complete List of Client Events (11 total)

1. `session.update` - Update session configuration
2. `input_audio_buffer.append` - Add audio bytes to input buffer
3. `input_audio_buffer.commit` - Commit audio buffer to conversation
4. `input_audio_buffer.clear` - Clear input audio buffer
5. `conversation.item.create` - Add item to conversation
6. `conversation.item.truncate` - Truncate previous assistant audio
7. `conversation.item.delete` - Remove item from conversation
8. `conversation.item.retrieve` - Get server's conversation item
9. `response.create` - Trigger response generation
10. `response.cancel` - Cancel in-progress response
11. `output_audio_buffer.clear` - Clear output audio buffer (WebRTC only)

### Client Event Details

#### 1. session.update

**Purpose:** Configure or reconfigure the session

**Schema:**
```json
{
  "type": "session.update",
  "session": {
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
      "silence_duration_ms": 500
    },
    "tools": [
      {
        "type": "function",
        "name": "get_weather",
        "description": "Get weather for a location",
        "parameters": {
          "type": "object",
          "properties": {
            "location": {"type": "string"}
          },
          "required": ["location"]
        }
      }
    ],
    "tool_choice": "auto",
    "temperature": 0.8,
    "max_response_output_tokens": 1000
  }
}
```

**Key Fields:**
- `modalities`: Array of `["text"]`, `["audio"]`, or `["text", "audio"]`
- `instructions`: System instructions (like system message)
- `voice`: Voice ID (see Audio Formats section)
- `input_audio_format`: `"pcm16"`, `"g711_ulaw"`, or `"g711_alaw"`
- `output_audio_format`: Same as input
- `input_audio_transcription`: Enable transcription with Whisper
- `turn_detection`: VAD configuration (see Turn Detection section)
- `tools`: Array of function definitions (same as Chat Completions API)
- `tool_choice`: `"auto"`, `"none"`, `"required"`, or specific function
- `temperature`: Model temperature (recommended: 0.8)
- `max_response_output_tokens`: Max tokens in response or `"inf"`

**Notes:**
- Can be sent at any time to update configuration
- All fields are optional except `type`
- Voice cannot be changed once synthesis starts
- Server responds with `session.updated` or `error`

#### 2. input_audio_buffer.append

**Purpose:** Add audio data to the input buffer

**Schema:**
```json
{
  "type": "input_audio_buffer.append",
  "audio": "base64_encoded_audio_data..."
}
```

**Key Fields:**
- `audio`: Base64-encoded audio bytes (no data URI prefix)

**Notes:**
- Audio must match `input_audio_format` from session
- Audio is buffered until `input_audio_buffer.commit` is sent
- Can send multiple append events before committing
- Used for streaming audio input

**Example:**
```javascript
// Send audio chunk
ws.send(JSON.stringify({
  type: "input_audio_buffer.append",
  audio: audioChunk.toString('base64')
}));
```

#### 3. input_audio_buffer.commit

**Purpose:** Commit buffered audio to conversation as user message

**Schema:**
```json
{
  "type": "input_audio_buffer.commit"
}
```

**Notes:**
- Creates a new conversation item with buffered audio
- Clears the input buffer after committing
- Server may auto-commit with VAD (if `turn_detection` enabled)
- Required for manual (push-to-talk) mode

#### 4. input_audio_buffer.clear

**Purpose:** Clear the input audio buffer without committing

**Schema:**
```json
{
  "type": "input_audio_buffer.clear"
}
```

**Notes:**
- Discards all buffered audio
- Useful for canceling input before commit

#### 5. conversation.item.create

**Purpose:** Add a new item to the conversation history

**Schema:**
```json
{
  "type": "conversation.item.create",
  "item": {
    "type": "message",
    "role": "user",
    "content": [
      {
        "type": "input_text",
        "text": "Hello, how are you?"
      }
    ]
  }
}
```

**Item Types:**
- `message` - User or assistant message
- `function_call` - Function call from assistant
- `function_call_output` - Function call result

**Content Types:**
- `input_text` - Text input
- `input_audio` - Audio input
- `text` - Text output (from assistant)
- `audio` - Audio output (from assistant)

**Notes:**
- Allows manual conversation management
- Can inject system, user, or assistant messages
- Server responds with `conversation.item.created`

#### 6. conversation.item.truncate

**Purpose:** Truncate previous assistant audio message

**Schema:**
```json
{
  "type": "conversation.item.truncate",
  "item_id": "item_123",
  "content_index": 0,
  "audio_end_ms": 1500
}
```

**Key Fields:**
- `item_id`: ID of item to truncate
- `content_index`: Index of content part
- `audio_end_ms`: Milliseconds to keep

**Notes:**
- Used when user interrupts assistant
- Removes audio after specified time
- Allows natural conversation flow

#### 7. conversation.item.delete

**Purpose:** Remove item from conversation history

**Schema:**
```json
{
  "type": "conversation.item.delete",
  "item_id": "item_123"
}
```

**Notes:**
- Removes item from server's conversation context
- Server responds with `conversation.item.deleted`

#### 8. conversation.item.retrieve

**Purpose:** Get server's representation of conversation item

**Schema:**
```json
{
  "type": "conversation.item.retrieve",
  "item_id": "item_123"
}
```

**Notes:**
- Useful for syncing client and server state
- Returns full item with all content

#### 9. response.create

**Purpose:** Manually trigger response generation

**Schema:**
```json
{
  "type": "response.create",
  "response": {
    "modalities": ["text", "audio"],
    "instructions": "Be concise",
    "voice": "alloy",
    "output_audio_format": "pcm16",
    "tools": [...],
    "tool_choice": "auto",
    "temperature": 0.8,
    "max_output_tokens": 500
  }
}
```

**Notes:**
- Overrides session configuration for this response
- All fields are optional
- Required in manual (non-VAD) mode
- Server responds with `response.created` and streaming events

#### 10. response.cancel

**Purpose:** Cancel in-progress response generation

**Schema:**
```json
{
  "type": "response.cancel"
}
```

**Notes:**
- Stops current response generation
- Useful when user interrupts
- Server sends `response.done` with status `"cancelled"`

#### 11. output_audio_buffer.clear

**Purpose:** Clear output audio buffer (WebRTC only)

**Schema:**
```json
{
  "type": "output_audio_buffer.clear"
}
```

**Notes:**
- WebRTC-specific event
- Not applicable to WebSocket connections

---

## Server Events

Server events are sent **from the server to the client** to communicate state changes and streaming data.

### Complete List of Server Events (28+ total)

#### Session Events
1. `session.created` - Session initialized
2. `session.updated` - Session configuration changed

#### Conversation Events
3. `conversation.created` - New conversation started
4. `conversation.item.created` - Item added to conversation
5. `conversation.item.truncated` - Item audio truncated
6. `conversation.item.deleted` - Item removed
7. `conversation.item.input_audio_transcription.completed` - Input transcription done
8. `conversation.item.input_audio_transcription.failed` - Transcription failed

#### Input Audio Buffer Events
9. `input_audio_buffer.committed` - Audio buffer committed
10. `input_audio_buffer.cleared` - Audio buffer cleared
11. `input_audio_buffer.speech_started` - User started speaking (VAD)
12. `input_audio_buffer.speech_stopped` - User stopped speaking (VAD)

#### Response Events
13. `response.created` - Response generation started
14. `response.done` - Response generation completed
15. `response.output_item.added` - Output item added to response
16. `response.output_item.done` - Output item completed
17. `response.content_part.added` - Content part added
18. `response.content_part.done` - Content part completed

#### Response Streaming Events (Delta)
19. `response.text.delta` - Text chunk
20. `response.text.done` - Text streaming done
21. `response.audio.delta` - Audio chunk
22. `response.audio.done` - Audio streaming done
23. `response.audio_transcript.delta` - Audio transcript chunk
24. `response.audio_transcript.done` - Audio transcript done
25. `response.function_call_arguments.delta` - Function args chunk
26. `response.function_call_arguments.done` - Function args done

#### Other Events
27. `rate_limits.updated` - Rate limit information
28. `error` - Error occurred

### Server Event Details

#### session.created

**Purpose:** First event on connection, provides session details

**Schema:**
```json
{
  "type": "session.created",
  "event_id": "event_123",
  "session": {
    "id": "sess_123",
    "object": "realtime.session",
    "model": "openai/gpt-oss-120b-realtime-preview-2024-10-01",
    "modalities": ["text", "audio"],
    "instructions": "",
    "voice": "alloy",
    "input_audio_format": "pcm16",
    "output_audio_format": "pcm16",
    "input_audio_transcription": null,
    "turn_detection": {
      "type": "server_vad",
      "threshold": 0.5,
      "prefix_padding_ms": 300,
      "silence_duration_ms": 500
    },
    "tools": [],
    "tool_choice": "auto",
    "temperature": 0.8,
    "max_response_output_tokens": "inf"
  }
}
```

**Notes:**
- Always first event after connection
- Provides default session configuration
- Client should typically send `session.update` after this

#### session.updated

**Purpose:** Confirms session configuration changes

**Schema:**
```json
{
  "type": "session.updated",
  "event_id": "event_124",
  "session": {
    // ... full session object with updates
  }
}
```

**Notes:**
- Sent in response to `session.update`
- Contains full effective configuration
- If update fails, `error` event is sent instead

#### response.created

**Purpose:** Indicates response generation has started

**Schema:**
```json
{
  "type": "response.created",
  "event_id": "event_125",
  "response": {
    "id": "resp_123",
    "object": "realtime.response",
    "status": "in_progress",
    "status_details": null,
    "output": [],
    "usage": null
  }
}
```

**Status Values:**
- `"in_progress"` - Currently generating
- `"completed"` - Finished successfully
- `"cancelled"` - Cancelled by client
- `"failed"` - Error occurred
- `"incomplete"` - Stopped due to token limit

#### response.audio.delta

**Purpose:** Stream audio chunk from assistant

**Schema:**
```json
{
  "type": "response.audio.delta",
  "event_id": "event_126",
  "response_id": "resp_123",
  "item_id": "item_456",
  "output_index": 0,
  "content_index": 0,
  "delta": "base64_encoded_audio_chunk..."
}
```

**Key Fields:**
- `response_id`: ID of response
- `item_id`: ID of output item
- `output_index`: Index in outputs array
- `content_index`: Index in content array
- `delta`: Base64-encoded audio bytes

**Notes:**
- Multiple events sent for streaming audio
- Audio is in `output_audio_format` from session
- Client should buffer and play audio chunks
- Audio format: PCM16, 24kHz, mono, little-endian

#### response.audio_transcript.delta

**Purpose:** Stream transcript of assistant audio

**Schema:**
```json
{
  "type": "response.audio_transcript.delta",
  "event_id": "event_127",
  "response_id": "resp_123",
  "item_id": "item_456",
  "output_index": 0,
  "content_index": 0,
  "delta": "Hello, "
}
```

**Notes:**
- Provides real-time transcription of assistant audio
- Useful for displaying captions
- Multiple events sent as text is generated

#### response.text.delta

**Purpose:** Stream text response from assistant

**Schema:**
```json
{
  "type": "response.text.delta",
  "event_id": "event_128",
  "response_id": "resp_123",
  "item_id": "item_456",
  "output_index": 0,
  "content_index": 0,
  "delta": "The weather "
}
```

**Notes:**
- Similar to Chat Completions streaming
- Used when `modalities` includes `"text"`

#### response.function_call_arguments.delta

**Purpose:** Stream function call arguments as they're generated

**Schema:**
```json
{
  "type": "response.function_call_arguments.delta",
  "event_id": "event_129",
  "response_id": "resp_123",
  "item_id": "item_456",
  "output_index": 0,
  "call_id": "call_789",
  "delta": "{\"location\": \"San"
}
```

**Notes:**
- Arguments are streamed as JSON string
- Client must parse complete JSON when done
- Used with function/tool calling

#### response.done

**Purpose:** Response generation completed

**Schema:**
```json
{
  "type": "response.done",
  "event_id": "event_130",
  "response": {
    "id": "resp_123",
    "object": "realtime.response",
    "status": "completed",
    "status_details": null,
    "output": [
      {
        "id": "item_456",
        "object": "realtime.item",
        "type": "message",
        "role": "assistant",
        "content": [
          {
            "type": "audio",
            "audio": "base64_complete_audio...",
            "transcript": "Hello, how can I help you?"
          }
        ]
      }
    ],
    "usage": {
      "total_tokens": 150,
      "input_tokens": 50,
      "output_tokens": 100,
      "input_token_details": {
        "cached_tokens": 0,
        "text_tokens": 40,
        "audio_tokens": 10
      },
      "output_token_details": {
        "text_tokens": 80,
        "audio_tokens": 20
      }
    }
  }
}
```

**Notes:**
- Final event for response
- Contains complete response with all outputs
- Includes token usage statistics
- Status indicates completion state

#### input_audio_buffer.speech_started

**Purpose:** VAD detected user started speaking

**Schema:**
```json
{
  "type": "input_audio_buffer.speech_started",
  "event_id": "event_131",
  "audio_start_ms": 1000
}
```

**Notes:**
- Only sent when `turn_detection` is enabled
- `audio_start_ms`: Time in buffer when speech started
- Can trigger `response.cancel` for interruption

#### input_audio_buffer.speech_stopped

**Purpose:** VAD detected user stopped speaking

**Schema:**
```json
{
  "type": "input_audio_buffer.speech_stopped",
  "event_id": "event_132",
  "audio_end_ms": 3500
}
```

**Notes:**
- Only sent when `turn_detection` is enabled
- `audio_end_ms`: Time in buffer when speech stopped
- May trigger auto-commit and response generation
- Followed by `input_audio_buffer.committed` if auto-commit

#### conversation.item.input_audio_transcription.completed

**Purpose:** Transcription of user audio completed

**Schema:**
```json
{
  "type": "conversation.item.input_audio_transcription.completed",
  "event_id": "event_133",
  "item_id": "item_789",
  "content_index": 0,
  "transcript": "What is the weather today?"
}
```

**Notes:**
- Only sent if `input_audio_transcription` is enabled
- Provides Whisper transcription of user audio
- Useful for logging and display

#### error

**Purpose:** Error occurred during processing

**Schema:**
```json
{
  "type": "error",
  "event_id": "event_134",
  "error": {
    "type": "invalid_request_error",
    "code": "invalid_audio_format",
    "message": "Audio format must be pcm16, g711_ulaw, or g711_alaw",
    "param": "input_audio_format",
    "event_id": "event_123"
  }
}
```

**Error Types:**
- `"invalid_request_error"` - Client sent invalid request
- `"server_error"` - Internal server error
- `"rate_limit_error"` - Rate limit exceeded

**Notes:**
- Connection stays open after errors
- Client must handle errors explicitly
- `event_id` references the event that caused error

#### rate_limits.updated

**Purpose:** Rate limit information

**Schema:**
```json
{
  "type": "rate_limits.updated",
  "event_id": "event_135",
  "rate_limits": [
    {
      "name": "requests",
      "limit": 1000,
      "remaining": 999,
      "reset_seconds": 60.0
    },
    {
      "name": "tokens",
      "limit": 100000,
      "remaining": 99850,
      "reset_seconds": 60.0
    }
  ]
}
```

**Notes:**
- Sent periodically during session
- Helps client manage rate limits
- Similar to HTTP rate limit headers

---

## Audio Formats

### Supported Audio Formats

The Realtime API supports three audio formats for both input and output:

1. **PCM16** (Recommended)
2. **G.711 μ-law** (Telephony)
3. **G.711 A-law** (Telephony)

### PCM16 Format

**Specification:**
- **Codec:** PCM (Pulse Code Modulation)
- **Bit Depth:** 16-bit signed integer
- **Sample Rate:** 24kHz (24,000 Hz)
- **Channels:** 1 (mono)
- **Byte Order:** Little-endian
- **Format:** Uncompressed raw audio

**Encoding for API:**
- Raw PCM samples encoded as Base64
- No data URI prefix (just Base64 string)
- No file container (no WAV header)

**Example:**
```javascript
// PCM16 audio buffer (Int16Array)
const pcmSamples = new Int16Array(1024);
// ... fill with audio samples

// Convert to bytes
const bytes = new Uint8Array(pcmSamples.buffer);

// Base64 encode
const base64Audio = Buffer.from(bytes).toString('base64');

// Send to API
ws.send(JSON.stringify({
  type: "input_audio_buffer.append",
  audio: base64Audio
}));
```

**Sample Calculation:**
- 1 second = 24,000 samples
- 1 sample = 2 bytes (16 bits)
- 1 second = 48,000 bytes
- 1 second Base64 ≈ 64,000 characters

### G.711 μ-law (PCMU)

**Specification:**
- **Codec:** G.711 μ-law
- **Sample Rate:** 8kHz (8,000 Hz)
- **Bit Depth:** 8-bit compressed
- **Channels:** 1 (mono)
- **Compression:** ~2:1 (8-bit vs 16-bit)

**Use Case:**
- Telephony applications (Twilio, Vonage)
- VoIP systems
- Legacy phone systems
- Bandwidth-constrained environments

**Format String:** `"g711_ulaw"`

**Notes:**
- Common in North America and Japan
- Lower quality than PCM16
- Some users report implementation issues with 8kHz input
- API internally expects 24kHz, so 8kHz may be upsampled

### G.711 A-law (PCMA)

**Specification:**
- **Codec:** G.711 A-law
- **Sample Rate:** 8kHz (8,000 Hz)
- **Bit Depth:** 8-bit compressed
- **Channels:** 1 (mono)
- **Compression:** ~2:1

**Use Case:**
- Telephony applications (primarily Europe)
- VoIP systems

**Format String:** `"g711_alaw"`

**Notes:**
- Common in Europe and rest of world
- Similar quality to μ-law
- Same considerations as μ-law

### Audio Format Comparison

| Format | Sample Rate | Bit Depth | Quality | Compression | Use Case |
|--------|-------------|-----------|---------|-------------|----------|
| PCM16 | 24kHz | 16-bit | High | None | Recommended, best quality |
| G.711 μ-law | 8kHz | 8-bit | Medium | 2:1 | Telephony (NA/Japan) |
| G.711 A-law | 8kHz | 8-bit | Medium | 2:1 | Telephony (Europe) |

### Voice IDs

The Realtime API supports 11 voice options:

**Available Voices:**
1. `"alloy"` (default)
2. `"ash"`
3. `"ballad"`
4. `"coral"`
5. `"echo"`
6. `"sage"`
7. `"shimmer"`
8. `"verse"`
9. `"fable"`
10. `"onyx"`
11. `"nova"`

**Voice Configuration:**
```json
{
  "type": "session.update",
  "session": {
    "voice": "alloy"
  }
}
```

**Important Notes:**
- Voice **cannot be changed** once audio synthesis starts
- Must set voice before first response
- Same voices as TTS API
- Voice characteristics vary (gender, tone, accent)

### Audio Encoding Best Practices

**For Sending Audio:**
1. Record audio at 24kHz, 16-bit, mono (PCM16)
2. Convert to raw PCM samples (no WAV header)
3. Base64 encode the raw bytes
4. Send in chunks (recommend 100-200ms chunks)
5. Don't include data URI prefix

**For Receiving Audio:**
1. Receive Base64-encoded audio in `response.audio.delta`
2. Decode Base64 to raw bytes
3. Convert to Int16Array (for PCM16)
4. Play through audio output (Web Audio API, etc.)
5. Buffer chunks for smooth playback

**Chunking Strategy:**
```javascript
// Send 100ms chunks (2400 samples = 4800 bytes)
const chunkSamples = 2400;
const chunkSize = chunkSamples * 2; // bytes

for (let i = 0; i < audioBuffer.length; i += chunkSize) {
  const chunk = audioBuffer.slice(i, i + chunkSize);
  const base64Chunk = Buffer.from(chunk).toString('base64');

  ws.send(JSON.stringify({
    type: "input_audio_buffer.append",
    audio: base64Chunk
  }));

  await sleep(100); // Wait 100ms between chunks
}
```

---

## Session Configuration

### Session Object Structure

The session object contains all configuration for the Realtime API session. It's provided in `session.created` and updated via `session.update`.

**Complete Session Schema:**
```typescript
interface Session {
  id: string;                              // Session ID
  object: "realtime.session";              // Object type
  model: string;                           // Model ID
  modalities: ("text" | "audio")[];        // Input/output modalities
  instructions: string;                    // System instructions
  voice: Voice;                            // Voice ID
  input_audio_format: AudioFormat;         // Input audio format
  output_audio_format: AudioFormat;        // Output audio format
  input_audio_transcription: {             // Transcription config
    model: "whisper-1";
  } | null;
  turn_detection: TurnDetection | null;    // Turn detection config
  tools: Tool[];                           // Function tools
  tool_choice: ToolChoice;                 // Tool selection
  temperature: number;                     // Model temperature
  max_response_output_tokens: number | "inf"; // Token limit
}

type Voice = "alloy" | "ash" | "ballad" | "coral" | "echo" | "sage" |
             "shimmer" | "verse" | "fable" | "onyx" | "nova";

type AudioFormat = "pcm16" | "g711_ulaw" | "g711_alaw";

type ToolChoice = "auto" | "none" | "required" |
                  { type: "function"; name: string };

interface TurnDetection {
  type: "server_vad" | "semantic_vad" | "none";
  threshold?: number;              // 0.0-1.0, VAD sensitivity
  prefix_padding_ms?: number;      // Padding before speech
  silence_duration_ms?: number;    // Silence before stop
  create_response?: boolean;       // Auto-create response
  interrupt_response?: boolean;    // Allow interruptions
  eagerness?: "auto" | "high" | "low"; // Semantic VAD only
}
```

### Default Session Configuration

When a connection is established, the server sends `session.created` with default configuration:

```json
{
  "type": "session.created",
  "session": {
    "id": "sess_...",
    "object": "realtime.session",
    "model": "openai/gpt-oss-120b-realtime-preview-2024-10-01",
    "modalities": ["text", "audio"],
    "instructions": "",
    "voice": "alloy",
    "input_audio_format": "pcm16",
    "output_audio_format": "pcm16",
    "input_audio_transcription": null,
    "turn_detection": {
      "type": "server_vad",
      "threshold": 0.5,
      "prefix_padding_ms": 300,
      "silence_duration_ms": 500
    },
    "tools": [],
    "tool_choice": "auto",
    "temperature": 0.8,
    "max_response_output_tokens": "inf"
  }
}
```

### Configuration Parameters

#### modalities

**Type:** `("text" | "audio")[]`
**Default:** `["text", "audio"]`

Controls input and output modalities for the session.

**Options:**
- `["text"]` - Text-only mode
- `["audio"]` - Audio-only mode
- `["text", "audio"]` - Multimodal (default)

**Example:**
```json
{
  "type": "session.update",
  "session": {
    "modalities": ["audio"]
  }
}
```

**Notes:**
- Can be overridden per-response in `response.create`
- Affects both input acceptance and output generation
- Text-only mode disables audio input/output

#### instructions

**Type:** `string`
**Default:** `""`

System-level instructions for the model (equivalent to system message in Chat Completions).

**Example:**
```json
{
  "type": "session.update",
  "session": {
    "instructions": "You are a helpful voice assistant. Respond concisely and naturally. Use a friendly tone."
  }
}
```

**Notes:**
- Can be updated at any time
- Can be overridden per-response in `response.create`
- Affects all subsequent responses

#### temperature

**Type:** `number` (0.0 - 2.0)
**Default:** `0.8`
**Recommended:** `0.8`

Model temperature for response generation.

**Notes:**
- OpenAI recommends 0.8 for this model architecture
- Higher = more random, lower = more deterministic
- Different behavior than other GPT models

#### max_response_output_tokens

**Type:** `number | "inf"`
**Default:** `"inf"`

Maximum tokens for each response output.

**Examples:**
- `1000` - Limit to 1000 tokens
- `"inf"` - Unlimited (default)

**Notes:**
- Can be overridden per-response
- Helps control response length and costs
- Response status will be `"incomplete"` if limit reached

#### input_audio_transcription

**Type:** `{ model: "whisper-1" } | null`
**Default:** `null`

Enable transcription of user audio input with Whisper.

**Example:**
```json
{
  "type": "session.update",
  "session": {
    "input_audio_transcription": {
      "model": "whisper-1"
    }
  }
}
```

**Notes:**
- When enabled, server sends `conversation.item.input_audio_transcription.completed`
- Useful for logging and display
- Uses Whisper-1 model
- Additional cost per audio input

---

## Voice Activity Detection (VAD)

Voice Activity Detection (VAD) automatically detects when the user starts and stops speaking.

### VAD Modes

#### 1. Server VAD (`server_vad`)

**Description:** Server analyzes audio and detects speech vs silence based on acoustic features.

**How it works:**
1. Client continuously sends audio via `input_audio_buffer.append`
2. Server analyzes audio in real-time
3. When speech detected → `input_audio_buffer.speech_started`
4. When silence detected → `input_audio_buffer.speech_stopped`
5. After silence threshold → Auto-commit and generate response

**Configuration:**
```json
{
  "type": "session.update",
  "session": {
    "turn_detection": {
      "type": "server_vad",
      "threshold": 0.5,
      "prefix_padding_ms": 300,
      "silence_duration_ms": 500,
      "create_response": true,
      "interrupt_response": true
    }
  }
}
```

**Parameters:**
- `threshold` (0.0-1.0): VAD sensitivity
  - Lower = more sensitive (detects quieter speech)
  - Higher = less sensitive (requires louder speech)
  - Default: 0.5
- `prefix_padding_ms`: Milliseconds of audio before speech start to include
  - Default: 300ms
  - Prevents cutting off beginning of speech
- `silence_duration_ms`: Milliseconds of silence before considering speech ended
  - Default: 500ms
  - **Most important parameter**
  - Lower = faster response, may interrupt mid-sentence
  - Higher = slower response, won't interrupt
- `create_response`: Auto-create response after speech stops
  - Default: true
  - If false, client must send `response.create`
- `interrupt_response`: Allow user to interrupt assistant
  - Default: true
  - If true, sends `conversation.interrupted` when user speaks during assistant response

**Use Cases:**
- Hands-free voice assistants
- Continuous conversation mode
- Voice-controlled applications

**Pros:**
- Natural conversation flow
- No button required
- Fast turn-taking

**Cons:**
- May trigger on background noise
- Can interrupt mid-sentence if threshold too low
- Requires tuning for environment

#### 2. Semantic VAD (`semantic_vad`)

**Description:** Uses AI to detect when user has finished their thought based on content, not just acoustics.

**How it works:**
1. Server analyzes both acoustic features AND semantic content
2. Detects end-of-turn based on meaning, not just silence
3. Less likely to interrupt mid-sentence
4. Better at detecting questions and complete thoughts

**Configuration:**
```json
{
  "type": "session.update",
  "session": {
    "turn_detection": {
      "type": "semantic_vad",
      "threshold": 0.5,
      "prefix_padding_ms": 300,
      "silence_duration_ms": 500,
      "create_response": true,
      "interrupt_response": true,
      "eagerness": "auto"
    }
  }
}
```

**Additional Parameter:**
- `eagerness`: Controls how quickly to detect end of turn
  - `"auto"` - Balanced (default)
  - `"high"` - Respond faster (may interrupt)
  - `"low"` - Wait longer (more complete thoughts)

**Use Cases:**
- Natural conversation interfaces
- Interviews and Q&A
- Complex multi-sentence inputs

**Pros:**
- Smarter detection (understands content)
- Less likely to interrupt mid-sentence
- Better for complex inputs

**Cons:**
- Slightly higher latency than server_vad
- Requires more processing
- May wait too long in some cases

#### 3. No VAD (`none` or `null`)

**Description:** Manual turn detection - client controls when to commit and respond.

**Configuration:**
```json
{
  "type": "session.update",
  "session": {
    "turn_detection": null
  }
}
```

**How it works:**
1. Client sends audio via `input_audio_buffer.append`
2. Client decides when user is done (e.g., button release)
3. Client sends `input_audio_buffer.commit`
4. Client sends `response.create` to trigger response

**Use Cases:**
- Push-to-talk applications
- Walkie-talkie style interfaces
- Environments with high background noise
- Games and applications with explicit controls

**Pros:**
- No false triggers
- Precise control
- Works in noisy environments

**Cons:**
- Requires button/UI
- Less natural conversation
- User must explicitly signal turns

### VAD Best Practices

**For Quiet Environments:**
```json
{
  "turn_detection": {
    "type": "server_vad",
    "threshold": 0.3,           // More sensitive
    "silence_duration_ms": 400   // Faster response
  }
}
```

**For Noisy Environments:**
```json
{
  "turn_detection": {
    "type": "server_vad",
    "threshold": 0.7,           // Less sensitive
    "silence_duration_ms": 700   // Wait longer
  }
}
```

**For Natural Conversation:**
```json
{
  "turn_detection": {
    "type": "semantic_vad",
    "eagerness": "auto",
    "silence_duration_ms": 500
  }
}
```

**For Manual Control:**
```json
{
  "turn_detection": null
}
```

---

## Turn Detection

Turn detection controls **when the assistant should respond** after the user has finished speaking.

### Turn Detection Flow

**With VAD (Automatic):**
```
1. User speaks → input_audio_buffer.speech_started
2. User stops → input_audio_buffer.speech_stopped
3. Wait silence_duration_ms
4. Auto-commit → input_audio_buffer.committed
5. Auto-generate → response.created (if create_response=true)
```

**Without VAD (Manual):**
```
1. User speaks (client buffers audio)
2. User releases button (client detects)
3. Client sends input_audio_buffer.commit
4. Client sends response.create
5. Server generates response
```

### Turn Detection Parameters

#### create_response

**Type:** `boolean`
**Default:** `true`

Automatically create response after turn ends.

**Example:**
```json
{
  "turn_detection": {
    "type": "server_vad",
    "create_response": false
  }
}
```

**When `true`:**
- Server auto-sends `response.create` after commit
- Natural conversation flow
- No client action needed

**When `false`:**
- Client must manually send `response.create`
- More control over response timing
- Useful for custom logic between turns

#### interrupt_response

**Type:** `boolean`
**Default:** `true`

Allow user to interrupt assistant's response.

**Example:**
```json
{
  "turn_detection": {
    "type": "server_vad",
    "interrupt_response": true
  }
}
```

**When `true`:**
- User speaking during assistant response triggers `conversation.interrupted`
- Server auto-cancels current response
- Server truncates assistant audio at interruption point
- Server may auto-start new response with user input

**When `false`:**
- User cannot interrupt assistant
- User input buffered until assistant finishes
- More formal turn-taking

### Interruption Handling

**Interruption Flow:**
```
1. Assistant speaking (response in progress)
2. User starts speaking → input_audio_buffer.speech_started
3. Server sends conversation.interrupted event
4. Server truncates assistant audio (conversation.item.truncate)
5. Server cancels response → response.done (status: "cancelled")
6. User continues speaking...
7. User stops → input_audio_buffer.speech_stopped
8. Server commits user input → input_audio_buffer.committed
9. Server creates new response (if create_response=true)
```

**Handling Interruptions (Client Side):**
```javascript
ws.on('message', (data) => {
  const event = JSON.parse(data);

  if (event.type === 'conversation.interrupted') {
    // Stop playing assistant audio
    audioPlayer.stop();

    // Clear audio buffer
    audioPlayer.clear();

    // Update UI (e.g., show "Listening...")
    updateStatus('listening');
  }

  if (event.type === 'input_audio_buffer.speech_stopped') {
    // User finished interrupting
    updateStatus('processing');
  }
});
```

### Turn Detection Best Practices

**For Natural Conversation:**
- Use `server_vad` or `semantic_vad`
- Set `create_response: true`
- Set `interrupt_response: true`
- Tune `silence_duration_ms` (400-800ms typical)

**For Formal Interviews:**
- Use `semantic_vad`
- Set `interrupt_response: false`
- Higher `silence_duration_ms` (700-1000ms)

**For Noisy Environments:**
- Use manual mode (`turn_detection: null`)
- Implement push-to-talk UI
- Client controls commit and response

**For Low Latency:**
- Use `server_vad`
- Lower `silence_duration_ms` (300-400ms)
- Risk of interrupting mid-sentence

---

## Modalities

Modalities control the input and output formats for the conversation.

### Modality Options

**Three Configurations:**

1. **Text Only** - `["text"]`
   - Input: Text messages only
   - Output: Text responses only
   - No audio processing

2. **Audio Only** - `["audio"]`
   - Input: Audio only
   - Output: Audio responses only
   - No text input/output

3. **Multimodal** - `["text", "audio"]` (default)
   - Input: Both text and audio
   - Output: Both text and audio
   - Full flexibility

### Setting Modalities

#### Session Level (Default for All Responses)

```json
{
  "type": "session.update",
  "session": {
    "modalities": ["text", "audio"]
  }
}
```

#### Response Level (Override for Single Response)

```json
{
  "type": "response.create",
  "response": {
    "modalities": ["text"]
  }
}
```

### Modality Behavior

#### Text-Only Mode

**Input:**
- Only accepts `conversation.item.create` with text content
- Audio input ignored or rejected

**Output:**
- Only generates `response.text.delta` events
- No `response.audio.delta` events
- No audio synthesis

**Use Cases:**
- Text chat interface over WebSocket
- Debugging and testing
- Environments without audio support

**Example:**
```json
{
  "type": "session.update",
  "session": {
    "modalities": ["text"]
  }
}

// Later...
{
  "type": "conversation.item.create",
  "item": {
    "type": "message",
    "role": "user",
    "content": [
      {
        "type": "input_text",
        "text": "Hello, what's the weather?"
      }
    ]
  }
}

{
  "type": "response.create"
}

// Server responds with:
// - response.created
// - response.output_item.added
// - response.content_part.added
// - response.text.delta (multiple)
// - response.text.done
// - response.output_item.done
// - response.done
```

#### Audio-Only Mode

**Input:**
- Only accepts `input_audio_buffer.append`
- Text input ignored or rejected

**Output:**
- Only generates `response.audio.delta` events
- No `response.text.delta` events
- May still include `response.audio_transcript.delta` if transcription enabled

**Use Cases:**
- Voice-only applications
- Phone/telephony integration
- Pure speech-to-speech

**Example:**
```json
{
  "type": "session.update",
  "session": {
    "modalities": ["audio"]
  }
}

// Later...
{
  "type": "input_audio_buffer.append",
  "audio": "base64_audio_data..."
}

{
  "type": "input_audio_buffer.commit"
}

{
  "type": "response.create"
}

// Server responds with:
// - response.created
// - response.output_item.added
// - response.content_part.added
// - response.audio.delta (multiple)
// - response.audio_transcript.delta (if transcription enabled)
// - response.audio.done
// - response.audio_transcript.done
// - response.output_item.done
// - response.done
```

#### Multimodal Mode (Default)

**Input:**
- Accepts both text and audio
- Can mix text and audio in conversation

**Output:**
- Generates both text and audio
- Client receives both delta streams
- Can render both simultaneously

**Use Cases:**
- Full-featured voice assistants
- Applications with visual and audio output
- Accessibility (subtitles + speech)

**Example:**
```json
{
  "type": "session.update",
  "session": {
    "modalities": ["text", "audio"]
  }
}

// Can send text input
{
  "type": "conversation.item.create",
  "item": {
    "type": "message",
    "role": "user",
    "content": [{"type": "input_text", "text": "Hello"}]
  }
}

// Or audio input
{
  "type": "input_audio_buffer.append",
  "audio": "base64_audio_data..."
}

// Server responds with both text and audio:
// - response.text.delta
// - response.audio.delta
// - response.audio_transcript.delta
```

### Modality Behavior Matrix

| Mode | Text Input | Audio Input | Text Output | Audio Output |
|------|------------|-------------|-------------|--------------|
| `["text"]` |  |  |  |  |
| `["audio"]` |  |  |  |  |
| `["text", "audio"]` |  |  |  |  |

### Modality Best Practices

**For Voice Assistants:**
```json
{
  "modalities": ["audio"],
  "input_audio_transcription": {
    "model": "whisper-1"  // For logging/display
  }
}
```

**For Accessible Apps:**
```json
{
  "modalities": ["text", "audio"]  // Both for accessibility
}
```

**For Debugging:**
```json
{
  "modalities": ["text"]  // Easier to log and debug
}
```

**Dynamic Switching:**
```javascript
// Start with audio only
ws.send(JSON.stringify({
  type: "session.update",
  session: { modalities: ["audio"] }
}));

// Switch to text for privacy
ws.send(JSON.stringify({
  type: "session.update",
  session: { modalities: ["text"] }
}));
```

---

## Tool/Function Calling

The Realtime API supports function calling similar to the Chat Completions API.

### Tool Definition

**Schema:**
```json
{
  "type": "session.update",
  "session": {
    "tools": [
      {
        "type": "function",
        "name": "get_weather",
        "description": "Get current weather for a location",
        "parameters": {
          "type": "object",
          "properties": {
            "location": {
              "type": "string",
              "description": "City and state, e.g. San Francisco, CA"
            },
            "unit": {
              "type": "string",
              "enum": ["celsius", "fahrenheit"],
              "description": "Temperature unit"
            }
          },
          "required": ["location"]
        }
      }
    ],
    "tool_choice": "auto"
  }
}
```

**Tool Structure:**
- `type`: Always `"function"`
- `name`: Function name (used to route calls)
- `description`: What the function does (helps model decide when to use)
- `parameters`: JSON Schema for function parameters

### Tool Choice Options

**1. `"auto"` (default)** - Model decides whether to call functions
```json
{"tool_choice": "auto"}
```

**2. `"none"` - Never call functions
```json
{"tool_choice": "none"}
```

**3. `"required"` - Must call at least one function
```json
{"tool_choice": "required"}
```

**4. Specific function** - Force specific function call
```json
{
  "tool_choice": {
    "type": "function",
    "name": "get_weather"
  }
}
```

### Function Call Flow

**1. Model Decides to Call Function**

Server sends:
```json
{
  "type": "response.output_item.added",
  "output_index": 0,
  "item": {
    "id": "item_123",
    "type": "function_call",
    "call_id": "call_456",
    "name": "get_weather",
    "arguments": ""  // Initially empty
  }
}

// Then streams arguments:
{
  "type": "response.function_call_arguments.delta",
  "item_id": "item_123",
  "call_id": "call_456",
  "delta": "{\"location"
}

{
  "type": "response.function_call_arguments.delta",
  "item_id": "item_123",
  "call_id": "call_456",
  "delta": "\": \"San Fra"
}

// ... more deltas

{
  "type": "response.function_call_arguments.done",
  "item_id": "item_123",
  "call_id": "call_456",
  "arguments": "{\"location\": \"San Francisco, CA\", \"unit\": \"celsius\"}"
}

{
  "type": "response.done",
  "response": {
    "status": "completed",
    "output": [
      {
        "type": "function_call",
        "call_id": "call_456",
        "name": "get_weather",
        "arguments": "{\"location\": \"San Francisco, CA\", \"unit\": \"celsius\"}"
      }
    ]
  }
}
```

**2. Client Executes Function**

Client parses arguments and calls function:
```javascript
const args = JSON.parse(functionCallEvent.arguments);
const result = await getWeather(args.location, args.unit);
// result = { temperature: 18, condition: "Sunny" }
```

**3. Client Sends Function Result**

```json
{
  "type": "conversation.item.create",
  "item": {
    "type": "function_call_output",
    "call_id": "call_456",
    "output": "{\"temperature\": 18, \"condition\": \"Sunny\"}"
  }
}
```

**4. Client Triggers Response with Result**

```json
{
  "type": "response.create"
}
```

**5. Model Uses Function Result**

Server generates response incorporating function result:
```json
{
  "type": "response.audio.delta",
  "delta": "base64_audio..."
}

// Audio transcript: "The weather in San Francisco is currently 18 degrees Celsius and sunny."
```

### Multiple Function Calls

The model can call multiple functions in one response:

```json
{
  "type": "response.done",
  "response": {
    "output": [
      {
        "type": "function_call",
        "call_id": "call_1",
        "name": "get_weather",
        "arguments": "{\"location\": \"San Francisco\"}"
      },
      {
        "type": "function_call",
        "call_id": "call_2",
        "name": "get_weather",
        "arguments": "{\"location\": \"New York\"}"
      }
    ]
  }
}
```

Client must send results for all calls:
```json
{
  "type": "conversation.item.create",
  "item": {
    "type": "function_call_output",
    "call_id": "call_1",
    "output": "{\"temperature\": 18}"
  }
}

{
  "type": "conversation.item.create",
  "item": {
    "type": "function_call_output",
    "call_id": "call_2",
    "output": "{\"temperature\": 22}"
  }
}

{
  "type": "response.create"
}
```

### Function Calling Best Practices

**1. Clear Descriptions**
```json
{
  "name": "get_weather",
  "description": "Get the current weather conditions and temperature for a specific city. Use this when the user asks about weather, temperature, or conditions."
}
```

**2. Detailed Parameter Descriptions**
```json
{
  "parameters": {
    "properties": {
      "location": {
        "type": "string",
        "description": "The city and state, e.g. 'San Francisco, CA' or 'New York, NY'. Use full city names."
      }
    }
  }
}
```

**3. Error Handling**
```javascript
try {
  const result = await executeFunction(name, args);

  ws.send(JSON.stringify({
    type: "conversation.item.create",
    item: {
      type: "function_call_output",
      call_id: callId,
      output: JSON.stringify(result)
    }
  }));
} catch (error) {
  ws.send(JSON.stringify({
    type: "conversation.item.create",
    item: {
      type: "function_call_output",
      call_id: callId,
      output: JSON.stringify({ error: error.message })
    }
  }));
}
```

**4. Streaming Function Calls**
```javascript
// Buffer arguments as they stream
let argsBuffer = '';

ws.on('message', (data) => {
  const event = JSON.parse(data);

  if (event.type === 'response.function_call_arguments.delta') {
    argsBuffer += event.delta;
  }

  if (event.type === 'response.function_call_arguments.done') {
    const args = JSON.parse(event.arguments); // Use complete args
    executeFunction(event.name, args);
  }
});
```

### Function Calling Example (Complete)

```javascript
// Define tools
ws.send(JSON.stringify({
  type: "session.update",
  session: {
    tools: [
      {
        type: "function",
        name: "get_weather",
        description: "Get current weather",
        parameters: {
          type: "object",
          properties: {
            location: { type: "string" }
          },
          required: ["location"]
        }
      }
    ],
    tool_choice: "auto"
  }
}));

// Handle function calls
ws.on('message', async (data) => {
  const event = JSON.parse(data);

  if (event.type === 'response.function_call_arguments.done') {
    const args = JSON.parse(event.arguments);

    // Execute function
    const result = await getWeather(args.location);

    // Send result
    ws.send(JSON.stringify({
      type: "conversation.item.create",
      item: {
        type: "function_call_output",
        call_id: event.call_id,
        output: JSON.stringify(result)
      }
    }));

    // Trigger response
    ws.send(JSON.stringify({
      type: "response.create"
    }));
  }
});
```

---

## Implementation Strategy

### For FakeAI Simulation

This section outlines how to implement a **simulated Realtime API** in FakeAI for testing and development purposes.

### Architecture Overview

**Components Needed:**

1. **WebSocket Server** - Accept WebSocket connections
2. **Session Manager** - Track session state per connection
3. **Event Handler** - Process client events and generate server events
4. **Audio Simulator** - Generate simulated audio responses
5. **VAD Simulator** - Simulate voice activity detection
6. **Streaming Engine** - Stream delta events realistically

### High-Level Implementation

```python
# fakeai/realtime_api.py

from fastapi import WebSocket, WebSocketDisconnect
import asyncio
import json
import base64
from typing import Dict, Any
import uuid
import time

class RealtimeSession:
    """Represents a single Realtime API session."""

    def __init__(self, session_id: str):
        self.id = session_id
        self.model = "openai/gpt-oss-120b-realtime-preview-2024-10-01"
        self.modalities = ["text", "audio"]
        self.instructions = ""
        self.voice = "alloy"
        self.input_audio_format = "pcm16"
        self.output_audio_format = "pcm16"
        self.input_audio_transcription = None
        self.turn_detection = {
            "type": "server_vad",
            "threshold": 0.5,
            "prefix_padding_ms": 300,
            "silence_duration_ms": 500,
            "create_response": True,
            "interrupt_response": True
        }
        self.tools = []
        self.tool_choice = "auto"
        self.temperature = 0.8
        self.max_response_output_tokens = "inf"

        # Runtime state
        self.audio_buffer = b''
        self.conversation_items = []
        self.current_response = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert session to JSON-serializable dict."""
        return {
            "id": self.id,
            "object": "realtime.session",
            "model": self.model,
            "modalities": self.modalities,
            "instructions": self.instructions,
            "voice": self.voice,
            "input_audio_format": self.input_audio_format,
            "output_audio_format": self.output_audio_format,
            "input_audio_transcription": self.input_audio_transcription,
            "turn_detection": self.turn_detection,
            "tools": self.tools,
            "tool_choice": self.tool_choice,
            "temperature": self.temperature,
            "max_response_output_tokens": self.max_response_output_tokens
        }

class RealtimeAPIHandler:
    """Handles Realtime API WebSocket connections."""

    def __init__(self):
        self.sessions: Dict[str, RealtimeSession] = {}

    async def handle_connection(self, websocket: WebSocket):
        """Handle a new WebSocket connection."""
        await websocket.accept()

        # Create new session
        session_id = f"sess_{uuid.uuid4().hex}"
        session = RealtimeSession(session_id)
        self.sessions[session_id] = session

        # Send session.created event
        await self.send_event(websocket, {
            "type": "session.created",
            "event_id": self.generate_event_id(),
            "session": session.to_dict()
        })

        try:
            # Main event loop
            while True:
                # Receive client event
                data = await websocket.receive_text()
                event = json.loads(data)

                # Handle event
                await self.handle_event(websocket, session, event)

        except WebSocketDisconnect:
            # Clean up session
            del self.sessions[session_id]

    async def handle_event(self, websocket: WebSocket,
                          session: RealtimeSession, event: Dict[str, Any]):
        """Handle a client event."""
        event_type = event.get("type")

        if event_type == "session.update":
            await self.handle_session_update(websocket, session, event)
        elif event_type == "input_audio_buffer.append":
            await self.handle_audio_append(websocket, session, event)
        elif event_type == "input_audio_buffer.commit":
            await self.handle_audio_commit(websocket, session, event)
        elif event_type == "conversation.item.create":
            await self.handle_item_create(websocket, session, event)
        elif event_type == "response.create":
            await self.handle_response_create(websocket, session, event)
        elif event_type == "response.cancel":
            await self.handle_response_cancel(websocket, session, event)
        # ... other event handlers

    async def handle_session_update(self, websocket: WebSocket,
                                    session: RealtimeSession, event: Dict[str, Any]):
        """Handle session.update event."""
        session_update = event.get("session", {})

        # Update session fields
        for key, value in session_update.items():
            if hasattr(session, key):
                setattr(session, key, value)

        # Send session.updated event
        await self.send_event(websocket, {
            "type": "session.updated",
            "event_id": self.generate_event_id(),
            "session": session.to_dict()
        })

    async def handle_audio_append(self, websocket: WebSocket,
                                  session: RealtimeSession, event: Dict[str, Any]):
        """Handle input_audio_buffer.append event."""
        audio_base64 = event.get("audio", "")
        audio_bytes = base64.b64decode(audio_base64)

        # Append to buffer
        session.audio_buffer += audio_bytes

        # Simulate VAD if enabled
        if session.turn_detection and session.turn_detection.get("type") in ["server_vad", "semantic_vad"]:
            await self.simulate_vad(websocket, session)

    async def handle_response_create(self, websocket: WebSocket,
                                     session: RealtimeSession, event: Dict[str, Any]):
        """Handle response.create event."""
        response_config = event.get("response", {})

        # Generate simulated response
        await self.generate_response(websocket, session, response_config)

    async def generate_response(self, websocket: WebSocket,
                               session: RealtimeSession, config: Dict[str, Any]):
        """Generate and stream a simulated response."""
        response_id = f"resp_{uuid.uuid4().hex}"
        item_id = f"item_{uuid.uuid4().hex}"

        # Send response.created
        await self.send_event(websocket, {
            "type": "response.created",
            "event_id": self.generate_event_id(),
            "response": {
                "id": response_id,
                "object": "realtime.response",
                "status": "in_progress",
                "status_details": None,
                "output": [],
                "usage": None
            }
        })

        # Send output_item.added
        await self.send_event(websocket, {
            "type": "response.output_item.added",
            "event_id": self.generate_event_id(),
            "response_id": response_id,
            "output_index": 0,
            "item": {
                "id": item_id,
                "object": "realtime.item",
                "type": "message",
                "role": "assistant",
                "content": []
            }
        })

        # Send content_part.added
        await self.send_event(websocket, {
            "type": "response.content_part.added",
            "event_id": self.generate_event_id(),
            "response_id": response_id,
            "item_id": item_id,
            "output_index": 0,
            "content_index": 0,
            "part": {
                "type": "audio",
                "audio": "",
                "transcript": ""
            }
        })

        # Generate simulated text and audio
        modalities = config.get("modalities", session.modalities)

        if "text" in modalities:
            await self.stream_text_response(websocket, response_id, item_id)

        if "audio" in modalities:
            await self.stream_audio_response(websocket, response_id, item_id)

        # Send response.done
        await self.send_event(websocket, {
            "type": "response.done",
            "event_id": self.generate_event_id(),
            "response": {
                "id": response_id,
                "status": "completed",
                "status_details": None,
                "output": [
                    {
                        "id": item_id,
                        "type": "message",
                        "role": "assistant",
                        "content": [
                            {
                                "type": "audio",
                                "audio": "simulated_complete_audio_base64...",
                                "transcript": "This is a simulated response."
                            }
                        ]
                    }
                ],
                "usage": {
                    "total_tokens": 50,
                    "input_tokens": 20,
                    "output_tokens": 30
                }
            }
        })

    async def stream_text_response(self, websocket: WebSocket,
                                   response_id: str, item_id: str):
        """Stream simulated text response."""
        text = "This is a simulated text response from the Realtime API."
        words = text.split()

        for i, word in enumerate(words):
            delta = word + (" " if i < len(words) - 1 else "")

            await self.send_event(websocket, {
                "type": "response.text.delta",
                "event_id": self.generate_event_id(),
                "response_id": response_id,
                "item_id": item_id,
                "output_index": 0,
                "content_index": 0,
                "delta": delta
            })

            # Simulate typing delay
            await asyncio.sleep(0.05)

        # Send text.done
        await self.send_event(websocket, {
            "type": "response.text.done",
            "event_id": self.generate_event_id(),
            "response_id": response_id,
            "item_id": item_id,
            "output_index": 0,
            "content_index": 0,
            "text": text
        })

    async def stream_audio_response(self, websocket: WebSocket,
                                    response_id: str, item_id: str):
        """Stream simulated audio response."""
        # Generate simulated audio chunks (silent PCM16)
        sample_rate = 24000
        chunk_duration_ms = 100
        samples_per_chunk = int(sample_rate * chunk_duration_ms / 1000)

        num_chunks = 20  # 2 seconds total

        for chunk_idx in range(num_chunks):
            # Generate silent audio (zeros)
            audio_chunk = bytes(samples_per_chunk * 2)  # 2 bytes per sample
            audio_base64 = base64.b64encode(audio_chunk).decode('utf-8')

            await self.send_event(websocket, {
                "type": "response.audio.delta",
                "event_id": self.generate_event_id(),
                "response_id": response_id,
                "item_id": item_id,
                "output_index": 0,
                "content_index": 0,
                "delta": audio_base64
            })

            # Simulate real-time audio streaming (100ms chunks)
            await asyncio.sleep(0.1)

        # Send audio.done
        await self.send_event(websocket, {
            "type": "response.audio.done",
            "event_id": self.generate_event_id(),
            "response_id": response_id,
            "item_id": item_id,
            "output_index": 0,
            "content_index": 0
        })

    async def simulate_vad(self, websocket: WebSocket, session: RealtimeSession):
        """Simulate voice activity detection."""
        # Simple simulation: detect speech if buffer has data
        buffer_duration_ms = len(session.audio_buffer) / (24000 * 2) * 1000

        if buffer_duration_ms > 100:  # More than 100ms of audio
            # Send speech_started if not already sent
            if not hasattr(session, '_speech_started'):
                session._speech_started = True

                await self.send_event(websocket, {
                    "type": "input_audio_buffer.speech_started",
                    "event_id": self.generate_event_id(),
                    "audio_start_ms": 0
                })

        # Simulate speech_stopped after silence_duration
        silence_duration_ms = session.turn_detection.get("silence_duration_ms", 500)

        if hasattr(session, '_speech_started') and buffer_duration_ms > silence_duration_ms:
            await self.send_event(websocket, {
                "type": "input_audio_buffer.speech_stopped",
                "event_id": self.generate_event_id(),
                "audio_end_ms": int(buffer_duration_ms)
            })

            # Auto-commit if enabled
            if session.turn_detection.get("create_response", True):
                await self.handle_audio_commit(websocket, session, {})
                await self.generate_response(websocket, session, {})

            # Reset state
            delattr(session, '_speech_started')

    async def send_event(self, websocket: WebSocket, event: Dict[str, Any]):
        """Send event to client."""
        await websocket.send_text(json.dumps(event))

    def generate_event_id(self) -> str:
        """Generate unique event ID."""
        return f"event_{uuid.uuid4().hex}"


# In app.py, add WebSocket endpoint

@app.websocket("/v1/realtime")
async def realtime_websocket(
    websocket: WebSocket,
    model: str = "openai/gpt-oss-120b-realtime-preview-2024-10-01"
):
    """Realtime API WebSocket endpoint."""
    # Verify authentication (check query params or headers)
    # For browser support, may need to accept token as query param

    handler = RealtimeAPIHandler()
    await handler.handle_connection(websocket)
```

### Key Implementation Details

#### 1. Audio Generation

For realistic audio simulation, you can:
- Generate silent PCM16 audio (zeros)
- Use TTS to generate actual speech
- Play back pre-recorded audio samples
- Use Faker to generate random audio data

```python
def generate_simulated_audio(text: str, duration_seconds: float) -> bytes:
    """Generate simulated PCM16 audio."""
    sample_rate = 24000
    num_samples = int(sample_rate * duration_seconds)

    # Generate silent audio (or use sine wave for testing)
    import numpy as np
    samples = np.zeros(num_samples, dtype=np.int16)

    # Optional: Add sine wave for testing
    # frequency = 440  # Hz (A4 note)
    # t = np.linspace(0, duration_seconds, num_samples)
    # samples = (np.sin(2 * np.pi * frequency * t) * 32767 * 0.5).astype(np.int16)

    return samples.tobytes()
```

#### 2. VAD Simulation

Simple VAD simulation based on audio buffer size:

```python
async def simulate_vad(self, websocket, session):
    """Simulate voice activity detection based on buffer."""
    buffer_size = len(session.audio_buffer)

    # Detect speech start
    if buffer_size > 4800 and not session.speech_active:  # ~100ms
        session.speech_active = True
        await self.send_event(websocket, {
            "type": "input_audio_buffer.speech_started",
            "event_id": self.generate_event_id(),
            "audio_start_ms": 0
        })

    # Detect speech stop (no new audio for X ms)
    current_time = time.time()
    if session.speech_active:
        if current_time - session.last_audio_time > 0.5:  # 500ms silence
            session.speech_active = False
            await self.send_event(websocket, {
                "type": "input_audio_buffer.speech_stopped",
                "event_id": self.generate_event_id(),
                "audio_end_ms": int((current_time - session.start_time) * 1000)
            })

            # Auto-commit and respond
            if session.turn_detection.get("create_response"):
                await self.auto_commit_and_respond(websocket, session)
```

#### 3. Function Calling

Simulate function call responses:

```python
async def generate_function_call_response(self, websocket, session):
    """Generate simulated function call."""
    tool = random.choice(session.tools)
    call_id = f"call_{uuid.uuid4().hex}"

    # Stream function arguments
    args = {"location": "San Francisco, CA"}
    args_json = json.dumps(args)

    for i in range(0, len(args_json), 5):
        chunk = args_json[i:i+5]
        await self.send_event(websocket, {
            "type": "response.function_call_arguments.delta",
            "delta": chunk,
            "call_id": call_id
        })
        await asyncio.sleep(0.05)

    # Send done
    await self.send_event(websocket, {
        "type": "response.function_call_arguments.done",
        "call_id": call_id,
        "arguments": args_json
    })
```

#### 4. Error Simulation

Simulate various error conditions:

```python
async def send_error(self, websocket, error_type: str, message: str,
                    code: str, event_id: str = None):
    """Send error event."""
    await self.send_event(websocket, {
        "type": "error",
        "event_id": self.generate_event_id(),
        "error": {
            "type": error_type,
            "code": code,
            "message": message,
            "param": None,
            "event_id": event_id
        }
    })
```

### Testing Strategy

**1. Unit Tests**
```python
# test_realtime_api.py

import pytest
from fastapi.testclient import TestClient
from websockets.sync.client import connect

def test_realtime_connection():
    """Test basic WebSocket connection."""
    with connect("ws://localhost:8000/v1/realtime?model=openai/gpt-oss-120b-realtime-preview-2024-10-01") as ws:
        # Receive session.created
        message = ws.recv()
        event = json.loads(message)
        assert event["type"] == "session.created"
        assert "session" in event

def test_session_update():
    """Test session.update event."""
    with connect("ws://localhost:8000/v1/realtime") as ws:
        ws.recv()  # session.created

        # Send session.update
        ws.send(json.dumps({
            "type": "session.update",
            "session": {
                "modalities": ["text"],
                "instructions": "Test instructions"
            }
        }))

        # Receive session.updated
        message = ws.recv()
        event = json.loads(message)
        assert event["type"] == "session.updated"
        assert event["session"]["modalities"] == ["text"]

def test_text_response():
    """Test text response generation."""
    with connect("ws://localhost:8000/v1/realtime") as ws:
        ws.recv()  # session.created

        # Create text item
        ws.send(json.dumps({
            "type": "conversation.item.create",
            "item": {
                "type": "message",
                "role": "user",
                "content": [{"type": "input_text", "text": "Hello"}]
            }
        }))

        # Create response
        ws.send(json.dumps({
            "type": "response.create"
        }))

        # Collect events
        events = []
        while True:
            message = ws.recv()
            event = json.loads(message)
            events.append(event)
            if event["type"] == "response.done":
                break

        # Verify event sequence
        event_types = [e["type"] for e in events]
        assert "response.created" in event_types
        assert "response.text.delta" in event_types
        assert "response.done" in event_types
```

**2. Integration Tests with OpenAI Client**
```python
# test_openai_realtime_client.py

from openai import AsyncOpenAI
import asyncio

async def test_with_openai_client():
    """Test with OpenAI's Realtime client."""
    client = AsyncOpenAI(
        api_key="test-key",
        base_url="ws://localhost:8000"
    )

    async with client.realtime.connect(
        model="openai/gpt-oss-120b-realtime-preview-2024-10-01"
    ) as conn:
        # Send session update
        await conn.session.update(
            modalities=["text"],
            instructions="You are a helpful assistant."
        )

        # Send message
        await conn.conversation.item.create(
            role="user",
            content=[{"type": "text", "text": "Hello"}]
        )

        # Create response
        response = await conn.response.create()

        # Verify response
        assert response.status == "completed"
        assert len(response.output) > 0
```

### Dependencies

Add to `pyproject.toml`:

```toml
[project.dependencies]
# ... existing dependencies
"websockets>=12.0"
"numpy>=1.24.0"  # For audio generation
```

### Configuration

Add Realtime API settings to `config.py`:

```python
class AppConfig(BaseSettings):
    # ... existing config

    # Realtime API settings
    realtime_enabled: bool = True
    realtime_simulate_vad: bool = True
    realtime_audio_generation: str = "silent"  # "silent", "sine", "tts"
    realtime_response_delay: float = 0.2  # Delay before response
```

---

## Summary

### Key Takeaways

**Connection:**
- WebSocket: `wss://api.openai.com/v1/realtime?model={model}`
- WebRTC: Lower latency, ephemeral tokens
- Authentication: `Authorization: Bearer {api_key}` + `OpenAI-Beta: realtime=v1`

**Event Architecture:**
- Bidirectional JSON events over WebSocket/WebRTC
- Client events: 11 types (session, audio, conversation, response control)
- Server events: 28+ types (lifecycle, streaming deltas, errors)

**Audio:**
- Three formats: PCM16 (24kHz), G.711 μ-law (8kHz), G.711 A-law (8kHz)
- Base64 encoded, no headers
- 11 voice options
- Streaming in ~100ms chunks

**VAD & Turn Detection:**
- Server VAD: Acoustic detection
- Semantic VAD: Content-aware detection
- Manual mode: Push-to-talk
- Configurable thresholds and timing

**Modalities:**
- Text only, audio only, or multimodal
- Session-level and response-level configuration
- Affects input acceptance and output generation

**Function Calling:**
- Same tool format as Chat Completions API
- Streamed arguments via delta events
- Client executes and returns results
- Supports multiple parallel calls

**Implementation:**
- FastAPI WebSocket endpoint
- Session state management
- Event handling and routing
- Audio simulation
- VAD simulation
- Streaming delta events

### Next Steps for FakeAI

1. Create `fakeai/realtime_api.py` with `RealtimeAPIHandler`
2. Add WebSocket endpoint to `app.py`
3. Implement session management
4. Implement event handlers for all 11 client events
5. Implement server event generation (28+ events)
6. Add audio generation (silent, sine wave, or TTS)
7. Implement VAD simulation
8. Add function calling support
9. Add comprehensive tests
10. Update documentation

---

**End of Research Document**

This document provides comprehensive technical details for implementing OpenAI Realtime API simulation in FakeAI. The implementation should focus on API compatibility and realistic behavior for testing purposes.
