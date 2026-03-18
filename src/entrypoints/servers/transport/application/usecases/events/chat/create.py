from src.application.protocols.events.chat import CreateChat
from src.entrypoints.servers.transport.infrastructure.storages.redis.repositories import presence
from src.infrastructure.storages.redis import redis
from src.infrastructure.storages.redis.collections import Gateway


class Repository:
    def __init__(self) -> None:
        self.presence = presence


class Storage:
    def __init__(self) -> None:
        self.redis = redis


class Container:
    def __init__(self, repository: Repository, storage: Storage) -> None:
        self.repository = repository
        self.storage = storage


class Usecase:
    def __init__(self) -> None:
        self.container = None

    def build(self) -> None:
        self.container = Container(repository=Repository(), storage=Storage())

    async def execute(self, payload: CreateChat) -> None:
        self.build()

        if users := payload.targets.user_ids:
            if nodes := await self.container.repository.presence.nodes(keys=users):
                message = payload.model_dump(mode="json")
                for node in nodes:
                    await self.container.storage.redis.publish(Gateway.node_events(node), message)
