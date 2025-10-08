"""
Fine-Tuning Service

This module provides the fine-tuning service for managing fine-tuning jobs,
events, checkpoints, and background processing with realistic training simulation.
"""

#  SPDX-License-Identifier: Apache-2.0

import asyncio
import json
import logging
import random
import time
import uuid
from collections import defaultdict
from typing import AsyncGenerator

from fakeai.config import AppConfig
from fakeai.metrics import MetricsTracker
from fakeai.models.fine_tuning import (
    FineTuningCheckpoint,
    FineTuningCheckpointList,
    FineTuningEvent,
    FineTuningJob,
    FineTuningJobList,
    FineTuningJobRequest,
    Hyperparameters,
)

logger = logging.getLogger(__name__)


class FineTuningService:
    """
    Service for managing fine-tuning jobs.

    Features:
    - Create and manage fine-tuning jobs
    - Background async processing with realistic training simulation
    - Event streaming via Server-Sent Events (SSE)
    - Checkpoint management at 25%, 50%, 75%, 100%
    - Lifecycle: validating_files -> queued -> running -> succeeded
    - Cancellation support
    """

    def __init__(
        self,
        config: AppConfig,
        metrics_tracker: MetricsTracker,
        file_storage: dict,
    ):
        """
        Initialize the fine-tuning service.

        Args:
            config: Application configuration
            metrics_tracker: Metrics tracking singleton
            file_storage: Reference to file storage (for validation)
        """
        self.config = config
        self.metrics_tracker = metrics_tracker
        self.file_storage = file_storage

        # In-memory storage
        self.fine_tuning_jobs: dict[str, FineTuningJob] = {}
        self.fine_tuning_events: dict[str,
                                      list[FineTuningEvent]] = defaultdict(list)
        self.fine_tuning_checkpoints: dict[str, list[FineTuningCheckpoint]] = (
            defaultdict(list)
        )
        self.fine_tuning_tasks: dict[str, asyncio.Task] = {}

        logger.info("FineTuningService initialized")

    async def create_fine_tuning_job(
        self, request: FineTuningJobRequest
    ) -> FineTuningJob:
        """
        Create a new fine-tuning job.

        Args:
            request: Fine-tuning job creation request

        Returns:
            Created FineTuningJob object

        Raises:
            ValueError: If training file not found or validation file not found
        """
        # Validate training file exists
        training_file = next(
            (f for f in self.file_storage if f.id == request.training_file), None)
        if not training_file:
            raise ValueError(
                f"Training file {
                    request.training_file} not found")

        # Validate validation file if provided
        if request.validation_file:
            validation_file = next(
                (f for f in self.file_storage if f.id == request.validation_file), None)
            if not validation_file:
                raise ValueError(
                    f"Validation file {
                        request.validation_file} not found")

        # Resolve "auto" hyperparameters
        hyperparameters = request.hyperparameters or Hyperparameters()
        resolved_hyperparameters = Hyperparameters(
            n_epochs=(
                3 if hyperparameters.n_epochs == "auto" else hyperparameters.n_epochs
            ),
            batch_size=(
                4
                if hyperparameters.batch_size == "auto"
                else hyperparameters.batch_size
            ),
            learning_rate_multiplier=(
                0.1
                if hyperparameters.learning_rate_multiplier == "auto"
                else hyperparameters.learning_rate_multiplier
            ),
        )

        # Create job
        job_id = f"ftjob-{uuid.uuid4().hex}"
        created_at = int(time.time())

        job = FineTuningJob(
            id=job_id,
            created_at=created_at,
            model=request.model,
            organization_id="org-fakeai",
            status="validating_files",
            hyperparameters=resolved_hyperparameters,
            training_file=request.training_file,
            validation_file=request.validation_file,
            integrations=request.integrations,
            seed=request.seed,
            estimated_finish=created_at + 35,  # ~35 seconds total
        )

        # Store job
        self.fine_tuning_jobs[job_id] = job

        # Add initial events
        initial_event = FineTuningEvent(
            id=f"ftevent-{uuid.uuid4().hex}",
            created_at=created_at,
            level="info",
            message="Fine-tuning job created",
            type="message",
        )
        self.fine_tuning_events[job_id].append(initial_event)

        # Add an initial metrics event with sample data
        metrics_event = FineTuningEvent(
            id=f"ftevent-{uuid.uuid4().hex}",
            created_at=created_at,
            level="info",
            message="Initial training metrics",
            data={"step": 0, "train_loss": 2.5, "learning_rate": 0.0001},
            type="metrics",
        )
        self.fine_tuning_events[job_id].append(metrics_event)

        # Start background processing
        task = asyncio.create_task(
            self._process_fine_tuning_job(
                job_id, request.suffix, training_file))
        self.fine_tuning_tasks[job_id] = task

        logger.info(
            f"Created fine-tuning job {job_id} for model {request.model}")
        return job

    async def list_fine_tuning_jobs(
        self, limit: int = 20, after: str | None = None
    ) -> FineTuningJobList:
        """
        List fine-tuning jobs with pagination.

        Args:
            limit: Maximum number of jobs to return
            after: Cursor for pagination (job_id to start after)

        Returns:
            FineTuningJobList with paginated results
        """
        # Get all jobs sorted by creation time (newest first)
        all_jobs = sorted(
            self.fine_tuning_jobs.values(),
            key=lambda j: j.created_at,
            reverse=True)

        # Apply pagination
        if after:
            # Find the index of the 'after' job
            try:
                after_idx = next(
                    i for i, j in enumerate(all_jobs) if j.id == after)
                all_jobs = all_jobs[after_idx + 1:]
            except StopIteration:
                all_jobs = []

        # Limit results
        jobs = all_jobs[:limit]
        has_more = len(all_jobs) > limit

        return FineTuningJobList(
            data=jobs,
            has_more=has_more,
        )

    async def retrieve_fine_tuning_job(self, job_id: str) -> FineTuningJob:
        """
        Retrieve a specific fine-tuning job.

        Args:
            job_id: Job identifier

        Returns:
            FineTuningJob object

        Raises:
            ValueError: If job not found
        """
        job = self.fine_tuning_jobs.get(job_id)
        if not job:
            raise ValueError(f"Fine-tuning job {job_id} not found")

        return job

    async def cancel_fine_tuning_job(self, job_id: str) -> FineTuningJob:
        """
        Cancel a running or queued fine-tuning job.

        Args:
            job_id: Job identifier

        Returns:
            Updated FineTuningJob object with cancelled status

        Raises:
            ValueError: If job not found or cannot be cancelled
        """
        job = self.fine_tuning_jobs.get(job_id)
        if not job:
            raise ValueError(f"Fine-tuning job {job_id} not found")

        # Can only cancel jobs that are not finished
        if job.status in ["succeeded", "failed", "cancelled"]:
            raise ValueError(f"Cannot cancel job with status {job.status}")

        # Update job status
        job.status = "cancelled"
        job.finished_at = int(time.time())

        # Cancel background task if running
        if job_id in self.fine_tuning_tasks:
            task = self.fine_tuning_tasks[job_id]
            task.cancel()
            del self.fine_tuning_tasks[job_id]

        # Add cancellation event
        event = FineTuningEvent(
            id=f"ftevent-{uuid.uuid4().hex}",
            created_at=int(time.time()),
            level="info",
            message="Fine-tuning job cancelled by user",
            type="message",
        )
        self.fine_tuning_events[job_id].append(event)

        logger.info(f"Cancelled fine-tuning job {job_id}")
        return job

    async def list_fine_tuning_events(
        self, job_id: str, limit: int = 20
    ) -> AsyncGenerator[str, None]:
        """
        Stream fine-tuning events via Server-Sent Events (SSE).

        Args:
            job_id: Job identifier
            limit: Maximum number of events to return

        Yields:
            SSE-formatted event strings

        Raises:
            ValueError: If job not found
        """
        job = self.fine_tuning_jobs.get(job_id)
        if not job:
            raise ValueError(f"Fine-tuning job {job_id} not found")

        # Get events for this job
        events = self.fine_tuning_events.get(job_id, [])
        events = events[-limit:] if limit else events

        # Stream events in SSE format
        for event in events:
            event_data = event.model_dump(mode="json")
            yield f"data: {json.dumps(event_data)}\n\n"

    async def list_fine_tuning_checkpoints(
        self, job_id: str, limit: int = 10
    ) -> FineTuningCheckpointList:
        """
        List checkpoints for a fine-tuning job.

        Args:
            job_id: Job identifier
            limit: Maximum number of checkpoints to return

        Returns:
            FineTuningCheckpointList with checkpoints

        Raises:
            ValueError: If job not found
        """
        job = self.fine_tuning_jobs.get(job_id)
        if not job:
            raise ValueError(f"Fine-tuning job {job_id} not found")

        # Get checkpoints for this job
        checkpoints = self.fine_tuning_checkpoints.get(job_id, [])

        # Sort by step number (newest first)
        checkpoints = sorted(
            checkpoints,
            key=lambda c: c.step_number,
            reverse=True)

        # Apply limit
        checkpoints = checkpoints[:limit] if limit else checkpoints

        first_id = checkpoints[0].id if checkpoints else None
        last_id = checkpoints[-1].id if checkpoints else None

        return FineTuningCheckpointList(
            data=checkpoints,
            has_more=False,
            first_id=first_id,
            last_id=last_id,
        )

    async def _process_fine_tuning_job(
        self, job_id: str, suffix: str | None = None, training_file=None
    ):
        """
        Background task to process a fine-tuning job through its lifecycle.

        This simulates the complete fine-tuning workflow:
        1. validating_files (1 second)
        2. queued (1 second)
        3. running (30 seconds with checkpoints at 25%, 50%, 75%, 100%)
        4. succeeded

        Args:
            job_id: Job identifier
            suffix: Optional suffix for fine-tuned model name
            training_file: Training file object for token estimation
        """
        try:
            job = self.fine_tuning_jobs[job_id]

            # Phase 1: Validating files (1 second)
            await asyncio.sleep(1.0)
            job.status = "queued"
            event = FineTuningEvent(
                id=f"ftevent-{uuid.uuid4().hex}",
                created_at=int(time.time()),
                level="info",
                message="Files validated successfully",
                type="message",
            )
            self.fine_tuning_events[job_id].append(event)

            # Phase 2: Queued (1 second)
            await asyncio.sleep(1.0)
            job.status = "running"
            event = FineTuningEvent(
                id=f"ftevent-{uuid.uuid4().hex}",
                created_at=int(time.time()),
                level="info",
                message="Training started",
                type="message",
            )
            self.fine_tuning_events[job_id].append(event)

            # Phase 3: Running with checkpoints (30 seconds total)
            total_steps = 100
            training_duration = 30.0
            checkpoint_steps = [25, 50, 75, 100]

            for step in range(1, total_steps + 1):
                await asyncio.sleep(training_duration / total_steps)

                # Generate metrics periodically
                if step % 10 == 0 or step in checkpoint_steps:
                    train_loss = 2.5 * (1 - step / total_steps) + \
                        random.uniform(0.0, 0.2)
                    valid_loss = train_loss + random.uniform(0.0, 0.3)
                    train_accuracy = (
                        0.3 + (0.65 * step / total_steps) + random.uniform(0.0, 0.05)
                    )

                    metrics = {
                        "step": step,
                        "train_loss": round(train_loss, 4),
                        "valid_loss": round(valid_loss, 4),
                        "train_accuracy": round(train_accuracy, 4),
                        "learning_rate": 0.0001 *
                        job.hyperparameters.learning_rate_multiplier,
                    }

                    event = FineTuningEvent(
                        id=f"ftevent-{uuid.uuid4().hex}",
                        created_at=int(time.time()),
                        level="info",
                        message=f"Step {step}/{total_steps} completed",
                        data=metrics,
                        type="metrics",
                    )
                    self.fine_tuning_events[job_id].append(event)

                # Create checkpoints at 25%, 50%, 75%, 100%
                if step in checkpoint_steps:
                    checkpoint_suffix = f"step-{step}"
                    if suffix:
                        checkpoint_model_name = (
                            f"ft:{job.model}:org-fakeai:{suffix}:{checkpoint_suffix}"
                        )
                    else:
                        checkpoint_model_name = (
                            f"ft:{job.model}:org-fakeai::{checkpoint_suffix}"
                        )

                    checkpoint = FineTuningCheckpoint(
                        id=f"ftckpt-{uuid.uuid4().hex}",
                        created_at=int(time.time()),
                        fine_tuning_job_id=job_id,
                        fine_tuned_model_checkpoint=checkpoint_model_name,
                        step_number=step,
                        metrics={
                            "train_loss": round(
                                2.5 * (1 - step / total_steps) +
                                random.uniform(0.0, 0.2),
                                4,
                            ),
                            "valid_loss": round(
                                2.5 * (1 - step / total_steps) +
                                random.uniform(0.0, 0.3),
                                4,
                            ),
                            "train_accuracy": round(
                                0.3 +
                                (0.65 * step / total_steps) +
                                random.uniform(0.0, 0.05),
                                4,
                            ),
                        },
                    )
                    self.fine_tuning_checkpoints[job_id].append(checkpoint)

                    logger.info(
                        f"Created checkpoint for job {job_id} at step {step}")

            # Phase 4: Succeeded
            job.status = "succeeded"
            job.finished_at = int(time.time())

            # Set fine-tuned model name
            timestamp = int(time.time())
            if suffix:
                job.fine_tuned_model = f"ft:{
                    job.model}:org-fakeai:{suffix}:{timestamp}"
            else:
                job.fine_tuned_model = f"ft:{
                    job.model}:org-fakeai::{timestamp}"

            # Calculate trained tokens (simulate based on training file size
            # and epochs)
            if training_file:
                # Rough estimate: ~1 token per 4 bytes, multiplied by number of
                # epochs
                estimated_tokens = (
                    training_file.bytes // 4
                ) * job.hyperparameters.n_epochs
                job.trained_tokens = estimated_tokens
            else:
                job.trained_tokens = random.randint(50000, 500000)

            event = FineTuningEvent(
                id=f"ftevent-{uuid.uuid4().hex}",
                created_at=int(time.time()),
                level="info",
                message=f"Training completed successfully. Fine-tuned model: {job.fine_tuned_model}",
                type="message",
            )
            self.fine_tuning_events[job_id].append(event)

            logger.info(f"Fine-tuning job {job_id} completed successfully")

        except asyncio.CancelledError:
            # Job was cancelled, cleanup already handled
            logger.info(f"Fine-tuning job {job_id} was cancelled")
            raise

        except Exception as e:
            # Handle errors
            logger.error(f"Error processing fine-tuning job {job_id}: {e}")
            job = self.fine_tuning_jobs.get(job_id)
            if job:
                job.status = "failed"
                job.finished_at = int(time.time())

                error_event = FineTuningEvent(
                    id=f"ftevent-{uuid.uuid4().hex}",
                    created_at=int(time.time()),
                    level="error",
                    message=f"Training failed: {str(e)}",
                    type="message",
                )
                self.fine_tuning_events[job_id].append(error_event)

        finally:
            # Cleanup task reference
            if job_id in self.fine_tuning_tasks:
                del self.fine_tuning_tasks[job_id]
