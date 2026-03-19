from fastapi import Body
from fastapi import Depends
from fastapi import Path
from fastapi import status
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.security import HTTPBearer

from src.domain.collections import UserNotChatMember
from src.entrypoints.http.common.collections import AUTHORIZATION_ERRORS
from src.entrypoints.servers.auth.application.usecases.users.current import Usecase as CurrentUserUsecase
from src.entrypoints.servers.read.application.usecases.chats.messages.search import Usecase
from src.entrypoints.servers.read.entrypoints.http.public.deps.chats.messages.search import dependency
from src.entrypoints.servers.read.entrypoints.http.public.deps.users.current import (
    dependency as current_user_dependency,
)
from src.entrypoints.servers.read.entrypoints.http.public.schemas.chat import Messages
from src.entrypoints.servers.read.entrypoints.http.public.schemas.chat import SearchMessages
from src.framework.openapi.utils import errors
from src.framework.routing import APIRouter


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
    authorization: HTTPAuthorizationCredentials = Depends(HTTPBearer(bearerFormat="JWT")),
    current_user: CurrentUserUsecase = Depends(current_user_dependency),
) -> Messages:
    user = await current_user.execute(authorization.credentials)
    data = body.deserialize()
    messages, more, prev, next = await usecase.execute(
        filters={"chat_id": chat_id, "user_id": user.id},
        pagination=data["pagination"],
    )
    return Messages.serialize(messages=messages, more=more, prev=prev, next=next)
