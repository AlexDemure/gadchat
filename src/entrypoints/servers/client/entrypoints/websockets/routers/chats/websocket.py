import json

from fastapi import Query
from fastapi import WebSocket
from fastapi import WebSocketDisconnect

from src.common.formats.utils import date
from src.framework.routing import APIRouter
from src.infrastructure.security.jwt import jwt
from src.infrastructure.security.jwt.collections import TokenInvalid

from ...manager import manager


router = APIRouter()


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
            payload = json.loads(raw)
            if payload.get("type") == "ping":
                await websocket.send_json({"event": "pong", "ts": date.now().isoformat()})
                continue
            await websocket.send_json(
                {"event": "ignored", "reason": "Use POST /chats/{chat_id}/messages:create for writes in this MVP"}
            )
    except WebSocketDisconnect:
        await manager.disconnect(uid, websocket)
