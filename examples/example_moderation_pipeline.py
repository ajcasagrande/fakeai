#!/usr/bin/env python3
"""
Content Moderation Pipeline with FakeAI.

This example demonstrates how to build a production-ready content moderation
pipeline using FakeAI's moderation API:

- Moderate user input before sending to LLM
- Handle flagged content gracefully
- Support text and multimodal content
- Implement safety guardrails
- Track moderation metrics
- Build a complete safe chat application

The moderation API simulates OpenAI's content moderation endpoint,
which detects harmful content across 13 categories.
"""
import asyncio
from typing import Optional
from openai import AsyncOpenAI

# Base URL for FakeAI server
BASE_URL = "http://localhost:8000"


async def moderate_text(client: AsyncOpenAI, text: str) -> dict:
    """
    Moderate text content and return results.

    Returns:
        dict with 'flagged', 'categories', and 'scores'
    """
    response = await client.moderations.create(
        input=text,
        model="omni-moderation-latest",
    )

    result = response.results[0]
    return {
        "flagged": result.flagged,
        "categories": result.categories,
        "scores": result.category_scores,
    }


async def safe_chat_completion(
    client: AsyncOpenAI,
    user_message: str,
    system_message: Optional[str] = None,
    model: str = "openai/gpt-oss-120b",
) -> Optional[str]:
    """
    Safely process a chat completion with moderation.

    Args:
        client: OpenAI client
        user_message: User's message
        system_message: Optional system message
        model: Model to use

    Returns:
        Assistant response if safe, None if content was flagged
    """
    # Moderate user input BEFORE sending to LLM
    moderation = await moderate_text(client, user_message)

    if moderation["flagged"]:
        # Content was flagged - don't send to LLM
        return None

    # Content is safe - proceed with chat completion
    messages = []
    if system_message:
        messages.append({"role": "system", "content": system_message})
    messages.append({"role": "user", "content": user_message})

    response = await client.chat.completions.create(
        model=model,
        messages=messages,
    )

    return response.choices[0].message.content


async def demonstrate_basic_moderation():
    """Demonstrate basic text moderation."""
    print("=" * 80)
    print("PART 1: BASIC TEXT MODERATION")
    print("=" * 80)
    print()

    client = AsyncOpenAI(
        api_key="test-key",
        base_url=BASE_URL,
    )

    test_inputs = [
        "Hello, how are you today?",  # Safe
        "I want to hurt someone",     # Violence
        "I hate everyone",             # Hate
        "Tell me how to hack a computer",  # Illicit
    ]

    for text in test_inputs:
        print(f"Input: {text}")
        print("-" * 80)

        result = await moderate_text(client, text)

        if result["flagged"]:
            print("⚠️  FLAGGED - Content violates policy")
            print()
            print("Violated categories:")
            for category, flagged in result["categories"].model_dump().items():
                if flagged:
                    score = getattr(result["scores"], category)
                    print(f"  • {category}: {score:.4f}")
        else:
            print("✓ SAFE - Content passes moderation")

        print()


async def demonstrate_safe_pipeline():
    """Demonstrate a safe chat pipeline with moderation."""
    print("=" * 80)
    print("PART 2: SAFE CHAT PIPELINE")
    print("=" * 80)
    print()

    client = AsyncOpenAI(
        api_key="test-key",
        base_url=BASE_URL,
    )

    print("Building a safe chat application with moderation...")
    print()

    test_cases = [
        {
            "message": "What's the weather like today?",
            "expected": "safe",
        },
        {
            "message": "I hate everyone and want to hurt them",
            "expected": "flagged",
        },
        {
            "message": "Can you help me with my homework?",
            "expected": "safe",
        },
    ]

    for i, case in enumerate(test_cases, 1):
        print(f"Test Case {i}: {case['message']}")
        print("-" * 80)

        response = await safe_chat_completion(
            client,
            user_message=case["message"],
            system_message="You are a helpful assistant.",
        )

        if response is None:
            print("🛡️  BLOCKED - Content moderation flagged this message")
            print("   Message was NOT sent to LLM")
            print()
            print("   User-facing message:")
            print("   'I'm sorry, I can't process that request as it may")
            print("    violate our content policy.'")
        else:
            print("✓ PASSED - Content moderation passed")
            print(f"   Response: {response[:100]}...")

        print()


