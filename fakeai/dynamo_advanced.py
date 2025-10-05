"""
NVIDIA AI-Dynamo Advanced Features Simulation.

Implements complete Dynamo architecture including:
- KVBM (KV Block Manager) with 4-tier memory hierarchy
- Block lifecycle state machine
- SLA-based planner with load predictors
- Disaggregated router (prefill/decode decision)
- Prefill queue management
- Dynamic endpoint registration
"""
import asyncio
import threading
import time
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable


# ============================================================================
# KVBM - KV Block Manager
# ============================================================================

class MemoryTier(Enum):
    """KVBM memory tiers (G1-G4)."""
    G1_GPU_HBM = "gpu_hbm"          # Device GPU memory
    G2_CPU_DRAM = "cpu_dram"        # Host CPU memory
    G3_LOCAL_SSD = "local_ssd"      # Local SSD storage
    G4_REMOTE_STORAGE = "remote"    # Remote object store


class BlockState(Enum):
    """KV block lifecycle states."""
    RESET = "reset"            # Uninitialized
    PARTIAL = "partial"        # Being filled
    COMPLETE = "complete"      # Filled but not visible
    REGISTERED = "registered"  # Finalized and visible for reuse


@dataclass
class KVBlock:
    """KV cache block."""
    block_id: str
    tokens: list[int] = field(default_factory=list)
    state: BlockState = BlockState.RESET
    tier: MemoryTier = MemoryTier.G1_GPU_HBM
    size_tokens: int = 16
    created_at: float = 0.0
    last_accessed: float = 0.0
    access_count: int = 0
    owner_request_id: str | None = None

    def __post_init__(self):
        if self.created_at == 0.0:
            self.created_at = time.time()


class KVBlockPool:
    """Block pool for a specific memory tier."""

    def __init__(self, tier: MemoryTier, capacity_blocks: int):
        self.tier = tier
        self.capacity = capacity_blocks
        self.active_pool: dict[str, KVBlock] = {}
        self.inactive_pool: deque[KVBlock] = deque()
        self._lock = threading.Lock()

    def allocate_block(self, size_tokens: int = 16) -> KVBlock | None:
        """Allocate a block from inactive pool or create new."""
        with self._lock:
            # Try to reuse from inactive pool
            if self.inactive_pool:
                block = self.inactive_pool.popleft()
                block.tokens = []
                block.state = BlockState.RESET
                block.created_at = time.time()
                self.active_pool[block.block_id] = block
                return block

            # Create new if capacity available
            if len(self.active_pool) < self.capacity:
                block = KVBlock(
                    block_id=f"{self.tier.value}_{uuid.uuid4().hex[:8]}",
                    size_tokens=size_tokens,
                    tier=self.tier,
                )
                self.active_pool[block.block_id] = block
                return block

            return None  # Pool full

    def release_block(self, block_id: str):
        """Release block back to inactive pool."""
        with self._lock:
            if block_id in self.active_pool:
                block = self.active_pool.pop(block_id)
                self.inactive_pool.append(block)

    def get_block(self, block_id: str) -> KVBlock | None:
        """Get block by ID."""
        with self._lock:
            return self.active_pool.get(block_id)

    def get_stats(self) -> dict[str, int]:
        """Get pool statistics."""
        with self._lock:
            return {
                "tier": self.tier.value,
                "capacity": self.capacity,
                "active_blocks": len(self.active_pool),
                "inactive_blocks": len(self.inactive_pool),
                "utilization_pct": (len(self.active_pool) / self.capacity * 100) if self.capacity > 0 else 0,
            }


