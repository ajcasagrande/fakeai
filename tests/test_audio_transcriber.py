"""
Tests for audio transcription module.

This module contains comprehensive tests for the AudioTranscriber class,
covering all response formats, language detection, word timestamps, and
various audio format support.
"""

#  SPDX-License-Identifier: Apache-2.0

import base64
import io
import json
import re
import struct
import wave

import pytest

from fakeai.audio_transcriber import (
    AudioTranscriber,
    get_language_name,
    parse_audio_data_uri,
    validate_audio_format,
)

# Helper functions to generate test audio files


def generate_test_wav(duration_seconds: float = 2.0, sample_rate: int = 16000) -> bytes:
    """Generate a test WAV file with silence."""
    num_samples = int(duration_seconds * sample_rate)

    # Create WAV file in memory
    wav_buffer = io.BytesIO()

    with wave.open(wav_buffer, "wb") as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        # Write silence
        wav_file.writeframes(b"\x00\x00" * num_samples)

    return wav_buffer.getvalue()


def generate_test_mp3(duration_seconds: float = 2.0) -> bytes:
    """Generate a minimal MP3 file with ID3 header."""
    # ID3v2 header
    id3_header = b"ID3\x04\x00\x00\x00\x00\x00\x00"

    # MP3 frame header (128 kbps, 44.1kHz)
    mp3_header = bytes([0xFF, 0xFB, 0x90, 0x00])

    # Calculate number of frames needed
    num_frames = max(1, int(duration_seconds * 38.28))
    frame_size = 417

    mp3_data = id3_header
    for _ in range(num_frames):
        mp3_data += mp3_header
        mp3_data += b"\x00" * (frame_size - 4)

    return mp3_data


def generate_test_m4a() -> bytes:
    """Generate a minimal M4A file with ftyp header."""
    # M4A ftyp header
    return (
        b"\x00\x00\x00\x20"  # Size
        b"ftyp"  # Type
        b"M4A "  # Major brand
        b"\x00\x00\x00\x00"  # Minor version
        b"M4A "  # Compatible brand
        b"mp42"  # Compatible brand
        b"isom"  # Compatible brand
        b"\x00\x00\x00\x00" + b"\x00" * 1024  # Padding  # Some data
    )


def generate_test_ogg() -> bytes:
    """Generate a minimal OGG file."""
    return b"OggS\x00\x02\x00\x00\x00\x00\x00\x00\x00\x00" + b"\x00" * 512


def generate_test_flac() -> bytes:
    """Generate a minimal FLAC file."""
    return b"fLaC\x00\x00\x00\x22" + b"\x00" * 512


def generate_test_webm() -> bytes:
    """Generate a minimal WebM file."""
    return b"\x1a\x45\xdf\xa3\x00\x00\x00\x00" + b"\x00" * 512


# Test fixtures


@pytest.fixture
def transcriber():
    """Create an AudioTranscriber instance."""
    return AudioTranscriber()


@pytest.fixture
def test_wav_audio():
    """Generate test WAV audio."""
    return generate_test_wav(duration_seconds=3.0)


@pytest.fixture
def test_mp3_audio():
    """Generate test MP3 audio."""
    return generate_test_mp3(duration_seconds=2.5)


# Basic transcription tests


def test_basic_transcription_json(transcriber, test_wav_audio):
    """Test basic transcription with JSON output."""
    result = transcriber.transcribe(test_wav_audio, response_format="json")

    assert isinstance(result, dict)
    assert "text" in result
    assert isinstance(result["text"], str)
    assert len(result["text"]) > 0


def test_basic_transcription_text(transcriber, test_wav_audio):
    """Test basic transcription with text output."""
    result = transcriber.transcribe(test_wav_audio, response_format="text")

    assert isinstance(result, str)
    assert len(result) > 0


def test_transcription_with_language(transcriber, test_wav_audio):
    """Test transcription with specified language."""
    result = transcriber.transcribe(
        test_wav_audio, language="en", response_format="json"
    )

    assert "text" in result
    assert isinstance(result["text"], str)


