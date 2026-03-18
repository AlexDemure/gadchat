import asyncio
import collections

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self.connections: dict[str, set[WebSocket]] = collections.defaultdict(set)
        self.lock = asyncio.Lock()

    async def connect(self, key: str, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self.lock:
            self.connections[key].add(websocket)

    async def disconnect(self, key: str, websocket: WebSocket) -> None:
        async with self.lock:
            if sockets := self.connections.get(key):
                sockets.discard(websocket)
                if not sockets:
                    self.connections.pop(key, None)

    async def connected(self, key: str) -> bool:
        async with self.lock:
            return bool(self.connections.get(key))

    async def sockets(self, keys: list[str]) -> dict[str, set[WebSocket]]:
        async with self.lock:
            return {key: set(self.connections.get(key, set())) for key in keys if self.connections.get(key)}
