from fastapi import Body
from fastapi import Depends
from fastapi import Path
from fastapi import status

from src.application.collections import UserNotChatMember
from src.entrypoints.http.common.collections import AUTHORIZATION_ERRORS
from src.entrypoints.servers.auth.entrypoints.http.common.deps import user
from src.entrypoints.servers.core.application.usecases.chats.messages.search import Usecase
from src.entrypoints.servers.core.entrypoints.http.public.deps.chats.messages.search import dependency
from src.entrypoints.servers.core.entrypoints.http.public.schemas.chat import Messages
from src.entrypoints.servers.core.entrypoints.http.public.schemas.chat import SearchMessages
from src.framework.openapi.utils import errors
from src.framework.routing import APIRouter
from src.infrastructure.databases.postgres.tables import User


router = APIRouter()


@router.post(
    "/api/chats/{chat_id}/messages:search",
    status_code=status.HTTP_200_OK,
    response_model=Messages,
    responses={status.HTTP_401_UNAUTHORIZED: {}, **errors(*AUTHORIZATION_ERRORS, UserNotChatMember)},
    description="Search messages",
)
async def query(
    chat_id: str = Path(...),
    body: SearchMessages = Body(...),
    usecase: Usecase = Depends(dependency),
    _user: User = Depends(user),
) -> Messages:
    data = body.deserialize()
    data["filters"]["chat_id"] = chat_id
    data["filters"]["user_id"] = _user.id
    messages, more, prev, next = await usecase(**data)
    return Messages.serialize(messages=messages, more=more, prev=prev, next=next)
