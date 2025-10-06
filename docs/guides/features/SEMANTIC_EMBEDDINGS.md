# Semantic Embeddings Module

## Overview

The semantic embeddings module (`fakeai/semantic_embeddings.py`) provides actual semantic embeddings using sentence transformers instead of random embeddings. This enables realistic similarity calculations for testing and development.

## Features

### Core Functionality
- **Sentence Transformers Integration**: Uses pre-trained transformer models for semantic embeddings
- **Multiple Model Support**: Supports various sentence transformer models
- **GPU Acceleration**: Automatic CUDA support with CPU fallback
- **Batch Encoding**: Efficient batch processing for multiple texts
- **LRU Caching**: 512-entry cache for identical texts
- **Dimension Adjustment**: Padding/truncation to match requested dimensions
- **L2 Normalization**: OpenAI-compatible normalized embeddings
- **Graceful Fallback**: Automatic fallback to random embeddings if unavailable

### Supported Models

| Model | Parameters | Dimensions | Max Sequence | Description |
|-------|-----------|------------|--------------|-------------|
| `all-MiniLM-L6-v2` | 22M | 384 | 256 | Fast and efficient (default) |
| `all-mpnet-base-v2` | 110M | 768 | 384 | High quality |

## Installation

### Basic Installation (Random Embeddings Only)
```bash
pip install fakeai
```

### With Semantic Embeddings
```bash
pip install fakeai sentence-transformers
```

## Configuration

### Environment Variables
```bash
# Enable semantic embeddings
export FAKEAI_USE_SEMANTIC_EMBEDDINGS=true

# Select model (default: all-MiniLM-L6-v2)
export FAKEAI_EMBEDDING_MODEL=all-MiniLM-L6-v2

# Use GPU if available (default: true)
export FAKEAI_EMBEDDING_USE_GPU=true
```

### Python Configuration
```python
from fakeai.config import AppConfig
from fakeai.fakeai_service import FakeAIService

config = AppConfig(
    use_semantic_embeddings=True,
    embedding_model="all-MiniLM-L6-v2",
    embedding_use_gpu=False,  # Force CPU
)
service = FakeAIService(config)
```

## Usage

### Basic Usage
```python
from fakeai.semantic_embeddings import SemanticEmbeddingGenerator

# Initialize generator
generator = SemanticEmbeddingGenerator(
    model_name="all-MiniLM-L6-v2",
    use_gpu=True,
)

# Check availability
if generator.is_available():
    print("Semantic embeddings ready!")

# Generate single embedding
text = "Machine learning is fascinating."
embedding = generator.encode(text)
print(f"Dimensions: {len(embedding)}")

# Generate batch embeddings
texts = ["First text", "Second text", "Third text"]
embeddings = generator.encode_batch(texts)
print(f"Generated {len(embeddings)} embeddings")
```

### Dimension Adjustment
```python
# Request specific dimensions
embedding_512 = generator.encode(text, dimensions=512)
embedding_1536 = generator.encode(text, dimensions=1536)

# Automatic padding/truncation with L2 normalization
assert len(embedding_512) == 512
assert len(embedding_1536) == 1536
```

### Similarity Calculation
```python
# Generate embeddings
emb1 = generator.encode("The cat sat on the mat.")
emb2 = generator.encode("A cat is sitting on the mat.")
emb3 = generator.encode("Quantum physics is complex.")

# Calculate cosine similarity
sim_similar = generator.get_similarity(emb1, emb2)
sim_dissimilar = generator.get_similarity(emb1, emb3)

print(f"Similar texts: {sim_similar:.4f}")      # High value (e.g., 0.85)
print(f"Dissimilar texts: {sim_dissimilar:.4f}") # Low value (e.g., 0.12)
```

### Integration with FakeAI Service
```python
from fakeai.config import AppConfig
from fakeai.fakeai_service import FakeAIService
from fakeai.models import EmbeddingRequest

# Create service with semantic embeddings
config = AppConfig(
    use_semantic_embeddings=True,
    embedding_model="all-MiniLM-L6-v2",
)
service = FakeAIService(config)

# Create embeddings via API
request = EmbeddingRequest(
    model="text-embedding-ada-002",
    input=["Text 1", "Text 2", "Text 3"],
    dimensions=1536,
)
response = await service.create_embedding(request)

# Access embeddings
for data in response.data:
    print(f"Index {data.index}: {len(data.embedding)} dimensions")
```

