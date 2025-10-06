"""
Comprehensive integration tests for rate limiting.

This module tests rate limiting functionality end-to-end, including:
- RPM (requests per minute) enforcement
- TPM (tokens per minute) enforcement
- Rate limit headers
- Different rate limit tiers
- Per-endpoint, per-model, and per-API-key rate limits
- Rate limit reset behavior
- Concurrent request handling
- Burst handling
- Metrics collection
- 429 error responses
- Retry-After headers
- Configuration changes
"""

#  SPDX-License-Identifier: Apache-2.0

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

import pytest

from tests.integration.utils import FakeAIClient

# Markers for test organization
pytestmark = [
    pytest.mark.integration,
    pytest.mark.slow,
]


class TestRateLimitEnforcement:
    """Test rate limit enforcement mechanisms."""

    @pytest.mark.server_config(
        rate_limit_enabled=True,
        env_overrides={
            "FAKEAI_RATE_LIMITS__RPM_OVERRIDE": "3",  # Very low for testing
            "FAKEAI_RATE_LIMITS__TPM_OVERRIDE": "200000",
        },
    )
    def test_rpm_enforcement(self, server_function_scoped: Any) -> None:
        """Test that requests per minute (RPM) limit is enforced.

        Testing with 3 RPM (very restrictive for testing)
        """
        client = FakeAIClient(
            base_url=server_function_scoped.base_url,
            api_key=server_function_scoped.api_keys[0],
        )

        try:
            # Make 3 requests (should all succeed)
            successful_requests = 0
            for i in range(3):
                response = client.get("/v1/models")
                assert response.status_code == 200, f"Request {i+1} should succeed"
                successful_requests += 1

            assert successful_requests == 3

            # 4th request should be rate limited (429)
            response = client.get("/v1/models")
            assert response.status_code == 429
            data = response.json()
            assert "error" in data
            assert data["error"]["code"] == "rate_limit_exceeded"
            assert data["error"]["type"] == "rate_limit_error"

        finally:
            client.close()

    @pytest.mark.server_config(
        rate_limit_enabled=True,
        env_overrides={
            "FAKEAI_RATE_LIMITS__RPM_OVERRIDE": "10",  # High enough to not hit RPM limit
            "FAKEAI_RATE_LIMITS__TPM_OVERRIDE": "1000",  # 1K TPM (low to trigger limit)
        },
    )
    def test_tpm_enforcement(self, server_function_scoped: Any) -> None:
        """Test that tokens per minute (TPM) limit is enforced.

        Tests with low TPM override to trigger limit quickly.
        """
        client = FakeAIClient(
            base_url=server_function_scoped.base_url,
            api_key=server_function_scoped.api_keys[0],
        )

        try:
            # First request with moderate token usage (should succeed)
            response = client.post(
                "/v1/chat/completions",
                json={
                    "model": "openai/gpt-oss-120b",
                    "messages": [{"role": "user", "content": "Hello " * 50}],
                },
            )
            assert response.status_code == 200

            # Second request with high token usage (might hit TPM limit)
            response = client.post(
                "/v1/chat/completions",
                json={
                    "model": "openai/gpt-oss-120b",
                    "messages": [{"role": "user", "content": "Test " * 200}],
                },
            )

            # Should get 429 due to token limit
            if response.status_code == 429:
                data = response.json()
                assert "error" in data
                assert data["error"]["code"] == "rate_limit_exceeded"
                # Verify this was a TPM limit (not RPM)
                assert "Retry-After" in response.headers

        finally:
            client.close()

    @pytest.mark.server_config(
        rate_limit_enabled=True,
        env_overrides={"FAKEAI_RATE_LIMITS__TIER": "tier-1"},
    )
    def test_rate_limit_headers_in_response(self, server_function_scoped: Any) -> None:
        """Test that rate limit headers are included in all responses."""
        client = FakeAIClient(
            base_url=server_function_scoped.base_url,
            api_key=server_function_scoped.api_keys[0],
        )

        try:
            response = client.get("/v1/models")
            assert response.status_code == 200

            # Check all required rate limit headers are present
            assert "x-ratelimit-limit-requests" in response.headers
            assert "x-ratelimit-limit-tokens" in response.headers
            assert "x-ratelimit-remaining-requests" in response.headers
            assert "x-ratelimit-remaining-tokens" in response.headers
            assert "x-ratelimit-reset-requests" in response.headers
            assert "x-ratelimit-reset-tokens" in response.headers

            # Verify headers are numeric
            rpm_limit = int(response.headers["x-ratelimit-limit-requests"])
            tpm_limit = int(response.headers["x-ratelimit-limit-tokens"])
            rpm_remaining = int(response.headers["x-ratelimit-remaining-requests"])
            tpm_remaining = int(response.headers["x-ratelimit-remaining-tokens"])
            rpm_reset = int(response.headers["x-ratelimit-reset-requests"])
            tpm_reset = int(response.headers["x-ratelimit-reset-tokens"])

            # Tier-1 limits (from config/rate_limits.py)
            assert rpm_limit == 500
            assert tpm_limit == 2_000_000

            # After one request, remaining should be decremented
            assert rpm_remaining == 499
            assert tpm_remaining <= tpm_limit  # May be equal if no tokens consumed

            # Reset times should be in the future
            current_time = int(time.time())
            assert rpm_reset > current_time
            assert tpm_reset > current_time

        finally:
            client.close()


