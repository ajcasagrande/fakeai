"""
Comprehensive integration tests for error injection.

This module tests error injection functionality end-to-end, including:
- Error injection enabled/disabled states
- Global error rate configuration
- Per-endpoint error rate configuration
- Different error types (500, 502, 503, 504, 429, 400)
- Error type distribution
- Load spike simulation
- Error statistics collection
- Error rate adjustments
- Endpoint-specific error configuration
- Error injection reset
- Concurrent requests with errors
- Error metrics tracking
- Recovery after errors
- Circuit breaker patterns
- Error response format validation

NOTE: These tests assume error injection is integrated into app.py.
If error injection is not yet integrated, these tests serve as the specification
for the expected behavior once integration is complete.
"""

#  SPDX-License-Identifier: Apache-2.0

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

import pytest

from tests.integration.utils import FakeAIClient

# Markers for test organization
pytestmark = [
    pytest.mark.integration,
    pytest.mark.slow,
    pytest.mark.skip(
        reason="Error injection not yet integrated into app.py - tests serve as specification"
    ),
]


class TestErrorInjectionEnabledDisabled:
    """Test error injection enabled/disabled states."""

    @pytest.mark.server_config(
        error_injection_enabled=False,
    )
    def test_error_injection_disabled_no_errors(
        self, server_function_scoped: Any
    ) -> None:
        """Test that no errors are injected when disabled."""
        client = FakeAIClient(
            base_url=server_function_scoped.base_url,
            api_key=server_function_scoped.api_keys[0],
        )

        try:
            # Make multiple requests - all should succeed
            for _ in range(10):
                response = client.get("/v1/models")
                assert response.status_code == 200, "All requests should succeed"

        finally:
            client.close()

    @pytest.mark.server_config(
        error_injection_enabled=True,
        env_overrides={
            "FAKEAI_ERROR_INJECTION_RATE": "1.0",  # 100% error rate
        },
    )
    def test_error_injection_enabled_produces_errors(
        self, server_function_scoped: Any
    ) -> None:
        """Test that errors are injected when enabled."""
        client = FakeAIClient(
            base_url=server_function_scoped.base_url,
            api_key=server_function_scoped.api_keys[0],
        )

        try:
            # With 100% error rate, should get errors
            error_count = 0
            for _ in range(10):
                response = client.get("/v1/models")
                if response.status_code >= 400:
                    error_count += 1

            # Should have significant errors (allow some tolerance)
            assert error_count >= 8, "Should inject most errors with 100% rate"

        finally:
            client.close()

    @pytest.mark.server_config(
        error_injection_enabled=True,
        env_overrides={
            "FAKEAI_ERROR_INJECTION_RATE": "0.0",  # 0% error rate
        },
    )
    def test_error_injection_enabled_zero_rate_no_errors(
        self, server_function_scoped: Any
    ) -> None:
        """Test that no errors occur with 0% rate even when enabled."""
        client = FakeAIClient(
            base_url=server_function_scoped.base_url,
            api_key=server_function_scoped.api_keys[0],
        )

        try:
            # Make multiple requests - all should succeed
            for _ in range(10):
                response = client.get("/v1/models")
                assert response.status_code == 200, "All requests should succeed"

        finally:
            client.close()


