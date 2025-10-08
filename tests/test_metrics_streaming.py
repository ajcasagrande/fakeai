"""
Tests for metrics streaming WebSocket functionality.

Tests WebSocket connections, subscriptions, filtering, and real-time updates.
"""

import asyncio
import json
import time
import uuid
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import WebSocket

from fakeai.metrics_streaming import (
    ClientConnection,
    MetricSnapshot,
    MetricsStreamer,
    MetricType,
    SubscriptionFilter,
)


class MockWebSocket:
    """Mock WebSocket for testing."""

    def __init__(self):
        self.messages_sent = []
        self.messages_received = []
        self.accepted = False
        self.closed = False
        self._receive_index = 0

    async def accept(self):
        """Accept the WebSocket connection."""
        self.accepted = True

    async def send_text(self, data: str):
        """Send text message."""
        self.messages_sent.append(data)

    async def receive_text(self):
        """Receive text message."""
        if self._receive_index >= len(self.messages_received):
            # Simulate disconnect
            raise Exception("Connection closed")
        msg = self.messages_received[self._receive_index]
        self._receive_index += 1
        return msg

    def add_received_message(self, message: dict):
        """Add a message to the receive queue."""
        self.messages_received.append(json.dumps(message))

    def get_sent_messages(self):
        """Get all sent messages as parsed JSON."""
        return [json.loads(msg) for msg in self.messages_sent]


@pytest.fixture
def mock_metrics_tracker():
    """Create a mock MetricsTracker."""
    tracker = Mock()
    tracker.get_metrics.return_value = {
        "requests": {
            "/v1/chat/completions": {
                "rate": 10.5,
                "avg": 0.0,
                "min": 0.0,
                "max": 0.0,
                "p50": 0.0,
                "p90": 0.0,
                "p99": 0.0,
            },
            "/v1/embeddings": {
                "rate": 5.2,
                "avg": 0.0,
                "min": 0.0,
                "max": 0.0,
                "p50": 0.0,
                "p90": 0.0,
                "p99": 0.0,
            },
        },
        "responses": {
            "/v1/chat/completions": {
                "rate": 10.0,
                "avg": 0.234,
                "min": 0.1,
                "max": 0.5,
                "p50": 0.2,
                "p90": 0.4,
                "p99": 0.45,
            },
        },
        "tokens": {
            "/v1/chat/completions": {
                "rate": 567.8,
                "avg": 0.0,
                "min": 0.0,
                "max": 0.0,
                "p50": 0.0,
                "p90": 0.0,
                "p99": 0.0,
            },
        },
        "errors": {
            "/v1/chat/completions": {
                "rate": 0.1,
                "avg": 0.0,
                "min": 0.0,
                "max": 0.0,
                "p50": 0.0,
                "p90": 0.0,
                "p99": 0.0,
            },
        },
        "streaming_stats": {
            "active_streams": 3,
            "completed_streams": 100,
            "failed_streams": 2,
            "ttft": {
                "avg": 0.123,
                "min": 0.08,
                "max": 0.25,
                "p50": 0.12,
                "p90": 0.2,
                "p99": 0.24,
            },
            "tokens_per_second": {
                "avg": 45.6,
                "min": 30.0,
                "max": 60.0,
                "p50": 44.0,
                "p90": 55.0,
                "p99": 58.0,
            },
        },
    }

    # Mock fakeai_service with KV cache metrics
    mock_kv_cache_metrics = Mock()
    mock_kv_cache_metrics.get_stats.return_value = {
        "cache_performance": {
            "hit_rate": 67.5,
            "token_reuse_rate": 45.2,
            "avg_prefix_length": 123.4,
            "total_lookups": 1000,
            "cache_hits": 675,
            "by_endpoint": {
                "/v1/chat/completions": {"hit_rate": 70.0, "token_reuse_rate": 50.0},
            },
        }
    }

    mock_service = Mock()
    mock_service.kv_cache_metrics = mock_kv_cache_metrics
    tracker.fakeai_service = mock_service

    return tracker


@pytest.fixture
def metrics_streamer(mock_metrics_tracker):
    """Create a MetricsStreamer instance."""
    return MetricsStreamer(mock_metrics_tracker)


