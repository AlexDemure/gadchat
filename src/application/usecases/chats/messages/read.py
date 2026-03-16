import uuid

from src.application.collections import MemberRequired
from src.common.formats.utils import date
from src.infrastructure.databases.orm.sqlalchemy.queries import Filter
from src.infrastructure.databases.orm.sqlalchemy.session import Session
from src.infrastructure.databases.postgres import adapters


class Repository:
    def __init__(self, session: Session) -> None:
        self.member = adapters.repositories.Member(session)
        self.message = adapters.repositories.Message(session)
        self.read = adapters.repositories.Read(session)


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
        member = await self.container.repository.member.user(chat_id=chat_id, user_id=user_id)
        if member is None:
            raise MemberRequired

        message = await self.container.repository.message.one(
            Filter.eq("id", message_id),
            Filter.eq("chat_id", chat_id),
        )
        return member, message

    async def __call__(self, chat_id: uuid.UUID, message_id: uuid.UUID, user_id: str) -> int:
        member, message = await self.validate(chat_id=chat_id, message_id=message_id, user_id=user_id)
        read = date.now()
        count = await self.container.repository.read.mark(
            member=member,
            message=message,
            read=read,
        )
        notifications = max(member.notifications - count, 0)
        await self.container.repository.member.mark_read(
            chat_member_id=member.id,
            message_id=message.id,
            read=read,
            unread_count=notifications,
        )
        return count
