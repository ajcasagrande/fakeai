"""
Advanced KV Cache Reuse Simulator with Realistic Behavior.

This module implements an extremely realistic KV cache simulation including:
- Advanced radix tree with compression and eviction
- Memory capacity management
- Multi-level cache (L1 per worker, L2 shared)
- Learning-based adaptive routing
- Cache coherency and invalidation
- Temporal locality simulation
- Predictive prefetching
"""

import hashlib
import heapq
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any

# ============================================================================
# Advanced Radix Tree with Compression and Eviction
# ============================================================================


@dataclass
class AdvancedRadixNode:
    """
    Advanced radix tree node with compression and LRU tracking.

    Supports path compression (merge single-child nodes) and detailed metrics.
    """

    token_sequence: tuple[int, ...] = field(
        default_factory=tuple)  # Compressed path
    children: dict[int, "AdvancedRadixNode"] = field(default_factory=dict)
    cache_blocks: list[str] = field(default_factory=list)
    worker_ids: set[str] = field(default_factory=set)
    hit_count: int = 0
    last_access: float = 0.0
    creation_time: float = field(default_factory=time.time)
    memory_bytes: int = 0
    version: int = 1  # For cache coherency
    is_dirty: bool = False  # For write-through tracking
    access_frequency: float = 0.0  # Exponentially weighted moving average


