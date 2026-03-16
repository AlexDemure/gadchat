import typing

from src.application.collections import ChatMemberRequired
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

    async def validate(self, chat_id: typing.Any, user_id: typing.Any) -> typing.Any:
        membership = await self.container.repository.chat_member.user(chat_id=chat_id, user_id=user_id)
        if membership is None:
            raise ChatMemberRequired
        return membership

    async def __call__(
        self,
        filters: dict[str, typing.Any],
        sorting: dict[str, typing.Any],
        pagination: dict[str, typing.Any],
    ) -> dict[str, typing.Any]:
        membership = await self.validate(
            chat_id=filters.get("chat_id"),
            user_id=filters.get("user_id"),
        )
        filters["shard_id"] = membership.shard_id
        return await self.container.repository.message.search(
            filters=filters,
            sorting=sorting,
            pagination=pagination,
        )