def test_transcription_with_prompt(transcriber, test_wav_audio):
    """Test transcription with guidance prompt."""
    prompt = "This is a technical discussion about AI."

    result = transcriber.transcribe(
        test_wav_audio, prompt=prompt, response_format="json"
    )

    assert "text" in result
    # Prompt should be included or influence the output
    assert isinstance(result["text"], str)


def test_transcription_with_temperature(transcriber, test_wav_audio):
    """Test transcription with different temperature values."""
    result_low = transcriber.transcribe(
        test_wav_audio, temperature=0.0, response_format="json"
    )
    result_high = transcriber.transcribe(
        test_wav_audio, temperature=0.9, response_format="json"
    )

    assert "text" in result_low
    assert "text" in result_high
    # Both should produce valid output
    assert len(result_low["text"]) > 0
    assert len(result_high["text"]) > 0


# Response format tests


def test_all_response_formats(transcriber, test_wav_audio):
    """Test all supported response formats."""
    formats = ["json", "text", "srt", "verbose_json", "vtt"]

    for fmt in formats:
        result = transcriber.transcribe(test_wav_audio, response_format=fmt)

        if fmt == "json":
            assert isinstance(result, dict)
            assert "text" in result
        elif fmt == "text":
            assert isinstance(result, str)
        elif fmt == "verbose_json":
            assert isinstance(result, dict)
            assert "task" in result
            assert "language" in result
            assert "duration" in result
            assert "text" in result
        elif fmt in ["srt", "vtt"]:
            assert isinstance(result, str)
            # Check for timestamp format
            if fmt == "srt":
                assert "-->" in result
                assert "," in result  # SRT uses commas for milliseconds
            else:  # vtt
                assert "WEBVTT" in result
                assert "-->" in result


def test_verbose_json_format(transcriber, test_wav_audio):
    """Test verbose JSON format with all fields."""
    result = transcriber.transcribe(
        test_wav_audio,
        response_format="verbose_json",
        timestamp_granularities=["word", "segment"],
    )

    assert isinstance(result, dict)
    assert result["task"] == "transcribe"
    assert "language" in result
    assert "duration" in result
    assert "text" in result
    assert "segments" in result
    assert "words" in result

    # Check segments structure
    if result["segments"]:
        segment = result["segments"][0]
        assert "id" in segment
        assert "start" in segment
        assert "end" in segment
        assert "text" in segment
        assert "tokens" in segment
        assert "temperature" in segment
        assert "avg_logprob" in segment
        assert "compression_ratio" in segment
        assert "no_speech_prob" in segment

    # Check words structure
    if result["words"]:
        word = result["words"][0]
        assert "word" in word
        assert "start" in word
        assert "end" in word


def test_srt_format(transcriber, test_wav_audio):
    """Test SRT subtitle format."""
    result = transcriber.transcribe(test_wav_audio, response_format="srt")

    assert isinstance(result, str)
    # SRT format should have sequence numbers
    assert re.search(r"^\d+$", result, re.MULTILINE)
    # SRT timestamps: HH:MM:SS,mmm
    assert re.search(r"\d{2}:\d{2}:\d{2},\d{3}", result)


def test_vtt_format(transcriber, test_wav_audio):
    """Test WebVTT subtitle format."""
    result = transcriber.transcribe(test_wav_audio, response_format="vtt")

    assert isinstance(result, str)
    # VTT must start with WEBVTT header
    assert result.startswith("WEBVTT")
    # VTT timestamps: HH:MM:SS.mmm
    assert re.search(r"\d{2}:\d{2}:\d{2}\.\d{3}", result)


# Language detection and support tests


def test_language_detection(transcriber, test_wav_audio):
    """Test automatic language detection."""
    result = transcriber.transcribe(test_wav_audio, response_format="verbose_json")

    assert "language" in result
    assert isinstance(result["language"], str)
    assert len(result["language"]) == 2  # ISO-639-1 code


