from fastapi import Body
from fastapi import status

from src.entrypoints.servers.gateway.entrypoints.http.public.schemas.chat import Event
from src.entrypoints.servers.gateway.entrypoints.http.public.schemas.chat import UnpinnedMessage
from src.framework.routing import APIRouter


router = APIRouter()


@router.post(
    "/message.unpinned.command",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=Event,
    description="Delete message pinned",
)
async def command(
    body: UnpinnedMessage = Body(...),
) -> Event:
    _ = body
    return Event.mock(topic="message.unpinned.command")