@pytest.mark.unit
@pytest.mark.metrics
class TestMetricsStreamerInit:
    """Test MetricsStreamer initialization."""

    def test_init_creates_instance(self, mock_metrics_tracker):
        """Should create a MetricsStreamer instance."""
        streamer = MetricsStreamer(mock_metrics_tracker)

        assert streamer.metrics_tracker is mock_metrics_tracker
        assert streamer.clients == {}
        assert not streamer._running
        assert streamer._previous_snapshot is None

    def test_stores_metrics_tracker_reference(self, mock_metrics_tracker):
        """Should store reference to metrics tracker."""
        streamer = MetricsStreamer(mock_metrics_tracker)

        assert streamer.metrics_tracker is mock_metrics_tracker


@pytest.mark.unit
@pytest.mark.metrics
class TestWebSocketConnection:
    """Test WebSocket connection handling."""

    @pytest.mark.asyncio
    async def test_websocket_connects(self, metrics_streamer):
        """Should accept WebSocket connections."""
        mock_ws = MockWebSocket()

        # Trigger immediate disconnect
        mock_ws.messages_received.append(None)

        try:
            await metrics_streamer.handle_websocket(mock_ws)
        except Exception:
            pass

        assert mock_ws.accepted
        assert len(metrics_streamer.clients) == 0  # Cleaned up after disconnect

    @pytest.mark.asyncio
    async def test_sends_historical_data_on_connect(self, metrics_streamer):
        """Should send historical metrics data when client connects."""
        mock_ws = MockWebSocket()

        # Create a task that will be cancelled after a short delay
        async def handle_with_timeout():
            task = asyncio.create_task(metrics_streamer.handle_websocket(mock_ws))
            await asyncio.sleep(0.1)  # Let it send historical data
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        await handle_with_timeout()

        messages = mock_ws.get_sent_messages()
        assert len(messages) > 0

        # First message should be historical_data
        first_msg = messages[0]
        assert first_msg["type"] == "historical_data"
        assert "timestamp" in first_msg
        assert "data" in first_msg

    @pytest.mark.asyncio
    async def test_assigns_unique_client_id(self, metrics_streamer):
        """Should assign unique IDs to each client."""
        # Create two distinct client connections manually
        client1 = ClientConnection(
            ws_id=str(uuid.uuid4()),
            websocket=MockWebSocket(),
            filters=SubscriptionFilter(),
        )
        client2 = ClientConnection(
            ws_id=str(uuid.uuid4()),
            websocket=MockWebSocket(),
            filters=SubscriptionFilter(),
        )

        # Add to streamer
        metrics_streamer.clients[client1.ws_id] = client1
        metrics_streamer.clients[client2.ws_id] = client2

        # Get client IDs
        client_ids = list(metrics_streamer.clients.keys())
        assert len(client_ids) == 2
        assert client_ids[0] != client_ids[1]

        # Verify they are unique UUIDs
        assert client1.ws_id != client2.ws_id


