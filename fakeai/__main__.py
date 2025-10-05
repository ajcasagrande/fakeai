#!/usr/bin/env python3
"""
FakeAI - Package entry point for python -m fakeai

This module enables running FakeAI using `python -m fakeai`.
"""
#  SPDX-License-Identifier: Apache-2.0

import sys

from fakeai.cli import main

if __name__ == "__main__":
    sys.exit(main())
