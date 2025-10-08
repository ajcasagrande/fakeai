"""
Enhanced Log Probability Generation for FakeAI

This module provides realistic log probability generation for both Chat and Completions APIs.
Key features:
- Hash-based deterministic generation (same input → same output)
- Temperature-aware distributions
- Proper logprob ranges based on token confidence
- Realistic gaps between alternatives
- UTF-8 byte arrays for Chat API
"""

#  SPDX-License-Identifier: Apache-2.0

import random
from typing import Any

from fakeai.models import (
    ChatLogprob,
    ChatLogprobs,
    LogProbs,
    TopLogprob,
)


def estimate_token_confidence(
    token: str, position: int, context_hash: int, temperature: float = 1.0
) -> str:
    """
    Estimate confidence level for a token based on multiple factors.

    Args:
        token: The token to estimate confidence for
        position: Position in the sequence (0-indexed)
        context_hash: Hash of the context for deterministic randomness
        temperature: Sampling temperature (affects confidence distribution)

    Returns:
        "high", "medium", or "low" confidence level
    """
    # Create deterministic seed from token, position, and context
    seed = hash((token, position, context_hash)) % (2**31)
    rng = random.Random(seed)

    # Common words/tokens tend to have higher confidence
    common_patterns = [
        "the",
        "a",
        "an",
        "and",
        "or",
        "but",
        "in",
        "on",
        "at",
        "to",
        "for",
        "of",
        "with",
        "from",
        "by",
        "as",
        "is",
        "are",
        "was",
        "were",
        "be",
        ".",
        ",",
        "!",
        "?",
        ":",
        ";",
        '"',
        "'",
        "(",
        ")",
        "-",
    ]

    # Base confidence based on token properties
    is_common = token.lower() in common_patterns
    is_punctuation = token in ".,;:!?()[]{}\"'-"
    is_short = len(token) <= 3

    # Calculate base confidence score (0-1)
    base_confidence = 0.5
    if is_common:
        base_confidence += 0.3
    if is_punctuation:
        base_confidence += 0.2
    if is_short:
        base_confidence += 0.1

    # Position affects confidence (earlier tokens may be less certain)
    position_factor = min(1.0, (position + 1) / 10)
    base_confidence = base_confidence * 0.7 + position_factor * 0.3

    # Temperature affects confidence distribution
    # Lower temp → higher confidence, higher temp → lower confidence
    if temperature < 0.5:
        base_confidence += 0.2
    elif temperature > 1.5:
        base_confidence -= 0.2

    # Add some randomness but keep it deterministic
    confidence_noise = rng.uniform(-0.1, 0.1)
    final_confidence = max(0.0, min(1.0, base_confidence + confidence_noise))

    # Map to confidence levels
    if final_confidence > 0.7:
        return "high"
    elif final_confidence > 0.4:
        return "medium"
    else:
        return "low"


def generate_realistic_top_logprobs(
    token: str,
    position: int,
    context_hash: int,
    token_logprob: float,
    top_k: int = 5,
    temperature: float = 1.0,
) -> list[dict[str, Any]]:
    """
    Generate realistic top-k alternative tokens with proper logprob gaps.

    The gaps between alternatives follow realistic patterns:
    - High confidence: large gap to next alternative (2-5 logprobs)
    - Medium confidence: medium gap (1-3 logprobs)
    - Low confidence: small gap (0.5-2 logprobs)

    Args:
        token: The selected token
        position: Position in the sequence
        context_hash: Hash of the context for deterministic generation
        token_logprob: Log probability of the selected token
        top_k: Number of alternatives to generate
        temperature: Sampling temperature

    Returns:
        List of dictionaries with "token" and "logprob" keys, sorted descending
    """
    # Create deterministic random generator
    seed = hash((token, position, context_hash, "alternatives")) % (2**31)
    rng = random.Random(seed)

    # Estimate confidence level
    confidence = estimate_token_confidence(
        token, position, context_hash, temperature)

    # Define gap ranges based on confidence
    if confidence == "high":
        gap_min, gap_max = 2.0, 5.0
    elif confidence == "medium":
        gap_min, gap_max = 1.0, 3.0
    else:  # low
        gap_min, gap_max = 0.5, 2.0

    # Generate alternatives
    alternatives = []
    current_logprob = token_logprob

    for i in range(top_k):
        # Generate gap (decreasing as we go down the list)
        gap = rng.uniform(gap_min, gap_max) * (1.0 - i * 0.15)
        current_logprob -= gap

        # Generate alternative token
        alt_token = generate_alternative_token(token, i, context_hash, rng)

        alternatives.append({"token": alt_token, "logprob": current_logprob})

    return alternatives


