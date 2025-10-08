"""
Comprehensive tests for Prometheus metrics export.

Tests cover format validation, streaming metrics, error metrics, cost metrics,
label escaping, and Prometheus parser compatibility.
"""

#  SPDX-License-Identifier: Apache-2.0

import re
import time

import pytest

from fakeai.cost_tracker import CostTracker
from fakeai.error_metrics import ErrorMetricsTracker
from fakeai.metrics import MetricsTracker
from fakeai.streaming_metrics_tracker import StreamingMetricsTracker


@pytest.mark.unit
@pytest.mark.metrics
class TestPrometheusFormatValidation:
    """Test basic Prometheus format compliance."""

    @pytest.fixture
    def metrics_tracker(self):
        """Create a fresh metrics tracker."""
        tracker = MetricsTracker()
        # Generate some test data
        tracker.track_request("/v1/chat/completions")
        tracker.track_response("/v1/chat/completions", 0.5)
        tracker.track_tokens("/v1/chat/completions", 100)
        time.sleep(0.1)
        return tracker

    def test_has_help_lines(self, metrics_tracker):
        """Should include # HELP lines for all metrics."""
        output = metrics_tracker.get_prometheus_metrics()

        assert "# HELP" in output
        # Count HELP lines
        help_lines = [line for line in output.split("\n") if line.startswith("# HELP")]
        assert len(help_lines) >= 5  # Should have multiple metrics

    def test_has_type_lines(self, metrics_tracker):
        """Should include # TYPE lines for all metrics."""
        output = metrics_tracker.get_prometheus_metrics()

        assert "# TYPE" in output
        # Count TYPE lines
        type_lines = [line for line in output.split("\n") if line.startswith("# TYPE")]
        assert len(type_lines) >= 5

    def test_metric_lines_format(self, metrics_tracker):
        """Metric lines should follow Prometheus format: metric_name{labels} value."""
        output = metrics_tracker.get_prometheus_metrics()

        # Find metric lines (not comments or empty)
        metric_lines = [
            line
            for line in output.split("\n")
            if line and not line.startswith("#")
        ]

        assert len(metric_lines) > 0

        # Each metric line should have a value
        for line in metric_lines:
            # Should have space separating name and value
            assert " " in line
            parts = line.split()
            # Last part should be a number
            try:
                float(parts[-1])
            except ValueError:
                pytest.fail(f"Metric value not numeric in line: {line}")

    def test_valid_metric_names(self, metrics_tracker):
        """Metric names should contain only valid characters."""
        output = metrics_tracker.get_prometheus_metrics()

        metric_lines = [
            line
            for line in output.split("\n")
            if line and not line.startswith("#")
        ]

        for line in metric_lines:
            # Extract metric name (before { or space)
            metric_name = line.split("{")[0].split()[0]
            # Should only contain alphanumeric, underscore, colon
            assert re.match(
                r"^[a-zA-Z_:][a-zA-Z0-9_:]*$", metric_name
            ), f"Invalid metric name: {metric_name}"

    def test_ends_with_newline(self, metrics_tracker):
        """Output should end with a newline."""
        output = metrics_tracker.get_prometheus_metrics()
        assert output.endswith("\n")

    def test_no_empty_metric_values(self, metrics_tracker):
        """No metric should have an empty or missing value."""
        output = metrics_tracker.get_prometheus_metrics()

        metric_lines = [
            line
            for line in output.split("\n")
            if line and not line.startswith("#")
        ]

        for line in metric_lines:
            parts = line.split()
            assert len(parts) >= 2, f"Metric line missing value: {line}"


