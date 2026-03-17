import typing

from src.application.collections import UserNotChatMember
from src.infrastructure.databases.orm.sqlalchemy.queries import And
from src.infrastructure.databases.orm.sqlalchemy.queries import Filter
from src.infrastructure.databases.orm.sqlalchemy.session import Session
from src.infrastructure.databases.postgres import adapters
from src.infrastructure.databases.postgres.tables import Message


class Repository:
    def __init__(self, session: Session) -> None:
        self.member = adapters.repositories.Member(session)
        self.message = adapters.repositories.Message(session)


class Container:
    def __init__(self, repository: Repository) -> None:
        self.repository = repository


class Usecase:
    def __init__(self, container: Container) -> None:
        self.container = container

    async def validate(self, chat_id: str, user_id: str) -> None:
        if not await self.container.repository.member.exists(
            And.combine(
                Filter.eq(key="chat_id", value=chat_id),
                Filter.eq(key="user_id", value=user_id),
            )
        ):
            raise UserNotChatMember

    async def execute(
        self,
        filters: dict[str, typing.Any],
        pagination: dict[str, typing.Any],
    ) -> tuple[list[Message], bool, str | None, str | None]:
        await self.validate(chat_id=filters.get("chat_id"), user_id=filters.get("user_id"))
        member = await self.container.repository.member.one(
            And.combine(
                Filter.eq(key="chat_id", value=filters.get("chat_id")),
                Filter.eq(key="user_id", value=filters.get("user_id")),
            )
        )
        filters["member_id"] = member.id
        return await self.container.repository.message.search(filters=filters, pagination=pagination)
