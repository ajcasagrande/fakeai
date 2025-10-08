#!/usr/bin/env python3
"""
FakeAI Per-Model Metrics Tracking

This module provides per-model metrics tracking with multi-dimensional analysis,
cost estimation, model comparison, and Prometheus export capabilities.
"""
#  SPDX-License-Identifier: Apache-2.0

import logging
import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)

# OpenAI-based pricing per 1K tokens (input/output)
MODEL_PRICING = {
    # GPT-OSS models (open-source)
    "openai/gpt-oss-120b": {"input": 0.01, "output": 0.03},
    "openai/gpt-oss-20b": {"input": 0.003, "output": 0.009},
    "gpt-oss-120b": {"input": 0.01, "output": 0.03},
    "gpt-oss-20b": {"input": 0.003, "output": 0.009},
    # GPT-4 family
    "gpt-4": {"input": 0.03, "output": 0.06},
    "gpt-4-0314": {"input": 0.03, "output": 0.06},
    "gpt-4-0613": {"input": 0.03, "output": 0.06},
    "gpt-4-32k": {"input": 0.06, "output": 0.12},
    "gpt-4-32k-0314": {"input": 0.06, "output": 0.12},
    "gpt-4-32k-0613": {"input": 0.06, "output": 0.12},
    "gpt-4-turbo": {"input": 0.01, "output": 0.03},
    "gpt-4-turbo-preview": {"input": 0.01, "output": 0.03},
    "gpt-4-turbo-2024-04-09": {"input": 0.01, "output": 0.03},
    "gpt-4-1106-preview": {"input": 0.01, "output": 0.03},
    "gpt-4-0125-preview": {"input": 0.01, "output": 0.03},
    "gpt-4-vision-preview": {"input": 0.01, "output": 0.03},
    "gpt-4o": {"input": 0.005, "output": 0.015},
    "gpt-4o-2024-05-13": {"input": 0.005, "output": 0.015},
    "gpt-4o-2024-08-06": {"input": 0.0025, "output": 0.01},
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
    "gpt-4o-mini-2024-07-18": {"input": 0.00015, "output": 0.0006},
    # GPT-3.5 family
    "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
    "gpt-3.5-turbo-0301": {"input": 0.0015, "output": 0.002},
    "gpt-3.5-turbo-0613": {"input": 0.0015, "output": 0.002},
    "gpt-3.5-turbo-1106": {"input": 0.001, "output": 0.002},
    "gpt-3.5-turbo-0125": {"input": 0.0005, "output": 0.0015},
    "gpt-3.5-turbo-16k": {"input": 0.003, "output": 0.004},
    "gpt-3.5-turbo-16k-0613": {"input": 0.003, "output": 0.004},
    "gpt-3.5-turbo-instruct": {"input": 0.0015, "output": 0.002},
    # DeepSeek models (reasoning)
    "deepseek-ai/DeepSeek-R1": {"input": 0.014, "output": 0.028},
    "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B": {"input": 0.006, "output": 0.012},
    "deepseek-v3": {"input": 0.027, "output": 0.11},
    # Mixtral models (MoE)
    "mixtral-8x7b": {"input": 0.0007, "output": 0.0007},
    "mixtral-8x22b": {"input": 0.002, "output": 0.006},
    # Claude models (Anthropic)
    "claude-3-opus-20240229": {"input": 0.015, "output": 0.075},
    "claude-3-sonnet-20240229": {"input": 0.003, "output": 0.015},
    "claude-3-haiku-20240307": {"input": 0.00025, "output": 0.00125},
    "claude-3-5-sonnet-20240620": {"input": 0.003, "output": 0.015},
    "claude-3-5-haiku-20241022": {"input": 0.001, "output": 0.005},
    # Embedding models
    "text-embedding-ada-002": {"input": 0.0001, "output": 0.0},
    "text-embedding-3-small": {"input": 0.00002, "output": 0.0},
    "text-embedding-3-large": {"input": 0.00013, "output": 0.0},
    # Llama models
    "meta-llama/Llama-3.1-70B-Instruct": {"input": 0.0009, "output": 0.0009},
    "meta-llama/Llama-3.1-8B-Instruct": {"input": 0.0002, "output": 0.0002},
    # Image models
    "dall-e-3": {"input": 0.04, "output": 0.08},  # per image (1024x1024)
    "dall-e-2": {"input": 0.02, "output": 0.02},  # per image (1024x1024)
    # Audio models
    "tts-1": {"input": 0.015, "output": 0.0},  # per 1K characters
    "tts-1-hd": {"input": 0.03, "output": 0.0},  # per 1K characters
    "whisper-1": {"input": 0.006, "output": 0.0},  # per minute
}