class AdvancedRadixTree:
    """
    Advanced radix tree with compression, eviction, and memory tracking.

    Features:
    - Path compression (merges single-child chains)
    - LRU eviction when capacity reached
    - Memory usage tracking
    - Tree balancing statistics
    - Prefix search optimization
    """

    def __init__(self, block_size: int = 16, max_memory_mb: float = 512.0):
        self.root = AdvancedRadixNode()
        self.block_size = block_size
        self.max_memory_bytes = int(max_memory_mb * 1024 * 1024)
        self.current_memory_bytes = 0
        self.total_nodes = 1  # Start with root
        self.compressed_paths = 0
        self.evicted_nodes = 0
        self.total_insertions = 0
        self._lock = threading.Lock()
        self._lru_queue: list[tuple[float, int, AdvancedRadixNode]] = (
            []
        )  # (last_access, counter, node)
        self._counter = 0  # Monotonic counter for tie-breaking

    def insert(self, tokens: list[int], worker_id: str) -> int:
        """
        Insert token sequence with path compression.

        Args:
            tokens: Token IDs to insert
            worker_id: Worker that has this prefix cached

        Returns:
            Number of blocks inserted
        """
        with self._lock:
            self._ensure_capacity()

            node = self.root
            blocks_inserted = 0
            i = 0

            while i < len(tokens):
                token = tokens[i]

                # Find or create child
                if token not in node.children:
                    # Check for compression opportunity
                    remaining = tokens[i:]
                    new_node = self._create_compressed_node(
                        remaining, worker_id)
                    node.children[token] = new_node
                    blocks_inserted += self._calculate_blocks(len(remaining))
                    self.total_nodes += 1

                    # Mark blocks in the new node
                    for j in range(
                        self.block_size, len(remaining) + 1, self.block_size
                    ):
                        # Use stable hashing for block IDs
                        token_bytes = str(tuple(tokens[:i + j])).encode()
                        block_hash = hashlib.md5(token_bytes).hexdigest()[:16]
                        block_id = f"block_{block_hash}"
                        new_node.cache_blocks.append(block_id)
                        new_node.worker_ids.add(worker_id)

                    node = new_node
                    break

                node = node.children[token]
                i += 1

                # Handle compressed paths
                seq_len = len(node.token_sequence)
                if seq_len > 1:
                    # Check if token sequence matches
                    remaining = tokens[
                        i: i + seq_len - 1
                    ]  # -1 because we already advanced by 1
                    if (
                        len(remaining) == seq_len - 1 and
                        tuple([token] + remaining) == node.token_sequence
                    ):
                        i += seq_len - 1
                    else:
                        # Need to split compressed node - for now just continue
                        pass

                # Mark complete blocks
                if i % self.block_size == 0 and i > 0:
                    # Use stable hashing for block IDs
                    token_bytes = str(tuple(tokens[:i])).encode()
                    block_hash = hashlib.md5(token_bytes).hexdigest()[:16]
                    block_id = f"block_{block_hash}"
                    if block_id not in node.cache_blocks:
                        node.cache_blocks.append(block_id)
                        blocks_inserted += 1
                    node.worker_ids.add(worker_id)

            # Update access patterns
            node.last_access = time.time()
            node.hit_count += 1
            node.access_frequency = self._update_ewma(
                node.access_frequency, 1.0)
            self.total_insertions += 1

            return blocks_inserted

    def _create_compressed_node(
        self, tokens: list[int], worker_id: str
    ) -> AdvancedRadixNode:
        """Create a compressed node for a token sequence."""
        node = AdvancedRadixNode(
            token_sequence=tuple(tokens),
            creation_time=time.time(),
            last_access=time.time(),
        )

        # Calculate memory usage
        node.memory_bytes = (
            len(tokens) * 8 +  # Token IDs (int64)
            len(worker_id) * 2 +  # Worker ID string
            256  # Overhead (dicts, lists, etc.)
        )
        self.current_memory_bytes += node.memory_bytes
        self.compressed_paths += 1

        # Add to LRU queue (use monotonic counter for stable ordering)
        self._counter += 1
        heapq.heappush(
            self._lru_queue,
            (node.last_access,
             self._counter,
             node))

        return node

    def _split_compressed_node(
            self,
            node: AdvancedRadixNode,
            new_sequence: list[int]):
        """Split a compressed node when sequences diverge."""
        # Find common prefix
        common_len = 0
        for i in range(min(len(node.token_sequence), len(new_sequence))):
            if node.token_sequence[i] == new_sequence[i]:
                common_len += 1
            else:
                break

        if common_len > 0:
            # Split the node
            old_suffix = node.token_sequence[common_len:]
            new_suffix = new_sequence[common_len:]

            # Update current node to common prefix
            node.token_sequence = node.token_sequence[:common_len]

            # Create child for old suffix if it exists
            if old_suffix:
                old_child = AdvancedRadixNode(token_sequence=old_suffix)
                node.children[old_suffix[0]] = old_child
                self.total_nodes += 1

            # Create child for new suffix if it exists
            if new_suffix:
                new_child = AdvancedRadixNode(token_sequence=new_suffix)
                node.children[new_suffix[0]] = new_child
                self.total_nodes += 1

    def find_longest_prefix(
        self, tokens: list[int]
    ) -> tuple[int, list[str], set[str], int]:
        """
        Find longest matching prefix with detailed stats.

        Args:
            tokens: Token IDs to match

        Returns:
            (matched_tokens, matched_blocks, worker_ids, tree_depth)
        """
        with self._lock:
            node = self.root
            matched_tokens = 0
            matched_blocks = []
            workers = set()
            depth = 0

            i = 0
            while i < len(tokens):
                token = tokens[i]

                if token not in node.children:
                    break

                node = node.children[token]
                depth += 1
                matched_tokens += 1
                i += 1

                # Handle compressed paths
                seq_len = len(node.token_sequence)
                if seq_len > 1:
                    # Check if remaining tokens match compressed sequence
                    remaining = tokens[
                        i: i + seq_len - 1
                    ]  # -1 because we already counted first token
                    match_len = 0
                    for j in range(min(len(remaining), seq_len - 1)):
                        if (
                            remaining[j] == node.token_sequence[j + 1]
                        ):  # +1 to skip first token already matched
                            match_len += 1
                            matched_tokens += 1
                        else:
                            break
                    i += match_len

                    # If didn't fully match, stop
                    if match_len < len(remaining) and match_len < seq_len - 1:
                        break

                # Collect blocks at block boundaries
                if (
                    matched_tokens > 0 and
                    matched_tokens % self.block_size == 0 and
                    node.cache_blocks
                ):
                    matched_blocks.extend(node.cache_blocks)
                    workers = workers.union(node.worker_ids)
                    node.hit_count += 1
                    node.access_frequency = self._update_ewma(
                        node.access_frequency, 1.0
                    )

            if matched_tokens > 0:
                node.last_access = time.time()

            return matched_tokens, matched_blocks, workers, depth

    def _ensure_capacity(self):
        """Evict least recently used nodes if over capacity."""
        while self.current_memory_bytes > self.max_memory_bytes and self._lru_queue:
            # Get least recently used node
            last_access, counter, node = heapq.heappop(self._lru_queue)

            # Only evict if not recently accessed
            if time.time() - node.last_access > 60.0:  # 60 second threshold
                self._evict_node(node)

    def _evict_node(self, node: AdvancedRadixNode):
        """Evict a node and free its memory."""
        self.current_memory_bytes -= node.memory_bytes
        self.evicted_nodes += 1
        node.cache_blocks.clear()
        node.worker_ids.clear()

    def _calculate_blocks(self, token_count: int) -> int:
        """Calculate number of complete blocks in token sequence."""
        return token_count // self.block_size

    def _update_ewma(
        self, current: float, new_value: float, alpha: float = 0.1
    ) -> float:
        """Update exponentially weighted moving average."""
        return alpha * new_value + (1 - alpha) * current

    def compress_tree(self) -> int:
        """
        Compress tree by merging single-child chains.

        Returns:
            Number of nodes eliminated
        """
        with self._lock:
            eliminated = self._compress_subtree(self.root)
            self.total_nodes -= eliminated
            return eliminated

    def _compress_subtree(self, node: AdvancedRadixNode) -> int:
        """Recursively compress a subtree."""
        eliminated = 0

        # Compress children first
        for child in list(node.children.values()):
            eliminated += self._compress_subtree(child)

        # If single child, merge
        if len(node.children) == 1 and not node.cache_blocks:
            child = next(iter(node.children.values()))
            # Merge token sequences
            node.token_sequence = node.token_sequence + child.token_sequence
            node.children = child.children
            node.cache_blocks = child.cache_blocks
            node.worker_ids = child.worker_ids
            eliminated += 1
            self.compressed_paths += 1

        return eliminated

    def get_stats(self) -> dict[str, Any]:
        """Get comprehensive tree statistics."""
        with self._lock:
            avg_chain_length = self._calculate_avg_chain_length()
            depth_histogram = self._calculate_depth_histogram()

            return {
                "total_nodes": self.total_nodes,
                "compressed_paths": self.compressed_paths,
                "memory_bytes": self.current_memory_bytes,
                "memory_mb": round(self.current_memory_bytes / (1024 * 1024), 2),
                "max_memory_mb": round(self.max_memory_bytes / (1024 * 1024), 2),
                "memory_utilization": round(
                    self.current_memory_bytes / self.max_memory_bytes * 100, 2
                ),
                "evicted_nodes": self.evicted_nodes,
                "total_insertions": self.total_insertions,
                "avg_chain_length": round(avg_chain_length, 2),
                "depth_histogram": depth_histogram,
                "block_size": self.block_size,
            }

    def _calculate_avg_chain_length(self) -> float:
        """Calculate average chain length in tree."""
        total_depth = 0
        leaf_count = 0

        def traverse(node: AdvancedRadixNode, depth: int):
            nonlocal total_depth, leaf_count

            if not node.children:
                total_depth += depth
                leaf_count += 1
            else:
                for child in node.children.values():
                    traverse(child, depth + 1 + len(child.token_sequence))

        traverse(self.root, 0)

        return total_depth / leaf_count if leaf_count > 0 else 0.0

    def _calculate_depth_histogram(self) -> dict[str, int]:
        """Calculate histogram of tree depths."""
        histogram = defaultdict(int)

        def traverse(node: AdvancedRadixNode, depth: int):
            if not node.children:
                # Bin depths into ranges
                bin_key = f"{(depth // 10) * 10}-{(depth // 10) * 10 + 9}"
                histogram[bin_key] += 1
            else:
                for child in node.children.values():
                    traverse(child, depth + 1 + len(child.token_sequence))

        traverse(self.root, 0)

        return dict(histogram)


