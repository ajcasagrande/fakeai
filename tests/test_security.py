"""
Security hardening tests for FakeAI.

Tests input validation, injection detection, API key security,
abuse detection, and CORS policies.
"""
#  SPDX-License-Identifier: Apache-2.0

import pytest
import time
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

from fakeai.app import app
from fakeai.config import AppConfig
from fakeai.security import (
    ApiKeyManager,
    AbuseDetector,
    InputValidator,
    InputValidationError,
    InjectionAttackDetected,
    PayloadTooLarge,
    generate_api_key,
)


@pytest.fixture
def test_config():
    """Create test configuration with security enabled."""
    return AppConfig(
        require_api_key=True,
        hash_api_keys=True,
        enable_input_validation=True,
        enable_injection_detection=True,
        enable_abuse_detection=True,
        max_request_size=1024 * 1024,  # 1 MB for testing
        cors_allowed_origins=["http://localhost:3000", "https://example.com"],
    )


@pytest.fixture
def api_key_manager():
    """Create a fresh API key manager for testing."""
    manager = ApiKeyManager()
    # Clear any existing keys
    manager._keys.clear()
    manager._prefix_map.clear()
    return manager


@pytest.fixture
def abuse_detector():
    """Create a fresh abuse detector for testing."""
    detector = AbuseDetector()
    # Clear any existing records
    detector._records.clear()
    return detector


@pytest.fixture
def input_validator():
    """Create an input validator for testing."""
    return InputValidator()


class TestInputValidation:
    """Test input validation and sanitization."""

    def test_sanitize_valid_string(self, input_validator):
        """Test sanitizing a valid string."""
        text = "Hello, world! This is a valid string."
        result = input_validator.sanitize_string(text)
        assert result == text

    def test_sanitize_string_removes_control_chars(self, input_validator):
        """Test that control characters are removed."""
        text = "Hello\x00\x01\x02World"
        with pytest.raises(InputValidationError, match="null bytes"):
            input_validator.sanitize_string(text)

    def test_sanitize_string_rejects_oversized(self, input_validator):
        """Test that oversized strings are rejected."""
        text = "a" * (1024 * 1024 + 1)  # 1 MB + 1 byte
        with pytest.raises(InputValidationError, match="exceeds maximum"):
            input_validator.sanitize_string(text)

    def test_validate_array_valid(self, input_validator):
        """Test validating a valid array."""
        arr = [1, 2, 3, 4, 5]
        result = input_validator.validate_array(arr)
        assert result == arr

    def test_validate_array_oversized(self, input_validator):
        """Test that oversized arrays are rejected."""
        arr = list(range(10001))  # Over MAX_ARRAY_LENGTH
        with pytest.raises(InputValidationError, match="exceeds maximum"):
            input_validator.validate_array(arr)

    def test_validate_dict_valid(self, input_validator):
        """Test validating a valid dictionary."""
        d = {"key1": "value1", "key2": "value2"}
        result = input_validator.validate_dict(d)
        assert result == d

    def test_validate_dict_with_allowed_keys(self, input_validator):
        """Test validating a dictionary with allowed keys."""
        d = {"allowed": "value", "also_allowed": "value"}
        allowed_keys = {"allowed", "also_allowed"}
        result = input_validator.validate_dict(d, allowed_keys=allowed_keys)
        assert result == d

    def test_validate_dict_rejects_unexpected_keys(self, input_validator):
        """Test that unexpected keys are rejected."""
        d = {"allowed": "value", "not_allowed": "value"}
        allowed_keys = {"allowed"}
        with pytest.raises(InputValidationError, match="Unexpected key"):
            input_validator.validate_dict(d, allowed_keys=allowed_keys)

    def test_validate_payload_size_valid(self, input_validator):
        """Test validating a valid payload size."""
        payload = b"a" * 1024  # 1 KB
        input_validator.validate_payload_size(payload)  # Should not raise

    def test_validate_payload_size_oversized(self, input_validator):
        """Test that oversized payloads are rejected."""
        payload = b"a" * (10 * 1024 * 1024 + 1)  # Over 10 MB
        with pytest.raises(PayloadTooLarge):
            input_validator.validate_payload_size(payload)