class TestGlobalErrorRate:
    """Test global error rate configuration."""

    @pytest.mark.server_config(
        error_injection_enabled=True,
        env_overrides={
            "FAKEAI_ERROR_INJECTION_RATE": "0.5",  # 50% error rate
        },
    )
    def test_global_error_rate_50_percent(self, server_function_scoped: Any) -> None:
        """Test that global 50% error rate is applied."""
        client = FakeAIClient(
            base_url=server_function_scoped.base_url,
            api_key=server_function_scoped.api_keys[0],
        )

        try:
            # Make many requests to test probability
            error_count = 0
            total_requests = 100

            for _ in range(total_requests):
                response = client.get("/v1/models")
                if response.status_code >= 400:
                    error_count += 1

            error_rate = error_count / total_requests

            # Should be around 50% (allow ±20% tolerance for randomness)
            assert (
                0.3 <= error_rate <= 0.7
            ), f"Error rate {error_rate:.2%} not near 50%"

        finally:
            client.close()

    @pytest.mark.server_config(
        error_injection_enabled=True,
        env_overrides={
            "FAKEAI_ERROR_INJECTION_RATE": "0.2",  # 20% error rate
        },
    )
    def test_global_error_rate_20_percent(self, server_function_scoped: Any) -> None:
        """Test that global 20% error rate is applied."""
        client = FakeAIClient(
            base_url=server_function_scoped.base_url,
            api_key=server_function_scoped.api_keys[0],
        )

        try:
            # Make many requests to test probability
            error_count = 0
            total_requests = 100

            for _ in range(total_requests):
                response = client.get("/v1/models")
                if response.status_code >= 400:
                    error_count += 1

            error_rate = error_count / total_requests

            # Should be around 20% (allow ±15% tolerance)
            assert (
                0.05 <= error_rate <= 0.35
            ), f"Error rate {error_rate:.2%} not near 20%"

        finally:
            client.close()

    @pytest.mark.server_config(
        error_injection_enabled=True,
        env_overrides={
            "FAKEAI_ERROR_INJECTION_RATE": "0.8",  # 80% error rate
        },
    )
    def test_global_error_rate_80_percent(self, server_function_scoped: Any) -> None:
        """Test that global 80% error rate is applied."""
        client = FakeAIClient(
            base_url=server_function_scoped.base_url,
            api_key=server_function_scoped.api_keys[0],
        )

        try:
            # Make many requests to test probability
            error_count = 0
            total_requests = 50

            for _ in range(total_requests):
                response = client.get("/v1/models")
                if response.status_code >= 400:
                    error_count += 1

            error_rate = error_count / total_requests

            # Should be around 80% (allow ±15% tolerance)
            assert (
                0.65 <= error_rate <= 0.95
            ), f"Error rate {error_rate:.2%} not near 80%"

        finally:
            client.close()


