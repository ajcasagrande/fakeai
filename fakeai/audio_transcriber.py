"""
Audio transcription module for Whisper-compatible API.

This module implements audio transcription and translation using simulated
Whisper-compatible endpoints. It supports multiple audio formats, language
detection, and various output formats (JSON, text, SRT, VTT).
"""

#  SPDX-License-Identifier: Apache-2.0

import base64
import hashlib
import io
import random
import re
import struct
import wave
from typing import Any

from faker import Faker

from fakeai.models import (
    TranscriptionRequest,
    TranscriptionResponse,
    TranscriptionSegment,
    TranscriptionWord,
    VerboseTranscriptionResponse,
)
from fakeai.utils import calculate_token_count

fake = Faker()


# Supported audio formats
SUPPORTED_FORMATS = {
    "mp3",
    "mp4",
    "mpeg",
    "mpga",
    "m4a",
    "wav",
    "webm",
    "ogg",
    "flac",
    "aac",
}

# Language code mapping (ISO-639-1) with common languages
SUPPORTED_LANGUAGES = {
    "en": "english",
    "es": "spanish",
    "fr": "french",
    "de": "german",
    "it": "italian",
    "pt": "portuguese",
    "nl": "dutch",
    "pl": "polish",
    "ru": "russian",
    "ja": "japanese",
    "ko": "korean",
    "zh": "chinese",
    "ar": "arabic",
    "hi": "hindi",
    "tr": "turkish",
    "vi": "vietnamese",
    "th": "thai",
    "id": "indonesian",
    "he": "hebrew",
    "uk": "ukrainian",
    "cs": "czech",
    "ro": "romanian",
    "sv": "swedish",
    "da": "danish",
    "fi": "finnish",
    "no": "norwegian",
    "el": "greek",
    "hu": "hungarian",
    "bg": "bulgarian",
    "hr": "croatian",
    "sk": "slovak",
    "sl": "slovenian",
    "lt": "lithuanian",
    "lv": "latvian",
    "et": "estonian",
    "is": "icelandic",
    "ga": "irish",
    "cy": "welsh",
    "sq": "albanian",
    "mk": "macedonian",
    "sr": "serbian",
    "bs": "bosnian",
    "mt": "maltese",
    "ca": "catalan",
    "eu": "basque",
    "gl": "galician",
    "af": "afrikaans",
    "sw": "swahili",
    "ms": "malay",
    "tl": "tagalog",
}


