"""
Event system for decoupled metrics tracking.

This module provides a pub-sub event system that decouples metrics tracking
from the core request handling logic. Services emit events and metrics
collectors subscribe to them.
"""

from .base import BaseEvent, EventSubscriber
from .bus import AsyncEventBus, EventBusFactory
from .emitter import EventEmitterMixin
from .event_types import (  # Request lifecycle events; Token events; Stream lifecycle events; Latency & performance events; Cache events; Model & resource events; Error & recovery events; Network & client events; Usage & billing events
    BackpressureDetectedEvent,
    BatchSizeChangedEvent,
    CacheEvictionEvent,
    CacheHitEvent,
    CacheLookupEvent,
    CacheMissEvent,
    CacheSpeedupMeasuredEvent,
    ChunkSentEvent,
    ClientDisconnectedEvent,
    CostCalculatedEvent,
    DecodeCompletedEvent,
    DecodeStartedEvent,
    ErrorOccurredEvent,
    ErrorPatternDetectedEvent,
    FirstTokenGeneratedEvent,
    GPUMetricsEvent,
    LatencyMeasuredEvent,
    ModelSelectedEvent,
    NetworkLatencyMeasuredEvent,
    PrefillCompletedEvent,
    PrefillStartedEvent,
    QueueDepthChangedEvent,
    QuotaUpdatedEvent,
    RateLimitHitEvent,
    RecoveryAttemptedEvent,
    RecoverySucceededEvent,
    RequestCompletedEvent,
    RequestDequeuedEvent,
    RequestFailedEvent,
    RequestQueuedEvent,
    RequestRoutedEvent,
    RequestStartedEvent,
    ResourceUtilizationEvent,
    SLOViolationEvent,
    StreamCancelledEvent,
    StreamCompletedEvent,
    StreamFailedEvent,
    StreamingTokenGeneratedEvent,
    StreamProgressEvent,
    StreamStartedEvent,
    ThroughputMeasuredEvent,
    TokenBatchGeneratedEvent,
    TokensGeneratedEvent,
    UsageRecordedEvent,
    WorkerAssignedEvent,
    WorkerCompletedEvent,
)

__all__ = [
    # Core classes
    "BaseEvent",
    "EventSubscriber",
    "AsyncEventBus",
    "EventBusFactory",
    "EventEmitterMixin",

    # Request lifecycle events
    "RequestStartedEvent",
    "RequestCompletedEvent",
    "RequestFailedEvent",
    "RequestQueuedEvent",
    "RequestDequeuedEvent",
    "RequestRoutedEvent",

    # Token events
    "TokensGeneratedEvent",
    "TokenBatchGeneratedEvent",
    "StreamingTokenGeneratedEvent",
    "FirstTokenGeneratedEvent",

    # Stream lifecycle events
    "StreamStartedEvent",
    "StreamProgressEvent",
    "StreamCompletedEvent",
    "StreamFailedEvent",
    "StreamCancelledEvent",

    # Latency & performance events
    "PrefillStartedEvent",
    "PrefillCompletedEvent",
    "DecodeStartedEvent",
    "DecodeCompletedEvent",
    "LatencyMeasuredEvent",
    "ThroughputMeasuredEvent",
    "QueueDepthChangedEvent",
    "BatchSizeChangedEvent",

    # Cache events
    "CacheLookupEvent",
    "CacheHitEvent",
    "CacheMissEvent",
    "CacheSpeedupMeasuredEvent",
    "CacheEvictionEvent",

    # Model & resource events
    "ModelSelectedEvent",
    "WorkerAssignedEvent",
    "WorkerCompletedEvent",
    "ResourceUtilizationEvent",
    "GPUMetricsEvent",

    # Error & recovery events
    "ErrorOccurredEvent",
    "ErrorPatternDetectedEvent",
    "RecoveryAttemptedEvent",
    "RecoverySucceededEvent",
    "SLOViolationEvent",

    # Network & client events
    "ChunkSentEvent",
    "BackpressureDetectedEvent",
    "ClientDisconnectedEvent",
    "NetworkLatencyMeasuredEvent",

    # Usage & billing events
    "UsageRecordedEvent",
    "QuotaUpdatedEvent",
    "RateLimitHitEvent",
    "CostCalculatedEvent",
]
