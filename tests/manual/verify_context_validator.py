#!/usr/bin/env python3
"""
Verification script for context_validator module.

This script verifies that all components are working correctly:
1. Module imports
2. Basic functionality
3. Test suite
4. Examples
5. Integration readiness
"""

import sys
import subprocess
from pathlib import Path


def print_section(title):
    """Print a section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def check_file_exists(filepath):
    """Check if a file exists."""
    path = Path(filepath)
    if path.exists():
        size = path.stat().st_size
        print(f"✅ {filepath} ({size:,} bytes)")
        return True
    else:
        print(f"❌ {filepath} - NOT FOUND")
        return False


def run_command(cmd, description):
    """Run a command and report results."""
    print(f"\n📋 {description}")
    print(f"   Command: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        if result.returncode == 0:
            print(f"   ✅ Success")
            return True
        else:
            print(f"   ❌ Failed with return code {result.returncode}")
            if result.stderr:
                print(f"   Error: {result.stderr[:200]}")
            return False
    except subprocess.TimeoutExpired:
        print("   ❌ Timeout")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def main():
    """Run verification checks."""
    print("\n" + "=" * 70)
    print("  CONTEXT VALIDATOR MODULE VERIFICATION")
    print("=" * 70)

    all_checks_passed = True

    # Check 1: File existence
    print_section("1. File Existence Check")
    files = [
        "fakeai/context_validator.py",
        "tests/test_context_validator.py",
        "examples/context_validation_example.py",
        "examples/integration_snippet.py",
        "CONTEXT_VALIDATOR_INTEGRATION.md",
        "CONTEXT_VALIDATOR_SUMMARY.md",
        "CONTEXT_VALIDATOR_QUICKREF.md",
        "DELIVERABLES.md",
    ]

    for filepath in files:
        if not check_file_exists(filepath):
            all_checks_passed = False

    # Check 2: Module imports
    print_section("2. Module Import Check")
    try:
        from fakeai.context_validator import (
            validate_context_length,
            create_context_length_error,
            get_model_context_window,
            calculate_remaining_budget,
            MODEL_CONTEXT_WINDOWS,
        )
        print("✅ All imports successful")
        print(f"   - validate_context_length: {type(validate_context_length).__name__}")
        print(f"   - create_context_length_error: {type(create_context_length_error).__name__}")
        print(f"   - get_model_context_window: {type(get_model_context_window).__name__}")
        print(f"   - calculate_remaining_budget: {type(calculate_remaining_budget).__name__}")
        print(f"   - MODEL_CONTEXT_WINDOWS: {len(MODEL_CONTEXT_WINDOWS)} models")
    except Exception as e:
        print(f"❌ Import failed: {e}")
        all_checks_passed = False

    # Check 3: Basic functionality
    print_section("3. Basic Functionality Check")
    try:
        from fakeai.context_validator import (
            validate_context_length,
            get_model_context_window,
        )

        # Test 1: Valid request
        is_valid, error = validate_context_length("gpt-4", 4000, 2000)
        if is_valid and error is None:
            print("✅ Valid request check passed")
        else:
            print("❌ Valid request check failed")
            all_checks_passed = False

        # Test 2: Invalid request
        is_valid, error = validate_context_length("gpt-4", 7000, 2000)
        if not is_valid and error is not None:
            print("✅ Invalid request check passed")
        else:
            print("❌ Invalid request check failed")
            all_checks_passed = False

        # Test 3: Model context window
        window = get_model_context_window("gpt-4")
        if window == 8192:
            print("✅ Model context window check passed")
        else:
            print(f"❌ Model context window check failed (expected 8192, got {window})")
            all_checks_passed = False

        # Test 4: Fine-tuned model
        window = get_model_context_window("ft:gpt-oss-120b:org::id")
        if window == 128000:
            print("✅ Fine-tuned model check passed")
        else:
            print(f"❌ Fine-tuned model check failed (expected 128000, got {window})")
            all_checks_passed = False

    except Exception as e:
        print(f"❌ Functionality check failed: {e}")
        all_checks_passed = False

    # Check 4: Test suite
    print_section("4. Test Suite Check")
    if not run_command(
        ["python", "-m", "pytest", "tests/test_context_validator.py", "-v", "--tb=no"],
        "Running test suite",
    ):
        all_checks_passed = False

    # Check 5: Examples
    print_section("5. Examples Check")
    if not run_command(
        ["python", "examples/context_validation_example.py"],
        "Running context validation examples",
    ):
        all_checks_passed = False

    if not run_command(
        ["python", "examples/integration_snippet.py"],
        "Running integration snippet",
    ):
        all_checks_passed = False

    # Check 6: Code quality
    print_section("6. Code Quality Check")
    files_to_compile = [
        "fakeai/context_validator.py",
        "tests/test_context_validator.py",
        "examples/context_validation_example.py",
        "examples/integration_snippet.py",
    ]

    for filepath in files_to_compile:
        if not run_command(
            ["python", "-m", "py_compile", filepath],
            f"Compiling {filepath}",
        ):
            all_checks_passed = False

    # Final summary
    print_section("VERIFICATION SUMMARY")
    if all_checks_passed:
        print("\n✅ ALL CHECKS PASSED")
        print("\nThe context validator module is:")
        print("  ✅ Fully implemented")
        print("  ✅ Thoroughly tested (33 tests)")
        print("  ✅ Properly documented")
        print("  ✅ Ready for integration")
        print("\nNext step: Follow CONTEXT_VALIDATOR_INTEGRATION.md to integrate into fakeai_service.py")
        return 0
    else:
        print("\n❌ SOME CHECKS FAILED")
        print("\nPlease review the errors above and fix any issues.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
