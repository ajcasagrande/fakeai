"""
FakeAI - OpenAI Compatible API Server

A fully-featured FastAPI implementation that mimics the OpenAI API.
It supports all endpoints and features of the official OpenAI API while returning
simulated responses instead of performing actual inference.
"""

#  SPDX-License-Identifier: Apache-2.0

__version__ = "0.0.4"

__all__ = [
    "app",
    "AppConfig",
    "FakeAIService",
    "run_server",
]
# Make key modules available at the package level for convenience

from fakeai.app import app as app
from fakeai.config import AppConfig as AppConfig
from fakeai.fakeai_service import FakeAIService as FakeAIService
from fakeai.cli import main as run_server
