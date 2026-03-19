from src.entrypoints.servers.transport.entrypoints.workers.pubsub.application.service import delivery
from src.infrastructure.storages.redis import redis


async def run() -> None:
    async with redis.subscription(delivery.channel) as pubsub:
        async for event in pubsub.listen():
            await delivery.execute(event)
