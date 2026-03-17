import typing

from src.configuration import settings
from src.entrypoints.http.common.schemas import Response
from src.entrypoints.http.public.schemas.base import Public
from src.infrastructure.databases.postgres.tables import File as _File


class File(Public, Response):
    id: str
    filename: str | None
    content_type: str | None
    path: str
    url: str

    @classmethod
    def serialize(cls, file: _File) -> typing.Self:
        return cls(
            id=file.id,
            filename=file.filename,
            content_type=file.content_type,
            path=file.path,
            url=f"{settings.MINIO_HOST.rstrip('/')}/{settings.MINIO_BUCKET}{file.path}",
        )