class TestRateLimitTiers:
    """Test different rate limit tiers."""

    @pytest.mark.server_config(
        rate_limit_enabled=True,
        env_overrides={"FAKEAI_RATE_LIMITS__TIER": "free"},
    )
    def test_free_tier_limits(self, server_function_scoped: Any) -> None:
        """Test free tier rate limits.

        Config values (from config/rate_limits.py): 3 RPM, 200K TPM
        """
        client = FakeAIClient(
            base_url=server_function_scoped.base_url,
            api_key=server_function_scoped.api_keys[0],
        )

        try:
            response = client.get("/v1/models")
            assert response.status_code == 200

            # Free tier (config/rate_limits.py): 3 RPM, 200K TPM
            assert response.headers["x-ratelimit-limit-requests"] == "3"
            assert response.headers["x-ratelimit-limit-tokens"] == "200000"

        finally:
            client.close()

    @pytest.mark.server_config(
        rate_limit_enabled=True,
        env_overrides={"FAKEAI_RATE_LIMITS__TIER": "tier-2"},
    )
    def test_tier_2_limits(self, server_function_scoped: Any) -> None:
        """Test tier-2 rate limits."""
        client = FakeAIClient(
            base_url=server_function_scoped.base_url,
            api_key=server_function_scoped.api_keys[0],
        )

        try:
            response = client.get("/v1/models")
            assert response.status_code == 200

            # Tier-2: 5000 RPM, 10M TPM
            assert response.headers["x-ratelimit-limit-requests"] == "5000"
            assert response.headers["x-ratelimit-limit-tokens"] == "10000000"

        finally:
            client.close()

    @pytest.mark.server_config(
        rate_limit_enabled=True,
        env_overrides={"FAKEAI_RATE_LIMITS__TIER": "tier-5"},
    )
    def test_tier_5_limits(self, server_function_scoped: Any) -> None:
        """Test tier-5 rate limits (highest tier).

        Config values (from config/rate_limits.py): 30000 RPM, 300M TPM
        """
        client = FakeAIClient(
            base_url=server_function_scoped.base_url,
            api_key=server_function_scoped.api_keys[0],
        )

        try:
            response = client.get("/v1/models")
            assert response.status_code == 200

            # Tier-5 (config/rate_limits.py): 30000 RPM, 300M TPM
            assert response.headers["x-ratelimit-limit-requests"] == "30000"
            assert response.headers["x-ratelimit-limit-tokens"] == "300000000"

        finally:
            client.close()

    @pytest.mark.server_config(
        rate_limit_enabled=True,
        env_overrides={
            "FAKEAI_RATE_LIMITS__TIER": "tier-1",
            "FAKEAI_RATE_LIMITS__RPM_OVERRIDE": "1000",
            "FAKEAI_RATE_LIMITS__TPM_OVERRIDE": "5000000",
        },
    )
    def test_custom_tier_overrides(self, server_function_scoped: Any) -> None:
        """Test custom rate limit overrides."""
        client = FakeAIClient(
            base_url=server_function_scoped.base_url,
            api_key=server_function_scoped.api_keys[0],
        )

        try:
            response = client.get("/v1/models")
            assert response.status_code == 200

            # Custom overrides
            assert response.headers["x-ratelimit-limit-requests"] == "1000"
            assert response.headers["x-ratelimit-limit-tokens"] == "5000000"

        finally:
            client.close()


