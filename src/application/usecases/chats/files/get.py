import uuid

from fastapi import HTTPException

from src.application.collections import MemberRequired
from src.infrastructure.databases.orm.sqlalchemy.queries import Filter
from src.infrastructure.databases.orm.sqlalchemy.session import Session
from src.infrastructure.databases.postgres import adapters
from src.infrastructure.storages.minio import minio


class Repository:
    def __init__(self, session: Session) -> None:
        self.member = adapters.repositories.Member(session)
        self.file = adapters.repositories.File(session)
        self.attachment = adapters.repositories.Attachment(session)


class Security:
    def __init__(self) -> None: ...


class Container:
    def __init__(self, repository: Repository, security: Security) -> None:
        self.repository = repository
        self.security = security


class Usecase:
    def __init__(self, container: Container) -> None:
        self.container = container

    async def validate(self, chat_id: uuid.UUID, user_id: str) -> None:
        if await self.container.repository.member.user(chat_id=chat_id, user_id=user_id) is None:
            raise MemberRequired

    async def __call__(self, chat_id: uuid.UUID, file_id: uuid.UUID, user_id: str) -> tuple[bytes, str | None]:
        await self.validate(chat_id=chat_id, user_id=user_id)

        if not await self.container.repository.attachment.exists_in_chat(chat_id=str(chat_id), file_id=str(file_id)):
            raise HTTPException(status_code=404, detail="File not found")

        row = await self.container.repository.file.one(Filter.eq("id", file_id))

        return await minio.download(row.key), row.content_type
