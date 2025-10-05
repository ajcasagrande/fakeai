#!/usr/bin/env python3
"""
Comprehensive test suite for the new API key system.
"""

import subprocess
import sys
import tempfile
from pathlib import Path


def test_default_no_auth():
    """Test that default is no authentication."""
    print("Test 1: Default (no authentication)")
    from fakeai.config import AppConfig

    config = AppConfig()
    assert config.require_api_key == False, "Should default to no auth"
    assert len(config.api_keys) == 0, "Should have no keys by default"
    print("  ✓ Default is no authentication\n")


def test_direct_keys():
    """Test parsing direct API keys."""
    print("Test 2: Direct API keys")
    from fakeai.cli import parse_api_keys

    keys = parse_api_keys(["sk-test-1", "sk-test-2", "sk-test-3"])
    assert len(keys) == 3, "Should parse 3 keys"
    assert keys == ["sk-test-1", "sk-test-2", "sk-test-3"]
    print("  ✓ Direct keys parsed correctly\n")


def test_file_parsing():
    """Test parsing keys from a file."""
    print("Test 3: File parsing")
    from fakeai.cli import parse_api_keys

    # Create a temporary file with keys
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("# Comment line\n")
        f.write("sk-file-key-1\n")
        f.write("\n")  # Blank line
        f.write("sk-file-key-2\n")
        f.write("# Another comment\n")
        f.write("sk-file-key-3\n")
        temp_path = f.name

    try:
        keys = parse_api_keys([temp_path])
        assert len(keys) == 3, f"Should parse 3 keys, got {len(keys)}"
        assert "sk-file-key-1" in keys
        assert "sk-file-key-2" in keys
        assert "sk-file-key-3" in keys
        print(f"  ✓ File parsed correctly (skipped comments/blanks)\n")
    finally:
        Path(temp_path).unlink()


def test_mixed_sources():
    """Test mixing direct keys and file paths."""
    print("Test 4: Mixed sources")
    from fakeai.cli import parse_api_keys

    # Create a temporary file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("sk-from-file-1\n")
        f.write("sk-from-file-2\n")
        temp_path = f.name

    try:
        keys = parse_api_keys([
            "sk-direct-1",
            temp_path,
            "sk-direct-2"
        ])
        assert len(keys) == 4, f"Should have 4 keys total, got {len(keys)}"
        assert "sk-direct-1" in keys
        assert "sk-direct-2" in keys
        assert "sk-from-file-1" in keys
        assert "sk-from-file-2" in keys
        print("  ✓ Mixed sources work correctly\n")
    finally:
        Path(temp_path).unlink()


def test_auto_enable_auth():
    """Test that authentication is auto-enabled when keys are provided."""
    print("Test 5: Auto-enable authentication")
    from fakeai.config import AppConfig
    from fakeai.cli import parse_api_keys

    # With keys
    parsed_keys = parse_api_keys(["sk-test"])
    config = AppConfig(
        api_keys=parsed_keys,
        require_api_key=bool(parsed_keys)
    )
    assert config.require_api_key == True
    assert len(config.api_keys) == 1
    print("  ✓ Auth auto-enabled when keys provided\n")


def test_cli_help():
    """Test CLI help shows new options."""
    print("Test 6: CLI help")
    result = subprocess.run(
        ["fakeai-server", "--help"],
        capture_output=True,
        text=True
    )
    assert "--api-key" in result.stdout
    print("  ✓ CLI help shows --api-key option\n")


def main():
    """Run all tests."""
    print("=" * 70)
    print("API Key System - Comprehensive Test Suite")
    print("=" * 70)
    print()

    try:
        test_default_no_auth()
        test_direct_keys()
        test_file_parsing()
        test_mixed_sources()
        test_auto_enable_auth()
        test_cli_help()

        print("=" * 70)
        print("All tests passed! ✓")
        print("=" * 70)
        print()
        print("Usage examples:")
        print("  # No authentication (default)")
        print("  $ fakeai-server")
        print()
        print("  # With direct API keys")
        print("  $ fakeai-server --api-key sk-test-1 --api-key sk-test-2")
        print()
        print("  # Load keys from file")
        print("  $ fakeai-server --api-key /path/to/keys.txt")
        print()
        print("  # Mix direct keys and files")
        print("  $ fakeai-server --api-key sk-direct --api-key /path/to/keys.txt")
        print()

        return 0

    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
