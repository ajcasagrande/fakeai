#!/usr/bin/env python3
"""
Rate Limiter Metrics Demo

This script demonstrates the comprehensive rate limiting metrics tracking
capabilities, including per-key metrics, throttling analytics, tier statistics,
and abuse pattern detection.
"""
#  SPDX-License-Identifier: Apache-2.0

import time

from fakeai.rate_limiter import RateLimiter
from fakeai.rate_limiter_metrics import RateLimiterMetrics


def print_section(title: str):
    """Print a section header."""
    print(f"\n{'=' * 80}")
    print(f"{title:^80}")
    print(f"{'=' * 80}\n")


def simulate_normal_usage(rate_limiter: RateLimiter, api_key: str):
    """Simulate normal API usage."""
    print(f"Simulating normal usage for {api_key}...")
    for i in range(20):
        allowed, retry_after, headers = rate_limiter.check_rate_limit(
            api_key, tokens=100
        )
        if not allowed:
            print(f"  Request {i+1}: THROTTLED (retry after {retry_after}s)")
            rate_limiter.metrics.record_retry(api_key)
        else:
            print(f"  Request {i+1}: Allowed")
        time.sleep(0.05)  # Small delay


def simulate_burst_behavior(rate_limiter: RateLimiter, api_key: str):
    """Simulate burst behavior (many requests at once)."""
    print(f"\nSimulating burst behavior for {api_key}...")
    for i in range(30):
        allowed, retry_after, headers = rate_limiter.check_rate_limit(
            api_key, tokens=50
        )
        if not allowed:
            print(f"  Burst request {i+1}: THROTTLED")
        # No delay - burst!


def simulate_heavy_usage(rate_limiter: RateLimiter, api_key: str):
    """Simulate heavy usage that exceeds limits."""
    print(f"\nSimulating heavy usage for {api_key}...")
    throttled_count = 0
    for i in range(100):
        allowed, retry_after, headers = rate_limiter.check_rate_limit(
            api_key, tokens=1000
        )
        if not allowed:
            throttled_count += 1
            rate_limiter.metrics.record_retry(api_key)
        time.sleep(0.01)
    print(f"  Throttled {throttled_count}/100 requests")


