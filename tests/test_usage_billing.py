"""
Tests for Usage and Billing Tracking API.

This module tests the comprehensive usage tracking and billing API
implementation for FakeAI.
"""

#  SPDX-License-Identifier: Apache-2.0

import time

import pytest

from fakeai.config import AppConfig
from fakeai.fakeai_service import FakeAIService, UsageTracker
from fakeai.models import (
    ChatCompletionRequest,
    EmbeddingRequest,
    ImageGenerationRequest,
    Message,
    Role,
)


@pytest.fixture
def config():
    """Create test configuration."""
    return AppConfig(response_delay=0.0, debug=True)


@pytest.fixture
def service(config):
    """Create FakeAI service."""
    return FakeAIService(config)


@pytest.fixture
def usage_tracker():
    """Create usage tracker."""
    return UsageTracker()


class TestUsageTracker:
    """Test UsageTracker class functionality."""

    def test_initialization(self, usage_tracker):
        """Test UsageTracker initialization."""
        assert isinstance(usage_tracker.usage_records, list)
        assert len(usage_tracker.usage_records) == 0
        assert "openai/gpt-oss-120b" in usage_tracker.MODEL_PRICING
        assert "sentence-transformers/all-mpnet-base-v2" in usage_tracker.MODEL_PRICING

    def test_track_usage(self, usage_tracker):
        """Test tracking usage records."""
        usage_tracker.track_usage(
            endpoint="/v1/chat/completions",
            model="openai/gpt-oss-120b",
            input_tokens=100,
            output_tokens=50,
            cached_tokens=20,
            project_id="proj-123",
            user_id="user-456",
        )

        assert len(usage_tracker.usage_records) == 1
        record = usage_tracker.usage_records[0]
        assert record["endpoint"] == "/v1/chat/completions"
        assert record["model"] == "openai/gpt-oss-120b"
        assert record["input_tokens"] == 100
        assert record["output_tokens"] == 50
        assert record["cached_tokens"] == 20
        assert record["project_id"] == "proj-123"
        assert record["user_id"] == "user-456"
        assert "timestamp" in record

    def test_calculate_cost_gpt4(self, usage_tracker):
        """Test cost calculation for GPT-4."""
        # GPT-4: $30 per 1M input, $60 per 1M output
        cost = usage_tracker.calculate_cost("openai/gpt-oss-120b", 1_000_000, 1_000_000)
        assert cost == 90.0  # $30 + $60

    def test_calculate_cost_gpt35_turbo(self, usage_tracker):
        """Test cost calculation for GPT-3.5-turbo."""
        # GPT-3.5-turbo: $0.50 per 1M input, $1.50 per 1M output
        cost = usage_tracker.calculate_cost(
            "meta-llama/Llama-3.1-8B-Instruct", 1_000_000, 1_000_000
        )
        assert cost == 2.0  # $0.50 + $1.50

    def test_calculate_cost_embeddings(self, usage_tracker):
        """Test cost calculation for embeddings."""
        # sentence-transformers/all-mpnet-base-v2: $0.10 per 1M tokens
        cost = usage_tracker.calculate_cost(
            "sentence-transformers/all-mpnet-base-v2", 1_000_000, 0
        )
        assert cost == 0.10

    def test_calculate_cost_small_amounts(self, usage_tracker):
        """Test cost calculation for small token amounts."""
        # 1000 input, 500 output tokens with GPT-4
        cost = usage_tracker.calculate_cost("openai/gpt-oss-120b", 1000, 500)
        expected = (1000 / 1_000_000) * 30.0 + (500 / 1_000_000) * 60.0
        assert abs(cost - expected) < 0.0001

    def test_calculate_cost_unknown_model(self, usage_tracker):
        """Test cost calculation for unknown model uses default pricing."""
        cost = usage_tracker.calculate_cost("unknown-model", 1_000_000, 1_000_000)
        assert cost == 3.0  # Default: $1 input, $2 output

    def test_get_usage_by_time_bucket_basic(self, usage_tracker):
        """Test basic time bucket aggregation."""
        current_time = time.time()

        # Add some usage records
        usage_tracker.track_usage(
            endpoint="/v1/chat/completions",
            model="openai/gpt-oss-120b",
            input_tokens=100,
            output_tokens=50,
        )
        usage_tracker.track_usage(
            endpoint="/v1/chat/completions",
            model="openai/gpt-oss-120b",
            input_tokens=200,
            output_tokens=100,
        )

        # Get buckets
        buckets = usage_tracker.get_usage_by_time_bucket(
            start_time=int(current_time) - 3600,
            end_time=int(current_time) + 3600,
            bucket_size="1h",
        )

        assert len(buckets) > 0
        bucket = buckets[0]
        assert bucket["input_tokens"] == 300
        assert bucket["output_tokens"] == 150
        assert bucket["num_requests"] == 2

    def test_get_usage_by_time_bucket_multiple_buckets(self, usage_tracker):
        """Test aggregation into multiple time buckets."""
        # Create records at different times (simulate by manipulating timestamps)
        base_time = int(time.time())

        # Manually create records with specific timestamps
        usage_tracker.usage_records.append(
            {
                "timestamp": base_time - 7200,  # 2 hours ago
                "endpoint": "/v1/chat/completions",
                "model": "openai/gpt-oss-120b",
                "input_tokens": 100,
                "output_tokens": 50,
                "cached_tokens": 0,
                "project_id": None,
                "user_id": None,
                "num_requests": 1,
            }
        )
        usage_tracker.usage_records.append(
            {
                "timestamp": base_time,  # Now
                "endpoint": "/v1/chat/completions",
                "model": "openai/gpt-oss-120b",
                "input_tokens": 200,
                "output_tokens": 100,
                "cached_tokens": 0,
                "project_id": None,
                "user_id": None,
                "num_requests": 1,
            }
        )

        # Get hourly buckets
        buckets = usage_tracker.get_usage_by_time_bucket(
            start_time=base_time - 7200,
            end_time=base_time + 3600,
            bucket_size="1h",
        )

        # Should have at least 2 buckets
        assert len(buckets) >= 2

    def test_get_usage_by_time_bucket_project_filter(self, usage_tracker):
        """Test filtering by project ID."""
        current_time = time.time()

        usage_tracker.track_usage(
            endpoint="/v1/chat/completions",
            model="openai/gpt-oss-120b",
            input_tokens=100,
            output_tokens=50,
            project_id="proj-123",
        )
        usage_tracker.track_usage(
            endpoint="/v1/chat/completions",
            model="openai/gpt-oss-120b",
            input_tokens=200,
            output_tokens=100,
            project_id="proj-456",
        )

        # Filter by project
        buckets = usage_tracker.get_usage_by_time_bucket(
            start_time=int(current_time) - 3600,
            end_time=int(current_time) + 3600,
            bucket_size="1h",
            project_id="proj-123",
        )

        assert len(buckets) > 0
        bucket = buckets[0]
        assert bucket["input_tokens"] == 100
        assert bucket["output_tokens"] == 50

    def test_get_usage_by_time_bucket_model_filter(self, usage_tracker):
        """Test filtering by model."""
        current_time = time.time()

        usage_tracker.track_usage(
            endpoint="/v1/chat/completions",
            model="openai/gpt-oss-120b",
            input_tokens=100,
            output_tokens=50,
        )
        usage_tracker.track_usage(
            endpoint="/v1/chat/completions",
            model="meta-llama/Llama-3.1-8B-Instruct",
            input_tokens=200,
            output_tokens=100,
        )

        # Filter by model
        buckets = usage_tracker.get_usage_by_time_bucket(
            start_time=int(current_time) - 3600,
            end_time=int(current_time) + 3600,
            bucket_size="1h",
            model="openai/gpt-oss-120b",
        )

        assert len(buckets) > 0
        bucket = buckets[0]
        assert bucket["input_tokens"] == 100
        assert bucket["output_tokens"] == 50

    def test_get_costs_by_time_bucket(self, usage_tracker):
        """Test cost aggregation by time bucket."""
        current_time = time.time()

        usage_tracker.track_usage(
            endpoint="/v1/chat/completions",
            model="openai/gpt-oss-120b",
            input_tokens=1000,
            output_tokens=500,
        )
        usage_tracker.track_usage(
            endpoint="/v1/embeddings",
            model="sentence-transformers/all-mpnet-base-v2",
            input_tokens=2000,
            output_tokens=0,
        )

        buckets = usage_tracker.get_costs_by_time_bucket(
            start_time=int(current_time) - 3600,
            end_time=int(current_time) + 3600,
            bucket_size="1h",
        )

        assert len(buckets) > 0
        bucket = buckets[0]
        assert "results" in bucket

        # Check for line items
        line_items = {r["line_item"] for r in bucket["results"]}
        assert "completions" in line_items
        assert "embeddings" in line_items

    def test_get_costs_by_time_bucket_project_grouping(self, usage_tracker):
        """Test cost aggregation with project grouping."""
        current_time = time.time()

        usage_tracker.track_usage(
            endpoint="/v1/chat/completions",
            model="openai/gpt-oss-120b",
            input_tokens=1000,
            output_tokens=500,
            project_id="proj-123",
        )
        usage_tracker.track_usage(
            endpoint="/v1/chat/completions",
            model="openai/gpt-oss-120b",
            input_tokens=2000,
            output_tokens=1000,
            project_id="proj-456",
        )

        buckets = usage_tracker.get_costs_by_time_bucket(
            start_time=int(current_time) - 3600,
            end_time=int(current_time) + 3600,
            bucket_size="1h",
        )

        assert len(buckets) > 0
        bucket = buckets[0]

        # Should have separate results for each project
        project_ids = {r.get("project_id") for r in bucket["results"]}
        assert "proj-123" in project_ids
        assert "proj-456" in project_ids


