"""
Tests for Vector Store Engine

Comprehensive tests for vector similarity search, chunking strategies,
metadata filtering, and relevance scoring.
"""

import numpy as np
import pytest

from fakeai.vector_store_engine import (
    AutoChunkingStrategy,
    StaticChunkingStrategy,
    VectorIndex,
    VectorStoreEngine,
    chunk_text,
)


@pytest.fixture
def sample_text():
    """Sample text for testing."""
    return """
    Natural language processing is a subfield of linguistics and computer science.
    It is concerned with the interactions between computers and human language.
    The goal of NLP is to enable computers to understand, interpret, and generate human language.

    Machine learning is a key technology in NLP. It allows systems to learn from data without
    being explicitly programmed. Deep learning, a subset of machine learning, has revolutionized
    NLP in recent years.

    Applications of NLP include machine translation, sentiment analysis, question answering,
    and text summarization. These applications have become increasingly sophisticated with
    advances in neural networks and transformer architectures.
    """


@pytest.fixture
def engine():
    """Create vector store engine."""
    return VectorStoreEngine(
        embedding_dimensions=128,  # Smaller for faster tests
        default_metric="cosine",
        use_faiss=False,  # Use numpy for deterministic tests
    )


class TestAutoChunkingStrategy:
    """Tests for auto chunking strategy."""

    def test_basic_chunking(self, sample_text):
        """Test basic auto chunking."""
        strategy = AutoChunkingStrategy(target_chunk_size=50, min_chunk_size=20)
        chunks = strategy.chunk_text(sample_text)

        assert len(chunks) > 0
        assert all("text" in chunk for chunk in chunks)
        assert all("token_count" in chunk for chunk in chunks)

    def test_respects_target_size(self, sample_text):
        """Test that chunks are close to target size."""
        strategy = AutoChunkingStrategy(target_chunk_size=100, min_chunk_size=50)
        chunks = strategy.chunk_text(sample_text)

        # Most chunks should be between min and target
        for chunk in chunks:
            assert chunk["token_count"] >= 10  # Allow some flexibility
            assert chunk["token_count"] <= 200  # Max should be reasonable

    def test_preserves_sentence_boundaries(self):
        """Test that sentence boundaries are preserved."""
        text = "First sentence. Second sentence. Third sentence."
        strategy = AutoChunkingStrategy(target_chunk_size=10, min_chunk_size=5)
        chunks = strategy.chunk_text(text)

        # Check that chunks end with sentence terminators
        for chunk in chunks[:-1]:  # Exclude last chunk
            text = chunk["text"]
            if len(text) > 10:  # Only for non-trivial chunks
                # Should contain complete sentences
                assert text.count(".") > 0 or text.count("!") > 0 or text.count("?") > 0

    def test_handles_long_sentences(self):
        """Test handling of very long sentences."""
        long_sentence = " ".join(["word"] * 500)
        strategy = AutoChunkingStrategy(target_chunk_size=50, max_chunk_size=100)
        chunks = strategy.chunk_text(long_sentence)

        assert len(chunks) > 1
        for chunk in chunks:
            assert chunk["token_count"] <= 120  # Allow some buffer

    def test_overlap_between_chunks(self):
        """Test that chunks have overlap."""
        # Create a long text to ensure multiple chunks
        text = ". ".join([f"This is sentence number {i}" for i in range(100)])
        strategy = AutoChunkingStrategy(
            target_chunk_size=50, min_chunk_size=20, overlap_ratio=0.2
        )
        chunks = strategy.chunk_text(text)

        # Should have multiple chunks
        assert len(chunks) > 1

        # Check for overlapping content
        found_overlap = False
        for i in range(len(chunks) - 1):
            text1 = chunks[i]["text"]
            text2 = chunks[i + 1]["text"]

            # Extract last words of first chunk and first words of second
            words1 = text1.split()[-10:]
            words2 = text2.split()[:10]

            # Check for overlap
            overlap_count = sum(1 for w in words1 if w in words2)
            if overlap_count > 0:
                found_overlap = True
                break

        # At least one chunk pair should have overlap
        assert found_overlap

    def test_metadata_propagation(self):
        """Test that metadata is propagated to chunks."""
        text = "Test sentence one. Test sentence two."
        metadata = {"source": "test", "category": "example"}
        strategy = AutoChunkingStrategy()
        chunks = strategy.chunk_text(text, metadata)

        for chunk in chunks:
            assert "metadata" in chunk
            assert chunk["metadata"]["source"] == "test"
            assert chunk["metadata"]["category"] == "example"

    def test_empty_text(self):
        """Test handling of empty text."""
        strategy = AutoChunkingStrategy()
        chunks = strategy.chunk_text("")

        assert len(chunks) == 0

    def test_short_text(self):
        """Test handling of very short text."""
        text = "Short."
        strategy = AutoChunkingStrategy(target_chunk_size=50, min_chunk_size=1)
        chunks = strategy.chunk_text(text)

        assert len(chunks) == 1
        assert chunks[0]["text"] == text