class KVBlockManager:
    """
    KV Block Manager with 4-tier memory hierarchy.

    Manages KV cache blocks across GPU, CPU, SSD, and remote storage tiers.
    Implements block lifecycle, eviction policies, and cross-tier transfers.
    """

    def __init__(
        self,
        g1_capacity: int = 1000,
        g2_capacity: int = 5000,
        g3_capacity: int = 20000,
        g4_capacity: int = 100000,
    ):
        # Create pools for each tier
        self.pools = {
            MemoryTier.G1_GPU_HBM: KVBlockPool(MemoryTier.G1_GPU_HBM, g1_capacity),
            MemoryTier.G2_CPU_DRAM: KVBlockPool(MemoryTier.G2_CPU_DRAM, g2_capacity),
            MemoryTier.G3_LOCAL_SSD: KVBlockPool(MemoryTier.G3_LOCAL_SSD, g3_capacity),
            MemoryTier.G4_REMOTE_STORAGE: KVBlockPool(MemoryTier.G4_REMOTE_STORAGE, g4_capacity),
        }

        # Block registry (all blocks across tiers)
        self.block_registry: dict[str, KVBlock] = {}

        # Eviction metrics
        self.evictions_by_tier = defaultdict(int)
        self.transfers_between_tiers = defaultdict(int)

        self._lock = threading.Lock()

    def allocate(self, tier: MemoryTier = MemoryTier.G1_GPU_HBM, size_tokens: int = 16) -> KVBlock | None:
        """Allocate block in specified tier."""
        block = self.pools[tier].allocate_block(size_tokens)
        if block:
            with self._lock:
                self.block_registry[block.block_id] = block
        return block

    def transition_state(self, block_id: str, new_state: BlockState):
        """Transition block to new state."""
        with self._lock:
            if block_id in self.block_registry:
                self.block_registry[block_id].state = new_state

    def offload_to_tier(self, block_id: str, target_tier: MemoryTier) -> bool:
        """
        Offload block to lower memory tier.

        Args:
            block_id: Block to offload
            target_tier: Target memory tier

        Returns:
            True if successful
        """
        with self._lock:
            if block_id not in self.block_registry:
                return False

            block = self.block_registry[block_id]
            current_tier = block.tier

            # Allocate in target tier
            target_pool = self.pools[target_tier]
            if len(target_pool.active_pool) >= target_pool.capacity:
                return False  # No space

            # Release from current tier
            self.pools[current_tier].release_block(block_id)

            # Move to target tier
            block.tier = target_tier
            target_pool.active_pool[block_id] = block

            # Track transfer
            self.transfers_between_tiers[f"{current_tier.value}->{target_tier.value}"] += 1

            return True

    def evict_lru(self, tier: MemoryTier) -> bool:
        """Evict least recently used block from tier."""
        pool = self.pools[tier]

        with self._lock:
            if not pool.active_pool:
                return False

            # Find LRU block
            lru_block = min(pool.active_pool.values(), key=lambda b: b.last_accessed)

            # Evict
            pool.release_block(lru_block.block_id)
            self.evictions_by_tier[tier.value] += 1

            return True

    def get_stats(self) -> dict[str, Any]:
        """Get KVBM statistics."""
        return {
            "pools": {tier.value: pool.get_stats() for tier, pool in self.pools.items()},
            "total_blocks": len(self.block_registry),
            "evictions_by_tier": dict(self.evictions_by_tier),
            "transfers": dict(self.transfers_between_tiers),
        }


# ============================================================================
# SLA-Based Planner
# ============================================================================

class LoadPredictor(Enum):
    """Load prediction strategies."""
    CONSTANT = "constant"      # Assumes current load stays constant
    ARIMA = "arima"           # Time-series trend analysis
    PROPHET = "prophet"       # Seasonal patterns


@dataclass
class SLATarget:
    """Service Level Agreement targets."""
    ttft_ms: float = 500.0     # Time to first token target (ms)
    itl_ms: float = 50.0       # Inter-token latency target (ms)
    throughput_rps: float = 10.0  # Requests per second target
    p95_ttft_ms: float | None = None  # p95 TTFT target
    p99_ttft_ms: float | None = None  # p99 TTFT target