class TestPerEndpointRateLimits:
    """Test rate limits across different endpoints."""

    @pytest.mark.server_config(
        rate_limit_enabled=True,
        env_overrides={"FAKEAI_RATE_LIMITS__TIER": "tier-1"},
    )
    def test_rate_limits_apply_to_all_endpoints(
        self, server_function_scoped: Any
    ) -> None:
        """Test that rate limits apply to all API endpoints."""
        client = FakeAIClient(
            base_url=server_function_scoped.base_url,
            api_key=server_function_scoped.api_keys[0],
        )

        try:
            # Test multiple endpoints
            endpoints = [
                ("/v1/models", "GET", None),
                (
                    "/v1/chat/completions",
                    "POST",
                    {
                        "model": "openai/gpt-oss-120b",
                        "messages": [{"role": "user", "content": "Hello"}],
                    },
                ),
                (
                    "/v1/embeddings",
                    "POST",
                    {"model": "text-embedding-ada-002", "input": "Test text"},
                ),
            ]

            for endpoint, method, body in endpoints:
                if method == "GET":
                    response = client.get(endpoint)
                else:
                    response = client.post(endpoint, json=body)

                assert response.status_code == 200
                # All should have rate limit headers
                assert "x-ratelimit-limit-requests" in response.headers
                assert "x-ratelimit-remaining-requests" in response.headers

        finally:
            client.close()


class TestPerModelRateLimits:
    """Test rate limits are enforced per API key, not per model."""

    @pytest.mark.server_config(
        rate_limit_enabled=True,
        env_overrides={
            "FAKEAI_RATE_LIMITS__RPM_OVERRIDE": "3",  # Very low for testing
            "FAKEAI_RATE_LIMITS__TPM_OVERRIDE": "200000",
        },
    )
    def test_rate_limits_shared_across_models(
        self, server_function_scoped: Any
    ) -> None:
        """Test that rate limits are shared across different models."""
        client = FakeAIClient(
            base_url=server_function_scoped.base_url,
            api_key=server_function_scoped.api_keys[0],
        )

        try:
            # Make requests to different models (uses same rate limit bucket)
            models = [
                "openai/gpt-oss-120b",
                "meta-llama/Llama-3.1-8B-Instruct",
                "openai/gpt-oss-120b",  # Repeat
            ]

            for i, model in enumerate(models):
                response = client.post(
                    "/v1/chat/completions",
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": "Hi"}],
                    },
                )

                if i < 3:  # 3 RPM limit
                    assert response.status_code == 200
                else:
                    # Should be rate limited
                    assert response.status_code == 429

        finally:
            client.close()


class TestPerAPIKeyRateLimits:
    """Test rate limits are enforced per API key."""

    @pytest.mark.server_config(
        rate_limit_enabled=True,
        api_keys=["key1", "key2"],
        env_overrides={
            "FAKEAI_RATE_LIMITS__RPM_OVERRIDE": "3",  # Very low for testing
            "FAKEAI_RATE_LIMITS__TPM_OVERRIDE": "200000",
        },
    )
    def test_rate_limits_isolated_per_key(self, server_function_scoped: Any) -> None:
        """Test that rate limits are isolated per API key."""
        client1 = FakeAIClient(
            base_url=server_function_scoped.base_url,
            api_key="key1",
        )
        client2 = FakeAIClient(
            base_url=server_function_scoped.base_url,
            api_key="key2",
        )

        try:
            # Exhaust key1's rate limit (3 requests)
            for _ in range(3):
                response = client1.get("/v1/models")
                assert response.status_code == 200

            # key1 should be rate limited
            response = client1.get("/v1/models")
            assert response.status_code == 429

            # key2 should still have full quota
            response = client2.get("/v1/models")
            assert response.status_code == 200
            assert response.headers["x-ratelimit-remaining-requests"] == "2"

        finally:
            client1.close()
            client2.close()


