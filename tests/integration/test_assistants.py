"""Integration tests for Assistants API.

This module tests the complete Assistants API including:
- Assistant creation, listing, retrieval, modification, deletion
- Thread creation, modification, deletion
- Message creation and listing
- Run creation, status polling, cancellation
- Run steps retrieval
- Tool usage (code interpreter, file search, function calling)
- Streaming runs
- Vector store integration
"""

import json
import time
from typing import Any

import pytest

from .utils import FakeAIClient


@pytest.mark.integration
class TestAssistantCreation:
    """Test assistant creation and basic operations."""

    def test_create_assistant_basic(self, client: FakeAIClient):
        """Test creating a basic assistant."""
        response = client.post(
            "/v1/assistants",
            json={
                "model": "gpt-4",
                "name": "Test Assistant",
                "description": "A test assistant for integration tests",
                "instructions": "You are a helpful test assistant.",
            },
        )
        response.raise_for_status()
        assistant = response.json()

        # Validate response structure
        assert assistant["object"] == "assistant"
        assert "id" in assistant
        assert assistant["id"].startswith("asst_")
        assert assistant["model"] == "gpt-4"
        assert assistant["name"] == "Test Assistant"
        assert assistant["description"] == "A test assistant for integration tests"
        assert assistant["instructions"] == "You are a helpful test assistant."
        assert "created_at" in assistant
        assert isinstance(assistant["created_at"], int)

    def test_create_assistant_with_tools(self, client: FakeAIClient):
        """Test creating an assistant with tools."""
        response = client.post(
            "/v1/assistants",
            json={
                "model": "gpt-4",
                "name": "Assistant with Tools",
                "instructions": "You can use tools.",
                "tools": [
                    {"type": "code_interpreter"},
                    {"type": "file_search"},
                ],
            },
        )
        response.raise_for_status()
        assistant = response.json()

        assert assistant["object"] == "assistant"
        assert len(assistant["tools"]) == 2
        assert any(tool["type"] == "code_interpreter" for tool in assistant["tools"])
        assert any(tool["type"] == "file_search" for tool in assistant["tools"])

    def test_create_assistant_with_function(self, client: FakeAIClient):
        """Test creating an assistant with function calling."""
        response = client.post(
            "/v1/assistants",
            json={
                "model": "gpt-4",
                "name": "Function Assistant",
                "instructions": "You can call functions.",
                "tools": [
                    {
                        "type": "function",
                        "function": {
                            "name": "get_weather",
                            "description": "Get the weather for a location",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "location": {
                                        "type": "string",
                                        "description": "City name",
                                    },
                                    "unit": {
                                        "type": "string",
                                        "enum": ["celsius", "fahrenheit"],
                                    },
                                },
                                "required": ["location"],
                            },
                        },
                    }
                ],
            },
        )
        response.raise_for_status()
        assistant = response.json()

        assert assistant["object"] == "assistant"
        assert len(assistant["tools"]) == 1
        assert assistant["tools"][0]["type"] == "function"
        assert assistant["tools"][0]["function"]["name"] == "get_weather"

    def test_create_assistant_with_metadata(self, client: FakeAIClient):
        """Test creating an assistant with metadata."""
        response = client.post(
            "/v1/assistants",
            json={
                "model": "gpt-4",
                "name": "Metadata Assistant",
                "metadata": {
                    "user_id": "123",
                    "environment": "test",
                },
            },
        )
        response.raise_for_status()
        assistant = response.json()

        assert assistant["object"] == "assistant"
        assert assistant["metadata"]["user_id"] == "123"
        assert assistant["metadata"]["environment"] == "test"

    def test_create_assistant_with_temperature(self, client: FakeAIClient):
        """Test creating an assistant with temperature and top_p."""
        response = client.post(
            "/v1/assistants",
            json={
                "model": "gpt-4",
                "name": "Temperature Assistant",
                "temperature": 0.7,
                "top_p": 0.9,
            },
        )
        response.raise_for_status()
        assistant = response.json()

        assert assistant["object"] == "assistant"
        assert assistant["temperature"] == 0.7
        assert assistant["top_p"] == 0.9


