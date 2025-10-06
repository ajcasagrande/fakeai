"""
Vector Store Search and Retrieval Engine

Implements actual vector similarity search for RAG workflows with:
- In-memory vector index (numpy-based with optional FAISS)
- Document chunking with multiple strategies
- Metadata storage and filtering
- Embedding generation and normalization
- Multiple similarity metrics
"""

#  SPDX-License-Identifier: Apache-2.0

import hashlib
import logging
import re
import time
from collections import defaultdict
from typing import Any, Literal

import numpy as np

from fakeai.utils import create_random_embedding, normalize_embedding

logger = logging.getLogger(__name__)

# Try to import FAISS for optimized vector search
try:
    import faiss

    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    logger.info(
        "FAISS not available, using numpy fallback for vector search. "
        "Install faiss-cpu or faiss-gpu for better performance."
    )


class ChunkingStrategy:
    """Base class for chunking strategies."""

    def chunk_text(
        self, text: str, metadata: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Chunk text into segments with metadata."""
        raise NotImplementedError


class AutoChunkingStrategy(ChunkingStrategy):
    """
    Dynamic chunking based on content.

    Attempts to preserve sentence and paragraph boundaries while
    maintaining reasonable chunk sizes.
    """

    def __init__(
        self,
        target_chunk_size: int = 512,
        min_chunk_size: int = 100,
        max_chunk_size: int = 1024,
        overlap_ratio: float = 0.15,
    ):
        """
        Initialize auto chunking strategy.

        Args:
            target_chunk_size: Target tokens per chunk
            min_chunk_size: Minimum tokens per chunk
            max_chunk_size: Maximum tokens per chunk
            overlap_ratio: Overlap ratio (0.1-0.3 recommended)
        """
        self.target_chunk_size = target_chunk_size
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
        self.overlap_ratio = overlap_ratio
        self.overlap_tokens = int(target_chunk_size * overlap_ratio)

    def chunk_text(
        self, text: str, metadata: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Chunk text with sentence boundary preservation."""
        # Handle empty text
        if not text or not text.strip():
            return []

        # Split into sentences (simple approach)
        sentences = self._split_sentences(text)

        # If no sentences found, treat entire text as one sentence
        if not sentences:
            sentences = [text.strip()]

        chunks = []
        current_chunk = []
        current_tokens = 0

        for sentence in sentences:
            sentence_tokens = self._estimate_tokens(sentence)

            # If sentence alone exceeds max, split it
            if sentence_tokens > self.max_chunk_size:
                # Flush current chunk first
                if current_chunk:
                    chunks.append(self._create_chunk(current_chunk, metadata))
                    current_chunk = []
                    current_tokens = 0

                # Split the long sentence
                sub_chunks = self._split_long_sentence(sentence)
                chunks.extend([self._create_chunk([s], metadata) for s in sub_chunks])
                continue

            # Check if adding sentence would exceed target
            if current_tokens + sentence_tokens > self.target_chunk_size:
                # If we have enough tokens, create chunk
                if current_tokens >= self.min_chunk_size:
                    chunks.append(self._create_chunk(current_chunk, metadata))

                    # Keep last few sentences for overlap
                    overlap_sentences = self._get_overlap_sentences(
                        current_chunk, self.overlap_tokens
                    )
                    current_chunk = overlap_sentences
                    current_tokens = sum(
                        self._estimate_tokens(s) for s in current_chunk
                    )
                # Otherwise, keep building
                current_chunk.append(sentence)
                current_tokens += sentence_tokens
            else:
                current_chunk.append(sentence)
                current_tokens += sentence_tokens

        # Add final chunk (allow short chunks for very short texts)
        if current_chunk:
            if current_tokens >= self.min_chunk_size or not chunks:
                # Create chunk if it meets min size, or if it's the only chunk
                chunks.append(self._create_chunk(current_chunk, metadata))

        return chunks

    def _split_sentences(self, text: str) -> list[str]:
        """Split text into sentences."""
        # Simple sentence splitter - preserves sentence boundaries
        # Also split on newlines to preserve line breaks
        sentences = re.split(r"(?<=[.!?])\s+|\n+", text)
        return [s.strip() for s in sentences if s.strip()]

    def _split_long_sentence(self, sentence: str) -> list[str]:
        """Split a very long sentence into smaller chunks."""
        words = sentence.split()
        chunks = []
        current = []
        current_tokens = 0

        for word in words:
            word_tokens = self._estimate_tokens(word)
            if current_tokens + word_tokens > self.target_chunk_size:
                if current:
                    chunks.append(" ".join(current))
                    # Keep overlap
                    overlap_size = int(len(current) * self.overlap_ratio)
                    current = current[-overlap_size:] if overlap_size > 0 else []
                    current_tokens = sum(self._estimate_tokens(w) for w in current)
            current.append(word)
            current_tokens += word_tokens

        if current:
            chunks.append(" ".join(current))

        return chunks

    def _get_overlap_sentences(
        self, sentences: list[str], target_tokens: int
    ) -> list[str]:
        """Get last few sentences to use as overlap."""
        overlap = []
        tokens = 0

        for sentence in reversed(sentences):
            sentence_tokens = self._estimate_tokens(sentence)
            if tokens + sentence_tokens > target_tokens:
                break
            overlap.insert(0, sentence)
            tokens += sentence_tokens

        return overlap

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count for text."""
        # Simple heuristic: words + punctuation
        words = len(text.split())
        punctuation = sum(1 for c in text if c in ".,;:!?()[]{}<>\"'`~@#$%^&*-+=|/\\")
        return max(1, words + punctuation)

    def _create_chunk(
        self, sentences: list[str], metadata: dict[str, Any] | None
    ) -> dict[str, Any]:
        """Create a chunk object from sentences."""
        text = " ".join(sentences)
        token_count = self._estimate_tokens(text)

        chunk = {
            "text": text,
            "token_count": token_count,
        }

        if metadata:
            chunk["metadata"] = metadata.copy()

        return chunk


class StaticChunkingStrategy(ChunkingStrategy):
    """
    Fixed-size chunking with configurable overlap.

    Simple and predictable chunking at word boundaries.
    """

    def __init__(
        self,
        chunk_size: int = 512,
        overlap: int = 50,
        preserve_sentences: bool = True,
    ):
        """
        Initialize static chunking strategy.

        Args:
            chunk_size: Fixed tokens per chunk
            overlap: Overlap in tokens between chunks
            preserve_sentences: Try to break at sentence boundaries
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.preserve_sentences = preserve_sentences

    def chunk_text(
        self, text: str, metadata: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Chunk text with fixed size and overlap."""
        # Tokenize by words
        words = text.split()

        chunks = []
        i = 0

        while i < len(words):
            # Extract chunk
            chunk_words = words[i : i + self.chunk_size]
            chunk_text = " ".join(chunk_words)

            # If preserve_sentences, try to end at sentence boundary
            if self.preserve_sentences and i + self.chunk_size < len(words):
                chunk_text = self._trim_to_sentence(chunk_text)

            token_count = len(chunk_text.split())

            chunk = {
                "text": chunk_text,
                "token_count": token_count,
                "start_index": i,
            }

            if metadata:
                chunk["metadata"] = metadata.copy()

            chunks.append(chunk)

            # Move forward with overlap
            step = max(1, self.chunk_size - self.overlap)
            i += step

        return chunks

    def _trim_to_sentence(self, text: str) -> str:
        """Trim text to last complete sentence."""
        # Find last sentence boundary
        for delimiter in [".", "!", "?"]:
            idx = text.rfind(delimiter)
            if idx > len(text) * 0.5:  # Only if we keep at least 50%
                return text[: idx + 1]
        return text


class VectorIndex:
    """
    In-memory vector index with similarity search.

    Uses FAISS if available, otherwise falls back to numpy.
    """

    def __init__(
        self,
        dimensions: int = 1536,
        metric: Literal["cosine", "euclidean", "dot"] = "cosine",
        use_faiss: bool = True,
    ):
        """
        Initialize vector index.

        Args:
            dimensions: Embedding dimensions
            metric: Similarity metric (cosine, euclidean, dot)
            use_faiss: Use FAISS if available
        """
        self.dimensions = dimensions
        self.metric = metric
        self.use_faiss = use_faiss and FAISS_AVAILABLE

        # Storage
        self.vectors: list[np.ndarray] = []
        self.chunk_ids: list[str] = []
        self.metadata: list[dict[str, Any]] = []

        # FAISS index
        self.faiss_index = None
        if self.use_faiss:
            self._init_faiss_index()

    def _init_faiss_index(self):
        """Initialize FAISS index."""
        if not FAISS_AVAILABLE:
            return

        if self.metric == "cosine":
            # For cosine, we normalize vectors and use inner product
            self.faiss_index = faiss.IndexFlatIP(self.dimensions)
        elif self.metric == "euclidean":
            self.faiss_index = faiss.IndexFlatL2(self.dimensions)
        else:  # dot product
            self.faiss_index = faiss.IndexFlatIP(self.dimensions)

        logger.info(f"Initialized FAISS index with {self.metric} metric")

    def add_vectors(
        self,
        vectors: list[list[float] | np.ndarray],
        chunk_ids: list[str],
        metadata: list[dict[str, Any]] | None = None,
    ):
        """Add vectors to the index."""
        if not vectors:
            return

        # Convert to numpy
        np_vectors = [
            np.array(v, dtype=np.float32) if not isinstance(v, np.ndarray) else v
            for v in vectors
        ]

        # Normalize for cosine similarity
        if self.metric == "cosine":
            np_vectors = [v / np.linalg.norm(v) for v in np_vectors]

        # Store
        self.vectors.extend(np_vectors)
        self.chunk_ids.extend(chunk_ids)
        self.metadata.extend(metadata or [{} for _ in range(len(vectors))])

        # Add to FAISS index
        if self.use_faiss and self.faiss_index is not None:
            vectors_array = np.vstack(np_vectors).astype(np.float32)
            self.faiss_index.add(vectors_array)

    def search(
        self,
        query_vector: list[float] | np.ndarray,
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Search for similar vectors.

        Args:
            query_vector: Query embedding
            top_k: Number of results to return
            filters: Metadata filters (AND logic)

        Returns:
            List of results with chunk_id, score, metadata
        """
        if not self.vectors:
            return []

        # Convert query to numpy
        query = (
            np.array(query_vector, dtype=np.float32)
            if not isinstance(query_vector, np.ndarray)
            else query_vector
        )

        # Normalize for cosine
        if self.metric == "cosine":
            query = query / np.linalg.norm(query)

        # Search
        if self.use_faiss and self.faiss_index is not None:
            results = self._search_faiss(query, top_k * 2, filters)
        else:
            results = self._search_numpy(query, top_k * 2, filters)

        # Apply filters and return top_k
        if filters:
            results = [
                r for r in results if self._matches_filters(r["metadata"], filters)
            ]

        return results[:top_k]

    def _search_faiss(
        self, query: np.ndarray, k: int, filters: dict[str, Any] | None
    ) -> list[dict[str, Any]]:
        """Search using FAISS index."""
        # Reshape query for FAISS
        query_array = query.reshape(1, -1)

        # Search
        k = min(k, len(self.vectors))
        distances, indices = self.faiss_index.search(query_array, k)

        # Convert to results
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx == -1:
                continue

            # Convert distance to score (0-1 range)
            if self.metric == "cosine" or self.metric == "dot":
                score = float(dist)  # Already similarity
            else:  # euclidean
                score = 1.0 / (1.0 + float(dist))

            results.append(
                {
                    "chunk_id": self.chunk_ids[idx],
                    "score": score,
                    "metadata": self.metadata[idx],
                }
            )

        return results

    def _search_numpy(
        self, query: np.ndarray, k: int, filters: dict[str, Any] | None
    ) -> list[dict[str, Any]]:
        """Search using numpy (fallback)."""
        # Stack all vectors
        vectors_array = np.vstack(self.vectors)

        # Calculate similarities
        if self.metric == "cosine" or self.metric == "dot":
            # Dot product (vectors already normalized for cosine)
            similarities = np.dot(vectors_array, query)
        else:  # euclidean
            # Euclidean distance, convert to similarity
            distances = np.linalg.norm(vectors_array - query, axis=1)
            similarities = 1.0 / (1.0 + distances)

        # Get top k indices
        top_indices = np.argsort(similarities)[::-1][:k]

        # Convert to results
        results = []
        for idx in top_indices:
            results.append(
                {
                    "chunk_id": self.chunk_ids[idx],
                    "score": float(similarities[idx]),
                    "metadata": self.metadata[idx],
                }
            )

        return results

    def _matches_filters(
        self, metadata: dict[str, Any], filters: dict[str, Any]
    ) -> bool:
        """Check if metadata matches filters (AND logic)."""
        for key, value in filters.items():
            if key not in metadata:
                return False
            if metadata[key] != value:
                return False
        return True

    def remove_vectors(self, chunk_ids: list[str]):
        """Remove vectors by chunk IDs."""
        # Find indices to remove
        indices_to_remove = [
            i for i, cid in enumerate(self.chunk_ids) if cid in chunk_ids
        ]

        # Remove in reverse order to maintain indices
        for idx in sorted(indices_to_remove, reverse=True):
            del self.vectors[idx]
            del self.chunk_ids[idx]
            del self.metadata[idx]

        # Rebuild FAISS index
        if self.use_faiss and self.faiss_index is not None:
            self._init_faiss_index()
            if self.vectors:
                vectors_array = np.vstack(self.vectors).astype(np.float32)
                self.faiss_index.add(vectors_array)

    def size(self) -> int:
        """Get number of vectors in index."""
        return len(self.vectors)


class VectorStoreEngine:
    """
    Vector store search and retrieval engine.

    Manages vector stores, chunking, embeddings, and search.
    """

    def __init__(
        self,
        embedding_dimensions: int = 1536,
        default_metric: Literal["cosine", "euclidean", "dot"] = "cosine",
        use_faiss: bool = True,
    ):
        """
        Initialize vector store engine.

        Args:
            embedding_dimensions: Dimensions for embeddings
            default_metric: Default similarity metric
            use_faiss: Use FAISS for vector search
        """
        self.embedding_dimensions = embedding_dimensions
        self.default_metric = default_metric
        self.use_faiss = use_faiss

        # Storage
        self.vector_stores: dict[str, VectorIndex] = {}
        self.store_chunks: dict[str, dict[str, dict[str, Any]]] = (
            {}
        )  # vs_id -> chunk_id -> chunk_data
        self.store_files: dict[str, dict[str, list[str]]] = (
            {}
        )  # vs_id -> file_id -> [chunk_ids]

        logger.info(
            f"Initialized VectorStoreEngine with {embedding_dimensions}D embeddings, "
            f"metric={default_metric}, use_faiss={use_faiss and FAISS_AVAILABLE}"
        )

    def add_file(
        self,
        vector_store_id: str,
        file_id: str,
        content: str,
        chunking_strategy: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Add file to vector store with chunking.

        Args:
            vector_store_id: Vector store ID
            file_id: File ID
            content: File content
            chunking_strategy: Chunking configuration
            metadata: File metadata

        Returns:
            Statistics about chunking and indexing
        """
        start_time = time.time()

        # Get or create vector store
        if vector_store_id not in self.vector_stores:
            self.vector_stores[vector_store_id] = VectorIndex(
                dimensions=self.embedding_dimensions,
                metric=self.default_metric,
                use_faiss=self.use_faiss,
            )
            self.store_chunks[vector_store_id] = {}
            self.store_files[vector_store_id] = {}

        # Initialize chunking strategy
        strategy = self._create_chunking_strategy(chunking_strategy)

        # Chunk the text
        file_metadata = metadata or {}
        file_metadata["file_id"] = file_id
        chunks = strategy.chunk_text(content, file_metadata)

        if not chunks:
            logger.warning(f"No chunks created for file {file_id}")
            return {
                "num_chunks": 0,
                "num_embeddings": 0,
                "processing_time": time.time() - start_time,
            }

        # Generate chunk IDs
        chunk_ids = [
            f"chunk_{file_id}_{hashlib.md5(chunk['text'].encode()).hexdigest()[:8]}"
            for chunk in chunks
        ]

        # Generate embeddings
        embeddings = []
        for chunk in chunks:
            embedding = create_random_embedding(
                chunk["text"], dimensions=self.embedding_dimensions
            )
            embedding = normalize_embedding(embedding)
            embeddings.append(embedding)

        # Prepare metadata for each chunk
        chunk_metadata = []
        for i, (chunk, chunk_id) in enumerate(zip(chunks, chunk_ids)):
            meta = {
                "file_id": file_id,
                "chunk_index": i,
                "token_count": chunk["token_count"],
            }
            if "metadata" in chunk:
                meta.update(chunk["metadata"])
            chunk_metadata.append(meta)

        # Add to vector index
        self.vector_stores[vector_store_id].add_vectors(
            embeddings, chunk_ids, chunk_metadata
        )

        # Store chunks
        for chunk_id, chunk, meta in zip(chunk_ids, chunks, chunk_metadata):
            self.store_chunks[vector_store_id][chunk_id] = {
                "id": chunk_id,
                "text": chunk["text"],
                "token_count": chunk["token_count"],
                "metadata": meta,
            }

        # Track file to chunks mapping
        self.store_files[vector_store_id][file_id] = chunk_ids

        processing_time = time.time() - start_time

        logger.info(
            f"Added file {file_id} to vector store {vector_store_id}: "
            f"{len(chunks)} chunks, {len(embeddings)} embeddings, "
            f"{processing_time:.3f}s"
        )

        return {
            "num_chunks": len(chunks),
            "num_embeddings": len(embeddings),
            "chunk_ids": chunk_ids,
            "processing_time": processing_time,
        }

    def search(
        self,
        vector_store_id: str,
        query: str,
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
        score_threshold: float = 0.0,
    ) -> list[dict[str, Any]]:
        """
        Search vector store.

        Args:
            vector_store_id: Vector store ID
            query: Query text
            top_k: Number of results to return
            filters: Metadata filters (AND logic)
            score_threshold: Minimum similarity score

        Returns:
            List of search results with chunk data and scores
        """
        if vector_store_id not in self.vector_stores:
            raise ValueError(f"Vector store {vector_store_id} not found")

        # Generate query embedding
        query_embedding = create_random_embedding(
            query, dimensions=self.embedding_dimensions
        )
        query_embedding = normalize_embedding(query_embedding)

        # Search
        results = self.vector_stores[vector_store_id].search(
            query_embedding, top_k=top_k * 2, filters=filters
        )

        # Filter by score threshold and add chunk data
        filtered_results = []
        for result in results:
            if result["score"] < score_threshold:
                continue

            chunk_id = result["chunk_id"]
            if chunk_id in self.store_chunks[vector_store_id]:
                chunk_data = self.store_chunks[vector_store_id][chunk_id]
                filtered_results.append(
                    {
                        "chunk_id": chunk_id,
                        "text": chunk_data["text"],
                        "score": result["score"],
                        "metadata": result["metadata"],
                        "token_count": chunk_data["token_count"],
                    }
                )

            if len(filtered_results) >= top_k:
                break

        return filtered_results

    def get_stats(self, vector_store_id: str) -> dict[str, Any]:
        """
        Get vector store statistics.

        Args:
            vector_store_id: Vector store ID

        Returns:
            Statistics about the vector store
        """
        if vector_store_id not in self.vector_stores:
            raise ValueError(f"Vector store {vector_store_id} not found")

        index = self.vector_stores[vector_store_id]
        chunks = self.store_chunks[vector_store_id]
        files = self.store_files[vector_store_id]

        total_tokens = sum(chunk["token_count"] for chunk in chunks.values())
        avg_chunk_size = total_tokens / len(chunks) if chunks else 0

        return {
            "vector_store_id": vector_store_id,
            "num_vectors": index.size(),
            "num_chunks": len(chunks),
            "num_files": len(files),
            "total_tokens": total_tokens,
            "avg_chunk_size": avg_chunk_size,
            "embedding_dimensions": self.embedding_dimensions,
            "metric": self.default_metric,
            "using_faiss": self.use_faiss and FAISS_AVAILABLE,
        }

    def delete_file(self, vector_store_id: str, file_id: str):
        """
        Remove file from vector store.

        Args:
            vector_store_id: Vector store ID
            file_id: File ID to remove
        """
        if vector_store_id not in self.vector_stores:
            raise ValueError(f"Vector store {vector_store_id} not found")

        # Get chunk IDs for file
        if file_id not in self.store_files[vector_store_id]:
            logger.warning(
                f"File {file_id} not found in vector store {vector_store_id}"
            )
            return

        chunk_ids = self.store_files[vector_store_id][file_id]

        # Remove from vector index
        self.vector_stores[vector_store_id].remove_vectors(chunk_ids)

        # Remove chunks
        for chunk_id in chunk_ids:
            if chunk_id in self.store_chunks[vector_store_id]:
                del self.store_chunks[vector_store_id][chunk_id]

        # Remove file mapping
        del self.store_files[vector_store_id][file_id]

        logger.info(
            f"Removed file {file_id} from vector store {vector_store_id}: "
            f"{len(chunk_ids)} chunks deleted"
        )

    def delete_vector_store(self, vector_store_id: str):
        """
        Delete entire vector store.

        Args:
            vector_store_id: Vector store ID
        """
        if vector_store_id not in self.vector_stores:
            raise ValueError(f"Vector store {vector_store_id} not found")

        del self.vector_stores[vector_store_id]
        del self.store_chunks[vector_store_id]
        del self.store_files[vector_store_id]

        logger.info(f"Deleted vector store {vector_store_id}")

    def _create_chunking_strategy(
        self, config: dict[str, Any] | None
    ) -> ChunkingStrategy:
        """Create chunking strategy from configuration."""
        if not config:
            return AutoChunkingStrategy()

        strategy_type = config.get("type", "auto")

        if strategy_type == "auto":
            return AutoChunkingStrategy(
                target_chunk_size=config.get("target_chunk_size", 512),
                min_chunk_size=config.get("min_chunk_size", 100),
                max_chunk_size=config.get("max_chunk_size", 1024),
                overlap_ratio=config.get("overlap_ratio", 0.15),
            )
        elif strategy_type == "static":
            return StaticChunkingStrategy(
                chunk_size=config.get("chunk_size", 512),
                overlap=config.get("overlap", 50),
                preserve_sentences=config.get("preserve_sentences", True),
            )
        else:
            logger.warning(f"Unknown chunking strategy: {strategy_type}, using auto")
            return AutoChunkingStrategy()


# Helper functions for standalone usage


def chunk_text(
    text: str,
    strategy: str = "auto",
    chunk_size: int = 512,
    overlap: int = 50,
    preserve_sentences: bool = True,
) -> list[str]:
    """
    Chunk text with specified strategy.

    Args:
        text: Text to chunk
        strategy: Chunking strategy ("auto" or "static")
        chunk_size: Target chunk size in tokens
        overlap: Overlap in tokens (for static chunking)
        preserve_sentences: Preserve sentence boundaries

    Returns:
        List of text chunks
    """
    if strategy == "auto":
        chunker = AutoChunkingStrategy(
            target_chunk_size=chunk_size,
            overlap_ratio=overlap / chunk_size if chunk_size > 0 else 0.1,
        )
    else:
        chunker = StaticChunkingStrategy(
            chunk_size=chunk_size,
            overlap=overlap,
            preserve_sentences=preserve_sentences,
        )

    chunks = chunker.chunk_text(text)
    return [chunk["text"] for chunk in chunks]