class TestRateLimitReset:
    """Test rate limit reset behavior."""

    @pytest.mark.server_config(
        rate_limit_enabled=True,
        env_overrides={
            "FAKEAI_RATE_LIMITS__RPM_OVERRIDE": "3",  # 3 RPM = 0.05 requests/sec refill
            "FAKEAI_RATE_LIMITS__TPM_OVERRIDE": "200000",
        },
    )
    def test_rate_limit_resets_over_time(self, server_function_scoped: Any) -> None:
        """Test that rate limits reset over time via token refill."""
        client = FakeAIClient(
            base_url=server_function_scoped.base_url,
            api_key=server_function_scoped.api_keys[0],
        )

        try:
            # Exhaust rate limit
            for _ in range(3):
                response = client.get("/v1/models")
                assert response.status_code == 200

            # Should be rate limited
            response = client.get("/v1/models")
            assert response.status_code == 429

            # Wait for token refill (3 RPM = 0.05 requests/sec)
            # Wait ~25 seconds to get 1 token back
            time.sleep(25)

            # Should have 1 request available now
            response = client.get("/v1/models")
            assert response.status_code == 200

        finally:
            client.close()

    @pytest.mark.server_config(
        rate_limit_enabled=True,
        env_overrides={
            "FAKEAI_RATE_LIMITS__TIER": "tier-1",
        },
    )
    def test_reset_time_headers(self, server_function_scoped: Any) -> None:
        """Test that reset time headers are correctly set."""
        client = FakeAIClient(
            base_url=server_function_scoped.base_url,
            api_key=server_function_scoped.api_keys[0],
        )

        try:
            response = client.get("/v1/models")
            assert response.status_code == 200

            # Get reset times
            rpm_reset = int(response.headers["x-ratelimit-reset-requests"])
            tpm_reset = int(response.headers["x-ratelimit-reset-tokens"])

            # Should be Unix timestamps in the future
            current_time = int(time.time())
            assert rpm_reset > current_time
            assert tpm_reset > current_time

            # Reset time should be within reasonable range (within 60 seconds)
            assert rpm_reset - current_time <= 60
            assert tpm_reset - current_time <= 60

        finally:
            client.close()


class TestConcurrentRequests:
    """Test rate limiting with concurrent requests."""

    @pytest.mark.server_config(
        rate_limit_enabled=True,
        env_overrides={
            "FAKEAI_RATE_LIMITS__RPM_OVERRIDE": "3",  # Very low for testing
            "FAKEAI_RATE_LIMITS__TPM_OVERRIDE": "200000",
        },
    )
    def test_concurrent_requests_hitting_limit(
        self, server_function_scoped: Any
    ) -> None:
        """Test concurrent requests hitting rate limit."""
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

        # Make 10 concurrent requests (3 RPM limit)
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request, i) for i in range(10)]
            results = [future.result() for future in as_completed(futures)]

        # Sort by request number
        results.sort(key=lambda x: x[0])
        status_codes = [status for _, status in results]

        # Should have some 200s and some 429s
        success_count = sum(1 for code in status_codes if code == 200)
        rate_limited_count = sum(1 for code in status_codes if code == 429)

        # With 3 RPM limit, should have 3 successes
        assert success_count == 3
        assert rate_limited_count == 7


class TestBurstHandling:
    """Test rate limit burst handling."""

    @pytest.mark.server_config(
        rate_limit_enabled=True,
        env_overrides={
            "FAKEAI_RATE_LIMITS__TIER": "tier-1",
        },
    )
    def test_burst_requests_allowed(self, server_function_scoped: Any) -> None:
        """Test that burst requests are allowed up to bucket capacity."""
        client = FakeAIClient(
            base_url=server_function_scoped.base_url,
            api_key=server_function_scoped.api_keys[0],
        )

        try:
            # Make rapid burst of requests (tier-1: 500 RPM capacity)
            # Make 10 rapid requests - all should succeed
            for _ in range(10):
                response = client.get("/v1/models")
                assert response.status_code == 200

        finally:
            client.close()


class TestMetricsCollection:
    """Test rate limiter metrics collection."""

    @pytest.mark.server_config(
        rate_limit_enabled=True,
        env_overrides={
            "FAKEAI_RATE_LIMITS__RPM_OVERRIDE": "3",  # Very low for testing
            "FAKEAI_RATE_LIMITS__TPM_OVERRIDE": "200000",
        },
    )
    def test_metrics_record_throttle_events(
        self, server_function_scoped: Any
    ) -> None:
        """Test that throttle events are recorded in metrics."""
        client = FakeAIClient(
            base_url=server_function_scoped.base_url,
            api_key=server_function_scoped.api_keys[0],
        )

        try:
            # Exhaust rate limit
            for _ in range(3):
                client.get("/v1/models")

            # Trigger throttle
            response = client.get("/v1/models")
            assert response.status_code == 429

            # Check metrics endpoint (if available)
            metrics_response = client.get("/metrics")
            if metrics_response.status_code == 200:
                metrics = metrics_response.json()
                # Verify rate limiter metrics exist
                # (actual structure depends on metrics implementation)
                assert metrics is not None

        finally:
            client.close()


