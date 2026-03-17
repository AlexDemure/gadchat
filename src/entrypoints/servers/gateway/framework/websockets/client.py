import asyncio
import collections
import datetime
import json
import typing

from fastapi import WebSocket


class Client:
    def __init__(self) -> None:
        self._by_user: dict[str, set[WebSocket]] = collections.defaultdict(set)
        self._lock = asyncio.Lock()

    async def connect(self, user_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._by_user[user_id].add(websocket)

    async def disconnect(self, user_id: str, websocket: WebSocket) -> None:
        last_seen_at = None
        async with self._lock:
            sockets = self._by_user.get(user_id)
            if not sockets:
                return
            sockets.discard(websocket)
            if not sockets:
                self._by_user.pop(user_id, None)
                last_seen_at = datetime.datetime.now(datetime.timezone.utc)
        if last_seen_at is not None:
            return

    async def send_to_users(self, user_ids: list[str], payload: dict[str, typing.Any]) -> None:
        serialized = json.dumps(payload, default=str)
        async with self._lock:
            targets = {socket for user_id in user_ids for socket in self._by_user.get(user_id, set())}

        stale: list[tuple[str, WebSocket]] = []
        for socket in targets:
            try:
                await socket.send_text(serialized)
            except Exception:
                for user_id in user_ids:
                    if socket in self._by_user.get(user_id, set()):
                        stale.append((user_id, socket))

        for user_id, socket in stale:
            await self.disconnect(user_id, socket)