@pytest.mark.integration
class TestAssistantManagement:
    """Test assistant listing, retrieval, modification, and deletion."""

    def test_list_assistants(self, client: FakeAIClient):
        """Test listing assistants."""
        # Create a few assistants first
        for i in range(3):
            client.post(
                "/v1/assistants",
                json={
                    "model": "gpt-4",
                    "name": f"List Test Assistant {i}",
                },
            )

        # List assistants
        response = client.get("/v1/assistants")
        response.raise_for_status()
        assistants_list = response.json()

        assert assistants_list["object"] == "list"
        assert "data" in assistants_list
        assert len(assistants_list["data"]) >= 3
        assert all(asst["object"] == "assistant" for asst in assistants_list["data"])

    def test_list_assistants_with_pagination(self, client: FakeAIClient):
        """Test listing assistants with pagination."""
        response = client.get("/v1/assistants", params={"limit": 2})
        response.raise_for_status()
        assistants_list = response.json()

        assert assistants_list["object"] == "list"
        assert len(assistants_list["data"]) <= 2

    def test_retrieve_assistant(self, client: FakeAIClient):
        """Test retrieving a specific assistant."""
        # Create assistant
        create_response = client.post(
            "/v1/assistants",
            json={
                "model": "gpt-4",
                "name": "Retrieve Test",
            },
        )
        created = create_response.json()

        # Retrieve assistant
        response = client.get(f"/v1/assistants/{created['id']}")
        response.raise_for_status()
        assistant = response.json()

        assert assistant["id"] == created["id"]
        assert assistant["name"] == "Retrieve Test"

    def test_modify_assistant(self, client: FakeAIClient):
        """Test modifying an assistant."""
        # Create assistant
        create_response = client.post(
            "/v1/assistants",
            json={
                "model": "gpt-4",
                "name": "Original Name",
                "instructions": "Original instructions",
            },
        )
        created = create_response.json()

        # Modify assistant
        response = client.post(
            f"/v1/assistants/{created['id']}",
            json={
                "name": "Modified Name",
                "instructions": "Modified instructions",
                "metadata": {"updated": "true"},
            },
        )
        response.raise_for_status()
        modified = response.json()

        assert modified["id"] == created["id"]
        assert modified["name"] == "Modified Name"
        assert modified["instructions"] == "Modified instructions"
        assert modified["metadata"]["updated"] == "true"

    def test_delete_assistant(self, client: FakeAIClient):
        """Test deleting an assistant."""
        # Create assistant
        create_response = client.post(
            "/v1/assistants",
            json={
                "model": "gpt-4",
                "name": "Delete Test",
            },
        )
        created = create_response.json()

        # Delete assistant
        response = client.delete(f"/v1/assistants/{created['id']}")
        response.raise_for_status()
        result = response.json()

        assert result["id"] == created["id"]
        assert result["object"] == "assistant.deleted"
        assert result["deleted"] is True

        # Verify deletion
        get_response = client.get(f"/v1/assistants/{created['id']}")
        assert get_response.status_code == 404