@dataclass
class WorkerAllocation:
    """Worker allocation plan."""
    prefill_workers: int = 1
    decode_workers: int = 1
    gpus_per_worker: int = 1
    tensor_parallel_size: int = 1


class SLABasedPlanner:
    """
    SLA-based planner for dynamic worker scaling.

    Monitors metrics, predicts load, and adjusts worker allocation
    to meet SLA targets for TTFT and ITL.
    """

    def __init__(
        self,
        sla_target: SLATarget,
        predictor_type: LoadPredictor = LoadPredictor.CONSTANT,
        adjustment_interval_seconds: int = 60,
    ):
        self.sla_target = sla_target
        self.predictor_type = predictor_type
        self.adjustment_interval = adjustment_interval_seconds

        # Current allocation
        self.current_allocation = WorkerAllocation()

        # Historical metrics
        self.request_rate_history: deque[tuple[float, float]] = deque(maxlen=100)
        self.ttft_history: deque[float] = deque(maxlen=1000)
        self.itl_history: deque[float] = deque(maxlen=1000)

        # Predictions
        self.predicted_load = 0.0
        self.predicted_ttft = 0.0

        # Scaling events
        self.scale_up_events = 0
        self.scale_down_events = 0

        self._lock = threading.Lock()

    def record_request_metrics(self, ttft_ms: float, itl_ms: float, request_count: int):
        """Record metrics for planning."""
        with self._lock:
            timestamp = time.time()
            self.request_rate_history.append((timestamp, request_count))
            self.ttft_history.append(ttft_ms)
            self.itl_history.append(itl_ms)

    def predict_load(self) -> float:
        """Predict future load using configured predictor."""
        if not self.request_rate_history:
            return 0.0

        if self.predictor_type == LoadPredictor.CONSTANT:
            # Use recent average
            recent_rates = [rate for _, rate in list(self.request_rate_history)[-10:]]
            return sum(recent_rates) / len(recent_rates) if recent_rates else 0.0

        elif self.predictor_type == LoadPredictor.ARIMA:
            # Simplified ARIMA: linear trend + average
            if len(self.request_rate_history) < 3:
                # Use constant predictor logic as fallback
                recent_rates = [rate for _, rate in list(self.request_rate_history)[-10:]]
                return sum(recent_rates) / len(recent_rates) if recent_rates else 0.0

            rates = [rate for _, rate in self.request_rate_history]
            # Simple trend: compare recent to older
            recent_avg = sum(rates[-5:]) / 5 if len(rates) >= 5 else rates[-1]
            older_avg = sum(rates[-10:-5]) / 5 if len(rates) >= 10 else recent_avg

            trend = recent_avg - older_avg
            predicted = recent_avg + trend  # Project trend forward

            return max(0.0, predicted)

        elif self.predictor_type == LoadPredictor.PROPHET:
            # Simplified Prophet: detect patterns
            if len(self.request_rate_history) < 10:
                return self.predict_load()  # Fall back

            # Use weighted average with recent bias
            rates = [rate for _, rate in self.request_rate_history]
            weights = [i + 1 for i in range(len(rates))]  # Linear weights
            weighted_sum = sum(r * w for r, w in zip(rates, weights))
            weight_sum = sum(weights)

            return weighted_sum / weight_sum if weight_sum > 0 else 0.0

        return 0.0

    def calculate_required_workers(self) -> WorkerAllocation:
        """
        Calculate required worker allocation to meet SLA.

        Uses formula from Dynamo SLA planner:
        prefill_replicas = ceil(predicted_load / throughput / gpus_per_engine)
        """
        import math

        predicted_load = self.predict_load()

        # Estimate throughput based on SLA targets
        # Simple model: if TTFT target is low, need more prefill capacity
        prefill_throughput_per_gpu = 1.0 / (self.sla_target.ttft_ms / 1000.0)
        decode_throughput_per_gpu = 1.0 / (self.sla_target.itl_ms / 1000.0)

        # Calculate required workers
        prefill_workers = max(1, math.ceil(predicted_load / prefill_throughput_per_gpu))
        decode_workers = max(1, math.ceil(predicted_load / decode_throughput_per_gpu))

        return WorkerAllocation(
            prefill_workers=prefill_workers,
            decode_workers=decode_workers,
            gpus_per_worker=self.current_allocation.gpus_per_worker,
            tensor_parallel_size=self.current_allocation.tensor_parallel_size,
        )

    def should_scale(self) -> tuple[bool, WorkerAllocation]:
        """
        Determine if scaling is needed.

        Returns:
            (should_scale, new_allocation)
        """
        required = self.calculate_required_workers()

        # Check if current allocation differs
        current = self.current_allocation

        if (required.prefill_workers != current.prefill_workers or
            required.decode_workers != current.decode_workers):
            return True, required

        return False, current

    def apply_allocation(self, allocation: WorkerAllocation):
        """Apply new worker allocation."""
        with self._lock:
            old_allocation = self.current_allocation
            self.current_allocation = allocation

            # Track scaling events
            if allocation.prefill_workers > old_allocation.prefill_workers:
                self.scale_up_events += 1
            elif allocation.prefill_workers < old_allocation.prefill_workers:
                self.scale_down_events += 1

    def get_stats(self) -> dict[str, Any]:
        """Get planner statistics."""
        with self._lock:
            return {
                "sla_targets": {
                    "ttft_ms": self.sla_target.ttft_ms,
                    "itl_ms": self.sla_target.itl_ms,
                    "throughput_rps": self.sla_target.throughput_rps,
                },
                "current_allocation": {
                    "prefill_workers": self.current_allocation.prefill_workers,
                    "decode_workers": self.current_allocation.decode_workers,
                    "gpus_per_worker": self.current_allocation.gpus_per_worker,
                },
                "predicted_load": self.predicted_load,
                "scale_events": {
                    "scale_up": self.scale_up_events,
                    "scale_down": self.scale_down_events,
                },
                "predictor_type": self.predictor_type.value,
            }


