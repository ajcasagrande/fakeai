"""
Comprehensive tests for error pattern detection and fingerprinting.

This test suite validates:
- Fingerprint generation and consistency
- Message normalization (UUIDs, request IDs, numbers, addresses)
- Pattern creation and tracking
- Pattern detection with thresholds
- Real-world error scenarios
- Complex multi-pattern scenarios

Tests ensure that similar errors are grouped together and different
errors generate unique fingerprints for effective error tracking.
"""

#  SPDX-License-Identifier: Apache-2.0

import time

import pytest

from fakeai.error_metrics_tracker import (
    ErrorMetricsTracker,
    ErrorRecord,
)


@pytest.mark.unit
@pytest.mark.metrics
class TestFingerprintGeneration:
    """Test error fingerprint generation for pattern detection."""

    def test_same_error_same_fingerprint(self):
        """Identical errors should generate the same fingerprint."""
        error1 = ErrorRecord(
            timestamp=time.time(),
            endpoint="/v1/chat/completions",
            status_code=500,
            error_type="DatabaseError",
            error_message="Connection failed",
        )

        error2 = ErrorRecord(
            timestamp=time.time(),
            endpoint="/v1/chat/completions",
            status_code=500,
            error_type="DatabaseError",
            error_message="Connection failed",
        )

        assert error1.fingerprint == error2.fingerprint

    def test_similar_errors_same_fingerprint(self):
        """Similar errors with different IDs should generate same fingerprint."""
        error1 = ErrorRecord(
            timestamp=time.time(),
            endpoint="/v1/chat/completions",
            status_code=500,
            error_type="DatabaseError",
            error_message="Connection failed for request req-abc123",
        )

        error2 = ErrorRecord(
            timestamp=time.time(),
            endpoint="/v1/chat/completions",
            status_code=500,
            error_type="DatabaseError",
            error_message="Connection failed for request req-xyz789",
        )

        # Request IDs differ but error pattern is the same
        assert error1.fingerprint == error2.fingerprint

    def test_different_errors_different_fingerprints(self):
        """Different errors should generate different fingerprints."""
        error1 = ErrorRecord(
            timestamp=time.time(),
            endpoint="/v1/chat/completions",
            status_code=500,
            error_type="DatabaseError",
            error_message="Connection timeout",
        )

        error2 = ErrorRecord(
            timestamp=time.time(),
            endpoint="/v1/chat/completions",
            status_code=400,
            error_type="ValidationError",
            error_message="Invalid API key",
        )

        assert error1.fingerprint != error2.fingerprint

    def test_different_endpoints_different_fingerprints(self):
        """Same error on different endpoints should have different fingerprints."""
        error1 = ErrorRecord(
            timestamp=time.time(),
            endpoint="/v1/chat/completions",
            status_code=500,
            error_type="TimeoutError",
            error_message="Request timeout",
        )

        error2 = ErrorRecord(
            timestamp=time.time(),
            endpoint="/v1/embeddings",
            status_code=500,
            error_type="TimeoutError",
            error_message="Request timeout",
        )

        assert error1.fingerprint != error2.fingerprint

    def test_fingerprint_length(self):
        """Fingerprints should be 8 character hex strings."""
        error = ErrorRecord(
            timestamp=time.time(),
            endpoint="/v1/chat/completions",
            status_code=500,
            error_type="InternalError",
            error_message="Something went wrong",
        )

        assert len(error.fingerprint) == 8
        assert all(c in '0123456789abcdef' for c in error.fingerprint)

    def test_fingerprint_stability(self):
        """Fingerprint should remain stable across multiple generations."""
        fingerprints = []
        for _ in range(10):
            error = ErrorRecord(
                timestamp=time.time(),
                endpoint="/v1/chat/completions",
                status_code=500,
                error_type="DatabaseError",
                error_message="Connection failed",
            )
            fingerprints.append(error.fingerprint)

        # All fingerprints should be identical
        assert len(set(fingerprints)) == 1


