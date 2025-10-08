#!/usr/bin/env python3
"""
Example: Using the Error Injection System

This example demonstrates how to use FakeAI's error injection system
to test error handling in your applications.
"""
#  SPDX-License-Identifier: Apache-2.0

import time

from fakeai.config import AppConfig
from fakeai.error_injector import ErrorInjector, ErrorType

# Example 1: Basic error injection setup
print("Example 1: Basic Error Injection")
print("-" * 50)

# Create error injector with 20% error rate
injector = ErrorInjector(global_error_rate=0.2, enabled=True)

# Simulate requests
print("Simulating 10 requests with 20% error rate:")
for i in range(10):
    should_error, error_response = injector.should_inject_error("/v1/chat/completions")
    if should_error:
        print(f"  Request {i+1}: ERROR - {error_response['error']['type']}")
    else:
        print(f"  Request {i+1}: SUCCESS")

# Get statistics
stats = injector.get_error_stats()
print(f"\nStatistics:")
print(f"  Total checks: {stats['statistics']['total_checks']}")
print(f"  Errors injected: {stats['statistics']['total_errors_injected']}")
print(f"  Error rate: {stats['statistics']['overall_error_rate']:.2%}")

# Example 2: Per-endpoint error rates
print("\n\nExample 2: Per-Endpoint Error Rates")
print("-" * 50)

injector = ErrorInjector(global_error_rate=0.0, enabled=True)
injector.set_endpoint_error_rate("/v1/chat/completions", 0.5)
injector.set_endpoint_error_rate("/v1/embeddings", 0.1)

print("Simulating requests to different endpoints:")
for endpoint in ["/v1/chat/completions", "/v1/embeddings", "/v1/models"]:
    errors = 0
    for _ in range(20):
        should_error, _ = injector.should_inject_error(endpoint)
        if should_error:
            errors += 1
    print(f"  {endpoint}: {errors}/20 errors ({errors/20:.0%})")

# Example 3: Specific error types
print("\n\nExample 3: Testing Specific Error Types")
print("-" * 50)

# Only inject service unavailable errors
injector = ErrorInjector(
    global_error_rate=1.0,
    enabled=True,
    error_types=[ErrorType.SERVICE_UNAVAILABLE],
)

print("Injecting only SERVICE_UNAVAILABLE errors:")
for i in range(3):
    should_error, error_response = injector.should_inject_error("/v1/chat/completions")
    if should_error:
        print(f"  Error {i+1}:")
        print(f"    Status: {error_response['status_code']}")
        print(f"    Type: {error_response['error']['type']}")
        print(f"    Message: {error_response['error']['message']}")

# Example 4: Load spike simulation
print("\n\nExample 4: Load Spike Simulation")
print("-" * 50)

injector = ErrorInjector(global_error_rate=0.1, enabled=True)
print("Normal operation (10% error rate):")

errors_before = 0
for _ in range(20):
    should_error, _ = injector.should_inject_error("/v1/chat/completions")
    if should_error:
        errors_before += 1
print(f"  Errors: {errors_before}/20 ({errors_before/20:.0%})")

# Simulate load spike (3x error rate multiplier)
print("\nSimulating load spike (3x multiplier for 2 seconds):")
injector.simulate_load_spike(duration_seconds=2.0, error_rate_multiplier=3.0)

errors_during = 0
for _ in range(20):
    should_error, _ = injector.should_inject_error("/v1/chat/completions")
    if should_error:
        errors_during += 1
print(f"  Errors during spike: {errors_during}/20 ({errors_during/20:.0%})")

# Wait for spike to expire
time.sleep(2.1)

errors_after = 0
for _ in range(20):
    should_error, _ = injector.should_inject_error("/v1/chat/completions")
    if should_error:
        errors_after += 1
print(f"  Errors after spike: {errors_after}/20 ({errors_after/20:.0%})")

# Example 5: Integration with AppConfig
print("\n\nExample 5: Configuration Integration")
print("-" * 50)

config = AppConfig(
    error_injection_enabled=True,
    error_injection_rate=0.15,
    error_injection_types=["internal_error", "gateway_timeout"],
)

print("Configuration loaded:")
print(f"  Enabled: {config.error_injection_enabled}")
print(f"  Rate: {config.error_injection_rate}")
print(f"  Types: {config.error_injection_types}")

# Create injector from config
injector = ErrorInjector(
    global_error_rate=config.error_injection_rate,
    enabled=config.error_injection_enabled,
    error_types=[ErrorType(t) for t in config.error_injection_types],
)

print("\nSimulating 10 requests with config-based injector:")
for i in range(10):
    should_error, error_response = injector.should_inject_error("/v1/chat/completions")
    if should_error:
        print(f"  Request {i+1}: ERROR - {error_response['error']['type']}")
    else:
        print(f"  Request {i+1}: SUCCESS")

# Example 6: Prometheus metrics
print("\n\nExample 6: Prometheus Metrics Export")
print("-" * 50)

injector = ErrorInjector(global_error_rate=0.3, enabled=True)

# Generate some activity
for _ in range(50):
    injector.should_inject_error("/v1/chat/completions")

metrics = injector.get_prometheus_metrics()
print("Sample Prometheus metrics:")
for line in metrics.split("\n")[:15]:  # Show first 15 lines
    if line and not line.startswith("#"):
        print(f"  {line}")

print("\n" + "=" * 50)
print("Error injection examples completed!")
print("=" * 50)
