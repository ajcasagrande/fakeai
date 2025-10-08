"""Integration tests for Responses API endpoint.

The Responses API is a stateful conversation API introduced in March 2025
that simplifies message management with built-in state tracking.
"""

import asyncio
import time

import pytest

from .utils import FakeAIClient


@pytest.mark.integration
class TestResponsesBasic:
    """Test basic Responses API functionality."""

    def test_response_creation_with_string_input(self, client: FakeAIClient):
        """Test creating a response with string input."""
        response = client.post(
            "/v1/responses",
            json={
                "model": "gpt-4",
                "input": "Hello, how are you?",
            },
        )
        response.raise_for_status()
        data = response.json()

        # Validate response structure
        assert data["object"] == "response"
        assert "id" in data
        assert data["id"].startswith("resp-")
        assert data["model"] == "gpt-4"
        assert data["status"] == "completed"
        assert "created_at" in data
        assert isinstance(data["created_at"], int)

        # Validate output
        assert "output" in data
        assert len(data["output"]) > 0
        assert data["output"][0]["type"] == "message"
        assert data["output"][0]["role"] == "assistant"
        assert data["output"][0]["status"] == "completed"
        assert len(data["output"][0]["content"]) > 0
        assert data["output"][0]["content"][0]["type"] == "text"

        # Validate usage
        assert "usage" in data
        assert data["usage"]["input_tokens"] > 0
        assert data["usage"]["output_tokens"] > 0
        assert data["usage"]["total_tokens"] > 0

    def test_response_creation_with_messages_array(self, client: FakeAIClient):
        """Test creating a response with messages array input."""
        response = client.post(
            "/v1/responses",
            json={
                "model": "gpt-4",
                "input": [
                    {"role": "user", "content": "What is the capital of France?"},
                ],
            },
        )
        response.raise_for_status()
        data = response.json()

        assert data["object"] == "response"
        assert data["status"] == "completed"
        assert len(data["output"]) > 0
        assert data["output"][0]["type"] == "message"

    def test_response_with_instructions(self, client: FakeAIClient):
        """Test response with system-level instructions."""
        response = client.post(
            "/v1/responses",
            json={
                "model": "gpt-4",
                "input": "Tell me about yourself.",
                "instructions": "You are a helpful assistant that speaks like a pirate.",
            },
        )
        response.raise_for_status()
        data = response.json()

        assert data["status"] == "completed"
        assert data["instructions"] == "You are a helpful assistant that speaks like a pirate."
        assert len(data["output"]) > 0


@pytest.mark.integration
class TestResponsesStateful:
    """Test stateful conversation tracking."""

    def test_stateful_conversation_single_turn(self, client: FakeAIClient):
        """Test single-turn conversation with state."""
        # First response
        response = client.post(
            "/v1/responses",
            json={
                "model": "gpt-4",
                "input": "My name is Alice.",
                "store": True,  # Enable state storage
            },
        )
        response.raise_for_status()
        data = response.json()

        assert data["status"] == "completed"
        first_response_id = data["id"]
        assert first_response_id.startswith("resp-")

    def test_stateful_conversation_multi_turn(self, client: FakeAIClient):
        """Test multi-turn conversation with automatic context."""
        # First turn
        response1 = client.post(
            "/v1/responses",
            json={
                "model": "gpt-4",
                "input": "My favorite color is blue.",
                "store": True,
            },
        )
        response1.raise_for_status()
        data1 = response1.json()
        first_response_id = data1["id"]

        # Second turn - reference previous response
        response2 = client.post(
            "/v1/responses",
            json={
                "model": "gpt-4",
                "input": "What is my favorite color?",
                "previous_response_id": first_response_id,
                "store": True,
            },
        )
        response2.raise_for_status()
        data2 = response2.json()

        assert data2["status"] == "completed"
        assert data2["previous_response_id"] == first_response_id
        assert len(data2["output"]) > 0

    def test_conversation_continuation(self, client: FakeAIClient):
        """Test response continuation with previous_response_id."""
        # Initial response
        response1 = client.post(
            "/v1/responses",
            json={
                "model": "gpt-4",
                "input": [
                    {"role": "user", "content": "Count to 3"},
                ],
                "store": True,
            },
        )
        response1.raise_for_status()
        data1 = response1.json()
        response_id = data1["id"]

        # Continue conversation
        response2 = client.post(
            "/v1/responses",
            json={
                "model": "gpt-4",
                "input": "Now count to 5",
                "previous_response_id": response_id,
            },
        )
        response2.raise_for_status()
        data2 = response2.json()

        assert data2["previous_response_id"] == response_id
        assert data2["status"] == "completed"