@pytest.mark.unit
@pytest.mark.metrics
class TestMessageNormalization:
    """Test error message normalization for fingerprinting."""

    def test_uuid_replacement(self):
        """UUIDs should be replaced with <UUID> placeholder."""
        error1 = ErrorRecord(
            timestamp=time.time(),
            endpoint="/v1/chat/completions",
            status_code=500,
            error_type="InternalError",
            error_message="Failed to process request 550e8400-e29b-41d4-a716-446655440000",
        )

        error2 = ErrorRecord(
            timestamp=time.time(),
            endpoint="/v1/chat/completions",
            status_code=500,
            error_type="InternalError",
            error_message="Failed to process request 123e4567-e89b-12d3-a456-426614174000",
        )

        assert error1.fingerprint == error2.fingerprint

    def test_request_id_replacement(self):
        """Request IDs should be replaced with <REQUEST_ID> placeholder."""
        error1 = ErrorRecord(
            timestamp=time.time(),
            endpoint="/v1/chat/completions",
            status_code=500,
            error_type="TimeoutError",
            error_message="Timeout for req-abc123xyz",
        )

        error2 = ErrorRecord(
            timestamp=time.time(),
            endpoint="/v1/chat/completions",
            status_code=500,
            error_type="TimeoutError",
            error_message="Timeout for req-def456uvw",
        )

        assert error1.fingerprint == error2.fingerprint

    def test_number_replacement(self):
        """Numbers should be replaced with <NUM> placeholder."""
        error1 = ErrorRecord(
            timestamp=time.time(),
            endpoint="/v1/chat/completions",
            status_code=500,
            error_type="TimeoutError",
            error_message="Database timeout after 5.2 seconds",
        )

        error2 = ErrorRecord(
            timestamp=time.time(),
            endpoint="/v1/chat/completions",
            status_code=500,
            error_type="TimeoutError",
            error_message="Database timeout after 3.7 seconds",
        )

        assert error1.fingerprint == error2.fingerprint

    def test_hex_address_replacement(self):
        """Hex addresses should be replaced with <ADDR> placeholder."""
        error1 = ErrorRecord(
            timestamp=time.time(),
            endpoint="/v1/chat/completions",
            status_code=500,
            error_type="MemoryError",
            error_message="Memory corruption at 0x7f8a2c3d4e5f",
        )

        error2 = ErrorRecord(
            timestamp=time.time(),
            endpoint="/v1/chat/completions",
            status_code=500,
            error_type="MemoryError",
            error_message="Memory corruption at 0x1a2b3c4d5e6f",
        )

        assert error1.fingerprint == error2.fingerprint

    def test_long_message_truncation(self):
        """Long messages should be truncated to avoid overly long signatures."""
        long_message = "Error occurred: " + ("x" * 300)

        error = ErrorRecord(
            timestamp=time.time(),
            endpoint="/v1/chat/completions",
            status_code=500,
            error_type="InternalError",
            error_message=long_message,
        )

        normalized = error._normalize_message(long_message)
        assert len(normalized) <= 200

    def test_combined_normalization(self):
        """Multiple normalization rules should work together."""
        error1 = ErrorRecord(
            timestamp=time.time(),
            endpoint="/v1/chat/completions",
            status_code=500,
            error_type="DatabaseError",
            error_message="Database timeout after 5.2s for request req-abc123 (UUID: 550e8400-e29b-41d4-a716-446655440000)",
        )

        error2 = ErrorRecord(
            timestamp=time.time(),
            endpoint="/v1/chat/completions",
            status_code=500,
            error_type="DatabaseError",
            error_message="Database timeout after 3.7s for request req-xyz789 (UUID: 123e4567-e89b-12d3-a456-426614174000)",
        )

        assert error1.fingerprint == error2.fingerprint


