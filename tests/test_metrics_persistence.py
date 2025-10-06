#!/usr/bin/env python3
"""
Tests for metrics persistence module.
"""
#  SPDX-License-Identifier: Apache-2.0

import json
import sqlite3
import tempfile
import time
from enum import Enum
from pathlib import Path

import pytest

from fakeai.metrics_persistence import (
    AggregationType,
    ExportFormat,
    MetricSnapshot,
    MetricsPersistence,
)


@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    yield db_path
    # Cleanup
    if db_path.exists():
        db_path.unlink()
    wal_path = db_path.with_suffix(".db-wal")
    if wal_path.exists():
        wal_path.unlink()
    shm_path = db_path.with_suffix(".db-shm")
    if shm_path.exists():
        shm_path.unlink()


@pytest.fixture
def persistence(temp_db):
    """Create MetricsPersistence instance."""
    mp = MetricsPersistence(db_path=temp_db, auto_cleanup=False)
    yield mp
    mp.shutdown()


class TestInitialization:
    """Test initialization and database setup."""

    def test_database_creation(self, temp_db):
        """Test that database is created with correct schema."""
        mp = MetricsPersistence(db_path=temp_db, auto_cleanup=False)

        # Check database file exists
        assert temp_db.exists()

        # Check schema
        conn = sqlite3.connect(str(temp_db))
        cursor = conn.cursor()

        # Check table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='metrics_timeseries'"
        )
        assert cursor.fetchone() is not None

        # Check indices exist
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'"
        )
        indices = cursor.fetchall()
        assert len(indices) >= 6  # At least 6 indices

        conn.close()
        mp.shutdown()

    def test_thread_local_connections(self, persistence):
        """Test that connections are thread-local."""
        conn1 = persistence._get_connection()
        conn2 = persistence._get_connection()
        assert conn1 is conn2  # Same thread should get same connection

    def test_wal_mode_enabled(self, temp_db):
        """Test that WAL mode is enabled."""
        mp = MetricsPersistence(db_path=temp_db, auto_cleanup=False)
        conn = mp._get_connection()
        cursor = conn.cursor()
        cursor.execute("PRAGMA journal_mode")
        mode = cursor.fetchone()[0]
        assert mode.lower() == "wal"
        mp.shutdown()


class TestSaveSnapshot:
    """Test saving metrics snapshots."""

    def test_save_simple_metrics(self, persistence):
        """Test saving simple metrics."""
        metrics = {
            "requests": {
                "/v1/chat/completions": {
                    "rate": 10.5,
                    "avg": 0.5,
                    "p99": 1.2,
                }
            }
        }

        persistence.save_snapshot(metrics)

        # Verify data was saved
        result = persistence.query(0, time.time() + 1)
        assert len(result.snapshots) == 3  # rate, avg, p99

    def test_save_streaming_metrics(self, persistence):
        """Test saving streaming metrics."""
        metrics = {
            "streaming_stats": {
                "active_streams": 5,
                "completed_streams": 100,
                "ttft": {
                    "avg": 0.05,
                    "p99": 0.15,
                },
            }
        }

        persistence.save_snapshot(metrics)

        # Verify data was saved
        result = persistence.query(0, time.time() + 1)
        assert len(result.snapshots) == 4  # active, completed, ttft_avg, ttft_p99

    def test_save_multiple_endpoints(self, persistence):
        """Test saving metrics for multiple endpoints."""
        metrics = {
            "requests": {
                "/v1/chat/completions": {"rate": 10.5},
                "/v1/embeddings": {"rate": 5.2},
                "/v1/completions": {"rate": 3.1},
            }
        }

        persistence.save_snapshot(metrics)

        # Verify data was saved
        result = persistence.query(0, time.time() + 1)
        assert len(result.snapshots) == 3

    def test_batch_insert_efficiency(self, persistence):
        """Test that batch insert is efficient."""
        # Create large metrics snapshot
        metrics = {
            "requests": {f"/v1/endpoint{i}": {"rate": float(i)} for i in range(100)}
        }

        start = time.time()
        persistence.save_snapshot(metrics)
        elapsed = time.time() - start

        # Should be fast (< 1 second for 100 records)
        assert elapsed < 1.0