def generate_alternative_token(
    original_token: str, alt_index: int, context_hash: int, rng: random.Random
) -> str:
    """
    Generate a plausible alternative token.

    Args:
        original_token: The original selected token
        alt_index: Index of this alternative (0 = closest alternative)
        context_hash: Context hash for deterministic generation
        rng: Random number generator

    Returns:
        A plausible alternative token
    """
    # Common alternatives for common tokens
    common_alternatives = {
        "the": ["a", "The", "this", "that", "its"],
        "a": ["the", "an", "one", "A", "some"],
        "and": ["or", "but", "And", "&", "plus"],
        "is": ["was", "are", "be", "Is", "has"],
        "to": ["for", "from", "To", "into", "toward"],
        ".": [".", ",", "!", "?", ";"],
        ",": [",", ".", ";", "and", " -"],
    }

    # If we have predefined alternatives, use them
    if original_token.lower() in common_alternatives and alt_index < len(
        common_alternatives[original_token.lower()]
    ):
        alternatives_list = common_alternatives[original_token.lower()]
        return alternatives_list[alt_index]

    # Generate plausible alternatives based on token type
    if original_token.isalpha():
        # For words, generate similar words
        if alt_index == 0:
            # Capitalization variant
            if original_token[0].islower():
                return original_token.capitalize()
            else:
                return original_token.lower()
        elif alt_index == 1:
            # Shorter variant
            if len(original_token) > 3:
                return original_token[: len(original_token) - 1]
            else:
                return original_token + "s"
        else:
            # Random similar word
            variations = [
                original_token + "s",
                original_token + "ed",
                original_token + "ing",
                "un" + original_token if len(original_token) > 4 else original_token,
                original_token[1:] if len(original_token) > 3 else original_token,
            ]
            return rng.choice(variations)
    elif original_token.isdigit():
        # For numbers, generate nearby numbers
        try:
            num = int(original_token)
            offset = [-2, -1, 1, 2, 10][min(alt_index, 4)]
            return str(num + offset)
        except ValueError:
            return original_token
    else:
        # For punctuation or special tokens, return common alternatives
        punct_alternatives = [".", ",", "!", "?", ";", ":", "-", "'", '"']
        if alt_index < len(punct_alternatives):
            return punct_alternatives[alt_index]
        return original_token


def token_to_bytes(token: str) -> list[int]:
    """
    Convert a token to its UTF-8 byte representation.

    Args:
        token: The token string

    Returns:
        List of byte values (0-255)
    """
    return list(token.encode("utf-8"))


