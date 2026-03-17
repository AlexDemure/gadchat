from fastapi import HTTPException
from fastapi import UploadFile

from src.common.files.collections import Mimetype


async def uploadfile(file: UploadFile, mimetypes: list[Mimetype]) -> tuple[bytes, Mimetype]:
    if not file.content_type:
        raise HTTPException(status_code=400)

    try:
        content_type = Mimetype(file.content_type)
    except ValueError as exc:
        raise HTTPException(status_code=415) from exc

    if content_type not in mimetypes:
        raise HTTPException(status_code=415)

    return await file.read(), content_type
