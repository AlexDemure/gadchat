from fastapi import Depends
from fastapi import status

from src.application.collections.enums.topic import Topic
from src.common.formats.utils import date
from src.common.formats.utils import uuid
from src.entrypoints.servers.auth.entrypoints.http.common.deps import user
from src.framework.routing import APIRouter
from src.protocols.events import PinMessage


router = APIRouter()


@router.get(
    f"/{Topic.message_pin.event}",
    status_code=status.HTTP_200_OK,
    response_model=PinMessage,
    description="Message pinned event",
    dependencies=[Depends(user)],
)
async def event() -> PinMessage:
    return PinMessage(
        event=Topic.message_pin.event,
        chat_id=uuid.unique(),
        message_id=uuid.unique(),
        pinned=date.now(),
    )