class TestStaticChunkingStrategy:
    """Tests for static chunking strategy."""

    def test_basic_static_chunking(self, sample_text):
        """Test basic static chunking."""
        strategy = StaticChunkingStrategy(chunk_size=50, overlap=10)
        chunks = strategy.chunk_text(sample_text)

        assert len(chunks) > 0
        assert all("text" in chunk for chunk in chunks)
        assert all("start_index" in chunk for chunk in chunks)

    def test_fixed_chunk_size(self):
        """Test that chunks are approximately fixed size."""
        text = " ".join(["word"] * 200)
        strategy = StaticChunkingStrategy(chunk_size=50, overlap=0)
        chunks = strategy.chunk_text(text)

        # Each chunk (except last) should have exactly chunk_size tokens
        for chunk in chunks[:-1]:
            assert 45 <= chunk["token_count"] <= 55  # Allow small variance

    def test_overlap_calculation(self):
        """Test that overlap is correctly calculated."""
        text = " ".join([f"word{i}" for i in range(200)])
        strategy = StaticChunkingStrategy(chunk_size=50, overlap=10)
        chunks = strategy.chunk_text(text)

        if len(chunks) > 1:
            # Check start indices
            for i in range(len(chunks) - 1):
                idx1 = chunks[i]["start_index"]
                idx2 = chunks[i + 1]["start_index"]
                # Step should be chunk_size - overlap = 40
                assert 35 <= (idx2 - idx1) <= 45

    def test_sentence_preservation(self):
        """Test sentence boundary preservation."""
        text = ". ".join([f"Sentence {i}" for i in range(50)])
        strategy = StaticChunkingStrategy(
            chunk_size=20, overlap=5, preserve_sentences=True
        )
        chunks = strategy.chunk_text(text)

        # Most chunks should end with periods
        ending_with_period = sum(1 for c in chunks if c["text"].rstrip().endswith("."))
        assert ending_with_period >= len(chunks) * 0.5

    def test_no_sentence_preservation(self):
        """Test chunking without sentence preservation."""
        text = ". ".join([f"Sentence {i}" for i in range(50)])
        strategy = StaticChunkingStrategy(
            chunk_size=20, overlap=5, preserve_sentences=False
        )
        chunks = strategy.chunk_text(text)

        assert len(chunks) > 0
        # Token counts should be more uniform without sentence preservation

    def test_zero_overlap(self):
        """Test chunking with zero overlap."""
        text = " ".join([f"word{i}" for i in range(100)])
        strategy = StaticChunkingStrategy(chunk_size=20, overlap=0)
        chunks = strategy.chunk_text(text)

        # Start indices should increment by exactly chunk_size
        for i in range(len(chunks) - 1):
            assert chunks[i + 1]["start_index"] - chunks[i]["start_index"] == 20


