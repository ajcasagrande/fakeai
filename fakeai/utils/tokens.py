"""
Token counting and text tokenization utilities.

This module provides functions for splitting text into token-equivalent chunks
and calculating approximate token counts for text strings.
"""

#  SPDX-License-Identifier: Apache-2.0

import re
from functools import lru_cache


def tokenize_text(text: str) -> list[str]:
    """
    Split text into token-equivalent chunks.

    Each token is approximately:
    - A word (e.g., "hello")
    - A punctuation mark (e.g., ".", ",")
    - A word with attached punctuation (e.g., "hello,")

    This mimics how actual tokenizers work, where punctuation
    is often separated as individual tokens.
    """
    if not text:
        return []

    # Split on word boundaries while keeping punctuation separate
    # This regex splits on spaces but also separates punctuation
    pattern = r"\b\w+\b|[^\w\s]"
    tokens = re.findall(pattern, text)
    return tokens


@lru_cache(maxsize=256)
def _cached_token_count(text: str) -> int:
    """
    Cached implementation of token counting.

    This internal function is cached to avoid recomputing token counts
    for repeated text strings.
    """
    if not text:
        return 0

    # Count words (space-separated tokens)
    word_count = len(text.split())

    # Count punctuation and special characters (roughly one token each)
    punctuation_count = sum(
        1 for char in text if char in ".,;:!?()[]{}<>\"'`~@#$%^&*-+=|/\\"
    )

    # Estimate final token count
    return max(1, word_count + punctuation_count)


def calculate_token_count(text: str) -> int:
    """
    Calculate an approximate token count for the given text.

    This is a simplified estimation based on the observation that
    tokens are roughly 4 characters on average in English text.

    Performance: Uses LRU caching for repeated text strings to reduce
    redundant calculations.
    """
    if not text:
        return 0

    # Use cached implementation for performance
    return _cached_token_count(text)