@pytest.mark.unit
@pytest.mark.metrics
class TestPatternCreation:
    """Test error pattern creation and tracking."""

    @pytest.fixture(autouse=True)
    def setup_tracker(self):
        """Create fresh tracker for each test."""
        tracker = ErrorMetricsTracker(
            max_recent_errors=500,
            error_budget_slo=0.999,
            window_seconds=300,
            pattern_threshold=3,
        )
        tracker.reset()
        yield tracker

    def test_first_error_creates_pattern(self, setup_tracker):
        """First error should create a new pattern."""
        tracker = setup_tracker

        tracker.record_error(
            endpoint="/v1/chat/completions",
            status_code=500,
            error_type="DatabaseError",
            error_message="Connection failed",
        )

        patterns = tracker.get_error_patterns(min_count=1)
        assert len(patterns) == 1
        assert patterns[0].count == 1

    def test_subsequent_errors_increment_count(self, setup_tracker):
        """Subsequent similar errors should increment pattern count."""
        tracker = setup_tracker

        for i in range(5):
            tracker.record_error(
                endpoint="/v1/chat/completions",
                status_code=500,
                error_type="DatabaseError",
                error_message=f"Connection failed (attempt {i})",
            )

        patterns = tracker.get_error_patterns(min_count=1)
        assert len(patterns) == 1
        assert patterns[0].count == 5

    def test_affected_models_tracked(self, setup_tracker):
        """Pattern should track all affected models."""
        tracker = setup_tracker

        tracker.record_error(
            endpoint="/v1/chat/completions",
            status_code=500,
            error_type="ModelError",
            error_message="Model loading failed",
            model="gpt-4",
        )

        tracker.record_error(
            endpoint="/v1/chat/completions",
            status_code=500,
            error_type="ModelError",
            error_message="Model loading failed",
            model="gpt-3.5-turbo",
        )

        tracker.record_error(
            endpoint="/v1/chat/completions",
            status_code=500,
            error_type="ModelError",
            error_message="Model loading failed",
            model="gpt-4",  # Duplicate
        )

        patterns = tracker.get_error_patterns(min_count=1)
        assert len(patterns) == 1
        assert len(patterns[0].affected_models) == 2
        assert "gpt-4" in patterns[0].affected_models
        assert "gpt-3.5-turbo" in patterns[0].affected_models

    def test_affected_users_tracked(self, setup_tracker):
        """Pattern should track all affected users."""
        tracker = setup_tracker

        tracker.record_error(
            endpoint="/v1/chat/completions",
            status_code=429,
            error_type="RateLimitError",
            error_message="Rate limit exceeded",
            user_id="user-123",
        )

        tracker.record_error(
            endpoint="/v1/chat/completions",
            status_code=429,
            error_type="RateLimitError",
            error_message="Rate limit exceeded",
            user_id="user-456",
        )

        tracker.record_error(
            endpoint="/v1/chat/completions",
            status_code=429,
            error_type="RateLimitError",
            error_message="Rate limit exceeded",
            user_id="user-123",  # Duplicate
        )

        patterns = tracker.get_error_patterns(min_count=1)
        assert len(patterns) == 1
        assert len(patterns[0].affected_users) == 2
        assert "user-123" in patterns[0].affected_users
        assert "user-456" in patterns[0].affected_users

    def test_example_request_ids_stored(self, setup_tracker):
        """Pattern should store example request IDs (max 10)."""
        tracker = setup_tracker

        for i in range(15):
            tracker.record_error(
                endpoint="/v1/chat/completions",
                status_code=500,
                error_type="InternalError",
                error_message="Server error",
                request_id=f"req-{i:03d}",
            )

        patterns = tracker.get_error_patterns(min_count=1)
        assert len(patterns) == 1
        assert len(patterns[0].example_request_ids) == 10  # Max 10
        assert "req-000" in patterns[0].example_request_ids
        assert "req-009" in patterns[0].example_request_ids

    def test_pattern_timestamps(self, setup_tracker):
        """Pattern should track first and last occurrence."""
        tracker = setup_tracker

        start_time = time.time()

        tracker.record_error(
            endpoint="/v1/chat/completions",
            status_code=500,
            error_type="DatabaseError",
            error_message="Connection failed",
        )

        time.sleep(0.1)

        tracker.record_error(
            endpoint="/v1/chat/completions",
            status_code=500,
            error_type="DatabaseError",
            error_message="Connection failed",
        )

        end_time = time.time()

        patterns = tracker.get_error_patterns(min_count=1)
        assert len(patterns) == 1

        pattern = patterns[0]
        assert pattern.first_seen >= start_time
        assert pattern.last_seen <= end_time
        assert pattern.last_seen > pattern.first_seen


