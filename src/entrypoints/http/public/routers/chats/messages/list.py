import uuid

from fastapi import Depends
from fastapi import Query

from src.application.usecases.chats.messages.list import Usecase
from src.entrypoints.http.common.collections import PAGE_SIZE_DEFAULT
from src.entrypoints.http.common.collections import PAGE_SIZE_MAX
from src.entrypoints.http.common.deps import user_id
from src.entrypoints.http.public.deps.chats.messages.list import dependency
from src.entrypoints.http.public.schemas.chat import MessagePage
from src.framework.routing import APIRouter


router = APIRouter()


@router.get("/chats/{chat_id}/messages", response_model=MessagePage)
async def query(
    chat_id: uuid.UUID,
    cursor: str | None = Query(default=None),
    direction: str = Query(default="before", pattern="^(before|after)$"),
    limit: int = Query(default=PAGE_SIZE_DEFAULT, ge=1, le=PAGE_SIZE_MAX),
    uid: str = Depends(user_id),
    usecase: Usecase = Depends(dependency),
) -> MessagePage:
    payload = await usecase(chat_id=chat_id, user_id=uid, cursor=cursor, direction=direction, limit=limit)
    return MessagePage.serialize(
        items=payload["items"],
        has_more=payload["has_more"],
        prev_cursor=payload["prev_cursor"],
        next_cursor=payload["next_cursor"],
    )