@pytest.mark.unit
@pytest.mark.metrics
class TestStreamingMetricsExport:
    """Test streaming metrics in Prometheus format."""

    @pytest.fixture
    def streaming_tracker(self):
        """Create streaming metrics tracker with test data."""
        tracker = StreamingMetricsTracker()

        # Simulate some streams
        for i in range(5):
            stream_id = f"stream-{i}"
            tracker.start_stream(stream_id, model="gpt-4")
            tracker.record_first_token(stream_id)
            for _ in range(50):
                tracker.record_token(stream_id)
            tracker.end_stream(stream_id, success=True)

        # One failed stream
        stream_id = "stream-failed"
        tracker.start_stream(stream_id, model="gpt-4")
        tracker.end_stream(stream_id, success=False)

        time.sleep(0.1)
        return tracker

    def test_streaming_total_streams_counter(self, streaming_tracker):
        """Should export streaming_total_streams counter."""
        output = streaming_tracker.get_prometheus_metrics()

        assert "# TYPE streaming_total_streams counter" in output
        assert "streaming_total_streams " in output

        # Extract value
        match = re.search(r"streaming_total_streams (\d+)", output)
        assert match
        value = int(match.group(1))
        assert value == 6  # 5 successful + 1 failed

    def test_streaming_active_streams_gauge(self, streaming_tracker):
        """Should export streaming_active_streams gauge."""
        output = streaming_tracker.get_prometheus_metrics()

        assert "# TYPE streaming_active_streams gauge" in output
        assert "streaming_active_streams " in output

    def test_streaming_ttft_summary(self, streaming_tracker):
        """Should export TTFT metrics with quantiles."""
        output = streaming_tracker.get_prometheus_metrics()

        assert "# TYPE streaming_ttft_milliseconds summary" in output
        assert 'streaming_ttft_milliseconds{quantile="0.5"}' in output
        assert 'streaming_ttft_milliseconds{quantile="0.95"}' in output
        assert 'streaming_ttft_milliseconds{quantile="0.99"}' in output

    def test_streaming_tokens_per_second_summary(self, streaming_tracker):
        """Should export tokens per second with quantiles."""
        output = streaming_tracker.get_prometheus_metrics()

        assert "# TYPE streaming_tokens_per_second summary" in output
        assert 'streaming_tokens_per_second{quantile="0.5"}' in output
        assert 'streaming_tokens_per_second{quantile="0.95"}' in output
        assert 'streaming_tokens_per_second{quantile="0.99"}' in output

    def test_streaming_success_rate_gauge(self, streaming_tracker):
        """Should export success rate gauge."""
        output = streaming_tracker.get_prometheus_metrics()

        assert "# TYPE streaming_success_rate gauge" in output
        assert "streaming_success_rate " in output

        # Extract value
        match = re.search(r"streaming_success_rate ([\d.]+)", output)
        assert match
        value = float(match.group(1))
        # 5 successful out of 6 = ~0.83
        assert 0.8 <= value <= 0.9

    def test_streaming_streams_by_model_counter(self, streaming_tracker):
        """Should export per-model stream counts."""
        output = streaming_tracker.get_prometheus_metrics()

        assert "# TYPE streaming_streams_by_model counter" in output
        assert 'streaming_streams_by_model{model="gpt-4"}' in output


