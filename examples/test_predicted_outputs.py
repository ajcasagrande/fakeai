#!/usr/bin/env python3
"""
Example demonstrating EAGLE/Predicted Outputs support in FakeAI.

Predicted Outputs (speculative decoding) provides 3-5× speedup for GPT-4o models
by accepting a prediction of what the output might be and using it to accelerate
generation.

Ideal for: document editing, code refactoring, translation updates.
"""
import asyncio
from fakeai import AppConfig
from fakeai.fakeai_service import FakeAIService
from fakeai.models import ChatCompletionRequest, Message, Role, PredictionContent


async def test_without_prediction():
    """Test regular request without prediction."""
    print("=" * 70)
    print("TEST 1: WITHOUT PREDICTION (Standard Generation)")
    print("=" * 70)
    print()

    config = AppConfig(response_delay=0.0)
    service = FakeAIService(config)

    request = ChatCompletionRequest(
        model="openai/gpt-oss-120b",
        messages=[Message(role=Role.USER, content="Refactor this code to use list comprehension")],
    )

    response = await service.create_chat_completion(request)

    print(f"Model: {response.model}")
    print(f"Response: {response.choices[0].message.content[:100]}...")
    print()
    print("Token usage:")
    print(f"  Completion tokens: {response.usage.completion_tokens}")
    if response.usage.completion_tokens_details:
        details = response.usage.completion_tokens_details
        print(f"  Accepted prediction tokens: {details.accepted_prediction_tokens}")
        print(f"  Rejected prediction tokens: {details.rejected_prediction_tokens}")
    print()


async def test_with_good_prediction():
    """Test with a good prediction (high similarity)."""
    print("=" * 70)
    print("TEST 2: WITH GOOD PREDICTION (High Similarity)")
    print("=" * 70)
    print()

    config = AppConfig(response_delay=0.0)
    service = FakeAIService(config)

    original_code = """
for item in items:
    result.append(item.upper())
"""

    # Prediction that's very similar to what model might generate
    prediction_text = "result = [item.upper() for item in items]"

    request = ChatCompletionRequest(
        model="openai/gpt-oss-120b",
        messages=[Message(role=Role.USER, content=f"Refactor this code: {original_code}")],
        prediction=PredictionContent(
            type="content",
            content=prediction_text
        )
    )

    response = await service.create_chat_completion(request)

    print(f"Model: {response.model}")
    print(f"Prediction provided: '{prediction_text}'")
    print(f"Actual response: '{response.choices[0].message.content[:100]}...'")
    print()
    print("Token usage:")
    print(f"  Completion tokens: {response.usage.completion_tokens}")
    if response.usage.completion_tokens_details:
        details = response.usage.completion_tokens_details
        print(f"  Accepted prediction tokens: {details.accepted_prediction_tokens}")
        print(f"  Rejected prediction tokens: {details.rejected_prediction_tokens}")

        if details.accepted_prediction_tokens + details.rejected_prediction_tokens > 0:
            acceptance_rate = (details.accepted_prediction_tokens /
                             (details.accepted_prediction_tokens + details.rejected_prediction_tokens))
            print(f"  Acceptance rate: {acceptance_rate:.1%}")
    print()


async def test_with_poor_prediction():
    """Test with a poor prediction (low similarity)."""
    print("=" * 70)
    print("TEST 3: WITH POOR PREDICTION (Low Similarity)")
    print("=" * 70)
    print()

    config = AppConfig(response_delay=0.0)
    service = FakeAIService(config)

    # Prediction that's completely unrelated
    prediction_text = "The weather is sunny today and I like pizza."

    request = ChatCompletionRequest(
        model="openai/gpt-oss-120b",
        messages=[Message(role=Role.USER, content="Explain quantum computing")],
        prediction=PredictionContent(
            type="content",
            content=prediction_text
        )
    )

    response = await service.create_chat_completion(request)

    print(f"Model: {response.model}")
    print(f"Prediction provided: '{prediction_text}'")
    print(f"Actual response: '{response.choices[0].message.content[:100]}...'")
    print()
    print("Token usage:")
    print(f"  Completion tokens: {response.usage.completion_tokens}")
    if response.usage.completion_tokens_details:
        details = response.usage.completion_tokens_details
        print(f"  Accepted prediction tokens: {details.accepted_prediction_tokens}")
        print(f"  Rejected prediction tokens: {details.rejected_prediction_tokens}")

        if details.accepted_prediction_tokens + details.rejected_prediction_tokens > 0:
            acceptance_rate = (details.accepted_prediction_tokens /
                             (details.accepted_prediction_tokens + details.rejected_prediction_tokens))
            print(f"  Acceptance rate: {acceptance_rate:.1%}")
    print()


async def main_all():
    """Run all tests."""
    await test_without_prediction()
    await test_with_good_prediction()
    await test_with_poor_prediction()

    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print()
    print("Predicted Outputs (EAGLE Speculative Decoding):")
    print("  • Supported on GPT-4o models only")
    print("  • Provide prediction via 'prediction' field")
    print("  • 3-5× speedup for good predictions")
    print("  • Tracks accepted_prediction_tokens and rejected_prediction_tokens")
    print("  • Acceptance rate: 60-80% typical for good predictions")
    print()
    print("Use cases:")
    print("  • Document editing (provide original as prediction)")
    print("  • Code refactoring (provide original code as prediction)")
    print("  • Translation updates (provide previous translation)")
    print("  • Iterative improvements")
    print()


if __name__ == "__main__":
    asyncio.run(main_all())
