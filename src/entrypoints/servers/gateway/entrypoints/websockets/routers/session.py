import json

from contextlib import asynccontextmanager
from contextlib import suppress

from fastapi import Query
from fastapi import WebSocket
from fastapi import WebSocketDisconnect
from pydantic import ValidationError

from src.application.protocols.transport import Event
from src.entrypoints.servers.gateway.application.usecases.commands.chat.create import Usecase as CreateChatUsecase
from src.entrypoints.servers.gateway.framework.websockets import manager
from src.entrypoints.servers.gateway.infrastructure.storages.redis.repositories import presence
from src.framework.routing import APIRouter
from src.infrastructure.brokers.collections import Topic
from src.infrastructure.security.jwt import jwt


router = APIRouter()


@asynccontextmanager
async def connection(user_id: str, websocket: WebSocket):
    await manager.connect(key=user_id, websocket=websocket)
    await presence.connect(key=user_id)
    try:
        yield
    finally:
        await manager.disconnect(key=user_id, websocket=websocket)
        await presence.disconnect(key=user_id)


@router.websocket("/ws")
async def connect(
    websocket: WebSocket,
    token: str = Query(...),
) -> None:
    user_id = jwt.decode(token=token).sub

    async with connection(user_id=user_id, websocket=websocket):
        with suppress(WebSocketDisconnect):
            while True:
                response = None

                request = await websocket.receive_text()

                try:
                    payload = json.loads(request)
                    event = Event.model_validate(payload)
                except (json.JSONDecodeError, ValidationError):
                    continue

                if event.topic is Topic.chat_create:
                    response = await CreateChatUsecase().execute(token=token, payload=payload)

                if not response:
                    continue

                await websocket.send_json(response.model_dump(mode="json"))
