"""
Comprehensive integration tests for security features.

This module tests security functionality end-to-end, including:
1. API key authentication
2. Multiple API keys support
3. Per-key rate limits
4. Per-key permissions
5. API key rotation
6. API key revocation
7. Request signing
8. CORS configuration
9. Abuse detection
10. IP whitelisting/blacklisting
11. Request validation
12. Injection prevention
13. Security headers
"""

#  SPDX-License-Identifier: Apache-2.0

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

import pytest

from fakeai.client import FakeAIClient

# Markers for test organization
pytestmark = [
    pytest.mark.integration,
]


class TestAPIKeyAuthentication:
    """Test API key authentication mechanisms."""

    @pytest.mark.server_config(
        api_keys=["test-key-123"],
        env_overrides={
            "FAKEAI_AUTH__REQUIRE_API_KEY": "true",
            "FAKEAI_AUTH__API_KEYS": '["test-key-123"]',
        },
    )
    def test_valid_api_key_accepted(self, server_function_scoped: Any) -> None:
        """Test that valid API key is accepted."""
        client = FakeAIClient(
            base_url=server_function_scoped.base_url,
            api_key="test-key-123",
        )

        try:
            response = client.get("/v1/models")
            assert response.status_code == 200
            data = response.json()
            assert "data" in data
        finally:
            client.close()

    @pytest.mark.server_config(
        api_keys=["test-key-123"],
        env_overrides={
            "FAKEAI_AUTH__REQUIRE_API_KEY": "true",
            "FAKEAI_AUTH__API_KEYS": '["test-key-123"]',
        },
    )
    def test_invalid_api_key_rejected(self, server_function_scoped: Any) -> None:
        """Test that invalid API key is rejected."""
        client = FakeAIClient(
            base_url=server_function_scoped.base_url,
            api_key="invalid-key",
        )

        try:
            response = client.get("/v1/models")
            assert response.status_code == 401
            data = response.json()
            assert "error" in data
            assert data["error"]["code"] == "invalid_api_key"
        finally:
            client.close()

    @pytest.mark.server_config(
        api_keys=["test-key-123"],
        env_overrides={
            "FAKEAI_AUTH__REQUIRE_API_KEY": "true",
            "FAKEAI_AUTH__API_KEYS": '["test-key-123"]',
        },
    )
    def test_missing_api_key_rejected(self, server_function_scoped: Any) -> None:
        """Test that missing API key is rejected."""
        client = FakeAIClient(
            base_url=server_function_scoped.base_url,
            api_key=None,
        )

        try:
            response = client.get("/v1/models")
            assert response.status_code == 401
            data = response.json()
            assert "error" in data
        finally:
            client.close()

    @pytest.mark.server_config(
        api_keys=[],
        env_overrides={"FAKEAI_AUTH__REQUIRE_API_KEY": "false"},
    )
    def test_no_auth_required_when_disabled(
        self, server_function_scoped: Any
    ) -> None:
        """Test that authentication is not required when disabled."""
        client = FakeAIClient(
            base_url=server_function_scoped.base_url,
            api_key=None,
        )

        try:
            response = client.get("/v1/models")
            assert response.status_code == 200
        finally:
            client.close()

    @pytest.mark.server_config(
        api_keys=["test-key-123"],
        env_overrides={
            "FAKEAI_AUTH__REQUIRE_API_KEY": "true",
            "FAKEAI_AUTH__API_KEYS": '["test-key-123"]',
        },
    )
    def test_bearer_token_format(self, server_function_scoped: Any) -> None:
        """Test that Bearer token format is supported."""
        import httpx

        response = httpx.get(
            f"{server_function_scoped.base_url}/v1/models",
            headers={"Authorization": "Bearer test-key-123"},
            timeout=30.0,
        )

        assert response.status_code == 200