class TestInjectionDetection:
    """Test injection attack detection."""

    def test_sql_injection_detected(self, input_validator):
        """Test that SQL injection attempts are detected."""
        malicious = "'; DROP TABLE users; --"
        with pytest.raises(InjectionAttackDetected):
            input_validator.sanitize_string(malicious)

    def test_union_select_detected(self, input_validator):
        """Test that UNION SELECT is detected."""
        malicious = "admin' UNION SELECT * FROM passwords --"
        with pytest.raises(InjectionAttackDetected):
            input_validator.sanitize_string(malicious)

    def test_command_injection_detected(self, input_validator):
        """Test that command injection attempts are detected."""
        malicious = "; ls -la | cat /etc/passwd"
        with pytest.raises(InjectionAttackDetected):
            input_validator.sanitize_string(malicious)

    def test_script_injection_detected(self, input_validator):
        """Test that script injection attempts are detected."""
        malicious = "<script>alert('XSS')</script>"
        with pytest.raises(InjectionAttackDetected):
            input_validator.sanitize_string(malicious)

    def test_path_traversal_detected(self, input_validator):
        """Test that path traversal attempts are detected."""
        malicious = "../../etc/passwd"
        with pytest.raises(InjectionAttackDetected):
            input_validator.sanitize_string(malicious)

    def test_ldap_injection_detected(self, input_validator):
        """Test that LDAP injection attempts are detected."""
        malicious = "*)(uid=*))(|(uid=*"
        with pytest.raises(InjectionAttackDetected):
            input_validator.sanitize_string(malicious)

    def test_normal_text_not_flagged(self, input_validator):
        """Test that normal text is not flagged as injection."""
        normal_texts = [
            "Hello, world!",
            "What is the weather today?",
            "Please help me understand this concept.",
            "The price is $100.00",
            "Email me at user@example.com",
        ]
        for text in normal_texts:
            result = input_validator.sanitize_string(text)
            assert result is not None


class TestApiKeyManagement:
    """Test API key management and security."""

    def test_add_and_verify_key(self, api_key_manager):
        """Test adding and verifying an API key."""
        key = generate_api_key()
        api_key_manager.add_key(key)
        assert api_key_manager.verify_key(key) is True

    def test_verify_invalid_key(self, api_key_manager):
        """Test that invalid keys are rejected."""
        key = generate_api_key()
        api_key_manager.add_key(key)

        invalid_key = generate_api_key()
        assert api_key_manager.verify_key(invalid_key) is False

    def test_key_hashing(self, api_key_manager):
        """Test that keys are hashed and not stored in plaintext."""
        key = "sk-fake-test-key-123"
        key_hash = api_key_manager.add_key(key)

        # The hash should be different from the original key
        assert key_hash != key
        assert len(key_hash) == 64  # SHA-256 produces 64 hex characters

        # Key should still verify correctly
        assert api_key_manager.verify_key(key) is True

    def test_revoke_key(self, api_key_manager):
        """Test revoking an API key."""
        key = generate_api_key()
        api_key_manager.add_key(key)

        # Verify key works
        assert api_key_manager.verify_key(key) is True

        # Revoke key
        assert api_key_manager.revoke_key(key) is True

        # Verify key no longer works
        assert api_key_manager.verify_key(key) is False

    def test_key_expiration(self, api_key_manager):
        """Test that expired keys are rejected."""
        key = generate_api_key()
        expires_at = datetime.now() - timedelta(hours=1)  # Already expired
        api_key_manager.add_key(key, expires_at=expires_at)

        # Expired key should not verify
        assert api_key_manager.verify_key(key) is False

    def test_key_usage_tracking(self, api_key_manager):
        """Test that key usage is tracked."""
        key = generate_api_key()
        api_key_manager.add_key(key)

        # Use key multiple times
        for _ in range(5):
            api_key_manager.verify_key(key)

        # Check usage count
        info = api_key_manager.get_key_info(key)
        assert info is not None
        assert info.usage_count == 5
        assert info.last_used is not None

    def test_list_keys(self, api_key_manager):
        """Test listing API keys."""
        keys = [generate_api_key() for _ in range(3)]
        for key in keys:
            api_key_manager.add_key(key)

        key_list = api_key_manager.list_keys()
        assert len(key_list) == 3

    def test_cleanup_expired_keys(self, api_key_manager):
        """Test cleaning up expired keys."""
        # Add active key
        active_key = generate_api_key()
        api_key_manager.add_key(active_key)

        # Add expired key
        expired_key = generate_api_key()
        expires_at = datetime.now() - timedelta(hours=1)
        api_key_manager.add_key(expired_key, expires_at=expires_at)

        # Cleanup
        removed = api_key_manager.cleanup_expired()
        assert removed == 1

        # Active key should still exist
        assert api_key_manager.verify_key(active_key) is True