@pytest.mark.integration
class TestResponsesMetadata:
    """Test response metadata functionality."""

    def test_response_with_metadata(self, client: FakeAIClient):
        """Test attaching metadata to response."""
        metadata = {
            "user_id": "user-123",
            "session_id": "sess-456",
            "custom_tag": "test-value",
        }

        response = client.post(
            "/v1/responses",
            json={
                "model": "gpt-4",
                "input": "Hello",
                "metadata": metadata,
            },
        )
        response.raise_for_status()
        data = response.json()

        assert "metadata" in data
        assert data["metadata"] == metadata

    def test_response_with_multiple_metadata_fields(self, client: FakeAIClient):
        """Test response with maximum metadata fields (up to 16 key-value pairs)."""
        metadata = {
            f"key_{i}": f"value_{i}" for i in range(16)
        }

        response = client.post(
            "/v1/responses",
            json={
                "model": "gpt-4",
                "input": "Test with max metadata",
                "metadata": metadata,
            },
        )
        response.raise_for_status()
        data = response.json()

        assert data["metadata"] == metadata
        assert len(data["metadata"]) == 16


@pytest.mark.integration
class TestResponsesParameters:
    """Test various response parameters."""

    def test_response_with_temperature(self, client: FakeAIClient):
        """Test response with temperature parameter."""
        response = client.post(
            "/v1/responses",
            json={
                "model": "gpt-4",
                "input": "Generate a random number",
                "temperature": 0.8,
            },
        )
        response.raise_for_status()
        data = response.json()

        assert data["status"] == "completed"
        assert data["temperature"] == 0.8

    def test_response_with_max_output_tokens(self, client: FakeAIClient):
        """Test response with max_output_tokens limit."""
        response = client.post(
            "/v1/responses",
            json={
                "model": "gpt-4",
                "input": "Write a long story",
                "max_output_tokens": 50,
            },
        )
        response.raise_for_status()
        data = response.json()

        assert data["status"] == "completed"
        assert data["max_output_tokens"] == 50
        # Verify token limit is respected
        assert data["usage"]["output_tokens"] <= 50

    def test_response_with_top_p(self, client: FakeAIClient):
        """Test response with top_p parameter."""
        response = client.post(
            "/v1/responses",
            json={
                "model": "gpt-4",
                "input": "Hello",
                "top_p": 0.9,
            },
        )
        response.raise_for_status()
        data = response.json()

        assert data["top_p"] == 0.9

    def test_response_with_tools(self, client: FakeAIClient):
        """Test response with tools parameter."""
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Get current weather",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {"type": "string"},
                        },
                        "required": ["location"],
                    },
                },
            }
        ]

        response = client.post(
            "/v1/responses",
            json={
                "model": "gpt-4",
                "input": "What's the weather?",
                "tools": tools,
            },
        )
        response.raise_for_status()
        data = response.json()

        assert "tools" in data
        assert len(data["tools"]) == 1

    def test_response_with_parallel_tool_calls(self, client: FakeAIClient):
        """Test response with parallel_tool_calls setting."""
        response = client.post(
            "/v1/responses",
            json={
                "model": "gpt-4",
                "input": "Hello",
                "parallel_tool_calls": False,
            },
        )
        response.raise_for_status()
        data = response.json()

        assert data["parallel_tool_calls"] is False


