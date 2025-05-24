"""
FakeAI Service Implementation

This module provides a simulated implementation of the OpenAI API services.
It simulates the behavior of the actual API by generating realistic responses
with appropriate delays to mimic real-world workloads.
"""
#  SPDX-License-Identifier: Apache-2.0

import asyncio
import base64
import logging
import random
import re
import time
import uuid
from collections.abc import AsyncGenerator
from typing import Any

from faker import Faker

from fakeai.config import AppConfig
from fakeai.models import (
    ChatCompletionChoice,
    ChatCompletionChunk,
    ChatCompletionChunkChoice,
    ChatCompletionRequest,
    ChatCompletionResponse,
    CompletionChoice,
    CompletionChunk,
    CompletionRequest,
    CompletionResponse,
    Delta,
    Embedding,
    EmbeddingRequest,
    EmbeddingResponse,
    FileListResponse,
    FileObject,
    GeneratedImage,
    ImageGenerationRequest,
    ImageGenerationResponse,
    LogProbs,
    Message,
    Model,
    ModelListResponse,
    ModelPermission,
    Role,
    TextGenerationRequest,
    TextGenerationResponse,
    Usage,
)
from fakeai.utils import (
    AsyncExecutor,
    SimulatedGenerator,
    calculate_token_count,
    create_random_embedding,
    normalize_embedding,
)

logger = logging.getLogger(__name__)
fake = Faker()