class TestUsageTrackingIntegration:
    """Test integration of usage tracking with service methods."""

    @pytest.mark.asyncio
    async def test_chat_completion_tracks_usage(self, service):
        """Test that chat completions track usage."""
        request = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[Message(role=Role.USER, content="Hello, how are you?")],
        )

        initial_count = len(service.usage_tracker.usage_records)
        response = await service.create_chat_completion(request)

        # Check usage was tracked
        assert len(service.usage_tracker.usage_records) == initial_count + 1
        record = service.usage_tracker.usage_records[-1]
        assert record["endpoint"] == "/v1/chat/completions"
        assert record["model"] == "openai/gpt-oss-120b"
        assert record["input_tokens"] > 0
        assert record["output_tokens"] > 0

    @pytest.mark.asyncio
    async def test_embeddings_track_usage(self, service):
        """Test that embeddings track usage."""
        request = EmbeddingRequest(
            model="sentence-transformers/all-mpnet-base-v2",
            input="Hello world",
        )

        initial_count = len(service.usage_tracker.usage_records)
        response = await service.create_embedding(request)

        # Check usage was tracked
        assert len(service.usage_tracker.usage_records) == initial_count + 1
        record = service.usage_tracker.usage_records[-1]
        assert record["endpoint"] == "/v1/embeddings"
        assert record["model"] == "sentence-transformers/all-mpnet-base-v2"
        assert record["input_tokens"] > 0
        assert record["output_tokens"] == 0

    @pytest.mark.asyncio
    async def test_images_track_usage(self, service):
        """Test that image generation tracks usage."""
        request = ImageGenerationRequest(
            model="stabilityai/stable-diffusion-2-1",
            prompt="A beautiful sunset",
            n=2,
        )

        initial_count = len(service.usage_tracker.usage_records)
        response = await service.generate_images(request)

        # Check usage was tracked
        assert len(service.usage_tracker.usage_records) == initial_count + 1
        record = service.usage_tracker.usage_records[-1]
        assert record["endpoint"] == "/v1/images/generations"
        assert record["model"] == "stabilityai/stable-diffusion-2-1"
        assert record["num_requests"] == 2

    @pytest.mark.asyncio
    async def test_chat_completion_with_metadata(self, service):
        """Test tracking with metadata (project_id)."""
        request = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[Message(role=Role.USER, content="Hello")],
            metadata={"project_id": "proj-test-123"},
            user="user-test-456",
        )

        response = await service.create_chat_completion(request)

        # Check metadata was tracked
        record = service.usage_tracker.usage_records[-1]
        assert record["project_id"] == "proj-test-123"
        assert record["user_id"] == "user-test-456"


