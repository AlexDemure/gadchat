from fastapi import Body
from fastapi import Depends
from fastapi import Path
from fastapi import Response
from fastapi import status

from src.application.collections import UserNotChatMember
from src.application.usecases.chats.position import Usecase
from src.entrypoints.http.common.collections import AUTHORIZATION_ERRORS
from src.entrypoints.http.common.deps import user
from src.entrypoints.http.public.deps.chats.position import dependency
from src.entrypoints.http.public.schemas.chat import PositionChat
from src.framework.openapi.utils import errors
from src.framework.routing import APIRouter
from src.infrastructure.databases.postgres.tables import User


router = APIRouter()


@router.patch(
    "/chats/{chat_id}:position",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    responses={status.HTTP_401_UNAUTHORIZED: {}, **errors(*AUTHORIZATION_ERRORS, UserNotChatMember)},
    description="Patch chat position",
)
async def command(
    chat_id: str = Path(...),
    body: PositionChat = Body(...),
    usecase: Usecase = Depends(dependency),
    _user: User = Depends(user),
) -> None:
    await usecase(user=_user, chat_id=chat_id, position=body.position)
