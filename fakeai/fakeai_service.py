"""
FakeAI Service Implementation

This module provides a simulated implementation of the OpenAI API services.
It simulates the behavior of the actual API by generating realistic responses
with appropriate delays to mimic real-world workloads.
"""

#  SPDX-License-Identifier: Apache-2.0

import asyncio
import base64
import hashlib
import json
import logging
import random
import re
import time
import uuid
from collections.abc import AsyncGenerator
from typing import Any

from faker import Faker

from fakeai.audio import (
    calculate_audio_input_tokens,
    extract_text_from_audio,
    generate_audio_output,
)
from fakeai.config import AppConfig
from fakeai.context_validator import (
    ContextLengthExceededError,
    create_context_length_error,
    validate_context_length,
)
from fakeai.dcgm_metrics import (
    DCGMMetricsSimulator,
)
from fakeai.dynamo_metrics import (
    DynamoMetricsCollector,
)
from fakeai.kv_cache import (
    KVCacheMetrics,
    SmartRouter,
    tokenize_for_cache,
)
from fakeai.logprobs_enhanced import (
    create_chat_logprobs,
    create_completion_logprobs,
)
from fakeai.metrics import MetricsTracker
from fakeai.models import (
    ArchiveOrganizationProjectResponse,
    AudioOutput,
    AudioSpeechesUsageResponse,
    AudioTranscriptionsUsageResponse,
    Batch,
    BatchListResponse,
    ChatCompletionChoice,
    ChatCompletionChunk,
    ChatCompletionChunkChoice,
    ChatCompletionRequest,
    ChatCompletionResponse,
    CompletionChoice,
    CompletionChunk,
    CompletionRequest,
    CompletionResponse,
    CompletionsUsageResponse,
    CompletionTokensDetails,
    CostAmount,
    CostBucket,
    CostResult,
    CostsResponse,
    CreateBatchRequest,
    CreateOrganizationInviteRequest,
    CreateOrganizationProjectRequest,
    CreateOrganizationUserRequest,
    CreateProjectUserRequest,
    CreateServiceAccountRequest,
    CreateVectorStoreFileBatchRequest,
    CreateVectorStoreFileRequest,
    CreateVectorStoreRequest,
    DeleteOrganizationInviteResponse,
    DeleteProjectUserResponse,
    DeleteServiceAccountResponse,
    Delta,
    EmbeddingRequest,
    EmbeddingResponse,
    EmbeddingsUsageResponse,
    FileListResponse,
    FileObject,
    ImageGenerationRequest,
    ImageGenerationResponse,
    ImagesUsageResponse,
    LogProbs,
    Message,
    Model,
    ModelCapabilitiesResponse,
    ModelListResponse,
    ModelPermission,
    ModelPricing,
    ModifyOrganizationProjectRequest,
    ModifyOrganizationUserRequest,
    ModifyProjectUserRequest,
    ModifyVectorStoreRequest,
    OrganizationInvite,
    OrganizationInviteListResponse,
    OrganizationProject,
    OrganizationProjectListResponse,
    OrganizationUser,
    OrganizationUserListResponse,
    ProjectUser,
    ProjectUserListResponse,
    PromptTokensDetails,
    RealtimeAudioFormat,
    RealtimeContent,
    RealtimeContentType,
    RealtimeError,
    RealtimeEvent,
    RealtimeEventType,
    RealtimeItem,
    RealtimeItemRole,
    RealtimeItemStatus,
    RealtimeItemType,
    RealtimeModality,
    RealtimeRateLimits,
    RealtimeResponse,
    RealtimeSession,
    RealtimeSessionConfig,
    RealtimeTool,
    RealtimeTurnDetection,
    RealtimeVoice,
    Role,
    ServiceAccount,
    ServiceAccountListResponse,
    SpeechRequest,
    TextGenerationRequest,
    TextGenerationResponse,
    Usage,
    UsageAggregationBucket,
    UsageResultItem,
    VectorStore,
    VectorStoreFile,
    VectorStoreFileBatch,
    VectorStoreFileListResponse,
    VectorStoreListResponse,
    VideoGenerationRequest,
    VideoGenerationResponse,
)
from fakeai.semantic_embeddings import (
    SemanticEmbeddingGenerator,
    get_semantic_embedding_generator,
)
from fakeai.services.audio_service import AudioService
from fakeai.services.embedding_service import EmbeddingService
from fakeai.services.image_generation_service import ImageGenerationService
from fakeai.services.moderation_service import ModerationService
from fakeai.services.vector_store_service import VectorStoreService
from fakeai.structured_outputs import (
    SchemaValidationError,
    format_as_json_string,
    generate_from_schema,
    validate_strict_schema,
)
from fakeai.utils import (
    AsyncExecutor,
    SimulatedGenerator,
    calculate_token_count,
    generate_simulated_audio,
    tokenize_text,
)
from fakeai.video import calculate_message_video_tokens
from fakeai.vision import calculate_message_image_tokens

logger = logging.getLogger(__name__)
fake = Faker()