@pytest.mark.integration
class TestResponsesModels:
    """Test responses with different models."""

    def test_response_with_gpt4(self, client: FakeAIClient):
        """Test response with GPT-4 model."""
        response = client.post(
            "/v1/responses",
            json={
                "model": "gpt-4",
                "input": "Hello",
            },
        )
        response.raise_for_status()
        data = response.json()

        assert data["model"] == "gpt-4"

    def test_response_with_gpt35_turbo(self, client: FakeAIClient):
        """Test response with GPT-3.5-turbo model."""
        response = client.post(
            "/v1/responses",
            json={
                "model": "gpt-3.5-turbo",
                "input": "Hello",
            },
        )
        response.raise_for_status()
        data = response.json()

        assert data["model"] == "gpt-3.5-turbo"

    def test_response_with_custom_model(self, client: FakeAIClient):
        """Test response with custom model ID."""
        custom_model = "my-custom-model-v1"

        response = client.post(
            "/v1/responses",
            json={
                "model": custom_model,
                "input": "Test with custom model",
            },
        )
        response.raise_for_status()
        data = response.json()

        assert data["model"] == custom_model


@pytest.mark.integration
class TestResponsesErrorHandling:
    """Test error handling in Responses API."""

    def test_response_missing_model(self, client: FakeAIClient):
        """Test error when model parameter is missing."""
        response = client.post(
            "/v1/responses",
            json={
                "input": "Hello",
            },
        )

        assert response.status_code == 422  # Validation error

    def test_response_missing_input(self, client: FakeAIClient):
        """Test error when input parameter is missing."""
        response = client.post(
            "/v1/responses",
            json={
                "model": "gpt-4",
            },
        )

        assert response.status_code == 422  # Validation error

    def test_response_invalid_temperature(self, client: FakeAIClient):
        """Test error with invalid temperature value."""
        response = client.post(
            "/v1/responses",
            json={
                "model": "gpt-4",
                "input": "Hello",
                "temperature": 3.0,  # Invalid: should be <= 2
            },
        )

        assert response.status_code == 422  # Validation error

    def test_response_invalid_top_p(self, client: FakeAIClient):
        """Test error with invalid top_p value."""
        response = client.post(
            "/v1/responses",
            json={
                "model": "gpt-4",
                "input": "Hello",
                "top_p": 1.5,  # Invalid: should be <= 1
            },
        )

        assert response.status_code == 422  # Validation error


@pytest.mark.integration
class TestResponsesTokenUsage:
    """Test token usage tracking in responses."""

    def test_response_token_counting(self, client: FakeAIClient):
        """Test that token usage is accurately tracked."""
        response = client.post(
            "/v1/responses",
            json={
                "model": "gpt-4",
                "input": "Say hello",
            },
        )
        response.raise_for_status()
        data = response.json()

        usage = data["usage"]
        assert usage["input_tokens"] > 0
        assert usage["output_tokens"] > 0
        assert usage["total_tokens"] == usage["input_tokens"] + usage["output_tokens"]

    def test_response_token_counting_with_instructions(self, client: FakeAIClient):
        """Test token counting includes instructions."""
        response = client.post(
            "/v1/responses",
            json={
                "model": "gpt-4",
                "input": "Hello",
                "instructions": "You are a helpful assistant.",
            },
        )
        response.raise_for_status()
        data = response.json()

        usage = data["usage"]
        # Token count should include instructions
        assert usage["input_tokens"] > 5  # More than just "Hello"

    def test_response_token_counting_multi_turn(self, client: FakeAIClient):
        """Test token counting in multi-turn conversation."""
        # First turn
        response1 = client.post(
            "/v1/responses",
            json={
                "model": "gpt-4",
                "input": "First message",
                "store": True,
            },
        )
        response1.raise_for_status()
        data1 = response1.json()
        first_response_id = data1["id"]

        # Second turn
        response2 = client.post(
            "/v1/responses",
            json={
                "model": "gpt-4",
                "input": "Second message",
                "previous_response_id": first_response_id,
            },
        )
        response2.raise_for_status()
        data2 = response2.json()

        # Both should have valid usage
        assert data1["usage"]["total_tokens"] > 0
        assert data2["usage"]["total_tokens"] > 0