# Default pricing for unknown models
DEFAULT_PRICING = {"input": 0.001, "output": 0.002}


@dataclass
class ModelStats:
    """Statistics for a single model."""

    model: str
    request_count: int = 0
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    total_tokens: int = 0
    total_latency_ms: float = 0.0
    error_count: int = 0

    # Latency tracking (for percentiles)
    latencies: list[float] = field(default_factory=list)

    # Endpoint breakdown
    endpoint_requests: dict[str, int] = field(
        default_factory=lambda: defaultdict(int))

    # User/API key breakdown
    user_requests: dict[str, int] = field(
        default_factory=lambda: defaultdict(int))
    user_tokens: dict[str, int] = field(
        default_factory=lambda: defaultdict(int))

    # Time series tracking (timestamp -> count)
    request_timeline: list[tuple[float, int]] = field(default_factory=list)

    # First and last request times
    first_request_time: float | None = None
    last_request_time: float | None = None

    def add_request(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        latency_ms: float,
        endpoint: str | None = None,
        user: str | None = None,
        error: bool = False,
    ):
        """Add a request to the stats."""
        current_time = time.time()

        self.request_count += 1
        self.total_prompt_tokens += prompt_tokens
        self.total_completion_tokens += completion_tokens
        self.total_tokens += prompt_tokens + completion_tokens
        self.total_latency_ms += latency_ms

        if latency_ms > 0:
            self.latencies.append(latency_ms)

        if error:
            self.error_count += 1

        if endpoint:
            self.endpoint_requests[endpoint] += 1

        if user:
            self.user_requests[user] += 1
            self.user_tokens[user] += prompt_tokens + completion_tokens

        self.request_timeline.append((current_time, 1))

        if self.first_request_time is None:
            self.first_request_time = current_time
        self.last_request_time = current_time

    def get_avg_latency_ms(self) -> float:
        """Get average latency in milliseconds."""
        if self.request_count == 0:
            return 0.0
        return self.total_latency_ms / self.request_count

    def get_error_rate(self) -> float:
        """Get error rate as percentage."""
        if self.request_count == 0:
            return 0.0
        return (self.error_count / self.request_count) * 100

    def get_latency_percentiles(self) -> dict[str, float]:
        """Get latency percentiles."""
        if not self.latencies:
            return {"p50": 0.0, "p90": 0.0, "p95": 0.0, "p99": 0.0}

        latencies_array = np.array(self.latencies)
        return {
            "p50": float(np.percentile(latencies_array, 50)),
            "p90": float(np.percentile(latencies_array, 90)),
            "p95": float(np.percentile(latencies_array, 95)),
            "p99": float(np.percentile(latencies_array, 99)),
        }

    def calculate_cost(self) -> float:
        """Calculate estimated cost for this model."""
        pricing = MODEL_PRICING.get(self.model, DEFAULT_PRICING)

        # Cost per 1K tokens
        input_cost = (self.total_prompt_tokens / 1000) * pricing["input"]
        output_cost = (self.total_completion_tokens / 1000) * pricing["output"]

        return input_cost + output_cost

    def get_uptime_seconds(self) -> float:
        """Get uptime in seconds (time between first and last request)."""
        if self.first_request_time is None or self.last_request_time is None:
            return 0.0
        return self.last_request_time - self.first_request_time