class AudioTranscriber:
    """
    Audio transcription and translation using Whisper-compatible API.

    This class simulates Whisper API behavior by generating realistic
    transcriptions based on audio metadata and providing multiple output
    formats with timestamps and confidence scores.
    """

    def __init__(self):
        """Initialize the audio transcriber."""
        self.fake = Faker()
        # Seed for consistent transcription based on content hash
        self._transcription_cache: dict[str, str] = {}

    def transcribe(
        self,
        audio_data: bytes,
        model: str = "whisper-1",
        language: str | None = None,
        prompt: str | None = None,
        response_format: str = "json",
        temperature: float = 0.0,
        timestamp_granularities: list[str] | None = None,
    ) -> dict[str, Any] | str:
        """
        Transcribe audio file.

        Args:
            audio_data: Audio file bytes
            model: Whisper model ID (whisper-1, etc.)
            language: Language code (ISO-639-1 format, e.g., 'en')
            prompt: Optional text to guide transcription style
            response_format: Output format (json, text, srt, verbose_json, vtt)
            temperature: Sampling temperature (0.0 to 1.0)
            timestamp_granularities: List of granularities (word, segment)

        Returns:
            Transcribed text in specified format
        """
        # Extract audio metadata
        duration = self.get_audio_duration(audio_data)
        detected_language = language or self._detect_language(audio_data)

        # Generate transcript text
        transcript_text = self._generate_transcript(
            audio_data, duration, detected_language, prompt, temperature
        )

        # Return based on format
        if response_format == "text":
            return transcript_text
        elif response_format == "json":
            return {"text": transcript_text}
        elif response_format == "verbose_json":
            return self._generate_verbose_json(
                transcript_text,
                detected_language,
                duration,
                temperature,
                timestamp_granularities or [],
            )
        elif response_format == "srt":
            return self._generate_srt(transcript_text, duration)
        elif response_format == "vtt":
            return self._generate_vtt(transcript_text, duration)
        else:
            # Default to JSON
            return {"text": transcript_text}

    def translate(
        self,
        audio_data: bytes,
        model: str = "whisper-1",
        prompt: str | None = None,
        response_format: str = "json",
        temperature: float = 0.0,
    ) -> dict[str, Any] | str:
        """
        Translate audio to English.

        Args:
            audio_data: Audio file bytes
            model: Whisper model ID
            prompt: Optional text to guide translation
            response_format: Output format (json, text, srt, verbose_json, vtt)
            temperature: Sampling temperature (0.0 to 1.0)

        Returns:
            Translated text in English
        """
        # Get duration and detect source language
        duration = self.get_audio_duration(audio_data)
        detected_language = self._detect_language(audio_data)

        # Generate transcript in original language first
        original_text = self._generate_transcript(
            audio_data, duration, detected_language, prompt, temperature
        )

        # Translate to English (simulated)
        translated_text = self._translate_to_english(original_text, detected_language)

        # Return in requested format
        if response_format == "text":
            return translated_text
        elif response_format == "json":
            return {"text": translated_text}
        elif response_format == "verbose_json":
            return self._generate_verbose_json(
                translated_text,
                "en",  # Output language is always English
                duration,
                temperature,
                [],
                task="translate",
            )
        elif response_format == "srt":
            return self._generate_srt(translated_text, duration)
        elif response_format == "vtt":
            return self._generate_vtt(translated_text, duration)
        else:
            return {"text": translated_text}

    def get_audio_duration(self, audio_data: bytes) -> float:
        """
        Extract audio duration in seconds from audio file.

        Attempts to parse audio metadata from various formats. Falls back to
        estimation based on file size if parsing fails.

        Args:
            audio_data: Audio file bytes

        Returns:
            Duration in seconds
        """
        # Try to detect format from magic bytes
        format_type = self._detect_audio_format(audio_data)

        try:
            if format_type == "wav":
                return self._parse_wav_duration(audio_data)
            elif format_type == "mp3":
                return self._estimate_mp3_duration(audio_data)
            else:
                # Fallback: estimate based on file size
                # Assuming average bitrate of 128 kbps
                return self._estimate_duration_from_size(audio_data)
        except Exception:
            # If all else fails, use reasonable default
            return self._estimate_duration_from_size(audio_data)

    def _detect_audio_format(self, audio_data: bytes) -> str:
        """Detect audio format from magic bytes."""
        if len(audio_data) < 12:
            return "unknown"

        # Check for WAV (RIFF...WAVE)
        if audio_data[:4] == b"RIFF" and audio_data[8:12] == b"WAVE":
            return "wav"

        # Check for MP3 (ID3 tag or sync frame)
        if audio_data[:3] == b"ID3" or (
            audio_data[0] == 0xFF and (audio_data[1] & 0xE0) == 0xE0
        ):
            return "mp3"

        # Check for M4A/MP4 (ftyp)
        if audio_data[4:8] == b"ftyp":
            return "m4a"

        # Check for OGG (OggS)
        if audio_data[:4] == b"OggS":
            return "ogg"

        # Check for FLAC (fLaC)
        if audio_data[:4] == b"fLaC":
            return "flac"

        # Check for WebM (EBML header)
        if audio_data[:4] == b"\x1a\x45\xdf\xa3":
            return "webm"

        return "unknown"

    def _parse_wav_duration(self, audio_data: bytes) -> float:
        """Parse duration from WAV file."""
        try:
            with wave.open(io.BytesIO(audio_data), "rb") as wav_file:
                frames = wav_file.getnframes()
                rate = wav_file.getframerate()
                duration = frames / float(rate)
                return duration
        except Exception:
            # If parsing fails, estimate
            return self._estimate_duration_from_size(audio_data)

    def _estimate_mp3_duration(self, audio_data: bytes) -> float:
        """Estimate MP3 duration from file size and average bitrate."""
        # Simple estimation: assume 128 kbps average bitrate
        # 128 kbps = 16 KB/s
        size_kb = len(audio_data) / 1024
        duration = size_kb / 16  # seconds
        return max(0.1, duration)

    def _estimate_duration_from_size(self, audio_data: bytes) -> float:
        """Estimate duration from file size using average bitrate."""
        # Assume 128 kbps average bitrate
        size_kb = len(audio_data) / 1024
        duration = size_kb / 16
        # Ensure minimum duration
        return max(0.5, min(duration, 3600))  # Cap at 1 hour

    def _detect_language(self, audio_data: bytes) -> str:
        """
        Detect language from audio content (simulated).

        Uses a hash of the audio data to consistently return the same
        language for the same audio file.

        Args:
            audio_data: Audio file bytes

        Returns:
            ISO-639-1 language code
        """
        # Create hash of audio data for consistent detection
        audio_hash = hashlib.md5(audio_data).hexdigest()
        hash_int = int(audio_hash[:8], 16)

        # Use hash to pick a language consistently
        language_codes = list(SUPPORTED_LANGUAGES.keys())
        selected_idx = hash_int % len(language_codes)

        return language_codes[selected_idx]

    def _generate_transcript(
        self,
        audio_data: bytes,
        duration: float,
        language: str,
        prompt: str | None,
        temperature: float,
    ) -> str:
        """
        Generate simulated transcript text.

        Creates realistic transcript based on duration and language using
        Faker library. Transcript is cached based on audio hash for consistency.

        Args:
            audio_data: Audio file bytes
            duration: Duration in seconds
            language: Language code
            prompt: Optional prompt to guide style
            temperature: Sampling temperature

        Returns:
            Transcribed text
        """
        # Create stable hash for caching
        audio_hash = hashlib.md5(audio_data).hexdigest()

        # Check cache
        cache_key = f"{audio_hash}_{language}_{temperature}"
        if cache_key in self._transcription_cache:
            return self._transcription_cache[cache_key]

        # Seed faker for consistent output
        hash_seed = int(audio_hash[:8], 16)
        random.seed(hash_seed)

        # Get locale for language
        locale = self._get_faker_locale(language)
        lang_faker = Faker(locale)

        # Estimate number of sentences based on duration
        # Average speech rate: 150 words per minute, ~15-20 words per sentence
        words_per_minute = 150
        total_words = int(duration / 60 * words_per_minute)
        num_sentences = max(1, int(total_words / 17))  # ~17 words per sentence

        # Generate sentences
        sentences = []
        if prompt:
            # If prompt provided, use it as context
            sentences.append(prompt)
            num_sentences = max(1, num_sentences - 1)

        # Generate additional sentences
        for _ in range(num_sentences):
            # Use lower temperature for more coherent text
            if temperature < 0.3:
                sentence = lang_faker.sentence(nb_words=random.randint(10, 25))
            elif temperature < 0.7:
                sentence = lang_faker.sentence(nb_words=random.randint(8, 20))
            else:
                # Higher temperature: more varied
                sentence = lang_faker.sentence(nb_words=random.randint(5, 30))

            sentences.append(sentence)

        transcript = " ".join(sentences)

        # Cache the result
        self._transcription_cache[cache_key] = transcript

        # Reset random seed
        random.seed()

        return transcript

    def _translate_to_english(self, text: str, source_language: str) -> str:
        """
        Translate text to English (simulated).

        For simulation purposes, we generate English text with similar
        characteristics to the input text.

        Args:
            text: Source text
            source_language: Source language code

        Returns:
            Translated English text
        """
        if source_language == "en":
            return text

        # For simulation, generate English text with similar word count
        word_count = len(text.split())
        num_sentences = max(1, word_count // 17)

        english_faker = Faker("en_US")
        sentences = []
        for _ in range(num_sentences):
            sentence = english_faker.sentence(nb_words=random.randint(10, 25))
            sentences.append(sentence)

        return " ".join(sentences)

    def _get_faker_locale(self, language_code: str) -> str:
        """
        Get Faker locale from language code.

        Maps ISO-639-1 language codes to Faker locales.

        Args:
            language_code: ISO-639-1 language code

        Returns:
            Faker locale string
        """
        locale_mapping = {
            "en": "en_US",
            "es": "es_ES",
            "fr": "fr_FR",
            "de": "de_DE",
            "it": "it_IT",
            "pt": "pt_PT",
            "nl": "nl_NL",
            "pl": "pl_PL",
            "ru": "ru_RU",
            "ja": "ja_JP",
            "ko": "ko_KR",
            "zh": "zh_CN",
            "ar": "ar_SA",
            "hi": "hi_IN",
            "tr": "tr_TR",
            "uk": "uk_UA",
            "cs": "cs_CZ",
            "ro": "ro_RO",
            "sv": "sv_SE",
            "da": "da_DK",
            "fi": "fi_FI",
            "no": "no_NO",
            "el": "el_GR",
            "hu": "hu_HU",
        }

        return locale_mapping.get(language_code, "en_US")

    def _generate_verbose_json(
        self,
        text: str,
        language: str,
        duration: float,
        temperature: float,
        timestamp_granularities: list[str],
        task: str = "transcribe",
    ) -> dict[str, Any]:
        """
        Generate verbose JSON response with segments and word timestamps.

        Args:
            text: Transcribed text
            language: Language code
            duration: Audio duration in seconds
            temperature: Sampling temperature
            timestamp_granularities: Requested granularities (word, segment)
            task: Task type (transcribe or translate)

        Returns:
            Verbose JSON response dictionary
        """
        # Split text into segments (roughly every 5-10 seconds)
        segments = self._create_segments(text, duration, temperature)

        # Generate word-level timestamps if requested
        words = None
        if "word" in timestamp_granularities:
            words = self._create_word_timestamps(text, duration)

        response = {
            "task": task,
            "language": language,
            "duration": round(duration, 2),
            "text": text,
        }

        if segments:
            response["segments"] = segments

        if words:
            response["words"] = words

        return response

    def _create_segments(
        self, text: str, duration: float, temperature: float
    ) -> list[dict[str, Any]]:
        """
        Create segment-level transcription with timing.

        Args:
            text: Full transcribed text
            duration: Total duration in seconds
            temperature: Sampling temperature

        Returns:
            List of segment dictionaries
        """
        # Split text into sentences
        sentences = re.split(r"(?<=[.!?])\s+", text)
        if not sentences:
            return []

        segments = []
        segment_duration = duration / len(sentences)
        current_time = 0.0

        for idx, sentence in enumerate(sentences):
            # Calculate segment timing
            start_time = current_time
            # Add small random variance to segment duration
            variance = random.uniform(0.8, 1.2)
            end_time = min(current_time + segment_duration * variance, duration)

            # Generate token IDs (simulated)
            token_count = calculate_token_count(sentence)
            token_ids = [random.randint(1000, 50000) for _ in range(token_count)]

            # Calculate segment metrics
            avg_logprob = random.uniform(-0.5, -0.05)  # Higher confidence
            compression_ratio = len(sentence) / token_count
            no_speech_prob = random.uniform(0.0, 0.05)  # Low probability of no speech

            segment = {
                "id": idx,
                "seek": int(start_time * 1000),  # Seek offset in milliseconds
                "start": round(start_time, 2),
                "end": round(end_time, 2),
                "text": sentence,
                "tokens": token_ids,
                "temperature": temperature,
                "avg_logprob": round(avg_logprob, 3),
                "compression_ratio": round(compression_ratio, 2),
                "no_speech_prob": round(no_speech_prob, 4),
            }

            segments.append(segment)
            current_time = end_time

        return segments

    def _create_word_timestamps(
        self, text: str, duration: float
    ) -> list[dict[str, Any]]:
        """
        Create word-level timestamps.

        Args:
            text: Transcribed text
            duration: Total duration in seconds

        Returns:
            List of word timestamp dictionaries
        """
        # Split into words (including punctuation)
        words = re.findall(r"\b\w+\b|[^\w\s]", text)
        if not words:
            return []

        word_timestamps = []
        word_duration = duration / len(words)
        current_time = 0.0

        for word in words:
            # Skip standalone punctuation for timestamps
            if re.match(r"^[^\w\s]+$", word):
                continue

            # Add small variance to word timing
            variance = random.uniform(0.7, 1.3)
            start_time = current_time
            end_time = min(current_time + word_duration * variance, duration)

            word_timestamps.append(
                {
                    "word": word,
                    "start": round(start_time, 2),
                    "end": round(end_time, 2),
                }
            )

            current_time = end_time

        return word_timestamps

    def _generate_srt(self, text: str, duration: float) -> str:
        """
        Generate SRT (SubRip) subtitle format.

        Args:
            text: Transcribed text
            duration: Total duration in seconds

        Returns:
            SRT formatted string
        """
        # Split into subtitle segments (roughly every 5 seconds or sentence)
        sentences = re.split(r"(?<=[.!?])\s+", text)
        if not sentences:
            return ""

        srt_lines = []
        segment_duration = duration / len(sentences)
        current_time = 0.0

        for idx, sentence in enumerate(sentences, start=1):
            start_time = current_time
            end_time = min(current_time + segment_duration, duration)

            # Format timestamps (HH:MM:SS,mmm)
            start_str = self._format_srt_timestamp(start_time)
            end_str = self._format_srt_timestamp(end_time)

            # Add SRT entry
            srt_lines.append(f"{idx}")
            srt_lines.append(f"{start_str} --> {end_str}")
            srt_lines.append(sentence)
            srt_lines.append("")  # Blank line between entries

            current_time = end_time

        return "\n".join(srt_lines)

    def _format_srt_timestamp(self, seconds: float) -> str:
        """Format seconds as SRT timestamp (HH:MM:SS,mmm)."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    def _generate_vtt(self, text: str, duration: float) -> str:
        """
        Generate WebVTT subtitle format.

        Args:
            text: Transcribed text
            duration: Total duration in seconds

        Returns:
            WebVTT formatted string
        """
        # WebVTT starts with header
        vtt_lines = ["WEBVTT", ""]

        # Split into subtitle segments
        sentences = re.split(r"(?<=[.!?])\s+", text)
        if not sentences:
            return "WEBVTT\n"

        segment_duration = duration / len(sentences)
        current_time = 0.0

        for sentence in sentences:
            start_time = current_time
            end_time = min(current_time + segment_duration, duration)

            # Format timestamps (HH:MM:SS.mmm)
            start_str = self._format_vtt_timestamp(start_time)
            end_str = self._format_vtt_timestamp(end_time)

            # Add VTT entry
            vtt_lines.append(f"{start_str} --> {end_str}")
            vtt_lines.append(sentence)
            vtt_lines.append("")  # Blank line between entries

            current_time = end_time

        return "\n".join(vtt_lines)

    def _format_vtt_timestamp(self, seconds: float) -> str:
        """Format seconds as WebVTT timestamp (HH:MM:SS.mmm)."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"


# Convenience functions for integration with FakeAI service


def parse_audio_data_uri(data_uri: str) -> bytes:
    """
    Parse base64 data URI to audio bytes.

    Args:
        data_uri: Data URI string (data:audio/...;base64,...)

    Returns:
        Decoded audio bytes
    """
    # Extract base64 data from URI
    if "," in data_uri:
        base64_data = data_uri.split(",", 1)[1]
    else:
        base64_data = data_uri

    return base64.b64decode(base64_data)


def validate_audio_format(filename: str) -> bool:
    """
    Validate if audio format is supported.

    Args:
        filename: Audio filename with extension

    Returns:
        True if format is supported
    """
    if not filename:
        return False

    extension = filename.rsplit(".", 1)[-1].lower()
    return extension in SUPPORTED_FORMATS


def get_language_name(language_code: str) -> str | None:
    """
    Get full language name from ISO-639-1 code.

    Args:
        language_code: Two-letter language code

    Returns:
        Full language name or None if not found
    """
    return SUPPORTED_LANGUAGES.get(language_code.lower())