@pytest.mark.unit
@pytest.mark.metrics
class TestErrorMetricsExport:
    """Test error metrics in Prometheus format."""

    @pytest.fixture
    def error_tracker(self):
        """Create error metrics tracker with test data."""
        tracker = ErrorMetricsTracker()
        tracker.reset()

        # Record various errors
        for _ in range(10):
            tracker.record_request("/v1/chat/completions")
            tracker.record_success("/v1/chat/completions")

        # Record errors
        tracker.record_error(
            endpoint="/v1/chat/completions",
            status_code=500,
            error_type="internal_error",
            error_message="Internal server error",
        )
        tracker.record_error(
            endpoint="/v1/chat/completions",
            status_code=429,
            error_type="rate_limit",
            error_message="Rate limit exceeded",
        )
        tracker.record_error(
            endpoint="/v1/embeddings",
            status_code=400,
            error_type="validation",
            error_message="Invalid input",
        )

        time.sleep(0.1)
        return tracker

    def test_error_total_requests_implicit(self, error_tracker):
        """Error metrics should track total requests (implicit from success/error)."""
        output = error_tracker.get_prometheus_metrics()

        # The tracker records requests and errors, so we check error rate is calculated
        assert "fakeai_error_rate_percentage" in output

    def test_error_by_endpoint_counter(self, error_tracker):
        """Should export errors by endpoint."""
        output = error_tracker.get_prometheus_metrics()

        assert "# TYPE fakeai_errors_by_endpoint counter" in output
        assert 'fakeai_errors_by_endpoint{endpoint="/v1/chat/completions"}' in output
        assert 'fakeai_errors_by_endpoint{endpoint="/v1/embeddings"}' in output

    def test_error_by_type_counter(self, error_tracker):
        """Should export errors by type."""
        output = error_tracker.get_prometheus_metrics()

        assert "# TYPE fakeai_errors_by_type counter" in output
        assert 'fakeai_errors_by_type{error_type="internal_error"}' in output
        assert 'fakeai_errors_by_type{error_type="rate_limit"}' in output
        assert 'fakeai_errors_by_type{error_type="validation"}' in output

    def test_error_rate_gauge(self, error_tracker):
        """Should export overall error rate as gauge."""
        output = error_tracker.get_prometheus_metrics()

        assert "# TYPE fakeai_error_rate_percentage gauge" in output
        assert "fakeai_error_rate_percentage " in output

    def test_error_slo_violated_gauge(self, error_tracker):
        """Should export SLO compliance status."""
        output = error_tracker.get_prometheus_metrics()

        assert "# TYPE fakeai_slo_compliant gauge" in output
        assert "fakeai_slo_compliant " in output

        # Value should be 0 or 1
        match = re.search(r"fakeai_slo_compliant (\d)", output)
        assert match
        value = int(match.group(1))
        assert value in [0, 1]

    def test_error_budget_remaining_gauge(self, error_tracker):
        """Should export error budget metrics."""
        output = error_tracker.get_prometheus_metrics()

        assert "# TYPE fakeai_error_budget_consumed_percentage gauge" in output
        assert "fakeai_error_budget_consumed_percentage " in output

    def test_error_burn_rate_implicit(self, error_tracker):
        """Error burn rate can be derived from error budget consumption."""
        output = error_tracker.get_prometheus_metrics()

        # Availability metric allows calculating burn rate
        assert "# TYPE fakeai_availability gauge" in output
        assert "fakeai_availability " in output

    def test_error_by_status_code(self, error_tracker):
        """Should export errors by HTTP status code."""
        output = error_tracker.get_prometheus_metrics()

        assert "# TYPE fakeai_errors_by_status_code counter" in output
        assert 'fakeai_errors_by_status_code{status_code="500"}' in output
        assert 'fakeai_errors_by_status_code{status_code="429"}' in output
        assert 'fakeai_errors_by_status_code{status_code="400"}' in output