@pytest.mark.integration
class TestThreads:
    """Test thread operations."""

    def test_create_thread_empty(self, client: FakeAIClient):
        """Test creating an empty thread."""
        response = client.post("/v1/threads", json={})
        response.raise_for_status()
        thread = response.json()

        assert thread["object"] == "thread"
        assert "id" in thread
        assert thread["id"].startswith("thread_")
        assert "created_at" in thread
        assert thread["metadata"] == {}

    def test_create_thread_with_messages(self, client: FakeAIClient):
        """Test creating a thread with initial messages."""
        response = client.post(
            "/v1/threads",
            json={
                "messages": [
                    {
                        "role": "user",
                        "content": "Hello, I need help with something.",
                    }
                ]
            },
        )
        response.raise_for_status()
        thread = response.json()

        assert thread["object"] == "thread"
        assert "id" in thread

    def test_create_thread_with_metadata(self, client: FakeAIClient):
        """Test creating a thread with metadata."""
        response = client.post(
            "/v1/threads",
            json={
                "metadata": {
                    "user_id": "user_123",
                    "session_id": "session_456",
                }
            },
        )
        response.raise_for_status()
        thread = response.json()

        assert thread["metadata"]["user_id"] == "user_123"
        assert thread["metadata"]["session_id"] == "session_456"

    def test_retrieve_thread(self, client: FakeAIClient):
        """Test retrieving a thread."""
        # Create thread
        create_response = client.post("/v1/threads", json={})
        created = create_response.json()

        # Retrieve thread
        response = client.get(f"/v1/threads/{created['id']}")
        response.raise_for_status()
        thread = response.json()

        assert thread["id"] == created["id"]
        assert thread["object"] == "thread"

    def test_modify_thread(self, client: FakeAIClient):
        """Test modifying a thread."""
        # Create thread
        create_response = client.post("/v1/threads", json={})
        created = create_response.json()

        # Modify thread
        response = client.post(
            f"/v1/threads/{created['id']}",
            json={
                "metadata": {
                    "modified": "true",
                    "timestamp": str(int(time.time())),
                }
            },
        )
        response.raise_for_status()
        modified = response.json()

        assert modified["id"] == created["id"]
        assert modified["metadata"]["modified"] == "true"

    def test_delete_thread(self, client: FakeAIClient):
        """Test deleting a thread."""
        # Create thread
        create_response = client.post("/v1/threads", json={})
        created = create_response.json()

        # Delete thread
        response = client.delete(f"/v1/threads/{created['id']}")
        response.raise_for_status()
        result = response.json()

        assert result["id"] == created["id"]
        assert result["object"] == "thread.deleted"
        assert result["deleted"] is True


@pytest.mark.integration
class TestMessages:
    """Test message operations in threads."""

    def test_create_message(self, client: FakeAIClient):
        """Test creating a message in a thread."""
        # Create thread
        thread = client.post("/v1/threads", json={}).json()

        # Create message
        response = client.post(
            f"/v1/threads/{thread['id']}/messages",
            json={
                "role": "user",
                "content": "What is the weather today?",
            },
        )
        response.raise_for_status()
        message = response.json()

        assert message["object"] == "thread.message"
        assert "id" in message
        assert message["id"].startswith("msg_")
        assert message["thread_id"] == thread["id"]
        assert message["role"] == "user"
        assert len(message["content"]) > 0
        assert message["content"][0]["type"] == "text"
        assert message["content"][0]["text"]["value"] == "What is the weather today?"

    def test_create_message_with_metadata(self, client: FakeAIClient):
        """Test creating a message with metadata."""
        thread = client.post("/v1/threads", json={}).json()

        response = client.post(
            f"/v1/threads/{thread['id']}/messages",
            json={
                "role": "user",
                "content": "Test message",
                "metadata": {"source": "test", "priority": "high"},
            },
        )
        response.raise_for_status()
        message = response.json()

        assert message["metadata"]["source"] == "test"
        assert message["metadata"]["priority"] == "high"

    def test_list_messages(self, client: FakeAIClient):
        """Test listing messages in a thread."""
        thread = client.post("/v1/threads", json={}).json()

        # Create multiple messages
        for i in range(3):
            client.post(
                f"/v1/threads/{thread['id']}/messages",
                json={
                    "role": "user",
                    "content": f"Message {i}",
                },
            )

        # List messages
        response = client.get(f"/v1/threads/{thread['id']}/messages")
        response.raise_for_status()
        messages_list = response.json()

        assert messages_list["object"] == "list"
        assert len(messages_list["data"]) == 3
        assert all(msg["object"] == "thread.message" for msg in messages_list["data"])

    def test_retrieve_message(self, client: FakeAIClient):
        """Test retrieving a specific message."""
        thread = client.post("/v1/threads", json={}).json()

        # Create message
        created = client.post(
            f"/v1/threads/{thread['id']}/messages",
            json={
                "role": "user",
                "content": "Retrieve this message",
            },
        ).json()

        # Retrieve message
        response = client.get(
            f"/v1/threads/{thread['id']}/messages/{created['id']}"
        )
        response.raise_for_status()
        message = response.json()

        assert message["id"] == created["id"]
        assert message["content"][0]["text"]["value"] == "Retrieve this message"

    def test_modify_message(self, client: FakeAIClient):
        """Test modifying a message."""
        thread = client.post("/v1/threads", json={}).json()

        # Create message
        created = client.post(
            f"/v1/threads/{thread['id']}/messages",
            json={
                "role": "user",
                "content": "Original message",
            },
        ).json()

        # Modify message metadata
        response = client.post(
            f"/v1/threads/{thread['id']}/messages/{created['id']}",
            json={
                "metadata": {"edited": "true"},
            },
        )
        response.raise_for_status()
        modified = response.json()

        assert modified["id"] == created["id"]
        assert modified["metadata"]["edited"] == "true"


