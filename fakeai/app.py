#!/usr/bin/env python3
"""
FakeAI: OpenAI Compatible API Server

This module provides a FastAPI implementation that mimics the OpenAI API.
It supports all endpoints and features of the official OpenAI API but returns
simulated responses instead of performing actual inference.
"""
#  SPDX-License-Identifier: Apache-2.0

import logging
import random
import time
from datetime import datetime
from typing import Annotated

import uvicorn

from fakeai.config import AppConfig
from fakeai.fakeai_service import FakeAIService, RealtimeSessionHandler
from fakeai.metrics import MetricsTracker
from fakeai.rate_limiter import RateLimiter
from fakeai.security import (
    ApiKeyManager,
    AbuseDetector,
    InputValidator,
    InjectionAttackDetected,
    PayloadTooLarge,
)
from fakeai.models import (
    ArchiveOrganizationProjectResponse,
    AudioSpeechesUsageResponse,
    AudioTranscriptionsUsageResponse,
    Batch,
    BatchListResponse,
    ChatCompletionRequest,
    ChatCompletionResponse,
    CompletionRequest,
    CompletionResponse,
    CompletionsUsageResponse,
    CostsResponse,
    CreateBatchRequest,
    CreateOrganizationInviteRequest,
    CreateOrganizationProjectRequest,
    CreateOrganizationUserRequest,
    CreateProjectUserRequest,
    CreateServiceAccountRequest,
    DeleteOrganizationInviteResponse,
    DeleteProjectUserResponse,
    DeleteServiceAccountResponse,
    EmbeddingRequest,
    EmbeddingResponse,
    EmbeddingsUsageResponse,
    ErrorDetail,
    ErrorResponse,
    FileListResponse,
    FileObject,
    FineTuningJob,
    FineTuningJobList,
    FineTuningJobRequest,
    FineTuningCheckpointList,
    ImageGenerationRequest,
    ImageGenerationResponse,
    ImagesUsageResponse,
    ModerationRequest,
    ModerationResponse,
    ModelCapabilitiesResponse,
    ModelListResponse,
    ModifyOrganizationProjectRequest,
    ModifyOrganizationUserRequest,
    ModifyProjectUserRequest,
    OrganizationInvite,
    OrganizationInviteListResponse,
    OrganizationProject,
    OrganizationProjectListResponse,
    OrganizationUser,
    OrganizationUserListResponse,
    ProjectUser,
    ProjectUserListResponse,
    RankingRequest,
    RankingResponse,
    ResponsesRequest,
    ResponsesResponse,
    ServiceAccount,
    ServiceAccountListResponse,
    SolidoRagRequest,
    SolidoRagResponse,
    SpeechRequest,
    TextGenerationRequest,
    TextGenerationResponse,
    VectorStore,
    VectorStoreFile,
    VectorStoreFileBatch,
    VectorStoreFileListResponse,
    VectorStoreListResponse,
    CreateVectorStoreRequest,
    ModifyVectorStoreRequest,
    CreateVectorStoreFileRequest,
    CreateVectorStoreFileBatchRequest,
)

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response, StreamingResponse

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize the application
app = FastAPI(
    title="FakeAI Server",
    description="An OpenAI-compatible API implementation for testing and development.",
    version="1.0.0",
)

# Load configuration
config = AppConfig()

# Add CORS middleware with configurable origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_allowed_origins,
    allow_credentials=config.cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize security components
api_key_manager = ApiKeyManager()
abuse_detector = AbuseDetector()
input_validator = InputValidator()

# Add API keys to manager (with hashing if enabled)
if config.hash_api_keys:
    for key in config.api_keys:
        api_key_manager.add_key(key)
else:
    # For backward compatibility, plain keys still work
    pass

# Initialize the FakeAI service
fakeai_service = FakeAIService(config)

# Get the metrics tracker singleton instance
metrics_tracker = fakeai_service.metrics_tracker

# Server readiness state
server_ready = False

# Initialize rate limiter
rate_limiter = RateLimiter()
rate_limiter.configure(
    tier=config.rate_limit_tier,
    rpm_override=config.rate_limit_rpm,
    tpm_override=config.rate_limit_tpm,
)


# Authentication dependency
async def verify_api_key(
    request: Request,
    api_key: Annotated[str | None, Header(alias="Authorization")] = None
):
    """Verifies the API key from the Authorization header with security checks."""
    client_ip = request.client.host if request.client else "unknown"

    # Check if IP is banned
    if config.enable_abuse_detection:
        is_banned, ban_time = abuse_detector.is_banned(client_ip)
        if is_banned:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"IP address temporarily banned. Retry after {int(ban_time)} seconds.",
                headers={"Retry-After": str(int(ban_time))},
            )

    # Skip authentication if not required
    if not config.require_api_key:
        return None

    if not api_key:
        if config.enable_abuse_detection:
            abuse_detector.record_failed_auth(client_ip)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key",
        )

    # Strip "Bearer " prefix if present
    if api_key.startswith("Bearer "):
        api_key = api_key[7:]

    # Verify API key
    is_valid = False
    if config.hash_api_keys:
        # Use secure API key manager
        is_valid = api_key_manager.verify_key(api_key)
    else:
        # Backward compatibility: plain key check
        is_valid = api_key in config.api_keys

    if not is_valid:
        if config.enable_abuse_detection:
            abuse_detector.record_failed_auth(client_ip)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    return api_key


