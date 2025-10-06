"""
Tests for SSE and other formatters.
"""

#  SPDX-License-Identifier: Apache-2.0

import json

import pytest

from fakeai.streaming.base import ErrorSeverity, StreamChunk, StreamError
from fakeai.streaming.sse import (
    JSONLinesFormatter,
    OpenAIChatFormatter,
    OpenAICompletionFormatter,
    PlainTextFormatter,
    SSEFormatter,
)


class TestSSEFormatter:
    """Test SSEFormatter class."""

    def test_format_simple_chunk(self):
        """Test formatting a simple chunk."""
        chunk = StreamChunk(
            chunk_id="chunk-1",
            sequence_number=0,
            data={"message": "Hello"},
        )

        formatted = SSEFormatter.format(chunk)

        assert formatted.startswith("data: ")
        assert formatted.endswith("\n\n")
        assert "Hello" in formatted

    def test_format_dict_data(self):
        """Test formatting chunk with dictionary data."""
        chunk = StreamChunk(
            chunk_id="chunk-1",
            sequence_number=0,
            data={"content": "Hello", "role": "assistant"},
        )

        formatted = SSEFormatter.format(chunk)

        # Verify JSON is embedded
        assert "data: {" in formatted
        assert "content" in formatted
        assert "role" in formatted

    def test_format_with_event_type(self):
        """Test formatting with custom event type."""
        chunk = StreamChunk(
            chunk_id="chunk-1",
            sequence_number=0,
            data={"test": "data"},
            chunk_type="custom_event",
        )

        formatted = SSEFormatter.format(chunk)

        assert "event: custom_event" in formatted

    def test_format_error(self):
        """Test formatting an error."""
        error = StreamError(
            error_code="test_error",
            message="Test error message",
            severity=ErrorSeverity.ERROR,
        )

        formatted = SSEFormatter.format_error(error)

        assert "event: error" in formatted
        assert "test_error" in formatted
        assert "Test error message" in formatted

    def test_format_done(self):
        """Test formatting done signal."""
        formatted = SSEFormatter.format_done()

        assert formatted == "data: [DONE]\n\n"

    def test_format_custom_event(self):
        """Test formatting custom event."""
        formatted = SSEFormatter.format_custom_event(
            "progress",
            {"percent": 50},
        )

        assert "event: progress" in formatted
        assert "percent" in formatted


class TestJSONLinesFormatter:
    """Test JSONLinesFormatter class."""

    def test_format_chunk(self):
        """Test formatting a chunk as JSON line."""
        chunk = StreamChunk(
            chunk_id="chunk-1",
            sequence_number=0,
            data={"content": "Hello"},
        )

        formatted = JSONLinesFormatter.format(chunk)

        assert formatted.endswith("\n")
        parsed = json.loads(formatted.strip())

        assert parsed["sequence"] == 0
        assert parsed["data"]["content"] == "Hello"

    def test_format_with_metadata(self):
        """Test formatting chunk with metadata."""
        chunk = StreamChunk(
            chunk_id="chunk-1",
            sequence_number=5,
            data={"content": "Hello"},
            metadata={"model": "gpt-4o"},
        )

        formatted = JSONLinesFormatter.format(chunk)
        parsed = json.loads(formatted.strip())

        assert parsed["metadata"]["model"] == "gpt-4o"

    def test_format_first_last_flags(self):
        """Test formatting with first/last flags."""
        chunk = StreamChunk(
            chunk_id="chunk-1",
            sequence_number=0,
            data={"content": "Hello"},
            is_first=True,
            is_last=False,
        )

        formatted = JSONLinesFormatter.format(chunk)
        parsed = json.loads(formatted.strip())

        assert parsed["is_first"] is True
        assert "is_last" not in parsed  # Only included if True

    def test_format_error(self):
        """Test formatting error as JSON line."""
        error = StreamError(
            error_code="test_error",
            message="Error message",
            severity=ErrorSeverity.WARNING,
        )

        formatted = JSONLinesFormatter.format_error(error)
        parsed = json.loads(formatted.strip())

        assert parsed["type"] == "error"
        assert parsed["error"]["error_code"] == "test_error"

    def test_format_done(self):
        """Test formatting done signal as JSON line."""
        formatted = JSONLinesFormatter.format_done()
        parsed = json.loads(formatted.strip())

        assert parsed["type"] == "done"