class TestQuery:
    """Test querying metrics."""

    def test_query_time_range(self, persistence):
        """Test querying by time range."""
        now = time.time()

        # Insert metrics at different times
        snapshots = [
            MetricSnapshot(now - 100, "/test", None, "metric1", 1.0),
            MetricSnapshot(now - 50, "/test", None, "metric2", 2.0),
            MetricSnapshot(now - 10, "/test", None, "metric3", 3.0),
        ]
        persistence._batch_insert(snapshots)

        # Query middle range
        result = persistence.query(now - 60, now - 40)
        assert len(result.snapshots) == 1
        assert result.snapshots[0].metric_value == 2.0

    def test_query_by_endpoint(self, persistence):
        """Test querying by endpoint."""
        now = time.time()

        snapshots = [
            MetricSnapshot(now, "/v1/chat", None, "metric", 1.0),
            MetricSnapshot(now, "/v1/embeddings", None, "metric", 2.0),
            MetricSnapshot(now, "/v1/chat", None, "metric", 3.0),
        ]
        persistence._batch_insert(snapshots)

        result = persistence.query(0, now + 1, endpoint="/v1/chat")
        assert len(result.snapshots) == 2

    def test_query_by_model(self, persistence):
        """Test querying by model."""
        now = time.time()

        snapshots = [
            MetricSnapshot(now, "/test", "gpt-4", "metric", 1.0),
            MetricSnapshot(now, "/test", "gpt-3.5", "metric", 2.0),
            MetricSnapshot(now, "/test", "gpt-4", "metric", 3.0),
        ]
        persistence._batch_insert(snapshots)

        result = persistence.query(0, now + 1, model="gpt-4")
        assert len(result.snapshots) == 2

    def test_query_by_metric_name(self, persistence):
        """Test querying by metric name."""
        now = time.time()

        snapshots = [
            MetricSnapshot(now, "/test", None, "requests_rate", 1.0),
            MetricSnapshot(now, "/test", None, "responses_rate", 2.0),
            MetricSnapshot(now, "/test", None, "requests_rate", 3.0),
        ]
        persistence._batch_insert(snapshots)

        result = persistence.query(0, now + 1, metric_name="requests_rate")
        assert len(result.snapshots) == 2

    def test_query_with_limit(self, persistence):
        """Test querying with result limit."""
        now = time.time()

        snapshots = [
            MetricSnapshot(now, "/test", None, f"metric{i}", float(i))
            for i in range(10)
        ]
        persistence._batch_insert(snapshots)

        result = persistence.query(0, now + 1, limit=5)
        assert len(result.snapshots) == 5
        assert result.total_count == 10

    def test_query_empty_result(self, persistence):
        """Test querying with no results."""
        result = persistence.query(0, 1)
        assert len(result.snapshots) == 0
        assert result.total_count == 0
        assert result.query_time_ms >= 0


class TestAggregation:
    """Test metric aggregation."""

    def test_aggregate_sum(self, persistence):
        """Test SUM aggregation."""
        now = time.time()

        # Insert 10 metrics over 10 seconds
        snapshots = [
            MetricSnapshot(now + i, "/test", None, "counter", 1.0) for i in range(10)
        ]
        persistence._batch_insert(snapshots)

        # Aggregate into 5-second buckets
        result = persistence.aggregate(
            now, now + 10, "counter", AggregationType.SUM, 5.0
        )

        assert len(result) == 2  # Two 5-second buckets
        assert result[0][1] == 5.0  # First bucket sum
        assert result[1][1] == 5.0  # Second bucket sum

    def test_aggregate_avg(self, persistence):
        """Test AVG aggregation."""
        now = time.time()

        snapshots = [
            MetricSnapshot(now, "/test", None, "latency", 1.0),
            MetricSnapshot(now + 1, "/test", None, "latency", 3.0),
            MetricSnapshot(now + 2, "/test", None, "latency", 5.0),
        ]
        persistence._batch_insert(snapshots)

        result = persistence.aggregate(
            now, now + 3, "latency", AggregationType.AVG, 10.0
        )

        assert len(result) == 1
        assert result[0][1] == 3.0  # Average of 1, 3, 5

    def test_aggregate_min_max(self, persistence):
        """Test MIN/MAX aggregation."""
        now = time.time()

        snapshots = [
            MetricSnapshot(now, "/test", None, "value", 5.0),
            MetricSnapshot(now + 1, "/test", None, "value", 10.0),
            MetricSnapshot(now + 2, "/test", None, "value", 2.0),
        ]
        persistence._batch_insert(snapshots)

        min_result = persistence.aggregate(
            now, now + 3, "value", AggregationType.MIN, 10.0
        )
        max_result = persistence.aggregate(
            now, now + 3, "value", AggregationType.MAX, 10.0
        )

        assert min_result[0][1] == 2.0
        assert max_result[0][1] == 10.0

    def test_aggregate_count(self, persistence):
        """Test COUNT aggregation."""
        now = time.time()

        snapshots = [
            MetricSnapshot(now + i, "/test", None, "request", 1.0) for i in range(15)
        ]
        persistence._batch_insert(snapshots)

        # Aggregate into 5-second buckets
        result = persistence.aggregate(
            now, now + 15, "request", AggregationType.COUNT, 5.0
        )

        assert len(result) == 3  # Three 5-second buckets
        assert result[0][1] == 5  # Count in first bucket


