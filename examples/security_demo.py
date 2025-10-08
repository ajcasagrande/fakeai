#!/usr/bin/env python3
"""
Security Features Demo for FakeAI

This script demonstrates various security features including:
- API key management (hashing, expiration, rotation)
- Input validation and injection detection
- Abuse detection and IP banning
- Rate limiting
"""
#  SPDX-License-Identifier: Apache-2.0

from datetime import datetime, timedelta

from fakeai.security import (
    AbuseDetector,
    ApiKeyManager,
    InjectionAttackDetected,
    InputValidator,
    PayloadTooLarge,
    generate_api_key,
)


def demo_api_key_management():
    """Demo API key management features."""
    print("\n" + "=" * 70)
    print("API Key Management Demo")
    print("=" * 70)

    manager = ApiKeyManager()

    # Generate secure API keys
    print("\n1. Generating secure API keys:")
    keys = []
    for i in range(3):
        key = generate_api_key()
        keys.append(key)
        print(f"   Generated: {key[:20]}... (64 chars total)")

    # Add keys to manager with hashing
    print("\n2. Adding keys with hashing:")
    for key in keys:
        key_hash = manager.add_key(key)
        print(f"   Key hash: {key_hash[:16]}... (SHA-256)")

    # Verify keys
    print("\n3. Verifying keys:")
    for key in keys:
        is_valid = manager.verify_key(key)
        print(f"   Key {key[:16]}... is valid: {is_valid}")

    # Invalid key test
    invalid_key = generate_api_key()
    is_valid = manager.verify_key(invalid_key)
    print(f"   Invalid key is valid: {is_valid}")

    # Key with expiration
    print("\n4. Adding key with expiration:")
    expiring_key = generate_api_key()
    expires_at = datetime.now() + timedelta(hours=1)
    manager.add_key(expiring_key, expires_at=expires_at)
    print(f"   Key expires at: {expires_at.isoformat()}")

    # Check key info
    info = manager.get_key_info(expiring_key)
    if info:
        print(f"   Created: {info.created_at.isoformat()}")
        print(f"   Expires: {info.expires_at.isoformat()}")
        print(f"   Usage count: {info.usage_count}")

    # Revoke a key
    print("\n5. Revoking a key:")
    key_to_revoke = keys[0]
    success = manager.revoke_key(key_to_revoke)
    print(f"   Revocation successful: {success}")
    is_valid = manager.verify_key(key_to_revoke)
    print(f"   Revoked key is valid: {is_valid}")

    # List all keys
    print("\n6. Listing all keys:")
    all_keys = manager.list_keys()
    print(f"   Total keys: {len(all_keys)}")
    for info in all_keys[:3]:  # Show first 3
        print(f"   - Prefix: {info.key_prefix}, Active: {info.is_active}")


