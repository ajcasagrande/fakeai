#!/usr/bin/env python3
"""
FakeAI Cost Tracking and Billing Simulation

This module provides comprehensive cost tracking and billing simulation for the FakeAI server,
including per-model pricing, budget management, cost optimization suggestions, and detailed
usage analytics.
"""
#  SPDX-License-Identifier: Apache-2.0

import logging
import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class BudgetPeriod(Enum):
    """Budget reset periods."""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    NEVER = "never"


class BudgetLimitType(Enum):
    """Budget limit enforcement types."""

    SOFT = "soft"  # Warning only, request continues
    HARD = "hard"  # Reject request if over budget


@dataclass
class ModelPricing:
    """Pricing information for a model."""

    model_id: str
    input_price_per_million: float  # USD per 1M input tokens
    output_price_per_million: float  # USD per 1M output tokens
    cached_input_price_per_million: float | None = None  # USD per 1M cached tokens


@dataclass
class ImagePricing:
    """Pricing information for image generation."""

    model: str
    size: str
    quality: str
    price: float  # USD per image


@dataclass
class AudioPricing:
    """Pricing information for audio."""

    model: str
    price_per_million_chars: float  # USD per 1M characters


@dataclass
class UsageRecord:
    """Record of API usage."""

    timestamp: float
    api_key: str
    model: str
    endpoint: str
    prompt_tokens: int
    completion_tokens: int
    cached_tokens: int = 0
    cost: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class BudgetConfig:
    """Budget configuration for an API key."""

    api_key: str
    limit: float  # USD
    period: BudgetPeriod = BudgetPeriod.MONTHLY
    limit_type: BudgetLimitType = BudgetLimitType.SOFT
    alert_threshold: float = 0.8  # Alert when 80% of budget used
    last_reset: float = field(default_factory=time.time)
    used: float = 0.0
    alerted: bool = False


@dataclass
class CostOptimizationSuggestion:
    """Cost optimization suggestion."""

    api_key: str
    suggestion_type: str
    description: str
    potential_savings: float
    details: dict[str, Any] = field(default_factory=dict)


# Real OpenAI pricing as of January 2025 (prices per 1M tokens)
MODEL_PRICING = {
    # GPT-4 models
    "gpt-4": ModelPricing("gpt-4", 30.00, 60.00),
    "gpt-4-0613": ModelPricing("gpt-4-0613", 30.00, 60.00),
    "gpt-4-32k": ModelPricing("gpt-4-32k", 60.00, 120.00),
    "gpt-4-32k-0613": ModelPricing("gpt-4-32k-0613", 60.00, 120.00),
    # GPT-4 Turbo models
    "gpt-4-turbo": ModelPricing("gpt-4-turbo", 10.00, 30.00),
    "gpt-4-turbo-preview": ModelPricing("gpt-4-turbo-preview", 10.00, 30.00),
    "gpt-4-1106-preview": ModelPricing("gpt-4-1106-preview", 10.00, 30.00),
    "gpt-4-0125-preview": ModelPricing("gpt-4-0125-preview", 10.00, 30.00),
    # GPT-4o models
    "gpt-4o": ModelPricing("gpt-4o", 5.00, 15.00, 2.50),
    "gpt-4o-2024-05-13": ModelPricing("gpt-4o-2024-05-13", 5.00, 15.00, 2.50),
    "gpt-4o-2024-08-06": ModelPricing("gpt-4o-2024-08-06", 2.50, 10.00, 1.25),
    "openai/gpt-oss-120b": ModelPricing("openai/gpt-oss-120b", 2.50, 10.00, 1.25),
    # GPT-4o mini
    "gpt-4o-mini": ModelPricing("gpt-4o-mini", 0.15, 0.60, 0.075),
    "gpt-4o-mini-2024-07-18": ModelPricing("gpt-4o-mini-2024-07-18", 0.15, 0.60, 0.075),
    "openai/gpt-oss-20b": ModelPricing("openai/gpt-oss-20b", 0.15, 0.60, 0.075),
    # GPT-3.5 Turbo
    "gpt-3.5-turbo": ModelPricing("gpt-3.5-turbo", 0.50, 1.50),
    "gpt-3.5-turbo-0125": ModelPricing("gpt-3.5-turbo-0125", 0.50, 1.50),
    "gpt-3.5-turbo-1106": ModelPricing("gpt-3.5-turbo-1106", 1.00, 2.00),
    "gpt-3.5-turbo-16k": ModelPricing("gpt-3.5-turbo-16k", 3.00, 4.00),
    # O1 models
    "o1": ModelPricing("o1", 15.00, 60.00),
    "o1-preview": ModelPricing("o1-preview", 15.00, 60.00),
    "o1-mini": ModelPricing("o1-mini", 3.00, 12.00),
    "deepseek-ai/DeepSeek-R1": ModelPricing("deepseek-ai/DeepSeek-R1", 15.00, 60.00),
    "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B": ModelPricing(
        "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B", 3.00, 12.00
    ),
    # Embeddings
    "text-embedding-3-small": ModelPricing("text-embedding-3-small", 0.02, 0.0),
    "text-embedding-3-large": ModelPricing("text-embedding-3-large", 0.13, 0.0),
    "text-embedding-ada-002": ModelPricing("text-embedding-ada-002", 0.10, 0.0),
    # Other models
    "mixtral-8x7b": ModelPricing("mixtral-8x7b", 0.50, 0.50),
    "mixtral-8x22b": ModelPricing("mixtral-8x22b", 1.00, 1.00),
    "deepseek-v3": ModelPricing("deepseek-v3", 0.27, 1.10),
}