@pytest.mark.integration
class TestRuns:
    """Test run operations."""

    def test_create_run(self, client: FakeAIClient):
        """Test creating a run."""
        # Create assistant and thread
        assistant = client.post(
            "/v1/assistants",
            json={
                "model": "gpt-4",
                "name": "Run Test Assistant",
                "instructions": "You are a helpful assistant.",
            },
        ).json()

        thread = client.post("/v1/threads", json={}).json()

        # Add message to thread
        client.post(
            f"/v1/threads/{thread['id']}/messages",
            json={
                "role": "user",
                "content": "What is 2+2?",
            },
        )

        # Create run
        response = client.post(
            f"/v1/threads/{thread['id']}/runs",
            json={
                "assistant_id": assistant["id"],
            },
        )
        response.raise_for_status()
        run = response.json()

        assert run["object"] == "thread.run"
        assert "id" in run
        assert run["id"].startswith("run_")
        assert run["thread_id"] == thread["id"]
        assert run["assistant_id"] == assistant["id"]
        assert run["status"] in [
            "queued",
            "in_progress",
            "completed",
            "requires_action",
        ]

    def test_create_run_with_instructions(self, client: FakeAIClient):
        """Test creating a run with custom instructions."""
        assistant = client.post(
            "/v1/assistants",
            json={"model": "gpt-4", "name": "Instructions Test"},
        ).json()

        thread = client.post("/v1/threads", json={}).json()

        client.post(
            f"/v1/threads/{thread['id']}/messages",
            json={"role": "user", "content": "Hello"},
        )

        response = client.post(
            f"/v1/threads/{thread['id']}/runs",
            json={
                "assistant_id": assistant["id"],
                "instructions": "Be very brief in your responses.",
            },
        )
        response.raise_for_status()
        run = response.json()

        assert run["instructions"] == "Be very brief in your responses."

    def test_retrieve_run(self, client: FakeAIClient):
        """Test retrieving a run."""
        assistant = client.post(
            "/v1/assistants",
            json={"model": "gpt-4", "name": "Retrieve Test"},
        ).json()

        thread = client.post("/v1/threads", json={}).json()
        client.post(
            f"/v1/threads/{thread['id']}/messages",
            json={"role": "user", "content": "Test"},
        )

        created = client.post(
            f"/v1/threads/{thread['id']}/runs",
            json={"assistant_id": assistant["id"]},
        ).json()

        # Retrieve run
        response = client.get(f"/v1/threads/{thread['id']}/runs/{created['id']}")
        response.raise_for_status()
        run = response.json()

        assert run["id"] == created["id"]
        assert run["object"] == "thread.run"

    def test_list_runs(self, client: FakeAIClient):
        """Test listing runs in a thread."""
        assistant = client.post(
            "/v1/assistants",
            json={"model": "gpt-4", "name": "List Runs Test"},
        ).json()

        thread = client.post("/v1/threads", json={}).json()
        client.post(
            f"/v1/threads/{thread['id']}/messages",
            json={"role": "user", "content": "Test"},
        )

        # Create multiple runs
        for _ in range(2):
            client.post(
                f"/v1/threads/{thread['id']}/runs",
                json={"assistant_id": assistant["id"]},
            )

        # List runs
        response = client.get(f"/v1/threads/{thread['id']}/runs")
        response.raise_for_status()
        runs_list = response.json()

        assert runs_list["object"] == "list"
        assert len(runs_list["data"]) >= 2
        assert all(run["object"] == "thread.run" for run in runs_list["data"])

    def test_modify_run(self, client: FakeAIClient):
        """Test modifying a run (metadata only)."""
        assistant = client.post(
            "/v1/assistants",
            json={"model": "gpt-4", "name": "Modify Test"},
        ).json()

        thread = client.post("/v1/threads", json={}).json()
        client.post(
            f"/v1/threads/{thread['id']}/messages",
            json={"role": "user", "content": "Test"},
        )

        created = client.post(
            f"/v1/threads/{thread['id']}/runs",
            json={"assistant_id": assistant["id"]},
        ).json()

        # Modify run
        response = client.post(
            f"/v1/threads/{thread['id']}/runs/{created['id']}",
            json={
                "metadata": {"updated": "true"},
            },
        )
        response.raise_for_status()
        modified = response.json()

        assert modified["metadata"]["updated"] == "true"

    def test_cancel_run(self, client: FakeAIClient):
        """Test cancelling a run."""
        assistant = client.post(
            "/v1/assistants",
            json={"model": "gpt-4", "name": "Cancel Test"},
        ).json()

        thread = client.post("/v1/threads", json={}).json()
        client.post(
            f"/v1/threads/{thread['id']}/messages",
            json={"role": "user", "content": "Test"},
        )

        created = client.post(
            f"/v1/threads/{thread['id']}/runs",
            json={"assistant_id": assistant["id"]},
        ).json()

        # Cancel run
        response = client.post(
            f"/v1/threads/{thread['id']}/runs/{created['id']}/cancel"
        )
        response.raise_for_status()
        cancelled = response.json()

        assert cancelled["id"] == created["id"]
        assert cancelled["status"] in ["cancelling", "cancelled"]