class TestVectorIndex:
    """Tests for vector index."""

    def test_add_and_search_vectors(self):
        """Test adding and searching vectors."""
        index = VectorIndex(dimensions=128, metric="cosine", use_faiss=False)

        # Create test vectors
        vectors = [np.random.rand(128).tolist() for _ in range(10)]
        chunk_ids = [f"chunk_{i}" for i in range(10)]
        metadata = [{"index": i} for i in range(10)]

        # Add vectors
        index.add_vectors(vectors, chunk_ids, metadata)

        assert index.size() == 10

        # Search
        query = np.random.rand(128)
        results = index.search(query, top_k=3)

        assert len(results) == 3
        assert all("chunk_id" in r for r in results)
        assert all("score" in r for r in results)
        assert all("metadata" in r for r in results)

    def test_cosine_similarity(self):
        """Test cosine similarity search."""
        index = VectorIndex(dimensions=4, metric="cosine", use_faiss=False)

        # Add identical vector
        vec = [1.0, 0.0, 0.0, 0.0]
        index.add_vectors([vec], ["chunk_1"], [{}])

        # Search with same vector
        results = index.search(vec, top_k=1)

        assert len(results) == 1
        # Cosine similarity should be 1.0 for identical vectors
        assert abs(results[0]["score"] - 1.0) < 0.01

    def test_euclidean_distance(self):
        """Test euclidean distance search."""
        index = VectorIndex(dimensions=4, metric="euclidean", use_faiss=False)

        # Add vectors
        vec1 = [1.0, 0.0, 0.0, 0.0]
        vec2 = [0.0, 1.0, 0.0, 0.0]
        index.add_vectors([vec1, vec2], ["chunk_1", "chunk_2"], [{}, {}])

        # Search with vec1
        results = index.search(vec1, top_k=2)

        assert len(results) == 2
        # First result should be vec1 (closest)
        assert results[0]["chunk_id"] == "chunk_1"
        assert results[0]["score"] > results[1]["score"]

    def test_metadata_filtering(self):
        """Test metadata filtering in search."""
        index = VectorIndex(dimensions=4, metric="cosine", use_faiss=False)

        # Add vectors with different metadata
        vec = [1.0, 0.0, 0.0, 0.0]
        index.add_vectors(
            [vec, vec, vec],
            ["chunk_1", "chunk_2", "chunk_3"],
            [{"category": "A"}, {"category": "B"}, {"category": "A"}],
        )

        # Search with filter
        results = index.search(vec, top_k=10, filters={"category": "A"})

        assert len(results) == 2
        assert all(r["metadata"]["category"] == "A" for r in results)

    def test_remove_vectors(self):
        """Test removing vectors from index."""
        index = VectorIndex(dimensions=4, metric="cosine", use_faiss=False)

        # Add vectors
        vectors = [[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0]]
        chunk_ids = ["chunk_1", "chunk_2", "chunk_3"]
        index.add_vectors(vectors, chunk_ids, [{}, {}, {}])

        assert index.size() == 3

        # Remove one vector
        index.remove_vectors(["chunk_2"])

        assert index.size() == 2
        assert "chunk_2" not in index.chunk_ids

    def test_empty_index_search(self):
        """Test searching empty index."""
        index = VectorIndex(dimensions=4, metric="cosine", use_faiss=False)

        results = index.search([1.0, 0.0, 0.0, 0.0], top_k=5)

        assert len(results) == 0