# Image generation pricing
IMAGE_PRICING = [
    # DALL-E 3
    ImagePricing("dall-e-3", "1024x1024", "standard", 0.040),
    ImagePricing("dall-e-3", "1024x1024", "hd", 0.080),
    ImagePricing("dall-e-3", "1024x1792", "standard", 0.080),
    ImagePricing("dall-e-3", "1024x1792", "hd", 0.120),
    ImagePricing("dall-e-3", "1792x1024", "standard", 0.080),
    ImagePricing("dall-e-3", "1792x1024", "hd", 0.120),
    # DALL-E 2
    ImagePricing("dall-e-2", "1024x1024", "standard", 0.020),
    ImagePricing("dall-e-2", "512x512", "standard", 0.018),
    ImagePricing("dall-e-2", "256x256", "standard", 0.016),
]

# Audio pricing
AUDIO_PRICING = {
    "tts-1": AudioPricing("tts-1", 15.00),  # $15 per 1M chars
    "tts-1-hd": AudioPricing("tts-1-hd", 30.00),  # $30 per 1M chars
    # $6 per 1M chars (0.006 per minute)
    "whisper-1": AudioPricing("whisper-1", 6.00),
}

# Fine-tuning pricing (training cost per 1M tokens)
FINE_TUNING_PRICING = {
    "gpt-4o-2024-08-06": {"training": 25.00, "input": 3.75, "output": 15.00},
    "gpt-4o-mini-2024-07-18": {"training": 3.00, "input": 0.30, "output": 1.20},
    "gpt-3.5-turbo": {"training": 8.00, "input": 3.00, "output": 6.00},
}


