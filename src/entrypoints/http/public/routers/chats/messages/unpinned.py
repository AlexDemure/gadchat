from fastapi import Depends
from fastapi import Path
from fastapi import Response
from fastapi import status

from src.application.collections import MessageNotFound
from src.application.collections import UserNotChatMember
from src.application.usecases.chats.messages.unpinned import Usecase
from src.entrypoints.http.common.collections import AUTHORIZATION_ERRORS
from src.entrypoints.http.common.deps import user
from src.entrypoints.http.public.deps.chats.messages.unpinned import dependency
from src.framework.openapi.utils import errors
from src.framework.routing import APIRouter
from src.infrastructure.databases.postgres.tables import User


router = APIRouter()


@router.delete(
    "/chats/{chat_id}/messages/{message_id}:pinned",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    responses={status.HTTP_401_UNAUTHORIZED: {}, **errors(*AUTHORIZATION_ERRORS, UserNotChatMember, MessageNotFound)},
    description="Delete message pinned",
)
async def command(
    chat_id: str = Path(...),
    message_id: str = Path(...),
    usecase: Usecase = Depends(dependency),
    _user: User = Depends(user),
) -> None:
    await usecase(user=_user, chat_id=chat_id, message_id=message_id)
