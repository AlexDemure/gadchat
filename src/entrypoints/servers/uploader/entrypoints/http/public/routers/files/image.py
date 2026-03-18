from fastapi import Depends
from fastapi import UploadFile
from fastapi import status

from src.common.files.collections import Mimetype
from src.entrypoints.http.common.deps.token import dependency as token
from src.entrypoints.servers.uploader.application.usecases.files.image import Usecase
from src.entrypoints.servers.uploader.entrypoints.http.common.utils import uploadfile
from src.entrypoints.servers.uploader.entrypoints.http.public.deps.files.image import dependency
from src.entrypoints.servers.uploader.entrypoints.http.public.schemas import File
from src.framework.routing import APIRouter


router = APIRouter()


@router.post(
    "/api/files:image",
    status_code=status.HTTP_201_CREATED,
    response_model=File,
    description="Upload image",
    dependencies=[Depends(token)],
)
async def command(
    file: UploadFile,
    usecase: Usecase = Depends(dependency),
) -> File:
    content, content_type = await uploadfile(file=file, mimetypes=Mimetype.image())
    stored = await usecase.execute(
        filename=file.filename,
        content_type=content_type,
        content=content,
    )
    return File.serialize(stored)
