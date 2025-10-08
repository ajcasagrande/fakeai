#!/usr/bin/env python3
"""
FakeAI: OpenAI Compatible API Server

This module provides a FastAPI implementation that mimics the OpenAI API.
It supports all endpoints and features of the official OpenAI API but returns
simulated responses instead of performing actual inference.
"""
#  SPDX-License-Identifier: Apache-2.0

from fakeai.context_validator import ContextLengthExceededError
import asyncio
import json
import logging
import random
import time
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Annotated

from fastapi import (
    Depends,
    FastAPI,
    Header,
    HTTPException,
    Query,
    Request,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, Response, StreamingResponse

from fakeai.admin_auth import (
    LoginRequest,
    LoginResponse,
    LogoutResponse,
    VerifyResponse,
    login,
    logout,
    start_session_cleaner,
    verify_admin,
    verify_session,
)
from fakeai.config import AppConfig
from fakeai.config.live_config import LiveConfigManager
from fakeai.events import EventBusFactory
from fakeai.fakeai_service import FakeAIService, RealtimeSessionHandler
from fakeai.handlers import admin_config
from fakeai.metrics_streaming import MetricsStreamer
from fakeai.model_metrics import ModelMetricsTracker
from fakeai.models import (
    ArchiveOrganizationProjectResponse,
    Assistant,
    AssistantList,
    AudioSpeechesUsageResponse,
    AudioTranscriptionsUsageResponse,
    Batch,
    BatchListResponse,
    ChatCompletionRequest,
    CompletionRequest,
    CompletionsUsageResponse,
    CostsResponse,
    CreateAssistantRequest,
    CreateBatchRequest,
    CreateMessageRequest,
    CreateOrganizationInviteRequest,
    CreateOrganizationProjectRequest,
    CreateOrganizationUserRequest,
    CreateProjectUserRequest,
    CreateRunRequest,
    CreateServiceAccountRequest,
    CreateThreadRequest,
    CreateVectorStoreFileBatchRequest,
    CreateVectorStoreFileRequest,
    CreateVectorStoreRequest,
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
    FineTuningCheckpointList,
    FineTuningJob,
    FineTuningJobList,
    FineTuningJobRequest,
    ImageGenerationRequest,
    ImageGenerationResponse,
    ImagesUsageResponse,
    MessageList,
    ModelCapabilitiesResponse,
    ModelListResponse,
    ModerationRequest,
    ModerationResponse,
    ModifyAssistantRequest,
    ModifyOrganizationProjectRequest,
    ModifyOrganizationUserRequest,
    ModifyProjectUserRequest,
    ModifyRunRequest,
    ModifyThreadRequest,
    ModifyVectorStoreRequest,
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
    Run,
    RunList,
    RunStep,
    RunStepList,
    ServiceAccount,
    ServiceAccountListResponse,
    SolidoRagRequest,
    SolidoRagResponse,
    SpeechRequest,
    TextGenerationRequest,
    TextGenerationResponse,
    Thread,
    ThreadMessage,
    VectorStore,
    VectorStoreFile,
    VectorStoreFileBatch,
    VectorStoreFileListResponse,
    VectorStoreListResponse,
    VideoGenerationRequest,
    VideoGenerationResponse,
)
from fakeai.rate_limiter import RateLimiter
from fakeai.security import (
    AbuseDetector,
    ApiKeyManager,
    InjectionAttackDetected,
    InputValidator,
    PayloadTooLarge,
)
from fakeai.services.assistants_service import AssistantsService

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Import here to avoid circular dependency
    from fakeai.events import EventBusFactory

    # Startup
    global server_ready
    # Give a brief moment for all initialization to complete
    await asyncio.sleep(0.1)
    server_ready = True

    # Create and start event bus with all metrics trackers
    event_bus = EventBusFactory.create_event_bus(
        metrics_tracker=fakeai_service.metrics_tracker,
        streaming_tracker=None,  # Not currently used in FakeAIService
        cost_tracker=None,  # Not currently used in FakeAIService
        model_tracker=model_metrics_tracker,
        dynamo_collector=fakeai_service.dynamo_metrics,
        error_tracker=None,  # Not currently used in FakeAIService
        kv_cache_metrics=fakeai_service.kv_cache_metrics,
    )
    await event_bus.start()

    # Store event bus in app state for access in handlers
    app.state.event_bus = event_bus
    logger.info("Event bus started")

    # Start metrics streamer
    await metrics_streamer.start()

    # Start admin session cleaner
    asyncio.create_task(start_session_cleaner())

    logger.info("Server is ready to accept requests")

    yield

    # Shutdown
    # Stop event bus
    if hasattr(app.state, 'event_bus'):
        await app.state.event_bus.stop()
        logger.info("Event bus stopped")

    await metrics_streamer.stop()


# Initialize the application
app = FastAPI(
    title="FakeAI Server",
    description="An OpenAI-compatible API implementation for testing and development.",
    version="1.0.0",
    lifespan=lifespan,
)

# Load configuration
config = AppConfig()

# Add CORS middleware with configurable origins (from modular config)
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.security.cors_allowed_origins,
    allow_credentials=config.security.cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handler for context length exceeded errors


@app.exception_handler(ContextLengthExceededError)
async def context_length_exceeded_handler(
        request: Request,
        exc: ContextLengthExceededError):
    """Handle context length exceeded errors with proper OpenAI-compatible format."""
    return JSONResponse(
        status_code=400,
        content=exc.error_dict,
    )


# Initialize security components
api_key_manager = ApiKeyManager()
abuse_detector = AbuseDetector()
input_validator = InputValidator()

# Add API keys to manager (with hashing if enabled)
if config.auth.hash_api_keys:
    for key in config.auth.api_keys:
        api_key_manager.add_key(key)
else:
    # For backward compatibility, plain keys still work
    pass

# Initialize the FakeAI service
fakeai_service = FakeAIService(config)

# Get the metrics tracker singleton instance
metrics_tracker = fakeai_service.metrics_tracker

# Initialize per-model metrics tracker
model_metrics_tracker = ModelMetricsTracker()

# Initialize metrics streamer
metrics_streamer = MetricsStreamer(metrics_tracker)

# Initialize assistants service
assistants_service = AssistantsService(config, metrics_tracker)

# Server readiness state
server_ready = False

# Initialize rate limiter
rate_limiter = RateLimiter()
rate_limiter.configure(
    tier=config.rate_limits.tier,
    rpm_override=config.rate_limits.rpm_override,
    tpm_override=config.rate_limits.tpm_override,
)

# Initialize live configuration manager
live_config_manager = LiveConfigManager(config)


# Authentication dependency
async def verify_api_key(
    request: Request,
    api_key: Annotated[str | None, Header(alias="Authorization")] = None,
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
    if config.auth.hash_api_keys:
        # Use secure API key manager
        is_valid = api_key_manager.verify_key(api_key)
    else:
        # Backward compatibility: plain key check
        is_valid = api_key in config.auth.api_keys

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
    logger.debug(
        "Request %s: %s %s from %s",
        request_id,
        request.method,
        endpoint,
        client_ip)
    start_time = time.time()

    # Track the request in the metrics
    metrics_tracker.track_request(endpoint)

    # Check if IP is banned (for non-health endpoints)
    if config.enable_abuse_detection and endpoint not in [
            "/health", "/metrics"]:
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
            input_validator.validate_payload_size(
                body, config.max_request_size)

            # Validate for injection attacks if enabled
            if config.enable_injection_detection and body:
                try:
                    body_str = body.decode("utf-8", errors="ignore")
                    # Quick check for injection patterns in the raw request
                    input_validator.sanitize_string(
                        body_str[:10000]
                    )  # Check first 10KB
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
                            )).model_dump(),
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
    if config.rate_limit_enabled:
        # Extract API key from Authorization header
        auth_header = request.headers.get("Authorization", "")
        api_key = auth_header[7:] if auth_header.startswith(
            "Bearer ") else auth_header

        # Use API key if available, otherwise use default key for rate limiting
        effective_api_key = api_key if api_key else "anonymous"

        # Estimate token count from request body for chat/completions endpoints
        estimated_tokens = 0
        if endpoint in [
            "/v1/chat/completions",
            "/v1/completions",
            "/v1/embeddings",
        ]:
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
            effective_api_key, estimated_tokens)

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
                    )).model_dump(),
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
        "timestamp": datetime.now().isoformat(),
    }


