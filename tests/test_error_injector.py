"""
Tests for error injection system.

This module tests the ErrorInjector class and its integration with
the FakeAI configuration system.
"""

#  SPDX-License-Identifier: Apache-2.0

import time
from unittest.mock import patch

import pytest

from fakeai.config import AppConfig
from fakeai.error_injector import (
    ERROR_TEMPLATES,
    ErrorInjector,
    ErrorStats,
    ErrorType,
    LoadSpike,
    get_error_injector,
    set_error_injector,
)


class TestErrorStats:
    """Tests for ErrorStats dataclass."""

    def test_initialization(self):
        """Test ErrorStats initialization."""
        stats = ErrorStats()
        assert stats.total_checks == 0
        assert stats.total_errors_injected == 0
        assert stats.error_rate() == 0.0
        assert stats.last_reset_time > 0

    def test_error_rate_calculation(self):
        """Test error rate calculation."""
        stats = ErrorStats()
        stats.total_checks = 100
        stats.total_errors_injected = 10
        assert stats.error_rate() == 0.1

        stats.total_checks = 0
        assert stats.error_rate() == 0.0


class TestLoadSpike:
    """Tests for LoadSpike dataclass."""

    def test_is_active(self):
        """Test load spike active detection."""
        spike = LoadSpike(
            start_time=time.time(),
            duration_seconds=2.0,
            error_rate_multiplier=3.0,
        )
        assert spike.is_active() is True

        # Wait for spike to expire
        time.sleep(2.1)
        assert spike.is_active() is False

    def test_get_multiplier(self):
        """Test multiplier retrieval."""
        spike = LoadSpike(
            start_time=time.time(),
            duration_seconds=2.0,
            error_rate_multiplier=3.0,
        )
        assert spike.get_multiplier() == 3.0

        # Wait for spike to expire
        time.sleep(2.1)
        assert spike.get_multiplier() == 1.0


