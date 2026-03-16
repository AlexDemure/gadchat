import uuid

from src.application.collections import MemberRequired
from src.infrastructure.databases.orm.sqlalchemy.session import Session
from src.infrastructure.databases.postgres import adapters


class Repository:
    def __init__(self, session: Session) -> None:
        self.member = adapters.repositories.Member(session)


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
        member = await self.container.repository.member.user(chat_id=chat_id, user_id=user_id)
        if member is None:
            raise MemberRequired
        return member

    async def __call__(self, chat_id: uuid.UUID, user_id: str) -> None:
        member = await self.validate(chat_id=chat_id, user_id=user_id)
        await self.container.repository.member.unpin(member_id=member.id, user_id=user_id)
