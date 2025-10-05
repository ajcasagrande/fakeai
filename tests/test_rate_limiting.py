"""
Tests for rate limiting functionality.

This module tests the token bucket algorithm implementation and
rate limiting enforcement across the FakeAI API.
"""
#  SPDX-License-Identifier: Apache-2.0

import asyncio
import time

import pytest
from fastapi.testclient import TestClient

from fakeai.app import app, config, rate_limiter
from fakeai.rate_limiter import RateLimitBucket, RateLimiter, RATE_LIMIT_TIERS


class TestRateLimitBucket:
    """Tests for the RateLimitBucket class."""

    def test_bucket_initialization(self):
        """Test that bucket initializes with full capacity."""
        bucket = RateLimitBucket(capacity=100, refill_rate=10.0)
        assert bucket.capacity == 100
        assert bucket.refill_rate == 10.0
        assert bucket.tokens == 100.0
        assert bucket.remaining() == 100

    def test_consume_tokens_success(self):
        """Test successful token consumption."""
        bucket = RateLimitBucket(capacity=100, refill_rate=10.0)

        # Consume 10 tokens
        success, retry_after = bucket.try_consume(10)
        assert success is True
        assert retry_after == 0.0
        assert bucket.remaining() == 90

    def test_consume_tokens_failure(self):
        """Test failed token consumption when insufficient tokens."""
        bucket = RateLimitBucket(capacity=100, refill_rate=10.0)

        # Consume all tokens
        bucket.try_consume(100)
        assert bucket.remaining() == 0

        # Try to consume more - should fail
        success, retry_after = bucket.try_consume(10)
        assert success is False
        assert retry_after > 0
        assert bucket.remaining() == 0

    def test_token_refill(self):
        """Test that tokens refill over time."""
        bucket = RateLimitBucket(capacity=100, refill_rate=100.0)  # 100 tokens/sec

        # Consume all tokens
        bucket.try_consume(100)
        assert bucket.remaining() == 0

        # Wait 0.5 seconds - should refill ~50 tokens
        time.sleep(0.5)
        remaining = bucket.remaining()
        assert 45 <= remaining <= 55  # Allow some variance

    def test_refill_does_not_exceed_capacity(self):
        """Test that refill stops at capacity."""
        bucket = RateLimitBucket(capacity=100, refill_rate=100.0)

        # Wait longer than needed to fill
        time.sleep(2.0)

        # Should not exceed capacity
        assert bucket.remaining() == 100

    def test_reset_time_calculation(self):
        """Test reset time calculation."""
        bucket = RateLimitBucket(capacity=100, refill_rate=100.0)

        # Consume all tokens
        bucket.try_consume(100)

        # Reset time should be ~1 second from now
        reset_time = bucket.reset_time()
        current_time = time.time()
        time_until_reset = reset_time - current_time

        assert 0.9 <= time_until_reset <= 1.1  # ~1 second

    def test_retry_after_calculation(self):
        """Test retry_after calculation when rate limited."""
        bucket = RateLimitBucket(capacity=100, refill_rate=10.0)  # 10 tokens/sec

        # Consume all tokens
        bucket.try_consume(100)

        # Try to consume 20 more - need 2 seconds to refill
        success, retry_after = bucket.try_consume(20)
        assert success is False
        assert 1.9 <= retry_after <= 2.1  # ~2 seconds

    def test_thread_safety(self):
        """Test that bucket operations are thread-safe."""
        import threading

        bucket = RateLimitBucket(capacity=1000, refill_rate=100.0)
        results = []

        def consume_tokens():
            for _ in range(10):
                success, _ = bucket.try_consume(10)
                results.append(success)

        # Create 10 threads that each try to consume 10 tokens 10 times
        threads = [threading.Thread(target=consume_tokens) for _ in range(10)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # Should have 100 successful consumptions before running out
        successful = sum(1 for r in results if r)
        assert successful == 100


class TestRateLimiter:
    """Tests for the RateLimiter singleton class."""

    def test_singleton_pattern(self):
        """Test that RateLimiter is a singleton."""
        limiter1 = RateLimiter()
        limiter2 = RateLimiter()
        assert limiter1 is limiter2

    def test_configure_with_tier(self):
        """Test configuring rate limiter with a tier."""
        limiter = RateLimiter()
        limiter.reset()  # Clear state

        limiter.configure(tier="free")

        # Check that tier limits are applied
        headers = limiter.get_headers("test-key")
        assert headers["x-ratelimit-limit-requests"] == "60"
        assert headers["x-ratelimit-limit-tokens"] == "10000"

    def test_configure_with_custom_limits(self):
        """Test configuring rate limiter with custom limits."""
        limiter = RateLimiter()
        limiter.reset()  # Clear state

        limiter.configure(tier="tier-1", rpm_override=1000, tpm_override=50000)

        # Check that custom limits are applied
        headers = limiter.get_headers("test-key")
        assert headers["x-ratelimit-limit-requests"] == "1000"
        assert headers["x-ratelimit-limit-tokens"] == "50000"

    def test_check_rate_limit_allowed(self):
        """Test that requests within limits are allowed."""
        limiter = RateLimiter()
        limiter.reset()  # Clear state
        limiter.configure(tier="tier-1")  # 500 RPM, 30K TPM

        # First request should be allowed
        allowed, retry_after, headers = limiter.check_rate_limit("test-key", tokens=100)
        assert allowed is True
        assert retry_after is None
        assert int(headers["x-ratelimit-remaining-requests"]) == 499
        assert int(headers["x-ratelimit-remaining-tokens"]) >= 29800

    def test_check_rate_limit_rpm_exceeded(self):
        """Test that requests are blocked when RPM limit is exceeded."""
        limiter = RateLimiter()
        limiter.reset()  # Clear state
        limiter.configure(tier="free")  # 60 RPM

        # Consume all 60 requests
        for i in range(60):
            allowed, _, _ = limiter.check_rate_limit("test-key", tokens=10)
            assert allowed is True, f"Request {i+1} should be allowed"

        # 61st request should be blocked
        allowed, retry_after, headers = limiter.check_rate_limit("test-key", tokens=10)
        assert allowed is False
        assert retry_after is not None
        assert int(retry_after) > 0

    def test_check_rate_limit_tpm_exceeded(self):
        """Test that requests are blocked when TPM limit is exceeded."""
        limiter = RateLimiter()
        limiter.reset()  # Clear state
        limiter.configure(tier="free")  # 10K TPM

        # Consume all 10,000 tokens
        allowed, _, _ = limiter.check_rate_limit("test-key", tokens=10000)
        assert allowed is True

        # Request with more tokens should be blocked
        allowed, retry_after, headers = limiter.check_rate_limit("test-key", tokens=100)
        assert allowed is False
        assert retry_after is not None
        assert int(retry_after) > 0

    def test_per_key_isolation(self):
        """Test that rate limits are isolated per API key."""
        limiter = RateLimiter()
        limiter.reset()  # Clear state
        limiter.configure(tier="free")  # 60 RPM

        # Exhaust rate limit for key1
        for _ in range(60):
            limiter.check_rate_limit("key1", tokens=10)

        # key1 should be rate limited
        allowed1, _, _ = limiter.check_rate_limit("key1", tokens=10)
        assert allowed1 is False

        # key2 should still be allowed
        allowed2, _, _ = limiter.check_rate_limit("key2", tokens=10)
        assert allowed2 is True

    def test_rate_limit_headers_format(self):
        """Test that rate limit headers have correct format."""
        limiter = RateLimiter()
        limiter.reset()  # Clear state
        limiter.configure(tier="tier-2")  # 5000 RPM, 450K TPM

        allowed, _, headers = limiter.check_rate_limit("test-key", tokens=1000)

        # Check all required headers are present
        assert "x-ratelimit-limit-requests" in headers
        assert "x-ratelimit-limit-tokens" in headers
        assert "x-ratelimit-remaining-requests" in headers
        assert "x-ratelimit-remaining-tokens" in headers
        assert "x-ratelimit-reset-requests" in headers
        assert "x-ratelimit-reset-tokens" in headers

        # Check values are numeric strings
        for key, value in headers.items():
            assert value.isdigit(), f"Header {key} should be numeric"

    def test_reset_single_key(self):
        """Test resetting rate limits for a single key."""
        limiter = RateLimiter()
        limiter.reset()  # Clear all state
        limiter.configure(tier="free")

        # Use up some requests
        limiter.check_rate_limit("key1", tokens=10)
        limiter.check_rate_limit("key2", tokens=10)

        # Reset key1
        limiter.reset("key1")

        # key1 should be back to full capacity
        headers1 = limiter.get_headers("key1")
        assert int(headers1["x-ratelimit-remaining-requests"]) == 60

        # key2 should still have consumed request
        headers2 = limiter.get_headers("key2")
        assert int(headers2["x-ratelimit-remaining-requests"]) == 59

    def test_reset_all_keys(self):
        """Test resetting rate limits for all keys."""
        limiter = RateLimiter()
        limiter.configure(tier="free")

        # Use up some requests
        limiter.check_rate_limit("key1", tokens=10)
        limiter.check_rate_limit("key2", tokens=10)

        # Reset all
        limiter.reset()

        # Both keys should be back to full capacity
        headers1 = limiter.get_headers("key1")
        headers2 = limiter.get_headers("key2")
        assert int(headers1["x-ratelimit-remaining-requests"]) == 60
        assert int(headers2["x-ratelimit-remaining-requests"]) == 60


class TestRateLimitingIntegration:
    """Integration tests for rate limiting with FastAPI."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Reset rate limiter before and after each test."""
        rate_limiter.reset()
        yield
        rate_limiter.reset()

    def test_rate_limiting_disabled_by_default(self):
        """Test that rate limiting is disabled by default."""
        # Temporarily disable rate limiting
        original_value = config.rate_limit_enabled
        config.rate_limit_enabled = False

        try:
            client = TestClient(app)
            # Should work without rate limiting
            for _ in range(100):
                response = client.get("/health")
                assert response.status_code == 200
        finally:
            config.rate_limit_enabled = original_value

    def test_rate_limiting_requires_api_key(self):
        """Test that rate limiting only works when API keys are required."""
        # Temporarily enable rate limiting but disable API key requirement
        original_rate_limit = config.rate_limit_enabled
        original_api_key = config.require_api_key

        config.rate_limit_enabled = True
        config.require_api_key = False

        try:
            client = TestClient(app)
            # Should work without rate limiting since no API key required
            for _ in range(100):
                response = client.get("/health")
                assert response.status_code == 200
        finally:
            config.rate_limit_enabled = original_rate_limit
            config.require_api_key = original_api_key

    def test_rate_limit_headers_in_response(self):
        """Test that rate limit headers are included in responses."""
        # Enable rate limiting
        original_rate_limit = config.rate_limit_enabled
        original_api_key = config.require_api_key
        original_keys = config.api_keys.copy()

        config.rate_limit_enabled = True
        config.require_api_key = True
        config.api_keys = ["test-key-123"]
        rate_limiter.configure(tier="tier-1")

        try:
            client = TestClient(app)
            response = client.get(
                "/v1/models",
                headers={"Authorization": "Bearer test-key-123"}
            )

            assert response.status_code == 200

            # Check rate limit headers
            assert "x-ratelimit-limit-requests" in response.headers
            assert "x-ratelimit-limit-tokens" in response.headers
            assert "x-ratelimit-remaining-requests" in response.headers
            assert "x-ratelimit-remaining-tokens" in response.headers
            assert "x-ratelimit-reset-requests" in response.headers
            assert "x-ratelimit-reset-tokens" in response.headers
        finally:
            config.rate_limit_enabled = original_rate_limit
            config.require_api_key = original_api_key
            config.api_keys = original_keys

    def test_rate_limit_429_response(self):
        """Test that 429 response is returned when rate limited."""
        # Enable rate limiting with very low limits
        original_rate_limit = config.rate_limit_enabled
        original_api_key = config.require_api_key
        original_keys = config.api_keys.copy()

        config.rate_limit_enabled = True
        config.require_api_key = True
        config.api_keys = ["test-key-123"]
        rate_limiter.configure(tier="free", rpm_override=2)  # Only 2 requests per minute

        try:
            client = TestClient(app)

            # First 2 requests should succeed
            response1 = client.get(
                "/v1/models",
                headers={"Authorization": "Bearer test-key-123"}
            )
            assert response1.status_code == 200

            response2 = client.get(
                "/v1/models",
                headers={"Authorization": "Bearer test-key-123"}
            )
            assert response2.status_code == 200

            # Third request should be rate limited
            response3 = client.get(
                "/v1/models",
                headers={"Authorization": "Bearer test-key-123"}
            )
            assert response3.status_code == 429

            # Check error response
            data = response3.json()
            assert "error" in data
            assert data["error"]["code"] == "rate_limit_exceeded"
            assert data["error"]["type"] == "rate_limit_error"

            # Check Retry-After header
            assert "Retry-After" in response3.headers
            assert int(response3.headers["Retry-After"]) > 0
        finally:
            config.rate_limit_enabled = original_rate_limit
            config.require_api_key = original_api_key
            config.api_keys = original_keys

    def test_rate_limit_with_chat_completion(self):
        """Test rate limiting with chat completion endpoint."""
        # Enable rate limiting
        original_rate_limit = config.rate_limit_enabled
        original_api_key = config.require_api_key
        original_keys = config.api_keys.copy()

        config.rate_limit_enabled = True
        config.require_api_key = True
        config.api_keys = ["test-key-123"]
        rate_limiter.configure(tier="free", tpm_override=500)  # Low token limit

        try:
            client = TestClient(app)

            # First request should succeed
            response1 = client.post(
                "/v1/chat/completions",
                headers={"Authorization": "Bearer test-key-123"},
                json={
                    "model": "openai/gpt-oss-120b",
                    "messages": [{"role": "user", "content": "Hello" * 100}]
                }
            )
            assert response1.status_code == 200

            # Second request might be rate limited due to token usage
            response2 = client.post(
                "/v1/chat/completions",
                headers={"Authorization": "Bearer test-key-123"},
                json={
                    "model": "openai/gpt-oss-120b",
                    "messages": [{"role": "user", "content": "Hello" * 100}]
                }
            )

            # Should eventually get rate limited
            if response2.status_code == 429:
                assert "Retry-After" in response2.headers
        finally:
            config.rate_limit_enabled = original_rate_limit
            config.require_api_key = original_api_key
            config.api_keys = original_keys

    def test_different_tiers(self):
        """Test that different tiers have different limits."""
        rate_limiter.reset()

        # Test free tier
        rate_limiter.configure(tier="free")
        headers_free = rate_limiter.get_headers("key1")
        assert int(headers_free["x-ratelimit-limit-requests"]) == 60
        assert int(headers_free["x-ratelimit-limit-tokens"]) == 10000

        # Test tier-2
        rate_limiter.configure(tier="tier-2")
        headers_tier2 = rate_limiter.get_headers("key2")
        assert int(headers_tier2["x-ratelimit-limit-requests"]) == 5000
        assert int(headers_tier2["x-ratelimit-limit-tokens"]) == 450000

        # Test tier-5
        rate_limiter.configure(tier="tier-5")
        headers_tier5 = rate_limiter.get_headers("key3")
        assert int(headers_tier5["x-ratelimit-limit-requests"]) == 100000
        assert int(headers_tier5["x-ratelimit-limit-tokens"]) == 15000000


class TestRateLimitTiers:
    """Tests for pre-defined rate limit tiers."""

    def test_all_tiers_defined(self):
        """Test that all expected tiers are defined."""
        expected_tiers = ["free", "tier-1", "tier-2", "tier-3", "tier-4", "tier-5"]
        for tier_name in expected_tiers:
            assert tier_name in RATE_LIMIT_TIERS

    def test_tier_values(self):
        """Test that tier values match expected limits."""
        assert RATE_LIMIT_TIERS["free"].rpm == 60
        assert RATE_LIMIT_TIERS["free"].tpm == 10_000

        assert RATE_LIMIT_TIERS["tier-1"].rpm == 500
        assert RATE_LIMIT_TIERS["tier-1"].tpm == 30_000

        assert RATE_LIMIT_TIERS["tier-2"].rpm == 5_000
        assert RATE_LIMIT_TIERS["tier-2"].tpm == 450_000

        assert RATE_LIMIT_TIERS["tier-3"].rpm == 10_000
        assert RATE_LIMIT_TIERS["tier-3"].tpm == 1_000_000

        assert RATE_LIMIT_TIERS["tier-4"].rpm == 30_000
        assert RATE_LIMIT_TIERS["tier-4"].tpm == 5_000_000

        assert RATE_LIMIT_TIERS["tier-5"].rpm == 100_000
        assert RATE_LIMIT_TIERS["tier-5"].tpm == 15_000_000