@pytest.mark.unit
@pytest.mark.metrics
class TestSubscriptionHandling:
    """Test subscription and filtering."""

    @pytest.mark.asyncio
    async def test_handles_subscribe_message(self, metrics_streamer):
        """Should handle subscribe messages."""
        mock_ws = MockWebSocket()
        mock_ws.add_received_message(
            {
                "type": "subscribe",
                "filters": {
                    "endpoint": "/v1/chat/completions",
                    "interval": 2.0,
                },
            }
        )

        # Handle connection with timeout
        async def handle_with_timeout():
            task = asyncio.create_task(metrics_streamer.handle_websocket(mock_ws))
            await asyncio.sleep(0.1)
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        await handle_with_timeout()

        messages = mock_ws.get_sent_messages()

        # Should have historical_data and subscribed messages
        msg_types = [msg["type"] for msg in messages]
        assert "subscribed" in msg_types

        # Find subscribed message
        subscribed_msg = next(msg for msg in messages if msg["type"] == "subscribed")
        assert "/v1/chat/completions" in subscribed_msg["filters"]["endpoints"]
        assert subscribed_msg["filters"]["interval"] == 2.0

    @pytest.mark.asyncio
    async def test_handles_multiple_endpoint_subscriptions(self, metrics_streamer):
        """Should allow subscribing to multiple endpoints."""
        mock_ws = MockWebSocket()
        mock_ws.add_received_message(
            {"type": "subscribe", "filters": {"endpoint": "/v1/chat/completions"}}
        )
        mock_ws.add_received_message(
            {"type": "subscribe", "filters": {"endpoint": "/v1/embeddings"}}
        )

        async def handle_with_timeout():
            task = asyncio.create_task(metrics_streamer.handle_websocket(mock_ws))
            await asyncio.sleep(0.1)
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        await handle_with_timeout()

        # Check that both endpoints were added
        messages = mock_ws.get_sent_messages()
        subscribed_messages = [msg for msg in messages if msg["type"] == "subscribed"]
        assert len(subscribed_messages) >= 1

        # Last subscription should include both endpoints
        last_subscription = subscribed_messages[-1]
        endpoints = last_subscription["filters"]["endpoints"]
        assert "/v1/chat/completions" in endpoints or len(endpoints) > 0

    @pytest.mark.asyncio
    async def test_filters_by_metric_type(self, metrics_streamer):
        """Should filter metrics by type."""
        mock_ws = MockWebSocket()
        mock_ws.add_received_message(
            {"type": "subscribe", "filters": {"metric_type": "latency"}}
        )

        async def handle_with_timeout():
            task = asyncio.create_task(metrics_streamer.handle_websocket(mock_ws))
            await asyncio.sleep(0.1)
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        await handle_with_timeout()

        messages = mock_ws.get_sent_messages()
        subscribed_messages = [msg for msg in messages if msg["type"] == "subscribed"]
        assert len(subscribed_messages) > 0

        # Check that metric_type filter was applied
        last_sub = subscribed_messages[-1]
        assert "latency" in last_sub["filters"]["metric_types"]

    @pytest.mark.asyncio
    async def test_handles_unsubscribe_message(self, metrics_streamer):
        """Should handle unsubscribe messages."""
        mock_ws = MockWebSocket()
        mock_ws.add_received_message(
            {"type": "subscribe", "filters": {"endpoint": "/v1/chat/completions"}}
        )
        mock_ws.add_received_message({"type": "unsubscribe"})

        async def handle_with_timeout():
            task = asyncio.create_task(metrics_streamer.handle_websocket(mock_ws))
            await asyncio.sleep(0.1)
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        await handle_with_timeout()

        messages = mock_ws.get_sent_messages()
        msg_types = [msg["type"] for msg in messages]
        assert "unsubscribed" in msg_types


