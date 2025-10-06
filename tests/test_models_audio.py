"""
Tests for audio models module.

This test suite verifies the audio models for TTS and Whisper API endpoints:
- Text-to-Speech (SpeechRequest)
- Audio Transcription (TranscriptionRequest, TranscriptionResponse)
- Audio Translation (AudioTranslationRequest)
- Word and segment level timing models
- Audio usage/billing models
"""

#  SPDX-License-Identifier: Apache-2.0

import pytest
from pydantic import ValidationError


class TestImportsFromModelsPackage:
    """Test that all audio models can be imported from the models package."""

    def test_import_audio_models_from_package(self):
        """Test importing audio models from fakeai.models package."""
        from fakeai.models import (
            AudioSpeechesUsageResponse,
            AudioTranscriptionsUsageResponse,
            AudioTranslationRequest,
            SpeechRequest,
            TranscriptionRequest,
            TranscriptionResponse,
            TranscriptionSegment,
            TranscriptionWord,
            VerboseTranscriptionResponse,
        )

        # Verify classes are imported correctly
        assert SpeechRequest is not None
        assert TranscriptionRequest is not None
        assert TranscriptionResponse is not None
        assert VerboseTranscriptionResponse is not None
        assert TranscriptionWord is not None
        assert TranscriptionSegment is not None
        assert AudioTranslationRequest is not None
        assert AudioSpeechesUsageResponse is not None
        assert AudioTranscriptionsUsageResponse is not None


class TestImportsFromAudioModule:
    """Test that audio models can be imported from the audio module."""

    def test_import_from_audio_module(self):
        """Test importing from fakeai.models.audio module."""
        from fakeai.models.audio import (
            AudioSpeechesUsageResponse,
            AudioTranscriptionsUsageResponse,
            AudioTranslationRequest,
            SpeechRequest,
            TranscriptionRequest,
            TranscriptionResponse,
            TranscriptionSegment,
            TranscriptionWord,
            VerboseTranscriptionResponse,
        )

        # Verify classes are imported correctly
        assert SpeechRequest is not None
        assert TranscriptionRequest is not None
        assert TranscriptionResponse is not None
        assert VerboseTranscriptionResponse is not None
        assert TranscriptionWord is not None
        assert TranscriptionSegment is not None
        assert AudioTranslationRequest is not None
        assert AudioSpeechesUsageResponse is not None
        assert AudioTranscriptionsUsageResponse is not None


class TestBackwardCompatibility:
    """Test that imports from different paths reference the same classes."""

    def test_speech_request_references_same_class(self):
        """Test that SpeechRequest imported from different paths is the same class."""
        from fakeai.models import SpeechRequest as SpeechRequestFromPackage
        from fakeai.models.audio import SpeechRequest as SpeechRequestFromAudio

        # Verify they reference the same class
        assert SpeechRequestFromPackage is SpeechRequestFromAudio

    def test_transcription_models_reference_same_class(self):
        """Test that transcription models reference the same classes."""
        from fakeai.models import (
            TranscriptionRequest as TranscriptionRequestFromPackage,
        )
        from fakeai.models import (
            TranscriptionResponse as TranscriptionResponseFromPackage,
        )
        from fakeai.models import (
            TranscriptionSegment as TranscriptionSegmentFromPackage,
        )
        from fakeai.models import TranscriptionWord as TranscriptionWordFromPackage
        from fakeai.models.audio import (
            TranscriptionRequest as TranscriptionRequestFromAudio,
        )
        from fakeai.models.audio import (
            TranscriptionResponse as TranscriptionResponseFromAudio,
        )
        from fakeai.models.audio import (
            TranscriptionSegment as TranscriptionSegmentFromAudio,
        )
        from fakeai.models.audio import TranscriptionWord as TranscriptionWordFromAudio

        # Verify all classes reference the same objects
        assert TranscriptionRequestFromPackage is TranscriptionRequestFromAudio
        assert TranscriptionResponseFromPackage is TranscriptionResponseFromAudio
        assert TranscriptionSegmentFromPackage is TranscriptionSegmentFromAudio
        assert TranscriptionWordFromPackage is TranscriptionWordFromAudio

    def test_usage_models_reference_same_class(self):
        """Test that usage models reference the same classes."""
        from fakeai.models import AudioSpeechesUsageResponse as AudioSpeechesFromPackage
        from fakeai.models import (
            AudioTranscriptionsUsageResponse as AudioTranscriptionsFromPackage,
        )
        from fakeai.models.audio import (
            AudioSpeechesUsageResponse as AudioSpeechesFromAudio,
        )
        from fakeai.models.audio import (
            AudioTranscriptionsUsageResponse as AudioTranscriptionsFromAudio,
        )

        # Verify they reference the same classes
        assert AudioSpeechesFromPackage is AudioSpeechesFromAudio
        assert AudioTranscriptionsFromPackage is AudioTranscriptionsFromAudio