@pytest.mark.unit
@pytest.mark.metrics
class TestPatternDetection:
    """Test error pattern detection with thresholds."""

    @pytest.fixture(autouse=True)
    def setup_tracker(self):
        """Create fresh tracker for each test."""
        tracker = ErrorMetricsTracker(
            max_recent_errors=500,
            error_budget_slo=0.999,
            window_seconds=300,
            pattern_threshold=3,
        )
        tracker.reset()
        yield tracker

    def test_patterns_above_threshold_returned(self, setup_tracker):
        """Only patterns above threshold should be returned."""
        tracker = setup_tracker

        # Pattern 1: 5 occurrences (above threshold)
        for _ in range(5):
            tracker.record_error(
                endpoint="/v1/chat/completions",
                status_code=500,
                error_type="DatabaseError",
                error_message="Connection timeout",
            )

        # Pattern 2: 2 occurrences (below threshold)
        for _ in range(2):
            tracker.record_error(
                endpoint="/v1/chat/completions",
                status_code=400,
                error_type="ValidationError",
                error_message="Invalid parameter",
            )

        # Use default threshold (3)
        patterns = tracker.get_error_patterns()
        assert len(patterns) == 1
        assert patterns[0].count == 5

    def test_recent_patterns_only(self, setup_tracker):
        """Only recent patterns should be returned when recent_only=True."""
        tracker = setup_tracker

        # Create pattern outside window
        old_error = ErrorRecord(
            timestamp=time.time() - 400,  # 400 seconds ago (outside 300s window)
            endpoint="/v1/chat/completions",
            status_code=500,
            error_type="OldError",
            error_message="Old error",
        )
        tracker._update_pattern(old_error)

        # Create recent pattern
        for _ in range(3):
            tracker.record_error(
                endpoint="/v1/chat/completions",
                status_code=500,
                error_type="RecentError",
                error_message="Recent error",
            )

        # With recent_only=True
        recent_patterns = tracker.get_error_patterns(recent_only=True)
        assert len(recent_patterns) == 1
        assert recent_patterns[0].error_type == "RecentError"

        # With recent_only=False
        all_patterns = tracker.get_error_patterns(recent_only=False)
        assert len(all_patterns) == 2

    def test_patterns_sorted_by_count_descending(self, setup_tracker):
        """Patterns should be sorted by count in descending order."""
        tracker = setup_tracker

        # Pattern 1: 3 occurrences
        for _ in range(3):
            tracker.record_error(
                endpoint="/v1/chat/completions",
                status_code=500,
                error_type="Error1",
                error_message="Error type 1",
            )

        # Pattern 2: 7 occurrences
        for _ in range(7):
            tracker.record_error(
                endpoint="/v1/chat/completions",
                status_code=400,
                error_type="Error2",
                error_message="Error type 2",
            )

        # Pattern 3: 5 occurrences
        for _ in range(5):
            tracker.record_error(
                endpoint="/v1/embeddings",
                status_code=503,
                error_type="Error3",
                error_message="Error type 3",
            )

        patterns = tracker.get_error_patterns(min_count=1)

        assert len(patterns) == 3
        assert patterns[0].count == 7  # Highest
        assert patterns[1].count == 5  # Middle
        assert patterns[2].count == 3  # Lowest

    def test_custom_min_count_threshold(self, setup_tracker):
        """Should support custom minimum count threshold."""
        tracker = setup_tracker

        # Pattern with 4 occurrences
        for _ in range(4):
            tracker.record_error(
                endpoint="/v1/chat/completions",
                status_code=500,
                error_type="DatabaseError",
                error_message="Connection failed",
            )

        # Pattern with 2 occurrences
        for _ in range(2):
            tracker.record_error(
                endpoint="/v1/chat/completions",
                status_code=400,
                error_type="ValidationError",
                error_message="Invalid input",
            )

        # min_count=5 should return nothing
        patterns_5 = tracker.get_error_patterns(min_count=5)
        assert len(patterns_5) == 0

        # min_count=3 should return 1 pattern
        patterns_3 = tracker.get_error_patterns(min_count=3)
        assert len(patterns_3) == 1

        # min_count=2 should return both patterns
        patterns_2 = tracker.get_error_patterns(min_count=2)
        assert len(patterns_2) == 2


