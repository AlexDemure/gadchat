import uuid

from src.application.collections import ChatMemberRequired
from src.common.formats.utils import date
from src.infrastructure.databases.orm.sqlalchemy.queries import Filter
from src.infrastructure.databases.orm.sqlalchemy.session import Session
from src.infrastructure.databases.postgres import adapters


class Repository:
    def __init__(self, session: Session) -> None:
        self.chat_member = adapters.repositories.ChatMember(session)
        self.message = adapters.repositories.Message(session)
        self.message_read = adapters.repositories.MessageRead(session)


class Security:
    def __init__(self) -> None: ...


class Container:
    def __init__(self, repository: Repository, security: Security) -> None:
        self.repository = repository
        self.security = security


class Usecase:
    def __init__(self, container: Container) -> None:
        self.container = container

    async def validate(
        self,
        chat_id: uuid.UUID,
        message_id: uuid.UUID,
        user_id: str,
    ) -> tuple[object, object]:
        chat_member = await self.container.repository.chat_member.user(chat_id=chat_id, user_id=user_id)
        if chat_member is None:
            raise ChatMemberRequired

        message = await self.container.repository.message.one(
            Filter.eq("id", message_id),
            Filter.eq("chat_id", chat_id),
        )
        return chat_member, message

    async def __call__(self, chat_id: uuid.UUID, message_id: uuid.UUID, user_id: str) -> int:
        chat_member, message = await self.validate(chat_id=chat_id, message_id=message_id, user_id=user_id)
        read_at = date.now()
        count = await self.container.repository.message_read.mark(
            chat_member=chat_member,
            message=message,
            read_at=read_at,
        )
        await self.container.repository.chat_member.mark_read(
            chat_member_id=chat_member.id,
            read_at=message.created,
        )
        return count