# ============================================================================
# Disaggregated Router
# ============================================================================

@dataclass
class DisaggregationDecision:
    """Decision whether to disaggregate prefill/decode."""
    use_remote_prefill: bool
    reason: str
    prefill_worker_id: str | None = None
    decode_worker_id: str | None = None


class DisaggregatedRouter:
    """
    Router for disaggregated prefill/decode decisions.

    Decides whether to execute prefill locally or remotely based on:
    - Prefill length threshold
    - Prefill queue capacity
    - Worker availability
    """

    def __init__(
        self,
        prefill_length_threshold: int = 512,
        queue_capacity_threshold: int = 10,
    ):
        self.prefill_length_threshold = prefill_length_threshold
        self.queue_capacity_threshold = queue_capacity_threshold

        # Statistics
        self.local_prefill_count = 0
        self.remote_prefill_count = 0
        self.queue_full_rejections = 0

        self._lock = threading.Lock()

    def make_decision(
        self,
        input_length: int,
        current_queue_depth: int,
        decode_worker_available: bool = True,
    ) -> DisaggregationDecision:
        """
        Decide whether to use remote prefill.

        Criteria:
        1. Input length > threshold AND
        2. Queue has capacity below threshold
        """
        use_remote = False
        reason = "local_prefill"

        # Check criteria
        if input_length > self.prefill_length_threshold:
            if current_queue_depth < self.queue_capacity_threshold:
                use_remote = True
                reason = "remote_prefill_beneficial"
            else:
                reason = "queue_full"
        else:
            reason = "short_input"

        # Update stats
        with self._lock:
            if use_remote:
                self.remote_prefill_count += 1
            else:
                self.local_prefill_count += 1

        return DisaggregationDecision(
            use_remote_prefill=use_remote,
            reason=reason,
        )

    def get_stats(self) -> dict[str, Any]:
        """Get router statistics."""
        with self._lock:
            total = self.local_prefill_count + self.remote_prefill_count
            return {
                "local_prefill_count": self.local_prefill_count,
                "remote_prefill_count": self.remote_prefill_count,
                "total_decisions": total,
                "remote_prefill_ratio": self.remote_prefill_count / total if total > 0 else 0.0,
                "queue_full_rejections": self.queue_full_rejections,
                "config": {
                    "prefill_length_threshold": self.prefill_length_threshold,
                    "queue_capacity_threshold": self.queue_capacity_threshold,
                },
            }