def main():
    """Run the demo."""
    print_section("Rate Limiter Metrics Demo")

    # Initialize rate limiter
    rate_limiter = RateLimiter()

    # Configure different tiers for different keys
    rate_limiter.configure(tier="free")
    print("Rate limiter configured with 'free' tier (60 RPM, 10K TPM)")

    # Reset metrics for clean demo
    rate_limiter.metrics.reset()

    # Scenario 1: Normal usage (tier-1)
    print_section("Scenario 1: Normal Usage (tier-1)")
    rate_limiter.configure(tier="tier-1")
    rate_limiter.metrics.assign_tier("user-alice", "tier-1")
    simulate_normal_usage(rate_limiter, "user-alice")

    # Scenario 2: Burst behavior (tier-1)
    print_section("Scenario 2: Burst Behavior (tier-1)")
    rate_limiter.metrics.assign_tier("user-bob", "tier-1")
    simulate_burst_behavior(rate_limiter, "user-bob")

    # Scenario 3: Heavy usage on free tier
    print_section("Scenario 3: Heavy Usage (free tier)")
    rate_limiter.configure(tier="free")
    rate_limiter.metrics.assign_tier("user-charlie", "free")
    simulate_heavy_usage(rate_limiter, "user-charlie")

    # Display per-key metrics
    print_section("Per-Key Metrics")
    for key in ["user-alice", "user-bob", "user-charlie"]:
        print(f"\n{key}:")
        stats = rate_limiter.metrics.get_key_stats(key)
        if stats:
            print(f"  Tier: {stats['tier']}")
            print(
                f"  Requests: {stats['requests']['total_attempted']} attempted, "
                f"{stats['requests']['total_allowed']} allowed, "
                f"{stats['requests']['total_throttled']} throttled"
            )
            print(f"  Success Rate: {stats['requests']['success_rate']:.1%}")
            print(
                f"  Tokens: {stats['tokens']['total_consumed']}/{stats['tokens']['total_requested']} "
                f"(efficiency: {stats['tokens']['efficiency']:.1%})"
            )
            print(
                f"  Throttling: {stats['throttling']['total_throttle_time_ms']:.0f}ms total, "
                f"{stats['throttling']['avg_retry_after_ms']:.0f}ms avg retry-after"
            )
            print(
                f"  Usage Patterns: {stats['usage_patterns']['current_burst_requests']} burst requests, "
                f"peak RPM: {stats['usage_patterns']['peak_rpm']:.1f}"
            )

    # Display tier statistics
    print_section("Tier Statistics")
    tier_stats = rate_limiter.metrics.get_tier_stats()
    for tier, stats in tier_stats.items():
        print(f"\n{tier}:")
        print(f"  Keys: {stats['key_count']}")
        print(
            f"  Total Requests: {stats['total_requests_attempted']} "
            f"({stats['total_requests_allowed']} allowed, "
            f"{stats['total_requests_throttled']} throttled)"
        )
        print(f"  Avg Throttle Rate: {stats['avg_throttle_rate']:.1%}")
        print(f"  Keys with High Throttle: {stats['keys_with_high_throttle']}")
        print(f"  Upgrade Opportunities: {stats['upgrade_opportunities']}")

    # Display throttle analytics
    print_section("Throttle Analytics")
    analytics = rate_limiter.metrics.get_throttle_analytics()
    print(f"Total Throttle Events: {analytics['total_throttle_events']}")

    print("\nDuration Histogram:")
    for bucket, count in analytics["duration_histogram"].items():
        print(f"  {bucket}: {count} events")

    print("\nRetry-After Distribution:")
    dist = analytics["retry_after_distribution"]
    if dist:
        print(f"  Min: {dist['min']:.0f}ms")
        print(f"  Median: {dist['median']:.0f}ms")
        print(f"  Avg: {dist['avg']:.0f}ms")
        print(f"  P90: {dist['p90']:.0f}ms")
        print(f"  P95: {dist['p95']:.0f}ms")
        print(f"  P99: {dist['p99']:.0f}ms")
        print(f"  Max: {dist['max']:.0f}ms")

    print("\nRPM vs TPM Exceeded:")
    exceeded = analytics["rpm_vs_tpm_exceeded"]
    print(f"  RPM only: {exceeded['rpm_only']}")
    print(f"  TPM only: {exceeded['tpm_only']}")
    print(f"  Both: {exceeded['both']}")

    # Display abuse pattern detection
    print_section("Abuse Pattern Detection")
    patterns = rate_limiter.metrics.detect_abuse_patterns()
    if patterns:
        for i, pattern in enumerate(patterns, 1):
            print(f"\n{i}. API Key: {pattern['api_key']} (Tier: {pattern['tier']})")
            print(f"   Severity: {pattern['severity'].upper()}")
            print(f"   Throttle Rate: {pattern['throttle_rate']:.1%}")
            print(f"   Total Requests: {pattern['total_requests']}")
            print("   Issues:")
            for issue in pattern["issues"]:
                print(f"     - {issue}")
    else:
        print("No abuse patterns detected.")

    # Display comprehensive metrics summary
    print_section("Comprehensive Metrics Summary")
    all_metrics = rate_limiter.metrics.get_all_metrics()
    summary = all_metrics["summary"]
    print(f"Total API Keys: {summary['total_keys']}")
    print(f"Total Throttle Events: {summary['total_throttle_events']}")
    print(f"Active Tiers: {', '.join(summary['tiers'])}")

    print("\nTo view these metrics via REST API:")
    print("  GET /metrics/rate-limits                    - All metrics")
    print("  GET /metrics/rate-limits/key/{api_key}     - Per-key stats")
    print("  GET /metrics/rate-limits/tier              - Tier aggregations")
    print("  GET /metrics/rate-limits/throttle-analytics - Throttling analytics")
    print("  GET /metrics/rate-limits/abuse-patterns    - Abuse detection")

    print_section("Demo Complete")


if __name__ == "__main__":
    main()
