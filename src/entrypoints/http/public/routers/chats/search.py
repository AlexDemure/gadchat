from fastapi import Body
from fastapi import Depends
from fastapi import status

from src.application.usecases.chats.search import Usecase
from src.entrypoints.http.common.collections import AUTHORIZATION_ERRORS
from src.entrypoints.http.common.deps import jwt
from src.entrypoints.http.public.deps.chats.search import dependency
from src.entrypoints.http.public.schemas.chat import Chats
from src.entrypoints.http.public.schemas.chat import SearchChats
from src.framework.openapi.utils import errors
from src.framework.routing import APIRouter


router = APIRouter()


@router.post(
    "/chats:search",
    response_model=Chats,
    responses={status.HTTP_401_UNAUTHORIZED: {}, **errors(*AUTHORIZATION_ERRORS)},
    description="Search chats with cursor pagination",
)
async def command(
    body: SearchChats = Body(...),
    uid: str = Depends(jwt),
    usecase: Usecase = Depends(dependency),
) -> Chats:
    payload = body.deserialize()
    payload["filters"]["user_id"] = uid
    payload = await usecase(
        filters=payload["filters"],
        sorting=payload["sorting"],
        pagination=payload["pagination"],
    )
    return Chats.serialize(
        items=payload["items"],
        has_more=payload["has_more"],
        prev_cursor=payload["prev_cursor"],
        next_cursor=payload["next_cursor"],
    )
