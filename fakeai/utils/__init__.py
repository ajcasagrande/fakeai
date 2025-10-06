"""
Utility functions and classes for the OpenAI simulated server.

This module re-exports all utilities from submodules to maintain backward
compatibility with the original utils.py interface.
"""

#  SPDX-License-Identifier: Apache-2.0

# Re-export Faker for backward compatibility
from faker import Faker

from fakeai.utils.async_executor import AsyncExecutor
from fakeai.utils.audio_generation import (
    estimate_audio_duration,
    generate_mp3_placeholder,
    generate_simulated_audio,
    generate_wav_audio,
)
from fakeai.utils.embeddings import create_random_embedding, normalize_embedding
from fakeai.utils.text_generation import SimulatedGenerator
from fakeai.utils.tokens import calculate_token_count, tokenize_text

fake = Faker()

__all__ = [
    # Token utilities
    "tokenize_text",
    "calculate_token_count",
    # Embedding utilities
    "create_random_embedding",
    "normalize_embedding",
    # Audio generation utilities
    "estimate_audio_duration",
    "generate_wav_audio",
    "generate_mp3_placeholder",
    "generate_simulated_audio",
    # Text generation
    "SimulatedGenerator",
    # Async execution
    "AsyncExecutor",
    # Faker instance
    "fake",
]