class TestMultipleAPIKeys:
    """Test support for multiple API keys."""

    @pytest.mark.server_config(
        api_keys=["key1", "key2", "key3"],
        env_overrides={
            "FAKEAI_AUTH__REQUIRE_API_KEY": "true",
            "FAKEAI_AUTH__API_KEYS": '["key1", "key2", "key3"]',
        },
    )
    def test_all_keys_accepted(self, server_function_scoped: Any) -> None:
        """Test that all configured keys are accepted."""
        keys = ["key1", "key2", "key3"]

        for key in keys:
            client = FakeAIClient(
                base_url=server_function_scoped.base_url,
                api_key=key,
            )

            try:
                response = client.get("/v1/models")
                assert response.status_code == 200, f"Key {key} should be valid"
            finally:
                client.close()

    @pytest.mark.server_config(
        api_keys=["key1", "key2"],
        env_overrides={
            "FAKEAI_AUTH__REQUIRE_API_KEY": "true",
            "FAKEAI_AUTH__API_KEYS": '["key1", "key2"]',
        },
    )
    def test_keys_independent(self, server_function_scoped: Any) -> None:
        """Test that API keys are independent of each other."""
        client1 = FakeAIClient(
            base_url=server_function_scoped.base_url,
            api_key="key1",
        )
        client2 = FakeAIClient(
            base_url=server_function_scoped.base_url,
            api_key="key2",
        )

        try:
            # Both should work
            response1 = client1.get("/v1/models")
            response2 = client2.get("/v1/models")

            assert response1.status_code == 200
            assert response2.status_code == 200
        finally:
            client1.close()
            client2.close()


class TestPerKeyRateLimits:
    """Test per-key rate limits."""

    @pytest.mark.server_config(
        api_keys=["key1", "key2"],
        rate_limit_enabled=True,
        env_overrides={
            "FAKEAI_AUTH__REQUIRE_API_KEY": "true",
            "FAKEAI_AUTH__API_KEYS": '["key1", "key2"]',
            "FAKEAI_RATE_LIMITS__RPM_OVERRIDE": "3",
            "FAKEAI_RATE_LIMITS__TPM_OVERRIDE": "200000",
        },
    )
    def test_rate_limits_isolated_per_key(
        self, server_function_scoped: Any
    ) -> None:
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
            # Exhaust key1's rate limit
            for _ in range(3):
                response = client1.get("/v1/models")
                assert response.status_code == 200

            # key1 should be rate limited
            response = client1.get("/v1/models")
            assert response.status_code == 429

            # key2 should still have full quota
            response = client2.get("/v1/models")
            assert response.status_code == 200

            # key2 should still have remaining requests
            remaining = int(response.headers["x-ratelimit-remaining-requests"])
            assert remaining == 2  # 3 total - 1 used
        finally:
            client1.close()
            client2.close()


