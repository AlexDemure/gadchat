from fastapi import Depends
from fastapi import Path
from fastapi import UploadFile
from fastapi import status

from src.application.collections import ChatNotFound
from src.application.collections import UserNotChatMember
from src.application.usecases.chats.files.uploads.document import Usecase
from src.common.files.collections import Mimetype
from src.entrypoints.http.common.collections import AUTHORIZATION_ERRORS
from src.entrypoints.http.common.deps import user
from src.entrypoints.http.common.utils import uploadfile
from src.entrypoints.http.public.deps.chats.files.uploads.document import dependency
from src.entrypoints.http.public.schemas.chat import File
from src.framework.openapi.utils import errors
from src.framework.routing import APIRouter
from src.infrastructure.databases.postgres.tables import User


router = APIRouter()


@router.post(
    "/chats/{chat_id}/files:upload:document",
    status_code=status.HTTP_201_CREATED,
    response_model=File,
    responses={status.HTTP_401_UNAUTHORIZED: {}, **errors(*AUTHORIZATION_ERRORS, ChatNotFound, UserNotChatMember)},
    description="Upload document",
)
async def command(
    file: UploadFile,
    chat_id: str = Path(...),
    usecase: Usecase = Depends(dependency),
    _user: User = Depends(user),
) -> File:
    content, content_type = await uploadfile(file=file, mimetypes=Mimetype.document())
    file = await usecase(
        user=_user,
        chat_id=chat_id,
        filename=file.filename,
        content_type=content_type,
        content=content,
    )
    return File.serialize(file)
