# Multi-Modal Content Guide

This guide explains how to use multi-modal content (text, images, and audio) in FakeAI.

## Table of Contents

- [Overview](#overview)
- [Content Types](#content-types)
- [Text Content](#text-content)
- [Image Content](#image-content)
- [Audio Content](#audio-content)
- [Combining Multiple Modalities](#combining-multiple-modalities)
- [Complete Examples](#complete-examples)

---

## Overview

FakeAI supports multi-modal content in chat completion messages, allowing you to combine text, images, and audio in a single request. This enables applications that process:

- Visual question answering
- Image description and analysis
- Audio transcription and understanding
- Combined text, image, and audio processing

Multi-modal content is specified using content arrays instead of simple text strings in the `content` field of a message.

---

## Content Types

There are three types of content parts:

1. **TextContent** - Plain text
2. **ImageContent** - Images via URL or base64
3. **InputAudioContent** - Audio in base64 format

All content parts are combined in an array within the `content` field of a message.

---

## Text Content

Text content is the simplest form and works exactly like traditional string content.

### Schema

```python
{
  "type": "text",
  "text": "Your text here"
}
```

### Example

```python
from fakeai.models import TextContent

text_content = TextContent(
    type="text",
    text="Describe this image in detail"
)
```

### Using with OpenAI Client

```python
from openai import OpenAI

client = OpenAI(
    api_key="sk-fakeai-1234567890abcdef",
    base_url="http://localhost:8000/v1"
)

response = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Hello!"}
            ]
        }
    ]
)
```

---

## Image Content

Images can be provided in two ways:
1. **URL**: A publicly accessible URL
2. **Base64**: Data URI with base64-encoded image data

### Schema

```python
{
  "type": "image_url",
  "image_url": {
    "url": "https://example.com/image.jpg",  # or data URI
    "detail": "auto"  # or "low" or "high"
  }
}
```

### Fields

- `url` (string, required): Image URL or data URI
- `detail` (string, optional): Processing detail level
  - `"auto"` (default): Let model decide
  - `"low"`: Lower resolution, faster
  - `"high"`: Higher resolution, more detailed

### Example with URL

```python
from fakeai.models import ImageContent, ImageUrl

image_content = ImageContent(
    type="image_url",
    image_url=ImageUrl(
        url="https://example.com/photo.jpg",
        detail="high"
    )
)
```

### Example with Base64

Images can be embedded directly in the request using base64 encoding:

```python
import base64
from fakeai.models import ImageContent, ImageUrl

# Read and encode an image
with open("image.png", "rb") as f:
    image_data = base64.b64encode(f.read()).decode("utf-8")

# Create data URI
data_uri = f"data:image/png;base64,{image_data}"

image_content = ImageContent(
    type="image_url",
    image_url=ImageUrl(
        url=data_uri,
        detail="high"
    )
)
```

### Using with OpenAI Client (URL)

```python
response = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "What's in this image?"},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "https://example.com/image.jpg",
                        "detail": "high"
                    }
                }
            ]
        }
    ]
)
```

### Using with OpenAI Client (Base64)

```python
import base64

# Read and encode image
with open("photo.jpg", "rb") as f:
    image_data = base64.b64encode(f.read()).decode("utf-8")

response = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Analyze this image"},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image_data}",
                        "detail": "high"
                    }
                }
            ]
        }
    ]
)
```

### Supported Image Formats

Common formats for base64 encoding:
- `data:image/png;base64,...`
- `data:image/jpeg;base64,...`
- `data:image/jpg;base64,...`
- `data:image/gif;base64,...`
- `data:image/webp;base64,...`

---

## Audio Content

Audio content allows you to include audio data in your requests.

### Schema

```python
{
  "type": "input_audio",
  "input_audio": {
    "data": "base64_encoded_audio",
    "format": "wav"  # or "mp3"
  }
}
```

### Fields

- `data` (string, required): Base64-encoded audio data
- `format` (string, required): Audio format
  - `"wav"`: WAV format
  - `"mp3"`: MP3 format

### Example

```python
from fakeai.models import InputAudioContent, InputAudio
import base64

# Read and encode audio file
with open("audio.wav", "rb") as f:
    audio_data = base64.b64encode(f.read()).decode("utf-8")

audio_content = InputAudioContent(
    type="input_audio",
    input_audio=InputAudio(
        data=audio_data,
        format="wav"
    )
)
```

### Using with OpenAI Client

```python
import base64

# Read and encode audio
with open("recording.mp3", "rb") as f:
    audio_data = base64.b64encode(f.read()).decode("utf-8")

response = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Transcribe and summarize this audio"},
                {
                    "type": "input_audio",
                    "input_audio": {
                        "data": audio_data,
                        "format": "mp3"
                    }
                }
            ]
        }
    ]
)
```

### Audio Output Configuration

You can also configure audio output:

```python
from fakeai.models import AudioConfig

response = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[{"role": "user", "content": "Tell me a story"}],
    modalities=["text", "audio"],
    audio=AudioConfig(
        voice="alloy",
        format="mp3"
    )
)
```

**Available Voices:**
- `alloy`
- `ash`
- `ballad`
- `coral`
- `echo`
- `fable`
- `onyx`
- `nova`
- `sage`
- `shimmer`
- `verse`

**Available Formats:**
- `mp3`
- `opus`
- `aac`
- `flac`
- `wav`
- `pcm16`

---

## Combining Multiple Modalities

You can combine text, images, and audio in a single message.

### Example: Text + Image + Audio

```python
import base64

# Load image
with open("diagram.png", "rb") as f:
    image_data = base64.b64encode(f.read()).decode("utf-8")

# Load audio
with open("explanation.wav", "rb") as f:
    audio_data = base64.b64encode(f.read()).decode("utf-8")

response = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Compare the visual diagram with the audio explanation"
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{image_data}",
                        "detail": "high"
                    }
                },
                {
                    "type": "input_audio",
                    "input_audio": {
                        "data": audio_data,
                        "format": "wav"
                    }
                }
            ]
        }
    ]
)

print(response.choices[0].message.content)
```

### Example: Multiple Images

```python
response = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Compare these two images"},
                {
                    "type": "image_url",
                    "image_url": {"url": "https://example.com/image1.jpg"}
                },
                {
                    "type": "image_url",
                    "image_url": {"url": "https://example.com/image2.jpg"}
                }
            ]
        }
    ]
)
```

---

## Complete Examples

### Example 1: Visual Question Answering

```python
from openai import OpenAI
import base64

client = OpenAI(
    api_key="sk-fakeai-1234567890abcdef",
    base_url="http://localhost:8000/v1"
)

# Load image
with open("chart.png", "rb") as f:
    image_data = base64.b64encode(f.read()).decode("utf-8")

response = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[
        {
            "role": "system",
            "content": "You are an expert at analyzing charts and graphs."
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "What are the key trends shown in this chart?"
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{image_data}",
                        "detail": "high"
                    }
                }
            ]
        }
    ],
    max_tokens=500
)

print(response.choices[0].message.content)
```

### Example 2: Audio Transcription and Analysis

```python
import base64

# Load audio file
with open("interview.mp3", "rb") as f:
    audio_data = base64.b64encode(f.read()).decode("utf-8")

response = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Transcribe this audio and extract key points"
                },
                {
                    "type": "input_audio",
                    "input_audio": {
                        "data": audio_data,
                        "format": "mp3"
                    }
                }
            ]
        }
    ],
    max_tokens=1000
)

print(response.choices[0].message.content)
```

### Example 3: Multi-Modal Conversation

```python
import base64

# Load resources
with open("screenshot.png", "rb") as f:
    screenshot_data = base64.b64encode(f.read()).decode("utf-8")

with open("audio_description.wav", "rb") as f:
    audio_data = base64.b64encode(f.read()).decode("utf-8")

response = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[
        {
            "role": "system",
            "content": "You are a helpful assistant that can analyze images and audio."
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Here's a screenshot of an issue I'm experiencing"
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{screenshot_data}",
                        "detail": "high"
                    }
                }
            ]
        },
        {
            "role": "assistant",
            "content": "I can see the error message in the screenshot. What else can you tell me?"
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Here's an audio recording of what happens"
                },
                {
                    "type": "input_audio",
                    "input_audio": {
                        "data": audio_data,
                        "format": "wav"
                    }
                }
            ]
        }
    ],
    max_tokens=1000
)

print(response.choices[0].message.content)
```

### Example 4: Streaming with Multi-Modal Content

```python
import base64

with open("image.jpg", "rb") as f:
    image_data = base64.b64encode(f.read()).decode("utf-8")

stream = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Describe this image in detail"},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image_data}",
                        "detail": "high"
                    }
                }
            ]
        }
    ],
    stream=True
)

print("Response: ", end="", flush=True)
for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
print()
```

### Example 5: Using Pydantic Models Directly

```python
from fakeai.models import (
    ChatCompletionRequest,
    Message,
    Role,
    TextContent,
    ImageContent,
    ImageUrl,
    InputAudioContent,
    InputAudio
)
import base64
import httpx

# Load resources
with open("photo.png", "rb") as f:
    image_b64 = base64.b64encode(f.read()).decode("utf-8")

with open("audio.mp3", "rb") as f:
    audio_b64 = base64.b64encode(f.read()).decode("utf-8")

# Build request with Pydantic models
request = ChatCompletionRequest(
    model="openai/gpt-oss-120b",
    messages=[
        Message(
            role=Role.USER,
            content=[
                TextContent(text="Analyze both the image and audio"),
                ImageContent(
                    image_url=ImageUrl(
                        url=f"data:image/png;base64,{image_b64}",
                        detail="high"
                    )
                ),
                InputAudioContent(
                    input_audio=InputAudio(
                        data=audio_b64,
                        format="mp3"
                    )
                )
            ]
        )
    ],
    temperature=0.7,
    max_tokens=500
)

# Send request
response = httpx.post(
    "http://localhost:8000/v1/chat/completions",
    headers={"Authorization": "Bearer sk-fakeai-1234567890abcdef"},
    json=request.model_dump(exclude_none=True)
)

data = response.json()
print(data["choices"][0]["message"]["content"])
```

---

## Best Practices

1. **Image Size**: Keep images reasonably sized. Large images should be resized before encoding to base64.

2. **Audio Duration**: For best results, keep audio clips under a few minutes.

3. **Base64 Encoding**: Always use UTF-8 encoding when converting binary data to base64 strings.

4. **Detail Level**: Use `"high"` detail for images with text or fine details, `"low"` for general scenes.

5. **Content Ordering**: Place text content before media content for clarity.

6. **Error Handling**: Always validate that files exist and can be read before encoding.

7. **Memory Usage**: Be mindful of memory when loading large media files.

---

## Troubleshooting

### Issue: Base64 String Too Long

**Problem**: Request fails due to large base64 data.

**Solution**: Resize images or compress audio before encoding:

```python
from PIL import Image
import io
import base64

# Resize image
img = Image.open("large_image.jpg")
img.thumbnail((1024, 1024))  # Max dimension 1024px

# Convert to base64
buffer = io.BytesIO()
img.save(buffer, format="JPEG", quality=85)
image_data = base64.b64encode(buffer.getvalue()).decode("utf-8")
```

### Issue: Invalid Data URI Format

**Problem**: Image not recognized.

**Solution**: Ensure proper data URI format:

```python
# Correct format
data_uri = f"data:image/{format};base64,{base64_string}"

# Examples:
# data:image/png;base64,iVBORw0KGgo...
# data:image/jpeg;base64,/9j/4AAQSk...
```

### Issue: Audio Format Not Supported

**Problem**: Audio format error.

**Solution**: Convert audio to WAV or MP3:

```python
from pydub import AudioSegment

# Convert to WAV
audio = AudioSegment.from_file("input.ogg")
audio.export("output.wav", format="wav")
```

---

## API Reference

For complete API documentation, see:
- [ENDPOINTS.md](ENDPOINTS.md) - Full endpoint reference
- [SCHEMAS.md](SCHEMAS.md) - Complete schema documentation