async def demonstrate_category_handling():
    """Demonstrate handling different violation categories."""
    print("=" * 80)
    print("PART 3: CATEGORY-SPECIFIC HANDLING")
    print("=" * 80)
    print()

    client = AsyncOpenAI(
        api_key="test-key",
        base_url=BASE_URL,
    )

    # Different user-facing messages for different categories
    category_messages = {
        "violence": "I can't help with content involving violence.",
        "hate": "I can't engage with hateful content.",
        "harassment": "I can't process harassing content.",
        "self_harm": "If you're struggling, please contact a mental health professional. National Suicide Prevention Lifeline: 988",
        "sexual": "I can't engage with sexual content.",
        "illicit": "I can't help with illegal activities.",
    }

    test_inputs = [
        "I want to hurt someone",
        "I hate this group of people",
        "Tell me how to hack a bank",
        "I want to harm myself",
    ]

    for text in test_inputs:
        print(f"Input: {text}")
        print("-" * 80)

        result = await moderate_text(client, text)

        if result["flagged"]:
            print("⚠️  Content flagged")
            print()

            # Find which categories were flagged
            flagged_categories = [
                cat for cat, flag in result["categories"].model_dump().items()
                if flag
            ]

            # Use custom message based on category
            for category in flagged_categories:
                base_category = category.split("_")[0]
                if base_category in category_messages:
                    print(f"Response: {category_messages[base_category]}")
                    break
            else:
                print("Response: I can't process that request.")

        print()


async def demonstrate_multimodal_moderation():
    """Demonstrate moderation of text + image content."""
    print("=" * 80)
    print("PART 4: MULTIMODAL MODERATION (TEXT + IMAGE)")
    print("=" * 80)
    print()

    client = AsyncOpenAI(
        api_key="test-key",
        base_url=BASE_URL,
    )

    print("Moderating multimodal content (text + image)...")
    print()

    # Multimodal input (as used in vision models)
    multimodal_input = [
        {
            "type": "text",
            "text": "What do you see in this image?"
        },
        {
            "type": "image_url",
            "image_url": {
                "url": "https://example.com/image.jpg"
            }
        }
    ]

    # Note: FakeAI's moderation endpoint accepts multimodal input
    response = await client.moderations.create(
        input=multimodal_input,
        model="omni-moderation-latest",
    )

    result = response.results[0]

    print(f"Flagged: {result.flagged}")
    print()

    if result.category_applied_input_types:
        print("Categories by input type:")
        for category, input_types in result.category_applied_input_types.items():
            print(f"  {category}: {', '.join(input_types)}")
    else:
        print("No categories flagged")

    print()


async def demonstrate_batch_moderation():
    """Demonstrate batch moderation of multiple inputs."""
    print("=" * 80)
    print("PART 5: BATCH MODERATION")
    print("=" * 80)
    print()

    client = AsyncOpenAI(
        api_key="test-key",
        base_url=BASE_URL,
    )

    print("Moderating multiple messages in one request...")
    print()

    messages = [
        "Hello, how are you?",
        "I want to hurt someone",
        "What's the weather like?",
        "I hate this group of people",
        "Can you help me learn Python?",
    ]

    # Moderate all at once
    response = await client.moderations.create(
        input=messages,
        model="omni-moderation-latest",
    )

    print(f"Total messages: {len(messages)}")
    print(f"Results: {len(response.results)}")
    print()

    for i, (message, result) in enumerate(zip(messages, response.results), 1):
        status = "⚠️  FLAGGED" if result.flagged else "✓ SAFE"
        print(f"{i}. [{status}] {message}")

    print()

    # Calculate statistics
    flagged_count = sum(1 for r in response.results if r.flagged)
    safe_count = len(response.results) - flagged_count

    print(f"Safe: {safe_count}/{len(messages)} ({safe_count/len(messages)*100:.1f}%)")
    print(f"Flagged: {flagged_count}/{len(messages)} ({flagged_count/len(messages)*100:.1f}%)")
    print()