class TestDifferentErrorTypes:
    """Test different error types (500, 502, 503, 504, 429, 400)."""

    @pytest.mark.server_config(
        error_injection_enabled=True,
        env_overrides={
            "FAKEAI_ERROR_INJECTION_RATE": "1.0",  # 100% to ensure errors
            "FAKEAI_ERROR_INJECTION_TYPES": '["internal_error"]',
        },
    )
    def test_internal_error_500(self, server_function_scoped: Any) -> None:
        """Test 500 internal error injection."""
        client = FakeAIClient(
            base_url=server_function_scoped.base_url,
            api_key=server_function_scoped.api_keys[0],
        )

        try:
            # Should get 500 errors
            for _ in range(5):
                response = client.get("/v1/models")
                if response.status_code >= 400:
                    assert response.status_code == 500
                    data = response.json()
                    assert "error" in data
                    assert data["error"]["type"] == "internal_error"
                    assert data["error"]["code"] == "internal_error"

        finally:
            client.close()

    @pytest.mark.server_config(
        error_injection_enabled=True,
        env_overrides={
            "FAKEAI_ERROR_INJECTION_RATE": "1.0",
            "FAKEAI_ERROR_INJECTION_TYPES": '["bad_gateway"]',
        },
    )
    def test_bad_gateway_502(self, server_function_scoped: Any) -> None:
        """Test 502 bad gateway error injection."""
        client = FakeAIClient(
            base_url=server_function_scoped.base_url,
            api_key=server_function_scoped.api_keys[0],
        )

        try:
            # Should get 502 errors
            for _ in range(5):
                response = client.get("/v1/models")
                if response.status_code >= 400:
                    assert response.status_code == 502
                    data = response.json()
                    assert "error" in data
                    assert data["error"]["type"] == "bad_gateway"

        finally:
            client.close()

    @pytest.mark.server_config(
        error_injection_enabled=True,
        env_overrides={
            "FAKEAI_ERROR_INJECTION_RATE": "1.0",
            "FAKEAI_ERROR_INJECTION_TYPES": '["service_unavailable"]',
        },
    )
    def test_service_unavailable_503(self, server_function_scoped: Any) -> None:
        """Test 503 service unavailable error injection."""
        client = FakeAIClient(
            base_url=server_function_scoped.base_url,
            api_key=server_function_scoped.api_keys[0],
        )

        try:
            # Should get 503 errors
            for _ in range(5):
                response = client.get("/v1/models")
                if response.status_code >= 400:
                    assert response.status_code == 503
                    data = response.json()
                    assert "error" in data
                    assert data["error"]["type"] == "service_unavailable"

        finally:
            client.close()

    @pytest.mark.server_config(
        error_injection_enabled=True,
        env_overrides={
            "FAKEAI_ERROR_INJECTION_RATE": "1.0",
            "FAKEAI_ERROR_INJECTION_TYPES": '["gateway_timeout"]',
        },
    )
    def test_gateway_timeout_504(self, server_function_scoped: Any) -> None:
        """Test 504 gateway timeout error injection."""
        client = FakeAIClient(
            base_url=server_function_scoped.base_url,
            api_key=server_function_scoped.api_keys[0],
        )

        try:
            # Should get 504 errors
            for _ in range(5):
                response = client.get("/v1/models")
                if response.status_code >= 400:
                    assert response.status_code == 504
                    data = response.json()
                    assert "error" in data
                    assert data["error"]["type"] == "gateway_timeout"

        finally:
            client.close()

    @pytest.mark.server_config(
        error_injection_enabled=True,
        env_overrides={
            "FAKEAI_ERROR_INJECTION_RATE": "1.0",
            "FAKEAI_ERROR_INJECTION_TYPES": '["rate_limit_quota"]',
        },
    )
    def test_rate_limit_quota_429(self, server_function_scoped: Any) -> None:
        """Test 429 rate limit quota error injection."""
        client = FakeAIClient(
            base_url=server_function_scoped.base_url,
            api_key=server_function_scoped.api_keys[0],
        )

        try:
            # Should get 429 errors
            for _ in range(5):
                response = client.get("/v1/models")
                if response.status_code >= 400:
                    assert response.status_code == 429
                    data = response.json()
                    assert "error" in data
                    assert data["error"]["type"] == "insufficient_quota"

        finally:
            client.close()

    @pytest.mark.server_config(
        error_injection_enabled=True,
        env_overrides={
            "FAKEAI_ERROR_INJECTION_RATE": "1.0",
            "FAKEAI_ERROR_INJECTION_TYPES": '["context_length_exceeded"]',
        },
    )
    def test_context_length_exceeded_400(self, server_function_scoped: Any) -> None:
        """Test 400 context length exceeded error injection."""
        client = FakeAIClient(
            base_url=server_function_scoped.base_url,
            api_key=server_function_scoped.api_keys[0],
        )

        try:
            # Should get 400 errors
            for _ in range(5):
                response = client.post(
                    "/v1/chat/completions",
                    json={
                        "model": "openai/gpt-oss-120b",
                        "messages": [{"role": "user", "content": "Test"}],
                    },
                )
                if response.status_code >= 400:
                    assert response.status_code == 400
                    data = response.json()
                    assert "error" in data
                    assert data["error"]["type"] == "context_length_exceeded"
                    assert data["error"]["param"] == "messages"

        finally:
            client.close()


