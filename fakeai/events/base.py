"""Base event classes and subscriber definitions."""

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Optional


@dataclass
class BaseEvent:
    """Base class for all events in the system."""

    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str = "base.event"
    timestamp: float = field(default_factory=time.time)
    request_id: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert event to dictionary representation."""
        result = {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp,
            "request_id": self.request_id,
            "metadata": self.metadata,
        }

        # Add all other fields
        for key, value in self.__dict__.items():
            if key not in result:
                result[key] = value

        return result


@dataclass
class EventSubscriber:
    """Event subscriber with metrics and circuit breaker."""

    event_type: str
    handler: Callable[[BaseEvent], Awaitable[None]]
    priority: int = 0
    success_count: int = 0
    error_count: int = 0
    timeout_count: int = 0
    total_processing_time_ms: float = 0.0
    _metrics_lock: asyncio.Lock = field(
        default_factory=asyncio.Lock, init=False, repr=False)

    @property
    def failure_rate(self) -> float:
        """Calculate failure rate of this subscriber."""
        total = self.success_count + self.error_count + self.timeout_count
        if total == 0:
            return 0.0
        return (self.error_count + self.timeout_count) / total

    @property
    def avg_processing_time_ms(self) -> float:
        """Calculate average processing time."""
        total_calls = self.success_count + self.error_count + self.timeout_count
        if total_calls == 0:
            return 0.0
        return self.total_processing_time_ms / total_calls

    def to_dict(self) -> dict[str, Any]:
        """Convert subscriber stats to dictionary."""
        return {
            "event_type": self.event_type,
            "handler_name": self.handler.__name__,
            "priority": self.priority,
            "success_count": self.success_count,
            "error_count": self.error_count,
            "timeout_count": self.timeout_count,
            "failure_rate": self.failure_rate,
            "avg_processing_time_ms": self.avg_processing_time_ms,
        }
