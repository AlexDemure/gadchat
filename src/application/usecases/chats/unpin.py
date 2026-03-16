import uuid

from src.application.collections import ChatMemberRequired
from src.infrastructure.databases.orm.sqlalchemy.session import Session
from src.infrastructure.databases.postgres import adapters


class Repository:
    def __init__(self, session: Session) -> None:
        self.chat_member = adapters.repositories.ChatMember(session)
        self.chat_pin = adapters.repositories.ChatPin(session)


class Security:
    def __init__(self) -> None: ...


class Container:
    def __init__(self, repository: Repository, security: Security) -> None:
        self.repository = repository
        self.security = security


class Usecase:
    def __init__(self, container: Container) -> None:
        self.container = container

    async def validate(self, chat_id: uuid.UUID, user_id: str):
        membership = await self.container.repository.chat_member.user(chat_id=chat_id, user_id=user_id)
        if membership is None:
            raise ChatMemberRequired
        return membership

    async def __call__(self, chat_id: uuid.UUID, user_id: str) -> None:
        membership = await self.validate(chat_id=chat_id, user_id=user_id)
        await self.container.repository.chat_pin.unpin(chat_member_id=membership.id, user_id=user_id)
