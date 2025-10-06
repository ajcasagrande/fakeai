#!/usr/bin/env python3
"""
Example of using lightweight LLM generation with FakeAI.

This example demonstrates how to enable and use the LLM generation module
for more realistic responses instead of template-based generation.
"""
#  SPDX-License-Identifier: Apache-2.0

import asyncio
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fakeai.config import AppConfig
from fakeai.llm_generator import (
    LightweightLLMGenerator,
    generate_with_llm,
    is_llm_available,
)


def example_basic_usage():
    """Example: Basic LLM generation usage."""
    print("=" * 60)
    print("Example 1: Basic LLM Generation")
    print("=" * 60)

    # Check if LLM is available
    if is_llm_available():
        print("✓ LLM backend is available")
    else:
        print("✗ LLM backend not available (install: pip install transformers torch)")
        print("  Falling back to template-based generation")
        return

    # Generate some text
    prompt = "The future of artificial intelligence is"
    print(f"\nPrompt: {prompt}")
    print("Generating response...\n")

    response = generate_with_llm(
        prompt=prompt,
        max_tokens=50,
        temperature=0.8,
    )

    print(f"Response: {response}")
    print()


def example_with_config():
    """Example: Using LLM generation with AppConfig."""
    print("=" * 60)
    print("Example 2: Using with AppConfig")
    print("=" * 60)

    # Create config with LLM enabled
    config = AppConfig(
        use_llm_generation=True,
        llm_model_name="distilgpt2",  # Fast, lightweight model
        llm_use_gpu=False,  # Set to True for GPU acceleration
    )

    print(f"LLM Generation enabled: {config.use_llm_generation}")
    print(f"Model: {config.llm_model_name}")
    print(f"Use GPU: {config.llm_use_gpu}")
    print()

    if not is_llm_available():
        print("LLM backend not available")
        return

    # Generate with different temperatures
    prompt = "In a world where robots"
    print(f"Prompt: {prompt}\n")

    for temp in [0.1, 0.5, 1.0]:
        print(f"Temperature {temp}:")
        response = generate_with_llm(
            prompt=prompt,
            max_tokens=30,
            temperature=temp,
        )
        print(f"  {response}\n")


def example_streaming():
    """Example: Streaming generation."""
    print("=" * 60)
    print("Example 3: Streaming Generation")
    print("=" * 60)

    if not is_llm_available():
        print("LLM backend not available")
        return

    gen = LightweightLLMGenerator()

    prompt = "Once upon a time, there was"
    print(f"Prompt: {prompt}\n")
    print("Streaming response: ", end="", flush=True)

    for token in gen.generate_stream(
        prompt=prompt,
        max_tokens=40,
        temperature=0.7,
    ):
        print(token, end="", flush=True)

    print("\n")


def example_deterministic():
    """Example: Deterministic generation with seed."""
    print("=" * 60)
    print("Example 4: Deterministic Generation (with seed)")
    print("=" * 60)

    if not is_llm_available():
        print("LLM backend not available")
        return

    prompt = "The secret to happiness is"
    seed = 42

    print(f"Prompt: {prompt}")
    print(f"Seed: {seed}\n")

    # Generate twice with same seed
    print("Generation 1:")
    response1 = generate_with_llm(prompt=prompt, max_tokens=25, seed=seed)
    print(f"  {response1}\n")

    print("Generation 2 (same seed):")
    response2 = generate_with_llm(prompt=prompt, max_tokens=25, seed=seed)
    print(f"  {response2}\n")

    if response1 == response2:
        print("✓ Responses are identical (cached or deterministic)")
    else:
        print("✗ Responses differ")


def example_cache_performance():
    """Example: Cache performance."""
    print("=" * 60)
    print("Example 5: Cache Performance")
    print("=" * 60)

    if not is_llm_available():
        print("LLM backend not available")
        return

    gen = LightweightLLMGenerator()
    gen.clear_cache()

    prompt = "The meaning of life is"

    print(f"Prompt: {prompt}\n")

    # First generation (no cache)
    import time

    start = time.time()
    response1 = gen.generate(prompt=prompt, max_tokens=30, temperature=0.7)
    time1 = time.time() - start
    print(f"First generation: {time1:.3f}s")
    print(f"  {response1}\n")

    # Second generation (from cache)
    start = time.time()
    response2 = gen.generate(prompt=prompt, max_tokens=30, temperature=0.7)
    time2 = time.time() - start
    print(f"Second generation: {time2:.3f}s (cached)")
    print(f"  {response2}\n")

    speedup = time1 / time2 if time2 > 0 else float("inf")
    print(f"Speedup: {speedup:.1f}x")

    # Show cache stats
    stats = gen.get_cache_stats()
    print(f"Cache: {stats['size']}/{stats['capacity']} entries")
    print()


def example_fallback_behavior():
    """Example: Fallback behavior when LLM is unavailable."""
    print("=" * 60)
    print("Example 6: Fallback Behavior")
    print("=" * 60)

    # Create a generator that will fail to load
    gen = LightweightLLMGenerator(model_name="nonexistent-model-xyz")

    if gen.is_available():
        print("LLM is available")
    else:
        print("✓ LLM is not available (as expected)")
        print("  Application should fall back to template-based generation")

    # Try to generate anyway
    response = gen.generate("test prompt")
    print(f"Response when unavailable: '{response}' (empty string)")
    print()


def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("FakeAI Lightweight LLM Generation Examples")
    print("=" * 60 + "\n")

    # Run examples
    example_basic_usage()
    example_with_config()
    example_streaming()
    example_deterministic()
    example_cache_performance()
    example_fallback_behavior()

    print("=" * 60)
    print("Examples complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
