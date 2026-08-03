from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Any


class EventBus:
    """Simple in-memory pub/sub for SSE campaign updates."""

    def __init__(self) -> None:
        self._subscribers: dict[str, list[asyncio.Queue]] = defaultdict(list)

    def subscribe(self, campaign_id: str) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue()
        self._subscribers[campaign_id].append(queue)
        return queue

    def unsubscribe(self, campaign_id: str, queue: asyncio.Queue) -> None:
        subs = self._subscribers.get(campaign_id, [])
        if queue in subs:
            subs.remove(queue)

    async def publish(self, campaign_id: str, event: dict[str, Any]) -> None:
        for queue in list(self._subscribers.get(campaign_id, [])):
            await queue.put(event)

    async def publish_all(self, event: dict[str, Any]) -> None:
        for campaign_id in list(self._subscribers.keys()):
            await self.publish(campaign_id, event)


event_bus = EventBus()
