"""
Server-Sent Events (SSE) and other output formatters.

This module provides formatters for converting stream chunks into various
output formats suitable for different streaming protocols.
"""

#  SPDX-License-Identifier: Apache-2.0

import json
from typing import Any

from fakeai.streaming.base import StreamChunk, StreamError


class SSEFormatter:
    """
    Server-Sent Events (SSE) formatter.

    Formats stream chunks according to the SSE protocol specification,
    compatible with OpenAI's streaming API format.
    """

    @staticmethod
    def format(chunk: StreamChunk) -> str:
        """
        Format a chunk as SSE event.

        Args:
            chunk: Chunk to format

        Returns:
            SSE-formatted string
        """
        # Convert chunk data to JSON
        if isinstance(chunk.data, dict):
            data_str = json.dumps(chunk.data, separators=(",", ":"))
        elif isinstance(chunk.data, str):
            data_str = chunk.data
        else:
            data_str = str(chunk.data)

        # Build SSE event
        lines = []

        # Add event type if specified
        if chunk.chunk_type and chunk.chunk_type != "data":
            lines.append(f"event: {chunk.chunk_type}")

        # Add data line
        lines.append(f"data: {data_str}")

        # Add blank line to terminate event
        lines.append("")

        return "\n".join(lines) + "\n"

    @staticmethod
    def format_error(error: StreamError) -> str:
        """
        Format an error as SSE event.

        Args:
            error: Error to format

        Returns:
            SSE-formatted error string
        """
        error_dict = error.to_dict()
        data_str = json.dumps(error_dict, separators=(",", ":"))

        lines = [
            "event: error",
            f"data: {data_str}",
            "",
        ]

        return "\n".join(lines) + "\n"

    @staticmethod
    def format_done() -> str:
        """
        Format stream completion signal.

        Returns:
            SSE-formatted done signal
        """
        return "data: [DONE]\n\n"

    @staticmethod
    def format_custom_event(event_type: str, data: Any) -> str:
        """
        Format a custom SSE event.

        Args:
            event_type: Event type name
            data: Event data

        Returns:
            SSE-formatted custom event
        """
        if isinstance(data, dict):
            data_str = json.dumps(data, separators=(",", ":"))
        elif isinstance(data, str):
            data_str = data
        else:
            data_str = str(data)

        lines = [
            f"event: {event_type}",
            f"data: {data_str}",
            "",
        ]

        return "\n".join(lines) + "\n"


class JSONLinesFormatter:
    """
    JSON Lines (JSONL) formatter.

    Formats each chunk as a single JSON object followed by a newline,
    suitable for line-delimited JSON streaming.
    """

    @staticmethod
    def format(chunk: StreamChunk) -> str:
        """
        Format a chunk as JSON line.

        Args:
            chunk: Chunk to format

        Returns:
            JSON line string
        """
        # Create JSON object with chunk data
        obj = {
            "type": chunk.chunk_type,
            "sequence": chunk.sequence_number,
            "timestamp": chunk.timestamp,
        }

        # Add chunk data
        if isinstance(chunk.data, dict):
            obj["data"] = chunk.data
        else:
            obj["data"] = {"content": chunk.data}

        # Add metadata if present
        if chunk.metadata:
            obj["metadata"] = chunk.metadata

        # Add flags
        if chunk.is_first:
            obj["is_first"] = True
        if chunk.is_last:
            obj["is_last"] = True

        return json.dumps(obj, separators=(",", ":")) + "\n"

    @staticmethod
    def format_error(error: StreamError) -> str:
        """
        Format an error as JSON line.

        Args:
            error: Error to format

        Returns:
            JSON line error string
        """
        obj = {
            "type": "error",
            "error": error.to_dict(),
        }

        return json.dumps(obj, separators=(",", ":")) + "\n"

    @staticmethod
    def format_done() -> str:
        """
        Format stream completion as JSON line.

        Returns:
            JSON line done signal
        """
        obj = {
            "type": "done",
            "timestamp": None,  # Will be filled by caller
        }

        return json.dumps(obj, separators=(",", ":")) + "\n"


class PlainTextFormatter:
    """
    Plain text formatter.

    Formats chunks as plain text content, suitable for simple text streaming
    without protocol overhead.
    """

    @staticmethod
    def format(chunk: StreamChunk) -> str:
        """
        Format a chunk as plain text.

        Args:
            chunk: Chunk to format

        Returns:
            Plain text string
        """
        # Extract text content from chunk
        if isinstance(chunk.data, dict):
            # Try to extract text from common response structures
            if "choices" in chunk.data:
                # Chat/completion format
                choices = chunk.data["choices"]
                if choices and len(choices) > 0:
                    choice = choices[0]
                    if "delta" in choice:
                        delta = choice["delta"]
                        return delta.get("content", "")
                    elif "text" in choice:
                        return choice["text"]
            elif "content" in chunk.data:
                return chunk.data["content"]
            elif "text" in chunk.data:
                return chunk.data["text"]
            # Fallback to JSON representation
            return json.dumps(chunk.data)
        elif isinstance(chunk.data, str):
            return chunk.data
        else:
            return str(chunk.data)

    @staticmethod
    def format_error(error: StreamError) -> str:
        """
        Format an error as plain text.

        Args:
            error: Error to format

        Returns:
            Plain text error string
        """
        return f"ERROR: {error.message}\n"

    @staticmethod
    def format_done() -> str:
        """
        Format stream completion signal.

        Returns:
            Empty string (no explicit done signal in plain text)
        """
        return ""


class OpenAIChatFormatter(SSEFormatter):
    """
    OpenAI Chat Completion streaming format.

    Specialized SSE formatter that matches OpenAI's chat completion
    streaming response format exactly.
    """

    @staticmethod
    def format_chat_chunk(
        chunk_id: str,
        model: str,
        created: int,
        delta: dict[str, Any],
        finish_reason: str | None = None,
        index: int = 0,
    ) -> str:
        """
        Format a chat completion chunk in OpenAI format.

        Args:
            chunk_id: Chunk identifier
            model: Model name
            created: Creation timestamp
            delta: Delta object with content changes
            finish_reason: Finish reason (for last chunk)
            index: Choice index

        Returns:
            SSE-formatted chat chunk
        """
        chunk_data = {
            "id": chunk_id,
            "object": "chat.completion.chunk",
            "created": created,
            "model": model,
            "choices": [
                {
                    "index": index,
                    "delta": delta,
                    "finish_reason": finish_reason,
                }
            ],
        }

        data_str = json.dumps(chunk_data, separators=(",", ":"))
        return f"data: {data_str}\n\n"


class OpenAICompletionFormatter(SSEFormatter):
    """
    OpenAI Completion streaming format.

    Specialized SSE formatter for legacy completion endpoint streaming.
    """

    @staticmethod
    def format_completion_chunk(
        chunk_id: str,
        model: str,
        created: int,
        text: str,
        finish_reason: str | None = None,
        index: int = 0,
    ) -> str:
        """
        Format a completion chunk in OpenAI format.

        Args:
            chunk_id: Chunk identifier
            model: Model name
            created: Creation timestamp
            text: Text delta
            finish_reason: Finish reason (for last chunk)
            index: Choice index

        Returns:
            SSE-formatted completion chunk
        """
        chunk_data = {
            "id": chunk_id,
            "object": "text_completion",
            "created": created,
            "model": model,
            "choices": [
                {
                    "text": text,
                    "index": index,
                    "finish_reason": finish_reason,
                    "logprobs": None,
                }
            ],
        }

        data_str = json.dumps(chunk_data, separators=(",", ":"))
        return f"data: {data_str}\n\n"
