from src.application.collections import ChatNotFound
from src.application.collections import UserNotChatMember
from src.common.files.collections import Mimetype
from src.common.formats.utils import date
from src.common.formats.utils import uuid
from src.infrastructure.databases.orm.sqlalchemy.queries import And
from src.infrastructure.databases.orm.sqlalchemy.queries import Filter
from src.infrastructure.databases.orm.sqlalchemy.session import Session
from src.infrastructure.databases.postgres import adapters
from src.infrastructure.databases.postgres.tables import File
from src.infrastructure.databases.postgres.tables import User
from src.infrastructure.storages.minio import minio


class Repository:
    def __init__(self, session: Session) -> None:
        self.chat = adapters.repositories.Chat(session)
        self.member = adapters.repositories.Member(session)
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

    async def validate(self, chat_id: str, user_id: str) -> None:
        if not await self.container.repository.chat.exists(Filter.eq(key="id", value=chat_id)):
            raise ChatNotFound

        if not await self.container.repository.member.exists(
            And.combine(
                Filter.eq(key="chat_id", value=chat_id),
                Filter.eq(key="user_id", value=user_id),
            )
        ):
            raise UserNotChatMember

    async def __call__(
        self,
        user: User,
        chat_id: str,
        filename: str,
        content_type: Mimetype,
        content: bytes,
    ) -> File:
        await self.validate(chat_id=chat_id, user_id=user.id)

        file_id = uuid.unique()

        path = f"/chats/{chat_id}/document/{file_id}{content_type.extension}"

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