# ============================================================================
# Cache Memory Manager
# ============================================================================


@dataclass
class CacheBlock:
    """Represents a cached block of tokens."""

    block_id: str
    tokens: tuple[int, ...]
    size_bytes: int
    creation_time: float
    last_access: float
    access_count: int = 0
    worker_id: str = ""
    version: int = 1
    is_dirty: bool = False


class CacheMemoryManager:
    """
    Manages cache memory with capacity limits and eviction.

    Features:
    - Per-worker memory limits
    - LRU eviction policy
    - Cold start simulation
    - Cache warming tracking
    - Temporal locality simulation
    """

    def __init__(
        self,
        capacity_per_worker_mb: float = 24.0 * 1024,  # 24 GB per worker
        block_size: int = 16,
    ):
        self.capacity_per_worker_bytes = int(
            capacity_per_worker_mb * 1024 * 1024)
        self.block_size = block_size
        self.worker_caches: dict[str,
                                 dict[str, CacheBlock]] = defaultdict(dict)
        self.worker_memory_usage: dict[str, int] = defaultdict(int)
        self.global_cache: dict[str, CacheBlock] = {}  # L2 shared cache
        self.global_memory_usage = 0
        self.global_capacity_bytes = int(
            capacity_per_worker_mb * 1024 * 1024 * 4
        )  # 4x worker
        self.eviction_counts: dict[str, int] = defaultdict(int)
        self.eviction_reasons: dict[str, int] = defaultdict(int)
        self.cache_warming_phase = True  # Start cold
        self.warming_requests = 0
        self.warming_threshold = 100  # Requests to warm up
        self._lock = threading.Lock()

    def allocate_block(
        self, worker_id: str, block_id: str, tokens: tuple[int, ...]
    ) -> bool:
        """
        Allocate a cache block for a worker.

        Args:
            worker_id: Worker to allocate for
            block_id: Unique block identifier
            tokens: Token sequence

        Returns:
            True if allocated, False if capacity exceeded
        """
        with self._lock:
            # Calculate block size
            size_bytes = len(tokens) * 8 + 256  # 8 bytes per token + overhead

            # Check if already cached
            if block_id in self.worker_caches[worker_id]:
                # Update access time
                block = self.worker_caches[worker_id][block_id]
                block.last_access = time.time()
                block.access_count += 1
                return True

            # Check capacity
            if (
                self.worker_memory_usage[worker_id] + size_bytes >
                self.capacity_per_worker_bytes
            ):
                # Evict LRU blocks
                if not self._evict_lru_blocks(worker_id, size_bytes):
                    self.eviction_reasons["capacity_exceeded"] += 1
                    return False

            # Allocate block
            block = CacheBlock(
                block_id=block_id,
                tokens=tokens,
                size_bytes=size_bytes,
                creation_time=time.time(),
                last_access=time.time(),
                worker_id=worker_id,
            )

            self.worker_caches[worker_id][block_id] = block
            self.worker_memory_usage[worker_id] += size_bytes

            # Update cache warming
            if self.cache_warming_phase:
                self.warming_requests += 1
                if self.warming_requests >= self.warming_threshold:
                    self.cache_warming_phase = False

            # Promote to L2 if frequently accessed
            if block.access_count > 5:
                self._promote_to_l2(block)

            return True

    def get_block(self, worker_id: str, block_id: str) -> CacheBlock | None:
        """Get a cached block if it exists."""
        # Check L1 (worker cache) - no lock needed for read
        if block_id in self.worker_caches[worker_id]:
            with self._lock:
                # Double-check with lock
                if block_id in self.worker_caches[worker_id]:
                    block = self.worker_caches[worker_id][block_id]
                    block.last_access = time.time()
                    block.access_count += 1

                    # Simulate temporal locality
                    if time.time() - block.creation_time < 300:  # 5 minute window
                        block.access_count += 2  # Boost recent blocks

                    return block

        # Check L2 (global cache)
        if block_id in self.global_cache:
            with self._lock:
                if block_id in self.global_cache:  # Double-check with lock
                    block = self.global_cache[block_id]
                    block.last_access = time.time()
                    block.access_count += 1

            # Promote back to L1 (outside lock to avoid recursion)
            self._demote_from_l2(block_id)
            self.allocate_block(worker_id, block_id, block.tokens)

            return block

        return None

    def _evict_lru_blocks(self, worker_id: str, size_needed: int) -> bool:
        """Evict least recently used blocks to free space."""
        worker_cache = self.worker_caches[worker_id]

        # Sort blocks by last access time
        sorted_blocks = sorted(
            worker_cache.items(),
            key=lambda x: x[1].last_access)

        freed_bytes = 0
        for block_id, block in sorted_blocks:
            if freed_bytes >= size_needed:
                break

            # Evict block
            del worker_cache[block_id]
            self.worker_memory_usage[worker_id] -= block.size_bytes
            freed_bytes += block.size_bytes
            self.eviction_counts[worker_id] += 1
            self.eviction_reasons["lru_eviction"] += 1

        return freed_bytes >= size_needed

    def _promote_to_l2(self, block: CacheBlock):
        """Promote frequently accessed block to L2 global cache."""
        with self._lock:
            if block.block_id in self.global_cache:
                return

            # Check L2 capacity
            if self.global_memory_usage + block.size_bytes > self.global_capacity_bytes:
                # Evict from L2
                self._evict_l2_blocks(block.size_bytes)

            self.global_cache[block.block_id] = block
            self.global_memory_usage += block.size_bytes

    def _demote_from_l2(self, block_id: str):
        """Remove block from L2 cache."""
        if block_id in self.global_cache:
            block = self.global_cache[block_id]
            self.global_memory_usage -= block.size_bytes
            del self.global_cache[block_id]

    def _evict_l2_blocks(self, size_needed: int):
        """Evict blocks from L2 cache."""
        sorted_blocks = sorted(
            self.global_cache.items(), key=lambda x: x[1].last_access
        )

        freed_bytes = 0
        for block_id, block in sorted_blocks:
            if freed_bytes >= size_needed:
                break

            del self.global_cache[block_id]
            self.global_memory_usage -= block.size_bytes
            freed_bytes += block.size_bytes
            self.eviction_reasons["l2_eviction"] += 1

    def get_stats(self) -> dict[str, Any]:
        """Get memory manager statistics."""
        with self._lock:
            total_l1_memory = sum(self.worker_memory_usage.values())
            total_evictions = sum(self.eviction_counts.values())

            return {
                "l1_memory_bytes": total_l1_memory,
                "l1_memory_mb": round(total_l1_memory / (1024 * 1024), 2),
                "l2_memory_bytes": self.global_memory_usage,
                "l2_memory_mb": round(self.global_memory_usage / (1024 * 1024), 2),
                "total_memory_mb": round(
                    (total_l1_memory + self.global_memory_usage) / (1024 * 1024), 2
                ),
                "cache_warming_phase": self.cache_warming_phase,
                "warming_progress": min(
                    100, round(self.warming_requests / self.warming_threshold * 100, 2)
                ),
                "total_evictions": total_evictions,
                "eviction_by_worker": dict(self.eviction_counts),
                "eviction_reasons": dict(self.eviction_reasons),
                "worker_memory_usage": {
                    wid: round(mem / (1024 * 1024), 2)
                    for wid, mem in self.worker_memory_usage.items()
                },
            }