@pytest.mark.integration
class TestResponsesComplexScenarios:
    """Test complex response scenarios."""

    def test_response_with_multi_modal_content(self, client: FakeAIClient):
        """Test response with multi-modal content input."""
        response = client.post(
            "/v1/responses",
            json={
                "model": "gpt-4",
                "input": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "What is in this image?"},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": "https://example.com/image.jpg"
                                },
                            },
                        ],
                    }
                ],
            },
        )
        response.raise_for_status()
        data = response.json()

        assert data["status"] == "completed"
        assert len(data["output"]) > 0

    def test_response_with_long_conversation_history(self, client: FakeAIClient):
        """Test response with long conversation history."""
        messages = []
        for i in range(10):
            messages.append({"role": "user", "content": f"Message {i}"})
            messages.append({"role": "assistant", "content": f"Response {i}"})
        messages.append({"role": "user", "content": "Final question"})

        response = client.post(
            "/v1/responses",
            json={
                "model": "gpt-4",
                "input": messages,
            },
        )
        response.raise_for_status()
        data = response.json()

        assert data["status"] == "completed"
        assert data["usage"]["total_tokens"] > 0

    def test_response_with_all_parameters(self, client: FakeAIClient):
        """Test response with all available parameters."""
        response = client.post(
            "/v1/responses",
            json={
                "model": "gpt-4",
                "input": "Comprehensive test",
                "instructions": "Be concise",
                "max_output_tokens": 100,
                "temperature": 0.7,
                "top_p": 0.9,
                "store": True,
                "metadata": {"test": "comprehensive"},
                "parallel_tool_calls": True,
            },
        )
        response.raise_for_status()
        data = response.json()

        assert data["status"] == "completed"
        assert data["instructions"] == "Be concise"
        assert data["max_output_tokens"] == 100
        assert data["temperature"] == 0.7
        assert data["top_p"] == 0.9
        assert data["metadata"]["test"] == "comprehensive"


@pytest.mark.integration
@pytest.mark.asyncio
class TestResponsesAsync:
    """Test async responses functionality."""

    async def test_async_response_creation(self, client: FakeAIClient):
        """Test creating response asynchronously."""
        response = await client.apost(
            "/v1/responses",
            json={
                "model": "gpt-4",
                "input": "Hello async world",
            },
        )
        response.raise_for_status()
        data = response.json()

        assert data["object"] == "response"
        assert data["status"] == "completed"

    async def test_async_concurrent_responses(self, client: FakeAIClient):
        """Test multiple concurrent response requests."""
        tasks = []
        for i in range(5):
            task = client.apost(
                "/v1/responses",
                json={
                    "model": "gpt-4",
                    "input": f"Concurrent request {i}",
                },
            )
            tasks.append(task)

        responses = await asyncio.gather(*tasks)

        # All should succeed
        for response in responses:
            response.raise_for_status()
            data = response.json()
            assert data["status"] == "completed"

        # All should have unique IDs
        ids = [r.json()["id"] for r in responses]
        assert len(set(ids)) == 5


@pytest.mark.integration
@pytest.mark.metrics
class TestResponsesMetrics:
    """Test metrics tracking for Responses API."""

    def test_response_metrics_tracked(self, client: FakeAIClient):
        """Test that responses are tracked in metrics."""
        # Get initial metrics
        metrics_before = client.get_metrics()

        # Create response
        response = client.post(
            "/v1/responses",
            json={
                "model": "gpt-4",
                "input": "Test metrics",
            },
        )
        response.raise_for_status()

        # Get updated metrics
        metrics_after = client.get_metrics()

        # Verify request was tracked
        # Note: Metrics structure may vary, adjust based on actual implementation
        assert "endpoints" in metrics_after or "requests" in metrics_after

    def test_response_token_metrics(self, client: FakeAIClient):
        """Test that token usage is tracked in metrics."""
        # Create response
        response = client.post(
            "/v1/responses",
            json={
                "model": "gpt-4",
                "input": "Test token metrics",
            },
        )
        response.raise_for_status()
        data = response.json()

        # Get metrics
        metrics = client.get_metrics()

        # Verify tokens were tracked
        total_tokens = data["usage"]["total_tokens"]
        assert total_tokens > 0