class TestVectorStoreEngine:
    """Tests for vector store engine."""

    def test_add_file_and_chunk(self, engine, sample_text):
        """Test adding file and automatic chunking."""
        result = engine.add_file(
            vector_store_id="vs_1",
            file_id="file_1",
            content=sample_text,
            chunking_strategy={"type": "auto", "target_chunk_size": 50},
        )

        assert result["num_chunks"] > 0
        assert result["num_embeddings"] == result["num_chunks"]
        assert len(result["chunk_ids"]) == result["num_chunks"]

    def test_search_returns_relevant(self, engine, sample_text):
        """Test that search returns relevant results."""
        # Add file
        engine.add_file(
            vector_store_id="vs_1",
            file_id="file_1",
            content=sample_text,
        )

        # Search
        results = engine.search(
            vector_store_id="vs_1", query="machine learning", top_k=3
        )

        assert len(results) > 0
        assert len(results) <= 3
        assert all("text" in r for r in results)
        assert all("score" in r for r in results)
        assert all("chunk_id" in r for r in results)

    def test_metadata_filtering(self, engine):
        """Test metadata filtering in search."""
        # Add multiple files with different metadata
        text1 = "This is about Python programming language and its syntax."
        text2 = "This is about JavaScript programming language and its syntax."

        engine.add_file(
            vector_store_id="vs_1",
            file_id="file_1",
            content=text1,
            metadata={"language": "python"},
        )
        engine.add_file(
            vector_store_id="vs_1",
            file_id="file_2",
            content=text2,
            metadata={"language": "javascript"},
        )

        # Get stats to verify files were added
        stats = engine.get_stats("vs_1")
        assert stats["num_files"] == 2

        # Search with filter - should return results from python file only
        results = engine.search(
            vector_store_id="vs_1",
            query="programming",
            top_k=10,
            filters={"language": "python"},
            score_threshold=0.0,  # Accept all scores
        )

        # At minimum, the filter should work (may return 0 results due to random embeddings)
        # Verify metadata filtering logic works
        assert all(r["metadata"]["language"] == "python" for r in results)

        # Also test that unfiltered search returns more or equal results
        results_all = engine.search(
            vector_store_id="vs_1",
            query="programming",
            top_k=10,
            score_threshold=0.0,
        )
        assert len(results_all) >= len(results)

    def test_chunking_strategies(self, engine, sample_text):
        """Test different chunking strategies."""
        # Auto chunking
        result_auto = engine.add_file(
            vector_store_id="vs_auto",
            file_id="file_1",
            content=sample_text,
            chunking_strategy={"type": "auto", "target_chunk_size": 50},
        )

        # Static chunking
        result_static = engine.add_file(
            vector_store_id="vs_static",
            file_id="file_1",
            content=sample_text,
            chunking_strategy={"type": "static", "chunk_size": 50, "overlap": 10},
        )

        assert result_auto["num_chunks"] > 0
        assert result_static["num_chunks"] > 0
        # Different strategies may produce different chunk counts

    def test_top_k_retrieval(self, engine, sample_text):
        """Test top-k retrieval."""
        engine.add_file(vector_store_id="vs_1", file_id="file_1", content=sample_text)

        # Test different k values
        for k in [1, 3, 5]:
            results = engine.search(vector_store_id="vs_1", query="test", top_k=k)
            assert len(results) <= k

    def test_score_threshold(self, engine, sample_text):
        """Test score threshold filtering."""
        engine.add_file(vector_store_id="vs_1", file_id="file_1", content=sample_text)

        # Search with high threshold
        results_high = engine.search(
            vector_store_id="vs_1", query="test", top_k=10, score_threshold=0.9
        )

        # Search with low threshold
        results_low = engine.search(
            vector_store_id="vs_1", query="test", top_k=10, score_threshold=0.0
        )

        # Low threshold should return more results
        assert len(results_low) >= len(results_high)
        # All results should be above threshold
        assert all(r["score"] >= 0.9 for r in results_high)

    def test_get_stats(self, engine, sample_text):
        """Test getting vector store statistics."""
        engine.add_file(vector_store_id="vs_1", file_id="file_1", content=sample_text)

        stats = engine.get_stats("vs_1")

        assert stats["vector_store_id"] == "vs_1"
        assert stats["num_vectors"] > 0
        assert stats["num_chunks"] > 0
        assert stats["num_files"] == 1
        assert stats["total_tokens"] > 0
        assert stats["avg_chunk_size"] > 0

    def test_delete_file(self, engine, sample_text):
        """Test deleting a file from vector store."""
        # Add file
        result = engine.add_file(
            vector_store_id="vs_1", file_id="file_1", content=sample_text
        )
        initial_count = result["num_chunks"]

        stats_before = engine.get_stats("vs_1")
        assert stats_before["num_files"] == 1

        # Delete file
        engine.delete_file("vs_1", "file_1")

        stats_after = engine.get_stats("vs_1")
        assert stats_after["num_files"] == 0
        assert stats_after["num_chunks"] == 0

    def test_delete_vector_store(self, engine, sample_text):
        """Test deleting entire vector store."""
        engine.add_file(vector_store_id="vs_1", file_id="file_1", content=sample_text)

        assert "vs_1" in engine.vector_stores

        engine.delete_vector_store("vs_1")

        assert "vs_1" not in engine.vector_stores

        # Should raise error when accessing deleted store
        with pytest.raises(ValueError, match="not found"):
            engine.get_stats("vs_1")

    def test_multiple_files_in_store(self, engine):
        """Test adding multiple files to same vector store."""
        texts = [
            "First document about Python programming.",
            "Second document about machine learning.",
            "Third document about data science.",
        ]

        for i, text in enumerate(texts):
            engine.add_file(vector_store_id="vs_1", file_id=f"file_{i}", content=text)

        stats = engine.get_stats("vs_1")
        assert stats["num_files"] == 3
        assert stats["num_chunks"] == 3
        assert stats["num_vectors"] == 3

        # Verify vector store has the data
        assert "vs_1" in engine.vector_stores
        assert engine.vector_stores["vs_1"].size() == 3

    def test_nonexistent_vector_store(self, engine):
        """Test operations on nonexistent vector store."""
        with pytest.raises(ValueError, match="not found"):
            engine.search(vector_store_id="nonexistent", query="test")

        with pytest.raises(ValueError, match="not found"):
            engine.get_stats("nonexistent")

    def test_empty_content(self, engine):
        """Test adding file with empty content."""
        result = engine.add_file(vector_store_id="vs_1", file_id="file_1", content="")

        assert result["num_chunks"] == 0
        assert result["num_embeddings"] == 0

    def test_large_document_chunking(self, engine):
        """Test chunking of large documents."""
        # Create large document
        large_text = ". ".join([f"Sentence number {i}" for i in range(500)])

        result = engine.add_file(
            vector_store_id="vs_1",
            file_id="file_1",
            content=large_text,
            chunking_strategy={"type": "static", "chunk_size": 100, "overlap": 20},
        )

        assert result["num_chunks"] > 5
        assert result["num_embeddings"] == result["num_chunks"]

    def test_search_sorting_by_score(self, engine):
        """Test that search results are sorted by score."""
        text = "Machine learning is a subset of artificial intelligence."
        engine.add_file(vector_store_id="vs_1", file_id="file_1", content=text)

        results = engine.search(
            vector_store_id="vs_1", query="machine learning", top_k=5
        )

        # Scores should be in descending order
        for i in range(len(results) - 1):
            assert results[i]["score"] >= results[i + 1]["score"]

    def test_chunk_metadata_includes_file_id(self, engine, sample_text):
        """Test that chunk metadata includes file_id."""
        engine.add_file(vector_store_id="vs_1", file_id="file_1", content=sample_text)

        results = engine.search(vector_store_id="vs_1", query="test", top_k=1)

        assert len(results) > 0
        assert results[0]["metadata"]["file_id"] == "file_1"


