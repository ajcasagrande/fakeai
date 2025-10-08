#!/usr/bin/env python3
"""
FakeAI Metrics Persistence Module

This module provides time-series metrics storage with SQLite backend,
multiple export formats, query capabilities, and replay support.
"""
#  SPDX-License-Identifier: Apache-2.0

import json
import logging
import os
import sqlite3
import struct
import threading
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class ExportFormat(Enum):
    """Supported export formats."""

    JSONL = "jsonl"  # JSON Lines
    CSV = "csv"  # CSV
    PARQUET = "parquet"  # Apache Parquet
    PROTOBUF = "protobuf"  # Protocol Buffers


class AggregationType(Enum):
    """Aggregation types for downsampling."""

    SUM = "sum"
    AVG = "avg"
    MIN = "min"
    MAX = "max"
    COUNT = "count"


@dataclass
class MetricSnapshot:
    """A single metric data point."""

    timestamp: float
    endpoint: str
    model: str | None
    metric_name: str
    metric_value: float


@dataclass
class QueryResult:
    """Result of a metrics query."""

    snapshots: list[MetricSnapshot]
    total_count: int
    query_time_ms: float


class MetricsPersistence:
    """
    Time-series metrics persistence with SQLite backend.

    Features:
    - Efficient SQLite storage with indexing
    - Automatic data rotation (7 days default)
    - Multiple export formats (JSONL, CSV, Parquet, Protobuf)
    - Query API with filtering and aggregation
    - Replay support for historical data
    - Compression for old data
    """

    def __init__(
        self,
        db_path: str | Path = "metrics.db",
        retention_days: int = 7,
        auto_cleanup: bool = True,
        compression_enabled: bool = True,
    ):
        """
        Initialize metrics persistence.

        Args:
            db_path: Path to SQLite database file
            retention_days: Number of days to retain data
            auto_cleanup: Automatically cleanup old data
            compression_enabled: Enable compression for old data
        """
        self.db_path = Path(db_path)
        self.retention_days = retention_days
        self.auto_cleanup = auto_cleanup
        self.compression_enabled = compression_enabled

        # Thread safety
        self._lock = threading.Lock()
        self._connection_local = threading.local()

        # Initialize database
        self._init_database()

        # Start cleanup thread if auto_cleanup enabled
        self._stop_cleanup = False
        if auto_cleanup:
            self._cleanup_thread = threading.Thread(
                target=self._cleanup_worker, daemon=True
            )
            self._cleanup_thread.start()

        logger.info(f"Metrics persistence initialized: {self.db_path}")

    def _get_connection(self) -> sqlite3.Connection:
        """Get thread-local database connection."""
        if not hasattr(self._connection_local, "conn"):
            self._connection_local.conn = sqlite3.connect(
                str(self.db_path),
                check_same_thread=False,
                isolation_level=None,  # Autocommit mode
            )
            self._connection_local.conn.execute("PRAGMA journal_mode=WAL")
            self._connection_local.conn.execute("PRAGMA synchronous=NORMAL")
            self._connection_local.conn.execute(
                "PRAGMA cache_size=-64000")  # 64MB
        return self._connection_local.conn

    def _init_database(self) -> None:
        """Initialize database schema."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Create main metrics table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS metrics_timeseries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                endpoint TEXT NOT NULL,
                model TEXT,
                metric_name TEXT NOT NULL,
                metric_value REAL NOT NULL
            )
        """
        )

        # Create indices for efficient queries
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_timestamp
            ON metrics_timeseries(timestamp)
        """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_endpoint
            ON metrics_timeseries(endpoint)
        """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_model
            ON metrics_timeseries(model)
        """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_metric_name
            ON metrics_timeseries(metric_name)
        """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_timestamp_endpoint
            ON metrics_timeseries(timestamp, endpoint)
        """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_timestamp_endpoint_model
            ON metrics_timeseries(timestamp, endpoint, model)
        """
        )

        conn.commit()
        logger.debug("Database schema initialized")

    def save_snapshot(self, metrics: dict[str, Any]) -> None:
        """
        Save metrics snapshot to disk.

        Args:
            metrics: Metrics dictionary from MetricsTracker.get_metrics()
        """
        timestamp = time.time()
        snapshots: list[MetricSnapshot] = []

        # Extract metrics from the nested structure
        # Format: {metric_type: {endpoint: {metric_name: value}}}
        for metric_type, endpoints in metrics.items():
            if metric_type == "streaming_stats":
                # Handle streaming stats separately
                for key, value in endpoints.items():
                    if isinstance(value, (int, float)):
                        snapshots.append(
                            MetricSnapshot(
                                timestamp=timestamp,
                                endpoint="/streaming",
                                model=None,
                                metric_name=f"streaming_{key}",
                                metric_value=float(value),
                            )
                        )
                    elif isinstance(value, dict):
                        for sub_key, sub_value in value.items():
                            if isinstance(sub_value, (int, float)):
                                snapshots.append(
                                    MetricSnapshot(
                                        timestamp=timestamp,
                                        endpoint="/streaming",
                                        model=None,
                                        metric_name=f"streaming_{key}_{sub_key}",
                                        metric_value=float(sub_value),
                                    ))
            elif isinstance(endpoints, dict):
                for endpoint, stats in endpoints.items():
                    if isinstance(stats, dict):
                        for stat_name, stat_value in stats.items():
                            if isinstance(stat_value, (int, float)):
                                snapshots.append(
                                    MetricSnapshot(
                                        timestamp=timestamp,
                                        endpoint=endpoint,
                                        model=None,
                                        metric_name=f"{metric_type}_{stat_name}",
                                        metric_value=float(stat_value),
                                    ))

        # Batch insert for efficiency
        if snapshots:
            self._batch_insert(snapshots)
            logger.debug(f"Saved {len(snapshots)} metric snapshots")

    def _batch_insert(self, snapshots: list[MetricSnapshot]) -> None:
        """Batch insert snapshots into database."""
        conn = self._get_connection()
        cursor = conn.cursor()

        data = [
            (
                s.timestamp,
                s.endpoint,
                s.model,
                s.metric_name,
                s.metric_value,
            )
            for s in snapshots
        ]

        cursor.executemany(
            """
            INSERT INTO metrics_timeseries
            (timestamp, endpoint, model, metric_name, metric_value)
            VALUES (?, ?, ?, ?, ?)
        """,
            data,
        )

        conn.commit()

    def query(
        self,
        start_time: float,
        end_time: float,
        endpoint: str | None = None,
        model: str | None = None,
        metric_name: str | None = None,
        limit: int | None = None,
    ) -> QueryResult:
        """
        Query historical metrics.

        Args:
            start_time: Start timestamp (Unix epoch)
            end_time: End timestamp (Unix epoch)
            endpoint: Filter by endpoint (optional)
            model: Filter by model (optional)
            metric_name: Filter by metric name (optional)
            limit: Maximum number of results (optional)

        Returns:
            QueryResult with snapshots and metadata
        """
        query_start = time.time()
        conn = self._get_connection()
        cursor = conn.cursor()

        # Build query
        where_clauses = ["timestamp >= ?", "timestamp <= ?"]
        params: list[Any] = [start_time, end_time]

        if endpoint is not None:
            where_clauses.append("endpoint = ?")
            params.append(endpoint)

        if model is not None:
            where_clauses.append("model = ?")
            params.append(model)

        if metric_name is not None:
            where_clauses.append("metric_name = ?")
            params.append(metric_name)

        where_sql = " AND ".join(where_clauses)
        limit_sql = f"LIMIT {limit}" if limit else ""

        # Execute query
        cursor.execute(
            f"""
            SELECT timestamp, endpoint, model, metric_name, metric_value
            FROM metrics_timeseries
            WHERE {where_sql}
            ORDER BY timestamp ASC
            {limit_sql}
        """,
            params,
        )

        # Build results
        snapshots = [
            MetricSnapshot(
                timestamp=row[0],
                endpoint=row[1],
                model=row[2],
                metric_name=row[3],
                metric_value=row[4],
            )
            for row in cursor.fetchall()
        ]

        # Get total count (without limit)
        cursor.execute(
            f"""
            SELECT COUNT(*)
            FROM metrics_timeseries
            WHERE {where_sql}
        """,
            params,
        )
        total_count = cursor.fetchone()[0]

        query_time = (time.time() - query_start) * 1000

        return QueryResult(
            snapshots=snapshots,
            total_count=total_count,
            query_time_ms=query_time,
        )

    def aggregate(
        self,
        start_time: float,
        end_time: float,
        metric_name: str,
        aggregation: AggregationType,
        interval_seconds: float,
        endpoint: str | None = None,
        model: str | None = None,
    ) -> list[tuple[float, float]]:
        """
        Aggregate metrics over time intervals (downsampling).

        Args:
            start_time: Start timestamp
            end_time: End timestamp
            metric_name: Metric to aggregate
            aggregation: Aggregation type (sum, avg, min, max, count)
            interval_seconds: Time bucket size in seconds
            endpoint: Filter by endpoint (optional)
            model: Filter by model (optional)

        Returns:
            List of (timestamp, value) tuples for each interval
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Build aggregation function
        agg_func_map = {
            AggregationType.SUM: "SUM",
            AggregationType.AVG: "AVG",
            AggregationType.MIN: "MIN",
            AggregationType.MAX: "MAX",
            AggregationType.COUNT: "COUNT",
        }
        agg_func = agg_func_map[aggregation]

        # Build WHERE clause
        where_clauses = [
            "timestamp >= ?",
            "timestamp <= ?",
            "metric_name = ?",
        ]
        params: list[Any] = [start_time, end_time, metric_name]

        if endpoint is not None:
            where_clauses.append("endpoint = ?")
            params.append(endpoint)

        if model is not None:
            where_clauses.append("model = ?")
            params.append(model)

        where_sql = " AND ".join(where_clauses)

        # Execute aggregation query
        cursor.execute(
            f"""
            SELECT
                CAST((timestamp - ?) / ? AS INTEGER) * ? + ? AS bucket_time,
                {agg_func}(metric_value) AS agg_value
            FROM metrics_timeseries
            WHERE {where_sql}
            GROUP BY bucket_time
            ORDER BY bucket_time ASC
        """,
            [start_time, interval_seconds, interval_seconds, start_time] + params,
        )

        return [(row[0], row[1]) for row in cursor.fetchall()]

    def export(
        self,
        format: ExportFormat,
        output_path: str | Path,
        start_time: float | None = None,
        end_time: float | None = None,
        endpoint: str | None = None,
        model: str | None = None,
    ) -> None:
        """
        Export metrics to file.

        Args:
            format: Export format (jsonl, csv, parquet, protobuf)
            output_path: Output file path
            start_time: Filter start time (optional)
            end_time: Filter end time (optional)
            endpoint: Filter by endpoint (optional)
            model: Filter by model (optional)
        """
        output_path = Path(output_path)

        # Query data
        if start_time is None:
            start_time = 0.0
        if end_time is None:
            end_time = time.time()

        result = self.query(
            start_time=start_time,
            end_time=end_time,
            endpoint=endpoint,
            model=model,
        )

        # Export based on format
        if format == ExportFormat.JSONL:
            self._export_jsonl(result.snapshots, output_path)
        elif format == ExportFormat.CSV:
            self._export_csv(result.snapshots, output_path)
        elif format == ExportFormat.PARQUET:
            self._export_parquet(result.snapshots, output_path)
        elif format == ExportFormat.PROTOBUF:
            self._export_protobuf(result.snapshots, output_path)
        else:
            raise ValueError(f"Unsupported export format: {format}")

        logger.info(
            f"Exported {len(result.snapshots)} metrics to {output_path} ({format.value})"
        )

    def _export_jsonl(
            self,
            snapshots: list[MetricSnapshot],
            output_path: Path) -> None:
        """Export to JSON Lines format."""
        with open(output_path, "w") as f:
            for snapshot in snapshots:
                line = json.dumps(
                    {
                        "timestamp": snapshot.timestamp,
                        "endpoint": snapshot.endpoint,
                        "model": snapshot.model,
                        "metric_name": snapshot.metric_name,
                        "metric_value": snapshot.metric_value,
                    }
                )
                f.write(line + "\n")

    def _export_csv(
            self,
            snapshots: list[MetricSnapshot],
            output_path: Path) -> None:
        """Export to CSV format."""
        import csv

        with open(output_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "endpoint", "model",
                             "metric_name", "metric_value"])
            for snapshot in snapshots:
                writer.writerow(
                    [
                        snapshot.timestamp,
                        snapshot.endpoint,
                        snapshot.model or "",
                        snapshot.metric_name,
                        snapshot.metric_value,
                    ]
                )

    def _export_parquet(
        self, snapshots: list[MetricSnapshot], output_path: Path
    ) -> None:
        """Export to Parquet format (requires pyarrow)."""
        try:
            import pyarrow as pa
            import pyarrow.parquet as pq
        except ImportError:
            raise ImportError(
                "pyarrow is required for Parquet export. Install with: pip install pyarrow"
            )

        # Convert to Arrow table
        table = pa.table(
            {
                "timestamp": [s.timestamp for s in snapshots],
                "endpoint": [s.endpoint for s in snapshots],
                "model": [s.model for s in snapshots],
                "metric_name": [s.metric_name for s in snapshots],
                "metric_value": [s.metric_value for s in snapshots],
            }
        )

        # Write to Parquet
        pq.write_table(table, output_path, compression="snappy")

    def _export_protobuf(
        self, snapshots: list[MetricSnapshot], output_path: Path
    ) -> None:
        """
        Export to Protocol Buffers format (compact binary).

        Custom simple format without protobuf library:
        - Header: "FBAI" (4 bytes magic), version (1 byte), count (4 bytes)
        - Record: timestamp (8 bytes double), endpoint_len (2 bytes), endpoint (UTF-8),
                  model_len (2 bytes), model (UTF-8), metric_name_len (2 bytes),
                  metric_name (UTF-8), metric_value (8 bytes double)
        """
        with open(output_path, "wb") as f:
            # Write header
            f.write(b"FBAI")  # Magic number
            f.write(struct.pack("B", 1))  # Version
            f.write(struct.pack("I", len(snapshots)))  # Count

            # Write records
            for snapshot in snapshots:
                # Timestamp (double)
                f.write(struct.pack("d", snapshot.timestamp))

                # Endpoint (length-prefixed UTF-8)
                endpoint_bytes = snapshot.endpoint.encode("utf-8")
                f.write(struct.pack("H", len(endpoint_bytes)))
                f.write(endpoint_bytes)

                # Model (length-prefixed UTF-8, empty if None)
                model_bytes = (snapshot.model or "").encode("utf-8")
                f.write(struct.pack("H", len(model_bytes)))
                f.write(model_bytes)

                # Metric name (length-prefixed UTF-8)
                metric_name_bytes = snapshot.metric_name.encode("utf-8")
                f.write(struct.pack("H", len(metric_name_bytes)))
                f.write(metric_name_bytes)

                # Metric value (double)
                f.write(struct.pack("d", snapshot.metric_value))

    def import_protobuf(self, input_path: str | Path) -> int:
        """
        Import metrics from Protocol Buffers format.

        Args:
            input_path: Path to protobuf file

        Returns:
            Number of metrics imported
        """
        input_path = Path(input_path)
        snapshots: list[MetricSnapshot] = []

        with open(input_path, "rb") as f:
            # Read header
            magic = f.read(4)
            if magic != b"FBAI":
                raise ValueError("Invalid protobuf file (bad magic number)")

            version = struct.unpack("B", f.read(1))[0]
            if version != 1:
                raise ValueError(f"Unsupported protobuf version: {version}")

            count = struct.unpack("I", f.read(4))[0]

            # Read records
            for _ in range(count):
                # Timestamp
                timestamp = struct.unpack("d", f.read(8))[0]

                # Endpoint
                endpoint_len = struct.unpack("H", f.read(2))[0]
                endpoint = f.read(endpoint_len).decode("utf-8")

                # Model
                model_len = struct.unpack("H", f.read(2))[0]
                model = f.read(model_len).decode(
                    "utf-8") if model_len > 0 else None

                # Metric name
                metric_name_len = struct.unpack("H", f.read(2))[0]
                metric_name = f.read(metric_name_len).decode("utf-8")

                # Metric value
                metric_value = struct.unpack("d", f.read(8))[0]

                snapshots.append(
                    MetricSnapshot(
                        timestamp=timestamp,
                        endpoint=endpoint,
                        model=model,
                        metric_name=metric_name,
                        metric_value=metric_value,
                    )
                )

        # Import into database
        if snapshots:
            self._batch_insert(snapshots)
            logger.info(f"Imported {len(snapshots)} metrics from {input_path}")

        return len(snapshots)

    def replay_metrics(
        self,
        start_time: float,
        end_time: float,
        speed_multiplier: float = 1.0,
        endpoint: str | None = None,
        model: str | None = None,
        callback: Any = None,
    ) -> None:
        """
        Replay historical metrics at same or adjusted rate.

        Args:
            start_time: Start timestamp
            end_time: End timestamp
            speed_multiplier: Speed multiplier (1.0 = real-time, 2.0 = 2x speed)
            endpoint: Filter by endpoint (optional)
            model: Filter by model (optional)
            callback: Function to call for each metric: callback(snapshot)
        """
        result = self.query(
            start_time=start_time,
            end_time=end_time,
            endpoint=endpoint,
            model=model,
        )

        if not result.snapshots:
            logger.warning("No metrics to replay")
            return

        logger.info(
            f"Replaying {len(result.snapshots)} metrics at {speed_multiplier}x speed"
        )

        # Replay with timing
        replay_start = time.time()
        first_timestamp = result.snapshots[0].timestamp

        for snapshot in result.snapshots:
            # Calculate delay to maintain timing
            elapsed_since_start = snapshot.timestamp - first_timestamp
            target_elapsed = elapsed_since_start / speed_multiplier
            actual_elapsed = time.time() - replay_start

            sleep_time = target_elapsed - actual_elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

            # Call callback
            if callback:
                callback(snapshot)

        logger.info("Replay completed")

    def cleanup_old_data(self, retention_days: int | None = None) -> int:
        """
        Delete data older than retention period.

        Args:
            retention_days: Number of days to retain (uses default if None)

        Returns:
            Number of records deleted
        """
        if retention_days is None:
            retention_days = self.retention_days

        cutoff_time = time.time() - (retention_days * 86400)

        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            DELETE FROM metrics_timeseries
            WHERE timestamp < ?
        """,
            (cutoff_time,),
        )

        deleted = cursor.rowcount
        conn.commit()

        if deleted > 0:
            # Vacuum to reclaim space
            cursor.execute("VACUUM")
            logger.info(f"Cleaned up {deleted} old metric records")

        return deleted

    def _cleanup_worker(self) -> None:
        """Background thread for automatic cleanup."""
        while not self._stop_cleanup:
            try:
                time.sleep(3600)  # Run every hour
                self.cleanup_old_data()
            except Exception as e:
                logger.error(f"Error in cleanup worker: {e}")

    def get_statistics(self) -> dict[str, Any]:
        """
        Get database statistics.

        Returns:
            Dictionary with statistics
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Total records
        cursor.execute("SELECT COUNT(*) FROM metrics_timeseries")
        total_records = cursor.fetchone()[0]

        # Time range
        cursor.execute(
            """
            SELECT MIN(timestamp), MAX(timestamp)
            FROM metrics_timeseries
        """
        )
        min_time, max_time = cursor.fetchone()

        # Unique endpoints
        cursor.execute(
            "SELECT COUNT(DISTINCT endpoint) FROM metrics_timeseries")
        unique_endpoints = cursor.fetchone()[0]

        # Unique metrics
        cursor.execute(
            "SELECT COUNT(DISTINCT metric_name) FROM metrics_timeseries")
        unique_metrics = cursor.fetchone()[0]

        # Database size
        db_size_bytes = os.path.getsize(
            self.db_path) if self.db_path.exists() else 0

        return {
            "total_records": total_records,
            "time_range": {
                "start": min_time if min_time else 0.0,
                "end": max_time if max_time else 0.0,
                "duration_hours": (max_time - min_time) / 3600 if min_time else 0.0,
            },
            "unique_endpoints": unique_endpoints,
            "unique_metrics": unique_metrics,
            "database_size_mb": db_size_bytes / (1024 * 1024),
            "retention_days": self.retention_days,
        }

    def shutdown(self) -> None:
        """Shutdown persistence and cleanup resources."""
        self._stop_cleanup = True

        # Close all connections
        if hasattr(self._connection_local, "conn"):
            self._connection_local.conn.close()

        logger.info("Metrics persistence shutdown complete")