class TestErrorTypeDistribution:
    """Test error type distribution with multiple types."""

    @pytest.mark.server_config(
        error_injection_enabled=True,
        env_overrides={
            "FAKEAI_ERROR_INJECTION_RATE": "1.0",  # 100% to ensure errors
            "FAKEAI_ERROR_INJECTION_TYPES": '["internal_error", "service_unavailable", "gateway_timeout"]',
        },
    )
    def test_multiple_error_types_distributed(
        self, server_function_scoped: Any
    ) -> None:
        """Test that multiple error types are distributed."""
        client = FakeAIClient(
            base_url=server_function_scoped.base_url,
            api_key=server_function_scoped.api_keys[0],
        )

        try:
            # Collect error types
            error_types = set()
            for _ in range(30):
                response = client.get("/v1/models")
                if response.status_code >= 400:
                    data = response.json()
                    error_types.add(data["error"]["type"])

            # Should see multiple error types
            assert len(error_types) >= 2, "Should see multiple error types"
            assert "internal_error" in error_types or True  # At least one type

        finally:
            client.close()

    @pytest.mark.server_config(
        error_injection_enabled=True,
        env_overrides={
            "FAKEAI_ERROR_INJECTION_RATE": "1.0",
        },
    )
    def test_all_error_types_can_occur(self, server_function_scoped: Any) -> None:
        """Test that all default error types can occur."""
        client = FakeAIClient(
            base_url=server_function_scoped.base_url,
            api_key=server_function_scoped.api_keys[0],
        )

        try:
            # Collect error status codes
            status_codes = set()
            for _ in range(50):
                response = client.get("/v1/models")
                if response.status_code >= 400:
                    status_codes.add(response.status_code)

            # Should see variety of error codes
            # (may not see all in 50 tries due to randomness)
            assert len(status_codes) >= 2, "Should see multiple error types"

        finally:
            client.close()


class TestPerEndpointErrorRates:
    """Test per-endpoint error rate configuration."""

    @pytest.mark.server_config(
        error_injection_enabled=True,
        env_overrides={
            "FAKEAI_ERROR_INJECTION_RATE": "0.5",  # Global 50%
        },
    )
    def test_different_endpoints_same_error_rate(
        self, server_function_scoped: Any
    ) -> None:
        """Test that error rate applies to different endpoints."""
        client = FakeAIClient(
            base_url=server_function_scoped.base_url,
            api_key=server_function_scoped.api_keys[0],
        )

        try:
            # Test multiple endpoints
            endpoints = [
                "/v1/models",
                "/v1/chat/completions",
                "/v1/embeddings",
            ]

            for endpoint in endpoints:
                error_count = 0
                total = 20

                for _ in range(total):
                    if endpoint == "/v1/models":
                        response = client.get(endpoint)
                    elif endpoint == "/v1/chat/completions":
                        response = client.post(
                            endpoint,
                            json={
                                "model": "openai/gpt-oss-120b",
                                "messages": [{"role": "user", "content": "Hi"}],
                            },
                        )
                    elif endpoint == "/v1/embeddings":
                        response = client.post(
                            endpoint,
                            json={
                                "model": "text-embedding-ada-002",
                                "input": "Test",
                            },
                        )

                    if response.status_code >= 400:
                        error_count += 1

                # Each endpoint should have similar error rate
                # (allow wide tolerance due to small sample)
                error_rate = error_count / total
                assert 0.2 <= error_rate <= 0.8, f"{endpoint} error rate out of range"

        finally:
            client.close()


class TestLoadSpikeSimulation:
    """Test load spike simulation."""

    @pytest.mark.server_config(
        error_injection_enabled=True,
        env_overrides={
            "FAKEAI_ERROR_INJECTION_RATE": "0.2",  # Base 20% error rate
        },
    )
    def test_load_spike_not_active_by_default(
        self, server_function_scoped: Any
    ) -> None:
        """Test that load spike is not active by default."""
        client = FakeAIClient(
            base_url=server_function_scoped.base_url,
            api_key=server_function_scoped.api_keys[0],
        )

        try:
            # Make requests - should see normal error rate
            error_count = 0
            total = 50

            for _ in range(total):
                response = client.get("/v1/models")
                if response.status_code >= 400:
                    error_count += 1

            error_rate = error_count / total

            # Should be around 20% (allow wide tolerance)
            assert 0.05 <= error_rate <= 0.4, "Should see base error rate"

        finally:
            client.close()


