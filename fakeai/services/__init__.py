"""
Services module for FakeAI.

This module contains service classes that handle business logic.
"""

#  SPDX-License-Identifier: Apache-2.0

from fakeai.services.audio_service import AudioService
from fakeai.services.batch_service import BatchService
from fakeai.services.chat_completion_service import ChatCompletionService
from fakeai.services.embedding_service import EmbeddingService
from fakeai.services.file_service import FileService
from fakeai.services.image_generation_service import ImageGenerationService
from fakeai.services.moderation_service import ModerationService

__all__ = [
    "AudioService",
    "BatchService",
    "ChatCompletionService",
    "EmbeddingService",
    "FileService",
    "ImageGenerationService",
    "ModerationService",
]
