"""
Complete integration snippet for fakeai_service.py

This file shows the exact code to add to each method in fakeai_service.py
to integrate context length validation.
"""

# ============================================================================
# IMPORTS (Add to top of fakeai_service.py)
# ============================================================================

from fakeai.context_validator import (
    create_context_length_error,
    validate_context_length,
)

# ============================================================================
# INTEGRATION 1: create_chat_completion()
# Insert after line 1571 (after calculating prompt_tokens)
# ============================================================================


def integration_chat_completion():
    """
    Add this validation block in create_chat_completion() after:
        prompt_tokens = text_tokens + input_image_tokens + input_video_tokens + input_audio_tokens
    """

    # Example context (this would be from the actual method):
    request_model = "gpt-4"
    text_tokens = 4000
    input_image_tokens = 1000
    input_audio_tokens = 500
    input_video_tokens = 500
    request_max_tokens = 2000

    # ===== ADD THIS VALIDATION BLOCK =====
    # Validate context length before proceeding
    is_valid, error_message = validate_context_length(
        model=request_model,
        prompt_tokens=text_tokens,
        max_tokens=request_max_tokens,
        image_tokens=input_image_tokens,
        audio_tokens=input_audio_tokens,
        video_tokens=input_video_tokens,
    )

    if not is_valid:
        from fastapi import HTTPException

        error_response = create_context_length_error(error_message)
        raise HTTPException(
            status_code=400,
            detail=error_response,
        )
    # ===== END VALIDATION BLOCK =====

    # Continue with existing code...


# ============================================================================
# INTEGRATION 2: create_chat_completion_stream()
# Insert after calculating prompt_tokens and multi-modal tokens
# ============================================================================


def integration_chat_completion_stream():
    """
    Add this validation block in create_chat_completion_stream() after
    calculating all token counts.
    """

    # Example context:
    request_model = "gpt-4"
    prompt_text = "Example prompt"
    request_max_tokens = 2000

    # ===== ADD THIS SECTION =====
    # Calculate all token types
    from fakeai.utils import calculate_token_count

    text_tokens = calculate_token_count(prompt_text)

    # Calculate multi-modal tokens (example - adjust based on actual messages)
    input_image_tokens = 0
    # for msg in request.messages:
    #     if msg.content:
    #         input_image_tokens += calculate_message_image_tokens(msg.content, request.model)

    input_video_tokens = 0
    # for msg in request.messages:
    #     if msg.content:
    #         input_video_tokens += calculate_message_video_tokens(msg.content, request.model)

    input_audio_tokens = 0
    # input_audio_tokens, _ = self._process_audio_input(request.messages)

    # Validate context length
    is_valid, error_message = validate_context_length(
        model=request_model,
        prompt_tokens=text_tokens,
        max_tokens=request_max_tokens,
        image_tokens=input_image_tokens,
        audio_tokens=input_audio_tokens,
        video_tokens=input_video_tokens,
    )

    if not is_valid:
        from fastapi import HTTPException

        error_response = create_context_length_error(error_message)
        raise HTTPException(
            status_code=400,
            detail=error_response,
        )
    # ===== END VALIDATION SECTION =====


# ============================================================================
# INTEGRATION 3: create_completion()
# Insert after calculating prompt_tokens (line ~2177)
# ============================================================================


def integration_completion():
    """
    Add this validation block in create_completion() after:
        prompt_tokens = calculate_token_count(prompt_text)
    """

    # Example context:
    request_model = "gpt-4"
    prompt_tokens = 5000
    request_max_tokens = 2000

    # ===== ADD THIS VALIDATION BLOCK =====
    # Validate context length
    is_valid, error_message = validate_context_length(
        model=request_model,
        prompt_tokens=prompt_tokens,
        max_tokens=request_max_tokens,
    )

    if not is_valid:
        from fastapi import HTTPException

        error_response = create_context_length_error(error_message)
        raise HTTPException(
            status_code=400,
            detail=error_response,
        )
    # ===== END VALIDATION BLOCK =====


# ============================================================================
# INTEGRATION 4: create_completion_stream()
# Insert after calculating prompt_tokens (line ~2232)
# ============================================================================


def integration_completion_stream():
    """
    Add this validation block in create_completion_stream() after
    processing prompt.
    """

    # Example context:
    request_model = "gpt-4"
    prompt_text = "Example prompt"
    request_max_tokens = 2000

    # ===== ADD THIS VALIDATION BLOCK =====
    from fakeai.utils import calculate_token_count

    prompt_tokens = calculate_token_count(prompt_text)

    # Validate context length
    is_valid, error_message = validate_context_length(
        model=request_model,
        prompt_tokens=prompt_tokens,
        max_tokens=request_max_tokens,
    )

    if not is_valid:
        from fastapi import HTTPException

        error_response = create_context_length_error(error_message)
        raise HTTPException(
            status_code=400,
            detail=error_response,
        )
    # ===== END VALIDATION BLOCK =====


# ============================================================================
# TESTING THE INTEGRATION
# ============================================================================


def test_integration():
    """
    Test the integration with realistic scenarios.
    """
    print("Testing Context Validator Integration\n")
    print("=" * 60)

    # Test 1: Valid request
    print("\nTest 1: Valid request")
    try:
        is_valid, error = validate_context_length(
            model="gpt-4",
            prompt_tokens=4000,
            max_tokens=2000,
        )
        print(f"✓ Valid request passed: {is_valid}")
    except Exception as e:
        print(f"✗ Error: {e}")

    # Test 2: Invalid request (exceeds context)
    print("\nTest 2: Invalid request (should fail)")
    try:
        is_valid, error = validate_context_length(
            model="gpt-4",
            prompt_tokens=7000,
            max_tokens=2000,
        )
        if not is_valid:
            from fastapi import HTTPException

            error_response = create_context_length_error(error)
            print(f"✓ Properly detected overflow")
            print(f"  Error code: {error_response['error']['code']}")
            print(f"  Message: {error_response['error']['message'][:80]}...")
    except HTTPException as e:
        print(f"✓ HTTPException raised correctly: {e.status_code}")

    # Test 3: Multi-modal request
    print("\nTest 3: Multi-modal request")
    try:
        is_valid, error = validate_context_length(
            model="gpt-4-turbo",
            prompt_tokens=50000,
            max_tokens=10000,
            image_tokens=20000,
            video_tokens=10000,
        )
        print(f"✓ Multi-modal validation: {is_valid}")
    except Exception as e:
        print(f"✗ Error: {e}")

    # Test 4: Fine-tuned model
    print("\nTest 4: Fine-tuned model")
    try:
        from fakeai.context_validator import get_model_context_window

        window = get_model_context_window("ft:gpt-oss-120b:org::id")
        print(f"✓ Fine-tuned model context: {window:,} tokens")
    except Exception as e:
        print(f"✗ Error: {e}")

    print("\n" + "=" * 60)
    print("Integration tests complete!")


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print(__doc__)
    test_integration()