### Global Generator
```python
from fakeai.semantic_embeddings import get_semantic_embedding_generator

# Get or create global singleton
generator = get_semantic_embedding_generator(
    model_name="all-MiniLM-L6-v2",
    use_gpu=True,
)

# Use generator
embedding = generator.encode("Test text")
```

## API Reference

### SemanticEmbeddingGenerator

```python
class SemanticEmbeddingGenerator:
    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        use_gpu: bool = True,
        cache_size: int = 512,
    ):
        """Initialize semantic embedding generator."""

    def encode(
        self,
        texts: str | list[str],
        dimensions: int | None = None,
    ) -> list[float] | list[list[float]]:
        """Generate embeddings for text(s)."""

    def encode_batch(
        self,
        texts: list[str],
        dimensions: int | None = None,
        batch_size: int = 32,
    ) -> list[list[float]]:
        """Batch encode multiple texts for efficiency."""

    def is_available(self) -> bool:
        """Check if semantic embeddings are available."""

    def get_similarity(
        self,
        embedding1: list[float],
        embedding2: list[float]
    ) -> float:
        """Calculate cosine similarity (-1.0 to 1.0)."""

    def get_model_info(self) -> dict[str, Any]:
        """Get model information."""
```

## Fallback Behavior

The module gracefully handles cases where sentence-transformers is not installed:

1. **Import Failure**: Falls back to random embeddings
2. **Model Load Failure**: Falls back to random embeddings
3. **Runtime Errors**: Falls back to random embeddings with logging

Fallback embeddings are:
- Deterministic (same text → same embedding)
- L2 normalized
- Hash-based for consistency

## Performance

### Benchmarks (CPU)
| Operation | Texts | Time | Throughput |
|-----------|-------|------|------------|
| Single encode | 1 | ~10ms | 100 texts/sec |
| Batch encode | 32 | ~200ms | 160 texts/sec |
| Cached encode | 1 | <1ms | 10,000+ texts/sec |

### GPU Acceleration
- **NVIDIA CUDA**: Automatic detection and use
- **Speedup**: 5-10× faster than CPU for large batches
- **Memory**: ~1GB VRAM for all-MiniLM-L6-v2

## Examples

See `/home/anthony/projects/fakeai/examples/semantic_embeddings_example.py` for a complete example demonstrating:
- Single and batch embeddings
- Semantic similarity calculation
- Custom dimension adjustment
- Comparison with random embeddings

## Testing

Run comprehensive tests:
```bash
pytest tests/test_semantic_embeddings.py -v
```

Test coverage includes:
- Basic encoding (single and batch)
- Dimension adjustment (padding/truncation)
- L2 normalization
- Similarity calculation
- Caching behavior
- GPU vs CPU consistency
- Integration with FakeAI service
- Fallback behavior

## Troubleshooting

### sentence-transformers not found
```bash
pip install sentence-transformers
```

### GPU not detected
```python
# Check CUDA availability
import torch
print(torch.cuda.is_available())

# Force CPU mode
config = AppConfig(
    use_semantic_embeddings=True,
    embedding_use_gpu=False,
)
```

### Model download issues
```python
# Pre-download model
from sentence_transformers import SentenceTransformer
model = SentenceTransformer("all-MiniLM-L6-v2")
```

### Memory issues
```python
# Use smaller model
config = AppConfig(
    embedding_model="all-MiniLM-L6-v2",  # 22M params
    # Instead of "all-mpnet-base-v2"      # 110M params
)

# Reduce batch size
embeddings = generator.encode_batch(texts, batch_size=16)
```

## Architecture

### Components
- **SemanticEmbeddingGenerator**: Main class for embedding generation
- **Lazy Loading**: Models loaded on first use
- **LRU Cache**: Fast lookup for repeated texts
- **Dimension Adjustment**: Padding/truncation with normalization
- **Global Singleton**: Optional shared instance

### Integration Points
- `fakeai_service.py`: Service integration via `create_embedding()`
- `config.py`: Configuration via `AppConfig`
- `utils.py`: Fallback via `create_random_embedding()`

## Future Enhancements

- [ ] Support for additional sentence transformer models
- [ ] Multilingual model support
- [ ] Custom fine-tuned models
- [ ] Persistent embedding cache
- [ ] Asynchronous batch processing
- [ ] Quantized models for faster inference

## References

- [Sentence Transformers Documentation](https://www.sbert.net/)
- [Hugging Face Model Hub](https://huggingface.co/models?library=sentence-transformers)
- [OpenAI Embeddings API](https://platform.openai.com/docs/guides/embeddings)