class TestStandaloneFunctions:
    """Tests for standalone helper functions."""

    def test_chunk_text_auto(self, sample_text):
        """Test standalone chunk_text with auto strategy."""
        chunks = chunk_text(sample_text, strategy="auto", chunk_size=50)

        assert len(chunks) > 0
        assert all(isinstance(c, str) for c in chunks)

    def test_chunk_text_static(self, sample_text):
        """Test standalone chunk_text with static strategy."""
        chunks = chunk_text(sample_text, strategy="static", chunk_size=50, overlap=10)

        assert len(chunks) > 0
        assert all(isinstance(c, str) for c in chunks)

    def test_chunk_text_empty(self):
        """Test chunk_text with empty string."""
        chunks = chunk_text("", strategy="auto")
        assert len(chunks) == 0


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_single_word_text(self, engine):
        """Test handling of single word."""
        result = engine.add_file(
            vector_store_id="vs_1", file_id="file_1", content="word"
        )

        assert result["num_chunks"] >= 1

    def test_very_long_line(self, engine):
        """Test handling of very long line without breaks."""
        text = " ".join(["word"] * 1000)
        result = engine.add_file(vector_store_id="vs_1", file_id="file_1", content=text)

        assert result["num_chunks"] > 0

    def test_special_characters(self, engine):
        """Test handling of special characters."""
        text = "Test with special chars: @#$%^&*()[]{}!?;:,.<>/"
        result = engine.add_file(vector_store_id="vs_1", file_id="file_1", content=text)

        assert result["num_chunks"] > 0

    def test_unicode_text(self, engine):
        """Test handling of unicode text."""
        text = "Unicode test: 你好世界 مرحبا العالم こんにちは世界"
        result = engine.add_file(vector_store_id="vs_1", file_id="file_1", content=text)

        assert result["num_chunks"] > 0

    def test_mixed_line_endings(self, engine):
        """Test handling of mixed line endings."""
        text = "Line 1\nLine 2\r\nLine 3\rLine 4"
        result = engine.add_file(vector_store_id="vs_1", file_id="file_1", content=text)

        assert result["num_chunks"] > 0