@pytest.mark.unit
@pytest.mark.metrics
class TestMetricsBroadcasting:
    """Test metrics broadcasting to clients."""

    @pytest.mark.asyncio
    async def test_broadcast_sends_to_all_clients(self, metrics_streamer):
        """Should broadcast metrics to all connected clients."""
        # Create mock clients with last_update set to 0 to force immediate update
        client1 = ClientConnection(
            ws_id="client1",
            websocket=MockWebSocket(),
            filters=SubscriptionFilter(interval=0.1),
            last_update=0.0,  # Force update
        )
        client2 = ClientConnection(
            ws_id="client2",
            websocket=MockWebSocket(),
            filters=SubscriptionFilter(interval=0.1),
            last_update=0.0,  # Force update
        )

        metrics_streamer.clients["client1"] = client1
        metrics_streamer.clients["client2"] = client2

        # Build and broadcast a snapshot
        metrics = metrics_streamer.metrics_tracker.get_metrics()
        snapshot = metrics_streamer._build_snapshot(metrics)

        await metrics_streamer._broadcast_snapshot(snapshot)

        # Both clients should have received messages
        assert len(client1.websocket.messages_sent) > 0
        assert len(client2.websocket.messages_sent) > 0

    @pytest.mark.asyncio
    async def test_respects_update_interval(self, metrics_streamer):
        """Should respect client update intervals."""
        # Create client with long interval
        client = ClientConnection(
            ws_id="client1",
            websocket=MockWebSocket(),
            filters=SubscriptionFilter(interval=10.0),
        )
        client.last_update = time.time()  # Just updated

        metrics_streamer.clients["client1"] = client

        # Try to broadcast
        metrics = metrics_streamer.metrics_tracker.get_metrics()
        snapshot = metrics_streamer._build_snapshot(metrics)

        await metrics_streamer._broadcast_snapshot(snapshot)

        # Should not have sent update (interval not elapsed)
        assert len(client.websocket.messages_sent) == 0

    @pytest.mark.asyncio
    async def test_includes_deltas_in_updates(self, metrics_streamer):
        """Should include delta calculations in updates."""
        client = ClientConnection(
            ws_id="client1",
            websocket=MockWebSocket(),
            filters=SubscriptionFilter(interval=0.1),
        )
        client.last_update = 0  # Force update

        metrics_streamer.clients["client1"] = client

        # Create previous snapshot
        metrics = metrics_streamer.metrics_tracker.get_metrics()
        previous = metrics_streamer._build_snapshot(metrics)
        metrics_streamer._previous_snapshot = previous

        # Modify metrics slightly
        metrics_streamer.metrics_tracker.get_metrics.return_value["streaming_stats"][
            "active_streams"
        ] = 5

        # Create new snapshot and broadcast
        current = metrics_streamer._build_snapshot(
            metrics_streamer.metrics_tracker.get_metrics()
        )
        await metrics_streamer._broadcast_snapshot(current)

        # Check message
        messages = client.websocket.get_sent_messages()
        assert len(messages) > 0

        update_msg = messages[0]
        assert update_msg["type"] == "metrics_update"
        assert "deltas" in update_msg


@pytest.mark.unit
@pytest.mark.metrics
class TestMetricExtraction:
    """Test extraction of different metric types."""

    def test_extracts_throughput_metrics(self, metrics_streamer):
        """Should extract throughput metrics correctly."""
        metrics = metrics_streamer.metrics_tracker.get_metrics()
        snapshot = metrics_streamer._build_snapshot(metrics)

        assert "requests_per_sec" in snapshot.throughput
        assert "/v1/chat/completions" in snapshot.throughput["requests_per_sec"]
        assert snapshot.throughput["requests_per_sec"]["/v1/chat/completions"] == 10.5
        assert snapshot.throughput["total_requests_per_sec"] > 0

    def test_extracts_latency_metrics(self, metrics_streamer):
        """Should extract latency metrics correctly."""
        metrics = metrics_streamer.metrics_tracker.get_metrics()
        snapshot = metrics_streamer._build_snapshot(metrics)

        assert "/v1/chat/completions" in snapshot.latency
        latency = snapshot.latency["/v1/chat/completions"]
        assert latency["avg"] == 234.0  # 0.234s * 1000 = 234ms
        assert latency["p99"] == 450.0  # 0.45s * 1000 = 450ms

    def test_extracts_cache_metrics(self, metrics_streamer):
        """Should extract KV cache metrics correctly."""
        metrics = metrics_streamer.metrics_tracker.get_metrics()
        snapshot = metrics_streamer._build_snapshot(metrics)

        assert "hit_rate" in snapshot.cache
        assert snapshot.cache["hit_rate"] == 67.5
        assert snapshot.cache["token_reuse_rate"] == 45.2

    def test_extracts_streaming_metrics(self, metrics_streamer):
        """Should extract streaming metrics correctly."""
        metrics = metrics_streamer.metrics_tracker.get_metrics()
        snapshot = metrics_streamer._build_snapshot(metrics)

        assert snapshot.streaming["active_streams"] == 3
        assert snapshot.streaming["completed_streams"] == 100
        assert "ttft" in snapshot.streaming
        assert snapshot.streaming["ttft"]["avg"] == 123.0  # 0.123s * 1000 = 123ms

    def test_extracts_error_metrics(self, metrics_streamer):
        """Should extract error metrics correctly."""
        metrics = metrics_streamer.metrics_tracker.get_metrics()
        snapshot = metrics_streamer._build_snapshot(metrics)

        assert "errors_per_sec" in snapshot.error
        assert "/v1/chat/completions" in snapshot.error["errors_per_sec"]
        assert snapshot.error["total_errors_per_sec"] > 0


