#!/usr/bin/env python3
"""
Metrics Aggregation Demo

Demonstrates the unified metrics aggregation module that combines
all metric sources (MetricsTracker, KV cache, DCGM, Dynamo) into
unified views with correlation analysis and health scoring.
"""
import asyncio
import time

from fakeai.dcgm_metrics import DCGMMetricsSimulator
from fakeai.dynamo_metrics import DynamoMetricsCollector
from fakeai.kv_cache import KVCacheMetrics, SmartRouter
from fakeai.metrics import MetricsTracker
from fakeai.metrics_aggregator import MetricsAggregator


def print_section(title: str):
    """Print section header."""
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print(f"{'=' * 70}\n")


async def main():
    """Run metrics aggregation demo."""
    print_section("Metrics Aggregation Demo")

    # Initialize all metric sources
    print("1. Initializing metric sources...")
    metrics_tracker = MetricsTracker()
    kv_metrics = KVCacheMetrics()
    dcgm_metrics = DCGMMetricsSimulator(num_gpus=4, gpu_model="H100-80GB")
    dynamo_metrics = DynamoMetricsCollector(window_size=300)

    # Create aggregator
    aggregator = MetricsAggregator(
        metrics_tracker=metrics_tracker,
        kv_metrics=kv_metrics,
        dcgm_metrics=dcgm_metrics,
        dynamo_metrics=dynamo_metrics,
    )

    print("   ✓ MetricsTracker initialized")
    print("   ✓ KVCacheMetrics initialized")
    print("   ✓ DCGMMetricsSimulator initialized (4x H100-80GB)")
    print("   ✓ DynamoMetricsCollector initialized")
    print("   ✓ MetricsAggregator initialized")

    # Simulate some workload
    print_section("2. Simulating Workload")

    # Simulate GPU workload
    print("   Setting GPU workload (80% compute, 60% memory)...")
    dcgm_metrics.set_global_workload(compute_intensity=0.8, memory_intensity=0.6)

    # Simulate API requests
    print("   Simulating API requests...")
    for i in range(100):
        metrics_tracker.track_request("/v1/chat/completions")
        metrics_tracker.track_response(
            "/v1/chat/completions", latency=0.5 + (i % 10) * 0.1
        )
        metrics_tracker.track_tokens("/v1/chat/completions", 50)

    # Simulate cache lookups
    print("   Simulating cache lookups...")
    for i in range(50):
        matched_tokens = 100 if i % 2 == 0 else 0  # 50% hit rate
        kv_metrics.record_cache_lookup("/v1/chat/completions", 200, matched_tokens)

    # Simulate Dynamo requests
    print("   Simulating inference requests...")
    for i in range(50):
        request_id = f"req-{i}"
        request_metrics = dynamo_metrics.start_request(
            request_id=request_id,
            model="openai/gpt-oss-120b",
            endpoint="/v1/chat/completions",
            input_tokens=200,
        )
        dynamo_metrics.record_prefill_start(request_id)
        time.sleep(0.001)  # Simulate processing
        dynamo_metrics.record_first_token(request_id)
        dynamo_metrics.complete_request(
            request_id=request_id,
            output_tokens=100,
            cached_tokens=50 if i % 2 == 0 else 0,
            kv_cache_hit=(i % 2 == 0),
            worker_id="worker-0",
        )

    print("   ✓ Workload simulation complete")

    # Wait for metrics to accumulate
    print("\n   Waiting for metrics to stabilize...")
    await asyncio.sleep(2)

    # Display unified metrics
    print_section("3. Unified Metrics")
    unified = aggregator.get_unified_metrics()

    print(f"Timestamp: {unified['timestamp']:.2f}")
    print(f"Sources: {', '.join(unified['sources'].keys())}")

    # Display API metrics
    if "metrics_tracker" in unified["sources"]:
        mt = unified["sources"]["metrics_tracker"]
        if "responses" in mt:
            for endpoint, stats in mt["responses"].items():
                if stats.get("rate", 0) > 0:
                    print(f"\nAPI Endpoint: {endpoint}")
                    print(f"  Requests/sec: {stats['rate']:.2f}")
                    print(f"  Avg Latency: {stats['avg'] * 1000:.2f}ms")
                    print(f"  P99 Latency: {stats['p99'] * 1000:.2f}ms")

    # Display cache metrics
    if "kv_cache" in unified["sources"]:
        cache = unified["sources"]["kv_cache"]
        print(f"\nKV Cache:")
        print(f"  Hit Rate: {cache.get('cache_hit_rate', 0):.2f}%")
        print(f"  Token Reuse Rate: {cache.get('token_reuse_rate', 0):.2f}%")
        print(
            f"  Avg Prefix Length: {cache.get('average_prefix_length', 0):.0f} tokens"
        )

    # Display GPU metrics
    if "dcgm" in unified["sources"]:
        dcgm = unified["sources"]["dcgm"]
        gpu_count = sum(1 for k in dcgm.keys() if k.startswith("gpu_"))
        print(f"\nGPU Metrics ({gpu_count} GPUs):")
        for gpu_key, gpu_data in dcgm.items():
            if isinstance(gpu_data, dict) and "gpu_id" in gpu_data:
                print(f"  GPU {gpu_data['gpu_id']}:")
                print(f"    Utilization: {gpu_data.get('gpu_utilization_pct', 0)}%")
                print(f"    Temperature: {gpu_data.get('temperature_c', 0)}°C")
                print(f"    Power: {gpu_data.get('power_usage_w', 0):.1f}W")

    # Display Dynamo metrics
    if "dynamo" in unified["sources"]:
        dynamo = unified["sources"]["dynamo"]
        summary = dynamo.get("summary", {})
        print(f"\nInference Metrics:")
        print(f"  Total Requests: {summary.get('total_requests', 0)}")
        print(
            f"  Success Rate: {summary.get('successful_requests', 0) / summary.get('total_requests', 1) * 100:.1f}%"
        )

        latency = dynamo.get("latency", {}).get("ttft", {})
        if latency:
            print(f"  TTFT P50: {latency.get('p50', 0):.1f}ms")
            print(f"  TTFT P99: {latency.get('p99', 0):.1f}ms")

    # Display correlated metrics
    print_section("4. Correlated Metrics")
    correlated = aggregator.get_correlated_metrics()

    print("Cross-System Correlations:")
    for correlation in correlated.get("correlations", []):
        print(f"\n  {correlation['metric_a']} vs {correlation['metric_b']}:")
        print(f"    Relationship: {correlation['relationship']}")
        print(f"    Insight: {correlation['insight']}")
        for key, value in correlation.get("values", {}).items():
            if isinstance(value, float):
                print(f"      {key}: {value:.2f}")
            else:
                print(f"      {key}: {value}")

    # Display derived metrics
    print("\nDerived Efficiency Metrics:")
    for metric_name, metric_data in correlated.get("derived_metrics", {}).items():
        print(f"\n  {metric_name}:")
        print(f"    Value: {metric_data['value']:.2f} {metric_data['unit']}")
        print(f"    Description: {metric_data['description']}")

    # Display health scores
    print_section("5. System Health")
    health = aggregator.get_health_score()

    print(f"Overall Health Score: {health['overall']['score']:.1f}/100")
    print(f"Status: {health['overall']['status'].upper()}")

    if health["overall"]["issues"]:
        print("\nIssues Detected:")
        for issue in health["overall"]["issues"]:
            print(f"  ⚠ {issue}")

    if health["overall"]["recommendations"]:
        print("\nRecommendations:")
        for rec in health["overall"]["recommendations"]:
            print(f"  → {rec}")

    print("\nSubsystem Health:")
    for subsystem, health_data in health["subsystems"].items():
        status_icon = (
            "✓"
            if health_data["status"] == "healthy"
            else "⚠" if health_data["status"] == "degraded" else "✗"
        )
        print(
            f"  {status_icon} {subsystem.upper()}: {health_data['score']:.1f}/100 ({health_data['status']})"
        )

    # Display time-series data
    print_section("6. Time-Series Data")

    # Wait a bit for time-series to accumulate
    print("Collecting time-series data...")
    await asyncio.sleep(3)

    # Get recent time-series
    metrics_to_query = [
        "gpu_utilization",
        "token_throughput",
        "cache_hit_rate",
        "queue_depth",
    ]
    for metric_name in metrics_to_query:
        series = aggregator.get_time_series(metric_name, "1s", 60)
        if series:
            print(f"\n  {metric_name}:")
            print(f"    Data points: {len(series)}")
            if series:
                values = [p["value"] for p in series]
                print(f"    Latest: {series[-1]['value']:.2f}")
                print(f"    Min: {min(values):.2f}")
                print(f"    Max: {max(values):.2f}")
                print(f"    Avg: {sum(values) / len(values):.2f}")

    # Export Prometheus format
    print_section("7. Prometheus Export")
    prometheus = aggregator.get_prometheus_unified()

    lines = prometheus.split("\n")
    metric_lines = [l for l in lines if l and not l.startswith("#")]
    help_lines = [l for l in lines if l.startswith("# HELP")]

    print(f"Total metrics: {len(metric_lines)}")
    print(f"Metric types: {len(help_lines)}")

    print("\nSample Prometheus output (first 10 lines):")
    for line in lines[:10]:
        print(f"  {line}")

    # Cleanup
    print_section("8. Cleanup")
    print("Shutting down components...")

    aggregator.shutdown()
    metrics_tracker.shutdown()
    dcgm_metrics.shutdown()

    print("   ✓ All components shut down")

    print_section("Demo Complete")
    print("The metrics aggregator successfully unified all metric sources,")
    print("calculated correlations, derived efficiency metrics, and provided")
    print("comprehensive health scoring with actionable recommendations.")
    print("\nFor production use, access via GET /metrics/unified endpoint.")


if __name__ == "__main__":
    asyncio.run(main())