# ==============================================================================
# ADMIN AUTHENTICATION API
# ==============================================================================

@app.post("/admin/login")
async def admin_login(request: LoginRequest) -> LoginResponse:
    """
    Admin login endpoint.

    Accepts any username/password for demo purposes.
    Returns a JWT token that can be used for authenticated admin requests.

    Example:
        curl -X POST http://localhost:8000/admin/login \
            -H "Content-Type: application/json" \
            -d '{"username": "admin", "password": "password"}'
    """
    return login(request.username, request.password)


@app.post("/admin/logout")
async def admin_logout(
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
) -> LogoutResponse:
    """
    Admin logout endpoint.

    Invalidates the current session.

    Example:
        curl -X POST http://localhost:8000/admin/logout \
            -H "Authorization: Bearer <token>"
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
        )

    # Strip "Bearer " prefix if present
    token = authorization
    if authorization.startswith("Bearer "):
        token = authorization[7:]

    return logout(token)


@app.get("/admin/verify")
async def admin_verify(
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
) -> VerifyResponse:
    """
    Verify admin session endpoint.

    Checks if the current session is valid.

    Example:
        curl -X GET http://localhost:8000/admin/verify \
            -H "Authorization: Bearer <token>"
    """
    if not authorization:
        return VerifyResponse(valid=False)

    # Strip "Bearer " prefix if present
    token = authorization
    if authorization.startswith("Bearer "):
        token = authorization[7:]

    return verify_session(token)


@app.get("/admin/status", dependencies=[Depends(verify_admin)])
async def admin_status(username: str = Depends(verify_admin)):
    """
    Example protected admin endpoint.

    This demonstrates how to protect routes with admin authentication.

    Example:
        curl -X GET http://localhost:8000/admin/status \
            -H "Authorization: Bearer <token>"
    """
    return {
        "message": f"Hello, admin {username}!",
        "timestamp": datetime.now().isoformat(),
        "server_ready": server_ready,
    }


# ==============================================================================
# ADMIN CONFIGURATION API
# ==============================================================================

@app.get("/admin/config", dependencies=[Depends(verify_admin)])
async def get_all_config_endpoint(username: str = Depends(verify_admin)):
    """
    Get all current configuration.

    Returns current values for all configuration sections:
    - KV cache settings
    - Dynamo/worker settings
    - Generation/timing settings
    - GPU/DCGM settings

    Example:
        curl -X GET http://localhost:8000/admin/config \
            -H "Authorization: Bearer <token>"
    """
    return await admin_config.get_all_config(live_config_manager)


@app.get("/admin/metrics", dependencies=[Depends(verify_admin)])
async def get_admin_metrics_endpoint(username: str = Depends(verify_admin)):
    """
    Get current system metrics for admin dashboard.

    Returns aggregated metrics from all tracking systems including:
    - Total requests processed
    - Active workers
    - Cache hit rate
    - Average TTFT/TPOT
    - GPU utilization
    - Queue depth
    - System uptime

    Requires admin authentication.
    """
    # Gather metrics from all trackers
    main_metrics = fakeai_service.metrics_tracker.get_metrics()
    kv_cache_stats = fakeai_service.kv_cache_metrics.get_stats()
    dynamo_metrics = fakeai_service.dynamo_metrics.get_stats_dict()
    dcgm_metrics = fakeai_service.dcgm_simulator.get_metrics_dict()

    # Calculate aggregate stats with proper null handling
    total_requests = sum(
        v.get(
            "count",
            0) for v in main_metrics.get(
            "requests",
            {}).values())

    worker_stats = dynamo_metrics.get("worker_stats", {})
    active_workers = worker_stats.get(
        "active_workers", 4) if worker_stats else 4

    cache_hit_rate = kv_cache_stats.get(
        "cache_hit_rate", 0.0) if kv_cache_stats else 0.0

    # Fix: Use correct field names - latency stats return "avg" not "avg_ms"
    # Fix: Use "itl" (inter-token latency) for TPOT, not "tpot" which doesn't
    # exist
    latency_data = dynamo_metrics.get("latency", {})
    ttft_data = latency_data.get("ttft", {}) if latency_data else {}
    itl_data = latency_data.get(
        "itl", {}) if latency_data else {}  # ITL is same as TPOT
    avg_ttft_ms = ttft_data.get("avg", 0.0) if ttft_data else 0.0
    avg_tpot_ms = itl_data.get(
        "avg", 0.0) if itl_data else 0.0  # Use ITL for TPOT

    # Get GPU utilization - fix field name from "utilization_percent" to
    # "gpu_utilization_pct"
    gpu_util = 0.0
    if dcgm_metrics and isinstance(dcgm_metrics, dict):
        gpu_utils = [
            gpu.get("gpu_utilization_pct", 0)
            for gpu in dcgm_metrics.values()
            if isinstance(gpu, dict) and "gpu_utilization_pct" in gpu
        ]
        gpu_util = sum(gpu_utils) / len(gpu_utils) if gpu_utils else 0.0

    queue_data = dynamo_metrics.get("queue", {})
    queue_depth = queue_data.get("current_depth", 0) if queue_data else 0

    # Calculate uptime
    start_time = getattr(
        fakeai_service.metrics_tracker,
        'start_time',
        time.time())
    uptime_seconds = int(time.time() - start_time)

    # Fix: Return field names that match TypeScript interface (avg_ttft_ms,
    # avg_tpot_ms)
    return {
        "success": True,
        "metrics": {
            "total_requests": total_requests or 0,
            "active_workers": active_workers or 0,
            "cache_hit_rate": cache_hit_rate or 0.0,
            "avg_ttft_ms": avg_ttft_ms or 0.0,
            "avg_tpot_ms": avg_tpot_ms or 0.0,
            "gpu_utilization": gpu_util or 0.0,
            "queue_depth": queue_depth or 0,
            "uptime_seconds": uptime_seconds or 0,
        }
    }


@app.patch("/admin/config/kv-cache", dependencies=[Depends(verify_admin)])
async def update_kv_cache_config_endpoint(
    update: admin_config.KVCacheConfigUpdate,
    username: str = Depends(verify_admin),
) -> admin_config.ConfigResponse:
    """
    Update KV cache configuration at runtime.

    Allows updating:
    - enabled: Enable/disable KV cache (boolean)
    - block_size: Cache block size, 8-64, must be power of 2 (integer)
    - overlap_weight: Weight for cache overlap scoring, 0.0-2.0 (float)
    - load_balance_weight: Weight for load balancing, 0.0-2.0 (float)

    Changes are applied immediately without server restart.

    Example:
        curl -X PATCH http://localhost:8000/admin/config/kv-cache \
            -H "Authorization: Bearer <token>" \
            -H "Content-Type: application/json" \
            -d '{"enabled": true, "block_size": 32}'
    """
    return await admin_config.update_kv_cache_config(update, live_config_manager)


@app.patch("/admin/config/dynamo", dependencies=[Depends(verify_admin)])
async def update_dynamo_config_endpoint(
    update: admin_config.DynamoConfigUpdate,
    username: str = Depends(verify_admin),
) -> admin_config.ConfigResponse:
    """
    Update Dynamo/worker configuration at runtime.

    Allows updating:
    - num_workers: Number of workers, 1-32 (integer)
    - worker_timeout: Worker timeout in seconds, 1.0-300.0 (float)
    - queue_depth_limit: Max queue depth, 1-10000 (integer)

    Changes are applied immediately without server restart.

    Example:
        curl -X PATCH http://localhost:8000/admin/config/dynamo \
            -H "Authorization: Bearer <token>" \
            -H "Content-Type: application/json" \
            -d '{"num_workers": 8, "queue_depth_limit": 1000}'
    """
    return await admin_config.update_dynamo_config(update, live_config_manager)


@app.patch("/admin/config/generation", dependencies=[Depends(verify_admin)])
async def update_generation_config_endpoint(
    update: admin_config.GenerationConfigUpdate,
    username: str = Depends(verify_admin),
) -> admin_config.ConfigResponse:
    """
    Update generation/timing configuration at runtime.

    Allows updating:
    - ttft_ms: Time to first token in milliseconds, 0.0-10000.0 (float)
    - ttft_variance_percent: TTFT variance as percentage, 0.0-100.0 (float)
    - itl_ms: Inter-token latency in milliseconds, 0.0-1000.0 (float)
    - itl_variance_percent: ITL variance as percentage, 0.0-100.0 (float)
    - response_delay: Base response delay in seconds, 0.0-10.0 (float)
    - random_delay: Enable random delay variation (boolean)
    - max_variance: Max variance factor, 0.0-1.0 (float)

    Changes are applied immediately without server restart.

    Example:
        curl -X PATCH http://localhost:8000/admin/config/generation \
            -H "Authorization: Bearer <token>" \
            -H "Content-Type: application/json" \
            -d '{"ttft_ms": 150.0, "itl_ms": 8.0}'
    """
    return await admin_config.update_generation_config(update, live_config_manager)


@app.patch("/admin/config/gpu", dependencies=[Depends(verify_admin)])
async def update_gpu_config_endpoint(
    update: admin_config.GPUConfigUpdate,
    username: str = Depends(verify_admin),
) -> admin_config.ConfigResponse:
    """
    Update GPU/DCGM configuration at runtime.

    Allows updating:
    - num_gpus: Number of GPUs, 1-8 (integer)
    - gpu_model: GPU model - A100-80GB, H100-80GB, or H200-141GB (string)
    - simulate_dcgm: Enable/disable DCGM simulation (boolean)

    Note: GPU model changes may require reinitialization of DCGM simulator.

    Changes are applied immediately without server restart.

    Example:
        curl -X PATCH http://localhost:8000/admin/config/gpu \
            -H "Authorization: Bearer <token>" \
            -H "Content-Type: application/json" \
            -d '{"num_gpus": 8, "gpu_model": "H100-80GB"}'
    """
    return await admin_config.update_gpu_config(update, live_config_manager)


@app.post("/admin/config/reset", dependencies=[Depends(verify_admin)])
async def reset_config_endpoint(
    username: str = Depends(verify_admin),
) -> admin_config.ConfigResponse:
    """
    Reset all configuration to defaults.

    Resets all configuration sections to their default values:
    - KV cache settings
    - Dynamo/worker settings
    - Generation/timing settings
    - GPU/DCGM settings

    Changes are applied immediately without server restart.

    Example:
        curl -X POST http://localhost:8000/admin/config/reset \
            -H "Authorization: Bearer <token>"
    """
    return await admin_config.reset_config(live_config_manager)


@app.get("/admin/config/history", dependencies=[Depends(verify_admin)])
async def get_config_history_endpoint(
    username: str = Depends(verify_admin),
    limit: int = Query(
        default=50,
        ge=1,
        le=200,
        description="Number of changes to return"),
):
    """
    Get configuration change audit trail.

    Returns a history of configuration changes with:
    - Timestamp of each change
    - Section and field changed
    - Old and new values
    - Most recent changes first

    Example:
        curl -X GET http://localhost:8000/admin/config/history?limit=20 \
            -H "Authorization: Bearer <token>"
    """
    return await admin_config.get_change_history(live_config_manager, limit=limit)


# Note: Startup and shutdown events are now handled by the lifespan context manager above


# Dashboard endpoints - SPA routing support
@app.get("/dashboard")
async def get_dashboard():
    """Serve the interactive metrics dashboard"""
    import os

    dashboard_path = os.path.join(
        os.path.dirname(__file__),
        "static",
        "dashboard.html")
    return FileResponse(dashboard_path, media_type="text/html")


@app.get("/dashboard/dynamo")
async def get_dynamo_dashboard():
    """Serve the advanced Dynamo dashboard with DCGM, KVBM, and SLA metrics"""
    import os

    dashboard_path = os.path.join(
        os.path.dirname(__file__), "static", "dashboard_advanced.html"
    )
    return FileResponse(dashboard_path, media_type="text/html")


# React SPA Dashboard - Serve static files and handle client-side routing
@app.get("/app")
async def get_app_dashboard():
    """Serve the React SPA dashboard"""
    from pathlib import Path

    app_path = Path(__file__).parent / "static" / "app" / "index.html"

    if not app_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Dashboard not built. Run 'python -m fakeai.dashboard.build' to build the dashboard."
        )

    return FileResponse(str(app_path), media_type="text/html")


# Serve static assets for SPA
@app.get("/app/{path:path}")
async def serve_app_static(path: str):
    """Serve static assets for the SPA dashboard or handle client-side routing"""
    from pathlib import Path

    static_dir = Path(__file__).parent / "static" / "app"
    file_path = static_dir / path

    # If the file exists, serve it
    if file_path.exists() and file_path.is_file():
        # Determine content type based on file extension
        content_type = "application/octet-stream"
        if path.endswith(".js"):
            content_type = "application/javascript"
        elif path.endswith(".css"):
            content_type = "text/css"
        elif path.endswith(".json"):
            content_type = "application/json"
        elif path.endswith(".png"):
            content_type = "image/png"
        elif path.endswith(".jpg") or path.endswith(".jpeg"):
            content_type = "image/jpeg"
        elif path.endswith(".svg"):
            content_type = "image/svg+xml"
        elif path.endswith(".ico"):
            content_type = "image/x-icon"
        elif path.endswith(".woff"):
            content_type = "font/woff"
        elif path.endswith(".woff2"):
            content_type = "font/woff2"
        elif path.endswith(".ttf"):
            content_type = "font/ttf"
        elif path.endswith(".eot"):
            content_type = "application/vnd.ms-fontobject"

        return FileResponse(str(file_path), media_type=content_type)

    # If the file doesn't exist, serve index.html for client-side routing
    index_path = static_dir / "index.html"

    if not index_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Dashboard not built. Run 'python -m fakeai.dashboard.build' to build the dashboard."
        )

    return FileResponse(str(index_path), media_type="text/html")


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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e))


@app.get("/v1/models/{model_id:path}/capabilities",
         dependencies=[Depends(verify_api_key)])
async def get_model_capabilities(model_id: str) -> ModelCapabilitiesResponse:
    """Get model capabilities including context window, pricing, and feature support"""
    return await fakeai_service.get_model_capabilities(model_id)


# Chat completions endpoints
@app.post("/v1/chat/completions",
          dependencies=[Depends(verify_api_key)],
          response_model=None)
async def create_chat_completion(
    request: ChatCompletionRequest,
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
):
    """Create a chat completion"""
    start_time = time.time()

    # Extract user from API key
    user = None
    if authorization and authorization.startswith("Bearer "):
        user = authorization[7:][:20]  # Use first 20 chars as identifier

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
        response = await fakeai_service.create_chat_completion(request)
        # Metrics tracked via events

        return response


# Completions endpoints
@app.post("/v1/completions",
          dependencies=[Depends(verify_api_key)],
          response_model=None)
async def create_completion(
    request: CompletionRequest,
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
):
    """Create a completion"""
    start_time = time.time()

    # Extract user from API key
    user = None
    if authorization and authorization.startswith("Bearer "):
        user = authorization[7:][:20]

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
        response = await fakeai_service.create_completion(request)
        # Metrics tracked via events

        return response


# Embeddings endpoint
@app.post("/v1/embeddings", dependencies=[Depends(verify_api_key)])
async def create_embedding(
    request: EmbeddingRequest,
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
) -> EmbeddingResponse:
    """Create embeddings"""
    start_time = time.time()

    # Extract user from API key
    user = None
    if authorization and authorization.startswith("Bearer "):
        user = authorization[7:][:20]

    response = await fakeai_service.create_embedding(request)
    # Metrics tracked via events

    return response


# Images endpoints
@app.post("/v1/images/generations", dependencies=[Depends(verify_api_key)])
async def generate_images(
        request: ImageGenerationRequest) -> ImageGenerationResponse:
    """Generate images"""
    return await fakeai_service.generate_images(request)


@app.get("/images/{image_id}.png")
async def get_image(image_id: str) -> Response:
    """
    Retrieve a generated image by ID.

    This endpoint serves actual generated images when image generation is enabled.
    Images are stored in memory and automatically cleaned up after retention period.
    """
    if not fakeai_service.image_generator:
        raise HTTPException(
            status_code=404,
            detail="Image generation is disabled. Enable with FAKEAI_GENERATE_ACTUAL_IMAGES=true",
        )

    image_bytes = fakeai_service.image_generator.get_image(image_id)

    if image_bytes is None:
        raise HTTPException(
            status_code=404,
            detail="Image not found or expired")

    return Response(
        content=image_bytes,
        media_type="image/png",
        headers={
            "Cache-Control": "public, max-age=3600",
            "Content-Disposition": f'inline; filename="{image_id}.png"',
        },
    )


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


# Video generation endpoint
@app.post("/v1/videos/generations", dependencies=[Depends(verify_api_key)])
async def generate_videos(
        request: VideoGenerationRequest) -> VideoGenerationResponse:
    """
    Generate videos from text prompts.

    This endpoint simulates video generation by creating placeholder videos.
    In a real implementation, this would call actual video generation models.
    """
    return await fakeai_service.generate_videos(request)


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


# Text generation endpoints (for Azure compatibility) - Moved to
# /v1/text/generation
@app.post("/v1/text/generation", dependencies=[Depends(verify_api_key)])
async def create_text_generation(
    request: TextGenerationRequest,
) -> TextGenerationResponse:
    """Create a text generation (Azure API compatibility)"""
    return await fakeai_service.create_text_generation(request)


# OpenAI Responses API endpoint (March 2025 format)
@app.post("/v1/responses",
          dependencies=[Depends(verify_api_key)],
          response_model=None)
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


# ═══════════════════════════════════════════════════════════════════════════
# Waterfall Chart Visualization Endpoints
# ═══════════════════════════════════════════════════════════════════════════


@app.get("/waterfall/data")
async def waterfall_data_endpoint(
    limit: int = Query(100, ge=1, le=1000),
    endpoint: str | None = Query(None),
    model: str | None = Query(None),
):
    """
    Get waterfall timing data as JSON.

    Returns detailed request timing data for visualization.
    """
    from fakeai.waterfall.api import get_waterfall_data

    return get_waterfall_data(limit=limit, endpoint=endpoint, model=model)


@app.get("/waterfall", response_class=HTMLResponse)
async def waterfall_chart_endpoint(
    limit: int = Query(100, ge=1, le=1000),
    endpoint: str | None = Query(None),
    model: str | None = Query(None),
    width: int = Query(1200, ge=800, le=3000),
    height: int = Query(600, ge=400, le=2000),
):
    """
    Get interactive waterfall chart HTML visualization.

    Shows request timeline, TTFT markers, and token generation.
    """
    from fakeai.waterfall.api import get_waterfall_chart_html

    return get_waterfall_chart_html(
        limit=limit, endpoint=endpoint, model=model, width=width, height=height
    )


@app.websocket("/metrics/stream")
async def metrics_stream(websocket: WebSocket):
    """
    Real-time metrics streaming via WebSocket.

    Supports subscription-based filtering by endpoint, model, and metric type.
    Clients can control update intervals and receive delta calculations.

    Example client usage:
    ```javascript
    const ws = new WebSocket('ws://localhost:8000/metrics/stream');
    ws.onopen = () => {
        ws.send(JSON.stringify({
            type: 'subscribe',
            filters: {
                endpoint: '/v1/chat/completions',
                interval: 1.0
            }
        }));
    };
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('Metrics update:', data);
    };
    ```
    """
    await metrics_streamer.handle_websocket(websocket)


@app.websocket("/kv-cache/stream")
async def kv_cache_stream(websocket: WebSocket):
    """
    Real-time KV cache metrics streaming via WebSocket.

    Streams cache performance and smart router statistics in real-time.
    """
    await websocket.accept()
    connected = True

    try:
        # Send initial data
        await websocket.send_json({
            "type": "connected",
            "timestamp": time.time()
        })

        while connected:
            # Wait for messages from client (ping, subscribe, etc.)
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=1.0)
                message = json.loads(data)

                if message.get("type") == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": time.time()
                    })
            except asyncio.TimeoutError:
                pass
            except json.JSONDecodeError:
                pass
            except Exception as e:
                # Client likely disconnected
                logger.debug(f"Error receiving from KV cache WebSocket: {e}")
                connected = False
                break

            # Send metrics update only if still connected
            try:
                metrics_data = {
                    "type": "kv_cache_update",
                    "timestamp": time.time(),
                    "data": {
                        "cache_performance": fakeai_service.kv_cache_metrics.get_stats(),
                        "smart_router": fakeai_service.kv_cache_router.get_stats(),
                    }}

                await websocket.send_json(metrics_data)
                await asyncio.sleep(1.0)  # Update every second
            except Exception as e:
                # Connection closed, stop sending
                logger.debug(f"Error sending to KV cache WebSocket: {e}")
                connected = False
                break

    except WebSocketDisconnect:
        logger.info("KV cache WebSocket client disconnected")
    except Exception as e:
        logger.error(f"KV cache WebSocket error: {e}")
        # Don't try to send error messages if connection is already closed
        if connected:
            try:
                await websocket.send_json({
                    "type": "error",
                    "message": str(e)
                })
            except Exception:
                # Connection closed, can't send error
                pass


@app.websocket("/ai-dynamo/stream")
async def ai_dynamo_stream(websocket: WebSocket):
    """
    Real-time AI-Dynamo metrics streaming via WebSocket.

    Streams comprehensive AI-Dynamo inference metrics in real-time.
    """
    await websocket.accept()
    connected = True

    try:
        # Send initial data
        await websocket.send_json({
            "type": "connected",
            "timestamp": time.time()
        })

        while connected:
            # Wait for messages from client (ping, subscribe, etc.)
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=1.0)
                message = json.loads(data)

                if message.get("type") == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": time.time()
                    })
            except asyncio.TimeoutError:
                pass
            except json.JSONDecodeError:
                pass
            except Exception as e:
                # Client likely disconnected
                logger.debug(f"Error receiving from AI-Dynamo WebSocket: {e}")
                connected = False
                break

            # Send metrics update only if still connected
            try:
                # Get AI-Dynamo metrics from dynamo_metrics tracker
                # Use the same data structure as the HTTP endpoint
                dynamo_stats = fakeai_service.dynamo_metrics.get_stats_dict()

                metrics_data = {
                    "type": "ai_dynamo_update",
                    "timestamp": time.time(),
                    "data": dynamo_stats
                }

                await websocket.send_json(metrics_data)
                await asyncio.sleep(1.0)  # Update every second
            except Exception as e:
                # Connection closed, stop sending
                logger.debug(f"Error sending to AI-Dynamo WebSocket: {e}")
                connected = False
                break

    except WebSocketDisconnect:
        logger.info("AI-Dynamo WebSocket client disconnected")
    except Exception as e:
        logger.error(f"AI-Dynamo WebSocket error: {e}")
        # Don't try to send error messages if connection is already closed
        if connected:
            try:
                await websocket.send_json({
                    "type": "error",
                    "message": str(e)
                })
            except Exception:
                # Connection closed, can't send error
                pass


@app.websocket("/dcgm/stream")
async def dcgm_stream(websocket: WebSocket):
    """
    Real-time DCGM metrics streaming via WebSocket.

    Streams comprehensive DCGM GPU metrics in real-time.
    """
    await websocket.accept()
    connected = True

    try:
        # Send initial data
        await websocket.send_json({
            "type": "connected",
            "timestamp": time.time()
        })

        while connected:
            # Wait for messages from client (ping, subscribe, etc.)
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=1.0)
                message = json.loads(data)

                if message.get("type") == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": time.time()
                    })
            except asyncio.TimeoutError:
                pass
            except json.JSONDecodeError:
                pass
            except Exception as e:
                # Client likely disconnected
                logger.debug(f"Error receiving from DCGM WebSocket: {e}")
                connected = False
                break

            # Send metrics update only if still connected
            try:
                # Get DCGM metrics from dcgm_simulator
                metrics = fakeai_service.dcgm_simulator.get_metrics_dict()

                metrics_data = {
                    "type": "dcgm_update",
                    "timestamp": time.time(),
                    "data": metrics
                }

                await websocket.send_json(metrics_data)
                await asyncio.sleep(1.0)  # Update every second
            except Exception as e:
                # Connection closed, stop sending
                logger.debug(f"Error sending to DCGM WebSocket: {e}")
                connected = False
                break

    except WebSocketDisconnect:
        logger.info("DCGM WebSocket client disconnected")
    except Exception as e:
        logger.error(f"DCGM WebSocket error: {e}")
        # Don't try to send error messages if connection is already closed
        if connected:
            try:
                await websocket.send_json({
                    "type": "error",
                    "message": str(e)
                })
            except Exception:
                # Connection closed, can't send error
                pass


@app.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with metrics summary"""
    return metrics_tracker.get_detailed_health()


