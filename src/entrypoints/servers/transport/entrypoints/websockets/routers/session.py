import json

from fastapi import Depends
from fastapi import Query
from fastapi import WebSocket
from pydantic import ValidationError

from src.application.protocols import commands
from src.application.protocols import transport
from src.entrypoints.servers.transport.application.usecases.commands.chats.create import Usecase as CreateChatUsecase
from src.entrypoints.servers.transport.application.usecases.commands.chats.messages.create import (
    Usecase as CreateMessageUsecase,
)
from src.entrypoints.servers.transport.application.usecases.sessions.connect import Usecase as ConnectUsecase
from src.entrypoints.servers.transport.entrypoints.websockets.deps.chats.create import (
    dependency as create_chat_dependency,
)
from src.entrypoints.servers.transport.entrypoints.websockets.deps.chats.messages.create import (
    dependency as create_message_dependency,
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
    usecase_create_message: CreateMessageUsecase = Depends(create_message_dependency),
) -> None:
    async with usecase_connect.execute(websocket=websocket, token=token) as connection:
        while True:
            request = await websocket.receive_text()

            try:
                payload = json.loads(request)
            except json.JSONDecodeError:
                continue

            try:
                event = transport.Event.model_validate(payload)
            except ValidationError:
                continue

            command = {"user_id": connection.user_id, **event.model_dump()}

            try:
                if event.topic is Topic.chat_create:
                    response = await usecase_create_chat.execute(commands.CreateChat.model_validate(command))
                elif event.topic is Topic.chat_message_create:
                    response = await usecase_create_message.execute(commands.CreateMessage.model_validate(command))
                else:
                    response = None

                if response:
                    await websocket.send_json(response.model_dump(mode="json", by_alias=True))
                else:
                    ...
            except Exception as exception:
                event.status = EventStatus.error
                event.error = str(exception)
                await websocket.send_json(event.model_dump(mode="json", by_alias=True))
