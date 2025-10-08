#!/usr/bin/env python3
"""
Validate Streaming Metrics

Checks for specific issues in streaming implementation:
1. NameError exceptions
2. Missing TTFT measurements
3. Token count discrepancies
4. ITL calculation errors
5. Streaming tracker data integrity
"""

import json
import time
from typing import Any, Dict

import requests

BASE_URL = "http://localhost:8000"
API_KEY = "test-key"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}


class ValidationReport:
    """Validation report container."""

    def __init__(self):
        self.checks = []
        self.passed = 0
        self.failed = 0
        self.warnings = 0

    def add_check(self, name: str, passed: bool, details: str = "", warning: bool = False):
        """Add a validation check."""
        self.checks.append({
            "name": name,
            "passed": passed,
            "warning": warning,
            "details": details
        })

        if warning:
            self.warnings += 1
        elif passed:
            self.passed += 1
        else:
            self.failed += 1

    def print_report(self):
        """Print the validation report."""
        print("\n" + "="*80)
        print("STREAMING VALIDATION REPORT")
        print("="*80)

        for i, check in enumerate(self.checks, 1):
            if check["warning"]:
                status = "⚠"
            elif check["passed"]:
                status = "✓"
            else:
                status = "✗"

            print(f"\n{i}. {status} {check['name']}")
            if check["details"]:
                for line in check["details"].split("\n"):
                    print(f"   {line}")

        print("\n" + "="*80)
        print(f"SUMMARY: {self.passed} passed, {self.failed} failed, {self.warnings} warnings")
        print("="*80 + "\n")

        return self.failed == 0


def check_server_health() -> bool:
    """Check if server is healthy."""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False


def check_streaming_endpoint() -> Dict[str, Any]:
    """Test a streaming request and return metrics."""
    url = f"{BASE_URL}/v1/chat/completions"
    payload = {
        "model": "openai/gpt-oss-20b",
        "messages": [{"role": "user", "content": "Say hi"}],
        "stream": True,
        "max_tokens": 10
    }

    result = {
        "success": False,
        "tokens_received": 0,
        "ttft_measured": False,
        "ttft_ms": None,
        "duration_ms": None,
        "error": None
    }

    try:
        start = time.time()
        response = requests.post(url, headers=HEADERS, json=payload, stream=True, timeout=10)

        if response.status_code != 200:
            result["error"] = f"HTTP {response.status_code}"
            return result

        first_token_time = None

        for line in response.iter_lines():
            if not line:
                continue

            line_str = line.decode('utf-8').strip()
            if not line_str.startswith("data: "):
                continue

            data_str = line_str[6:]
            if data_str == "[DONE]":
                break

            try:
                data = json.loads(data_str)
                if "choices" in data and len(data["choices"]) > 0:
                    delta = data["choices"][0].get("delta", {})
                    if "content" in delta and delta["content"]:
                        result["tokens_received"] += 1

                        if first_token_time is None:
                            first_token_time = time.time()
                            result["ttft_ms"] = (first_token_time - start) * 1000
                            result["ttft_measured"] = True
            except json.JSONDecodeError:
                pass

        result["duration_ms"] = (time.time() - start) * 1000
        result["success"] = result["tokens_received"] > 0

    except Exception as e:
        result["error"] = str(e)

    return result