@app.get("/kv-cache/metrics")
async def get_kv_cache_metrics():
    """Get KV cache and AI-Dynamo smart routing metrics."""
    return {
        "cache_performance": fakeai_service.kv_cache_metrics.get_stats(),
        "smart_router": fakeai_service.kv_cache_router.get_stats(),
    }


# Per-Model Metrics endpoints
@app.get("/metrics/by-model")
async def get_metrics_by_model():
    """Get metrics grouped by model in JSON format."""
    return model_metrics_tracker.get_all_models_stats()


@app.get("/metrics/by-model/prometheus")
async def get_model_metrics_prometheus():
    """Get per-model metrics in Prometheus format."""
    return Response(
        content=model_metrics_tracker.get_prometheus_metrics(),
        media_type="text/plain; version=0.0.4",
    )


@app.get("/metrics/by-model/{model_id:path}")
async def get_model_metrics(model_id: str):
    """Get metrics for a specific model."""
    return model_metrics_tracker.get_model_stats(model_id)


@app.get("/metrics/compare")
async def compare_models(
    model1: str = Query(..., description="First model ID"),
    model2: str = Query(..., description="Second model ID"),
):
    """
    Compare two models side-by-side.

    Returns comparison metrics including:
    - Request counts
    - Latency differences
    - Error rates
    - Cost comparisons
    - Winner determination
    """
    return model_metrics_tracker.compare_models(model1, model2)