# ============================================================================
# Adaptive Smart Router with Learning
# ============================================================================


@dataclass
class WorkerPerformance:
    """Track worker performance for adaptive routing."""

    worker_id: str
    success_count: int = 0
    failure_count: int = 0
    total_latency_ms: float = 0.0
    request_count: int = 0
    cache_hit_rate: float = 0.0
    avg_prefill_time_ms: float = 0.0
    affinity_scores: dict[str, float] = field(
        default_factory=dict)  # user -> score
    load_factor: float = 1.0  # Dynamic load multiplier


class AdaptiveRouter:
    """
    Learning-based adaptive router with affinity and predictive features.

    Features:
    - Track worker success rates
    - Affinity-based routing (sticky sessions)
    - Predictive prefetching simulation
    - Load shedding under extreme load
    - Dynamic worker pool scaling
    """

    def __init__(
        self,
        radix_tree: AdvancedRadixTree,
        memory_manager: CacheMemoryManager,
        kv_overlap_weight: float = 1.0,
        load_balance_weight: float = 0.5,
        affinity_weight: float = 0.3,
        num_workers: int = 4,
        max_workers: int = 16,
    ):
        self.radix_tree = radix_tree
        self.memory_manager = memory_manager
        self.kv_overlap_weight = kv_overlap_weight
        self.load_balance_weight = load_balance_weight
        self.affinity_weight = affinity_weight
        self.num_workers = num_workers
        self.max_workers = max_workers

        # Worker tracking
        self.workers: dict[str, WorkerPerformance] = {}
        self.active_requests: dict[str, int] = defaultdict(int)
        self.request_history: deque[tuple[str, float]] = deque(
            maxlen=1000
        )  # (worker_id, timestamp)

        # Initialize workers
        for i in range(num_workers):
            worker_id = f"worker-{i}"
            self.workers[worker_id] = WorkerPerformance(worker_id=worker_id)

        # Routing intelligence
        # user_id -> preferred_worker_id
        self.user_affinity: dict[str, str] = {}
        self.prefetch_predictions: dict[str, list[int]] = (
            {}
        )  # user_id -> predicted tokens
        self.load_shedding_active = False
        self.load_shedding_threshold = 0.9  # 90% capacity

        self._lock = threading.Lock()

    def route_request(
        self,
        tokens: list[int],
        estimated_output_tokens: int = 100,
        user_id: str | None = None,
    ) -> tuple[str, int, int]:
        """
        Route request using adaptive learning-based algorithm.

        Args:
            tokens: Input token IDs
            estimated_output_tokens: Expected output length
            user_id: Optional user ID for affinity routing

        Returns:
            (worker_id, matched_tokens, matched_blocks_count)
        """
        with self._lock:
            # Check if scaling needed
            self._check_scaling()

            # Check for load shedding
            if self._should_shed_load():
                raise RuntimeError("Load shedding active - server at capacity")

            # Find matching prefixes
            matched_tokens, matched_blocks, candidate_workers, depth = (
                self.radix_tree.find_longest_prefix(tokens)
            )

            # Predictive prefetching simulation
            if user_id and user_id in self.prefetch_predictions:
                predicted = self.prefetch_predictions[user_id]
                # If prediction matches, boost cache hit
                if tokens[: len(predicted)] == predicted:
                    matched_tokens = max(matched_tokens, len(predicted))

            best_worker_id = None
            best_cost = float("inf")

            for worker_id, worker in self.workers.items():
                # Calculate routing cost with learning
                cost = self._calculate_adaptive_cost(
                    tokens=tokens,
                    matched_tokens=(
                        matched_tokens if worker_id in candidate_workers else 0
                    ),
                    worker=worker,
                    estimated_output_tokens=estimated_output_tokens,
                    user_id=user_id,
                )

                if cost < best_cost:
                    best_cost = cost
                    best_worker_id = worker_id

            # Update affinity
            if user_id and best_worker_id:
                self._update_affinity(user_id, best_worker_id)

            # Track request
            self.active_requests[best_worker_id] += 1
            self.request_history.append((best_worker_id, time.time()))

            return best_worker_id, matched_tokens, len(matched_blocks)

    def _calculate_adaptive_cost(
        self,
        tokens: list[int],
        matched_tokens: int,
        worker: WorkerPerformance,
        estimated_output_tokens: int,
        user_id: str | None,
    ) -> float:
        """Calculate routing cost with adaptive learning."""
        # Base cost: prefill + decode
        total_tokens = len(tokens)
        tokens_to_prefill = total_tokens - matched_tokens
        prefill_blocks = tokens_to_prefill / self.radix_tree.block_size
        decode_blocks = estimated_output_tokens / self.radix_tree.block_size

        # Worker load
        load = self.active_requests[worker.worker_id]

        # Success rate factor (penalize low-performing workers)
        total_requests = worker.success_count + worker.failure_count
        success_rate = (worker.success_count /
                        total_requests if total_requests > 0 else 0.5)
        performance_penalty = (1.0 - success_rate) * 10  # 0-10 penalty

        # Affinity bonus (reduce cost for preferred worker)
        affinity_bonus = 0.0
        if user_id and user_id in self.user_affinity:
            if self.user_affinity[user_id] == worker.worker_id:
                affinity_bonus = -self.affinity_weight * prefill_blocks

        # Dynamic load factor (adaptive to worker performance)
        load_factor = worker.load_factor

        # Combined cost
        cost = (
            self.kv_overlap_weight * prefill_blocks * load_factor +
            decode_blocks +
            self.load_balance_weight * load +
            performance_penalty +
            affinity_bonus
        )

        return cost

    def complete_request(
        self,
        worker_id: str,
        tokens: list[int],
        output_tokens: int,
        success: bool = True,
        latency_ms: float = 0.0,
    ):
        """Complete a request and update worker performance."""
        with self._lock:
            self.active_requests[worker_id] -= 1

            worker = self.workers[worker_id]
            if success:
                worker.success_count += 1
            else:
                worker.failure_count += 1

            worker.request_count += 1
            worker.total_latency_ms += latency_ms

            # Update load factor based on performance
            avg_latency = worker.total_latency_ms / worker.request_count
            # Normalize to [0.5, 2.0] range
            worker.load_factor = 0.5 + min(1.5, avg_latency / 1000.0)

        # Update caches
        if success:
            self.radix_tree.insert(tokens, worker_id)

            # Allocate blocks to memory manager
            for i in range(0, len(tokens), self.radix_tree.block_size):
                block_tokens = tuple(tokens[i: i + self.radix_tree.block_size])
                # Use stable hashing for block IDs
                token_bytes = str(block_tokens).encode()
                block_hash = hashlib.md5(token_bytes).hexdigest()[:16]
                block_id = f"block_{block_hash}"
                self.memory_manager.allocate_block(
                    worker_id, block_id, block_tokens)

    def _update_affinity(self, user_id: str, worker_id: str):
        """Update user-worker affinity for sticky sessions."""
        self.user_affinity[user_id] = worker_id

        # Update affinity score
        worker = self.workers[worker_id]
        if user_id not in worker.affinity_scores:
            worker.affinity_scores[user_id] = 0.0

        # Exponential moving average
        worker.affinity_scores[user_id] = (
            0.9 * worker.affinity_scores[user_id] + 0.1 * 1.0
        )

    def _check_scaling(self):
        """Check if worker pool should scale up or down."""
        total_load = sum(self.active_requests.values())
        capacity = len(self.workers)
        utilization = total_load / capacity if capacity > 0 else 0

        # Scale up if high utilization and below max
        if utilization > 0.8 and len(self.workers) < self.max_workers:
            new_worker_id = f"worker-{len(self.workers)}"
            self.workers[new_worker_id] = WorkerPerformance(
                worker_id=new_worker_id)
            self.num_workers += 1

        # Scale down if low utilization and above minimum
        elif utilization < 0.2 and len(self.workers) > 4:
            # Remove least utilized worker
            least_utilized = min(
                self.workers.keys(), key=lambda wid: self.active_requests[wid]
            )
            if self.active_requests[least_utilized] == 0:
                del self.workers[least_utilized]
                self.num_workers -= 1

    def _should_shed_load(self) -> bool:
        """Check if load shedding should be active."""
        total_load = sum(self.active_requests.values())
        capacity = len(self.workers) * 10  # Assume 10 concurrent per worker
        utilization = total_load / capacity if capacity > 0 else 0

        self.load_shedding_active = utilization > self.load_shedding_threshold
        return self.load_shedding_active

    def get_stats(self) -> dict[str, Any]:
        """Get comprehensive routing statistics."""
        with self._lock:
            worker_stats = {}
            for worker_id, worker in self.workers.items():
                total_requests = worker.success_count + worker.failure_count
                success_rate = (
                    worker.success_count / total_requests * 100
                    if total_requests > 0
                    else 0.0
                )
                avg_latency = (
                    worker.total_latency_ms / worker.request_count
                    if worker.request_count > 0
                    else 0.0
                )

                worker_stats[worker_id] = {
                    "active_requests": self.active_requests[worker_id],
                    "total_requests": worker.request_count,
                    "success_rate": round(success_rate, 2),
                    "avg_latency_ms": round(avg_latency, 2),
                    "load_factor": round(worker.load_factor, 2),
                    "affinity_count": len(worker.affinity_scores),
                }

            # Recent request distribution
            recent_distribution = defaultdict(int)
            for worker_id, _ in self.request_history:
                recent_distribution[worker_id] += 1

            return {
                "workers": worker_stats,
                "active_workers": len(self.workers),
                "max_workers": self.max_workers,
                "load_shedding_active": self.load_shedding_active,
                "total_affinities": len(self.user_affinity),
                "recent_distribution": dict(recent_distribution),
                "config": {
                    "kv_overlap_weight": self.kv_overlap_weight,
                    "load_balance_weight": self.load_balance_weight,
                    "affinity_weight": self.affinity_weight,
                },
            }


