from fastapi import Depends
from fastapi import status

from src.application.collections.enums.topic import Topic
from src.common.formats.utils import date
from src.common.formats.utils import uuid
from src.entrypoints.servers.auth.entrypoints.http.common.deps import user
from src.framework.routing import APIRouter
from src.protocols.events import ReadMessage


router = APIRouter()


@router.get(
    f"/{Topic.message_read.event}",
    status_code=status.HTTP_200_OK,
    response_model=ReadMessage,
    description="Message read event",
    dependencies=[Depends(user)],
)
async def event() -> ReadMessage:
    return ReadMessage(
        event=Topic.message_read.event,
        chat_id=uuid.unique(),
        message_id=uuid.unique(),
        member_id=uuid.unique(),
        created=date.now(),
    )
