#!/usr/bin/env python3
"""
Reasoning Model Workflow with FakeAI.

This example demonstrates FakeAI's reasoning model support, showing:
- GPT-OSS models (open-source reasoning models)
- O1 models (legacy reasoning models)
- Reasoning content showing internal thinking
- Reasoning tokens in usage metrics
- Streaming reasoning vs content
- Comparison with regular models

GPT-OSS models (gpt-oss-120b, gpt-oss-20b) are OpenAI's open-source
reasoning models released under Apache 2.0 license (Aug 2025).
They use mixture-of-experts architecture and show their reasoning process.
"""
import asyncio

from openai import AsyncOpenAI

# Base URL for FakeAI server
BASE_URL = "http://localhost:8000"


async def demonstrate_basic_reasoning():
    """Demonstrate basic reasoning model behavior."""
    print("=" * 80)
    print("PART 1: BASIC REASONING MODEL")
    print("=" * 80)
    print()

    client = AsyncOpenAI(
        api_key="test-key",
        base_url=BASE_URL,
    )

    # Ask a question that benefits from reasoning
    print("Question: What is the sum of the first 10 prime numbers?")
    print()
    print("Model: gpt-oss-120b (reasoning model)")
    print("-" * 80)

    response = await client.chat.completions.create(
        model="gpt-oss-120b",
        messages=[
            {
                "role": "user",
                "content": "What is the sum of the first 10 prime numbers?",
            }
        ],
    )

    message = response.choices[0].message

    print("REASONING PROCESS:")
    print(message.reasoning_content)
    print()
    print("FINAL ANSWER:")
    print(message.content)
    print()
    print("TOKEN USAGE:")
    print(f"  Prompt tokens:     {response.usage.prompt_tokens}")
    print(f"  Completion tokens: {response.usage.completion_tokens}")
    if response.usage.completion_tokens_details:
        print(
            f"  Reasoning tokens:  {response.usage.completion_tokens_details.reasoning_tokens}"
        )
        actual_content_tokens = (
            response.usage.completion_tokens
            - response.usage.completion_tokens_details.reasoning_tokens
        )
        print(f"  Content tokens:    {actual_content_tokens}")
    print()


async def compare_reasoning_vs_regular():
    """Compare reasoning model output with regular model."""
    print("=" * 80)
    print("PART 2: REASONING MODEL vs REGULAR MODEL")
    print("=" * 80)
    print()

    client = AsyncOpenAI(
        api_key="test-key",
        base_url=BASE_URL,
    )

    question = "If I have 3 boxes with 4 apples each, and I eat 2 apples from each box, how many apples remain?"

    print(f"Question: {question}")
    print()

    # Test with regular model
    print("GPT-4 (Regular Model):")
    print("-" * 80)

    response = await client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": question}],
    )

    print("Answer (no reasoning shown):")
    print(response.choices[0].message.content)
    print()
    print(
        f"Has reasoning_content: {response.choices[0].message.reasoning_content is not None}"
    )
    print()

    # Test with reasoning model
    print("GPT-OSS-120B (Reasoning Model):")
    print("-" * 80)

    response = await client.chat.completions.create(
        model="gpt-oss-120b",
        messages=[{"role": "user", "content": question}],
    )

    print("Reasoning:")
    print(response.choices[0].message.reasoning_content)
    print()
    print("Answer:")
    print(response.choices[0].message.content)
    print()


