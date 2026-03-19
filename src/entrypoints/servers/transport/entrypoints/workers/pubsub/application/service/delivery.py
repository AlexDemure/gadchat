import typing

from fastapi import WebSocket

from src.application.protocols.transport import Event
from src.common.formats.utils import json
from src.entrypoints.servers.transport.framework.websockets import manager
from src.entrypoints.servers.transport.infrastructure.storages.redis.repositories import presence
from src.infrastructure.storages.redis.collections import Gateway


class Transport:
    def __init__(self) -> None:
        self.manager = manager


class Repository:
    def __init__(self) -> None:
        self.presence = presence


class Container:
    def __init__(self, transport: Transport, repository: Repository) -> None:
        self.transport = transport
        self.repository = repository


class Usecase:
    def __init__(self) -> None:
        self.container = Container(transport=Transport(), repository=Repository())

    @property
    def channel(self) -> str:
        return Gateway.node_events(self.container.repository.presence.node_id)

    async def execute(self, event: dict[str, typing.Any]) -> None:
        if event.get("type") != "message":
            return None

        data = event["data"]

        event = Event.model_validate(json.fromstring(data))

        connected = await self.container.repository.presence.users()

        users = [user_id for user_id in event.targets.user_ids if user_id in connected]

        connections = await self.container.transport.manager.sockets(keys=users)

        targets: dict[WebSocket, set[str]] = {}

        for user_id, sockets in connections.items():
            for socket in sockets:
                targets.setdefault(socket, set()).add(user_id)

        stale: list[tuple[str, WebSocket]] = []

        for socket, user_ids in targets.items():
            try:
                await socket.send_text(data)
            except Exception:
                for user_id in user_ids:
                    stale.append((user_id, socket))

        for user_id, socket in stale:
            await self.container.transport.manager.disconnect(key=user_id, websocket=socket)

        return None


delivery = Usecase()
