#!/usr/bin/env python3
"""
Run script for the FakeAI OpenAI compatible server.

This script provides a simple way to run the FakeAI server directly
from the source directory during development.
"""
#  SPDX-License-Identifier: Apache-2.0

import sys

from fakeai.cli import main

if __name__ == "__main__":
    sys.exit(main())
