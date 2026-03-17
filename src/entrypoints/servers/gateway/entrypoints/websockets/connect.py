import json
import typing

from fastapi import Query
from fastapi import WebSocket
from fastapi import WebSocketDisconnect
from pydantic import ValidationError

from src.application.collections import Topic
from src.common.http.collections import HTTPError
from src.entrypoints.servers.gateway.application.usecases.connect import Container
from src.entrypoints.servers.gateway.application.usecases.connect import Repository
from src.entrypoints.servers.gateway.application.usecases.connect import Usecase
from src.entrypoints.servers.gateway.framework.websockets.setup import websockets
from src.framework.routing import APIRouter
from src.infrastructure.databases.postgres import postgres
from src.infrastructure.security.jwt import jwt
from src.infrastructure.security.jwt.collections import TokenInvalid
from src.protocols import Event
from src.protocols.commands import CreateChat
from src.protocols.commands import CreateMessage
from src.protocols.commands import PinMessage
from src.protocols.commands import PositionChat
from src.protocols.commands import ReadMessage
from src.protocols.commands import UnpinMessage


router = APIRouter()

CommandSchema = typing.Union[CreateChat, PositionChat, CreateMessage, PinMessage, UnpinMessage, ReadMessage]
commands: dict[str, type[typing.Any]] = {
    Topic.chat_create.command: CreateChat,
    Topic.chat_position.command: PositionChat,
    Topic.message_create.command: CreateMessage,
    Topic.message_pin.command: PinMessage,
    Topic.message_unpin.command: UnpinMessage,
    Topic.message_read.command: ReadMessage,
}


def error(reason: str, detail: typing.Any = None) -> dict[str, typing.Any]:
    payload = {"event": "error", "reason": reason}
    if detail is not None:
        payload["detail"] = detail
    return payload


def command(payload: dict[str, typing.Any]) -> CommandSchema:
    topic = payload.get("topic")
    schema = commands.get(topic)
    if schema is None:
        raise ValueError(f"Unsupported topic: {topic}")
    return schema.model_validate(payload)


@router.websocket("/ws")
async def connect(websocket: WebSocket, token: str = Query(...)) -> None:
    try:
        user_id = jwt.decode(token=token).sub
    except TokenInvalid:
        await websocket.close(code=1008)
        return

    await websockets.connect(user_id, websocket)

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_json(error(reason="Invalid JSON payload"))
                continue

            if not isinstance(payload, dict):
                await websocket.send_json(error(reason="Payload must be an object"))
                continue

            try:
                body = command(payload)
            except ValueError as exception:
                await websocket.send_json(error(reason=str(exception)))
                continue
            except ValidationError as exception:
                await websocket.send_json(error(reason="Invalid command payload", detail=exception.errors()))
                continue

            try:
                async with postgres.orm.write() as session:
                    usecase = Usecase(Container(Repository(session)))
                    event = await usecase.publish(user_id=user_id, command=body)
            except HTTPError as exception:
                await websocket.send_json(error(reason=str(exception), detail=exception.http["detail"]))
                continue

            await websocket.send_json(Event.serialize(event).model_dump(mode="json"))
    except WebSocketDisconnect:
        await websockets.disconnect(user_id, websocket)
