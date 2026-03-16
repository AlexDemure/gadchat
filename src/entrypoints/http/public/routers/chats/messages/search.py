import uuid

from fastapi import Body
from fastapi import Depends
from fastapi import status

from src.application.usecases.chats.messages.search import Usecase
from src.entrypoints.http.common.collections import AUTHORIZATION_ERRORS
from src.entrypoints.http.common.deps import jwt
from src.entrypoints.http.public.deps.chats.messages.search import dependency
from src.entrypoints.http.public.schemas.chat import Messages
from src.entrypoints.http.public.schemas.chat import SearchMessages
from src.framework.openapi.utils import errors
from src.framework.routing import APIRouter


router = APIRouter()


@router.post(
    "/chats/{chat_id}/messages:search",
    response_model=Messages,
    responses={status.HTTP_401_UNAUTHORIZED: {}, **errors(*AUTHORIZATION_ERRORS)},
    description="Search chat messages with cursor pagination",
)
async def command(
    chat_id: uuid.UUID,
    body: SearchMessages = Body(...),
    uid: str = Depends(jwt),
    usecase: Usecase = Depends(dependency),
) -> Messages:
    payload = body.deserialize()
    payload["filters"]["chat_id"] = chat_id
    payload["filters"]["user_id"] = uid
    payload = await usecase(
        filters=payload["filters"],
        sorting=payload["sorting"],
        pagination=payload["pagination"],
    )
    return Messages.serialize(
        items=payload["items"],
        has_more=payload["has_more"],
        prev_cursor=payload["prev_cursor"],
        next_cursor=payload["next_cursor"],
    )