class TestPlainTextFormatter:
    """Test PlainTextFormatter class."""

    def test_format_string_data(self):
        """Test formatting chunk with string data."""
        chunk = StreamChunk(
            chunk_id="chunk-1",
            sequence_number=0,
            data="Hello world",
        )

        formatted = PlainTextFormatter.format(chunk)

        assert formatted == "Hello world"

    def test_format_chat_delta(self):
        """Test formatting chat completion delta."""
        chunk = StreamChunk(
            chunk_id="chunk-1",
            sequence_number=0,
            data={
                "choices": [
                    {
                        "delta": {
                            "content": "Hello",
                        },
                    }
                ]
            },
        )

        formatted = PlainTextFormatter.format(chunk)

        assert formatted == "Hello"

    def test_format_completion_text(self):
        """Test formatting completion text."""
        chunk = StreamChunk(
            chunk_id="chunk-1",
            sequence_number=0,
            data={
                "choices": [
                    {
                        "text": "Hello",
                    }
                ]
            },
        )

        formatted = PlainTextFormatter.format(chunk)

        assert formatted == "Hello"

    def test_format_error(self):
        """Test formatting error as plain text."""
        error = StreamError(
            error_code="test_error",
            message="Something went wrong",
            severity=ErrorSeverity.ERROR,
        )

        formatted = PlainTextFormatter.format_error(error)

        assert "ERROR" in formatted
        assert "Something went wrong" in formatted

    def test_format_done(self):
        """Test formatting done signal (empty)."""
        formatted = PlainTextFormatter.format_done()

        assert formatted == ""


class TestOpenAIChatFormatter:
    """Test OpenAIChatFormatter class."""

    def test_format_chat_chunk(self):
        """Test formatting OpenAI chat chunk."""
        formatted = OpenAIChatFormatter.format_chat_chunk(
            chunk_id="chatcmpl-123",
            model="gpt-4o",
            created=1234567890,
            delta={"content": "Hello"},
            index=0,
        )

        assert formatted.startswith("data: ")
        assert formatted.endswith("\n\n")

        # Parse JSON
        json_str = formatted.replace("data: ", "").strip()
        parsed = json.loads(json_str)

        assert parsed["id"] == "chatcmpl-123"
        assert parsed["object"] == "chat.completion.chunk"
        assert parsed["model"] == "gpt-4o"
        assert parsed["choices"][0]["delta"]["content"] == "Hello"

    def test_format_chat_chunk_with_finish_reason(self):
        """Test formatting chat chunk with finish reason."""
        formatted = OpenAIChatFormatter.format_chat_chunk(
            chunk_id="chatcmpl-123",
            model="gpt-4o",
            created=1234567890,
            delta={},
            finish_reason="stop",
        )

        json_str = formatted.replace("data: ", "").strip()
        parsed = json.loads(json_str)

        assert parsed["choices"][0]["finish_reason"] == "stop"


class TestOpenAICompletionFormatter:
    """Test OpenAICompletionFormatter class."""

    def test_format_completion_chunk(self):
        """Test formatting OpenAI completion chunk."""
        formatted = OpenAICompletionFormatter.format_completion_chunk(
            chunk_id="cmpl-123",
            model="gpt-3.5-turbo-instruct",
            created=1234567890,
            text="Hello",
            index=0,
        )

        assert formatted.startswith("data: ")
        assert formatted.endswith("\n\n")

        # Parse JSON
        json_str = formatted.replace("data: ", "").strip()
        parsed = json.loads(json_str)

        assert parsed["id"] == "cmpl-123"
        assert parsed["object"] == "text_completion"
        assert parsed["model"] == "gpt-3.5-turbo-instruct"
        assert parsed["choices"][0]["text"] == "Hello"

    def test_format_completion_chunk_with_finish_reason(self):
        """Test formatting completion chunk with finish reason."""
        formatted = OpenAICompletionFormatter.format_completion_chunk(
            chunk_id="cmpl-123",
            model="gpt-3.5-turbo-instruct",
            created=1234567890,
            text="",
            finish_reason="length",
        )

        json_str = formatted.replace("data: ", "").strip()
        parsed = json.loads(json_str)

        assert parsed["choices"][0]["finish_reason"] == "length"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