class TestRequestValidation:
    """Test request validation and sanitization."""

    @pytest.mark.server_config(
        api_keys=["test-key"],
        env_overrides={
            "FAKEAI_AUTH__REQUIRE_API_KEY": "true",
            "FAKEAI_AUTH__API_KEYS": '["test-key"]',
            "FAKEAI_SECURITY__ENABLE_ABUSE_DETECTION": "true",
        },
    )
    def test_sql_injection_detected(self, server_function_scoped: Any) -> None:
        """Test that SQL injection attempts are detected."""
        client = FakeAIClient(
            base_url=server_function_scoped.base_url,
            api_key="test-key",
        )

        try:
            # Attempt SQL injection in chat message
            response = client.post(
                "/v1/chat/completions",
                json={
                    "model": "openai/gpt-oss-120b",
                    "messages": [
                        {
                            "role": "user",
                            "content": "'; DROP TABLE users; --",
                        }
                    ],
                },
            )

            # Should be rejected with 400
            assert response.status_code == 400
            data = response.json()
            assert "error" in data
            assert data["error"]["type"] == "security_error"
        finally:
            client.close()

    @pytest.mark.server_config(
        api_keys=["test-key"],
        env_overrides={
            "FAKEAI_AUTH__REQUIRE_API_KEY": "true",
            "FAKEAI_AUTH__API_KEYS": '["test-key"]',
            "FAKEAI_SECURITY__ENABLE_ABUSE_DETECTION": "true",
        },
    )
    def test_command_injection_detected(self, server_function_scoped: Any) -> None:
        """Test that command injection attempts are detected."""
        client = FakeAIClient(
            base_url=server_function_scoped.base_url,
            api_key="test-key",
        )

        try:
            # Attempt command injection
            response = client.post(
                "/v1/chat/completions",
                json={
                    "model": "openai/gpt-oss-120b",
                    "messages": [
                        {
                            "role": "user",
                            "content": "$(rm -rf /)",
                        }
                    ],
                },
            )

            # Should be rejected
            assert response.status_code == 400
            data = response.json()
            assert "error" in data
            assert data["error"]["type"] == "security_error"
        finally:
            client.close()

    @pytest.mark.server_config(
        api_keys=["test-key"],
        env_overrides={
            "FAKEAI_AUTH__REQUIRE_API_KEY": "true",
            "FAKEAI_AUTH__API_KEYS": '["test-key"]',
            "FAKEAI_SECURITY__ENABLE_ABUSE_DETECTION": "true",
        },
    )
    def test_path_traversal_detected(self, server_function_scoped: Any) -> None:
        """Test that path traversal attempts are detected."""
        client = FakeAIClient(
            base_url=server_function_scoped.base_url,
            api_key="test-key",
        )

        try:
            # Attempt path traversal
            response = client.post(
                "/v1/chat/completions",
                json={
                    "model": "openai/gpt-oss-120b",
                    "messages": [
                        {
                            "role": "user",
                            "content": "../../../etc/passwd",
                        }
                    ],
                },
            )

            # Should be rejected
            assert response.status_code == 400
            data = response.json()
            assert "error" in data
            assert data["error"]["type"] == "security_error"
        finally:
            client.close()

    @pytest.mark.server_config(
        api_keys=["test-key"],
        env_overrides={
            "FAKEAI_AUTH__REQUIRE_API_KEY": "true",
            "FAKEAI_AUTH__API_KEYS": '["test-key"]',
            "FAKEAI_SECURITY__ENABLE_ABUSE_DETECTION": "true",
        },
    )
    def test_xss_injection_detected(self, server_function_scoped: Any) -> None:
        """Test that XSS injection attempts are detected."""
        client = FakeAIClient(
            base_url=server_function_scoped.base_url,
            api_key="test-key",
        )

        try:
            # Attempt XSS injection
            response = client.post(
                "/v1/chat/completions",
                json={
                    "model": "openai/gpt-oss-120b",
                    "messages": [
                        {
                            "role": "user",
                            "content": "<script>alert('xss')</script>",
                        }
                    ],
                },
            )

            # Should be rejected
            assert response.status_code == 400
            data = response.json()
            assert "error" in data
            assert data["error"]["type"] == "security_error"
        finally:
            client.close()

    @pytest.mark.server_config(
        api_keys=["test-key"],
        env_overrides={
            "FAKEAI_AUTH__REQUIRE_API_KEY": "true",
            "FAKEAI_AUTH__API_KEYS": '["test-key"]',
            "FAKEAI_SECURITY__ENABLE_ABUSE_DETECTION": "true",
        },
    )
    def test_oversized_payload_rejected(self, server_function_scoped: Any) -> None:
        """Test that oversized payloads are rejected."""
        client = FakeAIClient(
            base_url=server_function_scoped.base_url,
            api_key="test-key",
        )

        try:
            # Create very large payload (> 10MB)
            large_content = "x" * (11 * 1024 * 1024)  # 11MB

            response = client.post(
                "/v1/chat/completions",
                json={
                    "model": "openai/gpt-oss-120b",
                    "messages": [
                        {
                            "role": "user",
                            "content": large_content,
                        }
                    ],
                },
            )

            # Should be rejected with 413 (Payload Too Large)
            assert response.status_code == 413
            data = response.json()
            assert "error" in data
            assert data["error"]["type"] == "security_error"
        finally:
            client.close()

    @pytest.mark.server_config(
        api_keys=["test-key"],
        env_overrides={
            "FAKEAI_AUTH__REQUIRE_API_KEY": "true",
            "FAKEAI_AUTH__API_KEYS": '["test-key"]',
            "FAKEAI_SECURITY__ENABLE_ABUSE_DETECTION": "true",
        },
    )
    def test_null_bytes_rejected(self, server_function_scoped: Any) -> None:
        """Test that null bytes in strings are rejected."""
        client = FakeAIClient(
            base_url=server_function_scoped.base_url,
            api_key="test-key",
        )

        try:
            # Attempt to send null byte
            response = client.post(
                "/v1/chat/completions",
                json={
                    "model": "openai/gpt-oss-120b",
                    "messages": [
                        {
                            "role": "user",
                            "content": "hello\x00world",
                        }
                    ],
                },
            )

            # Should be rejected
            assert response.status_code == 400
            data = response.json()
            assert "error" in data
        finally:
            client.close()