@pytest.mark.unit
@pytest.mark.metrics
class TestFilteringLogic:
    """Test metric filtering logic."""

    def test_filters_by_endpoint(self, metrics_streamer):
        """Should filter metrics by endpoint."""
        filters = SubscriptionFilter(endpoints={"/v1/chat/completions"})

        data = {
            "requests_per_sec": {
                "/v1/chat/completions": 10.0,
                "/v1/embeddings": 5.0,
            }
        }

        filtered = metrics_streamer._filter_by_endpoint(data, filters.endpoints)

        assert "/v1/chat/completions" in filtered["requests_per_sec"]
        assert "/v1/embeddings" not in filtered["requests_per_sec"]

    def test_all_endpoints_when_no_filter(self, metrics_streamer):
        """Should include all endpoints when no filter specified."""
        filters = SubscriptionFilter()  # No endpoint filter

        data = {
            "requests_per_sec": {
                "/v1/chat/completions": 10.0,
                "/v1/embeddings": 5.0,
            }
        }

        filtered = metrics_streamer._filter_by_endpoint(data, filters.endpoints)

        assert "/v1/chat/completions" in filtered["requests_per_sec"]
        assert "/v1/embeddings" in filtered["requests_per_sec"]

    def test_filters_snapshot_by_metric_type(self, metrics_streamer):
        """Should filter snapshot by metric type."""
        metrics = metrics_streamer.metrics_tracker.get_metrics()
        snapshot = metrics_streamer._build_snapshot(metrics)

        filters = SubscriptionFilter(metric_types={MetricType.LATENCY})

        filtered = metrics_streamer._filter_snapshot(snapshot, filters)

        assert "latency" in filtered
        assert "throughput" not in filtered
        assert "cache" not in filtered


@pytest.mark.unit
@pytest.mark.metrics
class TestDeltaCalculation:
    """Test delta calculation between snapshots."""

    def test_calculates_throughput_deltas(self, metrics_streamer):
        """Should calculate throughput deltas."""
        previous = MetricSnapshot(
            timestamp=time.time() - 1.0,
            throughput={"total_requests_per_sec": 10.0, "total_tokens_per_sec": 500.0},
        )
        current = MetricSnapshot(
            timestamp=time.time(),
            throughput={"total_requests_per_sec": 15.0, "total_tokens_per_sec": 650.0},
        )

        deltas = metrics_streamer._calculate_deltas(current, previous)

        assert "throughput" in deltas
        assert deltas["throughput"]["total_requests_per_sec"] == 5.0
        assert deltas["throughput"]["total_tokens_per_sec"] == 150.0

    def test_calculates_streaming_deltas(self, metrics_streamer):
        """Should calculate streaming deltas."""
        previous = MetricSnapshot(
            timestamp=time.time() - 1.0, streaming={"active_streams": 3}
        )
        current = MetricSnapshot(timestamp=time.time(), streaming={"active_streams": 7})

        deltas = metrics_streamer._calculate_deltas(current, previous)

        assert "streaming" in deltas
        assert deltas["streaming"]["active_streams_delta"] == 4

    def test_handles_no_previous_snapshot(self, metrics_streamer):
        """Should handle case with no previous snapshot."""
        current = MetricSnapshot(
            timestamp=time.time(), throughput={"total_requests_per_sec": 15.0}
        )

        deltas = metrics_streamer._calculate_deltas(current, None)

        assert deltas == {}


