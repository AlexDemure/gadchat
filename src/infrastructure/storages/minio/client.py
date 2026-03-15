import contextlib
import typing

import aiofiles

from aioboto3 import Session

from src.common.files.collections import Mimetype
from src.configuration import settings

from .collections import ClientDisabled


class Minio:
    def __init__(self) -> None:
        self.session: typing.Any | None = None

    def start(self) -> None:
        if not settings.MINIO:
            return

        self.session = Session()

    def shutdown(self) -> None: ...

    @contextlib.asynccontextmanager
    async def client(self) -> typing.AsyncGenerator[typing.Any, None]:
        if not self.session:
            raise ClientDisabled

        async with self.session.client(
            "s3",
            endpoint_url=settings.MINIO_HOST,
            aws_access_key_id=settings.MINIO_ACCESS_KEY_ID,
            aws_secret_access_key=settings.MINIO_SECRET_ACCESS_KEY,
        ) as client:
            yield client

    async def upload(self, content: bytes, mimetype: Mimetype, path: str) -> None:
        if not self.session:
            raise ClientDisabled

        async with aiofiles.tempfile.NamedTemporaryFile("wb", suffix=mimetype.extension) as tmp:
            await tmp.write(content)
            async with self.client() as client:
                await client.upload_file(Filename=tmp.name, Bucket=settings.MINIO_BUCKET, Key=path)

    async def download(self, path: str) -> bytes:
        if not self.session:
            raise ClientDisabled

        async with aiofiles.tempfile.NamedTemporaryFile() as tmp:
            async with self.client() as client:
                await client.download_file(Filename=tmp.name, Bucket=settings.MINIO_BUCKET, Key=path)
                await tmp.seek(0)
                return await tmp.read()

    async def delete(self, path: str) -> None:
        if not self.session:
            raise ClientDisabled

        async with self.client() as client:
            await client.delete_object(Bucket=settings.MINIO_BUCKET, Key=path)
