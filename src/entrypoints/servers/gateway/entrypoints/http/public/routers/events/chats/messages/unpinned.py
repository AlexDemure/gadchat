from fastapi import Depends
from fastapi import status

from src.application.collections.enums.topic import Topic
from src.common.formats.utils import uuid
from src.entrypoints.servers.auth.entrypoints.http.common.deps import user
from src.framework.routing import APIRouter
from src.protocols.events import UnpinMessage


router = APIRouter()


@router.get(
    f"/{Topic.message_unpin.event}",
    status_code=status.HTTP_200_OK,
    response_model=UnpinMessage,
    description="Message unpinned event",
    dependencies=[Depends(user)],
)
async def event() -> UnpinMessage:
    return UnpinMessage(
        event=Topic.message_unpin.event,
        chat_id=uuid.unique(),
        message_id=uuid.unique(),
    )
