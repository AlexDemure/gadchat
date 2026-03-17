from fastapi import Depends
from fastapi import UploadFile
from fastapi import status

from src.common.files.collections import Mimetype
from src.entrypoints.servers.auth.entrypoints.http.common.deps import user
from src.entrypoints.servers.uploader.application.usecases.files.audio import Usecase
from src.entrypoints.servers.uploader.entrypoints.http.common.utils import uploadfile
from src.entrypoints.servers.uploader.entrypoints.http.public.deps.files.audio import dependency
from src.entrypoints.servers.uploader.entrypoints.http.public.schemas import File
from src.framework.routing import APIRouter


router = APIRouter()


@router.post(
    "/api/files:audio",
    status_code=status.HTTP_201_CREATED,
    response_model=File,
    description="Upload audio",
    dependencies=[Depends(user)],
)
async def command(
    file: UploadFile,
    usecase: Usecase = Depends(dependency),
) -> File:
    content, content_type = await uploadfile(file=file, mimetypes=Mimetype.audio())
    stored = await usecase.execute(
        filename=file.filename,
        content_type=content_type,
        content=content,
    )
    return File.serialize(stored)
