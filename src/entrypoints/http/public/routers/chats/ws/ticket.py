from fastapi import Depends

from src.entrypoints.http.common.deps import user_id
from src.entrypoints.http.public.collections.chats import sign_ws_ticket
from src.framework.routing import APIRouter


router = APIRouter()


@router.post("/ws-ticket")
async def command(uid: str = Depends(user_id)) -> dict[str, str]:
    return {"ticket": sign_ws_ticket(uid)}