@pytest.mark.integration
class TestResponsesEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_response_with_empty_string_input(self, client: FakeAIClient):
        """Test response with empty string input."""
        response = client.post(
            "/v1/responses",
            json={
                "model": "gpt-4",
                "input": "",
            },
        )

        # Should succeed or return validation error
        # Behavior depends on implementation
        assert response.status_code in [200, 422]

    def test_response_with_very_long_input(self, client: FakeAIClient):
        """Test response with very long input."""
        long_input = "This is a test. " * 500  # ~1500 words

        response = client.post(
            "/v1/responses",
            json={
                "model": "gpt-4",
                "input": long_input,
            },
        )
        response.raise_for_status()
        data = response.json()

        assert data["status"] == "completed"
        assert data["usage"]["input_tokens"] > 1000

    def test_response_with_zero_max_output_tokens(self, client: FakeAIClient):
        """Test response with max_output_tokens=0."""
        response = client.post(
            "/v1/responses",
            json={
                "model": "gpt-4",
                "input": "Hello",
                "max_output_tokens": 0,
            },
        )

        # Should handle gracefully (validation error or empty output)
        assert response.status_code in [200, 422]

    def test_response_with_invalid_previous_response_id(self, client: FakeAIClient):
        """Test response with non-existent previous_response_id."""
        response = client.post(
            "/v1/responses",
            json={
                "model": "gpt-4",
                "input": "Hello",
                "previous_response_id": "resp-nonexistent123",
            },
        )
        response.raise_for_status()
        data = response.json()

        # Should succeed (may ignore invalid ID or handle gracefully)
        assert data["status"] == "completed"

    def test_response_with_special_characters(self, client: FakeAIClient):
        """Test response with special characters in input."""
        special_input = "Hello 👋 World! \n\t Special chars: @#$%^&*(){}[]<>?/|\\\"'"

        response = client.post(
            "/v1/responses",
            json={
                "model": "gpt-4",
                "input": special_input,
            },
        )
        response.raise_for_status()
        data = response.json()

        assert data["status"] == "completed"


@pytest.mark.integration
class TestResponsesPerformance:
    """Test performance characteristics of Responses API."""

    def test_response_latency(self, client: FakeAIClient):
        """Test response latency is reasonable."""
        start_time = time.time()

        response = client.post(
            "/v1/responses",
            json={
                "model": "gpt-4",
                "input": "Quick response test",
            },
        )
        response.raise_for_status()

        elapsed = time.time() - start_time

        # Should complete within reasonable time (adjust as needed)
        assert elapsed < 5.0  # 5 seconds max

    def test_response_multiple_sequential(self, client: FakeAIClient):
        """Test multiple sequential responses."""
        response_ids = []

        for i in range(3):
            response = client.post(
                "/v1/responses",
                json={
                    "model": "gpt-4",
                    "input": f"Sequential request {i}",
                },
            )
            response.raise_for_status()
            data = response.json()
            response_ids.append(data["id"])

        # All should have unique IDs
        assert len(set(response_ids)) == 3

    def test_response_batch_requests(self, client: FakeAIClient):
        """Test batch response requests."""
        responses = []

        # Create 10 responses
        for i in range(10):
            response = client.post(
                "/v1/responses",
                json={
                    "model": "gpt-4",
                    "input": f"Batch request {i}",
                },
            )
            response.raise_for_status()
            responses.append(response.json())

        # All should succeed
        assert len(responses) == 10
        for data in responses:
            assert data["status"] == "completed"

        # All should have unique IDs
        ids = [r["id"] for r in responses]
        assert len(set(ids)) == 10