class TestSpeechRequestModel:
    """Test SpeechRequest model (TTS)."""

    def test_speech_request_instantiation(self):
        """Test basic SpeechRequest instantiation."""
        from fakeai.models import SpeechRequest

        request = SpeechRequest(model="tts-1", input="Hello, world!", voice="alloy")

        assert request.model == "tts-1"
        assert request.input == "Hello, world!"
        assert request.voice == "alloy"
        assert request.response_format == "mp3"  # default
        assert request.speed == 1.0  # default

    def test_speech_request_all_voices(self):
        """Test all supported voices."""
        from fakeai.models import SpeechRequest

        voices = ["alloy", "echo", "fable", "onyx", "nova", "shimmer", "marin", "cedar"]

        for voice in voices:
            request = SpeechRequest(model="tts-1", input="Test", voice=voice)
            assert request.voice == voice

    def test_speech_request_invalid_voice(self):
        """Test that invalid voice raises ValidationError."""
        from fakeai.models import SpeechRequest

        with pytest.raises(ValidationError):
            SpeechRequest(model="tts-1", input="Test", voice="invalid_voice")

    def test_speech_request_all_formats(self):
        """Test all supported response formats."""
        from fakeai.models import SpeechRequest

        formats = ["mp3", "opus", "aac", "flac", "wav", "pcm"]

        for fmt in formats:
            request = SpeechRequest(
                model="tts-1", input="Test", voice="alloy", response_format=fmt
            )
            assert request.response_format == fmt

    def test_speech_request_invalid_format(self):
        """Test that invalid format raises ValidationError."""
        from fakeai.models import SpeechRequest

        with pytest.raises(ValidationError):
            SpeechRequest(
                model="tts-1", input="Test", voice="alloy", response_format="ogg"
            )

    def test_speech_request_speed_validation(self):
        """Test speed parameter validation."""
        from fakeai.models import SpeechRequest

        # Valid speeds
        for speed in [0.25, 0.5, 1.0, 2.0, 4.0]:
            request = SpeechRequest(
                model="tts-1", input="Test", voice="alloy", speed=speed
            )
            assert request.speed == speed

        # Invalid speeds (too low)
        with pytest.raises(ValidationError):
            SpeechRequest(model="tts-1", input="Test", voice="alloy", speed=0.24)

        # Invalid speeds (too high)
        with pytest.raises(ValidationError):
            SpeechRequest(model="tts-1", input="Test", voice="alloy", speed=4.1)

    def test_speech_request_hd_model(self):
        """Test TTS with HD model."""
        from fakeai.models import SpeechRequest

        request = SpeechRequest(
            model="tts-1-hd",
            input="High definition audio",
            voice="nova",
            response_format="flac",
        )

        assert request.model == "tts-1-hd"
        assert request.voice == "nova"
        assert request.response_format == "flac"


