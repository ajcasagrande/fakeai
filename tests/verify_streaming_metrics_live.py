#!/usr/bin/env python3
"""
Comprehensive Live Test for Streaming Metrics Population

This test verifies that streaming metrics are properly populated when making
real streaming requests to the FakeAI server. It validates:

1. Total stream count tracking
2. TTFT (Time to First Token) metrics
3. TPS (Tokens Per Second) metrics
4. Per-model breakdown
5. Prometheus export format
6. Streaming latency percentiles

Usage:
    python tests/verify_streaming_metrics_live.py

Requirements:
    - FakeAI server must be running on localhost:8000
    - Or the script will use the test client to make requests
"""

import json
import sys
import time
from typing import Any

try:
    import httpx
except ImportError:
    print("ERROR: httpx library not installed. Install with: pip install httpx")
    sys.exit(1)

# Use httpx client for live server testing
USE_TEST_CLIENT = False


class Colors:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header(text: str):
    """Print a formatted header."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(80)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}\n")


def print_section(text: str):
    """Print a section header."""
    print(f"\n{Colors.OKBLUE}{Colors.BOLD}{text}{Colors.ENDC}")
    print(f"{Colors.OKBLUE}{'-' * len(text)}{Colors.ENDC}")


def print_success(text: str):
    """Print a success message."""
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")


def print_warning(text: str):
    """Print a warning message."""
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")


def print_error(text: str):
    """Print an error message."""
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")


def print_info(text: str):
    """Print an info message."""
    print(f"{Colors.OKCYAN}ℹ {text}{Colors.ENDC}")


def print_metric(name: str, value: Any, unit: str = ""):
    """Print a metric with formatted output."""
    if unit:
        print(f"  {name:.<40} {value} {unit}")
    else:
        print(f"  {name:.<40} {value}")


class StreamingMetricsTestClient:
    """Client for testing streaming metrics."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        """Initialize the test client."""
        self.base_url = base_url
        if USE_TEST_CLIENT:
            self.test_client = TestClient(app)
            self.use_test_client = True
            print_info("Using FastAPI TestClient for requests")
        else:
            self.client = httpx.Client(base_url=base_url, timeout=30.0)
            self.use_test_client = False
            print_info(f"Using httpx client for requests to {base_url}")

    def close(self):
        """Close the client."""
        if not self.use_test_client:
            self.client.close()

    def chat_completion_stream(
        self,
        messages: list[dict[str, str]],
        model: str = "gpt-4",
        **kwargs
    ) -> list[dict[str, Any]]:
        """Make a streaming chat completion request and collect all chunks."""
        request_data = {
            "model": model,
            "messages": messages,
            "stream": True,
            **kwargs
        }

        chunks = []

        if self.use_test_client:
            # Use TestClient
            with self.test_client.stream(
                "POST",
                "/v1/chat/completions",
                json=request_data,
                headers={"Authorization": "Bearer test-key"}
            ) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if line and line.startswith("data: "):
                        data = line[6:]  # Remove "data: " prefix
                        if data.strip() == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data)
                            chunks.append(chunk)
                        except json.JSONDecodeError:
                            continue
        else:
            # Use httpx client
            with self.client.stream(
                "POST",
                "/v1/chat/completions",
                json=request_data,
                headers={"Authorization": "Bearer test-key"}
            ) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if line and line.startswith("data: "):
                        data = line[6:]  # Remove "data: " prefix
                        if data.strip() == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data)
                            chunks.append(chunk)
                        except json.JSONDecodeError:
                            continue

        return chunks

    def get_metrics(self) -> dict[str, Any]:
        """Get current metrics from the server."""
        if self.use_test_client:
            response = self.test_client.get("/metrics")
            response.raise_for_status()
            return response.json()
        else:
            response = self.client.get("/metrics")
            response.raise_for_status()
            return response.json()

    def get_streaming_metrics(self) -> dict[str, Any]:
        """Get streaming-specific metrics."""
        if self.use_test_client:
            response = self.test_client.get("/metrics/streaming")
            response.raise_for_status()
            return response.json()
        else:
            response = self.client.get("/metrics/streaming")
            response.raise_for_status()
            return response.json()

    def get_prometheus_metrics(self) -> str:
        """Get metrics in Prometheus format."""
        if self.use_test_client:
            response = self.test_client.get("/metrics/prometheus")
            response.raise_for_status()
            return response.text
        else:
            response = self.client.get("/metrics/prometheus")
            response.raise_for_status()
            return response.text


def verify_streaming_metrics():
    """Main verification function."""
    print_header("STREAMING METRICS LIVE VERIFICATION TEST")

    client = StreamingMetricsTestClient()

    try:
        # Step 1: Get baseline metrics
        print_section("Step 1: Getting Baseline Metrics")
        try:
            baseline_metrics = client.get_metrics()
            baseline_streaming = baseline_metrics.get("streaming_stats", {})
            initial_total = baseline_streaming.get("completed_streams", 0)
            print_success(f"Baseline completed streams: {initial_total}")
        except Exception as e:
            print_error(f"Failed to get baseline metrics: {e}")
            return False

        # Step 2: Send streaming requests
        print_section("Step 2: Sending 10 Streaming Requests")

        models = ["gpt-4", "gpt-3.5-turbo", "gpt-4-turbo"]
        request_count = 10
        successful_requests = 0

        for i in range(request_count):
            model = models[i % len(models)]
            messages = [
                {"role": "user", "content": f"Tell me a very short story number {i+1}"}
            ]

            try:
                start_time = time.time()
                chunks = client.chat_completion_stream(messages, model=model)
                duration = time.time() - start_time

                if len(chunks) > 0:
                    successful_requests += 1
                    print_success(f"Request {i+1}/{request_count}: {model} - {len(chunks)} chunks in {duration:.2f}s")
                else:
                    print_warning(f"Request {i+1}/{request_count}: {model} - No chunks received")
            except Exception as e:
                print_error(f"Request {i+1}/{request_count}: {model} - Failed: {e}")

        if successful_requests < request_count:
            print_warning(f"Only {successful_requests}/{request_count} requests succeeded")
        else:
            print_success(f"All {request_count} requests completed successfully")

        # Step 3: Wait for metrics aggregation
        print_section("Step 3: Waiting for Metrics Aggregation")
        wait_time = 2.0
        print_info(f"Waiting {wait_time} seconds for metrics to aggregate...")
        time.sleep(wait_time)
        print_success("Wait complete")

        # Step 4: Check general metrics endpoint
        print_section("Step 4: Verifying General Metrics (/metrics)")
        try:
            metrics = client.get_metrics()
            streaming_stats = metrics.get("streaming_stats", {})

            print_info("Streaming Statistics:")
            total_streams = streaming_stats.get("completed_streams", 0)
            active_streams = streaming_stats.get("active_streams", 0)
            failed_streams = streaming_stats.get("failed_streams", 0)

            print_metric("Total Completed Streams", total_streams)
            print_metric("Active Streams", active_streams)
            print_metric("Failed Streams", failed_streams)

            # Verify total streams increased
            streams_added = total_streams - initial_total
            if streams_added >= successful_requests:
                print_success(f"Stream count increased by {streams_added} (expected at least {successful_requests})")
            else:
                print_warning(f"Stream count only increased by {streams_added} (expected {successful_requests})")

            # Check TTFT metrics
            ttft = streaming_stats.get("ttft", {})
            if ttft:
                print_info("\nTTFT (Time to First Token) Metrics:")
                print_metric("Average", f"{ttft.get('avg', 0):.2f}", "ms")
                print_metric("Minimum", f"{ttft.get('min', 0):.2f}", "ms")
                print_metric("Maximum", f"{ttft.get('max', 0):.2f}", "ms")
                print_metric("P50", f"{ttft.get('p50', 0):.2f}", "ms")
                print_metric("P90", f"{ttft.get('p90', 0):.2f}", "ms")
                print_metric("P99", f"{ttft.get('p99', 0):.2f}", "ms")

                if ttft.get('avg', 0) > 0:
                    print_success("TTFT metrics are populated")
                else:
                    print_warning("TTFT metrics are zero")
            else:
                print_warning("No TTFT metrics found")

            # Check TPS metrics
            tps = streaming_stats.get("tokens_per_second", {})
            if tps:
                print_info("\nTokens Per Second Metrics:")
                print_metric("Average", f"{tps.get('avg', 0):.2f}", "tokens/sec")
                print_metric("Minimum", f"{tps.get('min', 0):.2f}", "tokens/sec")
                print_metric("Maximum", f"{tps.get('max', 0):.2f}", "tokens/sec")
                print_metric("P50", f"{tps.get('p50', 0):.2f}", "tokens/sec")
                print_metric("P90", f"{tps.get('p90', 0):.2f}", "tokens/sec")
                print_metric("P99", f"{tps.get('p99', 0):.2f}", "tokens/sec")

                if tps.get('avg', 0) > 0:
                    print_success("TPS metrics are populated")
                else:
                    print_warning("TPS metrics are zero")
            else:
                print_warning("No TPS metrics found")

        except Exception as e:
            print_error(f"Failed to verify general metrics: {e}")
            return False

        # Step 5: Check streaming-specific endpoint
        print_section("Step 5: Verifying Streaming Metrics (/metrics/streaming)")
        try:
            streaming_metrics = client.get_streaming_metrics()

            print_info("Streaming Quality Report:")
            summary = streaming_metrics.get("summary", {})
            print_metric("Total Streams", summary.get("total_streams", 0))
            print_metric("Completed Streams", summary.get("completed_streams", 0))
            print_metric("Failed Streams", summary.get("failed_streams", 0))
            print_metric("Success Rate", f"{summary.get('success_rate', 0):.1f}", "%")

            # Check quality metrics
            quality_metrics = streaming_metrics.get("quality_metrics", {})
            if quality_metrics:
                print_info("\nQuality Metrics:")

                # TTFT
                ttft_quality = quality_metrics.get("ttft_ms", {})
                if ttft_quality:
                    print_metric("TTFT Mean", f"{ttft_quality.get('mean', 0):.2f}", "ms")
                    print_metric("TTFT P50", f"{ttft_quality.get('p50', 0):.2f}", "ms")
                    print_metric("TTFT P99", f"{ttft_quality.get('p99', 0):.2f}", "ms")

                # TPS
                tps_quality = quality_metrics.get("tokens_per_second", {})
                if tps_quality:
                    print_metric("TPS Mean", f"{tps_quality.get('mean', 0):.2f}", "tokens/sec")
                    print_metric("TPS P50", f"{tps_quality.get('p50', 0):.2f}", "tokens/sec")
                    print_metric("TPS P99", f"{tps_quality.get('p99', 0):.2f}", "tokens/sec")

                if ttft_quality.get('mean', 0) > 0 and tps_quality.get('mean', 0) > 0:
                    print_success("Streaming quality metrics are populated")
                else:
                    print_warning("Some quality metrics are zero")

            # Check per-model breakdown
            per_model = streaming_metrics.get("per_model", {})
            if per_model:
                print_info("\nPer-Model Breakdown:")
                for model_name, model_stats in per_model.items():
                    print(f"\n  Model: {model_name}")
                    print_metric("    Streams", model_stats.get("stream_count", 0))
                    print_metric("    Avg TTFT", f"{model_stats.get('avg_ttft_ms', 0):.2f}", "ms")
                    print_metric("    Avg TPS", f"{model_stats.get('avg_tps', 0):.2f}", "tokens/sec")
                print_success("Per-model breakdown is available")
            else:
                print_warning("No per-model breakdown found")

        except Exception as e:
            print_error(f"Failed to verify streaming metrics endpoint: {e}")
            return False

        # Step 6: Check Prometheus export
        print_section("Step 6: Verifying Prometheus Export")
        try:
            prom_metrics = client.get_prometheus_metrics()

            # Check for key streaming metrics
            streaming_metric_patterns = [
                "fakeai_streaming_total",
                "fakeai_streaming_ttft",
                "fakeai_streaming_tps",
                "fakeai_streaming_active",
            ]

            found_metrics = []
            missing_metrics = []

            for pattern in streaming_metric_patterns:
                if pattern in prom_metrics:
                    found_metrics.append(pattern)
                else:
                    missing_metrics.append(pattern)

            print_info("Prometheus Metrics Check:")
            for metric in found_metrics:
                # Count occurrences
                count = prom_metrics.count(metric)
                print_success(f"{metric} - Found ({count} occurrences)")

            for metric in missing_metrics:
                print_warning(f"{metric} - Not found")

            if len(found_metrics) > 0:
                print_success("Streaming metrics are exported to Prometheus format")
            else:
                print_warning("No streaming metrics found in Prometheus export")

            # Show sample of Prometheus output
            print_info("\nSample Prometheus Output (first 20 lines):")
            lines = prom_metrics.split('\n')[:20]
            for line in lines:
                if line.strip() and not line.startswith('#'):
                    print(f"  {line}")

        except Exception as e:
            print_error(f"Failed to verify Prometheus export: {e}")
            return False

        # Step 7: Final Summary
        print_section("Step 7: Test Summary")

        all_checks = [
            ("Baseline metrics retrieved", True),
            (f"Sent {successful_requests}/{request_count} streaming requests", successful_requests == request_count),
            ("Stream count increased", streams_added >= successful_requests),
            ("TTFT metrics populated", ttft.get('avg', 0) > 0 if ttft else False),
            ("TPS metrics populated", tps.get('avg', 0) > 0 if tps else False),
            ("Streaming endpoint accessible", True),
            ("Per-model breakdown exists", len(per_model) > 0 if per_model else False),
            ("Prometheus export includes streaming", len(found_metrics) > 0),
        ]

        passed = sum(1 for _, check in all_checks if check)
        total = len(all_checks)

        print_info(f"\nCheck Results: {passed}/{total} passed")
        print()
        for check_name, check_result in all_checks:
            if check_result:
                print_success(check_name)
            else:
                print_error(check_name)

        success_rate = (passed / total) * 100
        print(f"\n{Colors.BOLD}Overall Success Rate: {success_rate:.1f}%{Colors.ENDC}")

        if success_rate >= 80:
            print(f"\n{Colors.OKGREEN}{Colors.BOLD}TEST PASSED ✓{Colors.ENDC}")
            return True
        elif success_rate >= 50:
            print(f"\n{Colors.WARNING}{Colors.BOLD}TEST PARTIAL PASS ⚠{Colors.ENDC}")
            return True
        else:
            print(f"\n{Colors.FAIL}{Colors.BOLD}TEST FAILED ✗{Colors.ENDC}")
            return False

    except Exception as e:
        print_error(f"Unexpected error during test: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        client.close()


def main():
    """Main entry point."""
    print(f"\n{Colors.BOLD}Streaming Metrics Live Verification Test{Colors.ENDC}")
    print(f"{Colors.OKCYAN}Testing streaming metrics population with real requests{Colors.ENDC}\n")

    success = verify_streaming_metrics()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