# ============================================================================
# Prefill Queue
# ============================================================================

@dataclass
class PrefillQueueItem:
    """Item in prefill queue."""
    request_id: str
    input_tokens: list[int]
    kv_blocks: list[str]
    enqueue_time: float
    priority: int = 0


class PrefillQueue:
    """
    Prefill queue for caching and load balancing remote prefill requests.

    Uses NATS-style pub/sub pattern for distributed prefill workers.
    """

    def __init__(self, max_capacity: int = 100):
        self.max_capacity = max_capacity
        self.queue: deque[PrefillQueueItem] = deque()

        # Metrics
        self.total_enqueued = 0
        self.total_dequeued = 0
        self.total_rejected = 0
        self.max_depth_observed = 0

        self._lock = threading.Lock()

    def enqueue(self, item: PrefillQueueItem) -> bool:
        """
        Add item to queue.

        Returns:
            True if enqueued, False if queue full
        """
        with self._lock:
            if len(self.queue) >= self.max_capacity:
                self.total_rejected += 1
                return False

            self.queue.append(item)
            self.total_enqueued += 1
            self.max_depth_observed = max(self.max_depth_observed, len(self.queue))

            return True

    def dequeue(self) -> PrefillQueueItem | None:
        """Remove and return next item from queue."""
        with self._lock:
            if not self.queue:
                return None

            item = self.queue.popleft()
            self.total_dequeued += 1
            return item

    def peek(self) -> PrefillQueueItem | None:
        """Get next item without removing."""
        with self._lock:
            return self.queue[0] if self.queue else None

    def get_depth(self) -> int:
        """Get current queue depth."""
        with self._lock:
            return len(self.queue)

    def get_stats(self) -> dict[str, Any]:
        """Get queue statistics."""
        with self._lock:
            current_depth = len(self.queue)
            avg_wait_time = 0.0

            if self.queue:
                current_time = time.time()
                wait_times = [current_time - item.enqueue_time for item in self.queue]
                avg_wait_time = sum(wait_times) / len(wait_times)

            return {
                "current_depth": current_depth,
                "max_depth": self.max_depth_observed,
                "capacity": self.max_capacity,
                "utilization_pct": (current_depth / self.max_capacity * 100) if self.max_capacity > 0 else 0,
                "total_enqueued": self.total_enqueued,
                "total_dequeued": self.total_dequeued,
                "total_rejected": self.total_rejected,
                "rejection_rate": self.total_rejected / self.total_enqueued if self.total_enqueued > 0 else 0.0,
                "avg_wait_time_ms": avg_wait_time * 1000,
            }


# ============================================================================
# Dynamic Endpoint Registry
# ============================================================================

@dataclass
class EndpointInfo:
    """Registered endpoint information."""
    endpoint_id: str
    url: str
    model: str
    backend: str  # vllm, sglang, trtllm
    status: str = "healthy"  # healthy, degraded, unhealthy
    registered_at: float = 0.0
    last_health_check: float = 0.0
    request_count: int = 0
    error_count: int = 0
    avg_latency_ms: float = 0.0

    def __post_init__(self):
        if self.registered_at == 0.0:
            self.registered_at = time.time()


