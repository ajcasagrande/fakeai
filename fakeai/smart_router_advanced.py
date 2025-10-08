"""
Advanced Smart Router with Production-Grade Features.

This module extends the basic SmartRouter with:
- Multiple routing strategies (round-robin, least-loaded, cache-aware, hybrid, learned)
- Worker health tracking (success rate, latency, timeouts)
- Request affinity (conversation, user, model)
- Predictive routing (duration, cache hit likelihood)
- Cost function enhancements (memory pressure, queue depth, SLO penalties)
"""

#  SPDX-License-Identifier: Apache-2.0

import enum
import hashlib
import logging
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any

from fakeai.kv_cache import RadixTree, WorkerState

logger = logging.getLogger(__name__)


class RoutingStrategy(enum.Enum):
    """Available routing strategies."""

    ROUND_ROBIN = "round_robin"
    LEAST_LOADED = "least_loaded"
    CACHE_AWARE = "cache_aware"
    HYBRID = "hybrid"
    LEARNED = "learned"


@dataclass
class WorkerHealthMetrics:
    """Health metrics for a worker."""

    worker_id: str
    success_count: int = 0
    failure_count: int = 0
    timeout_count: int = 0
    total_latency_ms: float = 0.0
    request_count: int = 0
    last_success_time: float = 0.0
    last_failure_time: float = 0.0
    is_healthy: bool = True
    is_degraded: bool = False
    degraded_since: float | None = None
    unhealthy_since: float | None = None

    def get_success_rate(self) -> float:
        """Calculate success rate (0.0-1.0)."""
        total = self.success_count + self.failure_count
        return self.success_count / total if total > 0 else 1.0

    def get_average_latency_ms(self) -> float:
        """Calculate average latency in milliseconds."""
        return (
            self.total_latency_ms / self.request_count
            if self.request_count > 0
            else 0.0
        )

    def get_timeout_rate(self) -> float:
        """Calculate timeout rate (0.0-1.0)."""
        total = self.request_count
        return self.timeout_count / total if total > 0 else 0.0


@dataclass
class AdvancedWorkerState(WorkerState):
    """Extended worker state with advanced metrics."""

    queue_depth: int = 0
    memory_pressure: float = 0.0  # 0.0-1.0
    estimated_completion_time: float = 0.0
    request_history: deque = field(default_factory=lambda: deque(maxlen=100))


@dataclass
class RequestAffinity:
    """Request affinity information."""

    conversation_id: str | None = None
    user_id: str | None = None
    model_id: str | None = None


@dataclass
class RoutingDecision:
    """Detailed routing decision information."""

    worker_id: str
    strategy: RoutingStrategy
    matched_tokens: int
    matched_blocks: int
    cost: float
    cache_hit_probability: float
    estimated_duration_ms: float
    worker_load: int
    worker_health_score: float
    affinity_bonus: float
    reasoning: str


@dataclass
class CostWeights:
    """Configurable cost function weights."""

    kv_overlap: float = 1.0
    load_balance: float = 0.5
    memory_pressure: float = 0.3
    queue_depth: float = 0.4
    historical_performance: float = 0.2
    slo_violation_penalty: float = 2.0


@dataclass
class HealthThresholds:
    """Health check threshold configuration."""

    degraded_success_rate: float = 0.90
    unhealthy_success_rate: float = 0.70
    degraded_latency_ms: float = 5000.0
    unhealthy_latency_ms: float = 10000.0
    degraded_timeout_rate: float = 0.05
    unhealthy_timeout_rate: float = 0.15
    recovery_success_threshold: int = 10


