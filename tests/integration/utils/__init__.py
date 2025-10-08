"""Test utilities for integration tests."""

import httpx
from fastapi.testclient import TestClient
from httpx import ASGITransport

from fakeai.app import app


class FakeAIClient:
    """Simple wrapper around TestClient for integration tests."""

    def __init__(self, base_url: str = "http://testserver", api_key: str = "test-api-key"):
        """Initialize the client."""
        self.client = TestClient(app)
        self.base_url = base_url
        self.api_key = api_key
        self.default_headers = {"Authorization": f"Bearer {api_key}"}

    def close(self):
        """Close the client."""
        # TestClient doesn't need explicit closing, but we provide this for compatibility

    def get(self, url: str, **kwargs):
        """Make a GET request."""
        kwargs.setdefault("headers", {}).update(self.default_headers)
        return self.client.get(url, **kwargs)

    def post(self, url: str, **kwargs):
        """Make a POST request."""
        kwargs.setdefault("headers", {}).update(self.default_headers)
        return self.client.post(url, **kwargs)

    def put(self, url: str, **kwargs):
        """Make a PUT request."""
        kwargs.setdefault("headers", {}).update(self.default_headers)
        return self.client.put(url, **kwargs)

    def delete(self, url: str, **kwargs):
        """Make a DELETE request."""
        kwargs.setdefault("headers", {}).update(self.default_headers)
        return self.client.delete(url, **kwargs)

    def create_speech(
        self,
        input: str,
        voice: str,
        model: str = "tts-1",
        response_format: str = "mp3",
        speed: float = 1.0,
    ) -> bytes:
        """Create speech audio from text.

        Args:
            input: The text to convert to speech
            voice: Voice to use (alloy, echo, fable, onyx, nova, shimmer)
            model: TTS model to use (tts-1, tts-1-hd)
            response_format: Audio format (mp3, opus, aac, flac, wav, pcm)
            speed: Playback speed (0.25 to 4.0)

        Returns:
            bytes: The audio file content
        """
        response = self.post(
            "/v1/audio/speech",
            json={
                "model": model,
                "input": input,
                "voice": voice,
                "response_format": response_format,
                "speed": speed,
            },
        )
        response.raise_for_status()
        return response.content

    def create_moderation(
        self,
        input: str | list[str] | list[dict],
        model: str = "omni-moderation-latest",
    ) -> dict:
        """Create moderation for text or multi-modal content.

        Args:
            input: Text string, list of strings, or multi-modal content
            model: Moderation model to use

        Returns:
            dict: Moderation response
        """
        response = self.post(
            "/v1/moderations",
            json={
                "model": model,
                "input": input,
            },
        )
        response.raise_for_status()
        return response.json()

    def create_image(
        self,
        prompt: str,
        model: str = "dall-e-3",
        n: int = 1,
        size: str = "1024x1024",
        quality: str = "standard",
        response_format: str = "url",
        style: str = "vivid",
        user: str | None = None,
    ) -> dict:
        """Create an image from a text prompt.

        Args:
            prompt: Text description of the image
            model: Image generation model (dall-e-2, dall-e-3)
            n: Number of images to generate
            size: Image size
            quality: Image quality (standard, hd)
            response_format: Response format (url, b64_json)
            style: Image style (vivid, natural)
            user: Unique user identifier

        Returns:
            dict: Image generation response
        """
        request_data = {
            "model": model,
            "prompt": prompt,
            "n": n,
            "size": size,
            "quality": quality,
            "response_format": response_format,
            "style": style,
        }
        if user is not None:
            request_data["user"] = user

        response = self.post("/v1/images/generations", json=request_data)
        response.raise_for_status()
        return response.json()

    def create_embedding(
        self,
        input: str | list[str],
        model: str = "text-embedding-3-small",
        encoding_format: str = "float",
        dimensions: int | None = None,
        user: str | None = None,
    ) -> dict:
        """Create embeddings for text input.

        Args:
            input: Text string or list of strings to embed
            model: Embedding model to use
            encoding_format: Format for embeddings (float, base64)
            dimensions: Number of dimensions (for compatible models)
            user: Unique user identifier

        Returns:
            dict: Embedding response
        """
        request_data = {
            "model": model,
            "input": input,
            "encoding_format": encoding_format,
        }
        if dimensions is not None:
            request_data["dimensions"] = dimensions
        if user is not None:
            request_data["user"] = user

        response = self.post("/v1/embeddings", json=request_data)
        response.raise_for_status()
        return response.json()

    async def apost(self, url: str, **kwargs):
        """Make an async POST request.

        Args:
            url: URL path to POST to
            **kwargs: Additional request arguments

        Returns:
            httpx.Response: Response object
        """
        kwargs.setdefault("headers", {}).update(self.default_headers)
        transport = ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            return await client.post(url, **kwargs)

    async def aget(self, url: str, **kwargs):
        """Make an async GET request.

        Args:
            url: URL path to GET
            **kwargs: Additional request arguments

        Returns:
            httpx.Response: Response object
        """
        kwargs.setdefault("headers", {}).update(self.default_headers)
        transport = ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            return await client.get(url, **kwargs)

    def chat_completion(
        self,
        model: str,
        messages: list[dict],
        **kwargs,
    ) -> dict:
        """Create a chat completion.

        Args:
            model: Model to use
            messages: List of message dicts
            **kwargs: Additional chat completion parameters

        Returns:
            dict: Chat completion response
        """
        request_data = {
            "model": model,
            "messages": messages,
            **kwargs,
        }
        response = self.post("/v1/chat/completions", json=request_data)
        response.raise_for_status()
        return response.json()

    def chat_completion_stream(
        self,
        model: str,
        messages: list[dict],
        **kwargs,
    ):
        """Create a streaming chat completion.

        Args:
            model: Model to use
            messages: List of message dicts
            **kwargs: Additional chat completion parameters

        Yields:
            dict: Chat completion chunks
        """
        request_data = {
            "model": model,
            "messages": messages,
            "stream": True,
            **kwargs,
        }
        with self.client.stream("POST", "/v1/chat/completions", json=request_data, headers=self.default_headers) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if line.strip() and line.startswith("data: "):
                    data = line[6:]  # Remove "data: " prefix
                    if data.strip() == "[DONE]":
                        break
                    import json
                    yield json.loads(data)

    async def achat_completion(
        self,
        model: str,
        messages: list[dict],
        **kwargs,
    ) -> dict:
        """Create a chat completion asynchronously.

        Args:
            model: Model to use
            messages: List of message dicts
            **kwargs: Additional chat completion parameters

        Returns:
            dict: Chat completion response
        """
        request_data = {
            "model": model,
            "messages": messages,
            **kwargs,
        }
        response = await self.apost("/v1/chat/completions", json=request_data)
        response.raise_for_status()
        return response.json()

    async def achat_completion_stream(
        self,
        model: str,
        messages: list[dict],
        **kwargs,
    ):
        """Create a streaming chat completion asynchronously.

        Args:
            model: Model to use
            messages: List of message dicts
            **kwargs: Additional chat completion parameters

        Yields:
            dict: Chat completion chunks
        """
        request_data = {
            "model": model,
            "messages": messages,
            "stream": True,
            **kwargs,
        }
        kwargs_copy = kwargs.copy()
        kwargs_copy.setdefault("headers", {}).update(self.default_headers)
        transport = ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            async with client.stream("POST", "/v1/chat/completions", json=request_data, headers=self.default_headers) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.strip() and line.startswith("data: "):
                        data = line[6:]  # Remove "data: " prefix
                        if data.strip() == "[DONE]":
                            break
                        import json
                        yield json.loads(data)

    def get_metrics(self):
        """Get server metrics.

        Returns:
            dict: Server metrics
        """
        response = self.get("/metrics")
        if response.status_code == 200:
            return response.json()
        return None

    def get_prometheus_metrics(self):
        """Get Prometheus metrics.

        Returns:
            str: Prometheus metrics in text format
        """
        response = self.get("/metrics/prometheus")
        response.raise_for_status()
        return response.text


class ServerManager:
    """Simple server manager for integration tests requiring WebSocket connections."""

    def __init__(self, base_url: str = "http://testserver"):
        """Initialize the server manager.

        Args:
            base_url: Base URL for the test server
        """
        self.base_url = base_url
        self.client = TestClient(app)

    def get(self, url: str, **kwargs):
        """Make a GET request."""
        return self.client.get(url, **kwargs)

    def post(self, url: str, **kwargs):
        """Make a POST request."""
        return self.client.post(url, **kwargs)


__all__ = ["FakeAIClient", "ServerManager"]