@pytest.mark.integration
class TestRunStatusPolling:
    """Test run status polling and completion."""

    def test_poll_run_until_completion(self, client: FakeAIClient):
        """Test polling a run until it completes."""
        assistant = client.post(
            "/v1/assistants",
            json={"model": "gpt-4", "name": "Polling Test"},
        ).json()

        thread = client.post("/v1/threads", json={}).json()
        client.post(
            f"/v1/threads/{thread['id']}/messages",
            json={"role": "user", "content": "Say hello"},
        )

        run = client.post(
            f"/v1/threads/{thread['id']}/runs",
            json={"assistant_id": assistant["id"]},
        ).json()

        # Poll until completion (with timeout)
        max_attempts = 30
        for _ in range(max_attempts):
            response = client.get(f"/v1/threads/{thread['id']}/runs/{run['id']}")
            run_status = response.json()

            if run_status["status"] in ["completed", "failed", "cancelled", "expired"]:
                break

            time.sleep(0.5)

        # Verify final status
        assert run_status["status"] in [
            "completed",
            "failed",
            "cancelled",
            "expired",
        ]

        # If completed, check for usage
        if run_status["status"] == "completed":
            assert "usage" in run_status
            assert run_status["usage"]["total_tokens"] > 0


@pytest.mark.integration
class TestRunSteps:
    """Test run steps retrieval."""

    def test_list_run_steps(self, client: FakeAIClient):
        """Test listing run steps."""
        assistant = client.post(
            "/v1/assistants",
            json={"model": "gpt-4", "name": "Steps Test"},
        ).json()

        thread = client.post("/v1/threads", json={}).json()
        client.post(
            f"/v1/threads/{thread['id']}/messages",
            json={"role": "user", "content": "What is Python?"},
        )

        run = client.post(
            f"/v1/threads/{thread['id']}/runs",
            json={"assistant_id": assistant["id"]},
        ).json()

        # Wait a bit for run to progress
        time.sleep(1)

        # List run steps
        response = client.get(
            f"/v1/threads/{thread['id']}/runs/{run['id']}/steps"
        )
        response.raise_for_status()
        steps = response.json()

        assert steps["object"] == "list"
        assert "data" in steps
        # May or may not have steps depending on implementation
        if steps["data"]:
            assert all(
                step["object"] == "thread.run.step" for step in steps["data"]
            )

    def test_retrieve_run_step(self, client: FakeAIClient):
        """Test retrieving a specific run step."""
        assistant = client.post(
            "/v1/assistants",
            json={"model": "gpt-4", "name": "Step Retrieve Test"},
        ).json()

        thread = client.post("/v1/threads", json={}).json()
        client.post(
            f"/v1/threads/{thread['id']}/messages",
            json={"role": "user", "content": "Hello"},
        )

        run = client.post(
            f"/v1/threads/{thread['id']}/runs",
            json={"assistant_id": assistant["id"]},
        ).json()

        time.sleep(1)

        # Get steps list
        steps = client.get(
            f"/v1/threads/{thread['id']}/runs/{run['id']}/steps"
        ).json()

        if steps["data"]:
            step_id = steps["data"][0]["id"]

            # Retrieve specific step
            response = client.get(
                f"/v1/threads/{thread['id']}/runs/{run['id']}/steps/{step_id}"
            )
            response.raise_for_status()
            step = response.json()

            assert step["id"] == step_id
            assert step["object"] == "thread.run.step"


