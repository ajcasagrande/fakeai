"""
Chat Completion Service

This module provides the chat completion service, the most complex service in FakeAI.
It handles streaming and non-streaming completions, multi-modal content, tool calling,
reasoning models, KV cache integration, predicted outputs, and token timing.

Features:
- Streaming and non-streaming responses
- Multi-modal content (text, images, video, audio)
- Tool calling with parallel execution
- Reasoning models (gpt-oss, DeepSeek-R1)
- KV cache integration for speedup
- Predicted outputs (EAGLE/speculative decoding)
- Token timing and latency simulation
- Structured outputs (JSON schema)
- Prompt caching
- Audio input/output
- Logprobs generation
"""

#  SPDX-License-Identifier: Apache-2.0

import asyncio
import logging
import random
import re
import time
import uuid
from collections.abc import AsyncGenerator
from typing import Any

from fakeai.audio import (
    calculate_audio_input_tokens,
    extract_text_from_audio,
    generate_audio_output,
)
from fakeai.config import AppConfig
from fakeai.dynamo_metrics import DynamoMetricsCollector
from fakeai.kv_cache import KVCacheMetrics, SmartRouter, tokenize_for_cache
from fakeai.logprobs_enhanced import create_chat_logprobs
from fakeai.metrics import MetricsTracker
from fakeai.models import (
    AudioOutput,
    ChatCompletionChunk,
    ChatCompletionChunkChoice,
    ChatCompletionChoice,
    ChatCompletionRequest,
    ChatCompletionResponse,
    CompletionTokensDetails,
    Delta,
    Message,
    PromptTokensDetails,
    Role,
    Usage,
)
from fakeai.structured_outputs import (
    SchemaValidationError,
    format_as_json_string,
    generate_from_schema,
    validate_strict_schema,
)
from fakeai.utils import calculate_token_count, tokenize_text
from fakeai.video import calculate_message_video_tokens
from fakeai.vision import calculate_message_image_tokens

logger = logging.getLogger(__name__)


def extract_text_content(content: str | list | None) -> str:
    """
    Extract text from message content (string or content parts array).

    This is a critical helper used throughout the service for multi-modal content.

    Args:
        content: Message content (string, list of content parts, or None)

    Returns:
        Extracted text content as string
    """
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


