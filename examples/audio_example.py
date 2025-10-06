#!/usr/bin/env python3
"""
Example demonstrating audio input/output in FakeAI chat completions.

This example shows:
1. Processing audio input (speech-to-text)
2. Generating audio output (text-to-speech)
3. Token accounting for audio
4. Using modalities parameter
"""
#  SPDX-License-Identifier: Apache-2.0

import asyncio
import base64
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fakeai import AppConfig
from fakeai.fakeai_service import FakeAIService
from fakeai.models import (
    AudioConfig,
    ChatCompletionRequest,
    InputAudio,
    InputAudioContent,
    Message,
    Role,
    TextContent,
)
from fakeai.utils import generate_wav_audio


async def example_audio_input():
    """Example: Processing audio input."""
    print("=" * 60)
    print("Example 1: Audio Input Processing")
    print("=" * 60)

    config = AppConfig(response_delay=0.0)
    service = FakeAIService(config)

    # Create a 3-second audio input
    audio_bytes = generate_wav_audio(3.0)
    audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")

    # Create request with audio input
    request = ChatCompletionRequest(
        model="openai/gpt-oss-120b",
        messages=[
            Message(
                role=Role.USER,
                content=[
                    TextContent(type="text", text="I'm sending you audio:"),
                    InputAudioContent(
                        type="input_audio",
                        input_audio=InputAudio(data=audio_b64, format="wav"),
                    ),
                ],
            )
        ],
        max_tokens=50,
    )

    response = await service.create_chat_completion(request)

    print(f"\nResponse: {response.choices[0].message.content}")
    print(f"\nToken Usage:")
    print(f"  Prompt tokens: {response.usage.prompt_tokens}")
    print(f"  Audio input tokens: {response.usage.prompt_tokens_details.audio_tokens}")
    print(f"  Completion tokens: {response.usage.completion_tokens}")
    print(f"  Total tokens: {response.usage.total_tokens}")


async def example_audio_output():
    """Example: Generating audio output."""
    print("\n" + "=" * 60)
    print("Example 2: Audio Output Generation")
    print("=" * 60)

    config = AppConfig(response_delay=0.0)
    service = FakeAIService(config)

    # Create request with audio output
    request = ChatCompletionRequest(
        model="openai/gpt-oss-120b",
        messages=[Message(role=Role.USER, content="Say hello in a friendly way")],
        audio=AudioConfig(voice="alloy", format="mp3"),
        modalities=["text", "audio"],
        max_tokens=50,
    )

    response = await service.create_chat_completion(request)

    print(f"\nText Response: {response.choices[0].message.content}")

    if response.choices[0].message.audio:
        audio = response.choices[0].message.audio
        print(f"\nAudio Output:")
        print(f"  ID: {audio.id}")
        print(f"  Transcript: {audio.transcript}")
        print(f"  Data length: {len(audio.data)} characters (base64)")
        print(f"  Expires at: {audio.expires_at} (Unix timestamp)")

        # Decode audio to check size
        audio_bytes = base64.b64decode(audio.data)
        print(f"  Audio size: {len(audio_bytes)} bytes")

    print(f"\nToken Usage:")
    print(f"  Completion tokens: {response.usage.completion_tokens}")
    if response.usage.completion_tokens_details:
        print(
            f"  Audio output tokens: {response.usage.completion_tokens_details.audio_tokens}"
        )


async def example_audio_voices():
    """Example: Different audio voices."""
    print("\n" + "=" * 60)
    print("Example 3: Different Audio Voices")
    print("=" * 60)

    config = AppConfig(response_delay=0.0)
    service = FakeAIService(config)

    voices = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]

    for voice in voices:
        request = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[Message(role=Role.USER, content="Hello")],
            audio=AudioConfig(voice=voice, format="mp3"),
            max_tokens=20,
        )

        response = await service.create_chat_completion(request)

        if response.choices[0].message.audio:
            audio_size = len(base64.b64decode(response.choices[0].message.audio.data))
            print(f"  Voice '{voice}': {audio_size} bytes")


async def example_audio_input_and_output():
    """Example: Combined audio input and output."""
    print("\n" + "=" * 60)
    print("Example 4: Audio Input + Audio Output")
    print("=" * 60)

    config = AppConfig(response_delay=0.0)
    service = FakeAIService(config)

    # Create audio input
    audio_bytes = generate_wav_audio(5.0)
    audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")

    # Request with both audio input and output
    request = ChatCompletionRequest(
        model="openai/gpt-oss-120b",
        messages=[
            Message(
                role=Role.USER,
                content=[
                    TextContent(type="text", text="Please respond to this audio:"),
                    InputAudioContent(
                        type="input_audio",
                        input_audio=InputAudio(data=audio_b64, format="wav"),
                    ),
                ],
            )
        ],
        audio=AudioConfig(voice="echo", format="mp3"),
        modalities=["text", "audio"],
        max_tokens=50,
    )

    response = await service.create_chat_completion(request)

    print(f"\nText Response: {response.choices[0].message.content}")

    print(f"\nToken Usage:")
    print(f"  Input audio tokens: {response.usage.prompt_tokens_details.audio_tokens}")
    print(f"  Prompt tokens: {response.usage.prompt_tokens}")
    if response.usage.completion_tokens_details:
        print(
            f"  Output audio tokens: {response.usage.completion_tokens_details.audio_tokens}"
        )
    print(f"  Completion tokens: {response.usage.completion_tokens}")
    print(f"  Total tokens: {response.usage.total_tokens}")


async def example_modalities_control():
    """Example: Controlling output modalities."""
    print("\n" + "=" * 60)
    print("Example 5: Modalities Control")
    print("=" * 60)

    config = AppConfig(response_delay=0.0)
    service = FakeAIService(config)

    # Test 1: Only text (even with audio config)
    print("\nTest 1: Text-only modality")
    request1 = ChatCompletionRequest(
        model="openai/gpt-oss-120b",
        messages=[Message(role=Role.USER, content="Hello")],
        audio=AudioConfig(voice="alloy", format="mp3"),
        modalities=["text"],  # Only text requested
        max_tokens=20,
    )
    response1 = await service.create_chat_completion(request1)
    print(f"  Has audio output: {response1.choices[0].message.audio is not None}")
    print(f"  Has text output: {response1.choices[0].message.content is not None}")

    # Test 2: Text and audio
    print("\nTest 2: Text and audio modalities")
    request2 = ChatCompletionRequest(
        model="openai/gpt-oss-120b",
        messages=[Message(role=Role.USER, content="Hello")],
        audio=AudioConfig(voice="alloy", format="mp3"),
        modalities=["text", "audio"],
        max_tokens=20,
    )
    response2 = await service.create_chat_completion(request2)
    print(f"  Has audio output: {response2.choices[0].message.audio is not None}")
    print(f"  Has text output: {response2.choices[0].message.content is not None}")


async def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("FakeAI Audio Input/Output Examples")
    print("=" * 60)

    await example_audio_input()
    await example_audio_output()
    await example_audio_voices()
    await example_audio_input_and_output()
    await example_modalities_control()

    print("\n" + "=" * 60)
    print("All examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
