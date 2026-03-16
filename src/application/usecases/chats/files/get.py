import uuid

from fastapi import HTTPException

from src.application.collections import ChatMemberRequired
from src.infrastructure.databases.orm.sqlalchemy.queries import Filter
from src.infrastructure.databases.orm.sqlalchemy.session import Session
from src.infrastructure.databases.postgres import adapters
from src.infrastructure.storages.minio import minio


class Repository:
    def __init__(self, session: Session) -> None:
        self.chat_member = adapters.repositories.ChatMember(session)
        self.file = adapters.repositories.File(session)
        self.message_file = adapters.repositories.MessageFile(session)


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
        if await self.container.repository.chat_member.user(chat_id=chat_id, user_id=user_id) is None:
            raise ChatMemberRequired

    async def __call__(self, chat_id: uuid.UUID, file_id: uuid.UUID, user_id: str) -> tuple[bytes, str | None]:
        await self.validate(chat_id=chat_id, user_id=user_id)

        if not await self.container.repository.message_file.exists(
            Filter.eq("chat_id", chat_id),
            Filter.eq("file_id", file_id),
        ):
            raise HTTPException(status_code=404, detail="File not found")

        row = await self.container.repository.file.one(Filter.eq("id", file_id))

        return await minio.download(row.key), row.content_type