async def demonstrate_streaming_reasoning():
    """Show how reasoning is streamed before content."""
    print("=" * 80)
    print("PART 3: STREAMING REASONING MODEL")
    print("=" * 80)
    print()

    client = AsyncOpenAI(
        api_key="test-key",
        base_url=BASE_URL,
    )

    print("Model: gpt-oss-20b (optimized for low latency)")
    print("Question: Explain how binary search works")
    print()
    print("Watch how reasoning comes FIRST, then the answer:")
    print("-" * 80)

    reasoning_chunks = []
    content_chunks = []
    reasoning_done = False

    stream = await client.chat.completions.create(
        model="gpt-oss-20b",
        messages=[{"role": "user", "content": "Explain how binary search works"}],
        stream=True,
    )

    async for chunk in stream:
        if chunk.choices and chunk.choices[0].delta:
            delta = chunk.choices[0].delta

            # Reasoning tokens come first
            if delta.reasoning_content:
                reasoning_chunks.append(delta.reasoning_content)
                print(delta.reasoning_content, end="", flush=True)

            # Content tokens come after
            if delta.content:
                if not reasoning_done and reasoning_chunks:
                    print("\n")
                    print("-" * 80)
                    print("REASONING COMPLETE, NOW GENERATING ANSWER:")
                    print("-" * 80)
                    reasoning_done = True

                content_chunks.append(delta.content)
                print(delta.content, end="", flush=True)

    print("\n")
    print()
    print("SUMMARY:")
    print(f"  Reasoning tokens: {len(reasoning_chunks)} chunks")
    print(f"  Content tokens:   {len(content_chunks)} chunks")
    print()


async def demonstrate_o1_models():
    """Show O1 model family (legacy reasoning models)."""
    print("=" * 80)
    print("PART 4: O1 MODEL FAMILY (LEGACY)")
    print("=" * 80)
    print()

    client = AsyncOpenAI(
        api_key="test-key",
        base_url=BASE_URL,
    )

    print(
        "O1 models (deepseek-ai/DeepSeek-R1, deepseek-ai/DeepSeek-R1, deepseek-ai/DeepSeek-R1-Distill-Qwen-32B) also support reasoning."
    )
    print("These are the original reasoning models before GPT-OSS.")
    print()

    models = ["deepseek-ai/DeepSeek-R1", "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B"]

    for model in models:
        print(f"Model: {model}")
        print("-" * 80)

        response = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "What is 15% of 80?"}],
        )

        print("Reasoning:", response.choices[0].message.reasoning_content[:100] + "...")
        print("Answer:", response.choices[0].message.content[:100] + "...")

        if response.usage.completion_tokens_details:
            print(
                f"Reasoning tokens: {response.usage.completion_tokens_details.reasoning_tokens}"
            )

        print()


async def demonstrate_complex_reasoning():
    """Show reasoning on a complex multi-step problem."""
    print("=" * 80)
    print("PART 5: COMPLEX MULTI-STEP REASONING")
    print("=" * 80)
    print()

    client = AsyncOpenAI(
        api_key="test-key",
        base_url=BASE_URL,
    )

    problem = """A train leaves Station A at 2:00 PM traveling at 60 mph.
Another train leaves Station B (300 miles away) at 3:00 PM traveling toward Station A at 90 mph.
At what time will the trains meet?"""

    print("Problem:")
    print(problem)
    print()
    print("Model: gpt-oss-120b")
    print("-" * 80)

    response = await client.chat.completions.create(
        model="gpt-oss-120b",
        messages=[{"role": "user", "content": problem}],
    )

    print("REASONING (step-by-step thinking):")
    print()
    print(response.choices[0].message.reasoning_content)
    print()
    print("-" * 80)
    print("FINAL ANSWER:")
    print()
    print(response.choices[0].message.content)
    print()


async def demonstrate_reasoning_conversation():
    """Show reasoning in a multi-turn conversation."""
    print("=" * 80)
    print("PART 6: REASONING IN MULTI-TURN CONVERSATION")
    print("=" * 80)
    print()

    client = AsyncOpenAI(
        api_key="test-key",
        base_url=BASE_URL,
    )

    messages = [
        {
            "role": "user",
            "content": "I have $100. I spend 40% on groceries. How much do I have left?",
        }
    ]

    print("Turn 1:")
    print(messages[0]["content"])
    print("-" * 80)

    response = await client.chat.completions.create(
        model="gpt-oss-120b",
        messages=messages,
    )

    print("Reasoning:", response.choices[0].message.reasoning_content[:150] + "...")
    print("Answer:", response.choices[0].message.content)
    print()

    # Add to conversation
    messages.append(
        {
            "role": "assistant",
            "content": response.choices[0].message.content,
            "reasoning_content": response.choices[0].message.reasoning_content,
        }
    )

    messages.append(
        {
            "role": "user",
            "content": "Now I spend half of what's left on entertainment. How much remains?",
        }
    )

    print("Turn 2:")
    print(messages[-1]["content"])
    print("-" * 80)

    response = await client.chat.completions.create(
        model="gpt-oss-120b",
        messages=messages,
    )

    print("Reasoning:", response.choices[0].message.reasoning_content[:150] + "...")
    print("Answer:", response.choices[0].message.content)
    print()