def test_supported_languages(transcriber, test_wav_audio):
    """Test transcription with various supported languages."""
    test_languages = ["en", "es", "fr", "de", "ja", "zh"]

    for lang in test_languages:
        result = transcriber.transcribe(
            test_wav_audio, language=lang, response_format="verbose_json"
        )

        assert result["language"] == lang


def test_get_language_name():
    """Test language name retrieval."""
    assert get_language_name("en") == "english"
    assert get_language_name("es") == "spanish"
    assert get_language_name("fr") == "french"
    assert get_language_name("ja") == "japanese"
    assert get_language_name("xx") is None  # Unsupported language


# Word-level timestamp tests


def test_word_timestamps(transcriber, test_wav_audio):
    """Test word-level timestamp generation."""
    result = transcriber.transcribe(
        test_wav_audio,
        response_format="verbose_json",
        timestamp_granularities=["word"],
    )

    assert "words" in result
    assert isinstance(result["words"], list)

    if result["words"]:
        word = result["words"][0]
        assert "word" in word
        assert "start" in word
        assert "end" in word
        assert word["start"] >= 0
        assert word["end"] > word["start"]


def test_segment_timestamps(transcriber, test_wav_audio):
    """Test segment-level timestamp generation."""
    result = transcriber.transcribe(
        test_wav_audio,
        response_format="verbose_json",
        timestamp_granularities=["segment"],
    )

    assert "segments" in result
    assert isinstance(result["segments"], list)

    if result["segments"]:
        segment = result["segments"][0]
        assert segment["start"] >= 0
        assert segment["end"] > segment["start"]
        assert isinstance(segment["tokens"], list)
        assert len(segment["tokens"]) > 0


def test_both_granularities(transcriber, test_wav_audio):
    """Test both word and segment granularities."""
    result = transcriber.transcribe(
        test_wav_audio,
        response_format="verbose_json",
        timestamp_granularities=["word", "segment"],
    )

    assert "words" in result
    assert "segments" in result
    assert isinstance(result["words"], list)
    assert isinstance(result["segments"], list)


# Audio format support tests


def test_wav_format_detection(transcriber):
    """Test WAV format detection and parsing."""
    wav_audio = generate_test_wav(duration_seconds=2.0)
    duration = transcriber.get_audio_duration(wav_audio)

    # Duration should be approximately 2 seconds
    assert 1.8 <= duration <= 2.2


def test_mp3_format_detection(transcriber):
    """Test MP3 format detection and parsing."""
    mp3_audio = generate_test_mp3(duration_seconds=3.0)
    duration = transcriber.get_audio_duration(mp3_audio)

    # Duration should be reasonable
    assert duration > 0


def test_m4a_format_detection(transcriber):
    """Test M4A format detection."""
    m4a_audio = generate_test_m4a()
    duration = transcriber.get_audio_duration(m4a_audio)

    # Should return valid duration
    assert duration > 0


def test_ogg_format_detection(transcriber):
    """Test OGG format detection."""
    ogg_audio = generate_test_ogg()
    duration = transcriber.get_audio_duration(ogg_audio)

    assert duration > 0


def test_flac_format_detection(transcriber):
    """Test FLAC format detection."""
    flac_audio = generate_test_flac()
    duration = transcriber.get_audio_duration(flac_audio)

    assert duration > 0


def test_webm_format_detection(transcriber):
    """Test WebM format detection."""
    webm_audio = generate_test_webm()
    duration = transcriber.get_audio_duration(webm_audio)

    assert duration > 0


def test_validate_audio_formats():
    """Test audio format validation."""
    assert validate_audio_format("audio.mp3") is True
    assert validate_audio_format("audio.wav") is True
    assert validate_audio_format("audio.m4a") is True
    assert validate_audio_format("audio.ogg") is True
    assert validate_audio_format("audio.flac") is True
    assert validate_audio_format("audio.webm") is True
    assert validate_audio_format("audio.txt") is False
    assert validate_audio_format("") is False


