from fastapi import Body
from fastapi import Depends
from fastapi import status

from src.entrypoints.servers.auth.entrypoints.http.common.deps import user
from src.entrypoints.servers.gateway.entrypoints.http.public.schemas.chat import Event
from src.entrypoints.servers.gateway.entrypoints.http.public.schemas.chat import PositionChat
from src.framework.routing import APIRouter


router = APIRouter()


@router.post(
    "/chat.position.command",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=Event,
    description="Set chat position",
    dependencies=[Depends(user)],
)
async def command(body: PositionChat = Body(...)) -> Event:
    _ = body
    return Event.mock(topic="chat.position.command")