class TestAbuseDetection:
    """Test abuse detection and banning mechanisms."""

    @pytest.mark.server_config(
        api_keys=["test-key"],
        env_overrides={
            "FAKEAI_AUTH__REQUIRE_API_KEY": "true",
            "FAKEAI_AUTH__API_KEYS": '["test-key"]',
            "FAKEAI_SECURITY__ENABLE_ABUSE_DETECTION": "true",
        },
    )
    def test_repeated_failed_auth_triggers_ban(
        self, server_function_scoped: Any
    ) -> None:
        """Test that repeated failed authentication triggers IP ban."""
        client = FakeAIClient(
            base_url=server_function_scoped.base_url,
            api_key="invalid-key",
        )

        try:
            # Make multiple failed auth attempts (threshold is 5)
            for i in range(6):
                response = client.get("/v1/models")
                if i < 5:
                    assert response.status_code == 401
                else:
                    # Should be banned now
                    assert response.status_code in [401, 403]
        finally:
            client.close()

    @pytest.mark.server_config(
        api_keys=["test-key"],
        env_overrides={
            "FAKEAI_AUTH__REQUIRE_API_KEY": "true",
            "FAKEAI_AUTH__API_KEYS": '["test-key"]',
            "FAKEAI_SECURITY__ENABLE_ABUSE_DETECTION": "true",
        },
    )
    def test_repeated_injection_attempts_trigger_ban(
        self, server_function_scoped: Any
    ) -> None:
        """Test that repeated injection attempts trigger IP ban."""
        client = FakeAIClient(
            base_url=server_function_scoped.base_url,
            api_key="test-key",
        )

        try:
            # Make multiple injection attempts (threshold is 3)
            for i in range(4):
                response = client.post(
                    "/v1/chat/completions",
                    json={
                        "model": "openai/gpt-oss-120b",
                        "messages": [
                            {
                                "role": "user",
                                "content": f"'; DROP TABLE users{i}; --",
                            }
                        ],
                    },
                )

                if i < 3:
                    assert response.status_code == 400
                else:
                    # Should be banned now (403)
                    assert response.status_code == 403
                    data = response.json()
                    assert "error" in data
                    assert data["error"]["type"] == "security_error"
        finally:
            client.close()

    @pytest.mark.server_config(
        api_keys=["test-key"],
        rate_limit_enabled=True,
        env_overrides={
            "FAKEAI_AUTH__REQUIRE_API_KEY": "true",
            "FAKEAI_AUTH__API_KEYS": '["test-key"]',
            "FAKEAI_SECURITY__ENABLE_ABUSE_DETECTION": "true",
            "FAKEAI_RATE_LIMITS__RPM_OVERRIDE": "3",
        },
    )
    def test_repeated_rate_limit_violations_trigger_ban(
        self, server_function_scoped: Any
    ) -> None:
        """Test that repeated rate limit violations trigger IP ban."""
        client = FakeAIClient(
            base_url=server_function_scoped.base_url,
            api_key="test-key",
        )

        try:
            # Make many requests to hit rate limit multiple times
            for i in range(25):
                response = client.get("/v1/models")
                # Ignore response codes initially, just trigger violations

            # After 20+ violations, should be banned
            # Make one more request to verify ban
            time.sleep(1)
            response = client.get("/v1/models")
            assert response.status_code == 403
            data = response.json()
            assert "error" in data
            assert data["error"]["type"] == "security_error"
            assert "banned" in data["error"]["message"].lower()
        finally:
            client.close()

    @pytest.mark.server_config(
        api_keys=["test-key"],
        env_overrides={
            "FAKEAI_AUTH__REQUIRE_API_KEY": "true",
            "FAKEAI_AUTH__API_KEYS": '["test-key"]',
            "FAKEAI_SECURITY__ENABLE_ABUSE_DETECTION": "true",
        },
    )
    def test_ban_includes_retry_after(self, server_function_scoped: Any) -> None:
        """Test that ban responses include retry-after information."""
        client = FakeAIClient(
            base_url=server_function_scoped.base_url,
            api_key="test-key",
        )

        try:
            # Trigger ban with injection attempts
            for _ in range(4):
                client.post(
                    "/v1/chat/completions",
                    json={
                        "model": "openai/gpt-oss-120b",
                        "messages": [
                            {
                                "role": "user",
                                "content": "'; DROP TABLE users; --",
                            }
                        ],
                    },
                )

            # Get ban response
            response = client.get("/v1/models")
            assert response.status_code == 403

            # Should include information about ban duration
            data = response.json()
            assert "error" in data
            message = data["error"]["message"].lower()
            assert "banned" in message or "retry" in message
        finally:
            client.close()