class TestUsageAPIMethods:
    """Test usage API methods in FakeAI service."""

    @pytest.mark.asyncio
    async def test_get_completions_usage(self, service):
        """Test get_completions_usage API method."""
        # Create some usage
        request = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[Message(role=Role.USER, content="Test")],
        )
        await service.create_chat_completion(request)

        current_time = int(time.time())
        response = await service.get_completions_usage(
            start_time=current_time - 3600,
            end_time=current_time + 3600,
            bucket_width="1h",
        )

        assert response.object == "page"
        assert len(response.data) > 0
        bucket = response.data[0]
        assert bucket.object == "bucket"
        assert len(bucket.results) > 0
        result = bucket.results[0]
        assert result.input_tokens > 0
        assert result.num_model_requests > 0

    @pytest.mark.asyncio
    async def test_get_embeddings_usage(self, service):
        """Test get_embeddings_usage API method."""
        # Create some usage
        request = EmbeddingRequest(
            model="sentence-transformers/all-mpnet-base-v2",
            input="Test text",
        )
        await service.create_embedding(request)

        current_time = int(time.time())
        response = await service.get_embeddings_usage(
            start_time=current_time - 3600,
            end_time=current_time + 3600,
            bucket_width="1h",
        )

        assert response.object == "page"
        assert len(response.data) > 0

    @pytest.mark.asyncio
    async def test_get_costs(self, service):
        """Test get_costs API method."""
        # Create some usage
        request = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[Message(role=Role.USER, content="Test")],
        )
        await service.create_chat_completion(request)

        current_time = int(time.time())
        response = await service.get_costs(
            start_time=current_time - 3600,
            end_time=current_time + 3600,
            bucket_width="1h",
        )

        assert response.object == "page"
        assert len(response.data) > 0
        bucket = response.data[0]
        assert bucket.object == "bucket"
        assert len(bucket.results) > 0

        # Check cost calculation
        result = bucket.results[0]
        assert result.amount.value > 0
        assert result.amount.currency == "usd"
        assert result.line_item == "completions"

    @pytest.mark.asyncio
    async def test_get_costs_with_project_filter(self, service):
        """Test get_costs with project filter."""
        # Create usage for different projects
        request1 = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[Message(role=Role.USER, content="Test 1")],
            metadata={"project_id": "proj-A"},
        )
        await service.create_chat_completion(request1)

        request2 = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[Message(role=Role.USER, content="Test 2")],
            metadata={"project_id": "proj-B"},
        )
        await service.create_chat_completion(request2)

        current_time = int(time.time())

        # Filter by project A
        response = await service.get_costs(
            start_time=current_time - 3600,
            end_time=current_time + 3600,
            bucket_width="1h",
            project_id="proj-A",
        )

        # Should only have costs for project A
        assert len(response.data) > 0
        bucket = response.data[0]
        for result in bucket.results:
            if result.project_id is not None:
                assert result.project_id == "proj-A"

    @pytest.mark.asyncio
    async def test_multiple_endpoints_mixed_usage(self, service):
        """Test tracking multiple different API endpoints."""
        # Chat completion
        chat_req = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[Message(role=Role.USER, content="Hello")],
        )
        await service.create_chat_completion(chat_req)

        # Embeddings
        embed_req = EmbeddingRequest(
            model="sentence-transformers/all-mpnet-base-v2",
            input="Test",
        )
        await service.create_embedding(embed_req)

        # Images
        image_req = ImageGenerationRequest(
            model="stabilityai/stable-diffusion-2-1",
            prompt="A cat",
            n=1,
        )
        await service.generate_images(image_req)

        # Get costs - should have multiple line items
        current_time = int(time.time())
        response = await service.get_costs(
            start_time=current_time - 3600,
            end_time=current_time + 3600,
            bucket_width="1h",
        )

        assert len(response.data) > 0
        bucket = response.data[0]
        line_items = {r.line_item for r in bucket.results}

        assert "completions" in line_items
        assert "embeddings" in line_items
        assert "images" in line_items


