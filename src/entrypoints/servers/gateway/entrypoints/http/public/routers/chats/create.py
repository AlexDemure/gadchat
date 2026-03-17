from fastapi import Body
from fastapi import status

from src.entrypoints.servers.gateway.entrypoints.http.public.schemas.chat import CreateChat
from src.entrypoints.servers.gateway.entrypoints.http.public.schemas.chat import Event
from src.framework.routing import APIRouter


router = APIRouter()


@router.post(
    "/chat.create.command",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=Event,
    description="Create chat",
)
async def command(body: CreateChat = Body(...)) -> Event:
    _ = body
    return Event.mock(topic="chat.create.command")
