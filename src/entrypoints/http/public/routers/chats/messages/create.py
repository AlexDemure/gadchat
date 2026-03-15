import uuid

from fastapi import Body
from fastapi import Depends
from fastapi import HTTPException

from src.application.usecases.chats.messages.create import Usecase
from src.configuration import settings
from src.entrypoints.http.common.collections import REDIS_CHANNEL_EVENTS
from src.entrypoints.http.common.deps import user_id
from src.entrypoints.http.public.deps.chats.messages.create import dependency
from src.entrypoints.http.public.schemas.chat import ChatMessage
from src.entrypoints.http.public.schemas.chat import CreateMessage
from src.entrypoints.http.public.schemas.chat import MessageCommand
from src.entrypoints.http.public.schemas.chat import MessageCreated
from src.entrypoints.websockets.manager import manager
from src.framework.routing import APIRouter
from src.infrastructure.brokers.kafka import kafka
from src.infrastructure.storages.redis import redis


router = APIRouter()


@router.post("/messages")
async def command(
    body: CreateMessage = Body(...),
    uid: str = Depends(user_id),
    usecase: Usecase = Depends(dependency),
) -> MessageCommand:
    if body.chat_id:
        try:
            uuid.UUID(body.chat_id)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid chat_id") from exc

    ingress_event = {
        "sender_id": uid,
        "chat_id": body.chat_id,
        "peer_user_id": body.peer_user_id,
        "body": body.body,
        "attachments": body.attachments,
    }

    if settings.KAFKA:
        if not kafka:
            raise HTTPException(status_code=503, detail="Kafka broker is not available")
        await kafka.publish(
            ingress_event,
            topic=settings.KAFKA_TOPIC_INGRESS,
            key=str(ingress_event.get("chat_id") or ingress_event.get("peer_user_id") or "").encode("utf-8"),
        )
        return MessageCommand(status="accepted")

    stored = await usecase(
        sender_id=ingress_event["sender_id"],
        body=ingress_event["body"],
        attachments=ingress_event["attachments"],
        chat_id=uuid.UUID(ingress_event["chat_id"]) if ingress_event.get("chat_id") else None,
        peer_user_id=ingress_event.get("peer_user_id"),
    )

    delivery_event = MessageCreated.serialize(
        chat_id=str(stored["chat"].id),
        message=stored["message"],
        recipients=stored["recipients"],
    )

    if settings.REDIS and redis.client:
        await redis.publish(REDIS_CHANNEL_EVENTS, delivery_event)
    else:
        # fallback delivery for single-node/no-redis
        await manager.send_to_users(delivery_event.get("recipients", []), delivery_event)

    return MessageCommand(
        status="persisted",
        chat_id=str(stored["chat"].id),
        message=ChatMessage.serialize(stored["message"]),
    )