@app.get("/metrics/ranking")
async def get_model_ranking(
        metric: str = Query(
            default="request_count",
            description="Metric to rank by (request_count, latency, error_rate, cost, tokens)",
        ),
    limit: int = Query(
            default=10,
            ge=1,
            le=100,
            description="Number of models to return"),
):
    """
    Get top models ranked by a specific metric.

    Supports ranking by:
    - request_count: Most used models
    - latency: Fastest models
    - error_rate: Most reliable models
    - cost: Most expensive models
    - tokens: Highest token usage
    """
    return model_metrics_tracker.get_model_ranking(metric=metric, limit=limit)


@app.get("/metrics/costs")
async def get_costs_by_model():
    """Get estimated cost breakdown by model."""
    return {
        "costs_by_model": model_metrics_tracker.get_cost_by_model(),
        "total_cost_usd": sum(
            model_metrics_tracker.get_cost_by_model().values()),
    }


@app.get("/metrics/multi-dimensional")
async def get_multi_dimensional_metrics():
    """
    Get multi-dimensional metrics breakdown.

    Returns 2D breakdowns:
    - Model by endpoint
    - Model by user
    - Model by time (24h buckets)
    """
    return model_metrics_tracker.get_multi_dimensional_stats()


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


# Rate Limiter Metrics endpoints
@app.get("/metrics/rate-limits")
async def get_rate_limit_metrics():
    """
    Get comprehensive rate limiting metrics.

    Returns detailed statistics including:
    - Per-key metrics (requests, tokens, throttling)
    - Tier-level aggregations
    - Throttle analytics (histograms, distributions)
    - Abuse pattern detection
    """
    return rate_limiter.metrics.get_all_metrics()


