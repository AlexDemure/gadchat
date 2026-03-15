import uuid

from fastapi import Depends
from fastapi import UploadFile
from fastapi import status

from src.application.usecases.chats.files.uploads.document import Usecase
from src.entrypoints.http.common.collections import AUTHORIZATION_ERRORS
from src.entrypoints.http.common.deps import jwt
from src.entrypoints.http.public.deps.chats.files.uploads.document import dependency
from src.entrypoints.http.public.schemas.chat import UploadedFile
from src.framework.openapi.utils import errors
from src.framework.routing import APIRouter


router = APIRouter()


@router.post(
    "/chats/{chat_id}/files:upload:document",
    response_model=UploadedFile,
    responses={status.HTTP_401_UNAUTHORIZED: {}, **errors(*AUTHORIZATION_ERRORS)},
    description="Upload a document attachment to a chat",
)
async def command(
    chat_id: uuid.UUID,
    file: UploadFile,
    uid: str = Depends(jwt),
    usecase: Usecase = Depends(dependency),
) -> UploadedFile:
    model = await usecase(chat_id=chat_id, user_id=uid, file=file)
    return UploadedFile.serialize(model)
