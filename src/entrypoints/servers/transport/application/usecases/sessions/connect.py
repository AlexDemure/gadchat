import contextlib
import typing

from fastapi import WebSocket
from fastapi import WebSocketDisconnect

from src.entrypoints.servers.transport.framework.websockets import manager
from src.entrypoints.servers.transport.infrastructure.storages.redis.repositories import presence
from src.infrastructure.security.jwt import jwt


class Connection:
    def __init__(self, websocket: WebSocket, user_id: str) -> None:
        self.websocket = websocket
        self.user_id = user_id


class Transport:
    def __init__(self) -> None:
        self.manager = manager


class Repository:
    def __init__(self) -> None:
        self.presence = presence


class Security:
    def __init__(self) -> None:
        self.jwt = jwt


class Container:
    def __init__(self, transport: Transport, repository: Repository, security: Security) -> None:
        self.transport = transport
        self.repository = repository
        self.security = security


class Usecase:
    def __init__(self) -> None:
        self.container: Container | None = None

    def build(self) -> None:
        self.container = Container(transport=Transport(), repository=Repository(), security=Security())

    @contextlib.asynccontextmanager
    async def execute(self, websocket: WebSocket, token: str) -> typing.AsyncIterator[Connection]:
        self.build()

        user_id = self.container.security.jwt.decode(token=token).sub

        await self.container.transport.manager.connect(key=user_id, websocket=websocket)
        await self.container.repository.presence.connect(key=user_id)

        try:
            yield Connection(websocket=websocket, user_id=user_id)
        except WebSocketDisconnect:
            ...
        finally:
            await self.container.transport.manager.disconnect(key=user_id, websocket=websocket)
            await self.container.repository.presence.disconnect(key=user_id)