class DynamicEndpointRegistry:
    """
    Dynamic endpoint registration and management.

    Allows runtime registration of inference endpoints with
    health tracking and status monitoring.
    """

    def __init__(self):
        self.endpoints: dict[str, EndpointInfo] = {}
        self.endpoints_by_model: dict[str, list[str]] = defaultdict(list)

        self._lock = threading.Lock()

    def register_endpoint(
        self,
        url: str,
        model: str,
        backend: str = "vllm",
    ) -> str:
        """
        Register a new endpoint.

        Returns:
            endpoint_id
        """
        endpoint_id = f"ep_{uuid.uuid4().hex[:12]}"

        with self._lock:
            endpoint = EndpointInfo(
                endpoint_id=endpoint_id,
                url=url,
                model=model,
                backend=backend,
            )

            self.endpoints[endpoint_id] = endpoint
            self.endpoints_by_model[model].append(endpoint_id)

        return endpoint_id

    def unregister_endpoint(self, endpoint_id: str) -> bool:
        """Unregister endpoint."""
        with self._lock:
            if endpoint_id not in self.endpoints:
                return False

            endpoint = self.endpoints.pop(endpoint_id)

            # Remove from model mapping
            if endpoint.model in self.endpoints_by_model:
                if endpoint_id in self.endpoints_by_model[endpoint.model]:
                    self.endpoints_by_model[endpoint.model].remove(endpoint_id)

            return True

    def update_health(self, endpoint_id: str, status: str):
        """Update endpoint health status."""
        with self._lock:
            if endpoint_id in self.endpoints:
                self.endpoints[endpoint_id].status = status
                self.endpoints[endpoint_id].last_health_check = time.time()

    def record_request(self, endpoint_id: str, success: bool, latency_ms: float):
        """Record request metrics for endpoint."""
        with self._lock:
            if endpoint_id not in self.endpoints:
                return

            endpoint = self.endpoints[endpoint_id]
            endpoint.request_count += 1

            if not success:
                endpoint.error_count += 1

            # Update running average latency
            n = endpoint.request_count
            endpoint.avg_latency_ms = ((endpoint.avg_latency_ms * (n - 1)) + latency_ms) / n

    def get_endpoints_for_model(self, model: str) -> list[EndpointInfo]:
        """Get all endpoints serving a specific model."""
        with self._lock:
            endpoint_ids = self.endpoints_by_model.get(model, [])
            return [self.endpoints[eid] for eid in endpoint_ids if eid in self.endpoints]

    def get_healthy_endpoints(self, model: str | None = None) -> list[EndpointInfo]:
        """Get all healthy endpoints, optionally filtered by model."""
        with self._lock:
            endpoints = self.endpoints.values()

            if model:
                endpoints = [e for e in endpoints if e.model == model]

            return [e for e in endpoints if e.status == "healthy"]

    def get_stats(self) -> dict[str, Any]:
        """Get registry statistics."""
        with self._lock:
            total = len(self.endpoints)
            healthy = sum(1 for e in self.endpoints.values() if e.status == "healthy")
            degraded = sum(1 for e in self.endpoints.values() if e.status == "degraded")
            unhealthy = sum(1 for e in self.endpoints.values() if e.status == "unhealthy")

            return {
                "total_endpoints": total,
                "healthy_endpoints": healthy,
                "degraded_endpoints": degraded,
                "unhealthy_endpoints": unhealthy,
                "endpoints_by_model": {
                    model: len(endpoints)
                    for model, endpoints in self.endpoints_by_model.items()
                },
                "endpoints": [
                    {
                        "id": e.endpoint_id,
                        "url": e.url,
                        "model": e.model,
                        "backend": e.backend,
                        "status": e.status,
                        "requests": e.request_count,
                        "errors": e.error_count,
                        "error_rate": e.error_count / e.request_count if e.request_count > 0 else 0.0,
                        "avg_latency_ms": e.avg_latency_ms,
                    }
                    for e in self.endpoints.values()
                ],
            }


