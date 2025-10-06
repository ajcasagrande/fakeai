"""
Metrics configuration module.

This module provides metrics and monitoring configuration options.
"""

#  SPDX-License-Identifier: Apache-2.0

from pydantic import Field

from .base import ModuleConfig


class MetricsConfig(ModuleConfig):
    """Metrics and monitoring configuration settings."""

    # Metrics collection
    enable_metrics: bool = Field(
        default=True,
        description="Enable metrics collection and tracking.",
    )
    enable_prometheus: bool = Field(
        default=False,
        description="Enable Prometheus metrics endpoint.",
    )
    metrics_retention_hours: int = Field(
        default=24,
        description="Hours to retain metrics data in memory.",
    )

    # Error injection for testing
    error_injection_enabled: bool = Field(
        default=False,
        description="Enable error injection for testing.",
    )
    error_injection_rate: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Global error injection rate (0.0-1.0).",
    )
    error_injection_types: list[str] = Field(
        default_factory=lambda: [
            "internal_error",
            "service_unavailable",
            "gateway_timeout",
            "rate_limit_quota",
        ],
        description="List of error types to inject (internal_error, bad_gateway, service_unavailable, gateway_timeout, rate_limit_quota, context_length_exceeded).",
    )
