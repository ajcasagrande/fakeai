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
from fakeai.fakeai_service import FakeAIService
from fakeai.models import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    CompletionRequest,
    CompletionResponse,
    EmbeddingRequest,
    EmbeddingResponse,
    ErrorDetail,
    ErrorResponse,
    FileListResponse,
    FileObject,
    ImageGenerationRequest,
    ImageGenerationResponse,
    ModelListResponse,
    TextGenerationRequest,
    TextGenerationResponse,
)

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response, StreamingResponse

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

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the FakeAI service
fakeai_service = FakeAIService(config)


# Authentication dependency
async def verify_api_key(api_key: Annotated[str | None, Header(alias="Authorization")] = None):
    """Verifies the API key from the Authorization header."""
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key",
        )

    # Strip "Bearer " prefix if present
    if api_key.startswith("Bearer "):
        api_key = api_key[7:]

    # In a simulated environment, we can just check if the key is not empty
    # In a real implementation, you would validate against actual keys
    if not api_key or api_key == "invalid":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )
    return api_key


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests"""
    request_id = f"{int(time.time())}-{random.randint(1000, 9999)}"
    logger.info(f"Request {request_id}: {request.method} {request.url.path}")
    start_time = time.time()

    # Process the request
    try:
        response = await call_next(request)
        process_time = (time.time() - start_time) * 1000
        logger.info(
            f"Request {request_id} completed in {process_time:.2f}ms with status {response.status_code}"
        )
        return response
    except Exception as e:
        logger.exception(f"Request {request_id} failed: {str(e)}")
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
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


# Models endpoints
@app.get("/v1/models", dependencies=[Depends(verify_api_key)])
async def list_models() -> ModelListResponse:
    """List available models"""
    return await fakeai_service.list_models()


@app.get("/v1/models/{model_id}", dependencies=[Depends(verify_api_key)])
async def get_model(model_id: str):
    """Get model details"""
    return await fakeai_service.get_model(model_id)


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


# Text generation endpoints (for Azure compatibility)
@app.post("/v1/responses", dependencies=[Depends(verify_api_key)])
async def create_text_generation(
    request: TextGenerationRequest,
) -> TextGenerationResponse:
    """Create a text generation"""
    return await fakeai_service.create_text_generation(request)

