import uuid

from fastapi import Depends
from fastapi import status

from src.application.usecases.chats.messages.pin import Usecase
from src.entrypoints.http.common.collections import AUTHORIZATION_ERRORS
from src.entrypoints.http.common.deps import jwt
from src.entrypoints.http.public.deps.chats.messages.pin import dependency
from src.framework.openapi.utils import errors
from src.framework.routing import APIRouter


router = APIRouter()


@router.post(
    "/chats/{chat_id}/messages/{message_id}:pin",
    status_code=status.HTTP_202_ACCEPTED,
    responses={status.HTTP_401_UNAUTHORIZED: {}, **errors(*AUTHORIZATION_ERRORS)},
    description="Pin a message in chat",
)
async def command(
    chat_id: uuid.UUID,
    message_id: uuid.UUID,
    uid: str = Depends(jwt),
    usecase: Usecase = Depends(dependency),
) -> None:
    await usecase(chat_id=chat_id, message_id=message_id, user_id=uid)
