"""
Audio generation utilities for text-to-speech simulation.

This module provides functions for generating simulated audio files in various
formats (MP3, WAV, PCM, etc.) with realistic durations based on text length.
"""

#  SPDX-License-Identifier: Apache-2.0


def estimate_audio_duration(text: str, speed: float = 1.0) -> float:
    """
    Estimate the duration of generated audio based on text length.

    Uses a heuristic of ~150 words per minute at normal speed (1.0),
    which is typical for natural speech.

    Args:
        text: The text to estimate duration for
        speed: The playback speed multiplier (0.25 to 4.0)

    Returns:
        Estimated duration in seconds
    """
    # Count words (roughly)
    word_count = len(text.split())

    # Base rate: 150 words per minute at speed 1.0
    words_per_minute = 150

    # Calculate duration in minutes, then convert to seconds
    base_duration = (word_count / words_per_minute) * 60

    # Adjust for speed (higher speed = shorter duration)
    adjusted_duration = base_duration / speed

    return max(0.1, adjusted_duration)  # Minimum 0.1 seconds


def generate_wav_audio(duration_seconds: float, sample_rate: int = 24000) -> bytes:
    """
    Generate a minimal valid WAV audio file with silence.

    Creates a properly formatted WAV file with PCM 16-bit mono audio
    containing silence for the specified duration.

    Args:
        duration_seconds: Duration of audio in seconds
        sample_rate: Sample rate in Hz (default: 24000)

    Returns:
        Bytes containing a valid WAV file
    """
    import io
    import struct

    # Calculate number of samples
    num_samples = int(duration_seconds * sample_rate)

    # WAV file parameters
    num_channels = 1  # Mono
    bits_per_sample = 16
    byte_rate = sample_rate * num_channels * bits_per_sample // 8
    block_align = num_channels * bits_per_sample // 8
    data_size = num_samples * block_align

    # Create WAV file in memory
    wav_buffer = io.BytesIO()

    # Write RIFF header
    wav_buffer.write(b"RIFF")
    wav_buffer.write(struct.pack("<I", 36 + data_size))  # Chunk size
    wav_buffer.write(b"WAVE")

    # Write fmt subchunk
    wav_buffer.write(b"fmt ")
    wav_buffer.write(struct.pack("<I", 16))  # Subchunk size
    wav_buffer.write(struct.pack("<H", 1))  # Audio format (PCM)
    wav_buffer.write(struct.pack("<H", num_channels))
    wav_buffer.write(struct.pack("<I", sample_rate))
    wav_buffer.write(struct.pack("<I", byte_rate))
    wav_buffer.write(struct.pack("<H", block_align))
    wav_buffer.write(struct.pack("<H", bits_per_sample))

    # Write data subchunk
    wav_buffer.write(b"data")
    wav_buffer.write(struct.pack("<I", data_size))

    # Write silence (all zeros)
    wav_buffer.write(b"\x00" * data_size)

    return wav_buffer.getvalue()


def generate_mp3_placeholder(duration_seconds: float) -> bytes:
    """
    Generate a minimal MP3 file placeholder.

    Creates a very small MP3 file with proper headers. This is a placeholder
    that represents audio without containing actual encoded audio data.

    Args:
        duration_seconds: Duration of audio in seconds (for metadata)

    Returns:
        Bytes containing a minimal MP3 file
    """
    # Minimal MP3 frame header
    # FF FB: sync word + MPEG-1 Layer 3
    # 90: 128 kbps, 44.1kHz
    # 00: no padding, no private bit, mono
    mp3_header = bytes([0xFF, 0xFB, 0x90, 0x00])

    # ID3v2 header with duration metadata
    id3_header = b"ID3\x04\x00\x00\x00\x00\x00\x00"

    # Create a minimal valid MP3 file
    # For a realistic simulation, we create multiple frames
    num_frames = max(
        1, int(duration_seconds * 38.28)
    )  # ~38.28 frames per second at 128kbps
    frame_size = 417  # Size of a frame at 128kbps, 44.1kHz

    mp3_data = id3_header
    for _ in range(num_frames):
        mp3_data += mp3_header
        mp3_data += b"\x00" * (frame_size - 4)  # Pad frame with zeros

    return mp3_data


def generate_simulated_audio(
    text: str,
    voice: str,
    response_format: str = "mp3",
    speed: float = 1.0,
) -> bytes:
    """
    Generate simulated audio data for text-to-speech.

    Creates properly formatted audio files in the requested format with
    realistic duration based on the input text length and speed.

    Args:
        text: The text to convert to speech
        voice: The voice to use (alloy, echo, fable, onyx, nova, shimmer, marin, cedar)
        response_format: Audio format (mp3, opus, aac, flac, wav, pcm)
        speed: Playback speed multiplier (0.25 to 4.0)

    Returns:
        Bytes containing the audio file in the requested format
    """
    # Estimate duration based on text and speed
    duration = estimate_audio_duration(text, speed)

    # Generate audio based on format
    if response_format == "wav":
        return generate_wav_audio(duration)
    elif response_format == "pcm":
        # PCM is raw audio data (16-bit mono at 24kHz)
        sample_rate = 24000
        num_samples = int(duration * sample_rate)
        return b"\x00\x00" * num_samples  # 16-bit silence
    elif response_format == "mp3":
        return generate_mp3_placeholder(duration)
    elif response_format in ["opus", "aac", "flac"]:
        # For other formats, return MP3 as a placeholder
        # In a real implementation, you'd use proper encoding libraries
        return generate_mp3_placeholder(duration)
    else:
        # Default to MP3
        return generate_mp3_placeholder(duration)