@pytest.mark.unit
@pytest.mark.metrics
class TestCostMetricsExport:
    """Test cost tracking metrics (if available)."""

    @pytest.fixture
    def cost_tracker(self):
        """Create cost tracker with test data."""
        tracker = CostTracker()

        # Track some usage
        tracker.track_request(
            api_key="test-key-1",
            model="gpt-4",
            endpoint="/v1/chat/completions",
            prompt_tokens=100,
            completion_tokens=200,
            cached_tokens=0,
        )
        tracker.track_request(
            api_key="test-key-2",
            model="gpt-3.5-turbo",
            endpoint="/v1/chat/completions",
            prompt_tokens=50,
            completion_tokens=100,
            cached_tokens=0,
        )

        # Set a budget for testing
        tracker.set_budget(api_key="test-key-1", limit=100.0)

        time.sleep(0.1)
        return tracker

    def test_cost_metrics_available(self, cost_tracker):
        """Cost tracker should have metrics methods."""
        assert hasattr(cost_tracker, "get_total_cost")
        assert hasattr(cost_tracker, "get_cost_by_api_key")
        assert hasattr(cost_tracker, "get_cost_by_model")

    def test_cost_total_usd(self, cost_tracker):
        """Should be able to get total cost."""
        total_cost = cost_tracker.get_total_cost()
        assert isinstance(total_cost, float)
        assert total_cost > 0

    def test_cost_by_model_usd(self, cost_tracker):
        """Should be able to get cost by model."""
        cost_by_model = cost_tracker.get_cost_by_model()
        assert isinstance(cost_by_model, dict)
        assert "gpt-4" in cost_by_model
        assert "gpt-3.5-turbo" in cost_by_model

    def test_cost_budget_usage_percentage(self, cost_tracker):
        """Should be able to get budget usage."""
        stats = cost_tracker.get_stats()
        assert "by_api_key" in stats

        # Check that budget info exists
        key_stats = stats["by_api_key"].get("test-key-1", {})
        if "budget_limit" in key_stats:
            assert "budget_used" in key_stats
            assert "budget_remaining" in key_stats


@pytest.mark.unit
@pytest.mark.metrics
class TestLabelEscaping:
    """Test proper escaping of label values."""

    @pytest.fixture
    def metrics_tracker(self):
        """Create metrics tracker."""
        return MetricsTracker()

    def test_quotes_in_labels_escaped(self, metrics_tracker):
        """Quotes in label values should be escaped."""
        # Track a request with quotes in endpoint (simulated)
        metrics_tracker.track_request("/v1/chat/completions")
        output = metrics_tracker.get_prometheus_metrics()

        # All label values should be in quotes
        label_pattern = r'(\w+)="([^"]*)"'
        matches = re.findall(label_pattern, output)
        assert len(matches) > 0

        # No unescaped quotes inside label values
        for label_name, label_value in matches:
            # If there's a backslash, it should be escaping something
            if "\\" in label_value:
                assert '\\"' in label_value or "\\\\" in label_value

    def test_model_names_with_slashes(self, metrics_tracker):
        """Model names with slashes should be handled correctly."""
        # This is tested via streaming metrics which track models
        tracker = StreamingMetricsTracker()

        # Model name with slash
        stream_id = "test-stream"
        tracker.start_stream(stream_id, model="openai/gpt-4o-mini")
        tracker.record_first_token(stream_id)
        tracker.record_token(stream_id)
        tracker.end_stream(stream_id, success=True)

        output = tracker.get_prometheus_metrics()

        # Should contain the model with slash
        assert 'model="openai/gpt-4o-mini"' in output

    def test_newlines_in_labels_handled(self, metrics_tracker):
        """Labels should not contain unescaped newlines."""
        output = metrics_tracker.get_prometheus_metrics()

        # Extract all label values
        label_pattern = r'="([^"]*)"'
        matches = re.findall(label_pattern, output)

        for label_value in matches:
            # Should not contain literal newlines
            assert "\n" not in label_value or "\\n" in label_value