class TestExport:
    """Test metric export."""

    def test_export_jsonl(self, persistence):
        """Test export to JSON Lines format."""
        now = time.time()
        snapshots = [
            MetricSnapshot(now, "/test", "model1", "metric", 1.5),
            MetricSnapshot(now + 1, "/test", None, "metric", 2.5),
        ]
        persistence._batch_insert(snapshots)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            output_path = Path(f.name)

        try:
            # Query first to verify data exists
            result = persistence.query(now - 1, now + 2)
            assert len(result.snapshots) == 2

            persistence.export(
                ExportFormat.JSONL, output_path, start_time=now - 1, end_time=now + 2
            )

            # Verify output
            with open(output_path) as f:
                lines = f.readlines()

            assert len(lines) == 2
            obj1 = json.loads(lines[0])
            assert obj1["metric_value"] == 1.5
            assert obj1["model"] == "model1"
        finally:
            output_path.unlink()

    def test_export_csv(self, persistence):
        """Test export to CSV format."""
        now = time.time()
        snapshots = [
            MetricSnapshot(now, "/test", None, "metric", 1.5),
        ]
        persistence._batch_insert(snapshots)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            output_path = Path(f.name)

        try:
            persistence.export(ExportFormat.CSV, output_path)

            # Verify output
            with open(output_path) as f:
                lines = f.readlines()

            assert len(lines) == 2  # Header + 1 data row
            assert "timestamp" in lines[0]
            assert "metric" in lines[1]
        finally:
            output_path.unlink()

    def test_export_protobuf(self, persistence):
        """Test export to protobuf format."""
        now = time.time()
        snapshots = [
            MetricSnapshot(now, "/test", "model1", "metric", 1.5),
            MetricSnapshot(now + 1, "/test", None, "metric2", 2.5),
        ]
        persistence._batch_insert(snapshots)

        with tempfile.NamedTemporaryFile(suffix=".pb", delete=False) as f:
            output_path = Path(f.name)

        try:
            persistence.export(ExportFormat.PROTOBUF, output_path)

            # Verify file exists and has content
            assert output_path.exists()
            assert output_path.stat().st_size > 0

            # Verify magic number
            with open(output_path, "rb") as f:
                magic = f.read(4)
                assert magic == b"FBAI"
        finally:
            output_path.unlink()

    def test_export_with_filters(self, persistence):
        """Test export with filters."""
        now = time.time()
        snapshots = [
            MetricSnapshot(now, "/v1/chat", None, "metric", 1.0),
            MetricSnapshot(now, "/v1/embeddings", None, "metric", 2.0),
        ]
        persistence._batch_insert(snapshots)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            output_path = Path(f.name)

        try:
            persistence.export(ExportFormat.JSONL, output_path, endpoint="/v1/chat")

            with open(output_path) as f:
                lines = f.readlines()

            assert len(lines) == 1  # Only chat endpoint
        finally:
            output_path.unlink()


class TestImportExport:
    """Test import/export round-trip."""

    def test_protobuf_roundtrip(self, persistence):
        """Test protobuf export and import."""
        now = time.time()
        original_snapshots = [
            MetricSnapshot(now, "/test", "model1", "metric1", 1.5),
            MetricSnapshot(now + 1, "/test", None, "metric2", 2.5),
            MetricSnapshot(now + 2, "/test2", "model2", "metric3", 3.5),
        ]
        persistence._batch_insert(original_snapshots)

        with tempfile.NamedTemporaryFile(suffix=".pb", delete=False) as f:
            export_path = Path(f.name)

        try:
            # Query first to verify data exists
            result = persistence.query(now - 1, now + 10)
            assert len(result.snapshots) == 3

            # Export with explicit time range
            persistence.export(
                ExportFormat.PROTOBUF,
                export_path,
                start_time=now - 1,
                end_time=now + 10,
            )

            # Create new persistence instance
            with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
                new_db = Path(f.name)

            try:
                new_persistence = MetricsPersistence(db_path=new_db, auto_cleanup=False)

                # Import
                count = new_persistence.import_protobuf(export_path)
                assert count == 3

                # Verify data
                result = new_persistence.query(0, now + 10)
                assert len(result.snapshots) == 3
                assert result.snapshots[0].metric_value == 1.5
                assert result.snapshots[1].metric_value == 2.5
                assert result.snapshots[2].metric_value == 3.5

                new_persistence.shutdown()
            finally:
                if new_db.exists():
                    new_db.unlink()
        finally:
            export_path.unlink()


