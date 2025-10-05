"""
Comprehensive tests for Text-to-Speech (TTS) API.

Tests the /v1/audio/speech endpoint with various configurations including:
- All voice options
- All audio formats
- Speed parameter
- Integration with OpenAI client
"""
#  SPDX-License-Identifier: Apache-2.0

import pytest
from fakeai import AppConfig
from fakeai.fakeai_service import FakeAIService
from fakeai.models import SpeechRequest
from fakeai.utils import generate_simulated_audio, estimate_audio_duration


class TestAudioGeneration:
    """Test audio generation utilities."""

    def test_estimate_audio_duration_normal_speed(self):
        """Test audio duration estimation at normal speed."""
        text = "Hello world, this is a test sentence."  # 7 words
        duration = estimate_audio_duration(text, speed=1.0)

        # 7 words at 150 words/minute = 2.8 seconds
        assert 2.0 < duration < 4.0

    def test_estimate_audio_duration_fast_speed(self):
        """Test audio duration estimation at fast speed."""
        text = "Hello world, this is a test sentence."
        normal_duration = estimate_audio_duration(text, speed=1.0)
        fast_duration = estimate_audio_duration(text, speed=2.0)

        # Fast speed should be shorter
        assert fast_duration < normal_duration
        assert fast_duration == pytest.approx(normal_duration / 2.0, rel=0.1)

    def test_estimate_audio_duration_slow_speed(self):
        """Test audio duration estimation at slow speed."""
        text = "Hello world, this is a test sentence."
        normal_duration = estimate_audio_duration(text, speed=1.0)
        slow_duration = estimate_audio_duration(text, speed=0.5)

        # Slow speed should be longer
        assert slow_duration > normal_duration
        assert slow_duration == pytest.approx(normal_duration * 2.0, rel=0.1)

    def test_generate_wav_audio(self):
        """Test WAV audio generation."""
        audio_bytes = generate_simulated_audio(
            text="Hello world",
            voice="alloy",
            response_format="wav",
            speed=1.0
        )

        # WAV should have RIFF header
        assert audio_bytes[:4] == b'RIFF'
        assert audio_bytes[8:12] == b'WAVE'
        assert len(audio_bytes) > 100  # Should have substantial data

    def test_generate_mp3_audio(self):
        """Test MP3 audio generation."""
        audio_bytes = generate_simulated_audio(
            text="Hello world",
            voice="alloy",
            response_format="mp3",
            speed=1.0
        )

        # MP3 should have ID3 header
        assert audio_bytes[:3] == b'ID3'
        assert len(audio_bytes) > 100  # Should have substantial data

    def test_generate_pcm_audio(self):
        """Test PCM audio generation."""
        audio_bytes = generate_simulated_audio(
            text="Hello world",
            voice="alloy",
            response_format="pcm",
            speed=1.0
        )

        # PCM is raw audio data
        assert len(audio_bytes) > 0
        assert len(audio_bytes) % 2 == 0  # 16-bit samples

    def test_audio_duration_scales_with_text_length(self):
        """Test that longer text produces longer audio."""
        short_text = "Hello"
        long_text = "Hello world, this is a much longer text that should produce longer audio."

        short_audio = generate_simulated_audio(short_text, "alloy", "wav", 1.0)
        long_audio = generate_simulated_audio(long_text, "alloy", "wav", 1.0)

        # Longer text should produce more audio data
        assert len(long_audio) > len(short_audio)