# ============================================================================
# Complete Dynamo System
# ============================================================================

class DynamoSystem:
    """
    Complete NVIDIA Dynamo system simulation.

    Integrates all components:
    - KVBM with 4-tier memory
    - SLA-based planner
    - Disaggregated router
    - Prefill queue
    - Dynamic endpoint registry
    """

    def __init__(
        self,
        sla_target: SLATarget | None = None,
        enable_disaggregation: bool = True,
    ):
        # Initialize KVBM
        self.kvbm = KVBlockManager(
            g1_capacity=1000,   # GPU: 1000 blocks
            g2_capacity=5000,   # CPU: 5000 blocks
            g3_capacity=20000,  # SSD: 20000 blocks
            g4_capacity=100000, # Remote: 100000 blocks
        )

        # Initialize SLA planner
        if sla_target is None:
            sla_target = SLATarget(ttft_ms=500.0, itl_ms=50.0, throughput_rps=10.0)

        self.planner = SLABasedPlanner(
            sla_target=sla_target,
            predictor_type=LoadPredictor.CONSTANT,
            adjustment_interval_seconds=60,
        )

        # Initialize disaggregated router
        self.router = DisaggregatedRouter(
            prefill_length_threshold=512,
            queue_capacity_threshold=10,
        )

        # Initialize prefill queue
        self.prefill_queue = PrefillQueue(max_capacity=100)

        # Initialize endpoint registry
        self.endpoint_registry = DynamicEndpointRegistry()

        # System state
        self.enable_disaggregation = enable_disaggregation
        self.total_requests_processed = 0

    def process_request(
        self,
        request_id: str,
        input_length: int,
        model: str,
    ) -> dict[str, Any]:
        """
        Process request through Dynamo system.

        Returns:
            Processing decision and metrics
        """
        # Make disaggregation decision
        if self.enable_disaggregation:
            decision = self.router.make_decision(
                input_length=input_length,
                current_queue_depth=self.prefill_queue.get_depth(),
            )
        else:
            decision = DisaggregationDecision(
                use_remote_prefill=False,
                reason="disaggregation_disabled",
            )

        # Allocate KV blocks
        num_blocks_needed = (input_length + 15) // 16  # Round up to blocks

        allocated_blocks = []
        for _ in range(num_blocks_needed):
            block = self.kvbm.allocate(MemoryTier.G1_GPU_HBM, size_tokens=16)
            if block:
                allocated_blocks.append(block.block_id)

        # If remote prefill, enqueue
        if decision.use_remote_prefill:
            queue_item = PrefillQueueItem(
                request_id=request_id,
                input_tokens=list(range(input_length)),  # Simulated tokens
                kv_blocks=allocated_blocks,
                enqueue_time=time.time(),
            )
            enqueued = self.prefill_queue.enqueue(queue_item)

            if not enqueued:
                decision.reason = "queue_full_fallback_local"
                decision.use_remote_prefill = False

        self.total_requests_processed += 1

        return {
            "request_id": request_id,
            "decision": {
                "use_remote_prefill": decision.use_remote_prefill,
                "reason": decision.reason,
            },
            "kv_blocks_allocated": len(allocated_blocks),
            "blocks": allocated_blocks,
        }

    def get_comprehensive_stats(self) -> dict[str, Any]:
        """Get complete system statistics."""
        return {
            "system": {
                "total_requests_processed": self.total_requests_processed,
                "disaggregation_enabled": self.enable_disaggregation,
            },
            "kvbm": self.kvbm.get_stats(),
            "planner": self.planner.get_stats(),
            "router": self.router.get_stats(),
            "prefill_queue": self.prefill_queue.get_stats(),
            "endpoints": self.endpoint_registry.get_stats(),
        }