class UsageTracker:
    """
    Tracks API usage and calculates costs for billing.

    This class maintains detailed records of all API calls including:
    - Token usage (input, output, cached)
    - Model information
    - Timestamps for time-based aggregation
    - Project and user identifiers
    """

    # OpenAI pricing per 1M tokens (as of 2024)
    MODEL_PRICING = {
        # GPT-4 Turbo models
        "openai/gpt-oss-120b": {"input": 10.0, "output": 30.0},
        "openai/gpt-oss-120b-2024-04-09": {"input": 10.0, "output": 30.0},
        "openai/gpt-oss-120b-preview": {"input": 10.0, "output": 30.0},
        "openai/gpt-oss-120b-0125-preview": {"input": 10.0, "output": 30.0},
        "openai/gpt-oss-120b-1106-preview": {"input": 10.0, "output": 30.0},
        # GPT-4 models
        "openai/gpt-oss-120b": {"input": 30.0, "output": 60.0},
        "openai/gpt-oss-120b-0613": {"input": 30.0, "output": 60.0},
        "openai/gpt-oss-120b-32k": {"input": 60.0, "output": 120.0},
        "openai/gpt-oss-120b-32k-0613": {"input": 60.0, "output": 120.0},
        # GPT-4o models
        "openai/gpt-oss-120b": {"input": 5.0, "output": 15.0},
        "openai/gpt-oss-120b-2024-05-13": {"input": 5.0, "output": 15.0},
        "openai/gpt-oss-20b": {"input": 0.15, "output": 0.60},
        "openai/gpt-oss-20b-2024-07-18": {"input": 0.15, "output": 0.60},
        # GPT-3.5 Turbo models
        "meta-llama/Llama-3.1-8B-Instruct": {"input": 0.50, "output": 1.50},
        "meta-llama/Llama-3.1-8B-Instruct-0125": {"input": 0.50, "output": 1.50},
        "meta-llama/Llama-3.1-8B-Instruct-1106": {"input": 1.0, "output": 2.0},
        "meta-llama/Llama-3.1-8B-Instruct": {"input": 1.50, "output": 2.0},
        # deepseek-ai/DeepSeek-R1 models
        "deepseek-ai/DeepSeek-R1": {"input": 15.0, "output": 60.0},
        "deepseek-ai/DeepSeek-R1-2024-09-12": {"input": 15.0, "output": 60.0},
        "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B": {"input": 3.0, "output": 12.0},
        "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B-2024-09-12": {
            "input": 3.0,
            "output": 12.0,
        },
        # Embeddings
        "nomic-ai/nomic-embed-text-v1.5": {"input": 0.02, "output": 0.0},
        "BAAI/bge-m3": {"input": 0.13, "output": 0.0},
        "sentence-transformers/all-mpnet-base-v2": {"input": 0.10, "output": 0.0},
        # Images (per image, not per token)
        "stabilityai/stable-diffusion-xl-base-1.0": {
            "input": 0.040,
            "output": 0.0,
        },  # Standard 1024x1024
        "stabilityai/stable-diffusion-2-1": {
            "input": 0.020,
            "output": 0.0,
        },  # 1024x1024
        # Audio
        "tts-1": {"input": 15.0, "output": 0.0},  # per 1M characters
        "tts-1-hd": {"input": 30.0, "output": 0.0},  # per 1M characters
        "whisper-1": {"input": 0.006, "output": 0.0},  # per minute
    }

    def __init__(self):
        """Initialize the usage tracker."""
        # Store usage records: list of dicts with timestamp, model, tokens,
        # etc.
        self.usage_records: list[dict[str, Any]] = []

    def track_usage(
        self,
        endpoint: str,
        model: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        cached_tokens: int = 0,
        project_id: str | None = None,
        user_id: str | None = None,
        num_requests: int = 1,
    ) -> None:
        """
        Track usage for an API call.

        Args:
            endpoint: API endpoint (e.g., '/v1/chat/completions')
            model: Model ID used
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            cached_tokens: Number of cached input tokens
            project_id: Optional project identifier
            user_id: Optional user identifier
            num_requests: Number of API requests (default: 1)
        """
        record = {
            "timestamp": time.time(),
            "endpoint": endpoint,
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cached_tokens": cached_tokens,
            "project_id": project_id,
            "user_id": user_id,
            "num_requests": num_requests,
        }
        self.usage_records.append(record)

    def calculate_cost(
        self, model: str, input_tokens: int, output_tokens: int
    ) -> float:
        """
        Calculate cost in USD for given token usage.

        Args:
            model: Model ID
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Cost in USD
        """
        # Get pricing for model (use default if not found)
        pricing = self.MODEL_PRICING.get(
            model, {"input": 1.0, "output": 2.0}  # Default pricing
        )

        # Calculate cost (pricing is per 1M tokens)
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]

        return input_cost + output_cost

    def get_usage_by_time_bucket(
        self,
        start_time: int,
        end_time: int,
        bucket_size: str = "1d",
        project_id: str | None = None,
        model: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Get usage aggregated by time buckets.

        Args:
            start_time: Start timestamp (Unix)
            end_time: End timestamp (Unix)
            bucket_size: Time bucket size ('1m', '1h', '1d')
            project_id: Optional project filter
            model: Optional model filter

        Returns:
            List of time buckets with aggregated usage
        """
        # Determine bucket size in seconds
        bucket_seconds = {
            "1m": 60,
            "1h": 3600,
            "1d": 86400,
        }.get(bucket_size, 86400)

        # Filter records by time range
        filtered = [r for r in self.usage_records if start_time <=
                    r["timestamp"] <= end_time]

        # Apply optional filters
        if project_id:
            filtered = [r for r in filtered if r.get(
                "project_id") == project_id]
        if model:
            filtered = [r for r in filtered if r["model"] == model]

        # Group by time buckets
        buckets: dict[int, dict[str, Any]] = {}

        for record in filtered:
            # Calculate bucket start time
            bucket_start = int(
                record["timestamp"] //
                bucket_seconds *
                bucket_seconds)

            if bucket_start not in buckets:
                buckets[bucket_start] = {
                    "start_time": bucket_start,
                    "end_time": bucket_start + bucket_seconds,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "cached_tokens": 0,
                    "num_requests": 0,
                }

            # Aggregate
            buckets[bucket_start]["input_tokens"] += record["input_tokens"]
            buckets[bucket_start]["output_tokens"] += record["output_tokens"]
            buckets[bucket_start]["cached_tokens"] += record["cached_tokens"]
            buckets[bucket_start]["num_requests"] += record["num_requests"]

        # Convert to sorted list
        return sorted(buckets.values(), key=lambda x: x["start_time"])

    def get_costs_by_time_bucket(
        self,
        start_time: int,
        end_time: int,
        bucket_size: str = "1d",
        project_id: str | None = None,
        group_by: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Get costs aggregated by time buckets.

        Args:
            start_time: Start timestamp (Unix)
            end_time: End timestamp (Unix)
            bucket_size: Time bucket size ('1m', '1h', '1d')
            project_id: Optional project filter
            group_by: Optional grouping dimensions (e.g., ['model', 'project_id'])

        Returns:
            List of time buckets with cost breakdowns
        """
        # Determine bucket size in seconds
        bucket_seconds = {
            "1m": 60,
            "1h": 3600,
            "1d": 86400,
        }.get(bucket_size, 86400)

        # Filter records by time range
        filtered = [r for r in self.usage_records if start_time <=
                    r["timestamp"] <= end_time]

        # Apply project filter
        if project_id:
            filtered = [r for r in filtered if r.get(
                "project_id") == project_id]

        # Group by time buckets and dimensions
        buckets: dict[int, dict[str, list[dict[str, Any]]]] = {}

        for record in filtered:
            # Calculate bucket start time
            bucket_start = int(
                record["timestamp"] //
                bucket_seconds *
                bucket_seconds)

            if bucket_start not in buckets:
                buckets[bucket_start] = {
                    "start_time": bucket_start,
                    "end_time": bucket_start + bucket_seconds,
                    "results": [],
                }

            # Calculate cost for this record
            cost = self.calculate_cost(
                record["model"],
                record["input_tokens"],
                record["output_tokens"])

            # Determine line item based on endpoint
            endpoint = record["endpoint"]
            if "chat/completions" in endpoint or "completions" in endpoint:
                line_item = "completions"
            elif "embeddings" in endpoint:
                line_item = "embeddings"
            elif "images" in endpoint:
                line_item = "images"
            elif "audio/speech" in endpoint:
                line_item = "audio_speeches"
            elif "audio/transcriptions" in endpoint:
                line_item = "audio_transcriptions"
            else:
                line_item = "other"

            # Create or update result entry
            result_key = (line_item, record.get("project_id"))
            existing = next(
                (
                    r
                    for r in buckets[bucket_start]["results"]
                    if r["line_item"] == line_item and
                    r.get("project_id") == record.get("project_id")
                ),
                None,
            )

            if existing:
                existing["amount"]["value"] += cost
            else:
                buckets[bucket_start]["results"].append(
                    {
                        "line_item": line_item,
                        "amount": {"value": cost, "currency": "usd"},
                        "project_id": record.get("project_id"),
                    }
                )

        # Convert to sorted list
        return sorted(buckets.values(), key=lambda x: x["start_time"])


class FakeAIService:
    """Simulated implementation of OpenAI API services.

    This class provides methods that simulate the behavior of the OpenAI API,
    generating simulated responses that mimic the format and structure of the real API.
    """

    def __init__(self, config: AppConfig):
        """Initialize the simulated service with configuration."""
        self.config = config
        self.generator = SimulatedGenerator()
        self.executor = AsyncExecutor()

        # Create seeded random instance for deterministic behavior
        self._random = random.Random()
        self._current_seed = None

        # Initialize metrics tracker singleton
        self.metrics_tracker = MetricsTracker()

        # Initialize usage tracker for billing
        self.usage_tracker = UsageTracker()

        # Initialize KV cache system (AI-Dynamo simulation)
        self.kv_cache_router = SmartRouter(
            kv_overlap_weight=1.0,
            load_balance_weight=0.5,
            block_size=16,
            num_workers=4,
        )
        self.kv_cache_metrics = KVCacheMetrics()

        # Initialize Dynamo metrics collector (LLM inference metrics)
        self.dynamo_metrics = DynamoMetricsCollector(window_size=300)

        # Initialize DCGM GPU metrics simulator (4× H100 GPUs)
        self.dcgm_simulator = DCGMMetricsSimulator(
            num_gpus=4, gpu_model="H100-80GB")

        # Initialize semantic embeddings generator (optional)
        self.semantic_embeddings: SemanticEmbeddingGenerator | None = None
        if config.generation.use_semantic_embeddings:
            try:
                self.semantic_embeddings = get_semantic_embedding_generator(
                    model_name=config.generation.embedding_model,
                    use_gpu=config.generation.embedding_use_gpu,
                )
                logger.info(
                    f"Semantic embeddings enabled: model={
                        config.embedding_model}, " f"use_gpu={
                        config.embedding_use_gpu}")
            except Exception as e:
                logger.warning(
                    f"Failed to initialize semantic embeddings: {e}")
                logger.info("Falling back to random embeddings")

        # Initialize audio service
        self.audio_service = AudioService(
            config=config,
            metrics_tracker=self.metrics_tracker,
        )

        # Initialize embedding service
        self.embedding_service = EmbeddingService(
            config=config,
            metrics_tracker=self.metrics_tracker,
            model_registry=None,  # Will use _ensure_model_exists from parent
        )

        # Initialize moderation service
        self.moderation_service = ModerationService(
            config=config,
            metrics_tracker=self.metrics_tracker,
            model_registry=None,  # Will use _ensure_model_exists from parent
        )

        # Initialize image generator (optional)
        self.image_generator: ImageGenerator | None = None
        if config.generation.generate_actual_images:
            try:
                from fakeai.image_generator import ImageGenerator

                # Determine base URL from config
                base_url = f"http://{config.server.host}:{config.server.port}"
                self.image_generator = ImageGenerator(
                    base_url=base_url,
                    storage_backend=config.storage.image_storage_backend,
                    retention_hours=config.storage.image_retention_hours,
                )
                logger.info(
                    f"Image generator enabled: backend={
                        config.storage.image_storage_backend}, " f"retention={
                        config.storage.image_retention_hours}h")
            except Exception as e:
                logger.warning(f"Failed to initialize image generator: {e}")
                logger.info("Falling back to fake URLs")

        # Initialize image generation service
        self.image_generation_service = ImageGenerationService(
            config=config,
            metrics_tracker=self.metrics_tracker,
            image_generator=self.image_generator,
        )

        # Initialize file manager for batch processing and file uploads
        from fakeai.file_manager import FileManager

        self.file_manager = FileManager(storage_backend="memory")

        # Initialize batch metrics tracker
        from fakeai.batch_metrics import BatchMetricsTracker

        self.batch_metrics = BatchMetricsTracker()

        # Initialize batch service with all dependencies
        from fakeai.services.batch_service import BatchService

        self.batch_service = BatchService(
            config=config,
            metrics_tracker=self.metrics_tracker,
            model_registry=None,  # Will use _ensure_model_exists from parent
            file_manager=self.file_manager,
            batch_metrics=self.batch_metrics,
        )
        # Set parent service reference for batch execution
        self.batch_service.set_parent_service(self)

        # Initialize prompt cache system
        # Format: {hash: (token_count, timestamp)}
        self._prompt_cache: dict[str, tuple[int, float]] = {}

        # Initialize simulated data
        self._init_simulated_models()
        self._init_simulated_files()

        # Initialize fine-tuning service (after files are initialized)
        from fakeai.services.fine_tuning_service import FineTuningService

        self.fine_tuning_service = FineTuningService(
            config=config,
            metrics_tracker=self.metrics_tracker,
            file_storage=self.files,
        )

        # Initialize vector store service (will be set up after files are initialized)
        # Note: We'll use a simple file lookup adapter since FakeAIService uses
        # self.files list
        self.vector_store_service: VectorStoreService | None = None

        # Initialize organization and project management storage
        # user_id -> user data
        self.organization_users: dict[str, dict[str, Any]] = {}
        self.organization_invites: dict[str, dict[str, Any]] = (
            {}
        )  # invite_id -> invite data
        # project_id -> project data
        self.projects: dict[str, dict[str, Any]] = {}
        self.project_users: dict[str, dict[str, list[str]]] = (
            {}
        )  # project_id -> {user_id -> role}
        self.service_accounts: dict[str, dict[str, Any]] = (
            {}
        )  # project_id -> {account_id -> account data}

        # Initialize Assistants API storage
        # assistant_id -> Assistant object
        self.assistants: dict[str, Any] = {}
        self.threads: dict[str, Any] = {}  # thread_id -> Thread object
        self.thread_messages: dict[str, list[Any]] = (
            {}
        )  # thread_id -> list of ThreadMessage objects
        self.runs: dict[str, Any] = {}  # run_id -> Run object
        # run_id -> list of RunStep objects
        self.run_steps: dict[str, list[Any]] = {}
        self.run_tasks: dict[str, asyncio.Task] = (
            {}
        )  # run_id -> async task for background execution

    def _init_simulated_models(self) -> None:
        """Initialize simulated model data with comprehensive metadata."""
        creation_time = int(time.time()) - 10000
        base_permission = ModelPermission(
            id=f"modelperm-{uuid.uuid4().hex}",
            created=creation_time,
            allow_create_engine=False,
            allow_sampling=True,
            allow_logprobs=True,
            allow_search_indices=False,
            allow_view=True,
            allow_fine_tuning=False,
            organization="*",
            group=None,
            is_blocking=False,
        )

        def new_model(
            model_id: str,
            owned_by: str = "custom",
            context_window: int = 8192,
            max_output_tokens: int = 4096,
            supports_vision: bool = False,
            supports_audio: bool = False,
            supports_tools: bool = True,
            training_cutoff: str | None = None,
            pricing: ModelPricing | None = None,
        ) -> Model:
            """Create a new model instance with full metadata."""
            return Model(
                id=model_id,
                created=creation_time,
                owned_by=owned_by,
                permission=[base_permission],
                root=None,
                parent=None,
                context_window=context_window,
                max_output_tokens=max_output_tokens,
                supports_vision=supports_vision,
                supports_audio=supports_audio,
                supports_tools=supports_tools,
                training_cutoff=training_cutoff,
                pricing=pricing,
            )

        # Initialize with comprehensive metadata for all models
        self.models = {
            # GPT-2 (Legacy)
            "TinyLlama/TinyLlama-1.1B-Chat-v1.0": new_model(
                "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
                owned_by="openai",
                context_window=1024,
                max_output_tokens=1024,
                supports_tools=False,
                training_cutoff="2019-10",
                pricing=ModelPricing(
                    input_per_million=0.0,
                    output_per_million=0.0),
            ),
            # GPT-3.5 Family
            "meta-llama/Llama-3.1-8B-Instruct": new_model(
                "meta-llama/Llama-3.1-8B-Instruct",
                owned_by="openai",
                context_window=16385,
                max_output_tokens=4096,
                supports_tools=True,
                training_cutoff="2021-09",
                pricing=ModelPricing(
                    input_per_million=0.50,
                    output_per_million=1.50),
            ),
            # GPT-4 Family
            "openai/gpt-oss-120b": new_model(
                "openai/gpt-oss-120b",
                owned_by="openai",
                context_window=8192,
                max_output_tokens=8192,
                supports_tools=True,
                training_cutoff="2023-04",
                pricing=ModelPricing(
                    input_per_million=30.00,
                    output_per_million=60.00),
            ),
            "openai/gpt-oss-120b": new_model(
                "openai/gpt-oss-120b",
                owned_by="openai",
                context_window=128000,
                max_output_tokens=4096,
                supports_vision=True,
                supports_tools=True,
                training_cutoff="2023-12",
                pricing=ModelPricing(
                    input_per_million=10.00,
                    output_per_million=30.00),
            ),
            "openai/gpt-oss-120b": new_model(
                "openai/gpt-oss-120b",
                owned_by="openai",
                context_window=128000,
                max_output_tokens=16384,
                supports_vision=True,
                supports_audio=True,
                supports_tools=True,
                training_cutoff="2023-10",
                pricing=ModelPricing(
                    input_per_million=2.50,
                    output_per_million=10.00,
                    cached_input_per_million=1.25,
                ),
            ),
            "openai/gpt-oss-20b": new_model(
                "openai/gpt-oss-20b",
                owned_by="openai",
                context_window=128000,
                max_output_tokens=16384,
                supports_vision=True,
                supports_audio=True,
                supports_tools=True,
                training_cutoff="2023-10",
                pricing=ModelPricing(
                    input_per_million=0.15,
                    output_per_million=0.60,
                    cached_input_per_million=0.075,
                ),
            ),
            "openai/gpt-oss-120b-realtime": new_model(
                "openai/gpt-oss-120b-realtime",
                owned_by="openai",
                context_window=128000,
                max_output_tokens=4096,
                supports_vision=False,
                supports_audio=True,
                supports_tools=True,
                training_cutoff="2023-10",
                pricing=ModelPricing(
                    input_per_million=5.00,
                    output_per_million=20.00),
            ),
            # deepseek-ai/DeepSeek-R1 Reasoning Models
            "deepseek-ai/DeepSeek-R1": new_model(
                "deepseek-ai/DeepSeek-R1",
                owned_by="openai",
                context_window=200000,
                max_output_tokens=100000,
                supports_tools=False,
                training_cutoff="2023-10",
                pricing=ModelPricing(
                    input_per_million=15.00,
                    output_per_million=60.00),
            ),
            "deepseek-ai/DeepSeek-R1": new_model(
                "deepseek-ai/DeepSeek-R1",
                owned_by="openai",
                context_window=128000,
                max_output_tokens=32768,
                supports_tools=False,
                training_cutoff="2023-10",
                pricing=ModelPricing(
                    input_per_million=15.00,
                    output_per_million=60.00),
            ),
            "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B": new_model(
                "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B",
                owned_by="openai",
                context_window=128000,
                max_output_tokens=65536,
                supports_tools=False,
                training_cutoff="2023-10",
                pricing=ModelPricing(
                    input_per_million=3.00,
                    output_per_million=12.00),
            ),
            # gpt-oss Open Source Reasoning Models
            "gpt-oss-120b": new_model(
                "gpt-oss-120b",
                owned_by="openai",
                context_window=200000,
                max_output_tokens=100000,
                supports_tools=True,
                training_cutoff="2024-12",
                pricing=ModelPricing(
                    input_per_million=0.0,
                    output_per_million=0.0),
            ),
            "gpt-oss-20b": new_model(
                "gpt-oss-20b",
                owned_by="openai",
                context_window=200000,
                max_output_tokens=100000,
                supports_tools=True,
                training_cutoff="2024-12",
                pricing=ModelPricing(
                    input_per_million=0.0,
                    output_per_million=0.0),
            ),
            # Claude Models (Anthropic)
            "claude-3-opus": new_model(
                "claude-3-opus",
                owned_by="anthropic",
                context_window=200000,
                max_output_tokens=4096,
                supports_vision=True,
                supports_tools=True,
                training_cutoff="2023-08",
                pricing=ModelPricing(
                    input_per_million=15.00,
                    output_per_million=75.00),
            ),
            "claude-3-sonnet": new_model(
                "claude-3-sonnet",
                owned_by="anthropic",
                context_window=200000,
                max_output_tokens=4096,
                supports_vision=True,
                supports_tools=True,
                training_cutoff="2023-08",
                pricing=ModelPricing(
                    input_per_million=3.00,
                    output_per_million=15.00),
            ),
            "claude-3-haiku": new_model(
                "claude-3-haiku",
                owned_by="anthropic",
                context_window=200000,
                max_output_tokens=4096,
                supports_vision=True,
                supports_tools=True,
                training_cutoff="2023-08",
                pricing=ModelPricing(
                    input_per_million=0.25,
                    output_per_million=1.25),
            ),
            # Gemini Models (Google)
            "gemini-1.5-pro": new_model(
                "gemini-1.5-pro",
                owned_by="google",
                context_window=2000000,
                max_output_tokens=8192,
                supports_vision=True,
                supports_audio=True,
                supports_tools=True,
                training_cutoff="2024-01",
                pricing=ModelPricing(
                    input_per_million=1.25,
                    output_per_million=5.00),
            ),
            "gemini-1.5-flash": new_model(
                "gemini-1.5-flash",
                owned_by="google",
                context_window=1000000,
                max_output_tokens=8192,
                supports_vision=True,
                supports_audio=True,
                supports_tools=True,
                training_cutoff="2024-01",
                pricing=ModelPricing(
                    input_per_million=0.075,
                    output_per_million=0.30),
            ),
            # Mixtral Models (Mistral AI)
            "mixtral-8x7b": new_model(
                "mixtral-8x7b",
                owned_by="mistralai",
                context_window=32768,
                max_output_tokens=8192,
                supports_tools=True,
                training_cutoff="2023-12",
                pricing=ModelPricing(
                    input_per_million=0.50,
                    output_per_million=1.50),
            ),
            "mixtral-8x22b": new_model(
                "mixtral-8x22b",
                owned_by="mistralai",
                context_window=65536,
                max_output_tokens=16384,
                supports_tools=True,
                training_cutoff="2024-01",
                pricing=ModelPricing(
                    input_per_million=2.00,
                    output_per_million=6.00),
            ),
            "mistral-large": new_model(
                "mistral-large",
                owned_by="mistralai",
                context_window=128000,
                max_output_tokens=8192,
                supports_tools=True,
                training_cutoff="2024-02",
                pricing=ModelPricing(
                    input_per_million=4.00,
                    output_per_million=12.00),
            ),
            # DeepSeek Models
            "deepseek-v3": new_model(
                "deepseek-v3",
                owned_by="deepseek-ai",
                context_window=128000,
                max_output_tokens=8192,
                supports_tools=True,
                training_cutoff="2024-11",
                pricing=ModelPricing(
                    input_per_million=0.27,
                    output_per_million=1.10),
            ),
            "deepseek-ai/DeepSeek-R1-Distill-Llama-8B": new_model(
                "deepseek-ai/DeepSeek-R1-Distill-Llama-8B",
                owned_by="deepseek-ai",
                context_window=128000,
                max_output_tokens=8192,
                supports_tools=True,
                training_cutoff="2024-12",
                pricing=ModelPricing(
                    input_per_million=0.0,
                    output_per_million=0.0),
            ),
            # Llama Models (Meta)
            "llama-3.1-405b": new_model(
                "llama-3.1-405b",
                owned_by="meta",
                context_window=128000,
                max_output_tokens=4096,
                supports_tools=True,
                training_cutoff="2023-12",
                pricing=ModelPricing(
                    input_per_million=3.00,
                    output_per_million=3.00),
            ),
            "llama-3.1-70b": new_model(
                "llama-3.1-70b",
                owned_by="meta",
                context_window=128000,
                max_output_tokens=4096,
                supports_tools=True,
                training_cutoff="2023-12",
                pricing=ModelPricing(
                    input_per_million=0.88,
                    output_per_million=0.88),
            ),
            "llama-3.1-8b": new_model(
                "llama-3.1-8b",
                owned_by="meta",
                context_window=128000,
                max_output_tokens=4096,
                supports_tools=True,
                training_cutoff="2023-12",
                pricing=ModelPricing(
                    input_per_million=0.20,
                    output_per_million=0.20),
            ),
            # Embedding Models
            "sentence-transformers/all-mpnet-base-v2": new_model(
                "sentence-transformers/all-mpnet-base-v2",
                owned_by="openai",
                context_window=8191,
                max_output_tokens=0,
                supports_tools=False,
                training_cutoff="2021-09",
                pricing=ModelPricing(
                    input_per_million=0.10,
                    output_per_million=0.0),
            ),
            "nomic-ai/nomic-embed-text-v1.5": new_model(
                "nomic-ai/nomic-embed-text-v1.5",
                owned_by="openai",
                context_window=8191,
                max_output_tokens=0,
                supports_tools=False,
                training_cutoff="2022-12",
                pricing=ModelPricing(
                    input_per_million=0.02,
                    output_per_million=0.0),
            ),
            "BAAI/bge-m3": new_model(
                "BAAI/bge-m3",
                owned_by="openai",
                context_window=8191,
                max_output_tokens=0,
                supports_tools=False,
                training_cutoff="2022-12",
                pricing=ModelPricing(
                    input_per_million=0.13,
                    output_per_million=0.0),
            ),
            # Image Generation Models
            "stabilityai/stable-diffusion-2-1": new_model(
                "stabilityai/stable-diffusion-2-1",
                owned_by="openai",
                context_window=77,
                max_output_tokens=0,
                supports_tools=False,
                training_cutoff="2022-06",
                pricing=None,  # Priced per image
            ),
            "stabilityai/stable-diffusion-xl-base-1.0": new_model(
                "stabilityai/stable-diffusion-xl-base-1.0",
                owned_by="openai",
                context_window=77,
                max_output_tokens=0,
                supports_tools=False,
                training_cutoff="2023-11",
                pricing=None,  # Priced per image
            ),
            # TTS Models
            "tts-1": new_model(
                "tts-1",
                owned_by="openai",
                context_window=4096,
                max_output_tokens=0,
                supports_tools=False,
                training_cutoff=None,
                pricing=None,  # Priced per character
            ),
            "tts-1-hd": new_model(
                "tts-1-hd",
                owned_by="openai",
                context_window=4096,
                max_output_tokens=0,
                supports_tools=False,
                training_cutoff=None,
                pricing=None,  # Priced per character
            ),
        }

    def _init_simulated_files(self) -> None:
        """Initialize simulated file data."""
        creation_time = int(time.time()) - 5000
        self.files = [
            FileObject(
                id=f"file-{uuid.uuid4().hex}",
                bytes=random.randint(1000, 1000000),
                created_at=creation_time,
                filename=f"training_data_{i}.jsonl",
                purpose="fine-tune",
                status="processed",
                status_details=None,
            )
            for i in range(3)
        ]

        # Initialize vector store service with a file lookup adapter
        file_lookup = type(
            'FileLookup', (), {
                'get_file': lambda self, file_id: next(
                    (f for f in self.files if f.id == file_id), None)})()
        file_lookup.files = self.files  # Bind the files list

        self.vector_store_service = VectorStoreService(
            config=self.config,
            metrics_tracker=self.metrics_tracker,
            file_manager=file_lookup,
        )

    def _is_reasoning_model(self, model_id: str) -> bool:
        """Check if model supports reasoning content (gpt-oss and deepseek-ai/DeepSeek-R1 families)."""
        return (
            model_id.startswith("gpt-oss") or
            model_id.startswith("deepseek-ai/DeepSeek-R1") or
            "reasoning" in model_id.lower()
        )

    def _get_effective_max_tokens(self, request) -> int:
        """
        Get effective max tokens from request.

        Respects both max_tokens and max_completion_tokens parameters.
        max_completion_tokens takes precedence for deepseek-ai/DeepSeek-R1 models.

        Args:
            request: ChatCompletionRequest or similar

        Returns:
            Effective max tokens to generate (default: 100)
        """
        # For deepseek-ai/DeepSeek-R1 models, max_completion_tokens is
        # preferred
        if (
            hasattr(request, "max_completion_tokens") and
            request.max_completion_tokens is not None
        ):
            return request.max_completion_tokens

        # Otherwise use max_tokens
        if hasattr(request, "max_tokens") and request.max_tokens is not None:
            return request.max_tokens

        # Default
        return 100

    def _is_moe_model(self, model_id: str) -> bool:
        """Check if model uses Mixture of Experts architecture."""
        moe_patterns = [
            "mixtral",
            "gpt-oss",
            "deepseek-v3",
            "deepseek-v",
            "grok"]
        return any(pattern in model_id.lower() for pattern in moe_patterns)

    def _supports_predicted_outputs(self, model_id: str) -> bool:
        """Check if model supports Predicted Outputs / speculative decoding (EAGLE)."""
        return model_id.startswith("openai/gpt-oss-120b")

    def _set_seed_if_provided(self, seed: int | None) -> None:
        """Set random seed for deterministic generation."""
        if seed is not None:
            self._current_seed = seed
            self._random.seed(seed)
            # Also seed the global random for Faker and other utilities
            random.seed(seed)

    def _generate_fingerprint(self, seed: int | None) -> str:
        """Generate system fingerprint, deterministic when seed is provided."""
        if seed is not None:
            # Deterministic fingerprint based on seed
            import hashlib

            fingerprint_hash = hashlib.sha256(
                f"seed-{seed}".encode()).hexdigest()[:16]
            return f"fp_{fingerprint_hash}"
        else:
            # Random fingerprint
            return "fp_" + uuid.uuid4().hex[:16]

    def _ensure_model_exists(self, model_id: str) -> None:
        """Ensure a model exists, creating it if necessary.

        Supports:
        - Standard models
        - LoRA fine-tuned models (ft:base:org::id format)
        - MoE models (Mixtral, gpt-oss, DeepSeek)

        Args:
            model_id: The ID of the model to ensure exists.
        """
        if model_id in self.models:
            return

        # Create a default model instance
        creation_time = int(time.time()) - 10000
        base_permission = next(iter(self.models.values())).permission[0]

        # Determine ownership and lineage based on model ID
        if model_id.startswith("ft:"):
            # LoRA fine-tuned model: ft:base-model:org::unique-id
            parts = model_id.split(":")
            base_model = (parts[1] if len(parts) >
                          1 else "meta-llama/Llama-3.1-8B-Instruct")
            organization = parts[2] if len(parts) > 2 else "custom"
            owned_by = organization
            root = base_model
            parent = base_model
        elif "mixtral" in model_id.lower():
            owned_by = "mistralai"
            root = None
            parent = None
        elif "deepseek" in model_id.lower():
            owned_by = "deepseek-ai"
            root = None
            parent = None
        elif model_id.startswith("gpt-oss"):
            owned_by = "openai"
            root = None
            parent = None
        else:
            owned_by = "custom"
            root = None
            parent = None

        self.models[model_id] = Model(
            id=model_id,
            created=creation_time,
            owned_by=owned_by,
            permission=[base_permission],
            root=root,
            parent=parent,
        )

    # Safety and content moderation patterns

    # Harmful content patterns by category
    HARMFUL_PATTERNS = {
        "violence": [
            "how to kill",
            "how to murder",
            "how to hurt",
            "how to harm",
            "make a bomb",
            "build a weapon",
            "attack someone",
            "assassinate",
            "torture",
            "mutilate",
            "injure",
            "maim",
            "shoot",
            "stab",
        ],
        "illegal": [
            "how to hack",
            "how to steal",
            "how to rob",
            "how to break in",
            "make drugs",
            "sell drugs",
            "launder money",
            "forge documents",
            "evade taxes",
            "commit fraud",
            "bypass security",
            "counterfeit",
            "illegal download",
            "pirate software",
            "steal credit card",
        ],
        "self_harm": [
            "how to commit suicide",
            "ways to kill myself",
            "how to self-harm",
            "cutting myself",
            "overdose on",
            "end my life",
            "suicide methods",
            "painless death",
            "hang myself",
            "jump off",
        ],
        "sexual_minors": [
            "child abuse",
            "child exploitation",
            "csam",
            "underage sexual",
            "minor sexual",
            "child pornography",
            "sexualize children",
        ],
        "hate": [
            "hate speech against",
            "genocide",
            "ethnic cleansing",
            "racial slur",
            "discriminate against",
            "harass based on",
            "supremacist",
        ],
        "harassment": [
            "doxx",
            "doxing",
            "swat",
            "swatting",
            "harass",
            "cyberbully",
            "stalk",
            "threaten to kill",
            "death threat",
        ],
    }

    # Jailbreak and prompt injection patterns
    JAILBREAK_PATTERNS = [
        "ignore previous instructions",
        "disregard all prior",
        "forget your training",
        "you are now",
        "you are no longer",
        "ignore your guidelines",
        "ignore safety",
        "bypass restrictions",
        "act as if",
        "pretend you are",
        "simulate being",
        "roleplay as",
        "dan mode",
        "developer mode",
        "jailbreak mode",
        "unrestricted mode",
        "evil mode",
        "do anything now",
        "grandma exploit",
        "hypothetically",
        "in a fictional",
        "for educational purposes only",
        "as a creative writing",
        "in minecraft",
        "in a video game",
    ]

    # Default safety system message
    SAFETY_SYSTEM_MESSAGE = (
        "You are a helpful, harmless, and honest AI assistant. "
        "You will not provide information that could be used to harm people, "
        "break laws, or violate ethical guidelines. "
        "You will refuse requests for illegal activities, violence, self-harm, "
        "child exploitation, hate speech, or harassment.")

    def should_refuse_request(
            self, messages: list[Message]) -> tuple[bool, str | None]:
        """
        Check if the request should be refused due to harmful content.

        Args:
            messages: List of conversation messages

        Returns:
            Tuple of (should_refuse: bool, refusal_message: str | None)
        """
        if not self.config.enable_safety_features:
            return (False, None)

        # Extract all user message content
        user_texts = []
        for msg in messages:
            if msg.role == Role.USER and msg.content:
                # Use extract_text_content pattern from CLAUDE.md
                if isinstance(msg.content, str):
                    user_texts.append(msg.content)
                elif isinstance(msg.content, list):
                    texts = []
                    for part in msg.content:
                        if isinstance(part, dict) and part.get(
                                "type") == "text":
                            texts.append(part.get("text", ""))
                        elif hasattr(part, "type") and part.type == "text":
                            texts.append(part.text)
                    user_texts.append(" ".join(texts))

        # Check combined text
        full_text = " ".join(user_texts).lower()

        # Check for harmful content patterns
        for category, patterns in self.HARMFUL_PATTERNS.items():
            for pattern in patterns:
                if pattern.lower() in full_text:
                    refusal_msg = (
                        f"I cannot provide assistance with requests related to {
                            category.replace(
                                '_',
                                ' ')}. " "This type of content could cause harm and violates ethical guidelines. "
                        "If you're experiencing thoughts of self-harm, please contact a mental health "
                        "professional or crisis hotline immediately.")
                    logger.warning(
                        f"Safety refusal triggered: category={category}, pattern='{pattern}'")
                    return (True, refusal_msg)

        return (False, None)

    def is_jailbreak_attempt(self, messages: list[Message]) -> bool:
        """
        Detect potential jailbreak or prompt injection attempts.

        Args:
            messages: List of conversation messages

        Returns:
            True if jailbreak detected, False otherwise
        """
        if not self.config.enable_jailbreak_detection:
            return False

        # Extract user message content
        user_texts = []
        for msg in messages:
            if msg.role == Role.USER and msg.content:
                if isinstance(msg.content, str):
                    user_texts.append(msg.content)
                elif isinstance(msg.content, list):
                    texts = []
                    for part in msg.content:
                        if isinstance(part, dict) and part.get(
                                "type") == "text":
                            texts.append(part.get("text", ""))
                        elif hasattr(part, "type") and part.type == "text":
                            texts.append(part.text)
                    user_texts.append(" ".join(texts))

        full_text = " ".join(user_texts).lower()

        # Check for jailbreak patterns
        for pattern in self.JAILBREAK_PATTERNS:
            if pattern.lower() in full_text:
                logger.warning(
                    f"Jailbreak attempt detected: pattern='{pattern}'")
                return True

        return False

    def _prepend_safety_message(
            self, messages: list[Message]) -> list[Message]:
        """
        Prepend safety system message if no system message exists.

        Args:
            messages: Original message list

        Returns:
            Message list with safety message prepended if needed
        """
        if not self.config.prepend_safety_message:
            return messages

        # Check if system message already exists
        has_system = any(msg.role == Role.SYSTEM for msg in messages)

        if not has_system:
            safety_msg = Message(
                role=Role.SYSTEM,
                content=self.SAFETY_SYSTEM_MESSAGE)
            return [safety_msg] + messages

        return messages

    def _get_prompt_hash(self, messages: list[Message]) -> str:
        """Generate stable hash from messages for prompt caching.

        Args:
            messages: List of messages to hash

        Returns:
            SHA-256 hash of the serialized messages
        """
        # Serialize messages to a canonical JSON format for stable hashing
        message_data = []
        for msg in messages:
            # Serialize content (handle Pydantic models)
            content_data = msg.content
            if isinstance(content_data, list):
                # Handle list of content parts (multimodal)
                content_data = []
                for part in msg.content:
                    if hasattr(part, "model_dump"):
                        # Pydantic model - convert to dict
                        content_data.append(part.model_dump())
                    elif isinstance(part, dict):
                        # Already a dict
                        content_data.append(part)
                    else:
                        # Unknown type, convert to string
                        content_data.append(str(part))

            msg_dict = {
                "role": msg.role.value if hasattr(
                    msg.role, "value") else str(
                    msg.role), "content": content_data, }
            # Include optional fields if present
            if msg.name:
                msg_dict["name"] = msg.name
            if msg.tool_calls:
                msg_dict["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": tc.type,
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in msg.tool_calls
                ]
            if msg.tool_call_id:
                msg_dict["tool_call_id"] = msg.tool_call_id
            message_data.append(msg_dict)

        # Create stable JSON string (sorted keys)
        json_str = json.dumps(message_data, sort_keys=True)

        # Generate SHA-256 hash
        return hashlib.sha256(json_str.encode()).hexdigest()

    def _check_cache_hit(self, prompt_hash: str,
                         token_count: int) -> tuple[bool, int]:
        """Check if prompt is in cache and return cache hit info.

        Args:
            prompt_hash: Hash of the prompt messages
            token_count: Total token count of the prompt

        Returns:
            Tuple of (is_hit, cached_tokens)
            - is_hit: Whether this is a cache hit
            - cached_tokens: Number of tokens that were cached (rounded to 128 increments)
        """
        # Check if caching is enabled
        if not self.config.enable_prompt_caching:
            return False, 0

        # Check minimum token requirement
        if token_count < self.config.min_tokens_for_cache:
            return False, 0

        # Clean up expired entries
        current_time = time.time()
        expired_keys = [
            key
            for key, (_, timestamp) in self._prompt_cache.items()
            if current_time - timestamp > self.config.cache_ttl_seconds
        ]
        for key in expired_keys:
            del self._prompt_cache[key]

        # Check if hash exists in cache
        if prompt_hash in self._prompt_cache:
            cached_token_count, timestamp = self._prompt_cache[prompt_hash]

            # Check if entry is still valid (within TTL)
            if current_time - timestamp <= self.config.cache_ttl_seconds:
                # Calculate cached tokens in 128-token increments (OpenAI behavior)
                # This simulates how OpenAI rounds caching to block boundaries
                cached_tokens = (cached_token_count // 128) * 128
                return True, cached_tokens
            else:
                # Expired, remove from cache
                del self._prompt_cache[prompt_hash]
                return False, 0

        # Cache miss - add to cache for future requests
        self._prompt_cache[prompt_hash] = (token_count, current_time)
        return False, 0

    async def list_models(self) -> ModelListResponse:
        """List available models."""
        # Simulate some processing delay
        await asyncio.sleep(random.uniform(0.05, 0.2))

        return ModelListResponse(data=list(self.models.values()))

    async def get_model(self, model_id: str) -> Model:
        """Get model details."""
        # Simulate some processing delay
        await asyncio.sleep(random.uniform(0.05, 0.2))

        # Auto-create model if it doesn't exist
        self._ensure_model_exists(model_id)

        if model_id not in self.models:
            raise ValueError(f"Model '{model_id}' not found")

        return self.models[model_id]

    def get_model_capability(self, model_id: str, capability: str) -> bool:
        """
        Check if a model supports a specific capability.

        Args:
            model_id: The model identifier
            capability: The capability to check ("vision", "audio", "tools")

        Returns:
            True if the model supports the capability, False otherwise

        Raises:
            ValueError: If the capability name is invalid
        """
        self._ensure_model_exists(model_id)
        model = self.models[model_id]

        capability_map = {
            "vision": model.supports_vision,
            "audio": model.supports_audio,
            "tools": model.supports_tools,
        }

        if capability not in capability_map:
            raise ValueError(
                f"Invalid capability '{capability}'. "
                f"Valid capabilities: {', '.join(capability_map.keys())}"
            )

        return capability_map[capability]

    def get_model_pricing(self, model_id: str) -> ModelPricing | None:
        """
        Get pricing information for a model.

        Args:
            model_id: The model identifier

        Returns:
            ModelPricing object if available, None if model has no pricing info
        """
        self._ensure_model_exists(model_id)
        return self.models[model_id].pricing

    def validate_model_feature(
        self, model_id: str, feature: str, feature_name: str | None = None
    ) -> None:
        """
        Validate that a model supports a specific feature and raise error if not.

        Args:
            model_id: The model identifier
            feature: The feature to validate ("vision", "audio", "tools")
            feature_name: Human-readable feature name for error message (optional)

        Raises:
            ValueError: If the model does not support the feature
        """
        self._ensure_model_exists(model_id)

        if not self.get_model_capability(model_id, feature):
            feature_display = feature_name or feature
            raise ValueError(
                f"Model '{model_id}' does not support {feature_display}. "
                f"Please use a model with {feature} support."
            )

    async def get_model_capabilities(
            self, model_id: str) -> ModelCapabilitiesResponse:
        """
        Get comprehensive capability information for a model.

        Args:
            model_id: The model identifier

        Returns:
            ModelCapabilitiesResponse with all capability information
        """
        # Simulate some processing delay
        await asyncio.sleep(random.uniform(0.05, 0.2))

        self._ensure_model_exists(model_id)
        model = self.models[model_id]

        return ModelCapabilitiesResponse(
            id=model.id,
            context_window=model.context_window,
            max_output_tokens=model.max_output_tokens,
            supports_vision=model.supports_vision,
            supports_audio=model.supports_audio,
            supports_tools=model.supports_tools,
            training_cutoff=model.training_cutoff,
            pricing=model.pricing,
        )

    async def create_chat_completion(
        self, request: ChatCompletionRequest
    ) -> ChatCompletionResponse:
        """Create a chat completion."""
        # Set seed for deterministic generation
        self._set_seed_if_provided(request.seed)

        # Ensure model exists
        self._ensure_model_exists(request.model)

        # Start Dynamo request tracking
        request_id = f"req-{uuid.uuid4().hex[:12]}"

        # Handle structured outputs validation
        is_structured_output = False
        json_schema_name = None
        json_schema_obj = None

        if request.response_format:
            if (
                hasattr(request.response_format, "type") and
                request.response_format.type == "json_schema"
            ):
                is_structured_output = True
                json_schema_obj = request.response_format.json_schema.schema_
                json_schema_name = request.response_format.json_schema.name

                # Validate strict mode requirements
                if request.response_format.json_schema.strict:
                    try:
                        validate_strict_schema(json_schema_obj)
                    except SchemaValidationError as e:
                        pass

                        raise ValueError(
                            f"Invalid JSON schema for strict mode: {str(e)}"
                        )

                    # Enforce parallel_tool_calls=false for strict mode
                    if request.parallel_tool_calls is not False:
                        pass

                        raise ValueError(
                            "When using strict mode with structured outputs, parallel_tool_calls must be false"
                        )

        # Calculate token counts - handle both string and array content
        def extract_text_content(content):
            """Extract text from content (string or content parts array)."""
            if isinstance(content, str):
                return content
            elif isinstance(content, list):
                # Extract text from content parts
                texts = []
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "text":
                        texts.append(part.get("text", ""))
                    elif hasattr(part, "type") and part.type == "text":
                        texts.append(part.text)
                return " ".join(texts)
            return ""

        # Process audio inputs if present
        input_audio_tokens, audio_transcript = self._process_audio_input(
            request.messages
        )

        # Process vision inputs if present (calculate image tokens)
        input_image_tokens = 0
        for msg in request.messages:
            if msg.content:
                input_image_tokens += calculate_message_image_tokens(
                    msg.content, request.model
                )

        # Process video inputs if present (calculate video tokens - NVIDIA
        # Cosmos extension)
        input_video_tokens = 0
        for msg in request.messages:
            if msg.content:
                input_video_tokens += calculate_message_video_tokens(
                    msg.content, request.model
                )

        # Extract prompt text for token counting and KV cache routing
        prompt_text = " ".join(extract_text_content(msg.content)
                               for msg in request.messages if msg.content)

        # Add audio transcriptions to prompt text
        if audio_transcript:
            prompt_text = f"{prompt_text} {audio_transcript}".strip()

        # Calculate text tokens
        text_tokens = calculate_token_count(prompt_text)

        # Total prompt tokens = text + image + video + audio tokens
        prompt_tokens = (
            text_tokens +
            input_image_tokens +
            input_video_tokens +
            input_audio_tokens)

        # Add tokens from tool definitions if present
        tool_tokens = 0
        if request.tools:
            # Estimate tokens for tool definitions (rough approximation)
            tool_json = json.dumps([tool.model_dump()
                                   for tool in request.tools])
            tool_tokens = calculate_token_count(tool_json)
            prompt_tokens += tool_tokens

        # Validate context length if enabled
        if self.config.enable_context_validation:
            is_valid, error_message = validate_context_length(
                model=request.model,
                prompt_tokens=prompt_tokens,
                max_tokens=request.max_tokens,
                image_tokens=input_image_tokens,
                audio_tokens=input_audio_tokens,
                video_tokens=input_video_tokens,
            )
            if not is_valid:
                error_dict = create_context_length_error(error_message)
                raise ContextLengthExceededError(error_message, error_dict)

        # Start Dynamo metrics tracking for this request
        dynamo_request = self.dynamo_metrics.start_request(
            request_id=request_id,
            model=request.model,
            endpoint="/v1/chat/completions",
            input_tokens=prompt_tokens,
        )

        # Record prefill phase start
        self.dynamo_metrics.record_prefill_start(request_id)

        # Prompt caching check (hash-based, separate from KV cache)
        prompt_hash = self._get_prompt_hash(request.messages)
        is_prompt_cache_hit, prompt_cached_tokens = self._check_cache_hit(
            prompt_hash, prompt_tokens
        )

        # KV Cache routing (AI-Dynamo simulation)
        token_ids = tokenize_for_cache(prompt_text)
        worker_id, matched_tokens, matched_blocks = self.kv_cache_router.route_request(
            tokens=token_ids,
            estimated_output_tokens=self._get_effective_max_tokens(request),
        )

        # Record cache lookup
        self.kv_cache_metrics.record_cache_lookup(
            endpoint="/v1/chat/completions",
            total_tokens=len(token_ids),
            matched_tokens=matched_tokens,
        )

        # Mark request started on worker
        self.kv_cache_router.start_request(worker_id)

        # Combine both cache types: KV cache (from blocks) + Prompt cache (from hash)
        # Both can contribute to cached tokens independently
        total_cached_tokens = matched_tokens + prompt_cached_tokens

        # Get effective max tokens (respects max_completion_tokens)
        effective_max_tokens = self._get_effective_max_tokens(request)

        # Generate reasoning content for deepseek-ai/DeepSeek-R1 models
        reasoning_content = None
        reasoning_tokens = 0
        if self._is_reasoning_model(request.model):
            # Reserve tokens for reasoning (typically 30-50 tokens)
            reasoning_budget = min(
                50, effective_max_tokens // 2
            )  # Max 50 or half of budget
            reasoning_content = await self._generate_simulated_reasoning(
                request.messages,
                max_tokens=reasoning_budget,
            )
            reasoning_tokens = calculate_token_count(reasoning_content)

        # Calculate remaining budget for regular completion
        remaining_budget = max(10, effective_max_tokens - reasoning_tokens)

        # Check if we should generate tool calls
        should_call_tools = False
        tool_calls = None
        if request.tools and not is_structured_output:
            # Import tool calling engine
            from fakeai.tool_calling import ToolCallGenerator, ToolDecisionEngine

            engine = ToolDecisionEngine()
            should_call_tools = engine.should_call_tools(
                request.messages, request.tools, request.tool_choice
            )

            if should_call_tools:
                # Generate tool calls instead of regular completion
                generator = ToolCallGenerator()
                tool_calls = generator.generate_tool_calls(
                    tools_to_call=request.tools,
                    messages=request.messages,
                    parallel=(
                        request.parallel_tool_calls
                        if request.parallel_tool_calls is not None
                        else True
                    ),
                )
                completion_text = None  # No content when calling tools
                completion_tokens = 0
            else:
                # Generate regular response
                completion_text = await self._generate_simulated_completion(
                    request.messages,
                    max_tokens=remaining_budget,
                    temperature=request.temperature or 1.0,
                )
                completion_tokens = calculate_token_count(completion_text)
        elif is_structured_output:
            # Generate data matching the JSON schema
            generated_data = generate_from_schema(json_schema_obj)
            completion_text = format_as_json_string(generated_data)
            completion_tokens = calculate_token_count(completion_text)
        else:
            # Regular completion
            completion_text = await self._generate_simulated_completion(
                request.messages,
                max_tokens=remaining_budget,
                temperature=request.temperature or 1.0,
            )
            completion_tokens = calculate_token_count(completion_text)

        # Handle predicted outputs (EAGLE/speculative decoding)
        accepted_pred_tokens = 0
        rejected_pred_tokens = 0
        if request.prediction and self._supports_predicted_outputs(
                request.model):
            accepted_pred_tokens, rejected_pred_tokens = (
                self._simulate_speculative_decoding(
                    request.prediction.content, completion_text
                )
            )

        # Generate audio output if requested
        audio_output = None
        output_audio_tokens = 0
        if request.audio and (
                not request.modalities or "audio" in request.modalities):
            audio_config = {
                "voice": request.audio.voice,
                "format": request.audio.format,
            }
            audio_output, output_audio_tokens = self._generate_audio_output(
                completion_text, audio_config
            )

        # Track token generation (including reasoning, prediction, and audio
        # tokens)
        total_completion_tokens = (
            completion_tokens +
            reasoning_tokens +
            rejected_pred_tokens +
            output_audio_tokens
        )

        # Determine finish reason
        max_tokens_requested = self._get_effective_max_tokens(request)
        finish_reason = (
            "length" if completion_tokens >= max_tokens_requested else "stop"
        )

        # Create completion tokens details
        completion_tokens_details = None
        if (
            reasoning_tokens > 0 or
            accepted_pred_tokens > 0 or
            rejected_pred_tokens > 0 or
            output_audio_tokens > 0
        ):
            completion_tokens_details = CompletionTokensDetails(
                reasoning_tokens=reasoning_tokens,
                audio_tokens=output_audio_tokens,
                accepted_prediction_tokens=accepted_pred_tokens,
                rejected_prediction_tokens=rejected_pred_tokens,
            )

        # Complete request on worker (update KV cache)
        self.kv_cache_router.complete_request(
            worker_id, token_ids, total_completion_tokens
        )

        # Record first token for Dynamo TTFT tracking
        self.dynamo_metrics.record_first_token(request_id)

        # Complete Dynamo request tracking
        self.dynamo_metrics.complete_request(
            request_id=request_id,
            output_tokens=total_completion_tokens,
            cached_tokens=total_cached_tokens,
            kv_cache_hit=(matched_tokens > 0 or prompt_cached_tokens > 0),
            worker_id=worker_id,
            success=True,
            finish_reason=finish_reason,
        )

        # Generate logprobs if requested
        logprobs_result = None
        if request.logprobs:
            # Tokenize completion text
            completion_tokens_list = re.findall(
                r"\w+|[^\w\s]", completion_text)
            logprobs_result = create_chat_logprobs(
                text=completion_text,
                tokens=completion_tokens_list,
                top_logprobs=request.top_logprobs or 0,
                temperature=request.temperature or 1.0,
            )

        # Create response with KV cache statistics
        response = ChatCompletionResponse(
            id=f"chatcmpl-{uuid.uuid4().hex}",
            created=int(time.time()),
            model=request.model,
            choices=[
                ChatCompletionChoice(
                    index=i,
                    message=Message(
                        role=Role.ASSISTANT,
                        content=completion_text,
                        reasoning_content=reasoning_content,
                        audio=audio_output,
                        tool_calls=tool_calls if should_call_tools else None,
                    ),
                    finish_reason="tool_calls" if should_call_tools else finish_reason,
                    logprobs=logprobs_result,
                )
                for i in range(request.n or 1)
            ],
            usage=Usage(
                prompt_tokens=prompt_tokens,
                completion_tokens=total_completion_tokens,
                total_tokens=prompt_tokens + total_completion_tokens,
                prompt_tokens_details=PromptTokensDetails(
                    cached_tokens=total_cached_tokens,
                    audio_tokens=input_audio_tokens,
                ),
                completion_tokens_details=completion_tokens_details,
            ),
            system_fingerprint=self._generate_fingerprint(request.seed),
        )

        # Track usage for billing
        self.usage_tracker.track_usage(
            endpoint="/v1/chat/completions",
            model=request.model,
            input_tokens=prompt_tokens,
            output_tokens=total_completion_tokens,
            cached_tokens=total_cached_tokens,
            project_id=request.metadata.get("project_id") if request.metadata else None,
            user_id=request.user,
        )

        # Simulate GPU workload based on request size
        # Larger responses simulate higher GPU utilization
        compute_intensity = min(0.9, total_completion_tokens / 500.0)
        memory_intensity = min(0.9, prompt_tokens / 1000.0)
        self.dcgm_simulator.set_global_workload(
            compute_intensity, memory_intensity)

        return response

    async def create_chat_completion_stream(
        self, request: ChatCompletionRequest
    ) -> AsyncGenerator[ChatCompletionChunk, None]:
        """Create a streaming chat completion."""
        # Generate unique request ID for tracking
        request_id = f"req-{uuid.uuid4().hex[:12]}"

        # Track stream start time for latency calculations
        stream_start_time = time.time()

        # Initialize token tracking arrays
        token_timestamps = []
        token_count = 0

        # Ensure model exists
        self._ensure_model_exists(request.model)

        # Calculate prompt caching info (needed for final usage chunk)
        def extract_text_content(content):
            """Extract text from content (string or content parts array)."""
            if isinstance(content, str):
                return content
            elif isinstance(content, list):
                texts = []
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "text":
                        texts.append(part.get("text", ""))
                    elif hasattr(part, "type") and part.type == "text":
                        texts.append(part.text)
                return " ".join(texts)
            return ""

        prompt_text = " ".join(extract_text_content(msg.content)
                               for msg in request.messages if msg.content)
        prompt_tokens = calculate_token_count(prompt_text)

        # Process audio inputs if present
        input_audio_tokens, audio_transcript = self._process_audio_input(
            request.messages
        )
        if audio_transcript:
            prompt_text = f"{prompt_text} {audio_transcript}".strip()
            # Recalculate prompt tokens with audio transcript
            prompt_tokens = calculate_token_count(prompt_text)

        # Process vision inputs if present (calculate image tokens)
        input_image_tokens = 0
        for msg in request.messages:
            if msg.content:
                input_image_tokens += calculate_message_image_tokens(
                    msg.content, request.model
                )

        # Process video inputs if present (calculate video tokens)
        input_video_tokens = 0
        for msg in request.messages:
            if msg.content:
                input_video_tokens += calculate_message_video_tokens(
                    msg.content, request.model
                )

        # Total prompt tokens = text + image + video + audio tokens
        total_prompt_tokens = (
            prompt_tokens +
            input_image_tokens +
            input_video_tokens +
            input_audio_tokens)

        # Add tokens from tool definitions if present
        if request.tools:
            tool_json = json.dumps([tool.model_dump()
                                   for tool in request.tools])
            tool_tokens = calculate_token_count(tool_json)
            total_prompt_tokens += tool_tokens

        # Validate context length if enabled
        if self.config.enable_context_validation:
            is_valid, error_message = validate_context_length(
                model=request.model,
                prompt_tokens=total_prompt_tokens,
                max_tokens=request.max_tokens,
                image_tokens=input_image_tokens,
                audio_tokens=input_audio_tokens,
                video_tokens=input_video_tokens,
            )
            if not is_valid:
                error_dict = create_context_length_error(error_message)
                raise ContextLengthExceededError(error_message, error_dict)

        # Prompt caching check
        prompt_hash = self._get_prompt_hash(request.messages)
        is_prompt_cache_hit, prompt_cached_tokens = self._check_cache_hit(
            prompt_hash, prompt_tokens
        )

        # KV Cache routing (for streaming we still do this but mainly for
        # metrics)
        token_ids = tokenize_for_cache(prompt_text)
        worker_id, kv_matched_tokens, _ = self.kv_cache_router.route_request(
            tokens=token_ids,
            estimated_output_tokens=self._get_effective_max_tokens(request),
        )

        # Record cache lookup
        self.kv_cache_metrics.record_cache_lookup(
            endpoint="/v1/chat/completions",
            total_tokens=len(token_ids),
            matched_tokens=kv_matched_tokens,
        )

        # Mark request started on worker
        self.kv_cache_router.start_request(worker_id)

        # Calculate cache hit ratio for TTFT speedup
        cache_hit_ratio = (
            kv_matched_tokens / len(token_ids) if len(token_ids) > 0 else 0.0
        )

        # Combine both cache types
        total_cached_tokens = kv_matched_tokens + prompt_cached_tokens

        # Get effective max tokens
        effective_max_tokens = self._get_effective_max_tokens(request)

        # Generate reasoning content for deepseek-ai/DeepSeek-R1 models
        reasoning_content = None
        reasoning_tokens = 0
        if self._is_reasoning_model(request.model):
            reasoning_budget = min(50, effective_max_tokens // 2)
            reasoning_content = await self._generate_simulated_reasoning(
                request.messages,
                max_tokens=reasoning_budget,
            )
            reasoning_tokens = calculate_token_count(reasoning_content)

        # Calculate remaining budget for regular completion
        remaining_budget = max(10, effective_max_tokens - reasoning_tokens)

        # Check if we should generate tool calls
        should_call_tools = False
        tool_calls_to_stream = None
        if request.tools:
            from fakeai.tool_calling import ToolCallGenerator, ToolDecisionEngine

            engine = ToolDecisionEngine()
            should_call_tools = engine.should_call_tools(
                request.messages, request.tools, request.tool_choice
            )

            if should_call_tools:
                # Generate tool calls for streaming
                generator = ToolCallGenerator()
                tool_calls_to_stream = generator.generate_tool_calls(
                    tools_to_call=request.tools,
                    messages=request.messages,
                    parallel=(
                        request.parallel_tool_calls
                        if request.parallel_tool_calls is not None
                        else True
                    ),
                )

        # Generate simulated response (unless calling tools)
        if should_call_tools:
            completion_text = None
            content_tokens = []
        else:
            completion_text = await self._generate_simulated_completion(
                request.messages,
                max_tokens=remaining_budget,
                temperature=request.temperature or 1.0,
                stream=True,  # Make sure to set stream=True
            )
            # Split the completion text into token-equivalent chunks
            content_tokens = tokenize_text(completion_text)
            # DEBUG: Log token count and newline presence
            newline_tokens = [t for t in content_tokens if '\n' in t]
            logger.info(
                f"Content has {
                    len(content_tokens)} tokens, {
                    len(newline_tokens)} are newlines")
            if newline_tokens:
                logger.info(f"Sample newline tokens: {newline_tokens[:5]}")

        # Split reasoning into token-equivalent chunks
        reasoning_tokens_list = (
            tokenize_text(reasoning_content) if reasoning_content else []
        )
        stream_id = f"chatcmpl-{uuid.uuid4().hex}"
        system_fingerprint = "fp_" + uuid.uuid4().hex[:16]

        # First chunk with role
        first_chunk = ChatCompletionChunk(
            id=stream_id,
            created=int(time.time()),
            model=request.model,
            choices=[
                ChatCompletionChunkChoice(
                    index=i,
                    delta=Delta(role=Role.ASSISTANT),
                    finish_reason=None,
                )
                for i in range(request.n or 1)
            ],
            system_fingerprint=system_fingerprint,
        )
        yield first_chunk

        # Wait a bit before starting to stream - this will be our "time to first token"
        # Use configured TTFT with variance, adjusted for cache hits
        base_ttft = self.config.ttft_ms / 1000.0  # Convert ms to seconds

        # Cache hits reduce TTFT significantly
        # 50% cache → 30% faster (0.7x), 100% cache → 80% faster (0.2x)
        if cache_hit_ratio > 0:
            ttft_reduction = cache_hit_ratio * 0.8
            actual_ttft = base_ttft * (1.0 - ttft_reduction)
        else:
            actual_ttft = base_ttft

        # Apply variance
        ttft_variance = self.config.ttft_variance_percent / 100.0
        first_token_delay = random.uniform(
            actual_ttft * (1.0 - ttft_variance), actual_ttft * (1.0 + ttft_variance)
        )

        # Record speedup metrics
        self.kv_cache_metrics.record_speedup(
            endpoint="/v1/chat/completions",
            baseline_ttft=base_ttft,
            actual_ttft=actual_ttft,
            cache_hit_ratio=cache_hit_ratio,
        )

        await asyncio.sleep(first_token_delay)

        # Record first token received (TTFT measured)
        self.dynamo_metrics.record_first_token(request_id)

        # Calculate ITL (inter-token latency) parameters for use throughout
        # streaming
        itl_base = self.config.itl_ms / 1000.0  # Convert ms to seconds
        itl_variance = self.config.itl_variance_percent / 100.0
        itl_min = itl_base * (1.0 - itl_variance)
        itl_max = itl_base * (1.0 + itl_variance)

        # Stream reasoning content first (for deepseek-ai/DeepSeek-R1 models)
        if reasoning_tokens_list:
            for i, token in enumerate(reasoning_tokens_list):
                # Record the timestamp for this token
                current_time = time.time()
                relative_time = round(
                    (current_time - stream_start_time) * 1000
                )  # milliseconds
                token_timestamps.append(relative_time)

                # Use token as-is - tokenizer handles spacing
                chunk_text = token

                # Stream as reasoning_content
                chunk = ChatCompletionChunk(
                    id=stream_id,
                    created=int(time.time()),
                    model=request.model,
                    choices=[
                        ChatCompletionChunkChoice(
                            index=j,
                            delta=Delta(
                                reasoning_content=chunk_text,
                                token_timing=[relative_time],
                            ),
                            finish_reason=None,
                        )
                        for j in range(request.n or 1)
                    ],
                    system_fingerprint=system_fingerprint,
                )
                yield chunk

                # Simulate variable typing speed (inter-token latency)
                token_delay = random.uniform(itl_min, itl_max)
                await asyncio.sleep(token_delay)

        # Stream tool calls if requested
        if should_call_tools and tool_calls_to_stream:
            from fakeai.models import FunctionDelta, ToolCallDelta

            for tool_call_idx, tool_call in enumerate(tool_calls_to_stream):
                # Stream tool call in chunks: id, type, function name, then
                # arguments

                # Chunk 1: Tool call id and type
                chunk = ChatCompletionChunk(
                    id=stream_id,
                    created=int(time.time()),
                    model=request.model,
                    choices=[
                        ChatCompletionChunkChoice(
                            index=j,
                            delta=Delta(
                                tool_calls=[
                                    ToolCallDelta(
                                        index=tool_call_idx,
                                        id=tool_call.id,
                                        type="function",
                                    )
                                ]
                            ),
                            finish_reason=None,
                        )
                        for j in range(request.n or 1)
                    ],
                    system_fingerprint=system_fingerprint,
                )
                yield chunk
                await asyncio.sleep(random.uniform(itl_min, itl_max))

                # Chunk 2: Function name
                chunk = ChatCompletionChunk(
                    id=stream_id,
                    created=int(time.time()),
                    model=request.model,
                    choices=[
                        ChatCompletionChunkChoice(
                            index=j,
                            delta=Delta(
                                tool_calls=[
                                    ToolCallDelta(
                                        index=tool_call_idx,
                                        function=FunctionDelta(
                                            name=tool_call.function.name
                                        ),
                                    )
                                ]
                            ),
                            finish_reason=None,
                        )
                        for j in range(request.n or 1)
                    ],
                    system_fingerprint=system_fingerprint,
                )
                yield chunk
                await asyncio.sleep(random.uniform(itl_min, itl_max))

                # Chunk 3+: Function arguments (stream in chunks)
                args_str = tool_call.function.arguments
                args_chunks = [
                    args_str[i: i + 20] for i in range(0, len(args_str), 20)
                ]

                for args_chunk in args_chunks:
                    chunk = ChatCompletionChunk(
                        id=stream_id,
                        created=int(time.time()),
                        model=request.model,
                        choices=[
                            ChatCompletionChunkChoice(
                                index=j,
                                delta=Delta(
                                    tool_calls=[
                                        ToolCallDelta(
                                            index=tool_call_idx,
                                            function=FunctionDelta(
                                                arguments=args_chunk
                                            ),
                                        )
                                    ]
                                ),
                                finish_reason=None,
                            )
                            for j in range(request.n or 1)
                        ],
                        system_fingerprint=system_fingerprint,
                    )
                    yield chunk
                    await asyncio.sleep(random.uniform(itl_min, itl_max))

        # Stream the regular content token by token (unless tool calls)
        elif not should_call_tools:
            for i, token in enumerate(content_tokens):
                # Record the timestamp for this token
                current_time = time.time()
                relative_time = round(
                    (current_time - stream_start_time) * 1000
                )  # milliseconds
                token_timestamps.append(relative_time)

                # For tokens that are alphanumeric (words), add space before if not first
                # For punctuation and special chars (including newlines), send as-is
                # Use token as-is - tokenizer handles spacing
                chunk_text = token

                # Add timing information to the Delta object
                chunk = ChatCompletionChunk(
                    id=stream_id,
                    created=int(time.time()),
                    model=request.model,
                    choices=[
                        ChatCompletionChunkChoice(
                            index=j,
                            delta=Delta(
                                content=chunk_text,
                                token_timing=[
                                    relative_time
                                ],  # Include timing for this token
                            ),
                            finish_reason=None,
                        )
                        for j in range(request.n or 1)
                    ],
                    system_fingerprint=system_fingerprint,
                )
                yield chunk

                # Simulate variable typing speed - this gives us inter-token latency
                # Use configured ITL with variance
                itl_base = self.config.itl_ms / 1000.0  # Convert ms to seconds
                itl_variance = self.config.itl_variance_percent / 100.0
                itl_min = itl_base * (1.0 - itl_variance)
                itl_max = itl_base * (1.0 + itl_variance)
                token_delay = random.uniform(itl_min, itl_max)
                await asyncio.sleep(token_delay)

        # Include usage in final chunk if requested
        if request.stream_options and request.stream_options.include_usage:
            # Calculate usage statistics
            def extract_text_content(content):
                if isinstance(content, str):
                    return content
                elif isinstance(content, list):
                    texts = []
                    for part in content:
                        if isinstance(part, dict) and part.get(
                                "type") == "text":
                            texts.append(part.get("text", ""))
                        elif hasattr(part, "type") and part.type == "text":
                            texts.append(part.text)
                    return " ".join(texts)
                return ""

            prompt_tokens = calculate_token_count(
                " ".join(
                    extract_text_content(msg.content)
                    for msg in request.messages
                    if msg.content
                )
            )

            completion_tokens = len(content_tokens)
            reasoning_tokens_count = len(
                reasoning_tokens) if reasoning_tokens else 0
            total_completion_tokens = completion_tokens + reasoning_tokens_count

            # Build completion tokens details if needed
            completion_tokens_details = None
            if reasoning_tokens_count > 0:
                completion_tokens_details = CompletionTokensDetails(
                    reasoning_tokens=reasoning_tokens_count,
                    audio_tokens=0,
                    accepted_prediction_tokens=0,
                    rejected_prediction_tokens=0,
                )

            # Final chunk with usage
            final_chunk = ChatCompletionChunk(
                id=stream_id,
                created=int(time.time()),
                model=request.model,
                choices=[
                    ChatCompletionChunkChoice(
                        index=i,
                        delta=Delta(),
                        finish_reason="stop",
                    )
                    for i in range(request.n or 1)
                ],
                system_fingerprint=system_fingerprint,
                usage=Usage(
                    prompt_tokens=prompt_tokens,
                    completion_tokens=total_completion_tokens,
                    total_tokens=prompt_tokens + total_completion_tokens,
                    prompt_tokens_details=PromptTokensDetails(
                        cached_tokens=total_cached_tokens,
                        audio_tokens=0,
                    ),
                    completion_tokens_details=completion_tokens_details,
                ),
            )
            yield final_chunk

            # Track token generation and complete KV cache request
            self.kv_cache_router.complete_request(
                worker_id, token_ids, total_completion_tokens
            )
        else:
            # Final chunk without usage (default behavior)
            final_chunk = ChatCompletionChunk(
                id=stream_id,
                created=int(time.time()),
                model=request.model,
                choices=[
                    ChatCompletionChunkChoice(
                        index=i,
                        delta=Delta(),
                        finish_reason="stop",
                    )
                    for i in range(request.n or 1)
                ],
                system_fingerprint=system_fingerprint,
            )
            yield final_chunk

            # Track token generation and complete KV cache request
            completion_tokens = len(content_tokens)
            reasoning_tokens_count = (
                len(reasoning_tokens_list) if reasoning_tokens_list else 0
            )
            total_completion_tokens = completion_tokens + reasoning_tokens_count
            self.kv_cache_router.complete_request(
                worker_id, token_ids, total_completion_tokens
            )

            # Complete Dynamo metrics tracking for streaming request
            request_end_time = time.time()
            total_latency_ms = (request_end_time - stream_start_time) * 1000
            ttft_ms = first_token_delay * 1000 if first_token_delay else 0  # Convert back to ms
            self.dynamo_metrics.complete_request(
                request_id=request_id,
                output_tokens=total_completion_tokens,
                success=True,
            )

    async def create_completion(
            self, request: CompletionRequest) -> CompletionResponse:
        """Create a text completion."""
        # Ensure model exists
        self._ensure_model_exists(request.model)

        # Handle the prompt which can be a string, list of strings, or token
        # IDs
        prompt_text = self._process_prompt(request.prompt)
        prompt_tokens = calculate_token_count(prompt_text)

        # Generate simulated completion
        completion_text = await self._generate_simulated_completion(
            [Message(role=Role.USER, content=prompt_text)],
            max_tokens=request.max_tokens or 16,
            temperature=request.temperature or 1.0,
        )
        completion_tokens = calculate_token_count(completion_text)

        # Handle echo parameter
        if request.echo:
            completion_text = prompt_text + completion_text

        # Determine finish reason
        max_tokens_requested = request.max_tokens or 16
        finish_reason = (
            "length" if completion_tokens >= max_tokens_requested else "stop"
        )

        # Create response
        response = CompletionResponse(
            id=f"cmpl-{uuid.uuid4().hex}",
            created=int(time.time()),
            model=request.model,
            choices=[
                CompletionChoice(
                    text=completion_text,
                    index=i,
                    logprobs=(
                        self._generate_logprobs(
                            completion_text,
                            request.logprobs,
                            request.temperature or 1.0,
                        )
                        if request.logprobs
                        else None
                    ),
                    finish_reason=finish_reason,
                )
                for i in range(request.n or 1)
            ],
            usage=Usage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
            ),
        )

        # Metrics tracked via events
        total_tokens = prompt_tokens + completion_tokens

    async def create_completion_stream(
        self, request: CompletionRequest
    ) -> AsyncGenerator[CompletionChunk, None]:
        """Create a streaming text completion."""
        # Ensure model exists
        self._ensure_model_exists(request.model)

        # Track stream start time for latency calculations
        stream_start_time = time.time()
        token_timestamps = []

        # Handle the prompt which can be a string, list of strings, or token
        # IDs
        prompt_text = self._process_prompt(request.prompt)

        # Generate simulated completion
        completion_text = await self._generate_simulated_completion(
            [Message(role=Role.USER, content=prompt_text)],
            max_tokens=request.max_tokens or 16,
            temperature=request.temperature or 1.0,
            stream=True,
        )

        # Handle echo parameter
        if request.echo:
            text_to_stream = prompt_text + completion_text
        else:
            text_to_stream = completion_text

        # Split the completion text into token-equivalent chunks
        tokens = tokenize_text(text_to_stream)
        stream_id = f"cmpl-{uuid.uuid4().hex}"

        # Wait a bit before starting to stream - this will be our "time to first token"
        # Use configured TTFT with variance
        ttft_base = self.config.ttft_ms / 1000.0  # Convert ms to seconds
        ttft_variance = self.config.ttft_variance_percent / 100.0
        ttft_min = ttft_base * (1.0 - ttft_variance)
        ttft_max = ttft_base * (1.0 + ttft_variance)
        first_token_delay = random.uniform(ttft_min, ttft_max)
        await asyncio.sleep(first_token_delay)

        # Stream the content token by token
        token_count = 0
        for i, token in enumerate(tokens):
            # Record the timestamp for this token
            current_time = time.time()
            relative_time = round(
                (current_time - stream_start_time) * 1000
            )  # milliseconds
            token_timestamps.append(relative_time)

            # Use token as-is - tokenizer handles spacing
            chunk_text = token

            token_count += 1

            chunk = CompletionChunk(
                id=stream_id,
                created=int(time.time()),
                model=request.model,
                choices=[
                    CompletionChoice(
                        text=chunk_text,
                        index=j,
                        logprobs=(
                            self._generate_logprobs(
                                chunk_text, request.logprobs, request.temperature or 1.0
                            )
                            if request.logprobs
                            else None
                        ),
                        finish_reason=None,
                        # Add token timing information
                        token_timing=[relative_time],
                    )
                    for j in range(request.n or 1)
                ],
            )
            yield chunk

            # Simulate variable typing speed (inter-token latency)
            # Use configured ITL with variance
            itl_base = self.config.itl_ms / 1000.0
            itl_variance = self.config.itl_variance_percent / 100.0
            itl_min = itl_base * (1.0 - itl_variance)
            itl_max = itl_base * (1.0 + itl_variance)
            await asyncio.sleep(random.uniform(itl_min, itl_max))

        # Determine finish reason
        max_tokens_requested = request.max_tokens or 16
        finish_reason = "length" if token_count >= max_tokens_requested else "stop"

        # Final chunk with finish reason
        final_chunk = CompletionChunk(
            id=stream_id,
            created=int(time.time()),
            model=request.model,
            choices=[
                CompletionChoice(
                    text="",
                    index=i,
                    logprobs=None,
                    finish_reason=finish_reason,
                )
                for i in range(request.n or 1)
            ],
        )
        yield final_chunk

    async def create_embedding(
            self,
            request: EmbeddingRequest) -> EmbeddingResponse:
        """Create embeddings."""
        # Ensure model exists
        self._ensure_model_exists(request.model)

        # Delegate to embedding service
        response = await self.embedding_service.create_embedding(request)

        # Track usage for billing
        self.usage_tracker.track_usage(
            endpoint="/v1/embeddings",
            model=request.model,
            input_tokens=response.usage.prompt_tokens,
            output_tokens=0,
            user_id=request.user,
        )

        return response

    async def generate_images(
        self, request: ImageGenerationRequest
    ) -> ImageGenerationResponse:
        """
        Generate images.

        Delegates to ImageGenerationService for image generation.

        Args:
            request: Image generation request with prompt, model, size, etc.

        Returns:
            ImageGenerationResponse with generated images
        """
        # Delegate to image generation service
        response = await self.image_generation_service.generate_images(request)

        # Track usage for billing (images use request count, not tokens)
        model = request.model or "stabilityai/stable-diffusion-2-1"
        self.usage_tracker.track_usage(
            endpoint="/v1/images/generations",
            model=model,
            input_tokens=0,
            output_tokens=0,
            num_requests=request.n or 1,
            user_id=request.user,
        )

        return response

    async def create_speech(self, request: SpeechRequest) -> bytes:
        """
        Create text-to-speech audio.

        Delegates to AudioService for audio generation.

        Args:
            request: SpeechRequest containing model, input text, voice, format, and speed

        Returns:
            Bytes containing the audio file in the requested format
        """
        # Ensure model exists (auto-create TTS models if needed)
        self._ensure_model_exists(request.model)

        # Delegate to audio service
        return await self.audio_service.create_speech(request)

    async def generate_videos(
        self, request: VideoGenerationRequest
    ) -> VideoGenerationResponse:
        """
        Generate videos from text prompts.

        This is a simulated implementation that creates placeholder video URLs.
        In a real implementation, this would call actual video generation models.

        Args:
            request: VideoGenerationRequest containing prompt, model, duration, size, etc.

        Returns:
            VideoGenerationResponse with generated video URLs
        """
        import time

        from fakeai.models import GeneratedVideo, VideoGenerationResponse

        # Simulate processing delay based on video duration
        await asyncio.sleep(random.uniform(1.0, 2.0))

        # Create simulated video URL
        video_id = f"video-{int(time.time())}-{random.randint(1000, 9999)}"
        format_str = request.format.value if hasattr(
            request.format, 'value') else request.format
        video_url = f"http://localhost:8765/videos/{video_id}.{format_str}"

        video = GeneratedVideo(
            url=video_url,
            b64_json=None,
        )

        # Track usage
        model = request.model or "runway-gen3"
        self.usage_tracker.track_usage(
            endpoint="/v1/videos/generations",
            model=model,
            input_tokens=0,
            output_tokens=0,
            num_requests=1,
            user_id=request.user,
        )

        return VideoGenerationResponse(
            created=int(time.time()),
            data=[video],
        )

    async def list_files(self) -> FileListResponse:
        """List files."""
        # Simulate some processing delay
        await asyncio.sleep(random.uniform(0.05, 0.2))

        return FileListResponse(data=self.files)

    async def upload_file(self) -> FileObject:
        """Upload a file (simulated implementation)."""
        # Simulate processing delay
        await asyncio.sleep(random.uniform(0.5, 1.5))

        # Create a new simulated file
        new_file = FileObject(
            id=f"file-{uuid.uuid4().hex}",
            bytes=random.randint(1000, 1000000),
            created_at=int(time.time()),
            filename=f"uploaded_file_{len(self.files) + 1}.jsonl",
            purpose="fine-tune",
            status="uploaded",
            status_details=None,
        )

        # Add to our list
        self.files.append(new_file)

        return new_file

    async def get_file(self, file_id: str) -> FileObject:
        """Get file details."""
        # Simulate some processing delay
        await asyncio.sleep(random.uniform(0.05, 0.2))

        # Find the file
        for file in self.files:
            if file.id == file_id:
                return file

        raise ValueError(f"File with ID '{file_id}' not found")

    async def delete_file(self, file_id: str) -> dict[str, Any]:
        """Delete a file."""
        # Simulate some processing delay
        await asyncio.sleep(random.uniform(0.05, 0.2))

        # Find and remove the file
        for i, file in enumerate(self.files):
            if file.id == file_id:
                del self.files[i]
                return {"id": file_id, "object": "file", "deleted": True}

        raise ValueError(f"File with ID '{file_id}' not found")

    async def create_text_generation(
        self, request: TextGenerationRequest
    ) -> TextGenerationResponse:
        """Create a text generation (Azure API)."""
        # Ensure model exists
        self._ensure_model_exists(request.model)

        # Calculate token counts
        prompt_tokens = calculate_token_count(request.input)

        # Generate simulated response
        completion_text = await self._generate_simulated_completion(
            [Message(role=Role.USER, content=request.input)],
            max_tokens=request.max_output_tokens,
            temperature=request.temperature or 1.0,
        )
        completion_tokens = calculate_token_count(completion_text)

        # Create response
        response = TextGenerationResponse(
            id=f"txtgen-{uuid.uuid4().hex}",
            created=int(time.time()),
            output=completion_text,
            model=request.model,
            usage=Usage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
            ),
        )

        return response

    def _process_prompt(
        self, prompt: str | list[str] | list[int] | list[list[int]]
    ) -> str:
        """Process the prompt input into a string."""
        if isinstance(prompt, str):
            return prompt
        elif isinstance(prompt, list):
            if all(isinstance(item, str) for item in prompt):
                return "\n".join(prompt)
            elif all(isinstance(item, int) for item in prompt):
                # For simplicity, we'll use a placeholder for token IDs
                return f"[Token IDs input with {len(prompt)} tokens]"
            elif all(
                isinstance(item, list) and all(isinstance(i, int) for i in item)
                for item in prompt
            ):
                # For simplicity, we'll use a placeholder for batch token IDs
                return f"[Batch token IDs input with {len(prompt)} sequences]"

        raise ValueError("Unsupported prompt format")

    def _process_embedding_input(
        self, input_data: str | list[str] | list[int] | list[list[int]]
    ) -> list[str]:
        """Process the embedding input into a list of strings."""
        if isinstance(input_data, str):
            return [input_data]
        elif isinstance(input_data, list):
            if all(isinstance(item, str) for item in input_data):
                return input_data
            elif all(isinstance(item, int) for item in input_data):
                # For simplicity, we'll use a placeholder for token IDs
                return [f"[Token IDs input with {len(input_data)} tokens]"]
            elif all(
                isinstance(item, list) and all(isinstance(i, int) for i in item)
                for item in input_data
            ):
                # Convert each token ID list to a placeholder string
                return [
                    f"[Token IDs input with {
                        len(ids)} tokens]" for ids in input_data]

        raise ValueError("Unsupported input format for embeddings")

    def _generate_logprobs(
        self, text: str, logprob_count: int | None, temperature: float = 1.0
    ) -> LogProbs:
        """Generate realistic log probabilities using enhanced module."""
        if not logprob_count:
            return None

        # Tokenize the text
        tokens = re.findall(r"\w+|[^\w\s]", text)

        # Use the enhanced logprobs generation
        return create_completion_logprobs(
            text=text,
            tokens=tokens,
            logprobs=logprob_count,
            temperature=temperature)

    async def _generate_simulated_reasoning(
        self,
        messages: list[Message],
        max_tokens: int = 50,
    ) -> str:
        """Generate simulated reasoning content for gpt-oss and deepseek-ai/DeepSeek-R1 models."""

        # Helper to extract text from message content
        def get_text_content(content):
            if isinstance(content, str):
                return content
            elif isinstance(content, list):
                texts = []
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "text":
                        texts.append(part.get("text", ""))
                    elif hasattr(part, "type") and part.type == "text":
                        texts.append(part.text)
                return " ".join(texts)
            return str(content) if content else ""

        # Extract the last user message
        user_message = next(
            (
                get_text_content(msg.content)
                for msg in reversed(messages)
                if msg.role == Role.USER and msg.content
            ),
            "Tell me about AI.",
        )

        # Generate reasoning steps based on the user message
        reasoning_templates = [
            f"Let me think about this step by step. The user asked about '{user_message[:50]}{'...' if len(user_message) > 50 else ''}'. "
            f"First, I need to understand the key concepts involved. "
            f"Second, I should consider different perspectives. "
            f"Third, I'll formulate a comprehensive response.",
            f"Analyzing the question: '{user_message[:50]}{'...' if len(user_message) > 50 else ''}'. "
            f"Breaking this down: 1) Identify the main topic, 2) Consider relevant context, "
            f"3) Evaluate potential approaches, 4) Select the most appropriate response strategy.",
            f"Reasoning through this query: The question about '{user_message[:50]}{'...' if len(user_message) > 50 else ''}' "
            f"requires careful consideration. I'll examine the core elements, weigh different angles, "
            f"and construct a well-reasoned answer.",
        ]

        # Select a random template
        reasoning = random.choice(reasoning_templates)

        # Trim to max_tokens if needed
        reasoning_token_count = calculate_token_count(reasoning)
        if reasoning_token_count > max_tokens:
            # Trim by words to fit within max_tokens
            words = reasoning.split()
            trimmed_words = []
            for word in words:
                test_text = " ".join(trimmed_words + [word])
                if calculate_token_count(test_text) <= max_tokens:
                    trimmed_words.append(word)
                else:
                    break
            reasoning = " ".join(trimmed_words)

        # Simulate some delay for reasoning
        delay = 0.2 if not self.config.random_delay else random.uniform(
            0.1, 0.3)
        await asyncio.sleep(delay)

        return reasoning

    def _simulate_speculative_decoding(
        self, prediction_content: str, actual_output: str
    ) -> tuple[int, int]:
        """
        Simulate accepted and rejected prediction tokens for EAGLE/speculative decoding.

        Uses string similarity as a proxy for token-level acceptance.
        Typical acceptance rates: 60-80% for good predictions.

        Args:
            prediction_content: The predicted content provided in request
            actual_output: The actual generated output

        Returns:
            Tuple of (accepted_tokens, rejected_tokens)
        """
        if not prediction_content or not actual_output:
            return (0, 0)

        # Calculate token counts
        predicted_tokens = calculate_token_count(prediction_content)

        # Calculate similarity (proxy for token-level acceptance)
        from difflib import SequenceMatcher

        similarity = SequenceMatcher(
            None, prediction_content, actual_output).ratio()

        # Simulate acceptance rate (60-80% typical, correlates with similarity)
        acceptance_rate = min(0.8, similarity * 0.9)

        # Calculate accepted and rejected tokens
        accepted = int(predicted_tokens * acceptance_rate)
        rejected = predicted_tokens - accepted

        return (accepted, rejected)

    async def _generate_simulated_completion(
        self,
        messages: list[Message],
        max_tokens: int,
        temperature: float,
        stream: bool = False,
    ) -> str:
        """Generate a simulated completion based on the input messages."""

        # Helper to extract text from message content
        def get_text_content(content):
            if isinstance(content, str):
                return content
            elif isinstance(content, list):
                texts = []
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "text":
                        texts.append(part.get("text", ""))
                    elif hasattr(part, "type") and part.type == "text":
                        texts.append(part.text)
                return " ".join(texts)
            return str(content) if content else ""

        # Extract the last user message, or use a default if none exists
        user_message = next(
            (
                get_text_content(msg.content)
                for msg in reversed(messages)
                if msg.role == Role.USER and msg.content
            ),
            "Tell me about AI.",
        )

        # Generate a response with the executor to simulate computational work
        system_prompt = next(
            (
                get_text_content(msg.content)
                for msg in messages
                if msg.role == Role.SYSTEM and msg.content
            ),
            None,
        )

        # Calculate a realistic delay based on the number of tokens and
        # temperature
        token_factor = 0.01 * max_tokens
        temp_factor = 0.5 if temperature < 0.5 else 1.0 if temperature < 1.0 else 1.5
        base_delay = token_factor * temp_factor

        # Add some randomness to the delay
        delay = base_delay + random.uniform(0.2, 1.0)

        # If streaming, return quickly as we'll stream the tokens later
        if stream:
            delay = delay * 0.2

        # For debugging
        logger.info(
            f"Generating completion with delay {
                delay:.2f}s, stream={stream}")

        # Generate the response with a delay
        response = await self.executor.run_with_delay(
            self.generator.generate_response,
            user_message,
            max_tokens,
            delay=delay,
        )

        return response

    def _process_audio_input(self, messages: list[Message]) -> tuple[int, str]:
        """
        Process audio inputs from messages.

        Extracts audio from message content, transcribes it, and calculates tokens.

        Args:
            messages: List of Message objects

        Returns:
            Tuple of (audio_tokens, transcribed_text)
        """
        # Calculate audio input tokens
        audio_tokens = calculate_audio_input_tokens(messages)

        # Extract and transcribe audio to text
        audio_text = extract_text_from_audio(messages)

        return audio_tokens, audio_text

    def _generate_audio_output(
        self, text: str, audio_config: dict[str, str] | None
    ) -> tuple[AudioOutput | None, int]:
        """
        Generate audio output for assistant response.

        Args:
            text: Text to convert to audio
            audio_config: Audio configuration (voice, format)

        Returns:
            Tuple of (AudioOutput object or None, audio_tokens)
        """
        if not audio_config:
            return None, 0

        voice = audio_config.get("voice", "alloy")
        audio_format = audio_config.get("format", "mp3")

        # Generate audio output
        audio_data = generate_audio_output(text, voice, audio_format)

        # Create AudioOutput object
        audio_output = AudioOutput(
            id=audio_data["id"],
            data=audio_data["data"],
            transcript=audio_data["transcript"],
            expires_at=audio_data["expires_at"],
        )

        # Calculate audio tokens for output
        from fakeai.audio import estimate_audio_tokens
        from fakeai.utils import estimate_audio_duration

        duration = estimate_audio_duration(text, speed=1.0)
        audio_tokens = estimate_audio_tokens(duration)

        return audio_output, audio_tokens

    async def create_response(self, request) -> dict[str, Any]:
        """Create an OpenAI Responses API response."""
        # Ensure model exists
        self._ensure_model_exists(request.model)

        # Convert input to messages if it's a string
        if isinstance(request.input, str):
            messages = [Message(role=Role.USER, content=request.input)]
        else:
            messages = request.input

        # Add instructions as system message if provided
        if request.instructions:
            messages.insert(
                0,
                Message(
                    role=Role.SYSTEM,
                    content=request.instructions))

        # Generate completion
        completion_text = await self._generate_simulated_completion(
            messages,
            max_tokens=request.max_output_tokens or 1000,
            temperature=request.temperature or 1.0,
        )

        # Calculate tokens
        input_tokens = sum(
            calculate_token_count(
                msg.content if isinstance(msg.content, str) else str(msg.content)
            )
            for msg in messages
            if msg.content
        )
        output_tokens = calculate_token_count(completion_text)

        # Create response in Responses API format
        response_id = f"resp-{uuid.uuid4().hex}"

        response = {
            "id": response_id,
            "object": "response",
            "created_at": int(time.time()),
            "model": request.model,
            "status": "completed",
            "error": None,
            "incomplete_details": None,
            "instructions": request.instructions,
            "max_output_tokens": request.max_output_tokens,
            "metadata": request.metadata or {},
            "previous_response_id": request.previous_response_id,
            "temperature": request.temperature,
            "top_p": request.top_p,
            "parallel_tool_calls": request.parallel_tool_calls,
            "tool_choice": request.tool_choice,
            "tools": request.tools or [],
            "output": [
                {
                    "type": "message",
                    "id": f"msg-{uuid.uuid4().hex}",
                    "role": "assistant",
                    "status": "completed",
                    "content": [{"type": "text", "text": completion_text}],
                }
            ],
            "usage": {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens,
            },
        }

        # Metrics tracked via events
        total_tokens = input_tokens + output_tokens

    async def create_ranking(self, request) -> dict[str, Any]:
        """Create a NVIDIA NIM ranking response."""
        # Simulate ranking by scoring passages based on query-passage
        # similarity
        rankings = []

        for idx, passage in enumerate(request.passages):
            # Simple simulated scoring based on text overlap
            query_words = set(request.query.text.lower().split())
            passage_words = set(passage.text.lower().split())

            # Calculate overlap score
            overlap = len(query_words.intersection(passage_words))
            total_query_words = len(query_words)

            if total_query_words > 0:
                # Base score on overlap percentage
                base_score = overlap / total_query_words
            else:
                base_score = 0.0

            # Convert to logit-like score (add randomness for realism)
            logit = (base_score * 10.0) - 5.0 + random.uniform(-1.0, 1.0)

            rankings.append({"index": idx, "logit": logit})

        # Sort by logit descending (most relevant first)
        rankings.sort(key=lambda x: x["logit"], reverse=True)

        # Metrics tracked via events
        query_tokens = calculate_token_count(request.query.text)
        passage_tokens = sum(calculate_token_count(p.text)
                             for p in request.passages)
        total_tokens = query_tokens + passage_tokens
        await asyncio.sleep(random.uniform(0.1, 0.3))

        return {"rankings": rankings}

    async def create_moderation(self, request):
        """Create content moderation response (delegates to ModerationService)."""
        return await self.moderation_service.create_moderation(request)

    # Solido RAG API method

    async def create_solido_rag(self, request) -> dict[str, Any]:
        """
        Create a Solido RAG (Retrieval-Augmented Generation) response.

        Simulates document retrieval based on filters and generates
        an answer using the inference model with augmented context.

        Args:
            request: SolidoRagRequest object

        Returns:
            SolidoRagResponse with generated content
        """
        from fakeai.models import RagDocument, SolidoRagResponse, Usage

        # Normalize query to list
        queries = request.query if isinstance(
            request.query, list) else [request.query]
        combined_query = " ".join(queries)

        # Simulate document retrieval with filters
        filters = request.filters or {}
        top_k = request.top_k or 5

        # Generate simulated documents based on filters
        retrieved_docs = []
        for i in range(top_k):
            # Create document IDs and content related to query
            doc_id = f"doc-{uuid.uuid4().hex[:8]}"

            # Generate realistic content based on filters
            if filters.get("family") == "Solido" and filters.get(
                    "tool") == "SDE":
                # Generate Solido Design Environment documentation snippets
                doc_content = self._generate_solido_doc_content(
                    combined_query, i)
                source = f"Solido_SDE_User_Guide_2024.2_p{100 + i * 15}"
            else:
                # Generic documentation
                doc_content = fake.paragraph(nb_sentences=3)
                source = f"document_{i}.txt"

            # Calculate relevance score (decreasing order)
            score = max(0.5, 0.95 - (i * 0.1))

            retrieved_docs.append(
                RagDocument(
                    id=doc_id,
                    content=doc_content,
                    score=score,
                    metadata=filters,
                    source=source,
                )
            )

        # Generate augmented response using retrieved context
        context_text = "\n\n".join([doc.content for doc in retrieved_docs[:3]])

        # Create prompt with context
        augmented_prompt = (
            f"Context:\n{context_text}\n\nQuestion: {combined_query}\n\nAnswer:")

        # Calculate tokens
        prompt_tokens = calculate_token_count(augmented_prompt)

        # Generate completion
        completion_text = await self._generate_simulated_completion(
            messages=[],  # Context already in augmented_prompt
            max_tokens=200,
            temperature=0.7,
        )

        completion_tokens = calculate_token_count(completion_text)

        # Build response
        response = SolidoRagResponse(
            content=completion_text,
            retrieved_docs=retrieved_docs,
            usage=Usage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
            ),
        )

        return response.model_dump()

    def _generate_solido_doc_content(self, query: str, index: int) -> str:
        """Generate Solido-specific documentation content."""
        query_lower = query.lower()

        # Context-aware content based on query keywords
        if "pvtmc" in query_lower or "corner" in query_lower:
            templates = [
                "PVTMC Verifier provides fast, accurate full coverage verification of worst case corners. It analyzes process, voltage, and temperature variations to identify critical operating conditions.",
                "Corner analysis in Solido DE identifies worst-case operating conditions across PVT variations. The PVTMC Verifier tool automates this process with statistical methods.",
                "Process-Voltage-Temperature Monte Carlo (PVTMC) verification ensures your design meets specifications across all operating corners by analyzing statistical distributions.",
            ]
        elif "sweep" in query_lower or "variable" in query_lower:
            templates = [
                "Sweep configuration allows you to sweep design variables with a simple setup. Select variables from the dropdown and configure sweep ranges manually or using automatic stepping.",
                "Variable grouping in sweeps creates specific combinations rather than running all permutations. Linked variables must have the same number of points in each variable.",
                "Sweep ranges can be specified as comma-separated values (-40, 25, 125) or using start:step:end notation (-40:10:125) for automatic population.",
            ]
        elif "simulation" in query_lower or "test" in query_lower:
            templates = [
                "Solido Design Environment supports multiple simulation types including transient analysis, AC analysis, and DC operating point calculations across process corners.",
                "Test configuration allows selection of specific tests, corner groups, and cluster settings for distributed simulation runs.",
                "Simulation results can be viewed across distributions with cross-selection support, enabling efficient debugging and design iteration.",
            ]
        else:
            templates = [
                f"Solido Design Environment (SDE) is a comprehensive variation-aware design platform for custom IC design workflows. {fake.sentence()}",
                f"The Solido platform leverages AI-enabled technologies for library characterization, IP validation, and worst-case corner verification. {fake.sentence()}",
                f"Solido tools integrate seamlessly with industry-standard EDA flows, providing automated analysis and optimization capabilities. {fake.sentence()}",
            ]

        return templates[index % len(templates)]

    async def _retrieve_rag_context(
        self, query: str, filters: dict[str, Any], top_k: int
    ) -> tuple[list, str]:
        """
        Retrieve documents for RAG context.

        Args:
            query: Search query
            filters: Metadata filters
            top_k: Number of documents to retrieve

        Returns:
            Tuple of (retrieved_documents, context_text)
        """
        from fakeai.models import RagDocument

        # Generate retrieved documents
        retrieved_docs = []
        for i in range(top_k):
            doc_id = f"doc-{uuid.uuid4().hex[:8]}"

            # Generate content based on filters
            if filters.get("family") == "Solido":
                doc_content = self._generate_solido_doc_content(query, i)
                source = f"Solido_SDE_User_Guide_p{100 + i * 15}"
            else:
                doc_content = fake.paragraph(nb_sentences=2)
                source = f"document_{i}.txt"

            score = max(0.5, 0.95 - (i * 0.1))

            retrieved_docs.append(
                RagDocument(
                    id=doc_id,
                    content=doc_content,
                    score=score,
                    metadata=filters,
                    source=source,
                )
            )

        # Create context string
        context_text = "Retrieved Context:\n" + "\n\n".join(
            [f"[{i + 1}] {doc.content}" for i, doc in enumerate(retrieved_docs)]
        )

        return retrieved_docs, context_text

    # Batch API methods

    async def create_batch(self, request: CreateBatchRequest) -> Batch:
        """Create a new batch processing job (delegated to BatchService)."""
        return await self.batch_service.create_batch(request)

    async def retrieve_batch(self, batch_id: str) -> Batch:
        """Retrieve a batch by ID (delegated to BatchService)."""
        return await self.batch_service.retrieve_batch(batch_id)

    async def cancel_batch(self, batch_id: str) -> Batch:
        """Cancel a batch (delegated to BatchService)."""
        return await self.batch_service.cancel_batch(batch_id)

    async def list_batches(
        self,
        limit: int = 20,
        after: str | None = None,
    ) -> BatchListResponse:
        """List all batches (delegated to BatchService)."""
        return await self.batch_service.list_batches(limit=limit, after=after)

    # Organization and Project Management Methods

    async def list_organization_users(
        self,
        limit: int = 20,
        after: str | None = None,
    ) -> OrganizationUserListResponse:
        """List all users in the organization."""
        # Get all users
        all_users = list(self.organization_users.values())

        # Sort by added_at descending
        all_users.sort(key=lambda u: u.get("added_at", 0), reverse=True)

        # Apply pagination
        if after:
            try:
                after_idx = next(
                    i for i, u in enumerate(all_users) if u["id"] == after)
                all_users = all_users[after_idx + 1:]
            except StopIteration:
                pass

        # Limit results
        users = all_users[:limit]
        has_more = len(all_users) > limit

        # Convert to OrganizationUser objects
        user_objects = [OrganizationUser(**u) for u in users]

        first_id = user_objects[0].id if user_objects else None
        last_id = user_objects[-1].id if user_objects else None

        return OrganizationUserListResponse(
            data=user_objects,
            first_id=first_id,
            last_id=last_id,
            has_more=has_more,
        )

    async def get_organization_user(self, user_id: str) -> OrganizationUser:
        """Get a specific organization user."""
        user = self.organization_users.get(user_id)
        if not user:
            raise ValueError(f"User not found: {user_id}")
        return OrganizationUser(**user)

    async def create_organization_user(
        self, request: CreateOrganizationUserRequest
    ) -> OrganizationUser:
        """Add a user to the organization."""
        user_id = f"user-{uuid.uuid4().hex[:24]}"
        current_time = int(time.time())

        user_data = {
            "id": user_id,
            "name": fake.name(),
            "email": request.email,
            "role": request.role,
            "added_at": current_time,
        }

        self.organization_users[user_id] = user_data
        logger.info(
            f"Created organization user {user_id} with role {
                request.role}")

        return OrganizationUser(**user_data)

    async def modify_organization_user(
        self, user_id: str, request: ModifyOrganizationUserRequest
    ) -> OrganizationUser:
        """Modify an organization user's role."""
        user = self.organization_users.get(user_id)
        if not user:
            raise ValueError(f"User not found: {user_id}")

        user["role"] = request.role
        logger.info(
            f"Modified organization user {user_id} to role {
                request.role}")

        return OrganizationUser(**user)

    async def delete_organization_user(self, user_id: str) -> dict[str, Any]:
        """Remove a user from the organization."""
        user = self.organization_users.get(user_id)
        if not user:
            raise ValueError(f"User not found: {user_id}")

        del self.organization_users[user_id]

        # Also remove from all projects
        for project_id, project_user_dict in self.project_users.items():
            if user_id in project_user_dict:
                del project_user_dict[user_id]

        logger.info(f"Deleted organization user {user_id}")

        return {
            "object": "organization.user.deleted",
            "id": user_id,
            "deleted": True,
        }

    async def list_organization_invites(
        self,
        limit: int = 20,
        after: str | None = None,
    ) -> OrganizationInviteListResponse:
        """List all organization invites."""
        # Get all invites
        all_invites = list(self.organization_invites.values())

        # Sort by invited_at descending
        all_invites.sort(key=lambda i: i.get("invited_at", 0), reverse=True)

        # Apply pagination
        if after:
            try:
                after_idx = next(i for i, inv in enumerate(
                    all_invites) if inv["id"] == after)
                all_invites = all_invites[after_idx + 1:]
            except StopIteration:
                pass

        # Limit results
        invites = all_invites[:limit]
        has_more = len(all_invites) > limit

        # Convert to OrganizationInvite objects
        invite_objects = [OrganizationInvite(**inv) for inv in invites]

        first_id = invite_objects[0].id if invite_objects else None
        last_id = invite_objects[-1].id if invite_objects else None

        return OrganizationInviteListResponse(
            data=invite_objects,
            first_id=first_id,
            last_id=last_id,
            has_more=has_more,
        )

    async def create_organization_invite(
        self, request: CreateOrganizationInviteRequest
    ) -> OrganizationInvite:
        """Create an organization invite."""
        invite_id = f"invite-{uuid.uuid4().hex[:24]}"
        current_time = int(time.time())
        expires_at = current_time + (7 * 24 * 60 * 60)  # 7 days

        invite_data = {
            "id": invite_id,
            "email": request.email,
            "role": request.role,
            "status": "pending",
            "invited_at": current_time,
            "expires_at": expires_at,
            "accepted_at": None,
        }

        self.organization_invites[invite_id] = invite_data
        logger.info(
            f"Created organization invite {invite_id} for {
                request.email}")

        return OrganizationInvite(**invite_data)

    async def get_organization_invite(
            self, invite_id: str) -> OrganizationInvite:
        """Get a specific organization invite."""
        invite = self.organization_invites.get(invite_id)
        if not invite:
            raise ValueError(f"Invite not found: {invite_id}")
        return OrganizationInvite(**invite)

    async def delete_organization_invite(
        self, invite_id: str
    ) -> DeleteOrganizationInviteResponse:
        """Delete an organization invite."""
        invite = self.organization_invites.get(invite_id)
        if not invite:
            raise ValueError(f"Invite not found: {invite_id}")

        del self.organization_invites[invite_id]
        logger.info(f"Deleted organization invite {invite_id}")

        return DeleteOrganizationInviteResponse(
            id=invite_id,
            deleted=True,
        )

    async def list_organization_projects(
        self,
        limit: int = 20,
        after: str | None = None,
        include_archived: bool = False,
    ) -> OrganizationProjectListResponse:
        """List all projects in the organization."""
        # Get all projects
        all_projects = list(self.projects.values())

        # Filter archived projects if needed
        if not include_archived:
            all_projects = [
                p for p in all_projects if p.get("status") == "active"]

        # Sort by created_at descending
        all_projects.sort(key=lambda p: p.get("created_at", 0), reverse=True)

        # Apply pagination
        if after:
            try:
                after_idx = next(
                    i for i, p in enumerate(all_projects) if p["id"] == after
                )
                all_projects = all_projects[after_idx + 1:]
            except StopIteration:
                pass

        # Limit results
        projects = all_projects[:limit]
        has_more = len(all_projects) > limit

        # Convert to OrganizationProject objects
        project_objects = [OrganizationProject(**p) for p in projects]

        first_id = project_objects[0].id if project_objects else None
        last_id = project_objects[-1].id if project_objects else None

        return OrganizationProjectListResponse(
            data=project_objects,
            first_id=first_id,
            last_id=last_id,
            has_more=has_more,
        )

    async def create_organization_project(
        self, request: CreateOrganizationProjectRequest
    ) -> OrganizationProject:
        """Create a new project in the organization."""
        project_id = f"proj_{uuid.uuid4().hex[:24]}"
        current_time = int(time.time())

        project_data = {
            "id": project_id,
            "name": request.name,
            "created_at": current_time,
            "archived_at": None,
            "status": "active",
        }

        self.projects[project_id] = project_data
        self.project_users[project_id] = {}
        self.service_accounts[project_id] = {}
        logger.info(f"Created project {project_id} with name '{request.name}'")

        return OrganizationProject(**project_data)

    async def get_organization_project(
            self, project_id: str) -> OrganizationProject:
        """Get a specific project."""
        project = self.projects.get(project_id)
        if not project:
            raise ValueError(f"Project not found: {project_id}")
        return OrganizationProject(**project)

    async def modify_organization_project(
        self, project_id: str, request: ModifyOrganizationProjectRequest
    ) -> OrganizationProject:
        """Modify a project."""
        project = self.projects.get(project_id)
        if not project:
            raise ValueError(f"Project not found: {project_id}")

        project["name"] = request.name
        logger.info(f"Modified project {project_id} name to '{request.name}'")

        return OrganizationProject(**project)

    async def archive_organization_project(
        self, project_id: str
    ) -> ArchiveOrganizationProjectResponse:
        """Archive a project."""
        project = self.projects.get(project_id)
        if not project:
            raise ValueError(f"Project not found: {project_id}")

        current_time = int(time.time())
        project["archived_at"] = current_time
        project["status"] = "archived"
        logger.info(f"Archived project {project_id}")

        return ArchiveOrganizationProjectResponse(
            id=project_id,
            archived=True,
        )

    async def list_project_users(
        self,
        project_id: str,
        limit: int = 20,
        after: str | None = None,
    ) -> ProjectUserListResponse:
        """List all users in a project."""
        if project_id not in self.projects:
            raise ValueError(f"Project not found: {project_id}")

        # Get project users
        project_user_dict = self.project_users.get(project_id, {})
        all_users = []

        for user_id, role in project_user_dict.items():
            org_user = self.organization_users.get(user_id)
            if org_user:
                all_users.append(
                    {
                        "id": user_id,
                        "name": org_user["name"],
                        "email": org_user["email"],
                        "role": role,
                        "added_at": org_user.get("added_at", 0),
                    }
                )

        # Sort by added_at descending
        all_users.sort(key=lambda u: u.get("added_at", 0), reverse=True)

        # Apply pagination
        if after:
            try:
                after_idx = next(
                    i for i, u in enumerate(all_users) if u["id"] == after)
                all_users = all_users[after_idx + 1:]
            except StopIteration:
                pass

        # Limit results
        users = all_users[:limit]
        has_more = len(all_users) > limit

        # Convert to ProjectUser objects
        user_objects = [ProjectUser(**u) for u in users]

        first_id = user_objects[0].id if user_objects else None
        last_id = user_objects[-1].id if user_objects else None

        return ProjectUserListResponse(
            data=user_objects,
            first_id=first_id,
            last_id=last_id,
            has_more=has_more,
        )

    async def create_project_user(
        self, project_id: str, request: CreateProjectUserRequest
    ) -> ProjectUser:
        """Add a user to a project."""
        if project_id not in self.projects:
            raise ValueError(f"Project not found: {project_id}")

        # Verify user exists in organization
        org_user = self.organization_users.get(request.user_id)
        if not org_user:
            raise ValueError(
                f"User not found in organization: {
                    request.user_id}")

        # Add to project
        if project_id not in self.project_users:
            self.project_users[project_id] = {}

        self.project_users[project_id][request.user_id] = request.role
        logger.info(
            f"Added user {
                request.user_id} to project {project_id} with role {
                request.role}")

        return ProjectUser(
            id=request.user_id,
            name=org_user["name"],
            email=org_user["email"],
            role=request.role,
            added_at=org_user.get("added_at", int(time.time())),
        )

    async def get_project_user(
            self,
            project_id: str,
            user_id: str) -> ProjectUser:
        """Get a specific user in a project."""
        if project_id not in self.projects:
            raise ValueError(f"Project not found: {project_id}")

        project_user_dict = self.project_users.get(project_id, {})
        if user_id not in project_user_dict:
            raise ValueError(f"User not found in project: {user_id}")

        org_user = self.organization_users.get(user_id)
        if not org_user:
            raise ValueError(f"User data not found: {user_id}")

        return ProjectUser(
            id=user_id,
            name=org_user["name"],
            email=org_user["email"],
            role=project_user_dict[user_id],
            added_at=org_user.get("added_at", int(time.time())),
        )

    async def modify_project_user(
        self, project_id: str, user_id: str, request: ModifyProjectUserRequest
    ) -> ProjectUser:
        """Modify a user's role in a project."""
        if project_id not in self.projects:
            raise ValueError(f"Project not found: {project_id}")

        project_user_dict = self.project_users.get(project_id, {})
        if user_id not in project_user_dict:
            raise ValueError(f"User not found in project: {user_id}")

        org_user = self.organization_users.get(user_id)
        if not org_user:
            raise ValueError(f"User data not found: {user_id}")

        # Update role
        project_user_dict[user_id] = request.role
        logger.info(
            f"Modified user {user_id} in project {project_id} to role {
                request.role}")

        return ProjectUser(
            id=user_id,
            name=org_user["name"],
            email=org_user["email"],
            role=request.role,
            added_at=org_user.get("added_at", int(time.time())),
        )

    async def delete_project_user(
        self, project_id: str, user_id: str
    ) -> DeleteProjectUserResponse:
        """Remove a user from a project."""
        if project_id not in self.projects:
            raise ValueError(f"Project not found: {project_id}")

        project_user_dict = self.project_users.get(project_id, {})
        if user_id not in project_user_dict:
            raise ValueError(f"User not found in project: {user_id}")

        del project_user_dict[user_id]
        logger.info(f"Removed user {user_id} from project {project_id}")

        return DeleteProjectUserResponse(
            id=user_id,
            deleted=True,
        )

    async def list_service_accounts(
        self,
        project_id: str,
        limit: int = 20,
        after: str | None = None,
    ) -> ServiceAccountListResponse:
        """List all service accounts in a project."""
        if project_id not in self.projects:
            raise ValueError(f"Project not found: {project_id}")

        # Get service accounts
        account_dict = self.service_accounts.get(project_id, {})
        all_accounts = list(account_dict.values())

        # Sort by created_at descending
        all_accounts.sort(key=lambda a: a.get("created_at", 0), reverse=True)

        # Apply pagination
        if after:
            try:
                after_idx = next(
                    i for i, a in enumerate(all_accounts) if a["id"] == after
                )
                all_accounts = all_accounts[after_idx + 1:]
            except StopIteration:
                pass

        # Limit results
        accounts = all_accounts[:limit]
        has_more = len(all_accounts) > limit

        # Convert to ServiceAccount objects
        account_objects = [ServiceAccount(**a) for a in accounts]

        first_id = account_objects[0].id if account_objects else None
        last_id = account_objects[-1].id if account_objects else None

        return ServiceAccountListResponse(
            data=account_objects,
            first_id=first_id,
            last_id=last_id,
            has_more=has_more,
        )

    async def create_service_account(
        self, project_id: str, request: CreateServiceAccountRequest
    ) -> ServiceAccount:
        """Create a service account in a project."""
        if project_id not in self.projects:
            raise ValueError(f"Project not found: {project_id}")

        account_id = f"svc_acct_{uuid.uuid4().hex[:20]}"
        current_time = int(time.time())

        account_data = {
            "id": account_id,
            "name": request.name,
            "role": request.role,
            "created_at": current_time,
        }

        if project_id not in self.service_accounts:
            self.service_accounts[project_id] = {}

        self.service_accounts[project_id][account_id] = account_data
        logger.info(
            f"Created service account {account_id} in project {project_id}")

        return ServiceAccount(**account_data)

    async def get_service_account(
        self, project_id: str, service_account_id: str
    ) -> ServiceAccount:
        """Get a specific service account."""
        if project_id not in self.projects:
            raise ValueError(f"Project not found: {project_id}")

        account_dict = self.service_accounts.get(project_id, {})
        account = account_dict.get(service_account_id)
        if not account:
            raise ValueError(
                f"Service account not found: {service_account_id}")

        return ServiceAccount(**account)

    async def delete_service_account(
        self, project_id: str, service_account_id: str
    ) -> DeleteServiceAccountResponse:
        """Delete a service account."""
        if project_id not in self.projects:
            raise ValueError(f"Project not found: {project_id}")

        account_dict = self.service_accounts.get(project_id, {})
        if service_account_id not in account_dict:
            raise ValueError(
                f"Service account not found: {service_account_id}")

        del account_dict[service_account_id]
        logger.info(
            f"Deleted service account {service_account_id} from project {project_id}")

        return DeleteServiceAccountResponse(
            id=service_account_id,
            deleted=True,
        )

    # Usage and Billing API methods

    async def get_completions_usage(
        self,
        start_time: int,
        end_time: int,
        bucket_width: str = "1d",
        project_id: str | None = None,
        model: str | None = None,
    ) -> CompletionsUsageResponse:
        """
        Get usage data for completions endpoints.

        Args:
            start_time: Start timestamp (Unix)
            end_time: End timestamp (Unix)
            bucket_width: Time bucket size ('1m', '1h', '1d')
            project_id: Optional project filter
            model: Optional model filter

        Returns:
            CompletionsUsageResponse with aggregated usage
        """
        # Get usage buckets from tracker
        buckets = self.usage_tracker.get_usage_by_time_bucket(
            start_time=start_time,
            end_time=end_time,
            bucket_size=bucket_width,
            project_id=project_id,
            model=model,
        )

        # Convert to API format
        data = []
        for bucket in buckets:
            result = UsageResultItem(
                input_tokens=bucket["input_tokens"],
                output_tokens=bucket["output_tokens"],
                input_cached_tokens=bucket["cached_tokens"],
                num_model_requests=bucket["num_requests"],
            )

            agg_bucket = UsageAggregationBucket(
                start_time=bucket["start_time"],
                end_time=bucket["end_time"],
                results=[result],
            )
            data.append(agg_bucket)

        return CompletionsUsageResponse(
            data=data, has_more=False, next_page=None)

    async def get_embeddings_usage(
        self,
        start_time: int,
        end_time: int,
        bucket_width: str = "1d",
        project_id: str | None = None,
        model: str | None = None,
    ) -> EmbeddingsUsageResponse:
        """Get usage data for embeddings endpoints."""
        buckets = self.usage_tracker.get_usage_by_time_bucket(
            start_time=start_time,
            end_time=end_time,
            bucket_size=bucket_width,
            project_id=project_id,
            model=model,
        )

        data = []
        for bucket in buckets:
            result = UsageResultItem(
                input_tokens=bucket["input_tokens"],
                output_tokens=bucket["output_tokens"],
                input_cached_tokens=bucket["cached_tokens"],
                num_model_requests=bucket["num_requests"],
            )

            agg_bucket = UsageAggregationBucket(
                start_time=bucket["start_time"],
                end_time=bucket["end_time"],
                results=[result],
            )
            data.append(agg_bucket)

        return EmbeddingsUsageResponse(
            data=data, has_more=False, next_page=None)

    async def get_images_usage(
        self,
        start_time: int,
        end_time: int,
        bucket_width: str = "1d",
        project_id: str | None = None,
    ) -> ImagesUsageResponse:
        """Get usage data for images endpoints."""
        buckets = self.usage_tracker.get_usage_by_time_bucket(
            start_time=start_time,
            end_time=end_time,
            bucket_size=bucket_width,
            project_id=project_id,
        )

        data = []
        for bucket in buckets:
            result = UsageResultItem(
                input_tokens=bucket["input_tokens"],
                output_tokens=bucket["output_tokens"],
                input_cached_tokens=bucket["cached_tokens"],
                num_model_requests=bucket["num_requests"],
            )

            agg_bucket = UsageAggregationBucket(
                start_time=bucket["start_time"],
                end_time=bucket["end_time"],
                results=[result],
            )
            data.append(agg_bucket)

        return ImagesUsageResponse(data=data, has_more=False, next_page=None)

    async def get_audio_speeches_usage(
        self,
        start_time: int,
        end_time: int,
        bucket_width: str = "1d",
        project_id: str | None = None,
    ) -> AudioSpeechesUsageResponse:
        """Get usage data for audio speeches endpoints."""
        buckets = self.usage_tracker.get_usage_by_time_bucket(
            start_time=start_time,
            end_time=end_time,
            bucket_size=bucket_width,
            project_id=project_id,
        )

        data = []
        for bucket in buckets:
            result = UsageResultItem(
                input_tokens=bucket["input_tokens"],
                output_tokens=bucket["output_tokens"],
                input_cached_tokens=bucket["cached_tokens"],
                num_model_requests=bucket["num_requests"],
            )

            agg_bucket = UsageAggregationBucket(
                start_time=bucket["start_time"],
                end_time=bucket["end_time"],
                results=[result],
            )
            data.append(agg_bucket)

        return AudioSpeechesUsageResponse(
            data=data, has_more=False, next_page=None)

    async def get_audio_transcriptions_usage(
        self,
        start_time: int,
        end_time: int,
        bucket_width: str = "1d",
        project_id: str | None = None,
    ) -> AudioTranscriptionsUsageResponse:
        """Get usage data for audio transcriptions endpoints."""
        buckets = self.usage_tracker.get_usage_by_time_bucket(
            start_time=start_time,
            end_time=end_time,
            bucket_size=bucket_width,
            project_id=project_id,
        )

        data = []
        for bucket in buckets:
            result = UsageResultItem(
                input_tokens=bucket["input_tokens"],
                output_tokens=bucket["output_tokens"],
                input_cached_tokens=bucket["cached_tokens"],
                num_model_requests=bucket["num_requests"],
            )

            agg_bucket = UsageAggregationBucket(
                start_time=bucket["start_time"],
                end_time=bucket["end_time"],
                results=[result],
            )
            data.append(agg_bucket)

        return AudioTranscriptionsUsageResponse(
            data=data, has_more=False, next_page=None
        )

    async def get_costs(
        self,
        start_time: int,
        end_time: int,
        bucket_width: str = "1d",
        project_id: str | None = None,
        group_by: list[str] | None = None,
    ) -> CostsResponse:
        """
        Get cost data aggregated by time buckets.

        Args:
            start_time: Start timestamp (Unix)
            end_time: End timestamp (Unix)
            bucket_width: Time bucket size ('1m', '1h', '1d')
            project_id: Optional project filter
            group_by: Optional grouping dimensions

        Returns:
            CostsResponse with cost breakdowns
        """
        # Get cost buckets from tracker
        buckets = self.usage_tracker.get_costs_by_time_bucket(
            start_time=start_time,
            end_time=end_time,
            bucket_size=bucket_width,
            project_id=project_id,
            group_by=group_by,
        )

        # Convert to API format
        data = []
        for bucket in buckets:
            results = []
            for result_dict in bucket["results"]:
                result = CostResult(
                    amount=CostAmount(
                        value=result_dict["amount"]["value"],
                        currency="usd",
                    ),
                    line_item=result_dict["line_item"],
                    project_id=result_dict.get("project_id"),
                )
                results.append(result)

            cost_bucket = CostBucket(
                start_time=bucket["start_time"],
                end_time=bucket["end_time"],
                results=results,
            )
            data.append(cost_bucket)

        return CostsResponse(data=data, has_more=False, next_page=None)

    # ==================== Fine-Tuning API Methods ====================
    # NOTE: Fine-tuning functionality has been extracted to FineTuningService
    # See: fakeai/services/fine_tuning_service.py
    # Methods: create_fine_tuning_job, list_fine_tuning_jobs, retrieve_fine_tuning_job,
    #          cancel_fine_tuning_job, list_fine_tuning_events, list_fine_tuning_checkpoints


