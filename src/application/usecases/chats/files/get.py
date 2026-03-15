import uuid

from fastapi import HTTPException
from sqlalchemy import select

from src.application.usecases.chats.collections import ChatMemberRequired
from src.infrastructure.databases.orm.sqlalchemy import queries
from src.infrastructure.databases.orm.sqlalchemy.session import Session
from src.infrastructure.databases.postgres.crud import File
from src.infrastructure.databases.postgres.crud import Member
from src.infrastructure.databases.postgres.crud import MessageFile
from src.infrastructure.storages.minio import minio


class Repositories:
    def __init__(self, session: Session) -> None:
        self.file = File
        self.member = Member
        self.message_file = MessageFile
        self.session = session


class Security:
    def __init__(self) -> None: ...


class Container:
    def __init__(self, repositories: Repositories, security: Security) -> None:
        self.repositories = repositories
        self.security = security


class Usecase:
    def __init__(self, container: Container) -> None:
        self.container = container

    async def validate(self, *, chat_id: uuid.UUID, user_id: str) -> None:
        member = await self.container.repositories.member.user(
            self.container.repositories.session,
            queries.Filter.eq(key="chat_id", value=chat_id),
            queries.Filter.eq(key="user_id", value=user_id),
        )
        if member is None:
            raise ChatMemberRequired

    async def __call__(self, *, chat_id: uuid.UUID, file_id: uuid.UUID, user_id: str) -> tuple[bytes, str | None]:
        await self.validate(chat_id=chat_id, user_id=user_id)

        relation = await self.container.repositories.session.execute(
            select(self.container.repositories.message_file.table).where(
                self.container.repositories.message_file.table.chat_id == chat_id,
                self.container.repositories.message_file.table.file_id == file_id,
            )
        )
        if relation.scalar_one_or_none() is None:
            raise HTTPException(status_code=404, detail="File not found")

        row = await self.container.repositories.session.get(self.container.repositories.file.table, file_id)
        if row is None:
            raise HTTPException(status_code=404, detail="File not found")

        return await minio.download(row.key), row.content_type