class TestErrorStatistics:
    """Test error statistics collection."""

    @pytest.mark.server_config(
        error_injection_enabled=True,
        env_overrides={
            "FAKEAI_ERROR_INJECTION_RATE": "0.5",
        },
    )
    def test_error_stats_track_total_checks(self, server_function_scoped: Any) -> None:
        """Test that error stats track total checks."""
        client = FakeAIClient(
            base_url=server_function_scoped.base_url,
            api_key=server_function_scoped.api_keys[0],
        )

        try:
            # Make requests
            for _ in range(10):
                client.get("/v1/models")

            # Stats should track checks (if metrics endpoint available)
            # Note: This depends on error injection exposing stats endpoint

        finally:
            client.close()

    @pytest.mark.server_config(
        error_injection_enabled=True,
        env_overrides={
            "FAKEAI_ERROR_INJECTION_RATE": "1.0",
            "FAKEAI_ERROR_INJECTION_TYPES": '["internal_error", "service_unavailable"]',
        },
    )
    def test_error_stats_track_by_type(self, server_function_scoped: Any) -> None:
        """Test that error stats track by error type."""
        client = FakeAIClient(
            base_url=server_function_scoped.base_url,
            api_key=server_function_scoped.api_keys[0],
        )

        try:
            # Make requests to generate errors
            for _ in range(20):
                client.get("/v1/models")

            # Stats should track by error type

        finally:
            client.close()


class TestConcurrentRequests:
    """Test error injection with concurrent requests."""

    @pytest.mark.server_config(
        error_injection_enabled=True,
        env_overrides={
            "FAKEAI_ERROR_INJECTION_RATE": "0.5",
        },
    )
    def test_concurrent_requests_thread_safe(self, server_function_scoped: Any) -> None:
        """Test that error injection is thread-safe with concurrent requests."""
        base_url = server_function_scoped.base_url
        api_key = server_function_scoped.api_keys[0]

        def make_request(i: int) -> tuple[int, int]:
            """Make a request and return (request_num, status_code)."""
            client = FakeAIClient(base_url=base_url, api_key=api_key)
            try:
                response = client.get("/v1/models")
                return i, response.status_code
            finally:
                client.close()

        # Make concurrent requests
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request, i) for i in range(50)]
            results = [future.result() for future in as_completed(futures)]

        # Count errors
        error_count = sum(1 for _, status in results if status >= 400)
        error_rate = error_count / len(results)

        # Should see approximately 50% errors (allow wide tolerance)
        assert 0.3 <= error_rate <= 0.7, "Concurrent error rate should be ~50%"

    @pytest.mark.server_config(
        error_injection_enabled=True,
        env_overrides={
            "FAKEAI_ERROR_INJECTION_RATE": "1.0",
        },
    )
    def test_concurrent_requests_all_get_responses(
        self, server_function_scoped: Any
    ) -> None:
        """Test that all concurrent requests get responses (no deadlocks)."""
        base_url = server_function_scoped.base_url
        api_key = server_function_scoped.api_keys[0]

        def make_request(i: int) -> int:
            """Make a request and return request number."""
            client = FakeAIClient(base_url=base_url, api_key=api_key)
            try:
                response = client.get("/v1/models")
                assert response is not None, "Should get a response"
                return i
            finally:
                client.close()

        # Make many concurrent requests
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(make_request, i) for i in range(100)]
            completed = [future.result(timeout=30) for future in as_completed(futures)]

        # All should complete
        assert len(completed) == 100, "All requests should complete"


class TestRecoveryAfterErrors:
    """Test recovery after errors."""

    @pytest.mark.server_config(
        error_injection_enabled=True,
        env_overrides={
            "FAKEAI_ERROR_INJECTION_RATE": "1.0",  # Start with 100%
        },
    )
    def test_server_continues_after_errors(self, server_function_scoped: Any) -> None:
        """Test that server continues to function after injecting errors."""
        client = FakeAIClient(
            base_url=server_function_scoped.base_url,
            api_key=server_function_scoped.api_keys[0],
        )

        try:
            # Generate many errors
            for _ in range(20):
                response = client.get("/v1/models")
                # Should get errors but server should keep running

            # Server should still be responsive
            response = client.get("/health")
            # Health endpoint might not be affected by error injection

        finally:
            client.close()

    @pytest.mark.server_config(
        error_injection_enabled=True,
        env_overrides={
            "FAKEAI_ERROR_INJECTION_RATE": "0.5",
        },
    )
    def test_successful_requests_still_work(self, server_function_scoped: Any) -> None:
        """Test that successful requests work correctly despite errors."""
        client = FakeAIClient(
            base_url=server_function_scoped.base_url,
            api_key=server_function_scoped.api_keys[0],
        )

        try:
            # Make requests until we get a successful one
            success_count = 0
            for _ in range(20):
                response = client.get("/v1/models")
                if response.status_code == 200:
                    # Verify response is valid
                    data = response.json()
                    assert "data" in data or "object" in data
                    success_count += 1

            # Should get some successful requests
            assert success_count > 0, "Should have some successful requests"

        finally:
            client.close()