class AdvancedSmartRouter:
    """
    Production-grade smart router with advanced features.

    Features:
    - Multiple routing strategies
    - Worker health tracking and automatic failover
    - Request affinity (conversation, user, model)
    - Predictive routing with duration and cache hit estimation
    - Enhanced cost function with memory pressure, queue depth, etc.
    """

    def __init__(
        self,
        strategy: RoutingStrategy = RoutingStrategy.HYBRID,
        cost_weights: CostWeights | None = None,
        health_thresholds: HealthThresholds | None = None,
        block_size: int = 16,
        num_workers: int = 4,
    ):
        self.strategy = strategy
        self.cost_weights = cost_weights or CostWeights()
        self.health_thresholds = health_thresholds or HealthThresholds()
        self.block_size = block_size
        self.radix_tree = RadixTree(block_size)

        # Worker management
        self.workers: dict[str, AdvancedWorkerState] = {}
        self.worker_health: dict[str, WorkerHealthMetrics] = {}
        self._round_robin_index = 0
        self._lock = threading.Lock()

        # Affinity tracking
        # conversation_id -> worker_id
        self.conversation_affinity: dict[str, str] = {}
        self.user_affinity: dict[str, list[str]] = defaultdict(
            list
        )  # user_id -> [worker_ids]
        self.model_affinity: dict[str, list[str]] = defaultdict(
            list
        )  # model_id -> [worker_ids]

        # Learning tracking
        self.routing_history: deque = deque(maxlen=1000)
        self.worker_success_patterns: dict[str, dict[str, int]] = defaultdict(
            lambda: defaultdict(int)
        )

        # Initialize workers
        for i in range(num_workers):
            worker_id = f"worker-{i}"
            self.workers[worker_id] = AdvancedWorkerState(worker_id=worker_id)
            self.worker_health[worker_id] = WorkerHealthMetrics(
                worker_id=worker_id)

    def route_request(
        self,
        tokens: list[int],
        estimated_output_tokens: int = 100,
        conversation_id: str | None = None,
        user_id: str | None = None,
        model_id: str | None = None,
        priority: int = 0,
    ) -> tuple[str, int, int]:
        """
        Route request to optimal worker using configured strategy.

        Args:
            tokens: Input token IDs
            estimated_output_tokens: Expected output length
            conversation_id: Optional conversation identifier for affinity
            user_id: Optional user identifier for affinity
            model_id: Optional model identifier for affinity
            priority: Request priority (0=normal, higher=more important)

        Returns:
            (worker_id, matched_tokens, matched_blocks_count)
        """
        if not self.workers:
            raise ValueError("No workers registered")

        # Build affinity context
        affinity = RequestAffinity(
            conversation_id=conversation_id,
            user_id=user_id,
            model_id=model_id,
        )

        # Route based on strategy
        if self.strategy == RoutingStrategy.ROUND_ROBIN:
            decision = self._route_round_robin(
                tokens, estimated_output_tokens, affinity
            )
        elif self.strategy == RoutingStrategy.LEAST_LOADED:
            decision = self._route_least_loaded(
                tokens, estimated_output_tokens, affinity
            )
        elif self.strategy == RoutingStrategy.CACHE_AWARE:
            decision = self._route_cache_aware(
                tokens, estimated_output_tokens, affinity
            )
        elif self.strategy == RoutingStrategy.HYBRID:
            decision = self._route_hybrid(
                tokens, estimated_output_tokens, affinity)
        elif self.strategy == RoutingStrategy.LEARNED:
            decision = self._route_learned(
                tokens, estimated_output_tokens, affinity)
        else:
            raise ValueError(f"Unknown routing strategy: {self.strategy}")

        # Record routing decision
        self.routing_history.append(
            {
                "timestamp": time.time(),
                "worker_id": decision.worker_id,
                "strategy": self.strategy.value,
                "matched_tokens": decision.matched_tokens,
                "cost": decision.cost,
                "conversation_id": conversation_id,
                "user_id": user_id,
                "model_id": model_id,
            }
        )

        # Update affinity tracking
        if conversation_id:
            self.conversation_affinity[conversation_id] = decision.worker_id
        if user_id and decision.worker_id not in self.user_affinity[user_id]:
            self.user_affinity[user_id].append(decision.worker_id)
        if model_id and decision.worker_id not in self.model_affinity[model_id]:
            self.model_affinity[model_id].append(decision.worker_id)

        return decision.worker_id, decision.matched_tokens, decision.matched_blocks

    def _route_round_robin(
        self,
        tokens: list[int],
        estimated_output_tokens: int,
        affinity: RequestAffinity,
    ) -> RoutingDecision:
        """Round-robin routing (baseline)."""
        healthy_workers = self._get_healthy_workers()
        if not healthy_workers:
            healthy_workers = list(self.workers.keys())

        with self._lock:
            self._round_robin_index = (self._round_robin_index + 1) % len(
                healthy_workers
            )
            worker_id = healthy_workers[self._round_robin_index]

        matched_tokens, matched_blocks, _ = self.radix_tree.find_longest_prefix(
            tokens)

        return RoutingDecision(
            worker_id=worker_id,
            strategy=RoutingStrategy.ROUND_ROBIN,
            matched_tokens=matched_tokens,
            matched_blocks=len(matched_blocks),
            cost=0.0,
            cache_hit_probability=0.0,
            estimated_duration_ms=0.0,
            worker_load=self.workers[worker_id].active_requests,
            worker_health_score=self.worker_health[worker_id].get_success_rate(),
            affinity_bonus=0.0,
            reasoning="Round-robin: next worker in rotation",
        )

    def _route_least_loaded(
        self,
        tokens: list[int],
        estimated_output_tokens: int,
        affinity: RequestAffinity,
    ) -> RoutingDecision:
        """Route to worker with fewest active requests."""
        healthy_workers = self._get_healthy_workers()
        if not healthy_workers:
            healthy_workers = list(self.workers.keys())

        best_worker_id = min(
            healthy_workers,
            key=lambda w: (
                self.workers[w].active_requests,
                self.workers[w].queue_depth,
            ),
        )

        matched_tokens, matched_blocks, _ = self.radix_tree.find_longest_prefix(
            tokens)

        worker = self.workers[best_worker_id]
        return RoutingDecision(
            worker_id=best_worker_id,
            strategy=RoutingStrategy.LEAST_LOADED,
            matched_tokens=matched_tokens,
            matched_blocks=len(matched_blocks),
            cost=float(
                worker.active_requests),
            cache_hit_probability=0.0,
            estimated_duration_ms=0.0,
            worker_load=worker.active_requests,
            worker_health_score=self.worker_health[best_worker_id].get_success_rate(),
            affinity_bonus=0.0,
            reasoning=f"Least loaded: {
                worker.active_requests} active requests",
        )

    def _route_cache_aware(
        self,
        tokens: list[int],
        estimated_output_tokens: int,
        affinity: RequestAffinity,
    ) -> RoutingDecision:
        """Route to worker with best cache overlap."""
        matched_tokens, matched_blocks, candidate_workers = (
            self.radix_tree.find_longest_prefix(tokens)
        )

        healthy_workers = self._get_healthy_workers()
        if not healthy_workers:
            healthy_workers = list(self.workers.keys())

        # Filter candidates to healthy workers
        healthy_candidates = [
            w for w in candidate_workers if w in healthy_workers]

        if not healthy_candidates:
            # No cache hit - use least loaded
            return self._route_least_loaded(
                tokens, estimated_output_tokens, affinity)

        # Choose candidate with most cache overlap and lowest load
        best_worker_id = min(
            healthy_candidates,
            key=lambda w: (
                -matched_tokens,  # Maximize cache hit
                self.workers[w].active_requests,  # Minimize load
            ),
        )

        worker = self.workers[best_worker_id]
        cache_hit_prob = matched_tokens / len(tokens) if tokens else 0.0

        return RoutingDecision(
            worker_id=best_worker_id,
            strategy=RoutingStrategy.CACHE_AWARE,
            matched_tokens=matched_tokens,
            matched_blocks=len(matched_blocks),
            cost=float(len(tokens) - matched_tokens),
            cache_hit_probability=cache_hit_prob,
            estimated_duration_ms=0.0,
            worker_load=worker.active_requests,
            worker_health_score=self.worker_health[best_worker_id].get_success_rate(),
            affinity_bonus=0.0,
            reasoning=f"Cache-aware: {matched_tokens} tokens cached ({cache_hit_prob:.1%})",
        )

    def _route_hybrid(
        self,
        tokens: list[int],
        estimated_output_tokens: int,
        affinity: RequestAffinity,
    ) -> RoutingDecision:
        """Route using weighted combination of all factors."""
        # Check conversation affinity first
        if (
            affinity.conversation_id and
            affinity.conversation_id in self.conversation_affinity
        ):
            preferred_worker = self.conversation_affinity[affinity.conversation_id]
            if self._is_worker_available(preferred_worker):
                matched_tokens, matched_blocks, _ = self.radix_tree.find_longest_prefix(
                    tokens)
                worker = self.workers[preferred_worker]
                return RoutingDecision(
                    worker_id=preferred_worker,
                    strategy=RoutingStrategy.HYBRID,
                    matched_tokens=matched_tokens,
                    matched_blocks=len(matched_blocks),
                    cost=0.0,
                    cache_hit_probability=1.0,
                    estimated_duration_ms=0.0,
                    worker_load=worker.active_requests,
                    worker_health_score=self.worker_health[preferred_worker].get_success_rate(),
                    affinity_bonus=1.0,
                    reasoning=f"Conversation affinity: reusing worker {preferred_worker}",
                )

        # Find cache matches
        matched_tokens, matched_blocks, candidate_workers = (
            self.radix_tree.find_longest_prefix(tokens)
        )

        healthy_workers = self._get_healthy_workers()
        if not healthy_workers:
            healthy_workers = list(self.workers.keys())

        best_worker_id = None
        best_cost = float("inf")
        best_decision = None

        for worker_id in healthy_workers:
            worker = self.workers[worker_id]
            health = self.worker_health[worker_id]

            # Calculate comprehensive cost
            cost = self._calculate_comprehensive_cost(
                tokens=tokens,
                matched_tokens=matched_tokens if worker_id in candidate_workers else 0,
                worker=worker,
                health=health,
                estimated_output_tokens=estimated_output_tokens,
                affinity=affinity,
            )

            if cost < best_cost:
                best_cost = cost
                best_worker_id = worker_id

                cache_hit_prob = (
                    matched_tokens / len(tokens)
                    if tokens and worker_id in candidate_workers
                    else 0.0
                )
                affinity_bonus = self._calculate_affinity_bonus(
                    worker_id, affinity)

                best_decision = RoutingDecision(
                    worker_id=worker_id,
                    strategy=RoutingStrategy.HYBRID,
                    matched_tokens=(
                        matched_tokens if worker_id in candidate_workers else 0),
                    matched_blocks=(
                        len(matched_blocks) if worker_id in candidate_workers else 0),
                    cost=cost,
                    cache_hit_probability=cache_hit_prob,
                    estimated_duration_ms=self._predict_request_duration(
                        tokens,
                        estimated_output_tokens,
                        worker),
                    worker_load=worker.active_requests,
                    worker_health_score=health.get_success_rate(),
                    affinity_bonus=affinity_bonus,
                    reasoning=self._explain_hybrid_decision(
                        cost,
                        cache_hit_prob,
                        worker,
                        health,
                        affinity_bonus),
                )

        return best_decision

    def _route_learned(
        self,
        tokens: list[int],
        estimated_output_tokens: int,
        affinity: RequestAffinity,
    ) -> RoutingDecision:
        """Route based on learned historical patterns."""
        # Use historical success patterns to inform routing
        healthy_workers = self._get_healthy_workers()
        if not healthy_workers:
            healthy_workers = list(self.workers.keys())

        # Calculate learned scores based on historical success
        worker_scores = {}
        for worker_id in healthy_workers:
            health = self.worker_health[worker_id]
            success_rate = health.get_success_rate()
            avg_latency = health.get_average_latency_ms()

            # Normalize latency (lower is better, max 10s)
            latency_score = 1.0 - min(avg_latency / 10000.0, 1.0)

            # Combined learned score
            worker_scores[worker_id] = (
                success_rate * 0.7) + (latency_score * 0.3)

        # Choose worker with highest learned score
        best_worker_id = max(worker_scores.items(), key=lambda x: x[1])[0]

        matched_tokens, matched_blocks, _ = self.radix_tree.find_longest_prefix(
            tokens)

        worker = self.workers[best_worker_id]
        health = self.worker_health[best_worker_id]

        return RoutingDecision(
            worker_id=best_worker_id,
            strategy=RoutingStrategy.LEARNED,
            matched_tokens=matched_tokens,
            matched_blocks=len(matched_blocks),
            cost=1.0 -
            worker_scores[best_worker_id],
            cache_hit_probability=matched_tokens /
            len(tokens) if tokens else 0.0,
            estimated_duration_ms=health.get_average_latency_ms(),
            worker_load=worker.active_requests,
            worker_health_score=health.get_success_rate(),
            affinity_bonus=0.0,
            reasoning=f"Learned: historical success rate {
                health.get_success_rate():.1%}, " f"avg latency {
                health.get_average_latency_ms():.0f}ms",
        )

    def _calculate_comprehensive_cost(
        self,
        tokens: list[int],
        matched_tokens: int,
        worker: AdvancedWorkerState,
        health: WorkerHealthMetrics,
        estimated_output_tokens: int,
        affinity: RequestAffinity,
    ) -> float:
        """Calculate comprehensive routing cost with all factors."""
        w = self.cost_weights

        # KV cache overlap cost (lower is better)
        total_tokens = len(tokens)
        tokens_to_prefill = total_tokens - matched_tokens
        prefill_blocks = tokens_to_prefill / self.block_size
        kv_cost = w.kv_overlap * prefill_blocks

        # Decode cost
        decode_blocks = estimated_output_tokens / self.block_size

        # Load balance cost
        load_cost = w.load_balance * worker.active_requests

        # Memory pressure cost
        memory_cost = w.memory_pressure * worker.memory_pressure

        # Queue depth cost
        queue_cost = w.queue_depth * worker.queue_depth

        # Historical performance cost (inverse of success rate)
        success_rate = health.get_success_rate()
        perf_cost = w.historical_performance * (1.0 - success_rate)

        # SLO violation penalty (if worker is degraded/unhealthy)
        slo_penalty = 0.0
        if not health.is_healthy:
            slo_penalty = w.slo_violation_penalty * 2.0
        elif health.is_degraded:
            slo_penalty = w.slo_violation_penalty

        # Affinity bonus (negative cost)
        affinity_bonus = - \
            self._calculate_affinity_bonus(worker.worker_id, affinity)

        total_cost = (
            kv_cost +
            decode_blocks +
            load_cost +
            memory_cost +
            queue_cost +
            perf_cost +
            slo_penalty +
            affinity_bonus
        )

        return max(0.0, total_cost)

    def _calculate_affinity_bonus(
        self, worker_id: str, affinity: RequestAffinity
    ) -> float:
        """Calculate affinity bonus for a worker."""
        bonus = 0.0

        # Conversation affinity is strongest
        if affinity.conversation_id:
            if self.conversation_affinity.get(
                    affinity.conversation_id) == worker_id:
                bonus += 0.5

        # User affinity
        if affinity.user_id:
            if worker_id in self.user_affinity.get(affinity.user_id, []):
                bonus += 0.2

        # Model affinity
        if affinity.model_id:
            if worker_id in self.model_affinity.get(affinity.model_id, []):
                bonus += 0.1

        return bonus

    def _explain_hybrid_decision(
        self,
        cost: float,
        cache_hit_prob: float,
        worker: AdvancedWorkerState,
        health: WorkerHealthMetrics,
        affinity_bonus: float,
    ) -> str:
        """Generate human-readable explanation for hybrid routing decision."""
        reasons = []
        reasons.append(f"cost={cost:.2f}")

        if cache_hit_prob > 0:
            reasons.append(f"cache_hit={cache_hit_prob:.1%}")

        if worker.active_requests > 0:
            reasons.append(f"load={worker.active_requests}")

        if health.get_success_rate() < 1.0:
            reasons.append(f"success_rate={health.get_success_rate():.1%}")

        if affinity_bonus > 0:
            reasons.append(f"affinity_bonus={affinity_bonus:.2f}")

        return f"Hybrid: {', '.join(reasons)}"

    def _predict_request_duration(
        self,
        tokens: list[int],
        estimated_output_tokens: int,
        worker: AdvancedWorkerState,
    ) -> float:
        """Predict request duration in milliseconds."""
        # Simple model: base on historical latency and token count
        if not worker.request_history:
            # No history - estimate based on tokens
            # Assume ~50 tokens/second (20ms per token)
            total_tokens = len(tokens) + estimated_output_tokens
            return total_tokens * 20.0

        # Average historical latency
        recent_latencies = [req["latency_ms"]
                            for req in worker.request_history if "latency_ms" in req]
        if recent_latencies:
            avg_latency = sum(recent_latencies) / len(recent_latencies)
            return avg_latency

        return 1000.0  # Default 1s

    def _get_healthy_workers(self) -> list[str]:
        """Get list of healthy (non-failed) workers."""
        return [
            worker_id
            for worker_id, health in self.worker_health.items()
            if health.is_healthy
        ]

    def _is_worker_available(self, worker_id: str) -> bool:
        """Check if worker is available (exists and healthy)."""
        return worker_id in self.workers and self.worker_health[worker_id].is_healthy

    def update_worker_health(
        self,
        worker_id: str,
        success: bool,
        latency_ms: float,
        timeout: bool = False,
    ):
        """
        Update worker health based on request outcome.

        Args:
            worker_id: Worker identifier
            success: Whether request succeeded
            latency_ms: Request latency in milliseconds
            timeout: Whether request timed out
        """
        if worker_id not in self.worker_health:
            logger.warning(f"Unknown worker {worker_id}")
            return

        with self._lock:
            health = self.worker_health[worker_id]
            worker = self.workers[worker_id]

            health.request_count += 1
            health.total_latency_ms += latency_ms

            if timeout:
                health.timeout_count += 1
                health.failure_count += 1
                health.last_failure_time = time.time()
            elif success:
                health.success_count += 1
                health.last_success_time = time.time()
            else:
                health.failure_count += 1
                health.last_failure_time = time.time()

            # Add to worker history
            worker.request_history.append(
                {
                    "timestamp": time.time(),
                    "success": success,
                    "latency_ms": latency_ms,
                    "timeout": timeout,
                }
            )

            # Update health status
            self._update_health_status(worker_id)

    def _update_health_status(self, worker_id: str):
        """Update worker health status based on thresholds."""
        health = self.worker_health[worker_id]
        thresholds = self.health_thresholds

        success_rate = health.get_success_rate()
        avg_latency = health.get_average_latency_ms()
        timeout_rate = health.get_timeout_rate()

        # Determine health status based on current metrics
        is_unhealthy = (
            success_rate < thresholds.unhealthy_success_rate or
            avg_latency > thresholds.unhealthy_latency_ms or
            timeout_rate > thresholds.unhealthy_timeout_rate
        )

        is_degraded = (
            success_rate < thresholds.degraded_success_rate or
            avg_latency > thresholds.degraded_latency_ms or
            timeout_rate > thresholds.degraded_timeout_rate
        )

        # Check for recovery possibility if worker is currently
        # unhealthy/degraded
        can_recover = False
        if not health.is_healthy or health.is_degraded:
            # Check if we have enough recent successes
            recent_successes = sum(
                1
                for req in list(self.workers[worker_id].request_history)[-10:]
                if req.get("success", False)
            )
            can_recover = (
                recent_successes >= thresholds.recovery_success_threshold and
                not is_unhealthy and
                not is_degraded
            )
            # Debug logging
            if recent_successes >= thresholds.recovery_success_threshold:
                logger.debug(
                    f"Worker {worker_id} recovery check: recent_successes={recent_successes}, "
                    f"is_unhealthy={is_unhealthy}, is_degraded={is_degraded}, "
                    f"can_recover={can_recover}"
                )

        # State transitions
        if can_recover:
            # Recovery takes priority
            if not health.is_healthy:
                logger.info(f"Worker {worker_id} recovered from UNHEALTHY")
            elif health.is_degraded:
                logger.info(f"Worker {worker_id} recovered from DEGRADED")

            health.is_healthy = True
            health.is_degraded = False
            health.degraded_since = None
            health.unhealthy_since = None
        elif is_unhealthy:
            # Mark as unhealthy (or keep unhealthy status)
            if health.is_healthy:
                # Log only on transition
                logger.warning(
                    f"Worker {worker_id} marked UNHEALTHY: "
                    f"success_rate={success_rate:.2%}, "
                    f"latency={avg_latency:.0f}ms, "
                    f"timeout_rate={timeout_rate:.2%}"
                )
            health.is_healthy = False
            if health.unhealthy_since is None:
                health.unhealthy_since = time.time()
        elif is_degraded:
            # Mark as degraded (or keep degraded status)
            if health.is_healthy and not health.is_degraded:
                # Log only on transition
                logger.warning(
                    f"Worker {worker_id} marked DEGRADED: "
                    f"success_rate={success_rate:.2%}, "
                    f"latency={avg_latency:.0f}ms"
                )
            health.is_degraded = True
            if health.degraded_since is None:
                health.degraded_since = time.time()

    def start_request(self, worker_id: str):
        """Mark request as started on worker."""
        with self._lock:
            self.workers[worker_id].active_requests += 1
            self.workers[worker_id].queue_depth += 1
            self.workers[worker_id].total_requests += 1

    def complete_request(
        self,
        worker_id: str,
        tokens: list[int],
        output_tokens: int,
        success: bool = True,
        latency_ms: float = 0.0,
    ):
        """Mark request as completed and update cache."""
        with self._lock:
            self.workers[worker_id].active_requests -= 1
            self.workers[worker_id].queue_depth = max(
                0, self.workers[worker_id].queue_depth - 1
            )
            self.workers[worker_id].total_tokens_processed += (
                len(tokens) + output_tokens
            )

        # Update health
        self.update_worker_health(worker_id, success, latency_ms)

        # Update radix tree with this prefix (if successful)
        if success:
            self.radix_tree.insert(tokens, worker_id)

            # Update worker's cached blocks
            with self._lock:
                for i in range(0, len(tokens), self.block_size):
                    block_tokens = tokens[: i + self.block_size]
                    # Use stable hashing for block IDs
                    token_bytes = str(tuple(block_tokens)).encode()
                    block_hash = hashlib.md5(token_bytes).hexdigest()[:16]
                    block_id = f"block_{block_hash}"
                    self.workers[worker_id].cached_blocks.add(block_id)

    def get_routing_decision_explain(
        self,
        tokens: list[int],
        estimated_output_tokens: int = 100,
        conversation_id: str | None = None,
        user_id: str | None = None,
        model_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Explain why a routing decision was made.

        Returns detailed information about how each worker was evaluated
        and why the selected worker was chosen.
        """
        affinity = RequestAffinity(
            conversation_id=conversation_id,
            user_id=user_id,
            model_id=model_id,
        )

        matched_tokens, matched_blocks, candidate_workers = (
            self.radix_tree.find_longest_prefix(tokens)
        )

        worker_evaluations = []

        for worker_id, worker in self.workers.items():
            health = self.worker_health[worker_id]
            has_cache = worker_id in candidate_workers

            cost = self._calculate_comprehensive_cost(
                tokens=tokens,
                matched_tokens=matched_tokens if has_cache else 0,
                worker=worker,
                health=health,
                estimated_output_tokens=estimated_output_tokens,
                affinity=affinity,
            )

            worker_evaluations.append(
                {
                    "worker_id": worker_id,
                    "cost": round(cost, 3),
                    "health_status": (
                        "healthy"
                        if health.is_healthy and not health.is_degraded
                        else "degraded" if health.is_degraded else "unhealthy"
                    ),
                    "success_rate": round(health.get_success_rate(), 3),
                    "average_latency_ms": round(health.get_average_latency_ms(), 1),
                    "active_requests": worker.active_requests,
                    "queue_depth": worker.queue_depth,
                    "memory_pressure": round(worker.memory_pressure, 2),
                    "cache_hit": has_cache,
                    "matched_tokens": matched_tokens if has_cache else 0,
                    "affinity_bonus": round(
                        self._calculate_affinity_bonus(worker_id, affinity), 2
                    ),
                }
            )

        # Sort by cost (best first)
        worker_evaluations.sort(key=lambda x: x["cost"])

        selected_worker = worker_evaluations[0] if worker_evaluations else None

        return {
            "strategy": self.strategy.value,
            "total_input_tokens": len(tokens),
            "estimated_output_tokens": estimated_output_tokens,
            "cache_match": {
                "matched_tokens": matched_tokens,
                "matched_blocks": len(matched_blocks),
                "candidate_workers": list(candidate_workers),
            },
            "affinity": {
                "conversation_id": conversation_id,
                "user_id": user_id,
                "model_id": model_id,
                "has_conversation_affinity": conversation_id
                in self.conversation_affinity,
            },
            "selected_worker": selected_worker,
            "all_workers": worker_evaluations,
        }

    def optimize_worker_pool(self) -> dict[str, Any]:
        """
        Analyze worker pool and suggest optimizations.

        Returns:
            Optimization suggestions and pool analysis
        """
        with self._lock:
            total_requests = sum(
                w.total_requests for w in self.workers.values())
            total_active = sum(
                w.active_requests for w in self.workers.values())

            worker_utilization = {}
            for worker_id, worker in self.workers.items():
                if total_requests > 0:
                    utilization = worker.total_requests / total_requests
                else:
                    utilization = 0.0
                worker_utilization[worker_id] = utilization

            # Identify issues
            suggestions = []
            warnings = []

            # Check for overloaded workers
            max_active = max(
                (w.active_requests for w in self.workers.values()), default=0
            )
            if max_active > 10:
                suggestions.append(
                    f"High load detected: {max_active} active requests on busiest worker. "
                    "Consider adding more workers."
                )

            # Check for unhealthy workers
            unhealthy = [
                w_id for w_id,
                h in self.worker_health.items() if not h.is_healthy]
            if unhealthy:
                warnings.append(
                    f"{len(unhealthy)} unhealthy worker(s): {', '.join(unhealthy)}"
                )
                suggestions.append(
                    "Unhealthy workers detected. Investigate worker failures and consider restarting."
                )

            # Check for degraded workers
            degraded = [
                w_id
                for w_id, h in self.worker_health.items()
                if h.is_degraded and h.is_healthy
            ]
            if degraded:
                warnings.append(
                    f"{len(degraded)} degraded worker(s): {', '.join(degraded)}"
                )

            # Check for imbalanced utilization
            if worker_utilization:
                max_util = max(worker_utilization.values())
                min_util = min(worker_utilization.values())
                if max_util - min_util > 0.3:
                    suggestions.append(
                        f"Imbalanced worker utilization detected (max={
                            max_util:.1%}, min={
                            min_util:.1%}). " "Consider adjusting routing strategy or rebalancing workers.")

            # Check cache efficiency
            tree_stats = self.radix_tree.get_stats()
            avg_blocks_per_worker = (
                tree_stats["total_cached_blocks"] / len(self.workers)
                if self.workers
                else 0
            )
            if avg_blocks_per_worker < 10:
                suggestions.append(
                    "Low cache utilization detected. Workers have few cached blocks. "
                    "Consider using CACHE_AWARE or HYBRID routing strategy.")

        return {
            "total_workers": len(self.workers),
            "healthy_workers": len(
                [h for h in self.worker_health.values() if h.is_healthy]
            ),
            "degraded_workers": len(degraded),
            "unhealthy_workers": len(unhealthy),
            "total_active_requests": total_active,
            "worker_utilization": {
                k: round(v, 3) for k, v in worker_utilization.items()
            },
            "cache_stats": tree_stats,
            "suggestions": suggestions,
            "warnings": warnings,
        }

    def get_stats(self) -> dict[str, Any]:
        """Get comprehensive routing and health statistics."""
        with self._lock:
            worker_stats = {}
            for worker_id, worker in self.workers.items():
                health = self.worker_health[worker_id]
                worker_stats[worker_id] = {
                    "active_requests": worker.active_requests,
                    "total_requests": worker.total_requests,
                    "queue_depth": worker.queue_depth,
                    "memory_pressure": round(
                        worker.memory_pressure,
                        2),
                    "cached_blocks": len(
                        worker.cached_blocks),
                    "tokens_processed": worker.total_tokens_processed,
                    "health": {
                        "is_healthy": health.is_healthy,
                        "is_degraded": health.is_degraded,
                        "success_rate": round(
                            health.get_success_rate(),
                            3),
                        "average_latency_ms": round(
                            health.get_average_latency_ms(),
                            1),
                        "timeout_rate": round(
                            health.get_timeout_rate(),
                            3),
                        "total_requests": health.request_count,
                    },
                }

        tree_stats = self.radix_tree.get_stats()

        return {
            "strategy": self.strategy.value,
            "workers": worker_stats,
            "radix_tree": tree_stats,
            "affinity": {
                "active_conversations": len(self.conversation_affinity),
                "tracked_users": len(self.user_affinity),
                "tracked_models": len(self.model_affinity),
            },
            "routing_history_size": len(self.routing_history),
            "config": {
                "block_size": self.block_size,
                "num_workers": len(self.workers),
                "cost_weights": {
                    "kv_overlap": self.cost_weights.kv_overlap,
                    "load_balance": self.cost_weights.load_balance,
                    "memory_pressure": self.cost_weights.memory_pressure,
                    "queue_depth": self.cost_weights.queue_depth,
                    "historical_performance": self.cost_weights.historical_performance,
                    "slo_violation_penalty": self.cost_weights.slo_violation_penalty,
                },
                "health_thresholds": {
                    "degraded_success_rate": self.health_thresholds.degraded_success_rate,
                    "unhealthy_success_rate": self.health_thresholds.unhealthy_success_rate,
                    "degraded_latency_ms": self.health_thresholds.degraded_latency_ms,
                    "unhealthy_latency_ms": self.health_thresholds.unhealthy_latency_ms,
                },
            },
        }