@pytest.mark.integration
class TestCodeInterpreter:
    """Test code interpreter tool."""

    def test_code_interpreter_tool(self, client: FakeAIClient):
        """Test assistant with code interpreter."""
        assistant = client.post(
            "/v1/assistants",
            json={
                "model": "gpt-4",
                "name": "Code Interpreter Test",
                "instructions": "You are a Python code interpreter.",
                "tools": [{"type": "code_interpreter"}],
            },
        ).json()

        thread = client.post("/v1/threads", json={}).json()
        client.post(
            f"/v1/threads/{thread['id']}/messages",
            json={
                "role": "user",
                "content": "Calculate the sum of numbers from 1 to 100",
            },
        )

        run = client.post(
            f"/v1/threads/{thread['id']}/runs",
            json={"assistant_id": assistant["id"]},
        ).json()

        assert run["object"] == "thread.run"
        assert any(tool["type"] == "code_interpreter" for tool in run["tools"])


@pytest.mark.integration
class TestFileSearch:
    """Test file search tool."""

    def test_file_search_tool(self, client: FakeAIClient):
        """Test assistant with file search."""
        assistant = client.post(
            "/v1/assistants",
            json={
                "model": "gpt-4",
                "name": "File Search Test",
                "instructions": "You can search files.",
                "tools": [{"type": "file_search"}],
            },
        ).json()

        thread = client.post("/v1/threads", json={}).json()
        client.post(
            f"/v1/threads/{thread['id']}/messages",
            json={
                "role": "user",
                "content": "Search for information about AI",
            },
        )

        run = client.post(
            f"/v1/threads/{thread['id']}/runs",
            json={"assistant_id": assistant["id"]},
        ).json()

        assert run["object"] == "thread.run"
        assert any(tool["type"] == "file_search" for tool in run["tools"])


