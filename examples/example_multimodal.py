#!/usr/bin/env python3
"""
Multimodal Content with FakeAI.

This example demonstrates FakeAI's multimodal capabilities:
- Text + image messages (vision models)
- Text + audio messages (audio models)
- Vision token calculation
- Audio token calculation
- Multiple images in one request
- Image detail levels (low/high/auto)
- Base64 vs URL images
- Multimodal with streaming

FakeAI simulates vision models like GPT-4 Vision and audio models,
calculating appropriate token counts for different modalities.
"""
import asyncio
import base64

from openai import AsyncOpenAI

# Base URL for FakeAI server
BASE_URL = "http://localhost:8000"


def create_dummy_image_base64() -> str:
    """Create a small dummy image for testing (1x1 pixel PNG)."""
    # 1x1 red pixel PNG
    png_bytes = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg=="
    )
    return base64.b64encode(png_bytes).decode("utf-8")


async def demonstrate_basic_vision():
    """Demonstrate basic vision model usage."""
    print("=" * 80)
    print("PART 1: BASIC VISION MODEL")
    print("=" * 80)
    print()

    client = AsyncOpenAI(
        api_key="test-key",
        base_url=BASE_URL,
    )

    print("Model: openai/gpt-oss-120b-vision-preview")
    print("Content: Text + Image")
    print()

    # Create multimodal message with text + image
    response = await client.chat.completions.create(
        model="openai/gpt-oss-120b-vision-preview",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "What do you see in this image?"},
                    {
                        "type": "image_url",
                        "image_url": {"url": "https://example.com/image.jpg"},
                    },
                ],
            }
        ],
    )

    print("Response:")
    print(response.choices[0].message.content)
    print()
    print("Token Usage:")
    print(f"  Prompt tokens:     {response.usage.prompt_tokens}")
    print(f"  Completion tokens: {response.usage.completion_tokens}")
    print(f"  Total tokens:      {response.usage.total_tokens}")
    print()
    print("Note: Prompt tokens include both text and image tokens")
    print()


async def demonstrate_image_detail_levels():
    """Show how different image detail levels affect token usage."""
    print("=" * 80)
    print("PART 2: IMAGE DETAIL LEVELS")
    print("=" * 80)
    print()

    client = AsyncOpenAI(
        api_key="test-key",
        base_url=BASE_URL,
    )

    print("Image detail affects token usage:")
    print()

    detail_levels = ["low", "high", "auto"]

    for detail in detail_levels:
        print(f"Detail level: {detail}")
        print("-" * 80)

        response = await client.chat.completions.create(
            model="openai/gpt-oss-120b-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Describe this image"},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": "https://example.com/image.jpg",
                                "detail": detail,
                            },
                        },
                    ],
                }
            ],
        )

        print(f"  Prompt tokens: {response.usage.prompt_tokens}")
        print()

    print("Typical token usage:")
    print("  • low:  ~85 tokens per image")
    print("  • high: ~170-765 tokens (depends on image size)")
    print("  • auto: FakeAI chooses based on simulated image size")
    print()


async def demonstrate_multiple_images():
    """Demonstrate sending multiple images in one request."""
    print("=" * 80)
    print("PART 3: MULTIPLE IMAGES")
    print("=" * 80)
    print()

    client = AsyncOpenAI(
        api_key="test-key",
        base_url=BASE_URL,
    )

    print("Sending 3 images in one request...")
    print()

    response = await client.chat.completions.create(
        model="openai/gpt-oss-120b-vision-preview",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Compare these three images:"},
                    {
                        "type": "image_url",
                        "image_url": {"url": "https://example.com/image1.jpg"},
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": "https://example.com/image2.jpg"},
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": "https://example.com/image3.jpg"},
                    },
                ],
            }
        ],
    )

    print(f"Response: {response.choices[0].message.content[:150]}...")
    print()
    print("Token Usage:")
    print(f"  Prompt tokens: {response.usage.prompt_tokens}")
    print(f"  (Text tokens + 3 × image tokens)")
    print()


async def demonstrate_base64_images():
    """Demonstrate using base64-encoded images."""
    print("=" * 80)
    print("PART 4: BASE64-ENCODED IMAGES")
    print("=" * 80)
    print()

    client = AsyncOpenAI(
        api_key="test-key",
        base_url=BASE_URL,
    )

    print("Using base64-encoded image data...")
    print()

    # Create a small test image
    image_base64 = create_dummy_image_base64()

    response = await client.chat.completions.create(
        model="openai/gpt-oss-120b-vision-preview",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "What is this?"},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{image_base64}"},
                    },
                ],
            }
        ],
    )

    print(f"Response: {response.choices[0].message.content}")
    print()
    print(f"Prompt tokens: {response.usage.prompt_tokens}")
    print()
    print("Both URL and base64 images are supported!")
    print()