def demo_input_validation():
    """Demo input validation and sanitization."""
    print("\n" + "=" * 70)
    print("Input Validation Demo")
    print("=" * 70)

    validator = InputValidator()

    # Valid string
    print("\n1. Validating normal text:")
    normal_text = "Hello, world! This is a normal message."
    try:
        result = validator.sanitize_string(normal_text)
        print(f"   ✓ Valid: {result[:50]}")
    except Exception as e:
        print(f"   ✗ Error: {e}")

    # String with control characters
    print("\n2. String with null bytes:")
    bad_text = "Hello\x00World"
    try:
        result = validator.sanitize_string(bad_text)
        print(f"   ✓ Valid: {result}")
    except Exception as e:
        print(f"   ✗ Blocked: {type(e).__name__}")

    # Oversized string
    print("\n3. Oversized string:")
    huge_text = "a" * (1024 * 1024 + 1)
    try:
        result = validator.sanitize_string(huge_text)
        print(f"   ✓ Valid: {len(result)} chars")
    except Exception as e:
        print(f"   ✗ Blocked: {type(e).__name__}")

    # Array validation
    print("\n4. Array validation:")
    normal_array = [1, 2, 3, 4, 5]
    try:
        result = validator.validate_array(normal_array)
        print(f"   ✓ Valid array: {len(result)} items")
    except Exception as e:
        print(f"   ✗ Error: {e}")

    # Oversized array
    huge_array = list(range(10001))
    try:
        result = validator.validate_array(huge_array)
        print(f"   ✓ Valid array: {len(result)} items")
    except Exception as e:
        print(f"   ✗ Blocked oversized array: {type(e).__name__}")

    # Payload size validation
    print("\n5. Payload size validation:")
    normal_payload = b"a" * 1024
    try:
        validator.validate_payload_size(normal_payload)
        print(f"   ✓ Valid payload: {len(normal_payload)} bytes")
    except Exception as e:
        print(f"   ✗ Error: {e}")

    huge_payload = b"a" * (10 * 1024 * 1024 + 1)
    try:
        validator.validate_payload_size(huge_payload)
        print(f"   ✓ Valid payload: {len(huge_payload)} bytes")
    except PayloadTooLarge as e:
        print(f"   ✗ Blocked oversized payload: {len(huge_payload)} bytes")


def demo_injection_detection():
    """Demo injection attack detection."""
    print("\n" + "=" * 70)
    print("Injection Attack Detection Demo")
    print("=" * 70)

    validator = InputValidator()

    # Test cases: (name, input, should_block)
    test_cases = [
        ("Normal text", "What is the weather today?", False),
        ("SQL Injection", "'; DROP TABLE users; --", True),
        ("UNION SELECT", "admin' UNION SELECT * FROM passwords", True),
        ("Command injection", "; ls -la | cat /etc/passwd", True),
        ("Script injection", "<script>alert('XSS')</script>", True),
        ("Path traversal", "../../etc/passwd", True),
        ("LDAP injection", "*)(uid=*))(|(uid=*", True),
        ("Normal URL", "https://example.com/api/data", False),
        ("Email address", "user@example.com", False),
    ]

    print("\nTesting various inputs:")
    for name, text, should_block in test_cases:
        try:
            result = validator.sanitize_string(text)
            if should_block:
                print(f"   ✗ {name}: Should have been blocked!")
            else:
                print(f"   ✓ {name}: Allowed")
        except InjectionAttackDetected:
            if should_block:
                print(f"   ✓ {name}: Blocked (injection detected)")
            else:
                print(f"   ✗ {name}: False positive!")
        except Exception as e:
            print(f"   ? {name}: Unexpected error: {type(e).__name__}")


def demo_abuse_detection():
    """Demo abuse detection and IP banning."""
    print("\n" + "=" * 70)
    print("Abuse Detection Demo")
    print("=" * 70)

    detector = AbuseDetector()

    # Test IP addresses
    ips = ["192.168.1.100", "192.168.1.101", "192.168.1.102"]

    # Failed auth attempts
    print("\n1. Failed authentication attempts:")
    ip = ips[0]
    for i in range(6):
        detector.record_failed_auth(ip)
        is_banned, ban_time = detector.is_banned(ip)
        if is_banned:
            print(f"   Attempt {i+1}: IP {ip} banned for {int(ban_time)}s")
            break
        else:
            print(f"   Attempt {i+1}: IP {ip} not yet banned")

    # Injection attempts (lower threshold)
    print("\n2. Injection attack attempts:")
    ip = ips[1]
    for i in range(4):
        detector.record_injection_attempt(ip)
        is_banned, ban_time = detector.is_banned(ip)
        if is_banned:
            print(f"   Attempt {i+1}: IP {ip} banned for {int(ban_time)}s")
            break
        else:
            print(f"   Attempt {i+1}: IP {ip} not yet banned")

    # Rate limit violations
    print("\n3. Rate limit violations:")
    ip = ips[2]
    for i in range(21):
        detector.record_rate_limit_violation(ip)
        if i % 5 == 0:
            is_banned, ban_time = detector.is_banned(ip)
            if is_banned:
                print(f"   Violation {i+1}: IP {ip} banned for {int(ban_time)}s")
            else:
                print(f"   Violation {i+1}: IP {ip} not yet banned")

    # Check abuse records
    print("\n4. Abuse records:")
    for ip in ips:
        record = detector.get_record(ip)
        is_banned, ban_time = detector.is_banned(ip)
        print(f"   IP {ip}:")
        print(f"      Total violations: {record.get_total_violations()}")
        print(f"      Banned: {is_banned} ({int(ban_time)}s remaining)")

    # Reset a record
    print("\n5. Resetting abuse record:")
    ip = ips[0]
    print(
        f"   Before reset: violations = {detector.get_record(ip).get_total_violations()}"
    )
    detector.reset_record(ip)
    print(
        f"   After reset: violations = {detector.get_record(ip).get_total_violations()}"
    )


