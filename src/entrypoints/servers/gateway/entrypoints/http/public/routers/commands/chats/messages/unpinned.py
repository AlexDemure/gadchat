from fastapi import Body
from fastapi import Depends
from fastapi import status

from src.application.collections import Topic
from src.entrypoints.servers.auth.entrypoints.http.common.deps import user
from src.framework.routing import APIRouter
from src.protocols import Event
from src.protocols.commands import UnpinMessage


router = APIRouter()


@router.post(
    f"/{Topic.message_unpin.command}",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=Event,
    description="Unpin message command",
    dependencies=[Depends(user)],
)
async def command(body: UnpinMessage = Body(...)) -> Event:
    _ = body
    return Event.mock(topic=Topic.message_unpin.command)
