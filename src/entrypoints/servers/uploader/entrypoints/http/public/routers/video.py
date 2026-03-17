from fastapi import Depends
from fastapi import UploadFile
from fastapi import status

from src.common.files.collections import Mimetype
from src.entrypoints.servers.uploader.application.usecases import UploadVideo
from src.entrypoints.servers.uploader.entrypoints.http.common.utils import uploadfile
from src.entrypoints.servers.uploader.entrypoints.http.public.deps import video_dependency
from src.entrypoints.servers.uploader.entrypoints.http.public.schemas import File
from src.framework.routing import APIRouter


router = APIRouter()


@router.post(
    "/api/upload:video",
    status_code=status.HTTP_201_CREATED,
    response_model=File,
    description="Upload video",
)
async def command(
    file: UploadFile,
    usecase: UploadVideo = Depends(video_dependency),
) -> File:
    content, content_type = await uploadfile(file=file, mimetypes=Mimetype.video())
    stored = await usecase.execute(
        filename=file.filename,
        content_type=content_type,
        content=content,
    )
    return File.serialize(stored)
