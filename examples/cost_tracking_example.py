#!/usr/bin/env python3
"""
Example demonstrating the cost tracking and billing simulation features of FakeAI.

This example shows how to:
1. Track API usage costs
2. Set budget limits
3. Get cost summaries and breakdowns
4. Calculate cost savings from caching and batching
5. Get optimization suggestions
"""
#  SPDX-License-Identifier: Apache-2.0

from fakeai.cost_tracker import BudgetLimitType, BudgetPeriod, CostTracker


def main():
    """Demonstrate cost tracking features."""
    # Get the singleton cost tracker
    tracker = CostTracker()
    tracker.clear_history()  # Clear any previous history

    print("=" * 80)
    print("FakeAI Cost Tracking and Billing Simulation Example")
    print("=" * 80)
    print()

    # Example 1: Basic usage tracking
    print("1. Recording API Usage")
    print("-" * 80)

    api_key = "demo-key-123"

    # Record some chat completions
    for i in range(10):
        cost = tracker.record_usage(
            api_key=api_key,
            model="gpt-4o",
            endpoint="/v1/chat/completions",
            prompt_tokens=1000,
            completion_tokens=500,
        )
        if i == 0:
            print(f"   Cost per request: ${cost:.6f}")

    print(f"   Recorded 10 chat completion requests")
    print()

    # Example 2: Usage with caching
    print("2. Recording Usage with Prompt Caching")
    print("-" * 80)

    for i in range(5):
        cost = tracker.record_usage(
            api_key=api_key,
            model="gpt-4o",
            endpoint="/v1/chat/completions",
            prompt_tokens=2000,
            completion_tokens=500,
            cached_tokens=1000,  # 50% of prompt tokens from cache
        )
        if i == 0:
            print(f"   Cost per request (with cache): ${cost:.6f}")

    print(f"   Recorded 5 requests with prompt caching")
    print()

    # Example 3: Get cost breakdown by key
    print("3. Cost Breakdown by API Key")
    print("-" * 80)

    cost_info = tracker.get_cost_by_key(api_key)
    print(f"   API Key: {cost_info['api_key']}")
    print(f"   Total Cost: ${cost_info['total_cost']:.6f}")
    print(f"   Total Requests: {cost_info['requests']}")
    print(f"   Total Tokens: {cost_info['tokens']['total_tokens']:,}")
    print()
    print("   Costs by Model:")
    for model, cost in cost_info["by_model"].items():
        print(f"      {model}: ${cost:.6f}")
    print()

    # Example 4: Set budget limits
    print("4. Budget Management")
    print("-" * 80)

    tracker.set_budget(
        api_key=api_key,
        limit=1.00,  # $1.00 monthly limit
        period=BudgetPeriod.MONTHLY,
        limit_type=BudgetLimitType.SOFT,
        alert_threshold=0.8,  # Alert at 80%
    )

    used, remaining, over_limit = tracker.check_budget(api_key)
    print(f"   Budget Limit: $1.00")
    print(f"   Used: ${used:.6f}")
    print(f"   Remaining: ${remaining:.6f}")
    print(f"   Over Limit: {over_limit}")
    print()

    # Example 5: Cache savings
    print("5. Cache Savings Analysis")
    print("-" * 80)

    cache_savings = tracker.get_cache_savings(api_key)
    print(f"   Cached Tokens: {cache_savings['cached_tokens']:,}")
    print(f"   Regular Cost (no cache): ${cache_savings['regular_cost']:.6f}")
    print(f"   Cached Cost: ${cache_savings['cached_cost']:.6f}")
    print(f"   Savings: ${cache_savings['savings']:.6f}")
    print()

    # Example 6: Record batch processing
    print("6. Batch Processing Cost Tracking")
    print("-" * 80)

    for i in range(5):
        tracker.record_usage(
            api_key=api_key,
            model="gpt-4o",
            endpoint="/v1/batches",
            prompt_tokens=1000,
            completion_tokens=1000,
        )

    batch_savings = tracker.get_batch_savings(api_key)
    print(f"   Batch Requests: {batch_savings['batch_requests']}")
    print(f"   Completion Tokens: {batch_savings['completion_tokens']:,}")
    print(f"   Regular Cost: ${batch_savings['regular_cost']:.6f}")
    print(f"   Batch Cost (50% discount): ${batch_savings['batch_cost']:.6f}")
    print(f"   Savings: ${batch_savings['savings']:.6f}")
    print()

    # Example 7: Get comprehensive summary
    print("7. Comprehensive Cost Summary")
    print("-" * 80)

    summary = tracker.get_summary()
    print(f"   Total Cost: ${summary['total_cost']:.6f}")
    print(f"   Total Cost (24h): ${summary['total_cost_24h']:.6f}")
    print(f"   Projected Monthly Cost: ${summary['projected_monthly_cost']:.2f}")
    print(f"   Total Requests: {summary['total_requests']}")
    print(f"   Unique API Keys: {summary['unique_api_keys']}")
    print()

    # Example 8: Cost by model (across all keys)
    print("8. Costs by Model (All API Keys)")
    print("-" * 80)

    costs_by_model = tracker.get_cost_by_model()
    for model, cost in sorted(costs_by_model.items(), key=lambda x: x[1], reverse=True):
        print(f"   {model}: ${cost:.6f}")
    print()

    # Example 9: Optimization suggestions
    print("9. Cost Optimization Suggestions")
    print("-" * 80)

    # Record some expensive GPT-4 usage to trigger suggestions
    expensive_key = "expensive-key-456"
    for _ in range(100):
        tracker.record_usage(
            api_key=expensive_key,
            model="gpt-4",
            endpoint="/v1/chat/completions",
            prompt_tokens=1000,
            completion_tokens=500,
        )

    suggestions = tracker.get_optimization_suggestions(expensive_key)
    if suggestions:
        for suggestion in suggestions:
            print(f"   Type: {suggestion.suggestion_type}")
            print(f"   Description: {suggestion.description}")
            print(f"   Potential Savings: ${suggestion.potential_savings:.2f}/month")
            print()
    else:
        print("   No optimization suggestions at this time")
        print()

    # Example 10: Different pricing models
    print("10. Cost Comparison Across Models")
    print("-" * 80)

    models = [
        "gpt-4",
        "gpt-4-turbo",
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-3.5-turbo",
    ]

    test_key = "test-comparison"
    print("   Cost for 1M prompt tokens + 1M completion tokens:")
    print()

    for model in models:
        tracker.clear_history(test_key)  # Clear before each test
        cost = tracker.record_usage(
            api_key=test_key,
            model=model,
            endpoint="/v1/chat/completions",
            prompt_tokens=1_000_000,
            completion_tokens=1_000_000,
        )
        print(f"   {model:20s}: ${cost:.2f}")

    print()

    # Example 11: Image generation costs
    print("11. Image Generation Costs")
    print("-" * 80)

    image_key = "image-key"

    # Standard quality
    cost_standard = tracker.record_usage(
        api_key=image_key,
        model="dall-e-3",
        endpoint="/v1/images/generations",
        prompt_tokens=0,
        completion_tokens=0,
        metadata={"size": "1024x1024", "quality": "standard", "n": 1},
    )

    # HD quality
    cost_hd = tracker.record_usage(
        api_key=image_key,
        model="dall-e-3",
        endpoint="/v1/images/generations",
        prompt_tokens=0,
        completion_tokens=0,
        metadata={"size": "1024x1024", "quality": "hd", "n": 1},
    )

    print(f"   DALL-E 3 (1024x1024, standard): ${cost_standard:.3f}")
    print(f"   DALL-E 3 (1024x1024, HD):       ${cost_hd:.3f}")
    print()

    print("=" * 80)
    print("Cost tracking demonstration complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
