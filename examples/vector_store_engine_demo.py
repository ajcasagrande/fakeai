"""
Vector Store Engine Demo

Demonstrates the vector store engine capabilities:
- Document chunking with different strategies
- Embedding generation and indexing
- Similarity search with metadata filtering
- Multi-file vector stores
"""

from fakeai.vector_store_engine import VectorStoreEngine, chunk_text

# Sample documents
DOCUMENTS = {
    "python_guide": """
    Python is a high-level, interpreted programming language known for its simplicity and readability.
    It supports multiple programming paradigms including procedural, object-oriented, and functional programming.
    Python has a comprehensive standard library and a vast ecosystem of third-party packages.

    Common use cases include web development, data science, machine learning, automation, and scripting.
    Popular frameworks include Django and Flask for web development, NumPy and Pandas for data science,
    and TensorFlow and PyTorch for machine learning.
    """,
    "javascript_guide": """
    JavaScript is a versatile programming language primarily used for web development.
    It runs in the browser and enables interactive web pages through DOM manipulation.
    Modern JavaScript (ES6+) includes features like arrow functions, promises, and async/await.

    Node.js allows JavaScript to run on the server side, making it a full-stack language.
    Popular frameworks include React, Vue, and Angular for frontend development,
    and Express.js for backend development.
    """,
    "machine_learning": """
    Machine learning is a subset of artificial intelligence that enables systems to learn from data.
    Common algorithms include linear regression, decision trees, neural networks, and support vector machines.
    Deep learning uses neural networks with multiple layers to learn complex patterns.

    Applications include image recognition, natural language processing, recommendation systems, and predictive analytics.
    Key libraries include scikit-learn for traditional ML and TensorFlow/PyTorch for deep learning.
    """,
}


def demo_basic_usage():
    """Demonstrate basic vector store usage."""
    print("=" * 80)
    print("BASIC USAGE DEMO")
    print("=" * 80)

    # Create engine
    engine = VectorStoreEngine(
        embedding_dimensions=128,  # Smaller for demo
        default_metric="cosine",
    )

    # Add documents
    vs_id = "demo_store"
    for file_id, content in DOCUMENTS.items():
        result = engine.add_file(
            vector_store_id=vs_id,
            file_id=file_id,
            content=content,
            chunking_strategy={"type": "auto", "target_chunk_size": 100},
            metadata={"category": file_id.split("_")[0]},
        )
        print(f"\nAdded {file_id}:")
        print(f"  Chunks: {result['num_chunks']}")
        print(f"  Processing time: {result['processing_time']:.3f}s")

    # Get statistics
    stats = engine.get_stats(vs_id)
    print(f"\nVector Store Statistics:")
    print(f"  Files: {stats['num_files']}")
    print(f"  Chunks: {stats['num_chunks']}")
    print(f"  Vectors: {stats['num_vectors']}")
    print(f"  Total tokens: {stats['total_tokens']}")
    print(f"  Avg chunk size: {stats['avg_chunk_size']:.1f} tokens")


def demo_search():
    """Demonstrate search functionality."""
    print("\n" + "=" * 80)
    print("SEARCH DEMO")
    print("=" * 80)

    engine = VectorStoreEngine(embedding_dimensions=128)
    vs_id = "search_demo"

    # Add documents
    for file_id, content in DOCUMENTS.items():
        engine.add_file(vs_id, file_id, content)

    # Search queries
    queries = [
        "web development frameworks",
        "machine learning algorithms",
        "programming language features",
    ]

    for query in queries:
        print(f"\nQuery: '{query}'")
        results = engine.search(vs_id, query, top_k=3)

        for i, result in enumerate(results, 1):
            print(f"\n  Result {i}:")
            print(f"    Score: {result['score']:.4f}")
            print(f"    File: {result['metadata']['file_id']}")
            print(f"    Text: {result['text'][:100]}...")


def demo_metadata_filtering():
    """Demonstrate metadata filtering in search."""
    print("\n" + "=" * 80)
    print("METADATA FILTERING DEMO")
    print("=" * 80)

    engine = VectorStoreEngine(embedding_dimensions=128)
    vs_id = "filter_demo"

    # Add documents with metadata
    for file_id, content in DOCUMENTS.items():
        category = file_id.split("_")[0]
        engine.add_file(
            vs_id,
            file_id,
            content,
            metadata={"category": category, "language": "en"},
        )

    # Search with filters
    query = "programming"

    print(f"\nQuery: '{query}' (no filter)")
    results = engine.search(vs_id, query, top_k=5)
    print(f"  Found {len(results)} results")

    print(f"\nQuery: '{query}' (filter: category=python)")
    results = engine.search(vs_id, query, top_k=5, filters={"category": "python"})
    print(f"  Found {len(results)} results")
    for result in results:
        print(f"    - {result['metadata']['file_id']}")


def demo_chunking_strategies():
    """Demonstrate different chunking strategies."""
    print("\n" + "=" * 80)
    print("CHUNKING STRATEGIES DEMO")
    print("=" * 80)

    text = DOCUMENTS["python_guide"]

    # Auto chunking
    print("\nAuto Chunking:")
    auto_chunks = chunk_text(text, strategy="auto", chunk_size=100)
    print(f"  Chunks: {len(auto_chunks)}")
    for i, chunk in enumerate(auto_chunks[:2], 1):
        print(f"  Chunk {i}: {len(chunk.split())} words")

    # Static chunking
    print("\nStatic Chunking (with overlap):")
    static_chunks = chunk_text(text, strategy="static", chunk_size=50, overlap=10)
    print(f"  Chunks: {len(static_chunks)}")
    for i, chunk in enumerate(static_chunks[:2], 1):
        print(f"  Chunk {i}: {len(chunk.split())} words")


def demo_file_management():
    """Demonstrate file management operations."""
    print("\n" + "=" * 80)
    print("FILE MANAGEMENT DEMO")
    print("=" * 80)

    engine = VectorStoreEngine(embedding_dimensions=128)
    vs_id = "management_demo"

    # Add files
    for file_id, content in DOCUMENTS.items():
        engine.add_file(vs_id, file_id, content)

    print(f"\nInitial state:")
    stats = engine.get_stats(vs_id)
    print(f"  Files: {stats['num_files']}")
    print(f"  Chunks: {stats['num_chunks']}")

    # Delete a file
    engine.delete_file(vs_id, "python_guide")
    print(f"\nAfter deleting 'python_guide':")
    stats = engine.get_stats(vs_id)
    print(f"  Files: {stats['num_files']}")
    print(f"  Chunks: {stats['num_chunks']}")

    # Delete entire vector store
    engine.delete_vector_store(vs_id)
    print(f"\nVector store deleted")
    print(f"  Remaining stores: {len(engine.vector_stores)}")


def main():
    """Run all demos."""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "VECTOR STORE ENGINE DEMO" + " " * 34 + "║")
    print("╚" + "=" * 78 + "╝")

    demo_basic_usage()
    demo_search()
    demo_metadata_filtering()
    demo_chunking_strategies()
    demo_file_management()

    print("\n" + "=" * 80)
    print("DEMO COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
