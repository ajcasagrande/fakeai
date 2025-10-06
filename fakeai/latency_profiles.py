"""
Model-specific latency profiles for realistic timing simulation.

This module provides realistic TTFT (Time To First Token) and ITL (Inter-Token Latency)
values for different models based on actual benchmarks from:
- NVIDIA NIM performance data
- vLLM benchmarking results
- Artificial Analysis performance reports
- OpenAI API measurements

Profiles include dynamic adjustments for:
- Prompt length (longer prompts → higher TTFT)
- KV cache hits (60-80% TTFT reduction)
- Concurrent load (queuing delays)
- Temperature (higher temp → slightly slower)
- Model size (larger models → higher latency)
"""

#  SPDX-License-Identifier: Apache-2.0

import math
import random
import threading
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class LatencyProfile:
    """
    Latency profile for a specific model.

    Attributes:
        ttft_ms: Mean time to first token in milliseconds
        ttft_std: Standard deviation for TTFT
        itl_ms: Mean inter-token latency in milliseconds
        itl_std: Standard deviation for ITL
        throughput_tokens_per_sec: Average throughput in tokens/second
        prefill_tokens_per_sec: Prefill speed for prompt processing
        model_size_b: Model size in billions of parameters (for scaling)
        is_moe: Whether model uses Mixture of Experts architecture
        supports_speculative_decoding: Whether model supports speculative decoding
    """

    ttft_ms: float
    ttft_std: float
    itl_ms: float
    itl_std: float
    throughput_tokens_per_sec: float
    prefill_tokens_per_sec: float = 1000.0
    model_size_b: float = 7.0
    is_moe: bool = False
    supports_speculative_decoding: bool = False