class TestBucketSizes:
    """Test different time bucket sizes."""

    def test_bucket_size_1m(self, usage_tracker):
        """Test 1-minute bucket aggregation."""
        current_time = int(time.time())
        usage_tracker.track_usage(
            endpoint="/v1/chat/completions",
            model="openai/gpt-oss-120b",
            input_tokens=100,
            output_tokens=50,
        )

        buckets = usage_tracker.get_usage_by_time_bucket(
            start_time=current_time - 300,
            end_time=current_time + 300,
            bucket_size="1m",
        )

        assert len(buckets) > 0
        # Each bucket should be 60 seconds
        bucket = buckets[0]
        assert bucket["end_time"] - bucket["start_time"] == 60

    def test_bucket_size_1h(self, usage_tracker):
        """Test 1-hour bucket aggregation."""
        current_time = int(time.time())
        usage_tracker.track_usage(
            endpoint="/v1/chat/completions",
            model="openai/gpt-oss-120b",
            input_tokens=100,
            output_tokens=50,
        )

        buckets = usage_tracker.get_usage_by_time_bucket(
            start_time=current_time - 7200,
            end_time=current_time + 7200,
            bucket_size="1h",
        )

        assert len(buckets) > 0
        # Each bucket should be 3600 seconds
        bucket = buckets[0]
        assert bucket["end_time"] - bucket["start_time"] == 3600

    def test_bucket_size_1d(self, usage_tracker):
        """Test 1-day bucket aggregation."""
        current_time = int(time.time())
        usage_tracker.track_usage(
            endpoint="/v1/chat/completions",
            model="openai/gpt-oss-120b",
            input_tokens=100,
            output_tokens=50,
        )

        buckets = usage_tracker.get_usage_by_time_bucket(
            start_time=current_time - 86400,
            end_time=current_time + 86400,
            bucket_size="1d",
        )

        assert len(buckets) > 0
        # Each bucket should be 86400 seconds
        bucket = buckets[0]
        assert bucket["end_time"] - bucket["start_time"] == 86400