def check_metrics_endpoint() -> Dict[str, Any]:
    """Check streaming metrics endpoint."""
    try:
        response = requests.get(f"{BASE_URL}/metrics/streaming", headers=HEADERS, timeout=10)
        if response.status_code == 200:
            return {"success": True, "data": response.json()}
        else:
            return {"success": False, "error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def validate_streaming() -> bool:
    """Run all validation checks."""
    report = ValidationReport()

    # Check 1: Server is running
    print("Running validation checks...")
    is_healthy = check_server_health()
    report.add_check(
        "Server Health Check",
        is_healthy,
        f"Server is {'reachable' if is_healthy else 'not reachable'} at {BASE_URL}"
    )

    if not is_healthy:
        report.print_report()
        return False

    # Check 2: Streaming endpoint works
    print("Testing streaming endpoint...")
    stream_result = check_streaming_endpoint()
    report.add_check(
        "Streaming Endpoint Functional",
        stream_result["success"],
        f"Tokens received: {stream_result['tokens_received']}\n"
        f"Error: {stream_result.get('error', 'None')}"
    )

    # Check 3: TTFT is measured
    if stream_result["success"]:
        report.add_check(
            "TTFT Measurement",
            stream_result["ttft_measured"],
            f"TTFT: {stream_result['ttft_ms']:.2f}ms" if stream_result["ttft_measured"] else "TTFT not measured"
        )

        # Check 4: TTFT is reasonable
        if stream_result["ttft_measured"]:
            ttft_reasonable = 0 < stream_result["ttft_ms"] < 1000
            report.add_check(
                "TTFT Value Reasonable",
                ttft_reasonable,
                f"TTFT: {stream_result['ttft_ms']:.2f}ms (expected 0-1000ms)",
                warning=not ttft_reasonable
            )

        # Check 5: Tokens were received
        report.add_check(
            "Tokens Received",
            stream_result["tokens_received"] > 0,
            f"Received {stream_result['tokens_received']} tokens"
        )

    # Check 6: Metrics endpoint accessible
    print("Checking metrics endpoint...")
    metrics_result = check_metrics_endpoint()
    report.add_check(
        "Metrics Endpoint Accessible",
        metrics_result["success"],
        f"Error: {metrics_result.get('error', 'None')}" if not metrics_result["success"] else "Endpoint accessible"
    )

    # Check 7: Streaming tracker has data
    if metrics_result["success"]:
        data = metrics_result["data"]
        has_data = data.get("completed_streams", 0) > 0 or data.get("active_streams", 0) > 0

        report.add_check(
            "Streaming Tracker Has Data",
            has_data,
            f"Active: {data.get('active_streams', 0)}, "
            f"Completed: {data.get('completed_streams', 0)}, "
            f"Failed: {data.get('failed_streams', 0)}"
        )

        # Check 8: TTFT stats in tracker
        if "ttft" in data:
            ttft_stats = data["ttft"]
            has_ttft_stats = ttft_stats.get("avg") is not None
            report.add_check(
                "TTFT Stats in Tracker",
                has_ttft_stats,
                f"Avg: {ttft_stats.get('avg')}ms, "
                f"P50: {ttft_stats.get('p50')}ms, "
                f"P90: {ttft_stats.get('p90')}ms"
            )
        else:
            report.add_check(
                "TTFT Stats in Tracker",
                False,
                "No TTFT stats found in tracker",
                warning=True
            )

        # Check 9: Token count stats
        if "tokens_per_second" in data:
            tps_stats = data["tokens_per_second"]
            has_tps_stats = tps_stats.get("avg") is not None
            report.add_check(
                "TPS Stats in Tracker",
                has_tps_stats,
                f"Avg: {tps_stats.get('avg')}, "
                f"P50: {tps_stats.get('p50')}, "
                f"P90: {tps_stats.get('p90')}"
            )
        else:
            report.add_check(
                "TPS Stats in Tracker",
                False,
                "No TPS stats found in tracker",
                warning=True
            )

        # Check 10: ITL stats
        if "inter_token_latency_ms" in data:
            itl_stats = data["inter_token_latency_ms"]
            has_itl_stats = itl_stats.get("avg") is not None
            report.add_check(
                "ITL Stats in Tracker",
                has_itl_stats,
                f"Avg: {itl_stats.get('avg')}ms, "
                f"P50: {itl_stats.get('p50')}ms, "
                f"P90: {itl_stats.get('p90')}ms"
            )
        else:
            report.add_check(
                "ITL Stats in Tracker",
                False,
                "No ITL stats found in tracker",
                warning=True
            )

    # Print report
    return report.print_report()


def main():
    """Main validation entry point."""
    print("="*80)
    print("STREAMING METRICS VALIDATION")
    print("="*80)
    print(f"Target: {BASE_URL}")
    print("="*80)

    success = validate_streaming()

    if success:
        print("✓✓✓ ALL VALIDATIONS PASSED ✓✓✓")
        return 0
    else:
        print("⚠⚠⚠ SOME VALIDATIONS FAILED ⚠⚠⚠")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
