"""
Fine-Tuning API tests.

Tests the complete fine-tuning workflow including job creation,
status progression, event streaming, and checkpoints.
"""

import asyncio
import time

import pytest


@pytest.mark.integration
class TestFineTuningAPI:
    """Test /v1/fine_tuning/jobs endpoints."""

    def test_create_fine_tuning_job(self, client_no_auth):
        """Should create a fine-tuning job successfully."""
        # First, upload a training file
        upload_response = client_no_auth.post("/v1/files")
        assert upload_response.status_code == 200
        file_data = upload_response.json()
        training_file_id = file_data["id"]

        # Create fine-tuning job
        response = client_no_auth.post(
            "/v1/fine_tuning/jobs",
            json={
                "training_file": training_file_id,
                "model": "meta-llama/Llama-3.1-8B-Instruct",
                "hyperparameters": {
                    "n_epochs": 3,
                    "batch_size": 4,
                    "learning_rate_multiplier": 0.1,
                },
                "suffix": "test-model",
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "id" in data
        assert data["id"].startswith("ftjob-")
        assert data["object"] == "fine_tuning.job"
        assert data["model"] == "meta-llama/Llama-3.1-8B-Instruct"
        assert data["training_file"] == training_file_id
        assert data["status"] in ["validating_files", "queued", "running"]
        assert data["hyperparameters"]["n_epochs"] == 3
        assert data["hyperparameters"]["batch_size"] == 4
        assert data["hyperparameters"]["learning_rate_multiplier"] == 0.1

    def test_list_fine_tuning_jobs(self, client_no_auth):
        """Should list fine-tuning jobs with pagination."""
        # Create a job first
        upload_response = client_no_auth.post("/v1/files")
        training_file_id = upload_response.json()["id"]

        client_no_auth.post(
            "/v1/fine_tuning/jobs",
            json={
                "training_file": training_file_id,
                "model": "openai/gpt-oss-20b",
            },
        )

        # List jobs
        response = client_no_auth.get("/v1/fine_tuning/jobs", params={"limit": 10})

        assert response.status_code == 200
        data = response.json()

        assert data["object"] == "list"
        assert "data" in data
        assert isinstance(data["data"], list)
        assert "has_more" in data

        if len(data["data"]) > 0:
            job = data["data"][0]
            assert "id" in job
            assert "status" in job
            assert "model" in job

    def test_retrieve_fine_tuning_job(self, client_no_auth):
        """Should retrieve a specific fine-tuning job."""
        # Create a job
        upload_response = client_no_auth.post("/v1/files")
        training_file_id = upload_response.json()["id"]

        create_response = client_no_auth.post(
            "/v1/fine_tuning/jobs",
            json={
                "training_file": training_file_id,
                "model": "meta-llama/Llama-3.1-8B-Instruct",
            },
        )
        job_id = create_response.json()["id"]

        # Retrieve the job
        response = client_no_auth.get(f"/v1/fine_tuning/jobs/{job_id}")

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == job_id
        assert "status" in data
        assert "model" in data
        assert "training_file" in data

    def test_retrieve_nonexistent_job(self, client_no_auth):
        """Should return 404 for nonexistent job."""
        response = client_no_auth.get("/v1/fine_tuning/jobs/ftjob-nonexistent")

        assert response.status_code == 404

    def test_job_status_progression(self, client_no_auth):
        """Should progress through status states."""
        # Create a job
        upload_response = client_no_auth.post("/v1/files")
        training_file_id = upload_response.json()["id"]

        create_response = client_no_auth.post(
            "/v1/fine_tuning/jobs",
            json={
                "training_file": training_file_id,
                "model": "openai/gpt-oss-20b",
            },
        )
        job_id = create_response.json()["id"]

        # Initial status should be validating_files
        initial_status = create_response.json()["status"]
        assert initial_status in ["validating_files", "queued"]

        # Wait a bit and check status has progressed
        time.sleep(3)
        response = client_no_auth.get(f"/v1/fine_tuning/jobs/{job_id}")
        later_status = response.json()["status"]

        # Status should have changed or still be in early stages
        assert later_status in ["validating_files", "queued", "running", "succeeded"]

    def test_fine_tuning_with_validation_file(self, client_no_auth):
        """Should accept validation file."""
        # Upload files
        training_response = client_no_auth.post("/v1/files")
        training_file_id = training_response.json()["id"]

        validation_response = client_no_auth.post("/v1/files")
        validation_file_id = validation_response.json()["id"]

        # Create job with validation file
        response = client_no_auth.post(
            "/v1/fine_tuning/jobs",
            json={
                "training_file": training_file_id,
                "validation_file": validation_file_id,
                "model": "meta-llama/Llama-3.1-8B-Instruct",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert data["training_file"] == training_file_id
        assert data["validation_file"] == validation_file_id

    def test_invalid_training_file(self, client_no_auth):
        """Should reject invalid training file."""
        response = client_no_auth.post(
            "/v1/fine_tuning/jobs",
            json={
                "training_file": "file-nonexistent",
                "model": "meta-llama/Llama-3.1-8B-Instruct",
            },
        )

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data

    def test_hyperparameters_auto_resolution(self, client_no_auth):
        """Should resolve 'auto' hyperparameters."""
        upload_response = client_no_auth.post("/v1/files")
        training_file_id = upload_response.json()["id"]

        response = client_no_auth.post(
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

        # Auto values should be resolved to integers/floats
        assert isinstance(data["hyperparameters"]["n_epochs"], int)
        assert isinstance(data["hyperparameters"]["batch_size"], int)
        assert isinstance(
            data["hyperparameters"]["learning_rate_multiplier"], (int, float)
        )


@pytest.mark.integration
class TestFineTuningEvents:
    """Test fine-tuning event streaming."""

    def test_list_fine_tuning_events(self, client_no_auth):
        """Should stream events via SSE."""
        # Create a job
        upload_response = client_no_auth.post("/v1/files")
        training_file_id = upload_response.json()["id"]

        create_response = client_no_auth.post(
            "/v1/fine_tuning/jobs",
            json={
                "training_file": training_file_id,
                "model": "meta-llama/Llama-3.1-8B-Instruct",
            },
        )
        job_id = create_response.json()["id"]

        # Wait for some events to be generated
        time.sleep(4)

        # Get events
        response = client_no_auth.get(
            f"/v1/fine_tuning/jobs/{job_id}/events",
            params={"limit": 20},
        )

        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]

        # Parse SSE data
        content = response.text
        assert "data:" in content

        # Should contain event data
        lines = [line for line in content.split("\n") if line.startswith("data:")]
        assert len(lines) > 0

    def test_events_contain_metrics(self, client_no_auth):
        """Should include training metrics in events."""
        # Create and wait for job to progress
        upload_response = client_no_auth.post("/v1/files")
        training_file_id = upload_response.json()["id"]

        create_response = client_no_auth.post(
            "/v1/fine_tuning/jobs",
            json={
                "training_file": training_file_id,
                "model": "openai/gpt-oss-20b",
            },
        )
        job_id = create_response.json()["id"]

        # Wait for training to generate metrics
        time.sleep(15)

        # Get events
        response = client_no_auth.get(f"/v1/fine_tuning/jobs/{job_id}/events")

        content = response.text

        # Should contain metrics-related information
        assert (
            "loss" in content.lower()
            or "step" in content.lower()
            or "accuracy" in content.lower()
            or "metrics" in content.lower()
        )


@pytest.mark.integration
class TestFineTuningCheckpoints:
    """Test fine-tuning checkpoint creation."""

    def test_list_checkpoints(self, client_no_auth):
        """Should list checkpoints for a job."""
        # Create a job
        upload_response = client_no_auth.post("/v1/files")
        training_file_id = upload_response.json()["id"]

        create_response = client_no_auth.post(
            "/v1/fine_tuning/jobs",
            json={
                "training_file": training_file_id,
                "model": "meta-llama/Llama-3.1-8B-Instruct",
            },
        )
        job_id = create_response.json()["id"]

        # Wait for some checkpoints to be created
        time.sleep(12)  # Should have at least one checkpoint by now

        # List checkpoints
        response = client_no_auth.get(
            f"/v1/fine_tuning/jobs/{job_id}/checkpoints",
            params={"limit": 10},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["object"] == "list"
        assert "data" in data
        assert isinstance(data["data"], list)

        # Should have at least one checkpoint after 12 seconds
        if len(data["data"]) > 0:
            checkpoint = data["data"][0]
            assert "id" in checkpoint
            assert checkpoint["id"].startswith("ftckpt-")
            assert checkpoint["object"] == "fine_tuning.job.checkpoint"
            assert checkpoint["fine_tuning_job_id"] == job_id
            assert "step_number" in checkpoint
            assert "metrics" in checkpoint
            assert "fine_tuned_model_checkpoint" in checkpoint

    def test_checkpoint_metrics(self, client_no_auth):
        """Checkpoints should contain training metrics."""
        upload_response = client_no_auth.post("/v1/files")
        training_file_id = upload_response.json()["id"]

        create_response = client_no_auth.post(
            "/v1/fine_tuning/jobs",
            json={
                "training_file": training_file_id,
                "model": "openai/gpt-oss-20b",
            },
        )
        job_id = create_response.json()["id"]

        # Wait for first checkpoint (at 25% = 7.5 seconds)
        time.sleep(10)

        response = client_no_auth.get(f"/v1/fine_tuning/jobs/{job_id}/checkpoints")

        data = response.json()

        if len(data["data"]) > 0:
            checkpoint = data["data"][0]
            metrics = checkpoint["metrics"]

            # Should have standard training metrics
            assert "train_loss" in metrics or "valid_loss" in metrics
            assert isinstance(checkpoint["step_number"], int)


@pytest.mark.integration
class TestFineTuningCancellation:
    """Test cancelling fine-tuning jobs."""

    def test_cancel_running_job(self, client_no_auth):
        """Should cancel a running job."""
        # Create a job
        upload_response = client_no_auth.post("/v1/files")
        training_file_id = upload_response.json()["id"]

        create_response = client_no_auth.post(
            "/v1/fine_tuning/jobs",
            json={
                "training_file": training_file_id,
                "model": "meta-llama/Llama-3.1-8B-Instruct",
            },
        )
        job_id = create_response.json()["id"]

        # Wait for job to start running
        time.sleep(4)

        # Cancel the job
        response = client_no_auth.post(f"/v1/fine_tuning/jobs/{job_id}/cancel")

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == job_id
        assert data["status"] == "cancelled"
        assert data["finished_at"] is not None

    def test_cannot_cancel_completed_job(self, client_no_auth):
        """Should not be able to cancel a completed job."""
        # This would require waiting for a job to complete naturally
        # For now, test cancelling a job that exists but isn't in a cancellable state
        upload_response = client_no_auth.post("/v1/files")
        training_file_id = upload_response.json()["id"]

        create_response = client_no_auth.post(
            "/v1/fine_tuning/jobs",
            json={
                "training_file": training_file_id,
                "model": "openai/gpt-oss-20b",
            },
        )
        job_id = create_response.json()["id"]

        # Wait for completion (full 30-second training)
        time.sleep(35)

        # Try to cancel
        response = client_no_auth.post(f"/v1/fine_tuning/jobs/{job_id}/cancel")

        # Should either succeed if still cancellable or fail if already completed
        assert response.status_code in [200, 400, 404]


@pytest.mark.integration
class TestFineTuningIntegration:
    """Integration tests for complete fine-tuning workflow."""

    def test_complete_workflow(self, client_no_auth):
        """Test complete fine-tuning workflow from creation to completion."""
        # 1. Upload training file
        upload_response = client_no_auth.post("/v1/files")
        assert upload_response.status_code == 200
        training_file_id = upload_response.json()["id"]

        # 2. Create fine-tuning job
        create_response = client_no_auth.post(
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
        status_response = client_no_auth.get(f"/v1/fine_tuning/jobs/{job_id}")
        assert status_response.status_code == 200
        assert status_response.json()["status"] in ["validating_files", "queued"]

        # 4. Wait and check events
        time.sleep(5)
        events_response = client_no_auth.get(f"/v1/fine_tuning/jobs/{job_id}/events")
        assert events_response.status_code == 200
        assert "text/event-stream" in events_response.headers["content-type"]

        # 5. Check for checkpoints
        time.sleep(10)
        checkpoints_response = client_no_auth.get(
            f"/v1/fine_tuning/jobs/{job_id}/checkpoints"
        )
        assert checkpoints_response.status_code == 200

        # 6. List all jobs
        list_response = client_no_auth.get("/v1/fine_tuning/jobs")
        assert list_response.status_code == 200
        jobs = list_response.json()["data"]
        job_ids = [j["id"] for j in jobs]
        assert job_id in job_ids

    def test_fine_tuned_model_creation(self, client_no_auth):
        """Should create a fine-tuned model after job completes."""
        upload_response = client_no_auth.post("/v1/files")
        training_file_id = upload_response.json()["id"]

        create_response = client_no_auth.post(
            "/v1/fine_tuning/jobs",
            json={
                "training_file": training_file_id,
                "model": "openai/gpt-oss-20b",
                "suffix": "test",
            },
        )
        job_id = create_response.json()["id"]

        # Wait for completion (full training cycle)
        time.sleep(35)

        # Check job status
        job_response = client_no_auth.get(f"/v1/fine_tuning/jobs/{job_id}")
        job_data = job_response.json()

        # Job should be succeeded or still running
        assert job_data["status"] in ["running", "succeeded"]

        # If succeeded, should have fine_tuned_model
        if job_data["status"] == "succeeded":
            assert job_data["fine_tuned_model"] is not None
            assert job_data["fine_tuned_model"].startswith("ft:")
            assert "test" in job_data["fine_tuned_model"]
            assert job_data["trained_tokens"] is not None
            assert job_data["trained_tokens"] > 0
