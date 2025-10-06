"""
Example usage of the context validator module.

This script demonstrates:
1. Basic context length validation
2. Multi-modal token handling
3. Remaining budget calculation
4. Error handling
"""

from fakeai.context_validator import (
    calculate_remaining_budget,
    create_context_length_error,
    get_model_context_window,
    validate_context_length,
)


def example_basic_validation():
    """Example: Basic validation for chat completion."""
    print("=" * 60)
    print("EXAMPLE 1: Basic Validation")
    print("=" * 60)

    model = "gpt-4"
    prompt_tokens = 4000
    max_tokens = 2000

    is_valid, error = validate_context_length(
        model=model,
        prompt_tokens=prompt_tokens,
        max_tokens=max_tokens,
    )

    print(f"Model: {model}")
    print(f"Context Window: {get_model_context_window(model)}")
    print(f"Prompt Tokens: {prompt_tokens}")
    print(f"Max Tokens: {max_tokens}")
    print(f"Total: {prompt_tokens + max_tokens}")
    print(f"Valid: {is_valid}")
    if error:
        print(f"Error: {error}")
    print()


def example_exceeds_context():
    """Example: Request exceeds context window."""
    print("=" * 60)
    print("EXAMPLE 2: Exceeding Context Window")
    print("=" * 60)

    model = "gpt-4"
    prompt_tokens = 7000
    max_tokens = 2000

    is_valid, error = validate_context_length(
        model=model,
        prompt_tokens=prompt_tokens,
        max_tokens=max_tokens,
    )

    print(f"Model: {model}")
    print(f"Context Window: {get_model_context_window(model)}")
    print(f"Prompt Tokens: {prompt_tokens}")
    print(f"Max Tokens: {max_tokens}")
    print(f"Total: {prompt_tokens + max_tokens}")
    print(f"Valid: {is_valid}")
    if error:
        print(f"Error: {error}")
        print("\nFormatted Error Response:")
        error_response = create_context_length_error(error)
        import json

        print(json.dumps(error_response, indent=2))
    print()


def example_multi_modal():
    """Example: Multi-modal content with images and video."""
    print("=" * 60)
    print("EXAMPLE 3: Multi-Modal Content")
    print("=" * 60)

    model = "gpt-4"
    text_tokens = 3000
    image_tokens = 2000  # From vision processing
    video_tokens = 1500  # From video processing
    audio_tokens = 500  # From audio transcription
    max_tokens = 2000

    is_valid, error = validate_context_length(
        model=model,
        prompt_tokens=text_tokens,
        max_tokens=max_tokens,
        image_tokens=image_tokens,
        audio_tokens=audio_tokens,
        video_tokens=video_tokens,
    )

    total_prompt = text_tokens + image_tokens + audio_tokens + video_tokens
    print(f"Model: {model}")
    print(f"Context Window: {get_model_context_window(model)}")
    print(f"Text Tokens: {text_tokens}")
    print(f"Image Tokens: {image_tokens}")
    print(f"Audio Tokens: {audio_tokens}")
    print(f"Video Tokens: {video_tokens}")
    print(f"Total Prompt Tokens: {total_prompt}")
    print(f"Max Tokens: {max_tokens}")
    print(f"Grand Total: {total_prompt + max_tokens}")
    print(f"Valid: {is_valid}")
    if error:
        print(f"Error: {error}")
    print()


def example_remaining_budget():
    """Example: Calculate remaining token budget."""
    print("=" * 60)
    print("EXAMPLE 4: Remaining Token Budget")
    print("=" * 60)

    models = [
        ("gpt-4", 4000),
        ("gpt-4-turbo", 50000),
        ("gpt-oss-120b", 80000),
        ("meta-llama/Llama-3.1-70B-Instruct", 100000),
    ]

    for model, prompt_tokens in models:
        context_window = get_model_context_window(model)
        remaining = calculate_remaining_budget(
            model=model,
            prompt_tokens=prompt_tokens,
            reserved_tokens=1000,
        )
        percentage_used = (prompt_tokens / context_window) * 100

        print(f"\nModel: {model}")
        print(f"  Context Window: {context_window:,}")
        print(f"  Prompt Tokens: {prompt_tokens:,}")
        print(f"  Reserved: 1,000")
        print(f"  Remaining Budget: {remaining:,}")
        print(f"  Context Used: {percentage_used:.1f}%")


def example_fine_tuned_models():
    """Example: Fine-tuned models use base model context window."""
    print("=" * 60)
    print("EXAMPLE 5: Fine-Tuned Models")
    print("=" * 60)

    fine_tuned_models = [
        "ft:gpt-4:my-org::abc123",
        "ft:gpt-oss-120b:acme::xyz789",
        "ft:openai/gpt-oss-20b:company::model123",
    ]

    for model in fine_tuned_models:
        context_window = get_model_context_window(model)
        print(f"\nModel: {model}")
        print(f"  Context Window: {context_window:,}")

        # Validate with large prompt
        is_valid, error = validate_context_length(
            model=model,
            prompt_tokens=context_window - 1000,
            max_tokens=500,
        )
        print(
            f"  Can use {context_window - 1000:,} prompt + 500 completion: {is_valid}"
        )


def example_edge_cases():
    """Example: Edge cases and special scenarios."""
    print("=" * 60)
    print("EXAMPLE 6: Edge Cases")
    print("=" * 60)

    # Case 1: Unknown model uses default
    print("\n1. Unknown model (uses default):")
    model = "custom-model-2024"
    print(f"   Model: {model}")
    print(f"   Context Window: {get_model_context_window(model)}")

    # Case 2: None max_tokens (prompt-only validation)
    print("\n2. No max_tokens specified:")
    is_valid, error = validate_context_length(
        model="gpt-4",
        prompt_tokens=7000,
        max_tokens=None,
    )
    print(f"   Prompt: 7,000 tokens, max_tokens=None")
    print(f"   Valid: {is_valid}")

    # Case 3: Zero tokens
    print("\n3. Zero tokens:")
    is_valid, error = validate_context_length(
        model="gpt-4",
        prompt_tokens=0,
        max_tokens=0,
    )
    print(f"   Prompt: 0 tokens, max_tokens=0")
    print(f"   Valid: {is_valid}")

    # Case 4: Exact limit
    print("\n4. Exact context limit:")
    is_valid, error = validate_context_length(
        model="gpt-4",
        prompt_tokens=8192,
        max_tokens=0,
    )
    print(f"   Prompt: 8,192 tokens (exact limit)")
    print(f"   Valid: {is_valid}")

    # Case 5: One token over
    print("\n5. One token over limit:")
    is_valid, error = validate_context_length(
        model="gpt-4",
        prompt_tokens=8193,
        max_tokens=0,
    )
    print(f"   Prompt: 8,193 tokens (one over)")
    print(f"   Valid: {is_valid}")
    print()


def main():
    """Run all examples."""
    print("\n")
    print("*" * 60)
    print("CONTEXT VALIDATOR EXAMPLES")
    print("*" * 60)
    print("\n")

    example_basic_validation()
    example_exceeds_context()
    example_multi_modal()
    example_remaining_budget()
    example_fine_tuned_models()
    example_edge_cases()

    print("=" * 60)
    print("All examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
