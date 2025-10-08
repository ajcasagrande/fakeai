"""
Accurate token counting using tiktoken library with fallback mechanisms.

This module provides accurate token counting for OpenAI models using the tiktoken
library. If tiktoken is not available, it falls back to a simple heuristic-based
approach for token estimation.

Key features:
- Support for multiple OpenAI tokenizer encodings (cl100k_base, p50k_base, r50k_base)
- Model-specific tokenizer selection
- LRU caching for performance optimization
- Thread-safe operation
- Graceful degradation when tiktoken is unavailable
- Backward compatible with existing calculate_token_count()
"""

#  SPDX-License-Identifier: Apache-2.0

from functools import lru_cache

# Try to import tiktoken, but don't fail if it's not available
try:
    import tiktoken

    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False


# Model to encoding mappings
# Based on OpenAI's official model documentation
MODEL_TO_ENCODING = {
    # GPT-4 models (cl100k_base)
    "gpt-4": "cl100k_base",
    "gpt-4-0314": "cl100k_base",
    "gpt-4-0613": "cl100k_base",
    "gpt-4-32k": "cl100k_base",
    "gpt-4-32k-0314": "cl100k_base",
    "gpt-4-32k-0613": "cl100k_base",
    "gpt-4-turbo": "cl100k_base",
    "gpt-4-turbo-preview": "cl100k_base",
    "gpt-4-1106-preview": "cl100k_base",
    "gpt-4-0125-preview": "cl100k_base",
    "gpt-4-vision-preview": "cl100k_base",
    "gpt-4o": "cl100k_base",
    "gpt-4o-mini": "cl100k_base",
    # GPT-OSS models (cl100k_base - FakeAI-specific)
    "gpt-oss-120b": "cl100k_base",
    "gpt-oss-20b": "cl100k_base",
    "openai/gpt-oss-120b": "cl100k_base",
    "openai/gpt-oss-20b": "cl100k_base",
    # GPT-3.5 models (cl100k_base)
    "gpt-3.5-turbo": "cl100k_base",
    "gpt-3.5-turbo-0301": "cl100k_base",
    "gpt-3.5-turbo-0613": "cl100k_base",
    "gpt-3.5-turbo-16k": "cl100k_base",
    "gpt-3.5-turbo-16k-0613": "cl100k_base",
    "gpt-3.5-turbo-1106": "cl100k_base",
    "gpt-3.5-turbo-0125": "cl100k_base",
    # GPT-3 text models (p50k_base)
    "text-davinci-003": "p50k_base",
    "text-davinci-002": "p50k_base",
    "text-davinci-001": "p50k_base",
    "text-curie-001": "p50k_base",
    "text-babbage-001": "p50k_base",
    "text-ada-001": "p50k_base",
    # Code models (p50k_base)
    "code-davinci-002": "p50k_base",
    "code-davinci-001": "p50k_base",
    "code-cushman-002": "p50k_base",
    "code-cushman-001": "p50k_base",
    # Embedding models
    "text-embedding-ada-002": "cl100k_base",
    "text-embedding-3-small": "cl100k_base",
    "text-embedding-3-large": "cl100k_base",
}


@lru_cache(maxsize=128)
def _get_encoding_cached(encoding_name: str):
    """
    Get a tiktoken encoding with caching.

    This is cached to avoid repeatedly loading the same encoding,
    which can be expensive.

    Args:
        encoding_name: Name of the encoding (cl100k_base, p50k_base, etc.)

    Returns:
        tiktoken.Encoding instance

    Raises:
        ValueError: If encoding_name is invalid
    """
    if not TIKTOKEN_AVAILABLE:
        raise RuntimeError("tiktoken library is not available")

    try:
        return tiktoken.get_encoding(encoding_name)
    except Exception as e:
        raise ValueError(f"Invalid encoding name: {encoding_name}") from e


