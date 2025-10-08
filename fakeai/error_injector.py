#!/usr/bin/env python3
"""
FakeAI Error Injection System

This module provides a decoupled error injection system for simulating realistic
API failures to test error handling in client applications.

Features:
- Configurable error rates (0.0-1.0) per endpoint
- Multiple error types (500, 502, 503, 504, 429, context_length_exceeded)
- Time-based patterns (load spikes)
- Thread-safe state management
- Prometheus metrics integration
"""
#  SPDX-License-Identifier: Apache-2.0

import logging
import random
import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class ErrorType(Enum):
    """Types of errors that can be injected."""

    INTERNAL_ERROR = "internal_error"
    BAD_GATEWAY = "bad_gateway"
    SERVICE_UNAVAILABLE = "service_unavailable"
    GATEWAY_TIMEOUT = "gateway_timeout"
    RATE_LIMIT_QUOTA = "rate_limit_quota"
    CONTEXT_LENGTH_EXCEEDED = "context_length_exceeded"


@dataclass
class ErrorTemplate:
    """Template for generating error responses."""

    status_code: int
    error_type: str
    message: str
    code: str | None = None
    param: str | None = None


# Error templates for each error type
ERROR_TEMPLATES = {
    ErrorType.INTERNAL_ERROR: ErrorTemplate(
        status_code=500,
        error_type="internal_error",
        message="The server encountered an error processing your request.",
        code="internal_error",
    ),
    ErrorType.BAD_GATEWAY: ErrorTemplate(
        status_code=502,
        error_type="bad_gateway",
        message="The server received an invalid response from the upstream server.",
        code="bad_gateway",
    ),
    ErrorType.SERVICE_UNAVAILABLE: ErrorTemplate(
        status_code=503,
        error_type="service_unavailable",
        message="The server is overloaded or down for maintenance. Please try again later.",
        code="service_unavailable",
    ),
    ErrorType.GATEWAY_TIMEOUT: ErrorTemplate(
        status_code=504,
        error_type="gateway_timeout",
        message="The server timed out waiting for the model.",
        code="gateway_timeout",
    ),
    ErrorType.RATE_LIMIT_QUOTA: ErrorTemplate(
        status_code=429,
        error_type="insufficient_quota",
        message="You exceeded your current quota. Please check your plan and billing details.",
        code="insufficient_quota",
    ),
    ErrorType.CONTEXT_LENGTH_EXCEEDED: ErrorTemplate(
        status_code=400,
        error_type="context_length_exceeded",
        message="This model's maximum context length is 128000 tokens. However, your messages resulted in over 150000 tokens.",
        code="context_length_exceeded",
        param="messages",
    ),
}


@dataclass
class ErrorStats:
    """Statistics for injected errors."""

    total_checks: int = 0
    total_errors_injected: int = 0
    errors_by_type: dict[str, int] = field(
        default_factory=lambda: defaultdict(int))
    errors_by_endpoint: dict[str, int] = field(
        default_factory=lambda: defaultdict(int))
    last_reset_time: float = field(default_factory=time.time)

    def error_rate(self) -> float:
        """Calculate the overall error injection rate."""
        if self.total_checks == 0:
            return 0.0
        return self.total_errors_injected / self.total_checks


@dataclass
class LoadSpike:
    """Configuration for a temporary load spike."""

    start_time: float
    duration_seconds: float
    error_rate_multiplier: float

    def is_active(self) -> bool:
        """Check if the load spike is currently active."""
        elapsed = time.time() - self.start_time
        return 0 <= elapsed < self.duration_seconds

    def get_multiplier(self) -> float:
        """Get the current error rate multiplier."""
        if not self.is_active():
            return 1.0
        return self.error_rate_multiplier