class TestTranscriptionRequestModel:
    """Test TranscriptionRequest model (Whisper)."""

    def test_transcription_request_instantiation(self):
        """Test basic TranscriptionRequest instantiation."""
        from fakeai.models import TranscriptionRequest

        request = TranscriptionRequest(model="whisper-1")

        assert request.model == "whisper-1"
        assert request.language is None
        assert request.prompt is None
        assert request.response_format == "json"  # default
        assert request.temperature == 0.0  # default
        assert request.timestamp_granularities is None

    def test_transcription_request_with_language(self):
        """Test TranscriptionRequest with language specification."""
        from fakeai.models import TranscriptionRequest

        request = TranscriptionRequest(model="whisper-1", language="en")

        assert request.language == "en"

    def test_transcription_request_with_prompt(self):
        """Test TranscriptionRequest with prompt for style guidance."""
        from fakeai.models import TranscriptionRequest

        request = TranscriptionRequest(
            model="whisper-1", prompt="This is a technical discussion about AI."
        )

        assert request.prompt == "This is a technical discussion about AI."

    def test_transcription_request_all_formats(self):
        """Test all supported transcription response formats."""
        from fakeai.models import TranscriptionRequest

        formats = ["json", "text", "srt", "verbose_json", "vtt"]

        for fmt in formats:
            request = TranscriptionRequest(model="whisper-1", response_format=fmt)
            assert request.response_format == fmt

    def test_transcription_request_invalid_format(self):
        """Test that invalid format raises ValidationError."""
        from fakeai.models import TranscriptionRequest

        with pytest.raises(ValidationError):
            TranscriptionRequest(model="whisper-1", response_format="xml")

    def test_transcription_request_temperature_validation(self):
        """Test temperature parameter validation."""
        from fakeai.models import TranscriptionRequest

        # Valid temperatures
        for temp in [0.0, 0.5, 1.0]:
            request = TranscriptionRequest(model="whisper-1", temperature=temp)
            assert request.temperature == temp

        # Invalid temperature (too low)
        with pytest.raises(ValidationError):
            TranscriptionRequest(model="whisper-1", temperature=-0.1)

        # Invalid temperature (too high)
        with pytest.raises(ValidationError):
            TranscriptionRequest(model="whisper-1", temperature=1.1)

    def test_transcription_request_timestamp_granularities(self):
        """Test timestamp granularities parameter."""
        from fakeai.models import TranscriptionRequest

        # Single granularity
        request = TranscriptionRequest(
            model="whisper-1", timestamp_granularities=["word"]
        )
        assert request.timestamp_granularities == ["word"]

        # Multiple granularities
        request = TranscriptionRequest(
            model="whisper-1", timestamp_granularities=["word", "segment"]
        )
        assert request.timestamp_granularities == ["word", "segment"]

    def test_transcription_request_invalid_granularity(self):
        """Test that invalid granularity raises ValidationError."""
        from fakeai.models import TranscriptionRequest

        with pytest.raises(ValidationError):
            TranscriptionRequest(
                model="whisper-1", timestamp_granularities=["character"]
            )


class TestTranscriptionResponseModels:
    """Test TranscriptionResponse and VerboseTranscriptionResponse models."""

    def test_transcription_response_instantiation(self):
        """Test TranscriptionResponse instantiation."""
        from fakeai.models import TranscriptionResponse

        response = TranscriptionResponse(text="Hello, world!")

        assert response.text == "Hello, world!"

    def test_verbose_transcription_response_instantiation(self):
        """Test VerboseTranscriptionResponse instantiation."""
        from fakeai.models import VerboseTranscriptionResponse

        response = VerboseTranscriptionResponse(
            task="transcribe", language="en", duration=5.2, text="Hello, world!"
        )

        assert response.task == "transcribe"
        assert response.language == "en"
        assert response.duration == 5.2
        assert response.text == "Hello, world!"
        assert response.words is None
        assert response.segments is None

    def test_verbose_transcription_response_with_words(self):
        """Test VerboseTranscriptionResponse with word-level timestamps."""
        from fakeai.models import TranscriptionWord, VerboseTranscriptionResponse

        words = [
            TranscriptionWord(word="Hello", start=0.0, end=0.5),
            TranscriptionWord(word="world", start=0.6, end=1.0),
        ]

        response = VerboseTranscriptionResponse(
            task="transcribe",
            language="en",
            duration=1.0,
            text="Hello world",
            words=words,
        )

        assert len(response.words) == 2
        assert response.words[0].word == "Hello"
        assert response.words[0].start == 0.0
        assert response.words[0].end == 0.5

    def test_verbose_transcription_response_with_segments(self):
        """Test VerboseTranscriptionResponse with segment-level data."""
        from fakeai.models import TranscriptionSegment, VerboseTranscriptionResponse

        segments = [
            TranscriptionSegment(
                id=0,
                seek=0,
                start=0.0,
                end=2.0,
                text="First segment",
                tokens=[1, 2, 3],
                temperature=0.0,
                avg_logprob=-0.5,
                compression_ratio=1.2,
                no_speech_prob=0.01,
            )
        ]

        response = VerboseTranscriptionResponse(
            task="transcribe",
            language="en",
            duration=2.0,
            text="First segment",
            segments=segments,
        )

        assert len(response.segments) == 1
        assert response.segments[0].text == "First segment"
        assert response.segments[0].start == 0.0
        assert response.segments[0].end == 2.0