def _infer_encoding_from_model(model: str) -> str:
    """
    Infer the appropriate encoding for a model.

    Uses pattern matching and model prefixes to determine the encoding
    when the exact model name is not in the mapping.

    Args:
        model: Model name or identifier

    Returns:
        Encoding name (cl100k_base, p50k_base, or r50k_base)
    """
    # Normalize model name (remove org prefix if present)
    normalized = model.lower()

    # Check exact match first
    if normalized in MODEL_TO_ENCODING:
        return MODEL_TO_ENCODING[normalized]

    # Check for fine-tuned models (format: ft:base_model:org::id)
    if normalized.startswith("ft:"):
        parts = normalized.split(":")
        if len(parts) >= 2:
            base_model = parts[1]
            # Recursively check base model
            if base_model in MODEL_TO_ENCODING:
                return MODEL_TO_ENCODING[base_model]

    # Pattern matching for model families
    if any(
        pattern in normalized
        for pattern in ["gpt-4", "gpt-oss", "gpt-3.5-turbo", "text-embedding"]
    ):
        return "cl100k_base"
    elif any(
        pattern in normalized
        for pattern in [
            "text-davinci",
            "text-curie",
            "text-babbage",
            "text-ada",
            "code-",
        ]
    ):
        return "p50k_base"
    elif "codex" in normalized:
        return "p50k_base"

    # Default to cl100k_base (most common for modern models)
    return "cl100k_base"


def get_tokenizer_for_model(model: str):
    """
    Get the appropriate tokenizer for a model.

    Returns a tiktoken Encoding object configured for the specified model.
    Uses caching to avoid repeated loading of the same tokenizer.

    Args:
        model: Model name (e.g., "gpt-4", "gpt-3.5-turbo", "text-davinci-003")

    Returns:
        tiktoken.Encoding instance for the model

    Raises:
        RuntimeError: If tiktoken is not available
        ValueError: If the encoding cannot be loaded

    Example:
        >>> tokenizer = get_tokenizer_for_model("gpt-4")
        >>> tokens = tokenizer.encode("Hello, world!")
    """
    if not TIKTOKEN_AVAILABLE:
        raise RuntimeError(
            "tiktoken library is not available. Install with: pip install tiktoken"
        )

    encoding_name = _infer_encoding_from_model(model)
    return _get_encoding_cached(encoding_name)


@lru_cache(maxsize=1024)
def get_token_count(text: str, model: str = "gpt-4") -> int:
    """
    Get accurate token count for text using tiktoken.

    This is the main entry point for token counting. It uses tiktoken when
    available for accurate counting, and falls back to a heuristic method
    when tiktoken is not installed.

    The function is cached with an LRU cache of 1024 entries for performance.

    Args:
        text: The text to count tokens for
        model: Model name to determine which tokenizer to use (default: "gpt-4")

    Returns:
        Number of tokens in the text

    Example:
        >>> count = get_token_count("Hello, world!", model="gpt-4")
        >>> print(count)
        4
    """
    if not text:
        return 0

    if TIKTOKEN_AVAILABLE:
        try:
            tokenizer = get_tokenizer_for_model(model)
            return len(tokenizer.encode(text))
        except Exception:
            # Fall back to heuristic if anything goes wrong
            pass

    # Fallback heuristic when tiktoken is not available
    return _heuristic_token_count(text)


