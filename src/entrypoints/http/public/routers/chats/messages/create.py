from fastapi import Body
from fastapi import Depends
from fastapi import Path
from fastapi import Response
from fastapi import status

from src.application.collections import ChatNotFound
from src.application.collections import FileNotFound
from src.application.collections import MemberNotFound
from src.application.collections import MessageNotFound
from src.application.usecases.chats.messages.create import Usecase
from src.entrypoints.http.common.collections import AUTHORIZATION_ERRORS
from src.entrypoints.http.common.deps import user
from src.entrypoints.http.public.deps.chats.messages.create import dependency
from src.entrypoints.http.public.schemas.chat import CreateMessage
from src.framework.openapi.utils import errors
from src.framework.routing import APIRouter
from src.infrastructure.databases.postgres.tables import User


router = APIRouter()


@router.post(
    "/chats/{chat_id}/messages:create",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    responses={
        status.HTTP_401_UNAUTHORIZED: {},
        **errors(*AUTHORIZATION_ERRORS, ChatNotFound, MemberNotFound, FileNotFound, MessageNotFound),
    },
    description="Create message",
)
async def command(
    chat_id: str = Path(...),
    body: CreateMessage = Body(...),
    usecase: Usecase = Depends(dependency),
    _user: User = Depends(user),
) -> None:
    await usecase(user=_user, chat_id=chat_id, **body.deserialize())