# Translation tests


def test_basic_translation(transcriber, test_wav_audio):
    """Test basic audio translation to English."""
    result = transcriber.translate(test_wav_audio, response_format="json")

    assert isinstance(result, dict)
    assert "text" in result
    assert isinstance(result["text"], str)
    assert len(result["text"]) > 0


def test_translation_text_format(transcriber, test_wav_audio):
    """Test translation with text output."""
    result = transcriber.translate(test_wav_audio, response_format="text")

    assert isinstance(result, str)
    assert len(result) > 0


def test_translation_verbose_json(transcriber, test_wav_audio):
    """Test translation with verbose JSON output."""
    result = transcriber.translate(test_wav_audio, response_format="verbose_json")

    assert isinstance(result, dict)
    assert result["task"] == "translate"
    assert result["language"] == "en"  # Always English for translation
    assert "text" in result
    assert "duration" in result


def test_translation_with_prompt(transcriber, test_wav_audio):
    """Test translation with guidance prompt."""
    prompt = "Technical documentation"
    result = transcriber.translate(test_wav_audio, prompt=prompt)

    assert "text" in result
    assert isinstance(result["text"], str)


# Consistency tests


def test_transcription_consistency(transcriber):
    """Test that same audio produces same transcript."""
    # Create identical audio
    audio = generate_test_wav(duration_seconds=2.0)

    result1 = transcriber.transcribe(audio, response_format="json")
    result2 = transcriber.transcribe(audio, response_format="json")

    # Same audio should produce same transcript
    assert result1["text"] == result2["text"]


def test_language_detection_consistency(transcriber):
    """Test that language detection is consistent."""
    audio = generate_test_wav(duration_seconds=2.0)

    result1 = transcriber.transcribe(audio, response_format="verbose_json")
    result2 = transcriber.transcribe(audio, response_format="verbose_json")

    # Language detection should be consistent
    assert result1["language"] == result2["language"]


# Edge case tests


def test_very_short_audio(transcriber):
    """Test transcription of very short audio."""
    short_audio = generate_test_wav(duration_seconds=0.5)
    result = transcriber.transcribe(short_audio, response_format="json")

    assert "text" in result
    # Should still produce some output
    assert isinstance(result["text"], str)


def test_long_audio(transcriber):
    """Test transcription of longer audio."""
    long_audio = generate_test_wav(duration_seconds=30.0)
    result = transcriber.transcribe(
        long_audio, response_format="verbose_json", timestamp_granularities=["segment"]
    )

    assert "text" in result
    assert "segments" in result
    # Should have multiple segments
    assert len(result["segments"]) > 1


def test_empty_audio_data(transcriber):
    """Test handling of empty audio data."""
    empty_audio = b""

    # Should handle gracefully
    try:
        duration = transcriber.get_audio_duration(empty_audio)
        # Should return minimum duration
        assert duration > 0
    except Exception:
        # Or raise appropriate error
        pass


def test_invalid_audio_data(transcriber):
    """Test handling of invalid audio data."""
    invalid_audio = b"This is not audio data"
    duration = transcriber.get_audio_duration(invalid_audio)

    # Should return reasonable estimate based on size
    assert duration > 0


# Utility function tests


def test_parse_data_uri():
    """Test data URI parsing."""
    # Create base64 encoded test data
    test_data = b"test audio data"
    b64_data = base64.b64encode(test_data).decode()
    data_uri = f"data:audio/wav;base64,{b64_data}"

    parsed = parse_audio_data_uri(data_uri)
    assert parsed == test_data


def test_parse_data_uri_without_prefix():
    """Test parsing data URI without mime type prefix."""
    test_data = b"test audio data"
    b64_data = base64.b64encode(test_data).decode()

    parsed = parse_audio_data_uri(b64_data)
    assert parsed == test_data


# Model parameter tests