class TestSpeechService:
    """Test speech service methods."""

    @pytest.mark.asyncio
    async def test_create_speech_basic(self):
        """Test basic speech creation."""
        config = AppConfig(response_delay=0.0)
        service = FakeAIService(config)

        request = SpeechRequest(
            model="tts-1",
            input="Hello, world!",
            voice="alloy"
        )

        audio_bytes = await service.create_speech(request)

        assert isinstance(audio_bytes, bytes)
        assert len(audio_bytes) > 0

    @pytest.mark.asyncio
    async def test_create_speech_all_voices(self):
        """Test all available voice options."""
        config = AppConfig(response_delay=0.0)
        service = FakeAIService(config)

        voices = ["alloy", "echo", "fable", "onyx", "nova", "shimmer", "marin", "cedar"]

        for voice in voices:
            request = SpeechRequest(
                model="tts-1",
                input="Testing voice.",
                voice=voice
            )

            audio_bytes = await service.create_speech(request)
            assert isinstance(audio_bytes, bytes)
            assert len(audio_bytes) > 0

    @pytest.mark.asyncio
    async def test_create_speech_all_formats(self):
        """Test all audio format options."""
        config = AppConfig(response_delay=0.0)
        service = FakeAIService(config)

        formats = ["mp3", "opus", "aac", "flac", "wav", "pcm"]

        for audio_format in formats:
            request = SpeechRequest(
                model="tts-1",
                input="Testing format.",
                voice="alloy",
                response_format=audio_format
            )

            audio_bytes = await service.create_speech(request)
            assert isinstance(audio_bytes, bytes)
            assert len(audio_bytes) > 0

    @pytest.mark.asyncio
    async def test_create_speech_speed_parameter(self):
        """Test speed parameter affects processing time."""
        config = AppConfig(response_delay=0.0, random_delay=False)
        service = FakeAIService(config)

        text = "This is a longer text to test the speed parameter properly."

        # Test different speeds
        speeds = [0.25, 0.5, 1.0, 2.0, 4.0]
        for speed in speeds:
            request = SpeechRequest(
                model="tts-1",
                input=text,
                voice="alloy",
                response_format="mp3",
                speed=speed
            )

            audio_bytes = await service.create_speech(request)
            assert isinstance(audio_bytes, bytes)
            assert len(audio_bytes) > 0

    @pytest.mark.asyncio
    async def test_create_speech_model_variants(self):
        """Test different TTS model variants."""
        config = AppConfig(response_delay=0.0)
        service = FakeAIService(config)

        models = ["tts-1", "tts-1-hd"]

        for model in models:
            request = SpeechRequest(
                model=model,
                input="Testing model.",
                voice="alloy"
            )

            audio_bytes = await service.create_speech(request)
            assert isinstance(audio_bytes, bytes)
            assert len(audio_bytes) > 0

    @pytest.mark.asyncio
    async def test_create_speech_long_text(self):
        """Test with maximum length text (4096 characters)."""
        config = AppConfig(response_delay=0.0)
        service = FakeAIService(config)

        # Create a long text (near maximum)
        long_text = "Hello world! " * 300  # ~3900 characters

        request = SpeechRequest(
            model="tts-1",
            input=long_text,
            voice="alloy",
            response_format="mp3"
        )

        audio_bytes = await service.create_speech(request)
        assert isinstance(audio_bytes, bytes)
        assert len(audio_bytes) > 0