class ModelMetricsTracker:
    """
    Per-model metrics tracker with multi-dimensional analysis.

    Tracks metrics separately for each model, with breakdowns by:
    - Endpoint
    - User/API key
    - Time buckets

    Supports cost estimation, model comparison, and Prometheus export.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(
                        ModelMetricsTracker, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        # Move _initialized check inside lock to prevent TOCTOU race condition
        with self._lock:
            if self._initialized:
                return

            # Model stats storage - using dict instead of defaultdict to avoid
            # model="unknown" issue
            self._model_stats: dict[str, ModelStats] = {}

            # Multi-dimensional tracking
            # (model, endpoint) -> count
            self._model_endpoint_requests: dict[tuple[str, str], int] = defaultdict(
                int)

            # (model, user) -> count
            self._model_user_requests: dict[tuple[str, str], int] = defaultdict(
                int)

            # Time bucket tracking (hourly buckets)
            # (model, hour_timestamp) -> count
            self._model_time_requests: dict[tuple[str, int], int] = defaultdict(
                int)

            # Thread safety
            self._data_lock = threading.Lock()

            self._initialized = True
            logger.info("Model metrics tracker initialized")

    def track_request(
        self,
        model: str,
        endpoint: str,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        latency_ms: float = 0.0,
        user: str | None = None,
        error: bool = False,
    ):
        """
        Track a request for a specific model.

        Args:
            model: Model ID
            endpoint: API endpoint
            prompt_tokens: Number of input tokens
            completion_tokens: Number of output tokens
            latency_ms: Request latency in milliseconds
            user: User or API key identifier
            error: Whether the request resulted in an error
        """
        with self._data_lock:
            # Track in model stats
            if model not in self._model_stats:
                self._model_stats[model] = ModelStats(model=model)

            self._model_stats[model].add_request(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                latency_ms=latency_ms,
                endpoint=endpoint,
                user=user,
                error=error,
            )

            # Track multi-dimensional data
            self._model_endpoint_requests[(model, endpoint)] += 1

            if user:
                self._model_user_requests[(model, user)] += 1

            # Track by hour
            hour_timestamp = int(time.time() // 3600) * 3600
            self._model_time_requests[(model, hour_timestamp)] += 1

    def track_tokens(
            self,
            model: str,
            prompt_tokens: int,
            completion_tokens: int):
        """
        Track token usage for a model.

        Args:
            model: Model ID
            prompt_tokens: Number of input tokens
            completion_tokens: Number of output tokens
        """
        with self._data_lock:
            if model not in self._model_stats:
                self._model_stats[model] = ModelStats(model=model)

            self._model_stats[model].total_prompt_tokens += prompt_tokens
            self._model_stats[model].total_completion_tokens += completion_tokens
            self._model_stats[model].total_tokens += prompt_tokens + \
                completion_tokens

    def track_latency(self, model: str, latency_ms: float):
        """
        Track request latency for a model.

        Args:
            model: Model ID
            latency_ms: Request latency in milliseconds
        """
        with self._data_lock:
            if model not in self._model_stats:
                self._model_stats[model] = ModelStats(model=model)

            self._model_stats[model].latencies.append(latency_ms)
            self._model_stats[model].total_latency_ms += latency_ms

    def get_model_stats(self, model: str) -> dict[str, Any]:
        """
        Get all stats for a specific model.

        Args:
            model: Model ID

        Returns:
            Dictionary containing all stats for the model
        """
        with self._data_lock:
            if model not in self._model_stats:
                return {
                    "model": model,
                    "request_count": 0,
                    "error": "Model not found",
                }

            stats = self._model_stats[model]

            return {
                "model": model,
                "request_count": stats.request_count,
                "tokens": {
                    "prompt": stats.total_prompt_tokens,
                    "completion": stats.total_completion_tokens,
                    "total": stats.total_tokens,
                },
                "latency": {
                    "avg_ms": stats.get_avg_latency_ms(),
                    **stats.get_latency_percentiles(),
                },
                "errors": {
                    "count": stats.error_count,
                    "rate_percent": stats.get_error_rate(),
                },
                "cost": {
                    "total_usd": stats.calculate_cost(),
                    "per_request_usd": (
                        stats.calculate_cost() / stats.request_count
                        if stats.request_count > 0
                        else 0.0
                    ),
                },
                "endpoints": dict(stats.endpoint_requests),
                "users": dict(stats.user_requests),
                "uptime_seconds": stats.get_uptime_seconds(),
                "first_request": stats.first_request_time,
                "last_request": stats.last_request_time,
            }

    def get_all_models_stats(self) -> dict[str, dict[str, Any]]:
        """
        Get stats for all models.

        Returns:
            Dictionary mapping model ID to stats
        """
        with self._data_lock:
            return {model: self.get_model_stats(
                model) for model in self._model_stats.keys()}

    def compare_models(self, model1: str, model2: str) -> dict[str, Any]:
        """
        Compare two models side-by-side.

        Args:
            model1: First model ID
            model2: Second model ID

        Returns:
            Dictionary containing comparison metrics
        """
        stats1 = self.get_model_stats(model1)
        stats2 = self.get_model_stats(model2)

        if "error" in stats1 or "error" in stats2:
            return {
                "error": "One or both models not found",
                "model1": model1,
                "model2": model2,
            }

        # Calculate deltas and percentages
        def calc_delta(val1: float, val2: float) -> dict[str, float]:
            delta = val2 - val1
            percent = ((val2 - val1) / val1 * 100) if val1 > 0 else 0.0
            return {"delta": delta, "percent_change": percent}

        return {
            "model1": model1,
            "model2": model2,
            "comparison": {
                "request_count": {
                    "model1": stats1["request_count"],
                    "model2": stats2["request_count"],
                    **calc_delta(stats1["request_count"], stats2["request_count"]),
                },
                "avg_latency_ms": {
                    "model1": stats1["latency"]["avg_ms"],
                    "model2": stats2["latency"]["avg_ms"],
                    **calc_delta(
                        stats1["latency"]["avg_ms"], stats2["latency"]["avg_ms"]
                    ),
                },
                "error_rate_percent": {
                    "model1": stats1["errors"]["rate_percent"],
                    "model2": stats2["errors"]["rate_percent"],
                    **calc_delta(
                        stats1["errors"]["rate_percent"],
                        stats2["errors"]["rate_percent"],
                    ),
                },
                "total_cost_usd": {
                    "model1": stats1["cost"]["total_usd"],
                    "model2": stats2["cost"]["total_usd"],
                    **calc_delta(
                        stats1["cost"]["total_usd"], stats2["cost"]["total_usd"]
                    ),
                },
                "cost_per_request_usd": {
                    "model1": stats1["cost"]["per_request_usd"],
                    "model2": stats2["cost"]["per_request_usd"],
                    **calc_delta(
                        stats1["cost"]["per_request_usd"],
                        stats2["cost"]["per_request_usd"],
                    ),
                },
                "total_tokens": {
                    "model1": stats1["tokens"]["total"],
                    "model2": stats2["tokens"]["total"],
                    **calc_delta(stats1["tokens"]["total"], stats2["tokens"]["total"]),
                },
            },
            "winner": {
                "latency": (
                    model1
                    if stats1["latency"]["avg_ms"] < stats2["latency"]["avg_ms"]
                    else model2
                ),
                "error_rate": (
                    model1
                    if stats1["errors"]["rate_percent"] <
                    stats2["errors"]["rate_percent"]
                    else model2
                ),
                "cost_efficiency": (
                    model1
                    if stats1["cost"]["per_request_usd"] <
                    stats2["cost"]["per_request_usd"]
                    else model2
                ),
            },
        }

    def get_cost_by_model(self) -> dict[str, float]:
        """
        Get estimated cost per model.

        Returns:
            Dictionary mapping model ID to total cost in USD
        """
        with self._data_lock:
            return {
                model: stats.calculate_cost()
                for model, stats in self._model_stats.items()
            }

    def get_model_ranking(
        self, metric: str = "request_count", limit: int = 10
    ) -> list[dict[str, Any]]:
        """
        Get top models ranked by a specific metric.

        Args:
            metric: Metric to rank by (request_count, latency, error_rate, cost)
            limit: Maximum number of models to return

        Returns:
            List of models with their stats, sorted by the metric
        """
        all_stats = self.get_all_models_stats()

        # Define sorting keys
        sort_keys = {
            "request_count": lambda s: s["request_count"],
            "latency": lambda s: s["latency"]["avg_ms"],
            "error_rate": lambda s: s["errors"]["rate_percent"],
            "cost": lambda s: s["cost"]["total_usd"],
            "tokens": lambda s: s["tokens"]["total"],
        }

        if metric not in sort_keys:
            logger.warning(
                f"Unknown metric '{metric}', defaulting to 'request_count'")
            metric = "request_count"

        sorted_models = sorted(
            all_stats.values(),
            key=sort_keys[metric],
            reverse=True)

        return sorted_models[:limit]

    def get_prometheus_metrics(self) -> str:
        """
        Export metrics in Prometheus format with model labels.

        Returns:
            String containing Prometheus-formatted metrics
        """
        lines = []

        with self._data_lock:
            # Request count by model
            lines.append(
                "# HELP fakeai_model_requests_total Total requests per model")
            lines.append("# TYPE fakeai_model_requests_total counter")
            for model, stats in self._model_stats.items():
                lines.append(
                    f'fakeai_model_requests_total{{model="{model}"}} {stats.request_count}'
                )

            # Token usage by model
            lines.append(
                "# HELP fakeai_model_tokens_total Total tokens per model")
            lines.append("# TYPE fakeai_model_tokens_total counter")
            for model, stats in self._model_stats.items():
                lines.append(
                    f'fakeai_model_tokens_total{{model="{model}",type="prompt"}} {stats.total_prompt_tokens}'
                )
                lines.append(
                    f'fakeai_model_tokens_total{{model="{model}",type="completion"}} {stats.total_completion_tokens}'
                )

            # Latency by model
            lines.append(
                "# HELP fakeai_model_latency_milliseconds Request latency per model"
            )
            lines.append("# TYPE fakeai_model_latency_milliseconds summary")
            for model, stats in self._model_stats.items():
                percentiles = stats.get_latency_percentiles()
                if stats.request_count > 0:
                    lines.append(
                        f'fakeai_model_latency_milliseconds{{model="{model}",quantile="0.5"}} {percentiles["p50"]:.2f}'
                    )
                    lines.append(
                        f'fakeai_model_latency_milliseconds{{model="{model}",quantile="0.9"}} {percentiles["p90"]:.2f}'
                    )
                    lines.append(
                        f'fakeai_model_latency_milliseconds{{model="{model}",quantile="0.95"}} {percentiles["p95"]:.2f}'
                    )
                    lines.append(
                        f'fakeai_model_latency_milliseconds{{model="{model}",quantile="0.99"}} {percentiles["p99"]:.2f}'
                    )
                    lines.append(
                        f'fakeai_model_latency_milliseconds_sum{{model="{model}"}} {stats.total_latency_ms:.2f}'
                    )
                    lines.append(
                        f'fakeai_model_latency_milliseconds_count{{model="{model}"}} {stats.request_count}'
                    )

            # Error rate by model
            lines.append(
                "# HELP fakeai_model_errors_total Total errors per model")
            lines.append("# TYPE fakeai_model_errors_total counter")
            for model, stats in self._model_stats.items():
                lines.append(
                    f'fakeai_model_errors_total{{model="{model}"}} {stats.error_count}'
                )

            # Cost by model
            lines.append(
                "# HELP fakeai_model_cost_usd_total Total estimated cost per model in USD"
            )
            lines.append("# TYPE fakeai_model_cost_usd_total gauge")
            for model, stats in self._model_stats.items():
                cost = stats.calculate_cost()
                lines.append(
                    f'fakeai_model_cost_usd_total{{model="{model}"}} {cost:.6f}'
                )

            # Model-endpoint breakdown
            lines.append(
                "# HELP fakeai_model_endpoint_requests_total Requests per model-endpoint pair"
            )
            lines.append("# TYPE fakeai_model_endpoint_requests_total counter")
            for (model, endpoint), count in self._model_endpoint_requests.items():
                lines.append(
                    f'fakeai_model_endpoint_requests_total{{model="{model}",endpoint="{endpoint}"}} {count}'
                )

        return "\n".join(lines) + "\n"

    def get_multi_dimensional_stats(self) -> dict[str, Any]:
        """
        Get multi-dimensional statistics.

        Returns:
            Dictionary containing 2D breakdowns
        """
        with self._data_lock:
            # Model x Endpoint
            model_endpoint = {}
            for (model, endpoint), count in self._model_endpoint_requests.items():
                if model not in model_endpoint:
                    model_endpoint[model] = {}
                model_endpoint[model][endpoint] = count

            # Model x User
            model_user = {}
            for (model, user), count in self._model_user_requests.items():
                if model not in model_user:
                    model_user[model] = {}
                model_user[model][user] = count

            # Model x Time (recent 24 hours)
            current_hour = int(time.time() // 3600) * 3600
            hours_24_ago = current_hour - (24 * 3600)

            model_time = {}
            for (model, hour_ts), count in self._model_time_requests.items():
                if hour_ts >= hours_24_ago:
                    if model not in model_time:
                        model_time[model] = []
                    model_time[model].append(
                        {"timestamp": hour_ts, "count": count})

            return {
                "model_by_endpoint": model_endpoint,
                "model_by_user": model_user,
                "model_by_time_24h": model_time,
            }

    def reset_stats(self):
        """Reset all statistics."""
        with self._data_lock:
            self._model_stats.clear()
            self._model_endpoint_requests.clear()
            self._model_user_requests.clear()
            self._model_time_requests.clear()
            logger.info("Model metrics reset")
