"""
KV Cache Reuse Simulator with AI-Dynamo Smart Routing.

This module simulates NVIDIA AI-Dynamo's KV cache reuse and smart routing capabilities,
including radix tree prefix matching, overlap scoring, and multi-worker load balancing.
"""
import hashlib
import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any


@dataclass
class RadixNode:
    """Node in radix tree for prefix tracking."""

    token: int | None = None
    children: dict[int, "RadixNode"] = field(default_factory=dict)
    cache_blocks: list[str] = field(default_factory=list)
    worker_ids: set[str] = field(default_factory=set)
    hit_count: int = 0
    last_access: float = 0.0


class RadixTree:
    """Radix tree for efficient prefix matching (SGLang-style)."""

    def __init__(self, block_size: int = 16):
        self.root = RadixNode()
        self.block_size = block_size
        self._lock = threading.Lock()

    def insert(self, tokens: list[int], worker_id: str) -> int:
        """
        Insert token sequence and associate with worker.

        Args:
            tokens: Token IDs to insert
            worker_id: Worker that has this prefix cached

        Returns:
            Number of blocks inserted
        """
        with self._lock:
            node = self.root
            blocks_inserted = 0

            for i, token in enumerate(tokens):
                if token not in node.children:
                    node.children[token] = RadixNode(token=token)
                node = node.children[token]

                # Mark complete blocks
                if (i + 1) % self.block_size == 0:
                    block_id = f"block_{hash(tuple(tokens[: i + 1]))}"
                    if block_id not in node.cache_blocks:
                        node.cache_blocks.append(block_id)
                        blocks_inserted += 1
                    node.worker_ids.add(worker_id)

            node.last_access = time.time()
            return blocks_inserted

    def find_longest_prefix(
        self, tokens: list[int]
    ) -> tuple[int, list[str], set[str]]:
        """
        Find longest matching prefix.

        Args:
            tokens: Token IDs to match

        Returns:
            (matched_tokens, matched_blocks, worker_ids)
        """
        with self._lock:
            node = self.root
            matched_tokens = 0
            matched_blocks = []
            workers = set()

            for i, token in enumerate(tokens):
                if token not in node.children:
                    break

                node = node.children[token]
                matched_tokens += 1

                # Collect blocks at block boundaries
                if (i + 1) % self.block_size == 0 and node.cache_blocks:
                    matched_blocks.extend(node.cache_blocks)
                    workers = workers.union(node.worker_ids)
                    node.hit_count += 1

            if matched_tokens > 0:
                node.last_access = time.time()

            return matched_tokens, matched_blocks, workers

    def get_stats(self) -> dict[str, int]:
        """Get statistics about cached prefixes."""

        def count_nodes(node):
            count = 1
            for child in node.children.values():
                count += count_nodes(child)
            return count

        def count_blocks(node):
            total = len(node.cache_blocks)
            for child in node.children.values():
                total += count_blocks(child)
            return total

        with self._lock:
            return {
                "total_nodes": count_nodes(self.root),
                "total_cached_blocks": count_blocks(self.root),
            }


@dataclass
class WorkerState:
    """State of a simulated inference worker."""

    worker_id: str
    active_requests: int = 0
    cached_blocks: set[str] = field(default_factory=set)
    total_tokens_processed: int = 0
    total_requests: int = 0