class ErrorInjector:
    """
    Thread-safe error injection system for simulating API failures.

    This class provides configurable error injection with support for:
    - Global and per-endpoint error rates
    - Multiple error types with realistic templates
    - Time-based load spike simulation
    - Comprehensive statistics tracking
    """

    def __init__(
        self,
        global_error_rate: float = 0.0,
        enabled: bool = False,
        error_types: list[ErrorType] | None = None,
    ):
        """
        Initialize the error injector.

        Args:
            global_error_rate: Base error rate (0.0-1.0) applied to all endpoints
            enabled: Whether error injection is enabled
            error_types: List of error types to inject (defaults to all types)
        """
        if not 0.0 <= global_error_rate <= 1.0:
            raise ValueError("global_error_rate must be between 0.0 and 1.0")

        self._enabled = enabled
        self._global_error_rate = global_error_rate
        self._endpoint_error_rates: dict[str, float] = {}
        self._error_types = error_types or list(ErrorType)
        self._stats = ErrorStats()
        self._load_spike: LoadSpike | None = None
        self._lock = threading.Lock()

        logger.info(
            f"Error injector initialized: enabled={enabled}, "
            f"global_rate={global_error_rate}, error_types={len(self._error_types)}"
        )

    @property
    def enabled(self) -> bool:
        """Check if error injection is enabled."""
        return self._enabled

    def enable(self) -> None:
        """Enable error injection."""
        with self._lock:
            self._enabled = True
            logger.info("Error injection enabled")

    def disable(self) -> None:
        """Disable error injection."""
        with self._lock:
            self._enabled = False
            logger.info("Error injection disabled")

    def set_global_error_rate(self, rate: float) -> None:
        """
        Set the global error rate.

        Args:
            rate: Error rate (0.0-1.0)
        """
        if not 0.0 <= rate <= 1.0:
            raise ValueError("Error rate must be between 0.0 and 1.0")

        with self._lock:
            self._global_error_rate = rate
            logger.info(f"Global error rate set to {rate:.2%}")

    def set_endpoint_error_rate(self, endpoint: str, rate: float) -> None:
        """
        Set error rate for a specific endpoint.

        Args:
            endpoint: Endpoint path (e.g., "/v1/chat/completions")
            rate: Error rate (0.0-1.0)
        """
        if not 0.0 <= rate <= 1.0:
            raise ValueError("Error rate must be between 0.0 and 1.0")

        with self._lock:
            self._endpoint_error_rates[endpoint] = rate
            logger.info(f"Error rate for {endpoint} set to {rate:.2%}")

    def clear_endpoint_error_rate(self, endpoint: str) -> None:
        """
        Clear the error rate override for a specific endpoint.

        Args:
            endpoint: Endpoint path
        """
        with self._lock:
            if endpoint in self._endpoint_error_rates:
                del self._endpoint_error_rates[endpoint]
                logger.info(f"Cleared error rate override for {endpoint}")

    def set_error_types(self, error_types: list[ErrorType]) -> None:
        """
        Set the types of errors to inject.

        Args:
            error_types: List of error types
        """
        if not error_types:
            raise ValueError("error_types cannot be empty")

        with self._lock:
            self._error_types = error_types
            logger.info(
                f"Error types set to: {[e.value for e in error_types]}")

    def simulate_load_spike(
        self, duration_seconds: float, error_rate_multiplier: float = 3.0
    ) -> None:
        """
        Temporarily increase error rates to simulate a load spike.

        Args:
            duration_seconds: How long the spike should last
            error_rate_multiplier: Multiplier for error rates during spike
        """
        if duration_seconds <= 0:
            raise ValueError("duration_seconds must be positive")
        if error_rate_multiplier < 1.0:
            raise ValueError("error_rate_multiplier must be >= 1.0")

        with self._lock:
            self._load_spike = LoadSpike(
                start_time=time.time(),
                duration_seconds=duration_seconds,
                error_rate_multiplier=error_rate_multiplier,
            )
            logger.info(
                f"Load spike simulation started: duration={duration_seconds}s, "
                f"multiplier={error_rate_multiplier}x"
            )

    def clear_load_spike(self) -> None:
        """Clear any active load spike simulation."""
        with self._lock:
            if self._load_spike:
                self._load_spike = None
                logger.info("Load spike simulation cleared")

    def should_inject_error(
            self, endpoint: str) -> tuple[bool, dict[str, Any] | None]:
        """
        Determine if an error should be injected for this request.

        Args:
            endpoint: The endpoint being called

        Returns:
            Tuple of (should_inject, error_response_dict)
            - should_inject: Whether to inject an error
            - error_response_dict: Error response dict if should_inject is True, else None
        """
        with self._lock:
            self._stats.total_checks += 1

            # If disabled, never inject errors
            if not self._enabled:
                return False, None

            # Determine effective error rate
            endpoint_rate = self._endpoint_error_rates.get(
                endpoint, self._global_error_rate
            )

            # Apply load spike multiplier if active
            if self._load_spike and self._load_spike.is_active():
                effective_rate = min(
                    1.0, endpoint_rate * self._load_spike.get_multiplier()
                )
            else:
                effective_rate = endpoint_rate

            # Decide whether to inject error
            if random.random() >= effective_rate:
                return False, None

            # Select random error type
            error_type = random.choice(self._error_types)
            template = ERROR_TEMPLATES[error_type]

            # Build error response
            error_response = self._build_error_response(template)

            # Update statistics
            self._stats.total_errors_injected += 1
            self._stats.errors_by_type[error_type.value] += 1
            self._stats.errors_by_endpoint[endpoint] += 1

            logger.debug(
                f"Injecting {error_type.value} error for {endpoint} "
                f"(rate={effective_rate:.2%})"
            )

            return True, error_response

    def _build_error_response(self, template: ErrorTemplate) -> dict[str, Any]:
        """
        Build an error response dictionary from a template.

        Args:
            template: Error template

        Returns:
            Error response dictionary
        """
        error_detail = {
            "message": template.message,
            "type": template.error_type,
        }

        if template.code:
            error_detail["code"] = template.code

        if template.param:
            error_detail["param"] = template.param

        return {
            "status_code": template.status_code,
            "error": error_detail,
        }

    def get_error_stats(self) -> dict[str, Any]:
        """
        Get statistics about injected errors.

        Returns:
            Dictionary containing error statistics
        """
        with self._lock:
            load_spike_info = None
            if self._load_spike and self._load_spike.is_active():
                elapsed = time.time() - self._load_spike.start_time
                remaining = self._load_spike.duration_seconds - elapsed
                load_spike_info = {
                    "active": True,
                    "error_rate_multiplier": self._load_spike.error_rate_multiplier,
                    "elapsed_seconds": round(
                        elapsed,
                        2),
                    "remaining_seconds": round(
                        remaining,
                        2),
                }

            return {
                "enabled": self._enabled,
                "global_error_rate": self._global_error_rate,
                "endpoint_error_rates": dict(self._endpoint_error_rates),
                "error_types": [e.value for e in self._error_types],
                "statistics": {
                    "total_checks": self._stats.total_checks,
                    "total_errors_injected": self._stats.total_errors_injected,
                    "overall_error_rate": round(self._stats.error_rate(), 4),
                    "errors_by_type": dict(self._stats.errors_by_type),
                    "errors_by_endpoint": dict(self._stats.errors_by_endpoint),
                    "uptime_seconds": round(
                        time.time() - self._stats.last_reset_time, 2
                    ),
                },
                "load_spike": load_spike_info,
            }

    def reset_stats(self) -> None:
        """Reset error injection statistics."""
        with self._lock:
            self._stats = ErrorStats()
            logger.info("Error injection statistics reset")

    def get_prometheus_metrics(self) -> str:
        """
        Export error injection metrics in Prometheus format.

        Returns:
            String containing Prometheus-formatted metrics
        """
        with self._lock:
            lines = []

            # Enabled status
            lines.append(
                "# HELP fakeai_error_injection_enabled Whether error injection is enabled"
            )
            lines.append("# TYPE fakeai_error_injection_enabled gauge")
            lines.append(
                f"fakeai_error_injection_enabled {
                    1 if self._enabled else 0}")

            # Global error rate
            lines.append(
                "# HELP fakeai_error_injection_global_rate Global error injection rate"
            )
            lines.append("# TYPE fakeai_error_injection_global_rate gauge")
            lines.append(
                f"fakeai_error_injection_global_rate {
                    self._global_error_rate:.6f}")

            # Total checks
            lines.append(
                "# HELP fakeai_error_injection_checks_total Total number of error injection checks"
            )
            lines.append("# TYPE fakeai_error_injection_checks_total counter")
            lines.append(
                f"fakeai_error_injection_checks_total {
                    self._stats.total_checks}")

            # Total errors injected
            lines.append(
                "# HELP fakeai_error_injection_errors_total Total number of errors injected"
            )
            lines.append("# TYPE fakeai_error_injection_errors_total counter")
            lines.append(
                f"fakeai_error_injection_errors_total {
                    self._stats.total_errors_injected}")

            # Overall error rate
            lines.append(
                "# HELP fakeai_error_injection_rate Actual error injection rate"
            )
            lines.append("# TYPE fakeai_error_injection_rate gauge")
            lines.append(
                f"fakeai_error_injection_rate {
                    self._stats.error_rate():.6f}")

            # Errors by type
            lines.append(
                "# HELP fakeai_error_injection_by_type_total Errors injected by type"
            )
            lines.append("# TYPE fakeai_error_injection_by_type_total counter")
            for error_type, count in self._stats.errors_by_type.items():
                lines.append(
                    f'fakeai_error_injection_by_type_total{{type="{error_type}"}} {count}'
                )

            # Errors by endpoint
            lines.append(
                "# HELP fakeai_error_injection_by_endpoint_total Errors injected by endpoint"
            )
            lines.append(
                "# TYPE fakeai_error_injection_by_endpoint_total counter")
            for endpoint, count in self._stats.errors_by_endpoint.items():
                lines.append(
                    f'fakeai_error_injection_by_endpoint_total{{endpoint="{endpoint}"}} {count}'
                )

            # Load spike status
            if self._load_spike and self._load_spike.is_active():
                lines.append(
                    "# HELP fakeai_error_injection_load_spike_active Load spike simulation active"
                )
                lines.append(
                    "# TYPE fakeai_error_injection_load_spike_active gauge")
                lines.append("fakeai_error_injection_load_spike_active 1")

                lines.append(
                    "# HELP fakeai_error_injection_load_spike_multiplier Load spike error rate multiplier"
                )
                lines.append(
                    "# TYPE fakeai_error_injection_load_spike_multiplier gauge"
                )
                lines.append(
                    f"fakeai_error_injection_load_spike_multiplier {
                        self._load_spike.error_rate_multiplier:.2f}")
            else:
                lines.append(
                    "# HELP fakeai_error_injection_load_spike_active Load spike simulation active"
                )
                lines.append(
                    "# TYPE fakeai_error_injection_load_spike_active gauge")
                lines.append("fakeai_error_injection_load_spike_active 0")

            return "\n".join(lines) + "\n"


# Singleton instance (can be overridden in tests)
_error_injector_instance: ErrorInjector | None = None
_error_injector_lock = threading.Lock()


def get_error_injector() -> ErrorInjector:
    """
    Get the singleton ErrorInjector instance.

    Returns:
        ErrorInjector instance
    """
    global _error_injector_instance

    if _error_injector_instance is None:
        with _error_injector_lock:
            if _error_injector_instance is None:
                _error_injector_instance = ErrorInjector()

    return _error_injector_instance


def set_error_injector(injector: ErrorInjector) -> None:
    """
    Set the global error injector instance (useful for testing).

    Args:
        injector: ErrorInjector instance to use
    """
    global _error_injector_instance

    with _error_injector_lock:
        _error_injector_instance = injector
