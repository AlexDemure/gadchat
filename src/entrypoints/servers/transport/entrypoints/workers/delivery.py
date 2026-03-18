import json as stdjson

from fastapi import WebSocket

from src.application.protocols.transport import Event
from src.common.formats.utils import json
from src.entrypoints.servers.transport.framework.websockets import manager
from src.infrastructure.monitoring.logging import logger
from src.infrastructure.storages.redis import redis
from src.infrastructure.storages.redis.collections import Gateway


async def send_to_user_sockets(user_ids: list[str], payload: dict[str, object]) -> None:
    serialized = stdjson.dumps(payload, default=str)
    owners = await manager.sockets(keys=user_ids)

    targets: dict[WebSocket, set[str]] = {}
    for user_id, sockets in owners.items():
        for socket in sockets:
            targets.setdefault(socket, set()).add(user_id)

    stale: list[tuple[str, WebSocket]] = []
    for socket, socket_user_ids in targets.items():
        try:
            await socket.send_text(serialized)
        except Exception:
            for user_id in socket_user_ids:
                stale.append((user_id, socket))

    for user_id, socket in stale:
        await manager.disconnect(key=user_id, websocket=socket)


async def listen() -> None:
    pubsub = redis.pubsub()
    channel = Gateway.node_events(presence.node_id)
    await pubsub.subscribe(channel)

    try:
        async for message in pubsub.listen():
            if message.get("type") != "message":
                continue

            data = message.get("data")
            if not isinstance(data, str):
                continue

            event = Event.model_validate(json.fromstring(data))
            user_ids = event.targets.user_ids if event.targets else []
            if not user_ids:
                continue

            connected = await presence.users()
            targets = [user_id for user_id in user_ids if user_id in connected]
            if targets:
                await send_to_user_sockets(
                    user_ids=targets,
                    payload=event.model_dump(mode="json", by_alias=True),
                )
    except Exception:
        logger.exception("Gateway delivery listener crashed")
        raise
    finally:
        await pubsub.unsubscribe(channel)
        await pubsub.close()