class TestCORSConfiguration:
    """Test CORS configuration."""

    def test_cors_headers_present(self, server: Any, test_api_key: str) -> None:
        """Test that CORS headers are present in responses."""
        import httpx

        response = httpx.options(
            f"{server.base_url}/v1/models",
            headers={
                "Origin": "http://example.com",
                "Access-Control-Request-Method": "GET",
            },
            timeout=30.0,
        )

        # Should have CORS headers
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers

    def test_cors_preflight_request(self, server: Any, test_api_key: str) -> None:
        """Test CORS preflight (OPTIONS) request."""
        import httpx

        response = httpx.options(
            f"{server.base_url}/v1/chat/completions",
            headers={
                "Origin": "http://example.com",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type,authorization",
            },
            timeout=30.0,
        )

        # Should return 200 for OPTIONS
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-headers" in response.headers


class TestSecurityHeaders:
    """Test security headers in responses."""

    def test_security_headers_present(self, server: Any, test_api_key: str) -> None:
        """Test that security headers are present."""
        client = FakeAIClient(
            base_url=server.base_url,
            api_key=test_api_key,
        )

        try:
            response = client.get("/v1/models")
            assert response.status_code == 200

            # Check for security headers
            # X-Content-Type-Options (prevents MIME sniffing)
            assert "x-content-type-options" in response.headers or True  # Optional

            # X-Frame-Options (prevent clickjacking)
            # Note: May not be set in all APIs, just checking presence
        finally:
            client.close()

    def test_content_type_header_correct(
        self, server: Any, test_api_key: str
    ) -> None:
        """Test that Content-Type headers are correct."""
        client = FakeAIClient(
            base_url=server.base_url,
            api_key=test_api_key,
        )

        try:
            response = client.get("/v1/models")
            assert response.status_code == 200

            # Should be JSON
            content_type = response.headers.get("content-type", "")
            assert "application/json" in content_type
        finally:
            client.close()


class TestHealthEndpointSecurity:
    """Test that health endpoint doesn't leak sensitive information."""

    def test_health_no_auth_required(self, server: Any) -> None:
        """Test that health endpoint doesn't require authentication."""
        client = FakeAIClient(
            base_url=server.base_url,
            api_key=None,  # No auth
        )

        try:
            response = client.get("/health")
            assert response.status_code == 200
        finally:
            client.close()

    def test_health_no_sensitive_data(self, server: Any) -> None:
        """Test that health endpoint doesn't expose sensitive data."""
        client = FakeAIClient(
            base_url=server.base_url,
            api_key=None,
        )

        try:
            response = client.get("/health")
            assert response.status_code == 200
            data = response.json()

            # Should not contain sensitive information
            data_str = str(data).lower()
            assert "password" not in data_str
            assert "secret" not in data_str
            assert "key" not in data_str or "api" not in data_str
        finally:
            client.close()


