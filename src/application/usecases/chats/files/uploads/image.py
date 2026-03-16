import uuid

from fastapi import HTTPException
from fastapi import UploadFile

from src.application.collections import ChatMemberRequired
from src.common.files.collections import Mimetype
from src.common.formats.utils import date
from src.configuration import settings
from src.infrastructure.databases.orm.sqlalchemy.queries import Filter
from src.infrastructure.databases.orm.sqlalchemy.session import Session
from src.infrastructure.databases.postgres import adapters
from src.infrastructure.storages.minio import minio


class Repository:
    def __init__(self, session: Session) -> None:
        self.chat = adapters.repositories.Chat(session)
        self.chat_member = adapters.repositories.ChatMember(session)
        self.file = adapters.repositories.File(session)


class Security:
    def __init__(self) -> None: ...


class Storage:
    def __init__(self) -> None:
        self.minio = minio


class Container:
    def __init__(self, repository: Repository, security: Security, storage: Storage) -> None:
        self.repository = repository
        self.security = security
        self.storage = storage


class Usecase:
    def __init__(self, container: Container) -> None:
        self.container = container

    async def validate(self, chat_id: uuid.UUID, user_id: str) -> None:
        chat = await self.container.repository.chat.one(Filter.eq("id", chat_id))
        if await self.container.repository.chat_member.user(chat_id=chat.id, user_id=user_id) is None:
            raise ChatMemberRequired

    async def __call__(self, chat_id: uuid.UUID, user_id: str, file: UploadFile) -> object:
        await self.validate(chat_id=chat_id, user_id=user_id)
        mimetype = Mimetype(file.content_type)
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="File is empty")

        key = f"chat/{chat_id}/images/{uuid.uuid4()}{mimetype.extension}"
        await self.container.storage.minio.upload(content=content, mimetype=mimetype, path=key)
        return await self.container.repository.file.create(
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
