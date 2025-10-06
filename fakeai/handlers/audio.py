"""
Audio speech handler for the /v1/audio/speech endpoint.

This handler delegates to the AudioService for text-to-speech generation.
"""
#  SPDX-License-Identifier: Apache-2.0

from fakeai.config import AppConfig
from fakeai.handlers.base import EndpointHandler, RequestContext
from fakeai.handlers.registry import register_handler
from fakeai.metrics import MetricsTracker
from fakeai.models import SpeechRequest
from fakeai.services.audio_service import AudioService


@register_handler
class AudioSpeechHandler(EndpointHandler[SpeechRequest, bytes]):
    """
    Handler for the /v1/audio/speech endpoint.

    This handler processes text-to-speech requests and returns audio files
    in the requested format.

    Features:
        - Multiple voices (alloy, echo, fable, onyx, nova, shimmer, marin, cedar)
        - Multiple formats (mp3, opus, aac, flac, wav, pcm)
        - Speed control (0.25x to 4.0x)
        - Character-based token tracking
    """

    def __init__(
        self,
        config: AppConfig,
        metrics_tracker: MetricsTracker,
    ):
        """Initialize the handler."""
        super().__init__(config, metrics_tracker)
        self.audio_service = AudioService(
            config=config,
            metrics_tracker=metrics_tracker,
        )

    def endpoint_path(self) -> str:
        """Return the endpoint path."""
        return "/v1/audio/speech"

    async def execute(
        self,
        request: SpeechRequest,
        context: RequestContext,
    ) -> bytes:
        """
        Generate text-to-speech audio.

        Args:
            request: Speech request with text, voice, and format
            context: Request context

        Returns:
            Audio file as bytes
        """
        return await self.audio_service.create_speech(request)
