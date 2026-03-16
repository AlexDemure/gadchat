import uuid

from fastapi import Body
from fastapi import Depends
from fastapi import status

from src.application.usecases.chats.messages.read import Usecase
from src.entrypoints.http.common.collections import AUTHORIZATION_ERRORS
from src.entrypoints.http.common.deps import jwt
from src.entrypoints.http.public.deps.chats.messages.read import dependency
from src.entrypoints.http.public.schemas.chat import ReadMessages
from src.framework.openapi.utils import errors
from src.framework.routing import APIRouter


router = APIRouter()


@router.post(
    "/chats/{chat_id}/messages:read",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={status.HTTP_401_UNAUTHORIZED: {}, **errors(*AUTHORIZATION_ERRORS)},
    description="Mark messages as read up to the selected message",
)
async def command(
    chat_id: uuid.UUID,
    body: ReadMessages = Body(...),
    uid: str = Depends(jwt),
    usecase: Usecase = Depends(dependency),
) -> None:
    await usecase(chat_id=chat_id, message_id=body.message_id, user_id=uid)
