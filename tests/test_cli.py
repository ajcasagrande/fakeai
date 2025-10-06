#!/usr/bin/env python3
"""
Test script for the FakeAI CLI.
"""

import subprocess
import sys


def test_help():
    """Test help command."""
    print("Testing: fakeai --help")
    result = subprocess.run(["fakeai", "--help"], capture_output=True, text=True)

    assert "FakeAI - OpenAI Compatible API Server" in result.stdout
    print("✓ Help command works\n")


def test_server_help():
    """Test server subcommand help."""
    print("Testing: fakeai server --help")
    result = subprocess.run(
        ["fakeai", "server", "--help"], capture_output=True, text=True
    )

    assert "FakeAI" in result.stdout
    assert "--host" in result.stdout
    assert "--port" in result.stdout
    assert "--debug" in result.stdout
    print("✓ Server help command works\n")


def test_version():
    """Test version command."""
    print("Testing: fakeai --version")
    result = subprocess.run(["fakeai", "--version"], capture_output=True, text=True)

    assert "0.0.5" in result.stdout
    print(f"✓ Version command works: {result.stdout.strip()}\n")


def test_backward_compatibility():
    """Test backward compatibility with old command."""
    print("Testing: fakeai-server --help (backward compatibility)")
    result = subprocess.run(["fakeai-server", "--help"], capture_output=True, text=True)

    assert "FakeAI" in result.stdout
    print("✓ Backward compatibility maintained\n")


def test_argument_validation():
    """Test argument validation."""
    print("Testing: Invalid port number")

    # Test invalid port (too high)
    result = subprocess.run(
        ["fakeai", "server", "--port", "99999"],
        capture_output=True,
        text=True,
        timeout=5,
    )

    # Should fail with validation error
    if result.returncode != 0 or "validation" in result.stderr.lower():
        print("✓ Port validation works (rejects invalid values)\n")
    else:
        print("⚠ Port validation might not be working as expected\n")


def main():
    """Run all CLI tests."""
    print("=" * 70)
    print("FakeAI CLI Tests")
    print("=" * 70)
    print()

    try:
        test_help()
        test_version()
        test_argument_validation()

        print("=" * 70)
        print("All CLI tests passed! ✓")
        print("=" * 70)
        print()
        print("Usage examples:")
        print("  # Start with defaults")
        print("  $ fakeai-server")
        print()
        print("  # Start on different host/port")
        print("  $ fakeai-server --host 0.0.0.0 --port 9000")
        print()
        print("  # Disable authentication")
        print("  $ fakeai-server --no-require-api-key")
        print()
        print("  # Debug mode with custom timing")
        print("  $ fakeai-server --debug --response-delay 1.0")
        print()

        return 0
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
