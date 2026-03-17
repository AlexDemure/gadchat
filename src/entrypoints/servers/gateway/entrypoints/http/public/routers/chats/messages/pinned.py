from fastapi import Body
from fastapi import status

from src.entrypoints.servers.gateway.entrypoints.http.public.schemas.chat import Event
from src.entrypoints.servers.gateway.entrypoints.http.public.schemas.chat import PinnedMessage
from src.framework.routing import APIRouter


router = APIRouter()


@router.post(
    "/message.pinned.command",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=Event,
    description="Patch message pinned",
)
async def command(
    body: PinnedMessage = Body(...),
) -> Event:
    _ = body
    return Event.mock(topic="message.pinned.command")
