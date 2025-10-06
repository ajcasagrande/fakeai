"""
Context length validation for FakeAI.

Validates that prompt tokens + max_tokens doesn't exceed model context windows.
"""

from typing import Any

# Model context windows (in tokens)
MODEL_CONTEXT_WINDOWS = {
    "gpt-4": 8192,
    "gpt-4-32k": 32768,
    "gpt-4-turbo": 128000,
    "gpt-oss-120b": 128000,
    "gpt-oss-20b": 32768,
    "gpt-3.5-turbo": 16385,
    "gpt-3.5-turbo-16k": 16385,
    "claude-3-opus": 200000,
    "claude-3-sonnet": 200000,
    "gemini-pro": 32768,
    "meta-llama/Llama-3.1-8B-Instruct": 131072,
    "meta-llama/Llama-3.1-70B-Instruct": 131072,
    "meta-llama/Llama-3.1-405B-Instruct": 131072,
    "deepseek-ai/DeepSeek-R1": 64000,
    "mistral-7b": 32768,
    "mixtral-8x7b": 32768,
    "default": 8192,
}


def get_model_context_window(model: str) -> int:
    """
    Get context window for a model.

    Args:
        model: Model ID (e.g., "gpt-4", "openai/gpt-oss-120b")

    Returns:
        Context window size in tokens
    """
    # Handle fine-tuned models first (format: ft:base:org::id)
    if model.startswith("ft:"):
        parts = model.split(":")
        if len(parts) >= 2:
            base_model = parts[1]
            # Recursively get context window for base model
            return get_model_context_window(base_model)

    # Try direct lookup first (handles both simple names and full paths)
    if model in MODEL_CONTEXT_WINDOWS:
        return MODEL_CONTEXT_WINDOWS[model]

    # Try with just the last part after "/" for models with prefixes
    if "/" in model:
        model_name = model.split("/")[-1]
        if model_name in MODEL_CONTEXT_WINDOWS:
            return MODEL_CONTEXT_WINDOWS[model_name]

    # Default fallback
    return MODEL_CONTEXT_WINDOWS["default"]


def validate_context_length(
    model: str,
    prompt_tokens: int,
    max_tokens: int | None,
    image_tokens: int = 0,
    audio_tokens: int = 0,
    video_tokens: int = 0,
) -> tuple[bool, str | None]:
    """
    Validate that prompt + max_tokens doesn't exceed model context window.

    Args:
        model: Model ID
        prompt_tokens: Number of tokens in the prompt/messages
        max_tokens: Maximum tokens to generate (None means model default)
        image_tokens: Number of tokens from images
        audio_tokens: Number of tokens from audio
        video_tokens: Number of tokens from video

    Returns:
        Tuple of (is_valid, error_message). error_message is None if valid.
    """
    context_window = get_model_context_window(model)

    # Calculate total input tokens (including multi-modal)
    total_prompt_tokens = prompt_tokens + image_tokens + audio_tokens + video_tokens

    # If max_tokens is None, we only validate prompt length
    if max_tokens is None:
        if total_prompt_tokens > context_window:
            return False, _format_error_message(
                model=model,
                context_window=context_window,
                prompt_tokens=total_prompt_tokens,
                completion_tokens=0,
            )
        return True, None

    # Validate prompt + completion doesn't exceed context window
    total_tokens = total_prompt_tokens + max_tokens
    if total_tokens > context_window:
        return False, _format_error_message(
            model=model,
            context_window=context_window,
            prompt_tokens=total_prompt_tokens,
            completion_tokens=max_tokens,
        )

    return True, None


def calculate_remaining_budget(
    model: str, prompt_tokens: int, reserved_tokens: int = 1000
) -> int:
    """
    Calculate how many tokens can be generated given prompt length.

    Args:
        model: Model ID
        prompt_tokens: Number of tokens in the prompt
        reserved_tokens: Safety buffer for response (default: 1000)

    Returns:
        Maximum number of tokens that can be generated
    """
    context_window = get_model_context_window(model)
    remaining = context_window - prompt_tokens - reserved_tokens
    return max(0, remaining)


def _format_error_message(
    model: str, context_window: int, prompt_tokens: int, completion_tokens: int
) -> str:
    """
    Format error message matching OpenAI's style.

    Args:
        model: Model ID
        context_window: Model's context window size
        prompt_tokens: Number of tokens in prompt
        completion_tokens: Number of tokens in completion

    Returns:
        Formatted error message
    """
    total_tokens = prompt_tokens + completion_tokens

    if completion_tokens == 0:
        return (
            f"This model's maximum context length is {context_window} tokens. "
            f"However, your messages resulted in {total_tokens} tokens. "
            f"Please reduce the length of the messages."
        )

    return (
        f"This model's maximum context length is {context_window} tokens. "
        f"However, your messages resulted in {total_tokens} tokens "
        f"({prompt_tokens} in the messages, {completion_tokens} in the completion). "
        f"Please reduce the length of the messages or completion."
    )


def create_context_length_error(error_message: str) -> dict[str, Any]:
    """
    Create OpenAI-compatible error response for context length exceeded.

    Args:
        error_message: Error message from validate_context_length

    Returns:
        Error response dict
    """
    return {
        "error": {
            "message": error_message,
            "type": "invalid_request_error",
            "param": "messages",
            "code": "context_length_exceeded",
        }
    }
