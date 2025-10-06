"""
Tests for audio input/output functionality in chat completions.

Tests audio transcription, audio generation, token accounting,
and modalities parameter handling.
"""

#  SPDX-License-Identifier: Apache-2.0

import base64

import pytest

from fakeai import AppConfig
from fakeai.audio import (
    calculate_audio_input_tokens,
    estimate_audio_duration,
    estimate_audio_tokens,
    extract_audio_from_content,
    extract_text_from_audio,
    generate_audio_output,
    transcribe_audio_input,
)
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


class TestAudioUtilities:
    """Test audio utility functions."""

    def test_estimate_audio_tokens(self):
        """Test audio token estimation from duration."""
        # ~1.67 tokens per second
        assert estimate_audio_tokens(0.6) == 1
        assert estimate_audio_tokens(1.0) >= 1
        assert estimate_audio_tokens(10.0) >= 16
        assert estimate_audio_tokens(60.0) >= 100

    def test_estimate_audio_duration(self):
        """Test duration estimation from tokens."""
        # ~0.6 seconds per token
        assert estimate_audio_duration(1) >= 0.1
        assert estimate_audio_duration(10) >= 5.0
        assert estimate_audio_duration(100) >= 50.0

    def test_transcribe_audio_input_wav(self):
        """Test audio transcription for WAV format."""
        # Generate small WAV file (1 second)
        audio_bytes = generate_wav_audio(1.0)
        transcript = transcribe_audio_input(audio_bytes, "wav")

        assert isinstance(transcript, str)
        assert len(transcript) > 0
        assert "Hello" in transcript

    def test_transcribe_audio_input_mp3(self):
        """Test audio transcription for MP3 format."""
        # Simulate small MP3 file
        audio_bytes = b"\xff\xfb\x90\x00" * 100
        transcript = transcribe_audio_input(audio_bytes, "mp3")

        assert isinstance(transcript, str)
        assert len(transcript) > 0

    def test_extract_audio_from_content_dict(self):
        """Test extracting audio from dict-based content parts."""
        wav_audio = generate_wav_audio(2.0)
        audio_b64 = base64.b64encode(wav_audio).decode("utf-8")

        messages = [
            Message(
                role=Role.USER,
                content=[
                    {"type": "text", "text": "Please listen to this"},
                    {
                        "type": "input_audio",
                        "input_audio": {"data": audio_b64, "format": "wav"},
                    },
                ],
            )
        ]

        audio_inputs = extract_audio_from_content(messages)

        assert len(audio_inputs) == 1
        assert len(audio_inputs[0][0]) > 0  # audio_bytes
        assert audio_inputs[0][1] == "wav"  # format

    def test_extract_audio_from_content_pydantic(self):
        """Test extracting audio from Pydantic content parts."""
        wav_audio = generate_wav_audio(2.0)
        audio_b64 = base64.b64encode(wav_audio).decode("utf-8")

        messages = [
            Message(
                role=Role.USER,
                content=[
                    TextContent(type="text", text="Listen"),
                    InputAudioContent(
                        type="input_audio",
                        input_audio=InputAudio(data=audio_b64, format="wav"),
                    ),
                ],
            )
        ]

        audio_inputs = extract_audio_from_content(messages)

        assert len(audio_inputs) == 1
        assert len(audio_inputs[0][0]) > 0

    def test_generate_audio_output(self):
        """Test audio output generation."""
        text = "Hello, how are you?"
        audio_data = generate_audio_output(text, "alloy", "mp3")

        assert "id" in audio_data
        assert "data" in audio_data
        assert "transcript" in audio_data
        assert "expires_at" in audio_data
        assert audio_data["transcript"] == text
        assert audio_data["id"].startswith("audio-")

        # Verify base64 encoding
        audio_bytes = base64.b64decode(audio_data["data"])
        assert len(audio_bytes) > 0

    def test_calculate_audio_input_tokens(self):
        """Test calculating total audio input tokens."""
        wav_audio = generate_wav_audio(5.0)
        audio_b64 = base64.b64encode(wav_audio).decode("utf-8")

        messages = [
            Message(
                role=Role.USER,
                content=[
                    InputAudioContent(
                        type="input_audio",
                        input_audio=InputAudio(data=audio_b64, format="wav"),
                    )
                ],
            )
        ]

        tokens = calculate_audio_input_tokens(messages)
        assert tokens > 0
        assert tokens >= 8  # ~5 seconds * 1.67 tokens/sec

    def test_extract_text_from_audio(self):
        """Test extracting and transcribing text from audio."""
        wav_audio = generate_wav_audio(3.0)
        audio_b64 = base64.b64encode(wav_audio).decode("utf-8")

        messages = [
            Message(
                role=Role.USER,
                content=[
                    InputAudioContent(
                        type="input_audio",
                        input_audio=InputAudio(data=audio_b64, format="wav"),
                    )
                ],
            )
        ]

        text = extract_text_from_audio(messages)
        assert isinstance(text, str)
        assert len(text) > 0