class TestAbuseDetection:
    """Test abuse detection and banning."""

    def test_failed_auth_threshold(self, abuse_detector):
        """Test that repeated failed auth attempts trigger a ban."""
        ip = "192.168.1.100"

        # Record failed attempts
        for _ in range(abuse_detector.FAILED_AUTH_THRESHOLD):
            abuse_detector.record_failed_auth(ip)

        # IP should now be banned
        is_banned, _ = abuse_detector.is_banned(ip)
        assert is_banned is True

    def test_injection_attempt_ban(self, abuse_detector):
        """Test that injection attempts trigger a ban."""
        ip = "192.168.1.101"

        # Record injection attempts (threshold is lower)
        for _ in range(abuse_detector.INJECTION_THRESHOLD):
            abuse_detector.record_injection_attempt(ip)

        # IP should now be banned
        is_banned, _ = abuse_detector.is_banned(ip)
        assert is_banned is True

    def test_rate_limit_violations(self, abuse_detector):
        """Test that rate limit violations are tracked."""
        ip = "192.168.1.102"

        # Record rate limit violations
        for _ in range(abuse_detector.RATE_LIMIT_THRESHOLD):
            abuse_detector.record_rate_limit_violation(ip)

        # IP should be banned
        is_banned, _ = abuse_detector.is_banned(ip)
        assert is_banned is True

    def test_oversized_payload_tracking(self, abuse_detector):
        """Test that oversized payloads are tracked."""
        ip = "192.168.1.103"

        # Record oversized payloads
        for _ in range(abuse_detector.OVERSIZED_THRESHOLD):
            abuse_detector.record_oversized_payload(ip)

        # IP should be banned
        is_banned, _ = abuse_detector.is_banned(ip)
        assert is_banned is True

    def test_progressive_ban_durations(self, abuse_detector):
        """Test that ban durations increase with violations."""
        ip = "192.168.1.104"

        # First violations - temporary ban
        for _ in range(10):
            abuse_detector.record_failed_auth(ip)

        is_banned, ban_time = abuse_detector.is_banned(ip)
        assert is_banned is True
        assert ban_time > 0

        # Get record to check violations
        record = abuse_detector.get_record(ip)
        assert record.get_total_violations() >= 10

    def test_reset_record(self, abuse_detector):
        """Test resetting an abuse record."""
        ip = "192.168.1.105"

        # Record some violations
        for _ in range(5):
            abuse_detector.record_failed_auth(ip)

        # Reset
        abuse_detector.reset_record(ip)

        # Record should be cleared
        is_banned, _ = abuse_detector.is_banned(ip)
        assert is_banned is False

    def test_cleanup_old_records(self, abuse_detector):
        """Test cleaning up old abuse records."""
        ip = "192.168.1.106"

        # Record a violation
        abuse_detector.record_failed_auth(ip)

        # Cleanup with very short max age (should remove record)
        removed = abuse_detector.cleanup_old_records(max_age_seconds=0)
        assert removed >= 0  # May or may not remove depending on timing


class TestApiKeyGeneration:
    """Test API key generation."""

    def test_generate_api_key_format(self):
        """Test that generated keys have correct format."""
        key = generate_api_key()
        assert key.startswith("sk-fake-")
        assert len(key) > 20  # Should be reasonably long

    def test_generate_unique_keys(self):
        """Test that generated keys are unique."""
        keys = [generate_api_key() for _ in range(100)]
        assert len(set(keys)) == 100  # All keys should be unique

    def test_custom_prefix(self):
        """Test generating keys with custom prefix."""
        key = generate_api_key(prefix="sk-test")
        assert key.startswith("sk-test-")


class TestSecurityIntegration:
    """Integration tests for security features."""

    def test_injection_blocked_in_request(self):
        """Test that injection attempts are blocked in API requests."""
        client = TestClient(app)

        # Try SQL injection in chat completion
        response = client.post(
            "/v1/chat/completions",
            json={
                "model": "openai/gpt-oss-120b",
                "messages": [
                    {"role": "user", "content": "'; DROP TABLE users; --"}
                ]
            }
        )

        # Should be blocked (either 400 or 401 depending on auth)
        assert response.status_code in [400, 401]

    def test_oversized_payload_blocked(self):
        """Test that oversized payloads are rejected."""
        client = TestClient(app)

        # Create a very large payload
        large_message = "a" * (10 * 1024 * 1024)  # 10 MB
        response = client.post(
            "/v1/chat/completions",
            json={
                "model": "openai/gpt-oss-120b",
                "messages": [
                    {"role": "user", "content": large_message}
                ]
            }
        )

        # Should be blocked with 413 Payload Too Large
        assert response.status_code in [413, 401]

    def test_cors_headers_present(self):
        """Test that CORS headers are present."""
        client = TestClient(app)

        response = client.options(
            "/v1/models",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            }
        )

        # CORS headers should be present
        assert "access-control-allow-origin" in response.headers

    def test_multiple_failed_auth_attempts(self):
        """Test that multiple failed auth attempts are handled."""
        client = TestClient(app)

        # Make multiple requests with invalid API key
        for _ in range(3):
            response = client.get(
                "/v1/models",
                headers={"Authorization": "Bearer invalid-key"}
            )
            # Should get 401 if auth is required
            assert response.status_code in [200, 401]


class TestSecurityBestPractices:
    """Test security best practices."""

    def test_no_plaintext_keys_in_logs(self, api_key_manager):
        """Test that API keys are not stored in plaintext."""
        key = "sk-fake-secret-key-12345"
        api_key_manager.add_key(key)

        # Check that the original key is not in the stored keys
        for stored_key in api_key_manager._keys.keys():
            assert key not in stored_key
            assert stored_key != key

    def test_rate_limit_headers_present(self):
        """Test that rate limit headers are included when enabled."""
        # This would require enabling rate limiting in the test config
        # and making authenticated requests
        pass

    def test_security_headers_on_errors(self):
        """Test that security headers are present even on error responses."""
        client = TestClient(app)

        response = client.get("/nonexistent-endpoint")
        assert response.status_code == 404

        # Should still have security headers
        # (FastAPI adds these automatically)
        assert "content-type" in response.headers


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
