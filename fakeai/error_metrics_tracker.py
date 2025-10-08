"""
ErrorMetricsTracker - Comprehensive error tracking and analysis.

This module provides production-ready error tracking with pattern detection,
SLO monitoring, circuit breaker integration, and detailed error analytics.

Key Features:
- Error classification by type, endpoint, model, and status code
- Error rate tracking with configurable SLO thresholds
- Error pattern detection and fingerprinting
- Recent error storage for debugging
- Per-endpoint error budgets and SLO violations
- Circuit breaker state tracking
- Error recovery metrics
- Time-windowed aggregations

Best Practices 2025:
- Type hints with Python 3.12+ syntax
- Structured error fingerprinting for pattern detection
- Memory-bounded storage with LRU-style eviction
- Thread-safe concurrent access
- Observable with detailed error context
- Prometheus-compatible metrics
- SRE-focused: error budgets, SLOs, burn rates

Usage:
    tracker = ErrorMetricsTracker(
        max_recent_errors=500,
        error_budget_slo=0.999,  # 99.9% success rate
        window_seconds=300
    )

    # Record error
    tracker.record_error(
        endpoint="/v1/chat/completions",
        status_code=500,
        error_type="InternalServerError",
        error_message="Database connection failed",
        model="gpt-4",
        api_key="sk-abc123",
        request_id="req-xyz"
    )

    # Record success
    tracker.record_success(
        endpoint="/v1/chat/completions",
        model="gpt-4"
    )

    # Check SLO status
    slo_status = tracker.get_slo_status()
    if slo_status["slo_violated"]:
        alert_on_call()

    # Get metrics
    metrics = tracker.get_metrics()
    patterns = tracker.get_error_patterns()
"""
#  SPDX-License-Identifier: Apache-2.0

import hashlib
import logging
import threading
import time
from collections import Counter, defaultdict, deque
from dataclasses import asdict, dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class ErrorRecord:
    """
    Detailed record of a single error.

    Captures all relevant context for debugging and analysis.
    """

    timestamp: float
    endpoint: str
    status_code: int
    error_type: str
    error_message: str

    # Optional context
    model: Optional[str] = None
    api_key: Optional[str] = None
    request_id: Optional[str] = None
    user_id: Optional[str] = None
    stack_trace: Optional[str] = None

    # Derived fields
    fingerprint: Optional[str] = None

    def __post_init__(self):
        """Generate error fingerprint for pattern matching."""
        if not self.fingerprint:
            self.fingerprint = self._generate_fingerprint()

    def _generate_fingerprint(self) -> str:
        """
        Generate a fingerprint for error pattern detection.

        Combines error type, endpoint, and normalized message to create
        a signature that groups similar errors together.

        Returns:
            8-character hex fingerprint
        """
        # Normalize error message (remove dynamic parts)
        normalized_message = self._normalize_message(self.error_message)

        # Create signature
        signature = f"{self.error_type}:{self.endpoint}:{normalized_message}"

        # Hash to fingerprint
        hash_obj = hashlib.sha256(signature.encode())
        return hash_obj.hexdigest()[:8]

    def _normalize_message(self, message: str) -> str:
        """
        Normalize error message by removing dynamic content.

        Replaces UUIDs, timestamps, numbers, and other variable data
        with placeholders to enable pattern matching.

        Args:
            message: Raw error message

        Returns:
            Normalized message
        """
        import re

        # Replace UUIDs
        message = re.sub(
            r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',
            '<UUID>',
            message,
            flags=re.IGNORECASE
        )

        # Replace request IDs
        message = re.sub(r'req-[a-zA-Z0-9]+', '<REQUEST_ID>', message)

        # Replace hex addresses (before numbers to avoid breaking the pattern)
        message = re.sub(r'0x[0-9a-fA-F]+', '<ADDR>', message)

        # Replace numbers
        message = re.sub(r'\d+', '<NUM>', message)

        # Truncate to avoid overly long signatures
        return message[:200]

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "timestamp": self.timestamp,
            "endpoint": self.endpoint,
            "status_code": self.status_code,
            "error_type": self.error_type,
            "error_message": self.error_message,
            "model": self.model,
            "api_key": self.api_key[:20] + "..." if self.api_key else None,
            "request_id": self.request_id,
            "user_id": self.user_id,
            "fingerprint": self.fingerprint,
        }


