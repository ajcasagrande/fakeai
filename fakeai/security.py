"""
Security hardening module for FakeAI.

This module provides comprehensive security features including input validation,
sanitization, API key hashing, and abuse detection.
"""

#  SPDX-License-Identifier: Apache-2.0

import hashlib
import re
import secrets
import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable

# Maximum payload sizes (in bytes)
MAX_REQUEST_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_STRING_LENGTH = 1024 * 1024  # 1 MB for individual strings
MAX_ARRAY_LENGTH = 10000  # Maximum array elements
MAX_MESSAGE_HISTORY = 1000  # Maximum conversation messages

# Injection attack patterns
INJECTION_PATTERNS = [
    # SQL Injection patterns
    r"(?i)(union\s+select|insert\s+into|delete\s+from|drop\s+table|create\s+table)",
    r"(?i)(exec\s*\(|execute\s+immediate|xp_cmdshell)",
    r"(--|;--|\*/|/\*)",
    # Command injection patterns
    r"(\||;|\$\(|`|&&|\|\|)",
    r"(?i)(bash|sh|cmd|powershell|eval|system|exec)\s*\(",
    # Path traversal patterns
    r"(\.\./|\.\.\\|%2e%2e%2f|%2e%2e\\)",
    # Script injection patterns
    r"(?i)(<script|javascript:|onerror=|onload=|<iframe)",
    # LDAP injection patterns
    r"(\*\)|&\||!\(|=\*\))",
    # XXE patterns
    r"(?i)(<!entity|<!doctype|system\s+['\"])",
]

# Compile patterns for performance
COMPILED_INJECTION_PATTERNS = [re.compile(pattern) for pattern in INJECTION_PATTERNS]


class SecurityException(Exception):
    """Base exception for security violations."""

    pass


class InputValidationError(SecurityException):
    """Raised when input validation fails."""

    pass


class InjectionAttackDetected(SecurityException):
    """Raised when potential injection attack is detected."""

    pass


class PayloadTooLarge(SecurityException):
    """Raised when payload exceeds size limits."""

    pass


class RateLimitAbuse(SecurityException):
    """Raised when rate limit abuse is detected."""

    pass


@dataclass
class ApiKeyInfo:
    """Information about an API key."""

    key_hash: str
    key_prefix: str  # First 8 characters for identification
    created_at: datetime
    expires_at: datetime | None = None
    last_used: datetime | None = None
    usage_count: int = 0
    is_active: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AbuseRecord:
    """Record of abuse attempts from an IP address."""

    failed_auth_attempts: int = 0
    injection_attempts: int = 0
    oversized_payloads: int = 0
    rate_limit_violations: int = 0
    last_violation_time: float = 0.0
    ban_until: float = 0.0

    def get_total_violations(self) -> int:
        """Get total number of violations."""
        return (
            self.failed_auth_attempts
            + self.injection_attempts
            + self.oversized_payloads
            + self.rate_limit_violations
        )