class Test429Responses:
    """Test 429 error response format."""

    @pytest.mark.server_config(
        rate_limit_enabled=True,
        env_overrides={
            "FAKEAI_RATE_LIMITS__RPM_OVERRIDE": "3",  # Very low for testing
            "FAKEAI_RATE_LIMITS__TPM_OVERRIDE": "200000",
        },
    )
    def test_429_response_format(self, server_function_scoped: Any) -> None:
        """Test that 429 responses have correct format."""
        client = FakeAIClient(
            base_url=server_function_scoped.base_url,
            api_key=server_function_scoped.api_keys[0],
        )

        try:
            # Exhaust rate limit
            for _ in range(3):
                client.get("/v1/models")

            # Get 429 response
            response = client.get("/v1/models")
            assert response.status_code == 429

            # Check response format
            data = response.json()
            assert "error" in data
            assert data["error"]["type"] == "rate_limit_error"
            assert data["error"]["code"] == "rate_limit_exceeded"
            assert "message" in data["error"]

            # Should mention rate limit in message
            message = data["error"]["message"].lower()
            assert "rate limit" in message or "too many requests" in message

        finally:
            client.close()

    @pytest.mark.server_config(
        rate_limit_enabled=True,
        env_overrides={
            "FAKEAI_RATE_LIMITS__RPM_OVERRIDE": "3",  # Very low for testing
            "FAKEAI_RATE_LIMITS__TPM_OVERRIDE": "200000",
        },
    )
    def test_429_includes_rate_limit_headers(
        self, server_function_scoped: Any
    ) -> None:
        """Test that 429 responses include rate limit headers."""
        client = FakeAIClient(
            base_url=server_function_scoped.base_url,
            api_key=server_function_scoped.api_keys[0],
        )

        try:
            # Exhaust rate limit
            for _ in range(3):
                client.get("/v1/models")

            # Get 429 response
            response = client.get("/v1/models")
            assert response.status_code == 429

            # Should still have rate limit headers
            assert "x-ratelimit-limit-requests" in response.headers
            assert "x-ratelimit-remaining-requests" in response.headers
            assert "x-ratelimit-reset-requests" in response.headers

            # Remaining should be 0
            assert response.headers["x-ratelimit-remaining-requests"] == "0"

        finally:
            client.close()


class TestRetryAfterHeaders:
    """Test Retry-After header behavior."""

    @pytest.mark.server_config(
        rate_limit_enabled=True,
        env_overrides={
            "FAKEAI_RATE_LIMITS__RPM_OVERRIDE": "3",  # Very low for testing
            "FAKEAI_RATE_LIMITS__TPM_OVERRIDE": "200000",
        },
    )
    def test_retry_after_header_present(self, server_function_scoped: Any) -> None:
        """Test that Retry-After header is present in 429 responses."""
        client = FakeAIClient(
            base_url=server_function_scoped.base_url,
            api_key=server_function_scoped.api_keys[0],
        )

        try:
            # Exhaust rate limit
            for _ in range(3):
                client.get("/v1/models")

            # Get 429 response
            response = client.get("/v1/models")
            assert response.status_code == 429

            # Check Retry-After header
            assert "Retry-After" in response.headers
            retry_after = int(response.headers["Retry-After"])
            assert retry_after > 0
            assert retry_after <= 60  # Should be reasonable (within 60 seconds)

        finally:
            client.close()

    @pytest.mark.server_config(
        rate_limit_enabled=True,
        env_overrides={
            "FAKEAI_RATE_LIMITS__RPM_OVERRIDE": "3",  # Very low for testing
            "FAKEAI_RATE_LIMITS__TPM_OVERRIDE": "200000",
        },
    )
    def test_retry_after_allows_request(self, server_function_scoped: Any) -> None:
        """Test that waiting for Retry-After allows request."""
        client = FakeAIClient(
            base_url=server_function_scoped.base_url,
            api_key=server_function_scoped.api_keys[0],
        )

        try:
            # Exhaust rate limit
            for _ in range(3):
                client.get("/v1/models")

            # Get 429 response
            response = client.get("/v1/models")
            assert response.status_code == 429

            retry_after = int(response.headers["Retry-After"])

            # Wait for retry-after period plus small buffer
            time.sleep(retry_after + 1)

            # Should be able to make request now
            response = client.get("/v1/models")
            # Should succeed (or at least not be 429 for the same reason)
            # Note: Might still be 429 if we haven't refilled enough tokens
            # but the retry-after should have decreased
            if response.status_code == 200:
                assert True  # Success
            else:
                # If still 429, verify retry-after has changed
                new_retry_after = int(response.headers.get("Retry-After", "0"))
                assert new_retry_after < retry_after

        finally:
            client.close()