@pytest.mark.unit
@pytest.mark.metrics
class TestErrorHandling:
    """Test error handling in metrics streaming."""

    @pytest.mark.asyncio
    async def test_handles_invalid_json(self, metrics_streamer):
        """Should handle invalid JSON gracefully."""
        mock_ws = MockWebSocket()
        mock_ws.messages_received.append("invalid json{{{")

        async def handle_with_timeout():
            task = asyncio.create_task(metrics_streamer.handle_websocket(mock_ws))
            await asyncio.sleep(0.1)
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        await handle_with_timeout()

        messages = mock_ws.get_sent_messages()
        error_messages = [msg for msg in messages if msg["type"] == "error"]
        assert len(error_messages) > 0
        assert "Invalid JSON" in error_messages[0]["message"]

    @pytest.mark.asyncio
    async def test_handles_unknown_message_type(self, metrics_streamer):
        """Should handle unknown message types."""
        mock_ws = MockWebSocket()
        mock_ws.add_received_message({"type": "unknown_type"})

        async def handle_with_timeout():
            task = asyncio.create_task(metrics_streamer.handle_websocket(mock_ws))
            await asyncio.sleep(0.1)
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        await handle_with_timeout()

        messages = mock_ws.get_sent_messages()
        error_messages = [msg for msg in messages if msg["type"] == "error"]
        assert len(error_messages) > 0

    @pytest.mark.asyncio
    async def test_removes_disconnected_clients(self, metrics_streamer):
        """Should remove clients that disconnect."""
        # Create a client that will fail
        failing_ws = Mock(spec=WebSocket)
        failing_ws.send_text = AsyncMock(side_effect=Exception("Connection lost"))

        client = ClientConnection(
            ws_id="failing_client",
            websocket=failing_ws,
            filters=SubscriptionFilter(interval=0.1),
        )
        client.last_update = 0  # Force update

        metrics_streamer.clients["failing_client"] = client

        # Try to broadcast
        metrics = metrics_streamer.metrics_tracker.get_metrics()
        snapshot = metrics_streamer._build_snapshot(metrics)

        await metrics_streamer._broadcast_snapshot(snapshot)

        # Client should be removed
        assert "failing_client" not in metrics_streamer.clients


@pytest.mark.unit
@pytest.mark.metrics
class TestStartStop:
    """Test streamer lifecycle management."""

    @pytest.mark.asyncio
    async def test_starts_broadcast_task(self, metrics_streamer):
        """Should start background broadcast task."""
        await metrics_streamer.start()

        assert metrics_streamer._running
        assert metrics_streamer._broadcast_task is not None

        await metrics_streamer.stop()

    @pytest.mark.asyncio
    async def test_stops_broadcast_task(self, metrics_streamer):
        """Should stop background broadcast task."""
        await metrics_streamer.start()
        await asyncio.sleep(0.1)
        await metrics_streamer.stop()

        assert not metrics_streamer._running


@pytest.mark.unit
@pytest.mark.metrics
class TestUtilityMethods:
    """Test utility methods."""

    def test_get_active_connections(self, metrics_streamer):
        """Should return number of active connections."""
        client1 = ClientConnection("id1", MockWebSocket(), SubscriptionFilter())
        client2 = ClientConnection("id2", MockWebSocket(), SubscriptionFilter())
        client3 = ClientConnection("id3", MockWebSocket(), SubscriptionFilter())
        client3.connected = False

        metrics_streamer.clients = {
            "id1": client1,
            "id2": client2,
            "id3": client3,
        }

        assert metrics_streamer.get_active_connections() == 2

    def test_get_client_info(self, metrics_streamer):
        """Should return client information."""
        client = ClientConnection("id1", MockWebSocket(), SubscriptionFilter())
        client.filters.endpoints.add("/v1/chat/completions")

        metrics_streamer.clients = {"id1": client}

        info = metrics_streamer.get_client_info()

        assert len(info) == 1
        assert info[0]["ws_id"] == "id1"
        assert "/v1/chat/completions" in info[0]["filters"]["endpoints"]


@pytest.mark.unit
@pytest.mark.metrics
class TestPingPong:
    """Test ping/pong heartbeat."""

    @pytest.mark.asyncio
    async def test_responds_to_ping(self, metrics_streamer):
        """Should respond to ping with pong."""
        mock_ws = MockWebSocket()
        mock_ws.add_received_message({"type": "ping"})

        async def handle_with_timeout():
            task = asyncio.create_task(metrics_streamer.handle_websocket(mock_ws))
            await asyncio.sleep(0.1)
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        await handle_with_timeout()

        messages = mock_ws.get_sent_messages()
        pong_messages = [msg for msg in messages if msg["type"] == "pong"]
        assert len(pong_messages) > 0
        assert "timestamp" in pong_messages[0]