class RealtimeSessionHandler:
    """
    Handler for Realtime WebSocket API sessions.

    Manages conversation state, audio buffers, VAD simulation, and event generation
    for the OpenAI Realtime API.
    """

    def __init__(
            self,
            model: str,
            config: AppConfig,
            fakeai_service: FakeAIService):
        """Initialize the Realtime session handler."""
        self.model = model
        self.config = config
        self.fakeai_service = fakeai_service
        self.generator = SimulatedGenerator()

        # Session state
        self.session_id = f"sess_{uuid.uuid4().hex}"
        self.session_config = RealtimeSessionConfig()
        self.session = self._create_session()

        # Conversation state
        self.conversation_items: list[RealtimeItem] = []
        self.current_response: RealtimeResponse | None = None
        self.response_in_progress = False

        # Audio buffer state
        self.audio_buffer: list[str] = []  # Base64 audio chunks
        self.audio_buffer_committed = False
        self.speech_detected = False
        self.speech_start_time: float | None = None

        # VAD simulation state
        self.vad_threshold = 0.5
        self.silence_duration_ms = 500
        self.last_audio_time: float | None = None

        # Rate limiting
        self.rate_limits = [
            RealtimeRateLimits(
                name="requests",
                limit=1000,
                remaining=950,
                reset_seconds=60.0,
            ),
            RealtimeRateLimits(
                name="tokens",
                limit=100000,
                remaining=95000,
                reset_seconds=60.0,
            ),
        ]

    def _create_session(self) -> RealtimeSession:
        """Create a new Realtime session."""
        return RealtimeSession(
            id=self.session_id,
            model=self.model,
            expires_at=int(time.time()) + 3600,  # 1 hour
            modalities=self.session_config.modalities,
            instructions=self.session_config.instructions,
            voice=self.session_config.voice,
            input_audio_format=self.session_config.input_audio_format,
            output_audio_format=self.session_config.output_audio_format,
            input_audio_transcription=self.session_config.input_audio_transcription,
            turn_detection=self.session_config.turn_detection,
            tools=self.session_config.tools,
            tool_choice=self.session_config.tool_choice,
            temperature=self.session_config.temperature,
            max_response_output_tokens=self.session_config.max_response_output_tokens,
        )

    def _create_event(
        self,
        event_type: RealtimeEventType,
        **kwargs: Any,
    ) -> RealtimeEvent:
        """Create a Realtime event with a unique event ID."""
        return RealtimeEvent(
            type=event_type,
            event_id=f"event_{uuid.uuid4().hex}",
            **kwargs,
        )

    def update_session(self, session_config: dict[str, Any]) -> RealtimeEvent:
        """Update session configuration."""
        # Update session config
        if "modalities" in session_config:
            self.session_config.modalities = [
                RealtimeModality(m) for m in session_config["modalities"]
            ]
        if "instructions" in session_config:
            self.session_config.instructions = session_config["instructions"]
        if "voice" in session_config:
            self.session_config.voice = RealtimeVoice(session_config["voice"])
        if "input_audio_format" in session_config:
            self.session_config.input_audio_format = RealtimeAudioFormat(
                session_config["input_audio_format"]
            )
        if "output_audio_format" in session_config:
            self.session_config.output_audio_format = RealtimeAudioFormat(
                session_config["output_audio_format"]
            )
        if "turn_detection" in session_config:
            td = session_config["turn_detection"]
            if td is None:
                self.session_config.turn_detection = None
            else:
                self.session_config.turn_detection = RealtimeTurnDetection(
                    **td)
        if "tools" in session_config:
            self.session_config.tools = [
                RealtimeTool(**tool) for tool in session_config["tools"]
            ]
        if "tool_choice" in session_config:
            self.session_config.tool_choice = session_config["tool_choice"]
        if "temperature" in session_config:
            self.session_config.temperature = session_config["temperature"]
        if "max_response_output_tokens" in session_config:
            self.session_config.max_response_output_tokens = session_config[
                "max_response_output_tokens"
            ]

        # Update session object
        self.session = self._create_session()

        return self._create_event(
            RealtimeEventType.SESSION_UPDATED,
            session=self.session,
        )

    def append_audio_buffer(self, audio: str) -> list[RealtimeEvent]:
        """Append audio data to the input buffer."""
        self.audio_buffer.append(audio)
        self.last_audio_time = time.time()

        events = []

        # Simulate VAD - detect speech
        if not self.speech_detected and len(self.audio_buffer) >= 3:
            # Speech detected after a few chunks
            self.speech_detected = True
            self.speech_start_time = time.time()
            events.append(
                self._create_event(
                    RealtimeEventType.INPUT_AUDIO_BUFFER_SPEECH_STARTED,
                    audio_end_ms=int(self.speech_start_time * 1000),
                )
            )

        return events

    def commit_audio_buffer(self) -> list[RealtimeEvent]:
        """Commit the audio buffer and create a conversation item."""
        events = []

        # Mark as committed
        self.audio_buffer_committed = True

        # Stop speech if detected
        if self.speech_detected:
            speech_end_time = time.time()
            events.append(
                self._create_event(
                    RealtimeEventType.INPUT_AUDIO_BUFFER_SPEECH_STOPPED,
                    audio_end_ms=int(speech_end_time * 1000),
                )
            )
            self.speech_detected = False

        # Committed event
        events.append(
            self._create_event(RealtimeEventType.INPUT_AUDIO_BUFFER_COMMITTED)
        )

        # Create conversation item with audio
        item = RealtimeItem(
            id=f"item_{uuid.uuid4().hex}",
            type=RealtimeItemType.MESSAGE,
            status=RealtimeItemStatus.COMPLETED,
            role=RealtimeItemRole.USER,
            content=[
                RealtimeContent(
                    type=RealtimeContentType.INPUT_AUDIO,
                    audio="".join(self.audio_buffer),
                    transcript=self._transcribe_audio(self.audio_buffer),
                )
            ],
        )
        self.conversation_items.append(item)

        # Item created event
        events.append(
            self._create_event(
                RealtimeEventType.CONVERSATION_ITEM_CREATED,
                item=item,
            )
        )

        # Clear buffer
        self.audio_buffer.clear()
        self.audio_buffer_committed = False

        return events

    def clear_audio_buffer(self) -> RealtimeEvent:
        """Clear the audio buffer."""
        self.audio_buffer.clear()
        self.audio_buffer_committed = False
        self.speech_detected = False

        return self._create_event(RealtimeEventType.INPUT_AUDIO_BUFFER_CLEARED)

    def create_conversation_item(
            self, item_data: dict[str, Any]) -> RealtimeEvent:
        """Create a conversation item."""
        item = RealtimeItem(
            id=f"item_{uuid.uuid4().hex}",
            type=RealtimeItemType(item_data.get("type", "message")),
            status=RealtimeItemStatus(item_data.get("status", "completed")),
            role=(
                RealtimeItemRole(item_data.get("role", "user"))
                if "role" in item_data
                else None
            ),
            content=(
                [RealtimeContent(**content) for content in item_data.get("content", [])]
                if "content" in item_data
                else []
            ),
            call_id=item_data.get("call_id"),
            name=item_data.get("name"),
            arguments=item_data.get("arguments"),
            output=item_data.get("output"),
        )
        self.conversation_items.append(item)

        return self._create_event(
            RealtimeEventType.CONVERSATION_ITEM_CREATED,
            item=item,
        )

    def delete_conversation_item(self, item_id: str) -> RealtimeEvent:
        """Delete a conversation item."""
        self.conversation_items = [
            item for item in self.conversation_items if item.id != item_id
        ]

        return self._create_event(
            RealtimeEventType.CONVERSATION_ITEM_DELETED,
            item_id=item_id,
        )

    async def create_response(
        self, response_config: dict[str, Any] | None = None
    ) -> AsyncGenerator[RealtimeEvent, None]:
        """Create a response to the conversation."""
        if self.response_in_progress:
            yield self._create_event(
                RealtimeEventType.ERROR,
                error=RealtimeError(
                    type="invalid_request_error",
                    message="A response is already in progress",
                ),
            )
            return

        self.response_in_progress = True

        # Create response object
        response_id = f"resp_{uuid.uuid4().hex}"
        self.current_response = RealtimeResponse(
            id=response_id,
            status=RealtimeItemStatus.IN_PROGRESS,
            output=[],
        )

        # Response created event
        yield self._create_event(
            RealtimeEventType.RESPONSE_CREATED,
            response=self.current_response,
        )

        # Generate response content
        conversation_text = self._build_conversation_text()
        response_text = await self._generate_response_text(conversation_text)

        # Create output item
        output_item = RealtimeItem(
            id=f"item_{uuid.uuid4().hex}",
            type=RealtimeItemType.MESSAGE,
            status=RealtimeItemStatus.IN_PROGRESS,
            role=RealtimeItemRole.ASSISTANT,
            content=[],
        )

        # Output item added event
        yield self._create_event(
            RealtimeEventType.RESPONSE_OUTPUT_ITEM_ADDED,
            response_id=response_id,
            output_index=0,
            item=output_item,
        )

        # Determine modalities to generate
        modalities = (
            response_config.get("modalities", self.session_config.modalities)
            if response_config
            else self.session_config.modalities
        )

        content_index = 0

        # Generate text output if text modality is enabled
        if RealtimeModality.TEXT in modalities:
            # Content part added
            yield self._create_event(
                RealtimeEventType.RESPONSE_CONTENT_PART_ADDED,
                response_id=response_id,
                output_index=0,
                content_index=content_index,
                item=output_item,
            )

            # Stream text deltas
            words = response_text.split()
            accumulated_text = ""
            for i, word in enumerate(words):
                delta = word + (" " if i < len(words) - 1 else "")
                accumulated_text += delta

                yield self._create_event(
                    RealtimeEventType.RESPONSE_TEXT_DELTA,
                    response_id=response_id,
                    output_index=0,
                    content_index=content_index,
                    delta=delta,
                )

                # Simulate realistic typing speed
                await asyncio.sleep(random.uniform(0.02, 0.05))

            # Text done
            yield self._create_event(
                RealtimeEventType.RESPONSE_TEXT_DONE,
                response_id=response_id,
                output_index=0,
                content_index=content_index,
                delta=accumulated_text,
            )

            # Add text content to output item
            output_item.content.append(
                RealtimeContent(
                    type=RealtimeContentType.TEXT,
                    text=accumulated_text,
                )
            )

            # Content part done
            yield self._create_event(
                RealtimeEventType.RESPONSE_CONTENT_PART_DONE,
                response_id=response_id,
                output_index=0,
                content_index=content_index,
                item=output_item,
            )

            content_index += 1

        # Generate audio output if audio modality is enabled
        if RealtimeModality.AUDIO in modalities:
            # Content part added
            yield self._create_event(
                RealtimeEventType.RESPONSE_CONTENT_PART_ADDED,
                response_id=response_id,
                output_index=0,
                content_index=content_index,
                item=output_item,
            )

            # Generate simulated audio
            audio_data = self._generate_audio_from_text(response_text)

            # Stream audio in chunks
            chunk_size = 4096  # Base64 characters per chunk
            accumulated_audio = ""
            transcript = ""

            for i in range(0, len(audio_data), chunk_size):
                chunk = audio_data[i: i + chunk_size]
                accumulated_audio += chunk

                # Audio delta
                yield self._create_event(
                    RealtimeEventType.RESPONSE_AUDIO_DELTA,
                    response_id=response_id,
                    output_index=0,
                    content_index=content_index,
                    delta=chunk,
                )

                # Simulate realistic audio streaming
                await asyncio.sleep(0.05)

                # Periodically send transcript deltas
                if i % (chunk_size * 3) == 0 and i > 0:
                    # Simulate partial transcript
                    words_so_far = int((i / len(audio_data)) * len(words))
                    partial_transcript = " ".join(words[:words_so_far])
                    transcript_delta = partial_transcript[len(transcript):]
                    transcript = partial_transcript

                    if transcript_delta:
                        yield self._create_event(
                            RealtimeEventType.RESPONSE_AUDIO_TRANSCRIPT_DELTA,
                            response_id=response_id,
                            output_index=0,
                            content_index=content_index,
                            delta=transcript_delta,
                        )

            # Audio done
            yield self._create_event(
                RealtimeEventType.RESPONSE_AUDIO_DONE,
                response_id=response_id,
                output_index=0,
                content_index=content_index,
                delta=accumulated_audio,
            )

            # Final transcript
            final_transcript_delta = response_text[len(transcript):]
            if final_transcript_delta:
                yield self._create_event(
                    RealtimeEventType.RESPONSE_AUDIO_TRANSCRIPT_DELTA,
                    response_id=response_id,
                    output_index=0,
                    content_index=content_index,
                    delta=final_transcript_delta,
                )

            # Transcript done
            yield self._create_event(
                RealtimeEventType.RESPONSE_AUDIO_TRANSCRIPT_DONE,
                response_id=response_id,
                output_index=0,
                content_index=content_index,
                transcript=response_text,
            )

            # Add audio content to output item
            output_item.content.append(
                RealtimeContent(
                    type=RealtimeContentType.AUDIO,
                    audio=accumulated_audio,
                    transcript=response_text,
                )
            )

            # Content part done
            yield self._create_event(
                RealtimeEventType.RESPONSE_CONTENT_PART_DONE,
                response_id=response_id,
                output_index=0,
                content_index=content_index,
                item=output_item,
            )

        # Mark output item as completed
        output_item.status = RealtimeItemStatus.COMPLETED
        self.current_response.output.append(output_item)
        self.conversation_items.append(output_item)

        # Output item done
        yield self._create_event(
            RealtimeEventType.RESPONSE_OUTPUT_ITEM_DONE,
            response_id=response_id,
            output_index=0,
            item=output_item,
        )

        # Calculate usage
        input_tokens = calculate_token_count(conversation_text)
        output_tokens = calculate_token_count(response_text)
        self.current_response.usage = Usage(
            prompt_tokens=input_tokens,
            completion_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
        )

        # Mark response as completed
        self.current_response.status = RealtimeItemStatus.COMPLETED
        self.response_in_progress = False

        # Response done
        yield self._create_event(
            RealtimeEventType.RESPONSE_DONE,
            response=self.current_response,
        )

        # Rate limits updated
        yield self._create_event(
            RealtimeEventType.RATE_LIMITS_UPDATED,
            rate_limits=self.rate_limits,
        )

    def cancel_response(self) -> RealtimeEvent:
        """Cancel the current response."""
        if not self.response_in_progress:
            return self._create_event(
                RealtimeEventType.ERROR,
                error=RealtimeError(
                    type="invalid_request_error",
                    message="No response in progress to cancel",
                ),
            )

        self.response_in_progress = False
        if self.current_response:
            self.current_response.status = RealtimeItemStatus.INCOMPLETE

        return self._create_event(
            RealtimeEventType.RESPONSE_CANCELLED,
            response=self.current_response,
        )

    def _transcribe_audio(self, audio_chunks: list[str]) -> str:
        """Simulate audio transcription."""
        # In a real implementation, this would use Whisper or similar
        # For simulation, generate realistic text
        return self.generator.generate_response(
            prompt="transcribe audio",
            max_tokens=50,
        )

    def _build_conversation_text(self) -> str:
        """Build conversation text from items."""
        texts = []
        for item in self.conversation_items:
            if (
                item.type == RealtimeItemType.MESSAGE and
                item.role == RealtimeItemRole.USER
            ):
                for content in item.content:
                    if content.type == RealtimeContentType.TEXT and content.text:
                        texts.append(content.text)
                    elif (
                        content.type == RealtimeContentType.INPUT_AUDIO and
                        content.transcript
                    ):
                        texts.append(content.transcript)
        return " ".join(texts) if texts else "Hello"

    async def _generate_response_text(self, prompt: str) -> str:
        """Generate response text based on conversation."""
        # Use the simulated generator
        return self.generator.generate_response(
            prompt=prompt,
            max_tokens=100,
        )

    def _generate_audio_from_text(self, text: str) -> str:
        """Generate simulated audio from text."""
        # Generate fake PCM16 audio data (base64 encoded)
        # In a real implementation, this would use TTS
        audio_bytes = generate_simulated_audio(text, format="pcm16")
        return base64.b64encode(audio_bytes).decode("utf-8")

    # Vector Stores API methods

    async def create_vector_store(
        self, request: CreateVectorStoreRequest
    ) -> VectorStore:
        """Create a new vector store."""
        return await self.vector_store_service.create_vector_store(request)

    async def list_vector_stores(
        self,
        limit: int = 20,
        order: str = "desc",
        after: str | None = None,
        before: str | None = None,
    ) -> VectorStoreListResponse:
        """List all vector stores."""
        return await self.vector_store_service.list_vector_stores(
            limit=limit, order=order, after=after, before=before
        )

    async def retrieve_vector_store(self, vs_id: str) -> VectorStore:
        """Retrieve a vector store by ID."""
        return await self.vector_store_service.retrieve_vector_store(vs_id)

    async def modify_vector_store(
        self, vs_id: str, request: ModifyVectorStoreRequest
    ) -> VectorStore:
        """Modify a vector store."""
        return await self.vector_store_service.modify_vector_store(vs_id, request)

    async def delete_vector_store(self, vs_id: str) -> dict[str, Any]:
        """Delete a vector store."""
        return await self.vector_store_service.delete_vector_store(vs_id)

    async def create_vector_store_file(
        self, vs_id: str, request: CreateVectorStoreFileRequest
    ) -> VectorStoreFile:
        """Add a file to a vector store."""
        return await self.vector_store_service.add_file_to_vector_store(vs_id, request)

    async def list_vector_store_files(
        self,
        vs_id: str,
        limit: int = 20,
        order: str = "desc",
        after: str | None = None,
        before: str | None = None,
    ) -> VectorStoreFileListResponse:
        """List all files in a vector store."""
        return await self.vector_store_service.list_vector_store_files(
            vs_id, limit=limit, order=order, after=after, before=before
        )

    async def retrieve_vector_store_file(
        self, vs_id: str, file_id: str
    ) -> VectorStoreFile:
        """Retrieve a file from a vector store."""
        return await self.vector_store_service.retrieve_vector_store_file(vs_id, file_id)

    async def delete_vector_store_file(
        self, vs_id: str, file_id: str
    ) -> dict[str, Any]:
        """Delete a file from a vector store."""
        return await self.vector_store_service.delete_vector_store_file(vs_id, file_id)

    async def create_vector_store_file_batch(
        self, vs_id: str, request: CreateVectorStoreFileBatchRequest
    ) -> VectorStoreFileBatch:
        """Create a batch of files in a vector store."""
        return await self.vector_store_service.create_file_batch(vs_id, request)

    async def retrieve_vector_store_file_batch(
        self, vs_id: str, batch_id: str
    ) -> VectorStoreFileBatch:
        """Retrieve a file batch from a vector store."""
        return await self.vector_store_service.retrieve_file_batch(vs_id, batch_id)

    async def cancel_vector_store_file_batch(
        self, vs_id: str, batch_id: str
    ) -> VectorStoreFileBatch:
        """Cancel a file batch in a vector store."""
        return await self.vector_store_service.cancel_file_batch(vs_id, batch_id)
