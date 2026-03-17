from src.entrypoints.servers.client.application.collections import MessageNotFound
from src.entrypoints.servers.client.application.collections import UserNotChatMember
from src.infrastructure.databases.orm.sqlalchemy.queries import And
from src.infrastructure.databases.orm.sqlalchemy.queries import Filter
from src.infrastructure.databases.orm.sqlalchemy.session import Session
from src.infrastructure.databases.postgres import adapters
from src.infrastructure.databases.postgres.tables import User


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

    async def validate(self, chat_id: str, message_id: str, user_id: str) -> None:
        if not await self.container.repository.member.exists(
            And.combine(
                Filter.eq(key="chat_id", value=chat_id),
                Filter.eq(key="user_id", value=user_id),
            )
        ):
            raise UserNotChatMember

        if not await self.container.repository.message.exists(
            And.combine(
                Filter.eq(key="id", value=message_id),
                Filter.eq(key="chat_id", value=chat_id),
            )
        ):
            raise MessageNotFound

    async def execute(self, user: User, chat_id: str, message_id: str) -> None:
        await self.validate(chat_id=chat_id, message_id=message_id, user_id=user.id)
        await self.container.repository.message.update(id=message_id, pinned=None)

    async def publish(self, user: User, chat_id: str, message_id: str) -> None:
        await self.execute(user=user, chat_id=chat_id, message_id=message_id)