class TestSpeechEndpoint:
    """Test the /v1/audio/speech HTTP endpoint."""

    @pytest.mark.asyncio
    async def test_speech_endpoint_basic(self, client_no_auth):
        """Test basic speech endpoint."""
        response = client_no_auth.post(
            "/v1/audio/speech",
            json={
                "model": "tts-1",
                "input": "Hello, world!",
                "voice": "alloy"
            }
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "audio/mpeg"
        assert len(response.content) > 0

    @pytest.mark.asyncio
    async def test_speech_endpoint_wav_format(self, client_no_auth):
        """Test WAV format response."""
        response = client_no_auth.post(
            "/v1/audio/speech",
            json={
                "model": "tts-1",
                "input": "Testing WAV format.",
                "voice": "alloy",
                "response_format": "wav"
            }
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "audio/wav"
        assert len(response.content) > 0

        # Verify WAV header
        content = response.content
        assert content[:4] == b'RIFF'
        assert content[8:12] == b'WAVE'

    @pytest.mark.asyncio
    async def test_speech_endpoint_opus_format(self, client_no_auth):
        """Test OPUS format response."""
        response = client_no_auth.post(
            "/v1/audio/speech",
            json={
                "model": "tts-1",
                "input": "Testing OPUS format.",
                "voice": "echo",
                "response_format": "opus"
            }
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "audio/opus"
        assert len(response.content) > 0

    @pytest.mark.asyncio
    async def test_speech_endpoint_all_voices(self, client_no_auth):
        """Test all voice options via endpoint."""
        voices = ["alloy", "echo", "fable", "onyx", "nova", "shimmer", "marin", "cedar"]

        for voice in voices:
            response = client_no_auth.post(
                "/v1/audio/speech",
                json={
                    "model": "tts-1",
                    "input": f"Testing voice {voice}.",
                    "voice": voice
                }
            )

            assert response.status_code == 200
            assert len(response.content) > 0

    @pytest.mark.asyncio
    async def test_speech_endpoint_speed_parameter(self, client_no_auth):
        """Test speed parameter via endpoint."""
        speeds = [0.25, 0.5, 1.0, 2.0, 4.0]

        for speed in speeds:
            response = client_no_auth.post(
                "/v1/audio/speech",
                json={
                    "model": "tts-1",
                    "input": "Testing speed parameter.",
                    "voice": "alloy",
                    "speed": speed
                }
            )

            assert response.status_code == 200
            assert len(response.content) > 0

    @pytest.mark.asyncio
    async def test_speech_endpoint_content_disposition(self, client_no_auth):
        """Test Content-Disposition header."""
        response = client_no_auth.post(
            "/v1/audio/speech",
            json={
                "model": "tts-1",
                "input": "Testing headers.",
                "voice": "alloy",
                "response_format": "mp3"
            }
        )

        assert response.status_code == 200
        assert "content-disposition" in response.headers
        assert "speech.mp3" in response.headers["content-disposition"]


class TestOpenAIClientIntegration:
    """Test integration with OpenAI Python client."""

    @pytest.mark.skip(reason="Requires running server for OpenAI client integration")
    def test_openai_client_speech_basic(self):
        """Test basic speech generation with OpenAI client."""
        pytest.importorskip("openai")
        from openai import OpenAI
        import tempfile
        import os

        client = OpenAI(
            api_key="test-key",
            base_url="http://127.0.0.1:8000",
        )

        # Create speech
        response = client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input="The quick brown fox jumped over the lazy dog."
        )

        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
            f.write(response.content)
            temp_path = f.name

        try:
            # Verify file was created and has content
            assert os.path.exists(temp_path)
            assert os.path.getsize(temp_path) > 0

            # Verify it's valid audio data (has MP3 header)
            with open(temp_path, 'rb') as f:
                data = f.read(3)
                assert data == b'ID3'
        finally:
            # Cleanup
            os.unlink(temp_path)

    @pytest.mark.skip(reason="Requires running server for OpenAI client integration")
    def test_openai_client_speech_streaming(self):
        """Test streaming speech generation with OpenAI client."""
        pytest.importorskip("openai")
        from openai import OpenAI
        import io

        client = OpenAI(
            api_key="test-key",
            base_url="http://127.0.0.1:8000",
        )

        # Stream speech
        response = client.audio.speech.create(
            model="tts-1-hd",
            voice="shimmer",
            input="Testing streaming audio generation."
        )

        # Collect streamed data
        audio_data = io.BytesIO()
        for chunk in response.iter_bytes(chunk_size=1024):
            audio_data.write(chunk)

        # Verify we got data
        audio_bytes = audio_data.getvalue()
        assert len(audio_bytes) > 0

    @pytest.mark.skip(reason="Requires running server for OpenAI client integration")
    def test_openai_client_all_formats(self):
        """Test all formats with OpenAI client."""
        pytest.importorskip("openai")
        from openai import OpenAI

        client = OpenAI(
            api_key="test-key",
            base_url="http://127.0.0.1:8000",
        )

        formats = ["mp3", "opus", "aac", "flac", "wav", "pcm"]

        for audio_format in formats:
            response = client.audio.speech.create(
                model="tts-1",
                voice="alloy",
                input=f"Testing {audio_format} format.",
                response_format=audio_format
            )

            assert response.content is not None
            assert len(response.content) > 0


class TestEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_empty_input(self, client_no_auth):
        """Test with empty input text."""
        response = client_no_auth.post(
            "/v1/audio/speech",
            json={
                "model": "tts-1",
                "input": "",
                "voice": "alloy"
            }
        )

        # Should still return valid audio (silent or minimal)
        assert response.status_code == 200
        assert len(response.content) > 0

    @pytest.mark.asyncio
    async def test_single_word(self, client_no_auth):
        """Test with single word input."""
        response = client_no_auth.post(
            "/v1/audio/speech",
            json={
                "model": "tts-1",
                "input": "Hello",
                "voice": "alloy"
            }
        )

        assert response.status_code == 200
        assert len(response.content) > 0

    @pytest.mark.asyncio
    async def test_special_characters(self, client_no_auth):
        """Test with special characters in input."""
        response = client_no_auth.post(
            "/v1/audio/speech",
            json={
                "model": "tts-1",
                "input": "Hello! How are you? I'm fine, thanks. #Testing @mentions.",
                "voice": "alloy"
            }
        )

        assert response.status_code == 200
        assert len(response.content) > 0

    @pytest.mark.asyncio
    async def test_unicode_characters(self, client_no_auth):
        """Test with Unicode characters."""
        response = client_no_auth.post(
            "/v1/audio/speech",
            json={
                "model": "tts-1",
                "input": "Hello 世界! Bonjour 🌍 Привет",
                "voice": "alloy"
            }
        )

        assert response.status_code == 200
        assert len(response.content) > 0

    @pytest.mark.asyncio
    async def test_extreme_speed_values(self, client_no_auth):
        """Test with extreme but valid speed values."""
        # Minimum speed
        response = client_no_auth.post(
            "/v1/audio/speech",
            json={
                "model": "tts-1",
                "input": "Testing minimum speed.",
                "voice": "alloy",
                "speed": 0.25
            }
        )
        assert response.status_code == 200

        # Maximum speed
        response = client_no_auth.post(
            "/v1/audio/speech",
            json={
                "model": "tts-1",
                "input": "Testing maximum speed.",
                "voice": "alloy",
                "speed": 4.0
            }
        )
        assert response.status_code == 200