async def demonstrate_reasoning_with_tools():
    """Show reasoning models with tool calling."""
    print("=" * 80)
    print("PART 7: REASONING WITH TOOL CALLING")
    print("=" * 80)
    print()

    client = AsyncOpenAI(
        api_key="test-key",
        base_url=BASE_URL,
    )

    tools = [
        {
            "type": "function",
            "function": {
                "name": "calculate",
                "description": "Perform mathematical calculations",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expression": {
                            "type": "string",
                            "description": "The mathematical expression to evaluate",
                        }
                    },
                    "required": ["expression"],
                },
            },
        }
    ]

    print("Question: What is the square root of 144 plus 25?")
    print("Available tools: calculate()")
    print()
    print("Model: gpt-oss-120b")
    print("-" * 80)

    response = await client.chat.completions.create(
        model="gpt-oss-120b",
        messages=[
            {"role": "user", "content": "What is the square root of 144 plus 25?"}
        ],
        tools=tools,
    )

    print("REASONING (deciding whether to use tools):")
    print(response.choices[0].message.reasoning_content)
    print()

    if response.choices[0].message.tool_calls:
        print("TOOL CALLS:")
        for tool_call in response.choices[0].message.tool_calls:
            print(f"  Function: {tool_call.function.name}")
            print(f"  Arguments: {tool_call.function.arguments}")
        print()
    else:
        print("ANSWER (no tools needed):")
        print(response.choices[0].message.content)
        print()


async def main():
    """Run all reasoning model demonstrations."""
    print()
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 15 + "FakeAI Reasoning Model Demonstration" + " " * 26 + "║")
    print("╚" + "=" * 78 + "╝")
    print()
    print("This demo shows FakeAI's support for reasoning models that expose their")
    print("internal thinking process before generating final answers.")
    print()
    input("Press Enter to start...")
    print()

    try:
        await demonstrate_basic_reasoning()
        input("Press Enter to continue...")
        print()

        await compare_reasoning_vs_regular()
        input("Press Enter to continue...")
        print()

        await demonstrate_streaming_reasoning()
        input("Press Enter to continue...")
        print()

        await demonstrate_o1_models()
        input("Press Enter to continue...")
        print()

        await demonstrate_complex_reasoning()
        input("Press Enter to continue...")
        print()

        await demonstrate_reasoning_conversation()
        input("Press Enter to continue...")
        print()

        await demonstrate_reasoning_with_tools()

        print("=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print()
        print("Reasoning Models:")
        print()
        print("GPT-OSS Family (Open Source - Apache 2.0):")
        print("  • gpt-oss-120b - Large reasoning model (120B parameters)")
        print("  • gpt-oss-20b  - Fast reasoning model (20B parameters)")
        print("  • Mixture-of-experts architecture")
        print("  • Shows internal reasoning before final answer")
        print()
        print("O1 Family (Legacy):")
        print("  • deepseek-ai/DeepSeek-R1 - Preview of O1 capabilities")
        print(
            "  • deepseek-ai/DeepSeek-R1-Distill-Qwen-32B    - Smaller, faster O1 model"
        )
        print("  • deepseek-ai/DeepSeek-R1         - Full O1 model")
        print()
        print("Key Features:")
        print("  • reasoning_content field shows thinking process")
        print("  • reasoning_tokens tracked separately in usage")
        print("  • In streaming: reasoning comes BEFORE content")
        print("  • Works with tool calling and multi-turn conversations")
        print()
        print("When to use reasoning models:")
        print("  • Complex math problems")
        print("  • Multi-step logical reasoning")
        print("  • Planning and analysis tasks")
        print("  • Code generation with explanation")
        print()

    except Exception as e:
        print(f"Error: {e}")
        print()
        print("Make sure FakeAI server is running:")
        print("  python run_server.py")
        print()


if __name__ == "__main__":
    asyncio.run(main())
