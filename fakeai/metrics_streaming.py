#!/usr/bin/env python3
"""
FakeAI Metrics Streaming Module

Real-time metrics streaming via WebSocket for live dashboards and monitoring.
Provides subscription-based metric updates with filtering capabilities.
"""
#  SPDX-License-Identifier: Apache-2.0

import asyncio
import json
import logging
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics that can be streamed."""

    THROUGHPUT = "throughput"
    LATENCY = "latency"
    CACHE = "cache"
    QUEUE = "queue"
    STREAMING = "streaming"
    ERROR = "error"
    ALL = "all"


@dataclass
class SubscriptionFilter:
    """Filter configuration for metric subscriptions."""

    endpoints: Set[str] = field(default_factory=set)
    models: Set[str] = field(default_factory=set)
    metric_types: Set[MetricType] = field(default_factory=lambda: {MetricType.ALL})
    interval: float = 1.0  # Update interval in seconds


@dataclass
class ClientConnection:
    """Represents a connected WebSocket client."""

    ws_id: str
    websocket: WebSocket
    filters: SubscriptionFilter
    last_update: float = field(default_factory=time.time)
    connected: bool = True


@dataclass
class MetricSnapshot:
    """Snapshot of metrics at a point in time."""

    timestamp: float
    throughput: Dict[str, Any] = field(default_factory=dict)
    latency: Dict[str, Any] = field(default_factory=dict)
    cache: Dict[str, Any] = field(default_factory=dict)
    queue: Dict[str, Any] = field(default_factory=dict)
    streaming: Dict[str, Any] = field(default_factory=dict)
    error: Dict[str, Any] = field(default_factory=dict)


class MetricsStreamer:
    """
    Real-time metrics streaming service.

    Handles WebSocket connections and broadcasts metrics to subscribed clients
    with configurable filters and update intervals.
    """

    def __init__(self, metrics_tracker):
        """
        Initialize the metrics streamer.

        Args:
            metrics_tracker: MetricsTracker instance to pull metrics from
        """
        self.metrics_tracker = metrics_tracker
        self.clients: Dict[str, ClientConnection] = {}
        self._broadcast_task = None
        self._running = False
        self._previous_snapshot: Optional[MetricSnapshot] = None

        logger.info("MetricsStreamer initialized")

    async def start(self):
        """Start the background broadcast task."""
        if not self._running:
            self._running = True
            self._broadcast_task = asyncio.create_task(self._broadcast_loop())
            logger.info("MetricsStreamer started")

    async def stop(self):
        """Stop the background broadcast task."""
        self._running = False
        if self._broadcast_task:
            self._broadcast_task.cancel()
            try:
                await self._broadcast_task
            except asyncio.CancelledError:
                pass
        logger.info("MetricsStreamer stopped")

    async def handle_websocket(self, websocket: WebSocket):
        """
        Handle a WebSocket connection for metrics streaming.

        Args:
            websocket: WebSocket connection to handle
        """
        await websocket.accept()

        ws_id = str(uuid.uuid4())
        client = ClientConnection(
            ws_id=ws_id, websocket=websocket, filters=SubscriptionFilter()
        )
        self.clients[ws_id] = client

        logger.info(f"WebSocket client connected: {ws_id}")

        # Send historical data on connect
        await self._send_historical_data(client)

        try:
            while True:
                # Receive messages from client
                data = await websocket.receive_text()

                try:
                    message = json.loads(data)
                    await self._handle_client_message(client, message)
                except json.JSONDecodeError as e:
                    await self._send_error(client, f"Invalid JSON: {str(e)}")
                except Exception as e:
                    logger.exception(f"Error handling client message: {str(e)}")
                    await self._send_error(client, f"Internal error: {str(e)}")

        except Exception as e:
            logger.info(f"WebSocket client {ws_id} disconnected: {str(e)}")
        finally:
            client.connected = False
            if ws_id in self.clients:
                del self.clients[ws_id]
            logger.info(f"WebSocket client removed: {ws_id}")

    async def _handle_client_message(self, client: ClientConnection, message: dict):
        """
        Handle incoming messages from clients.

        Args:
            client: Client connection
            message: Parsed JSON message
        """
        msg_type = message.get("type")

        if msg_type == "subscribe":
            await self._handle_subscribe(client, message)
        elif msg_type == "unsubscribe":
            await self._handle_unsubscribe(client, message)
        elif msg_type == "ping":
            await self._send_message(client, {"type": "pong", "timestamp": time.time()})
        else:
            await self._send_error(client, f"Unknown message type: {msg_type}")

    async def _handle_subscribe(self, client: ClientConnection, message: dict):
        """
        Handle subscription requests.

        Args:
            client: Client connection
            message: Subscribe message with filters
        """
        filters = message.get("filters", {})

        # Update endpoint filter
        if "endpoint" in filters:
            endpoint = filters["endpoint"]
            if endpoint:
                client.filters.endpoints.add(endpoint)

        # Update model filter
        if "model" in filters:
            model = filters["model"]
            if model:
                client.filters.models.add(model)

        # Update metric type filter
        if "metric_type" in filters:
            metric_type_str = filters["metric_type"]
            try:
                metric_type = MetricType(metric_type_str)
                client.filters.metric_types.add(metric_type)
            except ValueError:
                await self._send_error(
                    client, f"Invalid metric type: {metric_type_str}"
                )
                return

        # Update interval
        if "interval" in filters:
            interval = filters["interval"]
            if isinstance(interval, (int, float)) and interval > 0:
                client.filters.interval = float(interval)

        # Send acknowledgment
        await self._send_message(
            client,
            {
                "type": "subscribed",
                "filters": {
                    "endpoints": list(client.filters.endpoints),
                    "models": list(client.filters.models),
                    "metric_types": [mt.value for mt in client.filters.metric_types],
                    "interval": client.filters.interval,
                },
            },
        )

        logger.info(f"Client {client.ws_id} subscribed with filters: {filters}")

    async def _handle_unsubscribe(self, client: ClientConnection, message: dict):
        """
        Handle unsubscribe requests.

        Args:
            client: Client connection
            message: Unsubscribe message
        """
        # Reset filters to defaults
        client.filters = SubscriptionFilter()

        await self._send_message(
            client, {"type": "unsubscribed", "timestamp": time.time()}
        )

        logger.info(f"Client {client.ws_id} unsubscribed")

    async def _send_historical_data(self, client: ClientConnection):
        """
        Send historical metrics data to a newly connected client.

        Args:
            client: Client connection
        """
        try:
            # Get current metrics
            metrics = self.metrics_tracker.get_metrics()

            # Build historical snapshot
            snapshot = self._build_snapshot(metrics)

            # Send to client
            await self._send_message(
                client,
                {
                    "type": "historical_data",
                    "timestamp": snapshot.timestamp,
                    "data": {
                        "throughput": snapshot.throughput,
                        "latency": snapshot.latency,
                        "cache": snapshot.cache,
                        "queue": snapshot.queue,
                        "streaming": snapshot.streaming,
                        "error": snapshot.error,
                    },
                },
            )

            logger.debug(f"Sent historical data to client {client.ws_id}")

        except Exception as e:
            logger.exception(f"Error sending historical data: {str(e)}")

    async def _broadcast_loop(self):
        """Background loop that broadcasts metrics to all clients."""
        while self._running:
            try:
                # Get current metrics
                metrics = self.metrics_tracker.get_metrics()

                # Build snapshot
                snapshot = self._build_snapshot(metrics)

                # Broadcast to all clients
                await self._broadcast_snapshot(snapshot)

                # Store for delta calculations
                self._previous_snapshot = snapshot

                # Wait before next broadcast
                await asyncio.sleep(0.5)  # Broadcast at 2Hz base rate

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception(f"Error in broadcast loop: {str(e)}")
                await asyncio.sleep(1.0)

    def _build_snapshot(self, metrics: dict) -> MetricSnapshot:
        """
        Build a metrics snapshot from raw metrics.

        Args:
            metrics: Raw metrics from MetricsTracker

        Returns:
            MetricSnapshot with organized data
        """
        snapshot = MetricSnapshot(timestamp=time.time())

        # Extract throughput metrics
        snapshot.throughput = self._extract_throughput(metrics)

        # Extract latency metrics
        snapshot.latency = self._extract_latency(metrics)

        # Extract cache metrics
        snapshot.cache = self._extract_cache_metrics()

        # Extract queue/streaming metrics
        snapshot.queue = self._extract_queue_metrics(metrics)
        snapshot.streaming = self._extract_streaming_metrics(metrics)

        # Extract error metrics
        snapshot.error = self._extract_error_metrics(metrics)

        return snapshot

    def _extract_throughput(self, metrics: dict) -> dict:
        """Extract throughput metrics (requests/sec, tokens/sec)."""
        throughput = {}

        # Requests per second by endpoint
        if "requests" in metrics:
            throughput["requests_per_sec"] = {}
            for endpoint, stats in metrics["requests"].items():
                throughput["requests_per_sec"][endpoint] = stats.get("rate", 0.0)

        # Responses per second by endpoint
        if "responses" in metrics:
            throughput["responses_per_sec"] = {}
            for endpoint, stats in metrics["responses"].items():
                throughput["responses_per_sec"][endpoint] = stats.get("rate", 0.0)

        # Tokens per second by endpoint
        if "tokens" in metrics:
            throughput["tokens_per_sec"] = {}
            for endpoint, stats in metrics["tokens"].items():
                throughput["tokens_per_sec"][endpoint] = stats.get("rate", 0.0)

        # Calculate totals
        throughput["total_requests_per_sec"] = sum(
            throughput.get("requests_per_sec", {}).values()
        )
        throughput["total_tokens_per_sec"] = sum(
            throughput.get("tokens_per_sec", {}).values()
        )

        return throughput

    def _extract_latency(self, metrics: dict) -> dict:
        """Extract latency metrics (avg, p50, p99, etc)."""
        latency = {}

        if "responses" in metrics:
            for endpoint, stats in metrics["responses"].items():
                latency[endpoint] = {
                    "avg": stats.get("avg", 0.0) * 1000,  # Convert to ms
                    "min": stats.get("min", 0.0) * 1000,
                    "max": stats.get("max", 0.0) * 1000,
                    "p50": stats.get("p50", 0.0) * 1000,
                    "p90": stats.get("p90", 0.0) * 1000,
                    "p99": stats.get("p99", 0.0) * 1000,
                }

        return latency

    def _extract_cache_metrics(self) -> dict:
        """Extract KV cache performance metrics."""
        try:
            cache_stats = (
                self.metrics_tracker.fakeai_service.kv_cache_metrics.get_stats()
            )

            # Extract cache performance
            cache_perf = cache_stats.get("cache_performance", {})

            return {
                "hit_rate": cache_perf.get("hit_rate", 0.0),
                "token_reuse_rate": cache_perf.get("token_reuse_rate", 0.0),
                "avg_prefix_length": cache_perf.get("avg_prefix_length", 0.0),
                "total_lookups": cache_perf.get("total_lookups", 0),
                "cache_hits": cache_perf.get("cache_hits", 0),
                "by_endpoint": cache_perf.get("by_endpoint", {}),
            }
        except (AttributeError, Exception) as e:
            logger.debug(f"KV cache metrics not available: {str(e)}")
            return {}

    def _extract_queue_metrics(self, metrics: dict) -> dict:
        """Extract queue depth and active request metrics."""
        queue = {}

        # Get active streams as a proxy for queue depth
        streaming_stats = metrics.get("streaming_stats", {})
        queue["active_streams"] = streaming_stats.get("active_streams", 0)
        queue["queue_depth"] = streaming_stats.get("active_streams", 0)

        return queue

    def _extract_streaming_metrics(self, metrics: dict) -> dict:
        """Extract streaming-specific metrics (TTFT, ITL)."""
        streaming = {}

        streaming_stats = metrics.get("streaming_stats", {})

        streaming["active_streams"] = streaming_stats.get("active_streams", 0)
        streaming["completed_streams"] = streaming_stats.get("completed_streams", 0)
        streaming["failed_streams"] = streaming_stats.get("failed_streams", 0)

        # TTFT stats
        ttft = streaming_stats.get("ttft", {})
        if ttft:
            streaming["ttft"] = {
                "avg": ttft.get("avg", 0.0) * 1000,  # Convert to ms
                "min": ttft.get("min", 0.0) * 1000,
                "max": ttft.get("max", 0.0) * 1000,
                "p50": ttft.get("p50", 0.0) * 1000,
                "p90": ttft.get("p90", 0.0) * 1000,
                "p99": ttft.get("p99", 0.0) * 1000,
            }

        # Tokens per second stats
        tps = streaming_stats.get("tokens_per_second", {})
        if tps:
            streaming["tokens_per_second"] = {
                "avg": tps.get("avg", 0.0),
                "min": tps.get("min", 0.0),
                "max": tps.get("max", 0.0),
                "p50": tps.get("p50", 0.0),
                "p90": tps.get("p90", 0.0),
                "p99": tps.get("p99", 0.0),
            }

        return streaming

    def _extract_error_metrics(self, metrics: dict) -> dict:
        """Extract error rate metrics."""
        errors = {}

        if "errors" in metrics:
            errors["errors_per_sec"] = {}
            for endpoint, stats in metrics["errors"].items():
                errors["errors_per_sec"][endpoint] = stats.get("rate", 0.0)

            # Calculate total error rate
            errors["total_errors_per_sec"] = sum(errors["errors_per_sec"].values())

        return errors

    async def _broadcast_snapshot(self, snapshot: MetricSnapshot):
        """
        Broadcast metrics snapshot to all connected clients.

        Args:
            snapshot: Metrics snapshot to broadcast
        """
        disconnected_clients = []

        for ws_id, client in list(self.clients.items()):
            if not client.connected:
                disconnected_clients.append(ws_id)
                continue

            # Check if enough time has passed since last update
            if time.time() - client.last_update < client.filters.interval:
                continue

            try:
                # Filter metrics based on client subscription
                filtered_data = self._filter_snapshot(snapshot, client.filters)

                # Calculate deltas if requested
                deltas = self._calculate_deltas(snapshot, self._previous_snapshot)

                # Send update
                await self._send_message(
                    client,
                    {
                        "type": "metrics_update",
                        "timestamp": snapshot.timestamp,
                        "data": filtered_data,
                        "deltas": deltas,
                    },
                )

                client.last_update = time.time()

            except Exception as e:
                logger.exception(f"Error broadcasting to client {ws_id}: {str(e)}")
                client.connected = False
                disconnected_clients.append(ws_id)

        # Clean up disconnected clients
        for ws_id in disconnected_clients:
            if ws_id in self.clients:
                del self.clients[ws_id]

    def _filter_snapshot(
        self, snapshot: MetricSnapshot, filters: SubscriptionFilter
    ) -> dict:
        """
        Filter snapshot data based on subscription filters.

        Args:
            snapshot: Metrics snapshot
            filters: Client subscription filters

        Returns:
            Filtered metrics data
        """
        filtered = {}

        # Determine which metric types to include
        include_all = MetricType.ALL in filters.metric_types

        # Filter throughput
        if include_all or MetricType.THROUGHPUT in filters.metric_types:
            filtered["throughput"] = self._filter_by_endpoint(
                snapshot.throughput, filters.endpoints
            )

        # Filter latency
        if include_all or MetricType.LATENCY in filters.metric_types:
            filtered["latency"] = self._filter_by_endpoint(
                snapshot.latency, filters.endpoints
            )

        # Filter cache
        if include_all or MetricType.CACHE in filters.metric_types:
            filtered["cache"] = snapshot.cache

        # Filter queue
        if include_all or MetricType.QUEUE in filters.metric_types:
            filtered["queue"] = snapshot.queue

        # Filter streaming
        if include_all or MetricType.STREAMING in filters.metric_types:
            filtered["streaming"] = snapshot.streaming

        # Filter errors
        if include_all or MetricType.ERROR in filters.metric_types:
            filtered["error"] = self._filter_by_endpoint(
                snapshot.error, filters.endpoints
            )

        return filtered

    def _filter_by_endpoint(self, data: dict, endpoints: Set[str]) -> dict:
        """
        Filter metrics data by endpoint.

        Args:
            data: Metrics data to filter
            endpoints: Set of endpoints to include (empty = all)

        Returns:
            Filtered data
        """
        if not endpoints:
            return data

        filtered = {}
        for key, value in data.items():
            if isinstance(value, dict):
                # Filter nested endpoint data
                filtered[key] = {
                    endpoint: metrics
                    for endpoint, metrics in value.items()
                    if endpoint in endpoints
                }
            else:
                # Include non-dict values as-is
                filtered[key] = value

        return filtered

    def _calculate_deltas(
        self, current: MetricSnapshot, previous: Optional[MetricSnapshot]
    ) -> dict:
        """
        Calculate deltas between current and previous snapshots.

        Args:
            current: Current snapshot
            previous: Previous snapshot (may be None)

        Returns:
            Dictionary of deltas
        """
        if not previous:
            return {}

        deltas = {}

        # Calculate throughput deltas
        if current.throughput and previous.throughput:
            deltas["throughput"] = {
                "total_requests_per_sec": (
                    current.throughput.get("total_requests_per_sec", 0.0)
                    - previous.throughput.get("total_requests_per_sec", 0.0)
                ),
                "total_tokens_per_sec": (
                    current.throughput.get("total_tokens_per_sec", 0.0)
                    - previous.throughput.get("total_tokens_per_sec", 0.0)
                ),
            }

        # Calculate active stream delta
        if current.streaming and previous.streaming:
            deltas["streaming"] = {
                "active_streams_delta": (
                    current.streaming.get("active_streams", 0)
                    - previous.streaming.get("active_streams", 0)
                ),
            }

        return deltas

    async def _send_message(self, client: ClientConnection, message: dict):
        """
        Send a JSON message to a client.

        Args:
            client: Client connection
            message: Message dictionary to send
        """
        try:
            await client.websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Error sending message to client {client.ws_id}: {str(e)}")
            client.connected = False
            raise

    async def _send_error(self, client: ClientConnection, error_message: str):
        """
        Send an error message to a client.

        Args:
            client: Client connection
            error_message: Error message to send
        """
        await self._send_message(
            client,
            {
                "type": "error",
                "timestamp": time.time(),
                "message": error_message,
            },
        )

    def subscribe(self, ws_id: str, filters: dict):
        """
        Subscribe a client to specific metrics (deprecated - use WebSocket messages).

        Args:
            ws_id: WebSocket client ID
            filters: Filter configuration
        """
        logger.warning(
            "subscribe() method is deprecated - use WebSocket subscribe message"
        )

        if ws_id not in self.clients:
            logger.warning(f"Client {ws_id} not found")
            return

        client = self.clients[ws_id]

        # Update filters
        if "endpoint" in filters:
            client.filters.endpoints.add(filters["endpoint"])
        if "model" in filters:
            client.filters.models.add(filters["model"])
        if "interval" in filters:
            client.filters.interval = filters["interval"]

    def broadcast_update(self, metrics: dict):
        """
        Broadcast metrics update to all subscribers (deprecated - automatic).

        Args:
            metrics: Metrics dictionary to broadcast
        """
        logger.warning(
            "broadcast_update() method is deprecated - broadcasting is automatic"
        )

    def get_active_connections(self) -> int:
        """
        Get the number of active WebSocket connections.

        Returns:
            Number of connected clients
        """
        return len([c for c in self.clients.values() if c.connected])

    def get_client_info(self) -> List[dict]:
        """
        Get information about all connected clients.

        Returns:
            List of client info dictionaries
        """
        return [
            {
                "ws_id": client.ws_id,
                "connected": client.connected,
                "filters": {
                    "endpoints": list(client.filters.endpoints),
                    "models": list(client.filters.models),
                    "metric_types": [mt.value for mt in client.filters.metric_types],
                    "interval": client.filters.interval,
                },
                "last_update": client.last_update,
            }
            for client in self.clients.values()
        ]
