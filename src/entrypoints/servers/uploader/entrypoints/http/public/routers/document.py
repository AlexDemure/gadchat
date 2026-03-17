from fastapi import Depends
from fastapi import UploadFile
from fastapi import status

from src.common.files.collections import Mimetype
from src.entrypoints.servers.uploader.application.usecases import UploadDocument
from src.entrypoints.servers.uploader.entrypoints.http.common.utils import uploadfile
from src.entrypoints.servers.uploader.entrypoints.http.public.deps import document_dependency
from src.entrypoints.servers.uploader.entrypoints.http.public.schemas import File
from src.framework.routing import APIRouter


router = APIRouter()


@router.post(
    "/api/upload:document",
    status_code=status.HTTP_201_CREATED,
    response_model=File,
    description="Upload document",
)
async def command(
    file: UploadFile,
    usecase: UploadDocument = Depends(document_dependency),
) -> File:
    content, content_type = await uploadfile(file=file, mimetypes=Mimetype.document())
    stored = await usecase.execute(
        filename=file.filename,
        content_type=content_type,
        content=content,
    )
    return File.serialize(stored)