# Request logging and rate limiting middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests and enforce rate limits with security checks"""
    request_id = f"{int(time.time())}-{random.randint(1000, 9999)}"
    endpoint = request.url.path
    client_ip = request.client.host if request.client else "unknown"
    logger.debug("Request %s: %s %s from %s", request_id, request.method, endpoint, client_ip)
    start_time = time.time()

    # Track the request in the metrics
    metrics_tracker.track_request(endpoint)

    # Check if IP is banned (for non-health endpoints)
    if config.enable_abuse_detection and endpoint not in ["/health", "/metrics"]:
        is_banned, ban_time = abuse_detector.is_banned(client_ip)
        if is_banned:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content=ErrorResponse(
                    error=ErrorDetail(
                        code="ip_banned",
                        message=f"IP address temporarily banned due to abuse. Retry after {int(ban_time)} seconds.",
                        param=None,
                        type="security_error",
                    )
                ).model_dump(),
                headers={"Retry-After": str(int(ban_time))},
            )

    # Validate payload size
    if config.enable_input_validation:
        try:
            body = await request.body()
            # Store body for later use since it can only be read once
            request._body = body

            # Check payload size
            input_validator.validate_payload_size(body, config.max_request_size)

            # Validate for injection attacks if enabled
            if config.enable_injection_detection and body:
                try:
                    body_str = body.decode("utf-8", errors="ignore")
                    # Quick check for injection patterns in the raw request
                    input_validator.sanitize_string(body_str[:10000])  # Check first 10KB
                except InjectionAttackDetected as e:
                    if config.enable_abuse_detection:
                        abuse_detector.record_injection_attempt(client_ip)
                    return JSONResponse(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        content=ErrorResponse(
                            error=ErrorDetail(
                                code="injection_detected",
                                message="Potential injection attack detected in request.",
                                param=None,
                                type="security_error",
                            )
                        ).model_dump(),
                    )

        except PayloadTooLarge as e:
            if config.enable_abuse_detection:
                abuse_detector.record_oversized_payload(client_ip)
            return JSONResponse(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                content=ErrorResponse(
                    error=ErrorDetail(
                        code="payload_too_large",
                        message=str(e),
                        param=None,
                        type="invalid_request_error",
                    )
                ).model_dump(),
            )
        except Exception as e:
            # Restore body for normal processing
            pass

    # Check rate limits if enabled
    rate_limit_headers = {}
    if config.rate_limit_enabled and config.require_api_key:
        # Extract API key from Authorization header
        auth_header = request.headers.get("Authorization", "")
        api_key = auth_header[7:] if auth_header.startswith("Bearer ") else auth_header

        if api_key and api_key in config.api_keys:
            # Estimate token count from request body for chat/completions endpoints
            estimated_tokens = 0
            if endpoint in ["/v1/chat/completions", "/v1/completions", "/v1/embeddings"]:
                try:
                    body = await request.body()
                    # Store body for later use since it can only be read once
                    request._body = body

                    # Rough estimate: 1 token per 4 characters
                    estimated_tokens = max(100, len(body) // 4)
                except Exception:
                    estimated_tokens = 100  # Default estimate

            # Check rate limits
            allowed, retry_after, rate_limit_headers = rate_limiter.check_rate_limit(
                api_key, estimated_tokens
            )

            if not allowed:
                # Record rate limit violation for abuse detection
                if config.enable_abuse_detection:
                    abuse_detector.record_rate_limit_violation(client_ip)

                # Return 429 with rate limit headers
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content=ErrorResponse(
                        error=ErrorDetail(
                            code="rate_limit_exceeded",
                            message="Rate limit exceeded. Please retry after the specified time.",
                            param=None,
                            type="rate_limit_error",
                        )
                    ).model_dump(),
                    headers={
                        **rate_limit_headers,
                        "Retry-After": retry_after,
                    },
                )

    # Process the request
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        process_time_ms = process_time * 1000

        # Track the response in the metrics
        metrics_tracker.track_response(endpoint, process_time)

        # Add rate limit headers to successful responses
        if rate_limit_headers:
            for header_name, header_value in rate_limit_headers.items():
                response.headers[header_name] = header_value

        logger.debug(
            "Request %s completed in %.2fms with status %s",
            request_id,
            process_time_ms,
            response.status_code,
        )
        return response
    except Exception as e:
        # Track the error in the metrics
        metrics_tracker.track_error(endpoint)

        logger.exception("Request %s failed: %s", request_id, str(e))
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                error=ErrorDetail(
                    code="internal_server_error",
                    message="An unexpected error occurred.",
                    param=None,
                    type="server_error",
                )
            ).model_dump(),
        )


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint with readiness status"""
    global server_ready
    status = "healthy" if server_ready else "starting"
    return {
        "status": status,
        "ready": server_ready,
        "timestamp": datetime.now().isoformat()
    }


# Startup event to mark server as ready
@app.on_event("startup")
async def startup_event():
    """Mark server as ready after startup."""
    global server_ready
    # Give a brief moment for all initialization to complete
    import asyncio
    await asyncio.sleep(0.1)
    server_ready = True
    logger.info("Server is ready to accept requests")


# Dashboard endpoint
@app.get("/dashboard")
async def get_dashboard():
    """Serve the interactive metrics dashboard"""
    import os
    dashboard_path = os.path.join(os.path.dirname(__file__), "static", "dashboard.html")
    return FileResponse(dashboard_path, media_type="text/html")


@app.get("/dashboard/dynamo")
async def get_dynamo_dashboard():
    """Serve the advanced Dynamo dashboard with DCGM, KVBM, and SLA metrics"""
    import os
    dashboard_path = os.path.join(os.path.dirname(__file__), "static", "dashboard_advanced.html")
    return FileResponse(dashboard_path, media_type="text/html")


# Models endpoints
@app.get("/v1/models", dependencies=[Depends(verify_api_key)])
async def list_models() -> ModelListResponse:
    """List available models"""
    return await fakeai_service.list_models()


@app.get("/v1/models/{model_id:path}", dependencies=[Depends(verify_api_key)])
async def get_model(model_id: str):
    """Get model details"""
    try:
        return await fakeai_service.get_model(model_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@app.get("/v1/models/{model_id:path}/capabilities", dependencies=[Depends(verify_api_key)])
async def get_model_capabilities(model_id: str) -> ModelCapabilitiesResponse:
    """Get model capabilities including context window, pricing, and feature support"""
    return await fakeai_service.get_model_capabilities(model_id)


# Chat completions endpoints
@app.post("/v1/chat/completions", dependencies=[Depends(verify_api_key)], response_model=None)
async def create_chat_completion(
    request: ChatCompletionRequest
):
    """Create a chat completion"""
    if request.stream:

        async def generate():
            async for chunk in fakeai_service.create_chat_completion_stream(request):
                yield f"data: {chunk.model_dump_json()}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
        )
    else:
        return await fakeai_service.create_chat_completion(request)


# Completions endpoints
@app.post("/v1/completions", dependencies=[Depends(verify_api_key)], response_model=None)
async def create_completion(
    request: CompletionRequest
):
    """Create a completion"""
    if request.stream:

        async def generate():
            async for chunk in fakeai_service.create_completion_stream(request):
                yield f"data: {chunk.model_dump_json()}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
        )
    else:
        return await fakeai_service.create_completion(request)


# Embeddings endpoint
@app.post("/v1/embeddings", dependencies=[Depends(verify_api_key)])
async def create_embedding(request: EmbeddingRequest) -> EmbeddingResponse:
    """Create embeddings"""
    return await fakeai_service.create_embedding(request)


# Images endpoints
@app.post("/v1/images/generations", dependencies=[Depends(verify_api_key)])
async def generate_images(request: ImageGenerationRequest) -> ImageGenerationResponse:
    """Generate images"""
    return await fakeai_service.generate_images(request)


# Audio (Text-to-Speech) endpoint
@app.post("/v1/audio/speech", dependencies=[Depends(verify_api_key)])
async def create_speech(request: SpeechRequest) -> Response:
    """
    Create text-to-speech audio.

    Generates audio from the input text using the specified voice and returns
    the audio file in the requested format.
    """
    # Generate audio bytes
    audio_bytes = await fakeai_service.create_speech(request)

    # Determine content type based on format
    content_type_map = {
        "mp3": "audio/mpeg",
        "opus": "audio/opus",
        "aac": "audio/aac",
        "flac": "audio/flac",
        "wav": "audio/wav",
        "pcm": "audio/pcm",
    }
    content_type = content_type_map.get(request.response_format, "audio/mpeg")

    # Return binary audio response
    return Response(
        content=audio_bytes,
        media_type=content_type,
        headers={
            "Content-Disposition": f'inline; filename="speech.{request.response_format}"',
        },
    )


# Files endpoints
@app.get("/v1/files", dependencies=[Depends(verify_api_key)])
async def list_files() -> FileListResponse:
    """List files"""
    return await fakeai_service.list_files()


@app.post("/v1/files", dependencies=[Depends(verify_api_key)])
async def upload_file():
    """Upload a file"""
    # This would typically handle file uploads
    return await fakeai_service.upload_file()


@app.get("/v1/files/{file_id}", dependencies=[Depends(verify_api_key)])
async def get_file(file_id: str) -> FileObject:
    """Get file details"""
    return await fakeai_service.get_file(file_id)


@app.delete("/v1/files/{file_id}", dependencies=[Depends(verify_api_key)])
async def delete_file(file_id: str):
    """Delete a file"""
    return await fakeai_service.delete_file(file_id)


# Text generation endpoints (for Azure compatibility) - Moved to /v1/text/generation
@app.post("/v1/text/generation", dependencies=[Depends(verify_api_key)])
async def create_text_generation(
    request: TextGenerationRequest,
) -> TextGenerationResponse:
    """Create a text generation (Azure API compatibility)"""
    return await fakeai_service.create_text_generation(request)


# OpenAI Responses API endpoint (March 2025 format)
@app.post("/v1/responses", dependencies=[Depends(verify_api_key)], response_model=None)
async def create_response(request: ResponsesRequest):
    """Create an OpenAI Responses API response"""
    return await fakeai_service.create_response(request)


# NVIDIA NIM Rankings API endpoint
@app.post("/v1/ranking", dependencies=[Depends(verify_api_key)])
async def create_ranking(request: RankingRequest) -> RankingResponse:
    """Create a NVIDIA NIM ranking response"""
    return await fakeai_service.create_ranking(request)


# Solido RAG API endpoint
@app.post("/rag/api/prompt", dependencies=[Depends(verify_api_key)])
async def create_solido_rag(request: SolidoRagRequest) -> SolidoRagResponse:
    """
    Create a Solido RAG response with retrieval-augmented generation.

    Retrieves relevant documents based on filters and generates
    context-aware responses using the specified inference model.
    """
    return await fakeai_service.create_solido_rag(request)


# Metrics endpoints
@app.get("/metrics")
async def get_metrics():
    """Get server metrics in JSON format"""
    return metrics_tracker.get_metrics()


@app.get("/metrics/prometheus")
async def get_prometheus_metrics():
    """Get server metrics in Prometheus format"""
    return Response(
        content=metrics_tracker.get_prometheus_metrics(),
        media_type="text/plain; version=0.0.4",
    )


@app.get("/metrics/csv")
async def get_csv_metrics():
    """Get server metrics in CSV format"""
    return Response(
        content=metrics_tracker.get_csv_metrics(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=metrics.csv"},
    )


@app.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with metrics summary"""
    return metrics_tracker.get_detailed_health()


