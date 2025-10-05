# Fine-Tuning API Endpoints for app.py
# Add these to app.py after the Vector Stores endpoints

# Add to imports at top of app.py:
"""
from fakeai.models import (
    ...
    FineTuningJob,
    FineTuningJobList,
    FineTuningJobRequest,
    FineTuningCheckpointList,
    ...
)
"""

# Add these endpoints after the Vector Stores endpoints:

# Fine-Tuning API endpoints
@app.post("/v1/fine_tuning/jobs", dependencies=[Depends(verify_api_key)])
async def create_fine_tuning_job(request: FineTuningJobRequest) -> FineTuningJob:
    """Create a fine-tuning job."""
    try:
        return await fakeai_service.create_fine_tuning_job(request)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.get("/v1/fine_tuning/jobs", dependencies=[Depends(verify_api_key)])
async def list_fine_tuning_jobs(
    after: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
) -> FineTuningJobList:
    """List fine-tuning jobs with pagination."""
    return await fakeai_service.list_fine_tuning_jobs(after=after, limit=limit)


@app.get("/v1/fine_tuning/jobs/{fine_tuning_job_id}", dependencies=[Depends(verify_api_key)])
async def retrieve_fine_tuning_job(fine_tuning_job_id: str) -> FineTuningJob:
    """Retrieve a fine-tuning job by ID."""
    try:
        return await fakeai_service.get_fine_tuning_job(fine_tuning_job_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@app.post("/v1/fine_tuning/jobs/{fine_tuning_job_id}/cancel", dependencies=[Depends(verify_api_key)])
async def cancel_fine_tuning_job(fine_tuning_job_id: str) -> FineTuningJob:
    """Cancel a fine-tuning job."""
    try:
        return await fakeai_service.cancel_fine_tuning_job(fine_tuning_job_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@app.get("/v1/fine_tuning/jobs/{fine_tuning_job_id}/events", dependencies=[Depends(verify_api_key)])
async def list_fine_tuning_events(
    fine_tuning_job_id: str,
    after: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
):
    """Stream fine-tuning events via SSE."""
    try:
        async def generate():
            async for event_data in fakeai_service.list_fine_tuning_events(
                fine_tuning_job_id, after=after, limit=limit
            ):
                yield event_data

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@app.get("/v1/fine_tuning/jobs/{fine_tuning_job_id}/checkpoints", dependencies=[Depends(verify_api_key)])
async def list_fine_tuning_checkpoints(
    fine_tuning_job_id: str,
    after: str | None = Query(default=None),
    limit: int = Query(default=10, ge=1, le=100),
) -> FineTuningCheckpointList:
    """List checkpoints for a fine-tuning job."""
    try:
        return await fakeai_service.list_fine_tuning_checkpoints(
            fine_tuning_job_id, after=after, limit=limit
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