# ============================================================================
# Cache Coordinator (Multi-level Cache Orchestration)
# ============================================================================


class CacheCoordinator:
    """
    Coordinates multi-level cache with coherency and invalidation.

    Features:
    - L1 (per-worker) and L2 (shared) cache management
    - Cache coherency protocol
    - Version tracking
    - Dirty block tracking
    - Invalidation propagation
    """

    def __init__(
        self,
        radix_tree: AdvancedRadixTree,
        memory_manager: CacheMemoryManager,
        router: AdaptiveRouter,
    ):
        self.radix_tree = radix_tree
        self.memory_manager = memory_manager
        self.router = router

        # Coherency tracking
        self.block_versions: dict[str, int] = defaultdict(int)
        self.dirty_blocks: set[str] = set()
        self.invalidation_count = 0
        self.coherency_violations = 0

        self._lock = threading.Lock()

    def get_cached_data(
        self, worker_id: str, block_id: str
    ) -> tuple[CacheBlock | None, bool]:
        """
        Get cached data with coherency check.

        Args:
            worker_id: Worker requesting data
            block_id: Block identifier

        Returns:
            (block, is_coherent)
        """
        with self._lock:
            block = self.memory_manager.get_block(worker_id, block_id)

            if not block:
                return None, True

            # Check coherency
            current_version = self.block_versions[block_id]
            is_coherent = block.version == current_version

            if not is_coherent:
                self.coherency_violations += 1

            return block, is_coherent

    def invalidate_block(self, block_id: str):
        """Invalidate a block across all caches."""
        with self._lock:
            # Increment version
            self.block_versions[block_id] += 1
            self.invalidation_count += 1

            # Mark as dirty
            self.dirty_blocks.add(block_id)

            # Propagate invalidation to all workers
            for worker_cache in self.memory_manager.worker_caches.values():
                if block_id in worker_cache:
                    worker_cache[block_id].version = self.block_versions[block_id]

            # Invalidate in L2
            if block_id in self.memory_manager.global_cache:
                self.memory_manager.global_cache[block_id].version = (
                    self.block_versions[block_id]
                )

    def sync_caches(self):
        """Synchronize all cache levels."""
        with self._lock:
            # Write back dirty blocks
            for block_id in list(self.dirty_blocks):
                current_version = self.block_versions[block_id]

                # Update all caches to current version
                for worker_cache in self.memory_manager.worker_caches.values():
                    if block_id in worker_cache:
                        worker_cache[block_id].version = current_version
                        worker_cache[block_id].is_dirty = False

                # Update L2
                if block_id in self.memory_manager.global_cache:
                    self.memory_manager.global_cache[block_id].version = current_version
                    self.memory_manager.global_cache[block_id].is_dirty = False

                self.dirty_blocks.remove(block_id)

    def get_stats(self) -> dict[str, Any]:
        """Get cache coherency statistics."""
        with self._lock:
            return {
                "total_versions": len(self.block_versions),
                "dirty_blocks": len(self.dirty_blocks),
                "invalidation_count": self.invalidation_count,
                "coherency_violations": self.coherency_violations,
                "coherency_rate": round(
                    (1 - self.coherency_violations / max(1, self.invalidation_count)) *
                    100,
                    2,
                ),
            }


