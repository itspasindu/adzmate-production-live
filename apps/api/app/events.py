from __future__ import annotations

import asyncio
import json
from collections import defaultdict
from collections.abc import AsyncIterator
from typing import Any


class EventBus:
    """Campaign SSE events — Redis pub/sub when available, in-memory fallback locally."""

    def __init__(self) -> None:
        self._subscribers: dict[str, list[asyncio.Queue]] = defaultdict(list)
        self._channel_prefix = "adzmate:sse:"

    def _channel(self, campaign_id: str) -> str:
        return f"{self._channel_prefix}{campaign_id}"

    def subscribe(self, campaign_id: str) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue()
        self._subscribers[campaign_id].append(queue)
        return queue

    def unsubscribe(self, campaign_id: str, queue: asyncio.Queue) -> None:
        subs = self._subscribers.get(campaign_id, [])
        if queue in subs:
            subs.remove(queue)

    async def publish(self, campaign_id: str, event: dict[str, Any]) -> None:
        from app.redis_client import get_redis

        client = await get_redis()
        if client:
            await client.publish(self._channel(campaign_id), json.dumps(event))
            return
        for queue in list(self._subscribers.get(campaign_id, [])):
            await queue.put(event)

    async def publish_all(self, event: dict[str, Any]) -> None:
        for campaign_id in list(self._subscribers.keys()):
            await self.publish(campaign_id, event)

    async def stream(self, campaign_id: str) -> AsyncIterator[dict[str, Any]]:
        """Yield events for SSE — uses Redis when configured."""
        from app.redis_client import get_redis

        client = await get_redis()
        if client:
            pubsub = client.pubsub()
            await pubsub.subscribe(self._channel(campaign_id))
            try:
                async for message in pubsub.listen():
                    if message.get("type") != "message":
                        continue
                    data = message.get("data")
                    if isinstance(data, bytes):
                        data = data.decode("utf-8")
                    yield json.loads(data)
            finally:
                await pubsub.unsubscribe(self._channel(campaign_id))
                await pubsub.aclose()
            return

        queue = self.subscribe(campaign_id)
        try:
            while True:
                yield await queue.get()
        finally:
            self.unsubscribe(campaign_id, queue)


event_bus = EventBus()