@dataclass
class ErrorPattern:
    """
    Detected error pattern across multiple occurrences.

    Groups errors by fingerprint to identify recurring issues.
    """

    fingerprint: str
    error_type: str
    endpoint: str
    normalized_message: str
    count: int
    first_seen: float
    last_seen: float
    affected_models: set[str] = field(default_factory=set)
    affected_users: set[str] = field(default_factory=set)
    example_request_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "fingerprint": self.fingerprint,
            "error_type": self.error_type,
            "endpoint": self.endpoint,
            "normalized_message": self.normalized_message,
            "count": self.count,
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
            "affected_models": list(self.affected_models),
            "affected_users_count": len(self.affected_users),
            "example_request_ids": self.example_request_ids[:5],
        }


@dataclass
class SLOStatus:
    """
    SLO (Service Level Objective) status for error rates.

    Tracks error budget consumption and SLO violations.
    """

    # SLO configuration
    target_success_rate: float  # e.g., 0.999 = 99.9%
    window_seconds: int

    # Current state
    total_requests: int
    successful_requests: int
    failed_requests: int
    current_success_rate: float
    current_error_rate: float

    # Error budget
    error_budget_total: int  # Total errors allowed
    error_budget_consumed: int  # Errors consumed
    error_budget_remaining: int  # Errors remaining
    error_budget_percentage: float  # Percentage remaining

    # SLO status
    slo_violated: bool
    burn_rate: float  # Current error rate / SLO error rate

    # Per-endpoint breakdown
    endpoint_error_rates: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