@pytest.mark.unit
@pytest.mark.metrics
class TestRealErrorExamples:
    """Test with realistic error scenarios."""

    @pytest.fixture(autouse=True)
    def setup_tracker(self):
        """Create fresh tracker for each test."""
        tracker = ErrorMetricsTracker(
            max_recent_errors=500,
            error_budget_slo=0.999,
            window_seconds=300,
            pattern_threshold=2,
        )
        tracker.reset()
        yield tracker

    def test_database_timeout_pattern(self, setup_tracker):
        """Database timeout errors with different values should match."""
        tracker = setup_tracker

        tracker.record_error(
            endpoint="/v1/chat/completions",
            status_code=500,
            error_type="DatabaseTimeout",
            error_message="Database timeout after 5.2s for request req-abc123",
            request_id="req-abc123",
        )

        tracker.record_error(
            endpoint="/v1/chat/completions",
            status_code=500,
            error_type="DatabaseTimeout",
            error_message="Database timeout after 3.7s for request req-xyz789",
            request_id="req-xyz789",
        )

        patterns = tracker.get_error_patterns()
        assert len(patterns) == 1
        assert patterns[0].count == 2
        assert "req-abc123" in patterns[0].example_request_ids
        assert "req-xyz789" in patterns[0].example_request_ids

    def test_api_key_validation_pattern(self, setup_tracker):
        """API key validation errors should be grouped together."""
        tracker = setup_tracker

        tracker.record_error(
            endpoint="/v1/chat/completions",
            status_code=401,
            error_type="AuthenticationError",
            error_message="Invalid API key: sk-abc123xyz",
            api_key="sk-abc123xyz",
        )

        tracker.record_error(
            endpoint="/v1/chat/completions",
            status_code=401,
            error_type="AuthenticationError",
            error_message="Invalid API key: sk-def456uvw",
            api_key="sk-def456uvw",
        )

        tracker.record_error(
            endpoint="/v1/embeddings",
            status_code=401,
            error_type="AuthenticationError",
            error_message="Invalid API key: sk-ghi789rst",
            api_key="sk-ghi789rst",
        )

        patterns = tracker.get_error_patterns()
        # Different endpoints should create different patterns
        assert len(patterns) == 2

        # Check that both patterns are auth errors
        for pattern in patterns:
            assert pattern.error_type == "AuthenticationError"

    def test_rate_limit_pattern(self, setup_tracker):
        """Rate limit errors should be grouped by pattern."""
        tracker = setup_tracker

        for i in range(5):
            tracker.record_error(
                endpoint="/v1/chat/completions",
                status_code=429,
                error_type="RateLimitError",
                error_message=f"Rate limit exceeded for model gpt-4: {20 + i} requests in 60 seconds",
                model="gpt-4",
                user_id=f"user-{i % 2}",
            )

        patterns = tracker.get_error_patterns()
        assert len(patterns) == 1
        assert patterns[0].count == 5
        assert patterns[0].error_type == "RateLimitError"
        assert "gpt-4" in patterns[0].affected_models
        assert len(patterns[0].affected_users) == 2

    def test_model_loading_failure_pattern(self, setup_tracker):
        """Model loading failures across different models should be tracked."""
        tracker = setup_tracker

        models = ["gpt-4", "gpt-3.5-turbo", "text-embedding-ada-002"]

        for model in models:
            for attempt in range(2):
                tracker.record_error(
                    endpoint="/v1/chat/completions",
                    status_code=500,
                    error_type="ModelLoadError",
                    error_message=f"Failed to load model weights from path /models/{model}/checkpoint-{attempt * 1000}.pt",
                    model=model,
                )

        patterns = tracker.get_error_patterns()
        assert len(patterns) == 1
        assert patterns[0].count == 6
        assert len(patterns[0].affected_models) == 3

    def test_memory_allocation_error_pattern(self, setup_tracker):
        """Memory errors with different addresses should be grouped."""
        tracker = setup_tracker

        addresses = ["0x7f8a2c3d4e5f", "0x1a2b3c4d5e6f", "0x9f8e7d6c5b4a"]

        for addr in addresses:
            tracker.record_error(
                endpoint="/v1/chat/completions",
                status_code=500,
                error_type="MemoryError",
                error_message=f"Failed to allocate 2048MB at address {addr}",
                model="gpt-4",
            )

        patterns = tracker.get_error_patterns()
        assert len(patterns) == 1
        assert patterns[0].count == 3

    def test_connection_refused_pattern(self, setup_tracker):
        """Connection errors with different ports should match."""
        tracker = setup_tracker

        tracker.record_error(
            endpoint="/v1/embeddings",
            status_code=503,
            error_type="ConnectionError",
            error_message="Connection refused: redis://localhost:6379",
        )

        tracker.record_error(
            endpoint="/v1/embeddings",
            status_code=503,
            error_type="ConnectionError",
            error_message="Connection refused: redis://localhost:6380",
        )

        patterns = tracker.get_error_patterns()
        assert len(patterns) == 1
        assert patterns[0].count == 2


