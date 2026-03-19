import json

from fastapi import Depends
from fastapi import Query
from fastapi import WebSocket
from pydantic import ValidationError

from src.application.protocols.commands.chat import CreateChat
from src.application.protocols.transport import Event
from src.entrypoints.servers.transport.application.usecases.commands.chats.create import Usecase as CreateChatUsecase
from src.entrypoints.servers.transport.application.usecases.sessions.connect import Usecase as ConnectUsecase
from src.entrypoints.servers.transport.entrypoints.websockets.deps.chats.create import (
    dependency as create_chat_dependency,
)
from src.entrypoints.servers.transport.entrypoints.websockets.deps.sessions.connect import (
    dependency as connect_dependency,
)
from src.framework.routing import APIRouter
from src.infrastructure.brokers.collections import EventStatus
from src.infrastructure.brokers.collections import Topic


router = APIRouter()


@router.websocket("/ws")
async def connect(
    websocket: WebSocket,
    token: str = Query(...),
    usecase_connect: ConnectUsecase = Depends(connect_dependency),
    usecase_create_chat: CreateChatUsecase = Depends(create_chat_dependency),
) -> None:
    async with usecase_connect.execute(websocket=websocket, token=token) as connection:
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

            command = {"user_id": connection.user_id, **event.model_dump()}

            try:
                if event.topic is Topic.chat_create:
                    response = await usecase_create_chat.execute(command=CreateChat.model_validate(command))
                await websocket.send_json(response.model_dump(mode="json"))
            except Exception as exception:
                event.status = EventStatus.error
                event.error = str(exception)
                await websocket.send_json(event.model_dump(mode="json"))
