from src.configuration import settings
from src.infrastructure.storages.redis import redis
from src.infrastructure.storages.redis.collections import Gateway


class Presence:
    def __init__(self) -> None:
        self.node_id = settings.hostname

    async def connect(self, key: str) -> None:
        await redis.sadd(Gateway.presence_user_nodes(key), self.node_id)
        await redis.sadd(Gateway.presence_node_users(self.node_id), key)

    async def disconnect(self, key: str) -> None:
        await redis.srem(Gateway.presence_user_nodes(key), self.node_id)
        await redis.srem(Gateway.presence_node_users(self.node_id), key)

    async def connected(self, key: str) -> bool:
        return await redis.sismember(Gateway.presence_node_users(self.node_id), key)

    async def users(self) -> set[str]:
        return await redis.smembers(Gateway.presence_node_users(self.node_id))

    async def nodes(self, keys: list[str]) -> set[str]:
        members: set[str] = set()
        for key in keys:
            members.update(await redis.smembers(Gateway.presence_user_nodes(key)))
        return members


presence = Presence()