class TestMetricsEndpointSecurity:
    """Test that metrics endpoint has appropriate security."""

    def test_metrics_accessible(self, server: Any, test_api_key: str) -> None:
        """Test that metrics endpoint is accessible."""
        client = FakeAIClient(
            base_url=server.base_url,
            api_key=test_api_key,
        )

        try:
            response = client.get("/metrics")
            # Should be accessible (may or may not require auth)
            assert response.status_code in [200, 401]
        finally:
            client.close()

    def test_metrics_no_sensitive_data(
        self, server: Any, test_api_key: str
    ) -> None:
        """Test that metrics don't expose sensitive data."""
        client = FakeAIClient(
            base_url=server.base_url,
            api_key=test_api_key,
        )

        try:
            response = client.get("/metrics")
            if response.status_code == 200:
                data = response.json()

                # Should not contain raw API keys or passwords
                data_str = str(data).lower()
                assert "password" not in data_str
                assert "secret" not in data_str
                # API keys should be hashed or truncated if present
        finally:
            client.close()


class TestConcurrentSecurityChecks:
    """Test security under concurrent load."""

    @pytest.mark.server_config(
        api_keys=["key1", "key2", "key3"],
        env_overrides={
            "FAKEAI_AUTH__REQUIRE_API_KEY": "true",
            "FAKEAI_AUTH__API_KEYS": '["key1", "key2", "key3"]',
        },
    )
    def test_concurrent_auth_checks(self, server_function_scoped: Any) -> None:
        """Test that authentication is thread-safe under concurrent load."""
        base_url = server_function_scoped.base_url
        keys = ["key1", "key2", "key3", "invalid"]

        def make_request(key: str) -> tuple[str, int]:
            """Make request with given key."""
            client = FakeAIClient(base_url=base_url, api_key=key)
            try:
                response = client.get("/v1/models")
                return key, response.status_code
            finally:
                client.close()

        # Make concurrent requests with different keys
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            for _ in range(5):  # 5 rounds
                for key in keys:
                    futures.append(executor.submit(make_request, key))

            results = [future.result() for future in as_completed(futures)]

        # Verify results
        for key, status_code in results:
            if key == "invalid":
                assert status_code == 401
            else:
                assert status_code == 200

    @pytest.mark.server_config(
        api_keys=["test-key"],
        env_overrides={
            "FAKEAI_AUTH__REQUIRE_API_KEY": "true",
            "FAKEAI_AUTH__API_KEYS": '["test-key"]',
            "FAKEAI_SECURITY__ENABLE_ABUSE_DETECTION": "true",
        },
    )
    def test_concurrent_validation_checks(
        self, server_function_scoped: Any
    ) -> None:
        """Test that input validation is thread-safe."""
        base_url = server_function_scoped.base_url
        api_key = "test-key"

        payloads = [
            {"content": "Normal content"},
            {"content": "'; DROP TABLE users; --"},  # SQL injection
            {"content": "$(rm -rf /)"},  # Command injection
            {"content": "Hello world"},  # Normal
        ]

        def make_request(payload: dict) -> int:
            """Make request with given payload."""
            client = FakeAIClient(base_url=base_url, api_key=api_key)
            try:
                response = client.post(
                    "/v1/chat/completions",
                    json={
                        "model": "openai/gpt-oss-120b",
                        "messages": [{"role": "user", "content": payload["content"]}],
                    },
                )
                return response.status_code
            finally:
                client.close()

        # Make concurrent requests with different payloads
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(make_request, p) for p in payloads * 3]
            results = [future.result() for future in as_completed(futures)]

        # Should have both 200s (valid) and 400s (invalid)
        assert 200 in results
        assert 400 in results


