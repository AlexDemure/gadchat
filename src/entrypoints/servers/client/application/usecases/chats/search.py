import typing

from src.infrastructure.databases.orm.sqlalchemy.session import Session
from src.infrastructure.databases.postgres import adapters
from src.infrastructure.databases.postgres.tables import Chat


class Repository:
    def __init__(self, session: Session) -> None:
        self.chat = adapters.repositories.Chat(session)


class Container:
    def __init__(self, repository: Repository) -> None:
        self.repository = repository


class Usecase:
    def __init__(self, container: Container) -> None:
        self.container = container

    async def execute(
        self,
        filters: dict[str, typing.Any],
        pagination: dict[str, typing.Any],
    ) -> tuple[list[Chat], bool, str | None, str | None]:
        return await self.container.repository.chat.search(filters=filters, pagination=pagination)