class TestAudioInputProcessing:
    """Test audio input processing in chat completions."""

    @pytest.mark.asyncio
    async def test_chat_completion_with_audio_input(self):
        """Test chat completion with audio input in messages."""
        config = AppConfig(response_delay=0.0)
        service = FakeAIService(config)

        # Create audio input
        wav_audio = generate_wav_audio(2.0)
        audio_b64 = base64.b64encode(wav_audio).decode("utf-8")

        request = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[
                Message(
                    role=Role.USER,
                    content=[
                        TextContent(type="text", text="What did I say?"),
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

        # Check response
        assert response.id.startswith("chatcmpl-")
        assert len(response.choices) == 1
        assert response.choices[0].message.content

        # Check token accounting includes audio tokens
        assert response.usage.prompt_tokens_details.audio_tokens > 0
        assert response.usage.total_tokens > 0

    @pytest.mark.asyncio
    async def test_audio_input_token_accounting(self):
        """Test that audio input tokens are correctly tracked."""
        config = AppConfig(response_delay=0.0)
        service = FakeAIService(config)

        # Create 10 second audio
        wav_audio = generate_wav_audio(10.0)
        audio_b64 = base64.b64encode(wav_audio).decode("utf-8")

        request = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[
                Message(
                    role=Role.USER,
                    content=[
                        InputAudioContent(
                            type="input_audio",
                            input_audio=InputAudio(data=audio_b64, format="wav"),
                        )
                    ],
                )
            ],
            max_tokens=20,
        )

        response = await service.create_chat_completion(request)

        # Audio tokens should be ~16-17 for 10 seconds
        audio_tokens = response.usage.prompt_tokens_details.audio_tokens
        assert audio_tokens >= 15
        assert audio_tokens <= 20

    @pytest.mark.asyncio
    async def test_multiple_audio_inputs(self):
        """Test handling multiple audio inputs in one message."""
        config = AppConfig(response_delay=0.0)
        service = FakeAIService(config)

        # Create two audio inputs
        audio1 = generate_wav_audio(2.0)
        audio2 = generate_wav_audio(3.0)
        audio1_b64 = base64.b64encode(audio1).decode("utf-8")
        audio2_b64 = base64.b64encode(audio2).decode("utf-8")

        request = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[
                Message(
                    role=Role.USER,
                    content=[
                        InputAudioContent(
                            type="input_audio",
                            input_audio=InputAudio(data=audio1_b64, format="wav"),
                        ),
                        TextContent(type="text", text="And also this:"),
                        InputAudioContent(
                            type="input_audio",
                            input_audio=InputAudio(data=audio2_b64, format="wav"),
                        ),
                    ],
                )
            ],
            max_tokens=50,
        )

        response = await service.create_chat_completion(request)

        # Should have audio tokens from both inputs
        assert response.usage.prompt_tokens_details.audio_tokens > 0


class TestAudioOutputGeneration:
    """Test audio output generation in chat completions."""

    @pytest.mark.asyncio
    async def test_chat_completion_with_audio_output(self):
        """Test generating audio output in response."""
        config = AppConfig(response_delay=0.0)
        service = FakeAIService(config)

        request = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[Message(role=Role.USER, content="Say hello")],
            audio=AudioConfig(voice="alloy", format="mp3"),
            modalities=["text", "audio"],
            max_tokens=50,
        )

        response = await service.create_chat_completion(request)

        # Check response has audio
        assert response.choices[0].message.audio is not None
        audio = response.choices[0].message.audio

        assert audio.id.startswith("audio-")
        assert len(audio.data) > 0
        assert audio.transcript == response.choices[0].message.content
        assert audio.expires_at > 0

        # Verify base64 audio data
        audio_bytes = base64.b64decode(audio.data)
        assert len(audio_bytes) > 0

        # Check audio tokens in completion
        assert response.usage.completion_tokens_details is not None
        assert response.usage.completion_tokens_details.audio_tokens > 0

    @pytest.mark.asyncio
    async def test_audio_output_different_voices(self):
        """Test audio output with different voices."""
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

            assert response.choices[0].message.audio is not None
            assert len(response.choices[0].message.audio.data) > 0

    @pytest.mark.asyncio
    async def test_audio_output_different_formats(self):
        """Test audio output with different formats."""
        config = AppConfig(response_delay=0.0)
        service = FakeAIService(config)

        formats = ["mp3", "opus", "aac", "flac", "wav", "pcm16"]

        for audio_format in formats:
            request = ChatCompletionRequest(
                model="openai/gpt-oss-120b",
                messages=[Message(role=Role.USER, content="Test")],
                audio=AudioConfig(voice="alloy", format=audio_format),
                max_tokens=20,
            )

            response = await service.create_chat_completion(request)

            assert response.choices[0].message.audio is not None
            audio_data = base64.b64decode(response.choices[0].message.audio.data)
            assert len(audio_data) > 0

    @pytest.mark.asyncio
    async def test_audio_output_token_accounting(self):
        """Test audio output tokens are correctly calculated."""
        config = AppConfig(response_delay=0.0)
        service = FakeAIService(config)

        request = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[Message(role=Role.USER, content="Generate a long response")],
            audio=AudioConfig(voice="alloy", format="mp3"),
            max_tokens=100,
        )

        response = await service.create_chat_completion(request)

        # Audio tokens should be proportional to text length
        assert response.usage.completion_tokens_details.audio_tokens > 0

        # Total completion tokens should include audio
        total_completion = response.usage.completion_tokens
        text_tokens = len(response.choices[0].message.content.split())
        audio_tokens = response.usage.completion_tokens_details.audio_tokens

        assert total_completion >= text_tokens


