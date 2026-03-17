from src.entrypoints.servers.gateway.application.collections import UserNotChatMember
from src.infrastructure.databases.orm.sqlalchemy.queries import And
from src.infrastructure.databases.orm.sqlalchemy.queries import Filter
from src.infrastructure.databases.orm.sqlalchemy.session import Session
from src.infrastructure.databases.postgres import adapters
from src.infrastructure.databases.postgres.tables import User


class Repository:
    def __init__(self, session: Session) -> None:
        self.member = adapters.repositories.Member(session)


class Container:
    def __init__(self, repository: Repository) -> None:
        self.repository = repository


class Usecase:
    def __init__(self, container: Container) -> None:
        self.container = container

    async def validate(self, user_id: str, chat_id: str) -> None:
        if not await self.container.repository.member.exists(
            And.combine(
                Filter.eq(key="chat_id", value=chat_id),
                Filter.eq(key="user_id", value=user_id),
            )
        ):
            raise UserNotChatMember

    async def execute(self, user: User, chat_id: str, position: int | None) -> None:
        await self.validate(user_id=user.id, chat_id=chat_id)

        member = await self.container.repository.member.one(
            And.combine(
                Filter.eq(key="chat_id", value=chat_id),
                Filter.eq(key="user_id", value=user.id),
            )
        )

        await self.container.repository.member.update(id=member.id, position=position)

    async def publish(self, user: User, chat_id: str, position: int | None) -> None:
        await self.execute(user=user, chat_id=chat_id, position=position)
