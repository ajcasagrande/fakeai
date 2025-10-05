# Fine-Tuning API Implementation for FakeAI
# This code should be added to fakeai_service.py

# Add to __init__ after line 517 (after self.service_accounts):
"""
        # Initialize fine-tuning storage
        self.fine_tuning_jobs: dict[str, FineTuningJob] = {}  # job_id -> job
        self.fine_tuning_events: dict[str, list[FineTuningEvent]] = {}  # job_id -> events
        self.fine_tuning_checkpoints: dict[str, list[FineTuningCheckpoint]] = {}  # job_id -> checkpoints
        self.fine_tuning_tasks: dict[str, asyncio.Task] = {}  # job_id -> background task
"""

# Add these methods at the end of FakeAIService class:

async def create_fine_tuning_job(self, request: FineTuningJobRequest) -> FineTuningJob:
    """Create a fine-tuning job."""
    # Ensure model exists
    self._ensure_model_exists(request.model)

    # Validate files exist
    training_file_exists = any(f.id == request.training_file for f in self.files)
    if not training_file_exists:
        raise ValueError(f"Training file '{request.training_file}' not found")

    if request.validation_file:
        validation_file_exists = any(f.id == request.validation_file for f in self.files)
        if not validation_file_exists:
            raise ValueError(f"Validation file '{request.validation_file}' not found")

    # Create job ID
    job_id = f"ftjob-{uuid.uuid4().hex}"

    # Resolve hyperparameters (convert "auto" to actual values)
    hyperparameters = request.hyperparameters or Hyperparameters()
    resolved_hyperparameters = Hyperparameters(
        n_epochs=3 if hyperparameters.n_epochs == "auto" else hyperparameters.n_epochs,
        batch_size=4 if hyperparameters.batch_size == "auto" else hyperparameters.batch_size,
        learning_rate_multiplier=0.1 if hyperparameters.learning_rate_multiplier == "auto" else hyperparameters.learning_rate_multiplier,
    )

    # Create fine-tuned model name
    suffix = request.suffix or "finetuned"
    fine_tuned_model_name = None  # Will be set when job completes

    # Estimate finish time (simulated: 60 seconds from now)
    estimated_finish = int(time.time()) + 60

    # Create job object
    job = FineTuningJob(
        id=job_id,
        created_at=int(time.time()),
        finished_at=None,
        model=request.model,
        fine_tuned_model=fine_tuned_model_name,
        organization_id="org-simulated",
        status="validating_files",
        hyperparameters=resolved_hyperparameters,
        training_file=request.training_file,
        validation_file=request.validation_file,
        result_files=[],
        trained_tokens=None,
        error=None,
        integrations=request.integrations,
        seed=request.seed,
        estimated_finish=estimated_finish,
    )

    # Store job
    self.fine_tuning_jobs[job_id] = job
    self.fine_tuning_events[job_id] = []
    self.fine_tuning_checkpoints[job_id] = []

    # Start background training simulation
    task = asyncio.create_task(self._simulate_fine_tuning(job_id, request.suffix or "finetuned"))
    self.fine_tuning_tasks[job_id] = task

    return job