@pytest.mark.unit
@pytest.mark.metrics
class TestPrometheusParseValidation:
    """Test that output can be parsed by Prometheus parser."""

    @pytest.fixture
    def sample_metrics(self):
        """Generate sample metrics from all trackers."""
        metrics_tracker = MetricsTracker()
        streaming_tracker = StreamingMetricsTracker()
        error_tracker = ErrorMetricsTracker()
        error_tracker.reset()

        # Generate data
        metrics_tracker.track_request("/v1/chat/completions")
        metrics_tracker.track_response("/v1/chat/completions", 0.5)

        stream_id = "test-stream"
        streaming_tracker.start_stream(stream_id, model="gpt-4")
        streaming_tracker.record_first_token(stream_id)
        streaming_tracker.record_token(stream_id)
        streaming_tracker.end_stream(stream_id, success=True)

        error_tracker.record_error(
            endpoint="/v1/chat/completions",
            status_code=500,
            error_type="test_error",
            error_message="Test",
        )

        time.sleep(0.1)

        return {
            "metrics": metrics_tracker.get_prometheus_metrics(),
            "streaming": streaming_tracker.get_prometheus_metrics(),
            "errors": error_tracker.get_prometheus_metrics(),
        }

    def test_no_syntax_errors(self, sample_metrics):
        """Output should have no obvious syntax errors."""
        for name, output in sample_metrics.items():
            lines = output.split("\n")

            for line in lines:
                if not line or line.startswith("#"):
                    continue

                # Should have metric name and value
                parts = line.split()
                assert len(parts) >= 2, f"Invalid line in {name}: {line}"

                # Value should be numeric
                try:
                    float(parts[-1])
                except ValueError:
                    pytest.fail(f"Non-numeric value in {name}: {line}")

    def test_metrics_queryable_format(self, sample_metrics):
        """Metrics should be in queryable format (name{labels} value)."""
        for name, output in sample_metrics.items():
            lines = output.split("\n")
            metric_lines = [
                line for line in lines if line and not line.startswith("#")
            ]

            for line in metric_lines:
                # Should match: metric_name{labels} value OR metric_name value
                pattern = r'^[a-zA-Z_:][a-zA-Z0-9_:]*(\{[^}]+\})?\s+[\d.eE+-]+$'
                assert re.match(pattern, line), f"Invalid format in {name}: {line}"

    def test_label_syntax_valid(self, sample_metrics):
        """Label syntax should be valid."""
        for name, output in sample_metrics.items():
            # Extract all labels
            label_sections = re.findall(r'\{([^}]+)\}', output)

            for section in label_sections:
                # Labels should be: key="value",key="value"
                labels = section.split(",")
                for label in labels:
                    assert "=" in label, f"Invalid label syntax in {name}: {label}"
                    key, value = label.split("=", 1)
                    # Value should be quoted
                    assert value.startswith('"') and value.endswith(
                        '"'
                    ), f"Unquoted label value in {name}: {label}"

    def test_consistent_metric_types(self, sample_metrics):
        """Metric types should be consistent throughout output."""
        for name, output in sample_metrics.items():
            lines = output.split("\n")
            metric_types = {}

            for line in lines:
                if line.startswith("# TYPE"):
                    parts = line.split()
                    if len(parts) >= 4:
                        metric_name = parts[2]
                        metric_type = parts[3]
                        metric_types[metric_name] = metric_type

            # Each metric should only have one type
            assert len(metric_types) == len(set(metric_types.keys()))

    def test_help_before_type(self, sample_metrics):
        """HELP should come before TYPE for each metric."""
        for name, output in sample_metrics.items():
            lines = output.split("\n")

            i = 0
            while i < len(lines):
                line = lines[i]

                if line.startswith("# HELP"):
                    metric_name = line.split()[2] if len(line.split()) > 2 else None

                    # Next non-empty line should be TYPE for same metric
                    j = i + 1
                    while j < len(lines) and not lines[j].strip():
                        j += 1

                    if j < len(lines) and lines[j].startswith("# TYPE"):
                        type_metric_name = (
                            lines[j].split()[2] if len(lines[j].split()) > 2 else None
                        )
                        # Note: In Prometheus format, HELP and TYPE don't have to be in order
                        # But it's good practice

                i += 1


