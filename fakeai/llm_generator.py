"""
Lightweight LLM generation module for FakeAI.

This module provides actual LLM-based text generation using lightweight models
(DistilGPT-2, GPT-2) as an alternative to template-based generation for more
realistic responses.
"""

#  SPDX-License-Identifier: Apache-2.0

import hashlib
import logging
import re
import threading
from collections import deque
from collections.abc import Generator
from typing import Any

logger = logging.getLogger(__name__)

# Pre-compiled regex pattern for streaming tokenization (used in generate_stream)
_STREAMING_TOKEN_PATTERN = re.compile(r"\b\w+\b|[^\w\s]")


class LightweightLLMGenerator:
    """
    Lightweight LLM generator using HuggingFace transformers.

    Provides actual LLM inference using small, fast models (DistilGPT-2 or GPT-2)
    with graceful fallback to template-based generation when transformers is not
    available or model loading fails.

    Features:
    - Lazy loading (models loaded on first use)
    - GPU acceleration (CUDA if available, CPU fallback)
    - Response caching for identical prompts
    - Streaming support
    - Configurable generation parameters (temperature, top_p, top_k, seed)
    - Thread-safe singleton pattern
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        """Thread-safe singleton implementation."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(
        self,
        model_name: str = "distilgpt2",
        use_gpu: bool = True,
        cache_size: int = 128,
    ):
        """
        Initialize the LLM generator.

        Args:
            model_name: Model to use (distilgpt2, gpt2, gpt2-medium, etc.)
            use_gpu: Whether to use GPU if available
            cache_size: Maximum number of cached responses
        """
        # Avoid re-initialization for singleton
        if hasattr(self, "_initialized"):
            return

        self.model_name = model_name
        self.use_gpu = use_gpu
        self.cache_size = cache_size

        # Lazy-loaded components
        self._model = None
        self._tokenizer = None
        self._device = None
        self._available = None

        # Response cache (LRU-style with dict)
        self._response_cache: dict[str, str] = {}
        self._cache_order: deque[str] = deque()  # Use deque for O(1) popleft
        self._cache_lock = threading.Lock()

        self._initialized = True

        logger.info(
            f"Initialized LightweightLLMGenerator with model={model_name}, "
            f"use_gpu={use_gpu}, cache_size={cache_size}"
        )

    def _try_import_transformers(self) -> tuple[Any | None, Any | None]:
        """
        Attempt to import transformers library.

        Returns:
            Tuple of (AutoModelForCausalLM, AutoTokenizer) or (None, None)
        """
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer

            return AutoModelForCausalLM, AutoTokenizer
        except ImportError:
            logger.warning(
                "transformers library not installed. Install with: "
                "pip install transformers torch"
            )
            return None, None

    def _try_import_torch(self) -> Any | None:
        """
        Attempt to import torch library.

        Returns:
            torch module or None
        """
        try:
            import torch

            return torch
        except ImportError:
            logger.warning(
                "torch library not installed. Install with: pip install torch"
            )
            return None

    def _load_model(self) -> bool:
        """
        Load the model and tokenizer.

        Returns:
            True if successful, False otherwise
        """
        if self._model is not None:
            return True

        # Import dependencies
        AutoModelForCausalLM, AutoTokenizer = self._try_import_transformers()
        if AutoModelForCausalLM is None:
            return False

        torch = self._try_import_torch()
        if torch is None:
            return False

        try:
            # Determine device
            if self.use_gpu and torch.cuda.is_available():
                self._device = "cuda"
                logger.info(f"Using CUDA device for LLM generation")
            else:
                self._device = "cpu"
                logger.info(f"Using CPU for LLM generation")

            # Load tokenizer
            logger.info(f"Loading tokenizer: {self.model_name}")
            self._tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                trust_remote_code=False,
            )

            # Set pad token if not set
            if self._tokenizer.pad_token is None:
                self._tokenizer.pad_token = self._tokenizer.eos_token

            # Load model
            logger.info(f"Loading model: {self.model_name}")
            self._model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                trust_remote_code=False,
                low_cpu_mem_usage=True,
            )

            # Move to device
            self._model = self._model.to(self._device)
            self._model.eval()  # Set to evaluation mode

            logger.info(
                f"Successfully loaded model {
                    self.model_name} on {
                    self._device}")
            return True

        except Exception as e:
            logger.error(f"Failed to load model {self.model_name}: {e}")
            self._model = None
            self._tokenizer = None
            self._device = None
            return False

    def is_available(self) -> bool:
        """
        Check if LLM backend is available.

        Returns:
            True if model is loaded and ready, False otherwise
        """
        if self._available is not None:
            return self._available

        # Try to load model on first check
        self._available = self._load_model()
        return self._available

    def _get_cache_key(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
        top_p: float,
        seed: int | None,
    ) -> str:
        """
        Generate cache key for a generation request.

        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Nucleus sampling threshold
            seed: Random seed (if any)

        Returns:
            Cache key string
        """
        cache_str = f"{prompt}|{max_tokens}|{temperature}|{top_p}|{seed}"
        return hashlib.sha256(cache_str.encode()).hexdigest()

    def _get_from_cache(self, cache_key: str) -> str | None:
        """
        Get response from cache.

        Args:
            cache_key: Cache key

        Returns:
            Cached response or None
        """
        with self._cache_lock:
            if cache_key in self._response_cache:
                # Move to end (most recently used)
                self._cache_order.remove(cache_key)
                self._cache_order.append(cache_key)
                return self._response_cache[cache_key]
        return None

    def _add_to_cache(self, cache_key: str, response: str) -> None:
        """
        Add response to cache.

        Args:
            cache_key: Cache key
            response: Generated response
        """
        with self._cache_lock:
            # Remove oldest if cache is full
            if len(self._response_cache) >= self.cache_size:
                oldest_key = self._cache_order.popleft()  # O(1) instead of O(n)
                del self._response_cache[oldest_key]

            # Add new entry
            self._response_cache[cache_key] = response
            self._cache_order.append(cache_key)

    def generate(
        self,
        prompt: str,
        max_tokens: int = 100,
        temperature: float = 1.0,
        top_p: float = 1.0,
        top_k: int = 50,
        seed: int | None = None,
        stop: list[str] | None = None,
    ) -> str:
        """
        Generate text using the LLM.

        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0 = deterministic, higher = more random)
            top_p: Nucleus sampling threshold (0.0-1.0)
            top_k: Top-k sampling (number of top tokens to consider)
            seed: Random seed for reproducibility
            stop: Stop sequences (generation stops when any is encountered)

        Returns:
            Generated text (prompt not included)
        """
        # Check if LLM is available
        if not self.is_available():
            logger.warning("LLM not available, returning empty string")
            return ""

        # Check cache
        cache_key = self._get_cache_key(
            prompt, max_tokens, temperature, top_p, seed)
        cached_response = self._get_from_cache(cache_key)
        if cached_response is not None:
            logger.debug(f"Cache hit for prompt: {prompt[:50]}...")
            return cached_response

        try:
            import torch

            # Set seed if provided
            if seed is not None:
                torch.manual_seed(seed)
                if torch.cuda.is_available():
                    torch.cuda.manual_seed(seed)

            # Tokenize input
            inputs = self._tokenizer(
                prompt,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=512,  # Prevent excessively long inputs
            )
            inputs = {k: v.to(self._device) for k, v in inputs.items()}

            # Generate
            with torch.no_grad():
                outputs = self._model.generate(
                    **inputs,
                    max_new_tokens=max_tokens,
                    temperature=max(0.01, temperature),  # Avoid zero
                    top_p=top_p,
                    top_k=top_k,
                    do_sample=temperature > 0.0,
                    pad_token_id=self._tokenizer.pad_token_id,
                    eos_token_id=self._tokenizer.eos_token_id,
                    num_return_sequences=1,
                )

            # Decode output
            generated_text = self._tokenizer.decode(
                outputs[0],
                skip_special_tokens=True,
            )

            # Remove prompt from output
            if generated_text.startswith(prompt):
                response = generated_text[len(prompt):].strip()
            else:
                response = generated_text.strip()

            # Apply stop sequences
            if stop:
                for stop_seq in stop:
                    if stop_seq in response:
                        response = response.split(stop_seq)[0]

            # Add to cache
            self._add_to_cache(cache_key, response)

            logger.debug(
                f"Generated {len(response)} chars for prompt: {prompt[:50]}..."
            )
            return response

        except Exception as e:
            logger.error(f"Error during generation: {e}")
            return ""

    def generate_stream(
        self,
        prompt: str,
        max_tokens: int = 100,
        temperature: float = 1.0,
        top_p: float = 1.0,
        top_k: int = 50,
        seed: int | None = None,
        stop: list[str] | None = None,
    ) -> Generator[str, None, None]:
        """
        Generate text token-by-token (streaming).

        Note: This is simulated streaming - we generate the full response first,
        then yield it token-by-token. True token-by-token generation would require
        more complex implementation with TextStreamer or custom generation loops.

        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Nucleus sampling threshold
            top_k: Top-k sampling
            seed: Random seed
            stop: Stop sequences

        Yields:
            Generated tokens one at a time
        """
        # Generate full response
        response = self.generate(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            seed=seed,
            stop=stop,
        )

        # If generation failed, return
        if not response:
            return

        # Tokenize response for streaming
        try:
            # Use tokenizer if available
            if self._tokenizer is not None:
                tokens = self._tokenizer.encode(response)
                for token_id in tokens:
                    token_text = self._tokenizer.decode([token_id])
                    if token_text:
                        yield token_text
            else:
                # Fallback: split by words and punctuation using pre-compiled pattern
                tokens = _STREAMING_TOKEN_PATTERN.findall(response)
                for token in tokens:
                    yield token
        except Exception as e:
            logger.error(f"Error during streaming: {e}")
            # Fallback: yield entire response
            yield response

    def clear_cache(self) -> None:
        """Clear the response cache."""
        with self._cache_lock:
            self._response_cache.clear()
            self._cache_order.clear()
        logger.info("Cleared LLM response cache")

    def get_cache_stats(self) -> dict[str, int]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache size and capacity
        """
        with self._cache_lock:
            return {
                "size": len(self._response_cache),
                "capacity": self.cache_size,
            }

    def unload_model(self) -> None:
        """
        Unload the model from memory.

        Useful for freeing GPU/CPU memory when the generator is no longer needed.
        """
        if self._model is not None:
            del self._model
            self._model = None
            logger.info("Unloaded LLM model from memory")

        if self._tokenizer is not None:
            del self._tokenizer
            self._tokenizer = None

        self._device = None
        self._available = None

        # Clear CUDA cache if available
        try:
            import torch

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                logger.info("Cleared CUDA cache")
        except Exception:
            pass


# Convenience functions for backward compatibility

_default_generator: LightweightLLMGenerator | None = None
_generator_lock = threading.Lock()


def get_generator(
    model_name: str = "distilgpt2",
    use_gpu: bool = True,
) -> LightweightLLMGenerator:
    """
    Get or create the default LLM generator instance.

    Args:
        model_name: Model to use
        use_gpu: Whether to use GPU

    Returns:
        LightweightLLMGenerator instance
    """
    global _default_generator

    with _generator_lock:
        if _default_generator is None:
            _default_generator = LightweightLLMGenerator(
                model_name=model_name,
                use_gpu=use_gpu,
            )
        return _default_generator


def generate_with_llm(
    prompt: str,
    max_tokens: int = 100,
    temperature: float = 1.0,
    **kwargs,
) -> str:
    """
    Convenience function for generating text with the default LLM.

    Args:
        prompt: Input prompt
        max_tokens: Maximum tokens to generate
        temperature: Sampling temperature
        **kwargs: Additional generation parameters

    Returns:
        Generated text
    """
    generator = get_generator()
    return generator.generate(
        prompt=prompt,
        max_tokens=max_tokens,
        temperature=temperature,
        **kwargs,
    )


def is_llm_available() -> bool:
    """
    Check if LLM generation is available.

    Returns:
        True if transformers/torch are installed and model can load
    """
    generator = get_generator()
    return generator.is_available()