async def _simulate_fine_tuning(self, job_id: str, suffix: str) -> None:
    """Simulate fine-tuning process in background."""
    try:
        job = self.fine_tuning_jobs[job_id]

        # Phase 1: Validating files (2 seconds)
        await asyncio.sleep(2)
        self._add_fine_tuning_event(
            job_id,
            level="info",
            message="Files validated successfully. Beginning training...",
            event_type="message",
        )
        job.status = "queued"

        # Phase 2: Queued (1 second)
        await asyncio.sleep(1)
        self._add_fine_tuning_event(
            job_id,
            level="info",
            message="Training job queued. Starting training...",
            event_type="message",
        )
        job.status = "running"

        # Phase 3: Training (30 seconds with progress updates)
        total_steps = 100
        n_epochs = job.hyperparameters.n_epochs if isinstance(job.hyperparameters.n_epochs, int) else 3

        for step in range(1, total_steps + 1):
            await asyncio.sleep(0.3)  # 30 seconds total

            # Generate realistic training metrics
            epoch = ((step - 1) * n_epochs) // total_steps + 1
            progress = step / total_steps

            # Loss decreases over time with some noise
            base_loss = 2.5 * (1 - progress * 0.8)  # Decrease from 2.5 to 0.5
            train_loss = base_loss + random.uniform(-0.1, 0.1)
            train_accuracy = min(0.95, 0.5 + progress * 0.45)  # Increase from 0.5 to 0.95

            # Validation metrics (slightly worse than training)
            val_loss = train_loss + random.uniform(0.05, 0.15)
            val_accuracy = train_accuracy - random.uniform(0.02, 0.08)

            # Log metrics every 10 steps
            if step % 10 == 0:
                metrics_data = {
                    "step": step,
                    "epoch": epoch,
                    "train_loss": round(train_loss, 4),
                    "train_accuracy": round(train_accuracy, 4),
                    "valid_loss": round(val_loss, 4),
                    "valid_accuracy": round(val_accuracy, 4),
                    "learning_rate": 0.0001 * (job.hyperparameters.learning_rate_multiplier if isinstance(job.hyperparameters.learning_rate_multiplier, (int, float)) else 0.1),
                }

                self._add_fine_tuning_event(
                    job_id,
                    level="info",
                    message=f"Step {step}/{total_steps}: train_loss={metrics_data['train_loss']:.4f}, valid_loss={metrics_data['valid_loss']:.4f}",
                    event_type="metrics",
                    data=metrics_data,
                )

            # Create checkpoints at 25%, 50%, 75%, and 100%
            if step in [25, 50, 75, 100]:
                checkpoint_id = f"ftckpt-{uuid.uuid4().hex}"
                checkpoint_model_name = f"ft:{job.model}:checkpoint-{step}:{uuid.uuid4().hex[:8]}"

                checkpoint = FineTuningCheckpoint(
                    id=checkpoint_id,
                    created_at=int(time.time()),
                    fine_tuning_job_id=job_id,
                    fine_tuned_model_checkpoint=checkpoint_model_name,
                    step_number=step,
                    metrics={
                        "train_loss": round(train_loss, 4),
                        "train_accuracy": round(train_accuracy, 4),
                        "valid_loss": round(val_loss, 4),
                        "valid_accuracy": round(val_accuracy, 4),
                    },
                )

                self.fine_tuning_checkpoints[job_id].append(checkpoint)

                # Register checkpoint model
                self._ensure_model_exists(checkpoint_model_name)

        # Phase 4: Success
        fine_tuned_model_name = f"ft:{job.model}:simulated:{suffix}:{uuid.uuid4().hex[:8]}"
        job.fine_tuned_model = fine_tuned_model_name
        job.status = "succeeded"
        job.finished_at = int(time.time())
        job.trained_tokens = random.randint(50000, 200000)

        # Create result files
        result_file_id = f"file-{uuid.uuid4().hex}"
        job.result_files = [result_file_id]

        # Register the fine-tuned model
        self._ensure_model_exists(fine_tuned_model_name)

        self._add_fine_tuning_event(
            job_id,
            level="info",
            message=f"Fine-tuning job completed successfully. Model: {fine_tuned_model_name}",
            event_type="message",
        )

    except asyncio.CancelledError:
        # Job was cancelled
        job = self.fine_tuning_jobs[job_id]
        job.status = "cancelled"
        job.finished_at = int(time.time())

        self._add_fine_tuning_event(
            job_id,
            level="info",
            message="Fine-tuning job cancelled by user.",
            event_type="message",
        )

    except Exception as e:
        # Job failed
        job = self.fine_tuning_jobs[job_id]
        job.status = "failed"
        job.finished_at = int(time.time())
        job.error = {
            "code": "training_failed",
            "message": f"Training failed: {str(e)}",
            "param": None,
        }

        self._add_fine_tuning_event(
            job_id,
            level="error",
            message=f"Fine-tuning job failed: {str(e)}",
            event_type="message",
        )


def _add_fine_tuning_event(
    self,
    job_id: str,
    level: str,
    message: str,
    event_type: str = "message",
    data: dict[str, Any] | None = None,
) -> None:
    """Add an event to a fine-tuning job's event log."""
    event = FineTuningEvent(
        id=f"ftevent-{uuid.uuid4().hex}",
        created_at=int(time.time()),
        level=level,
        message=message,
        type=event_type,
        data=data,
    )

    if job_id not in self.fine_tuning_events:
        self.fine_tuning_events[job_id] = []

    self.fine_tuning_events[job_id].append(event)


