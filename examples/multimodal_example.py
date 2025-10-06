#!/usr/bin/env python3
"""
Example demonstrating multimodal chat completions with image and audio inputs.

This example shows how to use FakeAI with:
- Image inputs (vision)
- Audio inputs (speech)
- Combined multimodal inputs
"""
import asyncio
import base64

from fakeai import AppConfig, FakeAIService
from fakeai.models import (
    ChatCompletionRequest,
    ImageContent,
    ImageUrl,
    InputAudio,
    InputAudioContent,
    Message,
    Role,
    TextContent,
)
from fakeai.utils import generate_wav_audio


async def example_vision_only():
    """Example with image input only."""
    print("=" * 70)
    print("Example 1: Vision (Image) Input Only")
    print("=" * 70)

    config = AppConfig(response_delay=0.0)
    service = FakeAIService(config)

    request = ChatCompletionRequest(
        model="openai/gpt-oss-120b",
        messages=[
            Message(
                role=Role.USER,
                content=[
                    TextContent(type="text", text="What do you see in this image?"),
                    ImageContent(
                        type="image_url",
                        image_url=ImageUrl(
                            url="https://example.com/1024x1024/sunset.jpg",
                            detail="high",
                        ),
                    ),
                ],
            )
        ],
        max_tokens=100,
    )

    response = await service.create_chat_completion(request)

    print(f"Response: {response.choices[0].message.content}\n")
    print(f"Token Usage:")
    print(f"  - Prompt tokens: {response.usage.prompt_tokens}")
    print(f"  - Completion tokens: {response.usage.completion_tokens}")
    print(f"  - Total tokens: {response.usage.total_tokens}")
    print()


async def example_audio_only():
    """Example with audio input only."""
    print("=" * 70)
    print("Example 2: Audio Input Only")
    print("=" * 70)

    config = AppConfig(response_delay=0.0)
    service = FakeAIService(config)

    # Generate sample audio (2 seconds)
    wav_audio = generate_wav_audio(2.0)
    audio_b64 = base64.b64encode(wav_audio).decode("utf-8")

    request = ChatCompletionRequest(
        model="openai/gpt-oss-120b",
        messages=[
            Message(
                role=Role.USER,
                content=[
                    TextContent(type="text", text="What did I say in the audio?"),
                    InputAudioContent(
                        type="input_audio",
                        input_audio=InputAudio(data=audio_b64, format="wav"),
                    ),
                ],
            )
        ],
        max_tokens=100,
    )

    response = await service.create_chat_completion(request)

    print(f"Response: {response.choices[0].message.content}\n")
    print(f"Token Usage:")
    print(f"  - Prompt tokens: {response.usage.prompt_tokens}")
    print(
        f"  - Audio input tokens: {response.usage.prompt_tokens_details.audio_tokens}"
    )
    print(f"  - Completion tokens: {response.usage.completion_tokens}")
    print(f"  - Total tokens: {response.usage.total_tokens}")
    print()


async def example_multimodal_combined():
    """Example with both image and audio inputs."""
    print("=" * 70)
    print("Example 3: Combined Multimodal (Image + Audio)")
    print("=" * 70)

    config = AppConfig(response_delay=0.0)
    service = FakeAIService(config)

    # Generate sample audio (3 seconds)
    wav_audio = generate_wav_audio(3.0)
    audio_b64 = base64.b64encode(wav_audio).decode("utf-8")

    request = ChatCompletionRequest(
        model="openai/gpt-oss-120b",
        messages=[
            Message(
                role=Role.USER,
                content=[
                    TextContent(
                        type="text",
                        text="Look at this image and listen to my question:",
                    ),
                    ImageContent(
                        type="image_url",
                        image_url=ImageUrl(
                            url="https://example.com/2048x1024/landscape.jpg",
                            detail="high",
                        ),
                    ),
                    InputAudioContent(
                        type="input_audio",
                        input_audio=InputAudio(data=audio_b64, format="wav"),
                    ),
                ],
            )
        ],
        max_tokens=150,
    )

    response = await service.create_chat_completion(request)

    print(f"Response: {response.choices[0].message.content}\n")
    print(f"Token Usage:")
    print(f"  - Total prompt tokens: {response.usage.prompt_tokens}")
    print(
        f"    - Text tokens: ~{response.usage.prompt_tokens - response.usage.prompt_tokens_details.audio_tokens}"
    )
    print(
        f"    - Image tokens: ~{response.usage.prompt_tokens - response.usage.prompt_tokens_details.audio_tokens - 10}"
    )
    print(f"    - Audio tokens: {response.usage.prompt_tokens_details.audio_tokens}")
    print(f"  - Completion tokens: {response.usage.completion_tokens}")
    print(f"  - Total tokens: {response.usage.total_tokens}")
    print()


async def example_multiple_images():
    """Example with multiple images."""
    print("=" * 70)
    print("Example 4: Multiple Images")
    print("=" * 70)

    config = AppConfig(response_delay=0.0)
    service = FakeAIService(config)

    request = ChatCompletionRequest(
        model="openai/gpt-oss-120b",
        messages=[
            Message(
                role=Role.USER,
                content=[
                    TextContent(type="text", text="Compare these two images:"),
                    ImageContent(
                        type="image_url",
                        image_url=ImageUrl(
                            url="https://example.com/512x512/image1.jpg", detail="high"
                        ),
                    ),
                    ImageContent(
                        type="image_url",
                        image_url=ImageUrl(
                            url="https://example.com/512x512/image2.jpg",
                            detail="low",  # Low detail for faster processing
                        ),
                    ),
                ],
            )
        ],
        max_tokens=150,
    )

    response = await service.create_chat_completion(request)

    print(f"Response: {response.choices[0].message.content}\n")
    print(f"Token Usage:")
    print(f"  - Prompt tokens: {response.usage.prompt_tokens}")
    print(f"  - Completion tokens: {response.usage.completion_tokens}")
    print(f"  - Total tokens: {response.usage.total_tokens}")
    print()


async def main():
    """Run all examples."""
    await example_vision_only()
    await example_audio_only()
    await example_multimodal_combined()
    await example_multiple_images()

    print("=" * 70)
    print("All multimodal examples completed successfully! ✅")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
