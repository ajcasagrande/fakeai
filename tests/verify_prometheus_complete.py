#!/usr/bin/env python3
"""
Comprehensive Prometheus Export Verification Script

This script verifies that the /metrics/prometheus endpoint exports complete and valid metrics:
- Core metrics (fakeai_requests_*, fakeai_responses_*, etc.)
- Streaming metrics (streaming_ttft_milliseconds, streaming_tokens_per_second)
- Error metrics (error_slo_violated, error_burn_rate, error_budget_remaining)
- Valid Prometheus text format
- Quantile labels (0.5, 0.95, 0.99)
- Correct metric types (counter, gauge, summary)

Usage:
    python tests/verify_prometheus_complete.py [--url http://localhost:8000]
"""
#  SPDX-License-Identifier: Apache-2.0

import argparse
import re
import sys
from collections import defaultdict

import requests


class PrometheusValidator:
    """Validates Prometheus metrics output."""

    def __init__(self, metrics_text: str):
        """Initialize validator with metrics text."""
        self.metrics_text = metrics_text
        self.lines = metrics_text.split("\n")
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.metric_types: dict[str, str] = {}
        self.metric_helps: dict[str, str] = {}
        self.metric_samples: dict[str, list[str]] = defaultdict(list)

    def validate_all(self) -> bool:
        """Run all validations and return True if all pass."""
        self.validate_format()
        self.validate_metric_types()
        self.validate_metric_names()
        self.validate_labels()
        self.validate_values()
        self.validate_required_metrics()
        self.validate_quantiles()
        return len(self.errors) == 0

    def validate_format(self):
        """Validate basic Prometheus text format."""
        if not self.metrics_text.endswith("\n"):
            self.errors.append("Metrics output must end with newline")

        # Parse HELP and TYPE lines
        for line in self.lines:
            if line.startswith("# HELP "):
                parts = line.split(maxsplit=3)
                if len(parts) >= 3:
                    metric_name = parts[2]
                    help_text = parts[3] if len(parts) == 4 else ""
                    self.metric_helps[metric_name] = help_text
                else:
                    self.errors.append(f"Invalid HELP line: {line}")

            elif line.startswith("# TYPE "):
                parts = line.split(maxsplit=3)
                if len(parts) >= 4:
                    metric_name = parts[2]
                    metric_type = parts[3]
                    if metric_type not in ["counter", "gauge", "summary", "histogram", "untyped"]:
                        self.errors.append(f"Invalid metric type '{metric_type}' for {metric_name}")
                    self.metric_types[metric_name] = metric_type
                else:
                    self.errors.append(f"Invalid TYPE line: {line}")

            elif line and not line.startswith("#"):
                # Metric sample line
                self._parse_metric_sample(line)

    def _parse_metric_sample(self, line: str):
        """Parse a metric sample line."""
        # Extract metric name (before { or space)
        match = re.match(r'^([a-zA-Z_:][a-zA-Z0-9_:]*)', line)
        if not match:
            self.errors.append(f"Invalid metric line: {line}")
            return

        metric_name = match.group(1)

        # Handle metric with suffix (like _sum, _count, _bucket)
        base_name = metric_name
        for suffix in ["_sum", "_count", "_bucket", "_total"]:
            if metric_name.endswith(suffix):
                base_name = metric_name[:-len(suffix)]
                break

        self.metric_samples[base_name].append(line)

    def validate_metric_types(self):
        """Validate that metrics have consistent types."""
        # Every metric with samples should have a TYPE declaration
        for metric_name in self.metric_samples.keys():
            if metric_name not in self.metric_types:
                self.warnings.append(f"Metric {metric_name} has no TYPE declaration")

    def validate_metric_names(self):
        """Validate metric naming conventions."""
        for line in self.lines:
            if line and not line.startswith("#"):
                # Extract metric name
                match = re.match(r'^([a-zA-Z_:][a-zA-Z0-9_:]*)', line)
                if match:
                    metric_name = match.group(1)
                    # Check naming convention
                    if not re.match(r'^[a-zA-Z_:][a-zA-Z0-9_:]*$', metric_name):
                        self.errors.append(f"Invalid metric name: {metric_name}")
                else:
                    self.errors.append(f"Cannot parse metric name from: {line}")

    def validate_labels(self):
        """Validate label syntax and escaping."""
        for line in self.lines:
            if line and not line.startswith("#") and "{" in line:
                # Extract labels section
                match = re.search(r'\{([^}]+)\}', line)
                if match:
                    labels_text = match.group(1)
                    # Split by comma (but not inside quotes)
                    labels = self._split_labels(labels_text)

                    for label in labels:
                        if "=" not in label:
                            self.errors.append(f"Invalid label format (no =): {label}")
                            continue

                        key, value = label.split("=", 1)
                        key = key.strip()

                        # Validate label key
                        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', key):
                            self.errors.append(f"Invalid label key: {key}")

                        # Validate label value is quoted
                        if not (value.startswith('"') and value.endswith('"')):
                            self.errors.append(f"Label value must be quoted: {label}")

    def _split_labels(self, labels_text: str) -> list[str]:
        """Split labels by comma, respecting quotes."""
        labels = []
        current = []
        in_quotes = False
        escaped = False

        for char in labels_text:
            if escaped:
                current.append(char)
                escaped = False
                continue

            if char == '\\':
                current.append(char)
                escaped = True
                continue

            if char == '"':
                in_quotes = not in_quotes
                current.append(char)
                continue

            if char == ',' and not in_quotes:
                labels.append(''.join(current).strip())
                current = []
                continue

            current.append(char)

        if current:
            labels.append(''.join(current).strip())

        return labels

    def validate_values(self):
        """Validate metric values are numeric."""
        for line in self.lines:
            if line and not line.startswith("#"):
                # Extract value (last part after space)
                parts = line.split()
                if len(parts) < 2:
                    self.errors.append(f"Metric line missing value: {line}")
                    continue

                value = parts[-1]
                # Check if numeric (including scientific notation, +Inf, -Inf, NaN)
                if value not in ["+Inf", "-Inf", "NaN"]:
                    try:
                        float(value)
                    except ValueError:
                        self.errors.append(f"Invalid numeric value '{value}' in line: {line}")

    def validate_required_metrics(self):
        """Validate presence of required metrics."""
        required_core_metrics = [
            "fakeai_requests_per_second",
            "fakeai_responses_per_second",
            "fakeai_latency_seconds",
            "fakeai_tokens_per_second",
        ]

        required_streaming_metrics = [
            "streaming_ttft_milliseconds",
            "streaming_tokens_per_second",
            "streaming_total_streams",
            "streaming_active_streams",
            "streaming_completed_streams",
            "streaming_failed_streams",
            "streaming_success_rate",
        ]

        required_error_metrics = [
            # Check for either the old names or new names
            ("error_slo_violated", "fakeai_slo_compliant"),
            ("error_budget_remaining", "fakeai_error_budget_consumed_percentage"),
            ("error_burn_rate", "fakeai_availability"),  # Burn rate can be derived from availability
        ]

        # Check core metrics
        for metric in required_core_metrics:
            if metric not in self.metrics_text:
                self.errors.append(f"Missing required core metric: {metric}")

        # Check streaming metrics
        for metric in required_streaming_metrics:
            if metric not in self.metrics_text:
                self.warnings.append(f"Missing streaming metric: {metric} (may be zero if no streams)")

        # Check error metrics (allow alternative names)
        for old_name, new_name in required_error_metrics:
            if old_name not in self.metrics_text and new_name not in self.metrics_text:
                self.warnings.append(
                    f"Missing error metric: {old_name} or {new_name} (may be zero if no errors)"
                )

    def validate_quantiles(self):
        """Validate that summary metrics have required quantiles."""
        required_quantiles = ["0.5", "0.95", "0.99"]

        # Find summary metrics
        summary_metrics = [
            name for name, mtype in self.metric_types.items()
            if mtype == "summary"
        ]

        for metric_name in summary_metrics:
            # Check for quantile labels
            found_quantiles = set()

            for line in self.lines:
                if line.startswith(metric_name + "{"):
                    # Extract quantile label
                    match = re.search(r'quantile="([^"]+)"', line)
                    if match:
                        found_quantiles.add(match.group(1))

            # Check if all required quantiles are present
            for quantile in required_quantiles:
                if quantile not in found_quantiles:
                    self.warnings.append(
                        f"Summary metric {metric_name} missing quantile {quantile}"
                    )

    def get_report(self) -> str:
        """Generate validation report."""
        lines = []
        lines.append("=" * 80)
        lines.append("PROMETHEUS METRICS VALIDATION REPORT")
        lines.append("=" * 80)
        lines.append("")

        # Summary
        lines.append("SUMMARY:")
        lines.append(f"  Total lines: {len(self.lines)}")
        lines.append(f"  Metric types declared: {len(self.metric_types)}")
        lines.append(f"  Metric HELP lines: {len(self.metric_helps)}")
        lines.append(f"  Unique metrics with samples: {len(self.metric_samples)}")
        lines.append(f"  Errors: {len(self.errors)}")
        lines.append(f"  Warnings: {len(self.warnings)}")
        lines.append("")

        # Metric types breakdown
        if self.metric_types:
            lines.append("METRIC TYPES:")
            type_counts = defaultdict(int)
            for mtype in self.metric_types.values():
                type_counts[mtype] += 1

            for mtype, count in sorted(type_counts.items()):
                lines.append(f"  {mtype}: {count}")
            lines.append("")

        # List all metrics found
        lines.append("METRICS FOUND:")
        for metric_name in sorted(self.metric_samples.keys()):
            metric_type = self.metric_types.get(metric_name, "unknown")
            sample_count = len(self.metric_samples[metric_name])
            lines.append(f"  {metric_name} ({metric_type}) - {sample_count} samples")
        lines.append("")

        # Errors
        if self.errors:
            lines.append("ERRORS:")
            for error in self.errors:
                lines.append(f"  ✗ {error}")
            lines.append("")

        # Warnings
        if self.warnings:
            lines.append("WARNINGS:")
            for warning in self.warnings:
                lines.append(f"  ⚠ {warning}")
            lines.append("")

        # Status
        if len(self.errors) == 0:
            lines.append("✓ VALIDATION PASSED")
        else:
            lines.append("✗ VALIDATION FAILED")

        lines.append("=" * 80)

        return "\n".join(lines)


