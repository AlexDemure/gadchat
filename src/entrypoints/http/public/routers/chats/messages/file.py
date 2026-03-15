import uuid

from fastapi import Depends
from fastapi import HTTPException
from fastapi import Response
from fastapi import UploadFile

from src.common.files.collections import Mimetype
from src.common.formats.utils import date
from src.configuration import settings
from src.entrypoints.http.common.deps import read
from src.entrypoints.http.common.deps import user_id
from src.entrypoints.http.common.deps import write
from src.entrypoints.http.public.schemas.chat import UploadedFile
from src.framework.routing import APIRouter
from src.infrastructure.databases.orm.sqlalchemy.session import Session
from src.infrastructure.databases.postgres.crud import File
from src.infrastructure.storages.minio import minio


router = APIRouter()


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


async def upload(
    *,
    file: UploadFile,
    folder: str,
    allowed: set[Mimetype],
    content_type_error: str,
    session: Session,
) -> UploadedFile:
    mimetype = validate_content_type(file.content_type, allowed, content_type_error)
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="File is empty")

    key = f"chat/{folder}/{uuid.uuid4()}{mimetype.extension}"
    await minio.upload(content=content, mimetype=mimetype, path=key)

    model = await File.create(
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
    return UploadedFile.serialize(model)


@router.post("/files/upload:image", response_model=UploadedFile)
async def command_image(
    file: UploadFile,
    _uid: str = Depends(user_id),
    session: Session = Depends(write),
) -> UploadedFile:
    return await upload(
        file=file,
        folder="images",
        allowed={
            Mimetype.png,
            Mimetype.jpeg,
            Mimetype.jpg,
            Mimetype.gif,
            Mimetype.bmp,
            Mimetype.webp,
            Mimetype.svg,
            Mimetype.tiff,
        },
        content_type_error="Unsupported image content-type",
        session=session,
    )


@router.post("/files/upload:video", response_model=UploadedFile)
async def command_video(
    file: UploadFile,
    _uid: str = Depends(user_id),
    session: Session = Depends(write),
) -> UploadedFile:
    return await upload(
        file=file,
        folder="videos",
        allowed={
            Mimetype.mp4,
            Mimetype.webm,
            Mimetype.avi,
            Mimetype.mov,
            Mimetype.mpeg,
            Mimetype.mkv,
        },
        content_type_error="Unsupported video content-type",
        session=session,
    )


@router.post("/files/upload:audio", response_model=UploadedFile)
async def command_audio(
    file: UploadFile,
    _uid: str = Depends(user_id),
    session: Session = Depends(write),
) -> UploadedFile:
    return await upload(
        file=file,
        folder="audios",
        allowed={
            Mimetype.mp3,
            Mimetype.wav,
            Mimetype.ogg,
            Mimetype.flac,
            Mimetype.aac,
        },
        content_type_error="Unsupported audio content-type",
        session=session,
    )


@router.post("/files/upload:document", response_model=UploadedFile)
async def command_document(
    file: UploadFile,
    _uid: str = Depends(user_id),
    session: Session = Depends(write),
) -> UploadedFile:
    return await upload(
        file=file,
        folder="documents",
        allowed={
            Mimetype.txt,
            Mimetype.csv,
            Mimetype.html,
            Mimetype.css,
            Mimetype.js,
            Mimetype.json,
            Mimetype.xml,
            Mimetype.pdf,
            Mimetype.doc,
            Mimetype.docx,
            Mimetype.xls,
            Mimetype.xlsx,
            Mimetype.ppt,
            Mimetype.pptx,
        },
        content_type_error="Unsupported document content-type",
        session=session,
    )


@router.get("/files/{file_id}/content")
async def query(
    file_id: uuid.UUID,
    session: Session = Depends(read),
) -> Response:
    row = await session.get(File.table, file_id)
    if row is None:
        raise HTTPException(status_code=404, detail="File not found")

    content = await minio.download(row.key)
    return Response(
        content=content,
        media_type=row.content_type or "application/octet-stream",
        headers={"Cache-Control": "public, max-age=604800"},
    )
