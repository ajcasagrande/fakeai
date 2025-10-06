#!/usr/bin/env python3
"""
Fix for FakeAI streaming implementation.

This script modifies the key components of the FakeAI server to fix streaming issues.
"""
#  SPDX-License-Identifier: Apache-2.0

import os
import sys


def fix_app_py():
    """Fix the app.py file."""
    app_py_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "fakeai", "app.py"
    )
    with open(app_py_path, "r") as f:
        content = f.read()

    # Fix the response_model for chat completions
    if "response_model=ChatCompletionRequest" in content:
        content = content.replace(
            "response_model=ChatCompletionRequest", "response_model=None"
        )
        print(
            "Fixed: Changed response_model=ChatCompletionRequest to response_model=None in app.py"
        )
    else:
        print("No issue found with response_model in app.py or already fixed")

    # Write the fixed content back
    with open(app_py_path, "w") as f:
        f.write(content)


def fix_service_py():
    """Fix the fakeai_service.py file."""
    service_py_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "fakeai", "fakeai_service.py"
    )
    with open(service_py_path, "r") as f:
        content = f.read()

    # Fix the stream parameter in create_chat_completion_stream
    stream_text = "stream=False,"
    stream_replacement = "stream=True,  # Make sure to set stream=True"

    if stream_text in content and stream_replacement not in content:
        content = content.replace(stream_text, stream_replacement)
        print(
            "Fixed: Changed stream=False to stream=True in create_chat_completion_stream"
        )
    else:
        print(
            "No issue found with stream parameter in create_chat_completion_stream or already fixed"
        )

    # Write the fixed content back
    with open(service_py_path, "w") as f:
        f.write(content)


def main():
    """Run the fixes."""
    print("Applying fixes to FakeAI streaming implementation...")
    fix_app_py()
    fix_service_py()
    print("\nFixes applied. Please restart your FakeAI server.")
    print('You can do this by running: pkill -f "fakeai.cli" && python -m fakeai.cli')


if __name__ == "__main__":
    main()
