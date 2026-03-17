from fastapi import Body
from fastapi import status

from src.entrypoints.servers.gateway.entrypoints.http.public.schemas.chat import Event
from src.entrypoints.servers.gateway.entrypoints.http.public.schemas.chat import ReadMessage
from src.framework.routing import APIRouter


router = APIRouter()


@router.post(
    "/message.read.command",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=Event,
    description="Read message",
)
async def command(
    body: ReadMessage = Body(...),
) -> Event:
    _ = body
    return Event.mock(topic="message.read.command")