def demo_security_scenarios():
    """Demo real-world security scenarios."""
    print("\n" + "=" * 70)
    print("Real-World Security Scenarios")
    print("=" * 70)

    manager = ApiKeyManager()
    validator = InputValidator()
    detector = AbuseDetector()

    # Scenario 1: Key rotation
    print("\n1. Key Rotation Scenario:")
    old_key = generate_api_key()
    new_key = generate_api_key()

    print("   Adding old key (expires in 1 day)...")
    expires_at = datetime.now() + timedelta(days=1)
    manager.add_key(old_key, expires_at=expires_at)

    print("   Adding new key (no expiration)...")
    manager.add_key(new_key)

    print("   Verifying both keys work...")
    print(f"   Old key valid: {manager.verify_key(old_key)}")
    print(f"   New key valid: {manager.verify_key(new_key)}")

    print("   Revoking old key...")
    manager.revoke_key(old_key)

    print("   After rotation:")
    print(f"   Old key valid: {manager.verify_key(old_key)}")
    print(f"   New key valid: {manager.verify_key(new_key)}")

    # Scenario 2: Brute force attack
    print("\n2. Brute Force Attack Scenario:")
    attacker_ip = "10.0.0.50"
    print(f"   Attacker IP: {attacker_ip}")
    print("   Attempting to guess API keys...")

    for attempt in range(6):
        fake_key = f"sk-fake-attempt-{attempt}"
        is_valid = manager.verify_key(fake_key)

        if not is_valid:
            detector.record_failed_auth(attacker_ip)

        is_banned, ban_time = detector.is_banned(attacker_ip)
        print(f"   Attempt {attempt+1}: Failed. Banned: {is_banned}")

        if is_banned:
            print(f"   Attacker banned for {int(ban_time)} seconds!")
            break

    # Scenario 3: Injection attack followed by DDoS
    print("\n3. Multi-Stage Attack Scenario:")
    attacker_ip = "10.0.0.51"

    print("   Stage 1: Injection attack...")
    for i in range(3):
        detector.record_injection_attempt(attacker_ip)
        print(f"   Injection attempt {i+1}")

    is_banned, ban_time = detector.is_banned(attacker_ip)
    print(f"   After injection attempts - Banned: {is_banned}")

    if is_banned:
        print(f"   Attacker banned for {int(ban_time)} seconds")
        print("   DDoS attack prevented by ban!")


def main():
    """Run all security demos."""
    print("\n" + "=" * 70)
    print("FakeAI Security Features Demo")
    print("=" * 70)

    try:
        demo_api_key_management()
        demo_input_validation()
        demo_injection_detection()
        demo_abuse_detection()
        demo_security_scenarios()

        print("\n" + "=" * 70)
        print("Demo Complete!")
        print("=" * 70)
        print("\nAll security features demonstrated successfully.")
        print("For more information, see SECURITY.md")

    except Exception as e:
        print(f"\nError during demo: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
