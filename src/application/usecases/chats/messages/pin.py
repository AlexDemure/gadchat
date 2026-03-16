import uuid

from src.application.collections import ChatMemberRequired
from src.infrastructure.databases.orm.sqlalchemy.queries import Filter
from src.infrastructure.databases.orm.sqlalchemy.session import Session
from src.infrastructure.databases.postgres import adapters


class Repository:
    def __init__(self, session: Session) -> None:
        self.chat_member = adapters.repositories.ChatMember(session)
        self.message = adapters.repositories.Message(session)


class Security:
    def __init__(self) -> None: ...


class Container:
    def __init__(self, repository: Repository, security: Security) -> None:
        self.repository = repository
        self.security = security


class Usecase:
    def __init__(self, container: Container) -> None:
        self.container = container

    async def validate(self, chat_id: uuid.UUID, message_id: uuid.UUID, user_id: str) -> None:
        membership = await self.container.repository.chat_member.user(chat_id=chat_id, user_id=user_id)
        if membership is None:
            raise ChatMemberRequired

        await self.container.repository.message.one(
            Filter.eq("id", message_id),
            Filter.eq("chat_id", chat_id),
        )

    async def __call__(self, chat_id: uuid.UUID, message_id: uuid.UUID, user_id: str) -> None:
        await self.validate(chat_id=chat_id, message_id=message_id, user_id=user_id)
        await self.container.repository.message.pin(message_id=message_id, chat_id=chat_id)
