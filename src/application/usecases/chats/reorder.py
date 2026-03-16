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

    async def validate(self, chat_ids: list[uuid.UUID], user_id: str) -> None:
        for chat_id in chat_ids:
            if await self.container.repository.chat_member.user(chat_id=chat_id, user_id=user_id) is None:
                raise ChatMemberRequired

    async def __call__(self, chat_ids: list[uuid.UUID], user_id: str) -> None:
        await self.validate(chat_ids=chat_ids, user_id=user_id)
        await self.container.repository.chat_pin.reorder(user_id=user_id, chat_ids=chat_ids)
