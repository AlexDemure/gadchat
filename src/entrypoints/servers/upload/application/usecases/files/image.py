from src.application.protocols import transport
from src.common.files.collections import Mimetype
from src.common.formats.utils import uuid
from src.infrastructure.storages.minio import minio


class Storage:
    def __init__(self) -> None:
        self.minio = minio


class Container:
    def __init__(self, storage: Storage) -> None:
        self.storage = storage


class Usecase:
    def __init__(self) -> None:
        self.container = Container(storage=Storage())

    async def execute(self, filename: str, content_type: Mimetype, content: bytes) -> transport.File:
        file_id = uuid.unique()

        path = f"/uploads/images/{file_id}{content_type.extension}"

        await self.container.storage.minio.upload(content=content, mimetype=content_type, path=path)

        return transport.File.create(
            filename=filename,
            content_type=content_type,
            size=len(content),
            path=path,
        )
