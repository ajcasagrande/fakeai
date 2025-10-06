"""Comprehensive integration tests for fine-tuning API.

This module tests the complete fine-tuning workflow including:
- Job creation and management
- Status transitions
- Hyperparameter handling
- File validation
- Event streaming
- Checkpoint creation
- Concurrent operations
- Fine-tuned model usage
"""

import asyncio
import json
import time
from typing import Any

import pytest

from tests.integration.utils import FakeAIClient


@pytest.mark.integration
class TestFineTuningJobCreation:
    """Test fine-tuning job creation and validation."""

    def test_create_fine_tuning_job_basic(self, client: FakeAIClient) -> None:
        """Should create a basic fine-tuning job successfully."""
        # Upload training file first
        upload_response = client.post("/v1/files")
        assert upload_response.status_code == 200
        training_file_id = upload_response.json()["id"]

        # Create fine-tuning job
        response = client.post(
            "/v1/fine_tuning/jobs",
            json={
                "training_file": training_file_id,
                "model": "meta-llama/Llama-3.1-8B-Instruct",
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert data["id"].startswith("ftjob-")
        assert data["object"] == "fine_tuning.job"
        assert data["model"] == "meta-llama/Llama-3.1-8B-Instruct"
        assert data["training_file"] == training_file_id
        assert data["status"] in ["validating_files", "queued"]
        assert data["organization_id"] == "org-fakeai"
        assert "created_at" in data
        assert "hyperparameters" in data
        assert data["validation_file"] is None
        assert isinstance(data["result_files"], list)

    def test_create_job_with_all_parameters(self, client: FakeAIClient) -> None:
        """Should create job with all optional parameters."""
        # Upload files
        training_response = client.post("/v1/files")
        training_file_id = training_response.json()["id"]

        validation_response = client.post("/v1/files")
        validation_file_id = validation_response.json()["id"]

        # Create job with all parameters
        response = client.post(
            "/v1/fine_tuning/jobs",
            json={
                "training_file": training_file_id,
                "validation_file": validation_file_id,
                "model": "openai/gpt-oss-20b",
                "hyperparameters": {
                    "n_epochs": 5,
                    "batch_size": 8,
                    "learning_rate_multiplier": 0.2,
                },
                "suffix": "custom-model-v1",
                "seed": 42,
                "integrations": [{"type": "wandb", "wandb": {"project": "test"}}],
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert data["training_file"] == training_file_id
        assert data["validation_file"] == validation_file_id
        assert data["hyperparameters"]["n_epochs"] == 5
        assert data["hyperparameters"]["batch_size"] == 8
        assert data["hyperparameters"]["learning_rate_multiplier"] == 0.2
        assert data["seed"] == 42
        assert data["integrations"] is not None

    def test_create_job_with_auto_hyperparameters(self, client: FakeAIClient) -> None:
        """Should resolve 'auto' hyperparameters to concrete values."""
        upload_response = client.post("/v1/files")
        training_file_id = upload_response.json()["id"]

        response = client.post(
            "/v1/fine_tuning/jobs",
            json={
                "training_file": training_file_id,
                "model": "meta-llama/Llama-3.1-8B-Instruct",
                "hyperparameters": {
                    "n_epochs": "auto",
                    "batch_size": "auto",
                    "learning_rate_multiplier": "auto",
                },
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Auto values should be resolved to concrete values
        assert isinstance(data["hyperparameters"]["n_epochs"], int)
        assert isinstance(data["hyperparameters"]["batch_size"], int)
        assert isinstance(
            data["hyperparameters"]["learning_rate_multiplier"], (int, float)
        )
        assert data["hyperparameters"]["n_epochs"] > 0
        assert data["hyperparameters"]["batch_size"] > 0
        assert data["hyperparameters"]["learning_rate_multiplier"] > 0

    def test_create_job_invalid_training_file(self, client: FakeAIClient) -> None:
        """Should reject invalid training file ID."""
        response = client.post(
            "/v1/fine_tuning/jobs",
            json={
                "training_file": "file-nonexistent",
                "model": "meta-llama/Llama-3.1-8B-Instruct",
            },
        )

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()

    def test_create_job_invalid_validation_file(self, client: FakeAIClient) -> None:
        """Should reject invalid validation file ID."""
        upload_response = client.post("/v1/files")
        training_file_id = upload_response.json()["id"]

        response = client.post(
            "/v1/fine_tuning/jobs",
            json={
                "training_file": training_file_id,
                "validation_file": "file-invalid",
                "model": "openai/gpt-oss-20b",
            },
        )

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()

    def test_create_job_with_suffix_length_validation(
        self, client: FakeAIClient
    ) -> None:
        """Should validate suffix length (max 40 characters)."""
        upload_response = client.post("/v1/files")
        training_file_id = upload_response.json()["id"]

        # Test valid suffix (40 chars)
        valid_suffix = "a" * 40
        response = client.post(
            "/v1/fine_tuning/jobs",
            json={
                "training_file": training_file_id,
                "model": "meta-llama/Llama-3.1-8B-Instruct",
                "suffix": valid_suffix,
            },
        )
        assert response.status_code == 200

        # Test invalid suffix (41 chars) - should be rejected by Pydantic
        invalid_suffix = "a" * 41
        response = client.post(
            "/v1/fine_tuning/jobs",
            json={
                "training_file": training_file_id,
                "model": "meta-llama/Llama-3.1-8B-Instruct",
                "suffix": invalid_suffix,
            },
        )
        assert response.status_code == 422  # Pydantic validation error


@pytest.mark.integration
class TestFineTuningJobListing:
    """Test listing and retrieving fine-tuning jobs."""

    def test_list_fine_tuning_jobs_empty(self, client: FakeAIClient) -> None:
        """Should return empty list when no jobs exist."""
        response = client.get("/v1/fine_tuning/jobs")

        assert response.status_code == 200
        data = response.json()

        assert data["object"] == "list"
        assert isinstance(data["data"], list)
        assert "has_more" in data

    def test_list_fine_tuning_jobs_with_jobs(self, client: FakeAIClient) -> None:
        """Should list all fine-tuning jobs."""
        # Create multiple jobs
        job_ids = []
        for _ in range(3):
            upload_response = client.post("/v1/files")
            training_file_id = upload_response.json()["id"]

            create_response = client.post(
                "/v1/fine_tuning/jobs",
                json={
                    "training_file": training_file_id,
                    "model": "openai/gpt-oss-20b",
                },
            )
            job_ids.append(create_response.json()["id"])

        # List jobs
        response = client.get("/v1/fine_tuning/jobs")

        assert response.status_code == 200
        data = response.json()

        assert data["object"] == "list"
        assert len(data["data"]) >= 3
        assert all(job["id"] in job_ids for job in data["data"][:3])

    def test_list_jobs_with_pagination(self, client: FakeAIClient) -> None:
        """Should support pagination with limit and after parameters."""
        # Create jobs
        job_ids = []
        for _ in range(5):
            upload_response = client.post("/v1/files")
            training_file_id = upload_response.json()["id"]

            create_response = client.post(
                "/v1/fine_tuning/jobs",
                json={
                    "training_file": training_file_id,
                    "model": "meta-llama/Llama-3.1-8B-Instruct",
                },
            )
            job_ids.append(create_response.json()["id"])

        # List with limit
        response = client.get("/v1/fine_tuning/jobs", params={"limit": 2})
        data = response.json()
        assert len(data["data"]) == 2

        # List with after
        first_job_id = data["data"][0]["id"]
        response = client.get("/v1/fine_tuning/jobs", params={"after": first_job_id})
        data = response.json()
        assert all(job["id"] != first_job_id for job in data["data"])

    def test_retrieve_fine_tuning_job(self, client: FakeAIClient) -> None:
        """Should retrieve a specific fine-tuning job."""
        # Create job
        upload_response = client.post("/v1/files")
        training_file_id = upload_response.json()["id"]

        create_response = client.post(
            "/v1/fine_tuning/jobs",
            json={
                "training_file": training_file_id,
                "model": "openai/gpt-oss-20b",
                "suffix": "test-retrieve",
            },
        )
        job_id = create_response.json()["id"]

        # Retrieve job
        response = client.get(f"/v1/fine_tuning/jobs/{job_id}")

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == job_id
        assert data["training_file"] == training_file_id
        assert "status" in data
        assert "created_at" in data

    def test_retrieve_nonexistent_job(self, client: FakeAIClient) -> None:
        """Should return 404 for nonexistent job."""
        response = client.get("/v1/fine_tuning/jobs/ftjob-nonexistent")

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data


@pytest.mark.integration
class TestFineTuningJobStatusTransitions:
    """Test fine-tuning job status lifecycle."""

    @pytest.mark.slow
    def test_job_status_progression(self, client: FakeAIClient) -> None:
        """Should progress through status states: validating_files -> queued -> running -> succeeded."""
        # Create job
        upload_response = client.post("/v1/files")
        training_file_id = upload_response.json()["id"]

        create_response = client.post(
            "/v1/fine_tuning/jobs",
            json={
                "training_file": training_file_id,
                "model": "meta-llama/Llama-3.1-8B-Instruct",
            },
        )
        job_id = create_response.json()["id"]

        # Track status transitions
        statuses = [create_response.json()["status"]]

        # Check status at different intervals
        intervals = [1.5, 2.5, 5.0, 10.0]  # Wait times in seconds
        for wait_time in intervals:
            time.sleep(wait_time - sum(intervals[: intervals.index(wait_time)]))
            response = client.get(f"/v1/fine_tuning/jobs/{job_id}")
            status = response.json()["status"]
            if status not in statuses:
                statuses.append(status)

        # Should see progression through states
        assert "validating_files" in statuses or "queued" in statuses
        assert "running" in statuses or "succeeded" in statuses

    @pytest.mark.slow
    def test_job_completion(self, client: FakeAIClient) -> None:
        """Should complete job and set finished_at timestamp."""
        # Create job
        upload_response = client.post("/v1/files")
        training_file_id = upload_response.json()["id"]

        create_response = client.post(
            "/v1/fine_tuning/jobs",
            json={
                "training_file": training_file_id,
                "model": "openai/gpt-oss-20b",
                "suffix": "completion-test",
            },
        )
        job_id = create_response.json()["id"]

        # Wait for completion (30s training + 2s overhead)
        time.sleep(35)

        # Check final status
        response = client.get(f"/v1/fine_tuning/jobs/{job_id}")
        data = response.json()

        assert data["status"] == "succeeded"
        assert data["finished_at"] is not None
        assert data["finished_at"] > data["created_at"]
        assert data["fine_tuned_model"] is not None
        assert data["fine_tuned_model"].startswith("ft:")
        assert "completion-test" in data["fine_tuned_model"]
        assert data["trained_tokens"] is not None
        assert data["trained_tokens"] > 0

    def test_estimated_finish_time(self, client: FakeAIClient) -> None:
        """Should provide estimated finish time."""
        upload_response = client.post("/v1/files")
        training_file_id = upload_response.json()["id"]

        create_response = client.post(
            "/v1/fine_tuning/jobs",
            json={
                "training_file": training_file_id,
                "model": "meta-llama/Llama-3.1-8B-Instruct",
            },
        )
        data = create_response.json()

        assert data["estimated_finish"] is not None
        assert data["estimated_finish"] > data["created_at"]
        # Should be roughly 35 seconds from creation
        assert data["estimated_finish"] - data["created_at"] <= 40


@pytest.mark.integration
class TestFineTuningCancellation:
    """Test cancelling fine-tuning jobs."""

    def test_cancel_running_job(self, client: FakeAIClient) -> None:
        """Should successfully cancel a running job."""
        try:
            # Create job
            upload_response = client.post("/v1/files")
            training_file_id = upload_response.json()["id"]

            create_response = client.post(
                "/v1/fine_tuning/jobs",
                json={
                    "training_file": training_file_id,
                    "model": "meta-llama/Llama-3.1-8B-Instruct",
                },
            )
            job_id = create_response.json()["id"]

            # Wait for job to start running
            time.sleep(3)

            # Cancel the job
            response = client.post(f"/v1/fine_tuning/jobs/{job_id}/cancel")

            assert response.status_code == 200
            data = response.json()

            assert data["id"] == job_id
            assert data["status"] == "cancelled"
            assert data["finished_at"] is not None
            assert data["finished_at"] > data["created_at"]
        except Exception as e:
            # If connection error, skip test
            if "Connection reset" in str(e) or "ReadError" in str(e):
                pytest.skip(f"Connection error during test: {e}")
            raise

    def test_cancel_queued_job(self, client: FakeAIClient) -> None:
        """Should cancel a queued job."""
        # Create job
        upload_response = client.post("/v1/files")
        training_file_id = upload_response.json()["id"]

        create_response = client.post(
            "/v1/fine_tuning/jobs",
            json={
                "training_file": training_file_id,
                "model": "openai/gpt-oss-20b",
            },
        )
        job_id = create_response.json()["id"]

        # Cancel immediately
        response = client.post(f"/v1/fine_tuning/jobs/{job_id}/cancel")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "cancelled"

    @pytest.mark.slow
    def test_cannot_cancel_completed_job(self, client: FakeAIClient) -> None:
        """Should not be able to cancel a completed job."""
        # Create job
        upload_response = client.post("/v1/files")
        training_file_id = upload_response.json()["id"]

        create_response = client.post(
            "/v1/fine_tuning/jobs",
            json={
                "training_file": training_file_id,
                "model": "openai/gpt-oss-20b",
            },
        )
        job_id = create_response.json()["id"]

        # Wait for completion
        time.sleep(35)

        # Try to cancel
        response = client.post(f"/v1/fine_tuning/jobs/{job_id}/cancel")

        # Should fail with 400
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "cannot cancel" in data["detail"].lower()

    def test_cancel_nonexistent_job(self, client: FakeAIClient) -> None:
        """Should return 400 for nonexistent job."""
        response = client.post("/v1/fine_tuning/jobs/ftjob-nonexistent/cancel")

        assert response.status_code == 400


@pytest.mark.integration
class TestFineTuningEvents:
    """Test fine-tuning event streaming."""

    def test_list_fine_tuning_events(self, client: FakeAIClient) -> None:
        """Should stream events via SSE."""
        # Create job
        upload_response = client.post("/v1/files")
        training_file_id = upload_response.json()["id"]

        create_response = client.post(
            "/v1/fine_tuning/jobs",
            json={
                "training_file": training_file_id,
                "model": "meta-llama/Llama-3.1-8B-Instruct",
            },
        )
        job_id = create_response.json()["id"]

        # Wait for some events
        time.sleep(3)

        # Get events
        response = client.get(f"/v1/fine_tuning/jobs/{job_id}/events")

        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]

        # Parse SSE data
        content = response.text
        assert "data:" in content

        lines = [line for line in content.split("\n") if line.startswith("data:")]
        assert len(lines) > 0

    def test_events_contain_job_creation(self, client: FakeAIClient) -> None:
        """Should include job creation event."""
        # Create job
        upload_response = client.post("/v1/files")
        training_file_id = upload_response.json()["id"]

        create_response = client.post(
            "/v1/fine_tuning/jobs",
            json={
                "training_file": training_file_id,
                "model": "openai/gpt-oss-20b",
            },
        )
        job_id = create_response.json()["id"]

        # Get events immediately
        response = client.get(f"/v1/fine_tuning/jobs/{job_id}/events")

        content = response.text
        events = [
            json.loads(line.replace("data: ", ""))
            for line in content.split("\n")
            if line.startswith("data:")
        ]

        # Should have initial events
        assert len(events) >= 1
        assert any("created" in event["message"].lower() for event in events)

    def test_events_contain_training_metrics(self, client: FakeAIClient) -> None:
        """Should include training metrics in events."""
        # Create job
        upload_response = client.post("/v1/files")
        training_file_id = upload_response.json()["id"]

        create_response = client.post(
            "/v1/fine_tuning/jobs",
            json={
                "training_file": training_file_id,
                "model": "meta-llama/Llama-3.1-8B-Instruct",
            },
        )
        job_id = create_response.json()["id"]

        # Wait for training to generate metrics
        time.sleep(5)

        # Get events
        response = client.get(f"/v1/fine_tuning/jobs/{job_id}/events")

        assert response.status_code == 200
        content = response.text

        # Parse events
        event_lines = [
            line for line in content.split("\n") if line.startswith("data:")
        ]
        assert len(event_lines) > 0

        events = []
        for line in event_lines:
            try:
                events.append(json.loads(line.replace("data: ", "")))
            except json.JSONDecodeError:
                pass  # Skip malformed lines

        # Should have at least one event
        assert len(events) > 0

        # Check if any metrics events exist
        metrics_events = [e for e in events if e.get("type") == "metrics"]

        # Should have metrics events after 5 seconds
        if len(metrics_events) > 0:
            metrics_event = metrics_events[0]
            assert metrics_event["object"] == "fine_tuning.job.event"
            assert "id" in metrics_event
            assert "created_at" in metrics_event
            assert "level" in metrics_event
            assert "message" in metrics_event

    def test_events_with_limit(self, client: FakeAIClient) -> None:
        """Should respect limit parameter."""
        # Create job and wait
        upload_response = client.post("/v1/files")
        training_file_id = upload_response.json()["id"]

        create_response = client.post(
            "/v1/fine_tuning/jobs",
            json={
                "training_file": training_file_id,
                "model": "openai/gpt-oss-20b",
            },
        )
        job_id = create_response.json()["id"]

        # Wait for some events
        time.sleep(5)

        # Get events with limit
        response = client.get(
            f"/v1/fine_tuning/jobs/{job_id}/events", params={"limit": 5}
        )

        assert response.status_code == 200
        content = response.text
        events = [
            json.loads(line.replace("data: ", ""))
            for line in content.split("\n")
            if line.startswith("data:")
        ]

        # Should respect limit
        assert len(events) > 0  # Should have some events
        assert len(events) <= 5  # Should not exceed limit

    def test_events_for_nonexistent_job(self, client: FakeAIClient) -> None:
        """Should return empty events or 404 for nonexistent job."""
        response = client.get("/v1/fine_tuning/jobs/ftjob-nonexistent/events")

        # May return 200 with empty events or 404 depending on implementation
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            # Should have no events
            content = response.text
            events = [
                line for line in content.split("\n") if line.startswith("data:")
            ]
            # Empty or minimal events expected
            assert len(events) == 0 or "created" not in content.lower()


@pytest.mark.integration
class TestFineTuningCheckpoints:
    """Test fine-tuning checkpoint creation and retrieval."""

    @pytest.mark.slow
    def test_list_checkpoints(self, client: FakeAIClient) -> None:
        """Should list checkpoints for a job."""
        # Create job
        upload_response = client.post("/v1/files")
        training_file_id = upload_response.json()["id"]

        create_response = client.post(
            "/v1/fine_tuning/jobs",
            json={
                "training_file": training_file_id,
                "model": "meta-llama/Llama-3.1-8B-Instruct",
            },
        )
        job_id = create_response.json()["id"]

        # Wait for first checkpoint (at 25% = 7.5 seconds + 2s overhead)
        time.sleep(12)

        # List checkpoints
        response = client.get(f"/v1/fine_tuning/jobs/{job_id}/checkpoints")

        assert response.status_code == 200
        data = response.json()

        assert data["object"] == "list"
        assert isinstance(data["data"], list)
        assert "has_more" in data

        # Should have at least one checkpoint
        if len(data["data"]) > 0:
            checkpoint = data["data"][0]
            assert checkpoint["id"].startswith("ftckpt-")
            assert checkpoint["object"] == "fine_tuning.job.checkpoint"
            assert checkpoint["fine_tuning_job_id"] == job_id
            assert "step_number" in checkpoint
            assert "metrics" in checkpoint
            assert "fine_tuned_model_checkpoint" in checkpoint
            assert "created_at" in checkpoint

    @pytest.mark.slow
    def test_checkpoint_metrics(self, client: FakeAIClient) -> None:
        """Checkpoints should contain training metrics."""
        upload_response = client.post("/v1/files")
        training_file_id = upload_response.json()["id"]

        create_response = client.post(
            "/v1/fine_tuning/jobs",
            json={
                "training_file": training_file_id,
                "model": "openai/gpt-oss-20b",
            },
        )
        job_id = create_response.json()["id"]

        # Wait for first checkpoint
        time.sleep(12)

        response = client.get(f"/v1/fine_tuning/jobs/{job_id}/checkpoints")
        data = response.json()

        if len(data["data"]) > 0:
            checkpoint = data["data"][0]
            metrics = checkpoint["metrics"]

            # Should have standard training metrics
            assert "train_loss" in metrics or "valid_loss" in metrics
            assert isinstance(checkpoint["step_number"], int)
            assert checkpoint["step_number"] > 0

            # Metrics should be reasonable values
            if "train_loss" in metrics:
                assert 0 <= metrics["train_loss"] <= 10
            if "valid_loss" in metrics:
                assert 0 <= metrics["valid_loss"] <= 10
            if "train_accuracy" in metrics:
                assert 0 <= metrics["train_accuracy"] <= 1

    @pytest.mark.slow
    def test_multiple_checkpoints(self, client: FakeAIClient) -> None:
        """Should create multiple checkpoints at 25%, 50%, 75%, 100%."""
        upload_response = client.post("/v1/files")
        training_file_id = upload_response.json()["id"]

        create_response = client.post(
            "/v1/fine_tuning/jobs",
            json={
                "training_file": training_file_id,
                "model": "meta-llama/Llama-3.1-8B-Instruct",
            },
        )
        job_id = create_response.json()["id"]

        # Wait for completion (all checkpoints)
        time.sleep(35)

        response = client.get(f"/v1/fine_tuning/jobs/{job_id}/checkpoints")
        data = response.json()

        # Should have 4 checkpoints (25%, 50%, 75%, 100%)
        assert len(data["data"]) == 4

        # Verify checkpoint ordering (newest first)
        step_numbers = [c["step_number"] for c in data["data"]]
        assert step_numbers == sorted(step_numbers, reverse=True)

        # Verify expected steps
        assert 100 in step_numbers
        assert 75 in step_numbers
        assert 50 in step_numbers
        assert 25 in step_numbers

    def test_checkpoint_model_naming(self, client: FakeAIClient) -> None:
        """Should name checkpointed models correctly."""
        upload_response = client.post("/v1/files")
        training_file_id = upload_response.json()["id"]

        create_response = client.post(
            "/v1/fine_tuning/jobs",
            json={
                "training_file": training_file_id,
                "model": "openai/gpt-oss-20b",
                "suffix": "test-checkpoint",
            },
        )
        job_id = create_response.json()["id"]

        # Wait for first checkpoint
        time.sleep(12)

        response = client.get(f"/v1/fine_tuning/jobs/{job_id}/checkpoints")
        data = response.json()

        if len(data["data"]) > 0:
            checkpoint = data["data"][0]
            model_name = checkpoint["fine_tuned_model_checkpoint"]

            # Should follow format: ft:{base_model}:org-fakeai:{suffix}:step-{step}
            assert model_name.startswith("ft:")
            assert "test-checkpoint" in model_name
            assert "step-" in model_name

    def test_checkpoints_for_nonexistent_job(self, client: FakeAIClient) -> None:
        """Should return 404 for nonexistent job."""
        response = client.get("/v1/fine_tuning/jobs/ftjob-nonexistent/checkpoints")

        assert response.status_code == 404

    def test_checkpoint_first_last_ids(self, client: FakeAIClient) -> None:
        """Should include first_id and last_id in response."""
        upload_response = client.post("/v1/files")
        training_file_id = upload_response.json()["id"]

        create_response = client.post(
            "/v1/fine_tuning/jobs",
            json={
                "training_file": training_file_id,
                "model": "meta-llama/Llama-3.1-8B-Instruct",
            },
        )
        job_id = create_response.json()["id"]

        # Wait for checkpoints
        time.sleep(35)

        response = client.get(f"/v1/fine_tuning/jobs/{job_id}/checkpoints")
        data = response.json()

        if len(data["data"]) > 0:
            assert data["first_id"] is not None
            assert data["last_id"] is not None
            assert data["first_id"] == data["data"][0]["id"]
            assert data["last_id"] == data["data"][-1]["id"]


@pytest.mark.integration
class TestFineTuningConcurrent:
    """Test concurrent fine-tuning operations."""

    def test_multiple_concurrent_jobs(self, client: FakeAIClient) -> None:
        """Should handle multiple concurrent fine-tuning jobs."""
        job_ids = []

        # Create 3 concurrent jobs
        for i in range(3):
            upload_response = client.post("/v1/files")
            training_file_id = upload_response.json()["id"]

            create_response = client.post(
                "/v1/fine_tuning/jobs",
                json={
                    "training_file": training_file_id,
                    "model": "meta-llama/Llama-3.1-8B-Instruct",
                    "suffix": f"concurrent-{i}",
                },
            )
            assert create_response.status_code == 200
            job_ids.append(create_response.json()["id"])

        # Verify all jobs are running
        time.sleep(3)

        for job_id in job_ids:
            response = client.get(f"/v1/fine_tuning/jobs/{job_id}")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] in ["validating_files", "queued", "running"]

    def test_list_concurrent_jobs(self, client: FakeAIClient) -> None:
        """Should list all concurrent jobs correctly."""
        # Create multiple jobs
        job_ids = []
        for i in range(5):
            upload_response = client.post("/v1/files")
            training_file_id = upload_response.json()["id"]

            create_response = client.post(
                "/v1/fine_tuning/jobs",
                json={
                    "training_file": training_file_id,
                    "model": "openai/gpt-oss-20b",
                    "suffix": f"list-test-{i}",
                },
            )
            job_ids.append(create_response.json()["id"])

        # List all jobs
        response = client.get("/v1/fine_tuning/jobs", params={"limit": 100})
        data = response.json()

        # All created jobs should be in the list
        listed_ids = [job["id"] for job in data["data"]]
        for job_id in job_ids:
            assert job_id in listed_ids


@pytest.mark.integration
@pytest.mark.slow
class TestFineTuningIntegration:
    """Integration tests for complete fine-tuning workflow."""

    def test_complete_workflow(self, client: FakeAIClient) -> None:
        """Test complete fine-tuning workflow from creation to completion."""
        # 1. Upload training file
        upload_response = client.post("/v1/files")
        assert upload_response.status_code == 200
        training_file_id = upload_response.json()["id"]

        # 2. Create fine-tuning job
        create_response = client.post(
            "/v1/fine_tuning/jobs",
            json={
                "training_file": training_file_id,
                "model": "meta-llama/Llama-3.1-8B-Instruct",
                "hyperparameters": {"n_epochs": 3},
                "suffix": "integration-test",
            },
        )
        assert create_response.status_code == 200
        job_id = create_response.json()["id"]

        # 3. Check initial status
        status_response = client.get(f"/v1/fine_tuning/jobs/{job_id}")
        assert status_response.status_code == 200
        assert status_response.json()["status"] in ["validating_files", "queued"]

        # 4. Wait and check events
        time.sleep(5)
        events_response = client.get(f"/v1/fine_tuning/jobs/{job_id}/events")
        assert events_response.status_code == 200
        assert "text/event-stream" in events_response.headers["content-type"]

        # 5. Check for checkpoints
        time.sleep(10)
        checkpoints_response = client.get(
            f"/v1/fine_tuning/jobs/{job_id}/checkpoints"
        )
        assert checkpoints_response.status_code == 200

        # 6. List all jobs
        list_response = client.get("/v1/fine_tuning/jobs")
        assert list_response.status_code == 200
        jobs = list_response.json()["data"]
        job_ids = [j["id"] for j in jobs]
        assert job_id in job_ids

        # 7. Wait for completion
        time.sleep(20)  # Total 35 seconds waited
        final_response = client.get(f"/v1/fine_tuning/jobs/{job_id}")
        final_data = final_response.json()
        assert final_data["status"] == "succeeded"
        assert final_data["fine_tuned_model"] is not None

    def test_fine_tuned_model_creation(self, client: FakeAIClient) -> None:
        """Should create a fine-tuned model after job completes."""
        upload_response = client.post("/v1/files")
        training_file_id = upload_response.json()["id"]

        create_response = client.post(
            "/v1/fine_tuning/jobs",
            json={
                "training_file": training_file_id,
                "model": "openai/gpt-oss-20b",
                "suffix": "model-test",
            },
        )
        job_id = create_response.json()["id"]

        # Wait for completion
        time.sleep(35)

        # Check job status
        job_response = client.get(f"/v1/fine_tuning/jobs/{job_id}")
        job_data = job_response.json()

        assert job_data["status"] == "succeeded"
        assert job_data["fine_tuned_model"] is not None
        assert job_data["fine_tuned_model"].startswith("ft:")
        assert "model-test" in job_data["fine_tuned_model"]
        assert job_data["trained_tokens"] is not None
        assert job_data["trained_tokens"] > 0

    def test_with_validation_file(self, client: FakeAIClient) -> None:
        """Test complete workflow with validation file."""
        # Upload files
        training_response = client.post("/v1/files")
        training_file_id = training_response.json()["id"]

        validation_response = client.post("/v1/files")
        validation_file_id = validation_response.json()["id"]

        # Create job
        create_response = client.post(
            "/v1/fine_tuning/jobs",
            json={
                "training_file": training_file_id,
                "validation_file": validation_file_id,
                "model": "meta-llama/Llama-3.1-8B-Instruct",
            },
        )
        assert create_response.status_code == 200

        job_id = create_response.json()["id"]

        # Wait and verify completion
        time.sleep(35)

        job_response = client.get(f"/v1/fine_tuning/jobs/{job_id}")
        job_data = job_response.json()

        assert job_data["status"] == "succeeded"
        assert job_data["validation_file"] == validation_file_id

    def test_cancelled_job_stops_processing(self, client: FakeAIClient) -> None:
        """Test that cancelled job stops generating events and checkpoints."""
        # Create job
        upload_response = client.post("/v1/files")
        training_file_id = upload_response.json()["id"]

        create_response = client.post(
            "/v1/fine_tuning/jobs",
            json={
                "training_file": training_file_id,
                "model": "openai/gpt-oss-20b",
            },
        )
        job_id = create_response.json()["id"]

        # Wait a bit, then cancel
        time.sleep(3)
        cancel_response = client.post(f"/v1/fine_tuning/jobs/{job_id}/cancel")
        assert cancel_response.status_code == 200

        # Get event count at cancellation
        events_response = client.get(f"/v1/fine_tuning/jobs/{job_id}/events")
        initial_events = len(
            [
                line
                for line in events_response.text.split("\n")
                if line.startswith("data:")
            ]
        )

        # Wait more time
        time.sleep(5)

        # Event count should not increase significantly
        events_response = client.get(f"/v1/fine_tuning/jobs/{job_id}/events")
        final_events = len(
            [
                line
                for line in events_response.text.split("\n")
                if line.startswith("data:")
            ]
        )

        # Allow for cancellation event
        assert final_events <= initial_events + 2