async def demonstrate_vision_streaming():
    """Demonstrate streaming with vision models."""
    print("=" * 80)
    print("PART 5: STREAMING WITH VISION")
    print("=" * 80)
    print()

    client = AsyncOpenAI(
        api_key="test-key",
        base_url=BASE_URL,
    )

    print("Streaming response for image analysis...")
    print()
    print("Response:")
    print("-" * 80)

    stream = await client.chat.completions.create(
        model="openai/gpt-oss-120b-vision-preview",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Describe this image in detail"},
                    {
                        "type": "image_url",
                        "image_url": {"url": "https://example.com/landscape.jpg"},
                    },
                ],
            }
        ],
        stream=True,
    )

    async for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            print(chunk.choices[0].delta.content, end="", flush=True)

    print()
    print()
    print("Vision models work with streaming too!")
    print()


async def demonstrate_audio_input():
    """Demonstrate audio input processing."""
    print("=" * 80)
    print("PART 6: AUDIO INPUT")
    print("=" * 80)
    print()

    client = AsyncOpenAI(
        api_key="test-key",
        base_url=BASE_URL,
    )

    print("Model: openai/gpt-oss-120b-audio-preview")
    print("Content: Text + Audio")
    print()

    # Create dummy audio data (base64-encoded)
    dummy_audio = base64.b64encode(b"fake audio data").decode("utf-8")

    response = await client.chat.completions.create(
        model="openai/gpt-oss-120b-audio-preview",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "What does this audio say?"},
                    {
                        "type": "input_audio",
                        "input_audio": {"data": dummy_audio, "format": "wav"},
                    },
                ],
            }
        ],
    )

    print("Response:")
    print(response.choices[0].message.content)
    print()
    print("Token Usage:")
    print(f"  Prompt tokens:  {response.usage.prompt_tokens}")
    if response.usage.prompt_tokens_details:
        print(f"  Audio tokens:   {response.usage.prompt_tokens_details.audio_tokens}")
        text_tokens = (
            response.usage.prompt_tokens
            - response.usage.prompt_tokens_details.audio_tokens
        )
        print(f"  Text tokens:    {text_tokens}")
    print()


async def demonstrate_audio_output():
    """Demonstrate audio output generation."""
    print("=" * 80)
    print("PART 7: AUDIO OUTPUT")
    print("=" * 80)
    print()

    client = AsyncOpenAI(
        api_key="test-key",
        base_url=BASE_URL,
    )

    print("Generating audio output...")
    print()

    response = await client.chat.completions.create(
        model="openai/gpt-oss-120b-audio-preview",
        modalities=["text", "audio"],
        audio={"voice": "alloy", "format": "mp3"},
        messages=[{"role": "user", "content": "Say hello in a friendly voice"}],
    )

    print("Response:")
    print(f"  Text: {response.choices[0].message.content}")
    if response.choices[0].message.audio:
        print(f"  Audio ID: {response.choices[0].message.audio.id}")
        print(f"  Audio expires: {response.choices[0].message.audio.expires_at}")
        print(f"  Audio transcript: {response.choices[0].message.audio.transcript}")
    print()
    print("Token Usage:")
    if response.usage.completion_tokens_details:
        print(
            f"  Audio output tokens: {response.usage.completion_tokens_details.audio_tokens}"
        )
    print()


async def demonstrate_vision_conversation():
    """Demonstrate multi-turn conversation with images."""
    print("=" * 80)
    print("PART 8: VISION IN MULTI-TURN CONVERSATION")
    print("=" * 80)
    print()

    client = AsyncOpenAI(
        api_key="test-key",
        base_url=BASE_URL,
    )

    print("Turn 1: Send image")
    print("-" * 80)

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "What color is the car in this image?"},
                {
                    "type": "image_url",
                    "image_url": {"url": "https://example.com/car.jpg"},
                },
            ],
        }
    ]

    response = await client.chat.completions.create(
        model="openai/gpt-oss-120b-vision-preview",
        messages=messages,
    )

    print(f"Assistant: {response.choices[0].message.content}")
    print(f"Tokens: {response.usage.prompt_tokens}")
    print()

    # Add response to conversation
    messages.append(
        {"role": "assistant", "content": response.choices[0].message.content}
    )

    # Turn 2: Follow-up (image still in context)
    messages.append({"role": "user", "content": "What about the wheels?"})

    print("Turn 2: Follow-up question")
    print("-" * 80)

    response = await client.chat.completions.create(
        model="openai/gpt-oss-120b-vision-preview",
        messages=messages,
    )

    print(f"Assistant: {response.choices[0].message.content}")
    print(f"Tokens: {response.usage.prompt_tokens}")
    print()
    print("Note: Image tokens counted again in prompt (entire context)")
    print()


