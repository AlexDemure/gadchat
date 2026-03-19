from fastapi import Depends
from fastapi import UploadFile
from fastapi import status

from src.application.protocols import transport
from src.common.files.collections import Mimetype
from src.entrypoints.http.common.deps.token import dependency as token
from src.entrypoints.servers.upload.application.usecases.files.document import Usecase
from src.entrypoints.servers.upload.entrypoints.http.common.utils import uploadfile
from src.entrypoints.servers.upload.entrypoints.http.public.deps.files.document import dependency
from src.framework.routing import APIRouter


router = APIRouter()


@router.post(
    "/api/files:document",
    status_code=status.HTTP_201_CREATED,
    response_model=transport.File,
    description="Upload document",
    dependencies=[Depends(token)],
)
async def command(
    file: UploadFile,
    usecase: Usecase = Depends(dependency),
) -> transport.File:
    content, content_type = await uploadfile(file=file, mimetypes=Mimetype.document())
    return await usecase.execute(filename=file.filename, content_type=content_type, content=content)