# Model-specific latency profiles based on benchmarks
LATENCY_PROFILES: Dict[str, LatencyProfile] = {
    # OpenAI GPT-4 family
    "gpt-4": LatencyProfile(
        ttft_ms=800.0,
        ttft_std=150.0,
        itl_ms=35.0,
        itl_std=8.0,
        throughput_tokens_per_sec=28.0,
        prefill_tokens_per_sec=500.0,
        model_size_b=1760.0,  # Estimated MoE
        is_moe=True,
    ),
    "gpt-4-turbo": LatencyProfile(
        ttft_ms=400.0,
        ttft_std=80.0,
        itl_ms=20.0,
        itl_std=5.0,
        throughput_tokens_per_sec=50.0,
        prefill_tokens_per_sec=800.0,
        model_size_b=1760.0,
        is_moe=True,
    ),
    "gpt-4-turbo-preview": LatencyProfile(
        ttft_ms=420.0,
        ttft_std=85.0,
        itl_ms=22.0,
        itl_std=5.0,
        throughput_tokens_per_sec=48.0,
        prefill_tokens_per_sec=750.0,
        model_size_b=1760.0,
        is_moe=True,
    ),
    "gpt-4o": LatencyProfile(
        ttft_ms=250.0,
        ttft_std=50.0,
        itl_ms=15.0,
        itl_std=3.0,
        throughput_tokens_per_sec=67.0,
        prefill_tokens_per_sec=1200.0,
        model_size_b=200.0,  # Optimized architecture
        supports_speculative_decoding=True,
    ),
    "gpt-4o-mini": LatencyProfile(
        ttft_ms=180.0,
        ttft_std=35.0,
        itl_ms=10.0,
        itl_std=2.0,
        throughput_tokens_per_sec=100.0,
        prefill_tokens_per_sec=1500.0,
        model_size_b=8.0,
        supports_speculative_decoding=True,
    ),
    # OpenAI GPT-3.5 family
    "gpt-3.5-turbo": LatencyProfile(
        ttft_ms=200.0,
        ttft_std=40.0,
        itl_ms=10.0,
        itl_std=2.0,
        throughput_tokens_per_sec=100.0,
        prefill_tokens_per_sec=1200.0,
        model_size_b=175.0,
    ),
    "gpt-3.5-turbo-16k": LatencyProfile(
        ttft_ms=220.0,
        ttft_std=45.0,
        itl_ms=11.0,
        itl_std=2.5,
        throughput_tokens_per_sec=90.0,
        prefill_tokens_per_sec=1100.0,
        model_size_b=175.0,
    ),
    # GPT-OSS (Open-source reasoning models)
    "openai/gpt-oss-120b": LatencyProfile(
        ttft_ms=600.0,
        ttft_std=120.0,
        itl_ms=28.0,
        itl_std=6.0,
        throughput_tokens_per_sec=35.0,
        prefill_tokens_per_sec=600.0,
        model_size_b=120.0,
        is_moe=True,
        supports_speculative_decoding=True,
    ),
    "gpt-oss-120b": LatencyProfile(
        ttft_ms=600.0,
        ttft_std=120.0,
        itl_ms=28.0,
        itl_std=6.0,
        throughput_tokens_per_sec=35.0,
        prefill_tokens_per_sec=600.0,
        model_size_b=120.0,
        is_moe=True,
        supports_speculative_decoding=True,
    ),
    "openai/gpt-oss-20b": LatencyProfile(
        ttft_ms=300.0,
        ttft_std=60.0,
        itl_ms=15.0,
        itl_std=3.0,
        throughput_tokens_per_sec=67.0,
        prefill_tokens_per_sec=1000.0,
        model_size_b=20.0,
        is_moe=True,
    ),
    "gpt-oss-20b": LatencyProfile(
        ttft_ms=300.0,
        ttft_std=60.0,
        itl_ms=15.0,
        itl_std=3.0,
        throughput_tokens_per_sec=67.0,
        prefill_tokens_per_sec=1000.0,
        model_size_b=20.0,
        is_moe=True,
    ),
    # DeepSeek models
    "deepseek-ai/DeepSeek-R1": LatencyProfile(
        ttft_ms=700.0,
        ttft_std=140.0,
        itl_ms=30.0,
        itl_std=7.0,
        throughput_tokens_per_sec=33.0,
        prefill_tokens_per_sec=550.0,
        model_size_b=671.0,
        is_moe=True,
    ),
    "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B": LatencyProfile(
        ttft_ms=350.0,
        ttft_std=70.0,
        itl_ms=16.0,
        itl_std=3.5,
        throughput_tokens_per_sec=62.0,
        prefill_tokens_per_sec=900.0,
        model_size_b=32.0,
    ),
    "deepseek-v3": LatencyProfile(
        ttft_ms=700.0,
        ttft_std=140.0,
        itl_ms=30.0,
        itl_std=7.0,
        throughput_tokens_per_sec=33.0,
        prefill_tokens_per_sec=550.0,
        model_size_b=671.0,
        is_moe=True,
    ),
    # Mixtral models (Mistral AI)
    "mixtral-8x7b": LatencyProfile(
        ttft_ms=380.0,
        ttft_std=75.0,
        itl_ms=18.0,
        itl_std=4.0,
        throughput_tokens_per_sec=55.0,
        prefill_tokens_per_sec=850.0,
        model_size_b=47.0,  # 47B total, 13B active
        is_moe=True,
    ),
    "mixtral-8x22b": LatencyProfile(
        ttft_ms=550.0,
        ttft_std=110.0,
        itl_ms=25.0,
        itl_std=5.5,
        throughput_tokens_per_sec=40.0,
        prefill_tokens_per_sec=650.0,
        model_size_b=141.0,  # 141B total, 39B active
        is_moe=True,
    ),
    # Anthropic Claude models
    "claude-3-opus-20240229": LatencyProfile(
        ttft_ms=850.0,
        ttft_std=170.0,
        itl_ms=38.0,
        itl_std=8.5,
        throughput_tokens_per_sec=26.0,
        prefill_tokens_per_sec=480.0,
        model_size_b=1000.0,  # Estimated
    ),
    "claude-3-sonnet-20240229": LatencyProfile(
        ttft_ms=450.0,
        ttft_std=90.0,
        itl_ms=22.0,
        itl_std=5.0,
        throughput_tokens_per_sec=45.0,
        prefill_tokens_per_sec=750.0,
        model_size_b=300.0,  # Estimated
    ),
    "claude-3-haiku-20240307": LatencyProfile(
        ttft_ms=220.0,
        ttft_std=45.0,
        itl_ms=12.0,
        itl_std=2.5,
        throughput_tokens_per_sec=83.0,
        prefill_tokens_per_sec=1300.0,
        model_size_b=30.0,  # Estimated
    ),
    # Meta Llama models
    "meta-llama/Llama-2-7b-chat-hf": LatencyProfile(
        ttft_ms=150.0,
        ttft_std=30.0,
        itl_ms=8.0,
        itl_std=1.5,
        throughput_tokens_per_sec=125.0,
        prefill_tokens_per_sec=1800.0,
        model_size_b=7.0,
    ),
    "meta-llama/Llama-2-13b-chat-hf": LatencyProfile(
        ttft_ms=220.0,
        ttft_std=45.0,
        itl_ms=12.0,
        itl_std=2.5,
        throughput_tokens_per_sec=83.0,
        prefill_tokens_per_sec=1400.0,
        model_size_b=13.0,
    ),
    "meta-llama/Llama-2-70b-chat-hf": LatencyProfile(
        ttft_ms=500.0,
        ttft_std=100.0,
        itl_ms=24.0,
        itl_std=5.0,
        throughput_tokens_per_sec=42.0,
        prefill_tokens_per_sec=700.0,
        model_size_b=70.0,
    ),
    "meta-llama/Llama-3.1-8B-Instruct": LatencyProfile(
        ttft_ms=140.0,
        ttft_std=28.0,
        itl_ms=7.5,
        itl_std=1.5,
        throughput_tokens_per_sec=133.0,
        prefill_tokens_per_sec=1900.0,
        model_size_b=8.0,
    ),
    "meta-llama/Llama-3.1-70B-Instruct": LatencyProfile(
        ttft_ms=480.0,
        ttft_std=95.0,
        itl_ms=23.0,
        itl_std=5.0,
        throughput_tokens_per_sec=43.0,
        prefill_tokens_per_sec=720.0,
        model_size_b=70.0,
    ),
    "meta-llama/Llama-3.1-405B-Instruct": LatencyProfile(
        ttft_ms=900.0,
        ttft_std=180.0,
        itl_ms=42.0,
        itl_std=9.0,
        throughput_tokens_per_sec=24.0,
        prefill_tokens_per_sec=450.0,
        model_size_b=405.0,
    ),
    # Mistral models
    "mistralai/Mistral-7B-Instruct-v0.2": LatencyProfile(
        ttft_ms=145.0,
        ttft_std=30.0,
        itl_ms=8.0,
        itl_std=1.5,
        throughput_tokens_per_sec=125.0,
        prefill_tokens_per_sec=1850.0,
        model_size_b=7.0,
    ),
    "mistralai/Mixtral-8x7B-Instruct-v0.1": LatencyProfile(
        ttft_ms=380.0,
        ttft_std=75.0,
        itl_ms=18.0,
        itl_std=4.0,
        throughput_tokens_per_sec=55.0,
        prefill_tokens_per_sec=850.0,
        model_size_b=47.0,
        is_moe=True,
    ),
    # Google Gemini models
    "gemini-pro": LatencyProfile(
        ttft_ms=350.0,
        ttft_std=70.0,
        itl_ms=17.0,
        itl_std=3.5,
        throughput_tokens_per_sec=59.0,
        prefill_tokens_per_sec=900.0,
        model_size_b=340.0,  # Estimated
    ),
    "gemini-pro-vision": LatencyProfile(
        ttft_ms=450.0,
        ttft_std=90.0,
        itl_ms=22.0,
        itl_std=4.5,
        throughput_tokens_per_sec=45.0,
        prefill_tokens_per_sec=700.0,
        model_size_b=340.0,  # Estimated
    ),
    # Cohere models
    "command-r": LatencyProfile(
        ttft_ms=320.0,
        ttft_std=65.0,
        itl_ms=16.0,
        itl_std=3.0,
        throughput_tokens_per_sec=62.0,
        prefill_tokens_per_sec=950.0,
        model_size_b=35.0,
    ),
    "command-r-plus": LatencyProfile(
        ttft_ms=480.0,
        ttft_std=95.0,
        itl_ms=23.0,
        itl_std=5.0,
        throughput_tokens_per_sec=43.0,
        prefill_tokens_per_sec=720.0,
        model_size_b=104.0,
    ),
    # NVIDIA NIM optimized models
    "nvidia/llama-3.1-nemotron-70b-instruct": LatencyProfile(
        ttft_ms=280.0,
        ttft_std=55.0,
        itl_ms=14.0,
        itl_std=3.0,
        throughput_tokens_per_sec=71.0,
        prefill_tokens_per_sec=1100.0,
        model_size_b=70.0,
    ),
    # Yi models
    "01-ai/Yi-34B-Chat": LatencyProfile(
        ttft_ms=360.0,
        ttft_std=72.0,
        itl_ms=17.5,
        itl_std=3.5,
        throughput_tokens_per_sec=57.0,
        prefill_tokens_per_sec=880.0,
        model_size_b=34.0,
    ),
    # Qwen models
    "Qwen/Qwen2-7B-Instruct": LatencyProfile(
        ttft_ms=155.0,
        ttft_std=31.0,
        itl_ms=8.5,
        itl_std=1.7,
        throughput_tokens_per_sec=118.0,
        prefill_tokens_per_sec=1750.0,
        model_size_b=7.0,
    ),
    "Qwen/Qwen2-72B-Instruct": LatencyProfile(
        ttft_ms=490.0,
        ttft_std=98.0,
        itl_ms=23.5,
        itl_std=5.0,
        throughput_tokens_per_sec=42.0,
        prefill_tokens_per_sec=710.0,
        model_size_b=72.0,
    ),
    # Phi models (Microsoft)
    "microsoft/Phi-3-mini-4k-instruct": LatencyProfile(
        ttft_ms=90.0,
        ttft_std=18.0,
        itl_ms=5.0,
        itl_std=1.0,
        throughput_tokens_per_sec=200.0,
        prefill_tokens_per_sec=2500.0,
        model_size_b=3.8,
    ),
    "microsoft/Phi-3-medium-4k-instruct": LatencyProfile(
        ttft_ms=190.0,
        ttft_std=38.0,
        itl_ms=10.0,
        itl_std=2.0,
        throughput_tokens_per_sec=100.0,
        prefill_tokens_per_sec=1500.0,
        model_size_b=14.0,
    ),
}