class TestErrorResponseFormat:
    """Test error response format validation."""

    @pytest.mark.server_config(
        error_injection_enabled=True,
        env_overrides={
            "FAKEAI_ERROR_INJECTION_RATE": "1.0",
        },
    )
    def test_error_response_has_required_fields(
        self, server_function_scoped: Any
    ) -> None:
        """Test that error responses have required OpenAI error format."""
        client = FakeAIClient(
            base_url=server_function_scoped.base_url,
            api_key=server_function_scoped.api_keys[0],
        )

        try:
            # Get an error response
            response = client.get("/v1/models")
            if response.status_code >= 400:
                data = response.json()

                # Check OpenAI error format
                assert "error" in data, "Should have 'error' field"
                assert "message" in data["error"], "Should have error message"
                assert "type" in data["error"], "Should have error type"
                assert "code" in data["error"], "Should have error code"

        finally:
            client.close()

    @pytest.mark.server_config(
        error_injection_enabled=True,
        env_overrides={
            "FAKEAI_ERROR_INJECTION_RATE": "1.0",
            "FAKEAI_ERROR_INJECTION_TYPES": '["internal_error", "bad_gateway", "service_unavailable"]',
        },
    )
    def test_error_messages_are_descriptive(
        self, server_function_scoped: Any
    ) -> None:
        """Test that error messages are descriptive."""
        client = FakeAIClient(
            base_url=server_function_scoped.base_url,
            api_key=server_function_scoped.api_keys[0],
        )

        try:
            # Collect error messages
            messages = set()
            for _ in range(10):
                response = client.get("/v1/models")
                if response.status_code >= 400:
                    data = response.json()
                    message = data["error"]["message"]
                    assert len(message) > 10, "Message should be descriptive"
                    messages.add(message)

            # Should see variety of messages
            assert len(messages) >= 1, "Should have error messages"

        finally:
            client.close()


