from fastapi import Body
from fastapi import Depends
from fastapi import status

from src.application.usecases.chats.create import Usecase
from src.entrypoints.http.common.collections import AUTHORIZATION_ERRORS
from src.entrypoints.http.common.deps import jwt
from src.entrypoints.http.public.deps.chats.create import dependency
from src.entrypoints.http.public.schemas.chat import Chat
from src.entrypoints.http.public.schemas.chat import CreateChat
from src.framework.openapi.utils import errors
from src.framework.routing import APIRouter


router = APIRouter()


@router.post(
    "/chats:create",
    response_model=Chat,
    responses={status.HTTP_401_UNAUTHORIZED: {}, **errors(*AUTHORIZATION_ERRORS)},
    description="Create a chat with selected members",
)
async def command(
    body: CreateChat = Body(...),
    uid: str = Depends(jwt),
    usecase: Usecase = Depends(dependency),
) -> Chat:
    payload = await usecase(uid, body.members)
    return Chat.serialize(
        chat=payload["chat"],
        members=payload["members"],
        pin_position=None,
        unread_count=0,
        last_message=payload["last_message"],
    )