@app.get("/metrics/rate-limits/key/{api_key}")
async def get_rate_limit_key_stats(api_key: str):
    """
    Get rate limiting statistics for a specific API key.

    Args:
        api_key: The API key to retrieve stats for

    Returns detailed metrics including:
    - Request counts (attempted, allowed, throttled)
    - Token consumption and efficiency
    - Throttling statistics
    - Usage patterns and peaks
    - Quota utilization
    """
    stats = rate_limiter.metrics.get_key_stats(api_key)
    if not stats:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No metrics found for API key: {api_key}",
        )
    return stats


@app.get("/metrics/rate-limits/tier")
async def get_rate_limit_tier_stats():
    """
    Get rate limiting statistics aggregated by tier.

    Returns per-tier aggregations including:
    - Total requests and tokens
    - Average throttle rates
    - Keys with high throttle rates
    - Quota exhaustion events
    - Upgrade opportunities
    """
    return rate_limiter.metrics.get_tier_stats()


@app.get("/metrics/rate-limits/throttle-analytics")
async def get_throttle_analytics():
    """
    Get detailed throttling analytics.

    Returns:
    - Throttle duration histogram
    - Retry-after distribution (percentiles)
    - RPM vs TPM exceeded breakdown
    """
    return rate_limiter.metrics.get_throttle_analytics()


