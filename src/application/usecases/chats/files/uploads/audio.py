import uuid

from fastapi import HTTPException
from fastapi import UploadFile

from src.application.usecases.chats.collections import ChatMemberRequired
from src.application.utils.files import upload_chat_file
from src.common.files.collections import Mimetype
from src.infrastructure.databases.orm.sqlalchemy import queries
from src.infrastructure.databases.orm.sqlalchemy.session import Session
from src.infrastructure.databases.postgres.crud import Chat
from src.infrastructure.databases.postgres.crud import Member


class Repositories:
    def __init__(self, session: Session) -> None:
        self.chat = Chat
        self.member = Member
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
        chat = await self.container.repositories.session.get(self.container.repositories.chat.table, chat_id)
        if chat is None:
            raise HTTPException(status_code=404, detail="Chat not found")

        member = await self.container.repositories.member.user(
            self.container.repositories.session,
            queries.Filter.eq(key="chat_id", value=chat.id),
            queries.Filter.eq(key="shard_id", value=chat.shard_id),
            queries.Filter.eq(key="user_id", value=user_id),
        )
        if member is None:
            raise ChatMemberRequired

    async def __call__(self, *, chat_id: uuid.UUID, user_id: str, file: UploadFile) -> object:
        await self.validate(chat_id=chat_id, user_id=user_id)
        return await upload_chat_file(
            session=self.container.repositories.session,
            chat_id=chat_id,
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
        )
