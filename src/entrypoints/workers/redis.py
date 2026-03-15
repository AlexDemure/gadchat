import asyncio
import contextlib
import json

from src.entrypoints.websockets.manager import manager
from src.infrastructure.storages.redis import redis
from src.infrastructure.storages.redis.collections import Channel


async def run() -> None:
    pubsub = redis.pubsub()
    await pubsub.subscribe(Channel.events)
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
            await pubsub.unsubscribe(Channel.events)
            await pubsub.close()