class FakeAIService:
    """Simulated implementation of OpenAI API services.

    This class provides methods that simulate the behavior of the OpenAI API,
    generating simulated responses that mimic the format and structure of the real API.
    """

    def __init__(self, config: AppConfig):
        """Initialize the simulated service with configuration."""
        self.config = config
        self.generator = SimulatedGenerator()
        self.executor = AsyncExecutor()

        # Initialize simulated data
        self._init_simulated_models()
        self._init_simulated_files()

    def _init_simulated_models(self) -> None:
        """Initialize simulated model data."""
        creation_time = int(time.time()) - 10000
        base_permission = ModelPermission(
            id=f"modelperm-{uuid.uuid4().hex}",
            created=creation_time,
            allow_create_engine=False,
            allow_sampling=True,
            allow_logprobs=True,
            allow_search_indices=False,
            allow_view=True,
            allow_fine_tuning=False,
            organization="*",
            group=None,
            is_blocking=False,
        )

        self.models = {
            "gpt-3.5-turbo": Model(
                id="gpt-3.5-turbo",
                created=creation_time,
                owned_by="openai",
                permission=[base_permission],
                root=None,
                parent=None,
            ),
            "gpt-4": Model(
                id="gpt-4",
                created=creation_time,
                owned_by="openai",
                permission=[base_permission],
                root=None,
                parent=None,
            ),
            "gpt-4-turbo": Model(
                id="gpt-4-turbo",
                created=creation_time,
                owned_by="openai",
                permission=[base_permission],
                root=None,
                parent=None,
            ),
            "text-embedding-ada-002": Model(
                id="text-embedding-ada-002",
                created=creation_time,
                owned_by="openai",
                permission=[base_permission],
                root=None,
                parent=None,
            ),
            "dall-e-2": Model(
                id="dall-e-2",
                created=creation_time,
                owned_by="openai",
                permission=[base_permission],
                root=None,
                parent=None,
            ),
            "dall-e-3": Model(
                id="dall-e-3",
                created=creation_time,
                owned_by="openai",
                permission=[base_permission],
                root=None,
                parent=None,
            ),
        }

    def _init_simulated_files(self) -> None:
        """Initialize simulated file data."""
        creation_time = int(time.time()) - 5000
        self.files = [
            FileObject(
                id=f"file-{uuid.uuid4().hex}",
                bytes=random.randint(1000, 1000000),
                created_at=creation_time,
                filename=f"training_data_{i}.jsonl",
                purpose="fine-tune",
                status="processed",
                status_details=None,
            )
            for i in range(3)
        ]

    async def list_models(self) -> ModelListResponse:
        """List available models."""
        # Simulate some processing delay
        await asyncio.sleep(random.uniform(0.05, 0.2))

        return ModelListResponse(data=list(self.models.values()))

    async def get_model(self, model_id: str) -> Model:
        """Get model details."""
        # Simulate some processing delay
        await asyncio.sleep(random.uniform(0.05, 0.2))

        if model_id not in self.models:
            raise ValueError(f"Model '{model_id}' not found")

        return self.models[model_id]

    async def create_chat_completion(
        self, request: ChatCompletionRequest
    ) -> ChatCompletionResponse:
        """Create a chat completion."""
        if request.model not in self.models:
            raise ValueError(f"Model '{request.model}' not found")

        # Calculate token counts
        prompt_tokens = calculate_token_count(
            " ".join(msg.content or "" for msg in request.messages if msg.content)
        )

        # Generate simulated response
        completion_text = await self._generate_simulated_completion(
            request.messages,
            max_tokens=request.max_tokens or 100,
            temperature=request.temperature or 1.0,
        )
        completion_tokens = calculate_token_count(completion_text)

        # Create response
        response = ChatCompletionResponse(
            id=f"chatcmpl-{uuid.uuid4().hex}",
            created=int(time.time()),
            model=request.model,
            choices=[
                ChatCompletionChoice(
                    index=i,
                    message=Message(role=Role.ASSISTANT, content=completion_text),
                    finish_reason="stop",
                )
                for i in range(request.n or 1)
            ],
            usage=Usage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
            ),
            system_fingerprint="fp_" + uuid.uuid4().hex[:16],
        )

        return response

    async def create_chat_completion_stream(
        self, request: ChatCompletionRequest
    ) -> AsyncGenerator[ChatCompletionChunk, None]:
        """Create a streaming chat completion."""
        if request.model not in self.models:
            raise ValueError(f"Model '{request.model}' not found")

        # Generate simulated response
        completion_text = await self._generate_simulated_completion(
            request.messages,
            max_tokens=request.max_tokens or 100,
            temperature=request.temperature or 1.0,
            stream=False,
        )

        # Split the completion text into chunks
        words = completion_text.split()
        stream_id = f"chatcmpl-{uuid.uuid4().hex}"
        system_fingerprint = "fp_" + uuid.uuid4().hex[:16]

        # First chunk with role
        first_chunk = ChatCompletionChunk(
            id=stream_id,
            created=int(time.time()),
            model=request.model,
            choices=[
                ChatCompletionChunkChoice(
                    index=i,
                    delta=Delta(role=Role.ASSISTANT),
                    finish_reason=None,
                )
                for i in range(request.n or 1)
            ],
            system_fingerprint=system_fingerprint,
        )
        yield first_chunk

        # Wait a bit before starting to stream
        await asyncio.sleep(random.uniform(0.1, 0.3))

        # Stream the content word by word
        for i in range(0, len(words), 1 + random.randint(0, 2)):
            chunk_words = words[i : i + 1 + random.randint(0, 2)]
            chunk_text = " ".join(chunk_words)

            if i > 0:  # Add a space before words except for the first chunk
                chunk_text = " " + chunk_text

            chunk = ChatCompletionChunk(
                id=stream_id,
                created=int(time.time()),
                model=request.model,
                choices=[
                    ChatCompletionChunkChoice(
                        index=j,
                        delta=Delta(content=chunk_text),
                        finish_reason=None,
                    )
                    for j in range(request.n or 1)
                ],
                system_fingerprint=system_fingerprint,
            )
            yield chunk

            # Simulate variable typing speed
            await asyncio.sleep(random.uniform(0.05, 0.2))

        # Final chunk with finish reason
        final_chunk = ChatCompletionChunk(
            id=stream_id,
            created=int(time.time()),
            model=request.model,
            choices=[
                ChatCompletionChunkChoice(
                    index=i,
                    delta=Delta(),
                    finish_reason="stop",
                )
                for i in range(request.n or 1)
            ],
            system_fingerprint=system_fingerprint,
        )
        yield final_chunk

    async def create_completion(self, request: CompletionRequest) -> CompletionResponse:
        """Create a text completion."""
        if request.model not in self.models:
            raise ValueError(f"Model '{request.model}' not found")

        # Handle the prompt which can be a string, list of strings, or token IDs
        prompt_text = self._process_prompt(request.prompt)
        prompt_tokens = calculate_token_count(prompt_text)

        # Generate simulated completion
        completion_text = await self._generate_simulated_completion(
            [Message(role=Role.USER, content=prompt_text)],
            max_tokens=request.max_tokens or 16,
            temperature=request.temperature or 1.0,
        )
        completion_tokens = calculate_token_count(completion_text)

        # Handle echo parameter
        if request.echo:
            completion_text = prompt_text + completion_text

        # Create response
        response = CompletionResponse(
            id=f"cmpl-{uuid.uuid4().hex}",
            created=int(time.time()),
            model=request.model,
            choices=[
                CompletionChoice(
                    text=completion_text,
                    index=i,
                    logprobs=self._generate_logprobs(completion_text, request.logprobs)
                    if request.logprobs
                    else None,
                    finish_reason="length"
                    if len(completion_text.split()) >= request.max_tokens
                    else "stop",
                )
                for i in range(request.n or 1)
            ],
            usage=Usage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
            ),
        )

        return response

    async def create_completion_stream(
        self, request: CompletionRequest
    ) -> AsyncGenerator[CompletionChunk, None]:
        """Create a streaming text completion."""
        if request.model not in self.models:
            raise ValueError(f"Model '{request.model}' not found")

        # Handle the prompt which can be a string, list of strings, or token IDs
        prompt_text = self._process_prompt(request.prompt)

        # Generate simulated completion
        completion_text = await self._generate_simulated_completion(
            [Message(role=Role.USER, content=prompt_text)],
            max_tokens=request.max_tokens or 16,
            temperature=request.temperature or 1.0,
            stream=False,
        )

        # Handle echo parameter
        if request.echo:
            text_to_stream = prompt_text + completion_text
        else:
            text_to_stream = completion_text

        # Split the completion text into chunks
        words = text_to_stream.split()
        stream_id = f"cmpl-{uuid.uuid4().hex}"

        # Stream the content word by word
        for i in range(0, len(words), 1 + random.randint(0, 2)):
            chunk_words = words[i : i + 1 + random.randint(0, 2)]
            chunk_text = " ".join(chunk_words)

            if i > 0:  # Add a space before words except for the first chunk
                chunk_text = " " + chunk_text

            chunk = CompletionChunk(
                id=stream_id,
                created=int(time.time()),
                model=request.model,
                choices=[
                    CompletionChoice(
                        text=chunk_text,
                        index=j,
                        logprobs=self._generate_logprobs(chunk_text, request.logprobs)
                        if request.logprobs
                        else None,
                        finish_reason=None,
                    )
                    for j in range(request.n or 1)
                ],
            )
            yield chunk

            # Simulate variable typing speed
            await asyncio.sleep(random.uniform(0.05, 0.2))

        # Final chunk with finish reason
        final_chunk = CompletionChunk(
            id=stream_id,
            created=int(time.time()),
            model=request.model,
            choices=[
                CompletionChoice(
                    text="",
                    index=i,
                    logprobs=None,
                    finish_reason="length"
                    if len(text_to_stream.split()) >= request.max_tokens
                    else "stop",
                )
                for i in range(request.n or 1)
            ],
        )
        yield final_chunk

    async def create_embedding(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """Create embeddings."""
        if request.model not in self.models:
            raise ValueError(f"Model '{request.model}' not found")

        # Convert input to a list of strings
        inputs = self._process_embedding_input(request.input)

        # Generate random embeddings with realistic properties
        dimensions = request.dimensions or 1536  # Default for text-embedding-ada-002

        # Calculate token count
        total_tokens = sum(calculate_token_count(text) for text in inputs)

        # Simulate computational delay based on input size and dimensions
        delay = 0.01 * (total_tokens / 100) * (dimensions / 1000)
        await asyncio.sleep(delay + random.uniform(0.05, 0.2))

        # Generate embeddings
        embeddings = []
        for i, text in enumerate(inputs):
            # Generate a random embedding vector with a stable hash based on the text
            embedding_vector = create_random_embedding(text, dimensions)

            # Normalize the embedding - OpenAI embeddings are L2 normalized
            embedding_vector = normalize_embedding(embedding_vector)

            embeddings.append(
                Embedding(
                    embedding=embedding_vector,
                    index=i,
                )
            )

        # Create response
        response = EmbeddingResponse(
            data=embeddings,
            model=request.model,
            usage=Usage(
                prompt_tokens=total_tokens,
                completion_tokens=0,
                total_tokens=total_tokens,
            ),
        )

        return response

    async def generate_images(
        self, request: ImageGenerationRequest
    ) -> ImageGenerationResponse:
        """Generate images."""
        # Validate model
        model = request.model or "dall-e-2"
        if model not in ["dall-e-2", "dall-e-3"]:
            raise ValueError(f"Invalid model for image generation: {model}")

        # Simulate processing delay based on image size, quality, and number
        size_factor = 1.0
        if request.size == "1024x1024":
            size_factor = 1.5
        elif request.size in ["1792x1024", "1024x1792"]:
            size_factor = 2.0

        quality_factor = 1.5 if request.quality == "hd" else 1.0
        delay = 1.0 * request.n * size_factor * quality_factor

        # Add some randomness to the delay
        delay = delay + random.uniform(0.5, 2.0)
        await asyncio.sleep(delay)

        # Generate simulated images
        images = []
        for _ in range(request.n):
            if request.response_format == "url":
                # Generate a fake image URL
                url = f"https://simulated-openai-images.example.com/{uuid.uuid4().hex}.png"
                images.append(GeneratedImage(url=url))
            else:
                # Generate a fake base64 image (just a placeholder)
                fake_b64 = base64.b64encode(b"simulated_image_data").decode("utf-8")
                images.append(GeneratedImage(b64_json=fake_b64))

        # Create response
        response = ImageGenerationResponse(
            created=int(time.time()),
            data=images,
        )

        return response

    async def list_files(self) -> FileListResponse:
        """List files."""
        # Simulate some processing delay
        await asyncio.sleep(random.uniform(0.05, 0.2))

        return FileListResponse(data=self.files)

    async def upload_file(self) -> FileObject:
        """Upload a file (simulated implementation)."""
        # Simulate processing delay
        await asyncio.sleep(random.uniform(0.5, 1.5))

        # Create a new simulated file
        new_file = FileObject(
            id=f"file-{uuid.uuid4().hex}",
            bytes=random.randint(1000, 1000000),
            created_at=int(time.time()),
            filename=f"uploaded_file_{len(self.files) + 1}.jsonl",
            purpose="fine-tune",
            status="uploaded",
            status_details=None,
        )

        # Add to our list
        self.files.append(new_file)

        return new_file

    async def get_file(self, file_id: str) -> FileObject:
        """Get file details."""
        # Simulate some processing delay
        await asyncio.sleep(random.uniform(0.05, 0.2))

        # Find the file
        for file in self.files:
            if file.id == file_id:
                return file

        raise ValueError(f"File with ID '{file_id}' not found")

    async def delete_file(self, file_id: str) -> dict[str, Any]:
        """Delete a file."""
        # Simulate some processing delay
        await asyncio.sleep(random.uniform(0.05, 0.2))

        # Find and remove the file
        for i, file in enumerate(self.files):
            if file.id == file_id:
                del self.files[i]
                return {"id": file_id, "object": "file", "deleted": True}

        raise ValueError(f"File with ID '{file_id}' not found")

    async def create_text_generation(
        self, request: TextGenerationRequest
    ) -> TextGenerationResponse:
        """Create a text generation (Azure API)."""
        if request.model not in self.models:
            raise ValueError(f"Model '{request.model}' not found")

        # Calculate token counts
        prompt_tokens = calculate_token_count(request.input)

        # Generate simulated response
        completion_text = await self._generate_simulated_completion(
            [Message(role=Role.USER, content=request.input)],
            max_tokens=request.max_output_tokens,
            temperature=request.temperature or 1.0,
        )
        completion_tokens = calculate_token_count(completion_text)

        # Create response
        response = TextGenerationResponse(
            id=f"txtgen-{uuid.uuid4().hex}",
            created=int(time.time()),
            output=completion_text,
            model=request.model,
            usage=Usage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
            ),
        )

        return response

    def _process_prompt(
        self, prompt: str | list[str] | list[int] | list[list[int]]
    ) -> str:
        """Process the prompt input into a string."""
        if isinstance(prompt, str):
            return prompt
        elif isinstance(prompt, list):
            if all(isinstance(item, str) for item in prompt):
                return "\n".join(prompt)
            elif all(isinstance(item, int) for item in prompt):
                # For simplicity, we'll use a placeholder for token IDs
                return f"[Token IDs input with {len(prompt)} tokens]"
            elif all(
                isinstance(item, list) and all(isinstance(i, int) for i in item)
                for item in prompt
            ):
                # For simplicity, we'll use a placeholder for batch token IDs
                return f"[Batch token IDs input with {len(prompt)} sequences]"

        raise ValueError("Unsupported prompt format")

    def _process_embedding_input(
        self, input_data: str | list[str] | list[int] | list[list[int]]
    ) -> list[str]:
        """Process the embedding input into a list of strings."""
        if isinstance(input_data, str):
            return [input_data]
        elif isinstance(input_data, list):
            if all(isinstance(item, str) for item in input_data):
                return input_data
            elif all(isinstance(item, int) for item in input_data):
                # For simplicity, we'll use a placeholder for token IDs
                return [f"[Token IDs input with {len(input_data)} tokens]"]
            elif all(
                isinstance(item, list) and all(isinstance(i, int) for i in item)
                for item in input_data
            ):
                # Convert each token ID list to a placeholder string
                return [
                    f"[Token IDs input with {len(ids)} tokens]" for ids in input_data
                ]

        raise ValueError("Unsupported input format for embeddings")

    def _generate_logprobs(self, text: str, logprob_count: int | None) -> LogProbs:
        """Generate random log probabilities."""
        if not logprob_count:
            return None

        # Simple tokenization by splitting on spaces and punctuation
        tokens = re.findall(r"\w+|[^\w\s]", text)

        # Generate random logprobs for each token
        token_logprobs = [-random.uniform(0.1, 5.0) for _ in tokens]

        # Generate top logprobs for each token
        top_logprobs = []
        for token in tokens:
            # Generate alternatives with lower probabilities
            alternatives = {}
            for _ in range(min(logprob_count, 5)):
                alt_token = fake.word()
                while alt_token == token or alt_token in alternatives:
                    alt_token = fake.word()
                alternatives[alt_token] = -random.uniform(5.0, 10.0)
            top_logprobs.append(alternatives)

        # Generate text offsets
        text_offset = [0]
        current_offset = 0
        for token in tokens[:-1]:
            current_offset += len(token) + 1  # +1 for space
            text_offset.append(current_offset)

        return LogProbs(
            tokens=tokens,
            token_logprobs=token_logprobs,
            top_logprobs=top_logprobs if logprob_count > 0 else None,
            text_offset=text_offset,
        )

    async def _generate_simulated_completion(
        self,
        messages: list[Message],
        max_tokens: int,
        temperature: float,
        stream: bool = False,
    ) -> str:
        """Generate a simulated completion based on the input messages."""
        # Extract the last user message, or use a default if none exists
        user_message = next(
            (
                msg.content
                for msg in reversed(messages)
                if msg.role == Role.USER and msg.content
            ),
            "Tell me about AI.",
        )

        # Generate a response with the executor to simulate computational work
        system_prompt = next(
            (
                msg.content
                for msg in messages
                if msg.role == Role.SYSTEM and msg.content
            ),
            None,
        )

        # Calculate a realistic delay based on the number of tokens and temperature
        token_factor = 0.01 * max_tokens
        temp_factor = 0.5 if temperature < 0.5 else 1.0 if temperature < 1.0 else 1.5
        base_delay = token_factor * temp_factor

        # Add some randomness to the delay
        delay = base_delay + random.uniform(0.2, 1.0)

        # If streaming, return quickly as we'll stream the tokens later
        if stream:
            delay = delay * 0.2

        # Generate the response with a delay
        response = await self.executor.run_with_delay(
            self.generator.generate_response,
            user_message,
            system_prompt,
            max_tokens,
            delay,
        )

        return response