class TestReplay:
    """Test metrics replay."""

    def test_replay_basic(self, persistence):
        """Test basic replay functionality."""
        now = time.time()
        snapshots = [
            MetricSnapshot(now, "/test", None, "metric", 1.0),
            MetricSnapshot(now + 0.1, "/test", None, "metric", 2.0),
            MetricSnapshot(now + 0.2, "/test", None, "metric", 3.0),
        ]
        persistence._batch_insert(snapshots)

        replayed = []

        def callback(snapshot):
            replayed.append(snapshot)

        # Replay at 10x speed
        persistence.replay_metrics(
            now, now + 1, speed_multiplier=10.0, callback=callback
        )

        assert len(replayed) == 3

    def test_replay_timing(self, persistence):
        """Test replay timing accuracy."""
        now = time.time()
        snapshots = [
            MetricSnapshot(now, "/test", None, "metric", 1.0),
            MetricSnapshot(now + 0.5, "/test", None, "metric", 2.0),
        ]
        persistence._batch_insert(snapshots)

        start = time.time()
        persistence.replay_metrics(now, now + 1, speed_multiplier=10.0)
        elapsed = time.time() - start

        # At 10x speed, 0.5 seconds should take ~0.05 seconds (with some tolerance)
        assert elapsed < 0.2  # Allow some overhead


class TestCleanup:
    """Test data cleanup."""

    def test_cleanup_old_data(self, persistence):
        """Test cleanup of old data."""
        now = time.time()

        # Insert old and new data
        snapshots = [
            MetricSnapshot(now - 10 * 86400, "/test", None, "old", 1.0),  # 10 days old
            MetricSnapshot(now - 5 * 86400, "/test", None, "medium", 2.0),  # 5 days old
            MetricSnapshot(now, "/test", None, "new", 3.0),  # Current
        ]
        persistence._batch_insert(snapshots)

        # Cleanup data older than 7 days
        deleted = persistence.cleanup_old_data(retention_days=7)
        assert deleted == 1

        # Verify only recent data remains
        result = persistence.query(0, now + 1)
        assert len(result.snapshots) == 2

    def test_cleanup_respects_retention(self, persistence):
        """Test cleanup respects retention period."""
        now = time.time()

        snapshots = [
            MetricSnapshot(now - 2 * 86400, "/test", None, "metric", 1.0),  # 2 days old
        ]
        persistence._batch_insert(snapshots)

        # Cleanup with 7-day retention should not delete
        deleted = persistence.cleanup_old_data(retention_days=7)
        assert deleted == 0


class TestStatistics:
    """Test statistics retrieval."""

    def test_get_statistics(self, persistence):
        """Test getting database statistics."""
        now = time.time()

        snapshots = [
            MetricSnapshot(now, "/v1/chat", None, "metric1", 1.0),
            MetricSnapshot(now + 1, "/v1/embeddings", None, "metric2", 2.0),
            MetricSnapshot(now + 2, "/v1/chat", None, "metric1", 3.0),
        ]
        persistence._batch_insert(snapshots)

        stats = persistence.get_statistics()

        assert stats["total_records"] == 3
        assert stats["unique_endpoints"] == 2
        assert stats["unique_metrics"] == 2
        assert stats["database_size_mb"] > 0
        assert stats["time_range"]["duration_hours"] > 0


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_database_query(self, persistence):
        """Test querying empty database."""
        result = persistence.query(0, time.time())
        assert len(result.snapshots) == 0
        assert result.total_count == 0

    def test_invalid_time_range(self, persistence):
        """Test query with invalid time range."""
        # Start time after end time
        result = persistence.query(time.time(), 0)
        assert len(result.snapshots) == 0

    def test_unsupported_export_format(self, persistence):
        """Test unsupported export format."""

        # Create a fake enum value
        class FakeFormat(Enum):
            UNSUPPORTED = "unsupported"

        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            output_path = Path(f.name)

        try:
            with pytest.raises(ValueError, match="Unsupported export format"):
                # Directly pass unsupported format to export() - it will raise ValueError
                persistence.export(FakeFormat.UNSUPPORTED, output_path)
        finally:
            if output_path.exists():
                output_path.unlink()

    def test_concurrent_access(self, persistence):
        """Test concurrent access to database."""
        import threading

        def insert_data(thread_id):
            snapshots = [
                MetricSnapshot(
                    time.time(), f"/thread{thread_id}", None, "metric", float(thread_id)
                )
            ]
            persistence._batch_insert(snapshots)

        threads = [threading.Thread(target=insert_data, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Verify all data was inserted
        result = persistence.query(0, time.time() + 1)
        assert len(result.snapshots) == 10
