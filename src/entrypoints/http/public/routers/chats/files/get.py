import uuid

from fastapi import Depends
from fastapi import Response
from fastapi import status

from src.application.usecases.chats.files.get import Usecase
from src.entrypoints.http.common.collections import AUTHORIZATION_ERRORS
from src.entrypoints.http.common.deps import jwt
from src.entrypoints.http.public.deps.chats.files.get import dependency
from src.framework.openapi.utils import errors
from src.framework.routing import APIRouter


router = APIRouter()


@router.get(
    "/chats/{chat_id}/files/{file_id}",
    responses={status.HTTP_401_UNAUTHORIZED: {}, **errors(*AUTHORIZATION_ERRORS)},
    description="Download chat attachment content by file id",
)
async def query(
    chat_id: uuid.UUID,
    file_id: uuid.UUID,
    uid: str = Depends(jwt),
    usecase: Usecase = Depends(dependency),
) -> Response:
    content, content_type = await usecase(chat_id=chat_id, file_id=file_id, user_id=uid)
    return Response(
        content=content,
        media_type=content_type or "application/octet-stream",
        headers={"Cache-Control": "public, max-age=604800"},
    )