class SmartRouter:
    """
    KV-cache aware smart router (AI-Dynamo style).

    Routes requests to workers based on:
    - KV cache overlap (prefix matching)
    - Worker load
    - Configurable weights
    """

    def __init__(
        self,
        kv_overlap_weight: float = 1.0,
        load_balance_weight: float = 0.5,
        block_size: int = 16,
        num_workers: int = 4,
    ):
        self.kv_overlap_weight = kv_overlap_weight
        self.load_balance_weight = load_balance_weight
        self.block_size = block_size
        self.radix_tree = RadixTree(block_size)
        self.workers: dict[str, WorkerState] = {}
        self._lock = threading.Lock()

        # Initialize workers
        for i in range(num_workers):
            worker_id = f"worker-{i}"
            self.workers[worker_id] = WorkerState(worker_id=worker_id)

    def route_request(
        self, tokens: list[int], estimated_output_tokens: int = 100
    ) -> tuple[str, int, int]:
        """
        Route request to optimal worker based on KV cache overlap.

        Args:
            tokens: Input token IDs
            estimated_output_tokens: Expected output length

        Returns:
            (worker_id, matched_tokens, matched_blocks_count)
        """
        if not self.workers:
            raise ValueError("No workers registered")

        # Find matching prefixes
        matched_tokens, matched_blocks, candidate_workers = (
            self.radix_tree.find_longest_prefix(tokens)
        )

        best_worker_id = None
        best_cost = float("inf")

        with self._lock:
            for worker_id, worker in self.workers.items():
                # Calculate routing cost
                cache_overlap = (
                    matched_tokens if worker_id in candidate_workers else 0
                )

                cost = self._calculate_cost(
                    tokens=tokens,
                    matched_tokens=cache_overlap,
                    worker=worker,
                    estimated_output_tokens=estimated_output_tokens,
                )

                if cost < best_cost:
                    best_cost = cost
                    best_worker_id = worker_id

        return best_worker_id, matched_tokens, len(matched_blocks)

    def _calculate_cost(
        self,
        tokens: list[int],
        matched_tokens: int,
        worker: WorkerState,
        estimated_output_tokens: int,
    ) -> float:
        """Calculate routing cost for a worker."""
        # Calculate blocks needing prefill
        total_tokens = len(tokens)
        tokens_to_prefill = total_tokens - matched_tokens
        prefill_blocks = tokens_to_prefill / self.block_size

        # Estimate decode load
        decode_blocks = estimated_output_tokens / self.block_size

        # Current worker load
        load = worker.active_requests

        # Combined cost (lower is better)
        cost = (
            self.kv_overlap_weight * prefill_blocks
            + decode_blocks
            + self.load_balance_weight * load
        )

        return cost

    def start_request(self, worker_id: str):
        """Mark request as started on worker."""
        with self._lock:
            self.workers[worker_id].active_requests += 1
            self.workers[worker_id].total_requests += 1

    def complete_request(self, worker_id: str, tokens: list[int], output_tokens: int):
        """Mark request as completed and update cache."""
        with self._lock:
            self.workers[worker_id].active_requests -= 1
            self.workers[worker_id].total_tokens_processed += len(tokens) + output_tokens

        # Update radix tree with this prefix
        self.radix_tree.insert(tokens, worker_id)

        # Update worker's cached blocks
        with self._lock:
            for i in range(0, len(tokens), self.block_size):
                block_tokens = tokens[: i + self.block_size]
                block_id = f"block_{hash(tuple(block_tokens))}"
                self.workers[worker_id].cached_blocks.add(block_id)

    def get_stats(self) -> dict[str, Any]:
        """Get routing and cache statistics."""
        with self._lock:
            worker_stats = {
                worker_id: {
                    "active_requests": worker.active_requests,
                    "total_requests": worker.total_requests,
                    "cached_blocks": len(worker.cached_blocks),
                    "tokens_processed": worker.total_tokens_processed,
                }
                for worker_id, worker in self.workers.items()
            }

        tree_stats = self.radix_tree.get_stats()

        return {
            "workers": worker_stats,
            "radix_tree": tree_stats,
            "config": {
                "kv_overlap_weight": self.kv_overlap_weight,
                "load_balance_weight": self.load_balance_weight,
                "block_size": self.block_size,
                "num_workers": len(self.workers),
            },
        }


class KVCacheMetrics:
    """Track KV cache performance metrics."""

    def __init__(self):
        self.cache_hits = 0
        self.cache_misses = 0
        self.total_tokens_processed = 0
        self.cached_tokens_reused = 0
        self.prefix_lengths = []
        self.hit_rates_by_endpoint = defaultdict(lambda: {"hits": 0, "misses": 0})
        self._lock = threading.Lock()

    def record_cache_lookup(
        self, endpoint: str, total_tokens: int, matched_tokens: int
    ):
        """Record a cache lookup event."""
        with self._lock:
            if matched_tokens > 0:
                self.cache_hits += 1
                self.hit_rates_by_endpoint[endpoint]["hits"] += 1
                self.cached_tokens_reused += matched_tokens
                self.prefix_lengths.append(matched_tokens)
            else:
                self.cache_misses += 1
                self.hit_rates_by_endpoint[endpoint]["misses"] += 1

            self.total_tokens_processed += total_tokens

    def get_cache_hit_rate(self) -> float:
        """Calculate overall cache hit rate."""
        with self._lock:
            total = self.cache_hits + self.cache_misses
            return (self.cache_hits / total * 100) if total > 0 else 0.0

    def get_token_reuse_rate(self) -> float:
        """Calculate percentage of tokens reused from cache."""
        with self._lock:
            if self.total_tokens_processed == 0:
                return 0.0
            return (self.cached_tokens_reused / self.total_tokens_processed * 100)

    def get_stats(self) -> dict[str, Any]:
        """Get comprehensive cache statistics."""
        with self._lock:
            avg_prefix = (
                sum(self.prefix_lengths) / len(self.prefix_lengths)
                if self.prefix_lengths
                else 0
            )

            return {
                "cache_hit_rate": round(self.get_cache_hit_rate(), 2),
                "token_reuse_rate": round(self.get_token_reuse_rate(), 2),
                "total_cache_hits": self.cache_hits,
                "total_cache_misses": self.cache_misses,
                "total_tokens_processed": self.total_tokens_processed,
                "cached_tokens_reused": self.cached_tokens_reused,
                "avg_prefix_length": round(avg_prefix, 2),
                "by_endpoint": dict(self.hit_rates_by_endpoint),
            }


def tokenize_for_cache(text: str) -> list[int]:
    """
    Convert text to token IDs for cache key generation.

    Uses stable hashing to generate deterministic token IDs.

    Args:
        text: Text to tokenize

    Returns:
        List of simulated token IDs
    """
    from fakeai.utils import tokenize_text

    # Get text tokens
    tokens = tokenize_text(text)

    # Convert to stable integer IDs
    token_ids = []
    for token in tokens:
        # Use hash for stable ID generation
        token_hash = hashlib.md5(token.encode()).digest()
        token_id = int.from_bytes(token_hash[:4], byteorder="big") % 50000
        token_ids.append(token_id)

    return token_ids