class TestErrorInjector:
    """Tests for ErrorInjector class."""

    def test_initialization_defaults(self):
        """Test ErrorInjector initialization with defaults."""
        injector = ErrorInjector()
        assert injector.enabled is False
        assert injector._global_error_rate == 0.0
        assert len(injector._error_types) == len(ErrorType)

    def test_initialization_with_params(self):
        """Test ErrorInjector initialization with custom parameters."""
        injector = ErrorInjector(
            global_error_rate=0.1,
            enabled=True,
            error_types=[ErrorType.INTERNAL_ERROR, ErrorType.SERVICE_UNAVAILABLE],
        )
        assert injector.enabled is True
        assert injector._global_error_rate == 0.1
        assert len(injector._error_types) == 2

    def test_initialization_validation(self):
        """Test ErrorInjector initialization validation."""
        with pytest.raises(ValueError, match="must be between 0.0 and 1.0"):
            ErrorInjector(global_error_rate=1.5)

        with pytest.raises(ValueError, match="must be between 0.0 and 1.0"):
            ErrorInjector(global_error_rate=-0.1)

    def test_enable_disable(self):
        """Test enabling and disabling error injection."""
        injector = ErrorInjector(enabled=False)
        assert injector.enabled is False

        injector.enable()
        assert injector.enabled is True

        injector.disable()
        assert injector.enabled is False

    def test_set_global_error_rate(self):
        """Test setting global error rate."""
        injector = ErrorInjector()
        injector.set_global_error_rate(0.25)
        assert injector._global_error_rate == 0.25

        with pytest.raises(ValueError):
            injector.set_global_error_rate(1.5)

        with pytest.raises(ValueError):
            injector.set_global_error_rate(-0.1)

    def test_set_endpoint_error_rate(self):
        """Test setting per-endpoint error rate."""
        injector = ErrorInjector()
        injector.set_endpoint_error_rate("/v1/chat/completions", 0.5)
        assert injector._endpoint_error_rates["/v1/chat/completions"] == 0.5

        with pytest.raises(ValueError):
            injector.set_endpoint_error_rate("/v1/chat/completions", 2.0)

    def test_clear_endpoint_error_rate(self):
        """Test clearing per-endpoint error rate."""
        injector = ErrorInjector()
        injector.set_endpoint_error_rate("/v1/chat/completions", 0.5)
        assert "/v1/chat/completions" in injector._endpoint_error_rates

        injector.clear_endpoint_error_rate("/v1/chat/completions")
        assert "/v1/chat/completions" not in injector._endpoint_error_rates

    def test_set_error_types(self):
        """Test setting error types."""
        injector = ErrorInjector()
        types = [ErrorType.INTERNAL_ERROR, ErrorType.GATEWAY_TIMEOUT]
        injector.set_error_types(types)
        assert injector._error_types == types

        with pytest.raises(ValueError, match="cannot be empty"):
            injector.set_error_types([])

    def test_should_inject_error_when_disabled(self):
        """Test that no errors are injected when disabled."""
        injector = ErrorInjector(global_error_rate=1.0, enabled=False)
        for _ in range(100):
            should_inject, error = injector.should_inject_error("/v1/chat/completions")
            assert should_inject is False
            assert error is None

    def test_should_inject_error_with_zero_rate(self):
        """Test that no errors are injected with zero rate."""
        injector = ErrorInjector(global_error_rate=0.0, enabled=True)
        for _ in range(100):
            should_inject, error = injector.should_inject_error("/v1/chat/completions")
            assert should_inject is False
            assert error is None

    def test_should_inject_error_with_full_rate(self):
        """Test that errors are always injected with rate 1.0."""
        injector = ErrorInjector(global_error_rate=1.0, enabled=True)
        for _ in range(10):
            should_inject, error = injector.should_inject_error("/v1/chat/completions")
            assert should_inject is True
            assert error is not None
            assert "error" in error
            assert "status_code" in error

    def test_should_inject_error_statistics(self):
        """Test that statistics are tracked correctly."""
        injector = ErrorInjector(global_error_rate=0.5, enabled=True)

        # Run multiple checks
        for _ in range(100):
            injector.should_inject_error("/v1/chat/completions")

        stats = injector.get_error_stats()
        assert stats["statistics"]["total_checks"] == 100
        # With 50% rate, we expect roughly 50 errors (allow some variance)
        assert 30 <= stats["statistics"]["total_errors_injected"] <= 70

    def test_should_inject_error_endpoint_override(self):
        """Test that endpoint-specific rates override global rate."""
        injector = ErrorInjector(global_error_rate=0.0, enabled=True)
        injector.set_endpoint_error_rate("/v1/chat/completions", 1.0)

        # Endpoint with override should always error
        should_inject, _ = injector.should_inject_error("/v1/chat/completions")
        assert should_inject is True

        # Other endpoints should never error
        should_inject, _ = injector.should_inject_error("/v1/embeddings")
        assert should_inject is False

    def test_error_response_structure(self):
        """Test error response structure."""
        injector = ErrorInjector(
            global_error_rate=1.0,
            enabled=True,
            error_types=[ErrorType.INTERNAL_ERROR],
        )
        should_inject, error = injector.should_inject_error("/v1/chat/completions")

        assert should_inject is True
        assert error is not None
        assert "status_code" in error
        assert "error" in error
        assert "message" in error["error"]
        assert "type" in error["error"]

        template = ERROR_TEMPLATES[ErrorType.INTERNAL_ERROR]
        assert error["status_code"] == template.status_code
        assert error["error"]["type"] == template.error_type
        assert error["error"]["message"] == template.message

    def test_error_types_injection(self):
        """Test that different error types are injected."""
        injector = ErrorInjector(
            global_error_rate=1.0,
            enabled=True,
            error_types=[
                ErrorType.INTERNAL_ERROR,
                ErrorType.SERVICE_UNAVAILABLE,
                ErrorType.GATEWAY_TIMEOUT,
            ],
        )

        # Collect error types over multiple runs
        error_types = set()
        for _ in range(50):
            should_inject, error = injector.should_inject_error("/v1/chat/completions")
            if should_inject and error:
                error_types.add(error["error"]["type"])

        # Should see multiple different error types
        assert len(error_types) >= 2

    def test_simulate_load_spike(self):
        """Test load spike simulation."""
        injector = ErrorInjector(global_error_rate=0.1, enabled=True)
        injector.simulate_load_spike(duration_seconds=1.0, error_rate_multiplier=5.0)

        # During spike, error rate should be higher
        stats_during_spike = injector.get_error_stats()
        assert stats_during_spike["load_spike"] is not None
        assert stats_during_spike["load_spike"]["active"] is True
        assert stats_during_spike["load_spike"]["error_rate_multiplier"] == 5.0

        # Wait for spike to expire
        time.sleep(1.1)

        # After spike, should return to normal
        stats_after_spike = injector.get_error_stats()
        assert stats_after_spike["load_spike"] is None

    def test_simulate_load_spike_validation(self):
        """Test load spike validation."""
        injector = ErrorInjector()

        with pytest.raises(ValueError, match="must be positive"):
            injector.simulate_load_spike(duration_seconds=0.0)

        with pytest.raises(ValueError, match="must be >= 1.0"):
            injector.simulate_load_spike(
                duration_seconds=1.0, error_rate_multiplier=0.5
            )

    def test_clear_load_spike(self):
        """Test clearing load spike."""
        injector = ErrorInjector(global_error_rate=0.1, enabled=True)
        injector.simulate_load_spike(duration_seconds=10.0, error_rate_multiplier=3.0)

        stats = injector.get_error_stats()
        assert stats["load_spike"] is not None

        injector.clear_load_spike()
        stats = injector.get_error_stats()
        assert stats["load_spike"] is None

    def test_get_error_stats(self):
        """Test getting error statistics."""
        injector = ErrorInjector(
            global_error_rate=0.2,
            enabled=True,
            error_types=[ErrorType.INTERNAL_ERROR],
        )
        injector.set_endpoint_error_rate("/v1/chat/completions", 0.5)

        # Generate some errors
        for _ in range(20):
            injector.should_inject_error("/v1/chat/completions")

        stats = injector.get_error_stats()

        assert stats["enabled"] is True
        assert stats["global_error_rate"] == 0.2
        assert "/v1/chat/completions" in stats["endpoint_error_rates"]
        assert stats["endpoint_error_rates"]["/v1/chat/completions"] == 0.5
        assert "internal_error" in stats["error_types"]
        assert stats["statistics"]["total_checks"] == 20
        assert stats["statistics"]["uptime_seconds"] >= 0

    def test_reset_stats(self):
        """Test resetting statistics."""
        injector = ErrorInjector(global_error_rate=1.0, enabled=True)

        # Generate errors
        for _ in range(10):
            injector.should_inject_error("/v1/chat/completions")

        stats_before = injector.get_error_stats()
        assert stats_before["statistics"]["total_checks"] == 10
        assert stats_before["statistics"]["total_errors_injected"] == 10

        # Reset
        injector.reset_stats()

        stats_after = injector.get_error_stats()
        assert stats_after["statistics"]["total_checks"] == 0
        assert stats_after["statistics"]["total_errors_injected"] == 0

    def test_get_prometheus_metrics(self):
        """Test Prometheus metrics export."""
        injector = ErrorInjector(
            global_error_rate=0.1,
            enabled=True,
            error_types=[ErrorType.INTERNAL_ERROR],
        )

        # Generate some errors
        for _ in range(10):
            injector.should_inject_error("/v1/chat/completions")

        metrics = injector.get_prometheus_metrics()

        assert "fakeai_error_injection_enabled" in metrics
        assert "fakeai_error_injection_global_rate" in metrics
        assert "fakeai_error_injection_checks_total" in metrics
        assert "fakeai_error_injection_errors_total" in metrics
        assert "fakeai_error_injection_rate" in metrics
        assert "fakeai_error_injection_by_type_total" in metrics
        assert "fakeai_error_injection_by_endpoint_total" in metrics

    def test_thread_safety(self):
        """Test thread safety of ErrorInjector."""
        import threading

        injector = ErrorInjector(global_error_rate=0.5, enabled=True)
        errors_count = []

        def worker():
            local_errors = 0
            for _ in range(100):
                should_inject, _ = injector.should_inject_error("/v1/chat/completions")
                if should_inject:
                    local_errors += 1
            errors_count.append(local_errors)

        # Run multiple threads
        threads = [threading.Thread(target=worker) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Verify stats are consistent
        stats = injector.get_error_stats()
        assert stats["statistics"]["total_checks"] == 1000
        assert stats["statistics"]["total_errors_injected"] == sum(errors_count)

    def test_all_error_types_have_templates(self):
        """Test that all error types have corresponding templates."""
        for error_type in ErrorType:
            assert error_type in ERROR_TEMPLATES
            template = ERROR_TEMPLATES[error_type]
            assert template.status_code > 0
            assert template.error_type
            assert template.message

    def test_context_length_error_has_param(self):
        """Test that context_length_exceeded error includes param."""
        injector = ErrorInjector(
            global_error_rate=1.0,
            enabled=True,
            error_types=[ErrorType.CONTEXT_LENGTH_EXCEEDED],
        )

        should_inject, error = injector.should_inject_error("/v1/chat/completions")
        assert should_inject is True
        assert error is not None
        assert "param" in error["error"]
        assert error["error"]["param"] == "messages"

    def test_rate_limit_error_status_code(self):
        """Test that rate limit errors have correct status code."""
        injector = ErrorInjector(
            global_error_rate=1.0,
            enabled=True,
            error_types=[ErrorType.RATE_LIMIT_QUOTA],
        )

        should_inject, error = injector.should_inject_error("/v1/chat/completions")
        assert should_inject is True
        assert error is not None
        assert error["status_code"] == 429


class TestErrorInjectorSingleton:
    """Tests for singleton ErrorInjector functions."""

    def test_get_error_injector_singleton(self):
        """Test that get_error_injector returns singleton instance."""
        injector1 = get_error_injector()
        injector2 = get_error_injector()
        assert injector1 is injector2

    def test_set_error_injector(self):
        """Test setting custom error injector instance."""
        custom_injector = ErrorInjector(global_error_rate=0.5, enabled=True)
        set_error_injector(custom_injector)

        retrieved = get_error_injector()
        assert retrieved is custom_injector
        assert retrieved._global_error_rate == 0.5


class TestConfigIntegration:
    """Tests for integration with AppConfig."""

    def test_config_error_injection_defaults(self):
        """Test default error injection configuration."""
        config = AppConfig()
        assert config.error_injection_enabled is False
        assert config.error_injection_rate == 0.0
        assert len(config.error_injection_types) > 0

    def test_config_error_injection_custom(self):
        """Test custom error injection configuration."""
        config = AppConfig(
            error_injection_enabled=True,
            error_injection_rate=0.1,
            error_injection_types=["internal_error", "service_unavailable"],
        )
        assert config.error_injection_enabled is True
        assert config.error_injection_rate == 0.1
        assert len(config.error_injection_types) == 2

    def test_config_error_injection_rate_validation(self):
        """Test error injection rate validation in config."""
        with pytest.raises(ValueError):
            AppConfig(error_injection_rate=1.5)

        with pytest.raises(ValueError):
            AppConfig(error_injection_rate=-0.1)

    def test_config_error_injection_types_validation(self):
        """Test error injection types validation in config."""
        with pytest.raises(ValueError, match="Invalid error type"):
            AppConfig(error_injection_types=["invalid_type"])

        # Valid types should work
        config = AppConfig(
            error_injection_types=[
                "internal_error",
                "bad_gateway",
                "service_unavailable",
                "gateway_timeout",
                "rate_limit_quota",
                "context_length_exceeded",
            ]
        )
        assert len(config.error_injection_types) == 6

    def test_config_from_environment(self):
        """Test loading error injection config from environment."""
        import os

        # Set environment variables
        os.environ["FAKEAI_ERROR_INJECTION_ENABLED"] = "true"
        os.environ["FAKEAI_ERROR_INJECTION_RATE"] = "0.15"
        os.environ["FAKEAI_ERROR_INJECTION_TYPES"] = (
            '["internal_error", "service_unavailable"]'
        )

        try:
            config = AppConfig()
            assert config.error_injection_enabled is True
            assert config.error_injection_rate == 0.15
            # Note: Pydantic may parse JSON list from env var
        finally:
            # Clean up
            del os.environ["FAKEAI_ERROR_INJECTION_ENABLED"]
            del os.environ["FAKEAI_ERROR_INJECTION_RATE"]
            del os.environ["FAKEAI_ERROR_INJECTION_TYPES"]