class InputValidator:
    """Validates and sanitizes user inputs."""

    @staticmethod
    def sanitize_string(value: str, max_length: int = MAX_STRING_LENGTH) -> str:
        """
        Sanitize a string value.

        Args:
            value: String to sanitize
            max_length: Maximum allowed length

        Returns:
            Sanitized string

        Raises:
            InputValidationError: If validation fails
        """
        if not isinstance(value, str):
            raise InputValidationError(f"Expected string, got {type(value).__name__}")

        if len(value) > max_length:
            raise InputValidationError(
                f"String length {len(value)} exceeds maximum {max_length}"
            )

        # Check for null bytes
        if "\x00" in value:
            raise InputValidationError("String contains null bytes")

        # Check for injection patterns
        for pattern in COMPILED_INJECTION_PATTERNS:
            if pattern.search(value):
                raise InjectionAttackDetected(
                    f"Potential injection attack detected: {pattern.pattern}"
                )

        # Remove control characters except newlines, tabs, and carriage returns
        sanitized = "".join(char for char in value if char >= " " or char in "\n\t\r")

        return sanitized

    @staticmethod
    def validate_array(
        value: list,
        max_length: int = MAX_ARRAY_LENGTH,
        item_validator: Callable | None = None,
    ) -> list:
        """
        Validate an array.

        Args:
            value: Array to validate
            max_length: Maximum array length
            item_validator: Optional function to validate each item

        Returns:
            Validated array

        Raises:
            InputValidationError: If validation fails
        """
        if not isinstance(value, list):
            raise InputValidationError(f"Expected list, got {type(value).__name__}")

        if len(value) > max_length:
            raise InputValidationError(
                f"Array length {len(value)} exceeds maximum {max_length}"
            )

        if item_validator:
            return [item_validator(item) for item in value]

        return value

    @staticmethod
    def validate_dict(
        value: dict,
        allowed_keys: set[str] | None = None,
        key_validator: Callable | None = None,
        value_validator: Callable | None = None,
    ) -> dict:
        """
        Validate a dictionary.

        Args:
            value: Dictionary to validate
            allowed_keys: Set of allowed keys (None for any)
            key_validator: Optional function to validate keys
            value_validator: Optional function to validate values

        Returns:
            Validated dictionary

        Raises:
            InputValidationError: If validation fails
        """
        if not isinstance(value, dict):
            raise InputValidationError(f"Expected dict, got {type(value).__name__}")

        result = {}
        for k, v in value.items():
            # Validate key
            if allowed_keys and k not in allowed_keys:
                raise InputValidationError(f"Unexpected key: {k}")

            if key_validator:
                k = key_validator(k)

            # Validate value
            if value_validator:
                v = value_validator(v)

            result[k] = v

        return result

    @staticmethod
    def validate_payload_size(payload: bytes, max_size: int = MAX_REQUEST_SIZE) -> None:
        """
        Validate payload size.

        Args:
            payload: Payload bytes
            max_size: Maximum allowed size

        Raises:
            PayloadTooLarge: If payload exceeds size limit
        """
        size = len(payload)
        if size > max_size:
            raise PayloadTooLarge(
                f"Payload size {size} bytes exceeds maximum {max_size} bytes"
            )