@app.get("/metrics/rate-limits/abuse-patterns")
async def get_abuse_patterns():
    """
    Detect potential abuse patterns across API keys.

    Analyzes:
    - High throttle rates (>50%)
    - Excessive retries
    - Burst behavior
    - Quota exhaustion patterns

    Returns list of API keys with detected abuse patterns,
    including severity classification.
    """
    return rate_limiter.metrics.detect_abuse_patterns()


# Moderation endpoint
@app.post("/v1/moderations", dependencies=[Depends(verify_api_key)])
async def create_moderation(request: ModerationRequest) -> ModerationResponse:
    """Classify if text and/or image inputs are potentially harmful."""
    return await fakeai_service.create_moderation(request)


# Batch API endpoints
@app.post("/v1/batches", dependencies=[Depends(verify_api_key)])
async def create_batch(request: CreateBatchRequest) -> Batch:
    """Create a batch processing job."""
    if fakeai_service.batch_service is None:
        raise HTTPException(
            status_code=501,
            detail="Batch service not available")
    return await fakeai_service.create_batch(request)


@app.get("/v1/batches/{batch_id}", dependencies=[Depends(verify_api_key)])
async def retrieve_batch(batch_id: str) -> Batch:
    """Retrieve a batch by ID."""
    if fakeai_service.batch_service is None:
        raise HTTPException(
            status_code=501,
            detail="Batch service not available")
    try:
        return await fakeai_service.retrieve_batch(batch_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e))


@app.post("/v1/batches/{batch_id}/cancel",
          dependencies=[Depends(verify_api_key)])
async def cancel_batch(batch_id: str) -> Batch:
    """Cancel a batch."""
    if fakeai_service.batch_service is None:
        raise HTTPException(
            status_code=501,
            detail="Batch service not available")
    try:
        return await fakeai_service.cancel_batch(batch_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e))


@app.get("/v1/batches", dependencies=[Depends(verify_api_key)])
async def list_batches(
    limit: int = Query(default=20, ge=1, le=100),
    after: str | None = Query(default=None),
) -> BatchListResponse:
    """List all batches with pagination."""
    if fakeai_service.batch_service is None:
        raise HTTPException(
            status_code=501,
            detail="Batch service not available")
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


@app.get("/v1/organization/users/{user_id}",
         dependencies=[Depends(verify_api_key)])
async def get_organization_user(user_id: str) -> OrganizationUser:
    """Get a specific organization user."""
    try:
        return await fakeai_service.get_organization_user(user_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e))


@app.post("/v1/organization/users", dependencies=[Depends(verify_api_key)])
async def create_organization_user(
    request: CreateOrganizationUserRequest,
) -> OrganizationUser:
    """Add a user to the organization."""
    return await fakeai_service.create_organization_user(request)


@app.post("/v1/organization/users/{user_id}",
          dependencies=[Depends(verify_api_key)])
async def modify_organization_user(
    user_id: str, request: ModifyOrganizationUserRequest
) -> OrganizationUser:
    """Modify an organization user's role."""
    try:
        return await fakeai_service.modify_organization_user(user_id, request)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e))


@app.delete("/v1/organization/users/{user_id}",
            dependencies=[Depends(verify_api_key)])
async def delete_organization_user(user_id: str) -> dict:
    """Remove a user from the organization."""
    try:
        return await fakeai_service.delete_organization_user(user_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e))


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


@app.get("/v1/organization/invites/{invite_id}",
         dependencies=[Depends(verify_api_key)])
async def get_organization_invite(invite_id: str) -> OrganizationInvite:
    """Get a specific organization invite."""
    try:
        return await fakeai_service.get_organization_invite(invite_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e))


@app.delete("/v1/organization/invites/{invite_id}",
            dependencies=[Depends(verify_api_key)])
async def delete_organization_invite(
    invite_id: str,
) -> DeleteOrganizationInviteResponse:
    """Delete an organization invite."""
    try:
        return await fakeai_service.delete_organization_invite(invite_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e))


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


@app.get("/v1/organization/projects/{project_id}",
         dependencies=[Depends(verify_api_key)])
async def get_organization_project(project_id: str) -> OrganizationProject:
    """Get a specific project."""
    try:
        return await fakeai_service.get_organization_project(project_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e))


@app.post("/v1/organization/projects/{project_id}",
          dependencies=[Depends(verify_api_key)])
async def modify_organization_project(
    project_id: str, request: ModifyOrganizationProjectRequest
) -> OrganizationProject:
    """Modify a project."""
    try:
        return await fakeai_service.modify_organization_project(project_id, request)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e))


@app.post(
    "/v1/organization/projects/{project_id}/archive",
    dependencies=[Depends(verify_api_key)],
)
async def archive_organization_project(
    project_id: str,
) -> ArchiveOrganizationProjectResponse:
    """Archive a project."""
    try:
        return await fakeai_service.archive_organization_project(project_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e))


# Project Users
@app.get(
    "/v1/organization/projects/{project_id}/users",
    dependencies=[Depends(verify_api_key)],
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e))


@app.post(
    "/v1/organization/projects/{project_id}/users",
    dependencies=[Depends(verify_api_key)],
)
async def create_project_user(
    project_id: str, request: CreateProjectUserRequest
) -> ProjectUser:
    """Add a user to a project."""
    try:
        return await fakeai_service.create_project_user(project_id, request)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e))


@app.get(
    "/v1/organization/projects/{project_id}/users/{user_id}",
    dependencies=[Depends(verify_api_key)],
)
async def get_project_user(project_id: str, user_id: str) -> ProjectUser:
    """Get a specific user in a project."""
    try:
        return await fakeai_service.get_project_user(project_id, user_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e))


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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e))


@app.delete(
    "/v1/organization/projects/{project_id}/users/{user_id}",
    dependencies=[Depends(verify_api_key)],
)
async def delete_project_user(
    project_id: str, user_id: str
) -> DeleteProjectUserResponse:
    """Remove a user from a project."""
    try:
        return await fakeai_service.delete_project_user(project_id, user_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e))


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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e))


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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e))


@app.get(
    "/v1/organization/projects/{project_id}/service_accounts/{service_account_id}",
    dependencies=[
        Depends(verify_api_key)],
)
async def get_service_account(
    project_id: str, service_account_id: str
) -> ServiceAccount:
    """Get a specific service account."""
    try:
        return await fakeai_service.get_service_account(project_id, service_account_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e))


@app.delete(
    "/v1/organization/projects/{project_id}/service_accounts/{service_account_id}",
    dependencies=[
        Depends(verify_api_key)],
)
async def delete_service_account(
    project_id: str, service_account_id: str
) -> DeleteServiceAccountResponse:
    """Delete a service account."""
    try:
        return await fakeai_service.delete_service_account(
            project_id, service_account_id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e))


# Usage and Billing API endpoints


@app.get("/v1/organization/usage/completions",
         dependencies=[Depends(verify_api_key)])
