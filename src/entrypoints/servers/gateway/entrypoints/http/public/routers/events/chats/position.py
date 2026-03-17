from fastapi import Depends
from fastapi import status

from src.application.collections.enums.topic import Topic
from src.common.formats.utils import uuid
from src.entrypoints.servers.auth.entrypoints.http.common.deps import user
from src.framework.routing import APIRouter
from src.protocols.events import PositionChat


router = APIRouter()


@router.get(
    f"/{Topic.chat_position.event}",
    status_code=status.HTTP_200_OK,
    response_model=PositionChat,
    description="Chat position updated event",
    dependencies=[Depends(user)],
)
async def event() -> PositionChat:
    return PositionChat(
        event=Topic.chat_position.event,
        chat_id=uuid.unique(),
        position=None,
    )