def _heuristic_token_count(text: str) -> int:
    """
    Simple heuristic-based token counting.

    This is used as a fallback when tiktoken is not available.
    Provides a reasonable approximation based on word and punctuation counts.

    Args:
        text: The text to count tokens for

    Returns:
        Estimated number of tokens
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


@lru_cache(maxsize=1024)
def tokenize_text_accurate(text: str, model: str = "gpt-4") -> list[int]:
    """
    Return token IDs for text using tiktoken.

    Converts text into a list of token IDs as defined by the model's tokenizer.
    This is useful for advanced use cases like prefix matching, cache keys, etc.

    Args:
        text: The text to tokenize
        model: Model name to determine which tokenizer to use (default: "gpt-4")

    Returns:
        List of token IDs (integers)

    Raises:
        RuntimeError: If tiktoken is not available

    Example:
        >>> tokens = tokenize_text_accurate("Hello, world!", model="gpt-4")
        >>> print(tokens)
        [9906, 11, 1917, 0]
    """
    if not TIKTOKEN_AVAILABLE:
        raise RuntimeError(
            "tiktoken library is not available. Install with: pip install tiktoken"
        )

    if not text:
        return []

    tokenizer = get_tokenizer_for_model(model)
    return tokenizer.encode(text)


def batch_token_count(texts: list[str], model: str = "gpt-4") -> list[int]:
    """
    Get token counts for multiple texts efficiently.

    Uses caching to optimize performance when counting tokens for multiple texts.

    Args:
        texts: List of texts to count tokens for
        model: Model name to determine which tokenizer to use (default: "gpt-4")

    Returns:
        List of token counts corresponding to each input text

    Example:
        >>> texts = ["Hello", "Hello, world!", "How are you?"]
        >>> counts = batch_token_count(texts, model="gpt-4")
        >>> print(counts)
        [1, 4, 4]
    """
    return [get_token_count(text, model) for text in texts]


def estimate_tokens_from_messages(
        messages: list[dict],
        model: str = "gpt-4") -> int:
    """
    Estimate token count for a list of chat messages.

    Takes into account the overhead of message formatting in the chat completion API.
    This includes role tokens, separator tokens, and message framing.

    Args:
        messages: List of message dictionaries with 'role' and 'content' keys
        model: Model name to determine which tokenizer to use (default: "gpt-4")

    Returns:
        Estimated total token count for the messages

    Example:
        >>> messages = [
        ...     {"role": "system", "content": "You are a helpful assistant."},
        ...     {"role": "user", "content": "Hello!"}
        ... ]
        >>> count = estimate_tokens_from_messages(messages, model="gpt-4")
    """
    if not messages:
        return 0

    total_tokens = 0

    # Each message has overhead for formatting
    # Format: <|im_start|>role\ncontent<|im_end|>\n
    # This is approximately 4 tokens per message in cl100k_base
    tokens_per_message = 4
    tokens_per_name = 1  # If name field is present

    for message in messages:
        total_tokens += tokens_per_message

        # Count role tokens (usually included in message overhead)
        role = message.get("role", "")
        if role:
            total_tokens += get_token_count(role, model)

        # Count content tokens
        content = message.get("content", "")
        if content:
            if isinstance(content, str):
                total_tokens += get_token_count(content, model)
            elif isinstance(content, list):
                # Multi-modal content (text + images/video)
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "text":
                        text_content = part.get("text", "")
                        total_tokens += get_token_count(text_content, model)

        # Count name tokens if present
        if "name" in message:
            total_tokens += tokens_per_name
            total_tokens += get_token_count(message["name"], model)

    # Add overhead for priming the assistant's response
    total_tokens += 3  # <|im_start|>assistant\n

    return total_tokens


def get_encoding_name_for_model(model: str) -> str:
    """
    Get the encoding name used by a model.

    Useful for debugging or understanding which tokenizer is being used.

    Args:
        model: Model name

    Returns:
        Encoding name (e.g., "cl100k_base", "p50k_base", "r50k_base")

    Example:
        >>> encoding = get_encoding_name_for_model("gpt-4")
        >>> print(encoding)
        "cl100k_base"
    """
    return _infer_encoding_from_model(model)


def is_tiktoken_available() -> bool:
    """
    Check if tiktoken library is available.

    Returns:
        True if tiktoken is installed and available, False otherwise

    Example:
        >>> if is_tiktoken_available():
        ...     print("Using accurate tiktoken-based counting")
        ... else:
        ...     print("Using heuristic fallback")
    """
    return TIKTOKEN_AVAILABLE


def calculate_token_count(text: str) -> int:
    """
    Calculate token count for the given text using tiktoken.

    Args:
        text: The text to count tokens for

    Returns:
        Number of tokens in the text
    """
    if not text:
        return 0

    return get_token_count(text, model="gpt-4")