async def demonstrate_mixed_modalities():
    """Demonstrate mixing text, images, and audio."""
    print("=" * 80)
    print("PART 9: MIXED MODALITIES")
    print("=" * 80)
    print()

    client = AsyncOpenAI(
        api_key="test-key",
        base_url=BASE_URL,
    )

    print("Sending text + image + audio in one request...")
    print()

    dummy_audio = base64.b64encode(b"audio data").decode("utf-8")

    response = await client.chat.completions.create(
        model="openai/gpt-oss-120b-audio-preview",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Compare this image and audio:"},
                    {
                        "type": "image_url",
                        "image_url": {"url": "https://example.com/scene.jpg"},
                    },
                    {
                        "type": "input_audio",
                        "input_audio": {"data": dummy_audio, "format": "wav"},
                    },
                ],
            }
        ],
    )

    print(f"Response: {response.choices[0].message.content}")
    print()
    print("Token Breakdown:")
    print(f"  Total prompt tokens: {response.usage.prompt_tokens}")
    if response.usage.prompt_tokens_details:
        print(
            f"  Audio tokens:        {response.usage.prompt_tokens_details.audio_tokens}"
        )
        other_tokens = (
            response.usage.prompt_tokens
            - response.usage.prompt_tokens_details.audio_tokens
        )
        print(f"  Text + image tokens: {other_tokens}")
    print()


async def main():
    """Run all multimodal demonstrations."""
    print()
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 18 + "FakeAI Multimodal Demonstration" + " " * 28 + "║")
    print("╚" + "=" * 78 + "╝")
    print()
    print("This demo shows FakeAI's multimodal capabilities including vision")
    print("and audio processing with accurate token calculation.")
    print()
    input("Press Enter to start...")
    print()

    try:
        await demonstrate_basic_vision()
        input("Press Enter to continue...")
        print()

        await demonstrate_image_detail_levels()
        input("Press Enter to continue...")
        print()

        await demonstrate_multiple_images()
        input("Press Enter to continue...")
        print()

        await demonstrate_base64_images()
        input("Press Enter to continue...")
        print()

        await demonstrate_vision_streaming()
        input("Press Enter to continue...")
        print()

        await demonstrate_audio_input()
        input("Press Enter to continue...")
        print()

        await demonstrate_audio_output()
        input("Press Enter to continue...")
        print()

        await demonstrate_vision_conversation()
        input("Press Enter to continue...")
        print()

        await demonstrate_mixed_modalities()

        print("=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print()
        print("Multimodal Capabilities:")
        print()
        print("Vision Models:")
        print(
            "  • openai/gpt-oss-120b-vision-preview, openai/gpt-oss-120b, openai/gpt-oss-20b"
        )
        print("  • Text + image(s) in messages")
        print("  • Image detail levels: low (~85 tokens), high (~170-765 tokens)")
        print("  • Supports URLs and base64-encoded images")
        print("  • Works with streaming")
        print()
        print("Audio Models:")
        print("  • openai/gpt-oss-120b-audio-preview")
        print("  • Audio input: WAV, MP3 formats")
        print("  • Audio output: 11 voice options, 6 formats")
        print("  • Audio tokens tracked separately")
        print()
        print("Token Calculation:")
        print("  • Text tokens: word count + punctuation")
        print("  • Image tokens: based on detail level")
        print("  • Audio tokens: based on duration")
        print("  • All tracked in usage.prompt_tokens_details")
        print()
        print("Content Format:")
        print("  messages[].content can be:")
        print("    • string (text only)")
        print("    • array of content parts (multimodal):")
        print("      - {type: 'text', text: '...'}")
        print("      - {type: 'image_url', image_url: {...}}")
        print("      - {type: 'input_audio', input_audio: {...}}")
        print()

    except Exception as e:
        print(f"Error: {e}")
        print()
        print("Make sure FakeAI server is running:")
        print("  python run_server.py")
        print()


if __name__ == "__main__":
    asyncio.run(main())