@app.get("/kv-cache/metrics")
async def get_kv_cache_metrics():
    """Get KV cache and AI-Dynamo smart routing metrics."""
    # Simple safe version that can't deadlock
    return {
        "cache_performance": {
            "cache_hit_rate": 0.0,
            "token_reuse_rate": 0.0,
            "total_cache_hits": 0,
            "total_cache_misses": 0,
        },
        "smart_router": {
            "workers": {},
            "radix_tree": {
                "total_nodes": 0,
                "total_cached_blocks": 0,
            },
            "config": {
                "num_workers": 4,
            }
        }
    }


# DCGM GPU Metrics endpoints
@app.get("/dcgm/metrics")
async def get_dcgm_metrics_prometheus():
    """Get simulated DCGM GPU metrics in Prometheus format."""
    # Return real simulated DCGM metrics in Prometheus format
    return Response(
        content=fakeai_service.dcgm_simulator.get_prometheus_metrics(),
        media_type="text/plain; version=0.0.4",
    )


@app.get("/dcgm/metrics/json")
async def get_dcgm_metrics_json():
    """Get simulated DCGM GPU metrics in JSON format."""
    # Return real simulated GPU metrics
    return fakeai_service.dcgm_simulator.get_metrics_dict()


# Dynamo LLM Metrics endpoints
@app.get("/dynamo/metrics")
async def get_dynamo_metrics_prometheus():
    """Get AI-Dynamo LLM inference metrics in Prometheus format."""
    # Return real Prometheus metrics from DynamoMetricsCollector
    return Response(
        content=fakeai_service.dynamo_metrics.get_prometheus_metrics(),
        media_type="text/plain; version=0.0.4",
    )