class TestTranscriptionWordModel:
    """Test TranscriptionWord model."""

    def test_transcription_word_instantiation(self):
        """Test TranscriptionWord instantiation."""
        from fakeai.models import TranscriptionWord

        word = TranscriptionWord(word="test", start=1.5, end=2.0)

        assert word.word == "test"
        assert word.start == 1.5
        assert word.end == 2.0


class TestTranscriptionSegmentModel:
    """Test TranscriptionSegment model."""

    def test_transcription_segment_instantiation(self):
        """Test TranscriptionSegment instantiation."""
        from fakeai.models import TranscriptionSegment

        segment = TranscriptionSegment(
            id=0,
            seek=0,
            start=0.0,
            end=5.0,
            text="This is a test segment",
            tokens=[10, 20, 30, 40],
            temperature=0.2,
            avg_logprob=-0.3,
            compression_ratio=1.5,
            no_speech_prob=0.05,
        )

        assert segment.id == 0
        assert segment.seek == 0
        assert segment.start == 0.0
        assert segment.end == 5.0
        assert segment.text == "This is a test segment"
        assert segment.tokens == [10, 20, 30, 40]
        assert segment.temperature == 0.2
        assert segment.avg_logprob == -0.3
        assert segment.compression_ratio == 1.5
        assert segment.no_speech_prob == 0.05


class TestAudioTranslationRequestModel:
    """Test AudioTranslationRequest model."""

    def test_audio_translation_request_instantiation(self):
        """Test basic AudioTranslationRequest instantiation."""
        from fakeai.models import AudioTranslationRequest

        request = AudioTranslationRequest(model="whisper-1")

        assert request.model == "whisper-1"
        assert request.prompt is None
        assert request.response_format == "json"  # default
        assert request.temperature == 0.0  # default

    def test_audio_translation_request_with_options(self):
        """Test AudioTranslationRequest with all options."""
        from fakeai.models import AudioTranslationRequest

        request = AudioTranslationRequest(
            model="whisper-1",
            prompt="Translate this to English",
            response_format="text",
            temperature=0.5,
        )

        assert request.model == "whisper-1"
        assert request.prompt == "Translate this to English"
        assert request.response_format == "text"
        assert request.temperature == 0.5

    def test_audio_translation_request_all_formats(self):
        """Test all supported translation response formats."""
        from fakeai.models import AudioTranslationRequest

        formats = ["json", "text", "srt", "verbose_json", "vtt"]

        for fmt in formats:
            request = AudioTranslationRequest(model="whisper-1", response_format=fmt)
            assert request.response_format == fmt


class TestAudioUsageModels:
    """Test audio usage/billing models."""

    def test_audio_speeches_usage_response_instantiation(self):
        """Test AudioSpeechesUsageResponse instantiation."""
        from fakeai.models import AudioSpeechesUsageResponse

        response = AudioSpeechesUsageResponse(
            object="page", data=[], has_more=False, next_page=None
        )

        assert response.object == "page"
        assert response.data == []
        assert response.has_more is False
        assert response.next_page is None

    def test_audio_transcriptions_usage_response_instantiation(self):
        """Test AudioTranscriptionsUsageResponse instantiation."""
        from fakeai.models import AudioTranscriptionsUsageResponse

        response = AudioTranscriptionsUsageResponse(
            object="page", data=[], has_more=False, next_page=None
        )

        assert response.object == "page"
        assert response.data == []
        assert response.has_more is False
        assert response.next_page is None

    def test_audio_usage_with_pagination(self):
        """Test audio usage models with pagination."""
        from fakeai.models import AudioSpeechesUsageResponse

        response = AudioSpeechesUsageResponse(
            object="page",
            data=[],
            has_more=True,
            next_page="https://api.openai.com/v1/usage/audio_speeches?page=2",
        )

        assert response.has_more is True
        assert response.next_page is not None
        assert "page=2" in response.next_page


