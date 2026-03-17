import json
import typing

from fastapi import Query
from fastapi import WebSocket
from fastapi import WebSocketDisconnect

from src.common.formats.utils import date
from src.common.http.collections import HTTPError
from src.entrypoints.servers.gateway.application.usecases.chats.create import Container
from src.entrypoints.servers.gateway.application.usecases.chats.create import Repository
from src.entrypoints.servers.gateway.application.usecases.chats.create import Usecase
from src.framework.routing import APIRouter
from src.infrastructure.databases.orm.sqlalchemy.queries import Filter
from src.infrastructure.databases.postgres import adapters
from src.infrastructure.databases.postgres import postgres
from src.infrastructure.security.jwt import jwt
from src.infrastructure.security.jwt.collections import TokenInvalid

from ...manager import manager


router = APIRouter()


def serialize_event(event: typing.Any) -> dict[str, typing.Any]:
    return {
        "id": event.id,
        "topic": event.topic,
        "priority": event.priority,
        "payload": event.payload,
        "created": event.created.isoformat(),
        "dispatched": event.dispatched.isoformat() if event.dispatched else None,
        "completed": event.completed.isoformat() if event.completed else None,
        "failed": event.failed.isoformat() if event.failed else None,
        "error": event.error,
    }


async def publish_chat_create(user_id: str, title: str, user_ids: list[str]) -> dict[str, typing.Any]:
    async with postgres.orm.write() as session:
        user = await adapters.repositories.User(session).one(Filter.eq(key="id", value=user_id))
        usecase = Usecase(Container(Repository(session)))
        event = await usecase.publish(user=user, title=title, user_ids=user_ids)
    return serialize_event(event)


@router.websocket("/ws")
async def query(websocket: WebSocket, token: str = Query(...)) -> None:
    try:
        uid = jwt.decode(token=token).sub
    except TokenInvalid:
        await websocket.close(code=1008)
        return

    await manager.connect(uid, websocket)
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_json({"event": "error", "reason": "Invalid JSON payload"})
                continue

            if payload.get("type") == "ping":
                await websocket.send_json({"event": "pong", "ts": date.now().isoformat()})
                continue

            if payload.get("type") == "chat.create":
                body = payload.get("payload", {})
                if not isinstance(body, dict):
                    await websocket.send_json({"event": "error", "reason": "Payload must be an object"})
                    continue

                raw_user_ids = body.get("user_ids", body.get("users", []))
                if not isinstance(raw_user_ids, list) or any(not isinstance(user_id, str) for user_id in raw_user_ids):
                    await websocket.send_json({"event": "error", "reason": "`user_ids` must be a string array"})
                    continue

                title = body.get("title", "")
                if title is None:
                    title = ""
                if not isinstance(title, str):
                    await websocket.send_json({"event": "error", "reason": "`title` must be a string"})
                    continue

                try:
                    event = await publish_chat_create(user_id=uid, title=title, user_ids=raw_user_ids)
                except HTTPError as error:
                    await websocket.send_json(
                        {
                            "event": "error",
                            "request_id": payload.get("id"),
                            "reason": str(error),
                            "detail": error.http["detail"],
                        }
                    )
                    continue

                await websocket.send_json(
                    {
                        "event": "chat.create.accepted",
                        "request_id": payload.get("id"),
                        "task": event,
                    }
                )
                continue

            await websocket.send_json(
                {"event": "ignored", "reason": f"Unsupported message type: {payload.get('type')}"}
            )
    except WebSocketDisconnect:
        await manager.disconnect(uid, websocket)
