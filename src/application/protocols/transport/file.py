import typing

from pydantic import BaseModel

from src.configuration import settings


class File(BaseModel):
    filename: str
    content_type: str
    size: int
    path: str
    url: str

    @classmethod
    def create(cls, filename: str, content_type: str, size: int, path: str) -> typing.Self:
        return cls(
            filename=filename,
            content_type=content_type,
            size=size,
            path=path,
            url=f"{settings.MINIO_HOST.rstrip('/')}/{settings.MINIO_BUCKET}{path}",
        )