# ============================================================================
# Advanced KV Cache Metrics
# ============================================================================


class AdvancedKVCacheMetrics:
    """
    Comprehensive metrics for advanced KV cache system.

    Aggregates metrics from all components.
    """

    def __init__(
        self,
        radix_tree: AdvancedRadixTree,
        memory_manager: CacheMemoryManager,
        router: AdaptiveRouter,
        coordinator: CacheCoordinator,
    ):
        self.radix_tree = radix_tree
        self.memory_manager = memory_manager
        self.router = router
        self.coordinator = coordinator

        # Additional tracking
        self.cache_hits = 0
        self.cache_misses = 0
        self.total_requests = 0
        self.prefix_lengths: list[int] = []
        self._lock = threading.Lock()

    def record_lookup(self, matched_tokens: int, total_tokens: int):
        """Record a cache lookup."""
        with self._lock:
            self.total_requests += 1
            if matched_tokens > 0:
                self.cache_hits += 1
                self.prefix_lengths.append(matched_tokens)
            else:
                self.cache_misses += 1

    def get_comprehensive_stats(self) -> dict[str, Any]:
        """Get all metrics from all components."""
        with self._lock:
            cache_hit_rate = (self.cache_hits / max(1,
                                                    self.cache_hits + self.cache_misses) * 100)
            avg_prefix = (
                sum(self.prefix_lengths) / len(self.prefix_lengths)
                if self.prefix_lengths
                else 0
            )

            # Prefix distribution histogram
            prefix_histogram = defaultdict(int)
            for prefix_len in self.prefix_lengths:
                bin_key = f"{(prefix_len // 50) * 50}-{(prefix_len // 50) * 50 + 49}"
                prefix_histogram[bin_key] += 1

            return {
                "cache_performance": {
                    "cache_hit_rate": round(cache_hit_rate, 2),
                    "cache_hits": self.cache_hits,
                    "cache_misses": self.cache_misses,
                    "total_requests": self.total_requests,
                    "avg_prefix_length": round(avg_prefix, 2),
                    "prefix_distribution": dict(prefix_histogram),
                },
                "radix_tree": self.radix_tree.get_stats(),
                "memory_manager": self.memory_manager.get_stats(),
                "adaptive_router": self.router.get_stats(),
                "cache_coordinator": self.coordinator.get_stats(),
            }