class TestModalitiesParameter:
    """Test modalities parameter handling."""

    @pytest.mark.asyncio
    async def test_text_only_modality(self):
        """Test requesting only text modality."""
        config = AppConfig(response_delay=0.0)
        service = FakeAIService(config)

        request = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[Message(role=Role.USER, content="Hello")],
            audio=AudioConfig(voice="alloy", format="mp3"),
            modalities=["text"],  # Only text requested
            max_tokens=20,
        )

        response = await service.create_chat_completion(request)

        # Should not have audio output
        assert response.choices[0].message.audio is None
        assert (
            response.usage.completion_tokens_details is None
            or response.usage.completion_tokens_details.audio_tokens == 0
        )

    @pytest.mark.asyncio
    async def test_text_and_audio_modalities(self):
        """Test requesting both text and audio modalities."""
        config = AppConfig(response_delay=0.0)
        service = FakeAIService(config)

        request = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[Message(role=Role.USER, content="Hello")],
            audio=AudioConfig(voice="alloy", format="mp3"),
            modalities=["text", "audio"],
            max_tokens=20,
        )

        response = await service.create_chat_completion(request)

        # Should have both text and audio
        assert response.choices[0].message.content is not None
        assert response.choices[0].message.audio is not None

    @pytest.mark.asyncio
    async def test_no_audio_config_no_audio_output(self):
        """Test that no audio is generated without audio config."""
        config = AppConfig(response_delay=0.0)
        service = FakeAIService(config)

        request = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[Message(role=Role.USER, content="Hello")],
            # No audio config provided
            modalities=["text", "audio"],
            max_tokens=20,
        )

        response = await service.create_chat_completion(request)

        # Should not have audio without config
        assert response.choices[0].message.audio is None


class TestAudioInputAndOutput:
    """Test combined audio input and output."""

    @pytest.mark.asyncio
    async def test_audio_input_with_audio_output(self):
        """Test processing audio input and generating audio output."""
        config = AppConfig(response_delay=0.0)
        service = FakeAIService(config)

        # Create audio input
        wav_audio = generate_wav_audio(3.0)
        audio_b64 = base64.b64encode(wav_audio).decode("utf-8")

        request = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[
                Message(
                    role=Role.USER,
                    content=[
                        InputAudioContent(
                            type="input_audio",
                            input_audio=InputAudio(data=audio_b64, format="wav"),
                        )
                    ],
                )
            ],
            audio=AudioConfig(voice="echo", format="mp3"),
            modalities=["text", "audio"],
            max_tokens=50,
        )

        response = await service.create_chat_completion(request)

        # Should have both input and output audio tokens
        assert response.usage.prompt_tokens_details.audio_tokens > 0
        assert response.usage.completion_tokens_details.audio_tokens > 0

        # Should have audio output
        assert response.choices[0].message.audio is not None

    @pytest.mark.asyncio
    async def test_full_audio_conversation(self):
        """Test a full audio conversation flow."""
        config = AppConfig(response_delay=0.0)
        service = FakeAIService(config)

        # Turn 1: User sends audio
        audio_input = generate_wav_audio(2.0)
        audio_b64 = base64.b64encode(audio_input).decode("utf-8")

        request1 = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[
                Message(
                    role=Role.USER,
                    content=[
                        TextContent(type="text", text="Listen to this:"),
                        InputAudioContent(
                            type="input_audio",
                            input_audio=InputAudio(data=audio_b64, format="wav"),
                        ),
                    ],
                )
            ],
            audio=AudioConfig(voice="alloy", format="mp3"),
            modalities=["text", "audio"],
            max_tokens=50,
        )

        response1 = await service.create_chat_completion(request1)

        # Verify first response
        assert response1.usage.prompt_tokens_details.audio_tokens > 0
        assert response1.choices[0].message.audio is not None

        # Turn 2: Continue conversation
        request2 = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[
                Message(
                    role=Role.USER,
                    content=[
                        TextContent(type="text", text="Listen to this:"),
                        InputAudioContent(
                            type="input_audio",
                            input_audio=InputAudio(data=audio_b64, format="wav"),
                        ),
                    ],
                ),
                response1.choices[0].message,
                Message(role=Role.USER, content="Can you repeat that?"),
            ],
            audio=AudioConfig(voice="alloy", format="mp3"),
            max_tokens=50,
        )

        response2 = await service.create_chat_completion(request2)

        # Verify second response
        assert response2.choices[0].message.content is not None
        assert response2.choices[0].message.audio is not None
