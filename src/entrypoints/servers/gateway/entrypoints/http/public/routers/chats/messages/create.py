from fastapi import Body
from fastapi import Depends
from fastapi import status

from src.entrypoints.servers.auth.entrypoints.http.common.deps import user
from src.entrypoints.servers.gateway.entrypoints.http.public.schemas.chat import CreateMessage
from src.entrypoints.servers.gateway.entrypoints.http.public.schemas.chat import Event
from src.framework.routing import APIRouter


router = APIRouter()


@router.post(
    "/message.create.command",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=Event,
    description="Create message",
    dependencies=[Depends(user)],
)
async def command(body: CreateMessage = Body(...)) -> Event:
    _ = body
    return Event.mock(topic="message.create.command")
