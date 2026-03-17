from fastapi import Body
from fastapi import Depends
from fastapi import status

from src.application.collections import RoleNotFound
from src.application.usecases.chats.create import Usecase
from src.entrypoints.http.common.collections import AUTHORIZATION_ERRORS
from src.entrypoints.http.common.deps import user
from src.entrypoints.http.public.deps.chats.create import dependency
from src.entrypoints.http.public.schemas.chat import Chat
from src.entrypoints.http.public.schemas.chat import CreateChat
from src.framework.openapi.utils import errors
from src.framework.routing import APIRouter
from src.infrastructure.databases.postgres.tables import User


router = APIRouter()


@router.post(
    "/chats:create",
    status_code=status.HTTP_201_CREATED,
    response_model=Chat,
    responses={status.HTTP_401_UNAUTHORIZED: {}, **errors(*AUTHORIZATION_ERRORS, RoleNotFound)},
    description="Create chat",
)
async def command(
    body: CreateChat = Body(...),
    usecase: Usecase = Depends(dependency),
    _user: User = Depends(user),
) -> Chat:
    chat = await usecase(user=_user, **body.deserialize())
    return Chat.serialize(user=_user, chat=chat)