class ChatCompletionService:
    """
    Service for creating chat completions.

    This is the most complex service in FakeAI, handling:
    - Streaming and non-streaming responses
    - Multi-modal inputs (text, images, video, audio)
    - Tool calling with intelligent decision-making
    - Reasoning models (GPT-OSS, DeepSeek-R1)
    - KV cache integration with AI-Dynamo simulation
    - Predicted outputs (EAGLE/speculative decoding)
    - Token timing with realistic latency profiles
    - Structured outputs with JSON schema validation
    - Prompt caching with hash-based detection
    - Audio input transcription and output generation
    - Logprobs generation for transparency
    """

    def __init__(
        self,
        config: AppConfig,
        metrics_tracker: MetricsTracker,
        model_registry: Any,
        kv_cache_router: SmartRouter,
        kv_cache_metrics: KVCacheMetrics,
        dynamo_metrics: DynamoMetricsCollector,
        usage_tracker: Any | None = None,
        llm_generator: Any | None = None,
        semantic_embeddings: Any | None = None,
    ):
        """
        Initialize the chat completion service.

        Args:
            config: Application configuration
            metrics_tracker: Metrics tracking singleton
            model_registry: Model registry for validation and auto-creation
            kv_cache_router: Smart router for KV cache management
            kv_cache_metrics: KV cache performance metrics
            dynamo_metrics: Dynamo latency metrics collector
            usage_tracker: Optional usage tracking for billing/monitoring
            llm_generator: Optional lightweight LLM generator
            semantic_embeddings: Optional semantic embedding generator
        """
        self.config = config
        self.metrics_tracker = metrics_tracker
        self.model_registry = model_registry
        self.kv_cache_router = kv_cache_router
        self.kv_cache_metrics = kv_cache_metrics
        self.dynamo_metrics = dynamo_metrics
        self.usage_tracker = usage_tracker
        self.llm_generator = llm_generator
        self.semantic_embeddings = semantic_embeddings

        # Random instance for deterministic generation with seeds
        self._random = random.Random()
        self._current_seed: int | None = None

        # Prompt cache for hash-based caching (separate from KV cache)
        self._prompt_cache: dict[str, tuple[int, float]] = {}  # hash -> (tokens, timestamp)

        logger.info("Initialized ChatCompletionService")

    async def create_chat_completion(
        self,
        request: ChatCompletionRequest,
    ) -> ChatCompletionResponse:
        """
        Create a chat completion.

        This handles the full non-streaming chat completion flow:
        1. Model validation and auto-creation
        2. Seed setting for determinism
        3. Structured output validation
        4. Multi-modal token calculation (text, images, video, audio)
        5. KV cache routing and speedup
        6. Prompt cache hit detection
        7. Reasoning content generation (for reasoning models)
        8. Tool calling decision and generation
        9. Regular completion generation
        10. Predicted outputs (EAGLE/speculative decoding)
        11. Audio output generation
        12. Logprobs generation
        13. Usage tracking and metrics

        Args:
            request: Chat completion request with all parameters

        Returns:
            ChatCompletionResponse with generated content and metadata
        """
        # Set seed for deterministic generation
        self._set_seed_if_provided(request.seed)

        # Ensure model exists (auto-create if needed)
        self.model_registry.ensure_model_exists(request.model)

        # Start Dynamo request tracking
        request_id = f"req-{uuid.uuid4().hex[:12]}"

        # Handle structured outputs validation
        is_structured_output = False
        json_schema_name = None
        json_schema_obj = None

        if request.response_format:
            if (
                hasattr(request.response_format, "type")
                and request.response_format.type == "json_schema"
            ):
                is_structured_output = True
                json_schema_obj = request.response_format.json_schema.schema
                json_schema_name = request.response_format.json_schema.name

                # Validate strict mode requirements
                if request.response_format.json_schema.strict:
                    try:
                        validate_strict_schema(json_schema_obj)
                    except SchemaValidationError as e:
                        raise ValueError(
                            f"Invalid JSON schema for strict mode: {str(e)}"
                        )

                    # Enforce parallel_tool_calls=false for strict mode
                    if request.parallel_tool_calls is not False:
                        raise ValueError(
                            "When using strict mode with structured outputs, "
                            "parallel_tool_calls must be false"
                        )

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

        # Process video inputs if present (calculate video tokens - NVIDIA Cosmos extension)
        input_video_tokens = 0
        for msg in request.messages:
            if msg.content:
                input_video_tokens += calculate_message_video_tokens(
                    msg.content, request.model
                )

        # Extract prompt text for token counting and KV cache routing
        prompt_text = " ".join(
            extract_text_content(msg.content)
            for msg in request.messages
            if msg.content
        )

        # Add audio transcriptions to prompt text
        if audio_transcript:
            prompt_text = f"{prompt_text} {audio_transcript}".strip()

        # Calculate text tokens
        text_tokens = calculate_token_count(prompt_text)

        # Total prompt tokens = text + image + video + audio tokens
        prompt_tokens = (
            text_tokens + input_image_tokens + input_video_tokens + input_audio_tokens
        )

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

        # Generate reasoning content for reasoning models
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
                    parallel=request.parallel_tool_calls
                    if request.parallel_tool_calls is not None
                    else True,
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
        if request.prediction and self._supports_predicted_outputs(request.model):
            (
                accepted_pred_tokens,
                rejected_pred_tokens,
            ) = self._simulate_speculative_decoding(
                request.prediction.content, completion_text
            )

        # Generate audio output if requested
        audio_output = None
        output_audio_tokens = 0
        if request.audio and (not request.modalities or "audio" in request.modalities):
            audio_config = {
                "voice": request.audio.voice,
                "format": request.audio.format,
            }
            audio_output, output_audio_tokens = self._generate_audio_output(
                completion_text, audio_config
            )

        # Track token generation (including reasoning, prediction, and audio tokens)
        total_completion_tokens = (
            completion_tokens
            + reasoning_tokens
            + rejected_pred_tokens
            + output_audio_tokens
        )
        self.metrics_tracker.track_tokens(
            "/v1/chat/completions", total_completion_tokens
        )

        # Determine finish reason
        max_tokens_requested = self._get_effective_max_tokens(request)
        finish_reason = (
            "length" if completion_tokens >= max_tokens_requested else "stop"
        )

        # Create completion tokens details
        completion_tokens_details = None
        if (
            reasoning_tokens > 0
            or accepted_pred_tokens > 0
            or rejected_pred_tokens > 0
            or output_audio_tokens > 0
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
        if request.logprobs and completion_text:
            # Tokenize completion text
            completion_tokens_list = re.findall(r"\w+|[^\w\s]", completion_text)
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
        if self.usage_tracker:
            self.usage_tracker.track_usage(
                endpoint="/v1/chat/completions",
                model=request.model,
                input_tokens=prompt_tokens,
                output_tokens=total_completion_tokens,
                cached_tokens=total_cached_tokens,
                project_id=request.metadata.get("project_id") if request.metadata else None,
                user_id=request.user,
            )

        return response

    async def create_chat_completion_stream(
        self,
        request: ChatCompletionRequest,
    ) -> AsyncGenerator[ChatCompletionChunk, None]:
        """
        Create a streaming chat completion.

        This handles the full streaming chat completion flow:
        1. Model validation
        2. Multi-modal token calculation
        3. KV cache routing for TTFT speedup
        4. Prompt cache hit detection
        5. Reasoning content generation (streamed first)
        6. Tool calling generation (streamed incrementally)
        7. Regular content streaming (token-by-token with timing)
        8. Final chunk with usage (if requested)

        The streaming implementation uses realistic latency simulation:
        - TTFT (Time to First Token) with cache speedup
        - ITL (Inter-Token Latency) with variance
        - Token timing information in deltas

        Args:
            request: Chat completion request with stream=True

        Yields:
            ChatCompletionChunk objects for SSE streaming
        """
        # Ensure model exists
        self.model_registry.ensure_model_exists(request.model)

        # Extract prompt text for caching and token counting
        prompt_text = " ".join(
            extract_text_content(msg.content)
            for msg in request.messages
            if msg.content
        )
        prompt_tokens = calculate_token_count(prompt_text)

        # Prompt caching check
        prompt_hash = self._get_prompt_hash(request.messages)
        is_prompt_cache_hit, prompt_cached_tokens = self._check_cache_hit(
            prompt_hash, prompt_tokens
        )

        # KV Cache routing (for streaming we still do this but mainly for metrics)
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

        # Generate reasoning content for reasoning models
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
                    parallel=request.parallel_tool_calls
                    if request.parallel_tool_calls is not None
                    else True,
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
                stream=True,  # Hint for LLM generator
            )
            # Split the completion text into token-equivalent chunks
            content_tokens = tokenize_text(completion_text)

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

        # Track start time for token timing calculations
        stream_start_time = time.time()
        token_timestamps = []

        # Calculate ITL (inter-token latency) parameters for use throughout streaming
        itl_base = self.config.itl_ms / 1000.0  # Convert ms to seconds
        itl_variance = self.config.itl_variance_percent / 100.0
        itl_min = itl_base * (1.0 - itl_variance)
        itl_max = itl_base * (1.0 + itl_variance)

        # Stream reasoning content first (for reasoning models)
        if reasoning_tokens_list:
            for i, token in enumerate(reasoning_tokens_list):
                # Record the timestamp for this token
                current_time = time.time()
                relative_time = round(
                    (current_time - stream_start_time) * 1000
                )  # milliseconds
                token_timestamps.append(relative_time)

                # For tokens that are alphanumeric (words), add space before if not first
                # For punctuation and special chars, no space needed
                chunk_text = token
                if i > 0 and (token[0].isalnum() if token else False):
                    chunk_text = " " + chunk_text

                # Stream as reasoning_content
                chunk = ChatCompletionChunk(
                    id=stream_id,
                    created=int(time.time()),
                    model=request.model,
                    choices=[
                        ChatCompletionChunkChoice(
                            index=j,
                            delta=Delta(
                                reasoning_content=chunk_text, token_timing=[relative_time]
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
                # Stream tool call in chunks: id, type, function name, then arguments

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
                args_chunks = [args_str[i : i + 20] for i in range(0, len(args_str), 20)]

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
                                            function=FunctionDelta(arguments=args_chunk),
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
                # For punctuation and special chars, no space needed
                chunk_text = token
                if i > 0 and (token[0].isalnum() if token else False):
                    chunk_text = " " + chunk_text

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
                token_delay = random.uniform(itl_min, itl_max)
                await asyncio.sleep(token_delay)

        # Include usage in final chunk if requested
        if request.stream_options and request.stream_options.include_usage:
            # Calculate usage statistics
            prompt_tokens_calc = calculate_token_count(
                " ".join(
                    extract_text_content(msg.content)
                    for msg in request.messages
                    if msg.content
                )
            )

            completion_tokens_calc = len(content_tokens)
            reasoning_tokens_count = len(reasoning_tokens_list) if reasoning_tokens_list else 0
            total_completion_tokens = completion_tokens_calc + reasoning_tokens_count

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
                    prompt_tokens=prompt_tokens_calc,
                    completion_tokens=total_completion_tokens,
                    total_tokens=prompt_tokens_calc + total_completion_tokens,
                    prompt_tokens_details=PromptTokensDetails(
                        cached_tokens=total_cached_tokens,
                        audio_tokens=0,
                    ),
                    completion_tokens_details=completion_tokens_details,
                ),
            )
            yield final_chunk

            # Track token generation and complete KV cache request
            self.metrics_tracker.track_tokens(
                "/v1/chat/completions", total_completion_tokens
            )
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
            completion_tokens_calc = len(content_tokens)
            reasoning_tokens_count = len(reasoning_tokens_list) if reasoning_tokens_list else 0
            total_completion_tokens = completion_tokens_calc + reasoning_tokens_count
            self.metrics_tracker.track_tokens(
                "/v1/chat/completions", total_completion_tokens
            )
            self.kv_cache_router.complete_request(
                worker_id, token_ids, total_completion_tokens
            )

    # Private helper methods

    async def _generate_simulated_completion(
        self,
        messages: list[Message],
        max_tokens: int,
        temperature: float,
        stream: bool = False,
    ) -> str:
        """
        Generate a simulated completion based on the input messages.

        Uses LLM generator if available, falls back to template-based generation.

        Args:
            messages: List of conversation messages
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            stream: Hint that this is for streaming (affects LLM generation)

        Returns:
            Generated completion text
        """
        # Extract the last user message
        user_message = next(
            (
                extract_text_content(msg.content)
                for msg in reversed(messages)
                if msg.role == Role.USER and msg.content
            ),
            "Tell me about AI.",
        )

        # Try to use LLM generator if available
        if self.llm_generator and self.llm_generator.is_available():
            try:
                # Build a simple prompt
                prompt = f"User: {user_message}\nAssistant:"

                # Generate with LLM
                response = self.llm_generator.generate(
                    prompt=prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    seed=self._current_seed,
                )

                if response:
                    return response
            except Exception as e:
                logger.warning(f"LLM generation failed: {e}, falling back to template")

        # Fallback to template-based generation
        from fakeai.utils.text_generation import SimulatedGenerator

        generator = SimulatedGenerator()
        return generator.generate_response(
            prompt=user_message,
            max_tokens=max_tokens,
        )

    async def _generate_simulated_reasoning(
        self,
        messages: list[Message],
        max_tokens: int = 50,
    ) -> str:
        """
        Generate simulated reasoning content for reasoning models.

        Args:
            messages: List of conversation messages
            max_tokens: Maximum tokens for reasoning

        Returns:
            Generated reasoning content
        """
        # Extract the last user message
        user_message = next(
            (
                extract_text_content(msg.content)
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

        return reasoning

    def _process_audio_input(self, messages: list[Message]) -> tuple[int, str]:
        """
        Process audio inputs from messages.

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
        self, text: str | None, audio_config: dict[str, str] | None
    ) -> tuple[AudioOutput | None, int]:
        """
        Generate audio output for assistant response.

        Args:
            text: Text to convert to audio
            audio_config: Audio configuration (voice, format)

        Returns:
            Tuple of (AudioOutput, audio_tokens)
        """
        if not text or not audio_config:
            return None, 0

        # Generate audio output (includes data, transcript, id, expires_at)
        audio_output_dict = generate_audio_output(
            text=text, voice=audio_config.get("voice", "alloy")
        )

        # Calculate audio tokens (roughly 1 token per character of text)
        audio_tokens = len(text)

        # Create AudioOutput object from dict
        audio_output = AudioOutput(
            id=audio_output_dict["id"],
            data=audio_output_dict["data"],
            expires_at=audio_output_dict["expires_at"],
            transcript=audio_output_dict["transcript"],
        )

        return audio_output, audio_tokens

    def _simulate_speculative_decoding(
        self, prediction_content: str, actual_output: str | None
    ) -> tuple[int, int]:
        """
        Simulate accepted and rejected prediction tokens for EAGLE/speculative decoding.

        Args:
            prediction_content: The predicted content
            actual_output: The actual generated content

        Returns:
            Tuple of (accepted_tokens, rejected_tokens)
        """
        if not actual_output:
            return 0, 0

        # Calculate token counts
        pred_tokens = calculate_token_count(prediction_content)
        actual_tokens = calculate_token_count(actual_output)

        # Simulate acceptance rate based on string similarity
        # Typical acceptance rates: 60-80% for good predictions
        from difflib import SequenceMatcher

        similarity = SequenceMatcher(None, prediction_content, actual_output).ratio()

        # Higher similarity → higher acceptance rate
        acceptance_rate = 0.5 + (similarity * 0.3)  # Range: 50-80%

        # Calculate accepted/rejected tokens
        max_checkable = min(pred_tokens, actual_tokens)
        accepted = int(max_checkable * acceptance_rate)
        rejected = pred_tokens - accepted

        return accepted, rejected

    def _is_reasoning_model(self, model_id: str) -> bool:
        """Check if model supports reasoning content."""
        return (
            model_id.startswith("gpt-oss")
            or model_id.startswith("deepseek-ai/DeepSeek-R1")
            or "reasoning" in model_id.lower()
        )

    def _supports_predicted_outputs(self, model_id: str) -> bool:
        """Check if model supports Predicted Outputs / speculative decoding."""
        return model_id.startswith("openai/gpt-oss-120b")

    def _get_effective_max_tokens(self, request: ChatCompletionRequest) -> int:
        """
        Get effective max tokens from request.

        Args:
            request: ChatCompletionRequest

        Returns:
            Effective max tokens (respects both max_tokens and max_completion_tokens)
        """
        # max_completion_tokens takes precedence for reasoning models
        if request.max_completion_tokens is not None:
            return request.max_completion_tokens
        elif request.max_tokens is not None:
            return request.max_tokens
        else:
            return 16  # Default

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

            fingerprint_hash = hashlib.sha256(f"seed-{seed}".encode()).hexdigest()[:16]
            return f"fp_{fingerprint_hash}"
        else:
            # Random fingerprint
            return "fp_" + uuid.uuid4().hex[:16]

    def _get_prompt_hash(self, messages: list[Message]) -> str:
        """
        Generate stable hash from messages for prompt caching.

        Args:
            messages: List of messages to hash

        Returns:
            SHA-256 hash of the serialized messages
        """
        import hashlib
        import json

        # Serialize messages to a canonical JSON format for stable hashing
        message_data = []
        for msg in messages:
            msg_dict = {
                "role": msg.role.value if hasattr(msg.role, "value") else str(msg.role),
                "content": extract_text_content(msg.content),
            }
            if msg.name:
                msg_dict["name"] = msg.name
            message_data.append(msg_dict)

        # Create stable JSON string
        message_json = json.dumps(message_data, sort_keys=True, separators=(",", ":"))

        # Generate hash
        return hashlib.sha256(message_json.encode()).hexdigest()

    def _check_cache_hit(self, prompt_hash: str, token_count: int) -> tuple[bool, int]:
        """
        Check if prompt is in cache and return cache hit info.

        Args:
            prompt_hash: Hash of the prompt messages
            token_count: Total token count of the prompt

        Returns:
            Tuple of (is_hit, cached_tokens)
        """
        current_time = time.time()

        # Check if hash exists and is recent (within 5 minutes)
        if prompt_hash in self._prompt_cache:
            cached_tokens, timestamp = self._prompt_cache[prompt_hash]
            if current_time - timestamp < 300:  # 5 minutes
                # Cache hit! Round cached tokens to 128 increments (per OpenAI spec)
                cached_tokens_rounded = (cached_tokens // 128) * 128
                return True, cached_tokens_rounded

        # Cache miss - add to cache
        self._prompt_cache[prompt_hash] = (token_count, current_time)

        # Clean old entries (keep last 100)
        if len(self._prompt_cache) > 100:
            # Sort by timestamp and keep most recent 100
            sorted_items = sorted(
                self._prompt_cache.items(), key=lambda x: x[1][1], reverse=True
            )
            self._prompt_cache = dict(sorted_items[:100])

        return False, 0