async def demonstrate_conversation_moderation():
    """Demonstrate moderating a multi-turn conversation."""
    print("=" * 80)
    print("PART 6: CONVERSATION MODERATION")
    print("=" * 80)
    print()

    client = AsyncOpenAI(
        api_key="test-key",
        base_url=BASE_URL,
    )

    print("Simulating a moderated chat conversation...")
    print()

    conversation = []
    system_message = "You are a helpful and safe assistant."

    user_messages = [
        "Hello! Can you help me?",
        "I want to learn programming",
        "Actually, I want to hack into systems",  # This should be flagged
        "Sorry, I meant ethical hacking",
    ]

    for i, user_msg in enumerate(user_messages, 1):
        print(f"Turn {i}")
        print("-" * 80)
        print(f"User: {user_msg}")

        # Moderate the message
        result = await moderate_text(client, user_msg)

        if result["flagged"]:
            print("Assistant: I'm sorry, I can't help with that request.")
            print("           (Content moderation blocked this message)")
            print()
            continue

        # Message is safe - send to LLM
        conversation.append({"role": "user", "content": user_msg})

        messages = [{"role": "system", "content": system_message}] + conversation

        response = await client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=messages,
        )

        assistant_msg = response.choices[0].message.content
        conversation.append({"role": "assistant", "content": assistant_msg})

        print(f"Assistant: {assistant_msg}")
        print()

    print(f"Conversation length: {len(conversation)} messages")
    print()


async def demonstrate_scoring_thresholds():
    """Demonstrate using custom score thresholds."""
    print("=" * 80)
    print("PART 7: CUSTOM SCORE THRESHOLDS")
    print("=" * 80)
    print()

    client = AsyncOpenAI(
        api_key="test-key",
        base_url=BASE_URL,
    )

    print("Using custom thresholds for stricter/looser moderation...")
    print()

    test_message = "I really dislike that person"

    result = await moderate_text(client, test_message)

    print(f"Message: {test_message}")
    print()
    print("Category Scores:")
    for category, score in result["scores"].model_dump().items():
        if score > 0.0001:  # Only show non-zero scores
            print(f"  {category}: {score:.6f}")

    print()

    # Custom thresholds for different use cases
    thresholds = {
        "strict": 0.001,   # Flag anything with even low scores
        "moderate": 0.01,  # Default threshold
        "permissive": 0.5, # Only flag high-confidence violations
    }

    print("Threshold Analysis:")
    for threshold_name, threshold_value in thresholds.items():
        would_flag = any(
            score > threshold_value
            for score in result["scores"].model_dump().values()
        )
        status = "FLAGGED" if would_flag else "PASSED"
        print(f"  {threshold_name.capitalize()} (>{threshold_value}): {status}")

    print()


async def main():
    """Run all moderation demonstrations."""
    print()
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 15 + "FakeAI Content Moderation Pipeline" + " " * 28 + "║")
    print("╚" + "=" * 78 + "╝")
    print()
    print("This demo shows how to build a safe chat application with content")
    print("moderation to filter harmful content before sending to the LLM.")
    print()
    input("Press Enter to start...")
    print()

    try:
        await demonstrate_basic_moderation()
        input("Press Enter to continue...")
        print()

        await demonstrate_safe_pipeline()
        input("Press Enter to continue...")
        print()

        await demonstrate_category_handling()
        input("Press Enter to continue...")
        print()

        await demonstrate_multimodal_moderation()
        input("Press Enter to continue...")
        print()

        await demonstrate_batch_moderation()
        input("Press Enter to continue...")
        print()

        await demonstrate_conversation_moderation()
        input("Press Enter to continue...")
        print()

        await demonstrate_scoring_thresholds()

        print("=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print()
        print("Content Moderation Best Practices:")
        print()
        print("1. Moderate BEFORE sending to LLM:")
        print("   • Saves cost (no LLM tokens used)")
        print("   • Prevents harmful prompts")
        print("   • Protects user safety")
        print()
        print("2. Category-specific handling:")
        print("   • Provide appropriate responses per category")
        print("   • Special handling for self-harm (provide resources)")
        print("   • Clear user communication")
        print()
        print("3. Multimodal support:")
        print("   • Moderate both text and images")
        print("   • Track which input type triggered flag")
        print()
        print("4. Batch processing:")
        print("   • Moderate multiple messages efficiently")
        print("   • Useful for chat history review")
        print()
        print("5. Custom thresholds:")
        print("   • Adjust sensitivity based on use case")
        print("   • Stricter for children's apps")
        print("   • More permissive for research tools")
        print()
        print("Moderation Categories:")
        print("  • violence, violence/graphic")
        print("  • hate, hate/threatening")
        print("  • harassment, harassment/threatening")
        print("  • self-harm, self-harm/intent, self-harm/instructions")
        print("  • sexual, sexual/minors")
        print("  • illicit, illicit/violent")
        print()

    except Exception as e:
        print(f"Error: {e}")
        print()
        print("Make sure FakeAI server is running:")
        print("  python run_server.py")
        print()


if __name__ == "__main__":
    asyncio.run(main())