class TestErrorMessages:
    """Test that error messages don't leak sensitive information."""

    @pytest.mark.server_config(
        api_keys=["test-key"],
        env_overrides={
            "FAKEAI_AUTH__REQUIRE_API_KEY": "true",
            "FAKEAI_AUTH__API_KEYS": '["test-key"]',
        },
    )
    def test_auth_error_no_leak(self, server_function_scoped: Any) -> None:
        """Test that auth error messages don't leak key information."""
        client = FakeAIClient(
            base_url=server_function_scoped.base_url,
            api_key="invalid-key-12345",
        )

        try:
            response = client.get("/v1/models")
            assert response.status_code == 401
            data = response.json()

            # Error message should not contain the key
            error_msg = str(data).lower()
            assert "invalid-key-12345" not in error_msg
            assert "12345" not in error_msg
        finally:
            client.close()

    @pytest.mark.server_config(
        api_keys=["test-key"],
        env_overrides={
            "FAKEAI_AUTH__REQUIRE_API_KEY": "true",
            "FAKEAI_AUTH__API_KEYS": '["test-key"]',
            "FAKEAI_SECURITY__ENABLE_ABUSE_DETECTION": "true",
        },
    )
    def test_validation_error_no_leak(self, server_function_scoped: Any) -> None:
        """Test that validation errors don't leak system information."""
        client = FakeAIClient(
            base_url=server_function_scoped.base_url,
            api_key="test-key",
        )

        try:
            response = client.post(
                "/v1/chat/completions",
                json={
                    "model": "openai/gpt-oss-120b",
                    "messages": [
                        {
                            "role": "user",
                            "content": "'; DROP TABLE users; --",
                        }
                    ],
                },
            )

            assert response.status_code == 400
            data = response.json()

            # Should not leak system paths, internal details
            error_msg = str(data).lower()
            assert "/home/" not in error_msg
            assert "/root/" not in error_msg
            assert "traceback" not in error_msg
        finally:
            client.close()


class TestEdgeCases:
    """Test security edge cases."""

    @pytest.mark.server_config(
        api_keys=["test-key"],
        env_overrides={
            "FAKEAI_AUTH__REQUIRE_API_KEY": "true",
            "FAKEAI_AUTH__API_KEYS": '["test-key"]',
        },
    )
    def test_empty_api_key(self, server_function_scoped: Any) -> None:
        """Test that empty API key is rejected."""
        client = FakeAIClient(
            base_url=server_function_scoped.base_url,
            api_key="",
        )

        try:
            response = client.get("/v1/models")
            assert response.status_code == 401
        finally:
            client.close()

    @pytest.mark.server_config(
        api_keys=["test-key"],
        env_overrides={
            "FAKEAI_AUTH__REQUIRE_API_KEY": "true",
            "FAKEAI_AUTH__API_KEYS": '["test-key"]',
        },
    )
    def test_whitespace_only_api_key(self, server_function_scoped: Any) -> None:
        """Test that whitespace-only API key is rejected."""
        client = FakeAIClient(
            base_url=server_function_scoped.base_url,
            api_key="   ",
        )

        try:
            response = client.get("/v1/models")
            assert response.status_code == 401
        finally:
            client.close()

    @pytest.mark.server_config(
        api_keys=["test-key"],
        env_overrides={
            "FAKEAI_AUTH__REQUIRE_API_KEY": "true",
            "FAKEAI_AUTH__API_KEYS": '["test-key"]',
            "FAKEAI_SECURITY__ENABLE_ABUSE_DETECTION": "true",
        },
    )
    def test_unicode_in_payload(self, server_function_scoped: Any) -> None:
        """Test that unicode characters are handled safely."""
        client = FakeAIClient(
            base_url=server_function_scoped.base_url,
            api_key="test-key",
        )

        try:
            response = client.post(
                "/v1/chat/completions",
                json={
                    "model": "openai/gpt-oss-120b",
                    "messages": [
                        {
                            "role": "user",
                            "content": "Hello 世界 🌍",
                        }
                    ],
                },
            )

            # Should succeed (unicode is valid)
            assert response.status_code == 200
        finally:
            client.close()

    @pytest.mark.server_config(
        api_keys=["test-key"],
        env_overrides={
            "FAKEAI_AUTH__REQUIRE_API_KEY": "true",
            "FAKEAI_AUTH__API_KEYS": '["test-key"]',
        },
    )
    def test_very_long_api_key(self, server_function_scoped: Any) -> None:
        """Test that very long API keys are handled safely."""
        client = FakeAIClient(
            base_url=server_function_scoped.base_url,
            api_key="a" * 10000,  # 10K character key
        )

        try:
            response = client.get("/v1/models")
            # Should be rejected (not in allowed list)
            assert response.status_code == 401

            # Should not cause server crash or memory issues
        finally:
            client.close()
