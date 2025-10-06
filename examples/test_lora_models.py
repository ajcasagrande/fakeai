#!/usr/bin/env python3
"""
Example demonstrating LoRA fine-tuned model support in FakeAI.

LoRA (Low-Rank Adaptation) models use the naming convention:
ft:base-model:organization::unique-id

Examples:
- ft:openai/gpt-oss-20b-2024-07-18:my-org::A7NZtdgI
- ft:meta-llama/Llama-3.1-8B-Instruct:custom::adapter-123
"""
import asyncio

from fakeai import AppConfig
from fakeai.fakeai_service import FakeAIService
from fakeai.models import ChatCompletionRequest, Message, Role


async def main():
    print("=" * 70)
    print("LoRA FINE-TUNED MODEL SUPPORT")
    print("=" * 70)
    print()

    config = AppConfig(response_delay=0.0)
    service = FakeAIService(config)

    # Test with LoRA fine-tuned model
    fine_tuned_model = "ft:openai/gpt-oss-20b-2024-07-18:my-org::A7NZtdgI"

    request = ChatCompletionRequest(
        model=fine_tuned_model,
        messages=[Message(role=Role.USER, content="Hello from fine-tuned model!")],
    )

    response = await service.create_chat_completion(request)

    print(f"Model ID: {response.model}")
    print(f"Response: {response.choices[0].message.content}")
    print()

    # Check model details
    model_details = await service.get_model(fine_tuned_model)
    print("Model Details:")
    print(f"  ID: {model_details.id}")
    print(f"  Owned by: {model_details.owned_by}")
    print(f"  Root (base model): {model_details.root}")
    print(f"  Parent: {model_details.parent}")
    print()

    # Test another fine-tuned model with different organization
    another_model = "ft:meta-llama/Llama-3.1-8B-Instruct:acme-corp::custom-adapter"

    request2 = ChatCompletionRequest(
        model=another_model,
        messages=[Message(role=Role.USER, content="Test message")],
    )

    response2 = await service.create_chat_completion(request2)
    model_details2 = await service.get_model(another_model)

    print(f"Second Model: {another_model}")
    print(f"  Owned by: {model_details2.owned_by}")
    print(f"  Base model: {model_details2.root}")
    print()

    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print()
    print("LoRA Fine-Tuned Model Naming Convention:")
    print("  ft:base-model:organization::unique-id")
    print()
    print("Parsing:")
    print("  • base-model → stored in 'root' and 'parent' fields")
    print("  • organization → stored in 'owned_by' field")
    print("  • Auto-created on first use via _ensure_model_exists()")
    print()
    print("Token counting:")
    print("  • No difference from base model")
    print("  • LoRA adapters merged at inference time")
    print("  • Zero latency overhead")
    print()


if __name__ == "__main__":
    asyncio.run(main())
