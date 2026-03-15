import asyncio
import contextlib
import json

from src.entrypoints.http.common.collections import REDIS_CHANNEL_EVENTS
from src.entrypoints.websockets.manager import manager
from src.infrastructure.storages.redis import redis


async def run() -> None:
    pubsub = redis.pubsub()
    await pubsub.subscribe(REDIS_CHANNEL_EVENTS)
    try:
        async for message in pubsub.listen():
            if message["type"] != "message":
                continue
            payload = json.loads(message["data"])
            await manager.send_to_users(payload.get("recipients", []), payload)
    except asyncio.CancelledError:
        raise
    finally:
        with contextlib.suppress(Exception):
            await pubsub.unsubscribe(REDIS_CHANNEL_EVENTS)
            await pubsub.close()
