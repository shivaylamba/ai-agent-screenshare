"""Event bus for component communication."""
import asyncio
from typing import Any, Dict, List, Callable
from dataclasses import dataclass
from datetime import datetime
from simple_logger import logger


@dataclass
class Event:
    """Represents an event."""
    type: str
    data: Any
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class EventBus:
    """Pub/sub event bus for async component communication."""

    def __init__(self):
        """Initialize event bus."""
        self._subscribers: Dict[str, List[asyncio.Queue]] = {}
        self._event_count = 0

        logger.info("Event bus initialized")

    async def publish(self, event_type: str, data: Any = None):
        """
        Publish an event.

        Args:
            event_type: Type of event
            data: Event data
        """
        event = Event(type=event_type, data=data)

        if event_type in self._subscribers:
            for queue in self._subscribers[event_type]:
                await queue.put(event)

            self._event_count += 1
            logger.debug(f"Published event: {event_type} (subscribers: {len(self._subscribers[event_type])})")

    def subscribe(self, event_types: List[str]) -> asyncio.Queue:
        """
        Subscribe to event types.

        Args:
            event_types: List of event types to subscribe to

        Returns:
            Queue that will receive events
        """
        queue = asyncio.Queue()

        for event_type in event_types:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []

            self._subscribers[event_type].append(queue)

        logger.info(f"Subscribed to events: {event_types}")
        return queue

    def unsubscribe(self, event_types: List[str], queue: asyncio.Queue):
        """
        Unsubscribe from event types.

        Args:
            event_types: Event types to unsubscribe from
            queue: Queue to remove
        """
        for event_type in event_types:
            if event_type in self._subscribers:
                if queue in self._subscribers[event_type]:
                    self._subscribers[event_type].remove(queue)

        logger.info(f"Unsubscribed from events: {event_types}")

    async def subscribe_async(self, event_types: List[str], callback: Callable):
        """
        Subscribe with a callback function.

        Args:
            event_types: Event types to subscribe to
            callback: Async function to call on events
        """
        queue = self.subscribe(event_types)

        async def listener():
            while True:
                event = await queue.get()
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(event)
                    else:
                        callback(event)
                except Exception as e:
                    logger.error(f"Error in event callback: {e}")

        asyncio.create_task(listener())

    def get_subscriber_count(self, event_type: str) -> int:
        """
        Get number of subscribers for an event type.

        Args:
            event_type: Event type to check

        Returns:
            Number of subscribers
        """
        return len(self._subscribers.get(event_type, []))

    def get_event_count(self) -> int:
        """
        Get total number of events published.

        Returns:
            Event count
        """
        return self._event_count

    def get_stats(self) -> Dict:
        """
        Get event bus statistics.

        Returns:
            Dictionary with statistics
        """
        return {
            'total_events': self._event_count,
            'event_types': list(self._subscribers.keys()),
            'subscribers_per_type': {
                et: len(subs) for et, subs in self._subscribers.items()
            }
        }