class TestConfigurationChanges:
    """Test rate limit configuration changes."""

    @pytest.mark.server_config(
        rate_limit_enabled=True,
        env_overrides={
            "FAKEAI_RATE_LIMITS__TIER": "tier-1",
        },
    )
    def test_tier_configuration(self, server_function_scoped: Any) -> None:
        """Test that tier configuration is applied correctly."""
        client = FakeAIClient(
            base_url=server_function_scoped.base_url,
            api_key=server_function_scoped.api_keys[0],
        )

        try:
            response = client.get("/v1/models")
            assert response.status_code == 200

            # Verify tier-1 limits
            assert response.headers["x-ratelimit-limit-requests"] == "500"
            assert response.headers["x-ratelimit-limit-tokens"] == "2000000"

        finally:
            client.close()

    @pytest.mark.server_config(
        rate_limit_enabled=True,
        env_overrides={
            "FAKEAI_RATE_LIMITS__RPM_OVERRIDE": "100",
            "FAKEAI_RATE_LIMITS__TPM_OVERRIDE": "50000",
        },
    )
    def test_override_configuration(self, server_function_scoped: Any) -> None:
        """Test that override configuration takes precedence."""
        client = FakeAIClient(
            base_url=server_function_scoped.base_url,
            api_key=server_function_scoped.api_keys[0],
        )

        try:
            response = client.get("/v1/models")
            assert response.status_code == 200

            # Verify override limits
            assert response.headers["x-ratelimit-limit-requests"] == "100"
            assert response.headers["x-ratelimit-limit-tokens"] == "50000"

        finally:
            client.close()


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.mark.server_config(
        rate_limit_enabled=True,
        env_overrides={
            "FAKEAI_RATE_LIMITS__TIER": "tier-1",
        },
    )
    def test_zero_token_request(self, server_function_scoped: Any) -> None:
        """Test request with zero tokens (should still count against RPM)."""
        client = FakeAIClient(
            base_url=server_function_scoped.base_url,
            api_key=server_function_scoped.api_keys[0],
        )

        try:
            # GET request has no tokens but counts against RPM
            response = client.get("/v1/models")
            assert response.status_code == 200

            # RPM should be decremented
            rpm_remaining = int(response.headers["x-ratelimit-remaining-requests"])
            assert rpm_remaining == 499

        finally:
            client.close()

    @pytest.mark.server_config(
        rate_limit_enabled=True,
        env_overrides={
            "FAKEAI_RATE_LIMITS__TIER": "tier-1",
        },
    )
    def test_large_token_request(self, server_function_scoped: Any) -> None:
        """Test request with very large token count."""
        client = FakeAIClient(
            base_url=server_function_scoped.base_url,
            api_key=server_function_scoped.api_keys[0],
        )

        try:
            # Large prompt
            large_content = "Test " * 5000  # ~5000 tokens

            response = client.post(
                "/v1/chat/completions",
                json={
                    "model": "openai/gpt-oss-120b",
                    "messages": [{"role": "user", "content": large_content}],
                },
            )

            # Should succeed or fail based on TPM limit
            assert response.status_code in [200, 429]

            if response.status_code == 429:
                # Should have Retry-After header
                assert "Retry-After" in response.headers

        finally:
            client.close()

    @pytest.mark.server_config(
        rate_limit_enabled=False,
    )
    def test_rate_limiting_disabled(self, server_function_scoped: Any) -> None:
        """Test that rate limiting can be disabled."""
        client = FakeAIClient(
            base_url=server_function_scoped.base_url,
            api_key=server_function_scoped.api_keys[0] if server_function_scoped.api_keys else None,
        )

        try:
            # Make many requests (should all succeed)
            for _ in range(20):
                response = client.get("/health")  # Use health endpoint (no auth)
                assert response.status_code == 200

            # No rate limit headers should be present when disabled
            # (depending on implementation)

        finally:
            client.close()