async def list_fine_tuning_jobs(
    self,
    after: str | None = None,
    limit: int = 20,
) -> FineTuningJobList:
    """List fine-tuning jobs."""
    await asyncio.sleep(random.uniform(0.05, 0.2))

    jobs = list(self.fine_tuning_jobs.values())

    # Sort by creation time (newest first)
    jobs.sort(key=lambda j: j.created_at, reverse=True)

    # Apply pagination
    if after:
        # Find the job with the given ID
        after_idx = next((i for i, j in enumerate(jobs) if j.id == after), -1)
        if after_idx >= 0:
            jobs = jobs[after_idx + 1:]

    # Limit results
    has_more = len(jobs) > limit
    jobs = jobs[:limit]

    return FineTuningJobList(data=jobs, has_more=has_more)


async def get_fine_tuning_job(self, job_id: str) -> FineTuningJob:
    """Get a fine-tuning job by ID."""
    await asyncio.sleep(random.uniform(0.05, 0.2))

    if job_id not in self.fine_tuning_jobs:
        raise ValueError(f"Fine-tuning job '{job_id}' not found")

    return self.fine_tuning_jobs[job_id]


async def cancel_fine_tuning_job(self, job_id: str) -> FineTuningJob:
    """Cancel a fine-tuning job."""
    await asyncio.sleep(random.uniform(0.05, 0.2))

    if job_id not in self.fine_tuning_jobs:
        raise ValueError(f"Fine-tuning job '{job_id}' not found")

    job = self.fine_tuning_jobs[job_id]

    # Can only cancel jobs that are running or queued
    if job.status not in ["validating_files", "queued", "running"]:
        raise ValueError(f"Cannot cancel job in status '{job.status}'")

    # Cancel the background task
    if job_id in self.fine_tuning_tasks:
        self.fine_tuning_tasks[job_id].cancel()
        del self.fine_tuning_tasks[job_id]

    job.status = "cancelled"
    job.finished_at = int(time.time())

    self._add_fine_tuning_event(
        job_id,
        level="info",
        message="Job cancelled by user request.",
        event_type="message",
    )

    return job


async def list_fine_tuning_events(
    self,
    job_id: str,
    after: str | None = None,
    limit: int = 20,
) -> AsyncGenerator[str, None]:
    """List fine-tuning events with SSE streaming."""
    if job_id not in self.fine_tuning_jobs:
        raise ValueError(f"Fine-tuning job '{job_id}' not found")

    events = self.fine_tuning_events.get(job_id, [])

    # Sort by creation time
    events.sort(key=lambda e: e.created_at)

    # Apply pagination
    if after:
        after_idx = next((i for i, e in enumerate(events) if e.id == after), -1)
        if after_idx >= 0:
            events = events[after_idx + 1:]

    # Limit results
    events = events[:limit]

    # Stream events as SSE
    for event in events:
        yield f"data: {event.model_dump_json()}\n\n"
        await asyncio.sleep(0.01)  # Small delay between events

    # Send final done marker
    yield "data: [DONE]\n\n"


async def list_fine_tuning_checkpoints(
    self,
    job_id: str,
    after: str | None = None,
    limit: int = 10,
) -> FineTuningCheckpointList:
    """List checkpoints for a fine-tuning job."""
    await asyncio.sleep(random.uniform(0.05, 0.2))

    if job_id not in self.fine_tuning_jobs:
        raise ValueError(f"Fine-tuning job '{job_id}' not found")

    checkpoints = self.fine_tuning_checkpoints.get(job_id, [])

    # Sort by step number (newest first)
    checkpoints.sort(key=lambda c: c.step_number, reverse=True)

    # Apply pagination
    if after:
        after_idx = next((i for i, c in enumerate(checkpoints) if c.id == after), -1)
        if after_idx >= 0:
            checkpoints = checkpoints[after_idx + 1:]

    # Limit results
    has_more = len(checkpoints) > limit
    checkpoints = checkpoints[:limit]

    first_id = checkpoints[0].id if checkpoints else None
    last_id = checkpoints[-1].id if checkpoints else None

    return FineTuningCheckpointList(
        data=checkpoints,
        has_more=has_more,
        first_id=first_id,
        last_id=last_id,
    )
