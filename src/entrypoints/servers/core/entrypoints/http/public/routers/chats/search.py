from fastapi import Body
from fastapi import Depends
from fastapi import status

from src.entrypoints.http.common.collections import AUTHORIZATION_ERRORS
from src.entrypoints.servers.auth.entrypoints.http.common.deps import user
from src.entrypoints.servers.core.application.usecases.chats.search import Usecase
from src.entrypoints.servers.core.entrypoints.http.public.deps.chats.search import dependency
from src.entrypoints.servers.core.entrypoints.http.public.schemas.chat import Chats
from src.entrypoints.servers.core.entrypoints.http.public.schemas.chat import SearchChats
from src.framework.openapi.utils import errors
from src.framework.routing import APIRouter
from src.infrastructure.databases.postgres.tables import User


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
    _user: User = Depends(user),
) -> Chats:
    data = body.deserialize()
    data["filters"]["user_id"] = _user.id
    chats, more, prev, next = await usecase(**data)
    return Chats.serialize(user=_user, chats=chats, more=more, prev=prev, next=next)