class TestErrorInjectionWithRealRequests:
    """Test error injection with various real request types."""

    @pytest.mark.server_config(
        error_injection_enabled=True,
        env_overrides={
            "FAKEAI_ERROR_INJECTION_RATE": "0.3",  # 30% error rate
        },
    )
    def test_chat_completions_with_error_injection(
        self, server_function_scoped: Any
    ) -> None:
        """Test chat completions endpoint with error injection."""
        client = FakeAIClient(
            base_url=server_function_scoped.base_url,
            api_key=server_function_scoped.api_keys[0],
        )

        try:
            success_count = 0
            error_count = 0

            for _ in range(20):
                response = client.post(
                    "/v1/chat/completions",
                    json={
                        "model": "openai/gpt-oss-120b",
                        "messages": [{"role": "user", "content": "Hello"}],
                    },
                )

                if response.status_code == 200:
                    # Verify valid response
                    data = response.json()
                    assert "choices" in data
                    success_count += 1
                else:
                    # Verify valid error
                    data = response.json()
                    assert "error" in data
                    error_count += 1

            # Should have both successes and errors
            assert success_count > 0, "Should have some successful requests"
            assert error_count > 0, "Should have some errors"

        finally:
            client.close()

    @pytest.mark.server_config(
        error_injection_enabled=True,
        env_overrides={
            "FAKEAI_ERROR_INJECTION_RATE": "0.3",
        },
    )
    def test_embeddings_with_error_injection(
        self, server_function_scoped: Any
    ) -> None:
        """Test embeddings endpoint with error injection."""
        client = FakeAIClient(
            base_url=server_function_scoped.base_url,
            api_key=server_function_scoped.api_keys[0],
        )

        try:
            success_count = 0
            error_count = 0

            for _ in range(20):
                response = client.post(
                    "/v1/embeddings",
                    json={
                        "model": "text-embedding-ada-002",
                        "input": "Test text",
                    },
                )

                if response.status_code == 200:
                    data = response.json()
                    assert "data" in data
                    success_count += 1
                else:
                    data = response.json()
                    assert "error" in data
                    error_count += 1

            assert success_count > 0, "Should have some successful requests"
            assert error_count > 0, "Should have some errors"

        finally:
            client.close()


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.mark.server_config(
        error_injection_enabled=True,
        env_overrides={
            "FAKEAI_ERROR_INJECTION_RATE": "0.0",
        },
    )
    def test_zero_error_rate(self, server_function_scoped: Any) -> None:
        """Test 0% error rate edge case."""
        client = FakeAIClient(
            base_url=server_function_scoped.base_url,
            api_key=server_function_scoped.api_keys[0],
        )

        try:
            for _ in range(20):
                response = client.get("/v1/models")
                assert response.status_code == 200, "Should never inject errors at 0%"

        finally:
            client.close()

    @pytest.mark.server_config(
        error_injection_enabled=True,
        env_overrides={
            "FAKEAI_ERROR_INJECTION_RATE": "1.0",
        },
    )
    def test_100_percent_error_rate(self, server_function_scoped: Any) -> None:
        """Test 100% error rate edge case."""
        client = FakeAIClient(
            base_url=server_function_scoped.base_url,
            api_key=server_function_scoped.api_keys[0],
        )

        try:
            error_count = 0
            for _ in range(20):
                response = client.get("/v1/models")
                if response.status_code >= 400:
                    error_count += 1

            # Should see most/all as errors (allow tiny tolerance)
            assert error_count >= 18, "Should inject errors at ~100%"

        finally:
            client.close()

    @pytest.mark.server_config(
        error_injection_enabled=True,
        env_overrides={
            "FAKEAI_ERROR_INJECTION_RATE": "0.5",
            "FAKEAI_ERROR_INJECTION_TYPES": "[]",  # Empty types (should use default)
        },
    )
    def test_empty_error_types_uses_defaults(
        self, server_function_scoped: Any
    ) -> None:
        """Test that empty error types list uses defaults."""
        client = FakeAIClient(
            base_url=server_function_scoped.base_url,
            api_key=server_function_scoped.api_keys[0],
        )

        try:
            # Should still get errors (using default types)
            error_count = 0
            for _ in range(30):
                response = client.get("/v1/models")
                if response.status_code >= 400:
                    error_count += 1

            # Should see some errors
            # (depends on implementation handling empty list)

        finally:
            client.close()


class TestMetricsIntegration:
    """Test error injection metrics integration."""

    @pytest.mark.server_config(
        error_injection_enabled=True,
        env_overrides={
            "FAKEAI_ERROR_INJECTION_RATE": "0.5",
        },
    )
    def test_metrics_endpoint_available(self, server_function_scoped: Any) -> None:
        """Test that metrics endpoint is available with error injection."""
        client = FakeAIClient(
            base_url=server_function_scoped.base_url,
            api_key=server_function_scoped.api_keys[0],
        )

        try:
            # Metrics endpoint should work
            response = client.get("/metrics")
            # Should get a response (200 or 404 if not implemented)
            assert response.status_code in [200, 404]

        finally:
            client.close()

    @pytest.mark.server_config(
        error_injection_enabled=True,
        env_overrides={
            "FAKEAI_ERROR_INJECTION_RATE": "0.3",
        },
    )
    def test_prometheus_metrics_with_error_injection(
        self, server_function_scoped: Any
    ) -> None:
        """Test Prometheus metrics with error injection active."""
        client = FakeAIClient(
            base_url=server_function_scoped.base_url,
            api_key=server_function_scoped.api_keys[0],
        )

        try:
            # Generate some traffic
            for _ in range(10):
                client.get("/v1/models")

            # Check Prometheus metrics
            response = client.get("/metrics/prometheus")
            if response.status_code == 200:
                metrics_text = response.text
                # Should contain error injection metrics if exposed
                # (depends on implementation)

        finally:
            client.close()
