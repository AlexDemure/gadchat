import typing

from src.entrypoints.servers.gateway.framework.websockets.setup import websockets


async def deliver(payload: dict[str, typing.Any]) -> None:
    recipients = payload.get("recipients", [])
    if not isinstance(recipients, list):
        return
    user_ids = [user_id for user_id in recipients if isinstance(user_id, str)]
    if not user_ids:
        return
    await websockets.send_to_users(user_ids, payload)