class ErrorMetricsTracker:
    """
    Production-ready error metrics tracker.

    Provides comprehensive error tracking with pattern detection,
    SLO monitoring, and detailed analytics.

    Thread Safety:
        All operations protected by RLock for correctness.

    Memory Management:
        - Recent errors stored in bounded deque (LRU-style)
        - Pattern detection with automatic cleanup
        - Configurable retention windows

    SRE Integration:
        - Error budgets based on SLO targets
        - Burn rate calculation for alerting
        - Per-endpoint error tracking
    """

    def __init__(
        self,
        max_recent_errors: int = 500,
        error_budget_slo: float = 0.999,
        window_seconds: int = 300,
        pattern_threshold: int = 3,
    ):
        """
        Initialize error metrics tracker.

        Args:
            max_recent_errors: Maximum recent errors to retain
            error_budget_slo: Target success rate (0.999 = 99.9%)
            window_seconds: Time window for metrics calculation
            pattern_threshold: Minimum occurrences to detect pattern
        """
        self.max_recent_errors = max_recent_errors
        self.error_budget_slo = error_budget_slo
        self.window_seconds = window_seconds
        self.pattern_threshold = pattern_threshold

        # Recent errors (bounded queue)
        self._recent_errors: deque[ErrorRecord] = deque(
            maxlen=max_recent_errors)

        # Error patterns
        self._patterns: dict[str, ErrorPattern] = {}

        # Counters
        self._total_requests = 0
        self._total_errors = 0
        self._total_successes = 0

        # Per-endpoint tracking
        self._requests_by_endpoint: dict[str, int] = defaultdict(int)
        self._errors_by_endpoint: dict[str, int] = defaultdict(int)
        self._successes_by_endpoint: dict[str, int] = defaultdict(int)

        # Per-error-type tracking
        self._errors_by_type: dict[str, int] = defaultdict(int)

        # Per-status-code tracking
        self._errors_by_status: dict[int, int] = defaultdict(int)

        # Per-model tracking
        self._errors_by_model: dict[str, int] = defaultdict(int)

        # Thread safety
        self._lock = threading.RLock()

        logger.info(
            f"ErrorMetricsTracker initialized: "
            f"slo={error_budget_slo}, "
            f"window={window_seconds}s, "
            f"max_errors={max_recent_errors}"
        )

    def record_error(
        self,
        endpoint: str,
        status_code: int,
        error_type: str,
        error_message: str,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        request_id: Optional[str] = None,
        user_id: Optional[str] = None,
        stack_trace: Optional[str] = None,
    ) -> None:
        """
        Record an error occurrence.

        Args:
            endpoint: API endpoint where error occurred
            status_code: HTTP status code
            error_type: Error type/class name
            error_message: Error message
            model: Model being used (optional)
            api_key: API key (optional)
            request_id: Request identifier (optional)
            user_id: User identifier (optional)
            stack_trace: Stack trace (optional)
        """
        with self._lock:
            # Create error record
            error = ErrorRecord(
                timestamp=time.time(),
                endpoint=endpoint,
                status_code=status_code,
                error_type=error_type,
                error_message=error_message,
                model=model,
                api_key=api_key,
                request_id=request_id,
                user_id=user_id,
                stack_trace=stack_trace,
            )

            # Store in recent errors
            self._recent_errors.append(error)

            # Update counters
            self._total_requests += 1
            self._total_errors += 1
            self._requests_by_endpoint[endpoint] += 1
            self._errors_by_endpoint[endpoint] += 1
            self._errors_by_type[error_type] += 1
            self._errors_by_status[status_code] += 1

            if model:
                self._errors_by_model[model] += 1

            # Update pattern tracking
            self._update_pattern(error)

            logger.debug(
                f"Recorded error: {endpoint} - {error_type} - {status_code} - "
                f"fingerprint={error.fingerprint}"
            )

    def record_success(
        self,
        endpoint: str,
        model: Optional[str] = None,
    ) -> None:
        """
        Record a successful request.

        Args:
            endpoint: API endpoint
            model: Model used (optional)
        """
        with self._lock:
            self._total_requests += 1
            self._total_successes += 1
            self._requests_by_endpoint[endpoint] += 1
            self._successes_by_endpoint[endpoint] += 1

    def record_request(
        self,
        endpoint: str,
        model: Optional[str] = None,
    ) -> None:
        """
        Record a request (success or failure tracked separately).

        Args:
            endpoint: API endpoint
            model: Model used (optional)
        """
        with self._lock:
            self._total_requests += 1
            self._requests_by_endpoint[endpoint] += 1

    def _update_pattern(self, error: ErrorRecord) -> None:
        """
        Update error pattern tracking.

        Args:
            error: Error record
        """
        fingerprint = error.fingerprint
        if not fingerprint:
            return

        if fingerprint in self._patterns:
            # Update existing pattern
            pattern = self._patterns[fingerprint]
            pattern.count += 1
            pattern.last_seen = error.timestamp

            if error.model:
                pattern.affected_models.add(error.model)
            if error.user_id:
                pattern.affected_users.add(error.user_id)
            if error.request_id and len(pattern.example_request_ids) < 10:
                pattern.example_request_ids.append(error.request_id)

        else:
            # Create new pattern
            pattern = ErrorPattern(
                fingerprint=fingerprint,
                error_type=error.error_type,
                endpoint=error.endpoint,
                normalized_message=error._normalize_message(
                    error.error_message),
                count=1,
                first_seen=error.timestamp,
                last_seen=error.timestamp,
            )

            if error.model:
                pattern.affected_models.add(error.model)
            if error.user_id:
                pattern.affected_users.add(error.user_id)
            if error.request_id:
                pattern.example_request_ids.append(error.request_id)

            self._patterns[fingerprint] = pattern

    def get_metrics(self) -> dict:
        """
        Get comprehensive error metrics.

        Returns:
            Dictionary containing all error metrics
        """
        with self._lock:
            # Calculate error rate
            error_rate = 0.0
            success_rate = 0.0
            if self._total_requests > 0:
                error_rate = self._total_errors / self._total_requests
                success_rate = self._total_successes / self._total_requests

            # Get windowed errors
            window_start = time.time() - self.window_seconds
            windowed_errors = [
                e for e in self._recent_errors
                if e.timestamp >= window_start
            ]

            # Top error types
            error_type_counts = Counter(e.error_type for e in windowed_errors)
            top_error_types = error_type_counts.most_common(10)

            # Top endpoints with errors
            endpoint_error_counts = Counter(
                e.endpoint for e in windowed_errors)
            top_error_endpoints = endpoint_error_counts.most_common(10)

            # Top status codes
            status_code_counts = Counter(
                e.status_code for e in windowed_errors)
            top_status_codes = status_code_counts.most_common(10)

            return {
                "total_requests": self._total_requests,
                "total_errors": self._total_errors,
                "total_successes": self._total_successes,
                "error_rate": round(error_rate, 6),
                "success_rate": round(success_rate, 6),
                "recent_errors_count": len(self._recent_errors),
                "windowed_errors_count": len(windowed_errors),
                "pattern_count": len(self._patterns),
                "top_error_types": [
                    {"type": type_, "count": count}
                    for type_, count in top_error_types
                ],
                "top_error_endpoints": [
                    {"endpoint": endpoint, "count": count}
                    for endpoint, count in top_error_endpoints
                ],
                "top_status_codes": [
                    {"status_code": code, "count": count}
                    for code, count in top_status_codes
                ],
                "errors_by_endpoint": dict(self._errors_by_endpoint),
                "errors_by_model": dict(self._errors_by_model),
            }

    def get_error_patterns(
        self,
        min_count: Optional[int] = None,
        recent_only: bool = True,
    ) -> list[ErrorPattern]:
        """
        Get detected error patterns.

        Args:
            min_count: Minimum occurrence count (defaults to pattern_threshold)
            recent_only: Only include patterns seen in time window

        Returns:
            List of error patterns sorted by count
        """
        with self._lock:
            if min_count is None:
                min_count = self.pattern_threshold

            patterns = list(self._patterns.values())

            # Filter by count
            patterns = [p for p in patterns if p.count >= min_count]

            # Filter by recency
            if recent_only:
                window_start = time.time() - self.window_seconds
                patterns = [p for p in patterns if p.last_seen >= window_start]

            # Sort by count descending
            patterns.sort(key=lambda p: p.count, reverse=True)

            return patterns

    def get_slo_status(self) -> SLOStatus:
        """
        Get SLO status and error budget information.

        Returns:
            SLO status with error budget details
        """
        with self._lock:
            # Calculate current metrics
            total = self._total_requests
            successes = self._total_successes
            failures = self._total_errors

            if total == 0:
                return SLOStatus(
                    target_success_rate=self.error_budget_slo,
                    window_seconds=self.window_seconds,
                    total_requests=0,
                    successful_requests=0,
                    failed_requests=0,
                    current_success_rate=1.0,
                    current_error_rate=0.0,
                    error_budget_total=0,
                    error_budget_consumed=0,
                    error_budget_remaining=0,
                    error_budget_percentage=100.0,
                    slo_violated=False,
                    burn_rate=0.0,
                )

            current_success_rate = successes / total
            current_error_rate = failures / total

            # Calculate error budget
            target_error_rate = 1.0 - self.error_budget_slo
            error_budget_total = int(total * target_error_rate)
            error_budget_consumed = failures
            error_budget_remaining = max(
                0, error_budget_total - error_budget_consumed)

            if error_budget_total > 0:
                error_budget_percentage = (
                    error_budget_remaining / error_budget_total) * 100
            else:
                error_budget_percentage = 100.0

            # Check SLO violation
            slo_violated = current_success_rate < self.error_budget_slo

            # Calculate burn rate
            if target_error_rate > 0:
                burn_rate = current_error_rate / target_error_rate
            else:
                burn_rate = 0.0

            # Per-endpoint error rates
            endpoint_error_rates = {}
            for endpoint in self._requests_by_endpoint:
                endpoint_total = self._requests_by_endpoint[endpoint]
                endpoint_errors = self._errors_by_endpoint.get(endpoint, 0)
                if endpoint_total > 0:
                    endpoint_error_rates[endpoint] = endpoint_errors / \
                        endpoint_total

            return SLOStatus(
                target_success_rate=self.error_budget_slo,
                window_seconds=self.window_seconds,
                total_requests=total,
                successful_requests=successes,
                failed_requests=failures,
                current_success_rate=current_success_rate,
                current_error_rate=current_error_rate,
                error_budget_total=error_budget_total,
                error_budget_consumed=error_budget_consumed,
                error_budget_remaining=error_budget_remaining,
                error_budget_percentage=error_budget_percentage,
                slo_violated=slo_violated,
                burn_rate=burn_rate,
                endpoint_error_rates=endpoint_error_rates,
            )

    def get_recent_errors(
        self,
        limit: int = 50,
        endpoint: Optional[str] = None,
        error_type: Optional[str] = None,
    ) -> list[ErrorRecord]:
        """
        Get recent errors with optional filtering.

        Args:
            limit: Maximum number of errors to return
            endpoint: Filter by endpoint (optional)
            error_type: Filter by error type (optional)

        Returns:
            List of recent errors
        """
        with self._lock:
            errors = list(self._recent_errors)

            # Filter by endpoint
            if endpoint:
                errors = [e for e in errors if e.endpoint == endpoint]

            # Filter by error type
            if error_type:
                errors = [e for e in errors if e.error_type == error_type]

            # Sort by timestamp descending (most recent first)
            errors.sort(key=lambda e: e.timestamp, reverse=True)

            # Limit
            return errors[:limit]

    def get_prometheus_metrics(self) -> str:
        """
        Export metrics in Prometheus format.

        Returns:
            Prometheus-formatted metrics string
        """
        metrics = self.get_metrics()
        slo_status = self.get_slo_status()
        lines = []

        # Total requests
        lines.append(f"# HELP error_total_requests Total number of requests")
        lines.append(f"# TYPE error_total_requests counter")
        lines.append(f"error_total_requests {metrics['total_requests']}")

        # Total errors
        lines.append(f"# HELP error_total_errors Total number of errors")
        lines.append(f"# TYPE error_total_errors counter")
        lines.append(f"error_total_errors {metrics['total_errors']}")

        # Error rate
        lines.append(f"# HELP error_rate Current error rate")
        lines.append(f"# TYPE error_rate gauge")
        lines.append(f"error_rate {metrics['error_rate']}")

        # Success rate
        lines.append(f"# HELP error_success_rate Current success rate")
        lines.append(f"# TYPE error_success_rate gauge")
        lines.append(f"error_success_rate {metrics['success_rate']}")

        # SLO status
        lines.append(
            f"# HELP error_slo_violated SLO violation status (1=violated)")
        lines.append(f"# TYPE error_slo_violated gauge")
        lines.append(
            f"error_slo_violated {
                1 if slo_status.slo_violated else 0}")

        # Error budget
        lines.append(f"# HELP error_budget_remaining Remaining error budget")
        lines.append(f"# TYPE error_budget_remaining gauge")
        lines.append(
            f"error_budget_remaining {
                slo_status.error_budget_remaining}")

        lines.append(
            f"# HELP error_budget_percentage Error budget remaining percentage")
        lines.append(f"# TYPE error_budget_percentage gauge")
        lines.append(
            f"error_budget_percentage {
                slo_status.error_budget_percentage}")

        # Burn rate
        lines.append(f"# HELP error_burn_rate Error budget burn rate")
        lines.append(f"# TYPE error_burn_rate gauge")
        lines.append(f"error_burn_rate {slo_status.burn_rate}")

        # Per-endpoint errors
        if metrics["errors_by_endpoint"]:
            lines.append(f"# HELP error_by_endpoint Errors by endpoint")
            lines.append(f"# TYPE error_by_endpoint counter")
            for endpoint, count in metrics["errors_by_endpoint"].items():
                safe_endpoint = endpoint.replace('"', '\\"')
                lines.append(
                    f'error_by_endpoint{{endpoint="{safe_endpoint}"}} {count}')

        # Per-error-type errors
        if metrics["top_error_types"]:
            lines.append(f"# HELP error_by_type Errors by type")
            lines.append(f"# TYPE error_by_type counter")
            for item in metrics["top_error_types"]:
                error_type = item["type"].replace('"', '\\"')
                count = item["count"]
                lines.append(f'error_by_type{{type="{error_type}"}} {count}')

        # Pattern count
        lines.append(
            f"# HELP error_pattern_count Number of detected error patterns")
        lines.append(f"# TYPE error_pattern_count gauge")
        lines.append(f"error_pattern_count {metrics['pattern_count']}")

        return "\n".join(lines) + "\n"

    def cleanup_old_patterns(self, age_seconds: int = 3600) -> int:
        """
        Remove old error patterns that haven't occurred recently.

        Args:
            age_seconds: Remove patterns not seen in this many seconds

        Returns:
            Number of patterns removed
        """
        with self._lock:
            cutoff = time.time() - age_seconds
            old_fingerprints = [
                fp for fp, pattern in self._patterns.items()
                if pattern.last_seen < cutoff
            ]

            for fp in old_fingerprints:
                del self._patterns[fp]

            if old_fingerprints:
                logger.info(
                    f"Cleaned up {
                        len(old_fingerprints)} old error patterns")

            return len(old_fingerprints)

    def reset(self) -> None:
        """
        Reset all metrics.

        WARNING: This clears all tracked data. Use only for testing.
        """
        with self._lock:
            self._recent_errors.clear()
            self._patterns.clear()
            self._total_requests = 0
            self._total_errors = 0
            self._total_successes = 0
            self._requests_by_endpoint.clear()
            self._errors_by_endpoint.clear()
            self._successes_by_endpoint.clear()
            self._errors_by_type.clear()
            self._errors_by_status.clear()
            self._errors_by_model.clear()

            logger.info("ErrorMetricsTracker reset")