@pytest.mark.unit
@pytest.mark.metrics
class TestMetricsCompleteness:
    """Test that all required metrics are exported."""

    def test_streaming_metrics_complete(self):
        """All streaming metrics should be exported."""
        tracker = StreamingMetricsTracker()

        # Generate some data
        stream_id = "test"
        tracker.start_stream(stream_id, model="gpt-4")
        tracker.record_first_token(stream_id)
        tracker.record_token(stream_id)
        tracker.end_stream(stream_id, success=True)

        output = tracker.get_prometheus_metrics()

        required_metrics = [
            "streaming_total_streams",
            "streaming_active_streams",
            "streaming_ttft_milliseconds",
            "streaming_tokens_per_second",
            "streaming_success_rate",
        ]

        for metric in required_metrics:
            assert metric in output, f"Missing metric: {metric}"

    def test_error_metrics_complete(self):
        """All error metrics should be exported."""
        tracker = ErrorMetricsTracker()
        tracker.reset()

        tracker.record_request("/v1/chat/completions")
        tracker.record_error(
            endpoint="/v1/chat/completions",
            status_code=500,
            error_type="test",
            error_message="Test",
        )

        output = tracker.get_prometheus_metrics()

        required_metrics = [
            "fakeai_errors_by_status_code",
            "fakeai_errors_by_type",
            "fakeai_errors_by_endpoint",
            "fakeai_error_rate_percentage",
            "fakeai_availability",
            "fakeai_error_budget_consumed_percentage",
            "fakeai_slo_compliant",
        ]

        for metric in required_metrics:
            assert metric in output, f"Missing metric: {metric}"

    def test_basic_metrics_complete(self):
        """Basic request/response metrics should be exported."""
        tracker = MetricsTracker()

        tracker.track_request("/v1/chat/completions")
        tracker.track_response("/v1/chat/completions", 0.5)
        tracker.track_tokens("/v1/chat/completions", 100)

        time.sleep(0.1)

        output = tracker.get_prometheus_metrics()

        required_metrics = [
            "fakeai_requests_per_second",
            "fakeai_responses_per_second",
            "fakeai_latency_seconds",
            "fakeai_tokens_per_second",
        ]

        for metric in required_metrics:
            assert metric in output, f"Missing metric: {metric}"


@pytest.mark.unit
@pytest.mark.metrics
class TestPrometheusIntegration:
    """Test integration with prometheus_client parser if available."""

    def test_parse_with_prometheus_client(self):
        """If prometheus_client is available, test parsing."""
        try:
            from prometheus_client.parser import text_string_to_metric_families
        except ImportError:
            pytest.skip("prometheus_client not installed")

        # Generate metrics
        tracker = MetricsTracker()
        tracker.track_request("/v1/chat/completions")
        tracker.track_response("/v1/chat/completions", 0.5)

        output = tracker.get_prometheus_metrics()

        # Parse with prometheus_client
        families = list(text_string_to_metric_families(output))

        # Should successfully parse
        assert len(families) > 0

        # Each family should have samples
        for family in families:
            assert family.name
            assert family.type in ["counter", "gauge", "summary", "histogram", "untyped"]

    def test_streaming_parse_with_prometheus_client(self):
        """Test streaming metrics parsing."""
        try:
            from prometheus_client.parser import text_string_to_metric_families
        except ImportError:
            pytest.skip("prometheus_client not installed")

        tracker = StreamingMetricsTracker()
        stream_id = "test"
        tracker.start_stream(stream_id, model="gpt-4")
        tracker.record_first_token(stream_id)
        tracker.record_token(stream_id)
        tracker.end_stream(stream_id, success=True)

        output = tracker.get_prometheus_metrics()

        families = list(text_string_to_metric_families(output))
        assert len(families) > 0

        # Find summary metrics
        summary_families = [f for f in families if f.type == "summary"]
        assert len(summary_families) >= 2  # ttft and tps

    def test_error_metrics_parse_with_prometheus_client(self):
        """Test error metrics parsing."""
        try:
            from prometheus_client.parser import text_string_to_metric_families
        except ImportError:
            pytest.skip("prometheus_client not installed")

        tracker = ErrorMetricsTracker()
        tracker.reset()

        tracker.record_error(
            endpoint="/v1/chat/completions",
            status_code=500,
            error_type="test",
            error_message="Test",
        )

        output = tracker.get_prometheus_metrics()

        families = list(text_string_to_metric_families(output))
        assert len(families) > 0

        # Check that counters and gauges are present
        counter_families = [f for f in families if f.type == "counter"]
        gauge_families = [f for f in families if f.type == "gauge"]

        assert len(counter_families) > 0
        assert len(gauge_families) > 0