def create_chat_logprobs(
    text: str,
    tokens: list[str],
    top_logprobs: int | None = None,
    temperature: float = 1.0,
) -> ChatLogprobs | None:
    """
    Generate ChatLogprobs for the Chat API.

    Args:
        text: The complete text (for context hashing)
        tokens: List of tokens
        top_logprobs: Number of top alternatives to include (0-20), or None
        temperature: Sampling temperature

    Returns:
        ChatLogprobs object or None if top_logprobs is None
    """
    if top_logprobs is None:
        return None

    # Create deterministic context hash
    context_hash = hash(text) % (2**31)

    # Generate log probabilities for each token
    content: list[ChatLogprob] = []

    for position, token in enumerate(tokens):
        # Generate logprob for this token based on confidence
        confidence = estimate_token_confidence(
            token, position, context_hash, temperature
        )

        # Map confidence to logprob range
        if confidence == "high":
            # High confidence: -0.01 to 0 (very close to 1.0 probability)
            seed = hash((token, position, context_hash, "logprob")) % (2**31)
            rng = random.Random(seed)
            token_logprob = -rng.uniform(0.001, 0.01)
        elif confidence == "medium":
            # Medium confidence: -0.5 to -0.1
            seed = hash((token, position, context_hash, "logprob")) % (2**31)
            rng = random.Random(seed)
            token_logprob = -rng.uniform(0.1, 0.5)
        else:  # low
            # Low confidence: -3.0 to -1.5
            seed = hash((token, position, context_hash, "logprob")) % (2**31)
            rng = random.Random(seed)
            token_logprob = -rng.uniform(1.5, 3.0)

        # Generate top alternatives
        alternatives_data = generate_realistic_top_logprobs(
            token,
            position,
            context_hash,
            token_logprob,
            top_k=min(top_logprobs, 5),  # API supports 0-20, we'll do up to 5
            temperature=temperature,
        )

        # Convert to TopLogprob objects
        top_logprobs_list = [
            TopLogprob(
                token=alt["token"],
                logprob=alt["logprob"],
                bytes=token_to_bytes(alt["token"]),
            )
            for alt in alternatives_data
        ]

        # Create ChatLogprob entry
        content.append(
            ChatLogprob(
                token=token,
                logprob=token_logprob,
                bytes=token_to_bytes(token),
                top_logprobs=top_logprobs_list,
            )
        )

    return ChatLogprobs(content=content)


def create_completion_logprobs(
        text: str,
        tokens: list[str],
        logprobs: int | None = None,
        temperature: float = 1.0) -> LogProbs | None:
    """
    Generate LogProbs for the Completions API (legacy format).

    Args:
        text: The complete text
        tokens: List of tokens
        logprobs: Number of top alternatives to include (0-5), or None
        temperature: Sampling temperature

    Returns:
        LogProbs object or None if logprobs is None
    """
    if logprobs is None or logprobs == 0:
        return None

    # Create deterministic context hash
    context_hash = hash(text) % (2**31)

    # Generate log probabilities for each token
    token_logprobs: list[float] = []
    top_logprobs_list: list[dict[str, float]] = []
    text_offset: list[int] = []

    current_offset = 0

    for position, token in enumerate(tokens):
        # Record text offset
        text_offset.append(current_offset)
        current_offset += len(token)

        # Generate logprob for this token
        confidence = estimate_token_confidence(
            token, position, context_hash, temperature
        )

        # Map confidence to logprob range
        if confidence == "high":
            seed = hash((token, position, context_hash, "logprob")) % (2**31)
            rng = random.Random(seed)
            token_logprob = -rng.uniform(0.001, 0.01)
        elif confidence == "medium":
            seed = hash((token, position, context_hash, "logprob")) % (2**31)
            rng = random.Random(seed)
            token_logprob = -rng.uniform(0.1, 0.5)
        else:  # low
            seed = hash((token, position, context_hash, "logprob")) % (2**31)
            rng = random.Random(seed)
            token_logprob = -rng.uniform(1.5, 3.0)

        token_logprobs.append(token_logprob)

        # Generate top alternatives
        alternatives_data = generate_realistic_top_logprobs(
            token,
            position,
            context_hash,
            token_logprob,
            top_k=min(logprobs, 5),
            temperature=temperature,
        )

        # Convert to dict format (legacy API format)
        alternatives_dict = {alt["token"]: alt["logprob"]
                             for alt in alternatives_data}
        # Include the selected token
        alternatives_dict[token] = token_logprob

        top_logprobs_list.append(alternatives_dict)

    return LogProbs(
        tokens=tokens,
        token_logprobs=token_logprobs,
        top_logprobs=top_logprobs_list,
        text_offset=text_offset,
    )