@pytest.mark.integration
class TestFunctionCalling:
    """Test function calling in assistants."""

    def test_function_calling_basic(self, client: FakeAIClient):
        """Test basic function calling."""
        assistant = client.post(
            "/v1/assistants",
            json={
                "model": "gpt-4",
                "name": "Function Test",
                "tools": [
                    {
                        "type": "function",
                        "function": {
                            "name": "get_current_weather",
                            "description": "Get current weather",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "location": {"type": "string"},
                                    "unit": {"type": "string", "enum": ["C", "F"]},
                                },
                                "required": ["location"],
                            },
                        },
                    }
                ],
            },
        ).json()

        thread = client.post("/v1/threads", json={}).json()
        client.post(
            f"/v1/threads/{thread['id']}/messages",
            json={
                "role": "user",
                "content": "What's the weather in San Francisco?",
            },
        )

        run = client.post(
            f"/v1/threads/{thread['id']}/runs",
            json={"assistant_id": assistant["id"]},
        ).json()

        assert run["object"] == "thread.run"
        # Function should be in tools
        assert any(
            tool["type"] == "function"
            and tool.get("function", {}).get("name") == "get_current_weather"
            for tool in run["tools"]
        )

    def test_submit_tool_outputs(self, client: FakeAIClient):
        """Test submitting tool outputs."""
        assistant = client.post(
            "/v1/assistants",
            json={
                "model": "gpt-4",
                "name": "Tool Output Test",
                "tools": [
                    {
                        "type": "function",
                        "function": {
                            "name": "calculate",
                            "description": "Perform calculation",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "expression": {"type": "string"},
                                },
                                "required": ["expression"],
                            },
                        },
                    }
                ],
            },
        ).json()

        thread = client.post("/v1/threads", json={}).json()
        client.post(
            f"/v1/threads/{thread['id']}/messages",
            json={"role": "user", "content": "Calculate 5 * 7"},
        )

        run = client.post(
            f"/v1/threads/{thread['id']}/runs",
            json={"assistant_id": assistant["id"]},
        ).json()

        # Poll for requires_action status
        max_attempts = 10
        for _ in range(max_attempts):
            run_status = client.get(
                f"/v1/threads/{thread['id']}/runs/{run['id']}"
            ).json()

            if run_status["status"] == "requires_action":
                # Submit tool outputs
                tool_call_id = run_status["required_action"]["submit_tool_outputs"][
                    "tool_calls"
                ][0]["id"]

                response = client.post(
                    f"/v1/threads/{thread['id']}/runs/{run['id']}/submit_tool_outputs",
                    json={
                        "tool_outputs": [
                            {
                                "tool_call_id": tool_call_id,
                                "output": "35",
                            }
                        ]
                    },
                )
                response.raise_for_status()
                break

            if run_status["status"] in ["completed", "failed"]:
                break

            time.sleep(0.5)


@pytest.mark.integration
@pytest.mark.streaming
class TestStreamingRuns:
    """Test streaming runs."""

    def test_create_run_with_streaming(self, client: FakeAIClient):
        """Test creating a streaming run."""
        assistant = client.post(
            "/v1/assistants",
            json={
                "model": "gpt-4",
                "name": "Streaming Test",
            },
        ).json()

        thread = client.post("/v1/threads", json={}).json()
        client.post(
            f"/v1/threads/{thread['id']}/messages",
            json={"role": "user", "content": "Tell me a short story"},
        )

        # Create streaming run
        response = client.post(
            f"/v1/threads/{thread['id']}/runs",
            json={
                "assistant_id": assistant["id"],
                "stream": True,
            },
        )
        response.raise_for_status()

        # For streaming, we should get SSE events
        # Note: This is a basic check - full streaming would need special handling
        assert response.status_code == 200


