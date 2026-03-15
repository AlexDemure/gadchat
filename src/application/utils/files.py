import uuid

from fastapi import HTTPException
from fastapi import UploadFile

from src.common.files.collections import Mimetype
from src.common.formats.utils import date
from src.configuration import settings
from src.infrastructure.databases.orm.sqlalchemy.session import Session
from src.infrastructure.databases.postgres.crud import File
from src.infrastructure.storages.minio import minio


def validate_content_type(
    content_type: str | None,
    allowed: set[Mimetype],
    error_detail: str,
) -> Mimetype:
    if not content_type:
        raise HTTPException(status_code=400, detail=error_detail)
    try:
        mimetype = Mimetype(content_type)
    except ValueError as exc:
        raise HTTPException(status_code=415, detail=error_detail) from exc
    if mimetype not in allowed:
        raise HTTPException(status_code=415, detail=error_detail)
    return mimetype


async def upload_chat_file(
    *,
    session: Session,
    chat_id: uuid.UUID,
    file: UploadFile,
    folder: str,
    allowed: set[Mimetype],
    content_type_error: str,
) -> object:
    mimetype = validate_content_type(file.content_type, allowed, content_type_error)
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="File is empty")

    key = f"chat/{chat_id}/{folder}/{uuid.uuid4()}{mimetype.extension}"
    await minio.upload(content=content, mimetype=mimetype, path=key)

    return await File.create(
        session,
        {
            "id": uuid.uuid4(),
            "storage": "s3",
            "bucket": settings.MINIO_BUCKET,
            "key": key,
            "filename": file.filename,
            "content_type": file.content_type,
            "size_bytes": len(content),
            "created": date.now(),
        },
    )
