from src.common.files.collections import Mimetype
from src.common.formats.utils import date
from src.common.formats.utils import uuid
from src.infrastructure.databases.orm.sqlalchemy.session import Session
from src.infrastructure.databases.postgres import adapters
from src.infrastructure.databases.postgres.tables import File
from src.infrastructure.storages.minio import minio


class Repository:
    def __init__(self, session: Session) -> None:
        self.file = adapters.repositories.File(session)


class Storage:
    def __init__(self) -> None:
        self.minio = minio


class Container:
    def __init__(self, repository: Repository, storage: Storage) -> None:
        self.repository = repository
        self.storage = storage


class Usecase:
    def __init__(self, container: Container) -> None:
        self.container = container

    async def execute(self, filename: str, content_type: Mimetype, content: bytes) -> File:
        file_id = uuid.unique()
        path = f"/uploads/audio/{file_id}{content_type.extension}"
        await self.container.storage.minio.upload(content=content, mimetype=content_type, path=path)
        return await self.container.repository.file.create(
            {
                "id": file_id,
                "path": path,
                "filename": filename,
                "content_type": content_type,
                "size": len(content),
                "created": date.now(),
            },
        )
