from fastapi import Depends
from fastapi import status

from src.application.collections import MessageKind
from src.application.collections.enums.topic import Topic
from src.common.formats.utils import date
from src.common.formats.utils import uuid
from src.entrypoints.servers.auth.entrypoints.http.common.deps import user
from src.framework.routing import APIRouter
from src.protocols.chat import Message
from src.protocols.events import CreateMessage


router = APIRouter()


@router.get(
    f"/{Topic.message_create.event}",
    status_code=status.HTTP_200_OK,
    response_model=CreateMessage,
    description="Message created event",
    dependencies=[Depends(user)],
)
async def event() -> CreateMessage:
    return CreateMessage(
        event=Topic.message_create.event,
        message=Message(
            id=uuid.unique(),
            kind=MessageKind.user,
            text=None,
            attachments=[],
            pinned=None,
            edited=None,
            created=date.now(),
            member=None,
            reply=None,
            forward=None,
        ),
    )