@pytest.mark.unit
@pytest.mark.metrics
class TestComplexScenarios:
    """Test complex multi-pattern scenarios."""

    @pytest.fixture(autouse=True)
    def setup_tracker(self):
        """Create fresh tracker for each test."""
        tracker = ErrorMetricsTracker(
            max_recent_errors=500,
            error_budget_slo=0.999,
            window_seconds=300,
            pattern_threshold=2,
        )
        tracker.reset()
        yield tracker

    def test_multiple_patterns_detected(self, setup_tracker):
        """Multiple distinct patterns should be detected simultaneously."""
        tracker = setup_tracker

        # Pattern 1: Database timeouts
        for i in range(4):
            tracker.record_error(
                endpoint="/v1/chat/completions",
                status_code=500,
                error_type="DatabaseTimeout",
                error_message=f"Database timeout after {i}s",
            )

        # Pattern 2: Auth failures
        for i in range(3):
            tracker.record_error(
                endpoint="/v1/chat/completions",
                status_code=401,
                error_type="AuthenticationError",
                error_message=f"Invalid API key sk-{i}",
            )

        # Pattern 3: Rate limits
        for i in range(5):
            tracker.record_error(
                endpoint="/v1/embeddings",
                status_code=429,
                error_type="RateLimitError",
                error_message=f"Rate limit exceeded: {i} requests",
            )

        patterns = tracker.get_error_patterns()
        assert len(patterns) == 3

        # Should be sorted by count
        assert patterns[0].count == 5  # Rate limits
        assert patterns[1].count == 4  # Database timeouts
        assert patterns[2].count == 3  # Auth failures

    def test_pattern_evolution_over_time(self, setup_tracker):
        """Patterns should evolve as new errors are added."""
        tracker = setup_tracker

        # Initial pattern
        tracker.record_error(
            endpoint="/v1/chat/completions",
            status_code=500,
            error_type="DatabaseError",
            error_message="Connection failed",
            model="gpt-4",
        )

        patterns = tracker.get_error_patterns(min_count=1)
        assert len(patterns) == 1
        assert patterns[0].count == 1
        assert len(patterns[0].affected_models) == 1

        # Add more occurrences with different models
        tracker.record_error(
            endpoint="/v1/chat/completions",
            status_code=500,
            error_type="DatabaseError",
            error_message="Connection failed",
            model="gpt-3.5-turbo",
        )

        tracker.record_error(
            endpoint="/v1/chat/completions",
            status_code=500,
            error_type="DatabaseError",
            error_message="Connection failed",
            model="gpt-4",  # Duplicate model
        )

        patterns = tracker.get_error_patterns(min_count=1)
        assert len(patterns) == 1
        assert patterns[0].count == 3
        assert len(patterns[0].affected_models) == 2

    def test_pattern_cleanup(self, setup_tracker):
        """Old patterns should be cleaned up."""
        tracker = setup_tracker

        # Create pattern that's old
        old_time = time.time() - 3700  # ~1 hour ago
        old_error = ErrorRecord(
            timestamp=old_time,
            endpoint="/v1/chat/completions",
            status_code=500,
            error_type="OldError",
            error_message="Old error message",
        )
        tracker._update_pattern(old_error)

        # Create recent pattern
        for _ in range(3):
            tracker.record_error(
                endpoint="/v1/chat/completions",
                status_code=500,
                error_type="RecentError",
                error_message="Recent error message",
            )

        # Verify both patterns exist
        all_patterns = tracker.get_error_patterns(min_count=1, recent_only=False)
        assert len(all_patterns) == 2

        # Clean up old patterns (age_seconds=3600 = 1 hour)
        removed = tracker.cleanup_old_patterns(age_seconds=3600)
        assert removed == 1

        # Verify only recent pattern remains
        remaining_patterns = tracker.get_error_patterns(min_count=1, recent_only=False)
        assert len(remaining_patterns) == 1
        assert remaining_patterns[0].error_type == "RecentError"

    def test_mixed_endpoint_patterns(self, setup_tracker):
        """Same error type on different endpoints should create separate patterns."""
        tracker = setup_tracker

        # Timeout on chat endpoint
        for i in range(3):
            tracker.record_error(
                endpoint="/v1/chat/completions",
                status_code=500,
                error_type="TimeoutError",
                error_message=f"Request timeout after {i}s",
            )

        # Timeout on embeddings endpoint
        for i in range(2):
            tracker.record_error(
                endpoint="/v1/embeddings",
                status_code=500,
                error_type="TimeoutError",
                error_message=f"Request timeout after {i}s",
            )

        patterns = tracker.get_error_patterns()
        assert len(patterns) == 2

        # Verify both are timeouts but on different endpoints
        endpoints = {p.endpoint for p in patterns}
        assert "/v1/chat/completions" in endpoints
        assert "/v1/embeddings" in endpoints

    def test_cascading_error_scenario(self, setup_tracker):
        """Simulate cascading failure scenario with multiple error types."""
        tracker = setup_tracker

        # Initial database issue
        for i in range(5):
            tracker.record_error(
                endpoint="/v1/chat/completions",
                status_code=500,
                error_type="DatabaseError",
                error_message=f"Connection pool exhausted: {i} connections active",
                model="gpt-4",
            )

        # Leads to timeout errors
        for i in range(4):
            tracker.record_error(
                endpoint="/v1/chat/completions",
                status_code=504,
                error_type="GatewayTimeout",
                error_message=f"Gateway timeout after {i}s waiting for database",
                model="gpt-4",
            )

        # Eventually triggers rate limiting as clients retry
        for i in range(3):
            tracker.record_error(
                endpoint="/v1/chat/completions",
                status_code=429,
                error_type="RateLimitError",
                error_message=f"Rate limit exceeded due to retries: {i} attempts",
                model="gpt-4",
            )

        patterns = tracker.get_error_patterns()
        assert len(patterns) == 3

        # All should affect the same model
        for pattern in patterns:
            assert "gpt-4" in pattern.affected_models

    def test_pattern_with_no_optional_fields(self, setup_tracker):
        """Patterns should work even without optional fields."""
        tracker = setup_tracker

        for _ in range(3):
            tracker.record_error(
                endpoint="/v1/chat/completions",
                status_code=500,
                error_type="InternalError",
                error_message="Generic error",
                # No model, user_id, or request_id
            )

        patterns = tracker.get_error_patterns()
        assert len(patterns) == 1
        assert patterns[0].count == 3
        assert len(patterns[0].affected_models) == 0
        assert len(patterns[0].affected_users) == 0
        assert len(patterns[0].example_request_ids) == 0

    def test_high_volume_pattern_detection(self, setup_tracker):
        """Pattern detection should handle high volume of errors."""
        tracker = setup_tracker

        # Simulate 100 errors across 5 patterns
        for pattern_id in range(5):
            for i in range(20):
                tracker.record_error(
                    endpoint="/v1/chat/completions",
                    status_code=500,
                    error_type=f"Error{pattern_id}",
                    error_message=f"Error pattern {pattern_id} occurrence {i}",
                    model=f"model-{pattern_id % 2}",
                    user_id=f"user-{i % 3}",
                    request_id=f"req-{pattern_id}-{i}",
                )

        patterns = tracker.get_error_patterns()
        assert len(patterns) == 5

        # All should have count of 20
        for pattern in patterns:
            assert pattern.count == 20
            assert len(pattern.example_request_ids) == 10  # Max 10
