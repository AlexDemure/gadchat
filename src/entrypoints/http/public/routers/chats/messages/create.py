import uuid

from fastapi import Body
from fastapi import Depends
from fastapi import status

from src.application.usecases.chats.messages.create import Usecase
from src.configuration import settings
from src.entrypoints.http.common.collections import AUTHORIZATION_ERRORS
from src.entrypoints.http.common.deps import jwt
from src.entrypoints.http.public.deps.chats.messages.create import dependency
from src.entrypoints.http.public.schemas.chat import CreateMessage
from src.framework.openapi.utils import errors
from src.framework.routing import APIRouter
from src.infrastructure.brokers.kafka import kafka


router = APIRouter()


@router.post(
    "/chats/{chat_id}/messages:create",
    status_code=status.HTTP_202_ACCEPTED,
    responses={status.HTTP_401_UNAUTHORIZED: {}, **errors(*AUTHORIZATION_ERRORS)},
    description="Publish a new chat message event",
)
async def command(
    chat_id: uuid.UUID,
    body: CreateMessage = Body(...),
    uid: str = Depends(jwt),
    usecase: Usecase = Depends(dependency),
) -> None:
    await usecase.validate(chat_id=chat_id, user_id=uid)

    ingress_event = {
        "sender_id": uid,
        "chat_id": str(chat_id),
        "peer_user_id": None,
        "body": body.body,
        "attachments": body.attachments,
    }

    await kafka.publish(
        ingress_event,
        topic=settings.KAFKA_TOPIC_INGRESS,
        key=str(ingress_event.get("chat_id") or ingress_event.get("peer_user_id") or "").encode("utf-8"),
    )
