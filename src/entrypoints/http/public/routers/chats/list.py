from fastapi import Depends
from fastapi import Query

from src.application.usecases.chats.list import Usecase
from src.entrypoints.http.common.deps import user_id
from src.entrypoints.http.public.deps.chats.list import dependency
from src.entrypoints.http.public.schemas.chat import Chats
from src.framework.routing import APIRouter


router = APIRouter()


@router.get("/chats", response_model=Chats)
async def query(
    limit: int = Query(default=20, ge=1, le=100),
    uid: str = Depends(user_id),
    usecase: Usecase = Depends(dependency),
) -> Chats:
    payload = await usecase(uid, limit)
    return Chats.serialize(payload["items"])
