"""
Metrics handler for the /metrics endpoint.

This handler provides access to server metrics.
"""
#  SPDX-License-Identifier: Apache-2.0

from typing import Any, Optional

from fakeai.config import AppConfig
from fakeai.events import AsyncEventBus
from fakeai.handlers.base import EndpointHandler, RequestContext
from fakeai.handlers.registry import register_handler
from fakeai.metrics import MetricsTracker


@register_handler
class MetricsHandler(EndpointHandler[None, dict[str, Any]]):
    """
    Handler for the /metrics endpoint.

    This handler provides access to server metrics including:
    - Requests per second by endpoint
    - Response times and latencies
    - Token usage rates
    - Error rates
    - Streaming statistics

    Features:
        - JSON format metrics
        - Per-endpoint breakdown
        - Streaming statistics
        - Health metrics
    """

    def __init__(
        self,
        config: AppConfig,
        metrics_tracker: MetricsTracker,
        event_bus: Optional[AsyncEventBus] = None,
    ):
        """Initialize the handler."""
        super().__init__(config, metrics_tracker, event_bus=event_bus)

    def endpoint_path(self) -> str:
        """Return the endpoint path."""
        return "/metrics"

    async def execute(
        self,
        request: None,
        context: RequestContext,
    ) -> dict[str, Any]:
        """
        Get server metrics.

        Args:
            request: Not used (GET request)
            context: Request context

        Returns:
            Dictionary containing all metrics
        """
        return self.metrics_tracker.get_metrics()

    def extract_model(self, request: None) -> str | None:
        """Metrics endpoint doesn't have a model parameter."""
        return None


@register_handler(endpoint="/metrics/prometheus")
class PrometheusMetricsHandler(EndpointHandler[None, str]):
    """
    Handler for the /metrics/prometheus endpoint.

    Returns metrics in Prometheus text format.
    """

    def __init__(
        self,
        config: AppConfig,
        metrics_tracker: MetricsTracker,
        event_bus: Optional[AsyncEventBus] = None,
    ):
        """Initialize the handler."""
        super().__init__(config, metrics_tracker, event_bus=event_bus)

    def endpoint_path(self) -> str:
        """Return the endpoint path."""
        return "/metrics/prometheus"

    async def execute(
        self,
        request: None,
        context: RequestContext,
    ) -> str:
        """
        Get server metrics in Prometheus format.

        Args:
            request: Not used (GET request)
            context: Request context

        Returns:
            Prometheus-formatted metrics string
        """
        return self.metrics_tracker.get_prometheus_metrics()

    def extract_model(self, request: None) -> str | None:
        """Metrics endpoint doesn't have a model parameter."""
        return None


@register_handler(endpoint="/health")
class HealthHandler(EndpointHandler[None, dict[str, Any]]):
    """
    Handler for the /health endpoint.

    Provides health check status with optional detailed metrics.
    """

    def __init__(
        self,
        config: AppConfig,
        metrics_tracker: MetricsTracker,
        event_bus: Optional[AsyncEventBus] = None,
    ):
        """Initialize the handler."""
        super().__init__(config, metrics_tracker, event_bus=event_bus)

    def endpoint_path(self) -> str:
        """Return the endpoint path."""
        return "/health"

    async def execute(
        self,
        request: None,
        context: RequestContext,
    ) -> dict[str, Any]:
        """
        Get health status.

        Args:
            request: Not used (GET request)
            context: Request context

        Returns:
            Health status dictionary
        """
        return {
            "status": "healthy",
            "ready": True,
            "timestamp": context.start_time,
        }

    def extract_model(self, request: None) -> str | None:
        """Health endpoint doesn't have a model parameter."""
        return None
