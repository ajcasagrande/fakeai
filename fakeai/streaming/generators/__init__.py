"""
Streaming generators for different response types.

This module provides specialized generators for different streaming scenarios:
- Chat completions (OpenAI chat API)
- Text completions (legacy completion API)
- Audio streaming
- Realtime bidirectional streaming
"""

#  SPDX-License-Identifier: Apache-2.0

from fakeai.streaming.generators.chat_stream import ChatStreamingGenerator
from fakeai.streaming.generators.completion_stream import CompletionStreamingGenerator

__all__ = [
    "ChatStreamingGenerator",
    "CompletionStreamingGenerator",
]
