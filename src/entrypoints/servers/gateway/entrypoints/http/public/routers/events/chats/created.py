from fastapi import Depends
from fastapi import status

from src.application.collections import Topic
from src.common.formats.utils import uuid
from src.entrypoints.servers.auth.entrypoints.http.common.deps import user
from src.framework.routing import APIRouter
from src.protocols.chat import Chat
from src.protocols.events import CreateChat


router = APIRouter()


@router.get(
    f"/{Topic.chat_create.event}",
    status_code=status.HTTP_200_OK,
    response_model=CreateChat,
    description="Chat created event",
    dependencies=[Depends(user)],
)
async def event() -> CreateChat:
    return CreateChat(
        event=Topic.chat_create.event,
        chat=Chat(id=uuid.unique(), title="Chat", members=[]),
    )