class ApiKeyManager:
    """
    Manages API keys with secure hashing and rotation support.

    Uses singleton pattern to ensure consistent key management across the application.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """Ensure only one instance exists (singleton pattern)."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ApiKeyManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        """Initialize the API key manager (only once)."""
        if self._initialized:
            return

        # Hash -> ApiKeyInfo mapping
        self._keys: dict[str, ApiKeyInfo] = {}

        # Prefix -> Hash mapping for fast lookups
        self._prefix_map: dict[str, str] = {}

        self._data_lock = threading.Lock()
        self._initialized = True

    @staticmethod
    def _hash_key(api_key: str) -> str:
        """
        Hash an API key using SHA-256.

        Args:
            api_key: The API key to hash

        Returns:
            Hex-encoded hash
        """
        return hashlib.sha256(api_key.encode()).hexdigest()

    @staticmethod
    def _get_prefix(api_key: str) -> str:
        """
        Get the first 8 characters of an API key for identification.

        Args:
            api_key: The API key

        Returns:
            First 8 characters
        """
        return api_key[:8] if len(api_key) >= 8 else api_key

    def add_key(
        self,
        api_key: str,
        expires_at: datetime | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """
        Add an API key to the manager.

        Args:
            api_key: The API key to add
            expires_at: Optional expiration datetime
            metadata: Optional metadata dictionary

        Returns:
            The key hash
        """
        key_hash = self._hash_key(api_key)
        key_prefix = self._get_prefix(api_key)

        with self._data_lock:
            if key_hash in self._keys:
                # Key already exists, update it
                info = self._keys[key_hash]
                if expires_at:
                    info.expires_at = expires_at
                if metadata:
                    info.metadata.update(metadata)
                return key_hash

            # Create new key info
            info = ApiKeyInfo(
                key_hash=key_hash,
                key_prefix=key_prefix,
                created_at=datetime.now(),
                expires_at=expires_at,
                metadata=metadata or {},
            )

            self._keys[key_hash] = info
            self._prefix_map[key_prefix] = key_hash

        return key_hash

    def verify_key(self, api_key: str) -> bool:
        """
        Verify an API key.

        Args:
            api_key: The API key to verify

        Returns:
            True if valid and active, False otherwise
        """
        key_hash = self._hash_key(api_key)

        with self._data_lock:
            if key_hash not in self._keys:
                return False

            info = self._keys[key_hash]

            # Check if key is active
            if not info.is_active:
                return False

            # Check if key is expired
            if info.expires_at and datetime.now() > info.expires_at:
                info.is_active = False
                return False

            # Update usage tracking
            info.last_used = datetime.now()
            info.usage_count += 1

            return True

    def revoke_key(self, api_key: str) -> bool:
        """
        Revoke an API key.

        Args:
            api_key: The API key to revoke

        Returns:
            True if key was revoked, False if not found
        """
        key_hash = self._hash_key(api_key)

        with self._data_lock:
            if key_hash not in self._keys:
                return False

            self._keys[key_hash].is_active = False
            return True

    def get_key_info(self, api_key: str) -> ApiKeyInfo | None:
        """
        Get information about an API key.

        Args:
            api_key: The API key

        Returns:
            ApiKeyInfo or None if not found
        """
        key_hash = self._hash_key(api_key)

        with self._data_lock:
            return self._keys.get(key_hash)

    def list_keys(self) -> list[ApiKeyInfo]:
        """
        List all API keys.

        Returns:
            List of ApiKeyInfo objects
        """
        with self._data_lock:
            return list(self._keys.values())

    def cleanup_expired(self) -> int:
        """
        Remove expired keys from storage.

        Returns:
            Number of keys removed
        """
        now = datetime.now()
        removed = 0

        with self._data_lock:
            expired_hashes = [
                key_hash
                for key_hash, info in self._keys.items()
                if info.expires_at and now > info.expires_at
            ]

            for key_hash in expired_hashes:
                info = self._keys.pop(key_hash)
                self._prefix_map.pop(info.key_prefix, None)
                removed += 1

        return removed


class AbuseDetector:
    """
    Detects and prevents abuse patterns including DDoS attempts,
    credential stuffing, and repeated violations.

    Uses singleton pattern for consistent abuse tracking across the application.
    """

    _instance = None
    _lock = threading.Lock()

    # Thresholds for automatic banning
    FAILED_AUTH_THRESHOLD = 5
    INJECTION_THRESHOLD = 3
    OVERSIZED_THRESHOLD = 10
    RATE_LIMIT_THRESHOLD = 20

    # Ban durations (seconds)
    TEMPORARY_BAN_DURATION = 300  # 5 minutes
    EXTENDED_BAN_DURATION = 3600  # 1 hour
    LONG_BAN_DURATION = 86400  # 24 hours

    def __new__(cls):
        """Ensure only one instance exists (singleton pattern)."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(AbuseDetector, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        """Initialize the abuse detector (only once)."""
        if self._initialized:
            return

        # IP address -> AbuseRecord mapping
        self._records: dict[str, AbuseRecord] = defaultdict(AbuseRecord)

        self._data_lock = threading.Lock()
        self._initialized = True

    def is_banned(self, ip_address: str) -> tuple[bool, float]:
        """
        Check if an IP address is currently banned.

        Args:
            ip_address: The IP address to check

        Returns:
            Tuple of (is_banned, seconds_until_unban)
        """
        with self._data_lock:
            record = self._records[ip_address]
            current_time = time.time()

            if record.ban_until > current_time:
                return True, record.ban_until - current_time

            return False, 0.0

    def record_failed_auth(self, ip_address: str) -> None:
        """
        Record a failed authentication attempt.

        Args:
            ip_address: The IP address
        """
        with self._data_lock:
            record = self._records[ip_address]
            record.failed_auth_attempts += 1
            record.last_violation_time = time.time()

            self._check_and_ban(ip_address, record)

    def record_injection_attempt(self, ip_address: str) -> None:
        """
        Record an injection attack attempt.

        Args:
            ip_address: The IP address
        """
        with self._data_lock:
            record = self._records[ip_address]
            record.injection_attempts += 1
            record.last_violation_time = time.time()

            # Injection attempts are serious - ban immediately after threshold
            if record.injection_attempts >= self.INJECTION_THRESHOLD:
                record.ban_until = time.time() + self.EXTENDED_BAN_DURATION

    def record_oversized_payload(self, ip_address: str) -> None:
        """
        Record an oversized payload attempt.

        Args:
            ip_address: The IP address
        """
        with self._data_lock:
            record = self._records[ip_address]
            record.oversized_payloads += 1
            record.last_violation_time = time.time()

            self._check_and_ban(ip_address, record)

    def record_rate_limit_violation(self, ip_address: str) -> None:
        """
        Record a rate limit violation.

        Args:
            ip_address: The IP address
        """
        with self._data_lock:
            record = self._records[ip_address]
            record.rate_limit_violations += 1
            record.last_violation_time = time.time()

            self._check_and_ban(ip_address, record)

    def _check_and_ban(self, ip_address: str, record: AbuseRecord) -> None:
        """
        Check if an IP should be banned based on violation counts.

        Args:
            ip_address: The IP address
            record: The abuse record
        """
        total_violations = record.get_total_violations()

        # Progressive ban durations
        if total_violations >= 50:
            record.ban_until = time.time() + self.LONG_BAN_DURATION
        elif total_violations >= 30:
            record.ban_until = time.time() + self.EXTENDED_BAN_DURATION
        elif total_violations >= 10:
            record.ban_until = time.time() + self.TEMPORARY_BAN_DURATION
        elif record.failed_auth_attempts >= self.FAILED_AUTH_THRESHOLD:
            record.ban_until = time.time() + self.TEMPORARY_BAN_DURATION
        elif record.rate_limit_violations >= self.RATE_LIMIT_THRESHOLD:
            record.ban_until = time.time() + self.TEMPORARY_BAN_DURATION

    def get_record(self, ip_address: str) -> AbuseRecord:
        """
        Get abuse record for an IP address.

        Args:
            ip_address: The IP address

        Returns:
            AbuseRecord
        """
        with self._data_lock:
            return self._records[ip_address]

    def reset_record(self, ip_address: str) -> None:
        """
        Reset abuse record for an IP address.

        Args:
            ip_address: The IP address
        """
        with self._data_lock:
            if ip_address in self._records:
                del self._records[ip_address]

    def cleanup_old_records(self, max_age_seconds: int = 86400) -> int:
        """
        Clean up old abuse records.

        Args:
            max_age_seconds: Maximum age of records to keep

        Returns:
            Number of records removed
        """
        current_time = time.time()
        cutoff_time = current_time - max_age_seconds
        removed = 0

        with self._data_lock:
            expired_ips = [
                ip
                for ip, record in self._records.items()
                if record.last_violation_time < cutoff_time
                and record.ban_until < current_time
            ]

            for ip in expired_ips:
                del self._records[ip]
                removed += 1

        return removed


def generate_api_key(prefix: str = "sk-fake") -> str:
    """
    Generate a secure random API key.

    Args:
        prefix: Key prefix (default: sk-fake)

    Returns:
        Generated API key
    """
    random_bytes = secrets.token_bytes(32)
    random_hex = random_bytes.hex()
    return f"{prefix}-{random_hex}"
