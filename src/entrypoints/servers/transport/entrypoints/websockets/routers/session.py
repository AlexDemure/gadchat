import contextlib
import json

from fastapi import Query
from fastapi import WebSocket
from fastapi import WebSocketDisconnect
from pydantic import ValidationError

from src.application.protocols.commands.chat import CreateChat
from src.application.protocols.transport import Event
from src.entrypoints.servers.transport.application.usecases.commands.chat.create import Usecase as CreateChatUsecase
from src.entrypoints.servers.transport.framework.websockets import manager
from src.entrypoints.servers.transport.infrastructure.storages.redis.repositories import presence
from src.framework.routing import APIRouter
from src.infrastructure.brokers.collections import EventStatus
from src.infrastructure.brokers.collections import Topic
from src.infrastructure.security.jwt import jwt


router = APIRouter()


@contextlib.asynccontextmanager
async def connection(user_id: str, websocket: WebSocket):
    await manager.connect(key=user_id, websocket=websocket)
    await presence.connect(key=user_id)
    try:
        yield
    finally:
        await manager.disconnect(key=user_id, websocket=websocket)
        await presence.disconnect(key=user_id)


@router.websocket("/ws")
async def connect(websocket: WebSocket, token: str = Query(...)) -> None:
    user_id = jwt.decode(token=token).sub

    async with connection(user_id=user_id, websocket=websocket):
        with contextlib.suppress(WebSocketDisconnect):
            while True:
                response = None

                request = await websocket.receive_text()

                try:
                    payload = json.loads(request)
                except json.JSONDecodeError:
                    continue

                try:
                    event = Event.model_validate(payload)
                except ValidationError:
                    continue

                command = {"user_id": user_id, **event.model_dump()}

                try:
                    if event.topic is Topic.chat_create:
                        response = await CreateChatUsecase().execute(command=CreateChat.model_validate(command))
                    await websocket.send_json(response.model_dump(mode="json"))
                except Exception as exception:
                    event.status = EventStatus.error
                    event.error = str(exception)
                    await websocket.send_json(event.model_dump(mode="json"))