async def get_completions_usage(
        start_time: int = Query(
            description="Start time (Unix timestamp)"),
    end_time: int = Query(
            description="End time (Unix timestamp)"),
        bucket_width: str = Query(
            default="1d",
            description="Time bucket width ('1m', '1h', '1d')"),
        project_id: str | None = Query(
            default=None,
            description="Optional project ID filter"),
        model: str | None = Query(
            default=None,
            description="Optional model filter"),
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


@app.get("/v1/organization/usage/embeddings",
         dependencies=[Depends(verify_api_key)])
async def get_embeddings_usage(
        start_time: int = Query(
            description="Start time (Unix timestamp)"),
    end_time: int = Query(
            description="End time (Unix timestamp)"),
        bucket_width: str = Query(
            default="1d",
            description="Time bucket width ('1m', '1h', '1d')"),
        project_id: str | None = Query(
            default=None,
            description="Optional project ID filter"),
        model: str | None = Query(
            default=None,
            description="Optional model filter"),
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


@app.get("/v1/organization/usage/images",
         dependencies=[Depends(verify_api_key)])
async def get_images_usage(
    start_time: int = Query(description="Start time (Unix timestamp)"),
    end_time: int = Query(description="End time (Unix timestamp)"),
    bucket_width: str = Query(
        default="1d", description="Time bucket width ('1m', '1h', '1d')"
    ),
    project_id: str | None = Query(
        default=None, description="Optional project ID filter"
    ),
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


@app.get("/v1/organization/usage/audio_speeches",
         dependencies=[Depends(verify_api_key)])
async def get_audio_speeches_usage(
    start_time: int = Query(description="Start time (Unix timestamp)"),
    end_time: int = Query(description="End time (Unix timestamp)"),
    bucket_width: str = Query(
        default="1d", description="Time bucket width ('1m', '1h', '1d')"
    ),
    project_id: str | None = Query(
        default=None, description="Optional project ID filter"
    ),
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


@app.get(
    "/v1/organization/usage/audio_transcriptions",
    dependencies=[Depends(verify_api_key)],
)
async def get_audio_transcriptions_usage(
    start_time: int = Query(description="Start time (Unix timestamp)"),
    end_time: int = Query(description="End time (Unix timestamp)"),
    bucket_width: str = Query(
        default="1d", description="Time bucket width ('1m', '1h', '1d')"
    ),
    project_id: str | None = Query(
        default=None, description="Optional project ID filter"
    ),
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
    bucket_width: str = Query(
        default="1d", description="Time bucket width ('1m', '1h', '1d')"
    ),
    project_id: str | None = Query(
        default=None, description="Optional project ID filter"
    ),
    group_by: list[str] | None = Query(
        default=None, description="Optional grouping dimensions"
    ),
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
async def realtime_websocket(websocket: WebSocket, model: str = Query(
        default="openai/gpt-oss-120b-realtime-preview-2024-10-01"), ):
    """
    Realtime WebSocket API endpoint.

    Provides bidirectional streaming conversation with audio and text support,
    voice activity detection, and function calling.
    """
    await websocket.accept()
    logger.info(
        f"Realtime WebSocket connection established for model: {model}")

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
                    response_event = session_handler.update_session(
                        session_config)
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
async def create_fine_tuning_job(
        request: FineTuningJobRequest) -> FineTuningJob:
    """Create a new fine-tuning job."""
    try:
        return await fakeai_service.fine_tuning_service.create_fine_tuning_job(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/v1/fine_tuning/jobs", dependencies=[Depends(verify_api_key)])
async def list_fine_tuning_jobs(
    limit: int = Query(default=20, ge=1, le=100),
    after: str | None = Query(default=None),
) -> FineTuningJobList:
    """List fine-tuning jobs with pagination."""
    return await fakeai_service.fine_tuning_service.list_fine_tuning_jobs(limit=limit, after=after)


@app.get("/v1/fine_tuning/jobs/{job_id}",
         dependencies=[Depends(verify_api_key)])
async def retrieve_fine_tuning_job(job_id: str) -> FineTuningJob:
    """Retrieve a specific fine-tuning job."""
    try:
        return await fakeai_service.fine_tuning_service.retrieve_fine_tuning_job(job_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/v1/fine_tuning/jobs/{job_id}/cancel",
          dependencies=[Depends(verify_api_key)])
async def cancel_fine_tuning_job(job_id: str) -> FineTuningJob:
    """Cancel a running or queued fine-tuning job."""
    try:
        return await fakeai_service.fine_tuning_service.cancel_fine_tuning_job(job_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/v1/fine_tuning/jobs/{job_id}/events",
         dependencies=[Depends(verify_api_key)])
async def list_fine_tuning_events(
    job_id: str,
    limit: int = Query(default=20, ge=1, le=100),
):
    """Stream fine-tuning events via Server-Sent Events (SSE)."""
    try:

        async def event_stream():
            async for event in fakeai_service.fine_tuning_service.list_fine_tuning_events(job_id, limit):
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


@app.get("/v1/fine_tuning/jobs/{job_id}/checkpoints",
         dependencies=[Depends(verify_api_key)])
async def list_fine_tuning_checkpoints(
    job_id: str,
    limit: int = Query(default=10, ge=1, le=100),
) -> FineTuningCheckpointList:
    """List checkpoints for a fine-tuning job."""
    try:
        return await fakeai_service.fine_tuning_service.list_fine_tuning_checkpoints(job_id, limit)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# Vector Stores API endpoints
@app.post("/v1/vector_stores", dependencies=[Depends(verify_api_key)])
async def create_vector_store(
        request: CreateVectorStoreRequest) -> VectorStore:
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


@app.get("/v1/vector_stores/{vector_store_id}",
         dependencies=[Depends(verify_api_key)])
async def retrieve_vector_store(vector_store_id: str) -> VectorStore:
    """Retrieve a vector store by ID."""
    try:
        return await fakeai_service.retrieve_vector_store(vector_store_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e))


@app.post("/v1/vector_stores/{vector_store_id}",
          dependencies=[Depends(verify_api_key)])
async def modify_vector_store(
    vector_store_id: str, request: ModifyVectorStoreRequest
) -> VectorStore:
    """Modify a vector store."""
    try:
        return await fakeai_service.modify_vector_store(vector_store_id, request)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e))


@app.delete("/v1/vector_stores/{vector_store_id}",
            dependencies=[Depends(verify_api_key)])
async def delete_vector_store(vector_store_id: str) -> dict:
    """Delete a vector store."""
    try:
        return await fakeai_service.delete_vector_store(vector_store_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e))


# Vector Store Files endpoints
@app.post("/v1/vector_stores/{vector_store_id}/files",
          dependencies=[Depends(verify_api_key)])
async def create_vector_store_file(
    vector_store_id: str, request: CreateVectorStoreFileRequest
) -> VectorStoreFile:
    """Add a file to a vector store."""
    try:
        return await fakeai_service.create_vector_store_file(vector_store_id, request)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e))


@app.get("/v1/vector_stores/{vector_store_id}/files",
         dependencies=[Depends(verify_api_key)])
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e))


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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e))


@app.delete(
    "/v1/vector_stores/{vector_store_id}/files/{file_id}",
    dependencies=[Depends(verify_api_key)],
)
async def delete_vector_store_file(vector_store_id: str, file_id: str) -> dict:
    """Remove a file from a vector store."""
    try:
        return await fakeai_service.delete_vector_store_file(vector_store_id, file_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e))


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
        return await fakeai_service.create_vector_store_file_batch(
            vector_store_id, request
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e))


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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e))


