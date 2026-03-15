import json

from fastapi import HTTPException
from fastapi import Query
from fastapi import WebSocket
from fastapi import WebSocketDisconnect

from src.common.formats.utils import date
from src.entrypoints.http.public.collections.chats import verify_ws_ticket
from src.entrypoints.websockets.manager import manager
from src.framework.routing import APIRouter


router = APIRouter()


@router.websocket("/ws")
async def query(websocket: WebSocket, ticket: str = Query(...)) -> None:
    try:
        uid = verify_ws_ticket(ticket)
    except HTTPException:
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
            await websocket.send_json({"event": "ignored", "reason": "Use POST /messages for writes in this MVP"})
    except WebSocketDisconnect:
        await manager.disconnect(uid, websocket)