class CostTracker:
    """
    Thread-safe singleton cost tracker for FakeAI.

    Tracks API costs based on token usage and pricing, manages budgets,
    and provides cost optimization suggestions.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(CostTracker, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        # Move _initialized check inside lock to prevent TOCTOU race condition
        with self._lock:
            if self._initialized:
                return

            # Usage tracking
            self._usage_records: list[UsageRecord] = []
            self._usage_lock = threading.Lock()

            # Per-key aggregated costs
            self._costs_by_key: dict[str, float] = defaultdict(float)
            self._costs_by_model: dict[str, float] = defaultdict(float)
            self._costs_by_endpoint: dict[str, float] = defaultdict(float)

            # Token tracking
            self._tokens_by_key: dict[str, dict[str, int]] = defaultdict(
                lambda: {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "cached_tokens": 0,
                    "total_tokens": 0,
                }
            )

            # Budget management
            self._budgets: dict[str, BudgetConfig] = {}
            self._budget_lock = threading.Lock()

            # Optimization tracking
            self._suggestions: list[CostOptimizationSuggestion] = []
            self._model_usage_count: dict[str, dict[str, int]] = defaultdict(
                lambda: defaultdict(int)
            )

            # Start background budget reset thread
            self._stop_thread = False
            self._budget_reset_thread = threading.Thread(
                target=self._budget_reset_loop)
            self._budget_reset_thread.daemon = True
            self._budget_reset_thread.start()

            self._initialized = True
            logger.info("Cost tracker initialized")

    def record_usage(
        self,
        api_key: str,
        model: str,
        endpoint: str,
        prompt_tokens: int,
        completion_tokens: int,
        cached_tokens: int = 0,
        metadata: dict[str, Any] | None = None,
    ) -> float:
        """
        Record API usage and return the cost.

        Args:
            api_key: API key making the request
            model: Model being used
            endpoint: API endpoint
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens
            cached_tokens: Number of cached tokens (if applicable)
            metadata: Additional metadata (e.g., image size, audio length)

        Returns:
            Cost in USD for this request
        """
        # Calculate cost
        cost = self._calculate_cost(
            model,
            endpoint,
            prompt_tokens,
            completion_tokens,
            cached_tokens,
            metadata or {},
        )

        # Record usage
        with self._usage_lock:
            record = UsageRecord(
                timestamp=time.time(),
                api_key=api_key,
                model=model,
                endpoint=endpoint,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                cached_tokens=cached_tokens,
                cost=cost,
                metadata=metadata or {},
            )
            self._usage_records.append(record)

            # Update aggregated costs
            self._costs_by_key[api_key] += cost
            self._costs_by_model[model] += cost
            self._costs_by_endpoint[endpoint] += cost

            # Update token counts
            self._tokens_by_key[api_key]["prompt_tokens"] += prompt_tokens
            self._tokens_by_key[api_key]["completion_tokens"] += completion_tokens
            self._tokens_by_key[api_key]["cached_tokens"] += cached_tokens
            self._tokens_by_key[api_key]["total_tokens"] += (
                prompt_tokens + completion_tokens
            )

            # Track model usage for optimization
            self._model_usage_count[api_key][model] += 1

        # Check budget
        self._check_budget(api_key, cost)

        # Generate optimization suggestions periodically
        if len(self._usage_records) % 100 == 0:
            self._generate_optimization_suggestions(api_key)

        return cost

    def _calculate_cost(
        self,
        model: str,
        endpoint: str,
        prompt_tokens: int,
        completion_tokens: int,
        cached_tokens: int,
        metadata: dict[str, Any],
    ) -> float:
        """Calculate cost based on usage."""
        # Handle fine-tuned models (ft:base:org::id format)
        if model.startswith("ft:"):
            parts = model.split(":")
            if len(parts) >= 2:
                base_model = parts[1]
                if base_model in FINE_TUNING_PRICING:
                    pricing = FINE_TUNING_PRICING[base_model]
                    cost = (
                        prompt_tokens / 1_000_000 * pricing["input"] +
                        completion_tokens / 1_000_000 * pricing["output"]
                    )
                    return cost

        # Image generation
        if endpoint == "/v1/images/generations":
            size = metadata.get("size", "1024x1024")
            quality = metadata.get("quality", "standard")
            n = metadata.get("n", 1)

            for pricing in IMAGE_PRICING:
                if (
                    pricing.model == model and
                    pricing.size == size and
                    pricing.quality == quality
                ):
                    return pricing.price * n

            # Default image cost
            return 0.020 * n

        # Audio
        if endpoint in ["/v1/audio/speech", "/v1/audio/transcriptions"]:
            if model in AUDIO_PRICING:
                chars = metadata.get("characters", 0)
                return chars / 1_000_000 * \
                    AUDIO_PRICING[model].price_per_million_chars
            return 0.0

        # Text/chat models
        if model in MODEL_PRICING:
            pricing = MODEL_PRICING[model]

            # Calculate input cost
            input_cost = prompt_tokens / 1_000_000 * pricing.input_price_per_million

            # Calculate cached input cost (if applicable)
            if cached_tokens > 0 and pricing.cached_input_price_per_million:
                cached_cost = (
                    cached_tokens /
                    1_000_000 *
                    pricing.cached_input_price_per_million)
                # Subtract cached tokens from regular input cost
                input_cost = (
                    (prompt_tokens - cached_tokens) /
                    1_000_000 *
                    pricing.input_price_per_million
                )
                input_cost += cached_cost

            # Calculate output cost
            output_cost = (
                completion_tokens /
                1_000_000 *
                pricing.output_price_per_million)

            return input_cost + output_cost

        # Unknown model - use GPT-3.5 turbo pricing as default
        logger.warning(
            f"Unknown model pricing for {model}, using default pricing")
        default_pricing = MODEL_PRICING["gpt-3.5-turbo"]
        return (
            prompt_tokens /
            1_000_000 *
            default_pricing.input_price_per_million +
            completion_tokens /
            1_000_000 *
            default_pricing.output_price_per_million)

    def get_cost_by_key(
        self, api_key: str, period_hours: int | None = None
    ) -> dict[str, Any]:
        """
        Get cost information for a specific API key.

        Args:
            api_key: API key to query
            period_hours: If specified, only include usage from last N hours

        Returns:
            Dictionary containing cost breakdown
        """
        with self._usage_lock:
            # Filter records by API key and time period
            cutoff_time = time.time() - (period_hours * 3600) if period_hours else 0
            records = [
                r
                for r in self._usage_records
                if r.api_key == api_key and r.timestamp >= cutoff_time
            ]

            # Get budget info if available (before early return)
            budget_info = None
            if api_key in self._budgets:
                budget = self._budgets[api_key]
                budget_info = {
                    "limit": budget.limit,
                    "used": budget.used,
                    "remaining": budget.limit - budget.used,
                    "percentage": (
                        (budget.used / budget.limit * 100) if budget.limit > 0 else 0),
                    "period": budget.period.value,
                }

            if not records:
                return {
                    "api_key": api_key,
                    "total_cost": 0.0,
                    "by_model": {},
                    "by_endpoint": {},
                    "tokens": self._tokens_by_key.get(api_key, {}),
                    "requests": 0,
                    "budget": budget_info,
                }

            # Calculate costs by model and endpoint
            costs_by_model = defaultdict(float)
            costs_by_endpoint = defaultdict(float)
            tokens_by_model = defaultdict(
                lambda: {"prompt": 0, "completion": 0, "cached": 0}
            )

            for record in records:
                costs_by_model[record.model] += record.cost
                costs_by_endpoint[record.endpoint] += record.cost
                tokens_by_model[record.model]["prompt"] += record.prompt_tokens
                tokens_by_model[record.model]["completion"] += record.completion_tokens
                tokens_by_model[record.model]["cached"] += record.cached_tokens

            total_cost = sum(costs_by_model.values())

            return {
                "api_key": api_key,
                "total_cost": total_cost,
                "by_model": dict(costs_by_model),
                "by_endpoint": dict(costs_by_endpoint),
                "tokens_by_model": dict(tokens_by_model),
                "tokens": self._tokens_by_key.get(api_key, {}),
                "requests": len(records),
                "budget": budget_info,
                "period_hours": period_hours,
            }

    def get_cost_by_model(self, period_hours: int |
                          None = None) -> dict[str, float]:
        """
        Get costs aggregated by model.

        Args:
            period_hours: If specified, only include usage from last N hours

        Returns:
            Dictionary mapping model names to costs
        """
        with self._usage_lock:
            if period_hours:
                cutoff_time = time.time() - (period_hours * 3600)
                records = [
                    r for r in self._usage_records if r.timestamp >= cutoff_time]
            else:
                records = self._usage_records

            costs = defaultdict(float)
            for record in records:
                costs[record.model] += record.cost

            return dict(costs)

    def get_cost_by_endpoint(self, period_hours: int |
                             None = None) -> dict[str, float]:
        """
        Get costs aggregated by endpoint.

        Args:
            period_hours: If specified, only include usage from last N hours

        Returns:
            Dictionary mapping endpoint names to costs
        """
        with self._usage_lock:
            if period_hours:
                cutoff_time = time.time() - (period_hours * 3600)
                records = [
                    r for r in self._usage_records if r.timestamp >= cutoff_time]
            else:
                records = self._usage_records

            costs = defaultdict(float)
            for record in records:
                costs[record.endpoint] += record.cost

            return dict(costs)

    def get_total_cost(self, period_hours: int | None = None) -> float:
        """
        Get total cost across all API keys.

        Args:
            period_hours: If specified, only include usage from last N hours

        Returns:
            Total cost in USD
        """
        costs_by_model = self.get_cost_by_model(period_hours)
        return sum(costs_by_model.values())

    def set_budget(
        self,
        api_key: str,
        limit: float,
        period: BudgetPeriod = BudgetPeriod.MONTHLY,
        limit_type: BudgetLimitType = BudgetLimitType.SOFT,
        alert_threshold: float = 0.8,
    ) -> None:
        """
        Set budget limit for an API key.

        Args:
            api_key: API key to set budget for
            limit: Budget limit in USD
            period: Budget reset period
            limit_type: SOFT (warning) or HARD (reject request)
            alert_threshold: Threshold for alert (0.0-1.0)
        """
        with self._budget_lock:
            if api_key in self._budgets:
                budget = self._budgets[api_key]
                budget.limit = limit
                budget.period = period
                budget.limit_type = limit_type
                budget.alert_threshold = alert_threshold
            else:
                self._budgets[api_key] = BudgetConfig(
                    api_key=api_key,
                    limit=limit,
                    period=period,
                    limit_type=limit_type,
                    alert_threshold=alert_threshold,
                )

        logger.info(
            f"Budget set for {api_key}: ${limit} ({
                period.value}, {
                limit_type.value})")

    def check_budget(self, api_key: str) -> tuple[float, float, bool]:
        """
        Check budget status for an API key.

        Args:
            api_key: API key to check

        Returns:
            Tuple of (used, remaining, over_limit)
        """
        with self._budget_lock:
            if api_key not in self._budgets:
                return (0.0, float("inf"), False)

            budget = self._budgets[api_key]
            used = budget.used
            remaining = budget.limit - used
            over_limit = used >= budget.limit

            return (used, remaining, over_limit)

    def _check_budget(self, api_key: str, cost: float) -> None:
        """Internal method to check and update budget after usage."""
        with self._budget_lock:
            if api_key not in self._budgets:
                return

            budget = self._budgets[api_key]
            budget.used += cost

            # Check if we've hit the alert threshold
            if (
                not budget.alerted and
                budget.used >= budget.limit * budget.alert_threshold
            ):
                budget.alerted = True
                logger.warning(
                    f"Budget alert for {api_key}: ${budget.used:.4f} / ${budget.limit:.2f} "
                    f"({budget.used / budget.limit * 100:.1f}%)"
                )

            # Check if we've exceeded the limit
            if budget.used >= budget.limit:
                if budget.limit_type == BudgetLimitType.HARD:
                    logger.error(
                        f"Budget exceeded for {api_key}: ${budget.used:.4f} / ${budget.limit:.2f}"
                    )
                else:
                    logger.warning(
                        f"Budget exceeded (soft limit) for {api_key}: ${
                            budget.used:.4f} / ${
                            budget.limit:.2f}")

    def _budget_reset_loop(self) -> None:
        """Background thread to reset budgets periodically."""
        while not self._stop_thread:
            time.sleep(3600)  # Check every hour
            self._reset_budgets()

    def _reset_budgets(self) -> None:
        """Reset budgets that have exceeded their period."""
        current_time = time.time()

        with self._budget_lock:
            for api_key, budget in self._budgets.items():
                should_reset = False

                if budget.period == BudgetPeriod.DAILY:
                    should_reset = current_time - budget.last_reset >= 86400
                elif budget.period == BudgetPeriod.WEEKLY:
                    should_reset = current_time - budget.last_reset >= 604800
                elif budget.period == BudgetPeriod.MONTHLY:
                    should_reset = current_time - budget.last_reset >= 2592000

                if should_reset:
                    logger.info(
                        f"Resetting budget for {api_key}: ${
                            budget.used:.4f} used in last period")
                    budget.used = 0.0
                    budget.alerted = False
                    budget.last_reset = current_time

    def get_projected_monthly_cost(self, api_key: str | None = None) -> float:
        """
        Calculate projected monthly cost based on recent usage.

        Args:
            api_key: If specified, only project for this API key. Otherwise, project total.

        Returns:
            Projected monthly cost in USD
        """
        # Use last 7 days of data to project
        cutoff_time = time.time() - (7 * 86400)

        with self._usage_lock:
            if api_key:
                records = [
                    r
                    for r in self._usage_records
                    if r.api_key == api_key and r.timestamp >= cutoff_time
                ]
            else:
                records = [
                    r for r in self._usage_records if r.timestamp >= cutoff_time]

            if not records:
                return 0.0

            # Calculate cost over the period
            total_cost = sum(r.cost for r in records)
            days_in_period = 7.0

            # Project to 30 days
            daily_cost = total_cost / days_in_period
            monthly_cost = daily_cost * 30

            return monthly_cost

    def _generate_optimization_suggestions(self, api_key: str) -> None:
        """Generate cost optimization suggestions for an API key."""
        with self._usage_lock:
            # Get recent records for this API key (last 24 hours)
            cutoff_time = time.time() - 86400
            records = [
                r
                for r in self._usage_records
                if r.api_key == api_key and r.timestamp >= cutoff_time
            ]

            if len(records) < 10:
                return  # Not enough data

            # Analyze model usage
            model_costs = defaultdict(float)
            model_counts = defaultdict(int)

            for record in records:
                model_costs[record.model] += record.cost
                model_counts[record.model] += 1

            # Suggest cheaper alternatives for expensive models
            if "gpt-4" in model_costs and model_costs["gpt-4"] > 1.0:
                # Check if GPT-4o or GPT-3.5 could be alternatives
                potential_savings = (
                    model_costs["gpt-4"] * 0.75
                )  # Assume 75% savings with GPT-4o

                suggestion = CostOptimizationSuggestion(
                    api_key=api_key,
                    suggestion_type="cheaper_model",
                    description=(
                        f"Consider using GPT-4o instead of GPT-4. "
                        f"You've spent ${model_costs['gpt-4']:.2f} on GPT-4 in the last 24h."
                    ),
                    potential_savings=potential_savings,
                    details={
                        "current_model": "gpt-4",
                        "suggested_model": "gpt-4o",
                        "current_cost": model_costs["gpt-4"],
                        "requests": model_counts["gpt-4"],
                    },
                )
                self._suggestions.append(suggestion)

            # Suggest using cache for repeated prompts
            # (simplified heuristic: check if there are many requests)
            if len(records) > 50:
                total_prompt_tokens = sum(r.prompt_tokens for r in records)
                estimated_cache_savings = (
                    total_prompt_tokens / 1_000_000 * 2.5 * 0.5
                )  # Estimate 50% cache hit

                if estimated_cache_savings > 0.10:
                    suggestion = CostOptimizationSuggestion(
                        api_key=api_key,
                        suggestion_type="enable_caching",
                        description=(
                            f"Enable prompt caching to reduce costs. " f"With {
                                len(records)} requests in 24h, caching could save ~${
                                estimated_cache_savings:.2f}/day."),
                        potential_savings=estimated_cache_savings * 30,
                        details={
                            "requests_per_day": len(records),
                            "daily_savings": estimated_cache_savings,
                        },
                    )
                    self._suggestions.append(suggestion)

            # Keep only last 100 suggestions
            if len(self._suggestions) > 100:
                self._suggestions = self._suggestions[-100:]

    def get_optimization_suggestions(
        self, api_key: str | None = None
    ) -> list[CostOptimizationSuggestion]:
        """
        Get cost optimization suggestions.

        Args:
            api_key: If specified, only return suggestions for this API key

        Returns:
            List of optimization suggestions
        """
        if api_key:
            return [s for s in self._suggestions if s.api_key == api_key]
        return self._suggestions.copy()

    def get_cache_savings(self, api_key: str |
                          None = None) -> dict[str, float]:
        """
        Calculate cost savings from cache hits.

        Args:
            api_key: If specified, only calculate for this API key

        Returns:
            Dictionary with savings information
        """
        with self._usage_lock:
            if api_key:
                records = [
                    r for r in self._usage_records if r.api_key == api_key]
            else:
                records = self._usage_records

            total_cached_tokens = sum(r.cached_tokens for r in records)

            # Calculate savings (cached tokens cost 50% less than regular tokens)
            # Using GPT-4o pricing as reference
            gpt4o_pricing = MODEL_PRICING["gpt-4o"]
            regular_cost = (
                total_cached_tokens /
                1_000_000 *
                gpt4o_pricing.input_price_per_million)
            cached_cost = (
                total_cached_tokens /
                1_000_000 *
                gpt4o_pricing.cached_input_price_per_million
            )
            savings = (
                regular_cost - cached_cost
                if gpt4o_pricing.cached_input_price_per_million
                else 0.0
            )

            return {
                "cached_tokens": total_cached_tokens,
                "savings": savings,
                "regular_cost": regular_cost,
                "cached_cost": cached_cost,
            }

    def get_batch_savings(self, api_key: str |
                          None = None) -> dict[str, float]:
        """
        Calculate cost savings from batch processing.

        Batch API provides 50% discount on completion tokens.

        Args:
            api_key: If specified, only calculate for this API key

        Returns:
            Dictionary with savings information
        """
        with self._usage_lock:
            if api_key:
                records = [
                    r
                    for r in self._usage_records
                    if r.api_key == api_key and r.endpoint == "/v1/batches"
                ]
            else:
                records = [
                    r for r in self._usage_records if r.endpoint == "/v1/batches"]

            if not records:
                return {
                    "batch_requests": 0,
                    "completion_tokens": 0,
                    "savings": 0.0,
                    "regular_cost": 0.0,
                    "batch_cost": 0.0,
                }

            total_completion_tokens = sum(r.completion_tokens for r in records)

            # Calculate savings (50% discount on completion tokens)
            gpt4o_pricing = MODEL_PRICING["gpt-4o"]
            regular_cost = (
                total_completion_tokens /
                1_000_000 *
                gpt4o_pricing.output_price_per_million
            )
            batch_cost = regular_cost * 0.5
            savings = regular_cost - batch_cost

            return {
                "batch_requests": len(records),
                "completion_tokens": total_completion_tokens,
                "savings": savings,
                "regular_cost": regular_cost,
                "batch_cost": batch_cost,
            }

    def get_summary(self) -> dict[str, Any]:
        """
        Get comprehensive cost summary.

        Returns:
            Dictionary with all cost information
        """
        # Don't hold lock while calling other methods that acquire locks
        total_cost = self.get_total_cost()
        total_cost_24h = self.get_total_cost(period_hours=24)
        total_cost_7d = self.get_total_cost(period_hours=168)

        # Get API keys first
        with self._usage_lock:
            api_keys = list(self._costs_by_key.keys())
            total_requests = len(self._usage_records)
            unique_api_keys = len(self._costs_by_key)

        costs_by_key = {key: self.get_cost_by_key(key) for key in api_keys}
        costs_by_model = self.get_cost_by_model()
        costs_by_endpoint = self.get_cost_by_endpoint()

        cache_savings = self.get_cache_savings()
        batch_savings = self.get_batch_savings()

        return {
            "total_cost": total_cost,
            "total_cost_24h": total_cost_24h,
            "total_cost_7d": total_cost_7d,
            "projected_monthly_cost": self.get_projected_monthly_cost(),
            "by_key": costs_by_key,
            "by_model": costs_by_model,
            "by_endpoint": costs_by_endpoint,
            "cache_savings": cache_savings,
            "batch_savings": batch_savings,
            "total_requests": total_requests,
            "unique_api_keys": unique_api_keys,
        }

    def clear_history(self, api_key: str | None = None) -> None:
        """
        Clear usage history.

        Args:
            api_key: If specified, only clear history for this API key. Otherwise, clear all.
        """
        with self._usage_lock:
            if api_key:
                self._usage_records = [
                    r for r in self._usage_records if r.api_key != api_key
                ]
                if api_key in self._costs_by_key:
                    del self._costs_by_key[api_key]
                if api_key in self._tokens_by_key:
                    del self._tokens_by_key[api_key]
                if api_key in self._model_usage_count:
                    del self._model_usage_count[api_key]
            else:
                self._usage_records.clear()
                self._costs_by_key.clear()
                self._costs_by_model.clear()
                self._costs_by_endpoint.clear()
                self._tokens_by_key.clear()
                self._model_usage_count.clear()
                self._suggestions.clear()

        logger.info(
            f"Cleared cost history{
                f' for {api_key}' if api_key else ''}")

    def shutdown(self) -> None:
        """Shutdown the cost tracker."""
        self._stop_thread = True
        if self._budget_reset_thread.is_alive():
            self._budget_reset_thread.join(timeout=1.0)
        logger.info("Cost tracker shutdown")