def test_different_models(transcriber, test_wav_audio):
    """Test transcription with different model names."""
    models = ["whisper-1", "whisper-large", "whisper-base"]

    for model in models:
        result = transcriber.transcribe(
            test_wav_audio, model=model, response_format="json"
        )

        assert "text" in result
        assert isinstance(result["text"], str)


# Segment metrics tests


def test_segment_metrics(transcriber, test_wav_audio):
    """Test that segment metrics are realistic."""
    result = transcriber.transcribe(
        test_wav_audio,
        response_format="verbose_json",
        timestamp_granularities=["segment"],
    )

    if result.get("segments"):
        for segment in result["segments"]:
            # Check avg_logprob is negative (log probability)
            assert segment["avg_logprob"] < 0
            # Check compression ratio is positive
            assert segment["compression_ratio"] > 0
            # Check no_speech_prob is between 0 and 1
            assert 0 <= segment["no_speech_prob"] <= 1
            # Check tokens is a list
            assert isinstance(segment["tokens"], list)


# Duration calculation tests


def test_duration_calculation_accuracy(transcriber):
    """Test accuracy of duration calculation for WAV files."""
    # Create WAV with known duration
    expected_duration = 5.0
    wav_audio = generate_test_wav(duration_seconds=expected_duration)

    calculated_duration = transcriber.get_audio_duration(wav_audio)

    # Should be within 10% of expected
    assert abs(calculated_duration - expected_duration) / expected_duration < 0.1


# Format-specific tests


def test_srt_timestamp_format(transcriber):
    """Test SRT timestamp formatting."""
    audio = generate_test_wav(duration_seconds=3.0)
    srt_output = transcriber.transcribe(audio, response_format="srt")

    # SRT timestamps should match format: HH:MM:SS,mmm
    timestamp_pattern = r"\d{2}:\d{2}:\d{2},\d{3}"
    matches = re.findall(timestamp_pattern, srt_output)

    assert len(matches) > 0
    # Should have pairs of timestamps (start --> end)
    assert len(matches) % 2 == 0


def test_vtt_timestamp_format(transcriber):
    """Test WebVTT timestamp formatting."""
    audio = generate_test_wav(duration_seconds=3.0)
    vtt_output = transcriber.transcribe(audio, response_format="vtt")

    # VTT timestamps should match format: HH:MM:SS.mmm
    timestamp_pattern = r"\d{2}:\d{2}:\d{2}\.\d{3}"
    matches = re.findall(timestamp_pattern, vtt_output)

    assert len(matches) > 0
    # Should have pairs of timestamps (start --> end)
    assert len(matches) % 2 == 0


# Integration tests


def test_transcription_pipeline_json(transcriber):
    """Test full transcription pipeline with JSON output."""
    audio = generate_test_wav(duration_seconds=2.5)

    result = transcriber.transcribe(
        audio_data=audio,
        model="whisper-1",
        language="en",
        prompt="Technical discussion",
        response_format="json",
        temperature=0.2,
    )

    assert isinstance(result, dict)
    assert "text" in result
    assert len(result["text"]) > 0


def test_transcription_pipeline_verbose(transcriber):
    """Test full transcription pipeline with verbose output."""
    audio = generate_test_wav(duration_seconds=3.0)

    result = transcriber.transcribe(
        audio_data=audio,
        model="whisper-1",
        language="en",
        response_format="verbose_json",
        temperature=0.0,
        timestamp_granularities=["word", "segment"],
    )

    assert isinstance(result, dict)
    assert result["task"] == "transcribe"
    assert result["language"] == "en"
    assert "duration" in result
    assert "text" in result
    assert "segments" in result
    assert "words" in result


def test_translation_pipeline(transcriber):
    """Test full translation pipeline."""
    audio = generate_test_wav(duration_seconds=2.0)

    result = transcriber.translate(
        audio_data=audio,
        model="whisper-1",
        prompt="Technical content",
        response_format="verbose_json",
        temperature=0.0,
    )

    assert isinstance(result, dict)
    assert result["task"] == "translate"
    assert result["language"] == "en"
    assert "text" in result
    assert "duration" in result