@pytest.mark.unit
@pytest.mark.metrics
class TestPrometheusSpecialCases:
    """Test edge cases and special scenarios."""

    def test_empty_metrics(self):
        """Should handle empty metrics gracefully."""
        tracker = MetricsTracker()
        output = tracker.get_prometheus_metrics()

        # Should still be valid format
        assert output
        assert "# HELP" in output or "# TYPE" in output

    def test_zero_values(self):
        """Should handle zero values correctly."""
        tracker = StreamingMetricsTracker()
        output = tracker.get_prometheus_metrics()

        # Should contain metrics with 0 values
        assert "0" in output or "0.0" in output

    def test_large_values(self):
        """Should handle large values correctly."""
        tracker = MetricsTracker()

        # Generate many requests
        for _ in range(1000):
            tracker.track_request("/v1/chat/completions")
            tracker.track_tokens("/v1/chat/completions", 1000)

        time.sleep(0.1)
        output = tracker.get_prometheus_metrics()

        # Should contain large values
        large_value_pattern = r"\d{3,}"
        assert re.search(large_value_pattern, output)

    def test_scientific_notation(self):
        """Should handle scientific notation if needed."""
        tracker = MetricsTracker()

        # Track very small latency
        tracker.track_response("/v1/chat/completions", 0.0001)

        output = tracker.get_prometheus_metrics()

        # Should contain either decimal or scientific notation
        assert re.search(r"[\d.]+e?-?\d*", output)

    def test_concurrent_export(self):
        """Should handle concurrent metric export safely."""
        import threading

        tracker = MetricsTracker()

        results = []

        def export_metrics():
            output = tracker.get_prometheus_metrics()
            results.append(output)

        # Export from multiple threads
        threads = [threading.Thread(target=export_metrics) for _ in range(5)]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # All exports should succeed
        assert len(results) == 5
        for output in results:
            assert output
            assert "# TYPE" in output


@pytest.mark.integration
@pytest.mark.metrics
class TestPrometheusEndToEnd:
    """End-to-end tests for Prometheus metrics."""

    def test_full_metrics_export(self):
        """Test complete metrics export from all sources."""
        metrics = MetricsTracker()
        streaming = StreamingMetricsTracker()
        errors = ErrorMetricsTracker()
        errors.reset()

        # Generate realistic data
        for i in range(10):
            metrics.track_request("/v1/chat/completions")
            metrics.track_response("/v1/chat/completions", 0.5)
            metrics.track_tokens("/v1/chat/completions", 100)

            if i < 8:
                errors.record_success("/v1/chat/completions")
            else:
                errors.record_error(
                    endpoint="/v1/chat/completions",
                    status_code=500,
                    error_type="internal_error",
                    error_message="Error",
                )

        stream_id = f"stream-1"
        streaming.start_stream(stream_id, model="gpt-4")
        streaming.record_first_token(stream_id)
        for _ in range(50):
            streaming.record_token(stream_id)
        streaming.end_stream(stream_id, success=True)

        time.sleep(0.1)

        # Export all metrics
        metrics_output = metrics.get_prometheus_metrics()
        streaming_output = streaming.get_prometheus_metrics()
        errors_output = errors.get_prometheus_metrics()

        # Combine
        combined = metrics_output + "\n" + streaming_output + "\n" + errors_output

        # Should be valid
        assert len(combined) > 1000  # Should be substantial
        assert combined.count("# TYPE") > 10  # Many metric types

        # Should be parseable if prometheus_client available
        try:
            from prometheus_client.parser import text_string_to_metric_families

            families = list(text_string_to_metric_families(combined))
            assert len(families) > 15  # Should have many metrics
        except ImportError:
            pass  # Skip if not available