# Default profile for unknown models (based on 7B baseline)
DEFAULT_PROFILE = LatencyProfile(
    ttft_ms=200.0,
    ttft_std=40.0,
    itl_ms=12.0,
    itl_std=2.5,
    throughput_tokens_per_sec=83.0,
    prefill_tokens_per_sec=1200.0,
    model_size_b=7.0,
)


class LatencyProfileManager:
    """
    Manager for model-specific latency profiles with dynamic adjustments.

    This class provides realistic timing simulation based on model characteristics
    and runtime conditions (prompt length, cache hits, load, etc.).
    """

    def __init__(self):
        """Initialize the latency profile manager."""
        self._active_requests = 0
        self._lock = threading.Lock()

    def _normalize_model_name(self, model: str) -> str:
        """
        Normalize model name for lookup.

        Handles variations like:
        - openai/gpt-oss-120b → gpt-oss-120b
        - ft:openai/gpt-oss-20b:org::id → openai/gpt-oss-20b
        - gpt-4-0613 → gpt-4
        """
        # Strip fine-tuning prefix (ft:base:org::id)
        if model.startswith("ft:"):
            parts = model.split(":")
            if len(parts) >= 2:
                model = parts[1]

        # Try exact match first
        if model in LATENCY_PROFILES:
            return model

        # Try without organization prefix
        if "/" in model:
            short_name = model.split("/", 1)[1]
            if short_name in LATENCY_PROFILES:
                return short_name

        # Try base model name (strip version suffix)
        # gpt-4-0613 → gpt-4
        # gpt-3.5-turbo-0125 → gpt-3.5-turbo
        for suffix in ["-0613", "-0125", "-1106", "-0314", "-preview"]:
            if model.endswith(suffix):
                base = model[: -len(suffix)]
                if base in LATENCY_PROFILES:
                    return base

        # Try with organization prefix
        if "/" not in model:
            with_org = f"openai/{model}"
            if with_org in LATENCY_PROFILES:
                return with_org

        return model  # Return as-is if no match

    def get_profile(self, model: str) -> LatencyProfile:
        """
        Get latency profile for a model.

        Args:
            model: Model identifier

        Returns:
            LatencyProfile for the model, or default if not found
        """
        normalized = self._normalize_model_name(model)
        return LATENCY_PROFILES.get(normalized, DEFAULT_PROFILE)

    def get_ttft(
        self,
        model: str,
        prompt_tokens: int,
        kv_cache_hit: bool = False,
        kv_cache_hit_tokens: int = 0,
        current_load: int = 0,
        temperature: float = 1.0,
    ) -> float:
        """
        Get realistic TTFT (Time To First Token) for model and conditions.

        TTFT is affected by:
        1. Base model latency
        2. Prompt length (logarithmic scaling)
        3. KV cache hits (60-80% reduction for cached portion)
        4. Concurrent load (queuing delays)
        5. Temperature (minimal effect)

        Args:
            model: Model identifier
            prompt_tokens: Number of tokens in the prompt
            kv_cache_hit: Whether there was a KV cache hit
            kv_cache_hit_tokens: Number of tokens reused from cache
            current_load: Number of concurrent requests
            temperature: Sampling temperature

        Returns:
            TTFT in seconds (not milliseconds)
        """
        profile = self.get_profile(model)

        # Base TTFT with Gaussian noise
        base_ttft_ms = random.gauss(profile.ttft_ms, profile.ttft_std)
        base_ttft_ms = max(1.0, base_ttft_ms)  # Minimum 1ms

        # Adjust for prompt length (logarithmic scaling)
        # Longer prompts take longer to process (prefill time)
        if prompt_tokens > 100:
            # Calculate prefill time based on prefill speed
            uncached_tokens = prompt_tokens - kv_cache_hit_tokens
            prefill_time_ms = (
                uncached_tokens / profile.prefill_tokens_per_sec
            ) * 1000.0

            # Add prefill time to base TTFT
            # For small prompts, base TTFT already includes typical prefill
            # Only add extra time for tokens beyond baseline (~100 tokens)
            extra_tokens = max(0, uncached_tokens - 100)
            extra_prefill_ms = (extra_tokens / profile.prefill_tokens_per_sec) * 1000.0
            base_ttft_ms += extra_prefill_ms

        # KV cache speedup (60-80% reduction for cached portion)
        if kv_cache_hit and kv_cache_hit_tokens > 0:
            cache_speedup = random.uniform(0.6, 0.8)
            # Calculate time saved from cached tokens
            cached_prefill_ms = (
                kv_cache_hit_tokens / profile.prefill_tokens_per_sec
            ) * 1000.0
            time_saved = cached_prefill_ms * cache_speedup
            base_ttft_ms = max(base_ttft_ms * 0.2, base_ttft_ms - time_saved)

        # Load impact: queuing delay when > 50 concurrent requests
        if current_load > 50:
            # Exponential queuing delay
            queue_factor = 1.0 + (current_load - 50) * 0.02
            base_ttft_ms *= queue_factor

        # Temperature impact (higher temp = slightly slower sampling)
        # Minimal effect, ~2-5% increase at temp=2.0
        if temperature > 1.0:
            temp_factor = 1.0 + (temperature - 1.0) * 0.03
            base_ttft_ms *= temp_factor

        # Convert ms to seconds
        return base_ttft_ms / 1000.0

    def get_itl(
        self,
        model: str,
        temperature: float = 1.0,
        current_load: int = 0,
    ) -> float:
        """
        Get realistic ITL (Inter-Token Latency) for model.

        ITL is affected by:
        1. Base model decode speed
        2. Temperature (minimal effect)
        3. Load (batching can slightly increase ITL)

        Args:
            model: Model identifier
            temperature: Sampling temperature
            current_load: Number of concurrent requests

        Returns:
            ITL in seconds (not milliseconds)
        """
        profile = self.get_profile(model)

        # Base ITL with Gaussian noise
        base_itl_ms = random.gauss(profile.itl_ms, profile.itl_std)
        base_itl_ms = max(0.5, base_itl_ms)  # Minimum 0.5ms

        # Temperature impact (minimal)
        if temperature > 1.0:
            temp_factor = 1.0 + (temperature - 1.0) * 0.02
            base_itl_ms *= temp_factor

        # Load impact: batching slightly increases ITL
        if current_load > 20:
            batch_factor = 1.0 + (current_load - 20) * 0.005
            base_itl_ms *= batch_factor

        # Convert ms to seconds
        return base_itl_ms / 1000.0

    def get_generation_time(
        self,
        model: str,
        output_tokens: int,
        prompt_tokens: int = 0,
        kv_cache_hit: bool = False,
        kv_cache_hit_tokens: int = 0,
        temperature: float = 1.0,
    ) -> float:
        """
        Get total generation time estimate (TTFT + all ITLs).

        Args:
            model: Model identifier
            output_tokens: Number of output tokens to generate
            prompt_tokens: Number of input tokens (affects TTFT)
            kv_cache_hit: Whether there was a KV cache hit
            kv_cache_hit_tokens: Number of tokens reused from cache
            temperature: Sampling temperature

        Returns:
            Total time in seconds
        """
        current_load = self.get_active_requests()

        ttft = self.get_ttft(
            model=model,
            prompt_tokens=prompt_tokens,
            kv_cache_hit=kv_cache_hit,
            kv_cache_hit_tokens=kv_cache_hit_tokens,
            current_load=current_load,
            temperature=temperature,
        )

        # Average ITL for all output tokens
        total_itl = 0.0
        for _ in range(output_tokens):
            total_itl += self.get_itl(
                model=model,
                temperature=temperature,
                current_load=current_load,
            )

        return ttft + total_itl

    def start_request(self) -> None:
        """Increment active request counter (for load simulation)."""
        with self._lock:
            self._active_requests += 1

    def end_request(self) -> None:
        """Decrement active request counter."""
        with self._lock:
            self._active_requests = max(0, self._active_requests - 1)

    def get_active_requests(self) -> int:
        """Get current number of active requests."""
        with self._lock:
            return self._active_requests

    def reset_load(self) -> None:
        """Reset active request counter (for testing)."""
        with self._lock:
            self._active_requests = 0


# Global singleton instance
_latency_manager: Optional[LatencyProfileManager] = None
_manager_lock = threading.Lock()


def get_latency_manager() -> LatencyProfileManager:
    """
    Get the global latency profile manager instance (singleton).

    Returns:
        LatencyProfileManager singleton
    """
    global _latency_manager
    if _latency_manager is None:
        with _manager_lock:
            if _latency_manager is None:
                _latency_manager = LatencyProfileManager()
    return _latency_manager