@pytest.mark.integration
class TestVectorStores:
    """Test vector store integration."""

    def test_create_assistant_with_vector_store(self, client: FakeAIClient):
        """Test creating assistant with vector store."""
        assistant = client.post(
            "/v1/assistants",
            json={
                "model": "gpt-4",
                "name": "Vector Store Test",
                "tools": [{"type": "file_search"}],
                "tool_resources": {
                    "file_search": {
                        "vector_store_ids": ["vs_test_123"],
                    }
                },
            },
        )
        response_data = assistant.json()

        assert response_data["object"] == "assistant"
        if "tool_resources" in response_data:
            assert "file_search" in response_data["tool_resources"]

    def test_thread_with_vector_store(self, client: FakeAIClient):
        """Test creating thread with vector store."""
        thread = client.post(
            "/v1/threads",
            json={
                "tool_resources": {
                    "file_search": {
                        "vector_store_ids": ["vs_test_456"],
                    }
                }
            },
        )
        response_data = thread.json()

        assert response_data["object"] == "thread"
        if "tool_resources" in response_data:
            assert "file_search" in response_data["tool_resources"]


@pytest.mark.integration
class TestAssistantsEndToEnd:
    """End-to-end tests for complete assistant workflows."""

    def test_complete_assistant_workflow(self, client: FakeAIClient):
        """Test complete workflow: create assistant, thread, message, run."""
        # 1. Create assistant
        assistant = client.post(
            "/v1/assistants",
            json={
                "model": "gpt-4",
                "name": "E2E Test Assistant",
                "instructions": "You are a helpful assistant.",
            },
        ).json()

        # 2. Create thread
        thread = client.post("/v1/threads", json={}).json()

        # 3. Add message
        message = client.post(
            f"/v1/threads/{thread['id']}/messages",
            json={
                "role": "user",
                "content": "What is the capital of France?",
            },
        ).json()

        # 4. Create run
        run = client.post(
            f"/v1/threads/{thread['id']}/runs",
            json={"assistant_id": assistant["id"]},
        ).json()

        # 5. Poll until complete
        max_attempts = 30
        for _ in range(max_attempts):
            run_status = client.get(
                f"/v1/threads/{thread['id']}/runs/{run['id']}"
            ).json()

            if run_status["status"] in ["completed", "failed"]:
                break

            time.sleep(0.5)

        # 6. Get messages
        messages = client.get(f"/v1/threads/{thread['id']}/messages").json()

        # Should have at least 2 messages (user + assistant)
        assert len(messages["data"]) >= 2

        # 7. Cleanup
        client.delete(f"/v1/threads/{thread['id']}")
        client.delete(f"/v1/assistants/{assistant['id']}")

        # Verify cleanup worked
        assert client.get(f"/v1/threads/{thread['id']}").status_code == 404
        assert client.get(f"/v1/assistants/{assistant['id']}").status_code == 404

    def test_multi_turn_conversation(self, client: FakeAIClient):
        """Test multi-turn conversation in a thread."""
        # Create assistant and thread
        assistant = client.post(
            "/v1/assistants",
            json={
                "model": "gpt-4",
                "name": "Multi-turn Test",
            },
        ).json()

        thread = client.post("/v1/threads", json={}).json()

        # Turn 1
        client.post(
            f"/v1/threads/{thread['id']}/messages",
            json={"role": "user", "content": "Hello"},
        )

        run1 = client.post(
            f"/v1/threads/{thread['id']}/runs",
            json={"assistant_id": assistant["id"]},
        ).json()

        # Wait for completion
        for _ in range(20):
            status = client.get(
                f"/v1/threads/{thread['id']}/runs/{run1['id']}"
            ).json()
            if status["status"] == "completed":
                break
            time.sleep(0.5)

        # Turn 2
        client.post(
            f"/v1/threads/{thread['id']}/messages",
            json={"role": "user", "content": "Can you help me with Python?"},
        )

        run2 = client.post(
            f"/v1/threads/{thread['id']}/runs",
            json={"assistant_id": assistant["id"]},
        ).json()

        # Get all messages
        messages = client.get(f"/v1/threads/{thread['id']}/messages").json()

        # Should have multiple messages
        assert len(messages["data"]) >= 2