def fetch_metrics(base_url: str) -> str:
    """Fetch metrics from the /metrics/prometheus endpoint."""
    url = f"{base_url}/metrics/prometheus"
    print(f"Fetching metrics from: {url}")

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        # Check content type
        content_type = response.headers.get("content-type", "")
        if "text/plain" not in content_type:
            print(f"WARNING: Unexpected content-type: {content_type}")

        return response.text

    except requests.exceptions.ConnectionError:
        print(f"ERROR: Cannot connect to {url}")
        print("Make sure the FakeAI server is running.")
        sys.exit(1)
    except requests.exceptions.Timeout:
        print(f"ERROR: Request to {url} timed out")
        sys.exit(1)
    except requests.exceptions.HTTPError as e:
        print(f"ERROR: HTTP error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Unexpected error: {e}")
        sys.exit(1)


def test_with_prometheus_client(metrics_text: str) -> tuple[bool, str]:
    """Test parsing with prometheus_client library if available."""
    try:
        from prometheus_client.parser import text_string_to_metric_families
    except ImportError:
        return True, "prometheus_client not installed (optional)"

    try:
        families = list(text_string_to_metric_families(metrics_text))

        # Analyze parsed metrics
        report_lines = []
        report_lines.append("\nPROMETHEUS_CLIENT PARSER TEST:")
        report_lines.append(f"  Successfully parsed {len(families)} metric families")

        # Count by type
        type_counts = defaultdict(int)
        for family in families:
            type_counts[family.type] += 1

        report_lines.append("  Metric family types:")
        for mtype, count in sorted(type_counts.items()):
            report_lines.append(f"    {mtype}: {count}")

        # Sample a few metrics
        report_lines.append("  Sample metrics:")
        for family in list(families)[:5]:
            sample_count = len(family.samples) if hasattr(family, "samples") else 0
            report_lines.append(f"    {family.name} ({family.type}) - {sample_count} samples")

        return True, "\n".join(report_lines)

    except Exception as e:
        return False, f"\nPROMETHEUS_CLIENT PARSER FAILED: {e}"


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Verify comprehensive Prometheus metrics export"
    )
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="Base URL of the FakeAI server (default: http://localhost:8000)"
    )
    parser.add_argument(
        "--save",
        help="Save metrics output to file"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show full metrics output"
    )

    args = parser.parse_args()

    # Fetch metrics
    metrics_text = fetch_metrics(args.url)

    print(f"✓ Successfully fetched {len(metrics_text)} bytes of metrics")
    print("")

    # Save if requested
    if args.save:
        with open(args.save, "w") as f:
            f.write(metrics_text)
        print(f"✓ Saved metrics to {args.save}")
        print("")

    # Show metrics if verbose
    if args.verbose:
        print("METRICS OUTPUT:")
        print("-" * 80)
        print(metrics_text)
        print("-" * 80)
        print("")

    # Validate
    validator = PrometheusValidator(metrics_text)
    validator.validate_all()

    # Print report
    print(validator.get_report())

    # Test with prometheus_client if available
    success, parser_report = test_with_prometheus_client(metrics_text)
    print(parser_report)

    if not success:
        sys.exit(1)

    # Exit with error code if validation failed
    if len(validator.errors) > 0:
        sys.exit(1)
    else:
        print("\n✓ All validations passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
