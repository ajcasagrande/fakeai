"""Event emitter mixin for handlers and services."""

from typing import Optional

from .base import BaseEvent
from .bus import AsyncEventBus


class EventEmitterMixin:
    """
    Mixin to add event emission capabilities to handlers and services.

    Usage:
        class MyHandler(EventEmitterMixin, EndpointHandler):
            def __init__(self, *args, event_bus: AsyncEventBus, **kwargs):
                super().__init__(*args, event_bus=event_bus, **kwargs)

            async def execute(self, request, context):
                await self.emit(RequestStartedEvent(...))
                # ... do work ...
                await self.emit(RequestCompletedEvent(...))
    """

    def __init__(
            self,
            *args,
            event_bus: Optional[AsyncEventBus] = None,
            **kwargs):
        """
        Initialize the mixin with an event bus.

        Args:
            event_bus: The event bus to emit events to
            *args, **kwargs: Passed to parent class
        """
        super().__init__(*args, **kwargs)
        self._event_bus = event_bus

    def set_event_bus(self, event_bus: AsyncEventBus) -> None:
        """
        Set the event bus for this emitter.

        Args:
            event_bus: The event bus to use
        """
        self._event_bus = event_bus

    async def emit(self, event: BaseEvent) -> None:
        """
        Emit an event to the event bus.

        If the event doesn't have a request_id and this emitter has a context
        with a request_id, it will be automatically filled in.

        Args:
            event: The event to emit
        """
        if self._event_bus is None:
            # No event bus configured, silently skip
            # This allows the system to work without events if needed
            return

        # Auto-fill request_id from context if available
        if not event.request_id and hasattr(self, "context"):
            event.request_id = getattr(self.context, "request_id", None)

        # Emit the event (non-blocking)
        await self._event_bus.publish(event)

    def has_event_bus(self) -> bool:
        """
        Check if this emitter has an event bus configured.

        Returns:
            True if event bus is configured, False otherwise
        """
        return self._event_bus is not None