@app.post(
    "/v1/vector_stores/{vector_store_id}/file_batches/{batch_id}/cancel",
    dependencies=[Depends(verify_api_key)],
)
async def cancel_vector_store_file_batch(
    vector_store_id: str, batch_id: str
) -> VectorStoreFileBatch:
    """Cancel a file batch in a vector store."""
    try:
        return await fakeai_service.cancel_vector_store_file_batch(
            vector_store_id, batch_id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e))


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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e))
# ==============================================================================
# ASSISTANTS API

# Assistants CRUD endpoints


@app.post("/v1/assistants", dependencies=[Depends(verify_api_key)])
async def create_assistant(request: CreateAssistantRequest) -> Assistant:
    """Create a new assistant."""
    return await assistants_service.create_assistant(request)


@app.get("/v1/assistants", dependencies=[Depends(verify_api_key)])
async def list_assistants(
    limit: int = Query(default=20, ge=1, le=100),
    order: str = Query(default="desc"),
    after: str | None = Query(default=None),
    before: str | None = Query(default=None),
) -> AssistantList:
    """List assistants with pagination."""
    return await assistants_service.list_assistants(
        limit=limit, order=order, after=after, before=before
    )


@app.get("/v1/assistants/{assistant_id}",
         dependencies=[Depends(verify_api_key)])
async def retrieve_assistant(assistant_id: str) -> Assistant:
    """Retrieve a specific assistant."""
    try:
        return await assistants_service.retrieve_assistant(assistant_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/v1/assistants/{assistant_id}",
          dependencies=[Depends(verify_api_key)])
async def modify_assistant(
    assistant_id: str, request: ModifyAssistantRequest
) -> Assistant:
    """Modify an existing assistant."""
    try:
        return await assistants_service.modify_assistant(assistant_id, request)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.delete("/v1/assistants/{assistant_id}",
            dependencies=[Depends(verify_api_key)])
async def delete_assistant(assistant_id: str) -> dict:
    """Delete an assistant."""
    try:
        return await assistants_service.delete_assistant(assistant_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# Threads endpoints
@app.post("/v1/threads", dependencies=[Depends(verify_api_key)])
async def create_thread(request: CreateThreadRequest) -> Thread:
    """Create a new thread."""
    return await assistants_service.create_thread(request)


@app.get("/v1/threads/{thread_id}", dependencies=[Depends(verify_api_key)])
async def retrieve_thread(thread_id: str) -> Thread:
    """Retrieve a specific thread."""
    try:
        return await assistants_service.retrieve_thread(thread_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/v1/threads/{thread_id}", dependencies=[Depends(verify_api_key)])
async def modify_thread(
        thread_id: str,
        request: ModifyThreadRequest) -> Thread:
    """Modify a thread."""
    try:
        return await assistants_service.modify_thread(thread_id, request)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.delete("/v1/threads/{thread_id}", dependencies=[Depends(verify_api_key)])
async def delete_thread(thread_id: str) -> dict:
    """Delete a thread."""
    try:
        return await assistants_service.delete_thread(thread_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# Messages endpoints
@app.post("/v1/threads/{thread_id}/messages",
          dependencies=[Depends(verify_api_key)])
async def create_message(
        thread_id: str,
        request: CreateMessageRequest) -> ThreadMessage:
    """Create a message in a thread."""
    try:
        return await assistants_service.create_message(thread_id, request)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/v1/threads/{thread_id}/messages",
         dependencies=[Depends(verify_api_key)])
async def list_messages(
    thread_id: str,
    limit: int = Query(default=20, ge=1, le=100),
    order: str = Query(default="desc"),
    after: str | None = Query(default=None),
    before: str | None = Query(default=None),
) -> MessageList:
    """List messages in a thread."""
    try:
        return await assistants_service.list_messages(
            thread_id=thread_id, limit=limit, order=order, after=after, before=before
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get(
    "/v1/threads/{thread_id}/messages/{message_id}",
    dependencies=[Depends(verify_api_key)],
)
async def retrieve_message(thread_id: str, message_id: str) -> ThreadMessage:
    """Retrieve a specific message."""
    try:
        return await assistants_service.retrieve_message(thread_id, message_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post(
    "/v1/threads/{thread_id}/messages/{message_id}",
    dependencies=[Depends(verify_api_key)],
)
async def modify_message(
    thread_id: str, message_id: str, request: dict
) -> ThreadMessage:
    """Modify a message (only metadata)."""
    try:
        return await assistants_service.modify_message(
            thread_id, message_id, metadata=request.get("metadata")
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# Runs endpoints
@app.post("/v1/threads/{thread_id}/runs",
          dependencies=[Depends(verify_api_key)],
          response_model=None)
async def create_run(thread_id: str, request: CreateRunRequest):
    """Create a run."""
    try:
        return await assistants_service.create_run(thread_id, request)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/v1/threads/{thread_id}/runs",
         dependencies=[Depends(verify_api_key)])
async def list_runs(
    thread_id: str,
    limit: int = Query(default=20, ge=1, le=100),
    order: str = Query(default="desc"),
    after: str | None = Query(default=None),
    before: str | None = Query(default=None),
) -> RunList:
    """List runs in a thread."""
    try:
        return await assistants_service.list_runs(
            thread_id=thread_id, limit=limit, order=order, after=after, before=before
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get(
    "/v1/threads/{thread_id}/runs/{run_id}",
    dependencies=[Depends(verify_api_key)],
)
async def retrieve_run(thread_id: str, run_id: str) -> Run:
    """Retrieve a specific run."""
    try:
        return await assistants_service.retrieve_run(thread_id, run_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post(
    "/v1/threads/{thread_id}/runs/{run_id}",
    dependencies=[Depends(verify_api_key)],
)
async def modify_run(
        thread_id: str,
        run_id: str,
        request: ModifyRunRequest) -> Run:
    """Modify a run (only metadata)."""
    try:
        return await assistants_service.modify_run(thread_id, run_id, request)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post(
    "/v1/threads/{thread_id}/runs/{run_id}/cancel",
    dependencies=[Depends(verify_api_key)],
)
async def cancel_run(thread_id: str, run_id: str) -> Run:
    """Cancel a run."""
    try:
        return await assistants_service.cancel_run(thread_id, run_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post(
    "/v1/threads/{thread_id}/runs/{run_id}/submit_tool_outputs",
    dependencies=[Depends(verify_api_key)],
)
async def submit_tool_outputs(
    thread_id: str, run_id: str, request: dict
) -> Run:
    """Submit tool outputs for a run."""
    try:
        tool_outputs = request.get("tool_outputs", [])
        return await assistants_service.submit_tool_outputs(thread_id, run_id, tool_outputs)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# Run Steps endpoints
@app.get(
    "/v1/threads/{thread_id}/runs/{run_id}/steps",
    dependencies=[Depends(verify_api_key)],
)
async def list_run_steps(
    thread_id: str,
    run_id: str,
    limit: int = Query(default=20, ge=1, le=100),
    order: str = Query(default="desc"),
    after: str | None = Query(default=None),
    before: str | None = Query(default=None),
) -> RunStepList:
    """List steps for a run."""
    try:
        return await assistants_service.list_run_steps(
            thread_id=thread_id,
            run_id=run_id,
            limit=limit,
            order=order,
            after=after,
            before=before,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get(
    "/v1/threads/{thread_id}/runs/{run_id}/steps/{step_id}",
    dependencies=[Depends(verify_api_key)],
)
async def retrieve_run_step(
        thread_id: str,
        run_id: str,
        step_id: str) -> RunStep:
    """Retrieve a specific run step."""
    try:
        return await assistants_service.retrieve_run_step(thread_id, run_id, step_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
