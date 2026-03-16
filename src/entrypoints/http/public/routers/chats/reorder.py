from fastapi import Body
from fastapi import Depends
from fastapi import status

from src.application.usecases.chats.reorder import Usecase
from src.entrypoints.http.common.collections import AUTHORIZATION_ERRORS
from src.entrypoints.http.common.deps import jwt
from src.entrypoints.http.public.deps.chats.reorder import dependency
from src.entrypoints.http.public.schemas.chat import ReorderChats
from src.framework.openapi.utils import errors
from src.framework.routing import APIRouter


router = APIRouter()


@router.put(
    "/chats:pins",
    status_code=status.HTTP_202_ACCEPTED,
    responses={status.HTTP_401_UNAUTHORIZED: {}, **errors(*AUTHORIZATION_ERRORS)},
    description="Reorder pinned chats for the current user",
)
async def command(
    body: ReorderChats = Body(...),
    uid: str = Depends(jwt),
    usecase: Usecase = Depends(dependency),
) -> None:
    await usecase(chat_ids=body.chats, user_id=uid)