class TestAudioModelsIntegration:
    """Test integration scenarios for audio models."""

    def test_tts_workflow(self):
        """Test complete TTS workflow with SpeechRequest."""
        from fakeai.models import SpeechRequest

        # Create a realistic TTS request
        request = SpeechRequest(
            model="tts-1-hd",
            input="The quick brown fox jumps over the lazy dog.",
            voice="nova",
            response_format="opus",
            speed=1.2,
        )

        # Verify all fields
        assert request.model == "tts-1-hd"
        assert "fox" in request.input
        assert request.voice == "nova"
        assert request.response_format == "opus"
        assert request.speed == 1.2

    def test_transcription_workflow(self):
        """Test complete transcription workflow."""
        from fakeai.models import (
            TranscriptionRequest,
            TranscriptionSegment,
            TranscriptionWord,
            VerboseTranscriptionResponse,
        )

        # Create transcription request
        request = TranscriptionRequest(
            model="whisper-1",
            language="en",
            response_format="verbose_json",
            timestamp_granularities=["word", "segment"],
        )

        # Create response with detailed timestamps
        words = [
            TranscriptionWord(word="Hello", start=0.0, end=0.5),
            TranscriptionWord(word="world", start=0.6, end=1.0),
        ]

        segments = [
            TranscriptionSegment(
                id=0,
                seek=0,
                start=0.0,
                end=1.0,
                text="Hello world",
                tokens=[1, 2],
                temperature=0.0,
                avg_logprob=-0.2,
                compression_ratio=1.0,
                no_speech_prob=0.01,
            )
        ]

        response = VerboseTranscriptionResponse(
            task="transcribe",
            language="en",
            duration=1.0,
            text="Hello world",
            words=words,
            segments=segments,
        )

        # Verify workflow
        assert request.model == "whisper-1"
        assert request.timestamp_granularities == ["word", "segment"]
        assert len(response.words) == 2
        assert len(response.segments) == 1
        assert response.text == "Hello world"

    def test_translation_workflow(self):
        """Test complete translation workflow."""
        from fakeai.models import AudioTranslationRequest, TranscriptionResponse

        # Create translation request (translates to English)
        request = AudioTranslationRequest(
            model="whisper-1", response_format="json", temperature=0.0
        )

        # Create simple response
        response = TranscriptionResponse(text="This is the translated text in English")

        # Verify workflow
        assert request.model == "whisper-1"
        assert request.response_format == "json"
        assert "English" in response.text


class TestModuleStructure:
    """Test the audio module structure and organization."""

    def test_audio_module_exports(self):
        """Test that audio module has correct exports."""
        import fakeai.models.audio as audio_module

        # Check that expected classes are available
        assert hasattr(audio_module, "SpeechRequest")
        assert hasattr(audio_module, "TranscriptionRequest")
        assert hasattr(audio_module, "TranscriptionResponse")
        assert hasattr(audio_module, "VerboseTranscriptionResponse")
        assert hasattr(audio_module, "TranscriptionWord")
        assert hasattr(audio_module, "TranscriptionSegment")
        assert hasattr(audio_module, "AudioTranslationRequest")
        assert hasattr(audio_module, "AudioSpeechesUsageResponse")
        assert hasattr(audio_module, "AudioTranscriptionsUsageResponse")

    def test_package_init_exports_audio(self):
        """Test that package __init__ exports audio models."""
        import fakeai.models as models_package

        # Check __all__ exists
        assert hasattr(models_package, "__all__")

        # Check all audio exports are in __all__
        expected_exports = [
            "SpeechRequest",
            "TranscriptionRequest",
            "TranscriptionResponse",
            "VerboseTranscriptionResponse",
            "TranscriptionWord",
            "TranscriptionSegment",
            "AudioTranslationRequest",
            "AudioSpeechesUsageResponse",
            "AudioTranscriptionsUsageResponse",
        ]

        for export in expected_exports:
            assert export in models_package.__all__, f"{export} not in __all__"
            assert hasattr(models_package, export), f"{export} not available in package"
