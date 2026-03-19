from fastapi import Body
from fastapi import Depends
from fastapi import status
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.security import HTTPBearer

from src.entrypoints.http.common.collections import AUTHORIZATION_ERRORS
from src.entrypoints.servers.auth.application.usecases.users.current import Usecase as CurrentUserUsecase
from src.entrypoints.servers.read.application.usecases.chats.search import Usecase
from src.entrypoints.servers.read.entrypoints.http.public.deps.chats.search import dependency
from src.entrypoints.servers.read.entrypoints.http.public.deps.users.current import (
    dependency as current_user_dependency,
)
from src.entrypoints.servers.read.entrypoints.http.public.schemas.chat import Chats
from src.entrypoints.servers.read.entrypoints.http.public.schemas.chat import SearchChats
from src.framework.openapi.utils import errors
from src.framework.routing import APIRouter


router = APIRouter()


@router.post(
    "/api/chats:search",
    status_code=status.HTTP_200_OK,
    response_model=Chats,
    responses={status.HTTP_401_UNAUTHORIZED: {}, **errors(*AUTHORIZATION_ERRORS)},
    description="Search chats",
)
async def query(
    body: SearchChats = Body(...),
    usecase: Usecase = Depends(dependency),
    authorization: HTTPAuthorizationCredentials = Depends(HTTPBearer(bearerFormat="JWT")),
    current_user: CurrentUserUsecase = Depends(current_user_dependency),
) -> Chats:
    user = await current_user.execute(authorization.credentials)
    data = body.deserialize()
    chats, more, prev, next = await usecase.execute(filters={"user_id": user.id}, pagination=data["pagination"])
    return Chats.serialize(chats=chats, more=more, prev=prev, next=next)