@app.get("/dynamo/metrics/json")
async def get_dynamo_metrics_json():
    """Get AI-Dynamo LLM inference metrics in JSON format."""
    # Return real metrics from DynamoMetricsCollector
    return fakeai_service.dynamo_metrics.get_stats_dict()


# Moderation endpoint
@app.post("/v1/moderations", dependencies=[Depends(verify_api_key)])
async def create_moderation(request: ModerationRequest) -> ModerationResponse:
    """Classify if text and/or image inputs are potentially harmful."""
    return await fakeai_service.create_moderation(request)


# Batch API endpoints
@app.post("/v1/batches", dependencies=[Depends(verify_api_key)])
async def create_batch(request: CreateBatchRequest) -> Batch:
    """Create a batch processing job."""
    return await fakeai_service.create_batch(request)


@app.get("/v1/batches/{batch_id}", dependencies=[Depends(verify_api_key)])
async def retrieve_batch(batch_id: str) -> Batch:
    """Retrieve a batch by ID."""
    try:
        return await fakeai_service.retrieve_batch(batch_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@app.post("/v1/batches/{batch_id}/cancel", dependencies=[Depends(verify_api_key)])
async def cancel_batch(batch_id: str) -> Batch:
    """Cancel a batch."""
    try:
        return await fakeai_service.cancel_batch(batch_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@app.get("/v1/batches", dependencies=[Depends(verify_api_key)])
async def list_batches(
    limit: int = Query(default=20, ge=1, le=100),
    after: str | None = Query(default=None),
) -> BatchListResponse:
    """List all batches with pagination."""
    return await fakeai_service.list_batches(limit=limit, after=after)


# Organization and Project Management API endpoints

# Organization Users
@app.get("/v1/organization/users", dependencies=[Depends(verify_api_key)])
async def list_organization_users(
    limit: int = Query(default=20, ge=1, le=100),
    after: str | None = Query(default=None),
) -> OrganizationUserListResponse:
    """List all users in the organization."""
    return await fakeai_service.list_organization_users(limit=limit, after=after)


@app.get("/v1/organization/users/{user_id}", dependencies=[Depends(verify_api_key)])
async def get_organization_user(user_id: str) -> OrganizationUser:
    """Get a specific organization user."""
    try:
        return await fakeai_service.get_organization_user(user_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@app.post("/v1/organization/users", dependencies=[Depends(verify_api_key)])
async def create_organization_user(request: CreateOrganizationUserRequest) -> OrganizationUser:
    """Add a user to the organization."""
    return await fakeai_service.create_organization_user(request)


@app.post("/v1/organization/users/{user_id}", dependencies=[Depends(verify_api_key)])
async def modify_organization_user(
    user_id: str, request: ModifyOrganizationUserRequest
) -> OrganizationUser:
    """Modify an organization user's role."""
    try:
        return await fakeai_service.modify_organization_user(user_id, request)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@app.delete("/v1/organization/users/{user_id}", dependencies=[Depends(verify_api_key)])
async def delete_organization_user(user_id: str) -> dict:
    """Remove a user from the organization."""
    try:
        return await fakeai_service.delete_organization_user(user_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# Organization Invites
@app.get("/v1/organization/invites", dependencies=[Depends(verify_api_key)])
async def list_organization_invites(
    limit: int = Query(default=20, ge=1, le=100),
    after: str | None = Query(default=None),
) -> OrganizationInviteListResponse:
    """List all organization invites."""
    return await fakeai_service.list_organization_invites(limit=limit, after=after)


@app.post("/v1/organization/invites", dependencies=[Depends(verify_api_key)])
async def create_organization_invite(
    request: CreateOrganizationInviteRequest,
) -> OrganizationInvite:
    """Create an organization invite."""
    return await fakeai_service.create_organization_invite(request)


@app.get("/v1/organization/invites/{invite_id}", dependencies=[Depends(verify_api_key)])
async def get_organization_invite(invite_id: str) -> OrganizationInvite:
    """Get a specific organization invite."""
    try:
        return await fakeai_service.get_organization_invite(invite_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@app.delete("/v1/organization/invites/{invite_id}", dependencies=[Depends(verify_api_key)])
async def delete_organization_invite(invite_id: str) -> DeleteOrganizationInviteResponse:
    """Delete an organization invite."""
    try:
        return await fakeai_service.delete_organization_invite(invite_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# Organization Projects
@app.get("/v1/organization/projects", dependencies=[Depends(verify_api_key)])
async def list_organization_projects(
    limit: int = Query(default=20, ge=1, le=100),
    after: str | None = Query(default=None),
    include_archived: bool = Query(default=False),
) -> OrganizationProjectListResponse:
    """List all projects in the organization."""
    return await fakeai_service.list_organization_projects(
        limit=limit, after=after, include_archived=include_archived
    )


@app.post("/v1/organization/projects", dependencies=[Depends(verify_api_key)])
async def create_organization_project(
    request: CreateOrganizationProjectRequest,
) -> OrganizationProject:
    """Create a new project in the organization."""
    return await fakeai_service.create_organization_project(request)


@app.get("/v1/organization/projects/{project_id}", dependencies=[Depends(verify_api_key)])
async def get_organization_project(project_id: str) -> OrganizationProject:
    """Get a specific project."""
    try:
        return await fakeai_service.get_organization_project(project_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@app.post("/v1/organization/projects/{project_id}", dependencies=[Depends(verify_api_key)])
async def modify_organization_project(
    project_id: str, request: ModifyOrganizationProjectRequest
) -> OrganizationProject:
    """Modify a project."""
    try:
        return await fakeai_service.modify_organization_project(project_id, request)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@app.post(
    "/v1/organization/projects/{project_id}/archive", dependencies=[Depends(verify_api_key)]
)
async def archive_organization_project(
    project_id: str,
) -> ArchiveOrganizationProjectResponse:
    """Archive a project."""
    try:
        return await fakeai_service.archive_organization_project(project_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# Project Users
@app.get(
    "/v1/organization/projects/{project_id}/users", dependencies=[Depends(verify_api_key)]
)
async def list_project_users(
    project_id: str,
    limit: int = Query(default=20, ge=1, le=100),
    after: str | None = Query(default=None),
) -> ProjectUserListResponse:
    """List all users in a project."""
    try:
        return await fakeai_service.list_project_users(
            project_id, limit=limit, after=after
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@app.post(
    "/v1/organization/projects/{project_id}/users", dependencies=[Depends(verify_api_key)]
)
async def create_project_user(
    project_id: str, request: CreateProjectUserRequest
) -> ProjectUser:
    """Add a user to a project."""
    try:
        return await fakeai_service.create_project_user(project_id, request)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@app.get(
    "/v1/organization/projects/{project_id}/users/{user_id}",
    dependencies=[Depends(verify_api_key)],
)
async def get_project_user(project_id: str, user_id: str) -> ProjectUser:
    """Get a specific user in a project."""
    try:
        return await fakeai_service.get_project_user(project_id, user_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@app.post(
    "/v1/organization/projects/{project_id}/users/{user_id}",
    dependencies=[Depends(verify_api_key)],
)
async def modify_project_user(
    project_id: str, user_id: str, request: ModifyProjectUserRequest
) -> ProjectUser:
    """Modify a user's role in a project."""
    try:
        return await fakeai_service.modify_project_user(project_id, user_id, request)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@app.delete(
    "/v1/organization/projects/{project_id}/users/{user_id}",
    dependencies=[Depends(verify_api_key)],
)
async def delete_project_user(project_id: str, user_id: str) -> DeleteProjectUserResponse:
    """Remove a user from a project."""
    try:
        return await fakeai_service.delete_project_user(project_id, user_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# Project Service Accounts
@app.get(
    "/v1/organization/projects/{project_id}/service_accounts",
    dependencies=[Depends(verify_api_key)],
)
async def list_service_accounts(
    project_id: str,
    limit: int = Query(default=20, ge=1, le=100),
    after: str | None = Query(default=None),
) -> ServiceAccountListResponse:
    """List all service accounts in a project."""
    try:
        return await fakeai_service.list_service_accounts(
            project_id, limit=limit, after=after
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@app.post(
    "/v1/organization/projects/{project_id}/service_accounts",
    dependencies=[Depends(verify_api_key)],
)
async def create_service_account(
    project_id: str, request: CreateServiceAccountRequest
) -> ServiceAccount:
    """Create a service account in a project."""
    try:
        return await fakeai_service.create_service_account(project_id, request)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@app.get(
    "/v1/organization/projects/{project_id}/service_accounts/{service_account_id}",
    dependencies=[Depends(verify_api_key)],
)
async def get_service_account(project_id: str, service_account_id: str) -> ServiceAccount:
    """Get a specific service account."""
    try:
        return await fakeai_service.get_service_account(project_id, service_account_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@app.delete(
    "/v1/organization/projects/{project_id}/service_accounts/{service_account_id}",
    dependencies=[Depends(verify_api_key)],
)
async def delete_service_account(
    project_id: str, service_account_id: str
) -> DeleteServiceAccountResponse:
    """Delete a service account."""
    try:
        return await fakeai_service.delete_service_account(project_id, service_account_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# Usage and Billing API endpoints


@app.get("/v1/organization/usage/completions", dependencies=[Depends(verify_api_key)])
async def get_completions_usage(
    start_time: int = Query(description="Start time (Unix timestamp)"),
    end_time: int = Query(description="End time (Unix timestamp)"),
    bucket_width: str = Query(default="1d", description="Time bucket width ('1m', '1h', '1d')"),
    project_id: str | None = Query(default=None, description="Optional project ID filter"),
    model: str | None = Query(default=None, description="Optional model filter"),
) -> CompletionsUsageResponse:
    """
    Get usage data for completions endpoints.

    Returns aggregated usage data grouped by time buckets.
    """
    return await fakeai_service.get_completions_usage(
        start_time=start_time,
        end_time=end_time,
        bucket_width=bucket_width,
        project_id=project_id,
        model=model,
    )


@app.get("/v1/organization/usage/embeddings", dependencies=[Depends(verify_api_key)])
async def get_embeddings_usage(
    start_time: int = Query(description="Start time (Unix timestamp)"),
    end_time: int = Query(description="End time (Unix timestamp)"),
    bucket_width: str = Query(default="1d", description="Time bucket width ('1m', '1h', '1d')"),
    project_id: str | None = Query(default=None, description="Optional project ID filter"),
    model: str | None = Query(default=None, description="Optional model filter"),
) -> EmbeddingsUsageResponse:
    """
    Get usage data for embeddings endpoints.

    Returns aggregated usage data grouped by time buckets.
    """
    return await fakeai_service.get_embeddings_usage(
        start_time=start_time,
        end_time=end_time,
        bucket_width=bucket_width,
        project_id=project_id,
        model=model,
    )


@app.get("/v1/organization/usage/images", dependencies=[Depends(verify_api_key)])
async def get_images_usage(
    start_time: int = Query(description="Start time (Unix timestamp)"),
    end_time: int = Query(description="End time (Unix timestamp)"),
    bucket_width: str = Query(default="1d", description="Time bucket width ('1m', '1h', '1d')"),
    project_id: str | None = Query(default=None, description="Optional project ID filter"),
) -> ImagesUsageResponse:
    """
    Get usage data for images endpoints.

    Returns aggregated usage data grouped by time buckets.
    """
    return await fakeai_service.get_images_usage(
        start_time=start_time,
        end_time=end_time,
        bucket_width=bucket_width,
        project_id=project_id,
    )


@app.get("/v1/organization/usage/audio_speeches", dependencies=[Depends(verify_api_key)])
async def get_audio_speeches_usage(
    start_time: int = Query(description="Start time (Unix timestamp)"),
    end_time: int = Query(description="End time (Unix timestamp)"),
    bucket_width: str = Query(default="1d", description="Time bucket width ('1m', '1h', '1d')"),
    project_id: str | None = Query(default=None, description="Optional project ID filter"),
) -> AudioSpeechesUsageResponse:
    """
    Get usage data for audio speeches endpoints.

    Returns aggregated usage data grouped by time buckets.
    """
    return await fakeai_service.get_audio_speeches_usage(
        start_time=start_time,
        end_time=end_time,
        bucket_width=bucket_width,
        project_id=project_id,
    )


@app.get("/v1/organization/usage/audio_transcriptions", dependencies=[Depends(verify_api_key)])
async def get_audio_transcriptions_usage(
    start_time: int = Query(description="Start time (Unix timestamp)"),
    end_time: int = Query(description="End time (Unix timestamp)"),
    bucket_width: str = Query(default="1d", description="Time bucket width ('1m', '1h', '1d')"),
    project_id: str | None = Query(default=None, description="Optional project ID filter"),
) -> AudioTranscriptionsUsageResponse:
    """
    Get usage data for audio transcriptions endpoints.

    Returns aggregated usage data grouped by time buckets.
    """
    return await fakeai_service.get_audio_transcriptions_usage(
        start_time=start_time,
        end_time=end_time,
        bucket_width=bucket_width,
        project_id=project_id,
    )


@app.get("/v1/organization/costs", dependencies=[Depends(verify_api_key)])
async def get_costs(
    start_time: int = Query(description="Start time (Unix timestamp)"),
    end_time: int = Query(description="End time (Unix timestamp)"),
    bucket_width: str = Query(default="1d", description="Time bucket width ('1m', '1h', '1d')"),
    project_id: str | None = Query(default=None, description="Optional project ID filter"),
    group_by: list[str] | None = Query(default=None, description="Optional grouping dimensions"),
) -> CostsResponse:
    """
    Get cost data aggregated by time buckets.

    Returns cost breakdowns grouped by line item and project.
    """
    return await fakeai_service.get_costs(
        start_time=start_time,
        end_time=end_time,
        bucket_width=bucket_width,
        project_id=project_id,
        group_by=group_by,
    )


# Realtime WebSocket API endpoint
@app.websocket("/v1/realtime")
async def realtime_websocket(
    websocket: WebSocket,
    model: str = Query(default="openai/gpt-oss-120b-realtime-preview-2024-10-01"),
):
    """
    Realtime WebSocket API endpoint.

    Provides bidirectional streaming conversation with audio and text support,
    voice activity detection, and function calling.
    """
    await websocket.accept()
    logger.info(f"Realtime WebSocket connection established for model: {model}")

    # Create session handler
    session_handler = RealtimeSessionHandler(
        model=model,
        config=config,
        fakeai_service=fakeai_service,
    )

    # Send session.created event
    from fakeai.models import RealtimeEventType
    session_created = session_handler._create_event(
        RealtimeEventType.SESSION_CREATED,
        session=session_handler.session,
    )
    await websocket.send_text(session_created.model_dump_json())

    try:
        while True:
            # Receive client event
            data = await websocket.receive_text()

            try:
                import json
                event_data = json.loads(data)
                event_type = event_data.get("type")

                logger.debug(f"Received Realtime event: {event_type}")

                # Handle different event types
                if event_type == "session.update":
                    # Update session configuration
                    session_config = event_data.get("session", {})
                    response_event = session_handler.update_session(session_config)
                    await websocket.send_text(response_event.model_dump_json())

                elif event_type == "input_audio_buffer.append":
                    # Append audio to buffer
                    audio = event_data.get("audio", "")
                    events = session_handler.append_audio_buffer(audio)
                    for event in events:
                        await websocket.send_text(event.model_dump_json())

                elif event_type == "input_audio_buffer.commit":
                    # Commit audio buffer
                    events = session_handler.commit_audio_buffer()
                    for event in events:
                        await websocket.send_text(event.model_dump_json())

                elif event_type == "input_audio_buffer.clear":
                    # Clear audio buffer
                    event = session_handler.clear_audio_buffer()
                    await websocket.send_text(event.model_dump_json())

                elif event_type == "conversation.item.create":
                    # Create conversation item
                    item_data = event_data.get("item", {})
                    event = session_handler.create_conversation_item(item_data)
                    await websocket.send_text(event.model_dump_json())

                elif event_type == "conversation.item.delete":
                    # Delete conversation item
                    item_id = event_data.get("item_id", "")
                    event = session_handler.delete_conversation_item(item_id)
                    await websocket.send_text(event.model_dump_json())

                elif event_type == "response.create":
                    # Create response (streaming)
                    response_config = event_data.get("response", {})
                    async for event in session_handler.create_response(response_config):
                        await websocket.send_text(event.model_dump_json())

                elif event_type == "response.cancel":
                    # Cancel current response
                    event = session_handler.cancel_response()
                    await websocket.send_text(event.model_dump_json())

                else:
                    # Unknown event type
                    from fakeai.models import RealtimeError, RealtimeEventType
                    error_event = session_handler._create_event(
                        RealtimeEventType.ERROR,
                        error=RealtimeError(
                            type="invalid_request_error",
                            code="unknown_event",
                            message=f"Unknown event type: {event_type}",
                        ),
                    )
                    await websocket.send_text(error_event.model_dump_json())

            except json.JSONDecodeError as e:
                # Invalid JSON
                from fakeai.models import RealtimeError, RealtimeEventType
                error_event = session_handler._create_event(
                    RealtimeEventType.ERROR,
                    error=RealtimeError(
                        type="invalid_request_error",
                        code="invalid_json",
                        message=f"Invalid JSON: {str(e)}",
                    ),
                )
                await websocket.send_text(error_event.model_dump_json())

            except Exception as e:
                # Other errors
                logger.exception(f"Error processing Realtime event: {str(e)}")
                from fakeai.models import RealtimeError, RealtimeEventType
                error_event = session_handler._create_event(
                    RealtimeEventType.ERROR,
                    error=RealtimeError(
                        type="server_error",
                        code="internal_error",
                        message=f"Internal server error: {str(e)}",
                    ),
                )
                await websocket.send_text(error_event.model_dump_json())

    except WebSocketDisconnect:
        logger.info("Realtime WebSocket connection closed")
    except Exception as e:
        logger.exception(f"Unexpected error in Realtime WebSocket: {str(e)}")


# Fine-Tuning API endpoints
@app.post("/v1/fine_tuning/jobs", dependencies=[Depends(verify_api_key)])
async def create_fine_tuning_job(request: FineTuningJobRequest) -> FineTuningJob:
    """Create a new fine-tuning job."""
    try:
        return await fakeai_service.create_fine_tuning_job(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/v1/fine_tuning/jobs", dependencies=[Depends(verify_api_key)])
async def list_fine_tuning_jobs(
    limit: int = Query(default=20, ge=1, le=100),
    after: str | None = Query(default=None),
) -> FineTuningJobList:
    """List fine-tuning jobs with pagination."""
    return await fakeai_service.list_fine_tuning_jobs(limit=limit, after=after)


@app.get("/v1/fine_tuning/jobs/{job_id}", dependencies=[Depends(verify_api_key)])
async def retrieve_fine_tuning_job(job_id: str) -> FineTuningJob:
    """Retrieve a specific fine-tuning job."""
    try:
        return await fakeai_service.retrieve_fine_tuning_job(job_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/v1/fine_tuning/jobs/{job_id}/cancel", dependencies=[Depends(verify_api_key)])
async def cancel_fine_tuning_job(job_id: str) -> FineTuningJob:
    """Cancel a running or queued fine-tuning job."""
    try:
        return await fakeai_service.cancel_fine_tuning_job(job_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/v1/fine_tuning/jobs/{job_id}/events", dependencies=[Depends(verify_api_key)])
async def list_fine_tuning_events(
    job_id: str,
    limit: int = Query(default=20, ge=1, le=100),
):
    """Stream fine-tuning events via Server-Sent Events (SSE)."""
    try:
        async def event_stream():
            async for event in fakeai_service.list_fine_tuning_events(job_id, limit):
                yield event

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            },
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/v1/fine_tuning/jobs/{job_id}/checkpoints", dependencies=[Depends(verify_api_key)])
async def list_fine_tuning_checkpoints(
    job_id: str,
    limit: int = Query(default=10, ge=1, le=100),
) -> FineTuningCheckpointList:
    """List checkpoints for a fine-tuning job."""
    try:
        return await fakeai_service.list_fine_tuning_checkpoints(job_id, limit)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# Vector Stores API endpoints
@app.post("/v1/vector_stores", dependencies=[Depends(verify_api_key)])
async def create_vector_store(request: CreateVectorStoreRequest) -> VectorStore:
    """Create a new vector store."""
    return await fakeai_service.create_vector_store(request)


@app.get("/v1/vector_stores", dependencies=[Depends(verify_api_key)])
async def list_vector_stores(
    limit: int = Query(default=20, ge=1, le=100),
    order: str = Query(default="desc"),
    after: str | None = Query(default=None),
    before: str | None = Query(default=None),
) -> VectorStoreListResponse:
    """List all vector stores with pagination."""
    return await fakeai_service.list_vector_stores(
        limit=limit, order=order, after=after, before=before
    )


@app.get("/v1/vector_stores/{vector_store_id}", dependencies=[Depends(verify_api_key)])
async def retrieve_vector_store(vector_store_id: str) -> VectorStore:
    """Retrieve a vector store by ID."""
    try:
        return await fakeai_service.retrieve_vector_store(vector_store_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@app.post("/v1/vector_stores/{vector_store_id}", dependencies=[Depends(verify_api_key)])
async def modify_vector_store(
    vector_store_id: str, request: ModifyVectorStoreRequest
) -> VectorStore:
    """Modify a vector store."""
    try:
        return await fakeai_service.modify_vector_store(vector_store_id, request)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@app.delete("/v1/vector_stores/{vector_store_id}", dependencies=[Depends(verify_api_key)])
async def delete_vector_store(vector_store_id: str) -> dict:
    """Delete a vector store."""
    try:
        return await fakeai_service.delete_vector_store(vector_store_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# Vector Store Files endpoints
@app.post("/v1/vector_stores/{vector_store_id}/files", dependencies=[Depends(verify_api_key)])
async def create_vector_store_file(
    vector_store_id: str, request: CreateVectorStoreFileRequest
) -> VectorStoreFile:
    """Add a file to a vector store."""
    try:
        return await fakeai_service.create_vector_store_file(vector_store_id, request)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@app.get("/v1/vector_stores/{vector_store_id}/files", dependencies=[Depends(verify_api_key)])
async def list_vector_store_files(
    vector_store_id: str,
    limit: int = Query(default=20, ge=1, le=100),
    order: str = Query(default="desc"),
    after: str | None = Query(default=None),
    before: str | None = Query(default=None),
) -> VectorStoreFileListResponse:
    """List all files in a vector store with pagination."""
    try:
        return await fakeai_service.list_vector_store_files(
            vector_store_id, limit=limit, order=order, after=after, before=before
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@app.get(
    "/v1/vector_stores/{vector_store_id}/files/{file_id}",
    dependencies=[Depends(verify_api_key)],
)
async def retrieve_vector_store_file(
    vector_store_id: str, file_id: str
) -> VectorStoreFile:
    """Retrieve a specific file from a vector store."""
    try:
        return await fakeai_service.retrieve_vector_store_file(vector_store_id, file_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@app.delete(
    "/v1/vector_stores/{vector_store_id}/files/{file_id}",
    dependencies=[Depends(verify_api_key)],
)
async def delete_vector_store_file(vector_store_id: str, file_id: str) -> dict:
    """Remove a file from a vector store."""
    try:
        return await fakeai_service.delete_vector_store_file(vector_store_id, file_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# Vector Store File Batches endpoints
@app.post(
    "/v1/vector_stores/{vector_store_id}/file_batches",
    dependencies=[Depends(verify_api_key)],
)
async def create_vector_store_file_batch(
    vector_store_id: str, request: CreateVectorStoreFileBatchRequest
) -> VectorStoreFileBatch:
    """Create a batch of files in a vector store."""
    try:
        return await fakeai_service.create_vector_store_file_batch(vector_store_id, request)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@app.get(
    "/v1/vector_stores/{vector_store_id}/file_batches/{batch_id}",
    dependencies=[Depends(verify_api_key)],
)
async def retrieve_vector_store_file_batch(
    vector_store_id: str, batch_id: str
) -> VectorStoreFileBatch:
    """Retrieve a file batch from a vector store."""
    try:
        return await fakeai_service.retrieve_vector_store_file_batch(
            vector_store_id, batch_id
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@app.post(
    "/v1/vector_stores/{vector_store_id}/file_batches/{batch_id}/cancel",
    dependencies=[Depends(verify_api_key)],
)
async def cancel_vector_store_file_batch(
    vector_store_id: str, batch_id: str
) -> VectorStoreFileBatch:
    """Cancel a file batch in a vector store."""
    try:
        return await fakeai_service.cancel_vector_store_file_batch(vector_store_id, batch_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@app.get(
    "/v1/vector_stores/{vector_store_id}/file_batches/{batch_id}/files",
    dependencies=[Depends(verify_api_key)],
)
async def list_vector_store_files_in_batch(
    vector_store_id: str,
    batch_id: str,
    limit: int = Query(default=20, ge=1, le=100),
    order: str = Query(default="desc"),
    after: str | None = Query(default=None),
    before: str | None = Query(default=None),
) -> VectorStoreFileListResponse:
    """List files in a specific batch."""
    try:
        # For simplicity, just list all files in the vector store
        return await fakeai_service.list_vector_store_files(
            vector_store_id, limit=limit, order=order, after=after, before=before
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
